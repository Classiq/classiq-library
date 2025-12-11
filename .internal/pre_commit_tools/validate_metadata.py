#!/usr/bin/env python3
# ruff: noqa: F841,E713

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
# Configuration
#
# if `DISABLED` is True, then nothing runs, and all the other flags are ignored.
IS_DISABLED: bool = True
# if `AUTO_FIX` is True, then the script
#   will automatically generate missing metadata files,
#   and will automatically delete un-needed metadata files
SHOULD_AUTO_FIX: bool = True
# if `VALIDATE_CONTENT` is False, then the only check will be "does a file exist"
#   and no content validation will happen
SHOULD_VALIDATE_METADATA_CONTENT: bool = True
# if `SKIP_MISSING` is True, then only existing fields will be validated
SHOULD_SKIP_MISSING_FIELDS: bool = True
# if `VALIDATE_SAME_NAME` is True, then, in the case where a folder has
#   a single `ipynb` file and a single `.qmod` file
#   then this pre-commit will enforce that they will have the same file name
SHOULD_VALIDATE_SAME_NAME: bool = True
# if `CLEAN_LEFTOVER` is True, then we will automatically delete un-needed metadata files
#   (and, if after deleting them, they will have an empty directory, it will also be deleted)
#   note that if `AUTO_FIX` is False, then we will not delete, we will only raise an error
SHOULD_CLEAN_LEFTOVER_METADATA: bool = True

#
# Metadata parameters
#

METADATA_FILE_JSON = ".metadata.json"

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
        name = os.path.basename(notebook)
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


def main(full_file_paths: Iterable[str], auto_fix: bool) -> bool:
    if IS_DISABLED:
        return True

    return validate_all_files(
        full_file_paths, auto_fix
    ) and clean_leftover_metadata_files(auto_fix)


def validate_all_files(full_file_paths: Iterable[str], auto_fix: bool) -> bool:
    errors = []

    for file in full_file_paths:
        if should_exclude_file(file):
            continue
        if error := validate_file(file, auto_fix):
            errors.append(error)
        if (
            SHOULD_VALIDATE_SAME_NAME
            and file.endswith(".ipynb")
            and (error := validate_same_name(file))
        ):
            errors.append(error)

    if errors:
        print("\n".join(errors))

    return not errors  # if not errors, return True = all is good


def validate_file(file: str, auto_fix: bool) -> str:
    errors = []

    if error := _validate_metadata_file_exists(file, auto_fix):
        return error
    if not SHOULD_VALIDATE_METADATA_CONTENT:
        return NO_ERROR

    metadata = _load_metadata(file)

    if not SHOULD_SKIP_MISSING_FIELDS and (
        error := _validate_metadata_fields(metadata, auto_fix, file)
    ):
        errors.append(error)
        if auto_fix:
            metadata = _load_metadata(file)  # reload

    for field_name in ["friendly_name", "description"]:
        if error := _validate_metadata_field_str(metadata, field_name):
            errors.append(error)

    for field_name, field_options in [
        ("vertical_tags", MetadataField_VerticalTag),
        ("problem_domain_tags", MetadataField_ProblemDomainTag),
        ("qmod_type", MetadataField_QmodType),
        ("level", MetadataField_Level),
    ]:
        if error := _validate_metadata_field_list(metadata, field_name, field_options):
            errors.append(error)

    if errors:
        errors.insert(0, f"File {file} contains {len(errors)} errors")
    return "\n\t".join(errors)


def _validate_metadata_file_exists(file: str, auto_fix: bool) -> str:
    filename, extension = os.path.splitext(file)
    metadata_file = filename + METADATA_FILE_JSON

    if not os.path.exists(metadata_file):
        if auto_fix:
            error = f"File '{file}' is missing a metadata file. Adding it. Please `git add` the new file '{metadata_file}'"
            if extra_error := generate_empty_metadata_file(metadata_file):
                error = f"{error}\n\t{extra_error}"
        else:
            error = f"File '{file}' is missing a metadata file. (Expecting '{metadata_file}')"
    else:
        error = NO_ERROR

    return error


def _load_metadata(file: str) -> dict:
    filename, extension = os.path.splitext(file)
    metadata_file = filename + METADATA_FILE_JSON

    with open(metadata_file) as f:
        return json.load(f)


def _dump_metadata(file: str, metadata: dict) -> None:
    filename, extension = os.path.splitext(file)
    metadata_file = filename + METADATA_FILE_JSON

    with open(metadata_file, "w") as f:
        return json.dump(metadata, f)


