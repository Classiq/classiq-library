#! /usr/bin/env python3
import json
import logging
import re
import sys
from pathlib import Path
from typing import List

PYTHON_DIALECT = "python"
NATIVE_DIALECT = "native"


def _get_qmod_path_for_metadata(metadata_path: Path) -> tuple[Path, str] | None:
    # Each metadata file has the same name as the qmod file, but with a .json extension,
    # so we replace the extension with qmod
    native_qmod_path = metadata_path.parent / (Path(metadata_path.stem).stem + ".qmod")
    if native_qmod_path.exists():
        return native_qmod_path, NATIVE_DIALECT
    python_qmod_path = metadata_path.parent / (Path(metadata_path.stem).stem + ".ipynb")
    if python_qmod_path.exists():
        return python_qmod_path, PYTHON_DIALECT

    # it is the libraries responsibility to ensure that each metadata file has a corresponding qmod file
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


def join_metadata_files(directory: Path, exclude_file: Path) -> List[dict]:
    metadata = []
    for metadata_path in sorted(directory.rglob("*.metadata.json")):
        if metadata_path == exclude_file:
            continue
        if metadata_path.suffixes == [".synthesis_options", ".json"]:
            continue
        with metadata_path.open() as fobj:
            single_metadata = json.load(fobj)

        qmod_data = _get_qmod_path_for_metadata(metadata_path)
        if qmod_data is None:
            continue

        qmod_path, dialect = qmod_data
        single_metadata["path"] = str(qmod_path.relative_to(directory))
        single_metadata["qmod_dialect"] = dialect
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
