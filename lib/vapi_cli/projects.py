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
  projects create --name=<project-name> [--description=<project-description>]

Where:
  --name    A required parameter that specifies the name of the project group to
            be created.
  --description   An optional parameter that contains the description for
            project group.

Creates a new project group with the given name."""


def create(params):
    """Handles the 'create' operation to create a project group.

    Expected flags in 'params' are translated to Json Field names for creation content
    """
    expectedArgs = {'--name': 'name',
                    '--description': 'description'}

    kwargs = translate_flags(expectedArgs, params)

    rsp = server.projects.create(**kwargs)
    if rsp is None:
        reportApiError(server, "Failure creating a project group.")
    else:
        try:
            pgid = server.json()["project_group_id"]
        except:
            pgid = "???"

        reportSuccess(server, f"Successfully created a project group with id {pgid}")


# ---  Change Operation  ---------------------------------------------
change_usage = """
Usage:
  projects change (--pgid=<project-group-id> | --id=<project-group-id>) [--name=<new-project-name>]
                  [--description=<new-project-description>] [--enforce-pwf=<pwf-status>]
                  [--auto-deploy=<auto-deploy-status]

Where:
  --pgid | --id    Either '--pgid' or '--id' is required and identifies the project group
            to be updated.
  --name    An optional parameter that identifies the new name for the project group.
  --description    An optional parameter that identifies the new description for the project group.
  --enforce-pwf     An optional parameter indicated the desired status of the Production Work Flow strategy.
            Possible values are "true" to turn on PWF or "false" to turn off PWF.
            The value strings are not case sensitive.
  -auto-deploy     An optional parameter indicated the desired status of the auto-deploy strategy.
            Possible values are "true" to turn on auto-deploy or "false" to turn off auto-deploy.
            The value strings are not case sensitive.

Modifies metadata attributes for a given project group."""


def update(params):
    """Handles the 'change' operation for modifying a project group.

    Expected flags in 'params' are translated to Json Field names to identify modifications to be made
    """

    pgid = params.get("--pgid", "missing_id")

    expectedArgs = {'--name': 'project_group_name',
                    '--description': 'description',
                    '--enforce-pwf': 'enforce_pwf',
                    '--auto-deploy': 'auto_deploy'}
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.projects.update(pgid, **kwargs)
    if rsp is None:
        reportApiError(server, f"Failure attempting to modify project group id {pgid}")
    else:
        reportSuccess(server, f"Changed project group id {pgid}")


# ---  Delete Operation  ---------------------------------------------
delete_usage = """
Usage:
  projects delete (--pgid=<project-group-id> | --id=<project-group-id>)

Where:
  --pgid | --id    Either '--pgid' or '--id' is required and identifies the project group
            to be deleted.

Deletes the indicated project group. At this time, only 1 project group can be 
deleted at a time. Note that resources contained in the project group will not be deleted."""


def delete(params):
    """Deletes one project group identified by the --pgid parameter.

    Future work should allow a list of project groups."""

    pgid = params.get("--pgid", "missing_id")
    rsp = server.projects.delete(pgid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to delete project group id {pgid}")
    else:
        reportSuccess(server, f"Deleted project group id '{pgid}'")


# ---  List Operation  -----------------------------------------------
list_usage = """
Usage:
  projects list [--sort=<sort-string>] [--summary]

Where:
  --sort   Comma separated string of project group field names on which to sort.
           Add " DESC" after a field name to change to a descending sort.
           If adding " DESC", the field list must be enclosed in quotes.
  --summary Flag requesting only summary output for each project group returned.

Generates a JSON list of project groups matching the input criteria."""


def report(params):
    """Handles the 'list' operation.
    'params' flags are translated into query-parameter variable names."""

    summaryFields = None
    if params["--summary"]:
        summaryFields = ["_id", "name", "dataset_count", "model_count", "enforce_pwf", "auto_deploy"]

    expectedArgs = {
        '--sort': 'sortby'
    }
    kwargs = translate_flags(expectedArgs, params)

    rsp = server.projects.report(**kwargs)

    if rsp is None:
        reportApiError(server, "Failure attempting to list project groups")
    else:
        reportSuccess(server, None, summaryFields=summaryFields)


# ---  Show Operation  -----------------------------------------------
show_usage = """
Usage:
  projects show (--pgid=<project-group-id> | --id=<project-group-id>)

