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


class Users:

    def __init__(self, server):
        self.server = server

    def get_token(self, user_name, password):
        """ Get an authentication token for the given user.

        :param user_name -- string containing the name of the user.
        :param password -- string containing unencrypted password for the user"""

        uri = f"/tokens"
        payload = {
            'grant_type': 'password',
            'username': user_name,
            'password': password
        }
        return self.server.post(uri, json=payload)
