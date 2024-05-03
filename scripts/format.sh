#!/bin/sh -e
set -x

ruff format app alembic
black app alembic
isort app alembic --profile=black