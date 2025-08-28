#!/usr/bin/env python3
import json
import sys


def unhook_random_seed(jupyter_notebook_file_path: str):
    with open(jupyter_notebook_file_path, "r") as f:
        data = json.load(f)

    if (
        type(data) is dict
        and "cells" in data
        and type(data["cells"]) is list
        and len(data["cells"]) > 0
        and type(data["cells"][0]) is dict
        and data["cells"][0].get("cell_type", "not found") == "code"
        and type(data["cells"][0]["source"]) is list
        and "import random\n" in data["cells"][0]["source"]
    ):
        data["cells"].pop(0)

        for cell in data["cells"]:
            if (
                cell.get("cell_type", "not found") == "code"
                and type(cell.get("execution_count", None)) is int
            ):
                cell["execution_count"] = cell["execution_count"] - 1

        with open(jupyter_notebook_file_path, "w") as f:
            json.dump(data, f, indent=1)


def main(full_paths: list[str]) -> None:
    for file_path in full_paths:
        unhook_random_seed(file_path)
    return True


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
