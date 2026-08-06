#!/usr/bin/env python3

from _common import get_cell_source, load_notebook, report, run_precommit, save_notebook

_STRIP_KEYS = [
    "id",
    "scrolled",
    "jp-MarkdownHeadingCollapsed",
    "editable",
    "is_executing",
    "pycharm",
    "vscode",
    "lines_to_next_cell",
    "executionInfo",
]

_STRIP_KEY_VALUES = [
    ("tags", []),
]

_STRIP_NESTED_KEYS = [
    ("jupyter", "outputs_hidden"),
    ("slideshow", "slide_type"),
]

_STRIP_NESTED_KEY_VALUES = [
    ("jupyter", "source_hidden", False),
]


def strip_single_notebook(notebook_path: str) -> bool:
    try:
        nb = load_notebook(notebook_path)
        did_nb_change = False

        for index, cell in enumerate(nb.cells):
            meta = cell.get("metadata", {})

            for key in _STRIP_KEYS:
                if key in meta:
                    nb.cells[index]["metadata"].pop(key)
                    did_nb_change = True

            for key, value in _STRIP_KEY_VALUES:
                if meta.get(key, None) == value:
                    nb.cells[index]["metadata"].pop(key)
                    did_nb_change = True

            for key, sub_key in _STRIP_NESTED_KEYS:
                if (
                    key in meta
                    and isinstance(key_value := meta[key], dict)
                    and sub_key in key_value
                ):
                    nb.cells[index]["metadata"][key].pop(sub_key)
                    did_nb_change = True
                    if not nb.cells[index]["metadata"][key]:
                        nb.cells[index]["metadata"].pop(key)

            for key, sub_key, value in _STRIP_NESTED_KEY_VALUES:
                if (
                    key in meta
                    and isinstance(key_value := meta[key], dict)
                    and sub_key in key_value
                    and key_value.get(sub_key, None) == value
                ):
                    nb.cells[index]["metadata"][key].pop(sub_key)
                    did_nb_change = True
                    if not nb.cells[index]["metadata"][key]:
                        nb.cells[index]["metadata"].pop(key)

        # A leading blank line hides the H1 title in the notebook UI
        if nb.cells and nb.cells[0].get("cell_type") == "markdown":
            text = get_cell_source(nb.cells[0])
            if (stripped := text.strip()) != text:
                nb.cells[0]["source"] = stripped.splitlines(keepends=True)
                did_nb_change = True

        if did_nb_change:
            report(notebook_path, "stripped unwanted metadata", fixed=True)
            save_notebook(notebook_path, nb)
            return False
    except Exception as exc:
        report(notebook_path, f"stripping metadata failed: {exc}")
        return False
    return True


if __name__ == "__main__":
    run_precommit(strip_single_notebook)
