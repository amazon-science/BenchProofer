# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Filesystem helpers.

Bundles are written by one process and read by others, so `write_text` and `write_json`
replace files atomically and a reader never sees a half-written artifact.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on Python 3.10
    import tomli as tomllib

__all__ = [
    "BYPRODUCTS",
    "artifact_files",
    "load_toml",
    "read_json",
    "read_text",
    "read_text_or_empty",
    "write_json",
    "write_text",
]

#: Directory names that hold byproducts rather than artifacts, at any depth. Bytecode
#: written while a bundle's Python is judged would otherwise tie its `manifest.json` to that
#: interpreter, and a rerun elsewhere would report the bundle as tampered with.
BYPRODUCTS = frozenset({"__pycache__"})


def write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def read_text(path: Path) -> str:
    """Read a text file as UTF-8."""
    return path.read_text(encoding="utf-8")


def read_text_or_empty(path: Path) -> str:
    """Read a text file as UTF-8, or "" when there is no file at ``path``."""
    return read_text(path) if path.is_file() else ""


def write_json(path: Path, value: Any) -> None:
    """Serialize ``value`` as JSON and write it atomically."""
    encoded = json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False)
    write_text(path, encoded + "\n")


def read_json(path: Path) -> Any:
    """Parse a JSON file."""
    return json.loads(read_text(path))


def load_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file."""
    with path.open("rb") as handle:
        document: dict[str, Any] = tomllib.load(handle)
    return document


def artifact_files(root: Path) -> list[Path]:
    """Every file under ``root`` that is an artifact rather than a byproduct, sorted."""
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and BYPRODUCTS.isdisjoint(path.relative_to(root).parts)
    )
