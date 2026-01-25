#!/usr/bin/env bash

set -e
set -x

mypy app
ruff check app
ruff format app --check
black app --check
isort app --profile=black --check-only
