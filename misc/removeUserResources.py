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

args = None
mvi = None
OWNER = "owner"

class ResourceCategory:
    def __init__(self, name, title, getter):
        self.name = name
        self.title = title
        self.getResourceList = getter
        self.userItems = []


def main(params):
    """ Remove all MVI resources associated with the given user. A confirmation prompt
    is given to ensure that the removal should proceed.
A "force" flag is provided to avoid the prompt.
    """
    global args
    args = getValidInputs()
    if args is None:
        exit(1)

    setupLogging(args.log)
    setupServer()

    resourceCategories = {
        "projects": {
            "title": "project groups",
            "userItems": [],
            "getResourceList": mvi.projects.report
        },
        "datasets": {
            "title": "datasets",
            "userItems": [],
            "getResourceList": mvi.datasets.report
        },
        "dltasks": {
            "title": "training tasks",
            "userItems": [],
            "getResourceList": mvi.dl_tasks.report
        },
        "trainedModels": {
            "title": "trained models",
            "userItems": [],
            "getResourceList": mvi.trained_models.report
        },
        "deployedModels": {
            "title": "deployed models",
            "userItems": [],
            "getResourceList": mvi.deployed_models.report
        },
        "bgtasks": {
            "title": "background tasks",
            "userItems": [],
            "getResourceList": getUserBgTasks
        }
    }

    getUserResources(args.user, resourceCategories)
    deleteUserResources(resourceCategories)


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
    global mvi
    try:
        mvi = vapi.connect_to_server(args.baseurl, args.token)
    except Exception as e:
        print("Error: Failed to setup mvi.", file=sys.stderr)
        print(e)
        exit(2)


def getUserResources(user, resourceCategories):
    """ Collects lists of user resources. The resource categories to collect are passed in."""

    for name, resource in resourceCategories.items():
        resource["userItems"] = retrieveUserResourceList(user, resource["title"], resource["getResourceList"])
        logger.debug(f"""Found {len(resource["userItems"])} {name} resources.""")


def retrieveUserResourceList(user, resourceName, method):
    logger.debug(f"Getting list of {resourceName}.")
    fullList = method()
    if not mvi.rsp_ok():
        print(
            f"Error: Got status code {mvi.status_code()} from {resourceName} lookup. Reason = {json.dumps(mvi.json(), indent=2)}")
        exit(3)
    return list(filter(lambda item: item[OWNER] == user, fullList))


def userResourceCount(resourceCategories):
    return sum(len(v["userItems"]) for _, v in resourceCategories.items())


def getUserBgTasks():
    logger.debug("Getting list of background tasks.")
    mvi.server.get("/bgtasks")
    if not mvi.rsp_ok():
        print(
            f"Error: Got status code {mvi.status_code()} from project lookup. Reason = {json.dumps(mvi.json(), indent=2)}")
        exit(3)
    return mvi.json()["task_list"]


def deleteUserResources(resourceCategories):
    """ Delete all files from the MVI mvi that are in the provided list of files."""

    numberOfResources = userResourceCount(resourceCategories)
    logger.debug(f"deleting {numberOfResources} total resources for user '{args.user}'.")
    if numberOfResources <= 0:
        print("No resources found for user '{args.user}'.")
        logger.info("Query found no resources to delete.")
        return

    if not okToRemoveResources(numberOfResources):
        return

    return
    # The vision-tools library does not support group/batch delete of files.
    # So we have to use the requests interface directly.
    idList = [dic['_id'] for dic in fileList]
    payload = {
        "action": "delete",
        "id_list": idList
    }

    url = f"{mvi.server.baseurl}/datasets/{args.dsid}/files/action"
    headers = {
        "x-auth-token":  mvi.server.token
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
        print(f"delete operation rejected by mvi with code {rsp.status_code}.", file=sys.stderr)
        if "success_count" in rspData:
            print(f"""successfully deleted {rspData["success_count"]}, failed on {rspData["fail_count"]}""", file=sys.stderr)
        print(json.dumps(rspData, indent=2), file=sys.stderr)


def okToRemoveResources(resourceCount):
    """ Prompts the user to confirm the removal operation."""
    doDelete = False
    if not args.force:
        userRsp = input(f"\nDo you want to proceed with removing {resourceCount} resources associated with user '{args.user}'? (y/N): ")
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
        description="Tool to delete all MVI resources associated with the given user.")
    parser.add_argument('--url', action="store", dest="baseurl", required=False,
                        help="Base url of the mvi (e.g. https://server.junk.com/api). "
                             "If not specified VAPI_BASE_URI will be used from environment.")
    parser.add_argument('--token', action="store", dest="token", required=False,
                        help="User token or API key. If not specified VAPI_TOKEN will be used from environment.")
    parser.add_argument('--user', action="store", dest="user", required=True,
                        help="User id of the user whose resources are to be deleted.")
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