Where:
  --pgid | --id  Either '--id' or '--pgid' is required and identifies the
            project group to be show.

Shows detail metadata information for the indicated project-group."""


def show(params):
    """Handles the 'show' operation to show details of a single project-group"""

    pgid = params.get("--pgid", "missing_id")
    rsp = server.projects.show(pgid)
    if rsp is None:
        reportApiError(server, f"Failure attempting to get project group id '{pgid}'")
    else:
        reportSuccess(server)


# ---  Add Operation  ------------------------------------------------
add_usage = """
Usage:
  projects add (--pgid=<project-group-id> | --id=<project-group-id>) 
               [(--dsid=<dataset-id> | --modelid=<model-id>)]

Where:
  --pgid | --id    Either '--pgid' or '--id' is required and identifies the project group
            to be updated.
  --dsid | --modelid    Either '--dsid' or '--modelid' is required, but both cannot be specified
            at the same time.
            If '--dsid' is provided, the indicated dataset is added to the project group.
            If '--modelid' is provided, the indicated trained model is added to the project group.
            Only 1 resource can be added at a time.

Adds a single resource (either a dataset or a trained model) to a given project group."""


def add(params):
    pgid = params.get("--pgid", "missing_id")
    dsid = params.get("--dsid", None)
    modelid = params.get("--modelid", None)

    if dsid is None and modelid is None:
        print("No dataset id or model id provided during 'remove' operation.", file=sys.stderr)
        return -1

    if dsid is not None and modelid is not None:
        print("Only one of '--dsid' or '--modelid' can be specified at a time.", file=sys.stderr)
        return -1

    if dsid is not None:
        rsp = server.datasets.update(dsid, project_group_id=pgid)
        id = dsid
        resource = "dataset"
    else:
        rsp = server.trained_models.update(modelid, project_group_id=pgid)
        id = modelid
        resource = "trained model"

    if rsp is None:
        reportApiError(server, f"Failure attempting to add {resource} id {id} to project group id '{pgid}'")
    else:
        reportSuccess(server, f"Successfully added {resource} id {id} to project group id '{pgid}'")


# ---  Remove Operation  --------------------------------------------
remove_usage = """
Usage:
  projects remove (--pgid=<project-group-id> | --id=<project-group-id>) 
               [(--dsid=<dataset-id> | --modelid=<model-id>)]

Where:
  --pgid | --id    Either '--pgid' or '--id' is required and identifies the project group
            to be updated.
  --dsid | --modelid    Either '--dsid' or '--modelid' is required, but both cannot be specified
            at the same time.
            If '--dsid' is provided, the indicated dataset is removed to the project group.
            If '--modelid' is provided, the indicated trained model is removed to the project group.
            Only 1 resource can be removed at a time.

Removes a single resource (either a dataset or a trained model) from a given project group."""


def remove(params):
    pgid = params.get("--pgid", "missing_id")
    dsid = params.get("--dsid", None)
    modelid = params.get("--modelid", None)

    if dsid is None and modelid is None:
        print("No dataset id or model id provided during 'remove' operation.", file=sys.stderr)
        return -1

    if dsid is not None and modelid is not None:
        print("Only one of '--dsid' or '--modelid' can be specified at a time.", file=sys.stderr)
        return -1

    if dsid is not None:
        rsp = server.datasets.update(dsid, project_group_id="")
        id = dsid
        resource = "dataset"
    else:
        rsp = server.trained_models.update(modelid, project_group_id="")
        id = modelid
        resource = "trained model"

    if rsp is None:
        reportApiError(server, f"Failure attempting to remove {resource} id {id} from project group id '{pgid}'")
    else:
        reportSuccess(server, f"Successfully removed {resource} id {id} from project group id '{pgid}'")

#    parser.add_argument("--latest", action="store_const", dest="modelid", const="latest", default="latest",
#                        help="use the most recently trained model associated with this project group.")
#    parser.add_argument("--production", action="store_const", dest="modelid", const="production",
#                        help="use the most recently trained 'production' model associated with this project group.")
#    parser.add_argument("--untested", action="store_const", dest="modelid", const="untested",
#                        help="use the most recently trained 'untested' model associated with this project group.")
#    parser.add_argument("--modelid", action="store", dest="modelid",
#                        help="use this model id (must be associated with the project group")
# ---  Deploy Operation  ---------------------------------------------
deploy_usage = """
Usage:
  projects deploy (--pgid=<project-group-id> | --id=<project-group-id>)
                  [ --latest ] [ --production ] [ --untested ] [ --modelid=<modelid> ]

