import concurrent.futures
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Iterator

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from nbconvert import MarkdownExporter
from nbformat import NotebookNode, read as read_notebook

from app_store_plugins.conversion_fixes import fix_notebook
from app_store_plugins.external_links import add_external_links_to_markdown, REPO_ROOT


MarkdownResources = dict[str, str | bytes]

APP_STORE_DOCS_DIR = REPO_ROOT / ".internal" / "app-store" / "docs"
DIRECTORIES_TO_COPY = ["algorithms", "applications", "tutorials", "community"]
RESOURCE_EXTENSIONS = ["png", "jpg"]


def _all_resources(path: Path) -> Iterator[Path]:
    for extension in RESOURCE_EXTENSIONS:
        yield from path.rglob(f"*.{extension}")


class JupyterToMarkdown(BasePlugin):
    def _convert_notebook(self, full_path: Path, relative_path: Path) -> None:
        dest_dir = (APP_STORE_DOCS_DIR / relative_path).parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._copy_source_resources(full_path.parent, dest_dir)
        markdown, resources = self._create_markdown_and_resources(
            full_path, relative_path
        )
        dest_md = (dest_dir / full_path.name).with_suffix(".md")
        dest_md.write_text(markdown)
        self._copy_created_resources(resources, dest_dir)

    @staticmethod
    def _copy_source_resources(src_dir: Path, dest_dir: Path) -> None:
        for resource in _all_resources(src_dir):
            resource_dest = dest_dir / resource.relative_to(src_dir)
            resource_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(resource, resource_dest)

    @staticmethod
    def _copy_created_resources(resources: MarkdownResources, dest_dir: Path) -> None:
        for filename, data in resources.items():
            if isinstance(data, str):
                data = data.encode("utf-8")
            with open(dest_dir / filename, "wb") as f:
                f.write(data)

    @staticmethod
    def _create_markdown_and_resources(
        full_path: Path, relative_path: Path
    ) -> tuple[str, MarkdownResources]:
        with open(full_path) as f:
            notebook: NotebookNode = read_notebook(f, as_version=4)
        fix_notebook(notebook)
        exporter: MarkdownExporter = MarkdownExporter()
        markdown, resources = exporter.from_notebook_node(notebook)
        markdown = add_external_links_to_markdown(markdown, relative_path)
        return markdown, resources["outputs"]

    def on_pre_build(self, config: MkDocsConfig) -> None:
        with concurrent.futures.ProcessPoolExecutor() as executor, TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            for dir_to_copy in DIRECTORIES_TO_COPY:
                shutil.copytree(REPO_ROOT / dir_to_copy, tmpdir_path / dir_to_copy)
            futures = [
                executor.submit(
                    self._convert_notebook, notebook, notebook.relative_to(tmpdir_path)
                )
                for notebook in tmpdir_path.rglob("*.ipynb")
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    print("Notebook conversion generated an exception: %s", exc)
