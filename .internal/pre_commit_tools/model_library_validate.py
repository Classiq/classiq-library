#!/usr/bin/env python3
"""Validate the Model Library lists in `.internal/model_library/`.

Every notebook in MODEL_LIBRARY_FOLDERS is listed in exactly one file:
- `model_library_config.json`: shown in the Model Library, with a title, a description
  and labels. The allowed labels are the config's own `vocabulary`.
- `model_library_excluded.json`: not shown. Kept sorted automatically.
So a new notebook fails this hook until someone decides which list it belongs to.
"""

import json
import sys
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StringConstraints,
    TypeAdapter,
    ValidationError,
)

from _common import PROJECT_ROOT, report

# The Model Library shows notebooks from these folders only
MODEL_LIBRARY_FOLDERS = ("algorithms", "applications")

CONFIG_PATH = ".internal/model_library/model_library_config.json"
EXCLUDED_PATH = ".internal/model_library/model_library_excluded.json"


def main() -> bool:
    config = load(CONFIG_PATH, ModelLibraryConfig)
    excluded = load(EXCLUDED_PATH, UniqueStrList)
    if config is None or excluded is None:
        return False
    return all(
        [
            sort_excluded(excluded),
            validate_labels(config),
            validate_coverage(config, excluded),
        ]
    )


#
# Schema
#


def _reject_repeats(items: list[str]) -> list[str]:
    if repeated := sorted({item for item in items if items.count(item) > 1}):
        raise ValueError(f"repeated: {repeated}")
    return items


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
UniqueStrList = Annotated[list[NonEmptyStr], AfterValidator(_reject_repeats)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Labels(StrictModel):
    domain: UniqueStrList
    framework: UniqueStrList
    building_block: UniqueStrList
    other: UniqueStrList


class Entry(StrictModel):
    title: NonEmptyStr
    description: NonEmptyStr
    labels: Labels


class ModelLibraryConfig(StrictModel):
    vocabulary: Labels
    notebooks: dict[str, Entry]


#
# Validation
#


def load(path: str, schema: Any) -> Any | None:
    """Parse `path` into `schema`; report every mismatch and return None if any."""
    try:
        return TypeAdapter(schema).validate_json((PROJECT_ROOT / path).read_text())
    except OSError as error:
        report(path, f"cannot read the file: {error}")
    except ValidationError as error:
        for e in error.errors():
            _report(path, e["loc"], e["msg"])
    return None


def sort_excluded(excluded: list[str]) -> bool:
    """Auto-fix: keep the excluded list sorted."""
    if excluded == sorted(excluded):
        return True
    (PROJECT_ROOT / EXCLUDED_PATH).write_text(
        json.dumps(sorted(excluded), indent=2) + "\n"
    )
    report(EXCLUDED_PATH, "sorted the list — please `git add`", fixed=True)
    return False


def validate_labels(config: ModelLibraryConfig) -> bool:
    """Every label is a term from the vocabulary of its category."""
    vocabulary = config.vocabulary.model_dump()
    result = True
    for path, entry in config.notebooks.items():
        for category, labels in entry.labels.model_dump().items():
            if unknown := sorted(set(labels) - set(vocabulary[category])):
                _report(
                    CONFIG_PATH,
                    ("notebooks", path, "labels", category),
                    f"not in the vocabulary: {unknown} — use a term from "
                    f"`vocabulary > {category}`, or add it there",
                )
                result = False
    return result


def validate_coverage(config: ModelLibraryConfig, excluded: list[str]) -> bool:
    """Every notebook in MODEL_LIBRARY_FOLDERS is in exactly one of the two lists."""
    notebooks = _notebooks_on_disk()
    shown, hidden = set(config.notebooks), set(excluded)
    folders = " or ".join(f"{folder}/" for folder in MODEL_LIBRARY_FOLDERS)
    result = True

    for path in sorted(notebooks - shown - hidden):
        report(
            path,
            f"not in the Model Library lists — add it to {CONFIG_PATH} (with a "
            f"title, a description and labels) to show it, or to {EXCLUDED_PATH}",
        )
        result = False

    for path in sorted(shown & hidden):
        report(path, f"in both {CONFIG_PATH} and {EXCLUDED_PATH} — keep one")
        result = False

    for list_path, paths in ((CONFIG_PATH, shown), (EXCLUDED_PATH, hidden)):
        for path in sorted(paths - notebooks):
            report(
                list_path,
                f"{path}: no such notebook in {folders} — if you renamed or moved "
                "it, update the path; if you deleted it, remove the entry",
            )
            result = False

    return result


def _notebooks_on_disk() -> set[str]:
    return {
        path.relative_to(PROJECT_ROOT).as_posix()
        for folder in MODEL_LIBRARY_FOLDERS
        for path in (PROJECT_ROOT / folder).rglob("*.ipynb")
        if ".ipynb_checkpoints" not in path.parts
    }


def _report(file: str, location: tuple, message: str) -> None:
    report(file, f"{' > '.join(map(str, location))}: {message}")


if __name__ == "__main__":
    sys.exit(not main())