def _validate_metadata_fields(metadata: dict, auto_fix: bool, file: str) -> str:
    if sorted(EMPTY_METADATA) != sorted(metadata):
        if auto_fix:
            missing_keys = EMPTY_METADATA.keys() - metadata.keys()
            for key in missing_keys:
                if key in EMPTY_METADATA_GENERATION:
                    metadata[key] = EMPTY_METADATA_GENERATION[key](file)
                else:
                    metadata[key] = EMPTY_METADATA[key]

            extra_keys = metadata.keys() - EMPTY_METADATA.keys()
            for key in extra_keys:
                del metadata[key]

            _dump_metadata(file, metadata)
            return f"Wrote new metadata. Added missing keys ({missing_keys}), and removed extra keys ({extra_keys})"
        else:
            return f"There are extra/missing fields. Expecting to have exactly {list(EMPTY_METADATA)}"
    else:
        return NO_ERROR


def _validate_metadata_field_str(metadata: dict, field_name: str) -> str:
    if field_name not in metadata:
        if SHOULD_SKIP_MISSING_FIELDS:
            error = NO_ERROR
        else:
            error = f"The field {field_name} is missing"
    elif type(metadata[field_name]) is not str:
        error = f"Field {field_name} should be `str`"
    elif not metadata[field_name]:
        error = f"Field {field_name} cannot be an empty string"
    else:
        error = NO_ERROR

    return error


def _validate_metadata_field_list(
    metadata: dict, field_name: str, field_options: list[str]
) -> str:
    if field_name not in metadata:
        if SHOULD_SKIP_MISSING_FIELDS:
            error = NO_ERROR
        else:
            error = f"The field {field_name} is missing"
    elif type(metadata[field_name]) is not list:
        error = f"Field {field_name} should be `list`"
    elif not all(type(value) == str for value in metadata[field_name]):
        error = f"Field {field_name} should be `list` of `str`"
    elif not all(value in field_options for value in metadata[field_name]):
        error = f"Field {field_name} options must be a subset of {field_options}"
    else:
        error = NO_ERROR

    return error


def generate_empty_metadata_file(file_path: str) -> str:
    if os.path.exists(file_path):
        return f"Metadata file already exists ({file_path})"
    try:
        metadata = EMPTY_METADATA.copy()
        for key, func in EMPTY_METADATA_GENERATION.items():
            metadata[key] = func(file_path)

        with open(file_path, "w") as f:
            json.dump(metadata, f, indent=2)
        return ""  # empty string means no errors
    except Exception as exc:
        return str(exc)


def should_exclude_file(file_path: str) -> bool:
    return bool(
        re.search("(?:^|/)(?:functions|community|\\.ipynb_checkpoints)/", file_path)
    )


def clean_leftover_metadata_files(auto_fix: bool) -> bool:
    if not SHOULD_CLEAN_LEFTOVER_METADATA:
        return True

    result = True

    for file in PROJECT_ROOT.rglob("*" + METADATA_FILE_JSON):
        folder = file.parent
        base_name = file.name[: -len(METADATA_FILE_JSON)]

        if not (
            (folder / (base_name + ".qmod")).exists()
            or (folder / (base_name + ".ipynb")).exists()
        ):
            result = False
            if auto_fix:
                print(f"Deleting orphan metadata file: {file}")
                file.unlink()

                if is_dir_empty(folder):
                    print(f"Deleting its folder: {folder}")
                    folder.rmdir()
            else:
                print(
                    f"A metadata file with no `.qmod` or `.ipynb` files was found ({file})"
                )
    return result


def validate_same_name(file_path_ipynb: str) -> str:
    notebook_path = Path(file_path_ipynb)
    folder = notebook_path.parent
    qmods = list(folder.rglob("*.qmod"))

    error = NO_ERROR
    if len(qmods) == 1:
        expected_qmod_path = file_path_ipynb[: -len("ipynb")] + "qmod"
        if not str(qmods[0]) == expected_qmod_path:
            error = f"Notebook {file_path_ipynb} has a single qmod file. The qmod file sits in {qmods[0]}, but is expected to sit in {expected_qmod_path}"
    return error


def is_dir_empty(folder: Path) -> bool:
    try:
        next(folder.iterdir())
        return False
    except StopIteration:
        return True


if __name__ == "__main__":
    if not main(sys.argv[1:], SHOULD_AUTO_FIX):
        sys.exit(1)
