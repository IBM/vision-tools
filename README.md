# vision-tools
## IBM Visual Insights API Tools
IBM Visual Insights makes computer vision with deep learning more accessible to business users. IBM Visual Insights
includes an intuitive toolset that empowers subject matter experts to label, train, and deploy deep learning vision
models, without coding or deep learning expertise. This repo provides a developer client API and command line (CLI) for
an existing installation. To learn more about IBM Visual Insights, check out the
[IBM Marketplace](https://www.ibm.com/us-en/marketplace/ibm-powerai-vision)

The IBM Visual Insights API tools has two parts; a Python API piece and a command line (CLI) piece.
The CLI piece uses the API piece to communicate with an IBM Visual Insights server. The CLI
is meant to make it easier to do automation via shell scripts while the API is meant to make it easier to
do automation scripting in Python.

The goal is that the tools will support all of the endpoints and options available from the IBM
Visual Insight ReST API. However, not everything is supported at this time.

## Setup
### Setting up Access to the Tools
It is a long term goal to create a PIP install image to make the tools easier to install and use.
But at this time, the following steps can be used to setup and use the IBM Visual Insight Tools.
(these steps assume that the cloned repo is in your home directory ("`$HOME`"))

 1. Ensure Python is at version 3.6 or above (e.g. `python3 -V`). If it is not, upgrade python 
 using your favorite install manager (pip, conda, etc.)
 1. Ensure that the Python _requests_ package is installed. (e.g. `pip install requests`)
 1. Clone this repo. (e.g. `git clone git@github.com:IBM/vision-tools.git`)
 1. Add the cloned repo's `cli` directory to your `PATH` environment variable.
    (e.g. `PATH=$PATH:$HOME/vision-tools/cli`) 
 1. Add the cloned repos's `lib` directory to your `PYTHONPATH` environment variable.
    (e.g. `export PYTHONPATH=$PYTHONPATH:$HOME/vision-tools/lib`)

At this point, the Visual Insights API CLI tools should be accessible. Run `vision --help` to see that the
command can be found. `vision datasets --help` can be run to ensure that sub-commands are accessible.

## Using the CLI Tool
### Introduction
All of the CLI operations are driven by a single command -- `vision`. This command takes an "_entity_"
(or "_object_") on which to operate. Currently supported entities are:

 * datasets
 * categories
 * files
 * object-tags
 * object-labels
 * action-tags
 * action-labels
 * dltasks
 * trained-models
 * deployed-models
 * projects

Each of these entities have operations that can be performed on them for creating, listing, showing details,
deleting, etc. Each entity will respond with the list of operations it supports when given the `--help` flag
(e.g. `vision datasets --help`). To get detailed help about an operation for an entity use `--help` with the
operation (e.g. `vision datasets list --help`).

Note that flags, entities, and operations can be abbreviated to the point of uniqueness. Using abbreviations is *NOT*
recommended in scripts, but can be useful on the command line to reduce typing.

### The Basics
The `vision` tool has the following usage:
```
Usage:  vision [--httpdetail] [--jsonoutput] [--host=<host>] [--token=<token>] [--log=<level>] [-?] <entity> [<args>...]

 Where:
     --httpdetail   Causes HTTP message details to be printed to STDERR
                    This information can be useful for debugging purposes or
                    to get the syntax for use with CURL.
     --jsonoutput   Intended to ease use by scripts, all output to STDOUT is in
                    JSON format. By default output to STDOUT is more human
                    friendly
     --host         Identifies the targeted PowerAI Vision server. If not
                    specified here, the VAPI_HOST environment variable is used.
     --token        The authentication token. If not specified here, the
                    VAPI_TOKEN environment variable is used.
     --log          Requests logging at the indicated level. Supported levels are
                    'error', 'warn', 'info', and 'debug'

     <entity> is required and must be one of:
        categories     -- work with category entities
        datasets       -- work with dataset entities
        files          -- work with dataset file entities
        object-tags    -- work with object detection tag entities
        object-labels  -- work with object detection label entities (aka annotation entities)
        dltasks        -- work with DL training tasks
        trained-models -- work with trained model entities
        deployed-models -- work with deployed model entities
        projects       -- work with project entities
        users          -- work with users
  
  'vision' provides access to Visual Insights entities via the ReST API.
  Use 'vision <entity> --help' for more information about operating on a given entity
```

Two pieces of information are required -- the host name of the server (`--host`) and the user's authentication
token (`--token`). It is often easier to specify this information via environment variables. The `$VAPI_HOST`
variable is used for the hostname and the `$VAPI_TOKEN` variable is used for the token. With this information,
`vision` will generate a base URL of `https://${VAPI_HOST}/visual-insights/api` to access the server.

In some installations, including those running IBM PowerAI Vision instead of IBM Visual Insights, 
the `$VAPI_INSTANCE` environment variable will be needed to adjust the generated base URL. Exporting a value in
`$VAPI_INSTANCE` will cause `vision` to generate a base URL of `https://${VAPI_HOST}/${VAPI_INSTANCE}/api`.

If a different port is needed, that port can be included with the hostname.

### Quick Start Summary
#### Using a Standalone Server with "visual-insights" URI

Assume that the target server is an IBM Visual Insights standalone server with host name `my-server.your-company.com`,
with a base URL of "`https://my-server.your-company.com/visual-insights`".<br>
Assume that the user is `janedoe` and her password is `Vis10nDemo`.

Perform the following steps for the easiest use:
 1. set VAPI_HOST -- `export VAPI_HOST=my-server.your-company.com`
 2. set VAPI_TOKEN -- `export VAPI_TOKEN=$(vision users token --user janedo --password Vis10nDemo)`
 3. ensure token is set -- `echo $VAPI_TOKEN`

If all went well, `vision` should report results from the server; try `vision datasets list --summary`.
If something failed, see the "debugging" section below.

#### Using a Server With Different URI (e.g. a Cloud Instance)

Assume that the target server has a host name of `my-provider.cloud-service.com` and the URI to access
the Visual Insights Application is `my-visual-insights-v120`.<br>
Assume that the user is `janedoe` and her password is `Vis10nDemo`.

Perform the following steps for the easiest use:
 1. set VAPI_HOST -- `export VAPI_HOST=my-server.your-company.com`
 2. set VAPI_TOKEN -- `export VAPI_TOKEN=$(vision users token --user janedo --password Vis10nDemo)`
 3. set VAPI_INSTANCE -- `export VAPI_INSTANCE="my-visual-insights-v120"`
 4. ensure token is set -- `echo $VAPI_TOKEN`

Note that the only difference is setting the `VAPI_INSTANCE` environment variable.

If all went well, `vision` should report results from the server; try `vision datasets list --summary`.
If something failed, see the "debugging" section below.

### Debugging
Two flags exist to assist with debugging. The `--httpdetail` flag and the `--log` flag.

The `--httpdetail` flag causes information from the `requests` package to be printed to STDERR.
This information includes the entire HTTP request that was sent to the server. The request
information includes all of the Headers that were sent. It can be quite useful to examine this
request information to ensure that information is accurate (e.g. host name, URL, input parameters, etc).
Be forewarned that if used when uploading a file (or importing a dataset or model), the detail will
include all of the encoded file contents. So it can be quite large in these cases.

The `--log` flag is fairly obvious. It uses the same logging levels as those provided by the Python `logging` module.
The only oddity with this flag is that the command must get through parsing of the command line before the specified
logging level will take effect. In most cases, that will not be a problem


## Attributions
In addition to the required external Python Packages, this toolset embeds the following:

#### docopt
This module is cloned from https://github.com/bazaar-projects/docopt-ng.git. It is a command
argument parser that takes a usage statement as the parsing definition. It is embedded to
ease install of the toolset and to cleanup some error messages to be more user friendly.

#### bats -- Bash Automated Testing System
BATS is used to drive the automated testing to the CLI. It is included in the `test` directory as
a zip file containing the 3 repos...
 * https://github.com/sstephenson/bats test/libs/bats<br>
   The core BATS driver.
 * https://github.com/ztombol/bats-assert test/libs/bats-assert<br>
   Very nice assertion functions to ease checking and make it more readable
 * https://github.com/ztombol/bats-support test/libs/bats-support<br>
   Support services for the `bats-assert` repo.


