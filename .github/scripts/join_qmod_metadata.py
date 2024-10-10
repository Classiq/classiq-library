#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from typing import List


def _get_qmod_path_for_metadata(metadata_path: Path) -> Path:
    # Each metadata file has the same name as the qmod file, but with a .json extension,
    # so we replace the extension with qmod
    qmod_path = metadata_path.parent / (Path(metadata_path.stem).stem + ".qmod")
    if not qmod_path.exists():
        raise RuntimeError(
            f"Could not find qmod file for metadata file {metadata_path} at {qmod_path}"
        )
    return qmod_path


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


def _get_qmod_type(qmod_path: Path) -> str:
    data = qmod_path.read_text()
    if _is_json(data):
        return "json"
    else:
        return "standalone"


def join_metadata_files(directory: Path, exclude_file: Path) -> List[dict]:
    metadata = []
    for metadata_path in directory.rglob("*.metadata.json"):
        if metadata_path == exclude_file:
            continue
        if metadata_path.suffixes == [".synthesis_options", ".json"]:
            continue
        with metadata_path.open() as fobj:
            single_metadata = json.load(fobj)
        qmod_path = _get_qmod_path_for_metadata(metadata_path)
        single_metadata["path"] = str(qmod_path.relative_to(directory))
        if single_metadata.get("qmod_dialect") is None:
            try:
                qmod_type = _get_qmod_type(qmod_path)
            except Exception as exc:
                raise RuntimeError(
                    f"Qmod {qmod_path} is not a valid qmod file"
                ) from exc
            single_metadata["qmod_dialect"] = qmod_type
        metadata.append(single_metadata)
    return metadata


def generate_unified_metadata_file(qmod_directory: str, metadata_filename: str) -> None:
    metadata = join_metadata_files(
        directory=Path(qmod_directory), exclude_file=Path(metadata_filename)
    )
    with open(metadata_filename, "w") as f:
        json.dump(metadata, f, indent=2)  # indent is for readability


if __name__ == "__main__":
    qmod_dir_path = sys.argv[1]
    metadata_file = sys.argv[2]
    generate_unified_metadata_file(
        qmod_directory=qmod_dir_path, metadata_filename=metadata_file
    )
