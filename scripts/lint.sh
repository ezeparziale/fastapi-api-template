#!/usr/bin/env bash

set -e
set -x

mypy app
ruff app
black app --check
isort app --profile=black --check-only