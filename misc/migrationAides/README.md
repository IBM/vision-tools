# Migration Aides README

## Overview
This directory contains some migration aides for migrating an MVI server.
There are 3 different tools that can be run individually. However, they can be built into a
docker container for easier, potentially consolidated, execution.

See [designNotes.md](https://github.com/IBM/vision-tools/blob/dev/misc/migrationAides/designNotes.md)
for information about the design considerations.

See [runNotes.md](https://github.com/IBM/vision-tools/blob/dev/misc/migrationAides/runNotes.md) for
information on how to perform a migration using the containerized approach.

## How to Build the Migration Container

The following steps will build the MVI migration container.

 1. clone the IBM/vision-tools repo (`git clone git@github.com:IBM/vision-tools.git`)
 2. cd to the migrationAides directory (`cd vision-tools/misc/migrationAides`)
 3. run the `build_image.sh` script (`./build_image.sh -t userId-1`)

The `-t` flag is the docker image tag, it can be any valid docker tag string.
The `build_image.sh` script will create a `build` directory in the current directory,
copy in the necessary files, and then do a `docker build`. Lastly, it will save the newly built docker image
into a file with the name `mvi-migration:userId-`. The docker image file will be in the `build` directory. 

The Dockerfile is set up to support containers for ppc64le and x86_64.