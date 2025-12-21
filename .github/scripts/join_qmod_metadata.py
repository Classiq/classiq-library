#! /usr/bin/env python3
import json
import logging
import re
import sys
from pathlib import Path
from typing import List

# Order matters: higher-priority suffixes first
QMOD_DICT = {".qmod": "native", ".ipynb": "python"}


def _get_qmod_path_for_metadata(metadata_path: Path) -> tuple[Path, str] | None:
    """
    Locate a .qmod or .ipynb file corresponding to the given metadata file.

    The metadata file is expected to have a .metadata.json suffix (e.g.,
    "example.metadata.json"). This function strips the .metadata.json suffix
    to get the base name, then looks for a matching .qmod or .ipynb file in
    the same directory (e.g., "example.qmod" or "example.ipynb").

    Files are checked in QMOD_DICT order:
    (.qmod, native),
    then (.ipynb, python).

    Returns the matched file path and its dialect, or `None` if no match exists.
    """
    meta_data_base_name = f"{metadata_path.parent / Path(metadata_path.stem).stem}"

    for suffix, dialect in QMOD_DICT.items():
        print(f"base name: {meta_data_base_name}{suffix}")
        if Path(f"{meta_data_base_name}{suffix}").exists():
            return Path(f"{meta_data_base_name}{suffix}"), dialect

    # it is the libraries responsibility to ensure that each metadata file has a corresponding qmod/ipynb file
    return None


def _is_json(data: str) -> bool:
    m = re.search(r"\S", data)
    if m is None:
        raise RuntimeError("Text must contain non-whitespace character")
    # Treat as json if first non-whitespace character is '{'
    if m.group(0) != "{":
        return False
    # Still verify that this is a valid json
    _ = json.loads(data)
    return True


def _enrich_metadata_with_qmod_info(
    single_metadata: dict, qmod_data: tuple[Path, str], directory: Path
) -> None:
    qmod_path, dialect = qmod_data
    single_metadata["path"] = str(qmod_path.relative_to(directory))
    single_metadata["qmod_dialect"] = dialect


def join_metadata_files(directory: Path, exclude_file: Path) -> List[dict]:
    metadata = []
    for metadata_path in directory.rglob("*.metadata.json"):
        if metadata_path == exclude_file:
            continue
        if metadata_path.suffixes == [".synthesis_options", ".json"]:
            continue
        with metadata_path.open() as fobj:
            single_metadata = json.load(fobj)

        qmod_data = _get_qmod_path_for_metadata(metadata_path)
        if qmod_data is None:
            continue

        _enrich_metadata_with_qmod_info(single_metadata, qmod_data, directory)
        metadata.append(single_metadata)
    return metadata


def generate_unified_metadata_file(qmod_directory: str, metadata_filename: str) -> None:
    metadata = join_metadata_files(
        directory=Path(qmod_directory), exclude_file=Path(metadata_filename)
    )
    with open(metadata_filename, "w") as f:
        json.dump(metadata, f, indent=2)  # indent is for readability


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    qmod_dir_path = sys.argv[1]
    metadata_file = sys.argv[2]
    generate_unified_metadata_file(
        qmod_directory=qmod_dir_path, metadata_filename=metadata_file
    )
