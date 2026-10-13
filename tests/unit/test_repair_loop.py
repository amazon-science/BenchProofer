# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The judge-and-repair loop edits a bundle as it stands and never undoes a repair.

A repair is an attempt, and the judgment after it is the only thing that says whether it
helped: one that made things worse is answered by the next repair, which is shown every
earlier round of the run. Gates, repairs and reviews are scripted, so each case says
exactly which round did what and checks what the loop did about it, including the one
shortfall it answers with another review rather than a repair.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from benchproofer.audit.session import LANES, SUBMISSION_GATES, Audit
from benchproofer.config import Settings
from benchproofer.core import replay
from benchproofer.core.bundle import Bundle
from benchproofer.core.rounds import RECORD, directory
from benchproofer.core.task import Task
from benchproofer.core.verdict import Level, Outcome, SkipReason, Status, Verdict
from benchproofer.errors import ProviderError
from benchproofer.pipeline import audit as reviewing
from benchproofer.pipeline import run
from benchproofer.pipeline.adjudicate import (
    DISQUALIFYING,
    REVIEWED,
    Adjudication,
    classified,
    required_gates,
)
from benchproofer.pipeline.audit import AuditResult
from benchproofer.pipeline.run import TaskOutcome, _process
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_json, read_text, write_text

LEVEL = Level.STATIC


def verdict(
    gate: str,
    status: Status = Status.PASS,
    summary: str = "",
    *,
    level: Level = LEVEL,
    **details: Any,
) -> Verdict:
    skip = SkipReason.INCONCLUSIVE if status is Status.SKIP else None
    return Verdict(
        gate=gate,
        status=status,
        summary=summary or f"{gate} {status}",
        level=level,
        skip_reason=skip,
        details=details,
    )


def ledger(level: Level = LEVEL, **overrides: Status | Verdict) -> dict[str, Verdict]:
    """A verdict for every required gate: favorable unless a case says otherwise."""
    found: dict[str, Verdict] = {}
    for gate in required_gates(level):
        given = overrides.get(gate.replace(".", "_"), Status.PASS)
        found[gate] = given if isinstance(given, Verdict) else verdict(gate, given, level=level)
    return found


def judged(bundle: Bundle, verdicts: dict[str, Verdict], level: Level = LEVEL) -> Adjudication:
    return Adjudication(
        task_key="coin-change",
        bundle=bundle,
        backend=bundle.backend_name,
        level=level,
        verdicts=verdicts,
        certification=classified(verdicts, level),
    )


#: The first judgment of every case: the solution verifies, the property-based test suite
#: objects.
WEAK = {"spec_strength_battery": Status.FAIL}
#: What a regressing repair produces: the checker no longer accepts the file.
BROKEN = {"spec_verifies": Status.FAIL, "spec_strength_battery": Status.FAIL}


