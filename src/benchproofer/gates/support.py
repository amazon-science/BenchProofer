# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Text formatting shared by several gates, and the check of a variant's marker regions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING

from ..core.markers import parse
from ..errors import MarkerError

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = ["besides", "found", "join_lines", "table", "unreadable"]

#: How many values a one-line summary lists before saying how many more there are.
_LISTED = 5


def join_lines(values: Iterable[str]) -> str:
    """Join a few values for a one-line summary."""
    items = list(values)
    head = ", ".join(items[:_LISTED])
    return head if len(items) <= _LISTED else f"{head}, and {len(items) - _LISTED} more"


def found(categories: Iterable[tuple[str, Iterable[str]]]) -> dict[str, list[str]]:
    """Each category of defect that has a case, by the name the details give it.

    In the order the caller lists them, which is the order its verdict decides in.
    """
    return {name: sorted(cases) for name, cases in categories if cases}


def besides(categories: Mapping[str, Sequence[str]], reported: str) -> str:
    """What a verdict about ``reported`` adds about the categories it is not about, or "".

    A gate judging many cases returns the first category that has one, since that is the
    category whose status says the most. The rest are not nothing: a repair told only about
    the first fixes it, and the round after is told about the second, one round per
    category. Named in the summary, one repair can address them all.
    """
    rest = [
        f"{name}: {join_lines(cases)}" for name, cases in categories.items() if name != reported
    ]
    return f"; the same pass also found {'; '.join(rest)}" if rest else ""


def table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    """Render an aligned plain-text table for an evidence file."""
    body = [[str(cell) for cell in row] for row in rows]
    widths = [len(str(header)) for header in headers]
    for row in body:
        for index, cell in enumerate(row[: len(widths)]):
            widths[index] = max(widths[index], len(cell))

    def line(cells: list[str]) -> str:
        padded = (cell.ljust(width) for cell, width in zip(cells, widths, strict=False))
        return "  ".join(padded).rstrip()

    lines = [line([str(header) for header in headers]), "  ".join("-" * w for w in widths)]
    lines.extend(line(row) for row in body)
    return "\n".join(lines) + "\n"


def unreadable(source: str, backend: Backend) -> str:
    """Why ``source``'s marker regions cannot be read, or "" when they can.

    A variant of the solution file -- a pre-fix implementation, a case of the property-based
    test suite -- whose regions cannot be read can be asked nothing about the specification,
    so the gate judging it names the file and this, for a repair to fix.
    """
    try:
        parse(source, backend.comment)
    except MarkerError as exc:
        return (
            "its marker regions cannot be read, so nothing can be asked of it about the "
            f"specification: {exc}"
        )
    return ""
