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
import base64
import json
import subprocess
import sys
import logging

import pymongo
import zipfile
import re


class OcpException(Exception):
    pass


clusterPresent = False
mongoDbCreds = None
tunnelProcess = None
mongoClient = None
mviDatabase = None
args = {}

collections = ["BGTasks", "DLTasks", "DataSets", "DataSetCategories", "DataSetFiles", "DataSetFileLabels",
               "DataSetFileUserKeys", "DataSetTags", "DataSetActiontags", "DataSetFileActionLabels",
               "DataSetFileObjectLabels", "InferenceOps", "InferenceDetails", "ProjectGroups", "TrainedModels",
               "WebAPIs", "UserDNNs", "DnnScripts", "DeployableBinaries", "DockerHostPorts", "SysUsers",
               "Tokens", "RegisteredApps"]


def main():
    global args
    args = getInputs()

    if args is not None:
        setLoggingControls(args.logLevel)
        try:
            loginToCluster()
            connectToMongo()
            restoreMongoCollections()
            disconnectFromMongo()
            logoutOfCluster()
        except OcpException as oe:
            print(oe)
            exit(2)
    else:
        exit(1)


def loginToCluster():
    if mongoDbCreds is not None:
        return

    if args.cluster is not None:
        cmdArgs = ["oc", "login", args.cluster]
        if args.ocpToken is not None:
            cmdArgs.extend(["--token", args.ocpToken])
        else:
            cmdArgs.extend(["--username", args.ocpUser, "--password", args.ocpPasswd])
        logging.info(f"logging into cluster '{args.cluster}'")

        process = subprocess.run(cmdArgs, capture_output=True)
        if process.returncode != 0:
            logging.error(f"Failed to login to cluster {cmdArgs}")
            logging.error(f"output = {process.stderr}")
            raise OcpException(f"Failed to login to cluster {args.cluster}.")

        setOcpProject()


def setOcpProject():
    cmdArgs = ["oc", "project", args.project]
    logging.debug(f"Setting project to '{args.project}'")

    process = subprocess.run(cmdArgs, capture_output=True)
    if process.returncode != 0:
        logging.error(f"Failed to login to cluster {cmdArgs}")
        logging.error(f"output = {process.stderr}")
        raise OcpException(f"Failed to connect to project {args.project}")


def connectToMongo():
    logging.info("Connecting to mongo")

    user, passwd = getMongoDbCredentials()
    tunnelToMongo()
    loginToDb(user, passwd)


def getMongoDbCredentials():
    """ Returns mongoDB username and password based upon provided access info."""

    # If mongoDb credentials provided to the script, use those
    if mongoDbCreds is not None:
        return mongoDbCreds["userName"], mongoDbCreds["password"]

    cmdArgs = ["oc", "get", "secret", "vision-secrets", "-o", "json"]

    # otherwise get credentials from the cluster
    process = subprocess.run(cmdArgs, capture_output=True)
    if process.returncode == 0:
        jsonData = json.loads(process.stdout)
        userName = base64.b64decode(jsonData["data"]["mongodb-admin-username"]).decode("utf-8")
        password = base64.b64decode(jsonData["data"]["mongodb-admin-password"]).decode("utf-8")
        logging.debug(f"user={userName}, pw={password}")
    else:
        logging.error(f"Failed to get Mongo info -- {cmdArgs}")
        logging.error(f"output = {process.stderr}")
        raise OcpException(f"Could not get Mongo connection info.")

    return userName, password


def tunnelToMongo():
    """ Sets up a tunnel the mongoDB if backing up a post 8.0.0 database."""
    if mongoDbCreds:
        return

    pod = getMongoPod()
    if pod is None:
        raise OcpException("Could not find MongoDB Pod.")
    establishTunnel(pod, 27017, 27017)


def getMongoPod():
    """ Returns the pod name of the running mongoDB pod in an OCP cluster."""
    cmdArgs = ["oc", "get", "pods"]
    pod = None

    process = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
    for line in process.stdout:
        string = line.decode();
        logging.debug(string)
        if re.search("-mongodb-", string):
            pod = string.split(" ")[0]
            break
    process.wait()

    return pod


def establishTunnel(mongoPod, remotePort, localPort):
    cmdArgs = ["oc", "port-forward", "--address",  "0.0.0.0", mongoPod, f"{localPort}", f"{remotePort}"]
    logging.debug(f"Setting tunnel to '{mongoPod}'")

    global tunnelProcess
    tunnelProcess = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)


def loginToDb(user, passwd, database="DLAAS"):
    """ Logins into MongoDB and setups access to the DLAAS database."""
    logging.debug(f"logging into mongo db '{database}', as '{user}'")

    uri = f"mongodb://{user}:{passwd}@localhost:27017/?authSource={database}&authMechanism=SCRAM-SHA-1"
    global mongoClient
    mongoClient = pymongo.MongoClient(uri)
    logging.debug(f"dbconn={mongoClient}")
    global mviDatabase
    mviDatabase = mongoClient[database]

    return mongoClient


def disconnectFromMongo():
    mongoClient.close()


