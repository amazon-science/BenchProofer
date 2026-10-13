# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Provenance stamped onto every verdict.

A recorded verdict has to say which judge computed it. `judge_digest` hashes the sources
that can reach a verdict, so it changes exactly when the judge does, unlike the version of
a working tree that is dirty whenever anyone builds bundles.
"""

from __future__ import annotations

import platform
import sys
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from ..util.digest import digest_paths

__all__ = ["environment_report", "judge_digest", "tool_version"]

#: Packages whose sources decide verdicts.
_JUDGE_PACKAGES = ("core", "gates", "backends", "oracles")


@lru_cache(maxsize=1)
def tool_version() -> str:
    """The installed distribution version."""
    try:
        return version("benchproofer")
    except PackageNotFoundError:
        from .._version import __version__

        return __version__


@lru_cache(maxsize=1)
def judge_digest() -> str:
    """Digest of the sources that produce verdicts."""
    package_root = Path(__file__).resolve().parent.parent
    sources: list[Path] = []
    for name in _JUDGE_PACKAGES:
        directory = package_root / name
        if directory.is_dir():
            sources.extend(sorted(directory.rglob("*.py")))
    return digest_paths(sources, relative_to=package_root)


def environment_report() -> dict[str, Any]:
    """Describe the environment a run happened in."""
    return {
        "tool_version": tool_version(),
        "judge_digest": judge_digest(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
    }
