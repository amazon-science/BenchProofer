# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer smoke``: check this installation against real benchmarks.

The command runs the suite in `benchproofer.smoke` and reports what happened, one
line per case. It answers "is Benchproofer working here", and it is written so
that the answer cannot be yes by omission: a case the machine cannot run is printed
as skipped with its reason, counted separately from the passes, and never folded into
the total.

Exit codes follow the convention in `benchproofer.cli.main`: 1 when a case failed or
errored, and 3 under ``--strict`` when the run was sound but skipped something.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..smoke.model import Case, CaseResult, CaseStatus
from ..smoke.report import SuiteResult, write_smoke_report
from ..smoke.runner import Progress, run_cases
from ..smoke.suites import GROUPS, SUITES, cases, select
from .display import emit_json, grid, note, problem, stderr, stdout
from .options import CacheDir, JsonOut, Offline, flag, settings_for

__all__ = ["smoke"]

_STYLE = {
    CaseStatus.PASSED: "green",
    CaseStatus.FAILED: "red",
    CaseStatus.SKIPPED: "yellow",
    CaseStatus.ERROR: "magenta",
}

Selection = Annotated[
    str,
    typer.Argument(
        metavar="SELECTION",
        help="A suite, a group, or one case id. See --list.",
    ),
]
Jobs = Annotated[
    int,
    typer.Option("--jobs", "-j", metavar="N", min=1, help="Cases to run at once."),
]
Slow = Annotated[
    bool,
    typer.Option(
        "--slow",
        help="Also select and run the cases that download datasets or build containers.",
    ),
]
Workspace = Annotated[
    Path | None,
    typer.Option(
        "--workspace",
        metavar="DIR",
        help="Where cases build their bundles. Contents are replaced per run.",
    ),
]
ReportDir = Annotated[
    Path | None,
    typer.Option("--report", metavar="DIR", help="Write smoke.json and smoke.md here."),
]
ListOnly = Annotated[
    bool,
    typer.Option("--list", help="List the suites, groups, and cases, and run nothing."),
]
Strict = Annotated[
    bool,
    typer.Option("--strict", help="Exit 3 if any case was skipped rather than run."),
]


def smoke(
    selection: Selection = "offline",
    jobs: Jobs = 1,
    slow: Slow = False,
    workspace: Workspace = None,
    cache_dir: CacheDir = None,
    offline: Offline = False,
    report_dir: ReportDir = None,
    json_out: JsonOut = False,
    list_only: ListOnly = False,
    strict: Strict = False,
) -> None:
    """Run the smoke suite and report what this installation can do."""
    settings = settings_for(cache_dir=cache_dir, offline=flag(offline))
    if list_only:
        _catalog(json_out=json_out, include_slow=slow)
        return

    selected = select(selection, include_slow=slow)
    directory = Path(workspace) if workspace else settings.cache_dir / "smoke"
    result = run_cases(
        selected,
        settings=settings,
        workspace=directory,
        jobs=jobs,
        include_slow=slow,
        progress=_Lines(enabled=not json_out),
        label=selection,
    )

    if report_dir is not None:
        report_dir.mkdir(parents=True, exist_ok=True)
        document, rendered = write_smoke_report(result, report_dir)
        if not json_out:
            note(f"Wrote {document} and {rendered}.")

    if json_out:
        emit_json(result.to_json())
    else:
        _render(result)

    if not result.sound:
        raise typer.Exit(code=1)
    skipped = result.of(CaseStatus.SKIPPED)
    if strict and skipped:
        problem(
            f"strict mode: {len(skipped)} of {result.total} case(s) were skipped, so this "
            f"run does not cover the suite"
        )
        raise typer.Exit(code=3)


def _catalog(*, json_out: bool, include_slow: bool = False) -> None:
    """Print what can be selected, without running anything.

    A suite is listed as the run would select it, so the counts here are the counts
    the same command without `--list` would report.
    """
    if json_out:
        emit_json(
            {
                "suites": [
                    {
                        "name": suite.name,
                        "summary": suite.summary,
                        "cases": [item.id for item in suite.cases(include_slow=include_slow)],
                    }
                    for suite in SUITES.values()
                ],
                "groups": {name: [item.id for item in group] for name, group in GROUPS.items()},
                "cases": [_case_json(item) for item in cases()],
            }
        )
        return

    suites = grid("suite", "cases", "what it covers")
    for suite in SUITES.values():
        suites.add_row(
            suite.name, str(len(suite.cases(include_slow=include_slow))), suite.summary
        )
    stdout.print(suites)

    listing = grid("case", "slow", "needs", "question")
    for item in cases():
        listing.add_row(
            item.id,
            "yes" if item.slow else "",
            ", ".join(item.requires),
            item.summary,
        )
    stdout.print()
    stdout.print(listing)


def _case_json(item: Case) -> dict[str, object]:
    """One case, as a JSON-serializable row."""
    return {
        "id": item.id,
        "group": item.group,
        "summary": item.summary,
        "requires": list(item.requires),
        "slow": item.slow,
    }


class _Lines(Progress):
    """Progress as one line per finished case, on stderr."""

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = enabled
        self._total = 0
        self._done = 0

    def start(self, total: int) -> None:
        """Record how many cases to expect."""
        self._total = total
        if self._enabled:
            stderr.print(f"[dim]running {total} case(s)[/dim]", highlight=False)

    def finished(self, result: CaseResult) -> None:
        """Print one line for a case that just finished."""
        self._done += 1
        if not self._enabled:
            return
        detail = result.message or "; ".join(item.describe() for item in result.observations)
        stderr.print(
            f"[dim]{self._done}/{self._total}[/dim] {result.case.id} "
            f"[{_STYLE[result.status]}]{result.status}[/] "
            f"[dim]{result.duration_s:.1f}s {detail}[/dim]",
            highlight=False,
        )


def _render(result: SuiteResult) -> None:
    """Print the counts per group, then everything that did not pass."""
    table = grid("group", *(str(status) for status in CaseStatus), title=result.headline())
    groups = result.groups()
    for name in sorted(groups):
        table.add_row(name, *(str(groups[name][str(status)]) for status in CaseStatus))
    stdout.print(table)

    unpassed = [item for item in result.results if item.status is not CaseStatus.PASSED]
    if not unpassed:
        return
    listing = grid("case", "status", "why", title=f"not passed ({len(unpassed)})")
    for item in unpassed:
        listing.add_row(item.case.id, f"[{_STYLE[item.status]}]{item.status}[/]", item.message)
    stdout.print()
    stdout.print(listing)
