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


class DeployedModels:

    def __init__(self, server):
        self.server = server

    def create(self, modelid, name, **kwargs):
        """ Deploy a trained model.

        :param modelid -- UUID of the model to deploy
        :param name   -- name for the new datasets
        :param kwargs -- optional fields for the creation payload. See
                        "POST /datasets" API documentation for details"""

        # TODO: figure out how to get to other objects in my package
        model = self.server.get(f"/trained-models/{modelid}")
        if model is None:
            return None

        uri = "/webapis"
        body = {
            "trained_model_id": modelid,
            "name": name if name is not None else model["name"],
            "usage": model["usage"]
        }
        body.update(kwargs)

        return self.server.post(uri, json=body)

    def report(self, **kwargs):
        """ Get a list of all deployed models that meet the given criteria.

        :param kwargs -- query parameters for `/trained-models`"""

        uri = "/webapis/"
        return self.server.get(uri, params=kwargs)


    def delete(self, model_id):
        """ Undeploy the indicated model

        :param model_id -- UUID of the targeted model"""

        uri = f"/webapis/{model_id}"
        return self.server.delete(uri)

    def show(self, model_id):
        """ Get details of the indicated deployed model

        :param model_id -- UUID of the desired model"""

        uri = f"/webapis/{model_id}"
        return self.server.get(uri)

    def infer(self, model_id, filepath, **kwargs):
        """Do basic inference.

        :param model_id  -- id of the deployed model for inferencing
        :param file  -- path to the file to infer
        :param kwargs  -- dictionary containing named parameters to
                          pass for the infernece"""

        uri = f"/dlapis/{model_id}"
        file = {'files': open(filepath, 'rb')}
        return self.server.post(uri, files=file, data=kwargs)
