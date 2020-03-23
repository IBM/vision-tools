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


#---------------------------------------------------
# Current bgtasks API does not allow getting a single task object.
# This script searches the overall list and extracts the object
# that matches the given ID. If a field name is given, that
# field is extracted from the task document
#
# This script is only meant to be used by the VAPI CLI BATS test env.
# It expects the "regular" test env variables to be set.
#
# usage:  getbginfo.py <task_id>  [<field_name>]
#

import sys
import os
import json
import requests


try:
    requests.packages.urllib3.disable_warnings()

    url = f"""https://{os.environ["VAPI_HOST"]}/{os.environ["VAPI_INSTANCE"]}/api/bgtasks"""
    headers = {'x-auth-token': os.environ["VAPI_TOKEN"]}
    rsp = requests.get(url, verify=False, headers=headers)

    bgDoc = [t for t in rsp.json()["task_list"] if t['_id'] == sys.argv[1]][0]
    if len(sys.argv) == 3:
        print(bgDoc[sys.argv[2]])
    else:
        print(bgDoc)
except Exception as e:
    print("Exception:", e, file=sys.stderr)
    print("argv:", sys.argv, file=sys.stderr)
    print("http_status:", rsp.status_code, file=sys.stderr)
#    print("jsondata:", rsp.json(), file=sys.stderr)
    print("")

