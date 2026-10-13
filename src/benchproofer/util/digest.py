# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Content digests.

A verdict is checked later against the digests of the bytes it was computed from, so
digests are normalized to be stable across platforms and re-serialization.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

__all__ = [
    "digest_bytes",
    "digest_file",
    "digest_json",
    "digest_paths",
    "digest_text",
    "short",
]


def digest_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def digest_text(text: str) -> str:
    r"""Digest text with newlines normalized to ``\n``.

    Line-ending normalization keeps a checkout on Windows from disagreeing with
    the verdict recorded on Linux.
    """
    return digest_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode())


def digest_json(value: Any) -> str:
    """Digest a JSON-compatible value under a canonical encoding."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return digest_text(encoded)


def digest_file(path: Path) -> str:
    """Digest a file's contents, treating it as text when it decodes as UTF-8."""
    data = path.read_bytes()
    try:
        return digest_text(data.decode())
    except UnicodeDecodeError:
        return digest_bytes(data)


def digest_paths(paths: Iterable[Path], *, relative_to: Path | None = None) -> str:
    """Digest a set of files together with their names.

    The result is order-independent: paths are sorted before hashing, so the
    digest describes the set of files rather than the traversal that produced it.
    """
    entries: list[tuple[str, str]] = []
    for path in paths:
        name = str(path.relative_to(relative_to)) if relative_to else str(path)
        entries.append((name, digest_file(path)))
    return digest_json(sorted(entries))


def short(digest: str, length: int = 12) -> str:
    """Truncate a digest for display."""
    return digest[:length]
