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
from glob import glob
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
    FILE_MIGRATION_RUNNING = "file_migration_running"
    FILE_MIGRATION_COMPLETE = "file_migration_complete"
    FILE_MIGRATION_FAILED = "file_migration_failed"
    ARTIFACT_COLLECTION_RUNNING = "artifact_collection_running"
    ARTIFACT_COLLECTION_COMPLETE = "artifact_collection_complete"
    ARTIFACT_COLLECTION_FAILED = "artifact_collection_failed"
    DB_MIGRATION_RUNNING = "db_migration_running"
    DB_MIGRATION_COMPLETE = "db_migration_complete"
    DB_MIGRATION_FAILED = "db_migration_failed"

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

topLevelCollections = [
    "BGTasks",
    "DLTasks",
    "TrainedModels",
    "DnnScripts",
    "DataSets",
    "ProjectGroups",
    "UserDNNs"
]

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
        migrateProjectGroups(args.projects.split(","))

    # TODO: add logic to check for success/failure and report status accordingly
    setStatus(Status.COMPLETE)


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
    """Collects and migrates artifacts associated with the given user."""

    with MongoAccessor.MongoAccessor(mongoDbCreds, mongoService=args.sMongoService) as ma:
        for user in userList:
            setStatus(Status.subStatus(Status.ARTIFACT_COLLECTION_RUNNING, user))
            flist, dbFile = collectUserArtifacts(ma, user)
            if dbFile is not None:
                setStatus(Status.subStatus(Status.ARTIFACT_COLLECTION_COMPLETE, user))
                migrateArtifacts(flist, dbFile, user)
            else:
                setStatus(Status.subStatus(Status.ARTIFACT_COLLECTION_FAILED, user))
    return flist, dbFile


def collectUserArtifacts(mongo, user):
    """ Collect DB artifacts associated with the indicated user and generates the file paths to migrate."""

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

    pathList, success = collectGroupArtifacts(mongo, backupFile, collectionDir, topLevelCollections, {"owner": user})

    backupFile.close()

    return [os.path.join(mountPoint, user)], zipFileName if success else None


def collectGroupArtifacts(mongo, backupFile, collectionDir, collectionList, query):
    """Collects DB artifacts based upon the given query."""

    dbCollections = mongo.getMviDatabase().list_collection_names()

    logging.info(f"Collecting DB docs for top level user collections.")
    pathList=[]
    for collection in collectionList:
        # If Collection is not in the DB, there is nothing the backup.
        if collection in dbCollections:
            pathList.extend(collectDocumentTreesAndFilePaths(mongo, backupFile, collectionDir, collection, query))
        else:
            logging.info(f"Skipping collection '{collection}'.")

    backupSecondLevelCollectionFiles(backupFile, collectionDir)

    import shutil
    shutil.rmtree(collectionDir)

    return pathList, True


def migrateProjectGroups(pgList):
    """Performs collection and migration of artifacts for each project group in the list."""
    with MongoAccessor.MongoAccessor(mongoDbCreds, mongoService=args.sMongoService) as ma:
        for pgid in pgList:
            setStatus(Status.subStatus(Status.ARTIFACT_COLLECTION_RUNNING, pgid))
            flist, dbFile = collectProjectGroupArtifacts(ma, pgid)
            if dbFile is not None:
                setStatus(Status.subStatus(Status.ARTIFACT_COLLECTION_COMPLETE, pgid))
                migrateArtifacts(flist, dbFile, pgid)
            else:
                setStatus(Status.subStatus(Status.ARTIFACT_COLLECTION_FAILED, pgid))
    return flist, dbFile


def collectDocumentTreesAndFilePaths(mongo, zipFile, wkDir, collection, query={}):
    """Collect document trees for the given collection and report file paths if relevant for the collection.
    Only the 'Datasets' collection has document trees. All others are single level document
    collection. Path names are reported for 'Datasets', 'TrainedModels', and 'DnnScripts'
    collections as this information is required in some migrations (e.g. project group migrations)."""

    dbCollection = mongo.getMviDatabase()[collection]

    pathList = []

    count = dbCollection.count_documents(query)
    if count > 0:
        documents = dbCollection.find(query)
        logging.info(f"Backing up documents from collection '{collection}' matching query '{query}'.")
        fileName = os.path.join(wkDir, f"{collection}")

        i = 0
        with open(fileName, "w") as file:
            file.write("[")
            for document in documents:
                if i > 0:
                    file.write(",")
                    if i % 1000 == 0:
                        logging.debug(f"{i}")
                file.write(json.dumps(document, indent=2))
                if collection == "DataSets":
                    pathList.append(f"{mountPoint}/{document['owner']}/datasets/{document['_id']}")
                    collectDatasetArtifacts(mongo, wkDir, document)
                elif collection == "TrainedModels":
                    pathList.extend(glob(f"{mountPoint}/{document['owner']}/trained-models/{document['_id']}*"))
                    pathList.extend(glob(f"{mountPoint}/{document['owner']}/trained-models/thumbnails/{document['_id']}*"))
                elif collection == "DnnScripts":
                    pathList.append(f"{mountPoint}/{document['owner']}/dnn-scripts/{document['_id']}.zip")
                i += 1
            file.write("]")

        logging.info(f"Backed up {i} documents from '{collection}' (query={query}).")
        zipFile.write(fileName, collection)
        os.remove(fileName)
    else:
        logging.info(f"No documents to migrate in '{collection}'.")

    return pathList