Where:
  --pgid | --id    Either '--pgid' or '--id' is required and identifies the project group
            with which the model being deployed must be associated.
  --latest  Optional parameter indicating that the most recently trained model associated
            with this project group should be deployed.
  --production  Optional parameter indicating that the most recently trained model that is
            marked as "production" and is associated with this project group should be deployed.
  --untested  Optional parameter indicating that the most recently trained model that is
            marked "untested" (called "unmarked" in the UI) and is associated with this
            project group should be deployed.
  --modelid   Optional parameter identifying the specific model id to deploy. The indicated model
            must be associated with this project group.

Note 1: Only one of '--latest', '--production', '--untested' or '--modelid' can be used.
Note 2: If none of  '--latest', '--production', '--untested' or '--modelid' is used, '--latest' is the default.

Deploys the indicated model for inference purposes."""


def deploy(params):
    pgid = getattr(params, "pgid", "missing-id")
    latest = getattr(params, "latest", False)
    production = getattr(params, "production", False)
    untested = getattr(params, "untested", False)
    modelid = getattr(params, "modelid", None)

    mutually_exclusive_flags_used = 0
    model = "latest"
    if latest:
        mutually_exclusive_flags_used += 1
    if production:
        model = "production"
        mutually_exclusive_flags_used += 1
    if untested:
        model = "untested"
        mutually_exclusive_flags_used += 1
    if modelid is not None:
        model = modelid
        mutually_exclusive_flags_used += 1

    if mutually_exclusive_flags_used > 1:
        print("ERROR: You cannot use more than one of '--latest', '--production', '--untested', or '--modelid'.",
              file=sys.stderr)
        return -1

    rsp = server.projects.deploy(pgid, modelid=model)
    if rsp is None:
        reportApiError(server, f"Failed trying to deploy '{model}' model for project group {pgid}")
    else:
        reportSuccess(server, f"Successfully deployed '{model}' model for project group {pgid}")


# noinspection PyTypeChecker
def predict(params):
    pgid = getattr(params, "pgid", None)
    modelid = getattr(params, "modelid", "latest")
    method = getattr(params, "method", "post")
    try:
        expectedArgs = ["confthre", "containHeatMap", "containRle", "containPolygon",
                        "attrthre", "waitForResults", "genCaption"]
        infParams = dict(filter(lambda item: (item[0] in expectedArgs) and (item[1] is not None),
                                vars(params).items()))
        # print(infParams)

        files = {'files': (params.files, open(params.files, 'rb'))}

        rsp = server.projects.predict(pgid, modelid, infParams)
        if rsp is None:
            reportApiError(server, f"Failed trying to predict with model '{modelid}' for project group {pgid}")
        else:
            reportSuccess(server)
    except IOError as ioe:
        reportUsageError(f"IO Error accessing file {params.files}; errno={ioe.errno}; msg={str(ioe)}\n")
    # except Exception as e:
    #    reportUsageError(server, f"Unexpected error predicting file {params.files}; msg={str(e)}\n")
    #    raise


cmd_usage = f"""
Usage:  projects {cli_utils.common_cmd_flags} <operation> [<args>...]

Where:
{cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      create  -- creates a new project group.
      list    -- report a list of project groups. 
      change  -- change certain attributes of a project group.
      delete  -- delete a project group.
      show    -- show a specific project group.
      add     -- adds a either a dataset or a trained model to a project group.
      remove  -- removes a either a dataset or a trained model from a project group.
      deploy  -- deploys a trained model that is associated with a project group.

Use 'projects <operation> --help' for more information on a specific command."""

usage_stmt = {
    "usage": cmd_usage,
    "create": create_usage,
    "list": list_usage,
    "change": change_usage,
    "delete": delete_usage,
    "show": show_usage,
    "add": add_usage,
    "remove": remove_usage,
    "deploy": deploy_usage
}

operation_map = {
    "create": create,
    "list": report,
    "change": update,
    "delete": delete,
    "show": show,
    "add": add,
    "remove": remove,
    "deploy": deploy
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, id="--pgid", argv=params, cmd_flags=cmd_flags)
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

