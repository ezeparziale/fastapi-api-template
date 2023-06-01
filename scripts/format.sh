#!/bin/sh -e
set -x

ruff app alembic --fix
black app alembic
isort app alembic --profile=black