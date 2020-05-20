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

token_usage = """
Usage:
  users token --user=<user-name> --password=<password>
  
Where:
  --user   Required parameter containing the user login name
  --password  Required parameter containing the user's password
  
Gets an authentication token for the given user"""


# ---  Token Operation  ----------------------------------------------
def token(params):
    """ Handles getting an authentication token for a specific user"""

    user = params.get("--user", None)
    pw = params.get("--password", None)
    rsp = server.users.get_token(user, pw)
    if rsp is None or rsp.get("result", "fail") == "fail":
        reportApiError(server, f"Failed to get token for user '{user}'")
    else:
        reportSuccess(server, rsp["token"])


cmd_usage = f"""
Usage:  users {cli_utils.common_cmd_flags} <operation> [<args>...]

Where:
{cli_utils.common_cmd_flag_descriptions}

   <operation> is required and must be one of:
      token  -- gets an authentication token for the given user

Use 'users <operation> --help' for more information on a specific command."""

usage_stmt = {
    "usage": cmd_usage,
    "token": token_usage
}

operation_map = {
    "token": token
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
