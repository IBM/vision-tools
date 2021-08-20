#!/usr/bin/env python
# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2021 IBM International Business Machines Corp.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#           http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  IBM_PROLOG_END_TAG

"""
This script manages MVI migration activities that are running in a POD. It is setup to handle
the pod being run in a deployment. Therefore, steps are taken to track migration progress so
that if the pod restarts, previously completed migration steps are not repeated.

The pod must be running on the source MVI server that is being migrated.

Note that aborting a migration must be performed outside of the POD by deleting the deployment.

This script can handle migrating an entire server, one or more users on a server, or one or more
project groups on a server. It does not support mixing of migration scopes (e.g. you cannot migrate users
and project groups in a single invocation).

For user and project group migration, the database migration must be done differently. The selection of
DB artifacts must be selective relative to the user(s) or project groups(s) specified. This selection
impacts which files are migrated when migrating project groups. Therefore, for users and project groups,
the database artifact collection must be performed before the files are collected and migrated.

This script uses subordinate scripts to accomplish some of its work. The file migration is
handled by a separate script. The database migration is a "mixed bag" due to the need to use information
from the DB artifacts to identify files to be migrated.
 * For full server migrations, a subordinate script is used to collect the DB artifacts (backupMviDb.py)
 * For project groups, DB artifact collection is performed in this script (as dataset and trained-model
       related files are determined by the DB artifacts collected).
 * For users, DB artifact collection is performed in this script as well. The files to migrate are not
       determined by the DB artifacts, but the DB artifact collection is the same and shared with
       project group DB artifact collection.

Actual migration of data is handled by subordinate scripts (migrateMviFiles.py and restoreMviDb.py).
The actual migration of data is performed on each item specified. So, if multiple users (or project groups)
were given on input, each user (or project group) is migrated independent of the others.
"""
import argparse
import os
import os.path
import json
import subprocess
import sys
import logging
import zipfile
from datetime import datetime

import vapi.accessors.MongoAccessor as MongoAccessor
from inspect import getsourcefile


class Status:
    STARTING = "starting"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    FILES_RUNNING = "files_running"
    FILES_COMPLETE = "files_complete"
    FILES_FAILED = "files_failed"
    DB_BACKUP_RUNNING = "db_backup_running"
    DB_BACKUP_COMPLETE = "db_backup_complete"
    DB_BACKUP_FAILED = "db_backup_failed"
    DB_RESTORE_RUNNING = "db_restore_running"
    DB_RESTORE_COMPLETE = "db_restore_complete"
    DB_RESTORE_FAILED = "db_restore_failed"
    DB_COMPLETE = "db_complete"
    DB_FAILED = "db_failed"

    @staticmethod
    def subStatus(status, item):
        return status + f"({item})"


# Migration sub-commands run from this script
SCRIPT_DIR = os.path.dirname(getsourcefile(lambda: 0))
MIGRATE_MVI_FILES_CMD = f"{SCRIPT_DIR}/migrateMviFiles.py"
BACKUP_MVI_DB_CMD = f"{SCRIPT_DIR}/backupMviDb.py"
RESTORE_MVI_DB_CMD = f"{SCRIPT_DIR}/restoreMviDb.py"

# Input parameter related variables
args = None
clusterPresent = False
mongoDbCreds = None

# Collections that are subordinate to datasets
secondLevelCollections = [
    "DataSetCategories",
    "DataSetFiles",
    "DataSetFileLabels",
    "DataSetFileUserKeys",
    "DataSetTags",
    "DataSetActiontags",
    "DataSetFileActionLabels",
    "DataSetFileObjectLabels"
]

# Shared variables
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
mountPoint = os.getenv("MIGMGR_MOUNTPOINT", "/opt/powerai-vision/data")
workDir = None
statusDir = None
dbDir = None
fileList = []


def main():
    global args
    args = getInputs()

    if args is not None:
        createWorkDirs(args.deploymentName)
        setLoggingControls(args.logLevel)
        if args.status:
            showStatus()
        else:
            doMigration()
    else:
        exit(1)


def createWorkDirs(deploymentName):
    import pathlib
    global workDir
    workDir = f"{mountPoint}/logs/migrations/{deploymentName}"
    print(f"creating workdir '{workDir}'", file=sys.stderr)
    pathlib.Path(workDir).mkdir(parents=True, exist_ok=True)

    global statusDir
    statusDir = f"{workDir}/status"
    pathlib.Path(statusDir).mkdir(exist_ok=True)

    global dbDir
    dbDir = f"{workDir}/db"
    pathlib.Path(dbDir).mkdir(exist_ok=True)
    pathlib.Path(f"{dbDir}/collections").mkdir(exist_ok=True)
    pathlib.Path(f"{dbDir}/zipfiles").mkdir(exist_ok=True)


