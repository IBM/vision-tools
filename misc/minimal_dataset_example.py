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


def printSummaryInfo(dsList):
    # Show summary information about each dataset

    summaryFields = ["_id", "name", "total_file_count"]
    cnt = 0
    for item in dsList:
        cnt += 1
        values = [item.get(field, "") for field in summaryFields]
        print("\t".join(str(value) for value in values))
    print(f"{cnt} items")


def main(params):
    """Example python script to illustrate minimal use of the vapi library.

    This script will generate a summary list of datasets if no parameters are provided.
    If 1 parameter is given, it is assumed to be a dataset ID and details for that ID will be show.
    More than 2 parameters results in an error.

    :param params:
    """
    try:
        # No parameters to `connect_to_server()` will used VAPI_* env variables
        # This setups the server class, it does not actually maintain a connection
        server = vapi.connect_to_server()
    except Exception as e:
        print("Error: Failed to setup server.", file=sys.stderr)
        logger.debug(dict(e))
        return 2

    if len(params) == 1:
        # Show details about the dataset passed in.
        server.datasets.show(params[0])
        if server.rsp_ok():
            # Pretty print the details
            print(json.dumps(server.json(), indent=2))
        else:
            # Something went wrong. Show the status code.
            # All of visual-inspections failure messages should be in json, so pretty print that
            print(f"Request failed with code {server.status_code()}", file=sys.stderr)
            print(json.dumps(server.json(), indent=2), file=sys.stderr)
            return 2

    elif len(params) == 0:
        # Get a list of all datasets visible to the current user
        server.datasets.report()
        if server.rsp_ok():
            printSummaryInfo(server.json())
        else:
            # Something went wrong. Show the status code.
            # All of visual-inspections failure messages should be in json, so pretty print that
            print(f"Request failed with code {server.status_code()}", file=sys.stderr)
            print(json.dumps(server.json(), indent=2), file=sys.stderr)
            return 2

    else:
        print(f"""ERROR: too many parameters
        USAGE: either
            {sys.argv[0]}              -- to show list of datasets
        or
            {sys.argv[0]} <DatasetId>  -- to show details of one dataset.""", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    main(sys.argv[1:])

