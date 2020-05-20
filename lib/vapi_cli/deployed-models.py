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
  deployed-models delete (--modelid=<model-id> | --id=<model-id>)

Where:
  --id | --modelid  Either '--id' or '--modelid' is required to identify the
           model to be deleted.

Deletes the indicated model. At this time, only 1 model can be 
deleted at a time."""


def delete(params):
    """Undeploys the model identified by the --modelid parameter."""

    modelid = params.get("--modelid", "missing_id")
    rsp = server.deployed_models.delete(modelid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to undeploy model id '{modelid}'")
    else:
        reportSuccess(server, f"Undeployed model id '{modelid}'")


# ---  List Operation  -----------------------------------------------
list_usage = """
Usage:
  deployed-models list [--sort=<sort_string>] [--summary]

Where:
  --sort   Comma separated string of field names on which to sort.
           Add " DESC" after a field name to change to a descending sort.
           If adding " DESC", the field list must be enclosed in quotes.
  --summary Flag requesting only summary output for each dataset returned

Generates a JSON list of deployed-models."""


def report(params):
    """Handles the 'list' operation.
    'params' flags are translated into query-parameter variable names."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "usage", "status", "nn_arch", "name"]

    expectedArgs = {
        '--sort': 'sortby'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.deployed_models.report(**kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list deployed-models")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Show Operation  -----------------------------------------------
show_usage = """
Usage:
  deployed-models show (--modelid=<model-id> | --id=<model-id>)

Where:
  --id | --modelid  Either '--id' or '--modelid' is required to identify the model to be
            shown.

Shows detail metadata information for the indicated model."""


def show(params):
    """Handles the 'show' operation to show details of a single model"""

    model = params.get("--modelid", "missing_id")
    rsp = server.deployed_models.show(model)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get model id '{model}'")
    else:
        reportSuccess(server)


# ---  Infer Operation   ---------------------------------------------
infer_usage = """
Usage:
  deployed-models infer (--modelid=<model-id> | --id=<mode-id>)
                        [--minconfidence=<min-confidence] [--heatmap=<true_or_false>]
                        [--rle=<true_or_false>]  [--polygons=<true_or_false>]
                        [--maxclasses=<integer>] [--caption=<true_or_false>]
                        [--wait=<true_or_false>] [--annotatefile=<output_file_path>]
                        <path-to-file>

Where:
  --id | --modelid  Either '--id' or '--modelid' is required to identify the deployed
             model to use for inferencing
  --minconfidence Optional parameter indicating the minimum confidence that an 
             inference must meet to be included in the results. This flag applies
             to all inference types. For object and action detection, the threshold
             is applied to each object/action detected.
  --heatmap  Optional True/False flag requesting that the heatmap be included in the
             returned result. The default is False.
             This flag is only relevant when doing classification.
  --rle      Optional True/False flag indicating whether RLE segmentation should be 
             included in the results or not. The default is False.
             This flag is only relevant with a model capable of returning segmenation
             results.
  --polygons Optional True/False flag indicating whether polygon segmentation info
             should be included in the results or not. The default is True.
             This flag is only relevant with a model capable of returning segmentation
             results.
  --maxclasses Optional flag indicating the number of classes that meet the minimum
             confidence level to be included in the results. The default is 1.
             This flag is only relevant to classification models
  --caption  Optional True/False flag indicating whether or not the video should
             be captioned or not. The default is True.
             This flag applies to Action Detection models only.
  --wait     Optional True/False flag indicating that whether the command should 
             wait for the inference results or not. The default is True.
             This flag only applies when inference a video (either for action 
             detection or object detection).
  --annotatefile Optional flag identifying the path where an annotated file should
             be stored. If not supplied, annotated images will not be generated.
             This flag only applies to object detection models.
             At this time, only bounding box annotations are done.
  <path-to-file>     Required parameter to identify the path to the file on which inference
             is to be performed.

Performs inference on the given file. This command will do classification, object
detection, or action detection depending upon the model being used. """


def infer(params):
    """Handles the 'infer' operation to a deployed model"""

    modelid = params.get("--modelid", "missing_id")
    filepath = params.get("<path-to-file>", None)
    annotateFile = params.get("--annotatefile")

    expectedArgs = {
        '--minconfidence': 'confthre',
        '--heatmap': 'containHeatMap',
        '--rle': 'containrle',
        '--polygons': 'containPolygon',
        'maxclasses': 'clsnum',
        'caption': 'genCaption',
        'wait': 'waitForResults'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.deployed_models.infer(modelid, filepath, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure inferring to model id '{modelid}'")
    else:
        reportSuccess(server)


cmd_usage = f"""
Usage:  deployed-models {cli_utils.common_cmd_flags} <operation> [<args>...]

Where:
{cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      list    -- report a list of deployed models
      delete  -- delete one or more deployed models
      show    -- show a specific deployed model
      infer   -- get an inference from a deployed model

Use 'trained-models <operation> --help' for more information on a specific command."""

usage_stmt = {
    "usage": cmd_usage,
    "list": list_usage,
    "delete": delete_usage,
    "show": show_usage,
    "infer": infer_usage
}

operation_map = {
    "list": report,
    "delete": delete,
    "show": show,
    "infer": infer
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

