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
import sys

import requests
import vapi
import logging as logger
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

args = None
server = None


def main(params):
    """ Example script to delete multiple files based upon query criteria.
The number of files matching the criteria will be  presented and the
user will be  prompted to perform the delete.
A "force" flag is provided to avoid the prompt.
    """
    global args
    args = getValidInputs()
    if args is None:
        exit(1)

    setupLogging(args.log)
    setupServer()
    listOfFiles = getFileList()
    deleteFilesInList(listOfFiles)


def setupLogging(log):
    """ Sets up the logging service."""

    log_level = logger.WARNING

    if log is not None:
        # Translate log level string to logger values
        if log.lower() == "error":
            log_level = logger.ERROR
        elif log.lower().startswith("warn"):
            log_level = logger.WARNING
        elif log.lower() == "info":
            log_level = logger.INFO
        elif log.lower() == "debug":
            log_level = logger.DEBUG

        logger.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)s: %(message)s',
                            datefmt='%H:%M:%S', level=log_level)


def setupServer():
    """ Setup the connection to the MVI Server."""
    global server
    try:
        server = vapi.connect_to_server(args.baseurl, args.token)
    except Exception as e:
        print("Error: Failed to setup server.", file=sys.stderr)
        print(e)
        exit(2)


def getFileList():
    """ Query MVI server for the list of files matching the given query."""
    files = server.files.report(args.dsid, query=args.queryString)
    if not server.rsp_ok():
        print(f"Error: Got status code {server.status_code()} from file lookup. Reason = {json.dumps(server.json(), indent=2)}")
        exit(2)
    return files


def deleteFilesInList(fileList):
    """ Delete all files from the MVI server that are in the provided list of files."""

    numberOfFiles = len(fileList)
    logger.debug(f"deleting {numberOfFiles} files from dataset id {args.dsid}.")
    if numberOfFiles <= 0:
        print("No files found matching the given query criteria.")
        logger.info("Query found no files to delete.")
        return
    if numberOfFiles > 1000:
        numberOfThreads = 16
    else:
        numberOfThreads = 8

    if not okToDeleteFiles(fileList):
        return
    logger.info(f"Deleting {numberOfFiles} files from dataset id {args.dsid}.")

    # The vision-tools library does not support group/batch delete of files.
    # So we have to use the requests interface directly.
    idList = [dic['_id'] for dic in fileList]
    payload = {
        "action": "delete",
        "id_list": idList
    }

    url = f"{server.server.baseurl}/datasets/{args.dsid}/files/action"
    headers = {
        "x-auth-token":  server.server.token
    }
    rsp = requests.post(url, headers=headers, verify=False, json=payload)

    rspData = rsp.json()
    if rsp.ok:
        if "result" in rspData:
            print(f"""successfully deleted {rspData["success_count"]}, failed on {rspData["fail_count"]}""")
            logger.debug(json.dumps(rsp.json(), indent=2))
        else:
            print(f"""""", file=sys.stderr)
            print(json.dumps(rspData, indent=2), file=sys.stderr)
    else:
        print(f"delete operation rejected by server with code {rsp.status_code}.", file=sys.stderr)
        if "success_count" in rspData:
            print(f"""successfully deleted {rspData["success_count"]}, failed on {rspData["fail_count"]}""", file=sys.stderr)
        print(json.dumps(rspData, indent=2), file=sys.stderr)


def okToDeleteFiles(fileList):
    """ Prompts the user to confirm the delete operation."""
    doDelete = False
    if not args.force:
        userRsp = input(f"\nDo you want to proceed with deleting {len(fileList)} files from dataset id {args.dsid}? (y/N): ")
        print()
        logger.debug(f"User responded with '{userRsp}'")
        lcRsp = userRsp.lower()
        if lcRsp == "y" or lcRsp == "yes":
            logger.debug("User confirmed delete.")
            doDelete = True
    else:
        doDelete = True
    return doDelete


def getValidInputs():
    """ parse command line options using argparse

    Sets default values if necessary.

    returns argparse results object
    """
    parser = argparse.ArgumentParser(
        description="Tool to delete files from a dataset based upon query criteria")
    parser.add_argument('--url', action="store", dest="baseurl", required=False,
                        help="Base url of the server (e.g. https://server.junk.com/api). "
                             "If not specified VAPI_BASE_URI will be used from environment.")
    parser.add_argument('--token', action="store", dest="token", required=False,
                        help="User token or API key. If not specified VAPI_TOKEN will be used from environment.")
    parser.add_argument('--dsid', action="store", dest="dsid", required=True,
                        help="Dataset id for dataset containing file.")
    parser.add_argument('--query', action="store", dest="queryString", required=True, type=str,
                        help="File query string. For example 'metadata.inspection_date > 20210302'. "
                             "Use 'vision files list --dsid <DSID> --query <QEUERY_STR> --sum' to get a list of"
                             "files that match the query to ensure the query is precise enough.")
    parser.add_argument('--log', action="store", required=False, type=str, default="warn",
                        help="Log level (debug, info, warn, error). Default is 'warn'.")
    parser.add_argument('--force', action="store", required=False, type=bool, default=False,
                        help="Do not perform the 'Are you sure?' prompt, just do the delete.")

    try:
        results = parser.parse_args()

    except argparse.ArgumentTypeError as e:
        logger.error(e.args)
        parser.print_help(sys.stderr)
        results = None

    return results


if __name__ == "__main__":
    main(sys.argv[1:])

