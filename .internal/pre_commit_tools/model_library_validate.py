#!/usr/bin/env python3
"""Validate the Model Library config (.internal/model_library/model_library_config.json).

The config lists the notebooks shown in the v2 web app's Model Library, each with a title,
a description and labels in four categories. The allowed labels are the config's own
`vocabulary`. Runs whenever the config or any notebook changes, so renaming or deleting a
listed notebook is caught too.
"""

import json
import sys
from pathlib import Path

from _common import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / ".internal" / "model_library" / "model_library_config.json"
CATEGORIES = ("domain", "framework", "building_block", "other")
ENTRY_KEYS = {"title", "description", "labels"}


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"duplicate keys: {duplicates}")
    return dict(pairs)


def _validate_vocabulary(vocabulary: object) -> list[str]:
    if not isinstance(vocabulary, dict) or set(vocabulary) != set(CATEGORIES):
        return [f"`vocabulary` must have exactly these lists: {list(CATEGORIES)}"]
    errors = []
    for category, terms in vocabulary.items():
        if not isinstance(terms, list) or not all(
            isinstance(term, str) and term.strip() for term in terms
        ):
            errors.append(
                f"vocabulary `{category}` must be a list of non-empty strings"
            )
        elif len(set(terms)) != len(terms):
            errors.append(f"vocabulary `{category}` has a repeated term")
    return errors


def _validate_entry(path: str, entry: object, vocabulary: dict) -> list[str]:
    if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
        return [f"{path}: must have exactly these keys: {sorted(ENTRY_KEYS)}"]
    errors = []
    if not path.endswith(".ipynb") or not (PROJECT_ROOT / path).is_file():
        errors.append(f"{path}: no such notebook")
    for key in ("title", "description"):
        if not isinstance(entry[key], str) or not entry[key].strip():
            errors.append(f"{path}: `{key}` must be a non-empty string")
    labels = entry["labels"]
    if not isinstance(labels, dict) or set(labels) != set(CATEGORIES):
        errors.append(
            f"{path}: `labels` must have exactly these lists: {list(CATEGORIES)}"
        )
        return errors
    for category in CATEGORIES:
        values = labels[category]
        if not isinstance(values, list):
            errors.append(f"{path}: labels `{category}` must be a list")
            continue
        unknown = [v for v in values if v not in vocabulary[category]]
        if unknown:
            errors.append(
                f"{path}: labels `{category}` not in the vocabulary: {unknown}"
            )
        if len(set(values)) != len(values):
            errors.append(f"{path}: labels `{category}` has a repeated label")
    return errors


def validate_config(config_path: Path = CONFIG_PATH) -> list[str]:
    try:
        config = json.loads(
            config_path.read_text(), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, ValueError) as error:
        return [f"cannot read the config: {error}"]
    if not isinstance(config, dict) or set(config) != {"vocabulary", "notebooks"}:
        return ["the config must have exactly two keys: `vocabulary` and `notebooks`"]
    errors = _validate_vocabulary(config["vocabulary"])
    if errors:
        return errors
    notebooks = config["notebooks"]
    if not isinstance(notebooks, dict) or not notebooks:
        return ["`notebooks` must be a non-empty object keyed by notebook path"]
    for path, entry in notebooks.items():
        errors.extend(_validate_entry(path, entry, config["vocabulary"]))
    return errors


if __name__ == "__main__":
    errors = validate_config()
    for error in errors:
        print(f"Model Library config: {error}")
    sys.exit(bool(errors))