def showStatus():
    """ Shows the statuses that have been set."""
    logging.debug("Showing current status...")
    os.system(f"ls -lrt {statusDir}")


def doMigration():
    """ Manages the migration steps based on command input parameters."""

    # Show that migration is running
    if not isStatusSet(Status.RUNNING):
        setStatus(Status.RUNNING)

    if args.wholeServer:
        migrateServer()
    elif args.users:
        migrateUsers(args.users.split(","))
    elif args.projects:
        migrateProjectGroups(args.projcts.split(","))


def migrateServer():
    flist, dbFile = collectWholeServerArtifacts()
    migrateArtifacts(flist, dbFile, "server")


def collectWholeServerArtifacts():
    """ performs the DB backup of the whole server."""
    logging.debug("preparing for DB backup.")

    bkupFile = os.path.join(dbDir, "zipfiles/dbBkup")
    # For now, create the backup command knowing that we are only working with 1.3.0.
    # If we expand migration support for ICP and OCP source clusters, this will have to change.
    backupCmd = [BACKUP_MVI_DB_CMD, "--log", args.logLevel, "--mongoservice", args.sMongoService]
    if args.sMongouser:
        backupCmd.extend(["--mongouser", args.sMongouser, "--mongopassword", args.sMongopw])
    backupCmd.append(bkupFile)

    logging.info(f"Starting DB Backup ({backupCmd})")
    bkupResult = subprocess.run(backupCmd)
    logging.debug(f"db backup returned... {bkupResult}.")

    if bkupResult.returncode == 0:
        logging.info("DB Backup complete.")
        # Have to add ".zip" to create the complete file name generated by the backup command
        bkupFile += ".zip"
    else:
        logging.info(f"DB Backup failed ({bkupResult.returncode})")
        bkupFile = None

    return [mountPoint], bkupFile


def migrateUsers(userList):
    with MongoAccessor.MongoAccessor(mongoDbCreds, mongoService=args.sMongoService) as ma:
        for user in userList:
            flist, dbFile = collectUserDbArtifacts(ma, user)
            migrateArtifacts(flist, dbFile, user)


def migrateProjectGroups(pgList):
    with MongoAccessor.MongoAccessor(mongoDbCreds, mongoService=args.sMongoService) as ma:
        for pgid in pgList:
            flist, dbFile = collectProjectGroupArtifacts(ma, pgid)
            migrateArtifacts(flist, dbFile, pgid)


def collectUsersArtifacts(ma):
    """Adds each user to the file list and collects all DB documents related to the given users."""
    # Convert user list into a directory list (ensure user names are lowercase)
    global fileList
    fileList = [f"data/users/{user.lower()}" for user in args.users.split(",")]

    for userPath in fileList:
        user = os.path.basename(userPath)
        setStatus(Status.subStatus(Status.DB_BACKUP_RUNNING, user))
        if collectUserDbArtifacts(ma, user):
            setStatus(Status.subStatus(Status.DB_BACKUP_COMPLETE, user))
        else:
            setStatus(Status.subStatus(Status.DB_BACKUP_FAILED, user))


def collectUserDbArtifacts(mongo, user):
    """Collects DB artifacts owned by the input user."""

    # Make sure the working collection directory exists
    collectionDir = os.path.join(dbDir, f"""collections/{user}-{timestamp}""")
    try:
        os.mkdir(collectionDir)
    except FileExistsError:
        pass

    # make sure we start with a new zip file
    zipDir = os.path.join(dbDir, "zipfiles")
    zipFileName = os.path.join(zipDir, f"{user}Db.zip")
    if os.path.exists(zipFileName):
        os.remove(zipFileName)
    backupFile = zipfile.ZipFile(zipFileName, mode="w", compression=zipfile.ZIP_DEFLATED)

    dbCollections = mongo.getMviDatabase().list_collection_names()

    logging.info(f"Collecting DB docs for top level user collections.")
    for collection in ["BGTasks", "DLTasks", "TrainedModels", "DnnScripts", "Datasets", "ProjectGroups"]:
        # If Collection is not in the DB, there is nothing the backup.
        if collection in dbCollections:
            backupTopLevelCollection(mongo, backupFile, collectionDir, collection, {"owner": user})
        else:
            logging.info(f"Skipping collection '{collection}'.")

    backupSecondLevelCollectionFiles(backupFile, collectionDir)
    backupFile.close()

    import shutil
    shutil.rmtree(collectionDir)

    return [os.path.join(mountPoint, user)], zipFileName


