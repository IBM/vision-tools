# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2020 IBM International Business Machines Corp.
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
import os
import requests
import json


class ConnectionDevices:

    def __init__(self, server):
        self.server = server

    def create(self, connectionInfo):
        """ Create a new Connection device.

        :param connectionInfo   -- payload for the new device connection
                           "POST /connections/devices" API documentation for details"""

        uri = "/connections/devices"

        response = self.server.post(uri, data=connectionInfo)
        return response

    def report(self, **kwargs):
        """ Get a list of all dnn scripts

        :param kwargs  -- query parameters for "GET /connections/devices" See the API
                          documentation for more information """

        uri = "/connections/devices"
        return self.server.get(uri, params=kwargs)

    def update(self, device_name, connectionInfo):
        """ Change metadata of a connection

        :param devicename   -- Device name of the targeted device connection
        :param connectionInfo -- Optional fields for the update payload. See the API
                         documentation for "PUT /connections/devices/{device_name}" for more
                         information"""

        uri = f"/connections/devices/{device_name}"
        rspData = self.server.put(uri, data=connectionInfo)

        return rspData


    def delete(self, device_name):
        """ Delete the connected device

        :param device_name  -- Device name to be deleted"""

        uri = f"/connections/devices/{device_name}"
        response = self.server.delete(uri)
        return response


    def devicestatus(self, device_name):
        """ Checks the status of Device connection

        :param device_name  -- Name of the device"""

        uri = f"/connections/devices/{device_name}/status"
        response = self.server.get(uri)
        print(response)

        return response


    def show(self, device_name):
        """ Get details of the indicated Device Connection

        :param device_name  -- Name of the device connection name"""

        uri = f"/connections/devices/{device_name}"
        return self.server.get(uri)

