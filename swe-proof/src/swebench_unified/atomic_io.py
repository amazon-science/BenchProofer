# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Crash-safe, concurrent-safe writes for files other processes read directly.

A bundle's `meta.json` is the only record of what has been verified about a cell,
and it is read directly by everything: the green classifier, the visualizer, the
triage worklist, and the next gate run. It is also rewritten concurrently, by
whichever process holds the cell's lock.

`Path.write_text` is a truncate followed by a write, so a reader that lands
between the two steps sees zero bytes and, having asked a well-formed question,
gets a malformed answer: the cell reads as having no verdicts, or the sweep dies
on `json.loads` of a file that is perfectly healthy.

Writing to a sibling temp file and renaming makes the swap atomic: `os.rename`
within a directory either has happened or has not, so a concurrent reader sees
the old contents or the new ones and never a prefix of the new ones. The temp
name carries the pid so two writers on one directory cannot collide on it, and it
is removed on any failure -- G-INTEGRITY does not allowlist it, and a leftover
SHOULD fail that gate rather than sit in a released bundle.

This does not replace the per-cell lock. The lock decides who may write; this
decides that whoever reads while a write is in flight still reads a whole file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Replace `path` with `data` in one observable step."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(data)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def write_text_atomic(path: Path, text: str) -> None:
    """Replace `path` with `text` in one observable step."""
    write_bytes_atomic(path, text.encode())


def write_json_atomic(path: Path, obj: Any, *, indent: int = 2,
                      sort_keys: bool = False) -> None:
    """`write_text_atomic` for JSON, with the trailing newline the corpus uses."""
    write_text_atomic(path, json.dumps(obj, indent=indent,
                                       sort_keys=sort_keys) + "\n")


def read_json_or_none(path: Path) -> Any | None:
    """Parse `path`, or None if it is absent or not yet whole.

    For readers that must survive a writer they do not coordinate with: a
    corpus-wide sweep should record the one unreadable cell and carry on rather
    than abort and lose every other verdict it had. Callers report the None loudly
    (as "not green", never as "nothing to do"), since an unreadable record is a
    cell whose state is unknown, not a cell that is fine.
    """
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None
