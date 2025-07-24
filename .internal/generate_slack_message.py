#!/usr/bin/env python3
import sys
from pathlib import Path


def get_notebook_description(notebook_path: Path) -> str:
    """
    Dummy description loader.
    You can customize this to:
    - Read metadata from the notebook
    - Or from a separate description file
    Currently returns a placeholder.
    """
    return f"Short description for `{notebook_path.name}`."


def _get_notebooks() -> tuple[list[str], int]:
    if len(sys.argv) != 2:
        print(
            'USAGE: generate_slack_message.py "<space-separated list of notebook paths>"',
            file=sys.stderr,
        )
        sys.exit(1)

    notebooks = sys.argv[1].split()

    if not notebooks:
        print("No new notebooks were provided.", file=sys.stderr)
        sys.exit(2)

    return notebooks


def main():
    _get_notebooks = _get_notebooks()

    if len(notebooks) == 1:
        header = "Hurray! A new notebook was added! What a wonderful day!\n"
    else:
        header = f"Hurray! {len(notebooks)} new notebooks were added! What a wonderful day!\n"
    print(header)

    for notebook in notebooks:
        notebook_path = Path(notebook)
        notebook_name = notebook_path.stem
        description = get_notebook_description(notebook_path)
        print(f"*{notebook_name}*:\n{description}\n")


if __name__ == "__main__":
    main()
