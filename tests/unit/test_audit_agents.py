# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The review as agent sessions: one per auditor, each in a workspace of its own.

The session is a double that plays the reviewer: it writes files into its workspace and
submits a payload naming them. What is pinned here is what the tool makes of that --
which files it lays out for which auditor, what it files and what it refuses, and what it
keeps from the review before -- since that part does not depend on the model.
"""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from test_audit_session import narrowed_since_drafting
from test_repair import LISTED, kept_round, refuted

from benchproofer.audit import prompts as audit_prompts
from benchproofer.audit.agents import Reviewers
from benchproofer.audit.session import JUDGED_ROLES, LANES, ROLE_READS, Audit, axioms_digest
from benchproofer.backends.base import Backend
from benchproofer.config import Settings
from benchproofer.core import material, replay, rounds, variant
from benchproofer.core.bundle import Bundle, Defect, Judgment, Review, Submission
from benchproofer.core.markers import replace_region
from benchproofer.core.prompts import SHARED
from benchproofer.core.readings import CITES, IMPL, SPEC, SPEC_UNCOMMENTED, readings
from benchproofer.core.task import Task
from benchproofer.core.verdict import SkipReason, Status, Verdict
from benchproofer.errors import ProviderError
from benchproofer.gates.audit import UNRULED
from benchproofer.llm.agentic import EDIT, READ_ONLY, AgentSession, SessionSpec, StepOutcome
from benchproofer.pipeline import audit as reviewing
from benchproofer.pipeline.audit import due, write_audit
from benchproofer.registries import BACKENDS
from benchproofer.smoke import fixtures
from benchproofer.util.fsio import write_text

#: A wrong implementation: pennies only, so 40 cents is forty coins rather than three.
PENNIES = "def impl(cents):\n    return (0, 0, 0, cents)\n"
#: A correct one reached another way.
LOOPED = (
    "def impl(cents):\n"
    "    counts = []\n"
    "    for value in (25, 10, 5):\n"
    "        counts.append(cents // value)\n"
    "        cents = cents % value\n"
    "    return (counts[0], counts[1], counts[2], cents)\n"
)

Answer = Callable[[SessionSpec], dict[str, Any] | None]


class Playing(AgentSession):
    """A session that plays each auditor as the case scripts it, by the auditor's workspace."""

    name = "playing"

    def __init__(self, **lanes: Answer) -> None:
        super().__init__()
        self.lanes = lanes
        self.asked: list[SessionSpec] = []

    def run(self, spec: SessionSpec) -> StepOutcome:
        self.asked.append(spec)
        answer = self.lanes.get(spec.cwd.name)
        payload = answer(spec) if answer is not None else None
        return StepOutcome(text="", payload=payload, turns=3, tool_uses=5)

    def lane(self, name: str) -> SessionSpec:
        return next(spec for spec in self.asked if spec.cwd.name == name)


@pytest.fixture
def falsifier() -> Backend:
    return BACKENDS.get("falsifier")


def reviewers(session: AgentSession, backend: Backend, settings: Settings) -> Reviewers:
    provider = SimpleNamespace(name="scripted", config=SimpleNamespace(model="reviewing-model"))
    return Reviewers(
        session=session,
        provider=provider,  # type: ignore[arg-type]
        backend=backend,
        settings=settings.model_copy(update={"audit_attacks": 1, "audit_controls": 1}),
    )


def writes(solution: str, **files: str) -> Callable[[Path], None]:
    """Write each named file into a workspace's scratch, as the shipped file with this body."""

    def write(workspace: Path) -> None:
        for name, body in files.items():
            write_text(
                workspace / "scratch" / name, replace_region(solution, "#", "impl", body)
            )

    return write


def attacking(solution: str, **extra: Any) -> Answer:
    """An attack auditor that files one attack and one control."""

    def answer(spec: SessionSpec) -> dict[str, Any]:
        writes(solution, **{"pennies.py": PENNIES, "looped.py": LOOPED})(spec.cwd)
        return {
            "attacks": [{"file": "scratch/pennies.py", "claim": "pennies only"}],
            "controls": [{"file": "scratch/looped.py", "claim": "a loop"}],
            **extra,
        }

    return answer


def judging(verdict: str = "sound", **extra: Any) -> Answer:
    return lambda spec: {"verdict": verdict, "summary": f"{spec.cwd.name} is fine", **extra}


def every_lane(solution: str) -> dict[str, Answer]:
    covered = {
        "behavior": "the fewest coins",
        "tested_by": "the task's test program",
        "covered_by": "assert nickels * 5 + pennies < 10",
    }
    return {
        "attack": attacking(solution),
        "faithfulness": judging(coverage=[covered]),
        "equivalence": judging(operations=[{"kind": "identical", "detail": "the same"}]),
        "disclosure": judging(),
    }


# ---- the workspaces ----------------------------------------------------


def test_each_auditor_is_asked_in_a_workspace_of_its_own(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change)

    # No fuzz auditor: the sound fixture assumes nothing.
    assert [spec.cwd.name for spec in session.asked] == [
        "attack",
        "faithfulness",
        "equivalence",
        "disclosure",
    ]
    attack = session.lane("attack")
    assert attack.tools == EDIT
    assert (attack.cwd / "bundles").is_dir()
    assert (attack.cwd / "repository").is_dir()
    assert os.access(attack.cwd / "tools", os.X_OK)
    assert "benchproofer.audit.tools" in (attack.cwd / "tools").read_text()
    # Every auditor with tools is told of them in the one shared description.
    for spec in session.asked:
        told = " ".join(spec.prompt.split())
        assert ("FILE is sent alone" in told) == (spec.cwd.name != "disclosure"), spec.cwd.name
        assert "runs a Python program where the benchmark's tests run, against" not in told
        # An auditor without a shell is not told it has one.
        assert "run commands" not in spec.system


def test_the_disclosure_auditor_reads_blind(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """What a solver can recover is not a question a reader of the answer can answer.

    What the solver does have is in the workspace: the statement and the code before the fix,
    so that content that code already has is not read as the specification handing it over.
    """
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change)

    blind = session.lane("disclosure")
    assert blind.tools == READ_ONLY
    assert sorted(path.name for path in blind.cwd.iterdir()) == [
        "before.md",
        "scratch",
        "spec.txt",
        "statement.md",
    ]
    assert (blind.cwd / "spec.txt").read_text() == falsifier.spec_view(sound.solution())
    assert (blind.cwd / "before.md").read_text() == material.pre_fix_block(coin_change)
    assert "the code before the fix already has discloses nothing" in blind.prompt


#: A module the golden patch changes one line of, far below the function's first line.
LONG_BEFORE = (
    "def make_change(cents, coins=(25, 10, 5, 1)):\n"
    + "".join(f"    step_{index} = {index}\n" for index in range(12))
    + "    return tuple(cents // coin for coin in coins)\n"
)
LONG_PATCH = (
    "diff --git a/change.py b/change.py\n--- a/change.py\n+++ b/change.py\n"
    "@@ -12,3 +12,3 @@\n     step_10 = 10\n     step_11 = 11\n"
    "-    return tuple(cents // coin for coin in coins)\n"
    "+    return tuple(cents // coin % 100 for coin in coins)\n"
)


class Exporting:
    """An oracle whose environment is the repository as it stood before the fix."""

    def export(self, task: Task, *, into: Path) -> Path:
        write_text(into / "change.py", LONG_BEFORE)
        return into


