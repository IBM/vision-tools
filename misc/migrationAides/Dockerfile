# IBM_SOURCE_PROLOG_BEGIN_TAG
# *****************************************************************
#
# IBM Confidential
# OCO Source Materials
#
# (C) Copyright IBM Corp. 2021
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office.
#
# *****************************************************************
# IBM_SOURCE_PROLOG_END_TAG

FROM registry.access.redhat.com/ubi8/python-36

ARG KUBECTL_VERSION="v1.16.2"
ARG HELM_VERSION="v3.2.1"
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
    # Install kubectl
    curl -LO "https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/${_ARCH}/kubectl" && \
	chmod +x kubectl && \
	mv kubectl /usr/local/bin/ && \
    # Install Helm
    curl -LO "https://get.helm.sh/helm-${HELM_VERSION}-linux-${_ARCH}.tar.gz" && \
	mkdir -p "/usr/local/helm-${HELM_VERSION}" && \
	tar -xzvf "helm-${HELM_VERSION}-linux-${_ARCH}.tar.gz" -C "/usr/local/helm-$HELM_VERSION" && \
	ln -s "/usr/local/helm-${HELM_VERSION}/linux-${_ARCH}/helm" /usr/local/bin/helm && \
	rm -f "helm-${HELM_VERSION}-linux-${_ARCH}.tar.gz" && \
    # Install OC
    curl -LO "https://mirror.openshift.com/pub/openshift-v4/clients/oc/${OC_VERSION}/${OC_ARCH}/oc.tar.gz" && \
    tar -xzvf "oc.tar.gz" -C "/usr/local/bin/" && \
    chmod +x /usr/local/bin/oc && \
    rm oc.tar.gz && \
    mkdir -p /usr/local/migration/vapi/accessors && \
    touch /usr/local/migration/vapi/__init__.py && \
    touch /usr/local/migration/vapi/accessors/__init__.py && \
    chmod -R 777 /usr/local/migration

USER 1979
COPY cmds/* /usr/local/migration/
COPY lib/vapi/accessors/* /usr/local/migration/vapi/accessors/

CMD python3 --version; rsync --version
