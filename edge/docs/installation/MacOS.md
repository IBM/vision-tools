# IBM Maximo Visual Inspection Edge Installation on MacOS

## Installation
Installation on MacOS follows the [basic inception process](inception_internals.md) with the following deltas:

- MacOS does not include the language code in response to the `locale` command. This will prevent the license acceptance script from working.
  - The workaround is to comment out the line:
    ```
    source $HOST_SERVICE_ROOT/bin/license.sh
    ```
    in the `startedge.sh` script.
