# Installing Prereqs on Ubuntu 20.04
These instructions are for Ubuntu 20.04 but should also work with Ubuntu 18.04

## Prereqs
- Nvidia Driver
- Docker
- Nvidia Container Toolkit
- /etc/docker/daemon.json

### Nvidia Driver
The driver should be available from the standard apt repo and will be installed from there
- `sudo apt update`
- `sudo apt search nvidia | grep '^nvidia-driver.*server'` list all available nvidia drivers
  - select a suitable version. If available, `nvidia-driver-470-server` is recommended
    - if version 470 is not available, select the next higher version
- `sudo apt install {{nvidia-driver version}}`
- verify that the driver is installed correctly
  - `nvidia-smi`
  - if this does not work try rebooting the server then running it again

### Docker
Install `docker-ce` from standard repo
- `sudo apt search docker-ce | grep 'docker-ce/'`
  - should show a version of docker-ce, if it does not,
    - `sudo apt-get update`
    - `sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common`
    - `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -`
    - `sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"`
    - `sudo apt-get update`
- `sudo apt-get install docker-ce`
- verify docker is installed and running
  - `sudo docker -v`

### Nvidia Container Toolkit
Allows containers to access the GPU
- `curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -`
- `distribution=$(. /etc/os-release;echo $ID$VERSION_ID)`
- `curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list`
- `sudo apt-get update`
- `sudo apt-get install nvidia-docker2`
- `sudo systemctl restart docker.service`
- verify the toolkit is installed and working
  - `docker run --rm nvidia/cuda:12.1.0-cudnn8-runtime-ubi8 nvidia-smi`
  - >NOTE from time to time Nvidia removes images from their hub. IE the `12.1.0` image might not be found. A list of available images can be found here https://gitlab.com/nvidia/container-images/cuda/blob/master/doc/unsupported-tags.md

### /etc/docker/daemon.json
Set the default runtime for docker
- edit the `/etc/docker/daemon.json` file to look like this
  ```
    {
       "runtimes" : {
          "nvidia" : {
             "path" : "/usr/bin/nvidia-container-runtime",
             "runtimeArgs" : []
          }
       }
    }
  ```
- `sudo systemctl restart docker`

