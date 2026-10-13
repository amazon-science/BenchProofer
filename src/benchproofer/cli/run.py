# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer run``: ingest, formalize, judge, repair, report.

The other stages in one command, for when one command is what you want. It freezes the
tasks as ``ingest`` does and hands them to `pipeline.run.execute`, the loop that drafts each
bundle, judges it and repairs it until it certifies or the repair budget runs out, at every
level, reviewing it at ``--level audited``; then it reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..core.verdict import Level
from ..pipeline.ingest import ingest as freeze_tasks
from ..pipeline.report import write_report
from ..pipeline.run import execute
from .check import exit_for
from .display import LineProgress, emit_json, note, render_report
from .options import (
    AuditModel,
    BackendOption,
    BenchmarkArgument,
    BundleRoot,
    CacheDir,
    Concurrency,
    Extra,
    Ids,
    JsonOut,
    LevelOption,
    Limit,
    Model,
    Offline,
    ProviderName,
    Record,
    backend_for,
    extras_from,
    flag,
    provider_for,
    reviewer_for,
    settings_for,
)

__all__ = ["run"]

ReportDir = Annotated[
    Path | None,
    typer.Option("--report", metavar="DIR", help="Write report.json and report.md here."),
]
Rebuild = Annotated[
    bool,
    typer.Option("--rebuild", help="Draft again even where a solution file already exists."),
]
Strict = Annotated[
    bool,
    typer.Option("--strict", help="Exit 3 unless every bundle in the run is certified."),
]
Rejudge = Annotated[
    bool,
    typer.Option(
        "--skip-certified/--rejudge",
        help="Leave bundles that already certify at this level alone, or judge them again.",
    ),
]


def run(
    benchmark: BenchmarkArgument,
    backend: BackendOption = None,
    ids: Ids = None,
    limit: Limit = None,
    extra: Extra = None,
    level: LevelOption = Level.STATIC,
    rebuild: Rebuild = False,
    skip_certified: Rejudge = True,
    provider: ProviderName = None,
    model: Model = None,
    audit_model: AuditModel = None,
    record: Record = False,
    concurrency: Concurrency = None,
    bundle_root: BundleRoot = None,
    cache_dir: CacheDir = None,
    offline: Offline = False,
    report_dir: ReportDir = None,
    json_out: JsonOut = False,
    strict: Strict = False,
) -> None:
    """Take a benchmark from upstream rows to judged bundles in one command.

    At every level this is the whole loop: draft, judge, repair, and judge again, until
    each bundle certifies or the repair budget runs out. At ``--level audited`` each round
    also reviews the bundle; pass ``--audit-model`` so the review is not written by the
    model that drafted the artifacts.

    Raising the level over a corpus judged at a lower one costs only the gates not asked
    before, and the verdicts already in each `manifest.json` still count. Runs under different
    *settings* -- another threshold, input budget or toolchain -- mix silently in one
    bundle root, since `manifest.json` records the verdict and not the run; give such a run its
    own ``--bundle-root``.
    """
    settings = settings_for(
        bundle_root=bundle_root,
        cache_dir=cache_dir,
        provider=provider,
        model=model,
        audit_model=audit_model,
        concurrency=concurrency,
        offline=flag(offline),
        record=flag(record),
    )
    resolved = backend_for(backend)
    ingestion = freeze_tasks(
        benchmark, settings, ids=tuple(ids or ()), limit=limit, extras=extras_from(extra)
    )
    if not json_out:
        # Named, because the bundles land under the suite the tasks belong to, which
        # is what a later `check` or `report` of this corpus takes.
        note(
            f"Ingested {ingestion.count} task(s) from {benchmark} as "
            f"{', '.join(ingestion.suites)}."
        )

    result = execute(
        list(ingestion.tasks),
        backend=resolved,
        provider=provider_for(settings, record=record),
        reviewer=reviewer_for(settings, record=record),
        settings=settings,
        level=level,
        rebuild=rebuild,
        skip_certified=skip_certified,
        progress=LineProgress(enabled=not json_out),
    )

    if report_dir is not None:
        report_dir.mkdir(parents=True, exist_ok=True)
        document, rendered = write_report(result.report, report_dir)
        if not json_out:
            note(f"Wrote {document} and {rendered}.")

    if json_out:
        emit_json(result.report.to_json())
    else:
        render_report(result.report)

    # A task whose drafting gave up is a result, not a broken run: the bundle stays
    # incomplete, `--strict` counts it, and the exit code stays 0.
    for outcome in result.unfinished():
        note(f"{outcome.task_key}: {outcome.unfinished}")

    exit_for(result, strict=strict)
