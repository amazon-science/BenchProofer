# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Judging and reporting a corpus.

What the gates decide about a bundle is checked by the smoke suite, against fixtures
that declare the reaction they were written to provoke. What is checked here is the
machinery around them: which bundles are found, how a `manifest.json` accumulates across runs,
and what a report says about a bundle nobody finished judging. Those are the paths
where a corpus could quietly look better than it is.

Every test runs offline with the falsifier backend, so the suite needs no verifier
toolchain and no container runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.task import Task
from benchproofer.core.verdict import Level, Outcome, SkipReason, Status, Verdict
from benchproofer.llm.agentic import AgentSession, SessionSpec, StepOutcome
from benchproofer.llm.null import NullProvider
from benchproofer.pipeline.adjudicate import (
    ORACLE_REQUIRED,
    STATIC_REQUIRED,
    adjudicate,
    bundles_under,
    certify,
    required_gates,
)
from benchproofer.pipeline.report import collect, write_report
from benchproofer.pipeline.run import execute, judge_bundles
from benchproofer.registries import BACKENDS, SESSIONS
from benchproofer.smoke import fixtures
from benchproofer.util.fsio import write_text

LEVEL = Level.STATIC
#: Gates cheap enough to run in a unit-test suite: they read the artifacts and never
#: invoke a verifier. The gates that do are exercised by the smoke suite.
CHEAP = ("artifact.integrity", "spec.hygiene")


@pytest.fixture
def staged(settings: Settings, tasks: dict[str, Task]) -> list[Bundle]:
    """Every fixture that can share one bundle root, copied into a fresh one."""
    return [
        fixtures.stage(target, tasks[target.task_id], settings)
        for target in fixtures.coexisting()
    ]


def passing(gate: str) -> Verdict:
    """A favorable verdict, as a gate would record it."""
    return Verdict(gate=gate, status=Status.PASS, summary="recorded by a test", level=LEVEL)


def test_a_corpus_is_discovered_at_one_fixed_depth(
    settings: Settings, staged: list[Bundle]
) -> None:
    """A bundle is <root>/<benchmark>/<task>/<backend>; nothing else is a bundle.

    One whose artifacts were removed but whose `manifest.json` remains is still found, so a
    verdict that cannot be re-checked stays visible.
    """
    (settings.bundle_root / "stray").mkdir(parents=True, exist_ok=True)
    (settings.bundle_root / fixtures.BENCHMARK / "coin-change" / "falsifier" / "deep").mkdir()
    staged[0].record([passing("artifact.integrity")])
    for artifact in staged[0].root.glob("solution.*"):
        artifact.unlink()

    found = bundles_under(settings.bundle_root)

    assert {bundle.root for bundle in found} == {bundle.root for bundle in staged}
    assert found == sorted(found, key=lambda bundle: bundle.root)


def test_reading_manifest_json_never_fills_a_missing_verdict_in(staged: list[Bundle]) -> None:
    """`certify` runs no gate, so an unjudged bundle is incomplete, not passing."""
    certification = certify(staged[0], LEVEL)

    assert certification.outcome is Outcome.INCOMPLETE
    assert certification.missing == list(STATIC_REQUIRED)
    assert not certification.failed


def test_oracle_evidence_is_required_only_at_the_oracle_level(staged: list[Bundle]) -> None:
    """A statically certified bundle is not certified once the oracle is asked for."""
    bundle = staged[0]
    bundle.record([passing(gate) for gate in STATIC_REQUIRED])

    assert certify(bundle, Level.STATIC).outcome is Outcome.CERTIFIED
    escalated = certify(bundle, Level.ORACLE)
    assert escalated.outcome is Outcome.INCOMPLETE
    assert escalated.missing == [
        gate for gate in ORACLE_REQUIRED if gate not in STATIC_REQUIRED
    ]
    assert "impl.conformance" in escalated.missing
    assert set(required_gates(Level.ORACLE)) == set(ORACLE_REQUIRED)


def test_a_bounded_search_that_found_nothing_is_not_a_pass(staged: list[Bundle]) -> None:
    """The asymmetry certification rests on: undecided is not favorable."""
    bundle = staged[0]
    inconclusive = Verdict(
        gate="spec.strength.mutation",
        status=Status.SKIP,
        skip_reason=SkipReason.INCONCLUSIVE,
        summary="the falsifier found no counterexample within its budget",
        level=LEVEL,
    )
    bundle.record([passing(gate) for gate in STATIC_REQUIRED if gate != inconclusive.gate])
    bundle.record([inconclusive])

    certification = certify(bundle, LEVEL)

    assert certification.outcome is Outcome.INCOMPLETE
    assert certification.undecided == ["spec.strength.mutation"]


