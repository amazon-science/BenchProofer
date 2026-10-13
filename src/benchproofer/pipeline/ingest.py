# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Ingestion: upstream rows in, frozen tasks out.

Ingestion is separated from formalization so that the inputs of a run are fixed
before any model or verifier touches them. A frozen ``task.json`` is what every
later stage reads, and it is never rewritten in place, so a bundle judged last week
cannot silently acquire a different statement this week.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ..benchmarks.base import Benchmark, LoadRequest
from ..config import Settings
from ..core.bundle import freeze_task, task_directory
from ..core.task import Task
from ..errors import BenchmarkError
from ..log import logger
from ..registries import BENCHMARKS

__all__ = ["Ingestion", "ingest", "load_tasks", "stream_tasks"]

log = logger(__name__)


@dataclass(frozen=True, slots=True)
class Ingestion:
    """What one ingestion produced."""

    benchmark: str
    tasks: tuple[Task, ...]
    frozen: tuple[Path, ...]
    #: Tasks already on disk that were left as they were.
    reused: int = 0

    @property
    def count(self) -> int:
        """How many tasks the ingestion covers."""
        return len(self.tasks)

    @property
    def suites(self) -> tuple[str, ...]:
        """The names later commands filter on: what the tasks call themselves.

        Usually the adapter's own name, but a row may name a suite of its own, as
        rows read by the `jsonl` adapter may. The frozen layout follows the task
        rather than the adapter, so this is what `formalize` and `check` take.
        """
        return tuple(sorted({task.benchmark for task in self.tasks}))


def stream_tasks(
    benchmark: str,
    settings: Settings,
    *,
    ids: tuple[str, ...] = (),
    limit: int | None = None,
    extras: dict[str, str] | None = None,
) -> Iterator[Task]:
    """Yield normalized tasks from one benchmark without writing anything.

    Raises:
        PluginError: The benchmark is not registered.
        BenchmarkError: The adapter cannot load here, or a row will not normalize.
    """
    adapter: Benchmark = BENCHMARKS.get(benchmark)
    available = adapter.availability()
    if not available:
        raise BenchmarkError(
            f"benchmark {benchmark!r} is unavailable: {available.detail}"
            + (f" ({available.hint})" if available.hint else "")
        )
    request = LoadRequest(
        cache_dir=settings.cache_dir / "datasets",
        ids=ids,
        limit=limit,
        offline=settings.offline,
        extras=dict(extras or {}),
    )
    yield from adapter.load(request)


def ingest(
    benchmark: str,
    settings: Settings,
    *,
    ids: tuple[str, ...] = (),
    limit: int | None = None,
    extras: dict[str, str] | None = None,
    refresh: bool = False,
) -> Ingestion:
    """Load a benchmark's tasks and freeze them under the bundle root.

    Args:
        benchmark: Registered adapter name.
        settings: Cache location, bundle root, and the offline switch.
        ids: Ingest only these task ids.
        limit: Ingest the adapter's first N tasks.
        extras: Adapter-specific options, from ``--extra key=value``.
        refresh: Overwrite inputs that are already frozen. Off by default, so
            re-running an ingestion cannot change what an existing bundle was
            judged against.
    """
    tasks: list[Task] = []
    frozen: list[Path] = []
    reused = 0
    for task in stream_tasks(benchmark, settings, ids=ids, limit=limit, extras=extras):
        existed = (task_directory(settings.bundle_root, task) / "task.json").exists()
        frozen.append(freeze_task(settings.bundle_root, task, refresh=refresh))
        tasks.append(task)
        reused += int(existed and not refresh)
    log.info("ingested %d task(s) from %s (%d already frozen)", len(tasks), benchmark, reused)
    return Ingestion(
        benchmark=benchmark, tasks=tuple(tasks), frozen=tuple(frozen), reused=reused
    )


def load_tasks(settings: Settings, *, benchmark: str | None = None) -> list[Task]:
    """Read every task already frozen under the bundle root.

    This is how a later command works offline on what an earlier one ingested,
    including for benchmarks whose adapter needs the network.
    """
    root = Path(settings.bundle_root)
    if not root.is_dir():
        return []
    pattern = f"{benchmark}/*/task.json" if benchmark else "*/*/task.json"
    tasks: list[Task] = []
    for path in sorted(root.glob(pattern)):
        try:
            tasks.append(Task.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception as exc:
            raise BenchmarkError(f"{path} is not a usable task: {exc}") from exc
    return tasks
