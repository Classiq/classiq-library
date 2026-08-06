#!/usr/bin/env python3
# ruff: noqa: F841,E713

import os
import re
from functools import partial
from pathlib import Path

from _common import report, run_precommit
from metadata_utils import (
    PROJECT_ROOT,
    ALL_FIELDS,
    ALL_FIELDS_BY_NAME,
    file_name_to_metadata_file_name,
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


def check_single_file(file: str, auto_fix: bool) -> bool:
    result = validate_file(file, auto_fix)
    if (
        Config.SHOULD_VALIDATE_SAME_NAME
        and file.endswith(".ipynb")
        and not validate_same_name(file)
    ):
        result = False
    return result


def validate_file(file: str, auto_fix: bool) -> bool:
    if not _validate_metadata_file_exists(file, auto_fix):
        return False

    if not Config.SHOULD_VALIDATE_METADATA_CONTENT:
        return True

    result = True
    metadata = load_metadata(file)

    if not _validate_no_extra_fields(metadata, auto_fix, file):
        result = False
        metadata = load_metadata(file)

    if not _validate_no_missing_fields(metadata, auto_fix, file):
        result = False
        metadata = load_metadata(file)

    if not _validate_metadata_fields(metadata, auto_fix, file):
        result = False

    return result


def _validate_metadata_file_exists(file: str, auto_fix: bool) -> bool:
    metadata_file = file_name_to_metadata_file_name(file)
    if os.path.exists(metadata_file):
        return True

    if auto_fix:
        report(
            file,
            f"missing metadata file — adding '{metadata_file}', please `git add`",
            fixed=True,
        )
        if extra_error := generate_empty_metadata_file(file):
            report(file, extra_error)
    else:
        report(file, f"missing metadata file (expecting '{metadata_file}')")
    return False


def _validate_no_extra_fields(metadata: dict, auto_fix: bool, file: str) -> bool:
    if Config.SHOULD_ALLOW_EXTRA_FIELDS:
        return True

    extra_fields = [field for field in metadata if field not in ALL_FIELDS_BY_NAME]
    if not extra_fields:
        return True

    if auto_fix:
        for field in extra_fields:
            metadata.pop(field)
        dump_metadata(file, metadata)
        report(file, f"removed extra metadata fields ({extra_fields})", fixed=True)
    else:
        report(file, f"metadata contains extra fields: ({extra_fields})")
    return False


def _validate_no_missing_fields(metadata: dict, auto_fix: bool, file: str) -> bool:
    if Config.SHOULD_SKIP_MISSING_FIELDS:
        return True

    missing_fields = [field for field in ALL_FIELDS if field.name not in metadata]
    if not missing_fields:
        return True

    if auto_fix:
        for field in missing_fields:
            metadata[field.name] = field.generate_default_value(file)
        dump_metadata(file, metadata)
        report(file, f"added missing metadata fields ({missing_fields})", fixed=True)
    else:
        report(file, f"metadata has missing fields: ({missing_fields})")
    return False


def _validate_metadata_fields(metadata: dict, auto_fix: bool, file: str) -> bool:
    result = True
    # iterating a copy because auto_fix may edit the dict
    metadata_copy = metadata.copy()

    for field_name, value in metadata_copy.items():
        if not Config.SHOULD_ALLOW_EXTRA_FIELDS:
            assert (
                field_name in ALL_FIELDS_BY_NAME
            ), f"Extra field found ({field_name}). Meaning that the previous `_validate_no_extra_fields` failed."

        field = ALL_FIELDS_BY_NAME[field_name]

        if not field.verify_type(value):
            report(
                file,
                f"field type error: {field_name} expects '{field._expected_type}', got '{type(value)}'",
            )
            result = False
            continue

        if not field.verify_value(value):
            if isinstance(field, FieldStr):
                report(
                    file, f"field value error: {field_name} expects non-empty string"
                )
            elif isinstance(field, FieldList):
                report(
                    file,
                    f"field value error: {field_name} expects one of {field.allowed_values}",
                )
            result = False

    return result


def should_exclude_file(file_path: str) -> bool:
    return (
        bool(
            re.search("(?:^|/)(?:functions|community|\\.ipynb_checkpoints)/", file_path)
        )
        or os.path.basename(file_path) in FILES_TO_NOT_GENERATE_METADATA
    )


def validate_same_name(file_path_ipynb: str) -> bool:
    if os.path.basename(file_path_ipynb) in FILES_TO_IGNORE_SAME_NAME:
        return True

    notebook_path = Path(file_path_ipynb)
    folder = notebook_path.parent
    qmods = list(folder.rglob("*.qmod"))

    if len(qmods) == 1:
        expected_qmod_path = file_path_ipynb[: -len("ipynb")] + "qmod"
        if str(qmods[0]) != expected_qmod_path:
            report(
                file_path_ipynb,
                f"single qmod file sits in {qmods[0]}, expected {expected_qmod_path}",
            )
            return False
    return True


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
                report(str(file), "orphan metadata file — deleting", fixed=True)
                file.unlink()

                if is_dir_empty(folder):
                    report(str(folder), "empty folder — deleting", fixed=True)
                    folder.rmdir()
            else:
                report(
                    str(file),
                    "orphan metadata file — no matching .qmod or .ipynb",
                )
    return result


if __name__ == "__main__":
    if not Config.IS_DISABLED:
        run_precommit(
            partial(check_single_file, auto_fix=Config.SHOULD_AUTO_FIX),
            filter_file=lambda f: not should_exclude_file(f),
            verify_all=(
                partial(clean_leftover_metadata_files, Config.SHOULD_AUTO_FIX)
                if Config.SHOULD_CLEAN_LEFTOVER_METADATA
                else None
            ),
        )
