import pytest

LAST = "test_last.py"


def pytest_collection_modifyitems(
    items: list[pytest.Function],
) -> list[pytest.Function]:
    return [i for i in items if i.module.__name__ != LAST] + [
        i for i in items if i.module.__name__ == LAST
    ]
