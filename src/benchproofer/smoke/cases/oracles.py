# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Does each correctness oracle answer the benchmark's own question.

An oracle is the only part of Benchproofer that can say a candidate really solves a
task, so the whole audit rests on it. Every case here asks the same three questions
of one oracle, and the third is the one that matters most:

1. Does it accept the benchmark's own solution? If not, nothing it says
   about anything else is worth reading.
2. Does it refuse the state of the task *before* the fix? An oracle that accepts the
   defective version is measuring nothing. A defective version that never terminates
   has to be reported as a timeout rather than as a rejection, because the oracle did
   not reach an answer.
3. Does it report a candidate it cannot judge as unanswered rather than as wrong?
   Collapsing "I could not run" into "it failed" is how a broken environment turns
   into an apparent defect in an artifact, and it is the failure mode this suite
   exists to catch.

The oracles that need a repository, a container, or the network are covered by cases
marked slow, so a normal run stays offline and a full run reaches SWE-bench.
"""

from __future__ import annotations

from ...core.task import SourceFile, Task
from ...oracles.base import Candidate, OracleResult, OracleStatus
from ...pipeline.ingest import ingest
from ...registries import ORACLES
from .. import fixtures
from ..model import Case, Context, Observation, check, equals

__all__ = ["CASES"]

#: Fixture tasks the inline-test oracle is asked about.
_INLINE = ("coin-change", "running-total")

#: A patch is the wrong shape for a single-module oracle: it has nothing to import.
#: Judging it is not the same as judging a wrong answer.
_UNJUDGEABLE = "--- a/change.py\n+++ b/change.py\n@@ -1 +1 @@\n-old\n+new\n"

#: Budget for judging a candidate that may not terminate. Long enough for a small
#: project's test file, short enough that a hang does not dominate the suite.
HANG_BUDGET_S = 30.0

#: The shape a bundle for `orchard-yield` submits: a program that prints the answer on
#: its last line, which is the Python copy of whatever the checker accepted.
_SHADOW = "# benchproofer:target solution.py\nimpl = 14 * 9 - 3\nprint(impl)\n"


def _judged(
    kind: str,
    task: Task,
    candidate: Candidate,
    context: Context,
    *,
    label: str,
    timeout_s: float | None = None,
) -> OracleResult:
    """Ask one oracle about one candidate, in its own scratch directory."""
    budget = float(context.settings.oracle_timeout_s) if timeout_s is None else timeout_s
    return ORACLES.get(kind).judge(
        task,
        candidate,
        workdir=context.path("judge", task.task_id, label),
        timeout_s=budget,
    )


def _shadow(source: str) -> Candidate:
    """A candidate that answers with a program, as a bundle does."""
    return Candidate(files=(SourceFile(path="solution.py", content=source),), label="shadow")


def _rejected(result: OracleResult, where: str) -> str:
    """Fail unless a defective candidate was not accepted, and say how it was judged.

    Two results are admissible. Failing the task's tests is the ordinary one. A
    defective program that never terminates is the other: the oracle reports a
    timeout, which is recorded as `OracleStatus.ERROR` because nothing was decided,
    and calling that a rejection would credit Benchproofer with a verdict it did not
    reach. Anything else, including a missing dependency, is a defect.

    Returns:
        A phrase describing the result, for the case's observations.
    """
    check(
        result.status is not OracleStatus.RESOLVED,
        f"{where} was accepted by the oracle: {result.detail}",
    )
    if result.status is OracleStatus.UNRESOLVED:
        return f"rejected: {result.detail}"
    check(
        result.timed_out,
        f"{where} was judged {result.status} rather than rejected: {result.detail}",
    )
    return f"never terminated: {result.detail}"


def inline_tests(context: Context) -> list[Observation]:
    """The inline-test oracle accepts each reference and rejects each pre-fix state."""
    tasks = fixtures.tasks(context.settings)
    observations: list[Observation] = []

    for task_id in _INLINE:
        task = tasks[task_id]
        equals(task.oracle.kind, "inline-tests", f"{task_id}: the fixture's oracle")

        reference = _judged(
            "inline-tests", task, Candidate.reference(task), context, label="reference"
        )
        equals(
            reference.status, OracleStatus.RESOLVED, f"{task_id}: the benchmark's own solution"
        )

        before = Candidate(files=task.context.files, label="pre-fix")
        check(
            not before.is_empty,
            f"{task_id}: the fixture ships no pre-fix files, so there is nothing to "
            "check the oracle discriminates against",
        )
        pre_fix = _judged("inline-tests", task, before, context, label="pre-fix")
        equals(
            pre_fix.status,
            OracleStatus.UNRESOLVED,
            f"{task_id}: the state of the task before the fix",
        )
        observations.append(
            Observation(task_id, f"reference={reference.status}, pre-fix={pre_fix.status}")
        )

    unjudgeable = _judged(
        "inline-tests",
        tasks[_INLINE[0]],
        Candidate(patch=_UNJUDGEABLE, label="patch-only"),
        context,
        label="unjudgeable",
    )
    equals(
        unjudgeable.status,
        OracleStatus.UNAVAILABLE,
        "a candidate the oracle cannot apply is reported as unanswered, not as wrong",
    )
    observations.append(Observation("patch-only candidate", str(unjudgeable.status)))
    return observations


def answer(context: Context) -> list[Observation]:
    """The answer oracle compares values, however the candidate arrives at one."""
    task = fixtures.tasks(context.settings)["orchard-yield"]
    equals(task.oracle.kind, "answer", "the fixture's oracle")

    reference = _judged("answer", task, Candidate.reference(task), context, label="reference")
    equals(reference.status, OracleStatus.RESOLVED, "the benchmark's own answer")

    formatted = _judged(
        "answer", task, Candidate(answer=" 123.\n", label="formatted"), context, label="format"
    )
    equals(
        formatted.status,
        OracleStatus.RESOLVED,
        "the right answer with stray punctuation and whitespace",
    )

    off_by_one = Candidate(answer="122", label="wrong")
    wrong = _judged("answer", task, off_by_one, context, label="off")
    equals(wrong.status, OracleStatus.UNRESOLVED, "an answer that is off by one")

    silent = _judged("answer", task, Candidate(label="silent"), context, label="silent")
    equals(
        silent.status,
        OracleStatus.UNAVAILABLE,
        "a candidate with no answer is reported as unanswered, not as wrong",
    )

    # What a bundle actually submits: the Python copy of the verified implementation,
    # which computes the answer instead of quoting it. Without this the conformance
    # gate could never be decided on a benchmark of this shape.
    computed = _judged("answer", task, _shadow(_SHADOW), context, label="shadow")
    equals(computed.status, OracleStatus.RESOLVED, "a program that prints the right answer")
    miscomputed = _judged(
        "answer", task, _shadow(_SHADOW.replace("- 3", "- 2")), context, label="shadow-wrong"
    )
    equals(miscomputed.status, OracleStatus.UNRESOLVED, "a program that prints the wrong one")

    return [
        Observation("expected", str(task.oracle.expected)),
        Observation("reference", str(reference.status)),
        Observation("' 123.'", str(formatted.status)),
        Observation("'122'", str(wrong.status)),
        Observation("no answer", str(silent.status)),
        Observation("computed answer", computed.detail),
        Observation("miscomputed answer", miscomputed.detail),
    ]


def declined(context: Context) -> list[Observation]:
    """A task with no mechanical check never reports a candidate as correct."""
    task = fixtures.tasks(context.settings)["orchard-yield"]
    for candidate in (
        Candidate.reference(task),
        Candidate(answer="wrong", label="wrong"),
        Candidate(label="empty"),
    ):
        result = _judged("none", task, candidate, context, label=candidate.label)
        equals(
            result.status,
            OracleStatus.UNAVAILABLE,
            f"the null oracle asked about a {candidate.label} candidate",
        )
    return [Observation("all candidates", str(OracleStatus.UNAVAILABLE))]


def _first(name: str, context: Context) -> Task:
    """Ingest one task from a remote benchmark."""
    ingestion = ingest(name, context.settings, limit=1)
    check(ingestion.tasks, f"{name}: ingested no task")
    return ingestion.tasks[0]


def pytest_files(context: Context) -> list[Observation]:
    """The pytest oracle runs a real project's own tests over a candidate."""
    task = _first("quixbugs", context)
    where = f"quixbugs/{task.task_id}"
    equals(task.oracle.kind, "pytest", f"{where}: the declared oracle")

    reference = _judged("pytest", task, Candidate.reference(task), context, label="reference")
    equals(
        reference.status,
        OracleStatus.RESOLVED,
        f"{where}: the project's own fixed version ({reference.detail})",
    )

    # An empty candidate leaves the program as the task ships it, which is the
    # defective version. Several QuixBugs bugs are infinite loops, so the budget is
    # short: a hang is one of the answers `_rejected` accepts, and waiting out the
    # benchmark's own two-minute allowance would only make the suite slower.
    pre_fix = _judged(
        "pytest",
        task,
        Candidate(label="pre-fix"),
        context,
        label="pre-fix",
        timeout_s=HANG_BUDGET_S,
    )
    answered = _rejected(pre_fix, f"{where}: the defective version shipped with the task")
    return [
        Observation("task", where),
        Observation("tests", ", ".join(task.oracle.tests)),
        Observation("reference", f"resolved: {reference.detail}"),
        Observation("pre-fix", answered),
    ]