def collectDatasetArtifacts(mongo, wkDir, dataset):
    logging.info(f"""Saving DatasetArtifacts for dataset id '{dataset["_id"]}'""")

    dbCollections = mongo.getMviDatabase().list_collection_names()

    for collection in secondLevelCollections:
        if collection in dbCollections:
            saveDatasetRelatedCollectionsToFile(mongo, wkDir, collection, {"dataset_id": dataset["_id"]})
        else:
            logging.info(f"Skipping collection '{collection}'.")


def saveDatasetRelatedCollectionsToFile(mongo, wkDir, collection, query):
    """Appends the documents from the given collection that match the query into collection file
     for later backup to the zip file"""
    logging.debug(f"""Saving collection '{collection}' using query '{query}'.""")

    dbCollection = mongo.getMviDatabase()[collection]
    count = dbCollection.count_documents(query)
    i = 0
    if count > 0:
        documents = dbCollection.find(query)
        fileName = os.path.join(wkDir, f"{collection}")
        prefix = "," if os.path.exists(fileName) else "["

        with open(fileName, "a") as file:
            i = 0
            for document in documents:

                if i > 0 and i % 1000 == 0:
                    logging.debug(f"{i}")

                file.write(prefix)
                file.write(json.dumps(document, indent=2))
                prefix = ","

                i += 1
        logging.info(f"Saved {i} documents matching query '{query}' from collection '{collection}' ({count}).")
    else:
        logging.info(f"No documents to migrate for '{collection}' matching '{query}'")


def backupSecondLevelCollectionFiles(zipFile, wkdir):
    """Backs up any second level collection files that exist into the zip file."""

    for collection in secondLevelCollections:
        fileName = os.path.join(wkdir, collection)
        if os.path.exists(fileName):
            logging.debug(f"Closing list for secondary collection '{collection}' ({fileName}).")
            # close the json list in the save file before backing it up in the zipfile.
            with open(fileName, "a") as file:
                file.write("]")
            zipFile.write(fileName, os.path.basename(fileName))
            os.remove(fileName)


def collectProjectGroupArtifacts(mongo, pgid):
    """Collects all artifacts associated with the given project group.
     Returns list of files to migrate and the zipfile containing the DB documents to migrate."""
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

    pg = saveProjectGroup(mongo, collectionDir, backupFile, pgid)
    pathList = []
    if pg:
        collectionList = topLevelCollections
        collectionList.remove("ProjectGroups")
        pathList, success = collectGroupArtifacts(mongo, backupFile, collectionDir, collectionList,
                                                  {"project_group_id": pgid})
        backupFile.close()
        if not success:
            logging.warning(f"Artifact collection failed for project group '{pgid}'.")
            os.remove(zipFileName)
            zipFileName = None
    else:
        logging.warning(f"Warning -- could not find project group with id '{pgid}'; nothing to migrate.")
        backupFile.close()          # must close before removing the zip
        os.remove(zipFileName)      # Must remove the zipfile so that it cannot be migrated
        zipFileName = None

    return pathList, zipFileName


def saveProjectGroup(mongo, wkDir, zipfile, pgid):
    """Collects and saves the project group document to the zipfile.
    Returns the project group document if it exists."""
    collection = "ProjectGroups"
    pgCollection = mongo.getMviDatabase()[collection]
    query = {"_id": pgid}
    count = pgCollection.count_documents(query)
    document = None
    if count > 0:
        fileName = os.path.join(wkDir, "ProjectGroups")

        documents = pgCollection.find(query)
        with open(fileName, "w") as file:
            file.write("[")
            i = 0
            document = documents[0]
            file.write(json.dumps(document, indent=2))
            file.write("]")

        zipfile.write(fileName, collection)
        os.remove(fileName)
    else:
        logging.info(f"No project group found for id '{pgid}'")

    return document


def migrateArtifacts(flist, dbfile, item):
    """Migrates both files and DB documents."""
    logging.info(f"Starting to migrate artifacts for '{item}'. dbfile = '{dbfile}'. Files = '{flist}'.")

    doFileMigration(flist, item)
    doDbMigration(dbfile, item)


def doFileMigration(flist, item):
    """ Performs the file migration if it has not already been done."""

    migrated = False
    logging.debug(f"attempting to start File Migration ({item}).")
    runningStatus = Status.subStatus(Status.FILE_MIGRATION_RUNNING, item)
    completeStatus = Status.subStatus(Status.FILE_MIGRATION_COMPLETE, item)
    failedStatus = Status.subStatus(Status.FILE_MIGRATION_FAILED, item)

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

    logging.debug(f"Starting DB migration for '{item}'.")

    setStatus(Status.subStatus(Status.DB_MIGRATION_RUNNING, item))
    rc = doDbRestore(fileName)
    if rc == 0:
        setStatus(Status.subStatus(Status.DB_MIGRATION_COMPLETE, item))
    else:
        setStatus(Status.subStatus(Status.DB_MIGRATION_FAILED, item))


def doDbRestore(filePath):
    """ performs the DB restore step if the DB backup completed succesfully and the restore
    has not already been done."""
    restoreCmd = [RESTORE_MVI_DB_CMD,
                  "--log", args.logLevel,
                  "--project", args.destProject,
                  "--cluster_url", args.destCluster,
                  "--ocptoken", args.destToken,
                  os.path.join(filePath)]

    logging.info(f"Starting DB Restore command. ({restoreCmd})")
    restoreResult = subprocess.run(restoreCmd)
    logging.debug(f"db restore returned... {restoreResult}.")

    if restoreResult.returncode == 0:
        logging.info("DB Restore complete.")
    else:
        logging.warning(f"DB Restore failed ({restoreResult.returncode})")

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
