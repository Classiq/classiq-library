import json


def read_notebook(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_notebook(path: str, notebook: dict) -> None:
    # the same format as `nbformat.write` - unescaped unicode, and a trailing newline
    # so that rewriting a notebook changes only what we've edited
    with open(path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write("\n")
