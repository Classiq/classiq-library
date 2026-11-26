#!/bin/bash

export SHOULD_TEST_ALL_FILES=true
export BROWSER=$(which echo)
python -W error -m pytest "$@"
