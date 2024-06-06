import re
from collections.abc import Iterable

import httpx
import nbformat
from utils_for_tests import iterate_notebooks

# the regex below is taken from this stackoverflow:
#   https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
#   I only removed the brackets in the regex
URL_REGEX = r"https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*"
# urls come in `[title](url)`
URL_IN_MARKDOWN_REGEX = re.compile(r"(?<=\]\()%s(?=\s*\))" % URL_REGEX)


def test_links() -> None:
    for notebook_path in iterate_notebooks():
        for cell_index, url in iterate_links_from_notebook(notebook_path):
            assert _test_single_url(
                url
            ), f'Broken link found! in file "{notebook_path}", cell number {cell_index} (counting only markdown cells), broken url: "{url}"'


def iterate_links_from_notebook(filename: str) -> Iterable[tuple[int, str]]:
    with open(filename) as f:
        notebook_data = nbformat.read(f, nbformat.NO_CONVERT)  # type: ignore[no-untyped-call]

    markdown_cells = [c for c in notebook_data["cells"] if c["cell_type"] == "markdown"]
    for cell_index, cell in enumerate(markdown_cells):
        found_urls = re.findall(URL_IN_MARKDOWN_REGEX, cell["source"])
        for url in found_urls:
            yield cell_index, url


def _test_single_url(url: str) -> bool:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        response = httpx.head(url, headers=headers, follow_redirects=True)
        return response.is_success
    except httpx.HTTPError:
        return False