def backupTopLevelCollection(mongo, zipFile, wkDir, collection, query={}):
    """Top level collections are immediately written to the zipFile. If the collection has "subordinate"
     collections, those associated subordinates are then collected but not written to the zip file."""

    dbCollection = mongo.getMviDatabase()[collection]

    documents = dbCollection.find(query)
    logging.info(f"Backing up documents from collection '{collection}' matching query '{query}'.")
    fileName = os.path.join(wkDir, f"{collection}")

    with open(fileName, "w") as file:
        file.write("[")
        i = 0
        for document in documents:
            if i > 0:
                file.write(",")
                if i % 1000 == 0:
                    logging.debug(f"{i}")
            file.write(json.dumps(document), indent=2)
            if collection == "Datasets":
                collectDatasetArtifacts(mongo, wkDir, document)
            i += 1
        file.write("]")
        logging.info(f"Backed up {i} documents from '{collection}' (query={query}).")

    zipFile.write(fileName)
    os.remove(fileName)


def collectDatasetArtifacts(mongo, wkDir, dataset):
    logging.info(f"""Saving DatasetArtifacts for dataset id '{dataset["_id"]}'""")

    dbCollections = mongo.getMviDatabase().list_collection_names()

    for collection in secondLevelCollections:
        if collection in dbCollections:
            saveDatasetRelatedCollectionsToFile(mongo, collection, {"dataset_id": dataset["_id"]})
        else:
            logging.info(f"Skipping collection '{collection}'.")


def saveDatasetRelatedCollectionsToFile(mongo, wkDir, collection, query):
    """Appends the documents from the given collection that match the query into collection file
     for later backup to the zip file"""
    logging.debug(f"""Saving collection '{collection}' using query '{query}'.""")

    dbCollection = mongo.getMviDatabase()[collection]
    documents = dbCollection.find(query)
    fileName = os.path.join(wkDir, f"{collection}")
    prefix = "," if os.path.exists(fileName) else "["

    with open(fileName, "a") as file:
        i = 0
        for document in documents:

            if i % 1000 == 0:
                logging.debug(f"{i}")

            file.write(prefix)
            file.write(json.dumps(document), indent=2)

            i += 1
        logging.info(f"Saved {i} documents matching query '{query}' from collection '{collection}'")


def backupSecondLevelCollectionFiles(zipFile, wkdir):
    """Backs up any second level collection files that exist into the zip file."""

    for collection in secondLevelCollections:
        fileName = os.path.join(wkdir, collection)
        if os.path.exists(fileName):
            # close the json list in the save file before backing it up in the zipfile.
            with open(fileName, "a") as file:
                file.write("]")
            zipFile.write(fileName)
            os.remove(fileName)


def collectProjectBasedArtifacts(mongo):
    """Collects all DB documents related to the given project IDs and
    adds appropriate files and directories to file list"""
    for pgid in args.projects:
        runningStatus = Status.subStatus(Status.DB_BACKUP_RUNNING, pgid)
        setStatus(runningStatus)
        collectProjectArtifacts(mongo, pgid)
        setStatus(Status.subStatus(Status.DB_BACKUP_COMPLETE, pgid))


def collectProjectArtifacts(mongo, pgid):
    # Make sure the working collection directory exists
    collectionDir = os.path.join(dbDir, f"""collections/{pgid}-{timestamp}""")
    try:
        os.mkdir(collectionDir)
    except FileExistsError:
        pass

    # make sure we start with a new zip file
    zipDir = os.path.join(dbDir, "zipfiles")
    zipFileName = os.path.join(zipDir, f"{pgid}Db.zip")
    if os.path.exists(zipFileName):
        os.remove(zipFileName)
    backupFile = zipfile.ZipFile(zipFileName, mode="w", compression=zipfile.ZIP_DEFLATED)

    pg = saveProjectGroup(mongo, collectionDir, pgid)
    if pg:
        collectPgModels(mongo, collectionDir, pgid)
        collectPgDatasets(mongo, collectionDir, pgid)


def saveProjectGroup(mongo, wkDir, zipfile, pgid):
    """Collects and saves the project group document to the zipfile.
    Returns the project group document"""
    pgCollection = mongo.getMviDatabase()["ProjectGroups"]

    documents = pgCollection.find({"_id": pgid})
    fileName = os.path.join(wkDir, "ProjectGroups")

    with open(fileName, "w") as file:
        file.write("[")
        i = 0
        if len(documents) > 0:
            document = documents[0]
            file.write(json.dumps(document), indent=2)
        else:
            document = None
        file.write("]")

    zipfile.write(fileName)
    os.remove(fileName)

    return document


