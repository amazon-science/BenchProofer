# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The correctness oracles that need nothing but this machine.

An oracle is the only component that can say a candidate really solves a task, so
the asymmetry it has to preserve is tested directly: a candidate it cannot judge is
reported as unanswered, never as wrong.

An oracle that runs tests also has something else a gate needs: the environment it
runs them in. `probe` lends that environment to a program the caller supplies, which
is how a specification's assumption about a callee stated as an axiom is put to the callee
itself, so the second half of this module is about what a program run there can see
and what its exit code is read as.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchproofer.core.plugin import Availability
from benchproofer.core.task import OracleSpec, SourceFile, Task, TaskContext
from benchproofer.oracles import docker
from benchproofer.oracles.base import Candidate, OracleResult, OracleStatus, Program
from benchproofer.oracles.docker import _compare
from benchproofer.registries import ORACLES
from benchproofer.util.proc import Completed

PATCH_ONLY = "--- a/change.py\n+++ b/change.py\n@@ -1 +1 @@\n-old\n+new\n"

#: An `axioms.py` in miniature: it reaches the module under test the way the
#: benchmark's own tests reach it, and reports on the callee it exercised.
GROUNDING = """\
import change

print("benchproofer:grounded change.make_change", change.make_change(40))
"""

#: What a bundle for an answer benchmark hands the oracle: not the answer, but the
#: Python copy of the implementation that was verified, which computes it.
SHADOW = """\
# benchproofer:target solution.py
impl = 14 * 9 - 3
print(impl)
"""


def judge(kind: str, task: Task, candidate: Candidate, workdir: Path) -> OracleResult:
    workdir.mkdir(parents=True, exist_ok=True)
    return ORACLES.get(kind).judge(task, candidate, workdir=workdir, timeout_s=60.0)


def probe(kind: str, task: Task, program: Program, workdir: Path) -> OracleResult:
    workdir.mkdir(parents=True, exist_ok=True)
    return ORACLES.get(kind).probe(task, program, workdir=workdir, timeout_s=60.0)


def shadow(source: str) -> Candidate:
    """A candidate that answers with a program, which is the form a bundle takes."""
    files = (SourceFile(path="solution.py", content=source),)
    return Candidate(files=files, label="shadow")


