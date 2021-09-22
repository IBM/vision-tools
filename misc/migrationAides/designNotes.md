# Migration Tool Design Notes

## Background and Requirements

The need for a migration tool originates in the transition of IBM Visual Insights to the Maximo Application Suite
(and the new name of Maximo Visual Inspection). This transition required a move from a standalone environment to
an Open Shift (aka OCP) environment. This move meant that there was not an easy way to move the storage from the
standalone environment into the OCP environment.

For most users, this transition can be handled by exporting datasets and models from the standalone 
environment and importing them into the OCP environment. This approach essentially recreates the resource which 
means new IDs are generated. There is a class of users where this approach is not effective. These users are
using the Maximo Visual Inspection App and performing inspections on manufacturing lines.  These users have
lots of data and lots of associations between resources. For these users, a different method is needed.

The following base requirements were brought forth:
 1. There needs to be a method to migrate an entire standalone server into an OCP instance.
 2. The migration must preserve all resource IDs so that all resource associations are maintained.
 3. The migration must allow for the consolidation of multiple standalone servers into a single OCP instance.

### Version 2 Requirements

The primary requirement for version 2 is that migrations must be able to be performed at a level less than
an entire server. All of the previous requirements mentioned above still apply. The level of granularity
for "server subset" migrations are:
 1. User Level
 2. Project Group Level

#### User Level Migrations

A user migration means that all resources (or artifacts) associated with a specific user must be migrated. 
This means all project groups, datasets, trained models, DL tasks (training tasks), custom models, and 
custom DNN scripts. Any deployed models will not be migrated. 

#### Project Group Migrations

A project group migration means that all resources (or artifacts) associated with a specific project group must be
migrated. This means all project groups, datasets, trained models, and DL tasks (training tasks).
Any deployed models will not be migrated.

## High Level Design

MVI holds its resources in two different places -- the local file system and an internal database.
The file system holds the images, videos, and generated models. The database contains the metadata to manage
the resources and associations (e.g. dataset to file associations, object annotations and their association to
files, model to source dataset associations, etc.).

This separation of data lead to using a 2-step approach for the migration; one step for the file system data, and a 
second step for the database.

### General Assumptions/Expectations

 1. The migration tool will perform a migration, not a backup and restore. This expectation means that both the 
    source system and the destination system must be up and running in order to perform the migration.

 2. Resource owner information must be preserved, but user creation is outside the scope of the migration tool.

 3. It should be possible to perform the file migration step without performing the database step. This assumption
    is to facilitate migrating the file system contents before the sever migration is to actually occur. When the actual
    migration is to occur, a smaller file move could be done that would require less time to complete.

 4. It is desirable to minimize the impact on client servers. Therefore, a containerized approach is needed.
    However, it should still be possible to run the individual scripts from a command line if desired and the
    prerequisites are met.

 5. All scripts must at least log to STDERR. This allows all logging to be available via the kubernetes/OCP
    logs facility.

#### Version 2 Changes

Version 2 no longer supports database migrations independent of filesystem migrations. Filesystem data can be
migrated without the database, but the database migration requires the filesystem to be transferred also.

### Filesystem Migration

The file system migration will be done using the `rsync` command. OCP supports using this command to move files
into and out of containers that have `rsync` installed in them. `rsync` provides a nice capability to move files
in an "archive" mode which preserves directory hierarchy, file ownership, and file permissions. Furthermore, `rsync`
will not copy the file again if nothing has changed.  This capability will speed things up if the migration must
be restarted. It also provides the ability to do the filesystem move in 2 stages. The first stage would move
the bulk of the files. The 2nd stage would be done at a later time and `rsync` would only move the modified
files; thus reducing the downtime needed for the migration.

#### Version 2 Changes

For user and project group migrations, the list of filesystem artifacts is generated from database queries.
When possible, whole directories are migrated; but for models, individual files are migrated. For individual
files, `tar` must be used as `rsync` via the `oc` command no longer supports individual files.

### Database Migration

Two primary factors influenced the approach for the database migration
  1. There was a large version change in the mongoDBs when MVI moved into the OCP environment.
  2. There is not an easy way to do a live transfer from one mongoDB to another.

Considering these factors, and the fact that we want control over how to handle duplicate key exceptions, the
database migration is performed by custom scripts (not mongo utilities) and is done in a backup and restore manner.
There will be one script to back up the collections that MVI cares about. The back up script will create a zip
file containing the extracted collections. There wil also be a restore script that will take the back up zip
file and restore it into the target mongoDB.  By using this back up and restore, the issues with mongoDB version
differences are avoided.

The scripts will connect directly to the mongoDB server in the appropriate cluster (standalone or OCP). This means 
that a method to communicate directly with the mongoDB server is required.  This will be accomplished using port
forwarding for the destination OCP cluster. In a containerized environment, the back up script will run inside
the standalone cluster and will therefore have direct access to the mongoDB pod. In the event that the back up
script is run directly, an SSH tunnel can be established to provide direct access to the source mongoDB server.

During the restore, mongodb bulk loads should be used. However, if exceptions occur (e.g. duplicate key exceptions),
the restore tool will fallback to individual document insertions until it has "gotten clear" of the conflicts. Any 
exceptions during individual document exceptions will cause the document to be skipped under the assumption that
it has already been migrated.

### Containerized Execution Management

When run in a containerized environment, there will be a manager script to manage the migration. This manager
script is not intended to be run directly. The individual "worker" scripts described above could be run directly,
the migration manager will not support it.

