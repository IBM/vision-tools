#!/bin/bash
# IBM_SHIP_PROLOG_BEGIN_TAG
# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020,2021. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************
# IBM_SHIP_PROLOG_END_TAG

STANDALONE=false
BASEDIR=$(cd $(dirname "${BASH_SOURCE[0]}")/.. && pwd)
BINDIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
PRODUCT_NAME="Maximo Visual Inspection"

DIR=mvi.logs."$(date|awk '{print $4"_"$2"_"$3"_"$6}'|sed 's/:/_/'g)"
DATADIR=./${DIR}
MISCDIR=${DATAPATH}/misc

# Usage
usage()
{
  info "Usage: $(basename $0) [options]"
  info ""
  info "Collect logs from MVI. Must have 'kubectl' or 'oc' installed and be logged in."
  info "All logs will be written to a new directory in the current working one with a"
  info "name of 'mvi.logs.<timestamp>'."
  info ""
  info "Options:"
  info "  -h, --help          Display this help text."
  info "      --namespace     The namespace that MVI is installed in. If not set,"
  info "                      will use the default namespace."
  info "      --standalone    Will collect OS information from the system this script"
  info "                      is running on. Only set if you are running MVI in"
  info "                      standalone mode on this system."
}

# Logging functions
info () {
  # Green
  printf "\E[0;32m[ INFO ] "
  tput sgr0;
  printf "%s\n" "$@";
}
warning () {
  # Yellow
  printf "\E[0;33m[ WARN ] "
  tput sgr0;
  printf "%s\n" "$@";
}
error () {
  # Red
  printf "\E[0;31m[ FAIL ] "
  tput sgr0;
  printf "%s\n" "$@";
}

# Helper function for waiting for processes
check_pid()
{
  local cnt=0
  while [[ $cnt -lt 5 ]]
  do
    sleep 1
    if [[ ! $(ps -p $1) =~ $1 ]]; then break; fi
    cnt=$((cnt+1))
    info "cxlffdc: waiting for slow process $1"
  done
  if [[ $(ps -p $1) =~ $1 ]]
  then
    kill -9 $1
  fi
}

# Make sure kubectl or oc is set up correctly
if command -v kubectl > /dev/null
then
  KUBE_CMD="kubectl"
elif command -v oc > /dev/null
then
  KUBE_CMD="oc"
else
  error "Either 'kubectl' or 'oc' is required to collect logs, but neither could be"
  error "found in the path.You can find installation instructions at:"
  error "  https://docs.openshift.com/container-platform/4.3/cli_reference/openshift_cli/getting-started-cli.html"
  exit 1
fi

# Process arguments
while [ $# -gt 0 ]
do
  key="$1"

  case $key in
    -n|--namespace)
    NAMESPACE="$2"
    shift
    shift
    ;;
    -s|--standalone)
    STANDALONE=true
    shift
    ;;
    -v|--version)
    info "v1.1"
    exit 0
    ;;
    -h|--help)
    usage
    exit 0
    ;;
    *) # Unknown option
    echo "Unknown option: $key"
    usage
    exit 1
    ;;
  esac
done

KUBE_CMD="${KUBE_CMD} --namespace ${NAMESPACE}"
info "Using kube/oc command '${KUBE_CMD}'"

# Set up the directory that we'll be dumping the logs into
if [[ -e $DATADIR ]]; then rm -rf $DATADIR 2>/dev/null; fi
mkdir -p $DATADIR

# Start actually collecting logs
info "Collecting ${PRODUCT_NAME} logs in parallel..."

# K8s/OCP information
$KUBE_CMD get clusterissuer -o wide > $DATADIR/get_clusterissuer.txt &
$KUBE_CMD version > $DATADIR/version.txt &
$KUBE_CMD get nodes -o wide > $DATADIR/get_nodes.txt &
$KUBE_CMD describe nodes > $DATADIR/describe_nodes.txt &
$KUBE_CMD get ingress -o yaml > $DATADIR/get_ingress.yaml &
$KUBE_CMD get componentstatus -o wide > $DATADIR/get_componentstatus.txt &
$KUBE_CMD api-versions > $DATADIR/kubectl_apiversions.txt &

