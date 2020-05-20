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


"""
Module providing output functions for the various Vision Tools commands.
"""
import os
import sys
import json
from types import SimpleNamespace
from vapi_cli.docopt import docopt
import logging as logger

# All of the Vision Tools requires python 3.6 due to format string
# Make the check in a common location
if sys.hexversion < 0x03060000:
    sys.exit("Python 3.6 or newer is required to run this program.")


# Common flag strings
common_cmd_flags = "[--httpdetail] [--jsonoutput] [--host=<host>] [--token=<token>] [--log=<level>]"
common_cmd_flag_descriptions = """   --httpdetail   Causes HTTP message details to be printed to STDERR
                  This information can be useful for debugging purposes or
                  to get the syntax for use with CURL.
   --jsonoutput   Intended to ease use by scripts, all output to STDOUT is in
                  JSON format. By default output to STDOUT is more human
                  friendly
   --host         Identifies the targeted PowerAI Vision server. If not
                  specified here, the VAPI_HOST environment variable is used.
   --token        The authentication token. If not specified here, the
                  VAPI_TOKEN environment variable is used.
   --log          Requests logging at the indicated level. Supported levels are
                  'error', 'warn', 'info', and 'debug'"""

limit_skip_flags = "[--limit=<nmbr>] [--skip=<nmbr>]"
limit_skip_flag_descriptions = """   --limit        Optional parameter to limit the number of returned results.
   --skip         Optional parameter to skip the number of matches before
                  returning results. Limit and Skip can be used to page
                  through results"""

show_httpdetail = False
json_only = False
host_name = None
token = None


def get_valid_input(usage, operation_map, id=None, argv=None, cmd_flags=None):
    """ Processes input parameters and creates namespace for returned results.

    This function can be used with Vision Tools commands that have an 'operation'
    parameter

    The results namespace that is composed of:
        - 'cmd_params': command level parameters object returned from docopt parsing of the
                        command level parameters
        - 'operation': function reference obtained from the `operation_map`
        - 'op_params': operation parameters object returned from docopt parsing of the operation
    Note that output controls are set from this function based upon the command level parameters.

    :param  usage  -- dictionary of usages indexed by operation name
    :param  operation_map  -- dictionary to map input operation name to the name
                   of the function that will service the operation
    :param  id -- optional parameter identifying the args flag to equate with id
    :param  argv -- argument array to process. If none, uses sys.argv
    :param  cmd_flags -- flags passed at the higher level command level (e.g. passed to 'vision')

    :returns result object
                   """

    global host_name
    global token

    #print(f"@@@ argv={argv}", file=sys.stderr)

    cmd_results = docopt(usage["usage"], options_first=True, argv=argv)
    if cmd_flags is not None:
        cmd_results.update(cmd_flags)
    results = SimpleNamespace()
    results.cmd_params = cmd_results
    results.operation = cmd_results["<operation>"]

    #print(f"@@@ cmd_results={cmd_results}", file=sys.stderr)

    host_name = cmd_results["--host"] if "--host" in cmd_results else None
    token = cmd_results["--token"] if "--token" in cmd_results else None

    if operation_map is not None:
        op = cmd_results["<operation>"]
        # handle abbreviated operations
        if op not in operation_map:
            matches = [i for i in operation_map.keys() if i.startswith(op)]
            if len(matches) == 1:
                cmd_results["<operation>"] = matches[0]
            else:
                op = None

        if op is not None:
            results.operation = operation_map[cmd_results["<operation>"]]
            args = cmd_results["<args>"]
            if len(args) > 0:
                args.pop(0)
            nargv = [cmd_results["<operation>"]] + cmd_results["<args>"]
            #nargv = cmd_results["<args>"]
            #print(f"@@@ nargv={nargv}", file=sys.stderr)
            op_results = docopt(usage[cmd_results["<operation>"]], argv=nargv)
            if id is not None:
                # need to ensure that the flag specified in the id parameter is setup to
                # match "-id" flag.
                id_param = op_results.get("--id", None)
                model_param = op_results.get(id, None)
                #print(f"@@@ id_param={id_param}, model_param={model_param} (id={id}", file=sys.stderr)
                if id_param != model_param:
                    if model_param is not None:
                        #print("@@@ using model_param", file=sys.stderr)
                        id_param = model_param
                    op_results["--id"] = id_param
                    op_results[id] = id_param

            results.op_params = op_results
            set_output_controls(cmd_results)

            # Ensure required parameters are present in either input or env vars
            # NOTE: we cannot validate VAPI_TOKEN here because user may be requesting a token.
            try:
                if host_name is None:
                    x = os.environ["VAPI_HOST"]
            except Exception:
                print("ERROR: Missing 'HOST' information.", file=sys.stderr)
                print("       Either use '--host' flag or export 'VAPI_HOST' environment variable.\n",
                      file=sys.stderr)
                print(usage["usage"], file=sys.stderr)
                results = None
        else:
            print("ERROR: Unknown operation -- {:s}".format(results.operation), file=sys.stderr)
            print(usage["usage"], file=sys.stderr)
            results = None
        logger.debug(results)
    return results


