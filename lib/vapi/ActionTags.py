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


class ActionTags:

    def __init__(self, server):
        self.server = server

    def create(self, ds_id, name, **kwargs):
        """ Create a new action Tag.

         Name is required."""
        uri = "/datasets/" + ds_id + "/action-tags"
        body = {"name": name}
        body.update(kwargs)

        return self.server.post(uri, json=body)

    def report(self, ds_id, **kwargs):
        """ Get a list of all action tags"""

        uri = "/datasets/" + ds_id + "/action-tags"
        return self.server.get(uri, params=kwargs)

    def delete(self, ds_id, tag_id):
        """ Delete the indicated action tag"""

        uri = "/datasets/" + ds_id + "/action-tags/" + tag_id
        return self.server.delete(uri)

    def show(self, ds_id, tag_id):
        """ Get details of the indicated action tag"""

        uri = "/datasets/" + ds_id + "/action-tags/" + tag_id
        return self.server.get(uri)