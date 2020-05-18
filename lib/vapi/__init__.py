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


# Set default logging handler to avoid "No handler found" warnings.
import logging as logger
from logging import NullHandler

from .base import Base
from .server import Server
from .projects import Projects
from .Datasets import Datasets
from .Files import Files
from .Categories import Categories
from .ObjectTags import ObjectTags
from .Objectlabels import ObjectLabels
from .ActionTags import ActionTags
from .ActionLabels import ActionLabels
from .Dltasks import DlTasks
from .TrainedModels import TrainedModels
from .DeployedModels import DeployedModels
from .InferenceResults import InferenceResults
from .Users import Users


def connect_to_server(host=None, token=None, instance=None, log_http_traffic=False):
    return Base(host, token, instance, log_http_traffic)


logger.getLogger(__name__).addHandler(NullHandler())
