import os
import re
import time
from collections.abc import Iterable

from functools import lru_cache
import httpx
import nbformat
import pytest
from utils_for_tests import (
    iterate_notebook_names,
    resolve_notebook_path,
    ROOT_DIRECTORY,
)

URL_ALLOW_LIST_FILE = ROOT_DIRECTORY / ".internal" / "url_allow_list.txt"
URL_GITHUB_PREFIX = "https://github.com/classiq/classiq-library/blob/main/"

# the regex below is taken from this stackoverflow:
#   https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
#   I only removed the brackets in the regex
# Update 2024/11/14 : removed `()` from the last `[...]`, since the regex was confused with the syntax `(... [...](...) )`
URL_REGEX = r"https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9@:%_\+.~#?&//=]*"
# urls come in `[title](url)`
URL_IN_MARKDOWN_REGEX = re.compile(r"(?<=\]\()%s(?=\s*\))" % URL_REGEX)

NUM_RETRIES = 5


@pytest.mark.parametrize("notebook_path", iterate_notebook_names())
def test_links(notebook_path: str) -> None:
    broken_links_messages = []
    for cell_index, url in iterate_links_from_notebook(notebook_path):
        if not _test_single_url(url):
            broken_links_messages.append(
                f'Broken link found! (#{len(broken_links_messages)+1}) in file "{notebook_path}", cell number {cell_index} (counting only markdown cells), broken url: "{url}"'
            )

    assert not broken_links_messages, (
        f'Found {len(broken_links_messages)} broken links in "{notebook_path}": \n\t'
        + "\n\t".join(broken_links_messages)
    )


def iterate_links_from_notebook(filename: str) -> Iterable[tuple[int, str]]:
    with open(resolve_notebook_path(filename)) as f:
        notebook_data = nbformat.read(f, nbformat.NO_CONVERT)

    markdown_cells = [c for c in notebook_data["cells"] if c["cell_type"] == "markdown"]
    for cell_index, cell in enumerate(markdown_cells):
        found_urls = re.findall(URL_IN_MARKDOWN_REGEX, cell["source"])
        for url in found_urls:
            yield cell_index, url


@lru_cache
def get_url_allow_list() -> list[str]:
    if URL_ALLOW_LIST_FILE.is_file():
        with open(URL_ALLOW_LIST_FILE) as f:
            data = f.read()
        return data.splitlines()
    else:
        return []


def check_file_instead_of_url(url: str) -> bool:
    if not url.lower().startswith(URL_GITHUB_PREFIX):
        return False

    file_location = url[len(URL_GITHUB_PREFIX) :]
    return (ROOT_DIRECTORY / file_location).is_file()


def _test_single_url(
    url: str,
    retry: int = NUM_RETRIES,
    use_head: bool = True,
    follow_redirects: bool = True,
) -> bool:
    if check_file_instead_of_url(url):
        return True

    if os.environ.get("LIMIT_TEST_LINKS_TO_FILES_ONLY", "false").lower() == "true":
        return True  # if we only wish to check files, then we end this test here.

    if any(url.startswith(allowed) for allowed in get_url_allow_list()):
        return True

    if retry == 0:
        return False

    if retry < NUM_RETRIES:
        time.sleep(0.08)

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
        # Too Many Requests
        if response.status_code == 429:
            # not sure what the rate limit we have, but it may be "X per hour" or "X per minute"
            # so let's add half-a-minute
            time.sleep(31)
            return _test_single_url(
                url,
                retry=retry - 1,
                use_head=use_head,
                follow_redirects=follow_redirects,
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
        return _test_single_url(
            url, retry=retry - 1, use_head=use_head, follow_redirects=follow_redirects
        )
