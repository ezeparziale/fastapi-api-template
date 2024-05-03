#!/usr/bin/env bash

set -e
set -x

# mypy app alembic
ruff check app alembic
black app alembic --check
isort app alembic --profile=black --check-only