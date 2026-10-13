# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Terminal rendering.

Human output and machine output are produced from the same values: a command
computes a result, then either prints it as JSON or hands it to one of these
renderers. Nothing here decides anything, so a change to how a table looks cannot
change what a command reports.
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from ..core.plugin import Availability
from ..core.verdict import Outcome, Status
from ..pipeline.report import Report
from ..pipeline.run import Progress, RunResult, TaskOutcome

__all__ = [
    "LineProgress",
    "availability_cells",
    "emit_json",
    "grid",
    "note",
    "outcome_style",
    "problem",
    "render_outcomes",
    "render_report",
    "stderr",
    "stdout",
]

stdout = Console()
stderr = Console(stderr=True)

_OUTCOME_STYLE = {
    Outcome.CERTIFIED: "green",
    Outcome.REJECTED: "red",
    Outcome.INCOMPLETE: "yellow",
    Outcome.DROPPED: "dim",
}
_STATUS_STYLE = {
    Status.PASS: "green",
    Status.FAIL: "red",
    Status.WAIVED: "cyan",
    Status.SKIP: "yellow",
    Status.ERROR: "magenta",
    Status.TIMEOUT: "magenta",
}
#: Styles for `pipeline.run.TaskOutcome.outcome`, which adds ``error`` to the
#: classifications: a task the tool could not process is not a judgment about it.
_TASK_STYLE = {str(outcome): style for outcome, style in _OUTCOME_STYLE.items()} | {
    "error": "magenta"
}


def emit_json(value: Any) -> None:
    """Print a JSON document on stdout, unstyled and safe to pipe."""
    print(json.dumps(value, indent=2, default=str, ensure_ascii=False))


def grid(*columns: str, title: str = "") -> Table:
    """Build a table with Benchproofer's house style."""
    table = Table(title=title or None, header_style="bold", box=None, pad_edge=False)
    for column in columns:
        table.add_column(column, overflow="fold")
    return table


def note(message: str) -> None:
    """Print an informational line."""
    stdout.print(message)


def problem(message: str) -> None:
    """Print a message that explains why a command is exiting non-zero."""
    stderr.print(f"[red]{message}[/red]")


def outcome_style(outcome: Outcome) -> str:
    """The style used for one classification."""
    return _OUTCOME_STYLE.get(outcome, "")


def availability_cells(availability: Availability) -> tuple[str, str]:
    """The status and detail columns describing whether a component can run here."""
    if availability:
        return "[green]ready[/green]", availability.version or availability.detail
    detail = availability.detail
    if availability.hint:
        detail = f"{detail} ({availability.hint})"
    return "[yellow]unavailable[/yellow]", detail


class LineProgress(Progress):
    """Progress as one line per finished task.

    Lines go to stderr, so a command's JSON or table output stays pipeable while a
    long run is still readable.
    """

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = enabled
        self._total = 0
        self._done = 0

    def start(self, total: int) -> None:
        """Record how many tasks to expect."""
        self._total = total

    def finished(self, outcome: TaskOutcome) -> None:
        """Print one line for a task that just finished."""
        self._done += 1
        if not self._enabled:
            return
        style = _TASK_STYLE.get(outcome.outcome, "")
        certification = outcome.certification
        detail = (
            outcome.error
            or outcome.unfinished
            or (certification.describe() if certification else "")
        )
        stderr.print(
            f"[dim]{self._done}/{self._total}[/dim] {outcome.task_key} "
            f"[{style}]{outcome.outcome}[/] [dim]{detail}[/dim]",
            highlight=False,
        )

    def done(self, result: RunResult) -> None:
        """Print the one-line summary of the whole run."""
        if self._enabled:
            stderr.print(f"[bold]{result.describe()}[/bold]", highlight=False)


def render_outcomes(outcomes: tuple[TaskOutcome, ...]) -> None:
    """List what happened to the first tasks, and how many more there were."""
    limit = 20
    table = grid("task", "outcome", "detail", title=f"{len(outcomes)} task(s)")
    for outcome in outcomes[:limit]:
        style = _TASK_STYLE.get(outcome.outcome, "")
        detail = (
            outcome.error
            or outcome.unfinished
            or ("drafted" if outcome.built else "reused artifacts")
        )
        table.add_row(outcome.task_key, f"[{style}]{outcome.outcome}[/]", detail)
    stdout.print(table)
    if len(outcomes) > limit:
        note(f"... and {len(outcomes) - limit} more")


def render_report(report: Report, *, limit: int = 20) -> None:
    """Print a corpus report: the counts, then the gates, then what is unfinished."""
    counts = report.counts()
    summary = grid("outcome", "bundles", title=f"level={report.level}")
    for outcome in Outcome:
        summary.add_row(
            f"[{outcome_style(outcome)}]{outcome}[/]", str(counts.get(str(outcome), 0))
        )
    summary.add_row("[bold]total[/bold]", str(report.total))
    stdout.print(summary)

    if report.gate_tally:
        gates = grid("gate", *(str(status) for status in Status))
        for gate_id in sorted(report.gate_tally):
            tally = report.gate_tally[gate_id]
            cells = [
                f"[{_STATUS_STYLE.get(status, '')}]{tally.get(str(status), 0)}[/]"
                if tally.get(str(status))
                else "."
                for status in Status
            ]
            gates.add_row(gate_id, *cells)
        stdout.print()
        stdout.print(gates)

    unfinished = [row for row in report.rows if row.outcome is not Outcome.CERTIFIED]
    if not unfinished:
        return
    stdout.print()
    listing = grid("bundle", "outcome", "why", title=f"not certified ({len(unfinished)})")
    for row in unfinished[:limit]:
        listing.add_row(
            row.key, f"[{outcome_style(row.outcome)}]{row.outcome}[/]", row.reason()
        )
    stdout.print(listing)
    if len(unfinished) > limit:
        note(f"... and {len(unfinished) - limit} more")
