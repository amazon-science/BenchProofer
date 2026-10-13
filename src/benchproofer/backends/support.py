# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared helpers for reading what a checker printed, and for finding a Lean toolchain.

A rejection is summarized in one line, because that line is what a report shows and
what a repair round works from, and every backend has to pick it out of a page of output.
"""

from __future__ import annotations

import dataclasses
import os
import re
import shutil
from pathlib import Path

from ..util.proc import Completed
from ._nagini_driver import CRASHED

__all__ = [
    "LEAN_ERROR",
    "LEAN_MALFORMED",
    "LEAN_SORRY",
    "LEAN_UNDECIDED",
    "crash_location",
    "crashed",
    "first_error",
    "lake_for",
    "within",
]

#: How much of a diagnostic to keep. A checker can print a whole page about one
#: obligation; the first line of it is what identifies the obligation.
LIMIT = 300

#: Where an error diagnostic starts in what Lean prints: `error:`, or with the
#: diagnostic's name in parentheses, `error(lean.unknownIdentifier):`, whatever the
#: parentheses hold. A file that printed only named errors is still one Lean refused.
_TAG = r"(?:\([^()\s]*\))?"
LEAN_ERROR = re.compile(rf"(?<![\w.])error{_TAG}:")
#: An error Lean placed at a line of the checked file, as `Backend.refusal_site` reads it:
#: `solution.lean:43:4: error: ...`, after whatever directory the file was checked in.
LEAN_REFUSAL_SITE = rf"^\s*\S*?\.lean:(?P<line>\d+):\d+: error{_TAG}:"

#: Lean reports a missing proof as a warning on a file it otherwise accepts, so this
#: is looked for on an accepting exit too. The quoting is left open because Lean up to
#: 4.2 wrote `uses 'sorry'` and later releases use backticks, and a pattern that stopped
#: firing would certify a stubbed proof.
LEAN_SORRY = re.compile(r"declaration uses [`']?sorry")
#: A Lean file the elaborator could not read, so its rejection is `malformed`. An
#: unknown tactic is one: the parser stops at its name, so the proof was never tried.
#: "expected" is anchored to the start of a diagnostic, as `LEAN_ERROR` spells it, where
#: it is the parser saying what it wanted; unanchored it would also match "but is
#: expected to have type", a proof that does not go through, which is a refutation.
LEAN_MALFORMED = re.compile(
    r"(unexpected token|unknown identifier|unknown constant|unknown tactic|"
    rf"failed to synthesize|unexpected end of input|error{_TAG}: expected)",
    re.IGNORECASE,
)
#: A Lean run that ran out of budget, such as the elaborator's heartbeats, which is a
#: bound and not a verdict: the file was neither accepted nor refuted.
LEAN_UNDECIDED = re.compile(
    r"(maximum number of heartbeats|maximum recursion depth|\(deterministic\) timeout)"
)
#: What a Python-hosted checker prints when it dies instead of reaching a verdict.
_TRACEBACK = "Traceback (most recent call last)"
#: What `_nagini_driver` prints ahead of a crash to place it in the file: the file, the
#: line and column of the construct being translated, and that construct. A result's
#: detail carries it after the exception, so it is not anchored to a line start.
_CRASH_SITE = re.compile(rf"(?<!\S)\S+:\d+:\d+: {re.escape(CRASHED)} .*$", re.MULTILINE)


def first_error(output: str, marker: str | re.Pattern[str] = "error") -> str:
    """Summarize a rejection in one line.

    Args:
        output: Everything the checker printed.
        marker: What its diagnostics contain: a substring matched without regard to
            case, such as ``error:`` where a summary line also says "error", or a
            compiled pattern, such as `LEAN_ERROR`.

    Returns:
        The first diagnostic line, or the first line of output when none is
        recognizable, or ``rejected`` when the checker said nothing at all.
    """
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in lines:
        if _says(line, marker):
            return line[:LIMIT]
    return lines[0][:LIMIT] if lines else "rejected"


def _says(line: str, marker: str | re.Pattern[str]) -> bool:
    """Whether ``line`` carries ``marker``, as `first_error` reads one."""
    if isinstance(marker, str):
        return marker.lower() in line.lower()
    return marker.search(line) is not None


def within(result: Completed, workdir: Path) -> Completed:
    """``result`` with the directory the file was checked in taken off each path it prints.

    A scratch path at the start of every diagnostic can fill a detail cut to a report's
    width. The file's own name stays, since it places a diagnostic in the file.
    """
    prefixes = {f"{workdir}{os.sep}", f"{workdir.resolve()}{os.sep}"}

    def relative(text: str) -> str:
        for prefix in prefixes:
            text = text.replace(prefix, "")
        return text

    return dataclasses.replace(
        result, stdout=relative(result.stdout), stderr=relative(result.stderr)
    )


def crashed(output: str) -> str | None:
    """Name the exception a checker died on, if it died on one.

    The exception is what tells a defect in the toolchain from one in the bundle. It is
    the last unindented line of the last traceback; the frames are the checker's own.

    Returns:
        The exception line, or ``None`` when nothing crashed.
    """
    reported = output.rfind(_TRACEBACK)
    if reported < 0:
        return None
    lines = output[reported:].splitlines()[1:]
    named = [line.strip() for line in lines if line.strip() and not line[0].isspace()]
    return named[-1][:LIMIT] if named else "no exception was named"


def crash_location(text: str) -> str:
    """The line placing a checker's crash at a position in the file, or "" for none.

    A crash with a position is the translator failing on a construct the file's author
    can write another way. The line is returned stripped, to be quoted back.
    """
    found = _CRASH_SITE.search(text)
    return found.group(0).strip() if found else ""


def lake_for(workspace: Path) -> Path | None:
    """The lake that owns a Lean workspace: the one beside it, else the one on PATH.

    ``scripts/install/velvet.sh`` unpacks the pinned toolchain next to the workspace it
    builds, and that is the one a verdict should come from.
    """
    pinned = workspace.parent / "lean" / "bin" / "lake"
    if pinned.is_file():
        return pinned
    found = shutil.which("lake")
    return Path(found) if found else None