$KUBE_CMD get all -o yaml > $DATADIR/get_all.yaml &
# The all-namespaces flag takes precedence over --namespace
$KUBE_CMD get events --all-namespaces > $DATADIR/get_all_events.txt &
$KUBE_CMD get events > $DATADIR/get_${NAMESPACE}_events.txt &

# In addition to get "all above", explicitly grab the same info in different formats
# Pods
$KUBE_CMD get pods -o wide > $DATADIR/get_pods.txt &
$KUBE_CMD describe pods > $DATADIR/describe_pods.txt &

# Deployments
$KUBE_CMD get deployments -o wide > $DATADIR/get_deployments.txt &
$KUBE_CMD describe deployments > $DATADIR/describe_deployments.txt &

# Jobs
$KUBE_CMD get jobs -o wide > $DATADIR/get_jobs.txt &
$KUBE_CMD describe jobs > $DATADIR/describe_jobs.txt &

# Services
$KUBE_CMD get services -o wide > $DATADIR/get_services.txt &
$KUBE_CMD describe services > $DATADIR/describe_services.txt &

# Routes
$KUBE_CMD get routes -o wide > $DATADIR/get_routes.txt &
$KUBE_CMD describe routes > $DATADIR/describe_routes.txt &

# Configmaps
$KUBE_CMD get configmap -o yaml > $DATADIR/get_configmap.yaml &
$KUBE_CMD describe configmap > $DATADIR/describe_configmap.txt &

# PVs and PVCs
$KUBE_CMD get persistentvolume -o wide > $DATADIR/get_persistentvolume.txt &
$KUBE_CMD describe persistentvolume > $DATADIR/describe_persistentvolume.txt &
$KUBE_CMD get persistentvolumeclaim -o wide > $DATADIR/get_persistentvolumeclaim.txt &
$KUBE_CMD describe persistentvolumeclaim > $DATADIR/describe_persistentvolumeclaim.txt &

# Certs
$KUBE_CMD get certs -o wide > $DATADIR/get_certs.txt &
$KUBE_CMD describe certs > $DATADIR/describe_certs.txt &

# Secrets
$KUBE_CMD get secrets -o wide > $DATADIR/get_secrets.txt &
$KUBE_CMD describe secrets > $DATADIR/describe_secrets.txt &

# Custom resources
$KUBE_CMD get visualinspection --all-namespaces > $DATADIR/get_cr_all_namespaces.txt &
$KUBE_CMD describe visualinspection --all-namespaces > $DATADIR/describe_cr_all_namespaces.txt &
$KUBE_CMD describe crd visualinspectionapps.mas.ibm.com > $DATADIR/describe_crd.txt &
$KUBE_CMD describe visualinspectionapps.mas.ibm.com > $DATADIR/describe_cr.txt &
$KUBE_CMD describe crd clusterpolicies.nvidia.com > $DATADIR/describe_gpu_crd.txt &
$KUBE_CMD describe clusterpolicies.nvidia.com > $DATADIR/describe_gpu_cr.txt &

# Get the actual logs from pods
for pod in $($KUBE_CMD get pods -o name)
do
  # OpenShift will append 'pod/' to the beginning of every pod name when we
  # use the '-o name' option. So, use ${pod:4} when getting the pod name to
  # strip off the 'pod/' prefix.
  $KUBE_CMD logs $pod > $DATADIR/logs_${pod:4} &
done

