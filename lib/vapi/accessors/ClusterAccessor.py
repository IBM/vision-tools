# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2021 IBM International Business Machines Corp.
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
import logging
import subprocess
import re


class OcpException(Exception):
    pass


class ClusterAccessor:
    """ Basic cluster access provider. Currently only supports OCP."""

    def __init__(self, standalone=False, clusterUrl=None, user=None, password=None, token=None, project=None):
        self.loggedIn = False
        self.standalone = standalone
        self.clusterUrl = clusterUrl
        self.user = user
        self.password = password
        self.token = token
        self.project = project

    def __enter__(self):
        self.loginToCluster()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        logging.debug(f"ClusterAccessor.__exit__; etype={exception_type}; evalue={exception_value}")
        #self.logoutOfCluster()

    def loginToCluster(self):
        logging.debug(f"logging into cluster; standalone={self.standalone}, cluster='{self.clusterUrl}'")
        if self.standalone:
            return

        if self.clusterUrl is not None:
            cmdArgs = ["oc", "login", "--server", self.clusterUrl]
            if self.token is not None:
                cmdArgs.extend(["--token", self.token])
            else:
                cmdArgs.extend(["--username", self.user, "--password", self.password])
            logging.info(f"logging into cluster '{self.clusterUrl}'")

            process = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                logging.error(f"Failed to login to cluster {cmdArgs}")
                logging.error(f"output = {stderr.decode('utf-8')}")
                raise OcpException(f"Failed to login to cluster {self.clusterUrl}.")

            self.loggedIn = True
            self.setOcpProject()

    def setOcpProject(self):
        cmdArgs = ["oc", "project", self.project]
        logging.debug(f"Setting project to '{self.project}'")

        process = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logging.error(f"Failed to login to cluster {cmdArgs}")
            logging.error(f"output = {stderr.decode('utf-8')}")
            raise OcpException(f"Failed to connect to project {self.project}")

    def logoutOfCluster(self):
        """ Logs out of the OCP cluster if the script performed a login to the cluster."""
        if self.loggedIn:
            cmdArgs = ["oc", "logout"]
            logging.info(f"logging out of cluster '{self.clusterUrl}'")

            process = subprocess.run(cmdArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            logging.debug(stdout.decode('utf-8'))

    def isStandalone(self):
        return self.standalone

    @staticmethod
    def getPods(filterStr):
        logging.debug(f"getPods; filterStr='{filterStr}")
        cmdArgs = ["oc", "get", "pods"]
        pods = []

        process = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
        for line in process.stdout:
            string = line.decode('utf-8')
            logging.debug(string)
            pod = string.split()[0]
            if filterStr:
                if re.search(filterStr, pod):
                    logging.debug(f"matched pod '{string}' (pod={pod}")
                    pods.append(pod)
            else:
                pods.append(pod)
        process.wait()

        return pods


