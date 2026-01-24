#!/bin/sh -e
set -x

ruff check app --fix
ruff format app
black app
isort app --profile=black
