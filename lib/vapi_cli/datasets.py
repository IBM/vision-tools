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

import json
import sys
import logging as logger
import vapi
import vapi_cli.cli_utils as cli_utils
from vapi_cli.cli_utils import reportSuccess, reportApiError, translate_flags

# All of Vision Tools requires python 3.6 due to format string
# Make the check in a common location
if sys.hexversion < 0x03060000:
    sys.exit("Python 3.6 or newer is required to run this program.")

server = None

# ---  Create Operation  ---------------------------------------------
create_usage = """
Usage: 
  datasets create --name=<dataset-name>

Where:
  --name    A required parameter that specifies the name of the dataset to
            be created

Creates a new dataset with the given name."""


def create(params):
    """Handles the 'change' operation for modifying a dataset.

    Expected flags in 'params' are translated to Json Field names for creation content
    """
    expectedArgs = {'--name': 'name'}

    kwargs = translate_flags(expectedArgs, params)

    rsp = server.datasets.create(**kwargs)
    if rsp is None:
        reportApiError(server, "Failure while creating a dataset")
    else:
        try:
            dsid = server.json()["dataset_id"]
        except:
            dsid = "???"

        reportSuccess(server, f"Successfully created dataset with id {dsid}")


# ---  Change Operation  ---------------------------------------------
change_usage = """
Usage:
  datasets change (--dsid=<dataset-id> | --id=<dataset_id>) [--pgid=<project-group-id>]

Where:
  --dsid | --id    Either '--dsid' or '--id' is required and identifies the dataset
            to be updated.
  --pgid    An optional parameter that indicates the project group with
            which to associate the dataset. An empty string ("") will
            break any current association.

Modifies metadata for a dataset. Currently the only modification available
through this operation is the project group association."""


