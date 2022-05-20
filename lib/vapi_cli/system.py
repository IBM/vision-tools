#!/usr/bin/env python3
# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2022 IBM International Business Machines Corp.
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

info_usage = """
Usage:
  system info

Gets info about the MVI server."""

server = None

# ---  Info Operation  -----------------------------------------------
info_usage = f"""
Usage:  system info

Gets server system information.
"""


def info(params):
    """ Gets MVI System info"""

    rsp = server.system.info()
    if rsp is None or rsp.get("result", "success") != "success":
        reportApiError(server, f"Failed to get system Info.")
    else:
        reportSuccess(server)


# ---  Version Operation  --------------------------------------------
version_usage = f"""
Usage:  system version

Gets server version information. This operation does not require authentication.
"""


def version(params):
    """ Gets MVI System info"""

    rsp = server.system.version()
    if rsp is None or rsp.get("result", "success") != "success":
        reportApiError(server, f"Failed to get system Info.")
    else:
        reportSuccess(server)

cmd_usage = f"""
Usage:  system {cli_utils.common_cmd_flags} <operation> [<args>...]

Where:
{cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      info    -- gets system information
      version -- gets system version information

Use 'system <operation> --help' for more information on a specific command."""

usage_stmt = {
    "usage": cmd_usage,
    "info": info_usage,
    "version": version_usage
}

operation_map = {
    "info": info,
    "version": version
}


def main(params, cmd_flags=None):
    global server

    args = cli_utils.get_valid_input(usage_stmt, operation_map, argv=params, cmd_flags=cmd_flags)
    if args is not None:
        # When requesting a token, we need to ignore any existing token info
        if args.cmd_params["<operation>"] == "token":
            cli_utils.token = ""
        try:
            server = vapi.connect_to_server(cli_utils.host_name, cli_utils.token)
        except Exception as e:
            print("Error: Failed to setup server.", file=sys.stderr)
            logger.debug(e)
            return 1

        args.operation(args.op_params)


if __name__ == "__main__":
    main(None)
