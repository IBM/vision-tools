#!/bin/bash
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
set -ex

ROOT_DIR=$(cd `dirname $0`; pwd)
WORK_DIR="${ROOT_DIR}/build"

usage() {
    echo "Usage: build.sh [-h] [-v string]"
    echo "Description: Builds MVI Migration docker imager. "
    echo "  [-h|--help]       Display this guide"
    echo "  [-t|--tag]        Tag name to assign to container [Default=${TAG}]."
}

while [ $# -gt 0 ]
do
key="$1"

case $key in
    -t|--tag)
    TAG="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help)
    usage
    exit 0
    ;;
    *)    # unknown option
    echo "Unknown option: $key"
    usage
    exit 1
    ;;
esac
done

if [ -z ${TAG} ]
then
    echo "TAG is not defined"
    exit 1
fi

ARCH=$(uname -m)
TAG="${TAG}_${ARCH}"
IMAGE_NAME="bcarl/mvi-migration"

rm -rf "${WORK_DIR}"
mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

# Create directory structure
cp -rp "${ROOT_DIR}/cmds" .
mkdir -p ./lib
cp -rp "${ROOT_DIR}/../../lib/vapi/accessors" ./lib

cp -p "${ROOT_DIR}/Dockerfile" .


# Build release package image
docker build -t ${IMAGE_NAME}:${TAG} -f Dockerfile .

docker save ${IMAGE_NAME}:${TAG} > "mvi-migration:${TAG}"
cd "${ROOT_DIR}"
