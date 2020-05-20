#!/usr/bin/env python3
# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2019,2020 IBM International Business Machines Corp.
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

import logging as logger
import sys
import vapi
import vapi_cli.cli_utils as cli_utils
from vapi_cli.cli_utils import reportSuccess, reportApiError, translate_flags

ds_cat_flags = "(--dsid=<dataset-id>)  (--catid=<cat-id> | --id=<cat-id>)"
ds_cat_description = """   --dsid    Required parameter identifying the dataset to which
              the file belongs
   --catid | --id  Required parameter identifying the targeted category"""

server = None

# ---  Create Operation  ---------------------------------------------
create_usage = """
Usage:   categories create --dsid=<dataset_id>  --name=<name>

Where:
   --dsid   Required parameter that identifies the dataset into which the
             category is to be loaded
   --name    category name

Creates a new category in the given dataset.
"""


def create(params):
    """Handles the 'create' operation for adding a category to a dataset.
    """

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", "")

    rsp = server.categories.create(dsid, name)
    if rsp is None:
        reportApiError(server, f"Failed to create category ({name}) in dataset {dsid}")
    else:
        catid = rsp.get("dataset_category_id", "???")
        reportSuccess(server, f"Successfully created category {catid} ({name}) in dataset {dsid}")


# ---  Change/Update Operation  --------------------------------------
change_usage = f"""
Usage:  categories change {ds_cat_flags} --name <name>

Where:
{ds_cat_description}
   --name  Parameter identifying the new name for the category

Modifies a category. Currently no modifications are allowed.
"""


def update(params):
    """Handles the 'change' operation for modifying a category.
    """

    dsid = params.get("--dsid", "missing_id")
    catid = params.get("--catid", "missing_id")

    expected_args = {'--name': 'name'}
    kwargs = translate_flags(expected_args, params)
    kwargs["action"] = "rename"

    rsp = server.categories.action(dsid, catid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change category id '{catid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Changed category id '{catid}' in dataset '{dsid}'")


delete_usage = f"""
Usage:  categories delete {ds_cat_flags}

Where:
{ds_cat_description}

Deletes the indicated category. At this time, only 1 category can be 
deleted at a time.
"""


# ---  Delete Operation  ---------------------------------------------
def delete(params):
    """Deletes one category identified by the --dsid and --catid parameters."""

    dsid = params.get("--dsid", "missing_id")
    catid = params.get("--catid", "missing_id")

    rsp = server.categories.delete(dsid, catid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete category id '{catid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Deleted category id '{catid}' in dataset '{dsid}'")


# ---  List/Report Operation  ----------------------------------------
list_usage = f"""
Usage:  categories list --dsid=<dataset_id> [--sort=<sort-string>] [--summary]

Where:
   --dsid   Required parameter that identifies the dataset to which the
             categories belong.
   --sort    Comma separated string of field names on which to sort.
             Add " DESC" after a field name to change to a descending sort.
             If adding " DESC", the field list must be enclosed in quotes.
    --summary Flag requesting only summary output for each dataset returned


Generates a JSON list of categories matching the input criteria.
"""


def report(params):
    """Handles the 'list' operation."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "name"]

    dsid = params.get("--dsid", "missing_id")

    expectedArgs = {'--sort': 'sortby'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.categories.report(dsid, **kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list categories")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Show Operation  -----------------------------------------------
show_usage = f"""
Usage:  categories show {ds_cat_flags}

Where:
{ds_cat_description}

Shows detail metadata information for the indicated category.
"""


def show(params):
    """Handles the 'show' operation to show details of a single category"""

    dsid = params.get("--dsid", "missing_id")
    catid = params.get("--catid", "missing_id")

    rsp = server.categories.show(dsid, catid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get category id '{catid}' in dataset id '{dsid}'")
    else:
        reportSuccess(server)


# ---  Count Operation  ----------------------------------------------
count_usage = f"""
Usage:  categories count {ds_cat_flags}

Where:
{ds_cat_description}

Shows the number of files assigned to this category.
"""


def count(params):
    """Handles the 'count' operation for counting files associated with a category.
    """

    dsid = params.get("--dsid", "missing_id")
    catid = params.get("--catid", "missing_id")

    kwargs = {"action": "calculate"}

    rsp = server.categories.action(dsid, catid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change category id '{catid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"{rsp.get('size', '???')} files")


cmd_usage = f"""
Usage:  categories {cli_utils.common_cmd_flags} <operation> [<args>...]

Where: {cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create   -- create a category in a dataset
      list     -- report a list of categories in a dataset
      change   -- change certain metadata attributes of a category 
      delete   -- delete a category
      show     -- show a metadata for a specific category
      count    -- count the number of file associated with a category

Use 'categories <operation> --help' for more information on a specific command.
"""

usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage,
    "count": count_usage
}

operation_map = {
    "create": create,
    "list": report,
    "change": update,
    "delete": delete,
    "show": show,
    "count": count
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, id="--catid", argv=params, cmd_flags=cmd_flags)
    if args is not None:
        try:
            server = vapi.connect_to_server(cli_utils.host_name, cli_utils.token)
        except Exception as e:
            print("Error: Failed to setup server.", file=sys.stderr)
            logger.debug(e)
            return 1

        args.operation(args.op_params)


if __name__ == "__main__":
    main(None)
