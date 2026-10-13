# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The command line, as a user meets it.

Three things are checked here that a unit test cannot see. The first is that every
command's option types are declarable at all, which is what ``--help`` proves. The
second is the exit-code contract: continuous integration reads exit codes, so
"benchproofer broke" (1), "the command line was wrong" (2), and "the tool worked and
the result did not meet the bar" (3) have to stay distinct. The exit-code cases run
the installed entry point in a subprocess, because the mapping lives in
``cli.main.main`` rather than in the typer application.

The third is that the commands compose: what one stage writes is what the next one
reads. The smoke suite drives the pipeline through its own API, so the wiring in
``cli/`` -- option to setting, argument to filter, result to exit code -- is only
covered by running the commands, which is what the last cases here do. They stay
hermetic by running on the ``scripted`` provider and the ``scripted`` session, which answer
from the packaged fixture instead of from a model.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from benchproofer import __version__
from benchproofer.cli.main import app
from benchproofer.config import Settings
from benchproofer.core import markers
from benchproofer.core.bundle import Bundle
from benchproofer.core.sites import RECORD
from benchproofer.core.task import Task
from benchproofer.core.verdict import Status, Verdict
from benchproofer.errors import ConfigError
from benchproofer.pipeline.repair import RepairResult
from benchproofer.registries import BACKENDS, SESSIONS
from benchproofer.smoke import fixtures
from benchproofer.smoke.scripted import REVIEW_MODEL, ScriptedSession
from benchproofer.smoke.suites import cases
from benchproofer.util.fsio import read_text, write_text

COMMANDS = (
    "catalog",
    "doctor",
    "ingest",
    "formalize",
    "audit",
    "check",
    "repair",
    "run",
    "report",
    "smoke",
)

#: The backend the fixture bundles are written for, and the fixture whose specification
#: is too weak to reject the bug its task is about.
BACKEND = "falsifier"
WEAK = "coin-change-weak"

#: Budgets tuned to what the fixture ships, as the review smoke cases tune them: two
#: wrong implementations and one correct one written differently, which is exactly the
#: evidence the two strength gates ask for, and two mutants where sixteen would only be
#: slower. Set through the environment, which is the third source of a setting.
BUDGETS = {
    "BENCHPROOFER_AUDIT_ATTACKS": "2",
    "BENCHPROOFER_AUDIT_MIN_ATTACKS": "2",
    "BENCHPROOFER_AUDIT_CONTROLS": "1",
    "BENCHPROOFER_MUTATION_LIMIT": "2",
}

