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

#---  Upload Operation  ---------------------------------------------
upload_usage = """
Usage:   files upload --dsid=<dataset_id>  [--metadata=<String>] [--labels=<String>] <file_paths>...

Where:
   --dsid   Required parameter that identifies the dataset into which the
            file(s) are to be loaded
   --metadata  Optional parameter that contains a Json object string of
            key/value pairs to be associated with the uploaded files.
   --labels    Optional parameter that contains a Json Array of label
            annotations to associate with the uploaded file. NOTE that
            labels cannot be applied to multiple files.
   <file_paths>   Space separated list of file paths to upload

Uploads one or more files to a dataset.
Note that at this time, directories of files are not supported."""


def upload(params):
    """Handles the 'upload' operation for loading files into a dataset.

    The "<file_paths>" from 'params' is passed to the library.
    """

    dsid = params.get("--dsid", "missing_id")
    expectedArgs = {
        '--metadata': 'user-metadata',
        '--labels': 'labels'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.files.upload(dsid, params["<file_paths>"], **kwargs)
    if rsp is None:
        try:
            results = server.json()["resultList"]
            total = len(results)
            success = sum([1 for x in results if x["result"] == "success"])
            fail = sum([1 for x in results if x["result"] == "fail"])
        except:
            total = "?"
            success = "?"
            fail = "?"

        reportApiError(server,
                       f"Failure uploading files to dataset {dsid}; total={total}, successes={success}, fails={fail}")
    else:
        try:
            results = server.json()["resultList"]
            total = len(results)
        except:
            total = "?"
        reportSuccess(server, f"Successfully uploaded {total} files to dataset {dsid}")


#---  Change/Update Operation  --------------------------------------
change_usage = f"""
Usage:  files change {ds_file_flags} [--catid=<category_id>]

Where:
{ds_file_description}
   --catid    Optional parameter to change the category with which the file
              is associated. The category must already exist. An
              empty string ("") for category id will disassociate the file
              from its current category

Modifies metadata for a file. Currently the only modification available
through this operation is the category association."""


def update(params):
    """Handles the 'change' operation for modifying a file.

    Expected flags in 'params' are translated to Json Field names to identify modifications to be made"""

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "missing_id")

    expectedArgs = {'--catid': 'target_category_id'}
    kwargs = translate_flags(expectedArgs, params)
    kwargs["action"] = "change_category"

    rsp = server.files.action(dsid, fileid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change file id '{fileid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Changed file id '{fileid}' in dataset '{dsid}'")


#---  Delete Operation  ---------------------------------------------
delete_usage = f"""
Usage:  files delete {ds_file_flags}

Where:
{ds_file_description}

Deletes the indicated file. At this time, only 1 file can be 
deleted at a time.
"""


def delete(params):
    """Deletes one file identified by the --dsid and --fileid parameters.

    Future work should allow a list of files."""

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "missing_id")

    rsp = server.files.delete(dsid, fileid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete file id '{fileid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Deleted file id '{fileid}' in dataset '{dsid}'")


#---  List/Report Operation  ----------------------------------------
list_usage = f"""
Usage:  files list --dsid=<dataset_id> [--catid=<category_id>] [--parentid=<parent_id>]
             [--query=<query_string>] [--sort=<string>] [--summary]
             {cli_utils.limit_skip_flags}

Where:
   --dsid    Required parameter that identifies the dataset to which the files
             belong.
   --catid   Optional parameter to filter results to files belonging to the
             indicated category. Only 1 category can be specified
   --parentid  Optional parameter to filter results to files with the
             indicated parent.  Only 1 parent can be specified.
   --query   Optional parameter containing set of comma separated query terms.
             Each query term has 3 parts; a field name, a comparison, and a value.
             Each of the 3 parts is separated by whitespace. Possible comparision strings
             are '==' (equal), '!=' (not equal), '>' (greater than), '<' (less than),
             '>=' (greater than or equal) and '<=' (less than or equal). Values can be 
             quoted strings or unquoted numbers
   --sort    Comma separated string of field names on which to sort.
             Add " DESC" after a field name to change to a descending sort.
             If adding " DESC", the field list must be enclosed in quotes.
   --summary Flag requesting only summary output for each dataset returned

Generates a JSON list of files matching the input criteria."""


def report(params):
    """Handles the 'list' operation.
    'params' flags are translated into query-parameter variable names."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "original_file_name", "file_type"]

    dsid = params.get("--dsid", "missing_id")

    expectedArgs = {'--catid': 'category_id',
                    '--parentid': 'parent_id',
                    '--query': 'query',
                    '--sort': 'sortby',
                    '--limit': 'limit',
                    '--skip': 'skip'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.files.report(dsid, **kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list files")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


#---  Show Operation  -----------------------------------------------
show_usage = f"""
Usage:  files show --dsid=<dataset_id> --fileid=<file_id>

Where:
{ds_file_description}

Shows detail metadata information for the indicated file."""


def show(params):
    """Handles the 'show' operation to show details of a single file"""

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "missing_id")

    rsp = server.files.show(dsid, fileid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get file id '{fileid}' in dataset id '{dsid}'")
    else:
        reportSuccess(server)


# ---  Download Operation  -------------------------------------------
download_usage = f"""
Usage:  files download --dsid=<dataset_id> --fileid=<file_id> [--thumbnail] [--output=<outputfilename>]

Where:
{ds_file_description}
   --thumbnail   Optional parameter to download the thumbnail instead of
                 the file.
   --output      Optional parameter identifying the name of the output file  path

Downloads the image associated with the indicated file."""


def download(params):
    """Handles the 'download' operation to show details of a single file"""

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "not-provided")
    thumbnail = params.get("--thumbnail", False)
    fname = params.get("--output", None)

    rsp = server.files.download(dsid, fileid, thumbnail, fname)
    if server.server.rsp_ok():
        reportSuccess(server, f"Downloaded file {fileid} from dataset {dsid} into file {rsp}")
    else:
        reportApiError(server, f"Failed to download file {fileid} from dataset {dsid}; status={server.server.status_code()}")



# ---  Copy Operation  ---------------------------------------------
copy_usage = """
Usage:   files copy --from=<origin_dataset_id> --to=<destination_dataset_id>  <file_ids>...

Where:
   --from   Required parameter that identifies the dataset that the
            file(s) are to be copied from (the origin dataset)
   --to     Required parameter that identifies the dataset that the
            file(s) are to be copied to (the destination dataset)
   <file_ids>   Space separated list of file ids to copied

Copies one or more files from the origin dataset into the destination dataset.
All associated category and annotations are copied; and created in the
destination dataset if they do not already exist."""


def copy(params):
    """Handles the 'copy' operation for loading files into a dataset.

    The "<file_paths>" from 'params' is passed to the library.
    """

    fromDs = params.get("--from", "missing-id")
    toDs = params.get("--to", "")
    rsp = server.files.copymove("copy", fromDs, toDs, params["<file_ids>"])
    if rsp is None:
        try:
            results = server.json()["result_list"]
            total = len(results)
            success = sum([1 for x in results if "new_file_id" in x])
            fail = total - success
        except:
            total = "?"
            success = "?"
            fail = "?"

        reportApiError(server,
                       f"Failure copying files from dataset {fromDs} to dataset {toDs}; total={total}, successes={success}, fails={fail}")
    else:
        try:
            results = server.json()["result_list"]
            total = len(results)
        except:
            total = "?"
        reportSuccess(server, f"Successfully copied {total} files to dataset {toDs}")


# ---  Move Operation  ---------------------------------------------
move_usage = """
Usage:   files move --from=<origin_dataset_id> --to=<destination_dataset_id>  <file_ids>...

Where:
   --from   Required parameter that identifies the dataset that the
            file(s) are to be moved from (the origin dataset)
   --to     Required parameter that identifies the dataset that the
            file(s) are to be moved to (the destination dataset)
   <file_ids>   Space separated list of file ids to moved

Moves one or more files from the origin dataset into the destination dataset.
All associated category and annotations are copied; and created in the
destination dataset if they do not already exist."""


def move(params):
    """Handles the 'move' operation for loading files into a dataset.

    The "<file_paths>" from 'params' is passed to the library.
    """

    fromDs = params.get("--from", "missing-id")
    toDs = params.get("--to", "")
    rsp = server.files.copymove("move", fromDs, toDs, params["<file_ids>"])
    if rsp is None:
        try:
            results = server.json()["result_list"]
            total = len(results)
            success = sum([1 for x in results if "new_file_id" in x])
            fail = total - success
        except:
            total = "?"
            success = "?"
            fail = "?"

        reportApiError(server,
                       f"Failure copying files from dataset {fromDs} to dataset {toDs}; total={total}, successes={success}, fails={fail}")
    else:
        try:
            results = server.json()["result_list"]
            total = len(results)
        except:
            total = "?"
        reportSuccess(server, f"Successfully moved {total} files to dataset {toDs}")


#---  savelabels Operation  -----------------------------------------
savelabels_usage = f"""
Usage:  files savelabels --dsid=<dataset_id> --fileid=<file_id> 
              (--label_file=<json_file> | <json_string>)

Where:
{ds_file_description}
   --label_File    Optional parameter identifying the file that contains the
              Json label information. Only one of '--label_file' or 
              '<json_string>' must be supplied.
   <json_string>  Optional string containing the json for the label.
              Only one of '--label_file' or '<json_string>' must be supplied.

Saves a group of labels belonging to the indicated file.  This command replaces
all labels currently associated with the file with those labels provided. For
adding a single label, see the 'object-labels' command."""


def savelabels(params):
    """Handles the 'savelabels' operation"""

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "missing_id")

    file_name = params.get("--label_file")
    if file_name is not None:
        try:
            with open(file_name) as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(f"ERROR: failed to read json data from file '{file_name}'; {e}", file=sys.stderr)
            return -1
    else:
        try:
            data = json.loads(params.get("<json_string>", ""))
        except Exception as e:
            print(f"ERROR: Failed to convert label input to json; {e}", file=sys.stderr)
            return -1

    rsp = server.object_labels.create(dsid, fileid, data)
    if rsp is None:
        reportApiError(server, f"Failed to save labels for file {fileid} in dataset {dsid}")
    else:
        reportSuccess(server, f"Successfully created labels for file {fileid} in dataset {dsid}.")


# --- getlabels Operation  -------------------------------------------
getlabels_usage = f"""
Usage:  files getlabels --dsid=<dataset_id> --fileid=<file_id> 

Where:
{ds_file_description}

Gets labels for the given file in "old style" format."""


def getlabels(params):
    """Handles the 'getlabels' operation"""

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "missing_id")

    rsp = server.object_labels.getlabels(dsid, fileid)
    if rsp is None:
        reportApiError(server, f"Failed to get labels for dataset {dsid} and file {fileid}")
    else:
        reportSuccess(server, None)


cmd_usage = f"""
Usage:  files {cli_utils.common_cmd_flags} <operation> [<args>...]

Where: {cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      upload   -- upload file(s) to a dataset
      list     -- report a list of files 
      change   -- change certain metadata attributes of a file
      delete   -- delete one or more files
      show     -- show a metadata for a specific file
      download -- download a file
      copy     -- copies one or more files from one dataset to another
      move     -- moves one or more files from one dataset to another
      savelabels -- save object labels to a file
      getlabels  -- get object labels associated with a file

Use 'files <operation> --help' for more information on a specific command."""

# Usage statement map  -- indexed by CLI operation name
usage_stmt = {
    "usage": cmd_usage,
    "upload": upload_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage,
    "download": download_usage,
    "copy": copy_usage,
    "move": move_usage,
    "getlabels": getlabels_usage,
    "savelabels": savelabels_usage
}

# Operation map to map CLI operation name to function implementing that operation
operation_map = {
    "upload": upload,
    "list": report,
    "change": update,
    "delete": delete,
    "show": show,
    "download": download,
    "copy": copy,
    "move": move,
    "getlabels": getlabels,
    "savelabels": savelabels
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, id="--fileid", argv=params, cmd_flags=cmd_flags)
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
