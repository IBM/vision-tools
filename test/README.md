# Visual Insights API Tools Automated Tests

## Introduction

The Vision Insights API tools are tested via the CLI commands. The library is not directly
tested. The test suite tests the CLI commands to ensure proper processing of arguments including
getting the argument parameters and translating them appropriately to the appropriate values
for the API.

In addition to argument validation, some level of output validation is also performed. Output 
is validated only to the level to ensure that the expected output is being provided and in the
appropriate order -- given the input parameters and arguments.

As mentioned in the top level README's attribution section, the test suite uses the Bash Automated
Test Automated Testing System. These repos are included in a zip file that must be unzipped before
running the test suite. A script (`runtests`) is provided to front-end the BATS tool so that
environment variables are set in the manner expected by the tests.

The tests themselves focus on the entities (objects) in Visual Insights (datasets, training tasks,
files, labels, etc.). The long running tests, like those testing training, are split out and not
included in the main run. These long running tests must be run separately, though they should
be run using the front-end script (`runtests`).

## Setup

To setup the filesystem environment, run the `setup.sh` command in the `test` directory.
It ensures that the BATS tool is setup and ready for use. No flags are required for setup.
Setup is a one-time operation, though it should be repeated if the `bats.zip` file is 
updated. `setup.sh` will handle the situation if things change in the environment. Currently,
setup just destroys the BATS directory tree and unzips the `bats.zip` file into the 
expected location.

## Running Tests

The test suite can be run by executing the `runtests` script. This script requires 2 pieces of
information (just like the Visual Insights API tools)...

  1. The hostname of the test server.<br>
     This name is most easily provided via the `$VAPI_HOST` environment variable, but
     it can also be provided via the `-h` flag on `runtests`.
  2. A valid authentication token.<br>
     The authentication token is most easily provided via the `$VAPI_TOKEN` environment
     variable. However, the user and password can be provided to the `runtests` command
     via the `-u` and `-p` flags. If these flags are used, the `runtests` command
     attempts to get an authentication token and saves it in `$VAPI_TOKEN`.

If run with no test list, `runtests` will execute the entire automated test suite; 
**except** for the long running tests. To run tests for a particular entity (or the
long tests), use `runtests ./tests/long_tests` (for some reason, BATS does not recognize
a relative path if it does not begin with a dot).

It is best to use a specific user for testing purposes. This user should have nothing 
in the server; no datasets, training tasks, or trained models. The tests check for
specific object names, but also checks counts when doing list tests. These list tests
will fail if other entities exist for the user on the server.

It is possible to change the format of the BATS output. Use the `-f` flag on `runtests`
and give the flags you wish to pass to BATS. If multiple flags need to be passed 
to BATS, enclose the entire set in double quotes. See the BATS repo referenced in
the top level README to find information on flags supported by BATS.
 
## Test Structure

### Tests

Tests are divided into directories by entity. Each directory contains files that
test 1-3 operations on the entity. The test files use a number prefix to
ensure that some things are validated before others so that those capabilities can
be used in other tests with the expectation that they will work.
 
Each test file is self-standing, meaning that it does not depend upon the execution
of any other tests before it or after it. This attribute means that each test file
must setup the server environment it needs and cleanup that environment before
exiting the test. BATS does not have a setup and teardown on a per file basis (the
setup and teardown supported by BATS is done for each test in the file). To get a
single setup and teardown to apply to the entire file, tests are added at the
beginning and end of the test file.

### Test Data

Data for the tests resides in the `test-data` directory. This directory contains images,
videos, zip file, exported datasets, and exported models that can be used by
tests to create the server environment the test needs to execute. 

Note that GitHub has a 100MB size limit for a file. This limit precludes most of
the exported models. So, the variation of models in testing is quite limited.

### Test Working Data

A working directory is created to be used by tests for any transient files. 
This directory is `test-wk-dir` and is destroyed and recreate at the 
start of each test run. Passing information between tests is not easy in BATS.
This test suite uses files in the `test-wk-dir` for that purpose.

### Helper Functions and Tools

There are some common activities performed by most of the tests (e.g. extracting
a UUID from command output). These functions are shared by using a `helpers`
directory containing a common `test-helpers.bash` script that is loaded for
each test.