#!/bin/sh -e
set -x

ruff format app
black app
isort app --profile=black