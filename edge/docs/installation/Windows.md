# IBM Maximo Visual Inspection Edge Installation on Windows 10
## Installation
Installation on Windows 10 follows the [basic inception process](inception_internals.md) with the following deltas:

- In order to run the `startedge.sh` script a linux shell is required. The Windows Subsystem for Linux 2 (WSL2) is recommended but it has been reported that a successful installation was also performed using Mingw-w64. This document will target WSL2.

- Docker is required. Docker Desktop is most commonly used but it is also possible to run Docker directly in WSL2. In either case, the Linux shell that you install into must support standard docker cli commands such as `docker run`.

## Installing WSL2 and Docker Desktop

### WSL2
There are a number of good guides for installing WSL on Windows 10. 

[This is one of the best](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10).

It is recommended that the Ubuntu 18.04 or 20.04 distro be installed and also that Windows Terminal be used to access the WSL2 environment.

### Docker Desktop

This is the [official guide for installing Docker Desktop on Windows 10](https://docs.docker.com/desktop/windows/install/).

The Docker Desktop GUI is not required to run MVI Edge. Everything required can be done from the shell in WSL2.

## Running Inception

Open Windows Terminal and once at the shell, follow the [basic inception process](inception_internals.md).

## Running with No GPU

> As of September 2021, WSL2 and DOcker Desktop do not provide access to the GPU on a Windows 10 system. There is a Microsoft Insider program that does provide this access but it has not been tried with MVI Edge. It is assumed that a deployment on Windows 10 will run without access to the GPU.

Even though the DLE container will not be able to access the GPU, it should still be installed. This will prevent annoying error notifications from being displayed in the UI when the controller performs normal polling and requests to the DLE.

There are two inferencing options when running with no GPU:

1 Perform all inferences on the MVI Training Server

- Note that you will not be able to deplopy models locally with this option

2 Run in CPU Mode as described in the [basic inception process](inception_internals.md).

- Note that while you will be able to deploy models locally in CPU Mode, these models will run very slowly as compared to running on GPU.
