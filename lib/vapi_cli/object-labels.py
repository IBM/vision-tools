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

# Common object-label usage flags and descriptions
ds_obj_label_flags = "--dsid=<dataset-id>  --labelid=<label-id>"
ds_obj_label_description = """   --dsid    Required parameter identifying the dataset to which
              the label belongs
   --labelid  Required parameter identifying the targeted object label"""

# Create operation
create_usage = """
Usage:   object_labels create --dsid=<dataset_id>  --fileid=<file_id>
                       --tagid=<tag_id>
                       (--json_file=<json_file> | <json_string>)

Where:
   --dsid   Required parameter that identifies the dataset into which the
             tag is to be loaded
   --fileid   Required parameter identifying the file to which the label
             belongs.
   --json_file    Optional parameter identifying the file that contains the
             Json label information. Only one of '--label_file' or 
             '<json_string>' must be supplied.
   <json_string>  Optional string containing the json for the label.
             Only one of '--label_file' or '<json_string>' must be supplied.

Creates a new object label on the given file in the given dataset.
"""


def create(params):
    """Handles the 'create' operation for adding an object tag to a dataset.
    """

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", "missing_id")
    tagid = params.get("--tagid", None)

    file_name = params.get("--label_file")
    if file_name is not None:
        try:
            with open(file_name) as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(f"ERROR: failed to read json data from file '{file_name}'; {e}")
            return -1
    else:
        try:
            data = json.loads(params.get("<json_string>", ""))
        except Exception as e:
            print(f"ERROR: Failed to convert label input to json; {e}")
            return -1

    logger.debug(f"dsid={dsid}, fileid={fileid}, tagid={tagid}, data={data}")
    rsp = server.object_labels.create(dsid, fileid, tagid, data)
    if rsp is None:
        reportApiError(server, f"Failed to create object tag in dataset {dsid}")
    else:
        # noinspection PyBroadException
        try:
            labelid = server.json()["id"]
        except:
            labelid = "???"
        reportSuccess(server, f"Successfully created object tag with id {labelid} in dataset {dsid}")


#---  Change/Update Operation  ---------------------------------------
change_usage = f"""
Usage:  object-labels change {ds_obj_label_flags} [--tagid <tag_id>]
                      [--generate_type=<gen_type>]
                      [(--json_file=<json_file> | <json_string>)]

Where:
{ds_obj_label_description}
   --tagid  Parameter identifying the id of the new tag (new tag must exist)
   --generate_type  Parameter identifying the new generate type (e.g. 'manual')
   --json_file    Optional parameter identifying the file that contains the
             Json label information. Only one of '--label_file' or 
             '<json_string>' can be supplied.
   <json_string>  Optional string containing the json for the label.
             Only one of '--label_file' or '<json_string>' can be supplied.

Modifies an object label. Use either '--label_file' or '<json_string>'
JSON data to modify either the 'bnd_box' or 'segment_polygons' properties.
Invalid properties in the JSON will be ignored.
"""


