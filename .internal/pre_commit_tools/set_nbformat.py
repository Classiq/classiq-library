#!/usr/bin/env python3

import sys
import json
import nbformat

VERSION_MAJOR = 4
VERSION_MINOR = 9


def main() -> bool:
    result = True
    for file in sys.argv[1:]:
        result &= update_single_notebook(file)
    return result


def update_single_notebook(notebook_path: str) -> bool:
    result = True
    try:
        nb = nbformat.read(notebook_path, as_version=VERSION_MAJOR)

        if (nb.nbformat, nb.nbformat_minor) != (VERSION_MAJOR, VERSION_MINOR):
            result = False  # this file required change
            print(
                f"Updating notebook version from {(nb.nbformat, nb.nbformat_minor)} to {(VERSION_MAJOR, VERSION_MINOR)} for '{notebook_path}'"
            )

            nb.nbformat = VERSION_MAJOR
            nb.nbformat_minor = VERSION_MINOR
            nbformat.validate(nb)
            nbformat.write(nb, notebook_path)
    except Exception as exc:
        result = False
        print(f"Upgrading version failed for '{notebook_path}'. Error: {exc}")
    return result


if __name__ == "__main__":
    sys.exit(not main())
