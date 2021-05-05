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
"""
import argparse
import os
import os.path
import subprocess
import sys
import logging
import time
from inspect import getsourcefile


class Status:
    STARTING = "starting"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    FILES_RUNNING = "files_running"
    FILES_COMPLETE = "files_complete"
    FILES_FAILED = "files_failed"
    DB_RUNNING = "db_running"
    DB_BACKUP_COMPLETE = "db_backup_complete"
    DB_BACKUP_FAILED = "db_backup_failed"
    DB_RESTORE_COMPLETE = "db_restore_complete"
    DB_RESTORE_FAILED = "db_restore_failed"
    DB_COMPLETE = "db_complete"
    DB_FAILED = "db_failed"


SCRIPT_DIR = os.path.dirname(getsourcefile(lambda: 0))
MIGRATE_MVI_FILES_CMD = f"{SCRIPT_DIR}/migrateMviFiles.py"
BACKUP_MVI_DB_CMD = f"{SCRIPT_DIR}/backupMviDb.py"
RESTORE_MVI_DB_CMD = f"{SCRIPT_DIR}/restoreMviDb.py"

args = None
mountPoint = os.getenv("MIGMGR_MOUNTPOINT", "/opt/mvi/data")
workDir = None
statusDir = None


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


def showStatus():
    """ Shows the statuses that have been set."""
    logging.debug("Showing current status...")
    os.system(f"ls -lrt {statusDir}")


def doMigration():
    """ Manages the migration steps based on command input parameters."""
    if args.restart:
        clearAllStatus()

    for migration in args.migrations:
        migration()


def doFileMigration():
    """ Performs the file migration if it has not already been done."""
    logging.debug("attempting to start File Migration.")
    if not isStatusSet(Status.FILES_COMPLETE) and not isStatusSet(Status.FILES_FAILED):
        logging.info(f"Preparing for File Migration ({MIGRATE_MVI_FILES_CMD})")
        fileMigrateCmd = [MIGRATE_MVI_FILES_CMD,
                          "--log", args.logLevel,
                          "--cluster_url", args.destCluster,
                          "--project", args.destProject,
                          "--ocptoken", args.destToken]

        logging.info(f"Starting file migration ({fileMigrateCmd})")
        setStatus(Status.FILES_RUNNING)
        filesResult = subprocess.run(fileMigrateCmd)
        logging.debug(f"file migration returned... {filesResult}.")

        if filesResult.returncode == 0:
            logging.info("File migration completed.")
            setStatus(Status.FILES_COMPLETE)
        else:
            logging.info(f"File migration failed ({filesResult.returncode})")
            setStatus(Status.FILES_FAILED)
    else:
        logging.info("File migration has already finished")


def doDbMigration():
    """ performs the DB migration if not already done.
    DB Migration is 2 steps, backup to a zip file and then restore into the destination cluster."""
    logging.debug("attempting to start DB migration.")

    if not isStatusSet(Status.DB_BACKUP_COMPLETE) and not isStatusSet(Status.DB_BACKUP_FAILED):
        doDbBackup()
    else:
        logging.info("Db Backup already done.")

    if isStatusSet(Status.DB_BACKUP_COMPLETE) \
            and not isStatusSet(Status.DB_RESTORE_COMPLETE) \
            and not isStatusSet(Status.DB_RESTORE_FAILED):
        doDbRestore()
    else:
        logging.info("DB Restore already done or DB Backup failed.")


def doDbBackup():
    """ performs the DB backup step if it has not already been done."""
    logging.debug("preparing for DB backup.")
    setStatus(Status.RUNNING)
    setStatus(Status.DB_RUNNING)

    # For now, create the backup command knowing that we are only working with 1.3.0.
    # If we expand migration support for ICP and OCP source clusters, this will have to change.
    backupCmd = [BACKUP_MVI_DB_CMD, "--log", args.logLevel, "--mongoservice", args.sMongoService]
    if args.sMongouser:
        backupCmd.extend(["--mongouser", args.sMongouser, "--mongopassword", args.sMongopw])
    backupCmd.append(os.path.join(workDir, "db_backup"))

    logging.info(f"Starting DB Backup ({backupCmd})")
    bkupResult = subprocess.run(backupCmd)
    logging.debug(f"db backup returned... {bkupResult}.")

    if bkupResult.returncode == 0:
        logging.info("DB Backup complete.")
        setStatus(Status.DB_BACKUP_COMPLETE)
    else:
        logging.info(f"DB Backup failed ({bkupResult.returncode})")
        setStatus(Status.DB_BACKUP_FAILED)
        setStatus(Status.DB_FAILED)


def doDbRestore():
    """ performs the DB restore step if the DB backup completed succesfully and the restore
    has not already been done."""
    restoreCmd = [RESTORE_MVI_DB_CMD,
                  "--log", args.logLevel,
                  "--project", args.destProject,
                  "--cluster_url", args.destCluster,
                  "--ocptoken", args.destToken,
                  os.path.join(workDir, "db_backup.zip")]

    logging.info(f"Starting DB Restore ({restoreCmd})")
    restoreResult = subprocess.run(restoreCmd)
    logging.debug(f"db restore returned... {restoreResult}.")

    if restoreResult.returncode == 0:
        logging.info("DB Restore complete.")
        setStatus(Status.DB_RESTORE_COMPLETE)
        logging.info("DB migration complete.")
        setStatus(Status.DB_COMPLETE)
    else:
        logging.info(f"DB Restore failed ({restoreResult.returncode})")
        setStatus(Status.DB_RESTORE_FAILED)
        setStatus(Status.DB_BACKUP_FAILED)


def setStatus(status):
    """ Sets the indicated status."""
    fpath = os.path.join(statusDir, status)
    logging.debug(f"Setting status '{status}' ({fpath}")
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

    parser.add_argument('--status', action="store_true", dest="status", required=False, default=False,
                        help="Requests migration status be returned.")

    parser.add_argument('--migType', action="store", dest="migType", type=str, required=False,
                        help="Type of migration to perform. Value must be 1 of 'all', 'files', or 'db'.")
    parser.add_argument('--restart', action="store_true", dest="restart", required=False, default=False,
                        help="Causes migration to start from the beginning again (clears all progress markers).")
    parser.add_argument('--dProject', action="store", dest="destProject", type=str, required=False,
                        help="The destination MVI project in the destination cluster.")
    parser.add_argument('--dCluster', action="store", dest="destCluster", type=str, required=False,
                        help="The destination cluster URL (for login purposes). Must be an OCP cluster.")
    parser.add_argument('--dToken', action="store", dest="destToken", type=str, required=False,
                        help="API Token for destination OCP cluster admin user.")
    parser.add_argument("--sMongouser", action="store", dest="sMongouser", type=str, required=False,
                        help="Source mongoDb Admin user for a pre-8.0.0 installation.")
    parser.add_argument("--sMongopw", action="store", dest="sMongopw", type=str, required=False,
                        help="Source mongoDb Admin password for a pre-8.0.0 installation.")
    parser.add_argument("--sMongoservice", action="store", dest="sMongoService", type=str, required=False,
                        help="Service name for the mongoDb service in the cluster.")
    try:
        results = parser.parse_args()

        if results.sMongouser or results.sMongopw:
            # If either mongo user or mongo password are provided, both must be provided
            if not results.sMongouser or not results.sMongopw:
                print(f"Error: Part of the mongo credentials is missing; user='{results.sMongouser}', pw='{results.sMongopw}'.")
                raise argparse.ArgumentTypeError

        if not results.status:
            if not results.migType:
                print(f"One of '--status' or '--migType' must be set.")
                raise argparse.ArgumentTypeError

            if results.migType.lower() == "full" or results.migType.lower() == "all":
                results.migrations = [doFileMigration, doDbMigration]
            elif results.migType.lower() == "files":
                results.migrations = [doFileMigration]
            elif results.migType.lower() == "db":
                results.migrations = [doDbMigration]
            else:
                print(f"ERROR: '--status' not set and '--migType' is not known ({results.migType})", file=sys.stderr)
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
