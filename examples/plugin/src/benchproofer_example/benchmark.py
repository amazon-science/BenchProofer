# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A benchmark adapter that ships its own tasks.

A real adapter downloads a pinned dataset and normalizes its rows. This one skips
the download so the example runs anywhere, and keeps everything else the same: it
describes itself for the catalog, reports whether it can run here, and yields
`Task` objects in a stable order.

The tasks are deliberately shaped like a repair benchmark. Each one ships a broken
module as its context and the fixed module as its reference, which is what gives a
bundle a pre-fix twin to discriminate against.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar

from benchproofer.benchmarks.base import Benchmark, BenchmarkInfo, LoadRequest
from benchproofer.core.plugin import Availability
from benchproofer.core.task import OracleSpec, Reference, SourceFile, Task, TaskContext
from benchproofer.util.digest import digest_text

ROWS = (
    {
        "task_id": "clamp",
        "path": "clamp.py",
        "statement": (
            "clamp(x, low, high) returns x confined to the closed interval "
            "[low, high]: low when x is below it, high when x is above it, and x "
            "otherwise. The implementation ignores the lower bound."
        ),
        "broken": "def clamp(x, low, high):\n    return min(x, high)\n",
        "fixed": "def clamp(x, low, high):\n    return max(low, min(x, high))\n",
        "tests": (
            "assert clamp(5, 0, 10) == 5\n"
            "assert clamp(-3, 0, 10) == 0\n"
            "assert clamp(42, 0, 10) == 10\n"
        ),
    },
    {
        "task_id": "count-vowels",
        "path": "vowels.py",
        "statement": (
            "count_vowels(s) returns how many characters of s are English vowels, "
            "in either case. The implementation misses uppercase vowels."
        ),
        "broken": ("def count_vowels(s):\n    return sum(1 for c in s if c in 'aeiou')\n"),
        "fixed": (
            "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')\n"
        ),
        "tests": (
            "assert count_vowels('') == 0\n"
            "assert count_vowels('rhythm') == 0\n"
            "assert count_vowels('Education') == 5\n"
        ),
    },
    {
        "task_id": "last-index",
        "path": "search.py",
        "statement": (
            "last_index(xs, target) returns the largest index at which target "
            "occurs in xs, or -1 when it does not occur. The implementation "
            "returns the first index instead of the last."
        ),
        "broken": (
            "def last_index(xs, target):\n"
            "    for i, x in enumerate(xs):\n"
            "        if x == target:\n"
            "            return i\n"
            "    return -1\n"
        ),
        "fixed": (
            "def last_index(xs, target):\n"
            "    found = -1\n"
            "    for i, x in enumerate(xs):\n"
            "        if x == target:\n"
            "            found = i\n"
            "    return found\n"
        ),
        "tests": (
            "assert last_index([], 1) == -1\n"
            "assert last_index([1, 2, 1], 1) == 2\n"
            "assert last_index([1, 2, 3], 4) == -1\n"
        ),
    },
)


class MiniBenchmark(Benchmark):
    """Three small repair tasks, shipped with the plugin."""

    name: ClassVar[str] = "mini"

    def info(self) -> BenchmarkInfo:
        """Describe the benchmark for `benchproofer catalog benchmarks`."""
        return BenchmarkInfo(
            name=self.name,
            title="Mini repair tasks (example plugin)",
            summary="Three one-line defects, shipped with the plugin rather than downloaded.",
            license="CC-BY-NC-4.0",
            languages=("python",),
            oracle="inline-tests",
            size=len(ROWS),
            remote=False,
        )

    def availability(self) -> Availability:
        """Always usable: nothing is downloaded and nothing is installed."""
        return Availability.ok()

    def load(self, request: LoadRequest) -> Iterator[Task]:
        """Yield the tasks in a fixed order, honoring the request's filters."""
        return self.take((_task(row) for row in ROWS), request)


def _task(row: dict[str, str]) -> Task:
    return Task(
        benchmark="mini",
        task_id=row["task_id"],
        statement=row["statement"],
        context=TaskContext(
            files=(SourceFile(path=row["path"], content=row["broken"]),),
            entry_points=(row["task_id"].replace("-", "_"),),
        ),
        reference=Reference(files=(SourceFile(path=row["path"], content=row["fixed"]),)),
        oracle=OracleSpec(kind="inline-tests", tests=(row["tests"],)),
        # What the normalization was derived from. A real adapter digests the
        # upstream bytes here, so a row that changed later is detectable.
        source_digest=digest_text(row["broken"] + row["fixed"] + row["tests"]),
    )
