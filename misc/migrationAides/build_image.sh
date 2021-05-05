#!/bin/bash
# IBM_SOURCE_PROLOG_BEGIN_TAG
# *****************************************************************
#
# IBM Confidential
# OCO Source Materials
#
# (C) Copyright IBM Corp. 2021
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office.
#
# *****************************************************************
# IBM_SOURCE_PROLOG_END_TAG
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
IMAGE_NAME="mvi-migration_${ARCH}"

mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

# Create directory structure
cp -rp "${ROOT_DIR}/cmds" .
mkdir -p ./lib
cp -rp "${ROOT_DIR}/../../lib/vapi/accessors" ./lib

cp -p "${ROOT_DIR}/Dockerfile" .


# Build release package image
docker build -t ${IMAGE_NAME}:${TAG} -f Dockerfile .

docker save ${IMAGE_NAME}:${TAG} > "${IMAGE_NAME}:${TAG}"
cd "${ROOT_DIR}"
