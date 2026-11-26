#!/usr/bin/env python3
"""
usage: update_links.py <notebook to update> <notebook to take the links from>

copies the platform links into the outputs of a notebook, keeping the rest of its outputs as they are
"""

import re
import sys

from notebook_utils import read_notebook, write_notebook

LINK_PATTERN = re.compile(
    r"Quantum program link: https://platform\.classiq\.io/circuit/\S+\n"
)

# cell index ; output index ; the link itself
Link = tuple[int, int, str]


def extract_links(cells: list[dict]) -> list[Link]:
    links = []
    for cell_index, cell in enumerate(cells):
        if cell.get("cell_type", "") == "code":
            outputs = cell.get("outputs", [])
            for output_index, output in enumerate(outputs):
                text = (
                    "".join(output.get("text", []))
                    if isinstance(output.get("text"), list)
                    else output.get("text", "")
                )
                match = LINK_PATTERN.search(text)
                if match:
                    links.append((cell_index, output_index, match.group(0)))
    return links


def validate_links(old_links: list[Link], new_links: list[Link]) -> bool:
    if len(old_links) != len(new_links):
        print(
            f"Error: the notebook printed {len(new_links)} links, but its outputs have {len(old_links)}",
            file=sys.stderr,
        )
        return False

    old_cell_indices = [cell_index for cell_index, _, _ in old_links]
    new_cell_indices = [cell_index for cell_index, _, _ in new_links]
    if old_cell_indices != new_cell_indices:
        print(
            "Error: the notebook printed its links in other cells than in its outputs",
            file=sys.stderr,
        )
        return False

    return True


def update_links(
    cells: list[dict], old_links: list[Link], new_links: list[Link]
) -> bool:
    for (cell_index, output_index, old_link), (_, _, new_link) in zip(
        old_links, new_links
    ):
        output = cells[cell_index]["outputs"][output_index]
        text = output["text"]
        for index, line in enumerate(text):
            if old_link in line:
                text[index] = line.replace(old_link, new_link)
                break
        else:
            print(
                "Error: couldn't find a link. this shouldn't happen.", file=sys.stderr
            )
            return False
    return True


def main(dest_file: str, source_file: str) -> bool:
    old_nb = read_notebook(dest_file)
    new_nb = read_notebook(source_file)

    old_links = extract_links(old_nb["cells"])
    new_links = extract_links(new_nb["cells"])

    if not validate_links(old_links, new_links):
        return False

    if not update_links(old_nb["cells"], old_links, new_links):
        return False

    write_notebook(dest_file, old_nb)

    print(f"Updated notebook written to: {dest_file}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            f"usage: {sys.argv[0]} <notebook to update> <notebook to take the links from>",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(not main(sys.argv[1], sys.argv[2]))
