# Maximo Visual Inspection Edge

This folder hierarchy contains resources for Maximo Visual Inspection Edge (MVIE).

MVIE is designed to bring the power of AI models trained with MVI to the edge as a self-contained solution that can run on edge nodes (anything from servers to laptops to devices such as an nVidia Jetson or a Raspberry Pi).

Edge nodes with GPUs can run models locally. For devices without GPUs, Edge can send inference requests to an MVI server or run the models on the CPU if lower performance is tolerable.


The standard MVIE product install includes:
- A Web UI and REST API, database, and MQTT Broker, all of which run in the `vision-edge-controller` container
- A runtime engine to run inspection pipelines that acquire images (from cameras, folders of images, or video files), processes acquired images using the models, and runs the inferenence data through Rules which can be configured through the UI. The runtime is provided by the `vision-edge-cme` container
- An inference engine that deploys the models and services inference requests. Inferencing is provided by the `vision-edge-dle` container

The resources here are intended to provide:
- Documentation on installing and running MVIE in currently unsupported environments and configurations that are not part of the standard product install
- Utilities and code samples that access the MVIE capabilities via APIs or modify the standard configurations. These will allow accessing product capabilities that are not exposed through the standard UI and install.

# Disclaimer
> The documentation and code samples provided herein are not part of the MVIE product and are not supported by IBM. All content in this repository is provided under the [Apache 2.0 License](https://github.com/fyeh/vision-tools/blob/dev/LICENSE) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied, including, without limitation, any warranties or conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A PARTICULAR PURPOSE. You are solely responsible for determining the appropriateness of using or redistributing the Work and assume any risks associated with Your exercise of permissions under this License.

