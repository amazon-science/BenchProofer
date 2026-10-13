# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Repair: answering a finding without that being a way out of it.

The repair session is a double that edits its workspace, and the checker is local
(`tests/doubles.py`), so these cases pin the bookkeeping, which is where a repair would
quietly make findings disappear:

* **Only a finding gets repaired.** A gate that could not run, or a review that showed
  too little, is not evidence of a defect in the artifacts.
* **The review is the review's.** The repair leaves the submissions and judgments on
  record as they were; a judgment whose files it changed no longer describes the bundle,
  and an attack aimed at the specification it replaced is the next review's to write again.
* **A session repair edits the bundle as it stands.** What the session left is carried into the
  repaired specification and written as it left it, and nothing is drafted after it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

import benchproofer.core.bundle as bundle_module
import benchproofer.formalize.session as session_module
import benchproofer.pipeline.repair as repair_module
from benchproofer.audit.agents import _repair_answers
from benchproofer.audit.session import ROLE_READS
from benchproofer.backends.base import Backend, CheckResult
from benchproofer.config import Settings
from benchproofer.core import differential, replay, rounds
from benchproofer.core.axioms import directive_line, with_declarations
from benchproofer.core.bundle import (
    Bundle,
    Judgment,
    Review,
    Submission,
    SubmissionKind,
    Twin,
)
from benchproofer.core.markers import parse, replace_region, wrap
from benchproofer.core.prompts import SHARED
from benchproofer.core.readings import SPEC, SPEC_UNCOMMENTED, readings
from benchproofer.core.runnable import quotes_lines
from benchproofer.core.scripts import script as write_script
from benchproofer.core.sites import RECORD
from benchproofer.core.task import Task
from benchproofer.core.verdict import Level, Status, Verdict
from benchproofer.errors import BenchproofError
from benchproofer.gates.battery import BatteryGate
from benchproofer.llm.agentic import EDIT, AgentSession, SessionSpec, StepOutcome
from benchproofer.pipeline.adjudicate import GATE_ORDER, required_gates
from benchproofer.pipeline.audit import due
from benchproofer.pipeline.repair import RepairResult, as_submitted, repair
from benchproofer.pipeline.route import Route, routed
from benchproofer.registries import BACKENDS
from benchproofer.smoke import fixtures
from benchproofer.util.digest import digest_file
from benchproofer.util.fsio import read_text, write_text
from doubles import Accepting

COMMENT = "#"
BATTERY = BatteryGate.id
#: The specification a repair is asked for: one obligation where the shipped file has
#: three, so a test can tell which specification an artifact carries.
REPAIRED = """\
# benchproofer:begin helpers
from hypothesis import given, strategies as st

AMOUNTS = st.integers(min_value=0, max_value=10000)
# benchproofer:end helpers


# benchproofer:begin impl
def impl(cents):
    counts = []
    for coin in (25, 10, 5, 1):
        counts.append(cents // coin)
        cents = cents - counts[-1] * coin
    return tuple(counts)
# benchproofer:end impl


# benchproofer:begin spec
@given(AMOUNTS)
def property_change_sums_to_the_amount(cents):
    quarters, dimes, nickels, pennies = impl(cents)
    assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents
# benchproofer:end spec
"""
#: The submission on record: it hands out pennies only, so 40 cents is not eight nickels.
ATTACK_IMPL = "def impl(cents):\n    return (0, 0, 0, cents)\n"
OTHER_IMPL = "def impl(cents):\n    return (cents, 0, 0, 0)\n"
#: A `conformance.py` that marks the implementation it carries, which is what makes
#: the same comparison runnable against a reviewer's submission.
HARNESS = (
    "from change import make_change\n\n\n"
    "def shadow_impl(cents):\n"
    "    # benchproofer:begin impl\n"
    "    counts = []\n"
    "    for coin in (25, 10, 5, 1):\n"
    "        counts.append(cents // coin)\n"
    "        cents = cents - counts[-1] * coin\n"
    "    return tuple(counts)\n"
    "    # benchproofer:end impl\n\n\n"
    "for cents in range(10000):\n"
    "    assert make_change(cents) == shadow_impl(cents)\n"
    'print("benchproofer:compared change.make_change 10000 every amount")\n'
)


def finding(
    gate: str,
    summary: str = "the specification accepts wrong implementation(s): uniqueness-1",
    *,
    status: Status = Status.FAIL,
    **details: object,
) -> Verdict:
    """One unfavorable verdict, in the shape a gate records it."""
    return Verdict(gate=gate, status=status, summary=summary, details=dict(details))


def filed(
    bundle: Bundle,
    *submitted: tuple[str, str],
    kind: SubmissionKind = "weakness",
    judged: bool = True,
) -> Review:
    """Record a review of the bundle as it stands, and return what was written.

    Each submission is the shipped file with one implementation spliced in, which is what
    the review stage produces.
    """
    solution = bundle.solution()
    cases = submitted or (("attack-1", ATTACK_IMPL),)
    digests = bundle.artifact_digests()
    review = Review(
        reviewer="scripted:reviewing-model",
        author="scripted:drafting-model",
        independent=True,
        submissions=tuple(
            Submission(
                id=name,
                file=f"{name}.py",
                claim=f"{name} returns the wrong coins",
                kind=kind,
            )
            for name, _ in cases
        ),
        judgments=(
            (
                Judgment(
                    role="faithfulness",
                    verdict="sound",
                    summary="every obligation is the task's",
                    reads={"solution.py": digests["solution.py"]},
                ),
                Judgment(
                    role="equivalence",
                    verdict="sound",
                    summary="the same computation",
                    reads={"solution.py": digests["solution.py"]},
                ),
            )
            if judged
            else ()
        ),
    )
    bundle.save_audit(
        review,
        {f"{name}.py": replace_region(solution, COMMENT, "impl", impl) for name, impl in cases},
    )
    return review


def repaired(
    bundle: Bundle,
    settings: Settings,
    *verdicts: Verdict,
    backend: Backend | None = None,
    session: AgentSession | None = None,
) -> RepairResult:
    """Repair one bundle against a local checker.

    The repair session is ``session``, by default one that writes `REPAIRED` and reports
    every finding answered.
    """
    return repair(
        bundle,
        backend=backend or Accepting(),
        settings=settings,
        verdicts=list(verdicts)
        or [finding("spec.strength.battery", too_weak=["uniqueness-1"])],
        session=session or Editing(REPORTED),
    )


def impl_of(source: str) -> str:
    """The implementation region of a solution file."""
    return parse(source, COMMENT)["impl"].text.strip()


# ---- what a repair writes --------------------------------------------------


MALFORMED = "case(s) the checker could not read, so their rejection is not evidence: "


class Witnessing(Accepting):
    """A checker under which a refused case needs a refutation witness to attribute it."""

    name = "witnessing"
    witness_required = True
    witness_placement = "* State it as a claim about `spec` at one input."


#: A pre-fix implementation's refutation witness as a drafter writes it, and one the session
#: wrote instead.
TWIN_WITNESS = "example : spec 40 (impl 40) = False := by decide"
SESSION_WITNESS = "example : spec 30 (impl 30) = False := by decide"


def unattributed_twin(why: str = "the case ships no witness") -> Verdict:
    """The discriminates verdict on a pre-fix implementation whose refusal is unattributed."""
    return finding(
        "spec.discriminates",
        f"twin rejection(s) not attributable to the specification: twin: {why}",
        status=Status.ERROR,
        unattributed=["twin"],
        reasons={"twin": why},
    )


@pytest.mark.parametrize(
    "verdict",
    [
        pytest.param(
            finding(BATTERY, MALFORMED + "uniqueness-2", malformed=["uniqueness-2"]),
            id="a case of the suite the checker could not read",
        ),
        pytest.param(
            unattributed_twin(), id="a pre-fix implementation whose refusal nothing attributes"
        ),
    ],
)
def test_a_finding_about_a_case_goes_to_the_repair_session(
    sound: Bundle, settings: Settings, verdict: Verdict
) -> None:
    """Which has the checker at hand, as `verified-swebench`'s author fixes its own cases.

    It is told the finding, and that a finding about a case is resolved by fixing the case,
    never the specification; nothing drafts the case again by a request.
    """
    session = Editing(REPORTED, solution=None)

    assert routed({verdict.gate: verdict}, Level.STATIC)[Route.REPAIR] == [verdict]
    repaired(sound, settings, verdict, session=session)

    (request,) = session.asked
    assert verdict.summary in request.prompt
    assert "fixing the case, never the specification" in request.prompt


@pytest.mark.parametrize("required", [True, False], ids=["witness required", "none required"])
def test_a_session_is_told_a_rejected_case_it_rewrites_needs_its_witness_again(
    sound: Bundle, settings: Settings, required: bool
) -> None:
    """Under a checker whose rejection attributes nothing without one, and only there."""
    session = Editing(REPORTED)

    repaired(
        sound,
        settings,
        backend=Witnessing() if required else Accepting(),
        session=session,
    )

    assert ("needs its witness again" in session.asked[0].prompt) is required


def test_a_repair_leaves_the_review_on_record_as_it_was(
    sound: Bundle, settings: Settings
) -> None:
    """The digests the judgments read say they no longer describe the bundle.

    The submissions keep the specification they were filed against: the next review's
    attack auditor, due again, writes fresh ones in their place.
    """
    before = filed(sound)
    attack = sound.submission_source(before.submissions[0])

    repaired(sound, settings)

    review = sound.audit()
    assert review is not None
    assert review.judgments
    assert any(judgment.stale(readings(sound, Accepting())) for judgment in review.judgments)
    assert due(sound, Accepting())
    assert review.reviewer == "scripted:reviewing-model"
    assert review.submissions == before.submissions
    assert sound.submission_source(review.submissions[0]) == attack


