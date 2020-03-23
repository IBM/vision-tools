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
load "${VCT_DIR}/helpers/test_helpers"

export BATS_TEST_FILE_BASENAME=$(basename ${BATS_TEST_FILENAME})
export VCT_DSID_FILE="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}-dsids"
export VCTLOG="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}.log"


@test "Dataset import Missing Args" {
    run vision dataset import
    assert_failure
    assert_output -p "Usage:"
}


@test "Dataset export Missing Args" {
    run vision dataset export
    assert_failure
    assert_output -p "Usage:"
}


@test "Dataset export Non-Existent Dataset" {
    run vision dataset export --dsid 123
    assert_failure
    assert_output -p "Failure attempting to export dataset id"
    # assert_output -p "Could not find dataset"   ## export not using exceptions for errors
}


@test "Dataset import " {
    run vision dataset import "$VCT_DATA_DIR/VCTST_CIC_dataset.zip"
    assert_success
    assert_output -e "Successfully created dataset with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    tid=$(extract_uuid $output)
    echo "cic: $tid" >>$VCT_DSID_FILE
    wait_for_task $tid 5
}

@test "Dataset export With Filename" {
    [ -f ${VCT_DSID_FILE} ] || fail "No dataset id file"
    dsid=$(awk '/^cic:/ {print $2}'  $VCT_DSID_FILE)
    [ -z $dsid ] && fail "No dataset id to export"

    zip_filename="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}-cic.zip"
    echo "id='${dsid}', zip='${zip_file}'" >>$VCTLOG
    run vision dataset export --dsid $dsid --filename ${zip_filename}
    assert_success
    assert_output -p ${zip_filename}
}

@test "Dataset export Raw; No Filename" {
    [ -f ${VCT_DSID_FILE} ] || fail "No dataset id file"
    dsid=$(awk '/^cic:/ {print $2}'  $VCT_DSID_FILE)
    [ -z $dsid ] && fail "No dataset id to export"

    cd $VCT_WK_DIR
    run vision dataset export --dsid $dsid --raw
    assert_success
    assert_output -p ".zip"
    run unzip -l $output
    assert_success
    assert_output -p "/__DEBUG/"
}


@test "Dataset import/export Tests Cleanup" {
    [ -f ${VCT_DSID_FILE} ] || skip "No dataset id file"
    dsid=$(awk '/^cic:/ {print $2}'  $VCT_DSID_FILE)
    [ -z $dsid ] && skip "No dataset id to export"

    run vision dataset delete --dsid $dsid
    assert_success
}