def update(params):
    """Handles the 'change' operation for modifying a dataset.

    Expected flags in 'params' are translated to Json Field names to identify modifications to be made
    """

    dsid = params.get("--dsid", "missing_id")

    expectedArgs = {'--pgid': 'project_group_id'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.datasets.update(dsid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to change dataset id {dsid}")
    else:
        reportSuccess(server, f"Changed dataset id {dsid}")


# ---  Delete Operation  ---------------------------------------------
delete_usage = """
Usage:
  datasets delete (--dsid=<dataset-id> | --id=<dataset-id>)

Where:
  --dsid | --id    Either '--dsid' or '--id' is required and identifies the
           dataset to be deleted.

Deletes the indicated dataset. At this time, only 1 dataset can be 
deleted at a time."""


def delete(params):
    """Deletes one dataset identified by the --dsid parameter.

    Future work should allow a list of datasets."""

    dsid = params.get("--dsid", "missing_id")
    rsp = server.datasets.delete(dsid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete dataset id {dsid}")
    else:
        reportSuccess(server, f"Deleted dataset id '{dsid}'")


# ---  List Operation  -----------------------------------------------
list_usage = """
Usage:
  datasets list [--pgid=<project-group-id>...] [--sort=<sort-string>] [--summary]

Where:
  --pgid   An optional parameter that identifies 1 or more project groups
           on which to filter the list.  Multiple project groups must
           be comma separated
  --sort   Comma separated string of field names on which to sort.
           Add " DESC" after a field name to change to a descending sort.
           If adding " DESC", the field list must be enclosed in quotes.
  --summary Flag requesting only summary output for each dataset returned

Generates a JSON list of datasets matching the input criteria."""


def report(params):
    """Handles the 'list' operation.
    'params' flags are translated into query-parameter variable names."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "name", "total_file_count"]

    expectedArgs = {
        '--pgid': 'pg_id',
        '--sort': 'sortby'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.datasets.report(**kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list datasets")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Show Operation  -----------------------------------------------
show_usage = """
Usage:
  datasets show (--dsid=<dataset-id> | --id=<dataset-id>)

Where:
  --dsid | --id  Either '--id' or '--dsid' is required and identifies the
            dataset to be show.

Shows detail metadata information for the indicated dataset."""


def show(params):
    """Handles the 'show' operation to show details of a single dataset"""

    dsid = params.get("--dsid", "missing_id")
    rsp = server.datasets.show(dsid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get dataset id '{dsid}'")
    else:
        reportSuccess(server)


# ---  Import Operation  ---------------------------------------------
import_usage = """
Usage:
  datasets import <file-path>

Where:
  <file-path> Required parameter identifying the path to the zip file to import.
              The file must be an IBM Visual Insights (PowerAI Vision) Dataset
              export zip file.

Import an exported dataset zip file to create the dataset in the server.
Importing a dataset creates a new dataset."""


def import_dataset(params):
    """Handles the 'export' operation."""

    filename = params.get("<file-path>", None)

    rsp = server.datasets.import_dataset(filename)
    if rsp is None:
        reportApiError(server, "Failure while importing a dataset.")
    else:
        try:
            dsid = server.json()["dataset_id"]
        except:
            dsid = "???"

        reportSuccess(server, f"Successfully created dataset with id {dsid}.")


# ---  Export Operation  ---------------------------------------------
export_usage = """
Usage:
  datasets export (--dsid=<dataset-id> | --id=<dataset-id>) [--filename=<file-name>] [--raw]

Where:
  --dsid | --id  Either '--dsid' or '--id' is required and identifies the
             dataset to be exported.
  --filename An optional parameter to specify the output file name.
             If no name is provided, the response headers are checked for
             a recommended name. If no filename can be determined, the
             request is aborted.
             It is recommended to provide a file name. 
  --raw      An optional flag to include the raw dataset metadata in the
             exported data.

Exports a dataset to a zip file."""


def export(params):
    """Handles the 'export' operation."""

    dsid = params.get("--dsid", "missing_id")
    filename = params.get("--filename", None)
    raw_mode = params.get("--raw", "false")

    filepath = server.datasets.export(dsid, filename, status_callback=None, raw=raw_mode)
    if filepath is None:
        reportApiError(server, f"Failure attempting to export dataset id '{dsid}'")
    else:
        reportSuccess(server, filepath)


# ---  Clone Operation  ---------------------------------------------
clone_usage = """
Usage:
  datasets clone (--dsid=<dataset-id> | --id=<dataset-id>) --name=<new-dataset-name>

Where:
  --dsid | --id  Either '--dsid' or '--id' is required and identifies the
             dataset to be cloned.
  --name     Required parameter to specify the name of the new dataset.

Clones an existing dataset into a new dataset."""


def clone(params):
    """Handles the 'clone' operation."""

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", "No Name")

    rsp = server.datasets.clone(dsid, name)
    if rsp is None:
        reportApiError(server, "Failure cloning dataset")
    else:
        try:
            clonedId = server.json()["dataset_id"]
        except:
            clonedId = "???"

        reportSuccess(server, f"Successfully cloned dataset with id {dsid} into id {clonedId}")


# ---  Train Operation  ----------------------------------------------
train_usage = """
Usage:
  datasets train (--dsid=<dataset-id> | --id=<dataset_id>) --type=<usage_type>
                 --name=<model_name> [--subtype=<usage-subtype>]
                 [--modelid=<trained-model-id] [--assets=<asset_type>]
                 [--userdnn=<custom_dnn_uuid>] [--hyper=<json_string>]

Where:
  --dsid | --id    Either '--dsid' or '--id' is required and identifies the
              dataset to be trained
   --type     Required parameter identifying the type model to train.
              Possible values are 'cic', 'cod' or 'act'
   --name     Required parameter identifying the name of the model
   --model_id Optional UUID of an existing trained  model on which to
              train.
   --subtype  Optional string to identify the usage specific subtype
              to train for. In the API pubs, this equates to the 'nn_arch'
              property. Values vary by usage and currently only 'cod'
              supports any subtypes. Possible values are
               > frcnn  -- default COD training type if no subtype is 
                           specified
               > tiny_yolo_v2 -- trains using tiny yolo version 2
               > frcnn_mrcnn -- trains with a segmentation capable model
                           This currently uses detectron
               > ssd -- trains for Single Shot Detector. This model also 
                        uses detectron 
   --assets   A comma separated list of asset types to generate during
              training. Asset generation is only available for certain
              model types. If requested on an unsupported model, it will
              be ignored. Currently, the only supported asset that can be
              specified is 'coreml'. The TensorRT asset is automatically
              generated.
   --modelid  Optional parameter to use an already trained model
              as the base model for training. It is the UUID of the trained
              model.
   --userdnn  This parameter is required if training from a user custom
              training model. It is the UUID of the user custom model.
   --hyper    Optional parameter to specify hyper-parameter tuning values for
              the training. This string contains valid JSON with properties
              and values for the parameters that are appropriate to the
              training requested. For example, to set iterations you would
              use `--hyper '{"iterations": 1000}'`.

Initiates training of a model for the dataset."""

strategy_params = f"""
                 [--iterations=<nmbr>] [--ratio=<real>]
                 [--weightdecay=<real>] [--learningrate=<real>]
                 [--momentum=<real>]

   --iterations  Optional parameter indicating the number of iterations
              or epochs to be run
   --ratio    Optional parameter indicating the percentage of images to
              use for training. For example '0.8' indicates 80% of 
              images for training and 20% for test. 
              Value can range from 0.1 to 0.99
   --weightdecay Optional parameter to control the rate of change for weights.
              Value can range from 0.0001 to 0.9999
   --learningrate Optional parameter to control learning adjustments.
              Value can range from 0.001 to 0.999.
   --momentum Optional parameter whose value can range from 0.1 to 0.9.
"""


def train(params):
    """Handles the 'train' operation to train a model from a dataset"""

    dsid = params.get("--dsid", "missing_id")
    name = params.get("--name", None)
    model_type = params.get("--type", None)
    strat_str = params.get("--hyper", None)

    expectedArgs = {
        '--assets': 'generateassets',
        '--modelid': 'pretrained_model',
        '--subtype': 'nn_arch',
        '--userdnn': 'userdnn_id',
        '--hyper': 'strategy'
    }
    kwargs = translate_flags(expectedArgs, params)

    # If --hyper given, must turn it into a json object before adding to kwargs
    if strat_str is not None:
        try:
            strat = json.loads(strat_str)
            kwargs["strategy"] = strat
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid json found in '--hyper' ({strat_str})", file=sys.stderr)
            print(train_usage, file=sys.stderr)
            exit(1)

    if model_type == "cod":
        kwargs["action"] = "create-cod-task"
        if kwargs.get("nn_arch", None) is None:
            kwargs["nn_arch"] = "frcnn"
    elif model_type == "act":
        kwargs["action"] = "create-act-task"
    else:
        kwargs["action"] = "create"

    rsp = server.dl_tasks.create(name, dsid, model_type, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to train dataset '{dsid}'")
    else:
        try:
            taskid = server.json()["task_id"]
        except:
            taskid = "???"
        reportSuccess(server, f"Started training task with id {taskid}")


cmd_usage = f"""
Usage:  datatsets {cli_utils.common_cmd_flags} <operation> [<args>...]

Where:
{cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create  -- creates a new dataset
      list    -- report a list of datasets 
      change  -- change certain metadata attributes of a dataset
      delete  -- delete one or more datasets
      show    -- show a specific dataset
      export  -- export a dataset
      import  -- import an exported dataset
      train   -- train a model based upon a dataset
      clone   -- copy the indicated dataset into a new dataset of the given name

Use 'datasets <operation> --help' for more information on a specific command."""

usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage,
    "train": train_usage,
    "export": export_usage,
    "import": import_usage,
    "clone": clone_usage
}

operation_map = {
    "create": create,
    "list": report,
    "change": update,
    "delete": delete,
    "show": show,
    "train": train,
    "export": export,
    "import": import_dataset,
    "clone": clone
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, id="--dsid", argv=params, cmd_flags=cmd_flags)
    if args is not None:
        try:
            server = vapi.connect_to_server(cli_utils.host_name, cli_utils.token)
        except Exception as e:
            print("Error: Failed to setup server.", file=sys.stderr)
            logger.debug(dict(e))
            return 1

        args.operation(args.op_params)


if __name__ == "__main__":
    main(sys.argv[1:])
