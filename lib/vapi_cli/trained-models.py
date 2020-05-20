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

# All of Vision Tools requires python 3.6 due to format string
# Make the check in a common location
if sys.hexversion < 0x03060000:
    sys.exit("Python 3.6 or newer is required to run this program.")

server = None

# ---  Delete Operation  ---------------------------------------------
delete_usage = """
Usage:
  trained-models delete (--modelid=<model-id> | --id=<model-id>)

Where:
  --modelid | --id   A required parameter that identifies the model to be
           deleted.

Deletes the indicated model. At this time, only 1 model can be 
deleted at a time."""


def delete(params):
    """Deletes one model identified by the --modelid parameter.

    Future work should allow a list of trained-models."""

    modelid = params.get("--modelid", "missing_id")
    rsp = server.trained_models.delete(modelid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete model id '{modelid}'")
    else:
        reportSuccess(server, f"Deleted model id '{modelid}'")


# ---  List Operation  -----------------------------------------------
list_usage = """
Usage:
  trained-models list [--usage=<model-type>] [--pgid=<project-group-id>...]
                     [--production_status=<status>] [--sort=<sort_string>]
                     [--summary]

Where:
  --usage  An optional parameter that identifies the type of model to list.
           Possible values are 
             > cic  -- for classification models
             > cod  -- for object detection models
             > act  -- for action detection models
  --pgid   An optional parameter that identifies 1 or more project groups
           on which to filter the list.  Multiple project groups must
           be comma separated
  --production_status An optional parameter to identifies the production
           status by which to filter the list. Possible values
             > production -- for models that have been tested and marked
                             ready for production
             > untested   -- for "freshly" trained models that have not yet
                             been validated.
             > rejected   -- for models that have been deemed "unworthy" of
                             production, but have not been deleted.
  --sort   Comma separated string of field names on which to sort.
           Add " DESC" after a field name to change to a descending sort.
           If adding " DESC", the field list must be enclosed in quotes.
  --summary Flag requesting only summary output for each dataset returned

Generates a JSON list of trained-models matching the input criteria."""


def report(params):
    """Handles the 'list' operation.
    'params' flags are translated into query-parameter variable names."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "usage", "status", "nn_arch", "name"]

    expectedArgs = {
        '--usage': 'usage',
        '--pgid': 'pg_id',
        '--production_status': 'production_status',
        '--sort': 'sortby'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.trained_models.report(**kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list trained-models")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Change Operation  ---------------------------------------------
change_usage = """
Usage:
  trained-models change (--modelid=<model-id> | --id=<model-id>) [--pgid=<project-group-id>]
                        [--prodstatus=<production-status-string]

Where:
  --modelid | --id  A required parameter that identifies the model to be
            changed.
  --pgid    An optional parameter identifying the project group with which
            the model is to be associated. Use an empty string ("") to
            break any project group association.
  --prodstatus Optional parameter identifying the new value for the model's
            production status. Possible values are
              > production
              > untested
              > rejected

Shows detail metadata information for the indicated model.
At the present time, only the project group association can be changed."""


def change(params):
    """Handles the 'change' operation for the indicated model"""

    model = params.get("--modelid", "missing_id")
    expectedArgs = {
        '--pgid': 'pg_id',
        '--prodstatus': 'production_status'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.trained_models.update(model, **kwargs)

    if rsp is None:
        reportApiError(server, f"Failure attempting to change model id '{model}'")
    else:
        reportSuccess(server)


# ---  Show Operation  -----------------------------------------------
show_usage = """
Usage:
  trained-models show (--modelid=<model-id> | --id=<model-id>)

Where:
  --modelid | --id  A required parameter that identifies the model to be
            shown.

Shows detail metadata information for the indicated model."""


def show(params):
    """Handles the 'show' operation to show details of a single model"""

    model = params.get("--modelid", "missing_id")
    rsp = server.trained_models.show(model)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get model id '{model}'")
    else:
        reportSuccess(server)


# ---  Deploy Operation  ---------------------------------------------
deploy_usage = """
Usage:
  trained-models deploy (--modelid=<model-id> | --id=<model-id>) [--name=<name>] [--accel=<accel_type>]
                        [--userdnnid=<user_dnn_UUID]
                        [--dnnscriptid=<dnn_script_UUID]

Where:
  --modelid | --id  Required parameter that identifies the model to deploy.
  --name     Optional parameter indicating the name for the deployed model.
             If not provided, the trained-model name is used.
  --accel    Optional parameter identifying the type of accelerator to use.
             Possible values are
               > GPU -- the default
               > GPU_TENSORRT -- use Tensor RT asset with GPU
               > CPU -- only use CPU
               > FPGA_XFDNN_8_BIT -- only relevant for tiny yolo models
               > FPGA_XFDNN_16_BIT -- only relevant for tiny yolo models
  --userdnnid Optional parameter specifying the UUID of a user supplied
             (custom) DNN to be used
  --dnnscriptid Optional parameter indicating the UUID of a pre/post
             processing DNN that should be loaded with the model.   

Deploys the indicated model for inference purposes."""


def deploy(params):
    """Handles the 'deploy' operation to deploy an inferencing endpoint"""

    model = params.get("--modelid", "missing_id")
    name = params.get("--name", None)
    expectedArgs = {
        '--accel': 'accel_type',
        '--userdnnid': 'userdnn_id',
        '--dnnscriptid': 'dnnscript_id'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.deployed_models.create(model, name, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get model id '{model}'")
    else:
        reportSuccess(server)


# ---  Import Operation  ---------------------------------------------
import_usage = """
Usage:
  trained-models import <file-path>

Where:
  <file-path> Required parameter identifying the path to the zip file to import.
              The file must be an IBM Visual Insights (PowerAI Vision) Model
              export zip file.

Import an exported trained model zip file into the server.."""


def import_model(params):
    """Handles the 'import' operation."""

    filename = params.get("<file-path>", None)

    rsp = server.trained_models.import_model(filename)
    if rsp is None:
        reportApiError(server, "Failure while importing a model.")
    else:
        try:
            modid = server.json()["trained_model_id"]
        except:
            modid = "???"

        reportSuccess(server, f"Successfully imported trained-model with id {modid}.")


# ---  Download_asset Operation  -------------------------------------
download_asset_usage = """
Usage:
  trained-models download-asset (--modelid=<model-id> | --id=<model-id>) --assettype=<asset-type>
                               [--filename=<file-name>]

Where:
  --modelid |--id  A required parameter that identifies the model to deploy.
   --assettype   The name of the asset to download. Currently supported
              asset types are 'coreml' and 'tensorrt'. Note that the asset
              must be created at training time.
  --filename An optional parameter to identify the name of the file into
             which the exported model is saved. It is recommended to 
             supply a name. If none is supplied, the name will be taken
             from the output stream if a name is present. Otherwise
             the export will fail.

Downloads the indicated asset from the indicated model."""


def download_asset(params):
    """Handles downloading the indicated asset from the indicated model"""

    model = params.get("--modelid", "missing_id")
    asset = params.get("--assettype", "unknown_asset")
    filename = params.get("--filename", None)

    rsp = server.trained_models.download_asset(model, asset, filename)
    if rsp is None:
        reportApiError(server, f"Failure attempting to asset '{asset}' for model id '{model}'")
    else:
        reportSuccess(server)


# ---  Export Operation  ---------------------------------------------
export_usage = """
Usage:
  trained-models export (--modelid=<model-id> | --id=<model-id>) [--filename=<file-name>]

Where:
  --modelid | --id  A required parameter that identifies the model to export.
  --filename An optional parameter to identify the name of the file into
             which the exported model is saved. It is recommended to 
             supply a name. If none is supplied, the name will be taken
             from the output stream if a name is present. Otherwise
             the export will fail.

Exports the indicated model to a zip file."""


def export(params):
    """Handles the 'export' operation for the indicated model"""

    model = params.get("--modelid", "missing_id")
    filename = params.get("--filename", None)

    filepath = server.trained_models.export(model, filename, status_callback=None)
    if filepath is None:
        reportApiError(server, f"Failure attempting to export model id '{model}'")
    else:
        reportSuccess(server, filepath)


cmd_usage = f"""
Usage:  trained-models {cli_utils.common_cmd_flags} <operation> [<args>...]

Where:
{cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      list    -- report a list of trained models
      delete  -- delete one or more trained models
      show    -- show a specific trained model
      import  -- import a previously exported trained model.
      deploy  -- deploys a trained model for inferencing purposes.
      download-asset -- downloads the indicated asset for the model
      export  -- exports the indicated model

Use 'trained-models <operation> --help' for more information on a specific command."""

usage_stmt = {
    "usage": cmd_usage,
    "list": list_usage,
    "delete": delete_usage,
    "show": show_usage,
    "change": change_usage,
    "deploy": deploy_usage,
    "download-asset": download_asset_usage,
    "import": import_usage,
    "export": export_usage
}

operation_map = {
    "list": report,
    "delete": delete,
    "show": show,
    "change": change,
    "deploy": deploy,
    "download-asset": download_asset,
    "import": import_model,
    "export": export
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, id="--modelid", argv=params, cmd_flags=cmd_flags)
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
