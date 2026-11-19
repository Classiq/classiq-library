#!/usr/bin/env python3

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
            print("Couldn't find link. This shouldn't happen.")
            return False
    return True


def validate_links_list(
    old_links: list[Link], new_links: list[Link], force: bool
) -> bool:
    # verify list length
    if len(old_links) != len(new_links):
        print("Error: Link count mismatch")
        return False

    if force:
        # verify cell index
        old_indices = [cell_index for cell_index, _, _ in old_links]
        new_indices = [cell_index for cell_index, _, _ in new_links]
        if old_indices != new_indices:
            print("Error: Link cell indices mismatch")
            return False

        # verify link pattern
        if not all(LINK_PATTERN.match(link) for _, _, link in new_links):
            print("Error: Not all new links match expected pattern")
            return False

    return True


def main(dest_file: str, source_file: str, force: bool = False) -> bool:
    old_nb = read_notebook(dest_file)
    new_nb = read_notebook(source_file)

    old_links = extract_links(old_nb["cells"])
    new_links = extract_links(new_nb["cells"])

    if not validate_links_list(old_links, new_links, force):
        return False

    if not update_links(old_nb["cells"], old_links, new_links):
        return False

    write_notebook(dest_file, old_nb)

    print(f"Updated notebook written to: {dest_file}")
    return True


if __name__ == "__main__":
    force = False
    if "--force" in sys.argv:
        force = True
        sys.argv.remove("--force")

    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <file in which we'll update the links> <file from which to take the links> [--force]"
        )
        sys.exit(1)

    if not main(sys.argv[1], sys.argv[2], force):
        sys.exit(1)
