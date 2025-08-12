import re
from nbformat import NotebookNode


def fix_notebook(notebook: NotebookNode) -> None:
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            _fix_markdown_cell(cell)


def _fix_markdown_cell(markdown_cell: NotebookNode) -> None:
    # Latex block fix
    markdown_cell.source = re.sub(
        r"\$\$\s*(.*?)\s*\$\$", r"\n$$\1$$\n", markdown_cell.source, flags=re.DOTALL
    )
    # Inline Latex fix
    markdown_cell.source = re.sub(
        r"\$\s*(.*?)\s*\$", r"$\1$", markdown_cell.source, flags=re.DOTALL
    )
    # Math env Latex fix
    markdown_cell.source = re.sub(
        r"\n\\begin\{(.*?)\}\s*(.*?)\s*\\end\{\1\}",
        r"\n$\\begin{\1}\2\\end{\1}$",
        markdown_cell.source,
        flags=re.DOTALL,
    )
    # List fix
    markdown_cell.source = re.sub(
        r"\n*^(\s*)?([-+*]|(\d+\.) )",
        r"\n\n\1\2",
        markdown_cell.source,
        flags=re.MULTILINE,
    )
    # HTML fix
    markdown_cell.source = re.sub(
        r"<(?!/)(?!div\b)(\w+)(?<!\bmarkdown)(?=\s|>)",
        r"<\1 markdown",
        markdown_cell.source,
        flags=re.DOTALL,
    )