def test_the_answer_oracle_compares_values_not_formatting(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    task = tasks["orchard-yield"]

    assert task.oracle.kind == "answer"
    attempts = [
        (task.oracle.expected, OracleStatus.RESOLVED),
        (f" {task.oracle.expected}.\n", OracleStatus.RESOLVED),
        ("122", OracleStatus.UNRESOLVED),
    ]
    for index, (answer, expected) in enumerate(attempts):
        candidate = Candidate(answer=answer, label="answer")
        result = judge("answer", task, candidate, tmp_path / f"answer-{index}")
        assert result.status is expected, f"{answer!r}: {result.detail}"


def test_a_candidate_with_no_answer_is_unanswered_rather_than_wrong(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    result = judge("answer", tasks["orchard-yield"], Candidate(label="silent"), tmp_path)

    assert result.status is OracleStatus.UNAVAILABLE
    assert not result.resolved


def test_a_shadow_is_judged_by_the_answer_it_computes(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    """A verified bundle answers with a program, because what it verified is one.

    Without this the conformance gate could never be decided on an answer benchmark:
    it hands every oracle a file, and a bundle that stated its answer as a literal
    would be claiming something no checker looked at.
    """
    task = tasks["orchard-yield"]
    off_by_one = shadow(SHADOW.replace("- 3", "- 2"))

    accepted = judge("answer", task, shadow(SHADOW), tmp_path / "accepted")
    rejected = judge("answer", task, off_by_one, tmp_path / "rejected")

    assert accepted.status is OracleStatus.RESOLVED, accepted.detail
    assert accepted.detail == "answer matches (123)"
    assert rejected.status is OracleStatus.UNRESOLVED, rejected.detail
    assert "'124'" in rejected.detail


@pytest.mark.parametrize(
    ("label", "program", "expected"),
    [
        ("shows its working", "print('126 - 3')\nprint(123)\n", OracleStatus.RESOLVED),
        (
            "warns on the way past",
            "import sys\n\nprint('note', file=sys.stderr)\nprint(123)\n",
            OracleStatus.RESOLVED,
        ),
        ("crashes", "raise ValueError('no idea')\n", OracleStatus.UNRESOLVED),
        ("prints nothing", "answer = 123\n", OracleStatus.UNRESOLVED),
        ("imports what is absent", "import not_a_module_here\n", OracleStatus.UNAVAILABLE),
    ],
)
def test_only_the_last_line_a_program_prints_is_read_as_its_answer(
    tasks: dict[str, Task], tmp_path: Path, label: str, program: str, expected: OracleStatus
) -> None:
    """A program that never states an answer is wrong; one that cannot run is unjudged."""
    result = judge("answer", tasks["orchard-yield"], shadow(program), tmp_path)

    assert result.status is expected, f"{label}: {result.detail}"


def test_the_inline_oracle_accepts_the_reference_and_rejects_the_pre_fix_state(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    task = tasks["coin-change"]
    assert task.oracle.kind == "inline-tests"

    reference = judge("inline-tests", task, Candidate.reference(task), tmp_path / "reference")
    pre_fix = judge(
        "inline-tests",
        task,
        Candidate(files=task.context.files, label="pre-fix"),
        tmp_path / "pre-fix",
    )

    assert reference.status is OracleStatus.RESOLVED, reference.detail
    assert pre_fix.status is OracleStatus.UNRESOLVED, pre_fix.detail


def test_a_candidate_the_oracle_cannot_apply_is_unanswered(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    """A patch has nothing to import, which is not the same as being wrong."""
    candidate = Candidate(patch=PATCH_ONLY, label="patch-only")

    result = judge("inline-tests", tasks["coin-change"], candidate, tmp_path)

    assert result.status is OracleStatus.UNAVAILABLE


@pytest.mark.parametrize("label", ["reference", "wrong", "empty"])
def test_a_benchmark_with_no_mechanical_check_never_reports_a_solution(
    tasks: dict[str, Task], tmp_path: Path, label: str
) -> None:
    task = tasks["orchard-yield"]
    candidates = {
        "reference": Candidate.reference(task),
        "wrong": Candidate(answer="wrong", label="wrong"),
        "empty": Candidate(label="empty"),
    }

    result = judge("none", task, candidates[label], tmp_path / label)

    assert result.status is OracleStatus.UNAVAILABLE


def test_a_timeout_is_recorded_as_undecided_and_says_it_timed_out() -> None:
    """A hang is not a rejection: nothing was decided."""
    result = OracleResult.timeout("pytest did not finish within 30s")

    assert result.status is OracleStatus.ERROR
    assert result.timed_out
    assert not result.resolved


# ---- lending the environment to one program ------------------------------


def test_a_program_runs_beside_the_module_the_benchmarks_tests_import(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    result = probe(
        "inline-tests",
        tasks["coin-change"],
        Program(source=GROUNDING, label="axioms"),
        tmp_path,
    )

    assert result.status is OracleStatus.RESOLVED, result.detail
    assert "benchproofer:grounded change.make_change" in result.output
    assert (tmp_path / "axioms.py").is_file()


def test_a_program_that_exits_non_zero_is_unresolved_rather_than_broken(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    """The caller wrote the program, so what a refusal means is the caller's business."""
    result = probe(
        "inline-tests",
        tasks["coin-change"],
        Program(source="raise SystemExit(3)\n", label="axioms"),
        tmp_path,
    )

    assert result.status is OracleStatus.UNRESOLVED
    assert result.detail == "axioms exited 3"


def test_a_program_may_ask_for_the_tree_the_benchmarks_own_fix_produces(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    """A callee the fix introduces does not exist in the task as it ships."""
    before = probe(
        "inline-tests",
        tasks["coin-change"],
        Program(source=GROUNDING, label="before"),
        tmp_path / "before",
    )
    after = probe(
        "inline-tests",
        tasks["coin-change"],
        Program(source=GROUNDING, label="after", with_reference=True),
        tmp_path / "after",
    )

    assert (before.status, after.status) == (OracleStatus.RESOLVED, OracleStatus.RESOLVED)
    assert before.output.strip().endswith("(1, 1, 0, 5)")
    assert after.output.strip().endswith("(1, 1, 1, 0)")


def test_a_benchmark_that_states_its_fix_as_a_patch_has_no_fixed_tree_to_offer(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    """Staging the unfixed task instead would ground the assumption against the bug."""
    task = tasks["coin-change"]
    patched = task.model_copy(
        update={"reference": task.reference.model_copy(update={"files": ()})}
    )

    result = probe(
        "inline-tests", patched, Program(source=GROUNDING, with_reference=True), tmp_path
    )

    assert result.status is OracleStatus.UNAVAILABLE
    assert "no solved module" in result.detail


def test_the_pytest_oracle_lays_out_the_tests_beside_the_code_under_test(
    tmp_path: Path,
) -> None:
    """A program run where the tests run may import their helpers, so they have to be there."""
    task = Task(
        benchmark="local",
        task_id="totals",
        statement="make the running total right",
        context=TaskContext(files=(SourceFile(path="totals.py", content="TOTAL = 1\n"),)),
        oracle=OracleSpec(
            kind="pytest",
            tests=("tests/test_totals.py::test_total",),
            files=(SourceFile(path="tests/test_totals.py", content="def test_total(): ...\n"),),
        ),
    )
    program = "import totals\n\nopen('tests/test_totals.py').read()\nprint(totals.TOTAL)\n"

    result = probe("pytest", task, Program(source=program, label="axioms"), tmp_path)

    assert result.status is OracleStatus.RESOLVED, result.output
    assert result.output.strip() == "1"


def test_an_oracle_with_no_environment_of_its_own_declines_to_run_a_program(
    tasks: dict[str, Task], tmp_path: Path
) -> None:
    """An oracle that compares answer strings has nowhere to run anything."""
    result = probe("answer", tasks["orchard-yield"], Program(source="print(1)\n"), tmp_path)

    assert result.status is OracleStatus.UNAVAILABLE
    assert "cannot run a program" in result.detail


def test_every_registered_oracle_reports_whether_it_can_run_here() -> None:
    """An oracle that cannot run says so, with a reason, before anything asks it."""
    for name in ORACLES.names():
        oracle = ORACLES.get(name)
        availability = oracle.availability()
        assert oracle.summary.strip(), f"{name} has no summary"
        assert bool(availability) or availability.detail, f"{name} is missing without a reason"

    assert ORACLES.get("docker").needs_docker
    assert not ORACLES.get("answer").needs_docker


@pytest.mark.parametrize(
    ("outcomes", "inert"),
    [
        ({"t::fixed": "FAILED", "t::kept_a": "PASSED", "t::kept_b": "FAILED"}, False),
        ({"t::fixed": "FAILED", "t::kept_a": "ERROR", "t::kept_b": "FAILED"}, True),
    ],
    ids=["a behavior wrong", "nothing kept"],
)
def test_a_candidate_that_loses_every_kept_test_broke_the_code_rather_than_a_behavior(
    outcomes: dict[str, str], inert: bool, coin_change: Task
) -> None:
    """Which is a fact about the edit, and what lets a caller not read it as a wrong answer."""
    task = coin_change.model_copy(
        update={
            "oracle": OracleSpec(
                kind="docker", tests=("t::fixed",), regression=("t::kept_a", "t::kept_b")
            )
        }
    )

    result = _compare(task, outcomes, 1.0, "", "")

    assert result.status is OracleStatus.UNRESOLVED
    assert bool(result.inert) is inert


@pytest.mark.parametrize("timed_out", [True, False], ids=["outlived", "finished"])
def test_a_container_is_killed_only_when_it_outlives_its_budget(
    timed_out: bool, monkeypatch: pytest.MonkeyPatch, coin_change: Task, tmp_path: Path
) -> None:
    """Only a timed-out container is killed: killing the `docker` client leaves it running."""
    calls: list[tuple[str, ...]] = []

    def fake(command: tuple[str, ...], **_: object) -> Completed:
        calls.append(tuple(command))
        late = timed_out and command[1] == "run"
        return Completed(tuple(command), -9 if late else 0, "", "", 1.0, late)

    monkeypatch.setattr(docker, "run", fake)

    result = docker._docker_run(coin_change, "image", tmp_path, 10)

    assert result.timed_out is timed_out
    name = calls[0][calls[0].index("--name") + 1]
    assert calls[1:] == ([("docker", "kill", name)] if timed_out else [])


def test_a_container_keeps_its_own_limits_for_when_its_client_is_gone(
    monkeypatch: pytest.MonkeyPatch, coin_change: Task, tmp_path: Path
) -> None:
    """A killed client sees no exit, so the container stops itself, at its cap or on EOF.

    Its cap is a little past the client's budget, so a client still waiting reports the
    timeout, and its standard input is held open by the client for as long as it runs.
    """
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def fake(command: tuple[str, ...], **options: object) -> Completed:
        calls.append((tuple(command), options))
        return Completed(tuple(command), 0, "", "", 1.0, False)

    monkeypatch.setattr(docker, "run", fake)

    docker._docker_run(coin_change, "image", tmp_path, 10)

    (command, options), *_ = calls
    script = command[command.index("-c") + 1]
    assert "--rm" in command and "--interactive" in command
    assert options["hold_stdin"] is True
    assert options["timeout_s"] == 10 + docker._STARTUP_S
    assert f"sleep {10 + docker._STARTUP_S + docker._CAP_GRACE_S} " in script
    assert "/bin/bash /bp/run.sh" in script


def test_a_program_run_in_the_image_prints_text_that_is_not_ascii(
    monkeypatch: pytest.MonkeyPatch, coin_change: Task, tmp_path: Path
) -> None:
    """An image whose locale is ASCII ends a program on its first such character otherwise."""
    oracle = docker.DockerOracle()
    monkeypatch.setattr(oracle, "availability", lambda: Availability.ok())
    monkeypatch.setattr(docker, "_ensure_image", lambda task, timeout_s: "image")
    monkeypatch.setattr(
        docker,
        "_docker_run",
        lambda task, image, workdir, budget: Completed(("docker",), 0, "", "", 1.0, False),
    )

    oracle.probe(coin_change, Program(source="print('\\u00e9')\n"), workdir=tmp_path)

    run = (tmp_path / "run.sh").read_text()
    assert "PYTHONIOENCODING=utf-8:backslashreplace" in run
    assert run.index("PYTHONIOENCODING") < run.index("/bp/probe.py")


def test_a_program_run_in_the_image_may_name_a_patch_in_place_of_the_golden_patch(
    monkeypatch: pytest.MonkeyPatch, coin_change: Task, tmp_path: Path
) -> None:
    """An attack's witness test runs once on the fixed code and once on the attack's patch."""
    oracle = docker.DockerOracle()
    monkeypatch.setattr(oracle, "availability", lambda: Availability.ok())
    monkeypatch.setattr(docker, "_ensure_image", lambda task, timeout_s: "image")
    monkeypatch.setattr(
        docker,
        "_docker_run",
        lambda task, image, workdir, budget: Completed(("docker",), 91, "", "", 1.0, False),
    )
    patched = "diff --git a/change.py b/change.py\n--- a/change.py\n+++ b/change.py\n"

    result = oracle.probe(
        coin_change,
        Program(source="pass\n", label="witness", with_reference=True, patch=patched),
        workdir=tmp_path,
    )

    assert (tmp_path / "reference.patch").read_text() == patched
    assert result.status is OracleStatus.UNAVAILABLE
    assert result.detail.startswith("the patch it was asked to run with does not apply")


@pytest.mark.parametrize("kind", ["inline-tests", "pytest"])
def test_an_oracle_that_stages_files_runs_no_program_on_a_patch_of_its_own(
    kind: str, coin_change: Task, tmp_path: Path
) -> None:
    """Staging the fixed tree instead would run it on code it did not ask for."""
    result = probe(
        kind, coin_change, Program(source="pass\n", label="witness", patch="diff"), tmp_path
    )

    assert result.status is OracleStatus.UNAVAILABLE
    assert "witness asks for a patch applied in place of" in result.detail
