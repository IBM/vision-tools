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

#----------------------------------------------------------------
# Function to extract the 1st substring matching the UUID pattern
extract_uuid() {
    echo "extracting UUID from '$@'" >&2
    echo $@ | python -c "import re,sys; print(re.search(r'([0-9a-f]+-[0-9a-f]+-[0-9a-f]+-[0-9a-f]+-[0-9a-f]+)', sys.stdin.read()).group(1))"
}


#----------------------------------------------------------------
#
# Get the value associated with the given key in the given file
# The file contains "key: value" pairs one per line. The key
# must begin in column 1.
#
# file with the matching key.
# First parameter is the file
# Second parameter is the key
get_key_value() {
    kvfile=$1
    key=$2

    if [ -f ${kvfile} ]
    then
        value=$(awk -v pattern="^${key}:" '$0 ~ pattern  {print $2}'  ${kvfile})
    else
        value=""
    fi
    echo "'${kvfile}', '${key}' ==> '${value}" >>$VCT_WK_DIR/log
    echo $value
}


#---------------------------------------------------------------
# Function to wait for a BG task to complete.
# First parameter is the task id
# Second parameter is timeout in minutes; 0 means not timeout
wait_for_task() {
    tid=$1
    timeout=$2
    interval=10
    count=$(( timeout*60/interval ))

    while true
    do
        # Start with sleep to ensure everthing has time to get setup before checking on it.
        sleep $interval
        status=$(python ${VCT_DIR}/helpers/getbginfo.py $tid "status")

        [ -z "$status" ] && return 1               # command to get status failed, return failure
        [ "$status" == "failed" ] && return 1      # task failed, return failure
        [ "$status" == "completed" ] && return 0   # task has completed, return success
        [ $timeout -ne 0 ] && [ $count -le 0 ] && return 1  # timeout given and out of time, return failure
        count=$(( count-1 ))
    done
}


#---------------------------------------------------------------
# Function to wait for a training task to complete.
# First parameter is the task id
# Second parameter is timeout in minutes; 0 means not timeout
wait_for_training() {
    tid=$1
    timeout=$2
    interval=30
    count=$(( timeout*60/interval ))

    while true
    do
        # Start with sleep to ensure everthing has time to get setup before checking on it.
        sleep $interval
        status=$(vision dltasks show --taskid $tid | python -c 'import json,sys;print(json.load(sys.stdin)["status"])')
        echo "status ==> $status"
        [ -z "$status" ] && return 1              # command to get status failed, return failure
        [ "$status" == "failed" ] && return 1     # training failed, return failure
        [ "$status" == "trained" ] && return 0    # training has completed, return success
        [ $timeout -ne 0 ] && [ $count -le 0 ] && return 1  # timeout given and out of time, return failure
        count=$(( count-1 ))
    done
}
