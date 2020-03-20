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


class InferenceResults:

    def __init__(self, server):
        self.server = server

    def report(self, **kwargs):
        """ Get a list of all inference results

        :param kwargs  -- query parameters for "GET /inferences" See the API
                          documentation for more information """

        uri = "/inferences"
        return self.server.get(uri, params=kwargs)

    def delete(self, inf_id):
        """ Delete the indicated inference results

        :param inf_id  -- UUID of the targeted inference results"""

        uri = "/inferences/" + inf_id
        return self.server.delete(uri)

    def show(self, inf_id):
        """ Get details of the indicated inference results

        :param inf_id  -- UUID of the targeted inference results"""

        uri = "/inferences/" + inf_id
        return self.server.get(uri)
