#!/usr/bin/env python3
# ruff: noqa: F841,E713

import os
import re
import json
import sys
from collections.abc import Iterable
from pathlib import Path

from metadata_utils import (
    PROJECT_ROOT,
    ALL_FIELDS,
    ALL_FIELDS_BY_NAME,
    file_name_to_metadata_file_name,
    NO_ERROR,
    METADATA_FILE_JSON_SUFFIX,
    is_dir_empty,
    generate_empty_metadata_file,
    load_metadata,
    dump_metadata,
    FieldStr,
    FieldList,
)
from metadata_consts import (
    Config,
    FILES_TO_NOT_GENERATE_METADATA,
    FILES_TO_IGNORE_SAME_NAME,
)


def main(full_file_paths: Iterable[str], auto_fix: bool) -> bool:
    if Config.IS_DISABLED:
        return True

    result = validate_all_files(full_file_paths, auto_fix)
    if Config.SHOULD_CLEAN_LEFTOVER_METADATA:
        result &= clean_leftover_metadata_files(auto_fix)
    return result


def validate_all_files(full_file_paths: Iterable[str], auto_fix: bool) -> bool:
    errors = []

    for file in full_file_paths:
        if should_exclude_file(file):
            continue
        if error := validate_file(file, auto_fix):
            errors.append(error)
        if (
            Config.SHOULD_VALIDATE_SAME_NAME
            and file.endswith(".ipynb")
            and (error := validate_same_name(file))
        ):
            errors.append(error)

    if errors:
        print("\n".join(errors))

    return not errors  # if not errors, return True = all is good


def validate_file(file: str, auto_fix: bool) -> str:
    if error := _validate_metadata_file_exists(file, auto_fix):
        return error

    if not Config.SHOULD_VALIDATE_METADATA_CONTENT:
        return NO_ERROR

    errors = []
    metadata = load_metadata(file)

    # remove extra fields
    if error := _validate_no_extra_fields(metadata, auto_fix, file):
        errors.append(error)
        metadata = load_metadata(file)

    # add missing fields
    if error := _validate_no_missing_fields(metadata, auto_fix, file):
        errors.append(error)
        metadata = load_metadata(file)

    # validate field type and value
    if error := _validate_metadata_fields(metadata, auto_fix, file):
        errors.append(error)
        metadata = load_metadata(file)

    if errors:
        errors.insert(0, f"File {file} contains {len(errors)} errors")
    return "\n\t".join(errors)


def _validate_metadata_file_exists(file: str, auto_fix: bool) -> str:
    metadata_file = file_name_to_metadata_file_name(file)
    if not os.path.exists(metadata_file):
        if auto_fix:
            error = f"File '{file}' is missing a metadata file. Adding it. Please `git add` the new file '{metadata_file}'"
            if extra_error := generate_empty_metadata_file(file):
                error = f"{error}\n\t{extra_error}"
        else:
            error = f"File '{file}' is missing a metadata file. (Expecting '{metadata_file}')"
    else:
        error = NO_ERROR

    return error


def _validate_no_extra_fields(metadata: dict, auto_fix: bool, file: str) -> str:
    if Config.SHOULD_ALLOW_EXTRA_FIELDS:
        return NO_ERROR

    extra_fields = [field for field in metadata if field not in ALL_FIELDS_BY_NAME]
    if not extra_fields:
        return NO_ERROR

    if auto_fix:
        for field in extra_fields:
            metadata.pop(field)
        dump_metadata(file, metadata)
        return f"Removed extra metadata fields ({extra_fields})"
    else:
        return f"Metadata contains extra fields: ({extra_fields})"


def _validate_no_missing_fields(metadata: dict, auto_fix: bool, file: str) -> str:
    if Config.SHOULD_SKIP_MISSING_FIELDS:
        return NO_ERROR

    missing_fields = [field for field in ALL_FIELDS if field.name not in metadata]
    if not missing_fields:
        return NO_ERROR

    if auto_fix:
        for field in missing_fields:
            metadata[field.name] = field.generate_default_value(file)
        dump_metadata(file, metadata)
        return f"Added missing metadata fields ({missing_fields})"
    else:
        return f"Metadata has missing fields: ({missing_fields})"


def _validate_metadata_fields(metadata: dict, auto_fix: bool, file: str) -> str:
    errors = []
    # we may edit the dict while iterating it.
    #   our edits will alter the value, so that's a safe edit
    #   nontheless, we create a copy to iterate the copy
    metadata_copy = metadata.copy()

    for field_name, value in metadata_copy.items():
        if not Config.SHOULD_ALLOW_EXTRA_FIELDS:
            assert (
                field_name in ALL_FIELDS_BY_NAME
            ), f"Extra field found ({field_name}). Meaning that the previous `_validate_no_extra_fields` failed."

        field = ALL_FIELDS_BY_NAME[field_name]

        if not field.verify_type(value):
            errors.append(
                f"Field type error: {field_name} expects '{field._expected_type}', but got '{type(value)}'"
            )
            continue

        if not field.verify_value(value):
            if isinstance(field, FieldStr):
                errors.append(
                    f"Field value error: {field_name} expects non-empty string"
                )
            elif isinstance(field, FieldList):
                errors.append(
                    f"Field value error: {field_name} expects the value to be one of {field.allowed_values}"
                )

    if errors:
        return f"Metadata fields has {len(errors)} errors:\n\t\t" + "\n\t\t".join(
            errors
        )
    else:
        return NO_ERROR


def should_exclude_file(file_path: str) -> bool:
    return (
        bool(
            re.search("(?:^|/)(?:functions|community|\\.ipynb_checkpoints)/", file_path)
        )
        or os.path.basename(file_path) in FILES_TO_NOT_GENERATE_METADATA
    )


def validate_same_name(file_path_ipynb: str) -> str:
    if os.path.basename(file_path_ipynb) in FILES_TO_IGNORE_SAME_NAME:
        return NO_ERROR

    notebook_path = Path(file_path_ipynb)
    folder = notebook_path.parent
    qmods = list(folder.rglob("*.qmod"))

    error = NO_ERROR
    if len(qmods) == 1:
        expected_qmod_path = file_path_ipynb[: -len("ipynb")] + "qmod"
        if not str(qmods[0]) == expected_qmod_path:
            error = f"Notebook {file_path_ipynb} has a single qmod file. The qmod file sits in {qmods[0]}, but is expected to sit in {expected_qmod_path}"
    return error


def clean_leftover_metadata_files(auto_fix: bool) -> bool:
    if not Config.SHOULD_CLEAN_LEFTOVER_METADATA:
        return True

    result = True

    for file in PROJECT_ROOT.rglob("*" + METADATA_FILE_JSON_SUFFIX):
        folder = file.parent
        base_name = file.name[: -len(METADATA_FILE_JSON_SUFFIX)]

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


if __name__ == "__main__":
    if not main(sys.argv[1:], Config.SHOULD_AUTO_FIX):
        sys.exit(1)
