# IBM_PROLOG_BEGIN_TAG
#
# Copyright 2021 IBM International Business Machines Corp.
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

FROM registry.access.redhat.com/ubi8/python-36

ARG OC_VERSION="4.4"

USER root
RUN  set -eux; \
    \
    arch="$(uname -m)"; \
    case  "${arch##*-}" in \
        ppc64le) \
            _ARCH='ppc64le'; \
            PLUGIN_INSTALL='echo plugin container-service not-supported on ppc64le'; \
            OC_ARCH='linux-ppc64le'; \
            ;; \
        x86_64) \
            _ARCH='amd64'; \
            PLUGIN_INSTALL='ibmcloud plugin install container-service'; \
            OC_ARCH='linux'; \
            ;; \
    esac; \
    pip install --upgrade pip && \
    pip install requests pymongo Vision-Tools && \
    # Install OC
    curl -LO "https://mirror.openshift.com/pub/openshift-v4/clients/oc/${OC_VERSION}/${OC_ARCH}/oc.tar.gz" && \
    tar -xzvf "oc.tar.gz" -C "/usr/local/bin/" && \
    chmod +x /usr/local/bin/oc && \
    rm oc.tar.gz && \
    mkdir -p /usr/local/migration/vapi/accessors && \
    touch /usr/local/migration/vapi/__init__.py && \
    touch /usr/local/migration/vapi/accessors/__init__.py && \
    chmod -R 775 /usr/local/migration

USER 1979:1979
COPY cmds/* /usr/local/migration/
COPY lib/accessors/* /usr/local/migration/vapi/accessors/

