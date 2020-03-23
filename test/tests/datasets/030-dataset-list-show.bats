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
export VCT_DSID_FILE_1="${VCT_WK_DIR}/DS_LS_1"
export VCT_DSID_FILE_2="${VCT_WK_DIR}/DS_LS_2"
export VCT_DSID_FILE_3="${VCT_WK_DIR}/DS_LS_3"


# The following 2 tests expects there to be no datasets present so that
# the list operation will return an empty json array
@test "Dataset List summary with no Datasets" {
    run vision dataset list --summary
    assert_success
    assert_output "0 items"
}


@test "Dataset List with no Datasets" {
    run vision dataset list
    assert_success
    assert_output "[]"
}


# The following test only creates some datasets to be used for the
# remaining list/show tests. It should always pass if the server
# is operating correctly. Note no content is needed for these tests.
# Datasets are created in a specific order with specific names
# so that the default sort will be different than the 'sort-by' test.
@test "Dataset list/show Tests Setup" {
    run vision dataset create --name "VCT_list_show 3rd sort"
    assert_success
    echo $(extract_uuid $output) >${VCT_DSID_FILE_3}

    run vision dataset create --name "VCT_list_show 1st sort"
    assert_success
    echo $(extract_uuid $output) >${VCT_DSID_FILE_1}

    run vision dataset create --name "VCT_list_show 2nd sort"
    assert_success
    echo $(extract_uuid $output) >${VCT_DSID_FILE_2}
}


@test "Dataset list summary output" {
    run vision dataset list --summary
    assert_success
    assert_line -p -n 0 "VCT_list_show 2nd sort"
    assert_line -p -n 1 "VCT_list_show 1st sort"
    assert_line -p -n 2 "VCT_list_show 3rd sort"
    assert_line -n 3 "3 items"
}


@test "Dataset list default output" {
    run vision dataset list
    assert_success
    assert_equal $(echo $output | python -c 'import sys,json;print(len(json.load(sys.stdin)))') 3

    # regenerate lines array containing only dataset names
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/dsld.out
    run awk -F':' '/ "name"/ {print $2}' ${VCT_WK_DIR}/dsld.out

    assert_line -p -n 0 "VCT_list_show 2nd sort"
    assert_line -p -n 1 "VCT_list_show 1st sort"
    assert_line -p -n 2 "VCT_list_show 3rd sort"
}


@test "Dataset list sorted summary output" {
    run vision dataset list --summary --sort name
    assert_success
    assert_line -p -n 0 "VCT_list_show 1st sort"
    assert_line -p -n 1 "VCT_list_show 2nd sort"
    assert_line -p -n 2 "VCT_list_show 3rd sort"
    assert_line -n 3 "3 items"
}


@test "Dataset list sorted default output" {
    run vision dataset list --sort name
    assert_success
    assert_equal $(echo $output | python -c 'import sys,json;print(len(json.load(sys.stdin)))') 3

    # regenerate lines array containing only dataset names
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/dslsd.out
    run awk -F':' '/ "name"/ {print $2}' ${VCT_WK_DIR}/dslsd.out

    assert_line -p -n 0 "VCT_list_show 1st sort"
    assert_line -p -n 1 "VCT_list_show 2nd sort"
    assert_line -p -n 2 "VCT_list_show 3rd sort"
}


@test "Dataset show with no Args" {
    run vision dataset show
    assert_failure
    assert_output -p "Error: Missing required"
    assert_output -p "Usage"
}


@test "Dataset show with bad Args" {
    run vision dataset show --dsid abc-123
    assert_failure
    assert_output -p "Failure attempting to get dataset id 'abc-123'"
    assert_output -p "Could not find dataset"
}

@test "Dataset show" {
    assert [ -f ${VCT_DSID_FILE_1} ]
    dsid=$(cat ${VCT_DSID_FILE_1})
    refute [ -z $dsid ]

    run vision dataset show --dsid $dsid
    assert_success
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/dss.out
    assert_equal "$(cat ${VCT_WK_DIR}/dss.out | awk -F':' '/ "name":/ {print $2}')" " \"VCT_list_show 1st sort\","
}


@test "Dataset list/show Tests Cleanup" {
    for f in $VCT_DSID_FILE_1 $VCT_DSID_FILE_2 $VCT_DSID_FILE_3
    do
        assert [ -f ${f} ]
        dsid=$(cat ${f})

        run vision dataset delete --dsid $dsid
        assert_success
    done
}
