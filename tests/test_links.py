import logging
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

logger = logging.getLogger(__name__)

# Domains that return specific HTTP error codes to CI (e.g. 403 bot-blocks)
_DOMAINS_BLOCKING_CI: dict[str, list[int]] = {
    "https://en.wikipedia.org/": [403],
    "https://pytorch.org/": [403],
}

# Domains that are unreachable from CI (connection times out)
_DOMAINS_TIMEOUT_IN_CI: set[str] = {
    "https://quantum-journal.org/",
    "https://theoryofcomputing.org/",
    "https://doi.org/10.22331/",  # redirects to quantum-journal.org
}

_URLS_BLOCKING_CI: dict[str, list[int]] = {
    "https://short.classiq.io/join-slack": [403, 302],
    "https://pubmed.ncbi.nlm.nih.gov/8604144/": [403],
    "https://users.cs.fiu.edu/~prabakar/ugc/2022/QC_notes/AndrewChilds_qa.pdf": [403],
    "https://www.e3s-conferences.org/articles/e3sconf/pdf/2019/50/e3sconf_ses18_04011.pdf": [
        403
    ],
    "https://www.mdpi.com/1099-4300/27/5/454": [403],
}

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

_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


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


def should_check_file_instead_of_url(url: str) -> bool:
    return url.lower().startswith(URL_GITHUB_PREFIX)


def check_file_instead_of_url(url: str) -> bool:
    file_location = url[len(URL_GITHUB_PREFIX) :]
    return (ROOT_DIRECTORY / file_location).is_file()


def _test_single_url(url: str) -> bool:
    """One-time checks that apply regardless of retry state."""
    if should_check_file_instead_of_url(url):
        return check_file_instead_of_url(url)

    if os.environ.get("LIMIT_TEST_LINKS_TO_FILES_ONLY", "false").lower() == "true":
        return True  # Don't test anything else. Treat as valid.

    if any(url.startswith(allowed) for allowed in get_url_allow_list()):
        return True

    return _try_url(url)


def _try_url(
    url: str,
    retry: int = NUM_RETRIES,
    use_head: bool = True,
    follow_redirects: bool = True,
) -> bool:
    if retry == 0:
        return False

    if retry < NUM_RETRIES:
        time.sleep(0.08)

    try:
        if use_head:
            response = httpx.head(
                url, headers=_REQUEST_HEADERS, follow_redirects=follow_redirects
            )
        else:
            response = httpx.get(
                url, headers=_REQUEST_HEADERS, follow_redirects=follow_redirects
            )

        # Cloudflare blocks us; treat as valid
        if (
            not response.is_success
            and response.headers.get("server", "").lower() == "cloudflare"
        ):
            return True

        # Known CI-blocking domains/URLs: server is reachable but actively refuses
        if any(
            url.startswith(prefix) and response.status_code in codes
            for prefix, codes in _DOMAINS_BLOCKING_CI.items()
        ):
            logger.info(
                "Got %d for %s — known CI-blocking domain, treating as valid",
                response.status_code,
                url,
            )
            return True
        if response.status_code in _URLS_BLOCKING_CI.get(url, []):
            logger.info(
                "Got %d for %s (final URL: %s) — known CI-blocking URL, treating as valid",
                response.status_code,
                url,
                response.url,
            )
            return True

        # Method not allowed → retry with GET
        if response.status_code == 405:
            return _try_url(
                url, retry - 1, use_head=False, follow_redirects=follow_redirects
            )

        # Rate limited → wait then retry
        if response.status_code == 429:
            # not sure what the rate limit we have, but it may be "X per hour" or "X per minute"
            # so let's add half-a-minute
            time.sleep(31)
            return _try_url(
                url, retry - 1, use_head=use_head, follow_redirects=follow_redirects
            )

        # HEAD rejected → retry with GET
        if not response.is_success and use_head:
            return _try_url(
                url, retry - 1, use_head=False, follow_redirects=follow_redirects
            )

        # Failed with redirects → retry without
        if not response.is_success and follow_redirects:
            return _try_url(url, retry - 1, use_head=use_head, follow_redirects=False)

        # Still 403 after exhausting HEAD/GET and redirect variants → retry fresh
        if response.status_code == 403:
            logger.info("Got 403 for %s (final URL: %s)", url, response.url)
            return _try_url(url, retry - 1, use_head=use_head, follow_redirects=True)

        # Log if any bypass entries appear stale (URL now reachable from CI)
        if response.is_success and any(url.startswith(p) for p in _DOMAINS_BLOCKING_CI):
            logger.info(
                "Got %d for %s — CI-blocking domain bypass may be removable",
                response.status_code,
                url,
            )
        if response.is_success and any(
            url.startswith(p) for p in _DOMAINS_TIMEOUT_IN_CI
        ):
            logger.info(
                "Got %d for %s — CI-timeout domain bypass may be removable",
                response.status_code,
                url,
            )
        if response.is_success and url in _URLS_BLOCKING_CI:
            logger.info(
                "Got %d for %s — CI-blocking URL bypass may be removable",
                response.status_code,
                url,
            )

        return response.is_success

    except httpx.TimeoutException:
        # Known CI-unreachable domains: server doesn't respond at all
        if any(url.startswith(prefix) for prefix in _DOMAINS_TIMEOUT_IN_CI):
            logger.info(
                "Timeout for %s — known CI-unreachable domain, treating as valid", url
            )
            return True
        return _try_url(
            url, retry - 1, use_head=use_head, follow_redirects=follow_redirects
        )

    except httpx.HTTPError:
        return _try_url(
            url, retry - 1, use_head=use_head, follow_redirects=follow_redirects
        )
