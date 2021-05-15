# Execution Notes

## Overview
This document starts with how to run the migration by hand using kubectl to kick things off.
It will be modified in the future to make use of the migration controller script when that script is done.
The goal of the migration controller is to hide the kubernetes overhead from the user by providing a single
command to start, monitor, and delete migrations.

## Running Containerized Migration by hand.

#### General Information

The steps below make use of `helm` and `kubectl`. These commands are include in `/opt/ibm/vision/bin`. In
the following instructions, it is assumed that these commands are in your `PATH` environment variable. If
they are not, either add them to your path (preferable) or use absolute paths where the command names are
used below.

Secondly, if you have run the OCP `oc` command on your server, it can change default cluster and cause
`kubectl` to ask for cluster and/or user login information. If you run into this situation, you can either
use the `kubectl.sh` command (also in `/opt/ibm/vision/bin`), or add the local cluster information to the 
kube config data (`~/.kube/config`). Once the local information is added, set the current context to local
(`kubectl config use-context local`). See `/opt/ibm/vision/config/kube.config` for the information
to add to `~/.kube/config`.

#### 1. Download the tar file

The containerized migration tool is available in a tar file that contains all of the pieces to be run.
The tar file is available at TAR_FILE_LOCATION

#### 2. Un-tar the migration tar file.

#### 3. Load the docker image.

The docker image is the file called `mvi-migration_ppc64le:<VERSION_NUMBER>`, where version number is a number
like `1.0.0`. There will be only 1 docker image in the tar file.

Assuming that the current version number, run `docker import mvi-migration_ppc64le:1.0.0`.

#### 4. Setup destination cluster for migration

Change the token expiration from the default to 3 days. Steps to modify the token expiration can be found here: https://docs.openshift.com/container-platform/4.6/authentication/configuring-internal-oauth.html
This change is needed for 2 reasons
 1. The `rsync` can take a long time and potential expire the OCP token before the database migration is done.
 2. The default token does not seem to allow multiple logins from different hosts, and the container will
    appear as a different host.

> TODO Add example yaml and ocp command to change the default token expiration.

Login to the destination cluster's OCP console and request a login token. Save the token for use in the deployment
later.

#### 5. Create and Edit the migration deployment yaml.

A deployment template is included in the tar file, called `migration_deployment_template.yaml`.
Collect the following information for the deployment yaml...
 - **chart name** -- available from `helm list`.
 - **release name** -- available from `helm list`.
 - **image name** -- docker image name loaded in previous step
 - **pvc name** -- available from `kubectl get pvc`
 - **deployment name** -- name of your choosing for the deployment (e.g. `mvi-migration-0501-1`, where `0501-1`
   is the date and an instance number.)
   
Use `sed` to edit the template file into a deployment yaml definition.
```bash
cat migration_deployment_template.yaml | sed -e 's/{{deploymentName}}/mvi-migration-0501-2/g' \
  -e 's/{{chartName}}/ibm-visual-inspection-prod-3.0.0/' \
  -e 's/{{releaseName}}/vision/' \
  -e 's/{{imageName}}/mvi-migration_ppc64le:1.0.0/' \
  -e 's/{{pvcName}}/vision-data-pvc/' > migration_deployment.yaml
```

Collect the following information for the migration...
 - **mongo user name** -- the name of the mongoDB user on the source system (e.g. `admin`).
 - **mongo password** -- the password for the mongoDB user on the source system.
 - **mongo service name** -- the name of the mongoDB service on the source system.
   On standalone systems, this is typically `vision-mongodb`. It can be obtained from `kubectl get services`.
 - **destination cluster URL** -- the URL provided when you get an OCP login token.
 - **destination token** -- the token provided when you get an OCP login token.
 - **destination project** -- the name of the MVI project on the destination cluster.

Edit the new `migration_deployment.yaml` file to change the variables associated with each of the migration
information items listed in the previous paragraph. If desired, the migration type can be change from `full` to 
either `files` or `db`.

#### 6. Apply the deployment

Running `kubectl apply -f migration_deployment.yaml` will start the deployment and the migration container.
All execution parameters have already been specified in the `migration_deployment.yaml` file.

#### 7. Monitor progress.

There are 2 ways to monitor progress.

##### To see detail logging information:
 1. `kubectl get pods | grep migration` to get the migration pod name.  The 1st field is the pod name; copy this value
 2. `kubectl logs <POD-NAME>` will show logs for the migration pod. Note that `<POD-NAME>` should be replaced with the
hame of the migration pod coped from step 1.

The `kubectl logs` command shows the contents of the log at the time it is run. You can use `kubectl logs -f <POD-NAME>` 
to "stream" the pod log and get continual updates.

##### To get progress summary information

If the migration is for a standalone system, it is possible to get migration stage progress information you can
do `ls -lrt /opt/ibm/vision/volume/data/logs/migrations/<DEPLOYMENT_NAME>`. This will provide an ordered list
of the completed and running stages.

If the migration is for a clustered system, run `kubectl exec -it <POD_NAME> -- /usr/local/migration/migmgr.py
--deployment <DEPLOYMENT_NAME> --status`. The `<POD_NAME>` is the pod name as described in getting detailed logging
information above. The `<deploymen_name>` is the same deployment name used in the `migration_deployment.yaml` file.
The output from this command provides the exact same information as listing the directory contents previously
described in this section.

#### 8. Cleanup the deployment.

Use `kubectl delete deployment migration-0506-1` to delete the deployment. This command will also cause an active
deployment to be canceled before it is deleted. Note that `migration-0506-1` should be the actual name of the
deployment. If this name is forgotten you can use `kubectl get deployments` to find it again.
