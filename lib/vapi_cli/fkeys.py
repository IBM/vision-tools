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
import json
import vapi
import vapi_cli.cli_utils as cli_utils
from vapi_cli.cli_utils import reportSuccess, reportApiError, translate_flags

# All of Vision Tools requires python 3.6 due to format string
# Make the check in a common location
if sys.hexversion < 0x03060000:
    sys.exit("Python 3.6 or newer is required to run this program.")

server = None

# Common flag and description strings for usage statements
ds_file_flags = "(--dsid=<dataset-id>)  ((--fileid=<file-id> | --id=<file-id>))"
ds_file_description = """   --dsid     Required parameter identifying the dataset to which
              the file belongs
   --fileid | --id   Required parameter identifying the targeted file"""

#---  Create a User Key Operation  -----------------------------------
create_usage = """
Usage:   fkeys create --dsid=<dataset_id>  --name=<name> [--description=<description>]

Where:
   --dsid   Required parameter that identifies the dataset into which the
            user metadata key is to be created.
   --name   Required parameter name of the new user metadata key
   --description   Optional parameter describing the user metadata key

Creates a new file user metadata key."""


def create(params):
    """Handles the creating a new file user metadata key.
    """

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", " no name ")

    rsp = server.file_keys.create(dsid, name, **params)
    if rsp is None:
        reportApiError(server, f"Failure attempting to create file user metadata key named '{name}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Created key '{name}' in dataset '{dsid}'")


#---  Change/Update Operation  --------------------------------------
change_usage = f"""
Usage:  fkeys change  --dsid=<dataset_id> --name=<key_name> [--description=<description>] [--newname=<new_name>]

Where:
   --dsid   Required parameter that identifies the dataset into which the
            user metadata key is to be created.
   --name   Required parameter identifying the name of the key to be changed.
   --description  Optional parameter containing the new description
   --newname   Optional parameter containing the new name

Modifies attributes of the specified key."""


def update(params):
    """Handles the changing attributes of a specific file user metadata key.

    Expected flags in 'params' are translated to Json Field names to identify modifications to be made"""

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", "missing_id")

    expectedArgs = {'--newname': 'name',
                    '--description': 'description'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.file_keys.update(dsid, name, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change file user metadata key '{name}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Changed file user metadata key'{name}' in dataset '{dsid}'")


#---  Delete Operation  ---------------------------------------------
delete_usage = f"""
Usage:  fkeys delete --dsid=<dataset_id> --name=<key-name>

Where:
   --dsid   Required parameter that identifies the dataset into which the
            user metadata key is to be created.
   --name   Required parameter identifying the name of the key to delete

Deletes the indicated user file key. NOTE: this operation will also delete
all file user metadata with the same key name from all files in the dataset.
"""


def delete(params):
    """Deletes one user file metadata key as specified.

    Future work should allow a list of files."""

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", "__NO_NAME_")

    rsp = server.file_keys.delete(dsid, name)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete file user metadata key '{name}' from dataset '{dsid}'")
    else:
        reportSuccess(server, f"Deleted file user metadata key '{name}' from dataset '{dsid}'")


#---  List/Report Operation  ----------------------------------------
list_usage = f"""
Usage:  fkeys list --dsid=<dataset_id> [--summary]
             {cli_utils.limit_skip_flags}

Where:
   --dsid    Required parameter that identifies the dataset to which the files
             belong.
  --sort   Comma separated string of field names on which to sort.
           Add " DESC" after a field name to change to a descending sort.
           If adding " DESC", the field list must be enclosed in quotes.
  --summary Flag requesting only summary output for each dataset returned

Generates a JSON list of files matching the input criteria."""


def report(params):
    """Handles the 'list' operation.
    'params' flags are translated into query-parameter variable names."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["name", "use_count"]

    dsid = params.get("--dsid", "missing_id")

    expectedArgs = {'--limit': 'limit',
                    '--skip': 'skip'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.file_keys.report(dsid, **kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list files")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


#---  Show Operation  -----------------------------------------------
show_usage = f"""
Usage:  fkeys show --dsid=<dataset_id> --name=<key_name>

Where:
   --dsid   Required parameter that identifies the dataset into which the
            user metadata key is to be created.
   --name   Required parameter identifying the name of the key to delete

Shows detail information for the indicated file user metadata key."""


def show(params):
    """Shows details of a specific file user metadata key"""

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", "missing_id")

    rsp = server.file_keys.show(dsid, name)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get file user metadata key '{name}' in dataset id '{dsid}'")
    else:
        reportSuccess(server)


cmd_usage = f"""
Usage:  fkeys {cli_utils.common_cmd_flags} <operation> [<args>...]

Where: {cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create   -- create a file user metadata key in a dataset
      list     -- list file user metadata keys in a dataset 
      change   -- change certain attributes of a file user metadata key
      delete   -- delete a specific file user metadata key
      show     -- show a specific file user metadata key

Use 'fkeys <operation> --help' for more information on a specific command."""

# Usage statement map  -- indexed by CLI operation name
usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage
}

# Operation map to map CLI operation name to function implementing that operation
operation_map = {
    "create": create,
    "list": report,
    "change": update,
    "delete": delete,
    "show": show
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, argv=params, cmd_flags=cmd_flags)
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
