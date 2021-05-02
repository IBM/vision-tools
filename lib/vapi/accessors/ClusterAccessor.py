import logging
import subprocess


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
        logging.debug(f"__exit__; etype={exception_type}; evalue={exception_value}")
        self.logoutOfCluster()

    def loginToCluster(self):
        if not self.standalone:
            return

        if self.clusterUrl is not None:
            cmdArgs = ["oc", "login", self.clusterUrl]
            if self.token is not None:
                cmdArgs.extend(["--token", self.token])
            else:
                cmdArgs.extend(["--username", self.user, "--password", self.password])
            logging.info(f"logging into cluster '{self.clusterUrl}'")

            process = subprocess.run(cmdArgs, capture_output=True)
            if process.returncode != 0:
                logging.error(f"Failed to login to cluster {cmdArgs}")
                logging.error(f"output = {process.stderr}")
                raise OcpException(f"Failed to login to cluster {self.clusterUrl}.")

            self.loggedIn = True
            self.setOcpProject()

    def setOcpProject(self):
        cmdArgs = ["oc", "project", self.project]
        logging.debug(f"Setting project to '{self.project}'")

        process = subprocess.run(cmdArgs, capture_output=True)
        if process.returncode != 0:
            logging.error(f"Failed to login to cluster {cmdArgs}")
            logging.error(f"output = {process.stderr}")
            raise OcpException(f"Failed to connect to project {self.project}")

    def logoutOfCluster(self):
        """ Logs out of the OCP cluster if the script performed a login to the cluster."""
        if self.loggedIn:
            cmdArgs = ["oc", "logout"]
            logging.info(f"logging out of cluster '{self.clusterUrl}'")

            process = subprocess.run(cmdArgs, capture_output=True)
            logging.debug(process.stdout)

    def isStandalone(self):
        return self.standalone

