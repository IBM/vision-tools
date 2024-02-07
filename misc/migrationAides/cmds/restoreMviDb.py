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
This script will restore a backup zip file into a running Mongo DB. It is designed
to restore into post 8.0.0 MVI environments only though there is nothing that prevents/blocks
restoring into a pre-8.0.0 environment.

This zip file is expected to have files with the name of the collection that is
backed up there. Only expected collections (those in the `collections` list are restored.
"""
import argparse
import json
import sys
import logging
import pymongo

import vapi.accessors.MongoAccessor as MongoAccessor
import zipfile

clusterPresent = False
mongoDbCreds = None
args = {}

collections = MongoAccessor.collections
fixUpMap = {}


def main():
    global args
    args = getInputs()

    # The fixUpMap must be initialized in code so that the reference functions have been seen by the parser
    global fixUpMap
    fixUpMap = {"TrainedModels": fixUpTrainedModel}

    if args is not None:
        setLoggingControls(args.logLevel)
        try:
            with MongoAccessor.MongoAccessor(mongoDbCreds, mongoDbName=args.mongoDbName,
                                             mongoConnectionString=args.mongoConnectionString) as ma:
                restoreMongoCollections(ma)
        except MongoAccessor.MviMongoException as me:
            print(me)
            exit(2)
    else:
        exit(1)


def restoreMongoCollections(mongo):
    """ Takes files from the specified zip file and restores them into the same
    same collection in the target mongoDB."""

    zipFileName = f"{args.zipfilename}"
    zipArchive = zipfile.ZipFile(zipFileName, mode="r")
    zippedFiles = zipArchive.namelist()

    logging.info(f"Looking to restore up to {len(zippedFiles)} collections.")
    for zippedFileName in zippedFiles:
        if zippedFileName in collections:
            restoreCollection(mongo, zipArchive, zippedFileName, zippedFileName)
        else:
            logging.info(f"Skipping archive file '{zippedFileName}'.")

    zipArchive.close()
    logging.info("Finished restore.")


def restoreCollection(mongo, zipArchive, zippedFileName, collection):
    """ Restore the indicated zipped file into the indicated collection."""

    logging.info(f"Restoring collection '{collection}' from {zippedFileName}.")

    with zipArchive.open(zippedFileName, 'r') as myfile:
        jsonData = json.loads(myfile.read())

    if jsonData:
        # We process the zipped collection in slices because the whole thing
        # can be too big for mongo to handle in 1 call. We use 1000 item slices.
        sliceSize = 1000
        sliceStart = 0
        sliceEnd = sliceSize
        numberOfItems = len(jsonData)
        inserted = sliceSize
        dbCollection = mongo.getMviDatabase()[collection]
        fixUpNeeded = fixUpRequired(collection)

        logging.info(f"Restoring {numberOfItems}...")
        while sliceStart < numberOfItems:
            logging.info(f"working with slice {sliceStart}-{sliceEnd}.")

            if fixUpNeeded:
                # Collections requiring "fix ups" must load documents individually.
                inserted = insertDocuments(dbCollection, collection, jsonData[sliceStart:sliceEnd])
            else:
                # Only bulk load a complete slice if we have saved at least 50 consecutive
                # documents without a failure.
                if inserted >= 50:
                    try:
                        dbCollection.insert_many(jsonData[sliceStart:sliceEnd])
                        inserted = sliceSize
                    except pymongo.errors.BulkWriteError:
                        # BulkWriteError usually indicates DuplicateKeyError, in which case MongoDB
                        # stops processing. So fallback to inserting individual documents where we
                        # can catch duplicate keys and continue through the slice.
                        inserted = insertDocuments(dbCollection, collection, jsonData[sliceStart:sliceEnd])
                else:
                    inserted = insertDocuments(dbCollection, collection, jsonData[sliceStart:sliceEnd])
            sliceStart = sliceEnd
            sliceEnd += sliceSize


def fixUpRequired(collectionName):
    """Determines if the indicated collection requires migration fix ups."""
    return collectionName in fixUpMap.keys()


def insertDocuments(dbCollection, collectionName, documents):
    """ Insert the documents in the document list one at a time so that DuplicateKeyError's
    can be caught, reported, and moved past. Count the number of consecutive successful saves
    and report that number back to the caller."""

    fixUpNeeded = fixUpRequired(collectionName)
    consecutiveInserts = 0
    logging.info("Restoring individual documents, which will handle duplicate keys and document fix ups.")
    for doc in documents:
        try:
            if fixUpNeeded:
                fixUpMap[collectionName](doc)
            dbCollection.insert(doc)
            consecutiveInserts += 1
        except pymongo.errors.DuplicateKeyError:
            logging.warning(f"""{collectionName}: duplicate Key f{doc["_id"]}""")
            consecutiveInserts = 0

    return consecutiveInserts


def fixUpTrainedModel(doc):
    """Fixes up a trained model document.
    The only fix required presently is for the 'thumbnail_path' attribute."""

    try:
        if doc["thumbnail_path"].startswith("uploads/"):
            doc["thumbnail_path"] = doc["thumbnail_path"].replace("uploads/", "/opt/powerai-vision/data/", 1)
            logging.debug(f"Fixed trained-model thumbnail_path -- f{doc['thumbnail_path']}")
    except KeyError as ke:
        logging.info(f"fixUpTrainedModel: Could not find 'thumbnail_path', in trained model '{doc['_id']}'.")


def getInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(description="Tool to restore an MVI MongoDB zip file backup.",
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
    parser.add_argument('--log', action="store", dest="logLevel", type=str, required=False, default="info",
                        help='Specify logging level (default is "info")')

    parser.add_argument('zipfilename', metavar='zipFile', type=str,
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
            "user": results.mongouser,
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
    """ Sets output control variables for logging out output content."""
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

    logging.basicConfig(format='%(asctime)s.%(msecs)d  restoreMviDb  %(levelname)s:  %(message)s',
                               datefmt='%H:%M:%S', level=log_level)


if __name__ == "__main__":
    main()