# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`spec.strength.battery`: a specification measured against implementations it must sort.

Every case comes with the verdict its author claims the checker will reach, and the cases
here are paired so that a wrong claim in either direction reads as itself: an accepted
wrong implementation is a specification too weak, a refused correct one a specification
too strong.

Whether that is a finding depends on what an accepting verdict is worth. A refutation is a
counterexample under any checker; no refutation is a proof under a prover and an empty
search under a falsifier. Both are asserted, against backends that differ in nothing else
(`tests/doubles.py`).

The screens come first: a case that changed the specification, or reaches for a construct the
checker cannot see past, is never evidence, and a property-based test suite whose own cases are
not evidence fails rather than skipping, because the bundle shipped them.
"""

from __future__ import annotations

import re
from collections.abc import Callable

import pytest

from benchproofer.backends.base import CheckResult
from benchproofer.config import Settings
from benchproofer.core import witness
from benchproofer.core.bundle import Bundle, Rival, Twin
from benchproofer.core.markers import parse, replace_region
from benchproofer.core.verdict import Level, SkipReason, Status, Verdict
from benchproofer.formalize.session import TWIN, Draft, Formalization
from benchproofer.gates import attribution
from benchproofer.gates.battery import BatteryGate, distinct
from benchproofer.pipeline.build import write_formalization
from benchproofer.pipeline.report import summarize
from benchproofer.pipeline.route import Route, route
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import write_text
from doubles import Proving, Rigged, Screening

COMMENT = "#"

#: Wrong: it counts dimes out of the whole amount rather than out of what the quarters
#: leave, so above a quarter the counts do not add up. A mistake the pre-fix implementation the
#: fixture ships does not make, since every case here has to be a case of its own.
TOO_MANY_DIMES = """\
def impl(cents):
    quarters = cents // 25
    dimes = cents // 10
    pennies = cents - quarters * 25 - dimes * 10
    return (quarters, dimes, 0, pennies)
