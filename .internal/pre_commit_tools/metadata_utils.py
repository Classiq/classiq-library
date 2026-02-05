import types
from dataclasses import dataclass
from typing import Callable, Any
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


@dataclass
class Field:
    name: str
    # Gets `notebook_file: str`, returns the default value of the appropriate type for the field
    generate_default_value: Callable[[str], Any]

    def verify_type(self, data: Any) -> bool:
        raise NotImplementedError

    def verify_value(self, data: Any) -> bool:
        raise NotImplementedError

    def get_value_error_message(self, data: Any) -> str:
        raise NotImplementedError


class FieldStr(Field):
    _expected_type = str

    def verify_type(self, data: Any) -> bool:
        return type(data) is str

    def verify_value(self, data: str) -> bool:
        # verify data is not empty
        return bool(data)


@dataclass
class FieldList(Field):
    allowed_values: list[str]

    _expected_type = list[str]

    def verify_type(self, data: Any) -> bool:
        # verify `list[str]`
        return type(data) is list and all(type(i) is str for i in data)

    def verify_value(self, data: list[str]) -> bool:
        return all(value in self.allowed_values for value in data)


def _auto_gen_description(file: str) -> str:
    with open(file) as f:
        data = json.load(f)

    if data["cells"][0]["cell_type"] == "markdown":
        return data["cells"][0]["source"][0].lstrip("#").strip()
    else:  # default
        return ""


def _auto_gen_friendly_name(file: str) -> str:
    try:
        name = os.path.basename(file)
        name = name[: -len(".ipynb")]
        name = name.replace("_", " ")
        name = name.title()
        return name
    except:
        return ""


# Order matters - that will be the order of the metadata file
ALL_FIELDS = [
    FieldStr("friendly_name", _auto_gen_friendly_name),
    FieldStr("description", _auto_gen_description),
    FieldList(
        "vertical_tags", list, ["finance", "retail", "pharma", "cyber", "telecom"]
    ),
    FieldList(
        "problem_domain_tags",
        list,
        [
            "optimization",
            "chemistry",
            "machine learning",
            "linear equation",
            "search",
            "risk analysis",
            # extras, may be ignores
            "adiabatic",
            "cfd",
        ],
    ),
    FieldList("qmod_type", list, ["function", "application", "algorithms"]),
    FieldList("level", list, ["basic", "advanced", "demos"]),
]

ALL_FIELDS_BY_NAME = {field.name: field for field in ALL_FIELDS}


def generate_empty_metadata_file(file: str) -> None:
    metadata = {field.name: field.generate_default_value(file) for field in ALL_FIELDS}
    return dump_metadata(file, metadata)


def load_metadata(file: str) -> dict:
    metadata_file = file_name_to_metadata_file_name(file)
    with open(metadata_file) as f:
        return json.load(f)


def dump_metadata(file: str, metadata: dict) -> None:
    priority = {"friendly_name": 0, "description": 1}
    sorted_metadata = dict(
        sorted(metadata.items(), key=lambda item: (priority.get(item[0], 100), item[0]))
    )

    metadata_file = file_name_to_metadata_file_name(file)
    with open(metadata_file, "w") as f:
        return json.dump(sorted_metadata, f, indent=2)


def file_name_to_metadata_file_name(file: str) -> str:
    filename, extension = os.path.splitext(file)
    metadata_file = filename + METADATA_FILE_JSON_SUFFIX
    return metadata_file


def is_dir_empty(folder: Path) -> bool:
    try:
        next(folder.iterdir())
        return False
    except StopIteration:
        return True
