# MVI Edge Web Utilities

The Web Utilities demonstrate how to interact with the Controller REST API for various functions.

See the README.md files in the individual folders for each utility for details.

These utilities must be added to the vision-edge-controller container after installation. Each utillity should be installed in a separate folder. For convenience, the installwebutils.sh script is provided. This script will install all utility folders in the current directory and commit the controller container so the utilities will remain installed if the container is removed and recreated (EG by running the startedge.sh script)

When installed by the installwebutils.sh script, the utilities will each be in their own folder. To access them, use `https://<hostname>/<name of folder>`