"""
#: Correct, written as a loop rather than four assignments.
BY_LOOP = """\
def impl(cents):
    counts = []
    for coin in (25, 10, 5, 1):
        counts.append(cents // coin)
        cents = cents - counts[-1] * coin
    return tuple(counts)
"""


def cased(name: str, kind: str, impl: str, solution: str) -> tuple[Rival, str]:
    """One case of the property-based test suite: its manifest entry and the file it indexes."""
    return (
        Rival(
            id=name,
            kind=kind,  # type: ignore[arg-type]
            expect="refute" if kind == "uniqueness" else "verify",
            file=f"{name}.py",
            rationale=f"the {kind} case this test is about",
        ),
        replace_region(solution, COMMENT, "impl", impl),
    )


def probe(solution: str) -> str:
    """The reference implementation with a probe beside it, which is what a case adds.

    An admissibility case keeps the shipped implementation and asserts what the
    specification says about it at an input the task exercises, and the gate checks
    exactly that shape.
    """
    body = parse(solution, COMMENT)["impl"].text.rstrip()
    return f"{body}\n\n\ndef probe_at_forty_cents():\n    assert impl(40) == (1, 1, 1, 0)\n"


def battery(bundle: Bundle, *cases: tuple[Rival, str]) -> None:
    """Replace the bundle's rivals with the cases a test is about."""
    for stale in bundle.rivals_dir.glob("*"):
        stale.unlink()
    bundle.save_battery(list(cases))


def balanced(bundle: Bundle, **impls: str) -> None:
    """A suite of rivals asking all three questions, whatever the backend under test.

    A prover requires the probe and a falsifier does not, and a property-based test suite that
    carries one anyway is judged the same either side of that line.
    """
    solution = bundle.solution()
    battery(
        bundle,
        cased("uniqueness-1", "uniqueness", impls.get("wrong", TOO_MANY_DIMES), solution),
        cased("soundness-1", "soundness", impls.get("right", BY_LOOP), solution),
        cased(
            "admissibility-1",
            "admissibility",
            impls.get("probe", probe(solution)),
            solution,
        ),
    )


def restaged(bundle: Bundle, solution: str) -> None:
    """Put ``solution`` in the bundle, dropping the pre-fix implementation of the old one.

    A pre-fix implementation is the solution it was drafted against with the code before the fix
    in it. Left beside another solution it is a file every case is compared with and no reader
    can place, and `spec.strength.battery` does compare: every case has to be a case of its own.
    """
    write_text(bundle.solution_path, solution)
    for stale in bundle.twins_dir.glob("*"):
        stale.unlink()


def context(
    bundle: Bundle,
    settings: Settings,
    *,
    backend: Screening | None = None,
    **rigging: object,
) -> Rigged:
    """A context whose checker answers from a script, keyed by rival."""
    return Rigged(
        bundle=bundle,
        backend=backend or Screening(),
        settings=settings,
        level=Level.STATIC,
        **rigging,  # type: ignore[arg-type]
    )


def slot(name: str) -> str:
    """The name the gate checks one rival under."""
    return f"rival-{name}"


def test_a_property_based_test_suite_that_behaved_as_claimed_passes_and_says_what_it_contained(
    sound: Bundle, settings: Settings
) -> None:
    balanced(sound)
    rigged = context(
        sound, settings, answers={slot("uniqueness-1"): CheckResult.no("cents=40")}
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.summary == (
        "3 case(s) behaved as claimed (1 admissibility, 1 soundness, 1 uniqueness)"
    )
    assert verdict.details["kinds"] == ["admissibility", "soundness", "uniqueness"]
    assert rigged.checked == [
        "solution",
        slot("uniqueness-1"),
        slot("soundness-1"),
        slot("admissibility-1"),
    ]
    assert verdict.evidence == ["evidence/battery.txt"]


def test_a_property_based_test_suite_attacking_only_one_direction_is_incomplete(
    sound: Bundle, settings: Settings
) -> None:
    """Every wrong implementation refuted says nothing about a spec that rejects all.

    The one case here would have behaved exactly as claimed: what the gate refuses is the
    conclusion, not the case, and no case is run.
    """
    solution = sound.solution()
    battery(sound, cased("uniqueness-1", "uniqueness", TOO_MANY_DIMES, solution))
    rigged = context(
        sound, settings, answers={slot("uniqueness-1"): CheckResult.no("cents=40")}
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.summary.endswith("no soundness case")
    assert rigged.checked == ["solution"]


def test_a_specification_that_accepts_a_wrong_implementation_is_too_weak(
    sound: Bundle, settings: Settings
) -> None:
    """Under a prover, verifying the uniqueness case is a proof of the defect."""
    balanced(sound)

    verdict = BatteryGate().run(context(sound, settings, backend=Proving()))

    assert verdict.status is Status.FAIL
    assert verdict.summary == "the specification accepts wrong implementation(s): uniqueness-1"
    assert verdict.details["too_weak"] == ["uniqueness-1"]


def test_the_same_property_based_test_suite_under_a_falsifier_is_a_search_that_came_up_empty(
    sound: Bundle, settings: Settings
) -> None:
    """No counterexample within a budget is not a demonstration that there is none."""
    balanced(sound)

    verdict = BatteryGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "falsifier" in verdict.summary
    assert verdict.details["too_weak"] == ["uniqueness-1"]


@pytest.mark.parametrize("backend", [Screening(), Proving()], ids=["falsifier", "prover"])
def test_a_specification_that_rejects_a_correct_implementation_is_too_strong(
    backend: Screening, sound: Bundle, settings: Settings
) -> None:
    """A spec that pinned down one implementation would mark a right answer wrong.

    Under either checker: the asymmetry is about accepting verdicts, and a counterexample
    is a witness.
    """
    balanced(sound)
    rigged = context(
        sound,
        settings,
        backend=backend,
        answers={
            slot("uniqueness-1"): CheckResult.no("cents=40"),
            slot("soundness-1"): CheckResult.no("property_change_is_the_fewest_coins"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.summary == "the specification rejects correct implementation(s): soundness-1"
    assert verdict.details["too_strong"] == ["soundness-1"]


#: A specification of the Nagini shape, whose rivals can be executed on the same drawn inputs as
#: the shipped body.
SPLIT = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin spec
def split_cents(cents: int) -> PSeq[int]:
    Requires(MustTerminate(2))
    Requires(cents >= 0)
    Ensures(len(Result()) == 2)
    Ensures(Result()[0] * 25 + Result()[1] == cents)
    Ensures(0 <= Result()[1] and Result()[1] < 25)
# benchproofer:end spec
# benchproofer:begin impl
    return PSeq(cents // 25, cents % 25)
# benchproofer:end impl
"""
#: Correct, through a local: on every input it returns what the shipped body returns.
BY_LOCAL = "    quarters = cents // 25\n    return PSeq(quarters, cents - quarters * 25)\n"
#: What a prover says of a correct rival whose proof is missing a step, and all it printed.
UNPROVED = CheckResult.no(
    "Postcondition of split_cents might not hold. Assertion Result()[1] < 25 might not "
    "hold. (solution.py:8:12)",
    output="Verification failed\nErrors:\nPostcondition of split_cents might not hold.\n"
    "Assertion Result()[1] < 25 might not hold. (solution.py:8:12)\n",
)
ACCEPTED = CheckResult.ok("all obligations discharged")


def split(
    bundle: Bundle,
    right: str = BY_LOCAL,
    *,
    wrong: str = "    return PSeq(cents // 25, 0)\n",
    probed: str = "    Assert(len(split_cents(40)) == 2)\n",
    solution: str = SPLIT,
) -> str:
    """Rivals over ``solution`` asking all three questions; returns the correct case's file.

    ``right``, ``wrong`` and ``probed`` are the correct case's body, the wrong case's body
    and the probe's body.
    """
    restaged(bundle, solution)
    body = parse(solution, COMMENT)["impl"].text.rstrip()
    correct = cased("soundness-1", "soundness", right, solution)
    battery(
        bundle,
        cased("uniqueness-1", "uniqueness", wrong, solution),
        correct,
        cased(
            "admissibility-1",
            "admissibility",
            f"{body}\n\n\ndef admissibility_probe() -> None:\n{probed}",
            solution,
        ),
    )
    return bundle.rival_source(correct[0])


def refusing_the_correct_case(
    bundle: Bundle, settings: Settings, right: str = BY_LOCAL
) -> Rigged:
    """A prover's context over `split` that refuses the correct case as `UNPROVED`."""
    split(bundle, right)
    return context(
        bundle,
        settings,
        backend=Proving(),
        answers={
            slot("uniqueness-1"): CheckResult.no("Postcondition might not hold."),
            slot("soundness-1"): UNPROVED,
            slot("admissibility-1"): ACCEPTED,
        },
    )


def test_a_correct_rival_the_checker_could_not_prove_is_a_defect_of_the_case(
    sound: Bundle, settings: Settings
) -> None:
    """Executed, it returns what the shipped body returns, so the specification admits it.

    What the checker refused is the rival's own proof, and reading that as a specification
    too strong sends a repair to rewrite a specification nothing was wrong with. With no
    proof session behind it, the case is a repair's to fix rather than recorded as a gap.
    """
    rigged = refusing_the_correct_case(sound, settings)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["unproved"] == ["soundness-1"]
    assert verdict.details["gaps"] == []
    assert verdict.details["reasons"]["soundness-1"].startswith(
        "executed on the same drawn inputs, it returns"
    )
    assert verdict.details["reasons"]["soundness-1"].endswith(
        f"; the checker said: {UNPROVED.detail}"
    )
    assert "too_strong" not in verdict.details
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "soundness-1: unproved\n  source:      rivals/soundness-1.py\n" in evidence
    assert f"  checker:     refuted: {UNPROVED.detail}\n" in evidence
    assert "  equivalence: executed on the same drawn inputs, it returns what the" in evidence
    assert "    Assertion Result()[1] < 25 might not hold. (solution.py:8:12)" in evidence


def after_a_session(bundle: Bundle, case: str, reported: str) -> None:
    """Record on ``case`` that a proof session ran on it and say what it reported."""
    manifest = bundle.battery()
    bundle.save_battery(
        [
            (
                rival.model_copy(update={"proof_session": reported})
                if rival.id == case
                else rival,
                bundle.rival_source(rival),
            )
            for rival in manifest
        ]
    )


#: What a proof session that spent its budget without closing the goal reports.
SPENT = "rival-soundness-1: a proof session (34 turn(s), reported stuck) did not close it"


def test_a_correct_case_a_proof_session_could_not_close_is_recorded_as_a_gap(
    sound: Bundle, settings: Settings
) -> None:
    """A repair would ask for the round a proof session has just spent its budget on.

    The case is correct and its proof is missing: a hole in the bundle's evidence, named in
    the summary, rather than a finding about the specification or a case to write again.
    Its kind still counts as asked.
    """
    rigged = refusing_the_correct_case(sound, settings)
    after_a_session(sound, "soundness-1", SPENT)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["gaps"] == ["soundness-1"]
    assert "unproved" not in verdict.details
    assert SPENT in verdict.details["gap_reasons"]["soundness-1"]
    assert "recorded as such" in verdict.summary
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "soundness-1: unproved after a proof session\n" in evidence
    assert SPENT in evidence


@pytest.mark.parametrize(
    ("session", "wrong"),
    [("", False), (SPENT, False), ("", True)],
    ids=("unproved", "after-a-proof-session", "beside-another-finding"),
)
def test_the_run_report_lists_each_correct_case_the_checker_refused_on_its_own_proof(
    sound: Bundle, settings: Settings, session: str, wrong: bool
) -> None:
    """So a reader of the report sees where the checker, not the specification, fell short.

    Whatever the verdict is about: a wrong rival the specification accepts is its finding,
    and the correct case refused on its own proof is listed all the same, with its reason.
    """
    rigged = refusing_the_correct_case(sound, settings)
    if wrong:
        rigged.answers[slot("uniqueness-1")] = ACCEPTED
    if session:
        after_a_session(sound, "soundness-1", session)
    verdict = BatteryGate().run(rigged)
    sound.record([verdict])
    assert ("unproved" in verdict.details) is not (wrong or bool(session))

    report = summarize([sound], level=Level.STATIC)

    (row,) = report.rows
    (case,) = row.unproved
    assert case.case == "soundness-1" and case.after_session is bool(session)
    assert case.reason.startswith("executed on the same drawn inputs, it returns")
    assert case.reason.endswith(
        f"the checker said: {UNPROVED.detail}" + (f"; {session}" if session else "")
    )
    (listed,) = report.to_json()["bundles"][0]["unproved"]
    assert listed == {
        "case": "soundness-1",
        "reason": case.reason,
        "after_proof_session": bool(session),
    }
    shown = report.to_markdown()
    assert "## Correct cases whose own proof the checker rejected (1)" in shown
    assert f"| {row.key} | `soundness-1` | {'failed' if session else 'none'} | " in shown


def test_a_wrong_case_carrying_the_accepted_implementation_is_set_aside(
    sound: Bundle, settings: Settings
) -> None:
    """It verifies because the solution file does, which says nothing about strength.

    Read as the specification accepting a wrong implementation, it sends a repair to
    strengthen a specification nothing was wrong with; the checker is not even asked. It
    was the property-based test suite's one uniqueness case, so that question is left unasked.
    """
    split(
        sound,
        wrong="    # the same body, with a comment\n    return PSeq(cents // 25, cents % 25)\n",
    )
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={slot("soundness-1"): ACCEPTED, slot("admissibility-1"): ACCEPTED},
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.summary.startswith("no uniqueness case remains once the case(s) repeating")
    assert verdict.details["set_aside"] == ["uniqueness-1"]
    assert "contains the reference implementation" in verdict.details["reasons"]["uniqueness-1"]
    assert "too_weak" not in verdict.details
    assert slot("uniqueness-1") not in rigged.checked
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "uniqueness-1: set aside\n" in evidence


def test_a_wrong_case_that_runs_as_the_accepted_one_is_a_defect_of_the_case(
    sound: Bundle, settings: Settings
) -> None:
    """Written differently, it returns what the shipped body returns on every draw."""
    split(sound, wrong="    kept = cents // 25\n    return PSeq(kept, cents % 25)\n")
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={
            slot("uniqueness-1"): ACCEPTED,
            slot("soundness-1"): ACCEPTED,
            slot("admissibility-1"): ACCEPTED,
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.details["not_evidence"] == ["uniqueness-1"]
    reason = verdict.details["reasons"]["uniqueness-1"]
    assert reason.startswith(
        "executed on the same drawn inputs, it computes what the reference implementation"
    )
    assert "too_weak" not in verdict.details
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "uniqueness-1: not wrong\n" in evidence


# ---- a case that repeats another is set aside --------------------------------
#
# A property-based test suite's breadth is the number of questions it asks, not the number of
# files it ships. So a case that carries another -- the reference implementation, the pre-fix
# implementation whose refusal `spec.discriminates` already asks for, an earlier case -- counts
# for nothing, and the suite is judged on the rest. Text decides it under any checker; a
# uniqueness case is compared by behavior too, since an added assertion defeats a textual
# comparison and changes nothing the case asks.


def twinned(bundle: Bundle, solution: str, body: str) -> None:
    """Give the bundle one pre-fix implementation of ``solution``, implemented as ``body``."""
    bundle.save_twins(
        [(Twin(id="twin", file="twin.py"), replace_region(solution, COMMENT, "impl", body))]
    )


def test_a_case_that_carries_an_earlier_case_is_set_aside_and_the_rest_judged(
    sound: Bundle, settings: Settings
) -> None:
    """Two files, one question: what the checker says of the second says it of the first.

    So the second is named and not run, and the property-based test suite passes on the cases
    that remain, which still ask every question.
    """
    solution = sound.solution()
    restaged(sound, solution)
    battery(
        sound,
        cased("uniqueness-1", "uniqueness", TOO_MANY_DIMES, solution),
        cased("uniqueness-2", "uniqueness", TOO_MANY_DIMES, solution),
        cased("soundness-1", "soundness", BY_LOOP, solution),
    )
    rigged = context(sound, settings, answers={slot("uniqueness-1"): CheckResult.no("40")})

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.summary.startswith(
        "2 case(s) behaved as claimed (1 soundness, 1 uniqueness); 1 case(s) repeating "
        "another of the bundle's files, set aside and not counted toward the gate's result: "
        "uniqueness-2 (it contains case uniqueness-1"
    )
    assert verdict.details["defects"] == {"set_aside": ["uniqueness-2"]}
    assert slot("uniqueness-2") not in rigged.checked
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "uniqueness-2: set aside\n" in evidence


#: The code before the fix, as a pre-fix implementation carries it: no dimes or nickels at all.
PRE_FIX = "def impl(cents):\n    return (cents // 25, 0, 0, cents % 25)\n"


def test_a_case_that_repeats_another_file_is_left_out_beside_one_of_its_kind(
    sound: Bundle,
) -> None:
    """What a bundle is written with is screened as the gate screens a case's text.

    A repeat that is the only case of its kind stays, since the gate then reports the kind
    as left without a case and a repair addresses it.
    """
    solution = sound.solution()
    twin = replace_region(solution, COMMENT, "impl", PRE_FIX)
    body = parse(solution, COMMENT)["impl"].text
    cases = [
        cased("uniqueness-1", "uniqueness", TOO_MANY_DIMES, solution),
        cased("uniqueness-2", "uniqueness", f"{PRE_FIX}# the code before the fix\n", solution),
        cased("soundness-1", "soundness", BY_LOOP, solution),
        cased("soundness-2", "soundness", f"{body}  # written again\n", solution),
    ]
    backend = BACKENDS.get(sound.backend_name)

    assert [rival.id for rival, _ in distinct(solution, [twin], cases, backend)] == [
        "uniqueness-1",
        "soundness-1",
    ]
    assert [rival.id for rival, _ in distinct(solution, [twin], cases[1:3], backend)] == [
        "uniqueness-2",
        "soundness-1",
    ]


def test_a_drafted_case_that_repeats_the_pre_fix_implementation_is_not_written_into_the_bundle(
    sound: Bundle,
) -> None:
    """Neither its file nor its entry ships, and the notes do not copy the suite."""
    backend = BACKENDS.get(sound.backend_name)
    solution = sound.solution()
    twin = replace_region(solution, COMMENT, "impl", PRE_FIX)

    def drafted(name: str, kind: str, source: str) -> Draft:
        return Draft(id=name, kind=kind, rationale=f"the {kind} case", source=source)

    written = write_formalization(
        sound,
        backend,
        Formalization(
            task_key="t",
            backend=backend.name,
            provider="p",
            model="m",
            solution=solution,
            accepted=True,
            check=CheckResult.ok("accepted"),
            rounds=3,
            twins=(drafted("twin", TWIN, twin),),
            rivals=(
                drafted(
                    "uniqueness-1",
                    "uniqueness",
                    cased("u", "uniqueness", TOO_MANY_DIMES, solution)[1],
                ),
                drafted("uniqueness-2", "uniqueness", twin),
                drafted(
                    "soundness-1", "soundness", cased("s", "soundness", BY_LOOP, solution)[1]
                ),
            ),
        ),
    )

    assert [rival.id for rival in sound.battery()] == ["uniqueness-1", "soundness-1"]
    assert not (sound.rivals_dir / "uniqueness-2.py").exists()
    assert "rivals/uniqueness-2.py" not in written
    notes = sound.notes_path.read_text()
    assert "the uniqueness case" not in notes
    assert "rounds" not in notes
    assert "evidence" not in notes


def test_a_correct_case_that_carries_the_accepted_implementation_asks_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """A soundness case is a *different* correct implementation, or it shows nothing.

    The specification admitting its own implementation is `spec.verifies`, not evidence
    that the specification describes the task rather than one way of meeting it.
    """
    solution = sound.solution()
    restaged(sound, solution)
    body = parse(solution, COMMENT)["impl"].text
    battery(
        sound,
        cased("uniqueness-1", "uniqueness", TOO_MANY_DIMES, solution),
        cased("soundness-1", "soundness", f"{body}  # written again\n", solution),
    )
    rigged = context(sound, settings, answers={slot("uniqueness-1"): CheckResult.no("40")})

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["set_aside"] == ["soundness-1"]
    assert "the reference implementation" in verdict.details["reasons"]["soundness-1"]


def test_a_uniqueness_case_that_runs_as_the_pre_fix_implementation_runs_asks_nothing_new(
    sound: Bundle, settings: Settings
) -> None:
    """The pre-fix implementation's mistake is one `spec.discriminates` already asks about.

    Caught by behavior rather than by text, which is what a rival rewritten through a local
    -- or shipped a second time with one assertion added -- would otherwise slip past.
    """
    split(sound, wrong="    quarters = cents // 25\n    return PSeq(quarters, 0)\n")
    twinned(sound, SPLIT, "    return PSeq(cents // 25, 0)\n")
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={slot("soundness-1"): ACCEPTED, slot("admissibility-1"): ACCEPTED},
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["set_aside"] == ["uniqueness-1"]
    reason = verdict.details["reasons"]["uniqueness-1"]
    assert reason.startswith(
        "executed on the same drawn inputs, it computes what the pre-fix implementation "
        "twin computes"
    )
    assert slot("uniqueness-1") not in rigged.checked


def test_an_admissibility_case_may_carry_the_accepted_implementation(
    sound: Bundle, settings: Settings
) -> None:
    """It is the reference implementation with a probe beside it; that is its whole shape."""
    balanced(sound)
    rigged = context(sound, settings, answers={slot("uniqueness-1"): CheckResult.no("40")})

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["defects"] == {}


def test_a_wrong_case_the_specification_accepts_is_still_a_weakness(
    sound: Bundle, settings: Settings
) -> None:
    """Only agreement moves an accepted wrong case onto the case itself."""
    split(sound)
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={
            slot("uniqueness-1"): ACCEPTED,
            slot("soundness-1"): ACCEPTED,
            slot("admissibility-1"): ACCEPTED,
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.details["too_weak"] == ["uniqueness-1"]
    assert "not_evidence" not in verdict.details


def test_a_refused_rival_that_computes_something_else_is_still_a_specification_too_strong(
    sound: Bundle, settings: Settings
) -> None:
    """Only agreement moves a refusal onto the case; a difference leaves it where it was."""
    rigged = refusing_the_correct_case(sound, settings, "    return PSeq(0, cents)\n")

    verdict = BatteryGate().run(rigged)

    assert verdict.details["too_strong"] == ["soundness-1"]
    assert "unproved" not in verdict.details
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert (
        "soundness-1: refuted" in evidence
        and "equivalence: undecided: executed on the same drawn inputs" in evidence
    )


class Placing(Proving):
    """A prover that places a failed obligation at the clause stating it, as Nagini does."""

    name = "placing"
    refusal_site = BACKENDS.get("nagini").refusal_site


#: `SPLIT` assuming a callee, which running a rival beside it cannot honor.
ASSUMING_SPLIT = SPLIT.replace(
    "# benchproofer:begin spec\n",
    "# benchproofer:begin axioms\n@ContractOnly\ndef quarter() -> int:\n"
    "    Ensures(Result() == 25)\n# benchproofer:end axioms\n\n# benchproofer:begin spec\n",
    1,
)
#: Correct, as a loop, whose invariant is the step a checker may not manage to preserve.
BY_COUNTING = (
    "    quarters = 0  # type: int\n"
    "    rest = cents  # type: int\n"
    "    while rest >= 25:\n"
    "        Invariant(rest >= 0 and quarters * 25 + rest == cents)\n"
    "        quarters = quarters + 1\n"
    "        rest = rest - 25\n"
    "    return PSeq(quarters, rest)\n"
)


def refused_at(source: str, text: str, message: str) -> CheckResult:
    """A refusal Nagini's way, placed at the first line of ``source`` holding ``text``."""
    line = next(n for n, row in enumerate(source.splitlines(), 1) if text in row)
    said = f"solution.py:{line}:8:{line}:40: error: {message}"
    return CheckResult.no(said, output=f"Verification failed\nErrors:\n{said}\n")


@pytest.mark.parametrize(
    ("placed", "message", "unproved"),
    [
        ("Invariant(", "Loop invariant might not be preserved.", True),
        ("Ensures(Result()[0]", "Postcondition of split_cents might not hold.", False),
    ],
    ids=["inside the implementation", "at a clause of the specification"],
)
def test_a_refusal_placed_inside_a_correct_rival_is_a_step_of_its_own_proof(
    sound: Bundle, settings: Settings, placed: str, message: str, unproved: bool
) -> None:
    """Where running it cannot decide it, where the checker placed the refusal still can.

    A loop invariant the rival writes is the rival's proof; a postcondition is the
    specification's, and a correct rival refused there is what too strong means.
    """
    source = split(sound, BY_COUNTING, solution=ASSUMING_SPLIT)
    refusal = refused_at(source, placed, message)
    rigged = context(
        sound,
        settings,
        backend=Placing(),
        answers={
            slot("uniqueness-1"): CheckResult.no("Postcondition might not hold."),
            slot("soundness-1"): refusal,
            slot("admissibility-1"): ACCEPTED,
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    if unproved:
        assert verdict.details["unproved"] == ["soundness-1"]
        assert "too_strong" not in verdict.details
        reason = verdict.details["reasons"]["soundness-1"]
        assert "lies inside the case's own implementation" in reason
        assert reason.endswith(f"the checker said: {refusal.detail}")
    else:
        assert verdict.details["too_strong"] == ["soundness-1"]
        assert "unproved" not in verdict.details


class Replaying(Proving):
    """A prover that replays the proof a case writes, placing refusals as Lean does."""

    name = "replaying"
    refusal_site = BACKENDS.get("lean4").refusal_site


class Elaborating(Replaying):
    """`Replaying`, with definitions elaborated before any proof of them, as Lean's are."""

    name = "elaborating"
    definitions_in_impl = True


def placed_at(source: str, text: str, message: str) -> CheckResult:
    """A refusal Lean's way, placed at the first line of ``source`` holding ``text``."""
    line = next(n for n, row in enumerate(source.splitlines(), 1) if text in row)
    said = f"work/check/solution.lean:{line}:4: error: {message}"
    return CheckResult.no(said, output=f"{said}\n")


def refused_in_its_own_region(bundle: Bundle, settings: Settings, backend: Proving) -> Rigged:
    """Rivals over `ASSUMING_SPLIT` whose correct case is refused inside what it wrote.

    The rival assumes a callee, so running it beside the reference implementation decides
    nothing and where the refusal was placed is all there is to go on.
    """
    source = split(bundle, BY_COUNTING, solution=ASSUMING_SPLIT)
    return context(
        bundle,
        settings,
        backend=backend,
        answers={
            slot("uniqueness-1"): CheckResult.no("unsolved goals"),
            slot("soundness-1"): placed_at(source, "while rest", "Application type mismatch"),
            slot("admissibility-1"): ACCEPTED,
        },
    )


def test_a_correct_case_whose_own_definition_does_not_elaborate_is_drafted_again(
    sound: Bundle, settings: Settings
) -> None:
    """It is not an implementation at all, so it says nothing about the specification.

    Nor is it a gap: a proof session cannot reach a definition, and "correct, proof
    missing" would describe a case that is neither.
    """
    rigged = refused_in_its_own_region(sound, settings, Elaborating())
    after_a_session(sound, "soundness-1", SPENT)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["not_evidence"] == ["soundness-1"]
    assert (
        "not an implementation of the specification"
        in verdict.details["reasons"]["soundness-1"]
    )
    assert "too_strong" not in verdict.details
    assert verdict.details["gaps"] == []


@pytest.mark.parametrize("session", [False, True], ids=["no session yet", "after a session"])
def test_a_correct_case_a_replaying_checker_refused_on_its_own_proof_is_the_case_s(
    session: bool, sound: Bundle, settings: Settings
) -> None:
    """A case to fix, or recorded as a gap once a proof session has spent its budget on it.

    A script that does not close and a specification too strong to admit the case are
    refused alike, so the refusal is read as the case's; the too-strong question is left to
    the control the review has to show the checker accepting.
    """
    rigged = refused_in_its_own_region(sound, settings, Replaying())
    if session:
        after_a_session(sound, "soundness-1", SPENT)

    verdict = BatteryGate().run(rigged)

    assert "too_strong" not in verdict.details
    if session:
        assert verdict.status is Status.PASS
        assert verdict.details["gaps"] == ["soundness-1"]
    else:
        assert verdict.status is Status.FAIL
        assert verdict.details["unproved"] == ["soundness-1"]


@pytest.mark.parametrize("name", ["lean4", "velvet"])
def test_lean_s_refusals_are_read_where_it_places_them(name: str) -> None:
    """Plain and tagged errors alike, after whatever directory the file was checked in."""
    site = BACKENDS.get(name).refusal_site
    found = [
        match.group("line")
        for said in (
            "work/w/solution.lean:43:4: error: Application type mismatch",
            "solution.lean:50:2: error(lean.unknownIdentifier): Unknown identifier `x`",
            "solution.lean:51:2: warning: unused variable",
        )
        if (match := re.search(site, said, re.MULTILINE))
    ]

    assert found == ["43", "50"]


def test_a_falsifiers_refusal_of_a_rival_is_a_counterexample_whatever_running_it_shows(
    sound: Bundle, settings: Settings
) -> None:
    """A bounded refuter refuses with an input, which no sample of other inputs outweighs.

    The correct case here runs as the shipped body does, which under a prover would make
    its refusal the case's own.
    """
    split(sound)
    rigged = context(
        sound,
        settings,
        answers={
            slot("uniqueness-1"): CheckResult.no("cents=40"),
            slot("soundness-1"): CheckResult.no("cents=40"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.details["too_strong"] == ["soundness-1"]
    assert "unproved" not in verdict.details


def test_the_evidence_carries_each_case_whole(sound: Bundle, settings: Settings) -> None:
    """A repair reads the file for what the checker said, so none of it is cut to a column."""
    balanced(sound)
    detail = "property_change_is_the_fewest_coins failed on cents=40, " + "x" * 80
    rigged = context(
        sound,
        settings,
        answers={
            slot("uniqueness-1"): CheckResult.no(detail, output=f"Falsifying example\n{detail}")
        },
    )

    BatteryGate().run(rigged)

    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "uniqueness-1: refuted\n  source:      rivals/uniqueness-1.py\n" in evidence
    assert "  kind:        uniqueness, expects refute\n" in evidence
    assert f"  checker:     refuted: {detail}\n" in evidence
    assert f"  output:\n    Falsifying example\n    {detail}\n" in evidence
    assert "soundness-1: verified" in evidence and "admissibility-1: verified" in evidence


def test_a_rival_that_changed_the_specification_fails_the_suite_that_ships_it(
    sound: Bundle, settings: Settings
) -> None:
    """A case attacking a different specification cannot be a case about this one."""
    solution = sound.solution()
    drifted = replace_region(
        replace_region(solution, COMMENT, "impl", TOO_MANY_DIMES),
        COMMENT,
        "spec",
        "def property_nothing(cents):\n    assert True\n",
    )
    battery(
        sound,
        (
            Rival(
                id="uniqueness-1",
                kind="uniqueness",
                expect="refute",
                file="uniqueness-1.py",
                rationale="attacks a specification this bundle does not ship",
            ),
            drifted,
        ),
        cased("soundness-1", "soundness", BY_LOOP, solution),
    )
    rigged = context(sound, settings)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "do not share the shipped specification: uniqueness-1" in verdict.summary
    assert rigged.checked == ["solution", slot("soundness-1")]


def test_a_rival_that_turns_the_checker_off_fails_rather_than_settling_anything(
    sound: Bundle, settings: Settings
) -> None:
    """`assume(False)` refutes nothing on the merits, so the suite cannot count it."""
    balanced(sound, wrong="def impl(cents):\n    assume(False)\n    return (0, 0, 0, 0)\n")
    rigged = context(sound, settings)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["not_evidence"] == ["uniqueness-1"]
    assert rigged.checked == ["solution", slot("soundness-1"), slot("admissibility-1")]


def test_a_case_whose_regions_cannot_be_read_is_a_defect_of_that_case_for_a_repair(
    sound: Bundle, settings: Settings
) -> None:
    """A case left with a second function's contract and no body is the case's own defect.

    Its file is named, with what is wrong with its regions, and the verdict goes to a repair:
    a crash of the gate would stop there, and no later repair would be told about the file.
    """
    solution = sound.solution()
    unpaired = cased("soundness-1", "soundness", BY_LOOP, solution)[1] + (
        "\n# benchproofer:begin spec.2\ndef property_second(cents):\n    assert True\n"
        "# benchproofer:end spec.2\n"
    )
    rival, _ = cased("soundness-1", "soundness", BY_LOOP, solution)
    battery(
        sound,
        cased("uniqueness-1", "uniqueness", TOO_MANY_DIMES, solution),
        (rival, unpaired),
        cased("admissibility-1", "admissibility", probe(solution), solution),
    )
    rigged = context(sound, settings)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "traceback" not in verdict.details
    assert verdict.details["not_evidence"] == ["soundness-1"]
    assert "rivals/soundness-1.py" in verdict.summary
    assert "function 2 has no impl.2 region" in verdict.summary
    assert route(verdict) is Route.REPAIR
    assert slot("soundness-1") not in rigged.checked


def test_a_rival_the_checker_could_not_read_is_not_a_refuted_one(
    sound: Bundle, settings: Settings
) -> None:
    """A syntax error rejects every case for free, which would certify any spec."""
    balanced(sound)
    rigged = context(
        sound, settings, answers={slot("uniqueness-1"): CheckResult.malformed("SyntaxError")}
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["malformed"] == ["uniqueness-1"]


def test_a_correct_rival_the_checker_could_not_read_is_not_a_specification_too_strong(
    sound: Bundle, settings: Settings
) -> None:
    """Otherwise a broken soundness case would convict a sound specification."""
    balanced(sound)
    rigged = context(
        sound,
        settings,
        answers={
            slot("uniqueness-1"): CheckResult.no("cents=40"),
            slot("soundness-1"): CheckResult.malformed("SyntaxError"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["malformed"] == ["soundness-1"]
    assert "too_strong" not in verdict.details


def test_a_rival_the_checker_reached_no_verdict_on_leaves_the_suite_undecided(
    sound: Bundle, settings: Settings
) -> None:
    """A run out of time is a fact about the machine, not about the specification."""
    balanced(sound)
    rigged = context(
        sound,
        settings,
        answers={slot("uniqueness-1"): CheckResult.unknown("timed out at 120s")},
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.TIMEOUT
    assert verdict.details["undecided"] == ["uniqueness-1"]


def test_a_property_based_test_suite_is_not_judged_until_the_shipped_specification_verifies(
    sound: Bundle, settings: Settings
) -> None:
    """Against a rejected file, every rival is rejected, and that measures nothing."""
    balanced(sound)
    rigged = context(sound, settings, answers={"solution": CheckResult.no("cents=40")})

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "spec.verifies (Verification check) is where that is recorded" in verdict.summary
    assert rigged.checked == ["solution"]


def test_a_bundle_with_no_property_based_test_suite_fails_for_a_repair_to_write_one(
    sound: Bundle, settings: Settings
) -> None:
    for stale in sound.rivals_dir.glob("*"):
        stale.unlink()

    verdict = BatteryGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL
    assert route(verdict) is Route.REPAIR
    assert "no property-based test suite in rivals/" in verdict.summary


def test_an_unreadable_rivals_index_is_a_failure_rather_than_an_absent_one(
    sound: Bundle, settings: Settings
) -> None:
    (sound.rivals_dir / "index.toml").write_text("[[rival]]\nid = 1\n")

    verdict = BatteryGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL
    assert "the property-based test suite's index is unusable" in verdict.summary


def test_a_manifest_entry_whose_file_is_missing_is_a_failure(
    sound: Bundle, settings: Settings
) -> None:
    balanced(sound)
    (sound.rivals_dir / "uniqueness-1.py").unlink()

    verdict = BatteryGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL


def judged(bundle: Bundle, *cases: str, **defects: list[str]) -> None:
    """Record a verdict of this gate that judged ``cases`` and found ``defects`` among them."""
    bundle.record(
        [
            Verdict(
                gate=BatteryGate.id,
                status=Status.FAIL,
                summary="as judged",
                details={"rivals": list(cases), "defects": defects},
            )
        ]
    )


def test_every_verdict_records_the_cases_it_judged(sound: Bundle, settings: Settings) -> None:
    balanced(sound)
    rigged = context(
        sound, settings, answers={slot("uniqueness-1"): CheckResult.no("cents=40")}
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.details["rivals"] == ["uniqueness-1", "soundness-1", "admissibility-1"]


def test_a_case_removed_that_the_last_verdict_found_no_defect_in_fails_the_suite(
    sound: Bundle, settings: Settings
) -> None:
    """Whoever removed it, and before any case runs; one it found defective as a case may go.

    A case the verdict names as a finding about the specification is no defect of its own.
    """
    balanced(sound)
    judged(
        sound,
        "uniqueness-1",
        "uniqueness-2",
        "soundness-1",
        "soundness-2",
        "admissibility-1",
        malformed=["uniqueness-2"],
        too_strong=["soundness-2"],
    )
    rigged = context(sound, settings)

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert route(verdict) is Route.REPAIR
    assert verdict.details["removed"] == ["soundness-2"]
    assert "soundness-2. A case leaves the suite only once" in verdict.summary
    assert verdict.details["rivals"] == [
        "admissibility-1",
        "soundness-1",
        "soundness-2",
        "uniqueness-1",
    ]
    assert rigged.checked == ["solution"]


def test_a_suite_that_lost_only_cases_found_defective_as_cases_is_judged(
    sound: Bundle, settings: Settings
) -> None:
    balanced(sound)
    judged(sound, "uniqueness-1", "uniqueness-2", "soundness-1", unproved=["uniqueness-2"])
    rigged = context(
        sound, settings, answers={slot("uniqueness-1"): CheckResult.no("cents=40")}
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS


def test_a_verdict_that_judged_no_suite_keeps_the_cases_the_one_before_bound_it_to(
    sound: Bundle, settings: Settings
) -> None:
    """So a case removed while the solution does not verify is missed once it does."""
    balanced(sound)
    judged(sound, "uniqueness-1", "uniqueness-2", "soundness-1", malformed=["uniqueness-1"])
    refused = {"solution": CheckResult.no("cannot establish Ensures at line 9")}

    blocked = BatteryGate().run(context(sound, settings, answers=refused))

    assert blocked.skip_reason is SkipReason.INCONCLUSIVE
    assert blocked.details["rivals"] == ["soundness-1", "uniqueness-2"]


def test_a_case_whose_claim_contradicts_its_kind_is_refused_when_it_is_written() -> None:
    """The one defect the gate never has to judge, because it cannot be recorded."""
    with pytest.raises(ValueError, match="requires expect='refute'"):
        Rival(
            id="uniqueness-1",
            kind="uniqueness",
            expect="verify",
            file="uniqueness-1.py",
            rationale="a wrong implementation the author expects to verify",
        )


# ---- a rejection nobody can attribute to the specification -------------------
#
# Under a checker that replays a proof script the bundle wrote, a rival that is merely
# rewritten is refused as a wrong one is, so a reject case carries a refutation witness and
# the gate reads its two builds (`gates.attribution`). `core.witness` screens the witness
# itself; what is asserted here is what the gate does with the builds' answers.


class Tactic(Proving):
    """A prover whose accepting verdict rests on a proof script the file carries."""

    name = "tactic"
    witness_required = True


#: A witness naming a property the spec region declares, false of the solution file.
#: Lean-shaped, whatever this double's comment token: the two backends that require a
#: witness are both Lean, and `core.witness` screens for a claim in that language.
WITNESS = "example : ¬ property_change_is_the_fewest_coins 40 := by decide"


def with_witness(bundle: Bundle, claim: str, **impls: str) -> None:
    """Rivals of every kind, whose uniqueness case carries ``claim`` as its witness."""
    solution = bundle.solution()
    wrong = impls.get("wrong", TOO_MANY_DIMES)
    rival, source = cased("uniqueness-1", "uniqueness", wrong, solution)
    battery(
        bundle,
        (rival.model_copy(update={"witness": claim}), source),
        cased("soundness-1", "soundness", impls.get("right", BY_LOOP), solution),
        cased("admissibility-1", "admissibility", probe(solution), solution),
    )


def refusing(**extra: CheckResult) -> dict[str, CheckResult]:
    """A script in which the uniqueness rival is refused, plus whatever a case adds."""
    return {slot("uniqueness-1"): CheckResult.no("cents=40"), **extra}


#: The checker's answers on a reject case that a witness is asked about: a refusal, and no
#: verdict at all, which the case's own proof may be what ran out of budget on.
UNANSWERED = pytest.mark.parametrize(
    "answer",
    [CheckResult.no("cents=40"), CheckResult.unknown("timed out at 120s")],
    ids=["refused", "no verdict"],
)


@UNANSWERED
def test_a_rejection_the_witness_accounts_for_passes(
    sound: Bundle, settings: Settings, answer: CheckResult
) -> None:
    """Holds of the rival, fails of the reference implementation: a counterexample."""
    with_witness(sound, WITNESS)
    rigged = context(
        sound,
        settings,
        backend=Tactic(),
        answers={
            slot("uniqueness-1"): answer,
            "witness-uniqueness-1-rival": CheckResult.ok("the witness holds"),
            "witness-uniqueness-1-accepted": CheckResult.no("the witness fails"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert rigged.checked == [
        "solution",
        slot("uniqueness-1"),
        "witness-uniqueness-1-rival",
        "witness-uniqueness-1-accepted",
        slot("soundness-1"),
        slot("admissibility-1"),
    ]


@UNANSWERED
def test_a_reject_case_with_no_witness_is_an_error_rather_than_a_pass(
    sound: Bundle, settings: Settings, answer: CheckResult
) -> None:
    """The case that would otherwise pass vacuously, and no build is spent on it."""
    with_witness(sound, "")
    rigged = context(sound, settings, backend=Tactic(), answers={slot("uniqueness-1"): answer})

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert verdict.details["unattributed"] == ["uniqueness-1"]
    assert verdict.details["reasons"] == {"uniqueness-1": "the case ships no witness"}
    assert not any(step.startswith("witness-") for step in rigged.checked)


@pytest.mark.parametrize(
    ("builds", "why", "second"),
    [
        (
            {"witness-uniqueness-1-rival": CheckResult.no("not proved")},
            "proof did not close against the rival",
            False,
        ),
        (
            {"witness-uniqueness-1-rival": CheckResult.malformed("unknown tactic 'grind'")},
            "could not be read, so nothing was asked of the claim",
            False,
        ),
        (
            {
                "witness-uniqueness-1-rival": CheckResult.ok("holds"),
                "witness-uniqueness-1-accepted": CheckResult.ok("holds here too"),
            },
            "does not discriminate the rival",
            True,
        ),
        (
            {"witness-uniqueness-1-rival": CheckResult.unknown("no answer in 300s")},
            "reached no verdict",
            False,
        ),
    ],
    ids=["fails of the rival", "unreadable", "holds of the accepted too", "no answer"],
)
def test_a_witness_whose_builds_do_not_attribute_the_rejection_is_an_error(
    builds: dict[str, CheckResult], why: str, second: bool, sound: Bundle, settings: Settings
) -> None:
    """Each way the witness's builds leave the rejection unattributed, each named apart.

    A proof that did not close leaves the claim undecided, and the second build is not
    reached. A build the checker could not read -- an unknown tactic, a `decide` with no
    instance -- never asked whether the claim holds, which is not the same thing and calls
    for a different repair. One that holds of the reference implementation too discriminates
    nothing, as `assert True` would not. A build that reached no verdict established nothing.
    """
    with_witness(sound, WITNESS)
    rigged = context(sound, settings, backend=Tactic(), answers=refusing(**builds))

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert verdict.details["unattributed"] == ["uniqueness-1"]
    assert why in verdict.details["reasons"]["uniqueness-1"]
    assert ("witness-uniqueness-1-accepted" in rigged.checked) is second


def test_a_reject_case_s_unattributed_rejection_names_what_its_proof_session_reported(
    sound: Bundle, settings: Settings
) -> None:
    """As for the pre-fix implementation: a reader sees its proof was tried, and how."""
    tried = "a proof session on its refutation witness (40 turn(s), reported stuck)"
    with_witness(sound, WITNESS)
    sound.save_battery(
        [
            (
                rival.model_copy(update={"proof_session": tried})
                if rival.id == "uniqueness-1"
                else rival,
                sound.rival_source(rival),
            )
            for rival in sound.battery()
        ]
    )
    builds = {"witness-uniqueness-1-rival": CheckResult.no("not proved")}
    rigged = context(sound, settings, backend=Tactic(), answers=refusing(**builds))

    verdict = BatteryGate().run(rigged)

    assert verdict.details["unattributed"] == ["uniqueness-1"]
    assert verdict.details["reasons"]["uniqueness-1"].endswith(tried)


class PlacedWitness(Placing):
    """`Placing`, under a checker whose rejection attributes nothing without a witness."""

    name = "placed-witness"
    witness_required = True


def test_a_witness_build_that_failed_inside_the_case_is_not_about_the_witness(
    sound: Bundle, settings: Settings
) -> None:
    """The witness is appended outside every region, so a refusal in one is the file's.

    A case whose own implementation does not go through fails the build the witness was
    going to be judged by, and reading that as the witness not holding sends the repair
    after the wrong thing.
    """
    backend = PlacedWitness()
    rival = parse(sound.solution(), backend.comment)["impl"]
    probed = witness.probe(
        replace_region(sound.solution(), backend.comment, "impl", TOO_MANY_DIMES),
        WITNESS,
        backend,
    )
    inside = f"solution.py:{rival.start + 1}:4: error: assignment might fail"

    why = attribution._refused(CheckResult.no(inside, output=inside), probed, backend, "rival")

    assert "against the rival failed inside its implementation region" in why


def test_a_property_based_test_suite_verdict_names_every_category_the_pass_found(
    sound: Bundle, settings: Settings
) -> None:
    """The verdict is the first category, and the rest are not nothing.

    A repair told only about the first spends its round on that one and is told about the
    second in the round after, one round per category. Named together, one repair answers
    them all.
    """
    with_witness(sound, WITNESS)
    rigged = context(
        sound,
        settings,
        backend=Tactic(),
        answers=refusing(
            **{
                "witness-uniqueness-1-rival": CheckResult.no("not proved"),
                slot("soundness-1"): CheckResult.malformed("solution.py:9: invalid syntax"),
            }
        ),
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert verdict.details["defects"] == {
        "unattributed": ["uniqueness-1"],
        "malformed": ["soundness-1"],
    }
    assert "also found malformed: soundness-1" in verdict.summary


def test_a_specification_that_accepts_the_wrong_rival_outranks_a_missing_witness(
    sound: Bundle, settings: Settings
) -> None:
    """A case that established a finding stands whatever the rest of the suite did.

    And there is nothing to attribute: the rival verified, so the specification admits a
    wrong implementation however the proof script behaved.
    """
    with_witness(sound, "")
    rigged = context(
        sound, settings, backend=Tactic(), answers={slot("uniqueness-1"): CheckResult.ok("")}
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["too_weak"] == ["uniqueness-1"]


def test_a_checker_that_discharges_its_own_obligation_needs_no_witness(
    sound: Bundle, settings: Settings
) -> None:
    """Under Nagini a rejection is the contract failing to hold, and there is no script.

    So the same rivals, with no witness anywhere in them and its probe admitted, passes --
    and pays for no additional build.
    """
    with_witness(sound, "")
    rigged = context(sound, settings, backend=Proving(), answers=refusing())

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["kinds"] == ["admissibility", "soundness", "uniqueness"]
    assert not any(step.startswith("witness-") for step in rigged.checked)


# ---- the third kind: a probe, not a rival -----------------------------------
#
# No rival can find a precondition that is too strong, because every rival is judged
# against that same precondition, and a specification that admits no input the task
# exercises is vacuously true of every case and every other gate. The probe is the
# accepted implementation with assertions added, and asks whether the obligations can
# hold at all.


def test_a_probe_the_specification_refuses_is_a_precondition_that_excludes_the_task(
    sound: Bundle, settings: Settings
) -> None:
    """Reported apart from a refused rival: the obligations cannot hold here.

    Run directly, the probe's call is outside the precondition, so the refusal is not the
    probe's own. A refused rival says the specification pins down an implementation, this
    says it may apply to nothing the task is about, and the two call for different repairs.
    """
    split(sound, probed="    Assert(len(split_cents(-40)) == 2)\n")
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={
            slot("uniqueness-1"): CheckResult.no("Postcondition might not hold."),
            slot("soundness-1"): ACCEPTED,
            slot("admissibility-1"): CheckResult.no("the precondition is not established"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["precondition"] == ["admissibility-1"]
    assert "too_strong" not in verdict.details


def test_a_refused_probe_that_holds_when_run_is_the_probe_s_to_fix(
    sound: Bundle, settings: Settings
) -> None:
    """The precondition admits its call and the implementation meets its assertion.

    So what the checker could not do is follow the probe -- a value asserted in another
    shape than the postcondition states it, a definition left unfolded -- and a repair
    fixes the probe rather than the specification.
    """
    split(sound)
    refused = CheckResult.no("Assert might fail. Assertion len(split_cents(40)) == 2")
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={
            slot("uniqueness-1"): CheckResult.no("Postcondition might not hold."),
            slot("soundness-1"): ACCEPTED,
            slot("admissibility-1"): refused,
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "precondition" not in verdict.details
    assert verdict.details["unproved"] == ["admissibility-1"]
    reason = verdict.details["reasons"]["admissibility-1"]
    assert "the precondition admits every call the probe makes" in reason
    assert reason.endswith(f"the checker said: {refused.detail}")
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "admissibility-1: unproved\n" in evidence


class Tactical(Replaying):
    """`Replaying`, where a rejection alone attributes nothing to the specification."""

    name = "tactical"
    witness_required = True


@pytest.mark.parametrize(
    ("backend", "refusing", "key"),
    [(Placing(), refused_at, "precondition"), (Tactical(), placed_at, "unproved")],
    ids=["placed at the call", "inside a replayed proof"],
)
def test_a_probe_refused_inside_a_replayed_proof_is_the_probe_s_to_prove(
    backend: Proving,
    refusing: Callable[[str, str, str], CheckResult],
    key: str,
    sound: Bundle,
    settings: Settings,
) -> None:
    """Running it cannot decide the question here, since the file assumes a callee.

    A checker that replays the probe's own proof refuses that proof where it does not
    close, so the probe gets the proof session, and then the gap, any correct case gets. One
    that discharges the obligation itself places a call the precondition refuses at the
    call, inside the probe, so there the refusal stays the precondition's.
    """
    split(sound, solution=ASSUMING_SPLIT)
    [probe] = [sound.rival_source(it) for it in sound.battery() if it.kind == "admissibility"]
    rigged = context(
        sound,
        settings,
        backend=backend,
        answers={
            slot("uniqueness-1"): CheckResult.no("Postcondition might not hold."),
            slot("soundness-1"): ACCEPTED,
            slot("admissibility-1"): refusing(probe, "Assert(len(", "unsolved goals"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is not Status.PASS
    assert verdict.details[key] == ["admissibility-1"]
    assert ({"precondition", "unproved"} - {key}).isdisjoint(verdict.details)


def test_only_a_property_based_test_suite_under_a_prover_is_asked_for_a_probe(
    sound: Bundle, settings: Settings
) -> None:
    """A probe establishes something by having its assertions discharged.

    Under a falsifier, whose accepting verdict is a search that found no counterexample, they
    never are, so the kind is not required; under a prover a property-based test suite with no
    probe fails, and no case is run.
    """
    solution = sound.solution()
    battery(
        sound,
        cased("uniqueness-1", "uniqueness", TOO_MANY_DIMES, solution),
        cased("soundness-1", "soundness", BY_LOOP, solution),
    )
    answers = {slot("uniqueness-1"): CheckResult.no("cents=40")}
    proving = context(sound, settings, backend=Proving(), answers=answers)

    falsified = BatteryGate().run(context(sound, settings, answers=answers))
    proved = BatteryGate().run(proving)

    assert falsified.status is Status.PASS
    assert proved.status is Status.FAIL
    assert proved.summary.endswith("no admissibility case")
    assert proving.checked == ["solution"]


@pytest.mark.parametrize(
    ("probed", "why"),
    [
        (lambda body: BY_LOOP, "rewrites the reference implementation"),
        (lambda body: body, "adds no obligation to discharge"),
    ],
    ids=["rewrites the implementation", "adds nothing"],
)
def test_a_probe_that_is_not_the_accepted_implementation_plus_something_is_not_a_probe(
    probed: Callable[[str], str], why: str, sound: Bundle, settings: Settings
) -> None:
    """Refused as a case that is no evidence, and never checked, rather than read as a finding.

    A rewritten implementation is the other kind, and may be rejected for reasons that have
    nothing to do with the inputs; and the solution file alone adds nothing `spec.verifies`
    has not established.
    """
    body = parse(sound.solution(), COMMENT)["impl"].text
    balanced(sound, probe=probed(body))
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={slot("uniqueness-1"): CheckResult.no("cents=40")},
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["not_evidence"] == ["admissibility-1"]
    assert why in verdict.details["reasons"]["admissibility-1"]
    assert slot("admissibility-1") not in rigged.checked


# ---- the uniqueness kind decided by a lemma ----------------------------------
#
# A specification that is a total function of its inputs has no wrong implementation to
# write a uniqueness rival from; a lemma the checker accepts at a statement Benchproofer
# generates decides the kind instead (`core.determinism`). The text is Lean's whatever this
# double's comment token, since that is the syntax the statement is generated from.


class Scripting(Proving):
    """A prover whose file carries a proof region, so a lemma has somewhere to live."""

    name = "scripting"
    proof_carrying = True


PINNED = """\
# benchproofer:begin spec
def Spec (n : Nat) (result : Nat) : Prop :=
  result = n + n
# benchproofer:end spec
# benchproofer:begin impl
def impl (n : Nat) : Nat :=
  2 * n
# benchproofer:end impl
# benchproofer:begin proof
theorem impl_meets_spec (n : Nat) : Spec n (impl n) := by
  unfold Spec impl; omega
# benchproofer:end proof
"""
#: The determinism statement generated from `PINNED`'s specification region.
DETERMINED = "∀ x1 r1 r2, Spec x1 r1 → Spec x1 r2 → r1 = r2"


def pinned(bundle: Bundle) -> None:
    """Rivals over `PINNED` with no uniqueness case, since there is none to write."""
    restaged(bundle, PINNED)
    body = parse(PINNED, COMMENT)["impl"].text
    battery(
        bundle,
        cased("soundness-1", "soundness", "def impl (n : Nat) : Nat :=\n  n + n\n", PINNED),
        cased(
            "admissibility-1",
            "admissibility",
            f"{body}\n\nexample : Spec 3 (impl 3) := by decide\n",
            PINNED,
        ),
    )


def test_a_lemma_the_checker_accepts_decides_the_uniqueness_question(
    sound: Bundle, settings: Settings
) -> None:
    """For every input at once, which is more than any set of rivals shows.

    It is asked before any case is run, since its result decides whether a kind is missing.
    """
    pinned(sound)
    rigged = context(sound, settings, backend=Scripting())

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["determinism"] == DETERMINED
    assert (
        "admits only one result per input is decided by a determinism lemma" in verdict.summary
    )
    assert rigged.checked[:2] == ["solution", "determinism"]


def test_a_lemma_the_checker_refuses_leaves_the_uniqueness_question_unasked(
    sound: Bundle, settings: Settings
) -> None:
    """A statement the file cannot prove says nothing, so the missing kind is still missing."""
    pinned(sound)
    rigged = context(
        sound,
        settings,
        backend=Scripting(),
        answers={"determinism": CheckResult.no("unsolved goals")},
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.summary.endswith("no uniqueness case")


def test_a_uniqueness_case_that_is_there_is_judged_and_the_lemma_is_not_asked(
    sound: Bundle, settings: Settings
) -> None:
    """The lemma decides a kind that is *absent*, not a case that behaved wrongly."""
    pinned(sound)
    manifest = sound.battery()
    sound.save_battery(
        [
            cased("uniqueness-1", "uniqueness", "def impl (n : Nat) : Nat :=\n  n\n", PINNED),
            *((rival, sound.rival_source(rival)) for rival in manifest),
        ]
    )
    rigged = context(sound, settings, backend=Scripting())

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["too_weak"] == ["uniqueness-1"]
    assert "determinism" not in rigged.checked


class Pinning(Scripting):
    """The same prover, whose rejection alone attributes nothing (`gates.attribution`)."""

    name = "pinning"
    witness_required = True


def test_a_uniqueness_case_nothing_attributes_is_decided_by_the_lemma(
    sound: Bundle, settings: Settings
) -> None:
    """A refusal at a line of the case's own witness decides nothing about the spec.

    The lemma does, for every input at once, so the case is recorded rather than erroring
    the property-based test suite: what it failed to establish is established.
    """
    pinned(sound)
    manifest = sound.battery()
    sound.save_battery(
        [
            cased("uniqueness-1", "uniqueness", "def impl (n : Nat) : Nat :=\n  n\n", PINNED),
            *((rival, sound.rival_source(rival)) for rival in manifest),
        ]
    )
    rigged = context(
        sound,
        settings,
        backend=Pinning(),
        answers={slot("uniqueness-1"): CheckResult.no("Spec does not hold")},
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["decided_by_lemma"] == ["uniqueness-1"]
    assert "unattributed" not in verdict.details
    assert "decided by that lemma instead" in verdict.summary
    evidence = (sound.evidence_dir / "battery.txt").read_text()
    assert "uniqueness-1: decided by the determinism lemma\n" in evidence


def test_a_lemma_decides_the_uniqueness_question_a_set_aside_case_left_unasked(
    sound: Bundle, settings: Settings
) -> None:
    """A repeat is no evidence, so the kind it was in is asked again of the lemma."""
    pinned(sound)
    body = parse(PINNED, COMMENT)["impl"].text
    sound.save_battery(
        [
            cased("uniqueness-1", "uniqueness", body, PINNED),
            *((rival, sound.rival_source(rival)) for rival in sound.battery()),
        ]
    )
    rigged = context(sound, settings, backend=Scripting())

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["determinism"] == DETERMINED
    assert verdict.details["defects"] == {"set_aside": ["uniqueness-1"]}
    assert "set aside and not counted toward the gate's result: uniqueness-1" in verdict.summary
    assert slot("uniqueness-1") not in rigged.checked


def test_a_uniqueness_case_nothing_attributes_still_errors_without_the_lemma(
    sound: Bundle, settings: Settings
) -> None:
    """Nothing else decides it: neither the checker's word nor the case's own rationale."""
    pinned(sound)
    manifest = sound.battery()
    sound.save_battery(
        [
            cased("uniqueness-1", "uniqueness", "def impl (n : Nat) : Nat :=\n  n\n", PINNED),
            *((rival, sound.rival_source(rival)) for rival in manifest),
        ]
    )
    rigged = context(
        sound,
        settings,
        backend=Pinning(),
        answers={
            slot("uniqueness-1"): CheckResult.no("Spec does not hold"),
            "determinism": CheckResult.no("unsolved goals"),
        },
    )

    verdict = BatteryGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert verdict.details["unattributed"] == ["uniqueness-1"]