def container(context: Context) -> list[Observation]:
    """The container oracle judges a SWE-bench instance in the project's own image."""
    task = _first("swebench-verified", context)
    equals(task.oracle.kind, "docker", f"{task.key}: the declared oracle")
    check(task.oracle.tests, f"{task.key}: lists no test that has to change to passing")

    reference = _judged("docker", task, Candidate.reference(task), context, label="reference")
    equals(
        reference.status,
        OracleStatus.RESOLVED,
        f"{task.key}: the benchmark's own patch ({reference.detail})",
    )

    pre_fix = _judged("docker", task, Candidate(label="pre-fix"), context, label="pre-fix")
    answered = _rejected(pre_fix, f"{task.key}: the repository with no patch applied at all")
    return [
        Observation("task", task.key),
        Observation("image", task.oracle.image or "none"),
        Observation(
            "tests",
            f"{len(task.oracle.tests)} target, {len(task.oracle.regression)} regression",
        ),
        Observation("reference", f"resolved: {reference.detail}"),
        Observation("pre-fix", answered),
    ]


CASES: tuple[Case, ...] = (
    Case(
        id="oracles.inline_tests",
        summary="the inline-test oracle accepts the golden patch and rejects the pre-fix state",
        procedure=inline_tests,
        requires=("benchmark:jsonl", "oracle:inline-tests"),
    ),
    Case(
        id="oracles.answer",
        summary="the answer oracle judges a value and a program that computes one",
        procedure=answer,
        requires=("benchmark:jsonl", "oracle:answer"),
    ),
    Case(
        id="oracles.declined",
        summary="a benchmark with no mechanical check never reports a candidate as correct",
        procedure=declined,
        requires=("benchmark:jsonl", "oracle:none"),
    ),
    Case(
        id="oracles.pytest",
        summary="the pytest oracle judges a QuixBugs task with the project's own tests",
        procedure=pytest_files,
        requires=(
            "benchmark:quixbugs",
            "oracle:pytest",
            "network",
            "tool:git",
            "module:pytest",
        ),
        slow=True,
    ),
    Case(
        id="oracles.docker",
        summary="the container oracle judges a SWE-bench instance in its own image",
        procedure=container,
        requires=("benchmark:swebench-verified", "oracle:docker", "docker", "network"),
        slow=True,
    ),
)
