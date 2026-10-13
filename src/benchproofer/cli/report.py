# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer report``: read the ledgers and say what they show.

Read-only by construction. It runs no gate and computes no new judgment, so a report
can be produced by anyone, at any time, from a corpus alone. Bundles nobody could
judge are counted as unfinished rather than folded into a rate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..core.verdict import Level
from ..pipeline.report import collect, write_report
from .display import emit_json, note, render_report
from .options import BundleRoot, JsonOut, LevelOption, settings_for

__all__ = ["report"]

BenchmarkFilter = Annotated[
    str | None,
    typer.Argument(metavar="[BENCHMARK]", help="Only include bundles from this benchmark."),
]
BackendFilter = Annotated[
    str | None,
    typer.Option("--backend", "-b", metavar="NAME", help="Only include bundles built with it."),
]
OutDir = Annotated[
    Path | None,
    typer.Option("--out", metavar="DIR", help="Write report.json and report.md here."),
]
Rows = Annotated[
    int,
    typer.Option("--rows", metavar="N", min=1, help="How many unfinished bundles to list."),
]


def report(
    benchmark: BenchmarkFilter = None,
    backend: BackendFilter = None,
    level: LevelOption = Level.STATIC,
    out: OutDir = None,
    rows: Rows = 20,
    bundle_root: BundleRoot = None,
    json_out: JsonOut = False,
) -> None:
    """Summarize the recorded verdicts of every bundle under the root."""
    settings = settings_for(bundle_root=bundle_root)
    summary = collect(settings.bundle_root, level=level, benchmark=benchmark, backend=backend)

    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        document, rendered = write_report(summary, out)
        if not json_out:
            note(f"Wrote {document} and {rendered}.")

    if json_out:
        emit_json(summary.to_json())
        return

    if not summary.total:
        note(f"No bundles under {settings.bundle_root}.")
        return
    render_report(summary, limit=rows)
