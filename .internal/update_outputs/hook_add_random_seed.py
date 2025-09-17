#!/usr/bin/env python3
import json
import sys

RANDOM_SEED = 8

CELL_SET_RANDOM = {
    "cell_type": "code",
    "execution_count": None,
    "id": "12345678-90ab-cdef-1234-567890abcdef",
    "metadata": {},
    "outputs": [],
    "source": [
        "import random\n",
        "import numpy as np\n",
        "import torch\n",
        "\n",
        "\n",
        f"random.seed({RANDOM_SEED})\n",
        f"np.random.seed({RANDOM_SEED})\n",
        f"torch.manual_seed({RANDOM_SEED})",
    ],
}
# numpy random:
# 	https://stackoverflow.com/questions/58544946/how-to-set-the-fixed-random-seed-in-numpy
# torch random:
# 	https://pytorch.org/docs/stable/notes/randomness.html


def hook_random_seed(jupyter_notebook_file_path: str):
    with open(jupyter_notebook_file_path, "r") as f:
        data = json.load(f)

    version = int(data.get("nbformat", "0")), int(data.get("nbformat_minor", "0"))
    if version < (4, 5):
        cell_set_random = CELL_SET_RANDOM.copy()
        cell_set_random.pop("id")
    else:
        cell_set_random = CELL_SET_RANDOM

    if (
        type(data) is dict
        and "cells" in data
        and type(data["cells"]) is list
        and len(data["cells"]) > 0
    ):
        data["cells"].insert(0, cell_set_random)
        with open(jupyter_notebook_file_path, "w") as f:
            json.dump(data, f, indent=1)


def main(full_paths: list[str]) -> None:
    for file_path in full_paths:
        hook_random_seed(file_path)
    return True


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