def test_the_disclosure_auditor_is_shown_each_changed_function_whole_as_it_stood(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """A hunk's few lines of context leave out what the code before the fix already did."""
    task = coin_change.model_copy(
        update={
            "context": coin_change.context.model_copy(update={"files": ()}),
            "reference": coin_change.reference.model_copy(update={"patch": LONG_PATCH}),
        }
    )
    session = Playing(**every_lane(sound.solution()))
    lanes = reviewers(session, falsifier, settings)
    lanes.oracle = Exporting()

    lanes.run(sound, task, ("disclosure",))

    before = (session.lane("disclosure").cwd / "before.md").read_text()
    assert "`make_change`, before the fix, lines 1-14" in before
    assert "def make_change(cents, coins=(25, 10, 5, 1)):" in before
    assert "% 100" not in before


def test_only_the_auditors_that_file_programs_are_given_the_drafting_guidance(
    sound: Bundle,
    tasks: dict[str, Task],
    coin_change: Task,
    settings: Settings,
    falsifier: Backend,
) -> None:
    """An attack or a fuzzer is written for the checker; a judging auditor writes none.

    A judging auditor reads by the review's own rules, the same for every backend, so a
    drafting idiom never becomes a standard the bundle is held to.
    """
    session = Playing(**every_lane(sound.solution()))
    reviewers(session, falsifier, settings).run(sound, coin_change)
    assumed = fixtures.stage(
        fixtures.fixture("safe-join-assumed"), tasks["safe-join"], settings
    )
    reviewers(session, falsifier, settings).run(assumed, tasks["safe-join"], ("fuzz",))

    guidance = falsifier.guidance()
    assert guidance
    assert [spec.cwd.name for spec in session.asked] == ["attack", *JUDGED_ROLES, "fuzz"]
    for spec in session.asked:
        assert (guidance in spec.system) == (spec.cwd.name not in JUDGED_ROLES), spec.cwd.name


def test_only_the_auditors_named_are_asked(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    assert [spec.cwd.name for spec in session.asked] == ["faithfulness"]


# ---- what each auditor is told --------------------------------------------


def test_an_auditor_that_stops_before_submitting_is_asked_for_its_review(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Without a submit call nothing an auditor did is recorded, so another turn asks for it."""
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change)

    for spec in session.asked:
        report = " ".join(spec.report.split())
        assert "Call the submit tool now, from what you already know." in report, spec.cwd.name
        assert "did not finish checking is `uncertain`" in report


def test_a_judging_auditor_is_told_it_hands_over_fields_and_no_file(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Only the attack and fuzz auditors file programs; a judging auditor's schema has none."""
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change)

    for spec in session.asked:
        system = " ".join(spec.system.split())
        judged = spec.cwd.name in JUDGED_ROLES
        assert ("No file of yours is handed over" in system) is judged, spec.cwd.name
        filed = "files you wrote in the scratch directory, named by path" in system
        assert filed is not judged
        assert "write the wrong implementation and hand it over" not in system


def test_every_auditor_that_runs_programs_is_told_how_a_program_runs(
    sound: Bundle,
    tasks: dict[str, Task],
    coin_change: Task,
    settings: Settings,
    falsifier: Backend,
) -> None:
    """Sent alone, without the workspace, set up as the tests are, and stopped at a limit."""
    session = Playing(**every_lane(sound.solution()))
    reviewers(session, falsifier, settings).run(sound, coin_change)
    assumed = fixtures.stage(
        fixtures.fixture("safe-join-assumed"), tasks["safe-join"], settings
    )
    reviewers(session, falsifier, settings).run(assumed, tasks["safe-join"], ("fuzz",))

    for spec in session.asked:
        prompt = " ".join(spec.prompt.split())
        told = all(
            said in prompt
            for said in (
                "`scratch/` included",
                "`django.setup()`",
                "`signal.alarm`",
                "`flush=True`",
            )
        )
        assert told is (spec.cwd.name != "disclosure"), spec.cwd.name


def test_the_attack_and_faithfulness_auditors_are_told_where_the_tests_are(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """`tests/` holds the test patch, which the repository copy does not have applied.

    The attack auditor is also given the rules that say which tests are counted, which its
    system prompt's guidance refers to.
    """
    patch = (
        "diff --git a/tests/test_change.py b/tests/test_change.py\n"
        "--- a/tests/test_change.py\n"
        "+++ b/tests/test_change.py\n"
        "@@ -1,2 +1,4 @@\n"
        " def test_forty():\n"
        "     assert make_change(40) == (1, 1, 1, 0)\n"
        "+def test_nickel():\n"
        "+    assert make_change(5) == (0, 0, 1, 0)\n"
    )
    task = coin_change.model_copy(update={"metadata": {"test_patch": patch}})
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, task, ("attack", "faithfulness"))

    for lane in ("attack", "faithfulness"):
        spec = session.lane(lane)
        prompt = " ".join(spec.prompt.split())
        assert "`tests/tests.patch` is its test patch" in prompt, lane
        assert "`repository/` does not have it applied" in prompt, lane
        assert "The FAIL_TO_PASS tests are these:" in prompt, lane
        assert (spec.cwd / "tests" / "tests.patch").read_text() == patch
    attack = " ".join(session.lane("attack").prompt.split())
    assert " ".join(SHARED.rules("tests").split()) in attack


def test_the_attack_auditor_is_asked_for_no_inputs_and_none_are_recorded(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """`conformance.py` replays inputs in a form of its own, which an auditor cannot know."""
    sound.write_evidence(
        "conformance.log", "benchproofer:compared change.make_change 100 amounts\n"
    )
    session = Playing(attack=attacking(sound.solution()))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))
    write_audit(sound, audit)

    spec = session.lane("attack")
    assert "inputs" not in spec.fields["attacks"]["items"]["properties"]
    assert "`inputs`" not in spec.prompt
    assert not (sound.evidence_dir / "conformance-witnesses.json").exists()


def test_the_attack_auditor_is_told_how_a_control_is_judged(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Through `conformance.py`, or on the checker's acceptance alone: never the tests."""
    session = Playing(attack=attacking(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))

    prompt = " ".join(session.lane("attack").prompt.split())
    assert "A control is not put to the benchmark's tests." in prompt
    assert CITATION in prompt
    assert "rests on the checker's acceptance alone" in prompt
    assert "each a copy of `solution.py` that writes only the regions named below" in prompt


def test_the_fuzz_rules_name_no_one_checker_s_constructs() -> None:
    """The fuzz auditor is asked under every backend, and reads them under its own."""
    rules = audit_prompts.LIBRARY.rules("fuzz")

    for construct in ("Nagini", "@Pure", "Requires", "Ensures", "Exsures"):
        assert construct not in rules
    assert "as a function of its arguments" in " ".join(rules.split())


def test_the_judging_auditors_that_run_candidates_are_told_which_regions_to_write(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change)

    regions = variant.rule(variant.owned(sound.solution(), falsifier))
    for lane in ("faithfulness", "equivalence"):
        assert regions in session.lane(lane).prompt, lane
    assert regions not in session.lane("disclosure").prompt


def test_the_equivalence_auditor_is_told_which_callees_have_a_models_line(
    sound: Bundle,
    tasks: dict[str, Task],
    coin_change: Task,
    settings: Settings,
    falsifier: Backend,
) -> None:
    """A `modeled` row is a call of one of them; any other definition's row is `changed`."""
    session = Playing(equivalence=judging())
    reviewers(session, falsifier, settings).run(sound, coin_change, ("equivalence",))
    assumed = fixtures.stage(
        fixtures.fixture("safe-join-assumed"), tasks["safe-join"], settings
    )
    reviewers(session, falsifier, settings).run(assumed, tasks["safe-join"], ("equivalence",))

    none, some = (" ".join(spec.prompt.split()) for spec in session.asked)
    assert "has no `benchproofer:models` line, so no row is `modeled`" in none
    assert "has a `benchproofer:models` line for these callees" in some
    assert "* `posixpath.normpath`" in some


def test_what_a_judging_auditor_checked_and_found_clean_is_recorded_apart_from_its_findings(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Filed as a finding, it would come back to the next session as one to carry."""
    clean = "the greedy order: ran every amount up to 100 against the fixed code, the same"
    session = Playing(
        equivalence=judging(
            operations=[{"kind": "identical", "detail": "the same"}], checked=[clean, " "]
        )
    )

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("equivalence",))
    write_audit(sound, audit)
    reviewers(session, falsifier, settings).run(sound, coin_change, ("equivalence",))

    (judgment,) = audit.judgments
    assert (judgment.checked, judgment.findings) == ((clean,), ())
    recorded = sound.audit()
    assert recorded is not None
    assert recorded.judgment("equivalence").checked == (clean,)  # type: ignore[union-attr]
    notes = (sound.audit_dir / "notes.md").read_text()
    assert f"Checked and found clean:\n\n- {clean}" in notes
    assert "checked" in session.asked[0].fields
    assert clean not in session.asked[1].prompt


# ---- what is filed -----------------------------------------------------


def test_an_attack_is_filed_from_the_file_the_session_names(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    session = Playing(attack=attacking(sound.solution()))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))

    assert [(item.id, item.kind, item.claim) for item in audit.submissions] == [
        ("attack-1", "weakness", "pennies only"),
        ("control-1", "control", "a loop"),
    ]
    assert audit.submissions[0].source == replace_region(sound.solution(), "#", "impl", PENNIES)
    assert audit.examined["attack"] == {
        name: digest
        for name, digest in readings(sound, falsifier).items()
        if name in ("solution:spec", "../task.json")
    }


#: An attack's witness test, and a control's refutation witness, as files a session writes.
WITNESS = "from change import make_change\nassert make_change(40) == (1, 1, 1, 0)\n"
REFUTATION = "example : ¬ property_change_is_the_fewest_coins 40 := by decide\n"


@pytest.mark.parametrize("required", [False, True], ids=["no witness read", "witness required"])
def test_an_attack_s_witness_test_and_a_control_s_refutation_are_filed_with_them(
    required: bool, sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Each from the file the session names; a control's only where a refusal needs a witness.

    The attack auditor is told of both as `./tools try` takes them, and they go on record
    beside the submission, the witness test as a file of its own.
    """
    backend = type("Witnessed", (type(falsifier),), {"witness_required": required})()

    def answer(spec: SessionSpec) -> dict[str, Any]:
        writes(sound.solution(), **{"pennies.py": PENNIES, "looped.py": LOOPED})(spec.cwd)
        write_text(spec.cwd / "scratch" / "witness.py", WITNESS)
        write_text(spec.cwd / "scratch" / "refutation.lean", REFUTATION)
        test = {"test": "scratch/witness.py"}
        return {
            "attacks": [
                {
                    "file": "scratch/pennies.py",
                    "claim": "pennies",
                    "cites": "test_forty",
                    **test,
                }
            ],
            "controls": [
                {
                    "file": "scratch/looped.py",
                    "claim": "a loop",
                    "refutation": "scratch/refutation.lean",
                    **test,
                }
            ],
        }

    session = Playing(attack=answer)
    audit = reviewers(session, backend, settings).run(sound, coin_change, ("attack",))
    write_audit(sound, audit)

    attack, control = audit.submissions
    assert (attack.test, attack.cites) == (WITNESS, "test_forty")
    assert (control.refutation, control.test) == (
        (REFUTATION, WITNESS) if required else ("", "")
    )
    recorded = sound.audit()
    assert recorded is not None
    filed = recorded.submissions[0]
    assert (filed.test, filed.cites) == ("attack-1.test.py", "test_forty")
    assert sound.submission_test(filed) == WITNESS
    assert recorded.submissions[1].refutation.strip() == (
        REFUTATION.strip() if required else ""
    )
    lane = session.lane("attack")
    assert "test" in lane.fields["attacks"]["items"]["properties"]
    assert ("refutation" in lane.fields["controls"]["items"]["properties"]) is required
    prompt = " ".join(lane.prompt.split())
    assert "## Witness tests" in prompt and "with `--cites`" in prompt
    assert ("`./tools try` with `--refutation`" in prompt) is required


def test_a_file_that_cannot_be_evidence_is_not_filed(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Another specification, a file outside the workspace, the shipped implementation."""
    solution = sound.solution()
    shipped = solution

    def answer(spec: SessionSpec) -> dict[str, Any]:
        write_text(spec.cwd / "scratch" / "other.py", solution.replace("pennies < 5", "True"))
        write_text(spec.cwd / "scratch" / "shipped.py", shipped)
        return {
            "attacks": [
                {"file": "scratch/other.py", "claim": "a weaker spec"},
                {"file": "/etc/hostname", "claim": "outside"},
                {"file": "scratch/shipped.py", "claim": "the answer itself"},
            ],
            "controls": [],
        }

    audit = reviewers(Playing(attack=answer), falsifier, settings).run(
        sound, coin_change, ("attack",)
    )

    assert audit.submissions == ()
    said = " ".join(audit.notes)
    assert "a specification other than the shipped one" in said
    assert "not a file in the workspace" in said
    assert "repeats an implementation already on record" in said


def filed_before(
    bundle: Bundle,
    backend: Backend,
    *,
    stands: bool,
    defects: tuple[Defect, ...] = (),
    attacks: bool = True,
) -> Submission:
    """Record one attack an earlier review filed, against the specification as it stands.

    Or, unless ``stands``, against one a repair has since replaced: what the attack auditor
    read then is recorded with a digest the specification no longer has. ``defects`` are
    what that auditor showed beside it; without ``attacks`` they are all it filed.
    """
    earlier = Submission(id="attack-3", kind="weakness", file="attack-3.py", claim="old")
    digests = readings(bundle, backend)
    read = {name: digests[name] for name in (SPEC, "../task.json")}
    if not stands:
        read[SPEC] = "an earlier digest"
    bundle.save_audit(
        Review(
            reviewer="scripted:reviewing-model",
            submissions=(earlier,) if attacks else (),
            defects=defects,
            examined={"attack": read},
        ),
        {
            "attack-3.py": replace_region(
                bundle.solution(), "#", "impl", "def impl(c):\n    return (c, 0, 0, 0)\n"
            )
        }
        if attacks
        else {},
    )
    return earlier


def test_a_re_review_of_the_same_specification_numbers_past_the_ids_and_keeps_them(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """What the auditor filed stands while the specification it attacked does."""
    filed_before(sound, falsifier, stands=True)
    session = Playing(attack=attacking(sound.solution()))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))

    assert [item.id for item in audit.submissions] == ["attack-4", "control-1"]
    assert [item.id for item in audit.review().submissions] == [
        "attack-3",
        "attack-4",
        "control-1",
    ]
    prompt = session.lane("attack").prompt
    assert "## Already on record" in prompt and "audit/attack-3.py" in prompt


def test_after_a_repair_changed_the_specification_a_re_review_replaces_what_it_filed(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """The earlier attacks are not run again; the auditor is shown each to write again.

    Each comes with what the gates ruled and the repair's entry for it, so the auditor can
    tell a weakness to write again from one the repair showed was not a defect.
    """
    filed_before(sound, falsifier, stands=False)
    ruled = "checker: verified; correctness: wrong (a weakness of the specification)"
    completeness = Verdict(
        gate="audit.spec_completeness",
        status=Status.FAIL,
        details={"rulings": {"attack-3": ruled}},
    )
    manifest = sound.manifest()
    manifest.verdicts = {**manifest.verdicts, completeness.gate: completeness}
    briefed = "`audit.spec_completeness` (fail): accepts implementation(s): attack-3"
    manifest.provenance = {
        **manifest.provenance,
        "repairs": [
            {
                "round": 1,
                "session": {
                    "briefed": {"16": briefed},
                    "findings": [
                        {"finding": "16", "outcome": "resolved", "witness": "pinned c"}
                    ],
                    "summary": "stated what the fix returns",
                },
            }
        ],
    }
    sound.save_manifest(manifest)
    session = Playing(attack=attacking(sound.solution()))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))

    assert [item.id for item in audit.review().submissions] == ["attack-4", "control-1"]
    prompt = " ".join(session.lane("attack").prompt.split())
    assert "First write again each counterexample the earlier review found" in prompt
    assert (
        f"`audit/attack-3.py` (weakness, `attack-3`): old * The gates ruled: {ruled}" in prompt
    )
    assert "The repair resolved it: pinned c" in prompt
    assert "The repair since then said: stated what the fix returns" in prompt


def test_an_auditor_that_filed_nothing_leaves_what_was_on_record(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Even against a specification since replaced: the gates then set each aside."""
    earlier = filed_before(sound, falsifier, stands=False)

    audit = reviewers(Playing(), falsifier, settings).run(sound, coin_change, ("attack",))

    assert audit.review().submissions == (earlier,)


def test_a_session_that_could_not_start_is_the_tools_failure_not_a_refusal(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """A review recorded as though the auditor reported would be read as an auditor that did."""

    class Unreachable(Playing):
        def run(self, spec: SessionSpec) -> StepOutcome:
            raise ProviderError("the session could not be started")

    with pytest.raises(ProviderError):
        reviewers(Unreachable(), falsifier, settings).run(sound, coin_change, ("faithfulness",))


def test_a_judging_auditor_s_copy_keeps_what_the_gates_noted_and_drops_the_review_s_verdicts(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """The conformance gate's note reaches the equivalence auditor, not the faithfulness one.

    The equivalence auditor's rules say what the repository side of `conformance.py` must
    call, which the note is evidence about; the faithfulness auditor judges coverage only.
    Both copies keep the gate's verdict, and an earlier review's own verdict is taken out
    of them, since the auditor could copy it.
    """
    note = "conformance.py reports the same agreement against the task's base commit"
    sound.record(
        [
            Verdict(
                gate="impl.conformance", status=Status.PASS, details={"undiscriminating": note}
            ),
            Verdict(gate="audit.faithfulness", status=Status.PASS, summary="it is faithful"),
        ]
    )
    seen: dict[str, dict[str, Verdict]] = {}

    def copied(spec: SessionSpec) -> dict[str, Any]:
        seen[spec.cwd.name] = (
            Bundle(next((spec.cwd / "bundles").rglob("manifest.json")).parent)
            .manifest()
            .verdicts
        )
        return judging()(spec)

    session = Playing(faithfulness=copied, equivalence=copied)
    reviewers(session, falsifier, settings).run(
        sound, coin_change, ("faithfulness", "equivalence")
    )

    for lane in ("faithfulness", "equivalence"):
        assert seen[lane]["impl.conformance"].details["undiscriminating"] == note
        assert "audit.faithfulness" not in seen[lane]
    equivalence = " ".join(session.lane("equivalence").prompt.split())
    assert f"noted: {note}." in equivalence
    assert "the repository side of `conformance.py` must call the repository's code" in (
        equivalence
    )
    faithfulness = " ".join(session.lane("faithfulness").prompt.split())
    assert note not in faithfulness
    assert "against the task's base commit" not in faithfulness


def test_a_judgment_carries_its_table_and_what_its_role_read(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    session = Playing(**every_lane(sound.solution()))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change)

    faithful = next(item for item in audit.judgments if item.role == "faithfulness")
    assert [row.covered_by for row in faithful.coverage] == [
        "assert nickels * 5 + pennies < 10"
    ]
    digests = readings(sound, falsifier)
    assert faithful.reads == {
        name: digests[name] for name in ROLE_READS["faithfulness"] if name in digests
    }
    equivalent = next(item for item in audit.judgments if item.role == "equivalence")
    assert [item.kind for item in equivalent.operations] == ["identical"]


def test_a_coverage_row_is_its_behavior_its_test_and_its_obligation(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """A row needs an obligation when a test names it, whatever the fix does there.

    So the auditor is asked for no `kind`, and one it sends anyway is not kept.
    """
    rows = [
        {"behavior": "the fewest coins", "tested_by": "t", "covered_by": "", "kind": "changed"},
        {"behavior": "a name", "tested_by": "t", "covered_by": "", "kind": "interface"},
    ]
    session = Playing(faithfulness=judging(coverage=rows))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    (faithful,) = audit.judgments
    assert [(row.behavior, row.required, row.uncovered) for row in faithful.coverage] == [
        ("the fewest coins", True, True),
        ("a name", True, True),
    ]
    schema = session.lane("faithfulness").fields["coverage"]["items"]
    assert "kind" not in schema["properties"]
    prompt = " ".join(session.lane("faithfulness").prompt.split())
    assert "a test naming it needs an obligation either way" in prompt
    assert "`plumbing`" not in prompt


def test_an_operation_is_filed_under_the_kind_it_names_or_as_changed(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """A kind Benchproofer does not know is `changed`.

    `unchanged` is behavior the fix leaves as it was, compared in the one environment the
    tests run in; `unbridged` differs only outside `correspondence.md`'s list, which the auditor
    is told to check rather than trust.
    """
    operations = [
        {"kind": "identical", "detail": "the same greedy pass"},
        {"kind": "unchanged", "detail": "the currency is not read, as before the fix"},
        {"kind": "unbridged", "detail": "`getD` apart from a key set to None"},
        {"kind": "harmless", "detail": "it also rejects a negative amount"},
    ]
    session = Playing(equivalence=judging(operations=operations))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("equivalence",))

    (equivalent,) = audit.judgments
    assert [item.kind for item in equivalent.operations] == [
        "identical",
        "unchanged",
        "unbridged",
        "changed",
    ]
    schema = session.lane("equivalence").fields["operations"]["items"]
    assert {"unchanged", "unbridged"} <= set(schema["properties"]["kind"]["enum"])
    prompt = " ".join(session.lane("equivalence").prompt.split())
    assert "`unchanged`" in prompt
    assert " ".join(SHARED.rules("environment").split()) in prompt
    assert "under `Outside the bridge`" in prompt
    assert "An entry is checked rather than trusted" in prompt
    # An input on which the fixed function runs only what the golden patch leaves as it was
    # is the third kind, traced through the function before the fix and after it.
    assert (
        "for the third, trace one input the entry names through the function before" in prompt
    )
    # One the model leaves out, which a test hands the changed function and a changed line
    # runs on, is not set aside as the fix leaving it alone.
    assert "Nor is behavior on an input the model's domain has to admit" in prompt
    assert " ".join(SHARED.rules("domain").split()) in prompt
    assert "Nor is a change that widens the domain" in prompt


def test_the_disclosure_auditor_is_told_what_is_not_a_finding_in_it(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Transcribable is no construct that hands a method over."""
    session = Playing(**every_lane(sound.solution()))

    reviewers(session, falsifier, settings).run(sound, coin_change, ("disclosure",))

    disclosure = " ".join(session.lane("disclosure").prompt.split())
    for construct in ("loop", "intermediate", "table", "literal", "oracle"):
        assert f"`{construct}:`" in disclosure
    assert "can be copied into code is not a finding on its own" in disclosure


def test_the_equivalence_session_is_shown_what_repairs_changed_since_drafting(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    narrowed_since_drafting(sound, falsifier)
    session = Playing(equivalence=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("equivalence",))

    asked = session.lane("equivalence").prompt
    assert "## What repairs changed since drafting" in asked
    assert "+    assume(cents < 100)" in asked
    assert "+* an amount of a dollar or more" in asked


def test_an_auditor_that_submitted_nothing_keeps_what_it_filed_before(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """The gate then reports it stale or missing, which is the accurate answer."""
    before = Judgment(role="faithfulness", verdict="unsound", summary="it omits nickels")
    sound.save_audit(Review(reviewer="scripted:reviewing-model", judgments=(before,)), {})

    audit = reviewers(Playing(), falsifier, settings).run(sound, coin_change, ("faithfulness",))

    assert audit.judgments == ()
    assert audit.kept_judgments == (before,)
    assert any("ended without submitting" in note for note in audit.notes)
    assert [record["lane"] for record in audit.sessions] == ["faithfulness"]


def test_a_finding_on_record_is_put_to_the_next_session_of_its_auditor(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """With no repair since, nothing has answered it, so it stays open."""
    before = Judgment(
        role="faithfulness",
        verdict="unsound",
        summary="it omits nickels",
        findings=("40 cents is answered with no nickel",),
    )
    sound.save_audit(Review(reviewer="scripted:reviewing-model", judgments=(before,)), {})
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    asked = session.lane("faithfulness")
    assert (
        "* 40 cents is answered with no nickel\n  * The repair's report says nothing of it."
    ) in asked.prompt
    assert "stays open until the specification addresses it" in asked.prompt
    # The finding is put in the prompt; the verdict beside it is not left in the copy.
    assert not [path for path in (asked.cwd / "bundles").rglob("audit") if path.is_dir()]


def test_an_auditor_is_shown_the_repair_s_entry_for_each_finding_and_judges_a_decline(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """A finding the repair declined with evidence is the auditor's to withdraw or keep."""
    found = ("40 cents has no nickel", "99 cents has 4 pennies", "1 cent is refused")
    before = Judgment(
        role="faithfulness", verdict="unsound", summary="it omits nickels", findings=found
    )
    sound.save_audit(Review(reviewer="scripted:reviewing-model", judgments=(before,)), {})
    manifest = sound.manifest()
    manifest.provenance["repairs"] = [
        {
            "session": {
                "summary": "The contract now states the nickel count.",
                "briefed": {f"12.{index}": text for index, text in enumerate(found, 1)},
                "findings": [
                    {
                        "finding": "12.1",
                        "outcome": "resolved",
                        "witness": "40 cents, one nickel",
                    },
                    {
                        "finding": "12.2",
                        "outcome": "not a defect",
                        "witness": "99 cents is 4 pennies in the fixed code " + "x" * 1_500,
                    },
                ],
            }
        }
    ]
    sound.save_manifest(manifest)
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    asked = session.lane("faithfulness").prompt
    assert "* 40 cents has no nickel\n  * The repair resolved it: 40 cents, one nickel" in asked
    assert (
        "* 99 cents has 4 pennies\n  * The repair found it no defect and changed nothing for "
        "it: 99 cents is 4 pennies in the fixed code " + "x" * 1_500
    ) in asked
    assert "* 1 cent is refused\n  * The repair's report says nothing of it." in asked
    assert "The repair since then said: The contract now states the nickel count." in asked
    told = " ".join(asked.split())
    assert "if it holds, withdraw the finding; if it does not, keep the finding" in told
    assert "neither resolved nor declined stays open" in told


def test_the_faithfulness_auditor_is_shown_what_the_review_found_in_earlier_rounds(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """The review's gates only, one line per finding, and what to do with one it reverses."""
    strict = Verdict(
        gate="audit.faithfulness",
        status=Status.FAIL,
        summary="It pins the nickel count. The task leaves it open.",
        details={"findings": ["Demands more than the task: 40 cents. More detail."]},
    )
    refused = Verdict(gate="spec.verifies", status=Status.FAIL, summary="The checker refused.")
    earlier = sound.manifest().model_copy(
        update={"verdicts": {verdict.gate: verdict for verdict in (strict, refused)}}
    )
    write_text(
        rounds.directory(sound, settings.cache_dir) / "00" / "manifest.json",
        earlier.model_dump_json(),
    )
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    asked = session.lane("faithfulness").prompt
    assert (
        "* Round 00:\n"
        "  * `audit.faithfulness` (fail): It pins the nickel count.\n"
        "    * Demands more than the task: 40 cents.\n"
    ) in asked
    assert "The checker refused." not in asked and "More detail." not in asked
    assert "decides which is right against the fixed code" in " ".join(asked.split())


@pytest.mark.parametrize("provenance", ["transliterated", "direct"])
def test_the_equivalence_auditor_checks_a_port_of_the_implementation_line_by_line(
    provenance: str, sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Only where `conformance.py` compares a translation, which no gate checks.

    The faithfulness auditor, which judges what the specification covers, is not asked.
    """
    compared = Verdict(
        gate="impl.conformance", status=Status.PASS, details={"provenance": provenance}
    )
    sound.record([compared])
    session = Playing(faithfulness=judging(), equivalence=judging())

    reviewers(session, falsifier, settings).run(
        sound, coin_change, ("faithfulness", "equivalence")
    )

    asked = " ".join(session.lane("equivalence").prompt.split())
    assert ("## The port in `conformance.py`" in asked) is (provenance == "transliterated")
    if provenance == "transliterated":
        assert "Check the port line by line against the implementation" in asked
        assert "values only the checker has" in asked
    assert "## The port in" not in session.lane("faithfulness").prompt


def test_the_equivalence_auditor_is_shown_what_a_repair_changed_in_the_programs(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Against the bundle as the last round judged it, and only where the programs changed.

    The faithfulness auditor is not shown it: whether a program compares less is no question
    of what the specification covers.
    """
    write_text(sound.root / "axioms.py", "print('benchproofer:grounded c')\n")
    last = rounds.directory(sound, settings.cache_dir) / "00"
    shutil.copytree(sound.root, last)
    write_text(last / "manifest.json", sound.manifest().model_dump_json())
    write_text(sound.conformance_path, sound.conformance() + "INPUTS = 10\n")
    session = Playing(faithfulness=judging(), equivalence=judging())

    reviewers(session, falsifier, settings).run(
        sound, coin_change, ("faithfulness", "equivalence")
    )

    block = session.lane("equivalence").prompt.split("## What changed in `conformance.py`")[1]
    assert "+++ now/conformance.py" in block and "+INPUTS = 10" in block
    assert "now/axioms.py" not in block
    assert "## What changed in" not in session.lane("faithfulness").prompt
    shutil.copy(sound.conformance_path, last / "conformance.py")
    again = Playing(equivalence=judging())
    reviewers(again, falsifier, settings).run(sound, coin_change, ("equivalence",))
    assert "## What changed in" not in again.lane("equivalence").prompt


def test_a_fuzzer_is_filed_against_a_callee_the_specification_assumes(
    tasks: dict[str, Task], settings: Settings, falsifier: Backend
) -> None:
    """And against the assumption as it stands, so it is kept until that changes."""
    bundle = fixtures.stage(fixtures.fixture("safe-join-assumed"), tasks["safe-join"], settings)

    def answer(spec: SessionSpec) -> dict[str, Any]:
        write_text(spec.cwd / "scratch" / "fuzz.py", "print('grounded posixpath.normpath')\n")
        return {
            "fuzzers": [
                {"callee": "posixpath.normpath", "file": "scratch/fuzz.py", "claim": "dots"},
                {"callee": "os.getcwd", "file": "scratch/fuzz.py", "claim": "not assumed"},
            ]
        }

    session = Playing(fuzz=answer)
    audit = reviewers(session, falsifier, settings).run(bundle, tasks["safe-join"], ("fuzz",))

    prompt = " ".join(session.lane("fuzz").prompt.split())
    assert "posixpath.normpath" in prompt
    # What a disagreement has to be to count: at an argument a call site can pass, with a
    # purity claim refuted by two calls that disagree, and quoting the line it breaks.
    assert "An argument no call site can pass" in prompt
    assert "a cache or `sys.modules` growing" in prompt
    assert "quotes, as written, the line of" in prompt
    assert [(item.id, item.callee) for item in audit.fuzzers] == [
        ("fuzz-1", "posixpath.normpath")
    ]
    assert audit.fuzzers[0].against == axioms_digest(bundle.solution(), falsifier)
    assert any("does not assume" in note for note in audit.notes)

    write_audit(bundle, audit)
    assert "fuzz" not in due(bundle, falsifier)


def test_the_equivalence_auditor_alone_is_asked_whether_the_golden_patch_changes_a_callee(
    tasks: dict[str, Task], settings: Settings, falsifier: Backend
) -> None:
    """It reads the golden patch operation by operation, and behavior decides.

    The fuzz auditor, which runs programs against the fixed tree, is not asked.
    """
    task = tasks["safe-join"]
    bundle = fixtures.stage(fixtures.fixture("safe-join-assumed"), task, settings)

    def fuzzed(spec: SessionSpec) -> dict[str, Any]:
        write_text(spec.cwd / "scratch" / "fuzz.py", "print('grounded posixpath.normpath')\n")
        return {"fuzzers": [{"callee": "posixpath.normpath", "file": "scratch/fuzz.py"}]}

    session = Playing(fuzz=fuzzed, equivalence=every_lane(bundle.solution())["equivalence"])

    audit = reviewers(session, falsifier, settings).run(bundle, task, ("fuzz", "equivalence"))

    asked = " ".join(session.lane("equivalence").prompt.split())
    assert "Never assume the function under spec or an operation the golden patch changes" in (
        asked
    )
    assert "Behavior decides whether the golden patch changes a callee" in asked
    assert "the same function bound under a new module or name" in asked
    fuzz = session.lane("fuzz")
    assert "changed" not in fuzz.fields["fuzzers"]["items"]["properties"]
    assert "golden patch changes its behaviour" not in fuzz.prompt
    assert [fuzzer.callee for fuzzer in audit.review().fuzzers] == ["posixpath.normpath"]


def _timeless(prompt: str) -> str:
    """The prompt without the line giving the session's start and stop times."""
    return re.sub(r"This session started at .*? minutes later;", "", prompt)


def test_the_auditors_that_state_the_rule_for_callees_are_shown_the_callees_the_rounds_list(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """The equivalence and faithfulness auditors, only where this run's rounds list a callee.

    With none listed, the equivalence prompt is the one a bundle with no rounds gets: the rule
    for callees alone. With one listed, both are shown it with its evidence and the rule for
    taking its result as an input, and the equivalence auditor what makes such an input
    `unsound`.
    """
    history = rounds.directory(sound, settings.cache_dir)
    alone = Playing(equivalence=judging())
    reviewers(alone, falsifier, settings).run(sound, coin_change, ("equivalence",))
    kept_round(history, "00", sound, refuted("os.cpu_count"))
    once = Playing(faithfulness=judging(), equivalence=judging())
    reviewers(once, falsifier, settings).run(
        sound, coin_change, ("faithfulness", "equivalence")
    )
    kept_round(history, "01", sound, refuted("os.cpu_count"), repairs=1)
    twice = Playing(faithfulness=judging(), equivalence=judging())
    reviewers(twice, falsifier, settings).run(
        sound, coin_change, ("faithfulness", "equivalence")
    )

    rule = " ".join(SHARED.rules("callee").split())
    assert _timeless(once.lane("equivalence").prompt) == _timeless(
        alone.lane("equivalence").prompt
    )
    for lane in ("faithfulness", "equivalence"):
        shut = " ".join(once.lane(lane).prompt.split())
        assert rule in shut and LISTED not in shut and "input of the model" not in shut
        asked = " ".join(twice.lane(lane).prompt.split())
        assert rule in asked
        assert (
            f"{LISTED} Each callee below was first stated" in asked
            and "* `os.cpu_count` * round 00: `audit.axiom_soundness` (the axiom-soundness "
            "gate) refuted it:"
            in asked
            and "* round 01: `audit.axiom_soundness`" in asked
        )
        assert "The model states each such call as an output" in asked
        assert "`conformance.py` compares them with the arguments" in asked
    equivalence = " ".join(twice.lane("equivalence").prompt.split())
    assert (
        "An input holding the result of a callee the list does not name is a finding, with the "
        "verdict `unsound`, and so is an input that breaks a condition, conditions 1 and 4 "
        "above all."
    ) in equivalence
    assert (
        "A callee's result the model takes as a parameter is not an `axiom`, and where "
        "nothing below allows it, its row is `changed`."
    ) in equivalence


def test_the_notes_say_whose_measurement_each_auditor_s_number_is(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """An auditor's count is its own scratch program's, not the bundle's `conformance.py`'s.

    The notes are what a reader of the bundle reads about the review, so a draw count in an
    auditor's summary read as the shipped program's makes the bundle look better evidenced.
    """
    session = Playing(
        **{
            **every_lane(sound.solution()),
            "equivalence": judging(
                summary="the same over 1,183,972 inputs",
                operations=[{"kind": "identical", "detail": "the same"}],
            ),
        }
    )
    audit = reviewers(session, falsifier, settings).run(sound, coin_change)

    write_audit(sound, audit)

    notes = (sound.audit_dir / "notes.md").read_text()
    assert "a count below is that auditor's scratch run" in " ".join(notes.split())
    assert "### equivalence: sound" in notes
    assert "the same over 1,183,972 inputs" in notes


# ---- which auditors are due -----------------------------------------------


def reviewed_by_sessions(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> Audit:
    audit = reviewers(Playing(**every_lane(sound.solution())), falsifier, settings).run(
        sound, coin_change
    )
    write_audit(sound, audit)
    return audit


def test_every_auditor_is_due_for_a_bundle_nobody_reviewed(
    sound: Bundle, falsifier: Backend
) -> None:
    assert due(sound, falsifier) == tuple(lane for lane in LANES if lane != "validation")


def test_no_auditor_is_due_while_the_review_describes_the_bundle(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    reviewed_by_sessions(sound, coin_change, settings, falsifier)

    assert due(sound, falsifier) == ()


def test_a_change_to_the_specification_makes_every_auditor_that_read_it_due(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    reviewed_by_sessions(sound, coin_change, settings, falsifier)
    write_text(sound.solution_path, sound.solution().replace("pennies < 5", "pennies <= 4"))

    assert due(sound, falsifier) == ("attack", "faithfulness", "equivalence", "disclosure")


def test_a_change_to_the_implementation_alone_makes_only_equivalence_due(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    reviewed_by_sessions(sound, coin_change, settings, falsifier)
    write_text(sound.solution_path, replace_region(sound.solution(), "#", "impl", LOOPED))

    assert due(sound, falsifier) == ("equivalence",)


def left_open(bundle: Bundle, *names: str) -> None:
    """Record a completeness verdict listing ``names`` as attacks without a ruling."""
    bundle.record(
        [
            Verdict(
                gate="audit.spec_completeness",
                status=Status.SKIP,
                skip_reason=SkipReason.INCONCLUSIVE,
                details={
                    UNRULED: dict.fromkeys(
                        names,
                        "the checker accepts it, and the benchmark's tests do not reject it; "
                        "its equivalent patch resolves the task",
                    )
                },
            )
        ]
    )


def validating(**ruling: str) -> Answer:
    """An attack validation auditor that rules on one attack or control."""
    return lambda spec: {"rulings": [ruling]}


def test_the_attack_validation_auditor_is_due_for_cases_the_gates_leave_without_a_ruling(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """Not while the attack auditor is due: the gates have yet to run what it will file."""
    reviewed_by_sessions(sound, coin_change, settings, falsifier)
    left_open(sound, "attack-1")

    assert due(sound, falsifier) == ("validation",)

    write_text(sound.solution_path, sound.solution().replace("pennies < 5", "pennies <= 4"))
    assert "validation" not in due(sound, falsifier)


def test_the_attack_validation_auditor_is_shown_each_case_with_what_the_gates_found(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """In a copy of the bundle that keeps the review, with the statement and the coverage table.

    Its ruling is recorded with what it was reached from, and counts the times it was asked
    about the attack with those files as they are; one that ruled on nothing was asked all the
    same.
    """
    reviewed_by_sessions(sound, coin_change, settings, falsifier)
    left_open(sound, "attack-1")
    session = Playing(
        validation=validating(
            id="attack-1", ruling="succeeds", input="make_change(40)", rests_on="test_forty"
        )
    )

    first = reviewers(session, falsifier, settings).run(sound, coin_change, ("validation",))
    write_audit(sound, first)
    silent = reviewers(Playing(), falsifier, settings).run(sound, coin_change, ("validation",))

    lane = session.lane("validation")
    prompt = " ".join(lane.prompt.split())
    assert lane.tools == EDIT
    assert (
        "### `attack-1`, filed as a wrong implementation the specification should refute"
        in (prompt)
    )
    assert "What the gates established: the checker accepts it, and the benchmark's tests" in (
        prompt
    )
    assert "The attack auditor's claim: pennies only" in prompt
    assert "| the fewest coins | the task's test program |" in prompt
    copy = next(path for path in (lane.cwd / "bundles").glob("*/*/*") if path.is_dir())
    assert (copy / "audit" / "attack-1.py").is_file()
    assert (lane.cwd / "statement.md").read_text() == coin_change.statement
    assert list(lane.fields) == ["rulings"]
    [ruling] = first.rulings
    assert (ruling.id, ruling.ruling, ruling.asked) == ("attack-1", "succeeds", 1)
    assert set(ruling.reads) == {SPEC_UNCOMMENTED, IMPL, "audit/attack-1.py"}
    [again] = silent.rulings
    assert (again.ruling, again.asked) == ("", 2)


#: From the rule on what a witness test's citation asks for, told to both auditors.
CITATION = "A sentence of the statement asks only for what it states."


def test_the_attack_validation_auditor_is_shown_a_witness_test_with_its_file_and_both_runs(
    sound: Bundle, coin_change: Task, settings: Settings, falsifier: Backend
) -> None:
    """With what it cites; a ruling on it is recorded with the citation it was reached from."""

    def witnessing(spec: SessionSpec) -> dict[str, Any]:
        writes(sound.solution(), **{"pennies.py": PENNIES})(spec.cwd)
        write_text(
            spec.cwd / "scratch" / "witness.py", "assert make_change(40) == (1, 1, 1, 0)\n"
        )
        attack = {"file": "scratch/pennies.py", "claim": "pennies only"}
        return {"attacks": [{**attack, "test": "scratch/witness.py", "cites": "test_forty"}]}

    filed = reviewers(Playing(attack=witnessing), falsifier, settings).run(
        sound, coin_change, ("attack",)
    )
    write_audit(sound, filed)
    runs = (
        'its witness test, which cites "test_forty", passes on the fixed code '
        "(witness-attack-1 exited 0) and fails with its equivalent patch in place of the "
        "golden patch (witness-attack-1-patched exited 1: AssertionError)"
    )
    sound.record(
        [
            Verdict(
                gate="audit.spec_completeness",
                status=Status.SKIP,
                skip_reason=SkipReason.INCONCLUSIVE,
                details={UNRULED: {"attack-1": f"the checker accepts it; {runs}"}},
            )
        ]
    )
    session = Playing(
        validation=validating(
            id="attack-1", ruling="fails", input="make_change(40)", rests_on="test_forty"
        )
    )

    ruled = reviewers(session, falsifier, settings).run(sound, coin_change, ("validation",))

    prompt = " ".join(session.lane("validation").prompt.split())
    assert '/audit/attack-1.test.py`, which cites "test_forty"' in prompt
    assert CITATION in prompt
    assert f"What the gates established: the checker accepts it; {runs}" in prompt
    [ruling] = ruled.rulings
    assert ruling.reads[CITES] and "audit/attack-1.test.py" in ruling.reads


#: Wrong another way: nickels and pennies only.
NICKELS = "def impl(cents):\n    return (0, 0, cents // 5, cents % 5)\n"


def test_a_review_asking_every_auditor_has_the_validation_auditor_rule_on_what_it_filed(
    sound: Bundle,
    coin_change: Task,
    settings: Settings,
    falsifier: Backend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """As `benchproofer audit --again` asks them: last, once the gates ran what was filed.

    Asked beside the attack auditor, it would see only the attacks and controls listed before
    the attack auditor filed anything, so those of this review would get no ruling.
    """
    reviewed_by_sessions(sound, coin_change, settings, falsifier)

    def attacking_again(spec: SessionSpec) -> dict[str, Any]:
        writes(sound.solution(), **{"nickels.py": NICKELS})(spec.cwd)
        return {"attacks": [{"file": "scratch/nickels.py", "claim": "nickels only"}]}

    session = Playing(
        **{**every_lane(sound.solution()), "attack": attacking_again},
        validation=validating(
            id="attack-2", ruling="succeeds", input="make_change(40)", rests_on="test_forty"
        ),
    )
    monkeypatch.setattr(reviewing, "require_session", lambda *_: session)
    monkeypatch.setattr(
        reviewing, "adjudicate", lambda bundle, **_: left_open(bundle, "attack-2")
    )
    provider = SimpleNamespace(name="scripted", config=SimpleNamespace(model="reviewing-model"))

    result = reviewing.review(
        sound,
        backend=falsifier,
        provider=provider,  # type: ignore[arg-type]
        settings=settings,
        again=LANES,
    )

    asked = [spec.cwd.name for spec in session.asked]
    assert asked == ["attack", "faithfulness", "equivalence", "disclosure", "validation"]
    assert (
        "### `attack-2`, filed as a wrong implementation" in session.lane("validation").prompt
    )
    assert result is not None
    assert [item.id for item in result.audit.submissions] == ["attack-2"]
    assert [(item.id, item.ruling) for item in result.audit.rulings] == [
        ("attack-2", "succeeds")
    ]
    assert [entry["lane"] for entry in result.audit.sessions] == asked
    recorded = sound.audit()
    assert recorded is not None and [item.id for item in recorded.rulings] == ["attack-2"]


def test_the_faithfulness_auditor_reads_the_fix_itself(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """What the fix changes is put in front of the auditor, not left for it to infer."""
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    asked = session.lane("faithfulness").prompt
    assert coin_change.reference.patch.strip().splitlines()[-1] in asked
    assert " ".join(SHARED.rules("task").split()) in " ".join(asked.split())


def test_the_faithfulness_auditor_is_told_the_functions_the_fix_changes(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """Read off the fix's code, with the rules for what has no row.

    A function the fix only refactors, and inputs on which the fixed function runs only what
    the fix leaves as it was, where neither the FAIL_TO_PASS tests
    nor the PASS_TO_PASS tests the test patch adds or edits check them.
    """
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    asked = session.lane("faithfulness").prompt
    assert "the functions it changes are these" in asked
    assert "* `make_change`" in asked
    assert "unless undoing that refactor fails one" in asked
    flat = " ".join(asked.split())
    assert (
        "runs only what the golden patch leaves as it was, and which neither the FAIL_TO_PASS "
        "tests nor the PASS_TO_PASS tests the test patch adds or edits check, is outside the "
        "table as well"
    ) in flat
    assert "an `Outside the bridge` entry that fails its check excuses neither" in flat


def test_the_attack_auditor_is_asked_for_more_controls_than_must_be_accepted(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """Three controls asked for, one needed: one it cannot get accepted is still filed."""
    session = Playing(attack=attacking(sound.solution()))
    asked = settings.model_copy(update={"audit_controls": 3, "audit_min_controls": 1})
    playing = Reviewers(
        session=session,
        provider=SimpleNamespace(name="scripted", config=SimpleNamespace(model="m")),  # type: ignore[arg-type]
        backend=falsifier,
        settings=asked,
    )

    playing.run(sound, coin_change, ("attack",))

    flat = " ".join(session.lane("attack").prompt.split())
    assert "Write 3 **correct** implementations" in flat
    assert "At least 1 of them must be accepted" in flat
    assert "still filed, as the rules below say, and counts toward the 3" in flat


def test_the_faithfulness_auditor_asks_that_the_domain_admit_what_the_tests_hand_the_fix(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """A PASS_TO_PASS test's inputs included, so that an attack can reach what it checks.

    Leaving a behaviour out of the obligations is not leaving its inputs out of the domain,
    and only an `Outside the bridge` entry of one of its three kinds, each with its check,
    leaves such an input out.
    """
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    flat = " ".join(session.lane("faithfulness").prompt.split())
    assert " ".join(SHARED.rules("domain").split()) in flat
    assert "leaving its inputs out of the domain can be" in flat
    assert "for the first kind, that the repository never has the value there" in flat


def test_the_faithfulness_auditor_is_asked_what_the_pre_fix_implementation_returns(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """On each FAIL_TO_PASS input, except a test that fails before the fix only on a name.

    The same walk names each value the test's assertions compare and the obligation that
    states it.
    """
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, coin_change, ("faithfulness",))

    asked = " ".join(session.lane("faithfulness").prompt.split())
    assert "every value its assertions compare, with the obligation that states each" in asked
    assert "say what the bundle's pre-fix implementation, in `twins/`, returns on that" in asked
    assert "only because it uses a name the golden patch adds" in asked
    assert "a missing behaviour or a wrong exception is not" in asked


def test_the_faithfulness_auditor_is_shown_no_submission(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """It judges what the specification covers, and nothing the attack auditor filed.

    The attacks and controls that cannot be determined by execution are the attack validation
    auditor's, and the attack auditor's defects go to `conformance.py`.
    """
    comparing(sound, "floatformat")
    lanes = every_lane(sound.solution())
    lanes["attack"] = attacking(sound.solution(), defects=[DEFECT])
    session = Playing(**lanes)

    audit = reviewers(session, falsifier, settings).run(sound, coin_change)

    lane = session.lane("faithfulness")
    prompt = " ".join(lane.prompt.split())
    assert "filed as a wrong implementation" not in prompt
    assert "Defects the attack auditor" not in prompt
    assert "try --as attack" not in prompt
    assert not (lane.cwd / "submissions").exists()
    [faithfulness] = [item for item in audit.judgments if item.role == "faithfulness"]
    assert "attacks" not in faithfulness.model_dump()


#: A defect as the attack auditor files it, and the function `conformance.py` compares it on.
DEFECT = {
    "defect": "the specification promises a value where the repository raises",
    "function": "floatformat",
    "input": '("1E+9999",)',
    "repository": "raises InvalidOperation",
    "specification": "promises the string '1E+9999'",
}
#: `DEFECT` as it is filed, its input in the spelling `differential.arguments` keeps.
FILED = Defect(**{**DEFECT, "input": "('1E+9999',)"})


def comparing(bundle: Bundle, *functions: str) -> None:
    """Record an `impl.conformance` verdict saying `conformance.py` compared ``functions``."""
    compared = [{"symbol": name, "inputs": 10} for name in functions]
    bundle.record(
        [Verdict(gate="impl.conformance", status=Status.PASS, details={"compared": compared})]
    )


def test_an_attack_auditor_s_defect_inputs_go_on_record_for_conformance_py(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """A defect shown by running code is put to `conformance.py` with the inputs on record.

    One that names a function `conformance.py` does not compare, or an input that is not an
    argument tuple, could not be put to it, and is not filed.
    """
    comparing(sound, "floatformat")
    unusable = [
        {"input": "no defect"},
        {**DEFECT, "defect": "another function", "function": "other"},
        {**DEFECT, "defect": "a call, not arguments", "input": 'floatformat("1E+9999")'},
    ]
    session = Playing(attack=attacking(sound.solution(), defects=[DEFECT, *unusable]))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))

    assert audit.defects == (FILED,)
    said = " ".join(audit.notes)
    assert "'another function' was not filed: its function, `other`, is not one" in said
    assert "'a call, not arguments' was not filed: its input is not an argument tuple" in said
    write_audit(sound, audit)
    recorded = sound.audit()
    assert recorded is not None and recorded.defects == (FILED,)
    [kept] = replay.stored(sound)
    assert (kept.function, kept.arguments, kept.source) == (
        "floatformat",
        "('1E+9999',)",
        replay.REVIEW,
    )
    assert "raises InvalidOperation" in (sound.audit_dir / "notes.md").read_text()
    prompt = " ".join(session.lane("attack").prompt.split())
    assert "The function is one of these: `floatformat`." in prompt
    schema = session.lane("attack").fields
    assert "notes" not in schema and "function" in schema["defects"]["items"]["required"]


def test_no_defect_can_be_filed_before_conformance_py_compared_a_function(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """There is no name its input could be handed to `conformance.py` under."""
    session = Playing(attack=attacking(sound.solution(), defects=[DEFECT]))

    audit = reviewers(session, falsifier, settings).run(sound, coin_change, ("attack",))

    assert audit.defects == ()
    prompt = " ".join(session.lane("attack").prompt.split())
    assert "`conformance.py` has compared no function yet, so no defect can be filed." in prompt


@pytest.mark.parametrize("stands", [True, False], ids=["stands", "since-repaired"])
def test_defects_on_record_stand_as_long_as_the_specification_they_were_shown_against(
    stands: bool, sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """Kept when the attack auditor is not asked, and beside its new ones while it stands.

    One a record holds without a function `conformance.py` compares is not kept.
    """
    earlier = Defect(defect="an earlier defect", function="floatformat", input="(40,)")
    unnamed = Defect(defect="a defect filed with no function", input="(40,)")
    filed_before(sound, falsifier, stands=stands, defects=(earlier, unnamed))
    comparing(sound, "floatformat")

    kept = reviewers(Playing(), falsifier, settings).run(sound, coin_change, ("faithfulness",))
    asked = reviewers(
        Playing(attack=attacking(sound.solution(), defects=[DEFECT])), falsifier, settings
    ).run(sound, coin_change, ("attack",))

    assert kept.defects == (earlier,)
    assert asked.defects == ((earlier,) if stands else ()) + (FILED,)


def test_defects_on_record_stand_beside_new_ones_when_the_earlier_review_filed_no_attack(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """Whether they stand turns on the specification they were shown against, not on attacks."""
    earlier = Defect(defect="an earlier defect", function="floatformat", input="(40,)")
    filed_before(sound, falsifier, stands=True, defects=(earlier,), attacks=False)
    comparing(sound, "floatformat")

    asked = reviewers(
        Playing(attack=attacking(sound.solution(), defects=[DEFECT])), falsifier, settings
    ).run(sound, coin_change, ("attack",))

    assert asked.defects == (earlier, FILED)


def test_the_faithfulness_auditor_is_told_the_listed_tests_the_test_patch_adds_or_edits(
    sound: Bundle, coin_change: Task, falsifier: Backend, settings: Settings
) -> None:
    """A row counts by them as by the failing tests; one the benchmark lists nowhere, not."""
    patch = (
        "diff --git a/tests/test_change.py b/tests/test_change.py\n"
        "--- a/tests/test_change.py\n"
        "+++ b/tests/test_change.py\n"
        "@@ -1,2 +1,8 @@\n"
        " def test_forty():\n"
        "     assert make_change(40) == (1, 1, 1, 0)\n"
        "+\n"
        "+def test_nickel():\n"
        "+    assert make_change(5) == (0, 0, 1, 0)\n"
        "+\n"
        "+def test_expected_to_fail():\n"
        "+    assert make_change(-5) is None\n"
    )
    oracle = coin_change.oracle.model_copy(
        update={"regression": ("tests/test_change.py::test_nickel[5]",)}
    )
    task = coin_change.model_copy(update={"oracle": oracle, "metadata": {"test_patch": patch}})
    session = Playing(faithfulness=judging())

    reviewers(session, falsifier, settings).run(sound, task, ("faithfulness",))

    asked = session.lane("faithfulness").prompt
    assert "* `tests/test_change.py::test_nickel[5]`" in asked
    assert "test_expected_to_fail" not in asked
