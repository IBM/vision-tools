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


class FileUserMetadata:
    """
    Provides access to all APIs related to file user metadata management..
    """

    def __init__(self, server):
        self.server = server

    def add(self, dsid, fileid, kvPairs):
        """ Adds a set of key/value metadata pairs to the specified file.

        :param dsid   -- UUID of the dataset containing the file
        :param fileid -- UUID of the file to which the metadata is to be added
        :param kvPairs  -- python dictionary of key/value pairs"""

        uri = f"/datasets/{dsid}/files/{fileid}/user-metadata"
        return self.server.post(uri, json=kvPairs)

    def delete(self, dsid, fileid, keys):
        """ Deletes the named key/value pairs from the specified file's user metadata.

        :param dsid   -- UUID of the dataset containing the file
        :param fileid -- UUID of the file to which the metadata is to be added
        :param keys   -- list containing key names of metadata to be deleted."""

        uri = f"/datasets/{dsid}/files/{fileid}/user-metadata"
        return self.server.delete(uri, json=keys)

    def report(self, dsid, fileid):
        """ Reports all key/value metadata pairs for the specified file.

        :param dsid   -- UUID of the dataset containing the file
        :param fileid -- UUID of the file to which the metadata is to be added
        :param format -- optional parameter to specify output format (not implemented yet)"""

        uri = f"/datasets/{dsid}/files/{fileid}/user-metadata"
        return self.server.get(uri)

    def show(self, dsid, fileid, key):
        """ Shows the value of a single User Metadata key/value pair

        :param dsid -- UUID of the targeted dataset
        :param fileid -- UUID of the targeted file
        :param  key -- name of the key/value to show"""

        uri = f"/datasets/{dsid}/files/{fileid}/user-metadata/{key}"
        return self.server.get(uri)

    def export(self, dsid, format=None, keys=None, query=None):
        """ "exports" file user metadata across all files in the dataset.

        :param dsid  -- UUID of the target dataset.
        :param format -- optional parameter controlling the format of the export.
        :param keys  -- optional parameter identifying keys to include in the export
        :param query -- optional parameter containing query filter for files to include in the export"""

        qparms = None
        if format is not None:
            qparms["format"] = format
        if keys is not None:
            qparms["keys"] = keys
        if query is not None:
            qparms["query"] = query

        uri = f"/datasets/{dsid}/files/user-metadata"
        self.server.get(uri, params=qparms)
        return self.server.text()
