# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The gates that read a recorded review.

What is pinned down is what they refuse to believe -- a submission aimed at a
specification the bundle no longer ships, one that turns the checker off, one filed twice
or repeating the shipped implementation, one nothing can run, a self-review, a judgment
reached from files that have since changed -- each beside the case it must not be
confused with. `audit.spec_completeness` and `audit.spec_soundness` read the same re-run
rows for opposite findings, in one pass of the checker and the oracle.

The checker and the benchmark's oracle answer from a script (`tests/doubles.py`); the
screens and the counting are the tool's own.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pytest

from benchproofer.audit.session import ROLE_READS
from benchproofer.backends.base import CheckResult
from benchproofer.config import Settings
from benchproofer.core import determinism, echo
from benchproofer.core.bundle import (
    AuditRole,
    Bundle,
    Coverage,
    Judgment,
    Operation,
    Review,
    Ruling,
    Submission,
)
from benchproofer.core.markers import parse, replace_region
from benchproofer.core.readings import CITES, IMPL, SPEC_UNCOMMENTED, readings, ruling_reads
from benchproofer.core.task import OracleSpec, Task
from benchproofer.core.verdict import Level, SkipReason, Status, Verdict
from benchproofer.gates.audit import (
    UNRULED,
    DisclosureJudgmentGate,
    EquivalenceJudgmentGate,
    FaithfulnessJudgmentGate,
    IndependenceGate,
    SpecCompletenessGate,
    SpecSoundnessGate,
)
from benchproofer.gates.base import Gate
from benchproofer.gates.reference import ATTEMPTS
from benchproofer.oracles.base import OracleResult
from benchproofer.pipeline.report import summarize
from benchproofer.pipeline.route import Route, route
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_text, write_json, write_text
from doubles import Proving, Rigged, Screening

COMMENT = "#"
AUTHOR = "provider:drafting-model"
REVIEWER = "provider:reviewing-model"
ATTACK = "the specification accepts this, and it does not solve the task"
CONTROL = "this solves the task, and the specification should accept it"
EVIDENCE = ["evidence/audit-submissions.txt"]

#: Wrong: it never hands out a nickel, which is the bug the task is about.
NO_NICKEL = """\
def impl(cents):
    quarters = cents // 25
    remainder = cents - quarters * 25
    dimes = remainder // 10
    pennies = remainder - dimes * 10
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
#: Accepted for a reason that has nothing to do with the specification.
RIGGED = """\
def impl(cents):
    assume(False)
    return (0, 0, 0, 0)
"""
#: Every judgment gate, with the role it reports.
JUDGMENT_GATES: tuple[tuple[type[Gate], AuditRole], ...] = (
    (FaithfulnessJudgmentGate, "faithfulness"),
    (EquivalenceJudgmentGate, "equivalence"),
    (DisclosureJudgmentGate, "disclosure"),
)
#: Every gate that reads the review directory.
AUDIT_GATES: tuple[type[Gate], ...] = (
    IndependenceGate,
    SpecCompletenessGate,
    SpecSoundnessGate,
    *(gate for gate, _ in JUDGMENT_GATES),
)


# ---- writing a review ----------------------------------------------------

Filed = tuple[Submission, dict[str, str]]


def transcribed(impl: str) -> str:
    """One implementation as something the benchmark's own tests can run."""
    return (
        "# benchproofer:target change.py\n"
        f"{impl}\n\n"
        "def make_change(cents):\n"
        "    return impl(cents)\n"
    )


#: The bundle's `conformance.py`, marking the implementation it carries: a
#: submission is judged by running it with the submission's code in that region.
HARNESS = """\
import change


def shadow(cents):
# benchproofer:begin impl
    quarters = cents // 25
    return (quarters, 0, 0, cents - quarters * 25)
# benchproofer:end impl


for cents in range(5000):
    assert change.make_change(cents) == shadow(cents)
print("benchproofer:compared change.make_change 5000 every amount under 5000")
"""

#: What `conformance.py` prints when the submission in it behaves like the repository, and
#: when the repository catches it out on a named input.
AGREES = OracleResult.ok(
    "conformance exited 0",
    output="benchproofer:compared change.make_change 5000 every amount under 5000\n",
)
DISAGREES = OracleResult.no(
    "conformance exited 1",
    output=(
        "benchproofer:disagrees change.make_change 30 -> the repository returns "
        "(1, 0, 1, 0), the submission returns (1, 0, 0, 5)\n"
    ),
)


def filed(
    name: str,
    source: str,
    *,
    kind: str = "weakness",
    shadow: str = "",
    claim: str = ATTACK,
) -> Filed:
    """One submission as the review stage writes it: the file, and its runnable form."""
    files = {f"{name}.py": source}
    if shadow:
        files[f"{name}.shadow.py"] = shadow
    return (
        Submission(
            id=name,
            file=f"{name}.py",
            kind=kind,  # type: ignore[arg-type]
            shadow=f"{name}.shadow.py" if shadow else "",
            claim=claim,
        ),
        files,
    )


def attacking(name: str, solution: str, impl: str, **fields: str) -> Filed:
    """An attack: one implementation spliced into the shipped specification."""
    fields.setdefault("shadow", transcribed(impl))
    return filed(name, replace_region(solution, COMMENT, "impl", impl), **fields)


def controlling(name: str, solution: str, impl: str, **fields: str) -> Filed:
    """A control: the same file, filed as an implementation that should be accepted."""
    fields.setdefault("claim", CONTROL)
    return attacking(name, solution, impl, kind="control", **fields)


def shipped_impl(bundle: Bundle) -> str:
    """The implementation the bundle itself ships, for a submission that repeats it."""
    return parse(bundle.solution(), COMMENT)["impl"].text


#: What a ruling of the attack validation auditor names: the input, and the FAIL_TO_PASS test
#: it rests on.
RULED_INPUT = "make_change(40)"
RULED_ON = "test_forty_cents"


def rule_on(
    bundle: Bundle,
    name: str,
    ruling: str,
    *,
    named: bool = True,
    asked: int = 1,
) -> Ruling:
    """Record the attack validation auditor's ruling on one submission of the review on record.

    Stamped with what it is reached from as the files now read, as the review stage stamps one.
    """
    review = bundle.audit()
    assert review is not None
    submission = next(item for item in review.submissions if item.id == name)
    digests = readings(bundle, Screening())
    record = Ruling(
        id=name,
        ruling=ruling,
        input=RULED_INPUT if named else "",
        rests_on=RULED_ON,
        why="the fixed code returns a nickel there",
        asked=asked,
        reads=ruling_reads(submission, digests),
    )
    bundle.save_audit(review.model_copy(update={"rulings": (*review.rulings, record)}), {})
    return record


def reviewed(
    bundle: Bundle,
    *submissions: Filed,
    judgments: Sequence[Judgment] = (),
    reviewer: str = REVIEWER,
    author: str = AUTHOR,
    independent: bool = True,
    harness: str = HARNESS,
) -> Review:
    """Write a review into the bundle, the way ``benchproofer audit`` writes one."""
    record = Review(
        reviewer=reviewer,
        author=author,
        independent=independent,
        submissions=tuple(submission for submission, _ in submissions),
        judgments=tuple(judgments),
    )
    sources: dict[str, str] = {}
    for _, files in submissions:
        sources.update(files)
    bundle.save_audit(record, sources)
    # A bundle judged at this level has a `conformance.py` to run a submission through.
    write_text(bundle.conformance_path, harness)
    return record


def judged(
    bundle: Bundle,
    role: AuditRole,
    verdict: str,
    *,
    summary: str = "",
    findings: Iterable[str] = (),
    operations: Iterable[Operation] = (),
    coverage: Iterable[Coverage] | None = None,
    reads: dict[str, str] | None = None,
) -> Judgment:
    """A judgment stamped with what its role read, as the review stage stamps one.

    A faithfulness judgment carries a coverage table unless one is given: a row the
    sound fixture's specification states. It reads `conformance.py` too, written as `HARNESS`.
    """
    write_text(bundle.conformance_path, HARNESS)
    digests = readings(bundle, BACKENDS.get(bundle.backend_name))
    names = ROLE_READS[role]
    if coverage is None:
        coverage = (COVERED,) if role == "faithfulness" else ()
    return Judgment(
        role=role,
        verdict=verdict,  # type: ignore[arg-type]
        summary=summary,
        findings=tuple(findings),
        operations=tuple(operations),
        coverage=tuple(coverage),
        reads={name: digests[name] for name in names if name in digests}
        if reads is None
        else reads,
    )


#: A behavior the coin-change task's test checks, and the line of the sound fixture's
#: specification that states it.
COVERED = Coverage(
    behavior="the change is the fewest coins",
    tested_by="the task's test program",
    covered_by="assert nickels * 5 + pennies < 10",
)


def preserving(*kinds: str) -> tuple[Operation, ...]:
    """One behavior-preserving correspondence per kind named."""
    return tuple(
        Operation(kind=kind, detail=f"operation {index}")  # type: ignore[arg-type]
        for index, kind in enumerate(kinds)
    )


def context(
    bundle: Bundle,
    settings: Settings,
    *,
    backend: Screening | None = None,
    attacks: int = 1,
    controls: int = 1,
    **rigging: object,
) -> Rigged:
    """A context that judges this bundle at level audited, with scripted answers."""
    return Rigged(
        bundle=bundle,
        backend=backend or Screening(),
        settings=settings.model_copy(
            update={"audit_min_attacks": attacks, "audit_min_controls": controls}
        ),
        level=Level.AUDITED,
        output=rigging.pop("output", DISAGREES),  # type: ignore[arg-type]
        **rigging,  # type: ignore[arg-type]
    )


def slot(name: str) -> str:
    """The name a submission gate checks one submission under."""
    return f"submission-{name}"


# ---- an absent or unreadable review --------------------------------------


@pytest.mark.parametrize("gate", AUDIT_GATES, ids=lambda gate: gate.id)
def test_a_bundle_with_no_review_is_not_a_bundle_that_passed_one(
    gate: type[Gate], sound: Bundle, settings: Settings
) -> None:
    verdict = gate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.ARTIFACT_ABSENT
    assert "benchproofer audit" in verdict.summary


@pytest.mark.parametrize("gate", AUDIT_GATES, ids=lambda gate: gate.id)
def test_an_unreadable_review_is_reported_rather_than_read_as_no_review(
    gate: type[Gate], sound: Bundle, settings: Settings
) -> None:
    """A record of an audit nobody can read must not look like a bundle nobody audited."""
    write_text(sound.audit_dir / "index.toml", "submissions = 3\n")

    verdict = gate().run(context(sound, settings))

    assert verdict.status is Status.FAIL


# ---- audit.spec_completeness: is the specification too weak? -------------


