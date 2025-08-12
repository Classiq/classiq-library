from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).parents[4]

CLASSIQ_PUBLIC_REPO = "https://github.com/Classiq/classiq-library/tree/main/"
IDE_MODEL_PAGE_ENDPOINT = "https://platform.classiq.io/dsl-synthesis"


@dataclass
class NotebookIDEAndGithubLinks:
    ide_link: str | None = None
    github_link: str | None = None


def _get_links_for_ide_and_github(
    notebook_relative_path: Path,
) -> NotebookIDEAndGithubLinks:
    links = NotebookIDEAndGithubLinks()
    if (REPO_ROOT / notebook_relative_path).is_file():
        links.github_link = f"{CLASSIQ_PUBLIC_REPO}{notebook_relative_path}"
    qmod_relative_path = notebook_relative_path.with_suffix(".qmod")
    if (REPO_ROOT / qmod_relative_path).is_file():
        links.ide_link = f"{IDE_MODEL_PAGE_ENDPOINT}#{qmod_relative_path}"
    return links


def _external_links_material_markdown_buttons(links: NotebookIDEAndGithubLinks) -> str:
    md_block = '<span class="doc-buttons">\n'

    if links.github_link:
        md_block += (
            f"[View on GitHub :material-github:]({links.github_link})"
            f"{{ .md-button .md-button--primary .doc-button target='_blank' }} "
        )

    if links.ide_link:
        md_block += (
            f"[Experiment in the IDE :material-microscope:]({links.ide_link})"
            f"{{ .md-button .md-button--primary .doc-button target='_blank' }}"
        )

    md_block += "\n</span>\n"
    return md_block


def _add_external_links_after_title(
    markdown: str, links: NotebookIDEAndGithubLinks
) -> str:
    lines = markdown.splitlines()
    lines_with_links = (
        lines[:1]
        + _external_links_material_markdown_buttons(links).splitlines()
        + lines[1:]
    )
    return "\n".join(lines_with_links)


def add_external_links_to_markdown(markdown: str, path_in_repo: Path) -> str:
    links = _get_links_for_ide_and_github(path_in_repo)
    markdown = _add_external_links_after_title(markdown, links)
    return markdown
