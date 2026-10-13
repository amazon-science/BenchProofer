# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer ingest``: fetch a benchmark and freeze its tasks.

Ingestion is its own command because the inputs of a run should be fixed, and
inspectable, before anything is drafted or judged. What this writes is what every
later command reads.
"""

from __future__ import annotations

from typing import Annotated

import typer

from ..pipeline.ingest import ingest as freeze_tasks
from .display import emit_json, grid, note, stdout
from .options import (
    BenchmarkArgument,
    BundleRoot,
    CacheDir,
    Extra,
    Ids,
    JsonOut,
    Limit,
    Offline,
    extras_from,
    flag,
    settings_for,
)

__all__ = ["ingest"]

Refresh = Annotated[
    bool,
    typer.Option(
        "--refresh",
        help="Overwrite inputs that are already frozen, even where bundles exist.",
    ),
]


def ingest(
    benchmark: BenchmarkArgument,
    ids: Ids = None,
    limit: Limit = None,
    extra: Extra = None,
    refresh: Refresh = False,
    bundle_root: BundleRoot = None,
    cache_dir: CacheDir = None,
    offline: Offline = False,
    json_out: JsonOut = False,
) -> None:
    """Normalize a benchmark's tasks and freeze them under the bundle root.

    Frozen inputs are never rewritten unless ``--refresh`` is given, so re-running
    this command cannot change the task an existing bundle was judged against.
    """
    settings = settings_for(bundle_root=bundle_root, cache_dir=cache_dir, offline=flag(offline))
    result = freeze_tasks(
        benchmark,
        settings,
        ids=tuple(ids or ()),
        limit=limit,
        extras=extras_from(extra),
        refresh=refresh,
    )

    if json_out:
        emit_json(
            {
                "benchmark": result.benchmark,
                "suites": list(result.suites),
                "count": result.count,
                "reused": result.reused,
                "bundle_root": str(settings.bundle_root),
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "language": task.language,
                        "oracle": task.oracle.kind,
                        "digest": task.digest(),
                    }
                    for task in result.tasks
                ],
            }
        )
        return

    if not result.count:
        note(f"No tasks matched in {benchmark!r}.")
        return

    shown = 20
    table = grid("task", "language", "oracle", "reference", title=result.benchmark)
    for task in result.tasks[:shown]:
        if task.reference.patch:
            reference = "patch"
        else:
            reference = "none" if task.reference.is_empty else "files"
        table.add_row(task.task_id, task.language, task.oracle.kind, reference)
    stdout.print(table)
    if result.count > shown:
        note(f"... and {result.count - shown} more")
    # Named, because what a later command filters on is the suite the tasks belong
    # to, which is not always the adapter that loaded them.
    note(
        f"Froze {result.count} task(s) as {', '.join(result.suites)} under "
        f"{settings.bundle_root} ({result.reused} already present)."
    )
