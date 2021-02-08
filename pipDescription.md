# vision-tools
## IBM MAximo Visual Inspection API Tools
IBM Maximo Visual Inspection makes computer vision with deep learning more accessible
to business users. IBM Maximo Visual Inspection includes an intuitive toolset that
empowers subject matter experts to label, train, and deploy deep learning vision models,
without coding or deep learning expertise. This repo provides a developer client API
and command line (CLI) for an existing installation. To learn more about IBM Maximo
Visual Inspection, check out the
[IBM Marketplace](https://www.ibm.com/us-en/marketplace/ibm-maximo-visual-inspection)

The IBM Maximo Visual Inspection API tools has two parts; a Python API piece and a
command line (CLI) piece. The CLI piece uses the API piece to communicate with an
IBM Maximo Visual Inspection server. The CLI is meant to make it easier to do automation
via shell scripts while the API is meant to make it easier to do automation scripting
in Python.

The goal is that the tools will support all of the endpoints and options available
from the IBM MAximo Visual Inspection ReST API. However, not everything is supported
at this time.

## Setup
Setup is performed via `pip install vision-tools`.

## Using the CLI Tool
### Introduction
All of the CLI operations are driven by a single command -- `vision`. This command takes
 a "_resource_" on which to operate. Currently supported resources are:

 * datasets
 * categories
 * files
 * fkeys
 * fmetadata
 * object-tags
 * object-labels
 * action-tags
 * action-labels
 * dltasks
 * trained-models
 * deployed-models
 * projects

Each of these resources have operations that can be performed on them for creating, listing,
showing details, deleting, etc. Each resource will respond with the list of operations it
supports when given the `--help` flag (e.g. `vision datasets --help`). To get detailed help
about an operation for an entity use `--help` with the operation
(e.g. `vision datasets list --help`).

Note that flags, resources, and operations can be abbreviated to the point of uniqueness.
Using abbreviations is *NOT* recommended in scripts, but can be useful on the command line
to reduce typing.

### The Basics
The `vision` tool has the following usage:
```
Usage:  vision [--httpdetail] [--jsonoutput] [--host=<host> | --uri=<serverUri>] [--token=<token>] [--log=<level>] [-?] <resource> [<args>...]

Where:
   --httpdetail   Causes HTTP message details to be printed to STDERR
                  This information can be useful for debugging purposes or
                  to get the syntax for use with CURL.
   --jsonoutput   Intended to ease use by scripts, all output to STDOUT is in
                  JSON format. By default output to STDOUT is more human
                  friendly
   --host         Identifies the targeted MVI server. If not
                  specified here, the VAPI_HOST environment variable is used.
                  This parameter has been deprecated. It is maintained for 
                  backward compatibility, but will be removed in a future 
                  release of the tools. 
   --uri          Identifies the base URI for the MVI server -- including the
                  '/api' "directory". If not specified, VAPI_BASE_URI
                  environment variable will be used.
   --token        The API Key token. If not specified here, the
                  VAPI_TOKEN environment variable is used.
   --log          Requests logging at the indicated level. Supported levels are
                  'error', 'warn', 'info', and 'debug'
   -?  displays this help message.

   <resource> is required and must be one of:
      categories     -- work with categories within a dataset
      datasets       -- work with datasets
      files          -- work with dataset files (images and/or videos)
      fkeys          -- work with user file metadata keys
      fmetadata      -- work with user file metadata key/value pairs
      object-tags    -- work with object detection tags 
      object-labels  -- work with object detection labels (aka annotations)
      dltasks        -- work with DL training tasks
      trained-models -- work with trained models
      deployed-models -- work with deployed models
      projects       -- work with projects
      users          -- work with users

'vision' provides access to Maximo Visual Inspection resources via the ReST API.
Use 'vision <resource> --help' for more information about operating on a given resource
```

Two pieces of information are required -- the base URI of the server (`--uri`) and the
user's API Key (`--token`). It is often easier to specify this information via environment
variables. The `$VAPI_BASE_URI` variable is used for the server URI and the `$VAPI_TOKEN`
variable is used for the API Key.

If a different port is needed, that port should be included with base URI.

### Quick Start Summary
#### Using a Standalone Server with "visual-insights" URI

Assume that the target server is a Maximo Application Suite environment with MVI available at 
`https://mvi-mas-my-server.your-company.com`. 
Assume that the user has already created an API key via the MVI UI and the value is `API-KEY-FROM-UI`.

Perform the following steps for the easiest use:
 1. set VAPI_BASE_URI
 2. set VAPI_TOKEN
 3. ensure token is set

Example commands...
```
export VAPI_BASE_URI="https://mvi-mas-my-server.your-company.com/api"
export VAPI_TOKEN="API-KEY-FROM-UI"
```

`vision` should now report results from the server; try `vision datasets list --summary`.
If something failed, see the "debugging" section below.

### International Language Support

With version 8.2.0 of Maximo Visual Inspection (GA'ed in January 2021), the API can generate
error messages in different languages. To get API messages in a language other than English,
export the `VAPI_LANGUAGE` environment variable with the desired language. The contents of
the `VAPI_LANGUAGE` environment variable are placed in the HTTP `Accept-Language` header
and only processed by the HTTP service on the server. So, any valid syntax for `Accept-Language`
can be set.

For example, to get API messages in French do:
```
export VAPI_LANGUAGE=fr
```

At this time, messages generated directly by the vision tools (e.g. usage messages) are
not translated at this time.

## Attributions
In addition to the required external Python Packages, this toolset embeds the following:

#### docopt
This module is cloned from https://github.com/bazaar-projects/docopt-ng.git. It is a command
argument parser that takes a usage statement as the parsing definition. It is embedded to
ease install of the toolset and to cleanup some error messages to be more user friendly.

#### bats -- Bash Automated Testing System
BATS is used to drive the automated testing to the CLI. It is included in the `test`
directory as a zip file containing the 3 repos...
 * https://github.com/sstephenson/bats test/libs/bats<br>
   The core BATS driver.
 * https://github.com/ztombol/bats-assert test/libs/bats-assert<br>
   Very nice assertion functions to ease checking and make it more readable
 * https://github.com/ztombol/bats-support test/libs/bats-support<br>
   Support services for the `bats-assert` repo.


