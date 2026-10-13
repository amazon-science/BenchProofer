# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer check``: judge bundles that are already on disk.

Judging reads artifacts and writes verdicts. It never drafts, so this command needs
no model and no credentials, and anyone can re-run it on someone else's bundles to
get the same verdicts. That reproducibility is the point: a claim in a bundle counts
for nothing until a gate here agrees with it.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer

from ..config import Settings
from ..core.bundle import Bundle
from ..core.verdict import Level, Verdict
from ..errors import ConfigError
from ..log import PROGRESS
from ..pipeline.adjudicate import bundles_under, required_gates
from ..pipeline.repair import as_submitted
from ..pipeline.run import RunResult, judge_bundles
from ..registries import BACKENDS
from .display import LineProgress, emit_json, note, problem, render_report
from .options import (
    BundleRoot,
    Concurrency,
    Ids,
    JsonOut,
    LevelOption,
    Limit,
    Offline,
    flag,
    settings_for,
    waivers_from,
)

__all__ = ["check", "exit_for", "fail_on", "select_bundles"]

BenchmarkFilter = Annotated[
    str | None,
    typer.Argument(metavar="[BENCHMARK]", help="Only judge bundles from this benchmark."),
]
BackendFilter = Annotated[
    str | None,
    typer.Option("--backend", "-b", metavar="NAME", help="Only judge bundles built with it."),
]
Only = Annotated[
    list[str] | None,
    typer.Option("--only", metavar="GATE", help="Run only this gate; repeatable."),
]
Waive = Annotated[
    list[str] | None,
    typer.Option(
        "--waive",
        metavar="GATE=REASON",
        help="Record this gate's failures as waived, for the reason given; repeatable. "
        "The gates the central claim rests on cannot be waived at all.",
    ),
]
Rejudge = Annotated[
    bool,
    typer.Option(
        "--skip-certified/--rejudge",
        help="Leave bundles that already certify alone, or judge everything again.",
    ),
]
Strict = Annotated[
    bool,
    typer.Option("--strict", help="Exit 3 unless every selected bundle is certified."),
]
AsSubmitted = Annotated[
    bool,
    typer.Option(
        "--as-submitted",
        help="Judge a copy of each bundle laid out as Benchproofer lays out the bundle a "
        "repair leaves: every pre-fix implementation and case of the property-based test "
        "suite spliced into the solution it ships, and the regions and digests recorded "
        "again. For judging a bundle that is still being edited; the verdicts and evidence "
        "go to the copy, not the bundle, and each gate is listed with what this run decided "
        "of it.",
    ),
]


def check(
    benchmark: BenchmarkFilter = None,
    backend: BackendFilter = None,
    ids: Ids = None,
    only: Only = None,
    waive: Waive = None,
    level: LevelOption = Level.STATIC,
    skip_certified: Rejudge = False,
    limit: Limit = None,
    concurrency: Concurrency = None,
    bundle_root: BundleRoot = None,
    offline: Offline = False,
    json_out: JsonOut = False,
    strict: Strict = False,
    as_submitted: AsSubmitted = False,
) -> None:
    """Run the gates over selected bundles and record what they found.

    A bundle whose gates reject it is a result, not a failure: it says the artifacts
    do not support the claim. The process exits non-zero only when the tool itself
    could not do its job, or when ``--strict`` asks for certification.
    """
    settings = settings_for(
        bundle_root=bundle_root, concurrency=concurrency, offline=flag(offline)
    )
    bundles = select_bundles(
        settings, benchmark=benchmark, backend=backend, ids=ids, limit=limit
    )
    started = datetime.now(timezone.utc)
    if as_submitted:
        settings, bundles = _submitted(settings, bundles, quiet=json_out)
        if not json_out:
            logging.getLogger(PROGRESS).setLevel(logging.INFO)
    result = judge_bundles(
        bundles,
        settings=settings,
        level=level,
        only=tuple(only or ()),
        waivers=waivers_from(waive),
        skip_certified=skip_certified,
        progress=LineProgress(enabled=not (json_out or as_submitted)),
    )

    if json_out:
        emit_json(result.report.to_json())
    elif as_submitted:
        for copy in bundles:
            typer.echo(_listed(copy, level, started))
    else:
        render_report(result.report)

    exit_for(result, strict=strict)


