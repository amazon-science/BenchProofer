# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run Nagini with two of its error paths made to report instead of crash.

Usage: ``<Nagini's python> _nagini_driver.py <Nagini's arguments> <file>``. It is run by
the interpreter Nagini is installed in rather than this project's, so it imports nothing
but Nagini and the standard library.

Two kinds of error Viper reports reach Nagini's error translation in a shape it does not
expect, and Nagini (1.2.0 and 1.3.1 alike) dies on an `AttributeError` instead of
printing them:

* A `ConsistencyError` has no `reason`. Viper is saying the translated program is not a
  well-formed one -- "Function X has a self-reference in its postcondition ... add a
  decreases clause" -- which is a finding about the file.
* An error at `NoPosition` has no `file`. Under it is a real verification failure, such
  as the implicit loop invariant Nagini adds for a local first assigned inside nested
  loops.

The first is printed as a checker error, followed by the line Nagini prints for an
inconsistent program, so it reads as a file the checker could not read. The second is
given line 0 of the file for a position, so Nagini goes on to report the failure it found.

A translator exception, such as an `AssertionError` from its type handling, is left to
crash but located: its traceback names no position in the file, and the translator's
visitors each hold the node they translate in a local called ``node``, so the innermost
one is printed as a line of the file ahead of the traceback.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from types import TracebackType
from typing import Any

#: What Nagini prints for a program Viper found inconsistent, which the backend reads.
INCONSISTENT = "Translated AST contains inconsistencies."
#: What the line locating a translator crash says after its position, which the backend
#: reads.
CRASHED = "the translator crashed on"
#: How much of the construct the translator crashed on to quote.
_SEGMENT = 160


def _reporting(convert: Any, target: str) -> Any:
    """`ErrorManager.convert`, printing the errors it would have crashed on and stopping."""

    def reporting(self: Any, errors: Any, jvm: Any, modules: Any, sif: Any) -> Any:
        inconsistent = [error for error in errors if not hasattr(error, "reason")]
        if not inconsistent:
            return convert(self, errors, jvm, modules, sif)
        for error in inconsistent:
            position = error.pos()
            where = (
                f"{target}:{position.line()}:{position.column()}"
                if hasattr(position, "line")
                else target
            )
            print(f"{where}: error: {error.readableMessage()}")
        print(INCONSISTENT)
        sys.stdout.flush()
        # The JVM is not shut down cleanly from here, and waiting for it can hang.
        os._exit(1)

    return reporting


def _positioned(owner: type, name: str, fallback: object) -> None:
    """Make one property of Nagini's `Position` answer ``fallback`` where it would raise."""
    getter = getattr(owner, name).fget

    def get(self: Any) -> Any:
        try:
            return getter(self)
        except AttributeError:
            return fallback

    setattr(owner, name, property(get))


def crash_site(trace: TracebackType | None, target: str) -> str | None:
    """The line of ``target`` a translator that raised was working on, or None.

    Read from the innermost frame whose ``node`` local is a syntax-tree node with a
    position, and quoted as the file spells it, on one line.
    """
    node: ast.AST | None = None
    while trace is not None:
        candidate = trace.tb_frame.f_locals.get("node")
        if isinstance(candidate, ast.AST) and hasattr(candidate, "lineno"):
            node = candidate
        trace = trace.tb_next
    if node is None:
        return None
    try:
        segment = ast.get_source_segment(Path(target).read_text(encoding="utf-8"), node)
    except (OSError, UnicodeDecodeError):
        segment = None
    if not segment:
        try:
            segment = ast.unparse(node)
        except Exception:  # noqa: BLE001 - a node the unparser refuses is still a position
            segment = type(node).__name__
    segment = " ".join(segment.split())
    if len(segment) > _SEGMENT:
        segment = segment[: _SEGMENT - 3] + "..."
    line = getattr(node, "lineno", 0)
    column = getattr(node, "col_offset", 0) + 1
    return f"{target}:{line}:{column}: {CRASHED} `{segment}`"


def main() -> None:
    """Patch the two error paths, hand the arguments to Nagini, and locate a crash."""
    from nagini_translation import main as nagini
    from nagini_translation.lib.errors import manager, wrappers

    target = sys.argv[-1]
    manager.ErrorManager.convert = _reporting(manager.ErrorManager.convert, target)
    for name, fallback in (
        ("file_name", target),
        ("line", 0),
        ("column", 0),
        ("line_end", 0),
        ("column_end", 0),
    ):
        _positioned(wrappers.Position, name, fallback)
    sys.argv = ["nagini", *sys.argv[1:]]
    try:
        code = nagini.main()
    except Exception:
        site = crash_site(sys.exc_info()[2], target)
        if site is not None:
            print(site)
            sys.stdout.flush()
        raise
    sys.exit(code)


if __name__ == "__main__":
    main()
