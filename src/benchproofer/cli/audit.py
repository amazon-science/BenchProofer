# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer audit``: have bundles reviewed adversarially.

This is the stage that looks for what no program can: a specification weak enough to
accept a wrong implementation, strong enough to refuse a correct one, describing a
different task than it claims, or giving away the implementation to a solver. It writes
what the review produced into the bundle and stops. Nothing here decides anything -- what
it submits is re-run by ``benchproofer check --level audited``, and a judgment counts only
while the files it was reached from are unchanged. The two gates that re-run the submissions
are judged before the attack validation auditor is asked, as ``run`` judges them, since it
rules on the attacks and controls that cannot be determined by execution
(`pipeline.audit.review`).

Reviewing is worth much more when the reviewer is not the model that drafted the
artifacts, so ``--audit-model`` is the option to reach for; a self-review is recorded
faithfully and reported as one.
"""

from __future__ import annotations

from typing import Annotated

import typer

from ..audit.session import LANES
from ..core.bundle import Bundle
from ..errors import BenchproofError
from ..pipeline.audit import AuditResult, needs_review, review
from ..registries import BACKENDS
from ..util.parallel import mapped
from .check import fail_on, select_bundles
from .display import emit_json, grid, note, stderr, stdout
from .options import (
    AuditModel,
    BundleRoot,
    CacheDir,
    Concurrency,
    Ids,
    JsonOut,
    Limit,
    Model,
    Offline,
    ProviderName,
    Record,
    flag,
    reviewer_for,
    settings_for,
)

__all__ = ["audit"]

BenchmarkFilter = Annotated[
    str | None,
    typer.Argument(metavar="[BENCHMARK]", help="Only review bundles from this benchmark."),
]
BackendFilter = Annotated[
    str | None,
    typer.Option("--backend", "-b", metavar="NAME", help="Only review bundles built with it."),
]
Again = Annotated[
    bool,
    typer.Option(
        "--again",
        help="Review even where a current review exists, adding to what is on record.",
    ),
]


def audit(
    benchmark: BenchmarkFilter = None,
    backend: BackendFilter = None,
    ids: Ids = None,
    limit: Limit = None,
    again: Again = False,
    provider: ProviderName = None,
    model: Model = None,
    audit_model: AuditModel = None,
    record: Record = False,
    concurrency: Concurrency = None,
    bundle_root: BundleRoot = None,
    cache_dir: CacheDir = None,
    offline: Offline = False,
    json_out: JsonOut = False,
) -> None:
    """Review selected bundles and write the review into each of them.

    A bundle that already carries a review of the artifacts it ships is left alone, so
    running this twice does not spend a budget twice. Pass ``--again`` to review a bundle
    further: while the specification stands, new submissions join those on record.
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
    bundles = select_bundles(
        settings, benchmark=benchmark, backend=backend, ids=ids, limit=limit
    )
    pending = bundles if again else [item for item in bundles if needs_review(item)]
    skipped = len(bundles) - len(pending)
    if not pending:
        note(
            f"All {len(bundles)} selected bundle(s) already have a current review. "
            "Judge them with: benchproofer check --level audited"
        )
        return

    engine = reviewer_for(settings, record=record)
    failures: dict[str, str] = {}

    def one(bundle: Bundle) -> AuditResult | None:
        try:
            result = review(
                bundle,
                backend=BACKENDS.get(bundle.backend_name),
                provider=engine,
                settings=settings,
                again=LANES if again else (),
            )
        except BenchproofError as exc:
            # One bundle's review never stops the others. Only the errors Benchproofer
            # raises deliberately are collected: anything else is a defect in the tool,
            # and its traceback is worth more than a row in a table.
            failures[bundle.root.as_posix()] = f"{type(exc).__name__}: {exc}"
            return None
        if result is None:
            if not json_out:
                stderr.print(f"[dim]nothing left to ask of[/dim] {bundle.root.as_posix()}")
            return None
        if not json_out:
            stderr.print(f"[dim]reviewed[/dim] {result.task_key} {_summary(result)}")
        return result

    reviewed = mapped(pending, one, workers=settings.concurrency, prefix="audit")
    reviews = [result for result in reviewed if result is not None]

    if json_out:
        emit_json(
            {
                "skipped": skipped,
                "reviews": [_document(result) for result in reviews],
                "errors": [
                    {"bundle": key, "error": detail} for key, detail in failures.items()
                ],
            }
        )
    else:
        _render(reviews, skipped=skipped)

    fail_on(failures.items())

    if not json_out:
        note("Re-run what the reviews submitted with: benchproofer check --level audited")


def _summary(result: AuditResult) -> str:
    """One line describing what a review filed."""
    judged = ", ".join(f"{item.role}={item.verdict}" for item in result.audit.judgments)
    filed = result.audit.submissions
    return (
        f"{sum(1 for item in filed if item.kind == 'weakness')} attack(s), "
        f"{sum(1 for item in filed if item.kind == 'control')} control(s), "
        f"{judged or 'no judgment'}"
    )


def _document(result: AuditResult) -> dict[str, object]:
    """One review, as JSON."""
    return {
        "task": result.task_key,
        "bundle": str(result.bundle.root),
        "reviewer": result.audit.reviewer,
        "independent": result.audit.independent,
        "submissions": [filed.id for filed in result.audit.submissions],
        "kept": [item.id for item in result.audit.kept],
        "judgments": {item.role: item.verdict for item in result.audit.judgments},
        "written": list(result.written),
        "notes": list(result.audit.notes),
    }


def _render(reviews: list[AuditResult], *, skipped: int) -> None:
    """Print what each review filed, and nothing about whether it holds up."""
    columns = ("task", "reviewer", "independent", "submissions", "judgments")
    table = grid(*columns, title=f"{len(reviews)} review(s)")
    for result in reviews:
        audited = result.audit
        table.add_row(
            result.task_key,
            audited.reviewer,
            "yes" if audited.independent else "[yellow]no[/yellow]",
            str(len(audited.on_record())),
            ", ".join(f"{item.role}={item.verdict}" for item in audited.judgments) or "none",
        )
    stdout.print(table)
    if skipped:
        note(f"{skipped} bundle(s) already had a current review; --again reviews them too.")