def test_an_attack_the_checker_refutes_is_the_specification_doing_its_job(
    sound: Bundle, settings: Settings
) -> None:
    """And the oracle is never asked about it: a refuted attack is already decided."""
    reviewed(sound, attacking("no-nickel", sound.solution(), NO_NICKEL))
    rigged = context(
        sound, settings, answers={slot("no-nickel"): CheckResult.no("failed on cents=40")}
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["refuted"] == ["no-nickel"]
    assert verdict.details["checked"] == 1
    assert verdict.details["rulings"]["no-nickel"].startswith(
        "checker: refuted; the attack fails: the checker refutes it"
    )
    assert verdict.summary.startswith("1 attack(s) failed: the checker refuted 1")
    assert rigged.probed == []
    assert verdict.evidence == EVIDENCE


@pytest.mark.parametrize(
    ("backend", "status"),
    [(Proving(), Status.FAIL), (Screening(), Status.SKIP)],
    ids=["prover", "falsifier"],
)
def test_an_attack_the_checker_accepts_and_the_oracle_rejects_is_the_finding(
    backend: Screening, status: Status, sound: Bundle, settings: Settings
) -> None:
    """Under a prover a proof of weakness; under a falsifier a search shortfall.

    The finding is recorded either way, so a repair still addresses it, but a slow machine
    cannot manufacture a defect in a sound specification.
    """
    reviewed(sound, attacking("no-nickel", sound.solution(), NO_NICKEL))
    rigged = context(sound, settings, backend=backend)

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is status
    if status is Status.SKIP:
        assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["too_weak"] == ["no-nickel"]
    assert verdict.details["claims"] == [ATTACK]
    assert [program.label for program in rigged.probed] == [slot("no-nickel")]


def test_a_submission_aimed_at_a_specification_the_bundle_no_longer_ships_decides_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """After a repair, an attack on the old specification answers nothing about this one.

    It is set aside like any other screened submission, and the attack auditor asked again.
    """
    drifted = replace_region(
        replace_region(sound.solution(), COMMENT, "impl", NO_NICKEL),
        COMMENT,
        "spec",
        "def property_nothing(cents):\n    assert True\n",
    )
    reviewed(sound, filed("stale", drifted, shadow=transcribed(NO_NICKEL)))
    rigged = context(sound, settings)

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "required" in verdict.details
    assert "set aside: 1 specification differs (stale)" in verdict.summary
    assert verdict.details["rulings"]["stale"].startswith("checker: specification differs")
    assert rigged.checked == ["solution"]


def test_a_submission_that_wins_by_turning_the_checker_off_is_set_aside(
    sound: Bundle, settings: Settings
) -> None:
    """`assume(False)` makes every property hold, which is not the specification's doing."""
    reviewed(sound, attacking("rigged", sound.solution(), RIGGED))
    rigged = context(sound, settings)

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert (
        "set aside: 1 uses a construct the solution file does not (rigged)" in verdict.summary
    )
    assert rigged.checked == ["solution"]


def test_two_submissions_with_the_same_implementation_count_as_one(
    sound: Bundle, settings: Settings
) -> None:
    """Indentation aside, one attack filed twice has attacked once."""
    solution = sound.solution()
    reviewed(
        sound,
        attacking("first", solution, NO_NICKEL),
        attacking("again", solution, NO_NICKEL.replace("    ", "        ")),
    )
    rigged = context(
        sound, settings, attacks=2, answers={slot("first"): CheckResult.no("failed")}
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "set aside: 1 duplicate (again)" in verdict.summary
    assert verdict.details["checked"] == 1
    assert rigged.checked == ["solution", slot("first")]


def test_a_submission_that_repeats_the_bundles_own_implementation_decides_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """It would verify and be judged correct, which the bundle already records itself."""
    reviewed(sound, controlling("copy", sound.solution(), shipped_impl(sound)))
    rigged = context(sound, settings)

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "set aside: 1 duplicate (copy)" in verdict.summary
    assert rigged.checked == ["solution"]
    assert rigged.probed == []


def test_a_submission_that_only_comments_the_bundles_own_implementation_decides_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """A comment is not code, so the shipped body with one added is still the shipped one."""
    commented = shipped_impl(sound).replace("\n", "\n    # the shipped body, restated\n", 1)
    reviewed(sound, attacking("commented", sound.solution(), f"{commented}  # unchanged"))
    rigged = context(sound, settings)

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "set aside: 1 duplicate (commented)" in verdict.summary
    assert rigged.checked == ["solution"]


def test_a_hash_inside_a_string_is_code_when_telling_submissions_apart(
    sound: Bundle, settings: Settings
) -> None:
    """Two attacks that differ only after a ``#`` in a string literal are two attacks."""
    solution = sound.solution()
    labelled = 'def impl(cents):\n    tag = "#{}"\n    return (0, 0, 0, cents)\n'
    reviewed(
        sound,
        attacking("first", solution, labelled.format("pennies")),
        attacking("second", solution, labelled.format("nickels")),
    )
    refuted = CheckResult.no("failed")
    rigged = context(
        sound, settings, attacks=2, answers={slot("first"): refuted, slot("second"): refuted}
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert "duplicate" not in verdict.summary
    assert rigged.checked == ["solution", slot("first"), slot("second")]


def test_a_submission_with_no_readable_regions_is_not_one_the_specification_defeated(
    sound: Bundle, settings: Settings
) -> None:
    reviewed(sound, filed("unreadable", "def impl(cents):\n    return ()\n"))

    verdict = SpecCompletenessGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert "set aside: 1 unreadable (unreadable)" in verdict.summary


def test_a_file_the_checker_rejected_without_reading_is_not_a_defeated_attack(
    sound: Bundle, settings: Settings
) -> None:
    """A syntax error is deterministic and says nothing about the specification."""
    reviewed(sound, attacking("broken", sound.solution(), "def impl(cents:\n"))
    rigged = context(
        sound, settings, answers={slot("broken"): CheckResult.malformed("SyntaxError")}
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "set aside: 1 unreadable (broken)" in verdict.summary


@pytest.mark.parametrize(
    ("kind", "gate"),
    [("weakness", SpecCompletenessGate), ("control", SpecSoundnessGate)],
    ids=["attack", "control"],
)
def test_a_submission_the_checker_never_decided_is_set_aside_unasked(
    kind: str, gate: type[Gate], sound: Bundle, settings: Settings
) -> None:
    """A checker that ran out of time neither refuted an attack nor refused a control.

    Read as a refutation, a loaded machine would credit a weak specification with an
    attack nobody ran, or turn the slowest bundles into the ones with the most too-strong
    findings. The oracle is not asked: there is no answer for it to weigh.
    """
    make = controlling if kind == "control" else attacking
    reviewed(
        sound, make("slow", sound.solution(), NO_NICKEL if kind == "weakness" else BY_LOOP)
    )
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={slot("slow"): CheckResult.unknown("no verdict within 120s", timed_out=True)},
        output=AGREES,
    )

    verdict = gate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "set aside: 1 undecided: the checker reached no verdict (slow)" in verdict.summary
    assert rigged.probed == []


def test_a_review_that_filed_fewer_attacks_than_the_run_asks_for_is_inconclusive(
    sound: Bundle, settings: Settings
) -> None:
    """Surviving one attack is not evidence when the run asked for three.

    The attack is re-run all the same: an unmet bar is a reason not to pass, never a
    reason to leave a defect the rows contain unreported.
    """
    reviewed(sound, attacking("no-nickel", sound.solution(), NO_NICKEL))
    rigged = context(
        sound, settings, attacks=3, answers={slot("no-nickel"): CheckResult.no("failed")}
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["filed"] == 1
    assert verdict.details["required"] == 3
    assert route(verdict) is Route.ASK_AGAIN
    assert rigged.checked == ["solution", slot("no-nickel")]


#: The bundle's `conformance.py` with the markers of the implementation it carries taken out.
UNMARKED = HARNESS.replace("# benchproofer:begin impl\n", "").replace(
    "# benchproofer:end impl\n", ""
)


@pytest.mark.parametrize(
    "output",
    [
        "benchproofer:compared change.make_change[every amount] 5000 amounts under 5000\n",
        AGREES.output + "benchproofer:disagree change.make_change 30 -> 4, the submission 3\n",
    ],
    ids=["alone", "beside-a-comparison"],
)
def test_a_submission_run_printing_a_line_no_reader_parses_is_undecided_and_names_it(
    sound: Bundle, settings: Settings, output: str
) -> None:
    """What that line said was not read, and it may have been the disagreement.

    Alone, it would leave the submission undecided for a reason nobody could see;
    beside a comparison that parses, it would rule the submission correct over a run
    whose disagreement went unread. Either way the line is named in the record.
    """
    reviewed(sound, attacking("by-loop", sound.solution(), BY_LOOP))
    rigged = context(sound, settings, output=OracleResult.ok("exited 0", output=output))

    verdict = SpecCompletenessGate().run(rigged)

    assert (
        "set aside: 1 undecided: no verdict on whether the attack succeeds (by-loop)"
        in verdict.summary
    )
    rows = (sound.evidence_dir / "audit-submissions.txt").read_text()
    assert f"printed `{output.splitlines()[-1]}`, which no line" in rows


def test_conformance_py_is_run_with_the_submission_in_place_of_the_drafters_code(
    sound: Bundle, settings: Settings
) -> None:
    """Everything but the implementation stays byte-identical.

    How a comparison draws inputs and reaches the repository is what makes a
    submission's answer comparable with the bundle's own.
    """
    reviewed(sound, attacking("no-nickel", sound.solution(), NO_NICKEL))
    rigged = context(sound, settings, backend=Proving())

    SpecCompletenessGate().run(rigged)

    (program,) = rigged.probed
    assert program.label == slot("no-nickel")
    assert program.with_reference
    assert "dimes = remainder // 10" in program.source
    assert "quarters = cents // 25\n    return (quarters" not in program.source
    for line in ("import change", "for cents in range(5000):", "benchproofer:compared"):
        assert line in program.source


@pytest.mark.parametrize(
    "gate", (SpecCompletenessGate, SpecSoundnessGate), ids=lambda gate: gate.id
)
def test_a_specification_that_does_not_verify_is_not_measured_by_its_submissions(
    gate: type[Gate], sound: Bundle, settings: Settings
) -> None:
    """Every variant of a rejected implementation is rejected, which measures nothing."""
    reviewed(
        sound,
        attacking("no-nickel", sound.solution(), NO_NICKEL),
        controlling("by-loop", sound.solution(), BY_LOOP),
    )
    rigged = context(sound, settings, answers={"solution": CheckResult.no("cents=40")})

    verdict = gate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "spec.verifies (Verification check) is where that is recorded" in verdict.summary
    assert rigged.checked == ["solution"]


@pytest.mark.parametrize(
    "gate", (SpecCompletenessGate, SpecSoundnessGate), ids=lambda gate: gate.id
)
def test_a_benchmark_with_no_oracle_of_its_own_cannot_support_either_finding(
    gate: type[Gate], sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """Nothing else can say what an implementation the checker answered about is worth."""
    write_json(
        sound.task_path,
        coin_change.model_copy(update={"oracle": OracleSpec()}).model_dump(mode="json"),
    )
    reviewed(
        sound,
        attacking("no-nickel", sound.solution(), NO_NICKEL),
        controlling("by-loop", sound.solution(), BY_LOOP),
    )

    verdict = gate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.ORACLE_UNAVAILABLE


# ---- audit.spec_soundness: is the specification too strong? --------------


def refused_at(source: str, region: str, message: str) -> CheckResult:
    """A prover's refusal placed on the first line inside one region of ``source``."""
    line = parse(source, COMMENT)[region].start + 1
    return CheckResult.no(f"solution.py:{line}:9:{line}:40: error: {message}")


#: What the attack auditor says of a control it could not get the prover to accept.
UNPROVED = "unproved: the loop needs an invariant on `cents` that no form I tried closes"


@pytest.mark.parametrize("region", ["impl", "spec"])
def test_a_control_a_prover_refuses_is_a_gap_wherever_the_refusal_is_placed(
    region: str, sound: Bundle, settings: Settings
) -> None:
    """A prover's refusal is either the specification's or a proof the control lacks.

    Its answer does not say which, and the line it names does not either: a missing loop
    invariant is reported at the postcondition it fails to establish. So the control counts
    neither way here, the oracle is not asked, and the verdict names it. Whether the
    specification is what refuses it is the attack validation auditor's to say, so the gate is
    undecided and lists it for that auditor, who is shown the claim saying what the attack
    auditor tried.
    """
    control = controlling("by-loop", sound.solution(), BY_LOOP, claim=UNPROVED)
    reviewed(sound, control)
    refusal = refused_at(control[1]["by-loop.py"], region, "Postcondition might not hold.")
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={slot("by-loop"): refusal},
        output=AGREES,
    )

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "too_strong" not in verdict.details
    assert verdict.details[UNRULED]["by-loop"].startswith("the prover refuses it, and nothing")
    assert route(verdict) is Route.ASK_AGAIN
    assert rigged.probed == []
    gap = verdict.details["rulings"]["by-loop"]
    assert gap.startswith("checker: gap") and "does not say whether the specification" in gap
    assert "Postcondition might not hold" in gap


def test_a_falsifier_s_refutation_of_a_correct_control_is_too_strong_for_it(
    sound: Bundle, settings: Settings
) -> None:
    """A falsifier's refusal is a produced counterexample.

    Unlike the too-weak finding, nothing about the search budget weakens it.
    """
    control = controlling("by-loop", sound.solution(), BY_LOOP)
    reviewed(sound, control)
    refusal = CheckResult.no("property_uses_the_fewest_coins failed on cents=30")
    rigged = context(
        sound, settings, backend=Screening(), answers={slot("by-loop"): refusal}, output=AGREES
    )

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["too_strong"] == ["by-loop"]
    assert verdict.details["claims"] == [CONTROL]
    assert verdict.evidence == EVIDENCE
    assert verdict.details["rulings"]["by-loop"].startswith("checker: refuted")


def test_a_refuted_control_nothing_could_run_is_left_to_the_attack_validation_auditor(
    sound: Bundle, settings: Settings
) -> None:
    """A falsifier refutes it, but `conformance.py` cannot say whether the control is correct.

    The control is set aside rather than counted either way, and the attack validation auditor
    is asked about it, since it may be a correct implementation the specification refuses.
    """
    reviewed(sound, controlling("by-loop", sound.solution(), BY_LOOP), harness="")
    refusal = CheckResult.no("property_uses_the_fewest_coins failed on cents=30")
    rigged = context(sound, settings, backend=Screening(), answers={slot("by-loop"): refusal})

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "too_strong" not in verdict.details
    shown = verdict.details[UNRULED]["by-loop"]
    assert shown.startswith("the checker refutes it, and nothing decided whether it is")
    assert route(verdict) is Route.ASK_AGAIN


def test_a_control_the_specification_accepts_shows_it_is_not_too_strong(
    sound: Bundle, settings: Settings
) -> None:
    reviewed(sound, controlling("by-loop", sound.solution(), BY_LOOP))
    rigged = context(sound, settings, output=AGREES)

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["admitted"] == ["by-loop"]
    assert [program.label for program in rigged.probed] == [slot("by-loop")]


def test_one_accepted_control_passes_though_the_review_is_asked_for_more(
    sound: Bundle, settings: Settings
) -> None:
    """The reviewer is asked for `audit_controls`; the gate needs `audit_min_controls`."""
    reviewed(sound, controlling("by-loop", sound.solution(), BY_LOOP))
    asked = settings.model_copy(update={"audit_controls": 3})

    verdict = SpecSoundnessGate().run(context(sound, asked, output=AGREES))

    assert verdict.status is Status.PASS
    assert (Settings().audit_controls, Settings().audit_min_controls) == (3, 1)


def test_a_control_the_benchmarks_own_tests_reject_establishes_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """The reviewer submitted it as correct; the benchmark disagreed, so it is not one."""
    reviewed(sound, controlling("wrong-control", sound.solution(), NO_NICKEL))

    verdict = SpecSoundnessGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "set aside: 1 not correct (wrong-control)" in verdict.summary


def test_a_wrong_implementation_the_spec_accepts_is_a_finding_whatever_it_was_filed_as(
    sound: Bundle, settings: Settings
) -> None:
    """The completeness gate reads every row, so a mislabeled control still convicts."""
    reviewed(sound, controlling("wrong-control", sound.solution(), NO_NICKEL))

    verdict = SpecCompletenessGate().run(context(sound, settings, backend=Proving()))

    assert verdict.status is Status.FAIL
    assert verdict.details["too_weak"] == ["wrong-control"]


def test_an_attack_the_tests_pass_is_not_a_control(sound: Bundle, settings: Settings) -> None:
    """As in `verified-swebench`, whose positive control is a file of its own.

    An attack the checker accepted and the benchmark's tests pass may still break what the
    statement asks for, which is the attack validation auditor's to rule on.
    """
    reviewed(sound, attacking("by-loop", sound.solution(), BY_LOOP))
    rigged = context(sound, settings, output=AGREES)

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.details["filed"] == 0


def test_a_faithful_verdict_stands_whatever_the_submissions_leave_open(
    sound: Bundle, settings: Settings
) -> None:
    """The faithfulness auditor judges coverage alone, as the SWE-Proof paper's does.

    An attack the tests pass is the attack validation auditor's to rule on, so the faithfulness
    verdict neither lists it nor waits for it.
    """
    reviewed(
        sound,
        attacking("no-nickel", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH),
        judgments=[judged(sound, "faithfulness", "sound")],
    )
    rigged = sequenced(sound, settings, rulings={slot("no-nickel"): RESOLVES})

    verdict = FaithfulnessJudgmentGate().run(rigged)
    completeness = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert {"passing", "unshown"}.isdisjoint(verdict.details)
    assert list(completeness.details[UNRULED]) == ["no-nickel"]


def test_a_review_that_filed_no_control_leaves_the_soundness_gate_inconclusive(
    sound: Bundle, settings: Settings
) -> None:
    """Attacks cannot show a specification is not too strong: everything refutes."""
    reviewed(sound, attacking("no-nickel", sound.solution(), NO_NICKEL))

    verdict = SpecSoundnessGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["filed"] == 0
    assert verdict.details["required"] == 1
    assert route(verdict) is Route.ASK_AGAIN


@pytest.mark.parametrize(
    "gate", (SpecCompletenessGate, SpecSoundnessGate), ids=lambda gate: gate.id
)
def test_a_run_that_asks_for_no_submissions_still_asks_for_one(
    gate: type[Gate], sound: Bundle, settings: Settings
) -> None:
    """A kind nobody submitted leaves its gate inconclusive, so zero cannot certify."""
    reviewed(sound)

    verdict = gate().run(context(sound, settings, attacks=0, controls=0))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["required"] == 1
    assert route(verdict) is Route.ASK_AGAIN


def test_the_two_directions_share_one_pass_of_the_checker_and_the_oracle(
    sound: Bundle, settings: Settings
) -> None:
    """Adding the second direction must not double what a run at this level costs."""
    solution = sound.solution()
    reviewed(
        sound,
        attacking("no-nickel", solution, NO_NICKEL),
        controlling("by-loop", solution, BY_LOOP),
    )
    rigged = context(
        sound,
        settings,
        answers={slot("no-nickel"): CheckResult.no("failed on cents=40")},
        outputs={slot("by-loop"): AGREES},
    )

    completeness = SpecCompletenessGate().run(rigged)
    soundness = SpecSoundnessGate().run(rigged)

    assert completeness.status is Status.PASS
    assert soundness.status is Status.PASS
    assert rigged.checked == ["solution", slot("no-nickel"), slot("by-loop")]
    assert [program.label for program in rigged.probed] == [slot("by-loop")]


# ---- audit.independence --------------------------------------------------


def test_a_review_written_by_the_bundles_own_author_is_not_independent(
    sound: Bundle, settings: Settings
) -> None:
    reviewed(sound, reviewer=AUTHOR, author=AUTHOR, independent=False)

    verdict = IndependenceGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL


def test_a_bundle_with_no_recorded_author_cannot_be_shown_independent(
    sound: Bundle, settings: Settings
) -> None:
    """A bundle from elsewhere need not say who wrote it, and that is not a failure."""
    reviewed(sound, author="")

    verdict = IndependenceGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE


def test_a_review_written_by_another_model_is_independent(
    sound: Bundle, settings: Settings
) -> None:
    reviewed(sound)

    verdict = IndependenceGate().run(context(sound, settings))

    assert verdict.status is Status.PASS
    assert verdict.details == {"reviewer": REVIEWER, "author": AUTHOR}


# ---- the judgment gates --------------------------------------------------


@pytest.mark.parametrize(("gate", "role"), JUDGMENT_GATES, ids=lambda item: str(item))
def test_an_unjudged_role_is_reported_as_unjudged_rather_than_sound(
    gate: type[Gate], role: AuditRole, sound: Bundle, settings: Settings
) -> None:
    reviewed(sound)

    verdict = gate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert f"filed no {role} judgment" in verdict.summary


@pytest.mark.parametrize(
    ("filed", "status"),
    [("sound", Status.PASS), ("unsound", Status.FAIL), ("uncertain", Status.SKIP)],
)
def test_a_current_judgment_is_reported_with_the_reviewers_own_summary(
    filed: str, status: Status, sound: Bundle, settings: Settings
) -> None:
    """An uncertain judgment is not a favorable one."""
    said = "the spec states what the task requires"
    reviewed(sound, judgments=[judged(sound, "faithfulness", filed, summary=said)])

    verdict = FaithfulnessJudgmentGate().run(context(sound, settings))

    assert verdict.status is status
    assert said in verdict.summary
    assert verdict.details["independent"] is True


def test_a_judgment_reached_from_a_file_that_has_since_changed_is_stale(
    sound: Bundle, settings: Settings
) -> None:
    """Not a weaker judgment: a judgment about a different bundle."""
    reviewed(sound, judgments=[judged(sound, "faithfulness", "sound", summary="fine")])
    write_text(sound.solution_path, sound.solution().replace("pennies < 5", "pennies <= 4"))

    verdict = FaithfulnessJudgmentGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["stale"] == [SPEC_UNCOMMENTED]
    assert route(verdict) is Route.ASK_AGAIN


def test_a_judgment_survives_a_change_to_a_file_its_role_never_read(
    sound: Bundle, settings: Settings
) -> None:
    """Otherwise every repair would cost a full re-review, however narrow it was."""
    reviewed(
        sound,
        judgments=[
            judged(sound, "faithfulness", "sound", summary="fine"),
            judged(sound, "disclosure", "sound", summary="says nothing away"),
        ],
    )
    write_text(sound.root / "notes.md", "the drafting log, written again\n")

    rigged = context(sound, settings)
    assert DisclosureJudgmentGate().run(rigged).status is Status.PASS
    assert FaithfulnessJudgmentGate().run(rigged).status is Status.PASS


@pytest.mark.parametrize("name", ["correspondence.md", "conformance.py"])
def test_a_faithfulness_judgment_expires_with_the_type_bridge_it_read(
    sound: Bundle, settings: Settings, name: str
) -> None:
    """Whether a clause states what a test checks may depend on the type bridge."""
    reviewed(sound, judgments=[judged(sound, "faithfulness", "sound", summary="fine")])
    write_text(sound.root / name, read_text(sound.root / name) + "\n# bridged again\n")

    verdict = FaithfulnessJudgmentGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.details["stale"] == [name]


def test_a_repair_to_the_implementation_alone_expires_only_equivalence(
    sound: Bundle, settings: Settings
) -> None:
    """The specification a solver sees is what faithfulness and disclosure read."""
    reviewed(
        sound,
        judgments=[
            judged(sound, "faithfulness", "sound", summary="fine"),
            judged(sound, "disclosure", "sound", summary="says nothing away"),
            judged(
                sound,
                "equivalence",
                "sound",
                summary="same",
                operations=preserving("identical"),
            ),
        ],
    )
    write_text(
        sound.solution_path,
        sound.solution().replace(
            "pennies = remainder - nickels * 5", "pennies = remainder % 5"
        ),
    )

    rigged = context(sound, settings)
    assert FaithfulnessJudgmentGate().run(rigged).status is Status.PASS
    assert DisclosureJudgmentGate().run(rigged).status is Status.PASS
    stale = EquivalenceJudgmentGate().run(rigged)
    assert stale.status is Status.SKIP and stale.details["stale"] == [IMPL]
    assert route(stale) is Route.ASK_AGAIN


def test_a_comment_in_the_implementation_expires_nothing(
    sound: Bundle, settings: Settings
) -> None:
    reviewed(
        sound,
        judgments=[
            judged(
                sound,
                "equivalence",
                "sound",
                summary="same",
                operations=preserving("identical"),
            ),
        ],
    )
    write_text(
        sound.solution_path,
        sound.solution().replace(
            "    quarters = cents // 25\n", "    # quarters first\n    quarters = cents // 25\n"
        ),
    )

    assert EquivalenceJudgmentGate().run(context(sound, settings)).status is Status.PASS


@pytest.mark.parametrize("verdict", ["sound", "unsound"])
def test_the_reviewers_verdict_decides_and_its_table_goes_to_the_repair(
    verdict: str, sound: Bundle, settings: Settings
) -> None:
    """As in `verified-swebench`, the evidence beside a verdict never turns it around.

    The rows naming a test that no obligation states are listed apart, for a repair to be
    shown; a row no test checks is not among them.
    """
    gap = Coverage(behavior="a negative amount is refused", tested_by="test_negative")
    aside = Coverage(behavior="the docstring mentions nickels")
    reviewed(
        sound,
        judgments=[judged(sound, "faithfulness", verdict, coverage=[COVERED, gap, aside])],
    )

    found = FaithfulnessJudgmentGate().run(context(sound, settings))

    assert found.status is (Status.PASS if verdict == "sound" else Status.FAIL)
    assert len(found.details["coverage"]) == 3
    assert [row.split(" | ")[0] for row in found.details["uncovered"]] == [
        "a negative amount is refused"
    ]


def test_a_judgment_that_records_nothing_it_read_cannot_be_placed(
    sound: Bundle, settings: Settings
) -> None:
    """A vacuously current judgment is not a current one."""
    reviewed(sound, judgments=[judged(sound, "faithfulness", "sound", reads={})])

    verdict = FaithfulnessJudgmentGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "records nothing it was reached from" in verdict.summary


# ---- audit.equivalence and audit.no_disclosure: the verdict decides --------


@pytest.mark.parametrize(
    ("verdict", "operations"),
    [
        ("sound", preserving("identical", "identical", "refinement", "axiom")),
        ("sound", (*preserving("identical"), Operation(kind="changed", detail="a guard"))),
        ("sound", preserving("identical", "unbridged")),
        ("sound", ()),
        ("unsound", preserving("identical", "identical")),
    ],
    ids=["rewritings", "a changed row", "unbridged, nothing declared", "none", "unsound"],
)
def test_the_equivalence_verdict_decides_and_its_operations_are_evidence(
    verdict: str, operations: tuple[Operation, ...], sound: Bundle, settings: Settings
) -> None:
    """As `verified-swebench`'s panels: what the judgment shows never flips a pass.

    Each operation goes into the details with its kind, for a reader and a repair. The rules
    tell the reviewer that a `changed` row, or an `unbridged` one `correspondence.md` does
    not declare, makes the verdict `unsound`.
    """
    reviewed(
        sound,
        judgments=[
            judged(sound, "equivalence", verdict, summary="as filed", operations=operations)
        ],
    )

    reported = EquivalenceJudgmentGate().run(context(sound, settings))

    assert reported.status is (Status.PASS if verdict == "sound" else Status.FAIL)
    assert reported.summary == "as filed"
    listed = [f"{item.kind}: {item.detail}" for item in operations]
    assert reported.details.get("operations", []) == listed


def test_a_bundle_with_no_correspondence_md_fails_equivalence_for_a_repair_to_write_one(
    sound: Bundle, settings: Settings
) -> None:
    """Whatever the review judged: the file is the claim the judgment checks."""
    reviewed(sound, judgments=[judged(sound, "equivalence", "sound", summary="as filed")])
    sound.correspondence_path.unlink()

    reported = EquivalenceJudgmentGate().run(context(sound, settings))

    assert reported.status is Status.FAIL
    assert route(reported) is Route.REPAIR
    assert "ships no correspondence.md" in reported.summary


@pytest.mark.parametrize(
    "finding",
    [
        "loop: this line walks the result: `assert all(count >= 0 for count in impl(cents))`",
        "the whole thing gives the algorithm away",
        "this line is transcribable and closes by rfl: `assert all(count >= 0 for count in "
        "impl(cents))`",
    ],
    ids=["quotes a line", "quotes nothing", "names no construct"],
)
def test_the_disclosure_verdict_decides_whatever_its_findings_quote(
    finding: str, sound: Bundle, settings: Settings
) -> None:
    """The rules ask a finding to quote its line; the gate does not check that it does."""
    reviewed(
        sound,
        judgments=[
            judged(
                sound,
                "disclosure",
                "unsound",
                summary="the specification spells out the answer",
                findings=[finding],
            )
        ],
    )

    verdict = DisclosureJudgmentGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL
    assert verdict.summary == "the specification spells out the answer"
    assert verdict.details["findings"] == [finding]


def test_a_sound_disclosure_judgment_needs_no_quotation(
    sound: Bundle, settings: Settings
) -> None:
    """There is no line to point at, which is the whole content of the verdict."""
    reviewed(
        sound,
        judgments=[
            judged(sound, "disclosure", "sound", summary="it states the requirement only")
        ],
    )

    verdict = DisclosureJudgmentGate().run(context(sound, settings))

    assert verdict.status is Status.PASS


def test_the_disclosure_judgment_does_not_expire_when_the_golden_patch_changes(
    sound: Bundle, settings: Settings
) -> None:
    """The reviewer was never shown it, so neither the gate nor the role may read it."""
    assert "../reference.patch" not in DisclosureJudgmentGate.sources
    assert "../reference.patch" not in ROLE_READS["disclosure"]


# ---- a submission that cannot run as written -----------------------------


class Sequenced(Proving):
    """A prover whose implementations may use a value only the verifier has, as Nagini's do."""

    name = "sequenced"
    foreign_tokens = ("PSeq",)


#: `NO_NICKEL` returning a sequence the verifier owns: no `conformance.py` can run it as it
#: stands.
NO_NICKEL_SEQ = """\
def impl(cents):
    quarters = cents // 25
    remainder = cents - quarters * 25
    dimes = remainder // 10
    return PSeq(quarters, dimes, 0, remainder - dimes * 10)
"""
#: `BY_LOOP` over the same sequence.
BY_LOOP_SEQ = """\
def impl(cents):
    counts = PSeq()
    for coin in (25, 10, 5, 1):
        counts = counts + PSeq(cents // coin)
        cents = cents - (cents // coin) * coin
    return counts
"""
#: The attack as the reviewer puts it into the repository.
ATTACK_PATCH = """\
diff --git a/change.py b/change.py
--- a/change.py
+++ b/change.py
@@ -1,3 +1,3 @@
 def make_change(cents):
-    return greedy(cents, (25, 10, 5, 1))
+    return greedy(cents, (25, 10, 1))
"""
RESOLVES = OracleResult.ok("2 FAIL_TO_PASS and 5 PASS_TO_PASS test(s) passed")
FAILS = OracleResult.no("1 FAIL_TO_PASS test(s) failing", failed=("test_forty_cents",))


def sequenced(
    bundle: Bundle, settings: Settings, *, backend: Screening | None = None, **rigging: object
) -> Rigged:
    """A context under ``backend``, `Sequenced` unless given, whose benchmark passes its fix."""
    rulings = {"reference": RESOLVES, **rigging.pop("rulings", {})}  # type: ignore[dict-item]
    return context(bundle, settings, backend=backend or Sequenced(), rulings=rulings, **rigging)


#: `NO_NICKEL` through a helper of the solution's that the bundle's `conformance.py` never
#: carries.
NO_NICKEL_HELPED = """\
def impl(cents):
    return without_nickels(cents)
"""


@pytest.mark.parametrize(
    ("failed", "said"),
    [
        (("test_forty_cents",), "(fails FAIL_TO_PASS test(s): test_forty_cents)"),
        (
            ("test_kept",),
            "(passes every FAIL_TO_PASS test, and fails PASS_TO_PASS test(s): test_kept)",
        ),
        (
            ("test_forty_cents", "test_kept"),
            "(fails FAIL_TO_PASS test(s): test_forty_cents; and PASS_TO_PASS test(s): "
            "test_kept)",
        ),
    ],
    ids=["the-fix", "what-it-keeps", "both"],
)
def test_a_wrong_implementation_is_reported_with_the_half_of_correct_it_broke(
    failed: tuple[str, ...], said: str, sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """Failing a test the fix makes pass, and only one it keeps passing, are opposite repairs.

    The first does not fix the bug; the second fixes it and breaks a property the fix
    preserves, which is what the specification then has to state.
    """
    _naming(sound, coin_change, "test_forty_cents", regression=("test_kept",))
    reviewed(sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    rejected = OracleResult.no("the patch broke a test", failed=failed)
    rigged = sequenced(sound, settings, rulings={slot("attack"): rejected})

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert f"accepts: attack {said}" in verdict.summary


@pytest.mark.parametrize(
    ("result", "ruled", "summary"),
    [
        (
            OracleResult.no("the patch broke a test", failed=("test_forty_cents",)),
            "checker: verified; the attack succeeds: its implementation is wrong and the "
            "specification accepts it",
            "attack(s) succeed, each a wrong implementation the specification accepts",
        ),
        (
            RESOLVES,
            "checker: verified; the attack fails, by the attack validation auditor's ruling",
            "the attack validation auditor ruled that 1 fail",
        ),
    ],
    ids=["succeeds", "fails"],
)
def test_what_the_gates_ruled_of_an_attack_says_whether_it_succeeds_and_why(
    result: OracleResult, ruled: str, summary: str, sound: Bundle, settings: Settings
) -> None:
    """The next review and the repair read the ruling, so it says what the attack showed.

    An attack succeeds where its implementation is wrong and the specification accepts it,
    and fails where its implementation is correct, here by the attack validation auditor's
    ruling on one whose patch the tests pass; what decided it follows.
    """
    reviewed(sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    if result.resolved:
        rule_on(sound, "attack", "fails")
    alone = settings.model_copy(update={"audit_min_attacks": 1})
    rigged = sequenced(sound, alone, rulings={slot("attack"): result})

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.details["rulings"]["attack"].startswith(ruled)
    assert summary in verdict.summary


#: A specification of the Nagini shape, whose implementation returns a sequence: an attack on it
#: can be executed on the same drawn inputs as the reference one, before its patch is judged.
SPLIT = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin spec
def split_cents(cents: int) -> PSeq[int]:
    Requires(MustTerminate(2))
    Requires(cents >= 0)
    Ensures(len(Result()) == 2)
# benchproofer:end spec
# benchproofer:begin impl
    return PSeq(cents // 25, cents % 25)
# benchproofer:end impl
"""


#: An attack on `SPLIT` that computes what its implementation computes.
SPLIT_ECHO = "    quarters = cents // 25\n    return PSeq(quarters, cents - quarters * 25)\n"
#: An attack on `SPLIT` that drops the remainder, which executing the two on the same drawn
#: inputs tells apart from its implementation.
TOLD = "    return PSeq(cents // 25, 0)\n"


class Carrying(Sequenced):
    """`Sequenced` under a checker that replays a proof the file carries, as Lean does.

    Its files cannot be executed on the same drawn inputs, so an attack equivalent to the
    solution file is found by proof: the checker is asked about a probe file under the slot
    `echo-<submission>`, answered from the script.
    """

    name = "carrying"
    proof_carrying = True


#: A specification whose precondition few of the inputs drawn for it meet; an attack on it
#: that returns what its implementation returns on every one that does is not told apart.
NARROW = """\
# benchproofer:begin spec
def total(a: int, b: int, c: int) -> int:
    Requires(MustTerminate(2))
    Requires(a == b and b == c and a >= 0)
    Ensures(Result() >= 0)
# benchproofer:end spec
# benchproofer:begin impl
    return a + b + c
# benchproofer:end impl
"""
#: A specification whose function takes a mapping, a type nothing draws for it.
HELD = """\
from typing import Dict

# benchproofer:begin spec
def grow(sizes: Dict[int, int], by: int) -> int:
    Requires(MustTerminate(2))
    Requires(by >= 0)
    Ensures(Result() >= by)
# benchproofer:end spec
# benchproofer:begin impl
    return by
# benchproofer:end impl
"""
#: Each way of ruling below is asked about with a patch the tests pass and with one they
#: reject.
PATCHES = pytest.mark.parametrize("rejected", [False, True], ids=["passes", "rejected"])
#: The attack each way of reaching an answer is asked about, with the file it is spliced
#: into: "" for the sound fixture's own.
ATTACKS: dict[str, tuple[str, str]] = {
    "same inputs, told apart": (SPLIT, TOLD),
    "same inputs told apart, conformance.py agrees": (SPLIT, TOLD),
    "same inputs told apart, conformance.py disagrees": (SPLIT, TOLD),
    "conformance.py disagrees": ("", NO_NICKEL),
    "same inputs, agreed": (SPLIT, SPLIT_ECHO),
    "conformance.py agrees": ("", BY_LOOP),
    "proved equal": ("", BY_LOOP_SEQ),
    "no proof closes": ("", NO_NICKEL_SEQ),
    "too few admissible": (NARROW, "    return 3 * a\n"),
    "a type nothing draws": (HELD, "    return by + 1\n"),
    "a value only the verifier has": ("", NO_NICKEL_SEQ),
    "a helper conformance.py lacks": ("", NO_NICKEL_HELPED),
    "no conformance.py": ("", NO_NICKEL),
    "conformance.py marks no implementation": ("", NO_NICKEL),
    "conformance.py compares only part of it": ("", NO_NICKEL),
}
#: `conformance.py` agreeing over what it compared, beside a function it could not.
GAPPED = OracleResult.ok(
    "conformance exited 0",
    output=AGREES.output + "benchproofer:skipped change.audit_log: needs a broker\n",
)
#: What the bundle's `conformance.py` prints, for the ways above that run it.
PRINTS: dict[str, OracleResult] = {
    "conformance.py agrees": AGREES,
    "same inputs told apart, conformance.py agrees": AGREES,
    "conformance.py compares only part of it": GAPPED,
}


def _attacked(
    sound: Bundle, settings: Settings, how: str, *, rejected: bool
) -> tuple[Verdict, Rigged]:
    """Review the attack ``how`` names, and judge it for completeness."""
    accepted, impl = ATTACKS[how]
    conformance = SPLIT_HARNESS if accepted and "conformance.py" in how else HARNESS
    reviewed(
        sound,
        attacking("attack", accepted or sound.solution(), impl, shadow=ATTACK_PATCH),
        harness=conformance,
    )
    rulings = {"reference": RESOLVES, slot("attack"): FAILS if rejected else RESOLVES}
    shipped: dict[str, object] = {"_solution": accepted} if accepted else {}
    if how in ("proved equal", "no proof closes"):
        refused = {"echo-attack": CheckResult.no("unsolved goals")}
        answers = refused if how == "no proof closes" else {}
        rigged = context(sound, settings, backend=Carrying(), rulings=rulings, answers=answers)
    elif "conformance.py" in how:
        if how == "no conformance.py":
            sound.conformance_path.unlink()
        if how == "conformance.py marks no implementation":
            write_text(sound.conformance_path, UNMARKED)
        output = PRINTS.get(how, DISAGREES)
        rigged = context(
            sound, settings, backend=Proving(), output=output, rulings=rulings, **shipped
        )
    else:
        rigged = context(sound, settings, backend=Sequenced(), rulings=rulings, **shipped)
    return SpecCompletenessGate().run(rigged), rigged


@PATCHES
@pytest.mark.parametrize(
    "how", ["conformance.py disagrees", "same inputs told apart, conformance.py disagrees"]
)
def test_an_accepted_attack_conformance_tells_apart_from_the_repository_is_wrong(
    how: str, rejected: bool, sound: Bundle, settings: Settings
) -> None:
    """Whatever its patch does, which is not asked.

    `conformance.py` with the attack's code in it found an input on which the repository's
    code does something else, whether or not executing the two files on the same drawn inputs
    told them apart first.
    """
    completeness, rigged = _attacked(sound, settings, how, rejected=rejected)

    assert completeness.status is Status.FAIL
    assert completeness.details["too_weak"] == ["attack"]
    assert slot("attack") not in rigged.judged
    assert UNRULED not in completeness.details


@PATCHES
@pytest.mark.parametrize(
    ("how", "found"),
    [
        ("same inputs, agreed", "executed on the same drawn inputs, it returns what"),
        ("proved equal", "the checker proves each function it defines equal"),
    ],
)
def test_an_accepted_attack_on_the_same_inputs_or_proved_equal_to_the_reference_is_correct(
    how: str, found: str, rejected: bool, sound: Bundle, settings: Settings
) -> None:
    """One whose patch the tests pass counts as an attack the specification survived.

    The patch is asked all the same, and one whose patch the tests reject cannot be determined
    by execution, since the model or the patch may be at fault: the gate is undecided until the
    attack validation auditor rules, and it is shown what the program found. One whose patch
    the tests pass is decided: the two compute the same.
    """
    completeness, rigged = _attacked(sound, settings, how, rejected=rejected)

    assert slot("attack") in rigged.judged
    if rejected:
        assert completeness.status is Status.SKIP
        shown = completeness.details[UNRULED]["attack"]
        assert shown.startswith(
            f"the checker accepts it, and the benchmark's tests reject its patch; {found}"
        )
        assert "does not resolve the task" in shown
        assert route(completeness) is Route.ASK_AGAIN
    else:
        assert completeness.status is Status.PASS
        assert completeness.details["agreed"] == ["attack"]


@PATCHES
def test_an_accepted_attack_conformance_agrees_with_is_left_to_the_validation_auditor(
    rejected: bool, sound: Bundle, settings: Settings
) -> None:
    """It is left to the attack validation auditor, whatever its patch does.

    `conformance.py` compares only on the inputs it draws, so its agreement does not say
    whether the attack breaks a behavior the task requires: the attack validation auditor
    rules on the attack with a patch the tests pass as well as with one they reject.
    """
    agrees = "conformance.py agrees"
    completeness, rigged = _attacked(sound, settings, agrees, rejected=rejected)

    assert completeness.status is Status.SKIP
    assert list(completeness.details[UNRULED]) == ["attack"]
    assert slot("attack") in rigged.judged
    tests = "reject its patch" if rejected else "do not reject it"
    assert completeness.details[UNRULED]["attack"].startswith(
        f"the checker accepts it, and the benchmark's tests {tests}; it agrees with the "
        "repository over 5,000 compared input"
    )
    assert route(completeness) is Route.ASK_AGAIN


@PATCHES
@pytest.mark.parametrize(
    "how",
    [
        "same inputs, told apart",
        "same inputs told apart, conformance.py agrees",
        "too few admissible",
        "a type nothing draws",
        "a value only the verifier has",
        "a helper conformance.py lacks",
        "no conformance.py",
        "conformance.py marks no implementation",
        "conformance.py compares only part of it",
        "no proof closes",
    ],
)
def test_an_accepted_attack_nothing_shows_equal_is_decided_by_its_patch(
    how: str, rejected: bool, sound: Bundle, settings: Settings
) -> None:
    """As `verified-swebench` decides every attack: a rejected patch makes it a weakness.

    One whose patch the tests pass cannot be determined by execution and goes to the attack
    validation auditor, since it may still break a behavior the task requires. That holds of one
    that executing the two files on the same drawn inputs told apart: the specification may
    leave out a behavior the statement does not ask for and no test checks, so a difference the
    tests do not see is that auditor's question, and is listed with the input it was found on.
    Agreement from `conformance.py` does not outweigh that difference. A rejected patch is run
    again before it is believed, one that resolves only once. Nothing runs the drafter's
    implementation in the attack's place: `conformance.py` is run only where it can carry the
    attack, and what it did not compare may be what the attack changed.
    """
    completeness, rigged = _attacked(sound, settings, how, rejected=rejected)

    ran = [slot("attack")] if how.endswith(("part of it", "conformance.py agrees")) else []
    assert [program.label for program in rigged.probed] == ran
    assert rigged.judged == ["reference", *[slot("attack")] * (ATTEMPTS if rejected else 1)]
    if rejected:
        assert completeness.status is Status.FAIL
        assert completeness.details["too_weak"] == ["attack"]
        assert UNRULED not in completeness.details
    else:
        assert completeness.status is Status.SKIP
        shown = completeness.details[UNRULED]["attack"]
        assert shown.startswith("the checker accepts it, and the benchmark's tests do not")
        told = "it does something else on `split_cents(" in shown
        assert told is how.startswith("same inputs")


#: A witness test: a program run where the benchmark's tests run, which checks what the
#: FAIL_TO_PASS test `CITED` checks.
WITNESS = "from change import make_change\nassert make_change(40) == (1, 1, 1, 0)\n"
CITED = "test_forty_cents"
#: What a witness test's two runs print, as the environment reports a program's exit.
PASSES = OracleResult.ok("witness exited 0")
FAILS_THERE = OracleResult.no("witness exited 1", output="AssertionError: (1, 1, 0, 5)\n")


def witnessed(
    name: str,
    solution: str,
    impl: str,
    *,
    cites: str = CITED,
    **fields: str,
) -> Filed:
    """An attack filed with its witness test and what the test cites."""
    submission, files = attacking(name, solution, impl, **fields)
    files[f"{name}.test.py"] = WITNESS
    return submission.model_copy(update={"test": f"{name}.test.py", "cites": cites}), files


@pytest.mark.parametrize(
    ("cites", "fixed", "patched", "said"),
    [
        (
            CITED,
            PASSES,
            FAILS_THERE,
            'its witness test, which cites "test_forty_cents", passes on the fixed code '
            "(witness exited 0) and fails with its equivalent patch in place of the golden "
            "patch "
            "(witness exited 1: AssertionError: (1, 1, 0, 5))",
        ),
        ("", PASSES, FAILS_THERE, "cites no sentence of the statement and no test it checks"),
        (CITED, FAILS_THERE, FAILS_THERE, "does not pass on the fixed code (witness exited 1)"),
        (CITED, PASSES, PASSES, "passes with its equivalent patch too, so it shows nothing"),
    ],
    ids=["holds", "no citation", "fails on the fixed code", "passes with the patch"],
)
def test_an_attack_whose_witness_test_holds_is_left_to_the_validation_auditor(
    cites: str,
    fixed: OracleResult,
    patched: OracleResult,
    said: str,
    sound: Bundle,
    settings: Settings,
) -> None:
    """It passes on the fixed code, fails with the attack's patch, and cites something.

    No program checks that what it cites asks for what it checks, so the attack goes to the
    attack validation auditor as a kind of its own, listed with both runs' results. A witness
    test that fails on the fixed code, passes with the patch, or cites nothing is evidence of
    nothing, which the ruling says, and the attack is what it would be without one: an attack
    whose patch the tests pass.
    """
    reviewed(
        sound,
        witnessed("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH, cites=cites),
    )
    rigged = sequenced(
        sound,
        settings,
        rulings={slot("attack"): RESOLVES},
        outputs={"witness-attack": fixed, "witness-attack-patched": patched},
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert said in verdict.details["rulings"]["attack"]
    assert verdict.status is Status.SKIP
    shown = verdict.details[UNRULED]["attack"]
    holds = said.startswith("its witness test, which cites")
    assert shown.startswith(
        "the checker accepts it, the benchmark's tests do not reject it, and its witness test "
        "passes on the fixed code and fails with its equivalent patch"
        if holds
        else "the checker accepts it, and the benchmark's tests do not reject it;"
    )
    assert said in shown
    runs = [(run.label, run.with_reference, run.patch) for run in rigged.probed]
    expected = [] if not cites else [("witness-attack", True, None)]
    if cites and fixed.resolved:
        expected.append(("witness-attack-patched", False, ATTACK_PATCH))
    assert runs == expected


@pytest.mark.parametrize(
    ("ruling", "asked", "status", "listed"),
    [
        ("succeeds", 1, Status.FAIL, "too_weak"),
        ("fails", 1, Status.PASS, "validated"),
        ("", 2, Status.SKIP, "discarded"),
    ],
    ids=["succeeds", "fails", "no ruling after it was asked again"],
)
def test_the_validation_auditor_rules_whether_a_witness_test_s_citation_asks_for_what_it_checks(
    ruling: str, asked: int, status: Status, listed: str, sound: Bundle, settings: Settings
) -> None:
    """`succeeds` makes the attack succeed and `fails` makes it fail, by that ruling alone.

    The ruling names what the test cites and the behavior it checks, as every ruling names
    what it rests on. An attack still without a ruling after the auditor was asked again is
    discarded, counting neither way.
    """
    reviewed(
        sound,
        witnessed("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH),
    )
    if ruling:
        rule_on(sound, "attack", ruling)
    else:
        rule_on(sound, "attack", "", named=False, asked=asked)
    rigged = sequenced(
        sound,
        settings,
        rulings={slot("attack"): RESOLVES},
        outputs={"witness-attack": PASSES, "witness-attack-patched": FAILS_THERE},
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is status
    assert UNRULED not in verdict.details
    said = verdict.details["rulings"]["attack"]
    if listed == "discarded":
        assert "asked about it again and gave no ruling" in said
        assert "discarded: no ruling of the attack validation auditor" in verdict.summary
    else:
        assert verdict.details[listed] == ["attack"]
        assert f"the attack validation auditor rules that the attack {ruling}" in said
        assert f"on the input {RULED_INPUT}, resting on {RULED_ON}" in said


def test_a_ruling_on_a_witness_test_expires_when_what_it_cites_changes(
    sound: Bundle, settings: Settings
) -> None:
    """The citation is part of the submission, as its files are: the ruling is about another."""
    reviewed(sound, witnessed("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    rule_on(sound, "attack", "succeeds")
    review = sound.audit()
    assert review is not None
    [ruled] = review.rulings
    assert ruled.reads[CITES]
    recited = review.submissions[0].model_copy(update={"cites": "test_ten_cents"})
    sound.save_audit(review.model_copy(update={"submissions": (recited,)}), {})

    verdict = SpecCompletenessGate().run(
        sequenced(
            sound,
            settings,
            rulings={slot("attack"): RESOLVES},
            outputs={"witness-attack": PASSES, "witness-attack-patched": FAILS_THERE},
        )
    )

    assert verdict.status is Status.SKIP
    assert list(verdict.details[UNRULED]) == ["attack"]


@pytest.mark.parametrize("how", ["conformance.py disagrees", "same inputs, agreed"])
def test_a_witness_test_is_not_run_where_the_programs_decide_the_attack(
    how: str, sound: Bundle, settings: Settings
) -> None:
    """Nor where the tests reject the patch: only an attack whose patch they pass is run."""
    accepted, impl = ATTACKS[how]
    reviewed(
        sound, witnessed("attack", accepted or sound.solution(), impl, shadow=ATTACK_PATCH)
    )
    shipped: dict[str, object] = {"_solution": accepted} if accepted else {}
    rigged = sequenced(
        sound,
        settings,
        backend=Proving() if "conformance.py" in how else None,
        rulings={slot("attack"): RESOLVES},
        **shipped,
    )

    SpecCompletenessGate().run(rigged)

    assert not [run for run in rigged.probed if run.label.startswith("witness-")]


class Witnessing(Proving):
    """A prover whose refusal says nothing without a refutation witness, as Lean's does."""

    name = "witnessing"
    witness_required = True


#: A control's refutation witness: a claim proved at one input that the specification
#: refuses what the control returns there.
REFUTATION = "example : ¬ property_change_is_the_fewest_coins 40 := by decide"


@pytest.mark.parametrize(
    ("objection", "ran", "found"),
    [
        (None, PASSES, ""),
        ("the witness holds of the reference implementation too", PASSES, "shows nothing"),
        (None, FAILS_THERE, "does not pass on the fixed code"),
    ],
    ids=["shown", "witness refused", "run disagrees"],
)
def test_a_refused_control_is_the_finding_where_its_refutation_witness_and_run_show_it(
    objection: str | None,
    ran: OracleResult,
    found: str,
    sound: Bundle,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The checker proves the witness, and a run shows the fixed code returns its result there.

    The witness is checked as the property-based test suite checks a reject case's
    (`attribution.attributed`); short of either, the refusal is a gap, as without a witness.
    """
    asked: list[tuple[str, str, str]] = []

    def attributed(
        context: Rigged, source: str, claim: str, *, slot: str, of: str
    ) -> str | None:
        asked.append((claim.strip(), slot, of))
        return objection

    monkeypatch.setattr("benchproofer.gates.audit.attributed", attributed)
    control, files = controlling("by-loop", sound.solution(), BY_LOOP)
    files["by-loop.test.py"] = WITNESS
    reviewed(
        sound,
        (
            control.model_copy(update={"test": "by-loop.test.py", "refutation": REFUTATION}),
            files,
        ),
    )
    rigged = context(
        sound,
        settings,
        backend=Witnessing(),
        answers={slot("by-loop"): CheckResult.no("unsolved goals")},
        outputs={"witness-by-loop": ran},
    )

    verdict = SpecSoundnessGate().run(rigged)

    assert asked == [(REFUTATION, slot("by-loop"), "control")]
    if not found:
        assert verdict.status is Status.FAIL
        assert verdict.details["too_strong"] == ["by-loop"]
        assert (
            "the checker proves its refutation witness" in verdict.details["rulings"]["by-loop"]
        )
        return
    assert verdict.status is Status.SKIP
    ruled = verdict.details["rulings"]["by-loop"]
    assert ruled.startswith("checker: gap") and found in ruled


def test_a_refused_controls_refutation_witness_is_read_only_where_a_refusal_needs_one(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under a checker that discharges the obligation itself, the refusal is a gap still."""
    monkeypatch.setattr(
        "benchproofer.gates.audit.attributed",
        lambda *_, **__: pytest.fail("a witness was checked where none is read"),
    )
    control, files = controlling("by-loop", sound.solution(), BY_LOOP)
    files["by-loop.test.py"] = WITNESS
    reviewed(
        sound,
        (
            control.model_copy(update={"test": "by-loop.test.py", "refutation": REFUTATION}),
            files,
        ),
    )
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={slot("by-loop"): CheckResult.no("unsolved goals")},
    )

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.details["rulings"]["by-loop"].startswith("checker: gap")
    assert not [run for run in rigged.probed if run.label.startswith("witness-")]


def test_a_too_weak_attack_equivalent_to_the_solution_names_the_lemma_for_a_repair_to_prove(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The probe could not close it, and the attack proves the solution file's claims.

    With the lemma proved the attack is equivalent to the solution file, so the repair is a
    proof rather than an obligation; without an attack that proves those claims, the lemma would
    decide nothing and is not named.
    """
    lemma = ("∀ x1 r1 r2, Spec x1 r1 → Spec x1 r2 → r1 = r2",)
    monkeypatch.setattr(echo, "determined", lambda *_: "the determinism probe")
    monkeypatch.setattr(determinism, "conjuncts", lambda *_: lemma)
    reviewed(sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    answers = {
        "echo-determined": CheckResult.no("unsolved goals"),
        "echo-attack": CheckResult.no("unsolved goals"),
    }

    for keeps in (True, False):
        monkeypatch.setattr(echo, "keeps_claims", lambda *_, keeps=keeps: keeps)
        rigged = sequenced(
            sound,
            settings,
            backend=Carrying(),
            rulings={slot("attack"): FAILS},
            answers=dict(answers),
        )

        verdict = SpecCompletenessGate().run(rigged)

        assert verdict.status is Status.FAIL
        assert verdict.details["too_weak"] == ["attack"]
        if keeps:
            assert verdict.details["determinism"] == list(lemma)
            assert f"state and prove `{lemma[0]}` in the proof region" in verdict.summary
        else:
            assert "determinism" not in verdict.details
            assert "state and prove" not in verdict.summary


def test_a_specification_proved_to_admit_one_result_makes_every_verified_attack_equivalent(
    sound: Bundle, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asked once per bundle, and enough for an attack that proves the accepted claims."""
    monkeypatch.setattr(echo, "determined", lambda *_: "the determinism probe")
    monkeypatch.setattr(echo, "keeps_claims", lambda *_: True)
    reviewed(
        sound,
        attacking("one", sound.solution(), NO_NICKEL_SEQ, shadow=""),
        attacking("two", sound.solution(), BY_LOOP_SEQ, shadow=""),
    )
    rigged = sequenced(
        sound,
        settings,
        backend=Carrying(),
        answers={
            "echo-one": CheckResult.no("unsolved goals"),
            "echo-two": CheckResult.no("unsolved goals"),
        },
    )

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["agreed"] == ["one", "two"]
    assert rigged.checked.count("echo-determined") == 1
    assert "echo-one" not in rigged.checked


@pytest.mark.parametrize(
    ("shadow", "rulings", "why"),
    [
        ("", {}, "filed no equivalent patch"),
        ("def make_change(cents):\n    return (0, 0, 0, 0)\n", {}, "not a unified diff"),
        (
            ATTACK_PATCH,
            {
                "submission-no-nickel": OracleResult.no(
                    "the candidate patch does not apply",
                    inert="the candidate patch does not apply",
                )
            },
            "says nothing about it",
        ),
        (
            ATTACK_PATCH,
            {"reference": OracleResult.no("3 FAIL_TO_PASS test(s) failing")},
            "cannot refute anything here",
        ),
    ],
    ids=["no patch", "not a diff", "does not apply", "fix does not resolve"],
)
def test_an_equivalent_patch_s_result_about_something_else_decides_nothing(
    shadow: str, rulings: dict[str, OracleResult], why: str, sound: Bundle, settings: Settings
) -> None:
    """Each is the reviewer's editing or the environment, not the specification."""
    reviewed(sound, attacking("no-nickel", sound.solution(), NO_NICKEL_SEQ, shadow=shadow))
    rigged = sequenced(sound, settings, rulings=rulings)

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "too_weak" not in verdict.details
    rows = (sound.evidence_dir / "audit-submissions.txt").read_text()
    assert why in rows


def test_a_recorded_verdict_on_the_benchmarks_own_fix_is_read_rather_than_rerun(
    sound: Bundle, settings: Settings
) -> None:
    reviewed(
        sound, attacking("no-nickel", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH)
    )
    sound.record([Verdict(gate="oracle.reference_resolves", status=Status.FAIL, summary="net")])
    rigged = sequenced(sound, settings, rulings={slot("no-nickel"): FAILS})

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert rigged.judged == []


def test_a_control_that_cannot_run_is_decided_by_the_checker_alone(
    sound: Bundle, settings: Settings
) -> None:
    """It verifies, so it is admitted."""
    reviewed(sound, controlling("by-loop", sound.solution(), BY_LOOP_SEQ))
    rigged = sequenced(sound, settings)

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["admitted"] == ["by-loop"]
    assert rigged.judged == [] and rigged.probed == []


def test_a_refused_control_that_cannot_run_is_never_put_to_the_benchmark_as_a_patch(
    sound: Bundle, settings: Settings
) -> None:
    """The patch that resolves is the fix itself, which would make any refusal a finding."""
    reviewed(sound, controlling("by-loop", sound.solution(), BY_LOOP_SEQ, shadow=ATTACK_PATCH))
    rigged = sequenced(
        sound,
        settings,
        answers={slot("by-loop"): CheckResult.no("property_uses_the_fewest_coins failed")},
        rulings={slot("by-loop"): RESOLVES},
    )

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "too_strong" not in verdict.details
    assert rigged.judged == []


def _naming(
    sound: Bundle,
    coin_change: Task,
    *tests: str,
    regression: tuple[str, ...] = (),
) -> None:
    """Give the bundle's task failing tests with ids, as a repository task has.

    And the tests it keeps passing, where given.
    """
    named = coin_change.oracle.model_copy(update={"tests": tests, "regression": regression})
    write_json(
        sound.task_path,
        coin_change.model_copy(update={"oracle": named}).model_dump(mode="json"),
    )


def test_a_row_survives_the_record(sound: Bundle) -> None:
    """`manifest.json` is read back by the gate, so what the review said must be kept.

    A record that still gives a row the `kind` the review once filed it under loads, without
    it, and so does one that still lists the submissions the faithfulness auditor was shown:
    nothing reads either.
    """
    row = Coverage(behavior="the option is renamed", tested_by="test_forty")
    reviewed(sound, judgments=[judged(sound, "faithfulness", "sound", coverage=[row])])
    index = sound.audit_dir / "index.toml"
    written = read_text(index)
    assert "kind" not in written.split("[[judgments.coverage]]")[1]
    assert "attacks" not in written
    written = written.replace('note = ""\n', 'note = ""\nkind = "interface"\n', 1)
    write_text(index, written.replace("findings = ", 'attacks = ["attack-1"]\nfindings = ', 1))

    recorded = sound.audit()

    assert recorded is not None
    faithful = recorded.judgment("faithfulness")
    assert faithful is not None
    assert faithful.coverage == (row,)


# ---- a control conformance.py cannot decide ----------------------------------------


def test_a_control_conformance_py_cannot_decide_rests_on_the_checker_as_one_it_cannot_run(
    sound: Bundle, settings: Settings
) -> None:
    """`conformance.py` then knows no more about it than about one it cannot run at all."""
    reviewed(sound, controlling("by-loop", sound.solution(), BY_LOOP))
    rigged = context(sound, settings, backend=Proving(), output=GAPPED)

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["admitted"] == ["by-loop"]
    rows = (sound.evidence_dir / "audit-submissions.txt").read_text()
    assert "could not compare change.audit_log" in rows


#: A `conformance.py` for `SPLIT` that can run an implementation over its sequences.
SPLIT_HARNESS = """\
import change


def PSeq(*items):
    return tuple(items)


def split_cents(cents):
# benchproofer:begin impl
    return PSeq(cents // 25, cents % 25)
# benchproofer:end impl


for cents in range(500):
    assert change.split_cents(cents) == split_cents(cents)
print("benchproofer:compared change.split_cents 500 every amount under 500")
"""


def test_an_attack_run_on_the_reference_s_inputs_is_decided_before_conformance_is_asked(
    sound: Bundle, settings: Settings
) -> None:
    """`conformance.py` is never asked about an attack the run found equal.

    What it compares is model values against repository ones, so its answer about an
    implementation the specification accepted in its own right adds nothing. The patch is
    asked, and no program is run; the tests reject it, which leaves whether the model or the
    patch is at fault to the attack validation auditor.
    """
    reviewed(sound, attacking("attack", SPLIT, SPLIT_ECHO, shadow=ATTACK_PATCH))
    write_text(sound.conformance_path, SPLIT_HARNESS)
    rigged = _echoing(sound, settings)

    verdict = SpecCompletenessGate().run(rigged)

    assert rigged.probed == []
    assert rigged.judged == ["reference", *[slot("attack")] * ATTEMPTS]
    assert verdict.status is Status.SKIP
    assert verdict.details[UNRULED]["attack"].startswith(
        "the checker accepts it, and the benchmark's tests reject its patch"
    )


def _echoing(sound: Bundle, settings: Settings, **rigging: object) -> Rigged:
    """A context whose attack computes what `SPLIT` does, with a patch the tests reject."""
    return context(
        sound,
        settings,
        backend=Proving(),
        output=AGREES,
        rulings={"reference": RESOLVES, slot("attack"): FAILS},
        _solution=SPLIT,
        **rigging,
    )


def test_a_rejected_patch_of_an_equivalent_attack_is_the_validation_auditors_to_rule_on(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """The gate lists it with what it established, and asks the attack validation auditor."""
    _naming(sound, coin_change, "tests/test_change.py::test_forty")
    reviewed(
        sound,
        attacking("attack", SPLIT, SPLIT_ECHO, shadow=ATTACK_PATCH),
        harness=SPLIT_HARNESS,
    )

    reported = SpecCompletenessGate().run(_echoing(sound, settings))

    assert reported.status is Status.SKIP
    said = reported.details[UNRULED]["attack"]
    assert said.startswith(
        "the checker accepts it, and the benchmark's tests reject its patch; executed on the "
        "same drawn inputs"
    )
    assert "test_forty_cents" in said
    assert route(reported) is Route.ASK_AGAIN


def _reviewed_echo(bundle: Bundle, task: Task, patch: str) -> None:
    """`SPLIT_ECHO` filed with ``patch``."""
    _naming(bundle, task, "tests/test_change.py::test_forty")
    reviewed(
        bundle, attacking("attack", SPLIT, SPLIT_ECHO, shadow=patch), harness=SPLIT_HARNESS
    )


#: A rejection that also fails a test which races, beside the one the attack fails.
FLAKES = OracleResult.no(
    "2 FAIL_TO_PASS test(s) failing", failed=("test_forty_cents", "test_reaches_the_network")
)


@pytest.mark.parametrize(
    ("answers", "status"),
    [((FAILS, RESOLVES), Status.PASS), ((FAILS, FAILS, FLAKES), Status.SKIP)],
    ids=["resolves on a later attempt", "rejected every time"],
)
def test_a_patch_counts_as_rejected_only_when_every_attempt_rejects_it(
    answers: tuple[OracleResult, ...],
    status: Status,
    sound: Bundle,
    settings: Settings,
    coin_change: Task,
) -> None:
    """A test that races or reaches the network fails a patch that resolves.

    So a rejected patch is run again, as the benchmark's own fix is, and resolving on any
    attempt counts. One rejected every time is reported with the attempts it took and the
    tests it failed every time.
    """
    _reviewed_echo(sound, coin_change, ATTACK_PATCH)
    rigged = _echoing(sound, settings)
    rigged.rulings[slot("attack")] = answers

    verdict = SpecCompletenessGate().run(rigged)

    assert rigged.judged.count(slot("attack")) == len(answers)
    assert verdict.status is status
    if status is Status.SKIP:
        row = verdict.details[UNRULED]["attack"]
        assert f"does not resolve the task in {ATTEMPTS} attempt(s)" in row
        assert "test_forty_cents" in row and "test_reaches_the_network" not in row
    else:
        assert UNRULED not in verdict.details


@pytest.mark.parametrize(
    ("indent", "run"), [("", False), ("    ", True)], ids=["the fix", "the fix re-indented"]
)
def test_a_patch_that_makes_the_fixs_own_change_resolves_without_a_run(
    indent: str, run: bool, sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """Headers, hunk positions and trailing whitespace aside, it is the fix itself.

    So no run of the benchmark's tests can reject it. Indentation is kept: a line moved into
    a block is another change.
    """
    reference = coin_change.reference.patch or ""
    patch = "diff --git a/change.py b/change.py\nindex 1a2b3c4..5d6e7f8 100644\n" + (
        reference.replace("@@ def make_change(cents):", "@@")
        .replace("+    nickels", f"+    {indent}nickels")
        .replace("\n", "  \n")
    )
    _reviewed_echo(sound, coin_change, patch)
    rigged = _echoing(sound, settings)

    verdict = SpecCompletenessGate().run(rigged)

    assert (slot("attack") in rigged.judged) is run
    if not run:
        assert verdict.status is Status.PASS


# ---- the attack validation auditor's rulings -------------------------------------------


@pytest.mark.parametrize(
    ("kind", "ruling", "status", "listed"),
    [
        ("passes", "succeeds", Status.FAIL, "too_weak"),
        ("passes", "fails", Status.PASS, "validated"),
        ("rejected", "succeeds", Status.FAIL, "too_weak"),
        ("rejected", "fails", Status.PASS, "validated"),
    ],
)
def test_an_attack_the_programs_leave_open_is_decided_by_the_validation_auditor(
    kind: str, ruling: str, status: Status, listed: str, sound: Bundle, settings: Settings
) -> None:
    """Whether its patch the tests pass breaks what the task requires, or who is at fault.

    An attack whose patch the tests pass, and one shown equal to the reference implementation
    whose patch they reject, cannot be determined by execution. The ruling says, with the input
    and the test it rests on, and the ruling's words go into what the gates ruled.
    """
    if kind == "passes":
        reviewed(
            sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH)
        )
        rigged = sequenced(sound, settings, rulings={slot("attack"): RESOLVES})
    else:
        reviewed(sound, attacking("attack", SPLIT, SPLIT_ECHO, shadow=ATTACK_PATCH))
        write_text(sound.conformance_path, SPLIT_HARNESS)
        rigged = _echoing(sound, settings)
    rule_on(sound, "attack", ruling)

    verdict = SpecCompletenessGate().run(rigged)

    assert verdict.status is status
    assert verdict.details[listed] == ["attack"]
    assert UNRULED not in verdict.details
    said = verdict.details["rulings"]["attack"]
    assert f"the attack validation auditor rules that the attack {ruling}" in said
    assert f"on the input {RULED_INPUT}, resting on {RULED_ON}" in said


@pytest.mark.parametrize(
    ("ruling", "status", "found"),
    [
        ("too_strong", Status.FAIL, "too_strong"),
        ("unproved", Status.SKIP, "unproved"),
        ("incorrect", Status.SKIP, ""),
    ],
)
def test_a_control_a_prover_refuses_is_decided_by_the_validation_auditor(
    ruling: str, status: Status, found: str, sound: Bundle, settings: Settings
) -> None:
    """Correct and refused by the specification fails the gate.

    Correct and refused for a proof it lacks is listed as unproved, for the run report, and
    one not correct is discarded; neither counts toward the controls the run asks for.
    """
    control = controlling("by-loop", sound.solution(), BY_LOOP, claim=UNPROVED)
    reviewed(sound, control)
    rule_on(sound, "by-loop", ruling)
    refusal = refused_at(control[1]["by-loop.py"], "impl", "Postcondition might not hold.")
    rigged = context(sound, settings, backend=Proving(), answers={slot("by-loop"): refusal})

    verdict = SpecSoundnessGate().run(rigged)

    assert verdict.status is status
    assert UNRULED not in verdict.details
    if found == "too_strong":
        assert verdict.details["too_strong"] == ["by-loop"]
    elif found == "unproved":
        assert list(verdict.details["unproved"]) == ["by-loop"]
        assert "unproved: correct, but the checker rejected a step" in verdict.summary
        assert route(verdict) is Route.ASK_AGAIN
    else:
        assert "unproved" not in verdict.details
        assert "discarded: not correct" in verdict.summary


def test_the_run_report_lists_a_control_ruled_unproved(
    sound: Bundle, settings: Settings
) -> None:
    """Beside the property-based test suite's correct cases refused on their own proof."""
    control = controlling("by-loop", sound.solution(), BY_LOOP, claim=UNPROVED)
    reviewed(sound, control)
    rule_on(sound, "by-loop", "unproved")
    refusal = refused_at(control[1]["by-loop.py"], "impl", "Postcondition might not hold.")
    rigged = context(sound, settings, backend=Proving(), answers={slot("by-loop"): refusal})
    sound.record([SpecSoundnessGate().run(rigged)])

    (row,) = summarize([sound], level=Level.AUDITED).rows

    (case,) = row.unproved
    assert case.case == "by-loop" and case.after_session
    assert "Postcondition might not hold" in case.reason
    assert "that it is correct, and the checker rejected a step of its own proof" in case.reason


def test_a_ruling_that_names_no_input_is_none_and_a_case_left_so_twice_is_discarded(
    sound: Bundle, settings: Settings
) -> None:
    """Asked once more first; after that, it counts neither way and the gate decides without it.

    With no other attack decided, that is too few for the run, which asks the attack auditor
    for more.
    """
    reviewed(sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    rule_on(sound, "attack", "succeeds", named=False)

    first = SpecCompletenessGate().run(
        sequenced(sound, settings, rulings={slot("attack"): RESOLVES})
    )
    review = sound.audit()
    assert review is not None
    sound.save_audit(review.model_copy(update={"rulings": ()}), {})
    rule_on(sound, "attack", "succeeds", named=False, asked=2)
    second = SpecCompletenessGate().run(
        sequenced(sound, settings, rulings={slot("attack"): RESOLVES})
    )

    assert first.status is Status.SKIP and list(first.details[UNRULED]) == ["attack"]
    assert second.status is Status.SKIP and UNRULED not in second.details
    assert second.details["required"] == 1
    assert "discarded: no ruling of the attack validation auditor" in second.summary
    assert route(second) is Route.ASK_AGAIN


@pytest.mark.parametrize("how", ["of another kind", "about other files"])
def test_a_ruling_of_another_kind_or_about_other_files_is_no_ruling(
    how: str, sound: Bundle, settings: Settings
) -> None:
    """An attack is not refused, and a ruling on the attack as it was is not about this one."""
    reviewed(sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    rule_on(sound, "attack", "too_strong" if how == "of another kind" else "succeeds")
    if how == "about other files":
        write_text(sound.audit_dir / "attack.shadow.py", ATTACK_PATCH + "\n")

    verdict = SpecCompletenessGate().run(
        sequenced(sound, settings, rulings={slot("attack"): RESOLVES})
    )

    assert verdict.status is Status.SKIP
    assert list(verdict.details[UNRULED]) == ["attack"]


def test_a_later_judgment_of_the_same_files_reads_what_the_first_ran(
    sound: Bundle, settings: Settings
) -> None:
    """The benchmark's tests run once on a submission, whatever the review adds to the record.

    The attack validation auditor's ruling changes the review's index and nothing the row was
    computed from, so the judgment after it reads the row the first one recorded; a judgment
    told not to read a record runs it again, and so does one after the submission changed.
    """
    reviewed(sound, attacking("attack", sound.solution(), NO_NICKEL_SEQ, shadow=ATTACK_PATCH))
    first = sequenced(sound, settings, rulings={slot("attack"): RESOLVES}, reuse=True)
    SpecCompletenessGate().run(first)
    rule_on(sound, "attack", "succeeds")

    again = sequenced(sound, settings, rulings={slot("attack"): RESOLVES}, reuse=True)
    verdict = SpecCompletenessGate().run(again)
    unread = sequenced(sound, settings, rulings={slot("attack"): RESOLVES})
    SpecCompletenessGate().run(unread)
    write_text(sound.audit_dir / "attack.shadow.py", ATTACK_PATCH + "\n")
    changed = sequenced(sound, settings, rulings={slot("attack"): RESOLVES}, reuse=True)
    SpecCompletenessGate().run(changed)

    assert slot("attack") in first.judged
    assert again.judged == [] and slot("attack") not in again.checked
    assert verdict.status is Status.FAIL and verdict.details["too_weak"] == ["attack"]
    assert slot("attack") in unread.judged
    assert slot("attack") in changed.judged
