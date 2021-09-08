# IBM Maximo Visual Inspection Edge Installation on NVIDIA Jetson Devices

## Installation
Installation on Jetson devices follows the [basic inception process](inception_internals.md) with the following deltas:

- `nvidia docker` does not need to be installed
- The `nvidia-smi` command is not available

## Recommended Devices

The main consideration when as to a Jetson device is appropriate for MVIE is the amount of RAM on the device.
- RAM is shared between the CPU and GPU
- Different models require different amounts of RAM to be loaded on the GPU

This being the case, devices with less than 8GB RAM are not recommended.

- The AGX Xavier, with 32GB RAM, is the most capable of the Jetson devices and would be an excellent choice for MVI Edge.

- The NX and TX2/TX2i devices, with 8GB, are suitable to run at least one model and in some cases more than one (classification models typically require much less RAM). 

- The TX2 NC and TX2 4GB, with 4GB, are not recommended unless only classification models are to be run.

- The Nano, with 2GB is not recommended.

## Other Considerations

- Disk space to fit the Docker images and models. You might want to attach a SATA driver/SD card and set up Docker to store images/containers on that mount point.
- If your GPU already has a model deployed and you try to deploy another, it's possible that there will not be enough available RAM for to deploy another model. When deploying a model using the UI, the failure to load the additional model will cause am error notification to this effect. When deploying directly via the DLE API or one of the command line clients, it will be necessary to monitor the DLE log to detect this condition.