def migrateArtifacts(flist, dbfile, item):
    logging.info(f"Starting to migrate artifacts for '{item}'. dbfile = '{dbfile}'. Files = '{flist}'.")

    doFileMigration(flist, item)
    doDbMigration(dbfile, item)


def doFileMigration(flist, item):
    """ Performs the file migration if it has not already been done."""

    migrated = False
    logging.debug(f"attempting to start File Migration ({item}).")
    runningStatus = Status.subStatus(Status.FILES_RUNNING, item)
    completeStatus = Status.subStatus(Status.FILES_COMPLETE, item)
    failedStatus = Status.subStatus(Status.FILES_FAILED, item)

    logging.info(f"Preparing for File Migration of '{item}' ({MIGRATE_MVI_FILES_CMD})")
    result = 0
    for filepath in flist:
        if os.path.exists(filepath):
            fileMigrateCmd = [MIGRATE_MVI_FILES_CMD,
                              "--log", args.logLevel,
                              "--cluster_url", args.destCluster,
                              "--project", args.destProject,
                              "--ocptoken", args.destToken,
                              filepath]

            logging.info(f"Starting file migration ({fileMigrateCmd})")
            setStatus(runningStatus)
            filesResult = subprocess.run(fileMigrateCmd)
            logging.debug(f"file migration returned... {filesResult}.")
            result += filesResult.returncode

            if result == 0:
                logging.info("File migration completed.")
                setStatus(completeStatus)
            else:
                logging.info(f"File migration of '{item}' failed ({filesResult.returncode})")
                setStatus(failedStatus)
        else:
            logging.info(f"file path '{filepath}' does not exist; ignoring it.")

    return


def doDbMigration(fileName, item):
    """ performs the DB migration if not already done.
    DB Migration is 2 steps, backup to a zip file and then restore into the destination cluster.
    Note that collecting artifacts will create the zip file in all cases except a whole server migration."""

    logging.debug("attempting to start DB migration.")

    backupCompleteStatus = Status.subStatus(Status.DB_BACKUP_COMPLETE, item)
    restoreRunningStatus = Status.subStatus(Status.DB_RESTORE_RUNNING, item)
    restoreCompleteStatus = Status.subStatus(Status.DB_RESTORE_COMPLETE, item)
    restoreFailedStatus = Status.subStatus(Status.DB_RESTORE_FAILED, item)

    setStatus(restoreRunningStatus)
    rc = doDbRestore(fileName)
    if rc == 0:
        setStatus(restoreCompleteStatus)
    else:
        setStatus(restoreFailedStatus)


def doDbRestore(filePath):
    """ performs the DB restore step if the DB backup completed succesfully and the restore
    has not already been done."""
    restoreCmd = [RESTORE_MVI_DB_CMD,
                  "--log", args.logLevel,
                  "--project", args.destProject,
                  "--cluster_url", args.destCluster,
                  "--ocptoken", args.destToken,
                  os.path.join(filePath)]

    logging.info(f"Starting DB Restore ({restoreCmd})")
    restoreCmd = "/usr/bin/ls"
    restoreResult = subprocess.run(restoreCmd)
    logging.debug(f"db restore returned... {restoreResult}.")

    if restoreResult.returncode == 0:
        logging.info("DB Restore complete.")
    else:
        logging.info(f"DB Restore failed ({restoreResult.returncode})")

    return restoreResult.returncode


def setStatus(status):
    """ Sets the indicated status."""
    fpath = os.path.join(statusDir, status)
    logging.debug(f"Setting status '{status}' ({fpath}).")
    with open(fpath, "w"):
        pass


def clearAllStatus():
    """ Clears all previously set statuses."""
    for f in os.listdir(statusDir):
        os.remove(os.path.join(statusDir, f))


def isStatusSet(status):
    """ Returns True if the indicated status is set (False otherwise)."""
    if os.path.exists(os.path.join(statusDir, status)):
        return True
    return False


def getInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(description="Tool to manage MVI migration.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
This script basically starts migration operations and reports status the operations being performed
by the POD in which this script is run. Parameters will vary based upon the requested operation.
In particular, `--status` request requires no additional  parameters.

Note that it is expected that this script will be called by another script (mviMigrate) and will
not be called directly by a user. As such flags can be terse.
''')

    parser.add_argument("--deployment", action="store", dest="deploymentName", type=str, required=True,
                        help="Name of the deployment with which the pod is associated.")
    parser.add_argument('--log', action="store", dest="logLevel", type=str, required=False, default="info",
                        help='Specify logging level (default is "info")')

    actionGroup = parser.add_mutually_exclusive_group(required=True)
    actionGroup.add_argument('--status', action="store_true", dest="status", required=False, default=False,
                        help="Requests migration status be returned.")
    actionGroup.add_argument('--migType', action="store", dest="migType", type=str, required=False,
                        help="Type of migration to perform. Value must be either 'full', or 'files'.")

    migGroup = parser.add_mutually_exclusive_group()
    migGroup.add_argument('--users', action="store", dest="users", type=str, required=False,
                          help="Comma separated list of users to be migrated.")
    migGroup.add_argument('--projects', action="store", dest="projects", type=str, required=False,
                          help="Comma separated list of project groups to be migrated.")
    migGroup.add_argument('--server', action="store_true", dest="wholeServer", required=False, default=False,
                          help="Requests that the all data on the server be migrated.")

    # Destination cluster info
    parser.add_argument('--dProject', action="store", dest="destProject", type=str, required=False,
                        help="The destination MVI project in the destination cluster.")
    parser.add_argument('--dCluster', action="store", dest="destCluster", type=str, required=False,
                        help="The destination cluster URL (for login purposes). Must be an OCP cluster.")
    parser.add_argument('--dToken', action="store", dest="destToken", type=str, required=False,
                        help="API Token for destination OCP cluster admin user.")

    # Source cluster info
    parser.add_argument('--sCluster', action="store", dest="srcCluster", type=str, required=False,
                        help="The destination cluster URL (for login purposes). Must be an OCP cluster.")
    parser.add_argument('--sToken', action="store", dest="srcToken", type=str, required=False,
                        help="API Token for destination OCP cluster admin user.")

    # Source access info when source is a standalone server.
    parser.add_argument("--sMongouser", action="store", dest="sMongouser", type=str, required=False,
                        help="Source mongoDb Admin user for a pre-8.0.0 installation.")
    parser.add_argument("--sMongopw", action="store", dest="sMongopw", type=str, required=False,
                        help="Source mongoDb Admin password for a pre-8.0.0 installation.")
    parser.add_argument("--sMongoservice", action="store", dest="sMongoService", type=str, required=False,
                        help="Service name for the mongoDb service in the cluster.")
    try:
        results = parser.parse_args()

        global mongoDbCreds
        mongoUserPresent = results.sMongouser is not None
        mongoPasswordPresent = results.sMongopw is not None

        if mongoUserPresent and mongoPasswordPresent:
            mongoDbCreds = {
                "userName": results.sMongouser,
                "password": results.sMongopw
            }
        elif mongoUserPresent or mongoPasswordPresent:
            print(
                "Only 1 of '--sMongouser' and '--sMongopw' was detected. If one is specified, both must be provided.",
                file=sys.stderr)
            results = None

        global clusterPresent
        if results is not None:
            clusterPresent = results.srcCluster is not None
            ocpTokenPresent = results.srcToken is not None

        if results.sMongouser or results.sMongopw:
            if clusterPresent:
                print(f"Error: You cannot specify a source cluster and mongoDB access credentials.")
                raise argparse.ArgumentTypeError
            elif not results.sMongouser or not results.sMongopw:
                # If either mongo user or mongo password are provided, both must be provided
                print(f"Error: Part of the mongo credentials is missing; user='{results.sMongouser}', pw='{results.sMongopw}'.")
                raise argparse.ArgumentTypeError

        if not results.status:
            if results.migType.lower() not in ["full", "all", "files"]:
                print(f"ERROR: Unknown migration type given in '--migType' ({results.migType})", file=sys.stderr)
                raise argparse.ArgumentTypeError

    except argparse.ArgumentTypeError as e:
        parser.print_help(sys.stderr)
        results = None

    return results


def setLoggingControls(log):
    """ Sets output control variables for logging out output content.
    Note that the command name is "hardcoded" in the log entry since multiple
    commands will be run in the container."""
    log_level = logging.INFO
    if log is not None:
        if log.lower() == "error":
            log_level = logging.ERROR
        elif log.lower().startswith("warn"):
            log_level = logging.WARNING
        elif log.lower() == "info":
            log_level = logging.INFO
        elif log.lower() == "debug":
            log_level = logging.DEBUG

    logging.basicConfig(format='%(asctime)s.%(msecs)d  migmgr  %(levelname)s:  %(message)s',
                        datefmt='%H:%M:%S', level=log_level)


if __name__ == "__main__":
    main()