class Scripted:
    """Stands in for the gates and for the repair session, one scripted answer per round.

    Judging records its verdicts in `manifest.json`, as the real one does; repairing writes a
    marker into the solution file, so that a case can tell which attempts' edits ended up
    on disk, and a report into `manifest.json`. A review is only counted. A round's gates may be
    judged in two steps, those a program decides and then those that read the review: the
    first step takes the round's scripted answer and the second reads the rest of it, and a
    round that judges only the review's gates takes an answer of its own. The review's own
    judging of the two submission gates, before the attack validation auditor is asked, reads
    the answer the gates that read the review then take. Judging the task's own checks, before
    anything is drafted, answers ``screened`` for each of them and consumes no answer.
    """

    def __init__(
        self,
        bundle: Bundle,
        *judgments: dict[str, Status | Verdict],
        level: Level = LEVEL,
        screened: Status = Status.PASS,
    ) -> None:
        self.bundle = bundle
        self.judgments = list(judgments)
        self.level = level
        self.screened = screened
        self.screens = 0
        self.repairs: list[dict[str, Any]] = []
        self.reviews = 0
        self.lanes: list[tuple[str, ...]] = []
        #: The answer the round's first step took, for its second step to read.
        self.round: dict[str, Verdict] | None = None

    def adjudicate(
        self, bundle: Bundle, *, only: tuple[str, ...] = (), **_: object
    ) -> Adjudication:
        if only == DISQUALIFYING:
            self.screens += 1
            screened = [verdict(gate, self.screened, level=self.level) for gate in only]
            recorded = bundle.record(screened).verdicts
            return judged(bundle, dict(recorded), self.level)
        if set(only) == set(SUBMISSION_GATES):
            if self.round is None:
                self.round = ledger(self.level, **self.judgments.pop(0))
            verdicts = {gate: self.round[gate] for gate in only}
            recorded = bundle.record(list(verdicts.values())).verdicts
            return replace(judged(bundle, dict(recorded), self.level), verdicts=verdicts)
        reviewing = bool(only) and set(REVIEWED) <= set(only)
        if not reviewing or self.round is None:
            self.round = ledger(self.level, **self.judgments.pop(0))
        answer = self.round
        if not only or reviewing:
            self.round = None
        verdicts = {gate: found for gate, found in answer.items() if not only or gate in only}
        recorded = bundle.record(list(verdicts.values())).verdicts
        return replace(judged(bundle, dict(recorded), self.level), verdicts=verdicts)

    def repair(self, bundle: Bundle, **kwargs: Any) -> SimpleNamespace:
        self.repairs.append(kwargs)
        number = len(self.repairs)
        path = bundle.solution_path
        write_text(path, read_text(path) + f"\n# attempt {number}\n")
        manifest = bundle.manifest()
        manifest.provenance.setdefault("repairs", []).append(
            {
                "round": number,
                "addressing": [verdict.gate for verdict in kwargs["verdicts"]],
                "session": {"summary": f"Attempt {number} edited the solution. It says so."},
            }
        )
        bundle.save_manifest(manifest)
        return SimpleNamespace(changed=True)

    def audit(self, bundle: Bundle, **kwargs: Any) -> AuditResult:
        self.reviews += 1
        self.lanes.append(tuple(kwargs.get("lanes") or ()))
        return reviewed(bundle, *self.lanes[-1])


def reviewed(bundle: Bundle, *lanes: str) -> AuditResult:
    """What one review that asked ``lanes`` produced, one session each and nothing filed."""
    return AuditResult(
        task_key="coin-change",
        bundle=bundle,
        audit=Audit(
            task_key="coin-change",
            backend="falsifier",
            provider="scripted",
            model="reviewing-model",
            sessions=tuple({"lane": lane} for lane in lanes),
        ),
        written=tuple(f"audit/{lane}.md" for lane in lanes),
    )


Drive = Callable[..., TaskOutcome]


@pytest.fixture
def drive(coin_change: Task, settings: Settings, monkeypatch: pytest.MonkeyPatch) -> Drive:
    """Take the coin-change task round the loop under a script, with a given budget.

    The bundle carries a review that still describes it (`due` names no auditor), so only a
    round that asks for another one has it reviewed; a case may patch `due` itself.
    """
    monkeypatch.setattr(reviewing, "due", lambda *_: ())

    def drive(script: Scripted, *, budget: int = 5, unreachable: bool = False) -> TaskOutcome:
        monkeypatch.setattr(run, "adjudicate", script.adjudicate)
        monkeypatch.setattr(reviewing, "adjudicate", script.adjudicate)
        monkeypatch.setattr(run, "repair", script.repair)
        monkeypatch.setattr(reviewing, "audit", script.audit)
        outcome = _process(
            coin_change,
            backend=BACKENDS.get("falsifier"),
            provider=None,  # type: ignore[arg-type]
            reviewer=None,  # type: ignore[arg-type]
            settings=settings.model_copy(update={"max_repairs": budget}),
            level=script.level,
            rebuild=False,
            judge=True,
            skip_certified=False,
        )
        assert bool(outcome.error) == unreachable, outcome.error
        return outcome

    return drive


