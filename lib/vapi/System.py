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


class System:

    def __init__(self, server):
        self.server = server

    def dvc_info(self):
        """ Get MVI system device info"""

        uri = f"/system/device-info"
        return self.server.get(uri)

    def info(self):
        """ Get MVI system info"""

        uri = f"/system"
        return self.server.get(uri)

    def version(self):
        """ Get MVI version info"""

        uri = f"/version-info"
        return self.server.get(uri)

