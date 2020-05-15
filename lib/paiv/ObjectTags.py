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


class ObjectTags:

    def __init__(self, server):
        self.server = server

    def create(self, ds_id, name):
        """ Create a new Object Tag.

        :param  ds_id   -- UUID of the targeted dataset
        :param  name   -- name for the new tag"""

        uri = f"/datasets/{ds_id}/tags"
        body = {"name": name}

        return self.server.post(uri, json=body)

    def report(self, ds_id, **kwargs):
        """ Get a list of all object tags

        :param ds_id  -- UUID for the dataset containing the desired tags"""

        uri = f"/datasets/{ds_id}/tags"
        return self.server.get(uri, params=kwargs)

    def delete(self, ds_id, tag_id):
        """ Delete the indicated object tag

        :param ds_id  -- UUID of the dataset containing the tag
        :param tag_id -- UUID of the tag to delete"""

        uri = f"/datasets/{ds_id}/tags/{tag_id}"
        return self.server.delete(uri)

    def show(self, ds_id, tag_id):
        """ Get details of the indicated object tag

        :param ds_id   -- UUID of the dataset containing the tag
        :param tag_id  -- UUID of the desired tag"""

        uri = f"/datasets/{ds_id}/tags/{tag_id}"
        return self.server.get(uri)

    def update(self, ds_id, tag_id, **kwargs):
        """ updates the specified object tag.

        :param ds_id   -- UUID of the dataset containing the target object tag
        :param tag_id  -- UUID of the object tag to be updated
        :param kwargs  -- dictionary of fields to change
        """

        kwargs["action"] = "update"

        uri = f"/datasets/{ds_id}/tags/{tag_id}/action"
        return self.server.post(uri, json=kwargs)