def logoutOfCluster():
    """ Logs out of the OCP cluster if the script performed a login to the cluster."""
    if mongoDbCreds is not None:
        return

    if tunnelProcess is not None:
        logging.debug("Terminating tunnel.")
        tunnelProcess.terminate()

    if args.cluster is not None:
        cmdArgs = ["oc", "logout"]
        logging.info(f"logging out of cluster '{args.cluster}'")

        process = subprocess.run(cmdArgs, capture_output=True)
        logging.debug(process.stdout)


def restoreMongoCollections():
    """ Takes files from the specified zip file and restores them into the same
    same collection in the target mongoDB."""

    zipFileName = f"{args.zipfilename}"
    zipArchive = zipfile.ZipFile(zipFileName, mode="r")
    zippedFiles = zipArchive.namelist()

    logging.info(f"Looking to restore up to {len(zippedFiles)} collections.")
    for zippedFileName in zippedFiles:
        if zippedFileName in collections:
            restoreCollection(zipArchive, zippedFileName, zippedFileName)
        else:
            logging.info(f"Skipping archive file '{zippedFileName}'.")

    zipArchive.close()
    logging.info("Finished restore.")


def restoreCollection(zipArchive, zippedFileName, collection):
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
        dbCollection = mviDatabase[collection]

        logging.info(f"Restoring {numberOfItems}...")
        while sliceStart < numberOfItems:
            logging.debug(f"working with slice {sliceStart}-{sliceEnd}.")
            # Only do a complete slice if we have saved at least 50 consecutive
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


def insertDocuments(dbCollection, collectionName, documents):
    """ Insert the documents in the document list one at a time so that DuplicateKeyError's
    can be caught, reported, and moved past. Count the number of consecutive successful saves
    and report that number back to the caller."""

    consecutiveInserts = 0
    logging.info("Falling back to individual document insertion to handle duplicate keys.")
    for doc in documents:
        try:
            dbCollection.insert(doc)
            consecutiveInserts += 1
        except pymongo.errors.DuplicateKeyError:
            logging.warning(f"""{collectionName}: duplicate Key f{doc["_id"]}""")
            consecutiveInserts = 0

    return consecutiveInserts


def getInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(description="Tool to restore an MVI MongoDB zip file backup.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
To restore into a pre-8.0.0 MVI installation, you must specify '--mongouser'
and '--mongopassword'; but the OCP cluster related parameters ('--cluster_url',
'--ocpuser', and '--ocppasswd, and '--ocptoken') should not be present.

For a post 8.0.0 MVI installation, either the OCP cluster related parameters
are required, OR you must be logged into the OCP cluster AND have set the 
project to the MVI project. The OCP user information must have enough 
authority to allow setting up a route to the mongoDB pod and to access the 
MongoDB credentials (typically an admin user).

If you are already logged into an OCP cluster, do not specify '--cluster_url', 
'--ocpuser', and '--ocppasswd'. However, if one these flags is specified, all 
must be specified. In this case, the script will login to the OCP cluster and 
then logout when done.

Note that '--ocptoken' can be used instead of '--ocpuser' and '--ocppasswd'. 
If '--ocptoken' is present, '--ocpuser' and '--ocppasswd' are ignored."
''')
    parser.add_argument('--project', action="store", dest="project", type=str, required=False,
                        help="Target MVI project in the cluster.")
    parser.add_argument("--mongouser", action="store", dest="mongouser", type=str, required=False,
                        help="MongoDb Admin user for a pre-8.0.0 installation.")
    parser.add_argument("--mongopassword", action="store", dest="mongopw", type=str, required=False,
                        help="MongoDb Admin password for a pre-8.0.0 installation.")
    parser.add_argument('--cluster_url', action="store", dest="cluster", type=str, required=False,
                        help="URL to OCP cluster.")
    parser.add_argument('--ocptoken', action="store", dest="ocpToken", type=str, required=False,
                        help="API Token for OCP cluster admin.")
    parser.add_argument('--ocpuser', action="store", dest="ocpUser", type=str, required=False,
                        help="Username for OCP cluster admin.")
    parser.add_argument('--ocppasswd', action="store", dest="ocpPasswd", type=str, required=False,
                        help="Password of OCP admin user.")
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
    if results is not None:
        clusterPresent = results.cluster is not None
        ocpTokenPresent = results.ocpToken is not None
        ocpUserPresent = results.ocpUser is not None
        ocpPasswdPresent = results.ocpPasswd is not None

        if clusterPresent or ocpUserPresent or ocpPasswdPresent or ocpTokenPresent:
            if mongoDbCreds is not None:
                print("Both mongo user credentials and OCP access information were detected. "
                      "You cannot specify both sets of info.", file=sys.stderr)
                results = None
            elif not (clusterPresent and ((ocpUserPresent and ocpPasswdPresent) or ocpTokenPresent)):
                print("If any of '--cluster_url', '--ocpuser', and '--ocppasswd' are specified, all must be specified.",
                      file=sys.stderr)
                print(f"cluster={clusterPresent}, user={ocpUserPresent}, pw={ocpPasswdPresent}, token={ocpTokenPresent}")
                parser.print_help(sys.stderr)
                results = None
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

    logging.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)s:  %(message)s',
                               datefmt='%H:%M:%S', level=log_level)


if __name__ == "__main__":
    main()