def test_judging_some_gates_adds_to_manifest_json_instead_of_replacing_it(
    settings: Settings, staged: list[Bundle]
) -> None:
    """Evidence gathered by an earlier run still counts, and is not silently reused."""
    bundle = staged[0]
    bundle.record([passing(gate) for gate in STATIC_REQUIRED])

    adjudication = adjudicate(
        bundle,
        backend=BACKENDS.get(bundle.backend_name),
        settings=settings,
        level=LEVEL,
        only=CHEAP,
    )

    assert sorted(adjudication.verdicts) == sorted(CHEAP)
    ledger = bundle.manifest().verdicts
    assert set(ledger) == set(STATIC_REQUIRED)
    assert ledger["spec.verifies"].summary == "recorded by a test"
    for gate in CHEAP:
        assert ledger[gate].summary != "recorded by a test"
        assert ledger[gate].tool_version


def test_one_unjudgeable_bundle_does_not_stop_the_others(
    settings: Settings, staged: list[Bundle]
) -> None:
    """A run reports what it could not do; it does not abandon the corpus."""
    ghost = Bundle(settings.bundle_root / fixtures.BENCHMARK / "ghost" / "falsifier")

    result = judge_bundles([*staged, ghost], settings=settings, level=LEVEL, only=CHEAP)

    assert result.total == len(staged) + 1
    assert {outcome.bundle.root for outcome in result.errors()} == {ghost.root}
    assert result.errors()[0].outcome == "error"
    judged = [outcome for outcome in result.outcomes if outcome.judged]
    assert len(judged) == len(staged)
    assert all(outcome.certification is not None for outcome in judged)
    # A bundle that could not be read is not a row in the report either way.
    assert result.report.total == len(staged)


def test_a_gate_that_crashes_is_undecided_rather_than_a_finding(
    settings: Settings, staged: list[Bundle]
) -> None:
    """A defect in the tool must not be recorded as a defect in the artifacts."""
    bundle = staged[0]
    for artifact in bundle.root.glob("solution.*"):
        artifact.unlink()

    adjudicate(
        bundle,
        backend=BACKENDS.get(bundle.backend_name),
        settings=settings,
        level=LEVEL,
        only=CHEAP,
    )
    ledger = bundle.manifest().verdicts

    # The gate that checks the artifact set reports the absence as a finding, because
    # a bundle with no solution really is not one.
    assert ledger["artifact.integrity"].status is Status.FAIL
    # The gate that wanted to read the file crashed, and a crash decides nothing.
    crashed = ledger["spec.hygiene"]
    assert crashed.status is Status.ERROR
    assert not crashed.ok
    assert not crashed.decided


def test_a_report_reads_the_corpus_back_and_writes_both_formats(
    settings: Settings, staged: list[Bundle], tmp_path: Path
) -> None:
    for bundle in staged:
        bundle.record([passing(gate) for gate in STATIC_REQUIRED])

    summary = collect(settings.bundle_root, level=LEVEL)

    assert summary.total == len(staged)
    assert len(summary.certified()) == len(staged)
    assert summary.counts()[str(Outcome.CERTIFIED)] == len(staged)
    assert all(not Path(row.path).is_absolute() for row in summary.rows)

    document, rendered = write_report(summary, tmp_path / "out")
    written = json.loads(document.read_text())

    assert written["counts"] == summary.counts()
    assert written["required_gates"] == list(STATIC_REQUIRED)
    assert "None." in rendered.read_text()


def test_a_report_names_the_gate_a_bundle_is_missing(
    settings: Settings, staged: list[Bundle]
) -> None:
    """An unfinished bundle is reported with its reason, not as a rate."""
    for bundle in staged:
        bundle.record([passing(gate) for gate in STATIC_REQUIRED if gate != "spec.verifies"])

    summary = collect(settings.bundle_root, level=LEVEL)

    assert summary.counts()[str(Outcome.INCOMPLETE)] == len(staged)
    for row in summary.rows:
        assert row.missing == ("spec.verifies",)
        assert "missing spec.verifies" in row.reason()