def test_a_repair_to_a_comment_in_the_specification_expires_only_disclosure(
    sound: Bundle,
) -> None:
    """What a comment says is not what the specification states.

    So faithfulness and equivalence read the specification with its comments masked, and
    stay current; disclosure reads the comments too, since one can give the fix away.
    """
    backend = Accepting()
    before = readings(sound, backend)
    write_text(
        sound.solution_path,
        sound.solution().replace(
            "def property_change_uses_no_negative_coin(cents):\n",
            "def property_change_uses_no_negative_coin(cents):  # every coin it hands out\n"
            "    # A count below zero would be change handed back.\n",
        ),
    )
    commented = readings(sound, backend)
    write_text(sound.solution_path, sound.solution().replace("count >= 0", "count > 0"))
    restated = readings(sound, backend)

    assert commented[SPEC] != before[SPEC]
    assert commented[SPEC_UNCOMMENTED] == before[SPEC_UNCOMMENTED]
    assert restated[SPEC_UNCOMMENTED] != before[SPEC_UNCOMMENTED]
    for role, names in ROLE_READS.items():
        judgment = Judgment(
            role=role,
            verdict="sound",
            summary="",
            reads={name: before[name] for name in names if name in before},
        )
        assert bool(judgment.stale(commented)) is (role == "disclosure")


# ---- `manifest.json` ------------------------------------------------------------


def test_the_repair_record_says_which_gates_each_repair_addressed(
    sound: Bundle, settings: Settings
) -> None:
    """Gate ids, not the findings: the artifacts are what say whether it worked.

    A second repair appends its round, since that record is the only history a bundle keeps.
    """
    filed(sound)

    repaired(
        sound,
        settings,
        finding("spec.strength.battery"),
        finding("spec.discriminates", "the specification accepts the pre-fix implementation"),
    )
    repaired(sound, settings, finding("spec.no_leakage", "it leaks"))

    first, second = sound.manifest().provenance["repairs"]
    assert {name: first[name] for name in first if name != "session"} == {
        "round": 1,
        "addressing": ["spec.strength.battery", "spec.discriminates"],
    }
    assert (second["round"], second["addressing"]) == (2, ["spec.no_leakage"])


def test_a_repair_leaves_the_earlier_verdicts_in_manifest_json(
    sound: Bundle, settings: Settings
) -> None:
    """They describe the artifacts that were there, and artifact.integrity says so."""
    sound.record([finding("spec.strength.battery")])

    repaired(sound, settings)

    manifest = sound.manifest()
    assert set(manifest.verdicts) == {"spec.strength.battery"}
    assert manifest.verdicts["spec.strength.battery"].status is Status.FAIL


def test_a_repair_lists_the_functions_drafting_recorded_and_keeps_the_record(
    sound: Bundle, settings: Settings
) -> None:
    """It reads what the golden patch edits from manifest.json, as each stage after drafting."""
    manifest = sound.manifest()
    kept = {"golden_patch": {"change.py": [["def recorded_site"]]}, "test_patch": {}}
    manifest.provenance = {**manifest.provenance, RECORD: kept}
    sound.save_manifest(manifest)
    sound.conformance_path.unlink()
    session = Editing(REPORTED)

    repaired(sound, settings, finding("spec.strength.battery"), session=session)

    assert "`recorded_site`" in session.asked[0].prompt
    assert sound.manifest().provenance[RECORD] == kept


def test_a_repair_records_the_regions_and_digests_of_the_file_it_wrote(
    sound: Bundle, settings: Settings
) -> None:
    """A stale digest here is what would let a repaired bundle certify on old evidence."""
    backend = Accepting()

    repaired(sound, settings, backend=backend)

    manifest = sound.manifest()
    assert manifest.regions == backend.region_digests(REPAIRED)
    assert manifest.artifacts == sound.artifact_digests()


def judged_from(bundle: Bundle, gate: str, evidence: str, *sources: str) -> None:
    """Record a verdict that read ``sources`` and wrote ``evidence``, as a gate does."""
    written = bundle.write_evidence(evidence, f"what {gate} printed\n")
    inputs = {
        f"{bundle.root.name}/{source}": digest_file(bundle.root / source) for source in sources
    }
    bundle.record(
        [
            Verdict(
                gate=gate,
                status=Status.PASS,
                summary=f"{gate} passed",
                inputs=inputs,
                evidence=[written],
            )
        ]
    )


def judged_round(bundle: Bundle) -> None:
    """The evidence a judged round leaves, an orphan and the replayed inputs included."""
    judged_from(bundle, "spec.verifies", "verifies.log", "solution.py")
    judged_from(bundle, "impl.conformance", "conformance.log", "solution.py", "conformance.py")
    judged_from(bundle, BATTERY, "battery.txt", "solution.py", "rivals/index.toml")
    # A gate that passed this time and failed before writes nothing on a pass.
    bundle.write_evidence("leakage.txt", "an earlier round's failure\n")
    bundle.write_evidence("conformance-witnesses.json", "[]\n")


def test_a_repair_clears_the_evidence_of_a_round_it_superseded(
    sound: Bundle, settings: Settings
) -> None:
    """The review before the next judgment would read it as describing this bundle.

    A `conformance.py` the repair replaced keeps its log, and the functions that log names are
    the ones the next attack is told to name inputs for. The inputs on record for
    `conformance.py` are kept across rounds by design.
    """
    judged_round(sound)

    repaired(sound, settings)

    left = sorted(path.name for path in sound.evidence_dir.iterdir())
    assert left == ["conformance-witnesses.json"]
    entry = sound.manifest().provenance["repairs"][-1]
    assert "evidence/conformance.log" in entry["cleared_evidence"]
    assert sound.manifest().artifacts == sound.artifact_digests()


def test_a_repair_keeps_the_evidence_of_a_verdict_whose_inputs_it_left_alone(
    sound: Bundle, settings: Settings
) -> None:
    """A repair of one case leaves the solution and `conformance.py` as they were judged."""
    judged_round(sound)
    rival = sound.battery()[1]
    edited = replace_region(sound.rival_source(rival), COMMENT, "impl", EDITED_RIVAL)
    session = Editing(REPORTED, solution=None, files={f"rivals/{rival.file}": edited})

    repaired(
        sound,
        settings,
        finding(BATTERY, MALFORMED + rival.id, malformed=[rival.id]),
        session=session,
    )

    left = sorted(path.name for path in sound.evidence_dir.iterdir())
    assert left == ["conformance-witnesses.json", "conformance.log", "verifies.log"]


def test_a_repair_that_produced_no_file_leaves_the_bundle_as_it_was(
    sound: Bundle, settings: Settings
) -> None:
    """Nothing changed, so nothing expires: the review on record still describes it."""
    was = sound.solution()
    filed(sound)

    result = repaired(sound, settings, session=Editing(REPORTED, solution=None))

    assert not result.changed
    assert result.written == ()
    assert sound.solution() == was
    review = sound.audit()
    assert review is not None
    assert [judgment.role for judgment in review.judgments] == ["faithfulness", "equivalence"]
    assert not any(judgment.stale(sound.artifact_digests()) for judgment in review.judgments)
    assert sound.manifest().provenance["repairs"][0]["changed"] is False


# ---- a repair by an agent session ---------------------------------------


REPORTED: dict[str, object] = {
    "status": "REPAIRED",
    "summary": "The contract now conserves the amount. The implementation was already right.",
    "findings": [
        {
            "finding": "7",
            "outcome": "resolved",
            "witness": "40 cents, where the shipped contract admitted forty pennies",
        }
    ],
}


class Editing(AgentSession):
    """A repair session that edits files in its workspace, then reports.

    What it saw is kept, since what a repair is shown is the point of these cases: the
    request, and the workspace laid out when it ran.
    """

    name = "editing"

    def __init__(
        self,
        payload: dict[str, object] | None,
        *,
        solution: str | None = REPAIRED,
        harness: str | None = None,
        files: dict[str, str | None] | None = None,
    ) -> None:
        super().__init__()
        self.payload = payload
        self.solution = solution
        self.harness = harness
        #: Other files it writes, by bundle-relative name; None removes one.
        self.files = files or {}
        self.asked: list[SessionSpec] = []
        self.seen: list[str] = []

    def run(self, request: SessionSpec) -> StepOutcome:
        self.asked.append(request)
        self.seen = sorted(
            path.relative_to(request.cwd).as_posix() for path in request.cwd.rglob("*")
        )
        shipped = next(request.cwd.glob("bundles/**/solution.py")).parent
        if self.solution is not None:
            write_text(shipped / "solution.py", self.solution)
        if self.harness is not None:
            write_text(shipped / "conformance.py", self.harness)
        for name, text in self.files.items():
            if text is None:
                (shipped / name).unlink()
            else:
                write_text(shipped / name, text)
        return StepOutcome(text="done", payload=self.payload, turns=3, tool_uses=5)


def by_session(
    bundle: Bundle,
    settings: Settings,
    session: Editing,
    monkeypatch: pytest.MonkeyPatch,
    *,
    history: Path | None = None,
    verdicts: Sequence[Verdict] | None = None,
    backend: Backend | None = None,
) -> RepairResult:
    """Repair one bundle through ``session``."""
    monkeypatch.setattr(repair_module, "require_session", lambda *_: session)
    return repair(
        bundle,
        backend=backend or Accepting(),
        settings=settings,
        verdicts=list(
            verdicts or [finding("spec.strength.battery", too_weak=["uniqueness-1"])]
        ),
        history=history,
    )


