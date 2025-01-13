#!/usr/bin/env bash

set -e
set -x

# mypy app
ruff check app
black app --check
isort app --profile=black --check-only