def update(params):
    """Handles the 'change' operation for modifying an object label.
    """

    dsid = params.get("--dsid", "missing_id")
    labelid = params.get("--labelid", "missing_id")

    expected_args = {
        '--tagid': 'tag_id',
        '--generate_type': 'generate_type',
    }
    kwargs = translate_flags(expected_args, params)

    file_name = params.get("--label_file")
    data = None
    if file_name is not None:
        try:
            with open(file_name) as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(f"ERROR: failed to read json data from file '{file_name}'; {e}")
            return -1
    elif "<json_string>" in params.keys() and params["<json_string>"] is not None:
        try:
            data = json.loads(params.get("<json_string>", ""))
        except Exception as e:
            print(f"ERROR: Failed to convert label input to json; {e}")
            return -1
    if data is not None:
        kwargs.update(data)

    rsp = server.object_labels.update(dsid, labelid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change label id '{labelid}' in dataset '{dsid}'")
    else:
        reportSuccess(server, f"Changed label id '{labelid}' in dataset '{dsid}'")


# ---  Delete Operation  ---------------------------------------
delete_usage = f"""
Usage:  object_labels delete --dsid=<dataset_id>
                      [--fileids=<file_ids>...] [--tagids=<tag_id>...]
                      [--modelid=<model_id>] [--gen_type=<gen_type>]
                      [--min_conf=<float>] [--max_conf=<float>]

Where:
   --dsid   Required parameter that identifies the dataset to which the labels
             belong.
   --fileids  One or more file ids on which to filter. Multiple ids are entered
               with separate flags or in a comma separated list
   --tagids   One or more tag ids on which to filter. Multiple ids are entered
               with separate flags or in a comma separated list
   --modelid  Id of model used to auto-label
   --gen_type  The method of label generation. Possible values are 'manual' or 'auto'
   --min_conf  Floating point number between 0.0 and 1.0 that is the minimum
               confidence value from auto-label generated labels
   --max_conf  Floating point number between 0.0 and 1.0 that is the minimum
               confidence value from auto-label generated labels
{cli_utils.limit_skip_flag_descriptions}


Deletes the indicated object label(s).

NOTE: 
    Care must be taken with this command, it is possible to delete more labels
    than you want. It is STRONGLY recommended that you use the "list" command
    with the same parameters to ensure that you will only delete the expected
    labels.
"""


def delete(params):
    """Deletes one object labels matching the input criteria."""

    dsid = params.get("--dsid", "missing_id")
    labelid = params.get("--label_id", None)

    expected_args = {"--ids": "ids",
                     "--tagids": "tag_ids",
                     "--fileids": "file_ids",
                     "--modelid": "model_id",
                     "--generate_type": "generate_type",
                     "--min_conf": "min_conf",
                     "--max_conf": "max_conf",
                     "--limit": "limit",
                     "--skip": "skip"
                     }
    kwargs = translate_flags(expected_args, params)

    rsp = server.object_labels.delete(dsid, labelid, None, kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete label(s) from dataset '{dsid}'")
    else:
        reportSuccess(server, f"Deleted object label id(s) from dataset '{dsid}'")


# ---  List/Report Operation  --------------------------------------
list_usage = f"""
Usage:  object_labels list --dsid=<dataset_id>
                      [--fileid=<file_id>] [--tagids=<tag_id>...]
                      [--modelid=<model_id>] [--gen_type=<gen_type>]
                      [--min_conf=<float>] [--max_conf=<float>]
                      {cli_utils.limit_skip_flags}
                      [--summary]


Where:
   --dsid      Required parameter that identifies the dataset to which the
               labels belong.
   --fileid    Optional parameter identifying the file with which the labels
               are associated.
   --tagids    One or more tag ids on which to filter. Multiple ids are entered
               with separate flags or in a comma separated list
   --modelid   Id of model used to auto-label
   --gen_type  The method of label generation. Possible values are 'manual' or
               'auto'
   --min_conf  Floating point number between 0.0 and 1.0 that is the minimum
               confidence value from auto-label generated labels
   --max_conf  Floating point number between 0.0 and 1.0 that is the minimum
               confidence value from auto-label generated labels
{cli_utils.limit_skip_flag_descriptions}
  --summary Flag requesting only summary output for each dataset returned

Generates a JSON list of object labels matching the input criteria.
"""


def report(params):
    """Handles the 'list' operation."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "name", "file_id"]

    dsid = params.get("--dsid", "missing_id")
    fileid = params.get("--fileid", None)

    expected_args = {"--ids": "ids",
                     "--tagids": "tag_ids",
                     "--modelid": "model_id",
                     "--gen_type": "generate_type",
                     "--min_conf": "min_conf",
                     "--max_conf": "max_conf",
                     "--limit": "limit",
                     "--skip": "skip"
                     }
    kwargs = translate_flags(expected_args, params)

    rsp = server.object_labels.report(dsid, fileid, **kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list tags")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Show Operation  ---------------------------------------------
show_usage = f"""
Usage:  object_tags show {ds_obj_label_flags}

Where:
{ds_obj_label_description}

Shows detail metadata information for the indicated object tag.
"""


def show(params):
    """Handles the 'show' operation to show details of a single label"""

    dsid = params.get("--dsid", "missing_id")
    labelid = params.get("--labelid", "missing_id")

    rsp = server.object_labels.show(dsid, labelid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get label id '{labelid}' in dataset id '{dsid}'")
    else:
        reportSuccess(server)


cmd_usage = f"""
Usage:  object_labels {cli_utils.common_cmd_flags} <operation> [<args>...]

Where: {cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create   -- create an object label (annotation) in a dataset
      list     -- report a list of object labels
      change   -- change certain metadata attributes of an object label
      delete   -- delete one or more label(s)
      show     -- show a metadata for a specific object label

Use 'object_labels <operation> --help' for more information on a specific command.
"""

# map of usage statement indexed by operation name
usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage
}

# Operation map mapping operation name to function name
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
