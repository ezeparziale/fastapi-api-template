#!/bin/sh -e
set -x

ruff app --fix
black app
isort app --profile=black