def reportApiError(server, msg=None):
    """Reports an API call failure to the user.

    :param server  -- the server object used to make the api call (It contains the last call data)
    :param msg     -- An optional message to precede the error information.

    This method also uses global variables 'scripting' and 'show_httpdetail' to control what output
    is generated."""

    httpstatus = server.status_code()
    httpreq = server.http_request_str()

    try:
        #jsondata = textwrap.indent(json.dumps(server.json(), indent=2), " " * 8)
        jsondata = json.dumps(server.json(), indent=2)
    except:
        jsondata = None

    if not json_only and msg is not None:
        print(msg, file=sys.stderr)
    if server.server.last_failure is not None:
        print(server.server.last_failure, file=sys.stderr)
    if jsondata is not None and jsondata != "null":
        print(jsondata, file=sys.stderr)

    if show_httpdetail:
        print_http_detail(server)

    exit(2)


def reportSuccess(server, msg=None, summaryFields=None):
    """ Shows success message or json output of so requested.

    If not running in "scripting mode", the 'msg' is shown if there is one, and not json is shown. If 'msg'
    is None, json is retrieved from the server object and shown.
    If in "scripting mode", 'msg' is ignored and whatever json is in the server object is shown.

    Detail HTTP exchange information will be shown on STDERR if 'show_httpdetail' is true (useful for debugging)

    :param server  -- the server object used to make the api call (It contains the last call data)
    :param msg     -- An optional message to precede the error information.
    :param summaryFields -- list of fields to pull from json objects. If present, JSON will not be shown.
    """
    try:
        if not json_only:
            if summaryFields is not None:
                cnt = 0
                for item in server.json():
                    cnt += 1
                    values = [item.get(field, "") for field in summaryFields]
                    print("\t".join(str(value) for value in values))
                print(f"{cnt} items")
            elif msg is not None and len(msg) > 0:
                print(msg)

        if json_only or (msg is None and summaryFields is None):
            try:
                jsondata = json.dumps(server.json(), indent=2)
            except:
                jsondata = None
            print(jsondata)

        if show_httpdetail:
            print_http_detail(server)
    except BrokenPipeError:
        pass


def translate_flags(argmap, args):
    """ Translates flags in 'args' using 'argmap' for the new value.
    If 'args' key is not found in 'argmap', it is ignored.
    New dictionary with the translated flags is returned."""
    params = {}
    # Loop through operation results to translate dashes off flags
    if len(args.items()) > 0:
        for (key, value) in args.items():
            if key in argmap and value is not None:
                params[argmap[key]] = value

    return params


def set_output_controls(params):
    """ Sets output control variables for logging out output content.

    Output controls are set by parameter or by ENV variable."""

    global show_httpdetail
    global json_only

    log = params.get("--log", None)
    show_httpdetail = params["--httpdetail"]
    json_only = params["--jsonoutput"]

    if log is not None:
        # Translate log level string to logger values
        log_level = None
        if log.lower() == "error":
            log_level = logger.ERROR
        elif log.lower().startswith("warn"):
            log_level - logger.WARNING
        elif log.lower() == "info":
            log_level = logger.INFO
        elif log.lower() == "debug":
            log_level = logger.DEBUG

        if log_level is not None:
            logger.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)s: %(filename)s-%(funcName)s -- %(message)s',
                               datefmt='%H:%M:%S', level=log_level)

    if not show_httpdetail:
        show_httpdetail = "VAPI_HTTPDETAIL" in os.environ
    if not json_only:
        json_only = "VAPI_JSONONLY" in os.environ


def print_http_detail(server):
    httpstatus = server.status_code()
    httpreq = server.http_request_str()
    print("========   HTTP Detail   ========", file=sys.stderr)
    print("    HTTP status code : {}".format(httpstatus), file=sys.stderr)
    #    print("    HTTP response:", file=sys.stderr)
    #    print(server.raw_http_response().text, file=sys.stderr)
    print("    HTTP request:", file=sys.stderr)
    print(httpreq, file=sys.stderr)
    print("========", file=sys.stderr)