def test_a_repair_that_made_things_worse_is_kept_and_the_next_one_addresses_it(
    sound: Bundle, drive: Drive
) -> None:
    """Nothing is undone: the second attempt edits the file the first one left."""
    original = read_text(sound.solution_path)
    script = Scripted(sound, WEAK, BROKEN, {})

    outcome = drive(script)

    assert outcome.certification is not None and outcome.certification.certified
    assert outcome.repairs == 2
    solution = read_text(sound.solution_path)
    assert solution.startswith(original)
    assert "# attempt 1" in solution and "# attempt 2" in solution
    second = script.repairs[1]
    assert [answered.gate for answered in second["verdicts"]] == [
        "spec.verifies",
        "spec.strength.battery",
    ]


def test_every_round_of_the_run_is_kept_as_judged_for_the_repair_that_follows(
    sound: Bundle, drive: Drive
) -> None:
    """A round's files exist nowhere else once a repair has edited them."""
    script = Scripted(sound, WEAK, BROKEN, {})

    drive(script)

    first, second = script.repairs
    history = first["history"]
    assert second["history"] == history
    assert sorted(entry.name for entry in history.iterdir()) == ["00", "01", "02"]
    assert "# attempt 1" in read_text(history / "01" / sound.solution_path.name)
    assert "# attempt 1" not in read_text(history / "00" / sound.solution_path.name)


def test_a_round_s_record_says_what_produced_it_and_every_finding_that_did_not_pass(
    sound: Bundle, drive: Drive
) -> None:
    """The repair after the round before, with the gates it answered and its report.

    Each finding is numbered as a repair session's brief numbers it, its details beneath it.
    """
    found = verdict(
        "spec.strength.battery",
        Status.FAIL,
        "The battery found rival-1 accepted.",
        findings=["rival-1 returns no coins. It is accepted."],
    )
    script = Scripted(sound, {"spec_strength_battery": found}, BROKEN, {})

    drive(script)

    history = script.repairs[0]["history"]
    first, second = (read_text(history / name / RECORD) for name in ("00", "01"))
    assert "Drafting: this is the bundle the run began with." in first
    assert "* `spec.strength.battery` -- " in first
    assert "The battery found rival-1 accepted.\n  * (7.1) rival-1 returns no" in first
    assert (
        "* After round 00, repair 1 addressed `spec.strength.battery`: Attempt 1 edited the "
        "solution. It says so." in second
    )
    assert "`spec.verifies`" in second and "rival-1" not in second
    assert not list(history.rglob("round.json"))


