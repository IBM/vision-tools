#!/usr/bin/env bats
# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2019,2020 IBM International Business Machines Corp.
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

#*************************************************************************
# This file is part of the VAPI tools CLI test bucket. It is a BATS test
# that expects a specific environment that is setup by the `runtests`
# script. It can be run directly from BATS if the following env variables
# are set
#   - BATS_HOME  - root directory of the BATS install (repo)
#   - VAPI_HOST  - test server host name
#   - VAPI_INSTANCE - root URI ("visual-insights" if not set)
#   - VAPI_TOKEN - test server authentication token
#   - VCT_DATA_DIR - VAPI Test bucket data dir (for files to use during testing
#   - VCT_WK_DIR - temp dir to be used as a working directory (must exist)
# This test uses extensions to the base BATS (see 1st to 'load' statments
#*************************************************************************


load "${BATS_HOME}/test/libs/bats-support/load.bash"
load "${BATS_HOME}/test/libs/bats-assert/load.bash"
load "${VCT_DIR}/helpers/test_helpers.bash"

export VCT_DSID_FILE="${VCT_WK_DIR}/$(basename ${BATS_TEST_FILENAME})-dsid"


@test "Files upload to Non-existent Dataset" {
    run vision files upload --ds abc
    assert_failure
    assert_output -p "Usage:"
}


@test "Files upload of Single Image" {
    run vision dataset create --name "vcts-1-image-upload"
    assert_success
    dsid=$(extract_uuid $output)

    run vision files upload --dsid ${dsid} ${VCT_DATA_DIR}/image1.jpg
    assert_success

    # Should validate the file count

    vision dataset delete --dsid ${dsid}
}


@test "Files upload Single Video" {
    run vision dataset create --name "vcts-1-video-upload"
    assert_success
    dsid=$(extract_uuid $output)

    run vision files upload --dsid ${dsid} ${VCT_DATA_DIR}/video1.mp4
    assert_success

    # Should validate the file count

    vision dataset delete --dsid ${dsid}
}


@test "Files upload Mix of Multiple Files" {
    run vision dataset create --name "vcts-mix-multiple-upload"
    assert_success
    dsid=$(extract_uuid $output)

    run vision files upload --dsid ${dsid} ${VCT_DATA_DIR}/video1.mp4 ${VCT_DATA_DIR}/image1.jpg ${VCT_DATA_DIR}/image2.png ${VCT_DATA_DIR}/image3.jpg
    assert_success

    # Should validate the file count

    vision dataset delete --dsid ${dsid}
}


@test "Files upload Zip File" {
    run vision dataset create --name "vcts-zip-upload"
    assert_success
    dsid=$(extract_uuid $output)

    run vision files upload --dsid ${dsid} ${VCT_DATA_DIR}/files.zip
    assert_success

    # Should validate the file count

    vision dataset delete --dsid ${dsid}
}


@test "Files upload coco zip File" {
    skip "Skipping COCO zip file for now"
    run vision dataset create --name "vcts-zip-upload"
    assert_success
    dsid=$(extract_uuid $output)

    run vision files upload --dsid ${dsid} ${VCT_DATA_DIR}/files_coco.zip
    assert_success

    # Should validate the file count

    vision dataset delete --dsid ${dsid}
}
