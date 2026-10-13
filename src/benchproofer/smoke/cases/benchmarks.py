# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Can each installed benchmark adapter be ingested here.

One case per registered adapter, generated from the registry. This is the group that
answers the generality question: the same code path, with no per-benchmark branch
anywhere downstream, has to turn a HumanEval row, a GSM8K word problem, a QuixBugs
repository and a SWE-bench instance into the same kind of `Task`.

What a case checks is deliberately about the *contract* rather than about the data.
A task must name its benchmark, carry a statement, agree with the catalog about which
oracle judges it, ship the benchmark's own solution in some form, and
record a digest of the upstream row so a dataset that changes underneath is
detectable. It must also survive being frozen and read back, because every later
stage reads the frozen copy rather than the adapter's output.

Adapters that download a dataset require ``network``; the ones whose download is
large are marked slow. Under the hermetic default they are reported as skipped, with
the reason, rather than quietly left out.
"""

from __future__ import annotations

from ...core.task import Task
from ...errors import PluginError
from ...pipeline.ingest import ingest, load_tasks
from ...registries import BENCHMARKS, ORACLES
from ..fixtures import BENCHMARK, tasks_file
from ..model import Case, Context, Observation, Procedure, check, equals

__all__ = ["CASES"]

#: How many tasks to ingest per adapter. Two is enough to catch a normalizer that
#: only works on the first row, and cheap enough for a suite.
SAMPLE = 2

#: Adapters whose cold-cache download or checkout runs into minutes.
_SLOW = frozenset(
    {"bigcodebench", "swebench-verified", "swebench-lite", "swebench-pro", "quixbugs"}
)

#: Extra requirements beyond the adapter itself.
_TOOLS: dict[str, tuple[str, ...]] = {"quixbugs": ("tool:git",)}


def _extras(name: str) -> dict[str, str]:
    """Adapter options for one case: the generic reader is pointed at the fixture tasks."""
    if name == "jsonl":
        return {"source": str(tasks_file()), "name": BENCHMARK}
    return {}


def _expected_benchmark(name: str) -> str:
    """The benchmark name the ingested tasks should carry."""
    return BENCHMARK if name == "jsonl" else name


def _has_reference(task: Task) -> bool:
    """True when the task ships the benchmark's own solution in some form."""
    reference = task.reference
    return bool(reference.patch or reference.files or reference.answer)


def _procedure(name: str) -> Procedure:
    """Build the case procedure for one benchmark adapter."""

    def run(context: Context) -> list[Observation]:
        adapter = BENCHMARKS.get(name)
        info = adapter.info()
        equals(info.name, name, f"{name}: the adapter's info names itself")
        check(info.title, f"{name}: the catalog entry has no title")
        check(info.summary, f"{name}: the catalog entry has no summary")
        check(
            info.oracle in ORACLES.names(),
            f"{name}: declares oracle {info.oracle!r}, which is not registered",
        )

        ingestion = ingest(name, context.settings, limit=SAMPLE, extras=_extras(name))
        check(ingestion.tasks, f"{name}: ingested no task")

        expected = _expected_benchmark(name)
        for task in ingestion.tasks:
            where = f"{name}/{task.task_id}"
            equals(task.benchmark, expected, f"{where}: benchmark name on the task")
            check(task.task_id.strip(), f"{name}: a task has an empty id")
            check(task.statement.strip(), f"{where}: statement is empty")
            check(
                task.oracle.kind in ORACLES.names(),
                f"{where}: is judged by oracle {task.oracle.kind!r}, which is not registered",
            )
            if info.oracle != "none":
                # An adapter that names an oracle attaches it to every task. One that
                # does not, such as the generic jsonl reader, passes through whatever
                # each row declares, which the check above covers.
                equals(
                    task.oracle.kind, info.oracle, f"{where}: oracle kind against the catalog"
                )
            check(
                task.source_digest,
                f"{where}: no digest of the upstream row, so a dataset that changed "
                "later would be undetectable",
            )
            check(
                _has_reference(task),
                f"{where}: ships no golden patch, reference file or expected answer, so the "
                "benchmark's own solution cannot be checked against the specification",
            )
            copy = Task.model_validate_json(task.model_dump_json())
            equals(copy.digest(), task.digest(), f"{where}: digest across a serialization")

        equals(
            len(ingestion.frozen),
            len(ingestion.tasks),
            f"{name}: frozen task files against ingested tasks",
        )
        reloaded = {task.task_id: task for task in load_tasks(context.settings)}
        for task in ingestion.tasks:
            frozen = reloaded.get(task.task_id)
            check(frozen is not None, f"{name}/{task.task_id}: was not frozen on disk")
            assert frozen is not None  # noqa: S101 - narrowing after the check above
            equals(
                frozen.digest(),
                task.digest(),
                f"{name}/{task.task_id}: digest of the frozen copy",
            )

        first = ingestion.tasks[0]
        return [
            Observation("catalog", f"{info.title}, oracle={info.oracle}, size={info.size}"),
            Observation("ingested", f"{ingestion.count} task(s)"),
            Observation(
                "first",
                f"{first.task_id}: {len(first.statement)} char statement, "
                f"{len(first.context.files)} context file(s), "
                f"{len(first.oracle.tests)} test(s)",
            ),
        ]

    return run


def _remote(name: str) -> bool:
    """Whether an adapter needs the network on a cold cache.

    An adapter that cannot even be imported here is assumed to need it. The
    ``benchmark:`` requirement is what actually reports that, so the guess only
    decides which of two skip reasons the case shows.
    """
    try:
        return BENCHMARKS.get(name).info().remote
    except PluginError:
        return True


def _requires(name: str) -> tuple[str, ...]:
    """What one adapter's case needs from this machine."""
    needs = [f"benchmark:{name}"]
    if _remote(name):
        needs.append("network")
    needs.extend(_TOOLS.get(name, ()))
    return tuple(needs)


CASES: tuple[Case, ...] = tuple(
    Case(
        id=f"benchmarks.{name}",
        summary=f"the {name} adapter ingests tasks that satisfy the task contract",
        procedure=_procedure(name),
        requires=_requires(name),
        slow=name in _SLOW,
    )
    for name in BENCHMARKS.names()
)
