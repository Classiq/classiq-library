import ast
from collections.abc import Iterable

import nbformat
from utils_for_tests import iterate_notebooks


def test_imports():
    for notebook_path in iterate_notebooks():
        for cell_index, import_name in iterate_links_from_notebook(notebook_path):
            assert _test_single_import(
                import_name
            ), f'Invalid import found. in file "{notebook_path}", cell number {cell_index} (counting only code cells), the import: "{import_name}" is invalid. please import from `classiq` directly.'


def iterate_links_from_notebook(filename: str) -> Iterable[tuple[int, str]]:
    with open(filename) as f:
        notebook_data = nbformat.read(f, nbformat.NO_CONVERT)

    code_cells = [c for c in notebook_data["cells"] if c["cell_type"] == "code"]
    for cell_index, cell in enumerate(code_cells):
        for import_name in iterate_imported_modules(cell["source"]):
            yield cell_index, import_name


def _test_single_import(import_name: str) -> bool:
    if "classiq" in import_name:
        return import_name == "classiq"
    else:
        return True


def iterate_imported_modules(code: str) -> Iterable[str]:
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module
