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
            # remove empty tags
            tags = cell.get("metadata", {}).get("tags", None)
            if tags == []:
                nb.cells[index]["metadata"].pop("tags")
                did_nb_change = True

            for key in [
                "pycharm",
                "id",
                "scrolled",
                "jp-MarkdownHeadingCollapsed",
                "editable",
            ]:
                if key in cell.get("metadata", {}):
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
                    # check if the parent key is now empty
                    if not nb.cells[index]["metadata"][key]:
                        nb.cells[index]["metadata"].pop(key)
                    did_nb_change = True

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
