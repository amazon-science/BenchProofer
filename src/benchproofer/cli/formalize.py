# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer formalize``: draft artifacts for tasks that are already frozen.

Drafting is separated from judging so that the two can be run by different people,
on different machines, with different budgets. This command writes bundles and stops;
nothing it produces is certified until ``benchproofer check`` judges it.
"""

from __future__ import annotations

from typing import Annotated

import typer

from ..config import Settings
from ..core.task import Task
from ..errors import ConfigError
from ..pipeline.ingest import load_tasks
from ..pipeline.run import execute
from .check import fail_on
from .display import LineProgress, emit_json, note, render_outcomes
from .options import (
    BackendOption,
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
    backend_for,
    flag,
    provider_for,
    settings_for,
)

__all__ = ["formalize", "select_tasks"]

BenchmarkFilter = Annotated[
    str | None,
    typer.Argument(metavar="[BENCHMARK]", help="Only formalize tasks from this benchmark."),
]
Rebuild = Annotated[
    bool,
    typer.Option("--rebuild", help="Draft again even where a solution file already exists."),
]


def formalize(
    benchmark: BenchmarkFilter = None,
    backend: BackendOption = None,
    ids: Ids = None,
    limit: Limit = None,
    rebuild: Rebuild = False,
    provider: ProviderName = None,
    model: Model = None,
    record: Record = False,
    concurrency: Concurrency = None,
    bundle_root: BundleRoot = None,
    cache_dir: CacheDir = None,
    offline: Offline = False,
    json_out: JsonOut = False,
) -> None:
    """Formalize frozen tasks into bundles, without judging them.

    Ingest first: this command reads the tasks that ``benchproofer ingest`` froze,
    so it works offline and on benchmarks whose adapter needs the network.
    """
    settings = settings_for(
        bundle_root=bundle_root,
        cache_dir=cache_dir,
        provider=provider,
        model=model,
        concurrency=concurrency,
        offline=flag(offline),
        record=flag(record),
    )
    resolved = backend_for(backend)
    tasks = select_tasks(settings, benchmark=benchmark, ids=ids, limit=limit)

    result = execute(
        tasks,
        backend=resolved,
        provider=provider_for(settings, record=record),
        settings=settings,
        judge=False,
        rebuild=rebuild,
        progress=LineProgress(enabled=not json_out),
    )

    if json_out:
        emit_json(
            {
                "backend": resolved.name,
                "tasks": [
                    {
                        "task": outcome.task_key,
                        "bundle": str(outcome.bundle.root),
                        "drafted": outcome.built,
                        "unfinished": outcome.unfinished,
                        "error": outcome.error,
                    }
                    for outcome in result.outcomes
                ],
            }
        )
    else:
        render_outcomes(result.outcomes)

    # A task whose drafting gave up produced no artifact, which is a result; a task
    # that could not be attempted at all is the tool failing, and exits 1 here as it
    # does in `check` and `run`.
    fail_on((outcome.task_key, outcome.error) for outcome in result.errors())

    if not json_out:
        note(f"Drafted with backend {resolved.name!r}. Judge them with: benchproofer check")


def select_tasks(
    settings: Settings,
    *,
    benchmark: str | None,
    ids: list[str] | None,
    limit: int | None,
) -> list[Task]:
    """Read frozen tasks and apply the id and limit filters.

    Raises:
        ConfigError: Nothing is frozen for this selection, which means ingestion has
            not run yet. Formalizing zero tasks silently would look like success.
    """
    tasks = load_tasks(settings, benchmark=benchmark)
    wanted = set(ids or ())
    if wanted:
        tasks = [task for task in tasks if task.task_id in wanted]
    if limit is not None:
        tasks = tasks[:limit]
    if not tasks:
        where = f"{settings.bundle_root}" + (f"/{benchmark}" if benchmark else "")
        raise ConfigError(
            f"no frozen tasks under {where}; run 'benchproofer ingest BENCHMARK' first"
        )
    return tasks