def test_a_session_repair_carries_the_bundle_forward_rather_than_drafting_it_again(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pre-fix implementation and the rivals keep their code under the repaired spec."""
    twins, battery = (
        dict(sound.twins()),
        {rival.id: sound.rival_source(rival) for rival in sound.battery()},
    )
    session = Editing(REPORTED)

    result = by_session(sound, settings, session, monkeypatch)

    assert result.changed and result.status == "REPAIRED"
    assert sound.solution() == REPAIRED
    comment = Accepting().comment
    for name, source in sound.twins():
        assert parse(source, comment)["spec"].text == parse(REPAIRED, comment)["spec"].text
        assert parse(source, comment)["impl"].text == parse(twins[name], comment)["impl"].text
    assert sorted(rival.id for rival in sound.battery()) == sorted(battery)
    for rival in sound.battery():
        carried = parse(sound.rival_source(rival), comment)
        assert carried["spec"].text == parse(REPAIRED, comment)["spec"].text
        assert carried["impl"].text == parse(battery[rival.id], comment)["impl"].text
    entry = sound.manifest().provenance["repairs"][-1]
    assert entry["addressing"] == ["spec.strength.battery"]
    assert entry["session"]["status"] == "REPAIRED"
    assert entry["session"]["summary"].startswith("The contract now conserves")


def updated(bundle: Bundle, case: str, *, impl: str = "", **fields: str) -> None:
    """Rewrite one rival: ``fields`` of its record, and ``impl`` where one is given."""
    bundle.save_battery(
        [
            (
                rival.model_copy(update=fields) if rival.id == case else rival,
                replace_region(bundle.rival_source(rival), COMMENT, "impl", impl)
                if rival.id == case and impl
                else bundle.rival_source(rival),
            )
            for rival in bundle.battery()
        ]
    )


def removing(bundle: Bundle, *cases: str) -> dict[str, str | None]:
    """The files a session writes to take ``cases`` out of the property-based test suite."""
    index = "".join(
        f'[[rival]]\nid = "{rival.id}"\nkind = "{rival.kind}"\nexpect = "{rival.expect}"\n'
        f'file = "{rival.file}"\nrationale = "kept"\n\n'
        for rival in bundle.battery()
        if rival.id not in cases
    )
    removed: dict[str, str | None] = {
        f"rivals/{rival.file}": None for rival in bundle.battery() if rival.id in cases
    }
    return {**removed, "rivals/index.toml": index}


def test_a_case_or_a_pre_fix_implementation_the_session_removed_stays_removed(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Their gates judge what is left: nothing the session did is undone.

    `spec.discriminates` fails a bundle with no pre-fix implementation, and
    `spec.strength.battery` one missing a case it judged and found no defect in.
    """
    first, second = sound.battery()[:2]
    files = {
        **removing(sound, first.id),
        **{f"twins/{name}.py": None for name, _ in sound.twins()},
    }

    by_session(sound, settings, Editing(REPORTED, files=files), monkeypatch)

    left = [rival.id for rival in sound.battery()]
    assert first.id not in left
    assert second.id in left
    assert sound.twins() == []


def test_an_index_the_session_left_unreadable_is_written_as_it_left_it(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """For the suite's gate to report."""
    broken = "[[rival]]\nid = 1\n"

    by_session(
        sound, settings, Editing(REPORTED, files={"rivals/index.toml": broken}), monkeypatch
    )

    assert read_text(sound.rivals_dir / "index.toml") == broken
    with pytest.raises(BenchproofError):
        sound.battery()


@pytest.mark.parametrize("edited", [False, True], ids=["left as it was", "edited"])
def test_a_refinement_map_the_session_left_is_kept(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch, edited: bool
) -> None:
    """Under a changed solution too: the equivalence auditor judges it against that solution."""
    mapped = "## Symbols\n\n## Operations\n\n* identical -- one loop over the coins\n"
    shipped = sound.correspondence_path.read_text()
    files = {"correspondence.md": mapped} if edited else {}

    by_session(sound, settings, Editing(REPORTED, files=files), monkeypatch)

    assert sound.solution() == REPAIRED
    assert sound.correspondence_path.read_text() == (mapped if edited else shipped)


def test_a_conformance_py_holding_the_old_python_copy_is_kept_as_the_session_left_it(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The copy of the implementation is the session's to keep in step, and it is told so.

    The conformance gate holds `conformance.py` to the implementation the bundle ships, so
    one the session left holding the old copy fails there rather than being rewritten.
    """
    backend = Accepting()
    harness = differential.substituted(
        "from change import make_change\n\n"
        "# benchproofer:begin impl\npass\n# benchproofer:end impl\n\n"
        "for cents in range(100):\n    assert make_change(cents) == impl(cents)\n",
        differential.executables(sound.solution(), backend),
    )
    assert harness is not None
    write_text(sound.conformance_path, harness)
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    assert sound.conformance_path.read_text() == harness
    assert differential.uncopied(harness, differential.executables(REPAIRED, backend))
    prompt = " ".join(session.asked[0].prompt.split())
    assert "Benchproofer does not update either" in prompt
    assert "change the copy or the quotation as well" in prompt


def test_a_session_repair_can_run_and_edit_and_never_search_the_web(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It is told the failing gates and may run and edit, but not search the web."""
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    request = session.asked[0]
    assert request.tools == EDIT
    task = sound.task()
    assert request.writable == (
        request.cwd / "bundles" / task.benchmark / task.task_id / Accepting().name,
    )
    assert "spec.strength.battery" in request.prompt
    assert "spec.verifies" in request.prompt
    assert "Do not read the source of Benchproofer, which judges this bundle" in request.prompt


def test_a_session_is_shown_every_row_and_finding_beneath_a_verdicts_summary(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A summary names the first few, and a repair shown only those answers one a round.

    The auditor's own findings come first, numbered after the gate as the auditor numbered them,
    and the summary above them is their heading rather than a finding of its own.
    """
    rows = [f"behavior {index} | tested by: test_forty | covered by: -" for index in "12345"]
    faithfulness = finding(
        "audit.faithfulness",
        "6 behavior(s) ... are stated by no obligation",
        uncovered=rows,
        findings=["the nickel count is never stated"],
        coverage=["not listed beneath the summary"],
    )
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[faithfulness])

    number = GATE_ORDER.index("audit.faithfulness") + 1
    prompt = session.asked[0].prompt
    assert "* `audit.faithfulness` -- " in prompt
    assert f"({number}) `audit.faithfulness`" not in prompt
    assert f"  * ({number}.1) the nickel count is never stated" in prompt
    assert all(
        f"  * ({number}.{index}) a tested behaviour no obligation states: {row}" in prompt
        for index, row in enumerate(rows, 2)
    )
    assert "not listed beneath the summary" not in prompt


def test_the_brief_round_md_and_the_auditors_number_a_finding_alike(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finding has one number, whichever list holds it and in whatever order it came.

    `round.md` lists every gate that did not pass and the brief only those a repair
    addresses, so a number is the gate's place in the order the gates run; the report's
    entry for a number is the text the auditor reading that finding is shown.
    """
    weak = finding("audit.spec_completeness", "the specification accepts attack-1")
    gaps = finding(
        "audit.faithfulness",
        "2 finding(s)",
        findings=["the nickel count is never stated", "the dime count is never stated"],
    )
    held = finding("spec.verifies", "the checker did not finish", status=Status.TIMEOUT)
    faithfulness, completeness = (
        str(GATE_ORDER.index(gate) + 1) for gate in (gaps.gate, weak.gate)
    )
    answered = [
        {
            "finding": f"{faithfulness}.2",
            "outcome": "resolved",
            "witness": "a dime in 10 cents",
        },
        {"finding": completeness, "outcome": "resolved", "witness": "40 cents"},
    ]
    session = Editing({**REPORTED, "findings": answered})
    record = repair_module.chronicle(
        sound, "00", {verdict.gate: verdict for verdict in (held, weak, gaps)}, [], ()
    )

    by_session(sound, settings, session, monkeypatch, verdicts=[weak, gaps])

    prompt = session.asked[0].prompt
    for line in (
        f"({completeness}) `audit.spec_completeness`",
        f"  * ({faithfulness}.1) the nickel count is never stated",
        f"  * ({faithfulness}.2) the dime count is never stated",
    ):
        assert line in prompt and line in record
    assert f"({GATE_ORDER.index(held.gate) + 1}) `spec.verifies`" in record
    briefed = sound.manifest().provenance["repairs"][0]["session"]["briefed"]
    assert briefed[f"{faithfulness}.2"] == "the dime count is never stated"
    answers, _ = _repair_answers(sound)
    assert answers["the dime count is never stated"] == (
        "The repair resolved it: a dime in 10 cents"
    )
    assert "the nickel count is never stated" not in answers


@pytest.mark.parametrize(
    ("left", "first"),
    [
        pytest.param(rounds.NOT_REACHED, "audit.spec_completeness", id="not reached"),
        pytest.param(rounds.NOT_A_DEFECT, "audit.faithfulness", id="not a defect"),
    ],
)
def test_the_findings_a_session_did_not_reach_are_briefed_first_the_next_round(
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    left: str,
    first: str,
) -> None:
    """A session that answers part of its brief leaves the rest for the next one.

    Its report gives an entry for each numbered finding, and the verdict holding one it did
    not reach comes first in the next brief, its findings keeping their numbers. One it found
    no defect is the review's to judge, not left open, so the gates keep their order.
    """
    weak = finding("audit.spec_completeness", "the specification accepts attack-1")
    gaps = finding(
        "audit.faithfulness",
        "2 finding(s)",
        findings=["the nickel count is never stated", "the dime count is never stated"],
    )
    faithfulness, completeness = (
        str(GATE_ORDER.index(gate) + 1) for gate in (gaps.gate, weak.gate)
    )
    assert int(faithfulness) < int(completeness)
    entries = [
        {"finding": f"{faithfulness}.{index}", "outcome": "resolved", "witness": "40 cents"}
        for index in (1, 2)
    ]
    first_session = Editing(
        {**REPORTED, "findings": [*entries, {"finding": completeness, "outcome": left}]}
    )
    by_session(sound, settings, first_session, monkeypatch, verdicts=[weak, gaps])
    second = Editing(REPORTED, solution=None)

    by_session(sound, settings, second, monkeypatch, verdicts=[weak, gaps])

    after = second.asked[0].prompt
    later = ({weak.gate, gaps.gate} - {first}).pop()
    assert after.index(f"`{first}`") < after.index(f"`{later}`")
    assert f"  * ({faithfulness}.2) the dime count is never stated" in after


def test_a_session_is_told_how_to_decline_a_finding_and_who_reads_its_entries(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finding it shows is no defect has an outcome of its own, judged by the next review.

    It is told that an auditor is shown each entry's text, and which auditor reads which
    entries; an auditor is shown all of it.
    """
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    request = session.asked[0]
    told = " ".join(request.prompt.split())
    entry = request.fields["findings"]["items"]  # type: ignore[index]
    assert entry["properties"]["outcome"]["enum"] == list(rounds.OUTCOMES)
    assert "outcome" in entry["required"] and "resolved" not in entry["properties"]
    for said in (
        "`not a defect`: you established that it is none and changed nothing for it",
        "The next review is shown each entry's text",
        "unless your entry for the finding that names the attack shows it was no defect",
        "the faithfulness and equivalence auditors are shown each of their own findings",
        "the fuzz auditor reads none of them",
        "the disclosure auditor reads none of them",
    ):
        assert said in told, said
    assert "as that finding's `not a defect` entry" in " ".join(request.system.split())

    manifest = sound.manifest()
    entries = manifest.provenance["repairs"][-1]["session"]
    entries["findings"] = [{"finding": "7", "outcome": "not a defect", "witness": "x" * 3_000}]
    sound.save_manifest(manifest)
    answers, _ = _repair_answers(sound)
    assert set(answers.values()) == {
        "The repair found it no defect and changed nothing for it: " + "x" * 3_000
    }


def test_a_session_is_told_to_state_what_a_test_the_fix_keeps_passing_asserts(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An attack that fixes the bug and breaks something else is answered by preservation.

    Stating the fix more strongly leaves that attack accepted, so the brief says which half
    of correct each finding broke and what the other half asks for.
    """
    weak = finding(
        "audit.spec_completeness",
        "the specification accepts implementation(s) the benchmark's own tests reject: "
        "attack-1 (passes every test the fix makes pass, and fails test(s) it keeps "
        "passing: test_kept)",
        too_weak=["attack-1"],
    )
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[weak])

    prompt = session.asked[0].prompt
    assert "fails test(s) it keeps passing: test_kept" in prompt
    assert "## Whether it fails a FAIL_TO_PASS or a PASS_TO_PASS test" in prompt
    assert "state that as an obligation" in prompt


def test_a_completeness_finding_naming_a_determinism_lemma_is_resolved_by_proving_it(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The verdict's words reach the session, which say what proving it decides."""
    lemma = "∀ x1 r1 r2, Spec x1 r1 → Spec x1 r2 → r1 = r2"
    weak = finding(
        "audit.spec_completeness",
        "the specification accepts implementation(s) the benchmark's own tests reject: "
        "attack-1; the checker could not prove that the specification admits one result per "
        f"input. Where it does, state and prove `{lemma}` in the proof region, one theorem "
        "each",
        too_weak=["attack-1"],
        determinism=[lemma],
    )
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[weak])

    prompt = session.asked[0].prompt
    assert f"state and prove `{lemma}`" in prompt


class Leaning(Accepting):
    """A checker for a backend whose solution file is not `solution.py`."""

    name = "leaning"
    extension = ".lean"


def test_a_session_repair_names_the_backend_s_own_solution_file(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A session on another backend, told to repair `solution.py`, reads nothing."""
    session = Editing(REPORTED, solution=None)

    by_session(sound, settings, session, monkeypatch, backend=Leaning())

    prompt = session.asked[0].prompt
    assert "solution.lean" in prompt and "solution.py" not in prompt


def test_a_session_repair_puts_files_of_its_own_in_a_directory_of_its_own(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A backend's checker may run from a project directory every session here shares.

    A session that writes its probes there, and tidies up after itself, deletes another
    session's files.
    """
    session = Editing(REPORTED, solution=None)

    by_session(sound, settings, session, monkeypatch)

    assert {"scratch", "tools"} <= set(session.seen)
    prompt = session.asked[0].prompt
    assert "`scratch/` is yours" in prompt
    assert "delete nothing" in prompt
    assert "./tools verify FILE" in prompt
    ran = subprocess.run(
        [(session.asked[0].cwd / "tools").as_posix(), "--help"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert ran.returncode == 0, ran.stderr


def test_a_session_repair_is_told_the_clock_it_is_stopped_by(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A session with no clock spends it waiting to be re-invoked, which nothing does."""
    session = Editing(REPORTED, solution=None)
    tuned = settings.model_copy(update={"repair_timeout_s": 1800.0, "repair_turns": 120})

    by_session(sound, tuned, session, monkeypatch)

    assert "30 minutes of wall clock and 120 turns" in session.asked[0].prompt


@pytest.mark.parametrize(
    ("status", "seconds", "said"),
    [
        (Status.PASS, 211.6, "took 212 s on `solution.py` when the gates last judged it"),
        (Status.TIMEOUT, 320.4, "did not finish `solution.py` when the gates last judged"),
        (None, 0.0, "has no time on record for `solution.py`"),
    ],
)
def test_a_session_repair_is_told_the_checker_s_limit_and_its_last_time(
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    status: Status | None,
    seconds: float,
    said: str,
) -> None:
    """A repair that grows the file past the checker's limit has repaired nothing."""
    if status is not None:
        sound.record(
            [
                Verdict(
                    gate="spec.verifies", status=status, details={"checker_duration_s": seconds}
                )
            ]
        )
    session = Editing(REPORTED, solution=None)
    tuned = settings.model_copy(update={"verify_timeout_s": 77})

    by_session(sound, tuned, session, monkeypatch)

    prompt = " ".join(session.asked[0].prompt.split())
    limit = Accepting().budget(77)
    assert f"The checker stops on a file after {limit:.0f} seconds." in prompt
    assert f"The checker {said}" in prompt
    assert "A file it cannot finish in its time is not a repair" in prompt


def test_a_session_repair_judges_its_copy_under_the_run_s_own_settings(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its environment is not the run's, so the command it is given carries the settings.

    The command runs every gate a program decides, as the round after it will, so the
    session sees a failure of `conformance.py`, `axioms.py`, the property-based test suite or
    the leakage check that it caused before it reports; not the task's own check, which
    nothing it does changes. It is run here with `--help`, which the command line rejects
    when an option before it is one `check` does not take.
    """
    session = Editing(REPORTED)
    tuned = settings.model_copy(
        update={
            "verify_timeout_s": 77,
            "model": "a-drafting-model",
            "audit_model": "a-reviewer",
        }
    )

    by_session(sound, tuned, session, monkeypatch)

    line = next(
        line for line in session.asked[0].prompt.splitlines() if "--only spec.verifies" in line
    )
    gates = line.split("--only ")[1:]
    assert [gate.strip() for gate in gates] == [
        gate for gate in required_gates(Level.ORACLE) if gate != "oracle.reference_resolves"
    ]
    script = Path(line.split()[0])
    text = script.read_text()
    (named,) = re.findall(r"^\. (\S+)$", text, re.MULTILINE)
    environment = Path(named).read_text()
    assert "BENCHPROOFER_VERIFY_TIMEOUT_S=77" in environment
    assert f"BENCHPROOFER_CACHE_DIR={tuned.cache_dir.as_posix()}" in environment
    assert "BENCHPROOFER_" not in text and "PYTHONPATH" not in text
    assert "BENCHPROOFER_BUNDLE_ROOT=" not in environment
    assert "--as-submitted" in text
    assert text.rstrip().endswith('"$@" --level oracle')
    assert "a-drafting-model" not in environment and "a-reviewer" not in environment
    ran = subprocess.run(
        [script.as_posix(), "--help"], capture_output=True, text=True, timeout=120
    )
    assert ran.returncode == 0, ran.stderr


def test_a_session_s_script_reaches_no_model_and_keeps_the_arguments_it_pins(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A session cannot lift its check to the review's level, nor start the review itself.

    An argument it passes comes before the pinned ones, so `--level audited` is overridden;
    and the script sets every setting that reaches a model to none, the run's own and one
    the session's shell inherited alike, so a command copied from it starts no model either.
    """
    write_text(
        tmp_path / "shown.py",
        "import json, os, sys\n"
        "print(json.dumps([sys.argv[1:], {k: v for k, v in os.environ.items()"
        " if k.startswith('BENCHPROOFER_')}]))\n",
    )
    monkeypatch.setenv("PYTHONPATH", tmp_path.as_posix())
    monkeypatch.setenv("BENCHPROOFER_SESSION_MODEL", "an-inherited-model")
    tuned = settings.model_copy(update={"provider": "anthropic", "model": "a-drafting-model"})
    path = tmp_path / "check"

    write_script(path, ["shown"], tuned, pinned=["--level", "oracle"])
    ran = subprocess.run(
        [path.as_posix(), "--level", "audited"],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )

    argv, environment = json.loads(ran.stdout)
    assert argv == ["--level", "audited", "--level", "oracle"]
    assert environment["BENCHPROOFER_PROVIDER"] == "null"
    assert environment["BENCHPROOFER_SESSION"] == ""
    assert environment["BENCHPROOFER_MODEL"] == environment["BENCHPROOFER_SESSION_MODEL"] == ""


def test_a_session_s_script_reads_the_run_s_environment_from_a_file_the_session_cannot(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The script shows neither the module path nor a setting, which it reads from a file.

    The module path says where Benchproofer's source is, and the file is outside the
    workspace, where the session may not read. A session's environment empties the run's
    module path and Benchproofer settings and names its own temporary directory, and what
    the script runs gets the run's own back.
    """
    from benchproofer.core.scripts import private

    write_text(
        tmp_path / "shown.py",
        "import json, os\n"
        "print(json.dumps({k: os.environ.get(k) for k in"
        " ('BENCHPROOFER_LEAN_WORKSPACE', 'BENCHPROOFER_OFFLINE', 'TMPDIR')}))\n",
    )
    monkeypatch.setenv("PYTHONPATH", tmp_path.as_posix())
    monkeypatch.setenv("BENCHPROOFER_LEAN_WORKSPACE", "/srv/lake")
    monkeypatch.delenv("TMPDIR", raising=False)
    workspace = tmp_path / "cache" / "scratch" / "task" / "agent-repair"
    path = workspace / "tools"

    write_script(path, ["shown"], settings.model_copy(update={"offline": True}))
    text = path.read_text()
    session = {
        **os.environ,
        **dict.fromkeys(private(os.environ), ""),
        "TMPDIR": (workspace / "tmp").as_posix(),
    }
    ran = subprocess.run(
        [path.as_posix()], capture_output=True, text=True, timeout=120, check=True, env=session
    )

    (named,) = re.findall(r"^\. (\S+)$", text, re.MULTILINE)
    assert not Path(named).is_relative_to(workspace)
    assert "PYTHONPATH" not in text and "/srv/lake" not in text
    assert "PYTHONPATH" in Path(named).read_text()
    assert json.loads(ran.stdout) == {
        "BENCHPROOFER_LEAN_WORKSPACE": "/srv/lake",
        "BENCHPROOFER_OFFLINE": "true",
        "TMPDIR": None,
    }


def test_the_check_a_session_runs_judges_what_submission_will_judge(
    sound: Bundle, tmp_path: Path
) -> None:
    """Pre-fix implementations and rivals spliced into the specification, regions recorded anew.

    Without that, the gates a session runs report drift against a manifest its edit has
    not reached and read every case as carrying another specification, all of which
    submission clears; sessions spend the rest of their budget on it.
    """
    backend = Accepting()
    write_text(sound.solution_path, REPAIRED)
    twin = dict(sound.twins())["twin"]
    assert not backend.same_spec(REPAIRED, twin)
    assert sound.manifest().artifacts != sound.artifact_digests()

    copy = as_submitted(sound, backend, tmp_path / "copies")

    assert copy.root != sound.root
    assert copy.manifest().regions == backend.region_digests(REPAIRED)
    assert copy.manifest().artifacts == copy.artifact_digests()
    carried = [source for _, source in copy.twins()]
    carried += [copy.rival_source(rival) for rival in copy.battery()]
    assert carried and all(backend.same_spec(REPAIRED, source) for source in carried)
    assert dict(sound.twins())["twin"] == twin


def test_a_session_repair_sees_this_run_s_earlier_rounds_and_a_repository_of_its_own(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The earlier rounds are read from disk, not summarized; the repository is a copy."""
    history = tmp_path / "rounds"
    write_text(history / "00" / "round.md", "# Round 00\n")
    write_text(history / "01-undone" / "round.md", "# Round 01\n")
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, history=history)

    assert "rounds/00/round.md" in session.seen
    assert "rounds/01-undone/round.md" in session.seen
    assert "repository" in session.seen
    assert any(path.endswith("/task.json") for path in session.seen)


def test_a_session_repair_is_told_what_each_earlier_round_found_and_what_the_repair_did(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Oldest first, the first sentence of each, so a finding a later one reverses is seen.

    The last round is the one the findings briefed in full come from, so it is not repeated.
    """
    history = tmp_path / "rounds"
    strict = finding(
        "audit.faithfulness",
        "It pins that no writer runs. The task does not ask that.",
        findings=["Demands more than the task: a writer may run under --check. Input: x."],
    )
    freed = {
        "round": 1,
        "addressing": ["audit.faithfulness"],
        "session": {"summary": "Freed. Then more."},
    }
    refused = {
        "round": 2,
        "addressing": ["audit.spec_soundness"],
        "session": {"refused": "the session changed nothing", "summary": "Blocked."},
    }
    for name, found, done in (
        ("00", strict, []),
        ("01", finding("audit.spec_soundness", "A right writer is refused."), [freed]),
        ("02", finding("spec.verifies", "The checker refused it."), [freed, refused]),
    ):
        recorded = sound.manifest().model_copy(
            update={"verdicts": {found.gate: found}, "provenance": {"repairs": done}}
        )
        write_text(history / name / "manifest.json", recorded.model_dump_json())
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, history=history)

    prompt = session.asked[0].prompt
    told = prompt[prompt.index("## What earlier rounds") : prompt.index("## What you have")]
    assert (
        "* Round 00 (`rounds/00/round.md` has it in full):\n"
        "  * `audit.faithfulness` (fail): It pins that no writer runs.\n"
        "    * Demands more than the task: a writer may run under --check.\n"
        "  * Then repair 1 addressed `audit.faithfulness`: Freed.\n"
        "* Round 01 (`rounds/01/round.md` has it in full):\n"
        "  * `audit.spec_soundness` (fail): A right writer is refused.\n"
        "  * Then repair 2 addressed `audit.spec_soundness`: Its work was not taken: the "
        "session changed nothing.\n"
    ) in told
    assert "Round 02" not in told and "The checker refused it." not in told


def kept_round(
    history: Path, name: str, bundle: Bundle, *verdicts: Verdict, repairs: int = 0
) -> Path:
    """Keep ``bundle`` as a round of this run judged it, as `pipeline.run` keeps one.

    Its manifest holds ``verdicts`` and a repair record of ``repairs`` repairs. Returns the
    round's directory.
    """
    kept = history / name
    shutil.copytree(bundle.root, kept)
    manifest = bundle.manifest().model_copy(
        update={
            "verdicts": {verdict.gate: verdict for verdict in verdicts},
            "provenance": {"repairs": [{"round": number} for number in range(1, repairs + 1)]},
        }
    )
    write_text(kept / "manifest.json", manifest.model_dump_json())
    return kept


def refuted(*callees: str) -> Verdict:
    """`audit.axiom_soundness` reporting a fuzzer's refutation of each of ``callees``."""
    return finding(
        "audit.axiom_soundness",
        f"an independent fuzzer disagrees with what the specification assumes of {callees[0]}",
        refuted=list(callees),
        witnesses=[
            f"fuzz-1: benchproofer:refuted {callee} two calls on (3,) returned 1 and 2; the "
            "axiom's line '@Pure' states one result"
            for callee in callees
        ],
    )


#: The heading of the section listing the callees a repair may take the result of as an input.
LISTED = "## Callees whose definition or axiom failed in two rounds"


@pytest.mark.parametrize(
    ("kept", "found"),
    [
        pytest.param(
            [(0, ("os.cpu_count",)), (1, ("os.cpu_count",))],
            ["os.cpu_count"],
            id="refuted in two rounds with a repair between",
        ),
        pytest.param([(0, ("os.cpu_count",))], [], id="refuted once"),
        pytest.param(
            [(0, ("os.cpu_count",)), (0, ("os.cpu_count",))],
            [],
            id="refuted twice with no repair between",
        ),
        pytest.param(
            [(0, ("os.cpu_count",)), (1, ("time.time",))],
            [],
            id="refuted once each, two callees",
        ),
        pytest.param(
            [(0, ("os.cpu_count", "time.time")), (1, ("time.time",))],
            ["time.time"],
            id="only the callee refuted twice",
        ),
    ],
)
def test_a_callee_is_eligible_once_a_repair_failed_to_state_it_again(
    kept: list[tuple[int, tuple[str, ...]]],
    found: list[str],
    sound: Bundle,
    tmp_path: Path,
) -> None:
    """Two rounds of this run, with a repair between them, refuted its axiom or definition.

    A round that asked an auditor again about an unchanged bundle has as many repairs on record
    as the round before it, so the two count once.
    """
    history = tmp_path / "rounds"
    for index, (repairs, callees) in enumerate(kept):
        kept_round(history, f"{index:02d}", sound, refuted(*callees), repairs=repairs)

    listed = rounds.eligible(history, Accepting())

    assert sorted(listed) == found
    for callee in found:
        assert [failed.round for failed in listed[callee]][-1] == f"{len(kept) - 1:02d}"
        assert all(
            failed.what == "`audit.axiom_soundness` (the axiom-soundness gate) refuted it"
            for failed in listed[callee]
        )
        assert listed[callee][0].lines == (
            f"fuzz-1: benchproofer:refuted {callee} two calls on (3,) returned 1 and 2; the "
            "axiom's line '@Pure' states one result",
        )


#: A Nagini solution file modeling `os.cpu_count` in its `axioms` region, at line 3.
MODELING = """\
from nagini_contracts.contracts import *
# benchproofer:begin axioms
# benchproofer:models os.cpu_count
@Pure
def cpu_count() -> int:
    return 4
# benchproofer:end axioms
# benchproofer:begin spec
def impl(n: int) -> int:
    Ensures(Result() == n)
# benchproofer:end spec
# benchproofer:begin impl
    return n
# benchproofer:end impl
"""


@pytest.mark.parametrize(
    ("line", "counted"),
    [
        pytest.param(5, True, id="under the declaration"),
        pytest.param(13, False, id="in the implementation"),
    ],
)
def test_a_checker_error_under_a_callee_s_declaration_counts_as_a_failed_round(
    line: int, counted: bool, sound: Bundle, tmp_path: Path
) -> None:
    """The checker placing an error under its declaration fails the definition, as a refutation.

    Read off the checker's output the verdict names, against the round's own solution file.
    """
    nagini = BACKENDS.get("nagini")
    history = tmp_path / "rounds"
    error = (
        f"solution.py:{line}:4:{line}:12: error: Verification failed: Postcondition might fail."
    )
    rejected = Verdict(
        gate="spec.verifies",
        status=Status.FAIL,
        summary="the checker rejected the solution",
        evidence=["evidence/verifies.log"],
    )
    first = kept_round(history, "00", sound, rejected)
    write_text(first / "solution.py", MODELING)
    write_text(first / "evidence" / "verifies.log", f"Verification failed\n{error}\n")
    kept_round(history, "01", sound, refuted("os.cpu_count"), repairs=1)

    listed = rounds.eligible(history, nagini)

    assert ("os.cpu_count" in listed) is counted
    if counted:
        (placed, fuzzed) = listed["os.cpu_count"]
        assert (placed.round, placed.lines) == ("00", (error,))
        assert placed.what.startswith("`spec.verifies` (the verification check) did not pass")
        assert fuzzed.round == "01"


def test_a_repair_is_shown_the_callees_its_rounds_let_it_take_the_result_of_as_an_input(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Each with its evidence, and the rule for taking one; a brief listing none has no rule.

    The system prompt states the rule for callees as drafting does, whatever the rounds list.
    """
    history = tmp_path / "rounds"
    kept_round(history, "00", sound, refuted("os.cpu_count"))
    once = Editing(REPORTED)
    by_session(sound, settings, once, monkeypatch, history=history)
    kept_round(history, "01", sound, refuted("os.cpu_count"), repairs=1)
    twice = Editing(REPORTED)
    by_session(sound, settings, twice, monkeypatch, history=history)

    shut = " ".join(once.asked[0].prompt.split())
    assert LISTED not in once.asked[0].prompt
    assert "input of the model" not in shut and "Callee results taken as inputs" not in shut
    brief = twice.asked[0].prompt
    listed = brief[brief.index(LISTED) : brief.index("## Run the gates yourself")]
    assert (
        "* `os.cpu_count`\n"
        "  * round 00: `audit.axiom_soundness` (the axiom-soundness gate) refuted it:\n"
        "    * `fuzz-1: benchproofer:refuted os.cpu_count two calls on (3,) returned 1 and 2; "
        "the axiom's line '@Pure' states one result`\n"
        "  * round 01: `audit.axiom_soundness` (the axiom-soundness gate) refuted it:\n"
    ) in listed
    told = " ".join(listed.split())
    assert "(a) its result can differ between two calls with the same arguments" in told
    assert (
        "Nor is the result of a call whose arguments the golden patch adds, changes or "
        "computes, even for a callee listed above"
    ) in told
    assert (
        "in a section of its own after `Outside the bridge`, `## Callee results taken" in told
    )
    for session in (once, twice):
        system = " ".join(session.asked[0].system.split())
        assert " ".join(SHARED.rules("callee").split()) in system
        assert LISTED not in session.asked[0].system


def test_a_session_that_reported_excluding_inputs_is_taken_for_the_gates_to_judge(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A narrowing is found by the conformance gate and the next review, not by the report.

    The report's account of what it excluded is kept in the repair record.
    """
    raised = "a negative amount: the repository raises ValueError (change.py:3)"
    session = Editing({**REPORTED, "excluded": raised})

    result = by_session(sound, settings, session, monkeypatch)

    assert result.changed
    assert sound.solution() == REPAIRED
    entry = sound.manifest().provenance["repairs"][-1]["session"]
    assert "refused" not in entry
    assert entry["excluded"] == raised
    prompt = " ".join(session.asked[0].prompt.split())
    assert "fails a bundle whose program declares one a run drew inadmissible" in prompt


def test_a_session_is_told_which_outside_the_bridge_entries_are_not_a_narrowing(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The three kinds the section is for, each named in the request, and a widening.

    Among them inputs on which the fixed function runs only what the golden patch leaves as
    it was: it returns or raises before the fix, or finds a condition the fix adds false and
    goes on into a branch the fix leaves alone. A change that widens the domain shuts out
    nothing, and is how a finding that the domain leaves out inputs the benchmark's tests
    hand a changed function is resolved.
    """
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    request = session.asked[0]
    prompt = " ".join(request.prompt.split())
    assert "An entry of one of the three kinds below is not a narrowing" in prompt
    assert " ".join(SHARED.rules("outside").split()) in prompt
    assert "runs only what the golden patch leaves as it was" in prompt
    assert "neither is `conformance.py` skipping, with a line naming the entry" in prompt
    assert "Nor is a change that widens the domain -- an input case added, a precondition" in (
        prompt
    )
    assert "three kinds" in request.fields["excluded"]["description"]
    # What an obligation has to be about is the system prompt's to say, not the brief's.
    assert "only with a frame" in request.system
    assert "only with a frame" not in request.prompt


def test_a_session_is_told_which_failing_tests_the_pre_fix_implementation_need_not_fail(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One that fails before the fix only on a name the golden patch adds, or on a type."""
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    system = " ".join(session.asked[0].system.split())
    assert "only because it uses a name the golden patch adds" in system
    assert "value, a missing behavior or a wrong exception." in system


def test_the_next_session_is_told_what_a_refused_session_left_and_excluded(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its edits went with its workspace, so `manifest.json` is what the next session is told.

    Why it was refused, what its report says it excluded and what it left of the bundle's
    files, ahead of the findings it was addressing, which stand.
    """
    raised = "a negative amount: the repository raises ValueError (change.py:3)"
    first = Editing(
        {**REPORTED, "excluded": raised},
        solution=REPAIRED.replace("# benchproofer:end spec\n", ""),
        files={"correspondence.md": "## Outside the bridge\n\n* a negative amount\n"},
    )
    by_session(sound, settings, first, monkeypatch)
    second = Editing(REPORTED)

    by_session(sound, settings, second, monkeypatch)

    prompt = second.asked[0].prompt
    note = prompt[: prompt.index("These gates did not pass")]
    assert "## Repairs that were not taken" in note
    assert "Repair 1, not taken: the repaired solution cannot be read" in note
    assert f"What it excluded, in its report's words: {raised}" in note
    assert "+++ left/correspondence.md" in note
    assert "    +* a negative amount" in note
    assert "* (7) `spec.strength.battery`" in prompt
    # The second session's work was taken, so the one after it is told of no refusal.
    assert "not taken" not in _brief_after(sound, settings, monkeypatch)


def test_the_next_session_is_told_a_session_changed_nothing(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every refusal reaches the next brief, with the report's account and no diff."""
    by_session(sound, settings, Editing(REPORTED, solution=None), monkeypatch)

    note = _brief_after(sound, settings, monkeypatch)

    assert "Repair 1, not taken: the session changed nothing a repair may change." in note
    assert "Its report: The contract now conserves the amount." in note
    assert "```diff" not in note and "Model the behaviour" not in note


def _brief_after(bundle: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch) -> str:
    """The opening of the brief the next repair session is given, before its findings."""
    session = Editing(REPORTED)
    by_session(bundle, settings, session, monkeypatch)
    prompt = session.asked[0].prompt
    return prompt[: prompt.index("These gates did not pass")]


class ByLabel(Accepting):
    """A checker that accepts every file but those checked under the labels it is given.

    The label is the directory a stage checks a file in, so a case can refuse the file a
    session left without refusing the one the bundle had.
    """

    name = "by-label"

    def __init__(self, answers: dict[str, CheckResult] | None = None) -> None:
        super().__init__()
        self.answers = answers or {}
        #: The label each call was made under.
        self.checked: list[str] = []

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        self.checked.append(workdir.name)
        return self.answers.get(workdir.name, CheckResult.ok("accepted"))


#: A rival as a session edits it: its own implementation, the shipped specification.
EDITED_RIVAL = "def impl(cents):\n    return (cents // 25, 0, 0, cents % 25)\n"


@pytest.mark.parametrize("report", [None, REPORTED], ids=["no report", "a report"])
def test_what_a_session_left_is_kept_for_the_gates_to_judge_whether_or_not_it_reported(
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    report: dict[str, object] | None,
) -> None:
    """A changed specification, a solution the checker refuses and the files beside it alike.

    Nothing it left is put to the checker on the way in: the gates judge it.
    """
    rival = sound.battery()[0]
    twins = [name for name, _ in sound.twins()]
    rivals = [case.id for case in sound.battery()]
    edited = replace_region(sound.rival_source(rival), COMMENT, "impl", EDITED_RIVAL)
    session = Editing(
        report,
        files={
            "correspondence.md": "## Symbols\n\n* for the new spec\n",
            "conformance.py": NARROWED,
            f"rivals/{rival.file}": edited,
        },
    )
    backend = ByLabel({"solution": CheckResult.no("Postcondition might not hold.")})

    result = by_session(sound, settings, session, monkeypatch, backend=backend)

    assert result.changed
    assert sound.solution() == REPAIRED
    assert sound.correspondence_path.read_text() == "## Symbols\n\n* for the new spec\n"
    assert sound.conformance_path.read_text() == NARROWED
    assert impl_of(sound.rival_source(rival)) == EDITED_RIVAL.strip()
    assert [name for name, _ in sound.twins()] == twins
    assert [case.id for case in sound.battery()] == rivals
    assert "solution" not in backend.checked
    assert "refused" not in sound.manifest().provenance["repairs"][-1]["session"]


def test_a_session_that_changed_nothing_leaves_the_bundle_and_its_review_alone(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finding about a case beside it included: the next session sees it again."""
    filed(sound)
    session = Editing({**REPORTED, "status": "BLOCKED"}, solution=None)
    malformed = finding(BATTERY, MALFORMED + "uniqueness-2", malformed=["uniqueness-2"])

    result = by_session(
        sound,
        settings,
        session,
        monkeypatch,
        verdicts=[finding("audit.faithfulness", "the obligations miss a behavior"), malformed],
    )

    assert not result.changed
    review = sound.audit()
    assert review is not None
    assert not any(judgment.stale(sound.artifact_digests()) for judgment in review.judgments)


def witnessed(bundle: Bundle, claim: str = TWIN_WITNESS) -> None:
    """Record ``claim`` as the witness of the bundle's pre-fix implementation."""
    bundle.save_twins(
        [
            (Twin(id=name, file=f"{name}.py", witness=claim), source)
            for name, source in bundle.twins()
        ]
    )


def test_a_pre_fix_implementation_carried_into_the_repaired_specification_keeps_its_witness(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The witness makes the pre-fix implementation's refusal evidence; splicing keeps it."""
    witnessed(sound)

    by_session(sound, settings, Editing(REPORTED), monkeypatch)

    assert sound.solution() == REPAIRED
    assert sound.twin_cases()["twin"].witness.strip() == TWIN_WITNESS


def rewritten(sound: Bundle) -> tuple[str, str]:
    """A case the session left carrying the specification its own solution replaced."""
    rival = sound.battery()[0]
    return rival.id, replace_region(sound.solution(), COMMENT, "impl", EDITED_RIVAL)


def test_a_witness_the_session_rewrote_is_carried_with_its_case(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rivals and the pre-fix implementation alike: gates judge, none is redrafted."""
    updated(sound, "uniqueness-1", witness=TWIN_WITNESS)
    witnessed(sound)
    rewitnessed = {
        f"{directory}/index.toml": (sound.root / directory / "index.toml")
        .read_text()
        .replace("spec 40 (impl 40)", "spec 30 (impl 30)")
        for directory in ("rivals", "twins")
    }
    session = Editing(REPORTED, solution=None, files=rewitnessed)

    by_session(
        sound,
        settings,
        session,
        monkeypatch,
        backend=Witnessing(),
        verdicts=[unattributed_twin("the witness does not hold of the twin")],
    )

    assert session.asked
    case = next(rival for rival in sound.battery() if rival.id == "uniqueness-1")
    assert case.witness.strip() == SESSION_WITNESS
    assert sound.twin_cases()["twin"].witness.strip() == SESSION_WITNESS


def test_a_carried_case_is_left_to_the_property_based_test_suite_to_judge(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spliced into the repaired specification, and put to no checker on the way in.

    The session had the checker, and `spec.strength.battery` runs it on every case.
    """
    case, source = rewritten(sound)
    backend = ByLabel()
    session = Editing(REPORTED, files={f"rivals/{case}.py": source})

    by_session(sound, settings, session, monkeypatch, backend=backend)

    assert backend.checked == []
    carried = next(rival for rival in sound.battery() if rival.id == case)
    assert impl_of(sound.rival_source(carried)) == EDITED_RIVAL.strip()
    assert Accepting().same_spec(sound.rival_source(carried), REPAIRED)


def assuming(solution: str, model: str) -> str:
    """``solution`` with an `axioms` region modeling the parser it assumes as ``model``."""
    region = wrap(COMMENT, "axioms", f"{model}\n{directive_line(COMMENT, 'json.loads')}")
    return f"{region}\n\n\n{solution}"


#: Two models of the same unchanged callee, as a repair that retypes it leaves them.
LOADS = 'def loads(text):\n    return {"n": int(text)}\n'
RETYPED = 'def loads(text: str) -> dict:\n    return {"n": int(text.strip())}\n'


def test_an_axioms_py_left_quoting_a_retyped_axiom_is_kept_as_the_session_left_it(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The quotation is the session's to keep in step, and the session is told so.

    The grounding gate refuses an `axioms.py` that lacks a declaration of the region the
    solution states, so nothing rewrites it on the way in.
    """
    shipped = assuming(sound.solution(), LOADS)
    write_text(sound.solution_path, shipped)
    region = parse(shipped, COMMENT)["axioms"].text
    grounding = with_declarations("print('grounding')\n", region, COMMENT)
    write_text(sound.axioms_path, grounding)
    session = Editing(REPORTED, solution=assuming(REPAIRED, RETYPED))

    by_session(sound, settings, session, monkeypatch)

    retyped = parse(sound.solution(), COMMENT)["axioms"].text
    assert read_text(sound.axioms_path) == grounding
    assert not quotes_lines(grounding, retyped, COMMENT)
    told = " ".join(session.asked[0].prompt.split())
    assert "Benchproofer does not update either" in told
    assert "change the copy or the quotation as well" in told


#: A program as a session leaves it: one comparison where the shipped one drew 10,000.
NARROWED = "print('benchproofer:compared change.make_change 1 input')\n"
#: The conformance gate's verdict on a disagreement with the repository's own code.
DISAGREES = finding(
    "impl.conformance",
    "the repository's own code disagrees with the verified implementation",
    compared_inputs=100,
    disagrees=["change.make_change"],
)
#: The grounding gate's verdict on an assumption the real callee refuted.
REFUTED = finding(
    "spec.axioms_grounded",
    "axioms.py refuted what the specification assumes of json.loads",
    refuted=["json.loads"],
)


@pytest.mark.parametrize(
    ("name", "verdict"),
    [
        pytest.param(
            "conformance.py",
            finding("audit.faithfulness", "the obligations miss a behavior"),
            id="conformance.py, another finding",
        ),
        pytest.param("conformance.py", DISAGREES, id="conformance.py, its own gate"),
        pytest.param("axioms.py", REFUTED, id="axioms.py, its own gate"),
        pytest.param("axioms.py", DISAGREES, id="axioms.py, the conformance gate"),
    ],
)
def test_a_program_a_session_changed_is_taken_as_it_left_it(
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    verdict: Verdict,
) -> None:
    """Whatever it was addressing: its gate runs it again, and the review reads the change."""
    if name == "axioms.py":
        write_text(sound.axioms_path, "print('grounding')\n")
    session = Editing(REPORTED, solution=None, files={name: NARROWED})

    result = by_session(sound, settings, session, monkeypatch, verdicts=[verdict])

    assert result.changed
    assert read_text(sound.root / name) == NARROWED
    entry = sound.manifest().provenance["repairs"][-1]["session"]
    assert name in entry["edited"] and "refused" not in entry
    told = " ".join(session.asked[0].system.split())
    assert "You may change either" in told


def test_a_session_writing_conformance_py_is_told_the_names_inputs_on_record_are_kept_under(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It is handed them under those names, so one naming its function otherwise drops them."""
    replay.record(sound, {"change.make_change": ["(40,)"]}, source=replay.GATE, spec="")
    sound.conformance_path.unlink()
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    assert "inputs on record for `change.make_change`" in session.asked[0].prompt


# ---- what a repair session is given -----------------------------------------


#: A test patch adding the test the fix is judged by, as a benchmark ships one.
TEST_PATCH = (
    "diff --git a/tests/test_change.py b/tests/test_change.py\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/tests/test_change.py\n"
    "@@ -0,0 +1,5 @@\n"
    "+from change import make_change\n"
    "+\n"
    "+\n"
    "+def test_forty_cents_takes_a_nickel():\n"
    "+    assert make_change(40) == (1, 1, 1, 0)\n"
)


def test_a_session_repair_reads_the_tests_as_the_benchmark_runs_them(
    coin_change: Task, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The test patch applied to its repository and kept beside it, as drafting has it.

    The brief names the tests rather than pasting the patch, which a long one would clip.
    """
    task = coin_change.model_copy(
        update={"metadata": {**coin_change.metadata, "test_patch": TEST_PATCH}}
    )
    bundle = fixtures.stage(fixtures.fixture("coin-change-sound"), task, settings)
    bundle_module.freeze_task(settings.bundle_root, task, refresh=True)
    session = Editing(REPORTED)

    by_session(bundle, settings, session, monkeypatch)

    workspace = session.asked[0].cwd
    assert "assert make_change(40) == (1, 1, 1, 0)" in read_text(
        workspace / "repository" / "tests" / "test_change.py"
    )
    assert read_text(workspace / "tests.patch") == TEST_PATCH
    prompt = session.asked[0].prompt
    assert "`tests.patch`, beside `repository/`, is that diff" in prompt
    assert "+def test_forty_cents_takes_a_nickel" not in prompt


def test_a_session_repair_is_given_the_rules_its_programs_are_held_to(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ones the gates apply to `conformance.py` and `axioms.py`, as their author has them.

    Where a finding is about each: the line protocol, the inputs handed back in
    `BENCHPROOFER_REPLAY`, the copy of the implementation in its region, and the exact quote
    of an `Outside the bridge` entry; the grounding protocol and the tree `axioms.py` runs
    against; and that the conformance gate runs its program twice, with a line printed before
    each run.
    """
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[DISAGREES, REFUTED])

    prompt = " ".join(session.asked[0].prompt.split())
    rules = differential.protocol_for(
        settings.inputs_for("demo"), settings.harness_timeout_s * differential.DEADLINE_SHARE
    )
    assert " ".join(rules.split()) in prompt
    for said in (
        "benchproofer:rechecked <function>",
        'globals().get("BENCHPROOFER_REPLAY", {})',
        "# benchproofer:begin impl",
        "quote at least five words of the entry exactly",
        "benchproofer:grounded <callee>",
        "# benchproofer:axioms apply-fix",
        "and again against the base commit",
        "It prints a line as it starts each gate and each run of `conformance.py`",
        "a run of `conformance.py` or `axioms.py` stopping after",
    ):
        assert said in prompt, said


#: The heading of each section of a repair's request that gives a file's rules.
SECTIONS = {
    "twins": "## The pre-fix implementation, in `twins/`",
    "rivals": "## The property-based test suite, in `rivals/`",
    "correspondence.md": "## `correspondence.md`",
    "conformance.py": "## `conformance.py`",
    "axioms.py": "## `axioms.py`",
}


def sections(prompt: str) -> list[str]:
    """The files whose rules a repair's request gives, in the order it gives them."""
    return [name for name, heading in SECTIONS.items() if f"\n{heading}\n" in prompt]


@pytest.mark.parametrize(
    ("verdict", "given"),
    [
        pytest.param(finding(BATTERY, too_weak=["uniqueness-1"]), ["rivals"], id="the suite"),
        pytest.param(unattributed_twin(), ["twins"], id="the pre-fix implementation"),
        pytest.param(DISAGREES, ["conformance.py"], id="conformance"),
        pytest.param(REFUTED, ["axioms.py"], id="grounding"),
        pytest.param(
            finding("audit.faithfulness", "the obligations miss a behavior"),
            [],
            id="the specification",
        ),
        pytest.param(
            finding("audit.faithfulness", "correspondence.md maps no operation to the guard"),
            ["correspondence.md"],
            id="a finding naming a file",
        ),
    ],
)
def test_a_session_is_given_the_rules_of_the_files_its_findings_are_about(
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    verdict: Verdict,
    given: list[str],
) -> None:
    """By the gate that found them or the file a finding names, and of no other file."""
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[verdict])

    prompt = session.asked[0].prompt
    assert sections(prompt) == given
    assert "The bundle has no" not in prompt


def test_a_session_given_a_first_draft_the_checker_refused_is_asked_for_every_file(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The repair writes what drafting left out, and one it leaves missing stays missing.

    Drafting writes nothing beside a solution the checker refuses, and nothing is drafted
    after a repair.
    """
    write_text(sound.solution_path, assuming(sound.solution(), LOADS))
    for directory in (sound.twins_dir, sound.rivals_dir):
        for path in directory.iterdir():
            path.unlink()
    for path in (sound.correspondence_path, sound.conformance_path, sound.axioms_path):
        path.unlink(missing_ok=True)
    session = Editing(REPORTED)

    result = by_session(
        sound,
        settings,
        session,
        monkeypatch,
        verdicts=[finding("spec.verifies", "the checker refutes it")],
    )

    prompt = session.asked[0].prompt
    assert sections(prompt) == list(SECTIONS)
    assert "are beside it" not in prompt and "is beside it" not in prompt
    assert (
        "The bundle has no pre-fix implementation in `twins/`, property-based test suite in "
        "`rivals/`, `correspondence.md`, `conformance.py` or `axioms.py` yet: write each, as "
        "the sections below say."
    ) in " ".join(prompt.split())
    assert result.written == ("solution.py",)
    assert not sound.battery() and not sound.twins()
    assert not sound.correspondence_path.exists()


def test_a_session_given_a_solution_whose_regions_cannot_be_read_is_given_the_rules_anyway(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """As a first draft can leave one: `spec.hygiene` reports it, and the repair rewrites it."""
    write_text(sound.solution_path, sound.solution().replace("# benchproofer:end spec\n", ""))
    for path in sound.twins_dir.iterdir():
        path.unlink()
    sound.conformance_path.unlink()
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[finding("spec.hygiene")])

    assert sections(session.asked[0].prompt) == ["twins", "conformance.py"]


def test_a_session_repair_is_told_what_each_tool_is_for_and_what_a_finding_asks(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`run` for what the real code does, and `try` for an attack it answers.

    Beside the rules of a mutant, of an admissibility case and of a rewritten rationale.
    """
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    prompt = " ".join(session.asked[0].prompt.split())
    assert "`./tools run FILE` runs the Python program FILE where" in prompt
    assert "run it with `./tools run`, where the benchmark's tests run" in prompt
    assert "put that copy to `./tools try` as an attack" in prompt
    assert "## A mutant the checker accepts" in prompt
    assert "keeps the solution file's implementation line for line" in prompt
    assert "keeps the rationale you wrote" in prompt
    assert "not a fair test" not in prompt


def test_a_session_repair_is_told_only_of_what_its_round_has(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No review before the first, no `twins/index.toml`, no earlier rounds or repairs."""
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    prompt = " ".join(session.asked[0].prompt.split())
    assert not (sound.root / "audit").exists() and "`audit/` is the review" not in prompt
    assert not sound.twins_index.exists() and "twins/index.toml" not in prompt
    assert "earlier rounds listed above" not in prompt
    assert "the last repair did not reach comes first" not in prompt
    assert "`axioms.py`, `correspondence.md`" not in prompt
    assert (
        "`conformance.py`, `correspondence.md`, `rivals/` and `twins/` are beside it" in prompt
    )

    filed(sound)
    later = Editing(REPORTED)
    by_session(sound, settings, later, monkeypatch)

    told = " ".join(later.asked[0].prompt.split())
    assert "`audit/` is the review" in told
    assert "the last repair did not reach comes first" in told


@pytest.mark.parametrize(
    ("backend", "shown", "hidden"),
    [
        pytest.param(
            BACKENDS.get("nagini"),
            "Malformed `# type:` comment",
            "old executable shape",
            id="nagini",
        ),
        pytest.param(BACKENDS.get("lean4"), "old executable shape", "`# type:`", id="lean4"),
        pytest.param(
            Accepting(), "Dropping a framing assert", "`# type:`", id="another checker"
        ),
    ],
)
def test_a_session_repair_is_shown_the_refused_cases_of_its_own_checker(
    backend: Backend, shown: str, hidden: str
) -> None:
    listed = (*backend.refused_cases, *session_module._REFUSED_CASES)

    assert any(shown in item for item in listed)
    assert not any(hidden in item for item in listed)


def test_a_session_repair_finds_its_brief_in_its_workspace(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """To read again once its context has been compacted, as the brief says."""
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    request = session.asked[0]
    assert read_text(request.cwd / "brief.md") == request.prompt
    assert "This brief is also in `brief.md`" in request.prompt


def test_a_session_repair_is_given_the_files_the_auditors_left(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finding cites the auditor's own scratch files, which live in its workspace."""
    review = sound.scratch(settings.cache_dir, "review")
    write_text(review / "faithfulness" / "scratch" / "probe.py", "print(make_change(40))\n")
    (review / "disclosure" / "scratch").mkdir(parents=True)
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch)

    assert "review/faithfulness/scratch/probe.py" in session.seen
    assert not any(path.startswith("review/disclosure") for path in session.seen)
    assert "`review/<auditor>/scratch/` holds the files each auditor left" in (
        " ".join(session.asked[0].prompt.split())
    )


def test_an_attack_a_completeness_finding_names_is_briefed_with_its_file_and_claim(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """So the session need not read the review's whole index to find them."""
    filed(sound)
    ruled = "checker: verified; correctness: wrong (a weakness of the specification)"
    weak = finding(
        "audit.spec_completeness",
        "the specification accepts implementation(s) the tests reject: attack-1",
        too_weak=["attack-1"],
        rulings={"attack-1": ruled},
    )
    session = Editing(REPORTED)

    by_session(sound, settings, session, monkeypatch, verdicts=[weak])

    number = GATE_ORDER.index(weak.gate) + 1
    assert (
        f"  * ({number}.1) `attack-1` (`audit/attack-1.py`): attack-1 returns the wrong coins "
        f"The gates ruled: {ruled}."
    ) in session.asked[0].prompt


def test_a_rationale_the_session_rewrote_with_its_case_is_kept(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Whatever digest it left beside it; one it left as it was is about the old file."""
    index = read_text(sound.rivals_dir / "index.toml")
    first, second = sound.battery()[:2]
    rewritten = index.replace(first.rationale, "It now hands out no dimes at all.")
    files = {
        "rivals/index.toml": rewritten,
        f"rivals/{first.file}": replace_region(
            sound.rival_source(first), COMMENT, "impl", OTHER_IMPL
        ),
        f"rivals/{second.file}": replace_region(
            sound.rival_source(second), COMMENT, "impl", ATTACK_IMPL
        ),
    }
    session = Editing(REPORTED, files=files)

    by_session(sound, settings, session, monkeypatch)

    kept = {rival.id: rival for rival in sound.battery()}
    assert kept[first.id].rationale == "It now hands out no dimes at all."
    assert kept[second.id].rationale == bundle_module.REWRITTEN


def test_the_check_a_session_runs_judges_its_programs_as_it_left_them(
    sound: Bundle, tmp_path: Path
) -> None:
    """`conformance.py` keeps the copy it holds, and `axioms.py` what it quotes.

    As the gates will judge them after the repair.
    """
    backend = Accepting()
    old = differential.substituted(HARNESS, differential.executables(sound.solution(), backend))
    assert old is not None
    write_text(sound.conformance_path, old)
    write_text(sound.axioms_path, "print('grounding')\n")
    edited = replace_region(sound.solution(), COMMENT, "impl", ATTACK_IMPL)
    write_text(sound.solution_path, edited)

    copy = as_submitted(sound, backend, tmp_path / "copies")

    assert read_text(copy.conformance_path) == old
    assert read_text(copy.axioms_path) == "print('grounding')\n"
