#!/usr/bin/env python3
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
import argparse
import json
import os
import subprocess
import sys
import logging as logger
import re


args = None
clusterCfg = None


def main():
    setupEnvironment()

    if args.status:
        reportStatus()
    elif args.migrate:
        startMigration()
    elif args.cleanup or args.abort:
        cleanupMigration()
    elif args.createDeployment:
        createDeployment()


def reportStatus():
    logger.debug(f"Reporting status on migration '{args.name}'")
    srcCluster = StandaloneSource(args.name, clusterCfg.source)
    srcCluster.getStatus()


def startMigration():
    ensureVersionCompatibility()
    srcCluster = StandaloneSource(args.name, clusterCfg.source)
    srcCluster.createDeployment(args, clusterCfg)
    srcCluster.startMigration()


def ensureVersionCompatibility():
    """Ensure that the MVI servers are different and that the migration is not migrating to a lower version.
    This routine expect "semver" strings like "V.R.F-extra", and does a numeric comparison of the "V.R.F" parts."""

    if "mviUrl" not in clusterCfg.source or "mviUrl" not in clusterCfg.destination:
        logger.warning("Cannot validate MVI versions because at least one on 'mviUrl' attribute "\
                       "is missing from the cluster config file.")
        return

    import requests
    # Disable warning messages about SSL certs
    requests.packages.urllib3.disable_warnings()

    if clusterCfg.source["mviUrl"] == clusterCfg.destination["mviUrl"]:
        print(f"Error: Source and destination MVI URL cannot be the same. Check '{args.configFile}'.",
              file=sys.stderr)

    pattern = r"^\s*(\d+)\.(\d+)\.(\d+)"
    if clusterCfg.source['mviUrl'].startswith("http"):
        sourceUrl = clusterCfg.source['mviUrl']
    else:
        sourceUrl = f"""https://{clusterCfg.source['mviUrl']}"""

    sourceVersionInfo = requests.get(url=f"{sourceUrl}/api/version-info", verify=False).json()
    sourceVersionStr = sourceVersionInfo["version"]
    strPieces = re.match(pattern, sourceVersionStr).groups()
    sourceVersion = (int(strPieces[0]), int(strPieces[1]), int(strPieces[2]))
    logger.info(f"Source MVI version = '{sourceVersionStr}' ({sourceVersion}).")

    if clusterCfg.destination['mviUrl'].startswith("http"):
        destinationUrl = clusterCfg.destination['mviUrl']
    else:
        destinationUrl = f"""https://{clusterCfg.destination['mviUrl']}"""

    destinationVersionInfo = requests.get(url=f"{destinationUrl}/api/version-info", verify=False).json()
    destinationVersionStr = destinationVersionInfo["version"]
    strPieces = re.match(pattern, destinationVersionStr).groups()
    destinationVersion = (int(strPieces[0]), int(strPieces[1]), int(strPieces[2]))
    logger.info(f"Destination MVI Version = '{destinationVersionStr}' ({destinationVersion}).")

    if destinationVersion < sourceVersion:
        print(f"Error: You cannot migrate to a down level server. "
              f"Source version = '{sourceVersionStr}' ({sourceVersion}); "
              f"Destination Version = '{destinationVersionStr}' ({destinationVersion}",
              file=sys.stderr)
        exit(3)


def cleanupMigration():
    logger.debug(f"Cleaning up migration '{args.name}'.")
    srcCluster = StandaloneSource(args.name, clusterCfg.source)
    srcCluster.cleanupMigration()


def createDeployment():
    ensureVersionCompatibility()
    srcCluster = StandaloneSource(args.name, clusterCfg.source)
    srcCluster.createDeployment(args, clusterCfg)


def setupEnvironment():
    """Collect input information and setup the working environment."""

    global args
    args = getInputs()
    if args is not None:
        setLoggingControls(args.logLevel)
        setupClusterConfig()
    else:
        exit(1)


def getInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(description="Tool to start, monitor, and cleanup an MVI migration.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
One of '--status', '--migrate', '--cleanup' or '--createDeployment' must be specified to indicate the desired action.
When specifying '--migrate' or '--createDeployment', then one of '--users', '--projects', or '--server' is
required to indicate the scope (or content) of the migration.
Note that '--createDeployment' can be used to create the deployment file so that it can be manually edited
and then manually applied to start the migration. This capability can be used for unforeseen special situations.
''')

    parser.add_argument("--name", action="store", dest="name", type=str, required=True,
                        help="Unique name for a single migration. It is used to separate operations and track status.")
    parser.add_argument('--config', action="store", dest="configFile", type=str, required=False,
                        help="Path to the cluster config file. If not specified on command line, "
                             "the MVI_MIG_CONFIG environment variable will be checked.")
    parser.add_argument('--log', action="store", dest="logLevel", type=str, required=False, default="warn",
                        help='Specify logging level; one of "error", "warn", "info", or "debug" (default is "warn")')

    actionGroup = parser.add_mutually_exclusive_group(required=True)
    actionGroup.add_argument('--status', action="store_true", dest="status", required=False, default=False,
                             help="Requests status of the named migration be returned.")
    actionGroup.add_argument('--migrate', action="store_true", dest="migrate", required=False, default=False,
                             help="Initiates a new migration with the given name.")
    actionGroup.add_argument('--abort', action="store_true", dest="abort", required=False, default=False,
                             help="Aborts the named migration.")
    actionGroup.add_argument('--cleanup', action="store_true", dest="cleanup", required=False, default=False,
                             help="Cleans up the completed named migration.")
    actionGroup.add_argument('--createDeployment', action="store_true", dest="createDeployment",
                             required=False, default=False,
                             help="Creates and saves the deployment definition to a file, but do not run the migration.")

    migGroup = parser.add_mutually_exclusive_group()
    migGroup.add_argument('--users', action="store", dest="users", type=str, required=False,
                          help="Comma separated list of users to be migrated.")
    migGroup.add_argument('--projects', action="store", dest="projects", type=str, required=False,
                          help="Comma separated list of project groups to be migrated.")
    migGroup.add_argument('--server', action="store_true", dest="wholeServer", required=False, default=False,
                          help="Requests that the all data on the server be migrated.")

    parser.add_argument('--filesonly', action="store_true", dest="filesOnly", required=False, default=False,
                        help="Indicates that only files are to be migrated (only relevant with '--migrate').")

    try:
        results = parser.parse_args()
        msg = None

        if results.migrate or results.createDeployment:
            # ensure scope of migration was specified.
            if not results.users and not results.projects and not results.wholeServer:
                msg = "You must provide one of '--users', '--projects', or '--server' when '--migrate' is given."
                raise argparse.ArgumentTypeError
        else:
            # Ensure that no migration related args are specified.
            if results.users or results.projects or results.wholeServer or results.filesOnly:
                msg = "You cannot provide any of '--users', '--projects', '--server', or '--filesonly'" \
                      " without '--migrate'."
                raise argparse.ArgumentTypeError

        if not results.configFile:
            if os.getenv("MVI_MIG_CONFIG") is None:
                msg = "A cluster configuration file must be identified via the '--config' arg or " \
                      "the 'MVI_MIG_CONFIG' environment variable."
                raise argparse.ArgumentTypeError
            results.configFile = os.getenv("MVI_MIG_CONFIG")

    except argparse.ArgumentTypeError:
        parser.print_usage(sys.stderr)
        if msg:
            print(f"error: {msg}", file=sys.stderr)
        results = None

    return results


def setLoggingControls(log):
    """ Sets output control variables for logging out output content.
    Note that the command name is "hardcoded" in the log entry since multiple
    commands will be run in the container."""
    log_level = logger.INFO
    if log is not None:
        if log.lower() == "error":
            log_level = logger.ERROR
        elif log.lower().startswith("warn"):
            log_level = logger.WARNING
        elif log.lower() == "info":
            log_level = logger.INFO
        elif log.lower() == "debug":
            log_level = logger.DEBUG

    logger.basicConfig(format='%(asctime)s.%(msecs)d  migrateMVI  %(levelname)s:  %(message)s',
                       datefmt='%H:%M:%S', level=log_level)


def setupClusterConfig():
    """Loads the json config file and sets up cluster access."""
    try:
        global clusterCfg
        clusterCfg = ClusterConfig(args.configFile)
    except IOError as ioe:
        print(f"Could not load ClusterConfig file '{args.configFile}' -- {ioe}", file=sys.stderr)
        exit(2)
    except json.JSONDecodeError as de:
        print(f"Failed to parse ClusterConfig file '{args.configFile}' -- {de}", file=sys.stderr)
        exit(2)
    except Exception as e:
        print(f"Unexpected error processing ClusterConfig file '{args.configFile}' -- {e}", file=sys.stderr)
        exit(2)

    logger.debug(f"clusterCfg = '{clusterCfg}'")

    setupSourceClusterAccess()


def setupSourceClusterAccess():
    """Determines source cluster type (standalone vs OCP) and sets up for accessing the source cluster."""
    if "clusterUrl" in clusterCfg.source and "clusterProject" in clusterCfg.source:
        if clusterCfg.source["clusterUrl"] == clusterCfg.destination["clusterUrl"]:
            if clusterCfg.source["clusterProject"] == clusterCfg.destination["clusterProject"]:
                print(f"Error: Cluster URL and project cannot be the same for both source and destination. "
                      f"Check the '{args.configFile}' config file.", file=sys.stderr)
                exit(3)
        # Setup for OCP access, including login
        logger.info("Setting up for OCP access to source cluster.")
        pass
    else:
        # Setup of Standalone access
        logger.info("Setting up for kubectl standalone access.")
        pass


class ClusterConfig:
    """ Convenience class for accessing cluster config properties."""

    def __init__(self, filePath):
        """Constructor using json config file as input"""
        with open(filePath) as cfgFile:
            vars(self).update(json.loads("".join(re.sub("\s+#+\s.*$", "", re.sub("\s+//\s.*$", "", line))
                                                 for line in cfgFile)))

    def __str__(self):
        """Stringify for logging purposes."""
        return ', '.join("%s: %s" % item for item in vars(self).items())

#--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# The following classes could be in separate files. They are included
# in this file to minimize what must be "installed" on a standalone
# server in order to use this script. The goal is a single file (this file)
# need be installed/copied onto the standalone server. Therefore the
# following classes are included in this script rather than being
# separate files that are imported.


class SourceAccess:
    """Base class to access and perform source cluster operations."""

    def __init__(self, deploymentName, srcInfo):
        self.ocCmd = "oc"
        self.ocFlags = ""
        self.deployment = {}
        self.imageName = "bcarl/mvi-migration"
        self.deploymentName = deploymentName
        self.info = srcInfo

    def createDeployment(self, params, clusterInfo):
        raise TypeError

    def startMigration(self):
        print(f"""Starting migration under deployment '{self.deploymentName}'.""")
        cmd = [self.ocCmd, "apply", "-f", self.getDeploymentFileName()]
        logger.info(subprocess.check_output(cmd))

    def getStatus(self):
        pod = self.getMigrationPod()
        cmd = [self.ocCmd, "exec", "-it", pod, "--", "/usr/local/migration/migmgr.py",
               "--deployment", self.deploymentName, "--status"]
        try:
            cmdstr = " ".join(cmd)
            logger.debug(f"getting status using '{cmdstr}'")
            os.system(cmdstr)
        except Exception as e:
            print(f"ERROR: failed to get status from the migration container ({e}).", file=sys.stderr)

    def getMigrationPod(self):
        """Gets the migration pod name for the current deployment. Must be a single pod matched to be successful."""
        filterStr = f"{self.deploymentName}-"
        pods = self.getPodNames(filterStr)
        if len(pods) == 1:
            logger.debug(f"matched to '{pods[0]}'")
            return pods[0]
        else:
            logger.error(f"Matched {len(pods)} to {filterStr}. matches={pods}")
        return None

    def getDeploymentFileName(self):
        return f"""{self.deploymentName}-deployment.json"""

    def abortMigration(self):
        self.cleanupMigration()

    def cleanupMigration(self):
        print(f"""Deleting deployment '{self.deploymentName}""")
        cmd = [self.ocCmd, "delete deployment", self.deploymentName]
        logger.info(subprocess.check_output(cmd))

    def getPodNames(self, filterStr):
        logger.debug(f"getPodName; filterStr='{filterStr}")
        cmdArgs = [self.ocCmd, "get", "pods"]
        pods = []

        process = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
        for line in process.stdout:
            string = line.decode('utf-8')
            pod = string.split()[0]
            if filterStr:
                if re.search(filterStr, pod):
                    logger.debug(f"matched pod '{pod}'")
                    pods.append(pod)
            else:
                pods.append(pod)
        process.wait()

        return pods

    def _getMongoServiceName(self):
        """Gets the list of services from the cluster and finds the mongodb service.
        NOTE: The search if for a service containing the string '-mongodb'."""
        try:
            svcs = json.loads(subprocess.check_output([self.ocCmd, self.ocFlags, "-o", "json", "get", "services"]))
        except json.JSONDecodeError as de:
            msg = f"ERROR: Could not get list of services from source cluster -- {de}"
            logger.error(msg)
            print(msg, file=sys.stderr)
            exit(5)

        mongo = [item for item in svcs["items"] if "-mongodb" in item["metadata"]["name"]]
        if len(mongo) > 0:
            return mongo[0]["metadata"]["name"]
        else:
            return "vision-mongodb"

    def _getPvcName(self):
        """Gets the PVC name from the source cluster.
        NOTE: the method expects only 1 PVC to exist in the cluster."""
        try:
            pvcs = json.loads(subprocess.check_output([self.ocCmd, self.ocFlags, "-o", "json", "get", "pvc"]))
        except json.JSONDecodeError as de:
            msg = f"ERROR: Could not get list of PVCs from source cluster -- {de}"
            logger.error(msg)
            print(msg, file=sys.stderr)
            exit(5)

        # pvc = [item for item in pvcs if "-mongodb" in item["metadata"]["name"]]
        if len(pvcs["items"]) > 0:
            return pvcs["items"][0]["metadata"]["name"]
        else:
            return "vision-data-pvc"

    def _saveDeploymentToFile(self):
        fileName = self.getDeploymentFileName()
        logger.info(f"Saving deployment to '{self.deployment}'")

        with open(fileName, 'w+') as fp:
            json.dump(self.deployment, fp, indent=2)

        print(f"Saved deployment definition in '{fileName}'.")

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# StandaloneSource extends the SourceAccess base class for source environments
# that are standalone kubernetes based. It sets variables for a standalone
# kubernetes environment and generates a deployment definition for a
# standalone environment
# TODO: create a common deployment definition that can be shared and added to for specific environments


class StandaloneSource(SourceAccess):
    """Class for standalone cluster access to data and operations."""

    def __init__(self, deploymentName, srcInfo):
        super().__init__(deploymentName, srcInfo)
        self.helmCmd = "/opt/ibm/vision/bin/helm.sh"
        self.ocCmd = "/opt/ibm/vision/bin/kubectl.sh"
        self.imageName = "docker.io/bcarl/mvi-migration:1.0.0_ppc64le"
        logger.debug(f"StandaloneSource: {str(self.__dict__)}")

    def _collectHelmInfo(self):
        try:
            helmInfo = json.loads(subprocess.check_output([self.helmCmd, "-o", "json", "list"]))
        except json.JSONDecodeError as de:
            msg = f"ERROR: Could not get list of helm info from source cluster -- {de}"
            logger.error(msg)
            print(msg, file=sys.stderr)
            exit(5)
        logger.debug("Returning helminfo -- ", helmInfo[0])
        return helmInfo[0]

    def createDeployment(self, params, clusterInfo):
        print("Creating deployment.")
        helmInfo = self._collectHelmInfo()
        mongoService = self._getMongoServiceName()
        pvcName = self._getPvcName()

        migType = "files" if params.filesOnly else "full"

        if params.wholeServer:
            migrationScope = "--server "
        elif params.users:
            migrationScope = f"--users {params.users} "
        elif params.projects:
            migrationScope = f"--projects {params.projects}"
        else:
            # This condition should have already been caught, but handle it just in case.
            logger.error("No migration scope specified in input params.")
            exit(4)

        self.deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.deploymentName,
                "labels": {
                    "run": self.deploymentName,
                    "app": "vision",
                    "chart": helmInfo["chart"],
                    "release": helmInfo["name"],
                }
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "metadata": {
                        "name": self.deploymentName,
                        "labels": {
                            "run": self.deploymentName,
                            "app": "vision",
                            "chart": helmInfo["chart"],
                            "release": helmInfo["name"]
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": self.deploymentName,
                                "image": self.imageName,
                                "imagePullPolicy": "IfNotPresent",
                                "command": [
                                    "/bin/sh",
                                    "-c"
                                ],
                                "args": [
                                    f"""touch /tmp/healthy && """
                                    f"""/usr/local/migration/migmgr.py --deployment {self.deploymentName} """
                                    f"""--migType {migType} {migrationScope} """
                                    f"""--sMongouser {clusterInfo.source["mongoUser"]} """
                                    f"""--sMongopw {clusterInfo.source["mongoPW"]} """
                                    f"""--sMongoservice {mongoService} """
                                    f"""--dCluster {clusterInfo.destination["clusterUrl"]} """
                                    f"""--dProject {clusterInfo.destination["clusterProject"]} """
                                    f"""--dToken {clusterInfo.destination["clusterToken"]} >&2 && sleep 365d"""
                                ],
                                "volumeMounts": [
                                    {
                                       "name": "dlaas-data",
                                      "mountPath": "/opt/powerai-vision/data",
                                     "subPath": "data"
                                    }
                                ],
                                "resources": {
                                    # No limits for standalone clusters
                                    "limits": {
                                        "cpu": 0,
                                        "memory": "0Gi",
                                    }
                                    # "limits": {
                                    #    "cpu": 8,
                                    #    "memory": "8Gi",
                                    # },
                                    # "requests": {
                                    #    "cpu": 4,
                                    #    "memory": "2Gi",
                                    # }
                                },
                                "readinessProbe": {
                                    "exec": {
                                        "command": [
                                            "cat",
                                            "/tmp/healthy"
                                        ],
                                    },
                                    "periodSeconds": 5
                                }
                            }
                        ],
                        "volumes": [
                            {
                                "name": "dlaas-data",
                                "persistentVolumeClaim": {
                                    "claimName": f"{pvcName}"
                                }
                            }
                        ],
                        "affinity": {
                            "nodeAffinity": {
                                "requiredDuringSchedulingIgnoredDuringExecution": {
                                    "nodeSelectorTerms": [
                                        {
                                            "matchExpressions": [
                                                {
                                                    "key": "kubernetes.io/arch",
                                                    "operator": "In",
                                                    "values": [
                                                        "ppc64le",
                                                        "amd64"
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                "selector": {
                    "matchLabels": {
                        "run": f"{self.deploymentName}"
                    }
                }
            }
        }
        self._saveDeploymentToFile()

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# OcpSource extends the SourceAccess base class for source environments that are
# OCP cloud based. It sets variables for an OCP environment and generates a
# deployment definition for an OCP environment. Note that the deployment
# definition requirements vary for Gen1 and Gen2 environments. The MVI version
# will be used to make that determination.
# TODO: Add support for OCP based source cluster.


class OcpSource(SourceAccess):
    """Class to perform OCP source operations."""

    def __init__(self, name, srcInfo):
        super().__init__(srcInfo)
        self.kubectl = f"oc --kubeconfig /tmp/{name}.config"

    def createDeployment(self, params, clusterInfo):
        pass


if __name__ == "__main__":
    main()
