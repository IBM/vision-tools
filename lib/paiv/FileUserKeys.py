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


class FileUserKeys:
    """
    Provides access to all APIs related to file user metadata Key management..
    """

    def __init__(self, server):
        self.server = server

    def create(self, dsid, keyName, **kwargs):
        """ Create a new User file metadata key.

        :param dsid    -- UUID of the dataset to contain the new keyName
        :param keyName -- key name
        :param kwargs  -- optional fields for the creation payload. See
                        "POST /datasets/{DSID}/files/user-keys" API documentation for details"""

        uri = f"/datasets/{dsid}/files/user-keys"
        body = {"name": keyName}
        body.update(kwargs)
        return self.server.post(uri, json=body)

    def report(self, dsid):
        """ Reports all file metadata keys defined/known for the specified dataset.

        :param dsid   -- UUID of the dataset containing the keys"""

        uri = f"/datasets/{dsid}/files/user-keys"
        return self.server.get(uri)

    def delete(self, dsid, keyName):
        """ Deletes the named key from the specified dataset.

        :param dsid    -- UUID of the dataset containing the key
        :param keyName -- name of the key to delete."""

        uri = f"/datasets/{dsid}/files/user-keys/{keyName}"
        return self.server.delete(uri)

    def show(self, dsid, keyName):
        """ Shows the named key's detail information

        :param dsid -- UUID of the targeted dataset
        :param keyName -- name of the key/value to show"""

        uri = f"/datasets/{dsid}/files/user-keys/{keyName}"
        return self.server.get(uri)

    def update(self, dsid, keyName, **kwargs):
        """ Updates fields in the named user file metadata key

        :param dsid -- UUID of the targeted dataset
        :param keyName -- Name of the user file metadata key to update
        :param **kwargs -- optional fields names and values to update."""

        uri = f"/datasets/{dsid}/files/user-keys/{keyName}"
        return self.server.put(uri, json=kwargs)
