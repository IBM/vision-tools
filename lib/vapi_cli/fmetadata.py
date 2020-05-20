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

#---  Create Operation  -----------------------------------
create_usage = """
Usage:   fmetadata (create|add) --dsid=<dataset_id>  --fileid=<file_id> (--data=<file_path> | <quoted-json-string>)

Where:
   --dsid   Required parameter identifying the dataset containing the target file.
   --fileid  Required parameter identifying the file for the metadata
   --data   Optional parameter identifying the path to a file containing the JSON key/value information.
            Either the '--data' parameter or the '<quoted-json-string>' parameter must be supplied.
   <quoted-json-string>  -- Optional string containing the JSON key/value information.
            Either the '--data' parameter or the '<quoted-json-string>' parameter must be supplied.

Creates a new user metadata information on the specified file."""


def create(params):
    """Handles creating new metadata key/value pairs on the specified file.
    """

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "no_file_id")
    dataFile = params.get("--data", None)

    if dataFile is not None:
        logger.error("Reading metadata from a file is not yet implemented.")
        return 1
    else:
        metadata = json.loads(params.get("<quoted-json-string>", "{}"))

    rsp = server.file_metadata.add(dsid, fileid, metadata)
    if server.rsp_ok():
        reportSuccess(server, None)
    else:
        reportApiError(server, f"Failure attempting to add user metadata to  file '{fileid}' in dataset '{dsid}'")


#---  Change/Update Operation  --------------------------------------
change_usage = f"""
Usage:  fmetadata change  --dsid=<dataset_id> --fileid=<file_id> --key=<key_name> <value>

Where:
   --dsid   Required parameter that identifies the dataset into which the
            user metadata key is to be created.
   --fileid  Required parameter identifying the file containing the metadata
   --key    Required parameter identifying the name of the key to be changed.
   <value>  New value for the specified key

Modifies the value of the specified key in the specified file's metadata."""


def update(params):
    """Handles the changing the value associated with a key in a files user metadata.
"""

    dsid = params.get("--dsid", "no_ds_id")
    fileid = params.get("--fileid", "no_file_id")
    key = params.get("--key", "no_key")
    value = params.get("<value>", None)

    data = {key: value}
    server.file_metadata.add(dsid, fileid, data)
    if server.rsp_ok():
        reportSuccess(server, f"Changed the value of metadata key'{key}' in file '{fileid}'")
    else:
        reportApiError(server, f"Failure attempting to change the value associated with '{key}' in file '{fileid}'")


#---  Delete Operation  ---------------------------------------------
delete_usage = f"""
Usage:  fmetadata delete --dsid=<dataset_id> --fileid=<file_id> <key-name>...

Where:
   --dsid    Required parameter that identifies the dataset into which the
             user metadata key is to be created.
   --fileid  Required parameter identifying the file containing the metadata
   key-name  space separated list of keys to delete.

Deletes the indicate key/value pair from the specified file.
"""


def delete(params):
    """Deletes one user file metadata key as specified.

    Future work should allow a list of files."""

    dsid = params.get("--dsid", "no_ds_id")
    fileid = params.get("--fileid", "no_file_id")
    keys = params.get("<key-name>", [])

    deletedKeys = server.file_metadata.delete(dsid, fileid, keys)
    if server.rsp_ok() is False:
        reportApiError(server, f"Failure attempting to delete user metadata from file '{fileid}'")
    else:
        reportSuccess(server, f"Deleted metadata with keys {deletedKeys} ({len(deletedKeys)} keys) from file '{fileid}'")


#---  List/Report Operation  ----------------------------------------
list_usage = f"""
Usage:  fmetadata list --dsid=<dataset_id> --fileid=<file_id>

Where:
   --dsid    Required parameter that identifies the dataset to which the file
             belong.
   --fileid  Required parameter identifying the file containing the metadata

Prints all key/value metadata pairs associated with the specified file."""


def report(params):
    """ Lists all user metadata on the specified file."""

    dsid = params.get("--dsid", "no_ds_id")
    fileid = params.get("--fileid", "no_file_id")

    server.file_metadata.report(dsid, fileid)

    if server.rsp_ok():
        reportSuccess(server, None)
    else:
        reportApiError(server, f"Failure attempting to list metadata on file {fileid} in dataset {dsid}")


#---  Export Operation  ----------------------------------------------
export_usage = f"""
Usage:  fmetadata export --dsid=<dataset_id>

Where:
   --dsid   Required parameter that identifies the dataset into which the
            user metadata key is to be created.

Exports file user metadata from all files in a dataset in CSV format."""


def export(params):
    """Exports file metadata for all files in a dataset in CSV format """

    dsid = params.get("--dsid", "missing_id")

    server.file_metadata.export(dsid)
    if server.rsp_ok():
        # Must strip the trailing new line.
        reportSuccess(server, server.raw_http_response().text[:-1])
    else:
        reportApiError(server, f"Failure attempting to export all files' user metadata in dataset id '{dsid}'")



cmd_usage = f"""
Usage:  fmetadata {cli_utils.common_cmd_flags} <operation> [<args>...]

Where: {cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create   -- create a user metadata key/value pair on a file
      add      -- alias for 'create'
      list     -- list user metadata on a file 
      change   -- change the value associated of user metadata key
      delete   -- delete a list user metadata from a file
      export   -- export all metadata pairs across all files in a dataset

Use 'fmetadata <operation> --help' for more information on a specific command."""

# Usage statement map  -- indexed by CLI operation name
usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "add": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "export": export_usage
}

# Operation map to map CLI operation name to function implementing that operation
operation_map = {
    "create": create,
    "add": create,
    "list": report,
    "change": update,
    "delete": delete,
    "export": export
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
