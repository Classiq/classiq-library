"""Mock the classiq API inside a notebook's kernel, and record deprecation warnings.

`test_deprecations.py` injects `INSTALL_MOCK` as a cell, right before the notebook's first cell.
- Every classiq API call returns a fake result, from `fake_results.FAKES`. Nothing is sent
  to the Classiq platform: an API call without a fake raises `MockedClassiqApiCall`.
- The fakes can't reproduce real results, so the notebook's `assert` statements are
  skipped, like with `python -O`.
- Every deprecation warning is recorded. `REPORT` evaluates to them.
"""

import ast
import warnings

from classiq._internals import client
from classiq._internals.api_wrapper import ApiWrapper
from classiq._internals.authentication import password_manager, token_manager
from IPython import get_ipython
from tests.deprecations.fake_results import FAKES
from tests.utils_for_tests import ROOT_DIRECTORY

# The code that the test runs inside the notebook's kernel
INSTALL_MOCK = (
    f"import sys; sys.path.insert(0, {str(ROOT_DIRECTORY)!r})\n"
    f"from {__name__} import install; sys.path.pop(0); install()"
)
REPORT = f"__import__('sys').modules[{__name__!r}].report()"

DEPRECATIONS = (
    DeprecationWarning,
    PendingDeprecationWarning,
    FutureWarning,
    SyntaxWarning,
)


class MockedClassiqApiCall(Exception):
    """The deprecation test has no fake result for this classiq API call."""


def install() -> None:
    global _first_cell
    _first_cell = get_ipython().execution_count
    get_ipython().ast_transformers.append(_SkipAsserts())
    warnings.showwarning = _record_warning
    warnings.simplefilter("always")
    _mock_client()
    _install_fakes()


def report() -> list[dict]:
    return list(_warnings.values())


class _SkipAsserts(ast.NodeTransformer):
    def visit_Assert(self, node: ast.Assert) -> ast.Pass:
        return ast.copy_location(ast.Pass(), node)


#
# Recording warnings
#

_first_cell = 0  # the execution count of the cell that installs the mock
_warnings: dict[tuple, dict] = {}
_showwarning = warnings.showwarning


def _record_warning(message, category, filename, lineno, file=None, line=None):
    # IPython compiles each cell twice. The first compile, named "<>", warns before the cell starts.
    if issubclass(category, DEPRECATIONS) and filename != "<>":
        location = f"{filename.split('site-packages/')[-1]}:{lineno}"
        _warnings.setdefault(
            (category, str(message), location),
            {
                # The notebook's code cell: 1, 2, ... (the mock is installed right before them)
                "cell": get_ipython().execution_count - _first_cell,
                "category": category.__name__,
                "message": str(message),
                "location": location,
            },
        )
    _showwarning(message, category, filename, lineno, file, line)


#
# The client: no authentication, and no request leaves the kernel
#


def _mock_client() -> None:
    async def request(self, http_client, method, url, *args, **kwargs):
        raise MockedClassiqApiCall(f"{method.upper()} {url}")

    def sync_call_api(self, http_method, url, *args, **kwargs):
        raise MockedClassiqApiCall(f"{http_method.upper()} {url}")

    async def authenticate(self, overwrite):
        pass

    token_manager.TokenManager._make_password_manager = classmethod(
        lambda cls, config: password_manager.DummyPasswordManager()
    )
    client.Client.check_host = lambda self: None
    client.Client.authenticate = authenticate
    client.Client.request = request
    client.Client.sync_call_api = sync_call_api


#
# The fakes
#


def _install_fakes() -> None:
    for name, fake in FAKES.items():
        setattr(ApiWrapper, name, classmethod(_api_call(fake)))


def _api_call(fake):
    async def api_call(cls, *args, **kwargs):
        return fake(*args, **kwargs)

    return api_call
