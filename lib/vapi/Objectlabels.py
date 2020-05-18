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


class ObjectLabels:

    def __init__(self, server):
        self.server = server

    def create(self, ds_id, file_id, tag_id, label_info):
        """ Create a new object annotation label.

        :param ds_id   -- UUID of the dataset containing the file to be annotated
        :param file_id -- UUID of the file to be annotated
        :param tag_id  -- UUID of the tag for the annotation
        :param label_info -- fields for the annotation payload. See API documentation
                         for "POST /datasets/<ds_id>/files/<file_id>/object-labels"
                         for more information"""

        uri = f"/datasets/{ds_id}/files/{file_id}/object-labels"
        body = {"tag_id": tag_id}
        body.update(label_info)

        return self.server.post(uri, json=body)

    def report(self, ds_id, file_id=None, **kwargs):
        """ Get a list of all object annotations matching the given criteria

        :param  ds_id   -- UUID of the dataset containing the annotations
        :param  file_id -- UUID of the file containing the annotations
        :param  kwargs -- optional query parameters identifying the criteria.
                          values for keys "file_ids" and "tag_ids" are lists that
                          will be translated into the format required by the API.
                          See the API documentation for
                          "GET /datasets/{ds_id}/object-labels" for more
                          information"""

        # Each of the args that can be lists, must be translated into a comma separated string
        for key in ["tag_ids"]:
            if key in kwargs:
                value = kwargs[key]
                if value is not None and isinstance(value, list) and len(value) > 0:
                    string = ",".join(value)
                    kwargs[key] = string
                else:
                    kwargs.pop(key)

        logger.info(f"report: ds_id={ds_id}, file_id={file_id}")
        if file_id is None:
            uri = "/datasets/" + ds_id + "/object-labels"
        else:
            uri = f"/datasets/{ds_id}/files/{file_id}/object-labels"
        return self.server.get(uri, params=kwargs)

    def update(self, ds_id, label_id=None, file_id=None, **kwargs):
        """ Change an object annotation

        :param ds_id   -- UUID of the dataset containing the annotation
        :param label_id -- UUID of the annotation label to change
        :param file_id  -- UUID of the file with which the annotation is associated"""

        if file_id is not None:
            uri = f"/datasets/{ds_id}/files/{file_id}/object-labels/{label_id}"
        else:
            uri = f"/datasets/{ds_id}/object-labels/{label_id}"
        return self.server.put(uri, json=kwargs)

    def delete(self, ds_id, label_id=None, file_id=None, **kwargs):
        """ Delete the indicated object annotation"""

        if file_id is not None:
            uri = "/datasets/" + ds_id + "/files/" + file_id + "/object-labels"
        else:
            uri = "/datasets/" + ds_id + "/object-labels"
        if label_id is not None:
            uri += "/" + label_id
        return self.server.delete(uri, params=kwargs)

    def show(self, ds_id, label_id, file_id=None):
        """ Get details of the indicated object annotation"""

        if file_id is not None:
            uri = "/datasets/" + ds_id + "/files/" + file_id + "/object-labels/" + label_id
        else:
            uri = "/datasets/" + ds_id + "/object-labels/" + label_id
        return self.server.get(uri)

    def savelabels(self, ds_id, file_id, label_info):
        """ Save a group of labels.

        :param ds_id   -- UUID of the dataset containing the file to be annotated
        :param file_id -- UUID of the file to be annotated
        :param label_info -- fields for the annotation payload. See API documentation
                         for "POST /datasets/<ds_id>/files/<file_id>/object-labels"
                         for more information"""

        uri = "/datasets/" + ds_id + "/files/" + file_id + "/labels"

        return self.server.post(uri, json=label_info)

    def getlabels(self, ds_id, file_id):
        """ Gets labels in "old style" format.

        :param ds_id   -- UUID of the dataset containing the file to be annotated
        :param file_id -- UUID of the file to be annotated
        """

        uri = "/datasets/" + ds_id + "/files/" + file_id + "/labels"

        return self.server.get(uri)
