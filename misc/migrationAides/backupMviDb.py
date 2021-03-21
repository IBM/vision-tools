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
This script will backup a Mongod DB. It is designed to work with pre-8.0.0
version of MVI (pre-MAS) as well as post 8.0.0.  The difference is in the
way the connection is made to Mongo.

With pre-8.0.0, the script requires
  1. An SSH tunnel has been establish to the MVI mongoDB pod
     (and is still active when this script is run).
  2. The mongoDB login credentials are provided as parameters to this script.
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
import base64
import json
import os
import subprocess
import sys
import logging
import shutil

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
               "Tokens", "RegisteredApps", "ServiceInfo"]


def main():
    global args
    args = getInputs()

    if args is not None:
        setLoggingControls(args.logLevel)
        try:
            loginToCluster()
            connectToMongo()
            backupMongoCollections()
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


def backupMongoCollections():
    """ Creates a zip file containing all collections in the collection list that exist in the database."""

    zipFileName = f"{args.zipfile}.zip"
    backupFile = zipfile.ZipFile(zipFileName, mode="w", compression=zipfile.ZIP_DEFLATED)
    dbCollections = mviDatabase.list_collection_names()

    from datetime import datetime
    now = datetime.now()

    dirname = f"""{now.strftime("%Y%m%d%H%M%S")}-{os.getpid()}"""
    os.mkdir(dirname)

    logging.info(f"backing up {len(collections)} collections.")
    for collection in collections:
        if collection in dbCollections:
            backupCollection(backupFile, collection)
        else:
            logging.info(f"Skipping collection '{collection}'.")

    backupFile.close()
    shutil.rmtree(dirname)
    logging.info("Finished backup.")


def backupCollection(zipFile, collection):
    """ Extract collection from DB, write it to a file, and add file to the zip file."""

    logging.info(f"Backing up collection {collection}.")
    dbCollection = mviDatabase[collection]
    documents = dbCollection.find({})
    fileName = f"{collection}-{os.getpid()}"
    file = open(fileName, "w")
    file.write("[")
    i = 0
    for document in documents:
        if i > 0:
            file.write(",")
        file.write(json.dumps(document))
        i += 1
    file.write("]")
    file.close()

    zipFile.write(fileName)
    os.remove(fileName)


def getInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(description="Tool to backup an MVI MongoDB to a zip file.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
To backup a pre-8.0.0 MVI installation, you must specify '--mongouser'
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