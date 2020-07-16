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
import os
import requests
from requests.auth import HTTPDigestAuth


class DnnScripts:

    def __init__(self, server):
        self.server = server

    def create(self, name, inputfile, **kwargs):
        """ Create a new Dnn script.

        :param name   -- name for the new dnn script
        :param kwargs -- optional fields for the creation payload. See
                        "POST /dnn-scripts" API documentation for details"""

        uri = "/dnn-scripts"
        #f = open('/Users/bsmita123/goodCustomFile.zip', 'rb')
        #file = {'files': open('/Users/bsmita123/goodCustomFile.zip', 'rb')}
        #url = "https://aprilmin3.aus.stglabs.ibm.com/visual-insights/api/dnn-scripts"
        #r = requests.post(url, auth=HTTPDigestAuth('admin', 'passw0rd'), files={"archive": ("test.zip", file)})
        #body = {'name': name, 'files': open('/Users/bsmita123/goodCustomFile.zip', 'rb')}
        #print(body)
        #body.update(kwargs)

        #return self.server.post(uri, json=body)
        return self.server.post(uri, files = inputfile, data = {'name': name})

    def report(self, **kwargs):
        """ Get a list of all dnn scripts

        :param kwargs  -- query parameters for "GET /dnn-scripts" See the API
                          documentation for more information """

        uri = "/dnn-scripts"
        return self.server.get(uri, params=kwargs)

    def update(self, dnnid, **kwargs):
        """ Change metadata of a dataset

        :param dnnid   -- UUID of the targeted DNN script
        :param kwargs -- optional fields for the update payload. See the API
                         documentation for "PUT /dnn-scripts/{dnn_id}" for more
                         information"""

        uri = f"/dnn-scripts/{dnnid}"
        return self.server.put(uri, json=kwargs)

    def delete(self, dnnid):
        """ Delete the indicated DNN script

        :param dnnid  -- UUID of the targeted DNN script"""

        uri = f"/dnn-scripts/{dnnid}"
        response = self.server.delete(uri)
        return response

    def show(self, dnnname):
        """ Get details of the indicated Dnn Script

        :param dnnname  -- Name of the targeted DNN script"""

        uri = f"/dnn-scripts/{dnnname}"
        return self.server.get(uri)

