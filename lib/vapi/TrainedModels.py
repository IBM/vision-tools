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


class TrainedModels:

    def __init__(self, server):
        self.server = server

    def report(self, **kwargs):
        """ Get a list of all trained models that meet the given criteria.

        :param kwargs -- query parameters for `/trained-models`"""

        uri = "/trained-models/"
        return self.server.get(uri, params=kwargs)

    def update(self, model_id, **kwargs):
        """ Change metadata of a trained model

        :param model_id -- UUID of the targeted model
        :param kwargs -- optional fields for the update payload. See the API
                         documentation for "PUT /trained-models/{model_id}" for more
                         information"""

        uri = f"/trained-models/{model_id}"
        return self.server.put(uri, json=kwargs)

    def delete(self, model_id):
        """ Delete the indicated trained model (this also deletes the associated dltask object as well)

        :param model_id -- UUID of the targeted model"""

        uri = f"/trained-models/{model_id}"
        return self.server.delete(uri)

    def show(self, model_id):
        """ Get details of the indicated trained model

        :param model_id -- UUID of the desired model"""

        uri = f"/trained-models/{model_id}"
        return self.server.get(uri)

    def action(self, model_id, **kwargs):
        """ performs the requested action on the given trained model

        :param model_id -- UUID of the targeted model
        :param kwargs -- fields for the payload
                        'action=' is required. Other named parameters
                        depend upon the action requested.
                        see '/trained-models/{model_id}/action`
                        documentation for details"""

        uri = "/trained-models/" + model_id + "/action"
        return self.server.get(uri, json=kwargs)

    def import_model(self, file_path):
        """ imports an AI Vision exported trained model zip file

        :param file_path -- directory path to the zip file to import"""

        uri = "/trained-models/import"

        file = {'files': open(file_path, 'rb')}

        return self.server.post(uri, files=file)

    def download_asset(self, model_id, asset_type="unknown", filename=None):
        """ Downloads the indicated asset type from the specified model

        :param  model_id -- UUID of the targeted model
        :param  asset_type -- Type of asset to download (e.g. 'coreml' or 'tensorrt')
        :param  filename -- Name of the file into which the asset is saved. If not provided
                    and it cannot be determined from HTTP response header information,
                    FileNotFoundError will be raised."""

        uri = f"/trained-models/{model_id}/assets/{asset_type}/download"
        logger.debug(F"download_asset: URL={uri}; filename={filename}")

        self.server.get(uri, stream=True)

        if self.server.raw_rsp().ok:
            filename = self.server.save_file(filename)

        return filename

    def export(self, model_id, filename=None, status_callback=None):
        """ exports the indicated model into the specified file

        :param model_id -- UUID of the model to be exported
        :param filename -- name of the file into which the exported model is saved.
                        If no filename is provided, it will be taken from the response
                        header. If no name is present in the header, a FileNotFoundError
                        is raised. It is best to provide a filename
        :param status_callback -- function to be called if progress updates are desired.
                        Status callbacks are made every 50 megabytes saved. Three parameters
                        are provided with the callback
                          - name of the file being saved into
                          - number of callbacks made (starting at 1)
                          - total number of bytes saved so far.

        :return: returns the absolute path of the saved file. """

        uri = f"/trained-models/{model_id}/export"
        logger.debug(F"export: URL={uri}; filename={filename}")

        self.server.get(uri, stream=True)
        if self.server.raw_rsp().ok:
            filename = self.server.save_file(filename, status_callback)

        return filename
