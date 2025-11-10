#!/usr/bin/env python3

import sys
import json
import nbformat

VERSION_MAJOR = 4


def main() -> bool:
    result = True
    for file in sys.argv[1:]:
        result &= strip_single_notebook(file)
    return result


def strip_single_notebook(notebook_path: str) -> bool:
    result = True
    try:
        nb = nbformat.read(notebook_path, as_version=VERSION_MAJOR)
        did_nb_change = False

        for index, cell in enumerate(nb.cells):
            for key in [
                "id",
                # collapse/scroll
                "scrolled",
                "jp-MarkdownHeadingCollapsed",
                # kept from a notebook that was abruptly closed
                "editable",
                "is_executing",
                # other
                "pycharm",
                "vscode",
                # I think these are not actually used
                "lines_to_next_cell",
                # metadata we don't need
                "executionInfo",
            ]:
                if key in cell.get("metadata", {}):
                    nb.cells[index]["metadata"].pop(key)
                    did_nb_change = True

            for key, value in [
                # remove empty tags
                ("tags", [])
            ]:
                if cell.get("metadata", {}).get(key, None) == value:
                    nb.cells[index]["metadata"].pop(key)
                    did_nb_change = True

            for key, sub_key in [
                ("jupyter", "outputs_hidden"),
                ("slideshow", "slide_type"),
            ]:
                if (
                    key in cell.get("metadata", {})
                    and isinstance(key_value := cell["metadata"][key], dict)
                    and sub_key in key_value
                ):
                    nb.cells[index]["metadata"][key].pop(sub_key)
                    did_nb_change = True
                    # check if the parent key is now empty
                    if not nb.cells[index]["metadata"][key]:
                        nb.cells[index]["metadata"].pop(key)

            for key, sub_key, value in [
                ("jupyter", "source_hidden", False),
            ]:
                if (
                    key in cell.get("metadata", {})
                    and isinstance(key_value := cell["metadata"][key], dict)
                    and sub_key in key_value
                    and key_value.get(sub_key, None) == value
                ):
                    nb.cells[index]["metadata"][key].pop(sub_key)
                    did_nb_change = True
                    # check if the parent key is now empty
                    if not nb.cells[index]["metadata"][key]:
                        nb.cells[index]["metadata"].pop(key)

            # keys that were intentionally kept:
            # - colab

        if did_nb_change:
            result = False
            print(f"Rewriting '{notebook_path}'")
            nbformat.validate(nb)
            nbformat.write(nb, notebook_path)
    except Exception as exc:
        result = False
        print(f"Upgrading version failed for '{notebook_path}'. Error: {exc}")
    return result


if __name__ == "__main__":
    sys.exit(not main())
