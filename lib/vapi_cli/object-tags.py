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

ds_tag_flags = "(--dsid=<dataset-id>)  (--tagid=<tag-id> | --id=<tag_id>)"
ds_tag_description = """   --dsid    Required parameter identifying the dataset to which
              the file belongs
   --tagid | --id Required parameter identifying the targeted object tag"""

server = None

# ---  Create Operation  ---------------------------------------------
create_usage = """
Usage:   object_tags create --dsid=<dataset_id>  --name=<name>

Where:
   --dsid   Required parameter that identifies the dataset into which the
             tag is to be loaded
   --name    Tag name

Creates a new object tag in the given dataset.
"""


def create(params):
    """Handles the 'create' operation for adding an object tag to a dataset.
    """

    dsid = params.get("--dsid", "missing_id")

    expected_args = {"--name": "name"}
    kwargs = translate_flags(expected_args, params)
    rsp = server.object_tags.create(dsid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failed to create object tag in dataset {dsid}")
    else:
        tagid = rsp.get("dataset_tag_id", "???")
        reportSuccess(server, f"Successfully created object tag with id {tagid} in dataset {dsid}")


# ---  Change/Update Operation  --------------------------------------
change_usage = f"""
Usage:  object_tags change {ds_tag_flags} --name=<name>

Where:
{ds_tag_description}
   --name  Parameter identifying the new name for the tag

Modifies an object tag. Currently no modifications are allowed.
"""


def update(params):
    """Handles the 'change' operation for modifying an object tag.
    """

    dsid = params.get("--dsid", "missingid")
    tagid = params.get("--tagid", "missing_id")

    expected_args = {'--name': 'name'}
    kwargs = translate_flags(expected_args, params)

    rsp = server.object_tags.update(dsid, tagid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change tag id '{tagid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Changed tag id '{tagid}' in dataset '{dsid}'")


# ---  Delete Operation  ---------------------------------------------
delete_usage = f"""
Usage:  object_tags delete {ds_tag_flags}

Where:
{ds_tag_description}

Deletes the indicated object tag. At this time, only 1 tag can be 
deleted at a time.
"""


def delete(params):
    """Deletes one object tag identified by the --dsid and --tagid parameters.

    Future work should allow a list of tags."""

    dsid = params.get("--dsid", "missing_id")
    tagid = params.get("--tagid", "missing_id")

    rsp = server.object_tags.delete(dsid, tagid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete tag id '{tagid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Deleted object tag id '{tagid}' in dataset '{dsid}'")


# ---  List/Report Operation  ----------------------------------------
list_usage = f"""
Usage:  object_tags list --dsid=<dataset_id> [--summary] [--sort=<sort-string>]

Where:
   --dsid   Required parameter that identifies the dataset to which the tags
             belong.
   --summary Optional flag to generate summary listing instead of json detail
   --sort    Comma separated string of field names on which to sort.
             Add " DESC" after a field name to change to a descending sort.
             If adding " DESC", the field list must be enclosed in quotes.

Generates a JSON list of object tags matching the input criteria.
"""


def report(params):
    """Handles the 'list' operation."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "name", "label_count"]

    dsid = params.get("--dsid", "missing_id")

    expectedArgs = {'--sort': 'sortby'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.object_tags.report(dsid, **kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list tags")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Show Operation  -----------------------------------------------
show_usage = f"""
Usage:  object_tags show {ds_tag_flags}

Where:
{ds_tag_description}

Shows detail metadata information for the indicated object tag.
"""


def show(params):
    """Handles the 'show' operation to show details of a single tag"""

    dsid = params.get("--dsid", "missing_id")
    tagid = params.get("--tagid", "missing_id")

    rsp = server.object_tags.show(dsid, tagid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get tag id '{tagid}' in dataset id '{dsid}'")
    else:
        reportSuccess(server)


cmd_usage = f"""
Usage:  object_tags {cli_utils.common_cmd_flags} <operation> [<args>...]

Where: {cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create   -- create an object tag in a dataset
      list     -- report a list of tags 
      change   -- change certain metadata attributes of tag 
      delete   -- delete one or more tag(s)
      show     -- show a metadata for a specific object tag

Use 'object_tags <operation> --help' for more information on a specific command.
"""

usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage
}

operation_map = {
    "create": create,
    "list": report,
    "change": update,
    "delete": delete,
    "show": show
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, id="--tagid", argv=params, cmd_flags=cmd_flags)
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