#: The gates that report an independent review, written out rather than derived from the
#: required set, so a level that quietly stopped requiring one of them fails here.
AUDIT_GATES = (
    "audit.independence",
    "audit.spec_completeness",
    "audit.spec_soundness",
    "audit.faithfulness",
    "audit.equivalence",
    "audit.no_disclosure",
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def _wide_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Render as if the terminal were wide.

    What is asserted here is what a command reports, not how rich lays it out, and at
    the 80 columns a test runner reports a path or a count is folded mid-value.
    """
    monkeypatch.setenv("COLUMNS", "200")


@pytest.fixture(autouse=True)
def _scripted_session(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Run every agent session a command starts on the ``scripted`` session.

    Registered in process as its entry point registers it, so a case reads this source
    tree's session rather than whatever the installed package's metadata names.
    """
    monkeypatch.setenv("BENCHPROOFER_SESSION", ScriptedSession.name)
    SESSIONS.register(ScriptedSession.name, ScriptedSession)
    yield
    SESSIONS.unregister(ScriptedSession.name)


def invoke(*arguments: str) -> Any:
    """Run the typer application in process and refuse to swallow a defect."""
    result = runner.invoke(app, list(arguments), catch_exceptions=False)
    assert result.exit_code == 0, f"{' '.join(arguments)} exited {result.exit_code}"
    return result


def document(*arguments: str) -> Any:
    """Run a command with ``--json`` and parse what it printed."""
    return json.loads(invoke(*arguments, "--json").stdout)


def attempt(*arguments: str) -> Any:
    """Run a command that is expected to fail, and return the result unjudged."""
    return runner.invoke(app, list(arguments), catch_exceptions=False)


def entry_point(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the console entry point the way a shell does."""
    return subprocess.run(
        [sys.executable, "-m", "benchproofer", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def scope(settings: Settings) -> tuple[str, ...]:
    """What every command in a multi-stage case needs: the corpus, and no network."""
    return ("--bundle-root", str(settings.bundle_root), "--offline")


def draft(settings: Settings, task: Task) -> Path:
    """Formalize one fixture task, and return the solution the next stage reads.

    The path is spelled out rather than looked up, because where a bundle lives is part
    of what the tool promises: ``<root>/<benchmark>/<task>/<backend>``.
    """
    invoke(
        "formalize",
        fixtures.BENCHMARK,
        "--id",
        task.task_id,
        "--backend",
        BACKEND,
        "--provider",
        "scripted",
        "--cache-dir",
        str(settings.cache_dir),
        *scope(settings),
    )
    return settings.bundle_root / fixtures.BENCHMARK / task.task_id / BACKEND / "solution.py"


def weaken(solution: Path) -> None:
    """Replace a drafted specification with one the task's own bug already satisfies.

    Spliced from the fixture that ships such a specification, which is what makes this a
    plausible mistake rather than a corruption: the file still verifies, and what objects
    to it is a gate about the task rather than one about the file.
    """
    comment = BACKENDS.get(BACKEND).comment
    weak = read_text(fixtures.fixture(WEAK).directory / "solution.py")
    write_text(
        solution,
        markers.replace_region(
            read_text(solution), comment, "spec", markers.parse(weak, comment)["spec"].text
        ),
    )


@pytest.mark.parametrize("command", COMMANDS)
def test_every_command_can_describe_itself(command: str) -> None:
    """A malformed option annotation fails here rather than in front of a user."""
    output = invoke(command, "--help").stdout

    assert command in output
    assert "Usage" in output


def test_the_catalog_reports_every_registry() -> None:
    listing = document("catalog")

    assert set(listing) == {
        "benchmarks",
        "backends",
        "oracles",
        "gates",
        "providers",
        "sessions",
    }
    for kind, rows in listing.items():
        assert rows, f"{kind} is empty"
        # A gate is identified by the id it records verdicts under; everything else
        # by the name it is registered as.
        assert all(row.get("name") or row["id"] for row in rows), f"{kind} has a nameless row"

    benchmarks = {row["name"] for row in listing["benchmarks"]}
    assert {"swebench-verified", "humaneval", "quixbugs", "jsonl"} <= benchmarks
    assert "artifact.integrity" in {row["id"] for row in listing["gates"]}


def test_the_doctor_reports_the_environment_without_needing_anything(tmp_path: Path) -> None:
    """The command that tells a new user what to install must run on a bare machine."""
    reported = document("doctor", "--bundle-root", str(tmp_path))

    assert reported["settings"]["bundle_root"] == str(tmp_path)
    assert reported["environment"]["python"].startswith("3.")
    assert isinstance(reported["ready_backends"], list)
    for name in ("backends", "oracles", "providers"):
        assert all("available" in row for row in reported[name])

    # The same values as a table, which is what a user without --json sees. A setting
    # resolved from a flag has to appear there too: the table is how someone finds out
    # which of the three sources won.
    printed = invoke("doctor", "--bundle-root", str(tmp_path)).output
    assert "settings in effect" in printed
    assert str(tmp_path) in printed


def test_the_smoke_catalog_lists_what_can_be_selected() -> None:
    listing = document("smoke", "--list")

    assert [item["id"] for item in listing["cases"]] == [item.id for item in cases()]
    assert {"offline", "all"} <= {suite["name"] for suite in listing["suites"]}
    assert listing["groups"]["pipeline"]


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (("catalog",), ("benchmarks", "gates", "jsonl", "artifact.integrity")),
        (("catalog", "backends"), ("backends", "falsifier")),
    ],
    ids=["every-registry", "one-registry"],
)
def test_the_catalog_prints_a_table_by_default(
    arguments: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    """--json is an alternative rendering of the same values, not the only one."""
    printed = invoke(*arguments).output

    for text in expected:
        assert text in printed, f"{' '.join(arguments)} did not mention {text!r}"


def test_the_smoke_command_runs_a_case_and_writes_its_report(tmp_path: Path) -> None:
    """`scripts/smoke.sh` runs the suite; this covers the command around it.

    Selecting one case, writing the report, and exiting 0 under ``--strict`` are the
    parts a suite of one case can check, and the case selected is the one that needs
    nothing from the machine, so it cannot be skipped here.
    """
    reports = tmp_path / "reports"

    result = document(
        "smoke",
        "registry.entry_points",
        "--workspace",
        str(tmp_path / "workspace"),
        "--cache-dir",
        str(tmp_path / "cache"),
        "--report",
        str(reports),
        "--offline",
        "--strict",
    )

    assert result["sound"]
    assert [case["status"] for case in result["cases"]] == ["passed"]
    assert json.loads((reports / "smoke.json").read_text(encoding="utf-8")) == result
    assert "registry.entry_points" in (reports / "smoke.md").read_text(encoding="utf-8")


def test_ingesting_a_local_benchmark_freezes_its_tasks(settings: Settings) -> None:
    arguments = (
        "ingest",
        "jsonl",
        "--extra",
        f"source={fixtures.tasks_file()}",
        "--extra",
        f"name={fixtures.BENCHMARK}",
        "--bundle-root",
        str(settings.bundle_root),
        "--offline",
    )

    frozen = document(*arguments)

    assert frozen["count"] >= 2
    assert frozen["reused"] == 0
    identifiers = {task["task_id"] for task in frozen["tasks"]}
    assert "coin-change" in identifiers
    for task in frozen["tasks"]:
        assert (
            settings.bundle_root / fixtures.BENCHMARK / task["task_id"] / "task.json"
        ).is_file()

    # The table a user sees names the suite the tasks were frozen as, because that is
    # what the next command filters on, and says how many were already there.
    printed = invoke(*arguments).output
    assert "coin-change" in printed
    assert f"as {fixtures.BENCHMARK}" in printed
    assert f"({frozen['count']} already present)" in printed

    # An input a bundle was judged against must not change under it.
    again = document(*arguments)
    assert again["reused"] == frozen["count"]
    assert [task["digest"] for task in again["tasks"]] == [
        task["digest"] for task in frozen["tasks"]
    ]


def test_ingesting_nothing_says_so_rather_than_reporting_success(settings: Settings) -> None:
    """A selection that matches no row is a mistake to point out, not zero tasks."""
    printed = invoke(
        "ingest",
        "jsonl",
        "--extra",
        f"source={fixtures.tasks_file()}",
        "--id",
        "no-such-task",
        "--bundle-root",
        str(settings.bundle_root),
        "--offline",
    ).output

    assert "No tasks matched" in printed
    assert not list(settings.bundle_root.glob("*/*/task.json"))


def test_a_report_over_unjudged_bundles_invents_no_verdicts(
    settings: Settings, tasks: dict[str, Task]
) -> None:
    """Reporting runs no gate, so a bundle nobody judged is unfinished, not passing.

    The default output is a table listing those bundles, and --json prints the same
    values, not more.
    """
    staged = [
        fixtures.stage(target, tasks[target.task_id], settings)
        for target in fixtures.coexisting()
    ]

    summary = document("report", "--bundle-root", str(settings.bundle_root))
    printed = invoke("report", "--bundle-root", str(settings.bundle_root)).output

    assert summary["total"] == len(staged)
    assert summary["counts"]["certified"] == 0
    assert summary["counts"]["incomplete"] == len(staged)
    assert summary["gates"] == {}
    for row in summary["bundles"]:
        assert set(row["missing"]) == set(summary["required_gates"])
    assert f"not certified ({len(staged)})" in printed
    for bundle in staged:
        assert bundle.manifest().task_id in printed


def test_formalizing_a_bundle_that_exists_reuses_it_and_reaches_no_model(
    settings: Settings, tasks: dict[str, Task], solution: str
) -> None:
    """Without --rebuild a drafted task is left alone, which is what resumes a run.

    The provider selected here is the one that refuses to answer, so a request to a
    model would fail the case rather than pass it slowly.
    """
    target = fixtures.fixture("coin-change-sound")
    bundle = fixtures.stage(target, tasks[target.task_id], settings)
    # What drafting read the patches to edit, which the resumed run keeps.
    manifest = bundle.manifest()
    kept = {"golden_patch": {"change.py": [["def make_change"]]}, "test_patch": {}}
    manifest.provenance = {**manifest.provenance, RECORD: kept}
    bundle.save_manifest(manifest)

    drafted = document(
        "formalize",
        fixtures.BENCHMARK,
        "--id",
        target.task_id,
        "--backend",
        target.backend,
        "--provider",
        "null",
        "--bundle-root",
        str(settings.bundle_root),
        "--cache-dir",
        str(settings.cache_dir),
        "--offline",
    )

    assert [task["drafted"] for task in drafted["tasks"]] == [False]
    assert [task["error"] for task in drafted["tasks"]] == [""]
    assert bundle.solution() == solution
    assert bundle.manifest().provenance[RECORD] == kept


def test_formalizing_a_task_that_could_not_be_attempted_exits_one(
    settings: Settings, tasks: dict[str, Task], monkeypatch: pytest.MonkeyPatch
) -> None:
    """No session and no provider means nothing was drafted: the tool failing, not a result."""
    monkeypatch.delenv("BENCHPROOFER_SESSION")
    assert "running-total" in tasks

    result = attempt(
        "formalize",
        fixtures.BENCHMARK,
        "--id",
        "running-total",
        "--backend",
        "falsifier",
        "--provider",
        "null",
        "--bundle-root",
        str(settings.bundle_root),
        "--cache-dir",
        str(settings.cache_dir),
        "--offline",
    )

    assert result.exit_code == 1
    assert "running-total" in result.output
    assert "Judge them with" not in result.output


def test_checking_one_gate_adds_to_manifest_json_rather_than_replacing_it(
    settings: Settings, tasks: dict[str, Task]
) -> None:
    """How a fixed gate is re-run over a corpus without paying for the others."""
    target = fixtures.fixture("coin-change-sound")
    fixtures.stage(target, tasks[target.task_id], settings)
    arguments = (
        "check",
        fixtures.BENCHMARK,
        "--backend",
        target.backend,
        "--bundle-root",
        str(settings.bundle_root),
        "--offline",
    )

    first = document(*arguments, "--only", "spec.hygiene")
    second = document(*arguments, "--only", "artifact.integrity")

    assert set(first["gates"]) == {"spec.hygiene"}
    assert set(second["gates"]) == {"spec.hygiene", "artifact.integrity"}
    # The required gates that never ran are reported as missing, so two favorable
    # verdicts are counted as incomplete rather than as progress.
    assert second["counts"] == {"certified": 0, "rejected": 0, "incomplete": 1, "dropped": 0}
    assert set(second["bundles"][0]["missing"]) == set(second["required_gates"]) - set(
        second["gates"]
    )


def test_a_corpus_that_is_not_certified_exits_three_under_strict(
    settings: Settings, tasks: dict[str, Task]
) -> None:
    """The distinction continuous integration reads: the tool worked, the evidence did not.

    One gate passing is not certification, and ``--strict`` alone turns that into exit 3.
    """
    target = fixtures.fixture("coin-change-sound")
    fixtures.stage(target, tasks[target.task_id], settings)

    result = attempt(
        "check",
        fixtures.BENCHMARK,
        "--only",
        "artifact.integrity",
        "--bundle-root",
        str(settings.bundle_root),
        "--offline",
        "--strict",
    )

    assert result.exit_code == 3
    assert "not certified" in result.output


@pytest.mark.slow
def test_a_run_takes_rows_to_judged_bundles_and_a_report(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one command the README shows, end to end, with no network and no model.

    ``--strict`` is what asserts the outcome: the command exits 3 unless every bundle
    it touched is certified, so a favorable exit code here means the fixture task was
    ingested, drafted, and judged by every required gate.
    """
    # Two mutants, set through the environment: this case is about the composition.
    monkeypatch.setenv("BENCHPROOFER_MUTATION_LIMIT", "2")
    reports = tmp_path / "reports"

    summary = document(
        "run",
        "jsonl",
        "--extra",
        f"source={fixtures.tasks_file()}",
        "--extra",
        f"name={fixtures.BENCHMARK}",
        "--id",
        "coin-change",
        "--backend",
        "falsifier",
        "--provider",
        "scripted",
        "--level",
        "static",
        "--bundle-root",
        str(settings.bundle_root),
        "--cache-dir",
        str(settings.cache_dir),
        "--report",
        str(reports),
        "--offline",
        "--strict",
    )

    assert summary["counts"] == {"certified": 1, "rejected": 0, "incomplete": 0, "dropped": 0}
    assert set(summary["gates"]) >= set(summary["required_gates"])
    assert summary["bundles"][0]["path"] == f"{fixtures.BENCHMARK}/coin-change/falsifier"
    written = json.loads((reports / "report.json").read_text(encoding="utf-8"))
    assert written["counts"] == summary["counts"]
    assert "# Benchproofer report" in (reports / "report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("again", [False, True], ids=["due", "again"])
def test_audit_asks_the_auditors_in_the_order_run_asks_them(
    again: bool, sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Through `pipeline.audit.review`, which asks the attack validation auditor last.

    `--again` asks every auditor beside those due, the attack validation auditor among them,
    which then rules on what the attack auditor filed in the same call.
    """
    from benchproofer.audit.session import LANES
    from benchproofer.cli import audit as command

    asked: list[tuple[str, ...]] = []
    monkeypatch.setattr(command, "review", lambda *_, again, **__: asked.append(tuple(again)))

    invoke("audit", fixtures.BENCHMARK, *scope(settings), *(["--again"] if again else []))

    assert asked == [LANES if again else ()]


@pytest.mark.slow
def test_the_audited_level_is_reachable_from_the_command_line(
    settings: Settings, coin_change: Task, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Draft, judge, review, judge again -- in that order, which is half of what is asserted.

    The smoke suite drives reviewing and repairing through their own API, so the commands
    around them are covered here. A bundle nobody has reviewed must not certify at this
    level; a repair must not treat a review that never happened as a defect in the
    artifacts; and neither of those is visible from a run that reviews first.
    """
    for name, value in BUDGETS.items():
        monkeypatch.setenv(name, value)
    where = scope(settings)
    draft(settings, coin_change)

    unreviewed = document("check", fixtures.BENCHMARK, "--level", "audited", *where)

    assert unreviewed["counts"] == {
        "certified": 0,
        "rejected": 0,
        "incomplete": 1,
        "dropped": 0,
    }
    assert set(AUDIT_GATES) <= set(unreviewed["bundles"][0]["undecided"])

    # Nothing here is a defect in the artifacts: the gates that objected are the ones
    # asking for a review, and redrafting a bundle because nobody has attacked it yet
    # would replace artifacts that may be sound with artifacts nobody has read either.
    unrepairable = document(
        "repair",
        fixtures.BENCHMARK,
        "--level",
        "audited",
        "--cache-dir",
        str(settings.cache_dir),
        *where,
    )

    assert unrepairable["repairs"] == []

    reviewed = document(
        "audit",
        fixtures.BENCHMARK,
        "--provider",
        "scripted",
        "--audit-model",
        REVIEW_MODEL,
        "--cache-dir",
        str(settings.cache_dir),
        *where,
    )
    [review] = reviewed["reviews"]

    assert review["reviewer"] == f"scripted:{REVIEW_MODEL}"
    assert review["independent"], "the bundle was reviewed by the model that drafted it"
    assert review["submissions"] == ["attack-1", "attack-2", "control-1"]
    assert review["judgments"] == {
        "faithfulness": "sound",
        "equivalence": "sound",
        "disclosure": "sound",
    }

    certified = document("check", fixtures.BENCHMARK, "--level", "audited", *where)

    assert certified["counts"] == {"certified": 1, "rejected": 0, "incomplete": 0, "dropped": 0}
    assert set(AUDIT_GATES) <= set(certified["required_gates"])

    # Reviewing again is not asked for, because the bundle already has a review of
    # the artifacts it ships; --again is how a budget is spent on a further one.
    again = invoke("audit", fixtures.BENCHMARK, *where).output
    assert "already have a current review" in again


@pytest.mark.slow
def test_a_rejected_bundle_is_repaired_and_certifies_again(
    settings: Settings, coin_change: Task, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The loop a corpus is built by, driven through the commands rather than the API.

    What certifies the bundle at the end is the repair, and the repair was aimed by the
    `manifest.json`: it is shown the verdicts on disk, and ``check`` is asked again afterwards
    because a repair judges nothing itself.
    """
    monkeypatch.setenv("BENCHPROOFER_MUTATION_LIMIT", "2")
    where = scope(settings)
    weaken(draft(settings, coin_change))

    rejected = document("check", fixtures.BENCHMARK, *where)

    assert rejected["counts"] == {"certified": 0, "rejected": 1, "incomplete": 0, "dropped": 0}
    assert "spec.discriminates" in rejected["bundles"][0]["failed"]

    repaired = document(
        "repair",
        fixtures.BENCHMARK,
        "--cache-dir",
        str(settings.cache_dir),
        *where,
    )
    [repair] = repaired["repairs"]

    assert "spec.discriminates" in repair["addressing"]
    assert repair["status"] == "REPAIRED"
    assert "solution.py" in repair["written"]

    certified = document("check", fixtures.BENCHMARK, *where)

    assert certified["counts"] == {"certified": 1, "rejected": 0, "incomplete": 0, "dropped": 0}


def test_a_bundle_holding_a_verdict_with_no_route_is_an_error_and_the_rest_are_repaired(
    settings: Settings, sound: Bundle, leaky: Bundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """As `run` reports such a task: the gate that recorded it is at fault, not the corpus."""
    sound.record(
        [
            Verdict(
                gate="spec.verifies",
                status=Status.FAIL,
                summary="the checker refutes it",
                details={"traceback": "..."},
            )
        ]
    )
    leaky.record(
        [Verdict(gate="spec.no_leakage", status=Status.FAIL, summary="the spec gives it away")]
    )
    answered: list[tuple[str, list[str]]] = []

    def repairing(bundle: Bundle, *, verdicts: list[Verdict], **_: object) -> RepairResult:
        answered.append((bundle.manifest().task_id, [verdict.gate for verdict in verdicts]))
        return RepairResult(task_key=bundle.manifest().task_id, bundle=bundle, written=())

    monkeypatch.setattr(
        importlib.import_module("benchproofer.cli.repair"), "repair_bundle", repairing
    )

    finished = attempt("repair", *scope(settings), "--json")

    assert finished.exit_code == 1
    reported = json.loads(finished.stdout)
    assert answered == [("running-total", ["spec.no_leakage"])]
    assert [entry["task"] for entry in reported["repairs"]] == ["running-total"]
    [error] = reported["errors"]
    assert error["bundle"] == sound.root.as_posix()
    assert error["error"].startswith("ValueError: no route for a spec.verifies verdict")


def test_the_version_is_printed_on_its_own_line(tmp_path: Path) -> None:
    finished = entry_point("--version", cwd=tmp_path)

    assert finished.returncode == 0
    assert finished.stdout.strip() == __version__


def test_a_command_line_mistake_is_not_reported_as_a_tool_failure(tmp_path: Path) -> None:
    assert entry_point("catalog", "--nonexistent", cwd=tmp_path).returncode == 2
    assert entry_point("catalog", "nonexistent", cwd=tmp_path).returncode == 2


def test_a_situation_the_user_can_fix_is_one_line_and_exit_one(tmp_path: Path) -> None:
    finished = entry_point("ingest", "no-such-benchmark", cwd=tmp_path)

    assert finished.returncode == 1
    assert "no-such-benchmark" in finished.stderr
    assert "Traceback" not in finished.stderr


def test_a_run_that_worked_but_covered_nothing_exits_three(tmp_path: Path) -> None:
    """--strict separates "the tool broke" from "the evidence is thin"."""
    finished = entry_point(
        "smoke",
        "benchmarks.swebench-verified",
        "--strict",
        "--workspace",
        str(tmp_path / "workspace"),
        "--cache-dir",
        str(tmp_path / "cache"),
        cwd=tmp_path,
    )

    assert finished.returncode == 3, finished.stderr
    assert "skipped" in finished.stderr


# ---- waivers ----------------------------------------------------------------
#
# A waiver is the one way a certificate can mean less than it says, so it has to carry a
# reason, the reason has to reach the report, and it cannot be spent on the gates the
# central claim is made of.


def test_a_waiver_carries_its_reason_into_the_report(
    settings: Settings, tasks: dict[str, Task]
) -> None:
    """The leaky fixture fails `spec.no_leakage`, which is a waivable objection."""
    target = fixtures.fixture("running-total-leaky")
    fixtures.stage(target, tasks[target.task_id], settings)
    because = "the statement quotes the code, and upstream will not amend it"

    report = document(
        "check",
        fixtures.BENCHMARK,
        "--backend",
        target.backend,
        "--bundle-root",
        str(settings.bundle_root),
        "--offline",
        "--waive",
        f"spec.no_leakage={because}",
    )

    row = report["bundles"][0]
    assert row["waived"] == [{"gate": "spec.no_leakage", "because": because}]
    # And the bundle certifies on less than the others, which is what the section says.
    assert "spec.no_leakage" not in row["failed"]


@pytest.mark.parametrize("entry", ["spec.strength.mutation", "=a reason", "  =  "])
def test_a_waiver_without_a_gate_and_a_reason_is_refused(
    settings: Settings, tasks: dict[str, Task], entry: str
) -> None:
    """A gate nobody can tell was overruled is the thing this rules out."""
    target = fixtures.fixture("running-total-leaky")
    fixtures.stage(target, tasks[target.task_id], settings)

    with pytest.raises(ConfigError, match=r"--waive expects gate=reason"):
        invoke(
            "check",
            fixtures.BENCHMARK,
            "--bundle-root",
            str(settings.bundle_root),
            "--offline",
            "--waive",
            entry,
        )


def test_the_gates_the_claim_is_made_of_cannot_be_waived(
    settings: Settings, tasks: dict[str, Task]
) -> None:
    """Not a weaker certificate but a false one, which no reason can make true."""
    target = fixtures.fixture("coin-change-sound")
    fixtures.stage(target, tasks[target.task_id], settings)

    with pytest.raises(ConfigError, match=r"spec\.verifies cannot be waived"):
        invoke(
            "check",
            fixtures.BENCHMARK,
            "--bundle-root",
            str(settings.bundle_root),
            "--offline",
            "--waive",
            "spec.verifies=the checker is being slow today",
        )