# Get GPU logs if the GPU namespace exists
if $KUBE_CMD get project gpu-operator-resources &> /dev/null
then
  $KUBE_CMD get deployments --namespace gpu-operator-resources > $DATADIR/nvidia_get_deployments.txt &
  $KUBE_CMD describe deployments --namespace gpu-operator-resources > $DATADIR/nvidia_describe_deployments.txt &
  $KUBE_CMD get pods --namespace gpu-operator-resources > $DATADIR/nvidia_get_pods.txt &
  $KUBE_CMD describe pods --namespace gpu-operator-resources > $DATADIR/nvidia_describe_pods.txt &
  $KUBE_CMD get daemonsets --namespace gpu-operator-resources > $DATADIR/nvidia_get_daemonsets.txt &
  $KUBE_CMD describe daemonsets --namespace gpu-operator-resources > $DATADIR/nvidia_describe_daemonsets.txt &
fi

# If we're running in standalone mode, get system details
if $STANDALONE
then
  info "Standalone mode selected. Collecting system details..."

  # Get distro information
  if [[ $(cat /etc/os-release 2>/dev/null) =~ Ubuntu ]];          then ubuntu=1; fi
  if [[ $(cat /etc/os-release 2>/dev/null) =~ Red ]];             then redhat=1; fi
  if [[ $(cat /etc/os-release 2>/dev/null) =~ Fedora ]];          then redhat=1; fi
  if [[ $(grep platform /proc/cpuinfo 2>/dev/null) =~ pSeries ]]; then VM=1;     fi
  ps_fields="user,group,ruser,rgroup,pid,tid,ppid,pgid,uid,tgid,nlwp,sgi_p,nice,pri,etime,pcpu,pmem,lim,rss,s,size,sz,vsz,trs,stat,f,stime,time,tty,comm,args"

  ulimit -a                            >  $DATADIR/ulimits
  top -n 1 -b                          >  $DATADIR/top
  ps -Tdaeo $ps_fields                 >  $DATADIR/ps
  env                                  >  $DATADIR/env
  uptime                               >  $DATADIR/uptime
  date                                 >> $DATADIR/uptime
  lspci -vvv                           >  $DATADIR/lspci_vvv
  cat /etc/*-release | egrep "PRETTY_NAME|^NAME|VERSION_ID|^VERSION=" >  $DATADIR/codelevels 2>/dev/null
  uname -a                             >> $DATADIR/codelevels
  if [[ $ubuntu ]]
  then
    dpkg -l|egrep "visual-inspection"   >> $DATADIR/codelevels
  elif [[ $redhat ]]
  then
    rpm -qa|egrep "visual-inspection"   >> $DATADIR/codelevels
  fi

  nvidia-smi   >  $DATADIR/nvidia-smi &
  check_pid $!

  info "Standalone mode selected. Collecting platform logs..."
  (
      dmesg > dmesg
      if [[ -e /var/log/syslog ]]
      then
        cp /var/log/syslog $DATADIR
        truncate --size=0 /var/log/syslog
      fi

      journalctl -n 50000 > $DATADIR/syslog
  ) &

  # Redhat version of syslog
  if [[ -e /var/log/messages ]]
  then
    cp /var/log/messages $DATADIR
    truncate --size=0   /var/log/messages
  fi

  if [[ -e /sys/firmware/opal/msglog ]]
  then
    cp /sys/firmware/opal/msglog $DATADIR/opal_msglog &
  fi

  if [[ ! $redhat ]]
  then
    # Collect kernel logs. RHEL now logs kernel to /var/log/messages
    (
      for file in $(ls -1 /var/log/kern.log)
      do
        lines=$(wc -l $file | awk '{print $1}')
        if [[ $lines -gt 0 ]]
        then
          tail -1000000 $file  > $DATADIR/${file##*/}
          truncate --size=0 $file
        fi
      done
    ) &
  fi
fi

# Wait for all processes to complete
wait
tar -czf $DIR.tgz $DIR
rm -Rf $DIR
info "FFDC Collected: $DATADIR.tgz"