def test_a_report_lists_each_callee_result_taken_as_an_input_as_a_call_no_gate_checks(
    settings: Settings, staged: list[Bundle], tmp_path: Path
) -> None:
    """Taking a callee's result as an input leaves the call unchecked, which fails no gate.

    So the report says so beside the outcome, entry by entry as `correspondence.md` lists
    them, and a section that is `Nothing.` lists none.
    """
    listing, quiet = staged[0], staged[1]
    entries = (
        "`pkg.net.Probe.run_command` at pkg/net.py:41: (a) it runs `ip`, a subprocess",
        "`pkg.clock.now` at pkg/clock.py:7: (a) the clock",
    )
    write_text(
        listing.correspondence_path,
        "## Not modeled\n\nNothing.\n\n## Outside the bridge\n\nNothing.\n\n"
        "## Callee results taken as inputs\n\n"
        "* `pkg.net.Probe.run_command` at pkg/net.py:41: (a) it runs `ip`,\n"
        "  a subprocess\n"
        "- `pkg.clock.now` at pkg/clock.py:7: (a) the clock\n",
    )
    write_text(quiet.correspondence_path, "## Callee results taken as inputs\n\nNothing.\n")
    for bundle in staged:
        bundle.record([passing(gate) for gate in STATIC_REQUIRED])

    summary = collect(settings.bundle_root, level=LEVEL)

    rows = {row.path: row for row in summary.rows}
    shown = rows[listing.root.relative_to(settings.bundle_root).as_posix()]
    assert shown.inputs == entries
    assert shown.outcome is Outcome.CERTIFIED
    assert not rows[quiet.root.relative_to(settings.bundle_root).as_posix()].inputs
    document, rendered = write_report(summary, tmp_path / "out")
    (written,) = [
        bundle for bundle in json.loads(document.read_text())["bundles"] if bundle["inputs"]
    ]
    assert written["inputs"] == list(shown.inputs)
    markdown = rendered.read_text()
    assert "## Callee results taken as inputs (2)" in markdown
    assert f"| {shown.key} | {entries[1]} |" in markdown


class Blocked(AgentSession):
    """A drafting session that reports it is blocked and writes no solution file."""

    name = "blocked"
    remote = False

    def run(self, spec: SessionSpec) -> StepOutcome:
        blocked = "the callee is a C extension"
        payload = {"status": "BLOCKED", "summary": "x", "blocked": blocked}
        return StepOutcome(text="", payload=payload)


def test_a_draft_that_was_never_finished_is_not_an_error(
    settings: Settings, coin_change: Task
) -> None:
    """A session that produced nothing to judge leaves a bundle incomplete.

    The tool did its job here: it asked, it gave up, and it said so. That
    is a fact about the attempt rather than a failure of the run, so it must not be
    reported as an error, which is what makes ``--strict`` the thing that decides
    whether a corpus is good enough.
    """
    SESSIONS.register(Blocked.name, Blocked)
    try:
        result = execute(
            [coin_change],
            backend=BACKENDS.get("falsifier"),
            provider=NullProvider(),
            settings=settings.model_copy(update={"session": Blocked.name}),
            level=LEVEL,
        )
    finally:
        SESSIONS.unregister(Blocked.name)

    outcome = result.outcomes[0]
    assert not result.errors()
    assert result.unfinished() == (outcome,)
    assert outcome.built and outcome.certification is None
    assert outcome.outcome == str(Outcome.INCOMPLETE)
    assert "nothing to judge" in outcome.unfinished

    # The message sends a reviewer to the notes, so the notes have to be there and have
    # to account for the attempt: an empty bundle explains nothing on its own.
    assert str(outcome.bundle.root) in outcome.unfinished
    notes = outcome.bundle.notes_path.read_text(encoding="utf-8")
    assert "artifacts: none" in notes
    assert "What the session had to work around" in notes


def test_a_report_can_be_narrowed_to_one_benchmark_or_backend(
    settings: Settings, staged: list[Bundle]
) -> None:
    assert collect(settings.bundle_root, benchmark=fixtures.BENCHMARK).total == len(staged)
    assert collect(settings.bundle_root, benchmark="elsewhere").total == 0
    assert collect(settings.bundle_root, backend="falsifier").total == len(staged)
    assert collect(settings.bundle_root, backend="dafny").total == 0
