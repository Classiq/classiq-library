#!/usr/bin/env python3

from _common import load_notebook, report, run_precommit, save_notebook

VERSION_MAJOR = 4
VERSION_MINOR = 9


def update_single_notebook(notebook_path: str) -> bool:
    try:
        nb = load_notebook(notebook_path)

        if (nb.nbformat, nb.nbformat_minor) != (VERSION_MAJOR, VERSION_MINOR):
            nb.nbformat = VERSION_MAJOR
            nb.nbformat_minor = VERSION_MINOR
            save_notebook(notebook_path, nb)
            report(
                notebook_path,
                f"updated nbformat version to ({VERSION_MAJOR}, {VERSION_MINOR})",
                fixed=True,
            )
            return False
    except Exception as exc:
        report(notebook_path, f"upgrading version failed: {exc}")
        return False
    return True


if __name__ == "__main__":
    run_precommit(update_single_notebook)
