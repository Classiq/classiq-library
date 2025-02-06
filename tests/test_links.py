import re
from collections.abc import Iterable

import httpx
import nbformat
import pytest
from utils_for_tests import iterate_notebooks

# the regex below is taken from this stackoverflow:
#   https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
#   I only removed the brackets in the regex
# Update 2024/11/14 : removed `()` from the last `[...]`, since the regex was confused with the syntax `(... [...](...) )`
URL_REGEX = r"https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9@:%_\+.~#?&//=]*"
# urls come in `[title](url)`
URL_IN_MARKDOWN_REGEX = re.compile(r"(?<=\]\()%s(?=\s*\))" % URL_REGEX)


@pytest.mark.parametrize("notebook_path", iterate_notebooks())
def test_links(notebook_path: str) -> None:
    for cell_index, url in iterate_links_from_notebook(notebook_path):
        assert _test_single_url(
            url
        ), f'Broken link found! in file "{notebook_path}", cell number {cell_index} (counting only markdown cells), broken url: "{url}"'


def iterate_links_from_notebook(filename: str) -> Iterable[tuple[int, str]]:
    with open(filename) as f:
        notebook_data = nbformat.read(f, nbformat.NO_CONVERT)

    markdown_cells = [c for c in notebook_data["cells"] if c["cell_type"] == "markdown"]
    for cell_index, cell in enumerate(markdown_cells):
        found_urls = re.findall(URL_IN_MARKDOWN_REGEX, cell["source"])
        for url in found_urls:
            yield cell_index, url


def _test_single_url(
    url: str, retry: int = 3, use_head: bool = True, follow_redirects: bool = True
) -> bool:
    if retry == 0:
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        if use_head:
            response = httpx.head(url, headers=headers, follow_redirects=True)
        else:
            response = httpx.get(url, headers=headers, follow_redirects=True)

        # we don't check cloudflare links
        if (not response.is_success) and response.headers.get(
            "server", ""
        ).lower() == "cloudflare":
            return True

        # Method not allowed
        if response.status_code == 405:
            return _test_single_url(
                url, retry, use_head=False, follow_redirects=follow_redirects
            )
        # give another retry with GET
        if (not response.is_success) and use_head:
            return _test_single_url(
                url, retry - 1, use_head=False, follow_redirects=follow_redirects
            )
        if (not response.is_success) and follow_redirects:
            return _test_single_url(
                url, retry - 1, use_head=use_head, follow_redirects=False
            )
        # Some flaky error with "doi.org" links
        if response.status_code == 403:
            return _test_single_url(url, retry - 1, use_head=use_head)

        return response.is_success
    except httpx.HTTPError:
        return False
