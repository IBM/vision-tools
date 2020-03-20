import requests
import json


class paiv(object):
    __version__ = "0.1"
    token = ""
    host = ""
    baseurl = ""
    last_rsp = None

    def __init__(self, host_in, token_in, instance="powerai-vision"):
        self.token = token_in
        self.host = host_in
        self.baseurl = "https://" + self.host + "/" + instance + "/api"
        self.last_rsp = None

        # Disable warning messages about SSL certs
        requests.packages.urllib3.disable_warnings()

    # -------------------------------------------------------------------
    # Helper Methods for HTTP Verbs. Methods are used to front-end
    # the 'requests' methods to add common parameters
    # such as certificate stuff and user authentication
    # information
    def __get(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        self.last_rsp = requests.get(url, verify=False, headers=headers, **kwargs)

        json = None
        if self.last_rsp.status_code == 200:
            json = self.json()
        return json

    def __post(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        self.last_rsp = requests.post(url, verify=False, headers=headers, **kwargs)

        json = None
        if self.last_rsp.status_code == 200:
            json = self.json()
        return json

    def __delete(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        self.last_rsp = requests.delete(url, verify=False, headers=headers, **kwargs)

        json = None
        if self.last_rsp.status_code == 200:
            json = self.json()
        return json

    def __put(self, uri, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = u'%s' % self.token
        url = self.baseurl + uri

        self.last_rsp = requests.put(url, verify=False, headers=headers, **kwargs)

        json = None
        if self.last_rsp.status_code == 200:
            json = self.json()
        return json

    def get_status_code(self):
        """ Get the status code from the last server request"""
        if self.last_rsp is None:
            return None
        return self.last_rsp.status_code

    def get_http_request_str(self):
        """ Gets the HTTP request that generated the current response"""
        if self.last_rsp is None:
            return None
        req = self.last_rsp.request
        msg = '{} {} {{{}}} {}'.format(
            req.method, req.url,
            ','.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            #req.body.decode("utf-8") if req.body is not None else ""
            req.body if req.body is not None else ""
        )
        return msg

    def json(self):
        """ Get the json data from the last server response"""
        try:
            return self.last_rsp.json()
        except:
            return None
 
    def get_project_group_list(self):
        """ Get the list of all project groups"""
        uri = "/projects"
        return self.__get(uri)

    def get_project_group_details(self, pgid):
        """ Get details of one project group"""
        uri = "/projects/" + pgid
        return self.__get(uri)

    def create_project_group(self, name, description=None, enforce_pwf=False, auto_deploy=False):
        """ Create a new project group using the input parameters"""
        uri = "/projects"
        body = {"name": name}
        if description is not None:
            body["description"] = description
        if enforce_pwf is True:
            body["enforce_pwf"] = "true"
        if auto_deploy is True:
            body["auto_deploy"] = "true"

        return self.__post(uri, json=body)

    def change_project_group(self, pgid, **kwargs):
        """ Change a project group using the input parameters"""
        uri = "/projects/" + pgid

        return self.__put(uri, json=kwargs)

    def delete_project_group(self, pgid):
        """ Delete the indicated project group"""
        uri = "/projects/" + pgid
        return self.__delete(uri)

    def set_pwf_policy(self, pgid, policy):
        """Set the indicated project group's pwf policy to the given string value"""
        uri = "/projects/" + pgid
        body = {"enforce_pwf": policy}
        return self.__put(uri, json=body)

    def pg_deploy(self, pgid, modelid="latest", json=None):
        """ Deploys the latest model indicated by 'mid' that is associated with the given pgid"""
        uri = "/projects/" + pgid + "/models/" + modelid + "/deploy"
        return self.__post(uri, json=json)

    def pg_predict(self, pgid, modelid="latest", files=None, params=None):
        """ Deploys the latest model indicated by 'mid' that is associated with the given pgid"""

        uri = "/projects/" + pgid + "/models/" + modelid + "/predict"
        return self.__post(uri, files=files, data=params)

    def pg_get_latest_model(self, pgid, modelid="latest"):
        """ Gets the metadata details for the latest model associated with the given pgid"""
        uri = "/projects/" + pgid + "/models/" + modelid
        return self.__get(uri)

    def pg_download_asset(self, pgid, asset_type="coreml", modelid="latest"):
        """ Downloads indicated asset_type for the latest model associated with the given pgid"""
        pass

    def list_project_group_datasets(self, pgid):
        """ List the datasets associated with the indicated project group"""
        json = self.get_project_group_details(pgid)
        models = None
        if json is not None:
            models = json["datasets"]
        return models

    def get_dataset_details(self, dsid):
        """ Get detail metadata information for the given dataset"""
        uri = "/datasets/" + dsid
        return self.__get(uri)

    def add_dataset_to_project_group(self, dsid, pgid):
        """ add the given dataset to the given project group"""
        uri = "/datasets/" + dsid
        body = {"project_group_id": pgid}
        return self.__put(uri, json=body)

    def remove_dataset_from_project_group(self, dsid):
        """ Clear the project group association for the given dataset"""
        uri = "/datasets/" + dsid
        body = {"project_group_id": ""}
        return self.__put(uri, json=body)

    def list_project_group_models(self, pgid):
        """ list the models associated with the given project group"""
        pg_details = self.get_project_group_details(pgid)
        models = None
        if pg_details is not None:
            models = pg_details["trained_models"]
        return models

    def get_trained_model_details(self, model_id):
        """ Get detailed trained model metadata information for the indicated model"""
        uri = "/trained-models/" + model_id
        return self.__get(uri)

    def add_model_to_project_group(self, model_id, pgid):
        """ Associated the given model with the given project group """
        uri = "/trained-models/" + model_id
        body = {"project_group_id": pgid}
        return self.__put(uri, json=body)

    def remove_model_from_project_group(self, model_id):
        """ Clear the project group association for the given model"""
        uri = "/trained-models/" + model_id
        body = {"project_group_id": ""}
        return self.__put(uri, json=body)

    def set_model_prod_status(self, model_id, status):
        """ Set the Production Status for the given model."""
        uri = "/trained-models/" + model_id
        body = {"production_status": status}
        return self.__put(uri, json=body)

    def change_dataset(self, pgid, **kwargs):
        """ Change fields/attributes of a dataset"""
        uri = "/datasets/" + pgid

        return self.__put(uri, json=kwargs)

    def change_trained_model(self, pgid, **kwargs):
        """ Change fields/attributes of a trained-model"""
        uri = "/trained-models/" + pgid

        return self.__put(uri, json=kwargs)
