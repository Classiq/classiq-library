import os
import re
import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605

NO_ERROR = ""  # return types are str, so we treat an emtpy string as no error to simplify `if not error:=func()`


#
# Metadata parameters
#

METADATA_FILE_JSON_SUFFIX = ".metadata.json"

EMPTY_METADATA = {
    "friendly_name": "",
    "description": "",
    "vertical_tags": [],
    "problem_domain_tags": [],
    "qmod_type": [],
    "level": [],
}


def _auto_gen_description(file: str) -> str:
    with open(file) as f:
        data = json.load(f)

    if data["cells"][0]["cell_type"] == "markdown":
        return data["cells"][0]["source"][0].lstrip("#").strip()
    else:  # default
        return EMPTY_METADATA["description"]


def _auto_gen_friendly_name(file: str) -> str:
    try:
        name = os.path.basename(file)
        name = name[: -len(".ipynb")]
        name = name.replace("_", " ")
        name = name.title()
        return name
    except:
        return EMPTY_METADATA["friendly_name"]


EMPTY_METADATA_GENERATION = {
    "friendly_name": _auto_gen_friendly_name,
    "description": _auto_gen_description,
}

MetadataField_VerticalTag = [
    "automotive",
    "retail",
    "pharma",
    "cyber",
    "telecom",
]

MetadataField_QmodType = [
    "function",
    "gate",
    "application",
    "algorithms",
]

MetadataField_Level = [
    "basic",
    "advanced",
    "demos",
]

MetadataField_ProblemDomainTag = [
    "optimization",
    "chemistry",
    "ml",
    "linear equation",
    "search",
    "risk analysis",
]

METADATA_FIELD_STR: list[str] = ["friendly_name", "description"]
METADATA_FIELD_LIST: list[tuple[str, list[str]]] = [
    ("vertical_tags", MetadataField_VerticalTag),
    ("problem_domain_tags", MetadataField_ProblemDomainTag),
    ("qmod_type", MetadataField_QmodType),
    ("level", MetadataField_Level),
]


def load_metadata(file: str) -> dict:
    filename, extension = os.path.splitext(file)
    metadata_file = filename + METADATA_FILE_JSON_SUFFIX

    with open(metadata_file) as f:
        return json.load(f)


def dump_metadata(file: str, metadata: dict) -> None:
    filename, extension = os.path.splitext(file)
    metadata_file = filename + METADATA_FILE_JSON_SUFFIX

    with open(metadata_file, "w") as f:
        return json.dump(metadata, f)


def generate_empty_metadata_file(file_path: str, original_file_path: str) -> str:
    if os.path.exists(file_path):
        return f"Metadata file already exists ({file_path})"
    try:
        metadata = EMPTY_METADATA.copy()
        for key, func in EMPTY_METADATA_GENERATION.items():
            metadata[key] = func(original_file_path)

        with open(file_path, "w") as f:
            json.dump(metadata, f, indent=2)
        return NO_ERROR
    except Exception as exc:
        return str(exc)


def is_dir_empty(folder: Path) -> bool:
    try:
        next(folder.iterdir())
        return False
    except StopIteration:
        return True
