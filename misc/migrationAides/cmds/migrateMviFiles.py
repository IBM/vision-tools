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
This script will migrate files from an MVI standalone installation (e.g. pre-8.0.0) to an MVI OCP based installation.
The destination MVI installation must be up and running as the script uses a running pod in the installation to
facilitate the transfer. Note that this script performs a "migration" and not a "backup". The files are moved from
a source installation to a destination installation.

This script must be run on the standalone system as it uses `rsync` and `rsync` requires either the source or the
destination to be "local".
"""
import argparse
import os
import subprocess
import sys
import logging

import vapi.accessors.ClusterAccessor as ClusterAccessor

clusterPresent = False
args = {}

mountPoint = os.getenv("MIGMGR_MOUNTPOINT", "/opt/powerai-vision/data/")


def main():
    global args
    args = getInputs()

    if args is not None:
        setLoggingControls(args.logLevel)
        try:
            with ClusterAccessor.ClusterAccessor(standalone=not clusterPresent, clusterUrl=args.cluster,
                                                 user=args.ocpUser, password=args.ocpPasswd, token=args.ocpToken,
                                                 project=args.project):
                taPod = getTaskAnalysisPodName()
                if taPod is not None:
                    if os.path.exists(args.filePath):
                        if os.path.isfile(args.filePath):
                            rc = migrateFile(taPod)
                        else:
                            rc = migrateDirectory(taPod)
                    else:
                        logging.error(f"File '{args.filePath}' does not exist!")
                        exit(3)
                else:
                    exit(3)
        except ClusterAccessor.OcpException as oe:
            print(oe)
            exit(2)
    else:
        exit(1)
    exit(rc)


def getTaskAnalysisPodName():
    """Gets the name of the task analysis pod on the target server."""
    taPod = None
    try:
        taPod = ClusterAccessor.ClusterAccessor.getPods("taskanaly")[0]
    except IndexError:
        logging.error("Could not find task analysis pod.")

    return taPod


def migrateFile(pod):
    """Migrates a file to the target server."""

    cmd = f"""tar -cf - {args.filePath} | oc exec - i {pod} -- bash -c "(cd /; tar -xvf -)" """
    logging.debug(f"copying file using ")
    rc = os.system(cmd)
    if rc != 0:
        logging.error(f"")
    return rc


def migrateDirectory(taPod):
    """Migrates file path provided in args to the target server. File path must be a directory."""

    dirName = ensureParentDirectoryTreeExists(taPod, args.filePath)
    if dirName is not None:
        cmdArgs = ["oc", "rsync", args.filePath, f"{taPod}:{dirName}"]
        logging.info(f"running '{cmdArgs}'")
        process = subprocess.run(cmdArgs)
        rc = process.returncode
        if rc != 0:
            logging.error(f"ERROR: rsync of '{args.filePath}' failed!")
    else:
        logging.error("ERROR: could not ensure parent directory exist!")
    return rc


def ensureParentDirectoryTreeExists(pod, filePath):
    """Create parent directory tree on the target server."""
    dirPath = os.path.dirname(args.filePath)
    cmdArgs = ["oc", "exec", "-i", pod, "--", "/usr/bin/mkdir", "-p", dirPath]
    logging.info(f"Ensure parent directory exists -- {cmdArgs}")
    result = subprocess.run(cmdArgs)
    rc = result.returncode
    if rc != 0:
        logging.warning(f"WARNING: Could not unsure 'f{dirPath}' exists in pod '{pod}'.")
        dirPath = None
    return dirPath


def getInputs():
    """ parse command line options using argparse.

    Sets default values if necessary and enforces "flag group" requirements.

    returns argparse results object on success.
    """
    parser = argparse.ArgumentParser(description="Tool to backup an MVI MongoDB to a zip file.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''

This script must be run on the standalone source MVI installation.
The destination MVI installation must be an OCP installation.

On the standalone system, the user running this script must have authority/permissions
to access the MVI user data and logs directory trees.

For the destination cluster, either the OCP cluster related parameters are required
OR you must be logged into the OCP cluster AND have set the project to the MVI
project. The OCP user information must have enough authority to allow communicating
with a POD running in that cluster.

If you are already logged into the destination OCP cluster, do not specify
'--cluster_url', '--ocpuser', '--ocppasswd', or '--ocptoken'. However, if one of
these flags is specified, all of the cluster information must be specified (see
note about '--ocptoken below). In this case, the script will login to the OCP
cluster and then logout when done.

Note that '--ocptoken' can be used instead of '--ocpuser' and '--ocppasswd'. 
If '--ocptoken' is present, '--ocpuser' and '--ocppasswd' are ignored."
''')
    parser.add_argument('--project', action="store", dest="project", type=str, required=False,
                        help="Target MVI project in the cluster.")
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
    parser.add_argument('--logdir', action="store", dest="logFile", type=str, required=False, default="./",
                        help='Optional directory to store logging output. Directory MUST end in a slash ("/")')
    parser.add_argument('--tar', action="store_true", dest="tarfile", required=False, default=False,
                             help="Indicates that the 'filePath' represents a tar file instead of a directory.")
    # Positional Args
    parser.add_argument('filePath', help="path to the directory (or tar file if '--tar' is specified) to be migrated.")

    try:
        results = parser.parse_args()

    except argparse.ArgumentTypeError as e:
        parser.print_help(sys.stderr)
        results = None

    global clusterPresent
    if results is not None:
        clusterPresent = results.cluster is not None
        ocpTokenPresent = results.ocpToken is not None
        ocpUserPresent = results.ocpUser is not None
        ocpPasswdPresent = results.ocpPasswd is not None

        if clusterPresent or ocpUserPresent or ocpPasswdPresent or ocpTokenPresent:
            if not (clusterPresent and ((ocpUserPresent and ocpPasswdPresent) or ocpTokenPresent)):
                print("If any of '--cluster_url', '--ocpuser', '--ocppasswd', or '--ocptoken' are specified, all must be specified.",
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

    logging.basicConfig(format='%(asctime)s.%(msecs)d  migrateMviFiles  %(levelname)s:  %(message)s',
                        datefmt='%H:%M:%S', level=log_level,
                        )


if __name__ == "__main__":
    main()