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


class Datasets:

    def __init__(self, server):
        self.server = server

    def create(self, name, **kwargs):
        """ Create a new dataset.

        :param name   -- name for the new datasets
        :param kwargs -- optional fields for the creation payload. See
                        "POST /datasets" API documentation for details"""

        uri = "/datasets"
        body = {"name": name}
        body.update(kwargs)

        return self.server.post(uri, json=body)

    def report(self, **kwargs):
        """ Get a list of all datasets

        :param kwargs  -- query parameters for "GET /datasets" See the API
                          documentation for more information """

        uri = "/datasets"
        return self.server.get(uri, params=kwargs)

    def update(self, dsid, **kwargs):
        """ Change metadata of a dataset

        :param dsid   -- UUID of the targeted dataset
        :param kwargs -- optional fields for the update payload. See the API
                         documentation for "PUT /datasets/{model_id}" for more
                         information"""

        uri = f"/datasets/{dsid}"
        return self.server.put(uri, json=kwargs)

    def delete(self, dsid):
        """ Delete the indicated dataset

        :param dsid  -- UUID of the targeted dataset"""

        uri = f"/datasets/{dsid}"
        return self.server.delete(uri)

    def show(self, dsid):
        """ Get details of the indicated dataset

        :param dsid  -- UUID of the targeted dataset"""

        uri = f"/datasets/{dsid}"
        return self.server.get(uri)

    def import_dataset(self, file_path):
        """ Imports an exported dataset zip file into the server.

        :param file_path -- path to zip file to upload"""

        file = {'files': open(file_path, 'rb')}

        uri = "/datasets/import"
        return self.server.post(uri, files=file)

    def export(self, dsid, filename=None, status_callback=None, raw=False):
        """ exports the indicated dataset into the specified file

        :param dsid   UUID of the dataset to be exported
        :param filename  name of the file into which the dataset is saved.
                        If no filename is provided, it will be taken from the response
                        header. If no name is present in the header, a FileNotFoundError
                        is raised. It is best to provide a filename
        :param status_callback  function to be called if progress updates are desired.
                        Status callbacks are made every 50 megabytes saved. Three parameters
                        are provided with the callback
                          - name of the file being saved into
                          - number of callbacks made (starting at 1)
                          - total number of bytes saved so far.
        :param raw   if True, causes raw metadata DB contents for the dataset to be included.

        :return: returns the absolute path of the saved file. """

        params = {"raw": raw}
        uri = f"/datasets/{dsid}/export"
        logger.debug(F"export: URL={uri}; params={params}; filename={filename}")

        self.server.get(uri, params=params, stream=True)
        if self.server.raw_rsp().ok:
            filename = self.server.save_file(filename, status_callback)
        else:
            filename = None

        return filename

    def clone(self, dsid, name):
        """ Handles creation of dataset clone request.

        :param dsid  UUID of the dataset to clone.
        :param name  name of the new dataset."""

        uri = f"/datasets/{dsid}/action"
        body = {
            "action" : "clone",
            "name": name
        }

        return self.server.post(uri, json=body)
