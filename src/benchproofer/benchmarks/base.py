# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The benchmark-adapter interface.

An adapter owns one upstream dataset. It fetches the rows, pins what it fetched,
and normalizes each row into a `Task`. Nothing downstream knows which benchmark a
task came from, which is the property that makes the tool general: a new
benchmark is a new adapter, not a new code path.

Adapters must be honest about pinning. `DatasetSpec` carries a revision and, when
the upstream host allows it, a checksum, so two people who run the same command
ingest the same bytes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from ..core.plugin import Availability
from ..core.task import Task

__all__ = ["Benchmark", "BenchmarkInfo", "LoadRequest"]


@dataclass(frozen=True, slots=True)
class BenchmarkInfo:
    """Static description of a benchmark, shown by ``benchproofer catalog``."""

    name: str
    title: str
    summary: str = ""
    url: str = ""
    license: str = ""
    languages: tuple[str, ...] = ("python",)
    #: Registered oracle the adapter attaches to its tasks.
    oracle: str = "none"
    #: Number of tasks upstream, when it is fixed and known.
    size: int | None = None
    #: True when loading requires network access on a cold cache.
    remote: bool = True


@dataclass(frozen=True, slots=True)
class LoadRequest:
    """Parameters of one ingestion.

    Selection is deterministic: `ids` wins, then `limit` takes the first tasks in
    the adapter's own stable order. There is no sampling, because a benchmark
    subset that changes between runs cannot be compared between runs.
    """

    cache_dir: Path
    ids: tuple[str, ...] = ()
    limit: int | None = None
    offline: bool = False
    extras: dict[str, str] = field(default_factory=dict)

    def wanted(self, task_id: str) -> bool:
        """True when a task id passes the id filter."""
        return not self.ids or task_id in self.ids


class Benchmark(ABC):
    """Base class for benchmark adapters."""

    #: Registry name, matching the entry point.
    name: ClassVar[str]

    @abstractmethod
    def info(self) -> BenchmarkInfo:
        """Describe this benchmark."""

    @abstractmethod
    def load(self, request: LoadRequest) -> Iterator[Task]:
        """Yield normalized tasks in a stable order.

        Implementations honor `request.ids`, `request.limit`, and
        `request.offline`, and set `Task.source_digest` from the upstream bytes so
        a row that changed later is detectable.
        """

    def availability(self) -> Availability:
        """Report whether this adapter can load anything here."""
        return Availability.ok()

    def take(self, tasks: Iterable[Task], request: LoadRequest) -> Iterator[Task]:
        """Apply the request's id and limit filters to a stream of tasks."""
        emitted = 0
        for task in tasks:
            if not request.wanted(task.task_id):
                continue
            yield task
            emitted += 1
            if request.limit is not None and emitted >= request.limit:
                return

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
