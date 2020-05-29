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


class DlTasks:
    action_map = {
        "cic": "create-cic-task",
        "cod": "create-cod-task",
        "act": "create-act-task"
    }

    def __init__(self, server):
        self.server = server

    def report(self, **kwargs):
        """ Get a list of all training tasks that meet the given criteria.

        :param kwargs -- query parameters for `/dltasks`"""

        uri = "/dltasks/"
        return self.server.get(uri, params=kwargs)

    def create(self, name, dsid, usage="", **kwargs):
        """ Creates a new training task.

        :param name -- name for the training task
        :param dsid -- id of the dataset to be trained
        :param usage -- type of model to create (cic, cod, or act)
        :param **kwargs -- additional named args for hyper-parameters"""

        action = self.action_map[usage.lower()] if usage.lower() in self.action_map else usage
        uri = "/dltasks/"
        body = {
            'name': name,
            'dataset_id': dsid,
            'usage': usage
        }
        body.update(kwargs)

        return self.server.post(uri, json=body)

    def action(self, task_id, **kwargs):
        """ performs the requested action on the given DLtask

        :param task_id -- UUID of the targeted training task
        :param kwargs -- fields for the payload
                        'action=' is required. Other named parameters
                        depend upon the action requested.
                        see '/dltasks/{task_id}/action`
                        documentation for details"""

        uri = f"/dltasks/{task_id}/action"
        return self.server.get(uri, json=kwargs)

    def delete(self, task_id):
        """ Delete the indicated training task

        :param task_id -- UUID of the targeted training task"""

        uri = f"/dltasks/{task_id}"
        return self.server.delete(uri)

    def show(self, task_id):
        """ Get details of the indicated training task

        :param task_id -- UUID of the desired training task"""

        uri = f"/dltasks/{task_id}"
        return self.server.get(uri)

    def status(self, task_id):
        """ Get training status message for the indicated training task

        :param task_id -- UUID of the desired training task"""

        uri = f"/dltasks/{task_id}/status"
        return self.server.get(uri)
