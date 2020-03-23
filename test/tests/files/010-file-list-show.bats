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

export BATS_TEST_FILE_BASENAME=$(basename ${BATS_TEST_FILENAME})
export VCT_DSID_FILE="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}.ids"

# The following 2 tests expects there to be no datasets present so that
# the list operation will return an empty json array
@test "File list summary with no Args" {
    run vision file list --summary
    assert_failure
    assert_output -p "Missing required arguments"
    assert_output -p "Usage:"
}


@test "File list with Bad Dataset Id" {
    run vision file list --dsid bad-123
    assert_failure
    assert_output -p "Failure attempting to list files"
}


# The following test only creates some datasets to be used for the
# remaining list/show tests. It should always pass if the server
# is operating correctly. Note no content is needed for these tests.
# Datasets are created in a specific order with specific names
# so that the default sort will be different than the 'sort-by' test.
@test "File list/show Tests Setup" {
    run vision dataset import ${VCT_DATA_DIR}/tiny-dataset.zip
    assert_success
    dsid=$(extract_uuid $output)
    printf "dsid: %s\n", ${dsid} >${VCT_DSID_FILE}
    wait_for_task ${dsid} 3
}


@test "File list Summary Output" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)

    run vision file list --dsid ${dsid} --summary
    assert_success
    printf "%s\n" ${lines[@]}
    assert_line -p -n 0 "image3.jpg"
    assert_line -p -n 1 "image2.png"
    assert_line -p -n 2 "image1.jpg"
    assert_line -p -n 3 "video1.mp4"
    assert_line -n 4 "4 items"
}


@test "File list default output" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)

    run vision file list --dsid ${dsid}
    assert_success
    assert_equal $(echo $output | python -c 'import sys,json;print(len(json.load(sys.stdin)))') 4

    # regenerate lines array containing only original file names
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/file-ld.out
    run awk -F':' '/ "original_file_name"/ {print $2}' ${VCT_WK_DIR}/file-ld.out

    assert_line -p -n 0 "image3.jpg"
    assert_line -p -n 1 "image2.png"
    assert_line -p -n 2 "image1.jpg"
    assert_line -p -n 3 "video1.mp4"
}


# Change sort order of 'created_at' (should reverse output)
@test "File list sorted summary output" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)

    run vision file list --dsid ${dsid} --summary --sort created_at
    assert_success
    assert_line -p -n 0 "video1.mp4"
    assert_line -p -n 1 "image1.jpg"
    assert_line -p -n 2 "image2.png"
    assert_line -p -n 3 "image3.jpg"
    assert_line -n 4 "4 items"
}


@test "File list sorted default output" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)

    run vision file list --dsid ${dsid} --sort name
    assert_success
    assert_equal $(echo $output | python -c 'import sys,json;print(len(json.load(sys.stdin)))') 4

    # regenerate lines array containing only dataset names
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/file-lsd.out
    run awk -F':' '/ "original_file_name"/ {print $2}' ${VCT_WK_DIR}/file-lsd.out

    assert_line -p -n 0 "image1.jpg"
    assert_line -p -n 1 "image2.png"
    assert_line -p -n 2 "image3.jpg"
    assert_line -p -n 3 "video1.mp4"
}

@test "File show with no Args" {
    run vision file show
    assert_failure
    assert_output -p "Error: Missing required"
    assert_output -p "Usage"
}

@test "File show with bad Dataset Id" {
    run vision file show --dsid bad-789 --fileid 123-def
    assert_failure
    assert_output -p "Failure attempting to get file id"
    assert_output -p "Could not find dataset"
}


@test "File show with bad File Id" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)

    run vision file show --dsid ${dsid} --fileid 123-def
    assert_failure
    assert_output -p "Failure attempting to get file id"
    assert_output -p "Could not find file"
}

@test "File show" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)
    fileid=$(vision file list --dsid ${dsid} --sum | head -1 | cut -f1)

    run vision file show --dsid ${dsid} --fileid ${fileid}
    assert_success
    assert_output -e "\"dataset_id\": *\"${dsid}\""
    assert_output -e "\"_id\": *\"${fileid}\""
    assert_output -e "\"original_file_name\": *\"image3.jpg\""
}

@test "File delete with no Args" {
    run vision file delete
    assert_failure
    assert_output -p "Error: Missing required"
    assert_output -p "Usage"
}

@test "File delete with bad Dataset Id" {
    run vision file delete --dsid bad-789 --fileid 123-def
    assert_failure
    assert_output -p "Failure attempting to delete file id"
    assert_output -p "Unknown dataset"
}

@test "File delete with bad File Id" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)

    run vision file delete --dsid ${dsid} --fileid 123-def
    assert_failure
    assert_output -p "Failure attempting to delete file id"
    assert_output -p "Could not find file"
}

@test "File delete" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)
    fileid=$(vision file list --dsid ${dsid} --sum | head -1 | cut -f1)

    run vision file delete --dsid ${dsid} --fileid ${fileid}
    assert_success
    assert_output -p "Deleted file id "
}

@test "File list/show/delete Tests Cleanup" {
    dsid=$(get_key_value ${VCT_DSID_FILE} dsid)
    run vision dataset delete --dsid $dsid
    assert_success
}
