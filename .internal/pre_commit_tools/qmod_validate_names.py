#!/usr/bin/env python3

from functools import partial

from _common import run_precommit, validate_filename, validate_unique_names

if __name__ == "__main__":
    run_precommit(
        validate_filename,
        verify_all=partial(validate_unique_names, "*.qmod", "qmod file", {"functions"}),
        extension="*.qmod",
    )
