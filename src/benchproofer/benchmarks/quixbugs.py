# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""QuixBugs: single-line bugs in classic algorithms.

Each task is one Python module with one defect, plus the project's own pytest file.
Two properties make it a useful benchmark for Benchproofer:

* the pre-fix implementation ships alongside the fixed one, so a bundle has a pre-fix
  implementation to discriminate against without anyone writing one by hand;
* the modules are small and self-contained, so their specifications are within
  reach of a solver and of the checkers, which makes it a good first target when
  bringing up a new backend.

The repository is not a dataset file, so it is fetched as a pinned checkout. Only
the files a given task's test actually imports are attached to that task, which is
what keeps a task self-contained.
"""

from __future__ import annotations

import ast
import difflib
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar

from ..core.plugin import Availability
from ..core.task import OracleSpec, Reference, SourceFile, Task, TaskContext
from ..errors import BenchmarkError
from ..util.digest import digest_json
from .base import Benchmark, BenchmarkInfo, LoadRequest
from .vcs import RepoSpec, checkout, git_availability

__all__ = ["QuixBugsBenchmark", "quixbugs"]

#: Directory holding the defective programs; also where a candidate is written.
_BUGGY = "python_programs"
#: Directory holding the fixed programs, used as the reference solution.
_FIXED = "correct_python_programs"
#: Directory holding the pytest files and their two helper modules.
_TESTS = "python_testcases"
#: Directory holding the parametrized inputs some tests load by name.
_DATA = "json_testcases"


class QuixBugsBenchmark(Benchmark):
    """The Python half of QuixBugs, one task per program."""

    name: ClassVar[str] = "quixbugs"
    spec: ClassVar[RepoSpec] = RepoSpec(
        url="https://github.com/jkoppel/QuixBugs",
        commit="4257f44b0ff1181dedaedee6a447e133219fcebf",
        license="MIT",
    )

    def info(self) -> BenchmarkInfo:
        """Describe QuixBugs."""
        return BenchmarkInfo(
            name=self.name,
            title="QuixBugs (Python)",
            summary=(
                "Classic algorithms with a one-line defect, shipped with both the "
                "broken and the fixed version, so every task has a pre-fix implementation."
            ),
            url=self.spec.url,
            license=self.spec.license,
            oracle="pytest",
            size=40,
        )

    def availability(self) -> Availability:
        """Report whether Git is available to fetch the checkout."""
        return git_availability()

    def load(self, request: LoadRequest) -> Iterator[Task]:
        """Fetch the pinned checkout and build one task per program."""
        root = checkout(self.spec, request.cache_dir, offline=request.offline)
        return self.take(self._tasks(root), request)

    def _tasks(self, root: Path) -> Iterator[Task]:
        for test in sorted((root / _TESTS).glob("test_*.py")):
            name = test.stem.removeprefix("test_")
            buggy = root / _BUGGY / f"{name}.py"
            fixed = root / _FIXED / f"{name}.py"
            if not (buggy.exists() and fixed.exists()):
                continue
            yield self._task(root, name, buggy, fixed, test)

    def _task(self, root: Path, name: str, buggy: Path, fixed: Path, test: Path) -> Task:
        broken = _read(buggy)
        repaired = _read(fixed)
        tests = _read(test)
        path = f"{_BUGGY}/{name}.py"
        return Task(
            benchmark=self.name,
            task_id=name,
            statement=_statement(broken, name),
            context=TaskContext(
                files=(SourceFile(path=path, content=broken),),
                entry_points=(name,),
            ),
            reference=Reference(
                patch=_diff(path, broken, repaired),
                files=(SourceFile(path=path, content=repaired),),
                symbols=(name,),
            ),
            oracle=OracleSpec(
                kind="pytest",
                tests=(f"{_TESTS}/{test.name}",),
                files=_support(root, name, tests, test),
                timeout_s=120,
            ),
            metadata={"source": self.spec.pin},
            source_digest=digest_json(
                {"program": broken, "reference": repaired, "tests": tests}
            ),
        )


def _support(root: Path, name: str, tests: str, test: Path) -> tuple[SourceFile, ...]:
    """Collect the files this task's test needs, and no others.

    The project's root ``conftest.py`` is always required: it defines the options
    the tests read to decide which version of a program to import. The remaining
    helpers are attached only when the test imports them.
    """
    wanted = [Path("conftest.py"), Path(_TESTS) / test.name]
    if "load_testdata" in tests:
        wanted.append(Path(_TESTS) / "load_testdata.py")
        wanted.append(Path(_DATA) / f"{name}.json")
    if "from node import" in tests:
        wanted.append(Path(_TESTS) / "node.py")

    files: list[SourceFile] = []
    for relative in wanted:
        source = root / relative
        if not source.exists():
            raise BenchmarkError(f"quixbugs/{name}: the checkout is missing {relative}")
        files.append(SourceFile(path=relative.as_posix(), content=_read(source)))
    return tuple(files)


def _statement(source: str, name: str) -> str:
    """Extract the problem statement, which each program carries as a trailing string.

    Falls back to naming the function when a program carries no such block, so a
    task is still usable rather than silently statement-free.
    """
    fallback = f"Repair the defect in {name}."
    try:
        module = ast.parse(source)
    except SyntaxError:
        return fallback
    blocks = [
        node.value.value
        for node in module.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    return blocks[-1].strip() if blocks else fallback


def _diff(path: str, before: str, after: str) -> str:
    """Render the golden patch as a unified diff."""
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        n=3,
    )
    return "".join(lines)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def quixbugs() -> QuixBugsBenchmark:
    """Entry point factory."""
    return QuixBugsBenchmark()
