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
import sys
import vapi
import os
import argparse
import json
import textwrap

import vapi_cli.cli_utils
from vapi_cli.cli_utils import show_httpdetail, reportApiError, reportSuccess

if sys.hexversion < 0x03060000:
    sys.exit("Python 3.6 or newer is required to run this program.")

server = None


def extractJson(params):
    json = vars(params)
    json.pop("cmd")
    json.pop("httpdetail")
    json.pop("pgid")
    json.pop("modelid")

    return json


def reportUsageError(msg):
    print(msg, file=sys.stderr)
    exit(1)


def create(params):
    expectedArgs = ["name", "description", "enforce_pwf", "auto_deploy"]
    kwargs = dict(filter(lambda elem: (elem[0] in expectedArgs) and (elem[1] is not None), vars(params).items()))

    rsp = server.projects.create(**kwargs)
    if rsp is None:
        reportApiError(server, "Failure while creating a project group")
    else:
        reportSuccess(server, "Successfully created project group")


def change(params):
    pgid = getattr(params, "pgid", None)

    expectedArgs = ["name", "description", "enforce_pwf", "auto_deploy"]
    kwargs = dict(filter(lambda elem: (elem[0] in expectedArgs) and (elem[1] is not None), vars(params).items()))

    rsp = server.projects.update(pgid, **kwargs)
    if rsp is None:
        reportApiError(server, "Failure attempting to change project group id '{}'".format(pgid))
    else:
        reportSuccess(server, "Changed project group id '{}'".format(pgid))


def delete(params):
    pgid = getattr(params, "pgid", None)
    rsp = server.projects.delete(pgid)
    if rsp is None:
        reportApiError(server, "Failure attempting to delete project group id '{}'".format(pgid))
    else:
        reportSuccess(server, "Deleted project group id '{}'".format(pgid))


def list(params):
    pg = server.projects.report()
    if pg is None:
        reportApiError(server, "Failure attempting to list project groups")
    else:
        reportSuccess(server, None)


def show(params):
    pgid = getattr(params, "pgid", None)
    rsp = server.projects.show(pgid)
    if rsp is None:
        reportApiError(server, "Failure attempting to get project group id '{}'".format(pgid))
    else:
        reportSuccess(server)


def add(params):
    pgid = getattr(params, "pgid", None)
    dsid = getattr(params, "model_id", None)
    modelid = getattr(params, "modelid", None)

    if dsid is None and modelid is None:
        reportUsageError("No dataset id or model id provided during 'add' operation")

    if dsid is not None:
        rsp = server.datasets.update(dsid, project_group_id=pgid)
        id = dsid
        resource = "dataset"
    else:
        rsp = server.trained_models.update(modelid, project_group_id=pgid)
        id = modelid
        resource = "model"

    if rsp is None:
        reportApiError(server, f"Failure attempting to add {resource} id {id} to project group id '{pgid}'")
    else:
        reportSuccess(server, f"Successfully added {resource} id {id} to project group id '{pgid}'")


def remove(params):
    pgid = getattr(params, "pgid", None)
    dsid = getattr(params, "model_id", None)
    modelid = getattr(params, "modelid", None)

    if dsid is None and modelid is None:
        reportUsageError("No dataset id or model id provided during 'remove' operation")

    if dsid is not None:
        rsp = server.datasets.update(dsid, project_group_id="")
        id = dsid
        resource = "dataset"
    else:
        rsp = server.trained_models.update(modelid, project_group_id="")
        id = modelid
        resource = "model"

    if rsp is None:
        reportApiError(server, f"Failure attempting to remove {resource} id {id} from project group id '{pgid}'")
    else:
        reportSuccess(server, f"Successfully removed {resource} id {id} from project group id '{pgid}'")


def deploy(params):
    pgid = getattr(params, "pgid", None)
    modelid = getattr(params, "modelid", "latest")

    rsp = server.projects.deploy(pgid, modelid=modelid)
    if rsp is None:
        reportApiError(server, f"Failed trying to deploy '{modelid}' model for project group {pgid}")
    else:
        reportSuccess(server, f"Successfully deployed '{modelid}' model for project group {pgid}")