The manager script will be the command run in the container. It will require parameters be supplied on the 
command line. These parameters will be provided in the deployment yaml definition in the "args" attribute.
The manager script will support a migration type of either "full", "files", or "db" to facilitate running
one of the migration steps without the other.

The migration manager will track status in a subdirectory of the `data/logs` directory. Using this directory will
preserve status. The migration manager should be able to skip steps if they have completed. This goal is due to
the fact that the container will be started in a deployment, which means that if the container dies, the pod will be
restarted. On restart, completed steps should be skipped. This skipping quality needs to have a way to override so
that a rerun of the migration will perform all step (as described above in the description of 2 stage migrations).

The migration manager will provide a method to view status of the migration.

### MVI Migration Controller Script

While it is possible to manually create the deployment and deploy it using `kubectl`; for reliability and ease
of use, a control script should be provided that provides the user interface to the migration facility.
The control script will be run on the standalone server being migrated.  It will collect all information that it
can automatically (e.g. **chartName**, **releaseName**, and**pvcName**).

Additional deployment information will be obtained with command line parameters.
 - **deploymentName** can be generated based upon the migration type.
 - **imageName** can be derived based upon server arch, but a version/tag parameter may be needed.

Actual control of the migration will be provided by command line parameters. These will at least include:
 - _--migrationType_ - "`full`", "`files`", or "`db`"; This will start a migration of the given type.
 - _--status_ - to show migration step status; Requires that a migration deployment be active.
 - _--delete_ - to abort and/or delete the migration deployment; Requires that a migration deployment exist.

The migration control script will load the docker image if it is not already loaded into docker. To facilitate
this step, another command line parameter may be needed to identify the location of the docker image file.

The control script is outside the scope of the initial delivery of the migration facility.

#### Version 2 Changes

In version 2, the controller script hides the yaml deployment work. A network config json file is required to
identify source and destination cluster (or server) information. The control script will provide an option to
output the deployment definition in case there is a need to modify it for special purposes. In this situation,
the user would have to apply the deployment definition manually.

### Migration Deployment

The following migration YAML template will be used by the migration control script.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{deploymentName}}
  labels:
    run: {{deploymentName}}
    app: vision
    chart: {{chartName}}
    release: {{releaseName}}
spec:
  replicas: 1
  template:
    metadata:
      name: {{deploymentName}}
      labels:
        run: {{deploymentName}}
        app: vision
        chart: {{chartName}}
        release: {{releaseName}}
    spec:
      containers:
        - name: {{deploymentName}}
          image: {{imageName}}
          imagePullPolicy: IfNotPresent
          command:
            - "/bin/sh"
            - "-c"
          args:
            - 'touch /tmp/healthy && touch /opt/powerai-vision/data/logs/migration && /usr/local/migration/migmgr PARAMS >&2 && sleep 180'
          volumeMounts:
            - name: dlaas-data
              mountPath: "/opt/powerai-vision/data"
              subPath: data
          resources:
            limits:
              cpu: 0
              memory: 0Mi
          readinessProbe:
            exec:
              command:
                - cat
                - /tmp/healthy
            periodSeconds: 5
      volumes:
        - name: dlaas-data
          persistentVolumeClaim:
            claimName: {{pvcName}}
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: kubernetes.io/arch
                    operator: In
                    values:
                      - ppc64le
                      - amd64
  selector:
    matchLabels:
      run: {{deploymentName}}
```

The following variables must be changed when deploying:

- **deploymentName**  -- the name of the deployment.
- **imageName** -- the name, including the tag, of the docker image containing the migration logic.
- **chartName** -- the name of the helm chart used to instantiate the MVI cluster
- **releaseName** -- the name of the release for the MVI instance in the cluster.
- **pvcName** -- the name of the PVC containing the file system used by MVI to store data

In a standalone environment, the **chartName** and the **releaeName** can be determine vis the `helm` command. The **
pvcName** can be determined from `kubectl get pvcs`.

The **deploymentName** must be unique in the cluster. It will be used to create the working directory used by the
migration manager for tracking status.

The `spec.template.spec.containers[0].args` contains the command string that will start the migration manager script.
The command string must `touch /tmp/healthy` before calling the migration manager so that kubernetes health checks work.
The ending `sleep` is to keep the container around so that logs can be examined.

NOTE: The deployment must be deleted (`kubedtl delete deployment <deploymentName>`) to prevent the migration from being
restarted when the `sleep` completes.

### Packaging

The goal is to have 2 files to perform a migration -- the controller script and the docker image containing the 
migration workers. The docker image will be provided via a docker repository (either Docker Hub and the RedHat Registry).
If the source server has internet access, the controller script will be the only file needed on the source server. 
The deployment definition will identify the docker image and its repository.

## Design Alternatives

### Use a pod instead of a deployment

The difference with using a pod instead of a deployment are
 - a pod will not automatically restart in the event of a failure
 - a pod will go to 'completed' state when it completes.
 - once the pod completes which means that status cannot be obtained, but also that the migration will not
   "accidentally" restart due to a server reboot.

The deployment approach was chosen because it was modeled after the dynamic DNN deployments used for training
and inferring. This approach ensured access to the PVC and services running in the cluster (specifically the
mongoDB service).

### Allow specification of user files to transfer

As currently designed, the migration facility migrates the entire server. This approach is required for the DB, but
for the file system artifacts, we could allow a parameter to identify the user directory(s) to be migrated.

## Future Consideration
l script described above will be considered if the migration facility is enhanced
in the future.

### Use a kubernetes job

This option was presented during review. The initial description appears to provide a good blend of pod and
deployment capabilities. If the migration facility is enchanced in the future, kubernetes job facility 
should be investigated further.