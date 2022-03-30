# IBM Maximo Visual Inspection Edge Installation on MacOS

## Installation
Installation on MacOS follows the [basic inception process](inception_internals.md) with the following deltas:

> All of these changes should be made after running inception and before running startedge.sh for the first time.

- MacOS does not include the language code in response to the `locale` command. This will prevent the license acceptance script from working.
  - The workaround is to comment out the line:
    ```
    source $HOST_SERVICE_ROOT/bin/license.sh
    ```
    in the `startedge.sh` script.

- Root installation directory, the following line in the `startedge.sh`, `stopedge.sh`, and `restartedge.sh` scripts should be changed:
  - from:
    ```
    HOST_ROOT=$(dirname $(realpath $BASH_SOURCE))
    ```
  - to:
    ```
    HOST_ROOT=$(dirname $(realpath $BASH_SOURCE:-$0))
    ```
- In order to get the shared memory size used to configure the database, this line in the `startedge.sh` and `restartedge.sh` scripts should be changed:
  - from:
    ```
    totmemkb=$(cat /proc/meminfo | grep MemTotal | awk '{ print $2 }')
    ```
  - to:
    ```
    totmemkb=$(sysctl hw.memsize | grep hw.memsiz | awk '{ print $2 }')
    ```
    *(Thanks to Huiyou Feng for this info)*
    
