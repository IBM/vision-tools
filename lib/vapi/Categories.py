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


class Categories:

    def __init__(self, server):
        self.server = server

    def create(self, dsid, name, **kwargs):
        """ Create a new category in the given dataset.
         Name is required. All other creation parameters are optional.
         See API documentation for information on other parameters"""

        uri = f"/datasets/{dsid}/categories"
        body = {"name": name}
        body.update(kwargs)

        return self.server.post(uri, json=body)

    def report(self, dsid, **kwargs):
        """ Get the list of all categories in the given dataset"""

        uri = f"/datasets/{dsid}/categories"
        return self.server.get(uri, params=kwargs)

    def delete(self, dsid, cid):
        """ Delete the indicated category from the specified dataset"""

        uri = f"/datasets/{dsid}/categories/{cid}"
        return self.server.delete(uri)

    def show(self, dsid, cid):
        """ Get details of an individual category for the specified dataset"""

        uri = f"/datasets/{dsid}/categories/{cid}"
        return self.server.get(uri)

    def action(self, dsid, cid, **kwargs):
        """ performs the requested action on the given category

        :param dsid -- UUID of the dataset containing the category
        :param cid  -- UUID of the targeted category
        :param kwargs -- fields for the payload
                        'action=' is required. Other named parameters
                        depend upon the action requested.
                        see '/datasets/{model_id}/categories/{cid}/action`
                        documentation for details"""

        uri = f"/datasets/{dsid}/categories/{cid}/action"
        return self.server.post(uri, json=kwargs)
