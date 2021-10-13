# Execution Notes

## Overview

This document describes the steps to perform a migration using 
the migration control script as the interface to the migration.

## Running a Migration using the `migrateMvi.py` Control Script

### 1. Pull the Docker Image

At this time, there is a problem with the deployment definition pulling the docker image. Therefore, the image
must be pulled manually. To pull the image onto the migration source server, run 
`docker pull docker.io/bcarl/mvi-migration:1.0.0_ppc64le`

### 2. Get the `migrateMvi.py` Control Script

This script must be obtained from the `ibm/vision-tools` repo at https://github.com. The repo can either be cloned onto the
migration source server or it can be cloned onto a different computer. If cloned onto a different computer, the
`migrateMvi.py` script must be copied onto the source server to be migrated.

The `migrateMvi.py` script requires Python at version 3.6 or higher. It optionally uses the `Requests` package in
order to check versions of the source and target MVI servers in the migration. This step can be bypassed when the 
source server is a standalone server.

### 3. Set up the Cluster Config File

The cluster config file is a JSON file that contains access information for the migration source and destination
servers. Information for the migration source is different for a standalone server than a cloud based
server. The following information is required for cloud based servers (note that the destination must be a cloud
based server)

 - `clusterUrl` -- The URL for the Open Shift CLI command
 - `clusterProject` -- The project name for the MVI application deployment
 - `clusterToken` -- The Open Shift API token to allow CLI access
 - `mviUrl` -- MVI API URL to validate versions (can be left out for standalone server migrations)

For a standalone source server, the following information is required

 - `mongoUser` -- MVI internal mongoDB server user name.
 - `mongoPw` -- MVI internal mongoDB server password.

An example cluster config file might look like
```json
{
    "destination": {
        "clusterUrl": "https://ocp.cli.cloud.ibm.com:12345",
        "clusterToken": "OCP_LOGIN_TOKEN",
        "clusterProject": "mas-testenv-visualinspection",
    },
    "source": {
        "mongoUser": "admin",
        "mongoPW": "MVI_MONGO_PW"
    }
} 
```
### 4. Start the Migration

To start the migration, use the `migrateMvi.py` script. This script requires the following information
 - _name_ -- a name for the migration passed via the `--name` flag. Each migration should have a unique name
   so that status information can be tracked separately. Uniqueness is not enforced at this time.
 - _clusterConfigInfo_ -- Path to the cluster config file described in Step 3 above. This path can be passed on either the 
   `--config` flag or via the `MVI_MIG_CONFIG` environment variable.
 - _--migrate_ -- identifies the operation to be preformed is a migration operation
 - _migrationScope_ -- specified via one of the following flags
   - **--server** -- to migrate the entire server
   - **--users** -- to migrate one (or more) users. The list of users is a comma separated parameter to the flag.
   - **--projects** -- to migrate one (or more) project groups. The list of project groups is a comma separated parameter to the flag

To start a migration named "_migration-0927-1_" for a single user with id "_janedoe_" use

 > ```migrateMvi.py --name migration-0927-1 --config migConfig.json --migrate --users janedoe```

Note that the `--filesonly` flag can be used to migrate only the filesystem based artifacts.

### 5. Monitor progress

There are 2 ways to monitor progress.

##### To get progress summary information

To get summary information for the sample migration command in Step 4 above, use the command

> ```migrateMvi.py --name migration-0927-1 --cofnig migConfig.json --status```

Note that collection of artifacts can take a few minutes. Migration of file artifacts can take several hours depending on
the size of the server, the scope of the migration, and the bandwidth of the network connection between the two server
environments. Currently, the summary status does not report percentage of files transferred.

##### To see detail logging information:
 1. `/opt/ibm/vision/bin/kubectl.sh get pods | grep <MIGRATION-NAME>` to get the migration pod name.
     The 1st field is the pod name; copy this value
 2. `/opt/ibm/vision/bin/kubectl.sh logs <POD-NAME>` will show logs for the migration pod.
    Note that `<POD-NAME>` should be replaced with the name of the migration pod copied from step 1.

The `/opt/ibm/vision/bin/kubectl.sh logs` command shows the contents of the log at the time it is run. 
You can use `/opt/ibm/vision/bin/kubectl.sh logs -f <POD-NAME>` to "stream" the pod log and get continual updates.
The logs will show the files that are being migrated, so there will be lots of detail.

### 6. Cleanup the deployment

Once the migration completes, the deployment will not automatically be deleted. The deployment must be manually
removed. This removal is done with the command

> ```migrateMvi.py --name migration-0927-1 --cofnig migConfig.json --cleanup```

As long as the deployment exists, the `migrateMvi.py --status` command can be reissued to see times for start and
end of each step. Once the deployment is removed, obtaining summary status will no longer work.

## Additional Information about `migrateMvi.py`

The `migrateMvi.py` script always saves the deployment definition into a JSON file. It is possible to have
this script only create the deployment definition file without applying it to start a migration. This technique
may be needed to facilitate some "special" (unforeseen) "fix-ups" to the deployment definition before it is applied.
Use the following command to only create the deployment definition

> ```migrateMvi.py --name migration-0927-1 --cofnig migConfig.json --createDeployment```

This technique can also be used to allow inspection of the deployment definition before it is applied.
