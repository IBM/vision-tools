# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2019,2022 IBM International Business Machines Corp.
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

from vapi.server import Server
from vapi.projects import Projects
from vapi.Datasets import Datasets
from vapi.Files import Files
from vapi.FileUserKeys import FileUserKeys
from vapi.FileUserMetadata import FileUserMetadata
from vapi.Categories import Categories
from vapi.ConnectionDevices import ConnectionDevices
from vapi.ObjectTags import ObjectTags
from vapi.Objectlabels import ObjectLabels
from vapi.ActionTags import ActionTags
from vapi.ActionLabels import ActionLabels
from vapi.Dltasks import DlTasks
from vapi.DnnScripts import DnnScripts
from vapi.TrainedModels import TrainedModels
from vapi.DeployedModels import DeployedModels
from vapi.InferenceResults import InferenceResults
from vapi.Users import Users
from vapi.System import System
from vapi.SseMonitor import SseMonitor


class Base:

    def __init__(self, host=None, token=None, instance=None, log_http_traffic=False, base_uri=None):
        # Get required parameters from ENV if not provided on input
        if base_uri is None:
            base_uri = os.getenv("VAPI_BASE_URI")
        if host is None:
            host = os.getenv("VAPI_HOST")
        if base_uri is None and host is None:
            msg = F"Could not find 'VAPI_BASE_URI' information in environment or input parameters"
            logger.error(" MVI:" + msg)
            raise Exception(msg)

        if token is None:
            token = os.getenv("VAPI_TOKEN")

        if base_uri is None:
            # Try to construct the base_uri from VAPI_HOST and VAPI_INSTANCE
            if instance is None:
                instance = os.getenv('VAPI_INSTANCE')
                if instance is None:
                    instance = ""
            base_uri = f"https://{host}/{instance}"

        # Strip trailing slash from URI if present and make sure it ends with "/api"
        if base_uri.endswith("/"):
            base_uri = base_uri[:-1]
        if not base_uri.endswith("/api"):
            base_uri += "/api"

        language = os.getenv("VAPI_LANGUAGE", "en-US")

        logger.info(F"MVI: setting up server '{base_uri}'")

        self.server = Server(base_uri, token, log_http_traffic, language=language)
        if self.server is not None:
            self.projects = Projects(self.server)
            self.datasets = Datasets(self.server)
            self.files = Files(self.server)
            self.file_keys = FileUserKeys(self.server)
            self.file_metadata = FileUserMetadata(self.server)
            self.categories = Categories(self.server)
            self.connection_devices = ConnectionDevices(self.server)
            self.object_tags = ObjectTags(self.server)
            self.object_labels = ObjectLabels(self.server)
            self.action_tags = ActionTags(self.server)
            self.action_labels = ActionLabels(self.server)
            self.inference_results = InferenceResults(self.server)
            self.dl_tasks = DlTasks(self.server)
            self.trained_models = TrainedModels(self.server)
            self.deployed_models = DeployedModels(self.server)
            self.dnnscripts = DnnScripts(self.server)
            self.sseMonitor = SseMonitor(self.server)
            self.users = Users(self.server)
            self.system = System(self.server)

    def raw_http_request(self):
        """ Gets the raw HTTP request for the last request that was sent"""
        return self.server.raw_http_req()

    def raw_http_response(self):
        """ Gets the raw response object for the last request that was sent"""
        return self.server.raw_rsp()

    def status_code(self):
        """ Get the status code from the last server request"""
        return self.server.status_code()

    def rsp_ok(self):
        """ Check for OK status from last server request"""
        return self.server.rsp_ok()

    def http_request_str(self):
        """ Gets the HTTP request that generated the current response"""
        return self.server.http_request_str()

    def json(self):
        """ Get the json data from the last server response"""
        return self.server.json()

    def text(self):
        """ Get response body as a string """
        return self.server.text()
