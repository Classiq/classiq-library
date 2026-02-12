#!/bin/bash

export JUPYTER_PLATFORM_DIRS=1
export SHOULD_TEST_ALL_FILES=true
export BROWSER=$(which echo)
python -m pytest -Werror "$@"
