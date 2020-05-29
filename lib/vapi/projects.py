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


class Projects:

    def __init__(self, server):
        self.server = server

    def create(self, name, **kwargs):
        """ Create a new project group.
         Name is required. All other creation parameters are optional.
         See API documentation for information on other parameters"""

        uri = "/projects"
        body = {"name": name}
        body.update(kwargs)

        return self.server.post(uri, json=body)

    def report(self):
        """ Get a list of all project groups"""

        uri = "/projects"
        return self.server.get(uri)

    def update(self, pgid, **kwargs):
        """ Change a project group"""

        uri = "/projects/" + pgid
        return self.server.put(uri, json=kwargs)

    def delete(self, pgid):
        """ Delete the indicated project group"""

        uri = "/projects/" + pgid
        return self.server.delete(uri)

    def show(self, pgid):
        """ Get details of the indicated project group"""

        uri = "/projects/" + pgid
        return self.server.get(uri)

    def set_pwf_policy(self, pgid, policy):
        """Set the indicated project group's pwf policy to the given value"""

        uri = "/projects/" + pgid
        body = {"enforce_pwf": policy}
        return self.server.put(uri, json=body)

    def deploy(self, pgid, modelid="latest", json=None):
        """ Deploys the latest model indicated by 'mid' that is associated with the indicated project group"""

        uri = "/projects/" + pgid + "/models/" + modelid + "/deploy"
        return self.server.post(uri, json=json)

    def predict(self, pgid, modelid="latest", files=None, params=None):
        """ Deploys the latest model indicated by 'mid' that is associated with the indicated project group"""

        uri = "/projects/" + pgid + "/models/" + modelid + "/predict"
        return self.server.post(uri, files=files, data=params)

    def get_model_info(self, pgid, modelid="latest"):
        """ Gets the metadata details for the latest model associated with the given pgid"""

        uri = "/projects/" + pgid + "/models/" + modelid
        return self.server.get(uri)

    def download_asset(self, pgid, asset_type="coreml", modelid="latest"):
        """ Downloads indicated asset_type for the latest model associated with the given pgid"""

        pass