def _submitted(
    settings: Settings, bundles: list[Bundle], *, quiet: bool
) -> tuple[Settings, list[Bundle]]:
    """Copies of these bundles laid out as `repair` lays out what a session left, under a root.

    The copies carry the verdicts, so the bundles themselves are left exactly as they are:
    a run of the gates part way through an edit is not a judgment of what will be shipped.
    """
    root = Path(f"{settings.bundle_root}.as-submitted")
    shutil.rmtree(root, ignore_errors=True)
    copies = [
        as_submitted(bundle, BACKENDS.get(bundle.backend_name), root) for bundle in bundles
    ]
    if not quiet:
        note(f"Judging copies under {root.resolve()}, so nothing is recorded in the bundles.")
    return settings.model_copy(update={"bundle_root": root}), copies


def _listed(copy: Bundle, level: Level, started: datetime) -> str:
    """Each gate ``level`` requires of a judged copy: what this run decided, or that it did not.

    A verdict this run reached is given whole, with the evidence it names, since the copy
    is where both are; one it did not reach is named as the last round's, not as fresh; and
    a pass is never called a certification, since the review's gates are not judged here.
    """
    verdicts = copy.manifest().verdicts
    lines = [
        f"{copy.root.resolve()}: the copy this run judged. Its verdicts are in its "
        "manifest.json and what each gate ran and printed in its evidence/; the bundle's own "
        "manifest.json and evidence/ still hold the last round's.",
        "",
    ]
    unfavourable: list[str] = []
    unrun: list[str] = []
    for gate in required_gates(level):
        verdict = verdicts.get(gate)
        said = _decided(verdict, started) if verdict is not None else ""
        if verdict is None or not said:
            recorded = f" (the last round recorded {verdict.status})" if verdict else ""
            lines.append(f"* {gate}: not run by this check{recorded}")
            unrun.append(gate)
            continue
        lines.append(f"* {gate} {said}")
        lines += [f"  evidence: {(copy.root / name).resolve()}" for name in verdict.evidence]
        if not verdict.ok:
            unfavourable.append(f"{gate} ({verdict.status})")
    lines.append("")
    if unfavourable:
        lines.append(f"Not passed: {', '.join(unfavourable)}.")
    elif unrun:
        lines.append(f"Every gate this check ran passed; it did not run {len(unrun)}.")
    else:
        lines.append("Every gate this check judges passed.")
    lines.append(
        "The review's gates (audit.*) are not judged by this check: the next review decides "
        "them, so a pass here is not a certification. --json prints every verdict with its "
        "details."
    )
    return "\n".join(lines)


def _decided(verdict: Verdict, started: datetime) -> str:
    """What this run decided of a gate, as `_listed` prints it, or "" where it did not run it.

    A run that measured nothing leaves the verdict the same inputs reached before standing
    (`pipeline.adjudicate`), and says so.
    """
    if verdict.judged_at >= started:
        return f"({verdict.status}): {verdict.summary}"
    again = verdict.details.get("remeasured")
    if isinstance(again, dict) and str(again.get("at") or "") >= started.isoformat():
        return (
            f"({verdict.status}, the last round's verdict, which stands: this run "
            f"{again.get('status')} on the same inputs, {again.get('summary')}): "
            f"{verdict.summary}"
        )
    return ""


def select_bundles(
    settings: Settings,
    *,
    benchmark: str | None,
    backend: str | None,
    ids: list[str] | None,
    limit: int | None,
) -> list[Bundle]:
    """Find the bundles under the root that match the filters.

    Raises:
        ConfigError: The selection is empty. Judging nothing would report zero
            findings, which reads the same as judging everything successfully.
    """
    wanted = set(ids or ())
    selected: list[Bundle] = []
    for bundle in bundles_under(settings.bundle_root):
        manifest = bundle.manifest()
        if benchmark and manifest.benchmark != benchmark:
            continue
        if backend and manifest.backend != backend:
            continue
        if wanted and manifest.task_id not in wanted:
            continue
        selected.append(bundle)
    if limit is not None:
        selected = selected[:limit]
    if not selected:
        raise ConfigError(
            f"no bundles matched under {settings.bundle_root}; "
            "run 'benchproofer formalize' first, or widen the filters"
        )
    return selected


def fail_on(failures: Iterable[tuple[str, str | None]]) -> None:
    """Print each thing the tool could not do, by what it was, and exit 1 if there is one."""
    failed = list(failures)
    for key, detail in failed:
        problem(f"{key}: {detail}")
    if failed:
        raise typer.Exit(code=1)


def exit_for(result: RunResult, *, strict: bool) -> None:
    """Exit 1 if a task could not be processed, or 3 if ``strict`` and one is not certified."""
    fail_on((outcome.task_key, outcome.error) for outcome in result.errors())
    uncertified = result.total - len(result.report.certified())
    if strict and uncertified:
        problem(f"strict mode: {uncertified} of {result.total} bundle(s) are not certified")
        raise typer.Exit(code=3)
