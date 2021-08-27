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

import vapi
import logging as logger

args = None
mvi = None
user = ""


class ResourceGroup:
    """Class for accessing and deleting resources in a resource group."""

    def __init__(self, name, title, getter, listDeleter, itemDeleter):
        self.name = name
        self.title = title                 # for messages
        self.getResourceList = getter      # reference to function to get a group's list of resources
        self.deleteResourceList = listDeleter  # reference to function to manage deleting a list of resources
        self.deleteItem = itemDeleter      # reference to function that deletes a single resource item
        self.userItems = []                # list of user resources for a resource group

    def retrieveUserResourceList(self, user):
        """Method using 'getResourceList' reference to get the list of resource and then filter by user."""
        logger.debug(f"Getting list of {self.title}.")
        fullList = self.getResourceList()
        if not mvi.rsp_ok():
            print(
                f"Error: Got status code {mvi.status_code()} from {self.title} lookup. Reason = {json.dumps(mvi.json(), indent=2)}")
            exit(3)
        self.userItems = list(filter(lambda item: item["owner"] == user, fullList))
        return self.userItems


def main(params):
    """ Remove all MVI resources associated with the given user. A confirmation prompt
    is given to ensure that the removal should proceed.
    A "force" flag is provided to avoid the prompt.
    """

    setupEnvironment()

    resourceGroups = setupResourceGroups()
    getUserResources(resourceGroups)

    # Abort if there are deployed models.
    if len(resourceGroups["deployedModels"].userItems) > 0:
        print(f"ERROR: There are deployed models in the server that prevent removing user resources.")
        logger.error("There are deployed models preventing the removal of user resources.")
        exit(3)

    deleteResources(resourceGroups)


def setupEnvironment():
    global args
    args = getValidInputs()
    if args is None:
        exit(1)

    setupLogging(args.log)
    setupServer()

    global user
    user = getUserName()


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


def setupResourceGroups():
    """Setup the resourceGroups object with all resources that need to be examined."""
    resourceGroups = {
        "projects": ResourceGroup("projects", "project groups", mvi.projects.report, singleDelete, mvi.projects.delete),
        "datasets": ResourceGroup("datasets", "datasets", mvi.datasets.report, singleDelete, mvi.datasets.delete),
        "dlTasks": ResourceGroup("dlTasks", "training tasks", mvi.dl_tasks.report, singleDelete, mvi.dl_tasks.delete),
        "trainedModels": ResourceGroup("trainedModels", "trained models", mvi.trained_models.report,
                                       trainedModelBatchDelete, None),
        "deployedModels": ResourceGroup("deployedModels", "deployed models", mvi.deployed_models.report, singleDelete,
                                        mvi.deployed_models.delete),
        "bgTasks": ResourceGroup("bgTasks", "background tasks", getUserBgTasks, bgTaskDelete, None)
    }
    return resourceGroups


def getUserName():
    """Translate user API key to user name."""
    mvi.server.get(f"/users/{mvi.server.token}")
    if not mvi.rsp_ok():
        print(
            f"Error: Got status code {mvi.status_code()} from user token lookup. Reason = {json.dumps(mvi.json(), indent=2)}")
        exit(3)
    return mvi.json()["username"]


def getUserResources(resourceCategories):
    """ Collects lists of user resources. The resource categories to collect are passed in."""
    print("Collecting user resource information.")
    for _, resource in resourceCategories.items():
        resource.retrieveUserResourceList(user)
        logger.debug(f"""Found {len(resource.userItems)} {resource.title}.""")


def userResourceCount(resourceCategories):
    return sum(len(r.userItems) for _, r in resourceCategories.items())


def getUserBgTasks():
    logger.debug("Getting list of background tasks.")
    mvi.server.get("/bgtasks")
    if not mvi.rsp_ok():
        print(
            f"Error: Got status code {mvi.status_code()} from project lookup. Reason = {json.dumps(mvi.json(), indent=2)}")
        exit(3)
    return mvi.json()["task_list"]


def deleteResources(resourceCategories):
    """ Delete all files from the MVI mvi that are in the provided list of files."""

    numberOfResources = userResourceCount(resourceCategories)
    logger.debug(f"deleting {numberOfResources} total resources for user '{user}'.")

    # Do not do anything further if there is nothing to remove.
    if numberOfResources <= 0:
        print(f"No resources found for user '{user}'.")
        logger.debug("Query found no resources to delete.")
        return

    if not okToRemoveResources(resourceCategories, numberOfResources):
        return

    for _, resource in resourceCategories.items():
        resource.deleteResourceList(resource)


def okToRemoveResources(resourceCategories, resourceCount):
    """ Prompts the user to confirm the removal operation."""
    doDelete = False
    if not args.force:
        print()
        for _, resource in resourceCategories.items():
            print(f"""There are {len(resource.userItems)} {resource.title} to remove.""")
        userRsp = input(
            f"\nDo you want to proceed with removing {resourceCount} resources associated with user '{user}'? (y/N): ")
        print()
        logger.debug(f"User responded with '{userRsp}'")
        lcRsp = userRsp.lower()
        if lcRsp == "y" or lcRsp == "yes":
            logger.debug("User confirmed delete.")
            doDelete = True
    else:
        doDelete = True
    return doDelete


def singleDelete(resource):
    """"Delete resources for a resource group that only supports deleting single items."""
    print(f"Deleting {len(resource.userItems)} {resource.title}.")
    for item in resource.userItems:
        logger.debug(f"""deleting {resource.title} with id {item["_id"]} using {resource.deleteItem}""")
        resource.deleteItem(item["_id"])
        if not mvi.rsp_ok():
            print(f"""Failed to delete {resource.name} with id {item["_id"]} -- status code = {mvi.server.status_code()}; {mvi.server.json()}""")


def trainedModelBatchDelete(resource):
    """Delete a list of trained models using the trained model batch delete API"""
    print(f"Deleting {len(resource.userItems)} {resource.title}.")
    if len(resource.userItems) > 0:
        payload = {
            "action": "delete",
            "model_list": [i["_id"] for i in resource.userItems]
        }
        mvi.server.post("/trained-models/action", json=payload)
        if not mvi.rsp_ok():
            print(f"Failed to delete trained models -- status code = {mvi.server.status_code()}; {mvi.server.json()}")


def bgTaskDelete(resource):
    """bgTasks have to be handled specially."""
    print(f"Deleting {len(resource.userItems)} {resource.title}.")
    mvi.server.delete("/bgtasks?status=working")
    mvi.server.delete("/bgtasks")
    if not mvi.rsp_ok():
        print(f"Failed to delete background tasks -- status code = {mvi.server.status_code()}; {mvi.server.json()}")


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