# noinspection PyTypeChecker
def predict(params):
    pgid = getattr(params, "pgid", None)
    modelid = getattr(params, "modelid", "latest")
    method = getattr(params, "method", "post")
    try:
        expectedArgs = ["confthre", "containHeatMap", "containRle", "containPolygon",
                        "attrthre", "waitForResults", "genCaption"]
        infParams = dict(filter(lambda elem: (elem[0] in expectedArgs) and (elem[1] is not None),
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


def add_pgid_flag(parser):
    parser.add_argument("--pgid", action="store", dest="pgid", required=True,
                        help="Project Group UUID")


def add_create_change_flags(parser):
    parser.add_argument("--name", action="store",
                        help="Name of the project group")
    parser.add_argument("--description", action="store",
                        help="Description of the project group")
    parser.add_argument("--enforce_pwf", action="store",
                        help="True/False flag indicating if Production Workflow should be enforced")
    parser.add_argument("--auto_deploy", action="store",
                        help="True/False flag indicating  models should be automatically deployed on production status changes")


def add_remove_add_flags(parser):
    add_pgid_flag(parser)
    parser.add_argument("--model_id", action="store",
                        help="dataset id to add/remove to/from the project group")
    parser.add_argument("--modelid", action="store",
                        help="model id to add/remove to/from the project group")


def add_deploy_predict_flags(parser):
    add_pgid_flag(parser)
    parser.add_argument("--latest", action="store_const", dest="modelid", const="latest", default="latest",
                        help="use the most recently trained model associated with this project group.")
    parser.add_argument("--production", action="store_const", dest="modelid", const="production",
                        help="use the most recently trained 'production' model associated with this project group.")
    parser.add_argument("--untested", action="store_const", dest="modelid", const="untested",
                        help="use the most recently trained 'untested' model associated with this project group.")
    parser.add_argument("--modelid", action="store", dest="modelid",
                        help="use this model id (must be associated with the project group")


def add_predict_flags(parser):
    add_deploy_predict_flags(parser)
    parser.add_argument("--post", action="store_const", dest="method", const="post",
                        help="Use POST method for prediction; POST is default")
    parser.add_argument("--get", action="store_const", dest="method", const="get", default="post",
                        help="Use GET method for prediction; POST is default")
    parser.add_argument("--file", action="store", dest="files", required=True,
                        help="path to file if using --post, or URL to file if using --get")
    parser.add_argument("--minconfidence", action="store", dest="confthre",
                        help="minimum confidence (0.0-1.0)")
    parser.add_argument("--heatmap", action="store", dest="containHeatMap", default=None,
                        help="'true' to include heatmap; 'false' to not include ('false' is default)")
    parser.add_argument("--rle", action="store", dest="containRle", default=None,
                        help="'true' to include  bitmap RLE; 'false' to not include ('false' is default)")
    parser.add_argument("--polygon", action="store", dest="containPolygon", default=None,
                        help="'true' to include polygon points; 'false' to not include ('true' is default)")
    parser.add_argument("--nmbrClasses", action="store", dest="clsnum", default=None,
                        help="Number of classes to return for classification; 1 is default")
    parser.add_argument("--waitForResults", action="store", dest="waitForResults", default=None,
                        help="on video inference: 'true' to wait for all results; 'false' to not wait"
                             " ('true' is default)")
    parser.add_argument("--gencaption", action="store", dest="genCaption", default=None,
                        help="on action inference: 'true' to generate captioned video; 'false' to not generate "
                             "('false' is default)")


def get_valid_input(params):
    # Main parser requires subcommand.
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    parser.add_argument('--httpdetail', action="store_true", default=False,
                        help="Flag to get HTTP request detail information")

    # Flags for the create sub-command
    create_parser = subparsers.add_parser('create', help="Create a project group")
    add_create_change_flags(create_parser)

    # Flags for the list sub-command
    list_parser = subparsers.add_parser('list', help="List project groups")

    # Flags for the change sub-command
    change_parser = subparsers.add_parser('change', help="Change attributes of a project group")
    add_create_change_flags(change_parser)
    add_pgid_flag(change_parser)

    # Flags for the delete sub-command
    delete_parser = subparsers.add_parser('delete', help="Delete a project group")
    add_pgid_flag(delete_parser)

    # flags for the show sub-command
    show_parser = subparsers.add_parser('show', help="Show details of a project group")
    add_pgid_flag(show_parser)

    # flags for the add sub-command
    add_parser = subparsers.add_parser('add', help="Add dataset or model to the project group")
    add_remove_add_flags(add_parser)

    # flags for the remove sub-command
    remove_parser = subparsers.add_parser('remove', help="Remove dataset or model from the project group")
    add_remove_add_flags(remove_parser)

    # flags for deploy sub-command
    deploy_parser = subparsers.add_parser('deploy', help="Deploy the latest model")
    add_deploy_predict_flags(deploy_parser)

    # flags for deploy sub-command
    predict_parser = subparsers.add_parser('predict', help="Predict using the latest model")
    add_predict_flags(predict_parser)

    results = parser.parse_args(args=params)
    # print(results)
    return results


def main(params):
    global server

    args = get_valid_input(params)
    if args is not None:
        cli_utils.show_httpdetail = args.httpdetail
        server = paiv.connect_to_server()

        globals()[args.cmd.replace("-", "_")](args)


if __name__ == "__main__":
    main(sys.argv)
