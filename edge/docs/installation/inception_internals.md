# IBM Maximo Visual Inspection Edge Inception Internals

Inception is the process by which MVIE is installed. In the most simple deployments this process reduces user input to 2 commands but for a typical production deployment several other steps will be required. There are also a number of non-default configurations that cannot be changed from the UI. This document presents the basic inception process and additional changes that might be desired in different scenarios.

## Inception Basics

>**Note** MVI Edge is officially supported on x86 and PPCLE servers running Ubuntu or RedHat Enterprise Linux, but it can be run on any platform that supports a linux shell and docker. For information on unsupported platforms, see the [Unsupported Platforms](#Unsupported-Platforms) section *after* reading this section.
<details>
  <summary>Click to expand</summary>

In the simplest case, MVIE is installed as follows:
1. The [Installation pre-requisites](https://www.ibm.com/docs/en/maximo-vi/8.3.0?topic=edge-planning) are provided
2. User selects an `<install root>` directory where they want to install MVIE. This directory must be created before proceeding with the inception process. 
>The final directory name in the path must be `vision-edge`. EG `/opt/ibm/vision-edge`.

3. User logs in to the Docker repository.

   1. An IBM Cloud Entitlement Key is required. This can be obtained by logging in to https://myibm.ibm.com/products-services/containerlibrary and copying the entitlement key.
   2. Login to the docker repository
      ```
      docker login cp.icr.io --username cp --password <entitlement key>
      ```
      > the user name must be `cp` and the `<entitlement key>` is the one copied in step 3.1 above

4. User `cd`'s to the `<install root>` and executes the `docker run` command:
    ```
    cd <install root>

    For version 8.3.0
      docker run --rm -v `pwd`:/opt/ibm/vision-edge --privileged -u root cp.icr.io/cp/visualinspection/vision-edge-inception:8.3.0
  
    For version 8.4.0
      docker run --rm -v `pwd`:/opt/ibm/vision-edge -e hostname=`hostname -f` --privileged -u root cp.icr.io/cp/visualinspection/vision-edge-inception:8.4.0
  
     For version 8.5.0
      docker run --rm -v `pwd`:/opt/ibm/vision-edge -e hostname=`hostname -f` --privileged -u root cp.icr.io/cp/visualinspection/vision-edge-inception:8.5.0
    ```
    - This will pull the inception image and run it.
    - The inception container will 
      - create the required sub-directories under the \<install root> with the required ownership and permissions.
        > The userid and groupid are the ones that are used internally by all the MVIE Service containers. These will be 900:9999. Within the containers the user and group names are both `visionedge`. A common practice is to create the `visionedge` user and group in the host os so owner and group are displayed in a more user-friendly manner. If this is done, the user *must* have the userid `900` and the group *must* have the groupid `9999`
      - populate sub-directories with scripts, templates, and properties files

5. User runs the startedge.sh script
    ```
    ./startedge.sh
    ```
    - This will:
      - display the license agreement, which the user must accept to continue
      - pull the 3 MVIE service images
      - generate certificates for the server
      - initialize the database
      - start the 3 service containers:
        - vision-edge-controller
        - vision-edge-cme
        - vision-edge-dle
> **NOTE** The startedge.sh script can be run at any time to restart the MVIE service containers. This is required whenever changes to the default configuration are made.

The system is now up and running. 

The startedge.sh script will display the URL to access the Web UI. To login, the default userid and password are `masadmin` and `VisionP@ssw0rd`.
</details>
   
## Operational Considerations
<details>
  <summary>Click to expand</summary>
**Pre-Install**
- Storage configuration
  - When run at the full capacity, an MVIE system will produce significant volumes of image files and metadata. This volume will be determined by the compute resources available on the system so there is no single storage configuration that can be recommended for all deployments, but the following are general recommendations for storage layout:
    - The MVIE `<install root>` should be located on a different storage volume than the one that docker will use. EG docker typically stores things under `/var` so the MVIE root should be located in a different volume.
    - The database directories (`<install root>/volume/run/psdata`, `<install root>/volume/run/pstbspc`, and `<install root>/volume/run/pgbackrest`) should be located on different volumes to prevent a single storage device failure from affecting both transactional data and database backups

**Pre or Post Install**
- Log File Rotation
  - MVIE containers do not write separate log files. Instead, all logging goes to the docker container logs and in production these can become quite large. The recommendation is to enable docker log file rotation as follows:
    - Create or edit the /etc/docker/daemon.json file
    - Insert the following (modify the number of files - `max-file` as desired)
    ```
    {
        "log-driver": "json-file",
        "log-opts": {
            "max-size": "10m",
            "max-file": "20"
        }
    }
    ```
    - Restart the docker daemon `systemctl docker restart`
</details>
   
## Non-default Configurations
<details>
  <summary>Click to expand</summary>

The basic flow of configuration settings is from the `<install root>/volume/run/var/config/vision-edge.properties` file to the startedge.sh script to the service containers. Property settings in the properties file are available to the startedge.sh script and may be passed as environment variables in the docker  run commands that start the containers. 

> NOTE Modifications to the `<install root>/volume/run/var/config/vision-edge.properties` and `<install root>/volume/run/var/config/controller.json` files will also be picked up directly by the vision-edge-controller container but can be overridden by environment variables passed to the container in the startedge.sh script.

Any time a modification is made to any of the configuration files, the startedge.sh script should be run to restart the containers so they will pick up the new settings.
### Logging Levels
Logging levels can be changed to increase or decrease the detail of information written to the service container logs. 

Logging levels are specified in the `<install root>/volume/run/var/config/vision-edge.properties` as:
|Variable|Description|
|-|-|
|CONTROLLER_LOG_LEVEL|Sets the vision-edge-controller container's logging level|
|CME_LOG_LEVEL|Sets the vision-edge-cme container's logging level|
|DLE_LOG_LEVEL|Sets the vision-edge-dle container's logging level|

The valid logging levels are:
|Setting|Description|
|-|-|
|TRACE|This is the most verbose logging level, probably only useful to developers working on the product or in extreme cases where troubleshooting at DEBUG level is not providing enough detail.
|DEBUG|Output detailed debugging log messages. This should only be used when troubleshooting the system or when detailed logging is desired when performing development or system integration activity. This level will create very large log files quickly and should not be enabled for extensive periods in production. Setting log file rotation is highly recommended to avoid running out of disk space.
|INFO|This is the default and provides a level of information suitable for a stable system
|WARN|This level provides information that is of special significance, either non-fatal errors or events such as ancillary services being started or stopped. It is suitable for a stable production system.
|ERROR|This level provides information when internal errors occur that may impact the functionality of the system.
|PANIC|This level provides information when events that would normally cause a system crash occur. The MVIE containers implement panic recovery where possible, so the system processes should restart automatically but whenever events of this severity occur, they should be addressed.

### Development Mode
Setting `DEVMODE=true` in the `<install root>/volume/run/var/config/vision-edge.properties` will start the vision-edge-controller container in development mode. When started in this mode:
- By default the UI will not allow deployment of models locally on systems with no GPU. In Development mode, models can be deployed locally when the system has no GPU.
  >**Note** The DLE container must be started in CPU Mode to deploy models with no GPU.
- Swagger documentation for the controller's REST API is enabled at https://`<host name>`/swagger/index.html
- Additional configuration info is displayed in the controller logs (DEBUG logging level must also be enabled). Since the controller gets configuration information from (in order of decreasing precedence):
  - environment variables set in the docker run command for the controller in the startedge.sh script
  - the vision-edge.properties file
  - the controller.json file
  - default values

  it can be useful to see it all in one place and to see which setting has taken precedence when the container is started.
  
  The complete set of configuration entries is output to the log file as a line of comma-separated values which indicate:

  - variable name
  - variable type 
  - effective value 
  - true if set in a configuration file
  - true if setting equals the default value

### CPU Mode - Local Inference with No GPU
By default, the vision-edge-dle container will not process inferences if there is no GPU on the edge node. Enabling CPU Mode will allow the DLE to run models on the CPU, which will run much slower than on GPU.
 To enable CPU Mode, set `DLE_ENABLE_CPU_FALLBACK=TRUE` in the vision-edge.properties file.
> **Note** the controller must be started in Development Mode to allow models to be deployed from the UI in CPU Mode.
</details>

## Unsupported Platforms
<details>
  <summary>Click to expand</summary>
As documented in the [Inception Basics](#Inception-Basics) section above, the installation of MVI Edge is a process of running the inception image as a "run-once" docker container that sets up the environment, and running the `startedge.sh` script to complete the installation. Any platform that can support docker and a linux shell to run the script are suitable for installation.

However, there are deltas from the standard installation procedure for different platforms. The deltas for the most common are documented separately:

- [MacOS](MacOS.md)
- [Windows](Windows.md)
- [NVIDIA Jetson](NVIDIA_Jetson.md)
</details>
