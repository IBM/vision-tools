#!/usr/bin/env bash
#
# Simple script to do package build.
# Possible future expansion would be to generate a "dev" 
# version number if built off of the 'dev' branch.

set -e

python ./setup.py bdist_wheel
