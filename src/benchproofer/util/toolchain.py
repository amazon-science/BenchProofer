# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Locating external verifier executables.

A backend asks for a tool by name and gets, in order of precedence: an override
environment variable, the repository-local directory `scripts/install/*.sh` writes into,
and `PATH`. The order keeps a checkout with pinned toolchains from being judged by
whatever version the machine happens to have.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .proc import run

__all__ = ["Probe", "absent", "find_tool", "probe_version"]

#: How much of a tool's own complaint to keep when it will not report a version.
_SAID_LIMIT = 200


def find_tool(name: str, *, toolchain_dir: Path) -> Path | None:
    """Locate an executable, or return None.

    Args:
        name: Executable name, for example ``dafny``. ``BENCHPROOFER_<NAME>`` holds an
            absolute override path.
        toolchain_dir: Repository-local toolchain root; ``<dir>/bin/<name>`` and
            ``<dir>/<name>/<name>`` are both tried.
    """
    override = os.environ.get(f"BENCHPROOFER_{name.upper().replace('-', '_')}")
    if override:
        candidate = Path(override).expanduser()
        return candidate if candidate.is_file() else None

    for relative in (Path("bin") / name, Path(name) / name, Path(name) / "bin" / name):
        candidate = toolchain_dir / relative
        if candidate.is_file():
            return candidate

    found = shutil.which(name)
    return Path(found) if found else None


def absent(name: str, *, toolchain_dir: Path) -> str:
    """Say that a tool was not found, and name the places it was looked for.

    The toolchain directory setting is relative to the working directory by default, so
    a pinned prover found in a checkout is not found one directory away; naming the
    directory searched tells that from a prover never installed.
    """
    return (
        f"{name} not found under {toolchain_dir} or on PATH "
        f"(BENCHPROOFER_TOOLCHAIN_DIR names another install)"
    )


@dataclass(frozen=True, slots=True)
class Probe:
    """What a tool said when it was asked for its version."""

    version: str | None
    #: The tool's own words, when it reported no version. Empty otherwise.
    said: str = ""

    @property
    def answered(self) -> bool:
        """True when the tool named a version.

        A tool that cannot say what it is cannot verify anything either, as an installed
        Lean with no toolchain configured refuses every file. Reading that as unavailable
        turns a machine's configuration into a skip with a reason, not a failing case.
        """
        return self.version is not None


def probe_version(executable: Path, args: tuple[str, ...] = ("--version",)) -> Probe:
    """Ask a tool for its version and report what came back."""
    result = run((str(executable), *args), timeout_s=30.0)
    match = re.search(r"\d+\.\d+(?:\.\d+)?", result.output)
    if match:
        return Probe(version=match.group(0))
    return Probe(version=None, said=_said(result.output) or f"exit status {result.returncode}")


def _said(output: str) -> str:
    """One line of a tool's output: what it complained about, if it did."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    spoken = next((line for line in lines if line.lower().startswith("error")), "")
    return (spoken or (lines[0] if lines else ""))[:_SAID_LIMIT]
