#!/usr/bin/env bash

set -e
set -x

coverage run -m pytest
# coverage combine
coverage report --show-missing
coverage html