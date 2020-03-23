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


@test "Dataset create missing args" {
    run vision dataset create
    assert_failure
    assert_output -p "Usage:"
}


@test "Dataset delete missing args" {
    run vision dataset delete
    assert_failure
    assert_output -p "Usage:"
}


@test "Delete Non-existent dataset" {
    run vision dataset delete --dsid 123
    assert_failure
    assert_output -p "Failure attempting to delete dataset id"
    assert_output -p "Could not find dataset"
}


@test "Dataset Create" {
    run vision dataset create --name "bats-ds-create"
    assert_success
    assert_output -e "Successfully created dataset with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    #    echo $output | awk '{print $6}' | tr -d "'." >$VCT_DSID_FILE
    extract_uuid $output >$VCT_DSID_FILE
}


@test "Dataset Delete" {
    [ -f ${VCT_DSID_FILE} ] || skip "No dataset id file"
    dsid=$(cat $VCT_DSID_FILE)
    [ -z $dsid ] && skip "No dataset id to delete"

    run vision dataset delete --dsid $dsid
    assert_success
    assert_output -p "Deleted dataset id"
}
