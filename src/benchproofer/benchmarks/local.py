# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Local JSON Lines adapter: the bring-your-own-benchmark path.

Point this at a file and every row becomes a task, so a benchmark that is not
published anywhere, or one that cannot leave a network, can be formalized with the
same commands as a public one::

    benchproofer ingest jsonl --extra source=my-tasks.jsonl --extra name=my-suite

Each line is a JSON object with the fields of `Task`. Only `task_id` and `statement`
are required; `benchmark` defaults to ``name``, and ``name`` to the file's stem. A row
that names its own `benchmark` keeps it, so one file can hold several suites.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

from ..core.plugin import Availability
from ..core.task import Task
from ..errors import BenchmarkError
from ..util.digest import digest_json
from .base import Benchmark, BenchmarkInfo, LoadRequest
from .dataset import read_rows

__all__ = ["JsonlBenchmark", "jsonl"]


class JsonlBenchmark(Benchmark):
    """Load tasks from a local JSON Lines file."""

    name: ClassVar[str] = "jsonl"

    def info(self) -> BenchmarkInfo:
        """Describe the adapter."""
        return BenchmarkInfo(
            name=self.name,
            title="Local JSON Lines file",
            summary="Tasks written by hand or exported from another tool.",
            languages=("any",),
            remote=False,
        )

    def availability(self) -> Availability:
        """This adapter is always usable; it reads a file the caller names."""
        return Availability.ok()

    def load(self, request: LoadRequest) -> Iterator[Task]:
        """Read every row of the named file as a task.

        Raises:
            BenchmarkError: ``source`` is missing, the file does not exist, or a
                row is not a valid task.
        """
        source = request.extras.get("source") or request.extras.get("path")
        if not source:
            raise BenchmarkError(
                "the jsonl benchmark needs a source file: --extra source=<file.jsonl>"
            )
        path = Path(source).expanduser()
        if not path.is_file():
            raise BenchmarkError(f"no such file: {path}")

        default_name = request.extras.get("name") or path.stem
        return self.take(self._tasks(path, default_name), request)

    def _tasks(self, path: Path, default_name: str) -> Iterator[Task]:
        for index, row in enumerate(read_rows(path), start=1):
            yield self._task(row, default_name, f"{path}:{index}")

    @staticmethod
    def _task(row: dict[str, Any], default_name: str, where: str) -> Task:
        payload = dict(row)
        payload.setdefault("benchmark", default_name)
        payload.setdefault("source_digest", digest_json(row))
        for required in ("task_id", "statement"):
            if not payload.get(required):
                raise BenchmarkError(f"{where}: missing {required!r}")
        try:
            return Task.model_validate(payload)
        except Exception as exc:
            raise BenchmarkError(f"{where}: {exc}") from exc


def jsonl() -> JsonlBenchmark:
    """Entry point factory."""
    return JsonlBenchmark()
