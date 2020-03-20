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


import os
import logging as logger

from paiv.server import Server
from paiv.projects import Projects
from paiv.Datasets import Datasets
from paiv.Files import Files
from paiv.Categories import Categories
from paiv.ObjectTags import ObjectTags
from paiv.Objectlabels import ObjectLabels
from paiv.ActionTags import ActionTags
from paiv.ActionLabels import ActionLabels
from paiv.Dltasks import DlTasks
from paiv.TrainedModels import TrainedModels
from paiv.DeployedModels import DeployedModels
from paiv.InferenceResults import InferenceResults
from paiv.Users import Users


class Base:

    def __init__(self, host=None, token=None, instance=None, log_http_traffic=False):
        # Get required parameters from ENV if not provided on input
        try:
            env_var = "VAPI_HOST"
            if host is None:
                host = os.environ[env_var]
            env_var = "VAPI_TOKEN"
            if token is None:
                token = os.environ[env_var]
        except KeyError:
            msg = F"Could not find environment variable {env_var}"
            logger.error("PAIV:" + msg)
            print(msg + "'\n")
            raise

        # Get optional parameters from ENV if not provided -- fallback to defaults if not present in ENV
        env_var = "VAPI_INSTANCE"
        if instance is None:
            if env_var in os.environ:
                instance = os.environ[env_var]
            else:
                instance = "visual-insights"

        logger.info(F"PAIV: setting up server with host={host}, instance={instance}")

        self.server = Server(host, token, instance, log_http_traffic)
        if self.server is not None:
            self.projects = Projects(self.server)
            self.datasets = Datasets(self.server)
            self.files = Files(self.server)
            self.categories = Categories(self.server)
            self.object_tags = ObjectTags(self.server)
            self.object_labels = ObjectLabels(self.server)
            self.action_tags = ActionTags(self.server)
            self.action_labels = ActionLabels(self.server)
            self.inference_results = InferenceResults(self.server)
            self.dl_tasks = DlTasks(self.server)
            self.trained_models = TrainedModels(self.server)
            self.deployed_models = DeployedModels(self.server)
            self.users = Users(self.server)

    def raw_http_request(self):
        """ Gets the raw HTTP request for the last request that was sent"""
        return self.server.get_raw_req()

    def raw_http_response(self):
        """ Gets the raw response object for the last request that was sent"""
        return self.server.raw_rsp()

    def status_code(self):
        """ Get the status code from the last server request"""
        return self.server.status_code()

    def http_request_str(self):
        """ Gets the HTTP request that generated the current response"""
        return self.server.http_request_str()

    def json(self):
        """ Get the json data from the last server response"""
        return self.server.json()
