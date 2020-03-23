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
# This test uses extensions to the base BATS (see 1st 'load' statments)
#*************************************************************************

load "${BATS_HOME}/test/libs/bats-support/load.bash"
load "${BATS_HOME}/test/libs/bats-assert/load.bash"

load "${VCT_DIR}/helpers/test_helpers"

export BATS_TEST_FILE_BASENAME=$(basename ${BATS_TEST_FILENAME})
export VCT_ID_FILE="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}-ids"
export VCTLOG="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}.log"


@test "Trained-model import Missing Args" {
    run vision trained-models import
    assert_failure
    assert_output -p "Usage:"
}

@test "Trained-model import " {
    run vision trained-models import "$VCT_DATA_DIR/cic-model-export.zip"
    assert_success
    assert_output -e "Successfully imported trained-model with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    tid=$(extract_uuid $output)
    echo "cic: $tid" >>$VCT_ID_FILE
}


@test "Trained-model export Missing Args" {
    run vision trained-models export
    assert_failure
    assert_output -p "Usage:"
}

@test "Trained-model export Non-Existent Trained-Models" {
    run vision trained-models export --modelid 123
    assert_failure
    assert_output -p "Failure attempting to export trained-model id"
    # assert_output -p "Could not find trained-models"   ## export not using exceptions for errors
}

@test "Trained-model export With Filename" {
    [ -f ${VCT_ID_FILE} ] || fail "No trained-models id file"
    modid=$(awk '/^cic:/ {print $2}'  $VCT_ID_FILE)
    [ -z $modid ] && fail "No trained-models id to export"

    zip_filename="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}-cic.zip"
    echo "id='${modid}', file=${zip_filename}" >>$VCTLOG
    run vision trained-models export --modelid $modid --filename ${zip_filename}
    assert_success
    assert_output -p ${zip_filename}
}

@test "Trained-model export Without Filename" {
    [ -f ${VCT_ID_FILE} ] || fail "No trained-models id file"
    modid=$(awk '/^cic:/ {print $2}'  $VCT_ID_FILE)
    [ -z $modid ] && fail "No trained-models id to export"

    cd $VCT_WK_DIR
    echo "id='${modid}', dir=${PWD}" >>$VCTLOG
    run vision trained-models export --modelid $modid
    assert_success
    assert_output -p ".zip"
}

@test "Trained-model delete no args" {
    run vision trained-models delete
    assert_failure
    assert_output -p "Usage:"
}

@test "Trained-model Bad Id" {
    run vision trained-models delete --id 123
    assert_failure
    assert_output -p "Failure attempting to delete model id"
    assert_output -p "Could not find trainedModel"
}

@test "Trained-model import/export Tests Cleanup" {
    [ -f ${VCT_ID_FILE} ] || fail "No trained-model id file"
    modid=$(awk '/^cic:/ {print $2}'  $VCT_ID_FILE)
    [ -z $modid ] && fail "No trained-models id to export"

    echo "id='${modid}'" >>$VCTLOG
    run vision trained-models delete --modelid $modid
    assert_success
}
