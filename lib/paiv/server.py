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
import json
import os
import re
import requests
import logging as logger


class Server(object):
    __version__ = "0.1"

    def __init__(self, server_host, auth_token, instance="visual-insights", log_http_traffic=False):
        self.token = auth_token
        self.host = server_host
        self.instance = instance
        self.baseurl = F"https://{self.host}/{instance}/api"
        self.last_rsp = None
        self.last_failure = None
        self.log_http_traffic = log_http_traffic

        # Disable warning messages about SSL certs
        requests.packages.urllib3.disable_warnings()

    def raw_http_req(self):
        """ Gets the raw HTTP request for the last request that was sent"""
        if self.last_rsp is None:
            return None
        return self.last_rsp.request

    def raw_rsp(self):
        """ Gets the raw response object for the last request that was sent"""
        if self.last_rsp is None:
            return None
        return self.last_rsp

    def status_code(self):
        """ Get the status code from the last server request"""
        if self.last_rsp is None:
            return None
        return self.last_rsp.status_code

    def rsp_ok(self):
        """ Safely check if last response was OK"""
        return self.last_rsp is not None and self.raw_rsp().ok

    def http_request_str(self):
        """ Gets the HTTP request that generated the current response"""
        if self.last_rsp is None:
            return None
        req = self.last_rsp.request
        msg = '{} {} {{{}}} {}'.format(
            req.method, req.url,
            ','.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            # req.body.decode("utf-8") if req.body is not None else ""
            req.body if req.body is not None else ""
        )
        return msg

    def text(self):
        """ Gets the raw response data"""
        return self.last_rsp.text

    def json(self):
        """ Get the json data from the last server response"""
        try:
            return self.last_rsp.json()
        except:
            return None

    def save_file(self, filename, status_callback=None):
        """Saves the file being streamed from the previous HTTP operation.

        :param  filename   name of the target file.  If not provided,
                           name is taken from the response headers. If
                           not present there either, FileNotFoundError is raised.
        :param  status_callback  function to call to report retrieval status.
                           Call backs are make every 50 megabytes saved.
                           3 parameters are provided on callbacks --
                             - filename
                             - number of callbacks made (starting with 1)
                             - total bytes saved so far

        Note that if the initial HTTP request failed, ConnectionError is raised."""

        rsp = self.raw_rsp()
        if rsp.ok:
            logger.debug("Waiting for content-info to download")
            if not filename:
                disp = rsp.headers['content-disposition']
                filename = re.findall("filename=(.+)", disp)[0]
                if not filename:
                    raise FileNotFoundError("No filename provided and not found in data stream")

            abspath = os.path.abspath(filename)
            logger.debug(f"saving to {abspath}")

            bytes_saved = 0
            cnt = 0
            chunk = 1024
            interval = 512 * chunk
            with open(filename, 'wb') as handle:
                for block in rsp.iter_content(chunk):
                    handle.write(block)
                    bytes_saved += chunk
                    if bytes_saved % interval == 0:
                        logger.debug(F"saved {bytes_saved} bytes")
                        if status_callback is not None:
                            if bytes_saved % (interval * 100) == 0:
                                cnt += 1
                                status_callback(filename, cnt, bytes_saved)
        else:
            logger.warning(F"Bad response status: status = {self.status_code()}; msg = {self.json()}")
            raise ConnectionError(F"Failed to save HTTP file {filename}")
        return abspath

    # -------------------------------------------------------------------
    # Helper Methods for HTTP Verbs. Methods are used to front-end
    # the 'requests' methods to add common parameters, to save
    # data for future reference, and to return only the JSON content.
    def get(self, uri, headers=None, fileDownload=False, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        if fileDownload is False:
            url = self.baseurl + uri
        else:
            url = f"https://{self.host}/{self.instance}/{uri}"

        try:
            self.last_rsp = requests.get(url, verify=False, headers=headers, **kwargs)
            self.last_failure = None
        except requests.exceptions.ConnectionError as e:
            self.last_rsp = None
            self.last_failure = f"Could not connect to server ({self.host})."
            logger.debug(e)

        jsonData = None
        if not kwargs.get("stream", False):
            if self.rsp_ok():
                jsonData = self.json()
            self.__log_http_messages()
        else:
            # Don't want to wait for whole json response if streaming is True
            logger.debug(f"""streaming detected ({kwargs.get("stream", False)})""")
        return jsonData

    def post(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        try:
            self.last_rsp = requests.post(url, verify=False, headers=headers, **kwargs)
            self.last_failure = None
        except requests.exceptions.ConnectionError as e:
            self.last_rsp = None
            self.last_failure = f"Could not connect to server ({self.host})."
            logger.debug(e)

        self.__log_http_messages()
        jsonData = None
        if self.rsp_ok():
            jsonData = self.json()
        return jsonData

    def delete(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        try:
            self.last_rsp = requests.delete(url, verify=False, headers=headers, **kwargs)
            self.last_failure = None
        except requests.exceptions.ConnectionError:
            self.last_rsp = None
            self.last_failure = f"Could not connect to server ({self.host})."

        self.__log_http_messages()
        jsonData = None
        if self.rsp_ok():
            jsonData = self.json()
        return jsonData

    def put(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        try:
            self.last_rsp = requests.put(url, verify=False, headers=headers, **kwargs)
            self.last_failure = None
        except requests.exceptions.ConnectionError:
            self.last_rsp = None
            self.last_failure = f"Could not connect to server ({self.host})."

        self.__log_http_messages()
        jsonData = None
        if self.rsp_ok():
            jsonData = self.json()
        return jsonData

    def __log_http_messages(self):
        """ Writes both the HTTP request and response messages to the log if traffic logging is turned on"""
        if self.log_http_traffic:
            logger.info(self.http_request_str())
            data = self.json()
            if data is not None:
                logger.info(json.dumps(data, indent=2))
            else:
                logger.info(self.raw_rsp().text)
