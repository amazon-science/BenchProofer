# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer repair``: repair bundles the gates would not certify.

A repair addresses verdicts, so this command reads `manifest.json` and nothing else: a bundle
nobody has judged has nothing to repair, and one held up only by a toolchain that is
not installed has nothing a model could fix. How an agent session repairs a bundle, and
what is written of what it leaves, is `pipeline.repair`'s.

The repaired bundle is not judged here: its recorded verdicts describe the artifacts it
had before, so ``benchproofer check`` is the next step.
"""

from __future__ import annotations

from typing import Annotated

import typer

from ..core.bundle import Bundle
from ..core.rounds import addressed
from ..core.verdict import Level, Verdict
from ..errors import BenchproofError
from ..pipeline.repair import RepairResult
from ..pipeline.repair import repair as repair_bundle
from ..pipeline.route import Route, routed
from ..registries import BACKENDS
from ..util.parallel import mapped
from .check import fail_on, select_bundles
from .display import emit_json, grid, note, stderr, stdout
from .options import (
    BundleRoot,
    CacheDir,
    Concurrency,
    Ids,
    JsonOut,
    LevelOption,
    Limit,
    Model,
    Offline,
    Record,
    flag,
    settings_for,
)

__all__ = ["repair"]

BenchmarkFilter = Annotated[
    str | None,
    typer.Argument(metavar="[BENCHMARK]", help="Only repair bundles from this benchmark."),
]
BackendFilter = Annotated[
    str | None,
    typer.Option("--backend", "-b", metavar="NAME", help="Only repair bundles built with it."),
]


def repair(
    benchmark: BenchmarkFilter = None,
    backend: BackendFilter = None,
    ids: Ids = None,
    limit: Limit = None,
    level: LevelOption = Level.STATIC,
    model: Model = None,
    record: Record = False,
    concurrency: Concurrency = None,
    bundle_root: BundleRoot = None,
    cache_dir: CacheDir = None,
    offline: Offline = False,
    json_out: JsonOut = False,
) -> None:
    """Repair selected bundles to address what their recorded gates found.

    The level decides which gates count, so it should be the level the bundles were
    judged at. A bundle whose unfavorable verdicts are all beyond a model's reach is
    reported as having nothing to repair, which is not the same as being sound.
    """
    settings = settings_for(
        bundle_root=bundle_root,
        cache_dir=cache_dir,
        model=model,
        concurrency=concurrency,
        offline=flag(offline),
        record=flag(record),
    )
    bundles = select_bundles(
        settings, benchmark=benchmark, backend=backend, ids=ids, limit=limit
    )
    unjudged = [item for item in bundles if not item.manifest().verdicts]
    failures: dict[str, str] = {}
    pending: list[tuple[Bundle, list[Verdict]]] = []
    for item in bundles:
        recorded = item.manifest().verdicts
        if not recorded:
            continue
        try:
            addressing = routed(recorded, level)[Route.REPAIR]
        except ValueError as exc:
            # A verdict the route table has no row for is a defect of the gate that
            # recorded it: that bundle is reported as an error, as `run` reports it, and
            # the others are repaired.
            failures[item.root.as_posix()] = f"{type(exc).__name__}: {exc}"
            continue
        if addressing:
            pending.append((item, addressing))
    if not pending and not failures:
        _explain(bundles, unjudged=unjudged, level=level, json_out=json_out)
        return
    skipped = len(bundles) - len(pending) - len(failures)

    repaired: list[RepairResult] = []
    if pending:

        def one(entry: tuple[Bundle, list[Verdict]]) -> RepairResult | None:
            bundle, verdicts = entry
            try:
                result = repair_bundle(
                    bundle,
                    backend=BACKENDS.get(bundle.backend_name),
                    settings=settings,
                    verdicts=verdicts,
                )
            except BenchproofError as exc:
                # One bundle's repair never stops the others. Only the errors Benchproofer
                # raises deliberately are collected: anything else is a defect in the
                # tool, and its traceback is worth more than a row in a table.
                failures[bundle.root.as_posix()] = f"{type(exc).__name__}: {exc}"
                return None
            if not json_out:
                stderr.print(
                    f"[dim]repaired[/dim] {result.task_key} {_summary(result, len(verdicts))}"
                )
            return result

        done = mapped(pending, one, workers=settings.concurrency, prefix="repair")
        repaired = [result for result in done if result is not None]

    if json_out:
        emit_json(
            {
                "level": str(level),
                "unjudged": [str(item.root) for item in unjudged],
                "repairs": [_document(result) for result in repaired],
                "errors": [
                    {"bundle": key, "error": detail} for key, detail in failures.items()
                ],
            }
        )
    else:
        _render(repaired, skipped=skipped)

    fail_on(failures.items())

    if not json_out:
        note(f"Judge the repaired bundles with: benchproofer check --level {level}")


def _addressed(result: RepairResult) -> list[str]:
    """The gate ids one repair was addressing, from the manifest.json it wrote."""
    history = result.bundle.manifest().provenance.get("repairs", [])
    last = history[-1] if isinstance(history, list) and history else {}
    return addressed(last) if isinstance(last, dict) else []


def _state(result: RepairResult) -> str:
    """What the session reported, or that it filed no report."""
    return result.status or "no report"


def _summary(result: RepairResult, findings: int) -> str:
    """One line describing what a repair produced."""
    return f"{findings} finding(s), {_state(result)}, {len(result.written)} file(s) written"


def _document(result: RepairResult) -> dict[str, object]:
    """One repair, as JSON."""
    return {
        "task": result.task_key,
        "bundle": str(result.bundle.root),
        "addressing": _addressed(result),
        "status": result.status,
        "written": list(result.written),
    }


def _render(repaired: list[RepairResult], *, skipped: int) -> None:
    """Print what each repair produced, and nothing about whether it worked."""
    columns = ("task", "addressing", "session", "written")
    table = grid(*columns, title=f"{len(repaired)} repair(s)")
    for result in repaired:
        table.add_row(
            result.task_key,
            ", ".join(_addressed(result)) or "-",
            _state(result),
            str(len(result.written)),
        )
    stdout.print(table)
    if skipped:
        note(f"{skipped} bundle(s) had nothing a repair could address.")


def _explain(
    bundles: list[Bundle], *, unjudged: list[Bundle], level: Level, json_out: bool
) -> None:
    """Say why there was nothing to do, which is not the same as success."""
    if json_out:
        emit_json(
            {
                "level": str(level),
                "unjudged": [str(item.root) for item in unjudged],
                "repairs": [],
                "errors": [],
            }
        )
        return
    if unjudged:
        note(
            f"{len(unjudged)} of {len(bundles)} selected bundle(s) have no verdicts, so "
            f"there is nothing to repair yet; judge them with: benchproofer check "
            f"--level {level}"
        )
    if len(unjudged) < len(bundles):
        note(
            "No selected bundle has an unfavorable verdict a repair could address. A gate "
            "that could not run -- no toolchain, no way to run the benchmark's tests, no "
            "review -- is not a defect in the artifacts, so it is not repaired."
        )
