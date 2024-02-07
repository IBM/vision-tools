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
This script will backup a MongoDB. It is designed to work with pre-8.0.0
version of MVI (pre-MAS) as well as post 8.0.0.  The difference is in the
way the connection is made to Mongo.

With pre-8.0.0, the script requires
  1. The mongoDB login credentials are provided as parameters to this script.
     The presence (or absence) of these creds is used to determine whether
     the script is backing a pre-8.0.0 MVI MongoDB or not.

For post 8.0.0, the script requires
  1. OCP cluster information for the cluster in which MVI is running.
     This information can be provided via parameters to the script, or the
     user can login and set the correct project before running this script.
  In a post 8.0.0 action, this script will obtain the MongoDB login credentials
  from the OCP cluster. To accomplish this, the OCP user login MUST have enough
  authority for the script to examine MVI secret information.

The mongoDB backup data is stored in a zipfile with the name provided to the script.
"""
import argparse
import json
import os
import sys
import logging
import shutil

import vapi.accessors.MongoAccessor as MongoAccessor
import zipfile

clusterPresent = False
mongoDbCreds = None
args = {}

collections = MongoAccessor.collections


def main():
    global args
    args = getInputs()

    if args is not None:
        setLoggingControls(args.logLevel)
        try:
            with MongoAccessor.MongoAccessor(mongoDbCreds, mongoDbName=args.mongoDbName,
                                             mongoConnectionString=args.mongoConnectionString) as ma:
                backupMongoCollections(ma)
        except MongoAccessor.MviMongoException as me:
            print(me)
            exit(2)
    else:
        exit(1)


def backupMongoCollections(mongo):
    """ Creates a zip file containing all collections in the collection list that exist in the database."""

    zipFileName = f"{args.zipfile}.zip"
    backupFile = zipfile.ZipFile(zipFileName, mode="w", compression=zipfile.ZIP_DEFLATED)
    dbCollections = mongo.getMviDatabase().list_collection_names()
    logging.debug(f"DB collections = {dbCollections}")

    from datetime import datetime
    now = datetime.now()

    dirname = f"""{now.strftime("%Y%m%d%H%M%S")}-{os.getpid()}"""
    os.mkdir(dirname)

    logging.info(f"backing up {len(collections)} collections.")
    for collection in collections:
        if collection in dbCollections:
            backupCollection(mongo, backupFile, collection)
        else:
            logging.info(f"Skipping collection '{collection}'.")

    backupFile.close()
    shutil.rmtree(dirname)
    logging.info("Finished backup.")


def backupCollection(mongo, zipFile, collection):
    """ Extract collection from DB, write it to a file, and add file to the zip file."""

    dbCollection = mongo.getMviDatabase()[collection]
    logging.info(f"Backing up {dbCollection.count_documents({})} documents from collection {collection}.")

    documents = dbCollection.find({})
    fileName = f"{collection}"

    with open(fileName, "w") as file:
        file.write("[")
        i = 0
        for document in documents:
            if i > 0:
                file.write(",")
                if i % 1000 == 0:
                    logging.debug(f"{i}")
            file.write(json.dumps(document))
            i += 1
        file.write("]")

    zipFile.write(fileName)
    os.remove(fileName)


#TODO: overhaul the parameters for external mongo DB
#TODO: currently need unecessary params for mongouser and mongopassword to get through code correctly.
#TODO: must have mongoconnectionstring and mongodbname
def getInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(description="Tool to backup an MVI MongoDB to a zip file.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
    This script currently only works on MVI 8.8.x and up installations.
                                     
    You must supply '--mongouser', '--mongopassword', '--mongoconnectionstring', and '--mongodbname' flags.
    All other parameters are no longer used, but have not been cleaned up yet.
    
    The '--mongouser', '--mongopassword' can be obtained from the "*-mongocfg-system-binding-3faa6f5e" secret
    in the MVI project to be backed up.
    
    If the mongo instance is not publicly accesssible, tunnels must be setup to reach each of the replica
    hosts.
''')
    parser.add_argument("--mongouser", action="store", dest="mongouser", type=str, required=True,
                        help="MongoDb Admin user for a pre-8.0.0 installation.")
    parser.add_argument("--mongopassword", action="store", dest="mongopw", type=str, required=True,
                        help="MongoDb Admin password for a pre-8.0.0 installation.")
    parser.add_argument("--mongoconnectionstring", action="store", dest="mongoConnectionString",
                        type=str, required=True,
                        help="Name of the MongoDB containing the MVI documents to be backed-up.")
    parser.add_argument('--mongodbname', action="store", dest="mongoDbName", type=str, required=True,
                        help="Name of the mongo DB containing the MVI data to be backed up.")
    parser.add_argument('--workDir', action="store", dest="workDir", type=str, required=False, default=None,
                        help="directory to use for work files.")
    parser.add_argument('--log', action="store", dest="logLevel", type=str, required=False, default="info",
                        help='Specify logging level (default is "info")')

    parser.add_argument('zipfile', metavar='zipFile', type=str,
                        help='Basename of the zip file to contain the DB backup.')
    try:
        results = parser.parse_args()

    except argparse.ArgumentTypeError as e:
        parser.print_help(sys.stderr)
        results = None

    global mongoDbCreds
    mongoUserPresent = results.mongouser is not None
    mongoPasswordPresent = results.mongopw is not None

    if mongoUserPresent and mongoPasswordPresent:
        mongoDbCreds = {
            "userName": results.mongouser,
            "password": results.mongopw
        }
    elif mongoUserPresent or mongoPasswordPresent:
        print("Only 1 of '--mongouser' and '--mongopassword' was detected. If one is specified, both must be provided.",
              file=sys.stderr)
        results = None

    global clusterPresent
    clusterPresent = False

    return results


def setLoggingControls(log):
    """ Sets output control variables for logging out output content.

    Output controls are set by parameter or by ENV variable."""
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

    logging.basicConfig(format='%(asctime)s.%(msecs)d  backupMviDb  %(levelname)s:  %(message)s',
                               datefmt='%H:%M:%S', level=log_level)


if __name__ == "__main__":
    main()