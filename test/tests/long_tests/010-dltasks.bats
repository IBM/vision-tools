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
#   - BATS_TEST_FILENAME - name of the test file being run (this file)
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
export VCT_ID_FILE="${VCT_WK_DIR}/${BATS_TEST_FILE_BASENAME}-ids"


@test "Dataset train Missing Args" {
    run vision datasets train
    assert_failure
    assert_output -p "Usage:"
}


@test "Dataset train Non-Existent Dataset" {
    run vision dataset train --dsid 123-abc-ef0 --name "VCTST-no-dataset" --type act
    assert_failure
    assert_output -p "Failure attempting to train dataset"
    # assert_output -p "Could not find dataset"    ## training task does not use "standard" exceptions, so this line is not present
}

@test "DLTask list summary with no tasks" {
    run vision dltask list --summary
    assert_success
    assert_output "0 items"
}

@test "DLTask list default output with no tasks" {
    run vision dltask list
    assert_success
    assert_output "[]"
}

@test "DLTask train Setup" {
    # Load dataset for CIC training
    run vision dataset import "$VCT_DATA_DIR/VCTST_CIC_dataset.zip"
    assert_success
    assert_output -e "Successfully created dataset with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    tid=$(extract_uuid $output)
    echo "cic-ds: $tid" >>$VCT_ID_FILE
    wait_for_task $tid 5
    [ $? -eq 0 ]

    # Load dataset for COD training
    run vision dataset import "$VCT_DATA_DIR/VCTST_COD_segm_dataset.zip"
    assert_success
    assert_output -e "Successfully created dataset with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    tid=$(extract_uuid $output)
    echo "cod-ds: $tid" >>$VCT_ID_FILE
    wait_for_task $tid 5
    [ $? -eq 0 ]
}


@test "Dataset train Bad Dataset " {
    # Bad dataset in this case is trying COD on a dataset with no labels
    dsid=$(get_key_value ${VCT_ID_FILE} "cic-ds")
    refute [ -z "$dsid" ]

    run vision dataset train --dsid $dsid --type cod --name "cod-on-cic"
    assert_failure
    assert_output -e "Failure attempting to train dataset"
}

@test "Dataset train Minimum Args" {
    dsid=$(get_key_value ${VCT_ID_FILE} "cic-ds")
    refute [ -z "$dsid" ]

    # Make sure the dataset completed import
    run python ${VCT_DIR}/helpers/getbginfo.py ${dsid} "status"
    assert_output -p "completed"

    run vision dataset train --dsid $dsid --type cic --name "dltask-cic"
    assert_success
    assert_output -e "Started training task with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    tid=$(extract_uuid $output)
    echo "cic-min-args-task: $tid" >>$VCT_ID_FILE
    wait_for_training $tid 30

    # Make sure training succeeded.
    run vision dltask show --taskid $tid
    assert_success
    assert_output -e '"status":  *"trained"'
}

@test "Dataset train with Hyperparameters" {
    dsid=$(get_key_value ${VCT_ID_FILE} "cod-ds")
    refute [ -z $dsid ]

    # Make sure the dataset completed import
    run python ${VCT_DIR}/helpers/getbginfo.py ${dsid} "status"
    assert_output -p "completed"

    run vision dataset train --dsid $dsid --type cod --name "dltask-cod" --hyper '{"max_iter": 1000, "ratio":0.75}'
    assert_success
    assert_output -e "Started training task with id [0-9a-f][0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]*-[0-9a-f]"
    tid=$(extract_uuid $output)
    echo "OUTPUT ==> $output"
    echo "dsid = $dsid; tid = $tid"
    echo "cod-hyper-task: $tid" >>$VCT_ID_FILE
    wait_for_training $tid 30
    [ $? -eq 0 ]
}

@test "DLTask list Summary Output" {
    run vision dltask list --summary
    assert_success
    printf "%s\n" ${lines[@]}
    assert_line -p -n 0 "dltask-cod"
    assert_line -p -n 1 "dltask-cic"
    assert_line -n 2 "2 items"
}

@test "DLTask list default output" {
    run vision dltask list
    assert_success
    # Ensure 2 elements in returned json array
    assert_equal $(echo $output | python -c 'import sys,json;print(len(json.load(sys.stdin)))') 2

    # regenerate lines array containing only task names
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/dltask-ld.out
    run awk -F':' '/^    "name"/ {print $2}' ${VCT_WK_DIR}/dltask-ld.out

    assert_line -p -n 0 "dltask-cod"
    assert_line -p -n 1 "dltask-cic"
}


# Change sort order of 'created_at' (should reverse output)
@test "DLTask list sorted summary output" {
    run vision dltask list --summary --sort created_at
    assert_success
    assert_line -p -n 0 "dltask-cic"
    assert_line -p -n 1 "dltask-cod"
    assert_line -n 2 "2 items"
}


@test "DLTask list sorted default output" {
    run vision dltask list --sort name
    assert_success
    # Ensure 2 elements in returned json array
    assert_equal $(echo $output | python -c 'import sys,json;print(len(json.load(sys.stdin)))') 2

    # regenerate lines array containing only task names
    printf "%s\n" "${lines[@]}" >${VCT_WK_DIR}/task-lsd.out
    run awk -F':' '/^    "name"/ {print $2}' ${VCT_WK_DIR}/task-lsd.out

    assert_line -p -n 0 "dltask-cic"
    assert_line -p -n 1 "dltask-cod"
}

@test "DLTask show with no Args" {
    run vision dltask show
    assert_failure
    assert_output -p "Error: Missing required"
    assert_output -p "Usage"
}

@test "DLTask show with bad Task Id" {
    run vision dltask show --taskid 123-def
    assert_failure
    assert_output -p "Failure attempting to get dltask id"
    #assert_output -p "Could not find task"
}


@test "DLTask show" {
    taskid=$(get_key_value ${VCT_ID_FILE} cic-min-args-task)

    run vision dltask show --task ${taskid}
    assert_success
    assert_output -e "\"_id\": *\"${taskid}\""
    assert_output -e "\"name\": *\"dltask-cic\""
}

@test "DLTask delete with no Args" {
    run vision dltask delete
    assert_failure
    assert_output -p "Error: Missing required"
    assert_output -p "Usage"
}

@test "DLTask delete with bad Task Id" {
    run vision dltask delete --taskid bad-789
    assert_failure
    assert_output -p "Failure attempting to delete dltask id"
}


@test "DLTask delete" {
    taskid=$(get_key_value ${VCT_ID_FILE} cic-min-args-task)

    run vision dltask delete --taskid ${taskid}
    assert_success
    assert_output -p "Deleted dltask id "
}

@test "DLTask train Tests Cleanup" {
    tid=$(get_key_value ${VCT_ID_FILE} "cic-min-args-task")
    [ -z $tid ] || run vision dltask delete --taskid $tid

    tid=$(get_key_value ${VCT_ID_FILE} "cod-on-cic-task")
    [ -z $tid ] || run vision dltask delete --taskid $tid

    tid=$(get_key_value ${VCT_ID_FILE} "cod-hyper-task")
    [ -z $tid ] || run vision dltask delete --taskid $tid
}