def test_a_round_s_manifest_and_record_hold_only_what_that_round_judged(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A review's verdict from before the round, which it did not reach, is in neither."""
    monkeypatch.setattr(reviewing, "due", lambda *_: ("attack",))
    sound.record([verdict("audit.faithfulness", Status.FAIL, "An old finding.", level=AUDITED)])
    script = Scripted(sound, {"spec_verifies": Status.FAIL}, {}, level=AUDITED)

    drive(script, budget=1)

    kept = script.repairs[0]["history"] / "00"
    assert set(read_json(kept / "manifest.json")["verdicts"]) == {
        gate for gate in required_gates(AUDITED) if gate not in REVIEWED
    }
    assert "`spec.verifies`" in read_text(kept / RECORD)
    assert "An old finding." not in read_text(kept / RECORD)


def test_a_round_that_asked_an_auditor_again_names_it_in_its_record(
    sound: Bundle, drive: Drive, settings: Settings
) -> None:
    """No repair came before it, and what it found is listed as any round's is."""
    script = Scripted(sound, SHORT, {"audit_spec_completeness": Status.FAIL}, level=AUDITED)

    drive(script, budget=0)

    record = read_text(directory(sound, settings.cache_dir) / "01" / RECORD)
    assert (
        "No repair: this round asked the review again about the bundle round 00 judged "
        "(`attack`)" in record
    )
    assert "* (16) `audit.spec_completeness`" in record


def test_the_rounds_a_repair_sees_are_this_run_s_only(sound: Bundle, drive: Drive) -> None:
    """A round from an earlier run judged other code, so a new run starts with none."""
    drive(Scripted(sound, WEAK, {}))
    script = Scripted(sound, WEAK, {})

    drive(script)

    history = script.repairs[0]["history"]
    assert sorted(entry.name for entry in history.iterdir()) == ["00", "01"]


def test_a_repair_that_left_the_bundle_as_it_was_spends_one_and_the_next_repairs_again(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A session that reported BLOCKED is not the last word, and it costs a repair.

    Judging an unchanged bundle again would only repeat its verdicts, so the next round
    repairs it again straight away, until the budget is spent.
    """
    script = Scripted(sound, WEAK, WEAK, WEAK)
    calls: list[dict[str, Any]] = []

    def unchanged(bundle: Bundle, **kwargs: Any) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(changed=False)

    monkeypatch.setattr(script, "repair", unchanged)

    outcome = drive(script, budget=3)

    assert (outcome.repairs, len(calls)) == (3, 3)
    assert len(script.judgments) == 2
    assert outcome.certification is not None
    assert outcome.certification.failed == ["spec.strength.battery"]


def test_a_round_after_an_unchanged_repair_is_judged_once_it_changes_the_bundle(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = Scripted(sound, WEAK, {})
    answers = iter([False, True])

    def repairing(bundle: Bundle, **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(changed=next(answers))

    monkeypatch.setattr(script, "repair", repairing)

    outcome = drive(script)

    assert outcome.certification is not None and outcome.certification.certified
    assert outcome.repairs == 2
    assert script.judgments == []


def test_the_bundle_a_run_ends_with_is_the_last_one_judged(sound: Bundle, drive: Drive) -> None:
    """And a `manifest.json` that is about it, whatever it says."""
    script = Scripted(sound, WEAK, BROKEN)

    outcome = drive(script, budget=1)

    assert "# attempt 1" in read_text(sound.solution_path)
    recorded = sound.manifest().verdicts
    assert recorded["spec.verifies"].status is Status.FAIL
    assert outcome.certification is not None
    assert sorted(outcome.certification.failed) == ["spec.strength.battery", "spec.verifies"]
    assert outcome.repairs == 1


# ---- a review that showed too little ----------------------------------------------

AUDITED = Level.AUDITED
#: An auditor undecided only because the review had fewer attacks decided than asked.
SHORT = {
    "audit_spec_completeness": verdict(
        "audit.spec_completeness",
        Status.SKIP,
        "4 of the 5 attack(s) on record were decided and this run asks for 5",
        level=AUDITED,
        filed=5,
        required=5,
    )
}
#: A faithfulness judgment reached from a specification that has changed since.
STALE = verdict(
    "audit.faithfulness",
    Status.SKIP,
    "the faithfulness judgment was reached from the specification as it was before",
    level=AUDITED,
    stale=["spec"],
)


@pytest.mark.parametrize(
    ("first", "lane"),
    [
        pytest.param(SHORT, "attack", id="too few attacks decided"),
        pytest.param({"audit_faithfulness": STALE}, "faithfulness", id="a stale judgment"),
    ],
)
def test_a_review_that_showed_too_little_is_reviewed_again_not_repaired(
    sound: Bundle, drive: Drive, first: dict[str, Status | Verdict], lane: str
) -> None:
    """The specification failed no test: it was not tested enough to say.

    A repair would be told to fix what nothing showed wrong, so the auditor that showed too
    little is asked again instead.
    """
    script = Scripted(sound, first, {}, level=AUDITED)

    outcome = drive(script)

    assert outcome.certification is not None and outcome.certification.certified
    assert (script.lanes, script.repairs) == ([(lane,)], [])
    assert (outcome.reviewed_again, outcome.repairs) == (1, 0)


@pytest.mark.parametrize(
    "failing", ["spec.verifies", "spec.strength.battery", "impl.conformance"]
)
def test_a_bundle_a_program_rejects_is_repaired_before_it_is_reviewed(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch, failing: str
) -> None:
    """A review would be spent on files the repair is about to change.

    The repair answers only what this round found: a review's verdicts on record from
    before it are about the files the previous repair changed.
    """
    monkeypatch.setattr(reviewing, "due", lambda *_: ("attack",))
    sound.record([verdict("audit.faithfulness", Status.FAIL, level=AUDITED)])
    script = Scripted(sound, {failing.replace(".", "_"): Status.FAIL}, {}, level=AUDITED)

    outcome = drive(script, budget=1)

    assert script.lanes == [("attack",)]
    (only,) = script.repairs
    assert [answered.gate for answered in only["verdicts"]] == [failing]
    assert outcome.certification is not None and outcome.certification.certified


def test_a_gate_that_crashed_does_not_keep_the_bundle_from_its_review(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No repair answers the tool's defect, so held back for it the task would end there.

    Reviewed, the bundle is repaired for what the review found, and the gate measures the
    bundle that repair leaves.
    """
    monkeypatch.setattr(reviewing, "due", lambda *_: ("faithfulness",))
    crashed = verdict(
        "spec.strength.mutation", Status.ERROR, "KeyError: 'solution'", traceback="..."
    )
    first = {"spec_strength_mutation": crashed, "audit_faithfulness": Status.FAIL}
    script = Scripted(sound, first, {}, level=AUDITED)

    outcome = drive(script)

    assert script.lanes == [("faithfulness",), ("faithfulness",)]
    (only,) = script.repairs
    assert [answered.gate for answered in only["verdicts"]] == ["audit.faithfulness"]
    assert outcome.certification is not None and outcome.certification.certified


def test_a_pre_fix_implementation_the_checker_reached_no_verdict_on_is_repaired(
    sound: Bundle, drive: Drive
) -> None:
    """A timeout on one of the bundle's files is the file's to answer, as on the solution.

    Otherwise the task would end there with its budget unspent.
    """
    undecided = verdict(
        "spec.discriminates",
        Status.TIMEOUT,
        "the checker reached no verdict on pre-fix implementation(s): twin",
        undecided=["twin"],
    )
    script = Scripted(sound, {"spec_discriminates": undecided}, {})

    outcome = drive(script)

    (only,) = script.repairs
    assert [answered.gate for answered in only["verdicts"]] == ["spec.discriminates"]
    assert outcome.certification is not None and outcome.certification.certified


def test_a_round_that_asks_an_auditor_again_does_not_judge_the_unchanged_bundle_s_other_gates(
    sound: Bundle, drive: Drive
) -> None:
    """They judged these files in the round before, and would say the same.

    The review's own judging of the submission gates, before the attack validation auditor
    is asked, comes between the review and the gates that read it.
    """
    script = Scripted(sound, SHORT, {}, level=AUDITED)
    judged: list[tuple[str, ...]] = []
    scripted = script.adjudicate

    def counting(
        bundle: Bundle, *, only: tuple[str, ...] = (), **kwargs: object
    ) -> Adjudication:
        judged.append(only)
        return scripted(bundle, only=only, **kwargs)

    script.adjudicate = counting  # type: ignore[method-assign]

    drive(script, budget=1)

    decided = tuple(gate for gate in judged[1] if gate not in REVIEWED)
    assert judged[0] == DISQUALIFYING and decided == judged[1]
    assert judged[2:] == [REVIEWED, SUBMISSION_GATES, REVIEWED]


def test_a_review_that_files_a_defect_s_input_has_conformance_py_judged_on_it(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The input joins those on record, which every run of `conformance.py` compares.

    So the round judges `impl.conformance` again beside the gates that read the review, and a
    disagreement on the input reaches this round's repair.
    """
    monkeypatch.setattr(reviewing, "due", lambda *_: ("attack",))
    script = Scripted(sound, {}, level=AUDITED)
    judged: list[tuple[str, ...]] = []
    scripted = script.adjudicate

    def counting(
        bundle: Bundle, *, only: tuple[str, ...] = (), **kwargs: object
    ) -> Adjudication:
        judged.append(only)
        return scripted(bundle, only=only, **kwargs)

    scripted_review = script.audit

    def filing(bundle: Bundle, **kwargs: Any) -> AuditResult:
        result = scripted_review(bundle, **kwargs)
        replay.record(bundle, {"change.make_change": ["(40,)"]}, source=replay.REVIEW, spec="")
        return result

    monkeypatch.setattr(script, "adjudicate", counting)
    monkeypatch.setattr(script, "audit", filing)
    drive(script, budget=1)

    assert judged[-1] == ("impl.conformance", *REVIEWED)


@pytest.mark.parametrize(
    ("short", "found", "lane"),
    [
        pytest.param(SHORT, "audit.spec_completeness", "attack", id="too few attacks decided"),
        pytest.param(
            {"audit_faithfulness": STALE},
            "audit.faithfulness",
            "faithfulness",
            id="a stale judgment",
        ),
    ],
)
def test_an_auditor_short_beside_a_finding_is_asked_again_before_the_repair(
    sound: Bundle, drive: Drive, short: dict[str, Status | Verdict], found: str, lane: str
) -> None:
    """So what the auditor finds reaches the same repair as the finding beside it.

    Repaired first, the bundle would be one the auditor never read, and what it found would
    wait for another repair.
    """
    beside = {"audit_equivalence": Status.FAIL}
    second = {found.replace(".", "_"): Status.FAIL, **beside}
    script = Scripted(sound, {**short, **beside}, second, {}, level=AUDITED)

    outcome = drive(script)

    assert (script.lanes, outcome.reviewed_again) == ([(lane,)], 1)
    (only,) = script.repairs
    assert [answered.gate for answered in only["verdicts"]] == [found, "audit.equivalence"]
    assert outcome.certification is not None and outcome.certification.certified


def test_no_auditor_is_asked_again_after_a_repair_that_changed_nothing(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bundle is the one that auditor last read, and it is not judged again either."""
    first = {**SHORT, "audit_faithfulness": Status.FAIL}
    script = Scripted(sound, first, first, level=AUDITED)
    monkeypatch.setattr(
        script,
        "repair",
        lambda bundle, **kwargs: SimpleNamespace(changed=False),
    )

    outcome = drive(script, budget=2)

    assert (script.reviews, outcome.repairs) == (1, 2)
    assert script.judgments == []


def test_what_a_second_review_found_is_kept(sound: Bundle, drive: Drive) -> None:
    """The attacks a review filed stay on record for good."""
    script = Scripted(sound, SHORT, {"audit_spec_completeness": Status.FAIL}, level=AUDITED)

    outcome = drive(script, budget=0)

    assert outcome.certification is not None
    assert outcome.certification.failed == ["audit.spec_completeness"]


def test_a_task_whose_review_is_asked_again_still_gets_its_whole_repair_budget(
    sound: Bundle, drive: Drive
) -> None:
    """Asking an auditor again is not a repair, so it spends none of the budget."""
    found = {"audit_equivalence": Status.FAIL}
    script = Scripted(sound, SHORT, found, found, {}, level=AUDITED)

    outcome = drive(script, budget=2)

    assert (script.reviews, outcome.reviewed_again, outcome.repairs) == (1, 1, 2)
    assert outcome.certification is not None and outcome.certification.certified


def test_an_auditor_that_fell_short_the_same_way_twice_is_not_asked_a_third_time(
    sound: Bundle, drive: Drive
) -> None:
    """It was asked the same question of the same files, so it would answer the same way.

    The rest of the budget would go on that, and the bundle would read afterwards as one
    the whole budget could not decide.
    """
    script = Scripted(sound, SHORT, SHORT, SHORT, level=AUDITED)

    outcome = drive(script, budget=5)

    assert (script.reviews, outcome.reviewed_again, outcome.repairs) == (1, 1, 0)
    assert outcome.certification is not None
    assert outcome.certification.undecided == ["audit.spec_completeness"]


def test_an_auditor_that_showed_too_little_after_the_last_repair_is_still_asked_again(
    sound: Bundle, drive: Drive
) -> None:
    """Asking is not a repair, so a spent budget does not leave a judgment nobody finished.

    The last repair answered the finding; the review of its bundle then showed too little,
    and the auditor is asked about that bundle once more before the task ends.
    """
    script = Scripted(
        sound,
        {"audit_equivalence": Status.FAIL},
        {"audit_faithfulness": STALE},
        {},
        level=AUDITED,
    )

    outcome = drive(script, budget=1)

    assert (script.lanes[-1:], outcome.reviewed_again, outcome.repairs) == (
        [("faithfulness",)],
        1,
        1,
    )
    assert outcome.certification is not None and outcome.certification.certified


def test_a_case_left_open_after_the_validation_auditor_reported_lets_it_be_asked_again(
    sound: Bundle, drive: Drive
) -> None:
    """An attack listed after the attack validation auditor reported was not asked about.

    The round that asks it again judges the two submission gates first, and the auditor is
    asked only while they list an attack or a control without a ruling.
    """

    def unruled(*cases: str) -> dict[str, Verdict]:
        return {
            "audit_spec_completeness": verdict(
                "audit.spec_completeness",
                Status.SKIP,
                "an attack that cannot be determined by execution has no ruling",
                level=AUDITED,
                unruled=dict.fromkeys(cases, "cannot be determined by execution"),
            )
        }

    script = Scripted(
        sound, unruled("attack-1"), unruled("attack-1", "attack-2"), {}, level=AUDITED
    )

    outcome = drive(script, budget=5)

    assert script.lanes == [("validation",)]
    assert (outcome.reviewed_again, outcome.repairs) == (2, 0)
    assert outcome.certification is not None and outcome.certification.certified


def test_a_repair_that_changed_the_bundle_lets_a_short_auditor_be_asked_again(
    sound: Bundle, drive: Drive
) -> None:
    """It would be asked about other files, so it is not the question it already answered."""
    script = Scripted(
        sound,
        SHORT,
        {**SHORT, "audit_equivalence": Status.FAIL},
        SHORT,
        {},
        level=AUDITED,
    )

    outcome = drive(script, budget=5)

    assert (script.reviews, outcome.reviewed_again, outcome.repairs) == (2, 2, 1)
    assert outcome.certification is not None and outcome.certification.certified


# ---- a task whose own solution fails its own tests --------------------------------------


# ---- a stage that could not reach a model at all ---------------------------------------


def test_a_repair_that_cannot_start_a_session_ends_the_task_on_the_environment(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An expired credential is not a model with nothing to say, round after round.

    Every further round would fail the same way, and the bundle would end up reading as
    one five repairs could not help.
    """
    script = Scripted(sound, WEAK, WEAK, WEAK, level=AUDITED)

    def unreachable(bundle: Bundle, **kwargs: Any) -> None:
        script.repairs.append(kwargs)
        raise ProviderError("Could not load AWS credentials")

    monkeypatch.setattr(script, "repair", unreachable)

    outcome = drive(script, unreachable=True)

    assert outcome.outcome == "error"
    assert outcome.error == "Could not load AWS credentials"
    assert (len(script.repairs), outcome.repairs) == (1, 0)


def test_a_review_that_cannot_reach_a_model_ends_the_task_on_the_environment(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Judging on would spend the budget answering gates that say nobody reviewed it."""
    monkeypatch.setattr(reviewing, "due", lambda *_: ("attack",))
    script = Scripted(sound, {"audit_faithfulness": Status.FAIL}, level=AUDITED)

    def unreachable(bundle: Bundle, **kwargs: Any) -> None:
        script.reviews += 1
        raise ProviderError("the request failed after 3 attempt(s)")

    monkeypatch.setattr(script, "audit", unreachable)

    outcome = drive(script, unreachable=True)

    assert outcome.error == "the request failed after 3 attempt(s)"
    assert (script.reviews, len(script.repairs), outcome.judged) == (1, 0, False)


def test_a_task_whose_own_solution_fails_its_tests_is_dropped_before_it_is_drafted(
    sound: Bundle, drive: Drive, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing drafted for it can address that, so nothing is drafted, reviewed or repaired."""
    sound.solution_path.unlink()

    def drafted(*_: object, **__: object) -> None:
        raise AssertionError("a dropped task was drafted")

    monkeypatch.setattr(run, "build", drafted)
    script = Scripted(sound, level=AUDITED, screened=Status.FAIL)

    outcome = drive(script)

    assert outcome.outcome == str(Outcome.DROPPED)
    assert outcome.certification is not None
    assert outcome.certification.failed == ["oracle.reference_resolves"]
    assert (script.screens, script.reviews, len(script.repairs)) == (1, 0, 0)


def test_a_task_found_failing_its_own_tests_later_ends_the_loop(
    sound: Bundle, drive: Drive
) -> None:
    """The suite's finding beside it is left unrepaired: the task is not judged at all."""
    failing = {"oracle_reference_resolves": Status.FAIL, **WEAK}
    script = Scripted(sound, failing, level=AUDITED)

    outcome = drive(script)

    assert outcome.outcome == str(Outcome.DROPPED)
    assert (script.screens, len(script.repairs)) == (1, 0)


def test_a_static_run_asks_nothing_of_the_task_s_oracle_before_drafting(
    sound: Bundle, drive: Drive
) -> None:
    script = Scripted(sound, {}, screened=Status.FAIL)

    outcome = drive(script)

    assert script.screens == 0
    assert outcome.certification is not None and outcome.certification.certified


@pytest.mark.parametrize(
    ("due", "again", "unruled", "calls"),
    [
        (("attack",), (), True, [("attack",), SUBMISSION_GATES, ("validation",)]),
        (("attack",), (), False, [("attack",), SUBMISSION_GATES]),
        ((), ("validation",), True, [SUBMISSION_GATES, ("validation",)]),
        (
            ("attack", "fuzz"),
            ("faithfulness",),
            False,
            [("attack", "fuzz", "faithfulness"), SUBMISSION_GATES],
        ),
        ((), LANES, True, [LANES[:-1], SUBMISSION_GATES, ("validation",)]),
        ((), (), True, []),
    ],
    ids=[
        "some execution cannot determine",
        "none execution cannot determine",
        "asked again",
        "another auditor asked again",
        "every auditor",
        "nothing due",
    ],
)
def test_the_attack_validation_auditor_is_asked_once_the_gates_ran_what_is_on_record(
    due: tuple[str, ...],
    again: tuple[str, ...],
    unruled: bool,
    calls: list[tuple[str, ...]],
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After the other auditors, and only where the submission gates list some with no ruling.

    An auditor asked again joins those due in one review, after the attack auditor, so it is
    shown what the attack auditor files in it. So when every auditor is asked, as
    ``benchproofer audit --again`` asks them, the attack validation auditor still rules on what
    the attack auditor filed in the same review. What the review returns holds both reviews'
    sessions. A review that asked nothing judges no gate.
    """
    made: list[tuple[str, ...]] = []

    def audited(bundle: Bundle, *, lanes: tuple[str, ...], **_: object) -> AuditResult:
        made.append(tuple(lanes))
        return reviewed(bundle, *lanes)

    def judging(bundle: Bundle, *, only: tuple[str, ...] = (), **_: object) -> Adjudication:
        made.append(only)
        details = (
            {"unruled": {"attack-1": "cannot be determined by execution"}} if unruled else {}
        )
        found = verdict("audit.spec_completeness", Status.SKIP, level=AUDITED, **details)
        return judged(bundle, dict(bundle.record([found]).verdicts), AUDITED)

    monkeypatch.setattr(reviewing, "due", lambda *_: due)
    monkeypatch.setattr(reviewing, "audit", audited)
    monkeypatch.setattr(reviewing, "adjudicate", judging)

    result = reviewing.review(
        sound,
        backend=BACKENDS.get("falsifier"),
        provider=SimpleNamespace(),  # type: ignore[arg-type]
        settings=settings,
        level=AUDITED,
        again=again,  # type: ignore[arg-type]
    )

    assert made == calls
    assert (result is not None) is bool(calls)
    lanes = [lane for asked in calls if asked != SUBMISSION_GATES for lane in asked]
    if result is not None:
        assert [session["lane"] for session in result.audit.sessions] == lanes
