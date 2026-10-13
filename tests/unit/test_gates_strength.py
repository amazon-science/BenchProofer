# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The two mechanical strength gates: a floor, and the one case the benchmark supplies.

Both ask the same question as the property-based test suite -- is this specification strong
enough to be worth verifying against -- and neither needs anyone to write a case.
`spec.discriminates` runs the pre-fix implementation, which is the one wrong program the
benchmark itself identified; `spec.strength.mutation` corrupts the shipped implementation a
token at a time and fails on any corruption the specification accepts that computes something
else.

What the tests here pin down is the bookkeeping, because that is where a strength verdict
turns into a false claim: an answer the checker reached about a file it could not read is
not a rejection on the merits, a refusal is not counted as a kill, and a run that timed out
is not a survivor. A gate that counted them would report a machine under load as a strong
specification, or a typo as a defect in one.
"""

from __future__ import annotations

import re

import pytest

from benchproofer.backends.base import CheckResult
from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle, Twin
from benchproofer.core.markers import parse, replace_region, wrap
from benchproofer.core.mutation import generate
from benchproofer.core.task import Reference, SourceFile, Task, TaskContext
from benchproofer.core.verdict import Level, SkipReason, Status
from benchproofer.gates.discriminates import DiscriminatesGate
from benchproofer.gates.mutation import MutationGate
from benchproofer.pipeline.route import Route, route
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import write_json, write_text
from doubles import Proving, Rigged, Screening

COMMENT = "#"
#: The code before the fix, which is what the pre-fix implementation carries.
NO_NICKEL = """\
def impl(cents):
    quarters = cents // 25
    remainder = cents - quarters * 25
    dimes = remainder // 10
    pennies = remainder - dimes * 10
    return (quarters, dimes, 0, pennies)
"""


def context(
    bundle: Bundle,
    settings: Settings,
    *,
    backend: Screening | None = None,
    answers: dict[str, CheckResult] | None = None,
    **rigging: object,
) -> Rigged:
    """A context whose checker answers from a script.

    The shipped file verifies unless a test says otherwise, so that the fallback answer
    a test scripts is about the variants it is reasoning about. Both gates refuse to
    measure anything against a specification the checker rejected, which is its own
    case below rather than a precondition of every other one.
    """
    return Rigged(
        bundle=bundle,
        backend=backend or Screening(),
        settings=settings,
        level=Level.STATIC,
        answers={"solution": CheckResult.ok("accepted by the script"), **(answers or {})},
        **rigging,  # type: ignore[arg-type]
    )


def twinned(bundle: Bundle, source: str, name: str = "twin") -> None:
    """Replace the bundle's pre-fix implementations with the one a test is about."""
    for stale in bundle.twins_dir.glob("*"):
        stale.unlink()
    write_text(bundle.twins_dir / f"{name}.py", source)


# ---- spec.discriminates --------------------------------------------------


def test_a_specification_that_rejects_the_pre_fix_implementation_passes(
    sound: Bundle, settings: Settings
) -> None:
    rigged = context(sound, settings, answers={"twin-twin": CheckResult.no("cents=40")})

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["twins"] == ["twin"]
    assert verdict.evidence == ["evidence/discriminates.txt"]


def test_a_specification_the_bug_already_satisfies_is_too_weak(
    sound: Bundle, settings: Settings
) -> None:
    """Then verifying against it says nothing about the task it came from."""
    verdict = DiscriminatesGate().run(context(sound, settings, backend=Proving()))

    assert verdict.status is Status.FAIL
    assert verdict.details["accepted"] == ["twin"]


def test_the_same_pre_fix_implementation_under_a_falsifier_is_a_search_that_came_up_empty(
    sound: Bundle, settings: Settings
) -> None:
    verdict = DiscriminatesGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["accepted"] == ["twin"]


def test_a_pre_fix_implementation_with_a_different_specification_is_not_one(
    sound: Bundle, settings: Settings
) -> None:
    """A rejection of a different specification is not a fact about this one."""
    twinned(
        sound,
        replace_region(
            replace_region(sound.solution(), COMMENT, "impl", NO_NICKEL),
            COMMENT,
            "spec",
            "def property_nothing(cents):\n    assert True\n",
        ),
    )
    rigged = context(sound, settings)

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["drifted"] == ["twin"]
    assert rigged.checked == ["solution"]


def test_a_pre_fix_implementation_whose_regions_cannot_be_read_is_a_defect_for_a_repair(
    sound: Bundle, settings: Settings
) -> None:
    """A second function's contract with no body is the file's defect, named for a repair."""
    twinned(
        sound,
        replace_region(sound.solution(), COMMENT, "impl", NO_NICKEL)
        + "\n# benchproofer:begin spec.2\ndef property_second(cents):\n    assert True\n"
        "# benchproofer:end spec.2\n",
    )
    rigged = context(sound, settings)

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "traceback" not in verdict.details
    assert verdict.details["not_evidence"] == ["twin"]
    assert "twins/twin.py" in verdict.summary
    assert "function 2 has no impl.2 region" in verdict.summary
    assert route(verdict) is Route.REPAIR
    assert rigged.checked == ["solution"]


def test_a_pre_fix_implementation_verdict_names_every_category_the_pass_found(
    sound: Bundle, settings: Settings
) -> None:
    """The verdict is the first category, and the rest are not nothing.

    A repair told only about the first spends its round on that one and is told about the
    second in the round after, one round per category. Named together, one repair answers
    them all.
    """
    twinned(sound, replace_region(sound.solution(), COMMENT, "impl", NO_NICKEL))
    write_text(
        sound.twins_dir / "elsewhere.py",
        replace_region(
            replace_region(sound.solution(), COMMENT, "impl", NO_NICKEL),
            COMMENT,
            "spec",
            "def property_nothing(cents):\n    assert True\n",
        ),
    )

    verdict = DiscriminatesGate().run(context(sound, settings, backend=Proving()))

    assert verdict.status is Status.FAIL
    assert verdict.details["defects"] == {"drifted": ["elsewhere"], "accepted": ["twin"]}
    assert "also found accepted: twin" in verdict.summary


def test_a_pre_fix_implementation_that_assumes_what_it_should_compute_fails_the_gate(
    sound: Bundle, settings: Settings
) -> None:
    """Such a pre-fix implementation is accepted whatever the specification says: weakness."""
    twinned(
        sound,
        replace_region(
            sound.solution(),
            COMMENT,
            "impl",
            "def impl(cents):\n    assume(False)\n    return (0, 0, 0, 0)\n",
        ),
    )
    rigged = context(sound, settings)

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["not_evidence"] == ["twin"]
    assert rigged.checked == ["solution"]


def test_a_pre_fix_implementation_the_checker_could_not_read_is_not_a_rejected_one(
    sound: Bundle, settings: Settings
) -> None:
    """Otherwise a broken pre-fix implementation would certify any specification for free."""
    rigged = context(
        sound, settings, answers={"twin-twin": CheckResult.malformed("SyntaxError")}
    )

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["malformed"] == ["twin"]


def test_a_pre_fix_implementation_the_checker_reached_no_verdict_on_leaves_the_gate_undecided(
    sound: Bundle, settings: Settings
) -> None:
    rigged = context(sound, settings, answers={"twin-twin": CheckResult.unknown("timed out")})

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.TIMEOUT
    assert verdict.details["undecided"] == ["twin"]


# Under a checker that replays a proof script the file writes, a pre-fix implementation's
# refusal alone attributes nothing; its refutation witness does (`gates.attribution`).


class Tactic(Proving):
    """A prover whose accepting verdict rests on a proof script the file carries."""

    name = "tactic"
    witness_required = True


#: A witness naming a property the spec region declares, false of the solution file.
#: Lean-shaped, whatever this double's comment token: the checkers that require a witness
#: are both Lean, and `core.witness` screens for a claim in that language.
TWIN_WITNESS = "example : \u00ac property_change_is_the_fewest_coins 40 := by decide"
#: What the checker says of the pre-fix implementation under such a checker: its own proof does
#: not close.
SCRIPT_FAILS = CheckResult.no(
    "solution.py:13:5: error: unsolved goals",
    output="solution.py:13:5: error: unsolved goals",
)


def witnessed(bundle: Bundle, claim: str, session: str = "") -> None:
    """Record ``claim`` as the bundle's pre-fix implementation's refutation witness."""
    ((name, source),) = bundle.twins()
    bundle.save_twins(
        [(Twin(id=name, file=f"{name}.py", witness=claim, proof_session=session), source)]
    )


@pytest.mark.parametrize(
    "answer",
    [SCRIPT_FAILS, CheckResult.unknown("maximum number of heartbeats has been reached")],
    ids=["refused", "no verdict"],
)
def test_a_pre_fix_implementation_whose_witness_discriminates_is_rejected_on_the_merits(
    sound: Bundle, settings: Settings, answer: CheckResult
) -> None:
    """Holds of the pre-fix implementation, fails of the solution file: the two are told apart.

    Both builds leave the pre-fix implementation's own proof out, so where that proof is what
    the checker could not finish, the witness still answers.
    """
    witnessed(sound, TWIN_WITNESS)
    rigged = context(
        sound,
        settings,
        backend=Tactic(),
        answers={
            "twin-twin": answer,
            "witness-twin-twin-twin": CheckResult.ok("the witness holds"),
            "witness-twin-twin-accepted": CheckResult.no("the witness fails"),
        },
    )

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.PASS
    assert rigged.checked == [
        "solution",
        "twin-twin",
        "witness-twin-twin-twin",
        "witness-twin-twin-accepted",
    ]


@pytest.mark.parametrize(
    "refusal",
    [
        SCRIPT_FAILS,
        # Line 22 is in the `spec` region. The specification region is shared with a file
        # the checker accepts, so where a refusal is placed does not say the specification
        # refused the bug: the property-based test suite's rule, not a looser one.
        CheckResult.no(
            "solution.py:22:5: error: unsolved goals", output="solution.py:22:5: error"
        ),
    ],
    ids=["inside the twin", "at the specification"],
)
def test_a_pre_fix_implementation_with_no_witness_leaves_the_question_undecided(
    sound: Bundle, settings: Settings, refusal: CheckResult
) -> None:
    """Neither a skip that certifies nor a finding: an error for a repair to resolve."""
    rigged = context(sound, settings, backend=Tactic(), answers={"twin-twin": refusal})

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert not verdict.ok
    assert verdict.details["unattributed"] == ["twin"]
    assert verdict.details["reasons"] == {"twin": "the case ships no witness"}
    assert not any(step.startswith("witness-") for step in rigged.checked)
    assert "unattributed" in (sound.evidence_dir / "discriminates.txt").read_text()


def test_a_witness_that_binds_anything_is_refused_before_it_is_built(
    sound: Bundle, settings: Settings
) -> None:
    """Its hypothesis could assume what it is there to show, so neither build is asked."""
    witnessed(sound, "example (n : Nat) : ¬ property_change_is_the_fewest_coins n := by simp")
    rigged = context(sound, settings, backend=Tactic(), answers={"twin-twin": SCRIPT_FAILS})

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert "the witness binds (n : Nat)" in verdict.details["reasons"]["twin"]
    assert not any(step.startswith("witness-") for step in rigged.checked)


def test_a_witness_that_does_not_hold_of_the_pre_fix_implementation_attributes_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """Then the pre-fix implementation's own script likely caused the refusal: no second build.

    What a proof session on the witness reported ends the reason, so a reader and the
    repair see that its proof was tried and how that ended.
    """
    tried = "twin: a proof session on its refutation witness (40 turn(s), reported stuck)"
    witnessed(sound, TWIN_WITNESS, session=tried)
    rigged = context(
        sound,
        settings,
        backend=Tactic(),
        answers={
            "twin-twin": SCRIPT_FAILS,
            "witness-twin-twin-twin": CheckResult.no("unsolved goals"),
        },
    )

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert (
        "proof did not close against the pre-fix implementation"
        in verdict.details["reasons"]["twin"]
    )
    assert verdict.details["reasons"]["twin"].endswith(tried)
    assert "witness-twin-twin-accepted" not in rigged.checked


def test_a_witness_that_holds_of_the_accepted_file_too_does_not_discriminate(
    sound: Bundle, settings: Settings
) -> None:
    """A claim true of both says nothing about which one the specification refuses."""
    witnessed(sound, TWIN_WITNESS)
    rigged = context(
        sound,
        settings,
        backend=Tactic(),
        answers={
            "twin-twin": SCRIPT_FAILS,
            "witness-twin-twin-twin": CheckResult.ok("holds"),
            "witness-twin-twin-accepted": CheckResult.ok("holds here too"),
        },
    )

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.ERROR
    assert (
        "does not discriminate the pre-fix implementation" in verdict.details["reasons"]["twin"]
    )


def test_a_checker_that_discharges_the_obligation_itself_needs_no_witness(
    sound: Bundle, settings: Settings
) -> None:
    """The same refusal under a prover whose answer is the contract failing to hold."""
    rigged = context(
        sound,
        settings,
        backend=Proving(),
        answers={
            "twin-twin": CheckResult.no(
                "solution.py:13:5: error: postcondition might not hold",
                output="solution.py:13:5: error: postcondition might not hold",
            )
        },
    )

    verdict = DiscriminatesGate().run(rigged)

    assert verdict.status is Status.PASS


#: A file the fix only adds, which replaces nothing.
ADDS_A_FILE = "--- /dev/null\n+++ b/extra.py\n@@ -0,0 +1,2 @@\n+def extra():\n+    return 1\n"
STUB = SourceFile(path="totals.py", content='def total(values):\n    """Sum them."""\n')
FILLED = SourceFile(
    path="totals.py",
    content='def total(values):\n    """Sum them."""\n    return sum(values)\n',
)
BROKEN = SourceFile(path="totals.py", content="def total(values):\n    return 0\n")
FIXED = SourceFile(path="totals.py", content="def total(values):\n    return sum(values)\n")


@pytest.mark.parametrize(
    ("reference", "starting", "lost"),
    [
        # A from-scratch task is not a bundle missing an artifact.
        (Reference(answer="123"), TaskContext(), False),
        # A patch that creates a file has no pre-fix state for a pre-fix implementation to
        # translate.
        (Reference(patch=ADDS_A_FILE), TaskContext(), False),
        # A signature and a docstring are not the behavior a pre-fix implementation translates.
        (Reference(files=[FILLED]), TaskContext(files=[STUB]), False),
        # A line of the starting file is gone, so there was a body to translate.
        (Reference(files=[FIXED]), TaskContext(files=[BROKEN]), True),
        # The task as shipped is a repair, and its bundle lost the pre-fix implementation.
        (None, None, True),
    ],
    ids=["from scratch", "adds a file", "fills a stub", "rewrites a file", "repair"],
)
def test_a_missing_pre_fix_implementation_is_a_gap_only_where_the_fix_replaced_code(
    sound: Bundle,
    settings: Settings,
    coin_change: Task,
    reference: Reference | None,
    starting: TaskContext | None,
    lost: bool,
) -> None:
    """The gate decides by the drafter's predicate (`material.has_pre_fix`).

    A gate reading "a patch is there" or "there is a starting file" would fail a bundle for
    a pre-fix implementation the drafter was right not to write. One the bundle lost fails
    it, so that a repair writes it.
    """
    for stale in sound.twins_dir.glob("*"):
        stale.unlink()
    if reference is not None:
        write_json(
            sound.task_path,
            coin_change.model_copy(
                update={"reference": reference, "context": starting}
            ).model_dump(mode="json"),
        )

    verdict = DiscriminatesGate().run(context(sound, settings))

    if lost:
        assert verdict.status is Status.FAIL
        assert "has no pre-fix implementation in twins/" in verdict.summary
    else:
        assert verdict.status is Status.SKIP
        assert verdict.skip_reason is SkipReason.NOT_APPLICABLE


# ---- spec.strength.mutation ----------------------------------------------


def test_a_specification_whose_every_mutant_is_refused_passes_without_counting_them(
    sound: Bundle, settings: Settings
) -> None:
    """A refusal can be the proof or the language catching the mutant, so it is no kill."""
    rigged = context(sound, settings, otherwise=CheckResult.no("a counterexample"))

    verdict = MutationGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["survived"] == []
    assert len(verdict.details["refused"]) == verdict.details["generated"]
    assert "refused by the checker, which are not counted" in verdict.summary
    assert verdict.evidence == ["evidence/mutation.txt"]


def test_one_mutant_the_checker_accepts_fails_the_specification_as_too_weak(
    sound: Bundle, settings: Settings
) -> None:
    """Under a prover, an accepted corruption is a proof that the spec is loose."""
    mutants = Screening().mutants(sound.solution(), limit=settings.mutation_limit)
    refused = {f"mutant-{m.id}": CheckResult.no("a counterexample") for m in mutants[1:]}

    verdict = MutationGate().run(context(sound, settings, backend=Proving(), answers=refused))

    assert verdict.status is Status.FAIL
    assert verdict.details["survived"] == [mutants[0].id]
    assert mutants[0].id in verdict.summary


def test_the_same_survivor_under_a_falsifier_is_a_search_that_came_up_empty(
    sound: Bundle, settings: Settings
) -> None:
    verdict = MutationGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert len(verdict.details["survived"]) == verdict.details["generated"]


def test_a_mutant_the_checker_could_not_read_is_not_a_program(
    sound: Bundle, settings: Settings
) -> None:
    """`+` turned into `-` over a sequence is a type error, not a rival implementation."""
    mutants = Screening().mutants(sound.solution(), limit=6)
    answers = {f"mutant-{m.id}": CheckResult.no("a counterexample") for m in mutants[:2]}
    for mutant in mutants[2:]:
        answers[f"mutant-{mutant.id}"] = CheckResult.malformed("type error: str - str")

    verdict = MutationGate().run(
        context(
            sound,
            settings.model_copy(update={"mutation_limit": 6}),
            backend=Proving(),
            answers=answers,
        )
    )

    assert verdict.status is Status.PASS
    assert verdict.details["not_programs"] == [mutant.id for mutant in mutants[2:]]
    assert verdict.details["excluded"] == []


def test_a_run_whose_every_mutant_is_not_a_program_measured_nothing(
    sound: Bundle, settings: Settings
) -> None:
    verdict = MutationGate().run(
        context(sound, settings, otherwise=CheckResult.malformed("type error: str - str"))
    )

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.NOT_APPLICABLE
    assert len(verdict.details["not_programs"]) == verdict.details["generated"]


def refused_at(line: int) -> CheckResult:
    """A refusal the checker placed at one line of the file it was handed."""
    said = f"solution.py:{line}:5: error: unsolved goals"
    return CheckResult.no(said, output=said)


@pytest.mark.parametrize(
    ("backend", "line"),
    [(Tactic(), 12), (Tactic(), 25), (Proving(), 12)],
    ids=["inside its own proof", "at a clause of the specification", "by the contract"],
)
def test_a_refusal_is_not_counted_wherever_the_checker_places_it(
    sound: Bundle, settings: Settings, backend: Screening, line: int
) -> None:
    """Line 12 is inside the solution's `impl` region and line 25 inside its `spec` region.

    A mutant carries the solution file's proof, written for the reference implementation, so
    under a checker that replays it a refusal can be the proof not closing; under any checker it
    can be the language catching the edit. Where the line falls tells the two apart from the
    specification's own answer no better than nothing does.
    """
    verdict = MutationGate().run(
        context(sound, settings, backend=backend, otherwise=refused_at(line))
    )

    assert verdict.status is Status.PASS
    assert len(verdict.details["refused"]) == verdict.details["generated"]
    assert "refused" in (sound.evidence_dir / "mutation.txt").read_text()


def test_a_mutant_the_checker_reached_no_verdict_on_is_not_a_survivor(
    sound: Bundle, settings: Settings
) -> None:
    """Counting a timeout as a survivor would turn a slow machine into a finding."""
    mutants = Screening().mutants(sound.solution(), limit=6)
    answers = {f"mutant-{m.id}": CheckResult.no("a counterexample") for m in mutants[:5]}
    answers[f"mutant-{mutants[5].id}"] = CheckResult.unknown("timed out", timed_out=True)

    verdict = MutationGate().run(
        context(
            sound,
            settings.model_copy(update={"mutation_limit": 6}),
            backend=Proving(),
            answers=answers,
        )
    )

    assert verdict.status is Status.PASS
    assert verdict.details["excluded"] == [mutants[5].id]


#: A file of the Nagini shape whose first assignment is dead: every path overwrites it, so
#: a mutant of that line computes what the reference implementation computes.
CLAMPED = """\
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin spec
def clamp(score: int) -> int:
    Requires(MustTerminate(2))
    Ensures(Implies(score < 0, Result() == 0))
    Ensures(Implies(score > 100, Result() == 100))
    Ensures(Implies(0 <= score and score <= 100, Result() == score))
# benchproofer:end spec
# benchproofer:begin impl
    result = 7  # type: int
    if score < 0:
        result = 0
    elif score > 100:
        result = 100
    else:
        result = score
    return result
# benchproofer:end impl
"""
#: The dead line, as the file has it.
DEAD = "    result = 7  # type: int"
REFUTED = CheckResult.no("Postcondition of clamp might not hold.")


def on_line(solution: str, line: str) -> list[str]:
    """The ids of the mutants `Proving` makes of ``solution`` that edit ``line``."""
    return [m.id for m in Proving().mutants(solution, limit=24) if m.before == line]


def clamped(
    bundle: Bundle,
    settings: Settings,
    accepted: list[str],
    *,
    solution: str = CLAMPED,
    backend: Screening | None = None,
    **answers: CheckResult,
) -> Rigged:
    """A context over ``solution`` whose checker accepts exactly the mutants named."""
    proved = CheckResult.ok("all obligations discharged")
    return context(
        bundle,
        settings,
        backend=backend or Proving(),
        answers={
            **{f"mutant-{name}": proved for name in accepted},
            **{f"mutant-{name}": answer for name, answer in answers.items()},
        },
        otherwise=REFUTED,
        _solution=solution,
    )


def test_a_survivor_that_computes_what_the_shipped_code_computes_is_set_aside(
    sound: Bundle, settings: Settings
) -> None:
    """No specification can refute a program that returns what the shipped one returns.

    Counted as survivors, edits to a value every path overwrites read as a specification
    that leaves the implementation unconstrained, and no repair of it can move the score.
    """
    dead = on_line(CLAMPED, DEAD)
    assert len(dead) == 2

    verdict = MutationGate().run(clamped(sound, settings, dead))

    assert verdict.status is Status.PASS
    assert verdict.details["equivalent"] == dead
    assert verdict.details["survived"] == []
    evidence = (sound.evidence_dir / "mutation.txt").read_text()
    assert f"{dead[0]}: equivalent" in evidence
    assert (
        "equivalence: executed on the same drawn inputs, it returns what the reference"
        in evidence
    )


class Scripting(Proving):
    """A prover whose file carries a proof, so a determinism lemma can be asked of it."""

    name = "scripting"
    proof_carrying = True


#: A specification that pins its result: exactly one result satisfies it at each input, so
#: a mutant that verifies against it returns what the accepted definition returns. Lean's
#: shape, whatever this double's comment token, since that is the syntax the statement the
#: checker is asked for is generated from.
PINNED = """\
# benchproofer:begin spec
def Spec (n : Nat) (result : Nat) : Prop :=
  result = n + n
# benchproofer:end spec
# benchproofer:begin impl
def doubled (n : Nat) : Nat :=
  2 * n
# benchproofer:end impl
# benchproofer:begin proof
theorem doubled_meets_spec (n : Nat) : Spec n (doubled n) := by
  unfold Spec doubled; omega
# benchproofer:end proof
"""


def test_every_survivor_of_a_specification_that_pins_its_result_is_equivalent(
    sound: Bundle, settings: Settings
) -> None:
    """One result per input, and the mutant satisfies the specification: it returns that one.

    So nothing here could be refused by a stronger specification, and no mutant survives.
    """
    mutants = [mutant.id for mutant in Scripting().mutants(PINNED, limit=24)]
    assert mutants
    rigged = context(
        sound,
        settings,
        backend=Scripting(),
        otherwise=CheckResult.ok("all obligations discharged"),
        _solution=PINNED,
    )

    verdict = MutationGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["equivalent"] == mutants
    assert verdict.details["survived"] == []
    evidence = (sound.evidence_dir / "mutation.txt").read_text()
    assert "the checker proves the specification admits one result per input" in evidence


def test_a_survivor_that_computes_something_else_is_still_a_survivor(
    sound: Bundle, settings: Settings
) -> None:
    """The screen sets aside what agrees, and a survivor that differs is the finding."""
    ceiling = on_line(CLAMPED, "        result = 100")
    assert ceiling

    verdict = MutationGate().run(clamped(sound, settings, ceiling))

    assert verdict.status is Status.FAIL
    assert verdict.details["survived"] == ceiling
    assert verdict.details["equivalent"] == []
    evidence = (sound.evidence_dir / "mutation.txt").read_text()
    assert f"{ceiling[0]}: survived" in evidence
    assert "equivalence: not shown: executed beside the reference implementation" in evidence
    assert "something else on `clamp(" in evidence


def test_a_survivor_that_cannot_be_run_to_compare_is_still_a_survivor(
    sound: Bundle, settings: Settings
) -> None:
    """A file assuming a callee has something no direct run can stand in for.

    So the question of equivalence is not decided, and the survivor is charged against the
    specification.
    """
    assuming = CLAMPED.replace(
        "# benchproofer:begin spec",
        "# benchproofer:begin helpers\n@Pure\n@ContractOnly\ndef ceiling() -> int:\n"
        "    Ensures(Result() == 100)\n# benchproofer:end helpers\n\n"
        "# benchproofer:begin spec",
    )
    dead = on_line(assuming, DEAD)

    verdict = MutationGate().run(clamped(sound, settings, dead, solution=assuming))

    assert verdict.status is Status.FAIL
    assert verdict.details["survived"] == dead
    assert verdict.details["equivalent"] == []


def test_a_falsifier_sets_no_survivor_aside(sound: Bundle, settings: Settings) -> None:
    """There the specification is properties run on drawn inputs, which agreement is too."""
    dead = on_line(CLAMPED, DEAD)

    verdict = MutationGate().run(clamped(sound, settings, dead, backend=Screening()))

    assert verdict.details["survived"] == dead
    assert verdict.details["equivalent"] == []
    evidence = (sound.evidence_dir / "mutation.txt").read_text()
    assert "undecided: not run, since under a bounded refuter" in evidence


#: An implementation whose one statement is wider than any column an evidence table fits.
WIDE = """\
def impl(cents):
    return (cents // 25, (cents % 25) // 10, (cents % 25 % 10) // 5, cents % 25 % 10 % 5)
"""


def test_the_evidence_carries_each_mutant_whole(sound: Bundle, settings: Settings) -> None:
    """A repair reads the file to see which lines the specification leaves unconstrained.

    So each mutant is there as a whole: where it is, the full line before and after, and
    what the checker said, however wide the line.
    """
    solution = replace_region(sound.solution(), COMMENT, "impl", WIDE)
    detail = "property_change_is_the_fewest_coins failed on cents=40"
    mutants = Proving().mutants(solution, limit=settings.mutation_limit)

    MutationGate().run(
        context(
            sound,
            settings,
            backend=Proving(),
            otherwise=CheckResult.no(detail),
            _solution=solution,
        )
    )

    evidence = (sound.evidence_dir / "mutation.txt").read_text()
    lines = solution.splitlines()
    assert any(len(mutant.before) > 80 for mutant in mutants)
    for mutant in mutants:
        assert lines[mutant.line - 1] == mutant.before
        assert f"{mutant.id}: refused\n  operator:    {mutant.operator}\n" in evidence
        assert f"  line:        {mutant.line}\n" in evidence
        assert f"  before:      {mutant.before}\n  after:       {mutant.after}\n" in evidence
    assert f"  checker:     refuted: {detail}\n" in evidence


def test_one_line_dense_with_literals_does_not_take_every_pick_of_its_operators() -> None:
    """An operator's first picks in file order would all land on the densest line.

    So each literal operator's share of the limit is spread through every place it applies.
    """
    body = (
        "def f(n):\n    table = (3, 4, 5, 6, 7, 8)\n    if n > 40:\n        return 41\n"
        "    if n > 50:\n        return 51\n    return n + 60\n"
    )
    source = f"{wrap(COMMENT, 'spec', 'assert True')}\n{wrap(COMMENT, 'impl', body)}\n"
    dense = parse(source, COMMENT)["impl"].start + 2

    mutants = generate(source, COMMENT, limit=12)

    assert len(mutants) == 12
    for operator in ("off_by_one_up", "off_by_one_down"):
        lines = {mutant.line for mutant in mutants if mutant.operator == operator}
        assert dense in lines
        assert lines - {dense}, f"every {operator} pick is on the densest line"


#: An implementation carrying the hints a checker reasons with, as a Nagini one does.
ANNOTATED = """\
    i = 0
    n = len(b)
    while i < n:
        Invariant(0 <= i and i <= n)
        Invariant(MustTerminate(n - i + 1))
        if b[i] > 127:
            return False
        i = i + 1
    return True
"""


def test_a_checkers_own_hints_are_never_what_gets_mutated() -> None:
    """A mutated hint is the same program with a broken proof, and it dies for that.

    The checker then refuses it because a step no longer discharges, not because the
    specification caught a behavior change, so it is a mutant spent on nothing: one the
    specification could have accepted is never tried.
    """
    solution = replace_region(
        "# benchproofer:begin spec\ndef f(b):\n    pass\n"
        "# benchproofer:end spec\n\n# benchproofer:begin impl\n    pass\n"
        "# benchproofer:end impl\n",
        COMMENT,
        "impl",
        ANNOTATED,
    )

    unaware = generate(solution, COMMENT, limit=24)
    aware = generate(solution, COMMENT, limit=24, annotations=("Invariant(", "MustTerminate("))

    assert any("Invariant" in mutant.excerpt for mutant in unaware)
    assert not any("Invariant" in mutant.excerpt for mutant in aware)
    assert aware, "the behavioral tokens are still mutable"


LEAN = "--"


def lean(body: str) -> str:
    """A Lean solution whose implementation region is ``body``."""
    return f"{wrap(LEAN, 'spec', 'def Spec : Prop := True')}\n{wrap(LEAN, 'impl', body)}\n"


def mutated(source: str, *, comment: str = LEAN) -> dict[str, set[str]]:
    """Each operator's edits of ``source``, as the lines it rewrote."""
    edits: dict[str, set[str]] = {}
    for mutant in generate(source, comment, limit=1000):
        edits.setdefault(mutant.operator, set()).add(mutant.after.strip())
    return edits


def test_a_lean_implementation_is_mutated_where_it_is_spelled_as_lean_spells_it() -> None:
    """Relations, connectives, options and conditionals, which no ASCII operator reaches."""
    body = (
        "def impl (a b : Nat) (o : Option Nat) : Option Nat :=\n"
        "  if a ≤ b ∧ b ≥ 2 ∨ a ≠ 3 then some (a + 0) else if ¬ o.isSome then none else o\n"  # noqa: RUF001
        "def other (a b : Nat) : Bool := decide (a = b)\n"
    )

    edits = mutated(lean(body))

    line = body.splitlines()[1].strip()
    assert line.replace("a ≤ b", "a < b", 1) in edits["le_to_lt"]
    assert line.replace("b ≥ 2", "b > 2", 1) in edits["ge_to_gt"]
    assert line.replace("a ≠ 3", "a = 3", 1) in edits["ne_to_eq"]
    assert line.replace("∧", "∨", 1) in edits["and_to_or"]  # noqa: RUF001
    assert line.replace("∨ a", "∧ a", 1) in edits["or_to_and"]  # noqa: RUF001
    assert line.replace("¬ o.isSome", "o.isSome", 1) in edits["drop_not"]
    assert line.replace("some (a + 0)", "none", 1) in edits["some_to_none"]
    assert line.replace("then none", "then some default", 1) in edits["none_to_some"]
    assert line.replace(".isSome", ".isNone", 1) in edits["is_some_to_is_none"]
    assert "def other (a b : Nat) : Bool := decide (a ≠ b)" in edits["eq_to_ne"]
    assert edits["swap_branches"] == {
        line.replace("if a ≤ b ∧ b ≥ 2 ∨ a ≠ 3 then", "if ¬(a ≤ b ∧ b ≥ 2 ∨ a ≠ 3) then"),  # noqa: RUF001
        line.replace("if ¬ o.isSome then", "if ¬(¬ o.isSome) then"),
    }


def test_a_constructor_in_a_pattern_is_not_edited_as_a_value() -> None:
    """Edited there it leaves what it binds unbound, which no checker can read."""
    body = (
        "def impl (o : Option Nat) : Option Nat :=\n"
        "  match o with\n"
        "  | some x => some x\n"
        "  | none => none\n"
        "def other (o : Option Nat) : Option Nat := Id.run do\n"
        "  let some y := o | return none\n"
        "  return some y\n"
    )

    edits = mutated(lean(body))

    assert edits["some_to_none"] == {"| some x => none", "return none"}
    assert edits["none_to_some"] == {
        "| none => some default",
        "let some y := o | return some default",
    }


def test_the_predicate_of_a_velvet_choice_is_not_negated() -> None:
    """Velvet finds a value for `x :| x = e` and none for `x :| x ≠ e`, which it refuses."""
    body = "  do\n    let out :| out = n + n\n    let same := decide (out = n)\n    return out"

    edits = mutated(lean(body))

    assert edits["eq_to_ne"] == {"let same := decide (out ≠ n)"}


def test_a_named_condition_and_a_pattern_condition_are_not_negated() -> None:
    """`if h : c` hands `h : c` to its branch, and `if let` binds a pattern."""
    body = (
        "def impl (a b : Nat) (o : Option Nat) : Nat :=\n"
        "  if h : a < b then a else if let some x := o then x else b\n"
    )

    assert "swap_branches" not in mutated(lean(body))


def test_leans_arrows_and_combinators_are_not_read_as_arithmetic() -> None:
    """`<-`, `<|`, `|>`, `<$>`, `<*>`, `<|>` and `<;>` edited as a relation are not programs."""
    body = (
        "def impl (f : Nat → Nat) (xs : List Nat) (o p : Option Nat) : IO Nat := do\n"
        "  let x <- pure (f <| xs.length)\n"
        "  let ys := xs |>.map f\n"
        "  let z := (f <$> o) <|> p\n"
        "  let w := (· + ·) <$> o <*> p\n"
        "  return x\n"
    )

    edits = mutated(lean(body))

    for operator in ("lt_to_le", "gt_to_ge", "sub_to_add", "mul_to_add"):
        assert operator not in edits, edits.get(operator)
    assert "let w := (· - ·) <$> o <*> p" in edits["add_to_sub"]


@pytest.mark.parametrize(
    ("comment", "body", "kept"),
    [
        pytest.param(
            COMMENT,
            "def impl(n):\n"
            '    message = \'Auto-created: 1 or 2\' + """a < b"""\n'
            "    return n + 1, message\n",
            "return n - 1, message",
            id="python",
        ),
        pytest.param(
            LEAN,
            "def impl (n : Nat) : Prod Nat String :=\n"
            '  if n = 0 ∧ "a-b" = "c" then (n + 1, "x < y") else (n, s!"1 or 2")\n',
            'if ¬(n = 0 ∧ "a-b" = "c") then (n + 1, "x < y") else (n, s!"1 or 2")',
            id="lean",
        ),
        pytest.param(
            "//",
            'method Impl(n: int) returns (r: int, s: string) {\n  r := n + 1; s := "a-1";\n}\n',
            'r := n - 1; s := "a-1";',
            id="another language",
        ),
    ],
)
def test_a_string_literal_is_prose_to_the_mutator(comment: str, body: str, kept: str) -> None:
    """A `-` turned into `+` inside a message is not an operator changed.

    And where an edit quotes code around a literal, it quotes the literal as written.
    """
    source = f"{wrap(comment, 'spec', 'spec')}\n{wrap(comment, 'impl', body)}\n"

    after = {line for lines in mutated(source, comment=comment).values() for line in lines}

    assert kept in after
    literals = re.findall(r"'[^']*'|\"[^\"]*\"", body)
    for mutant in generate(source, comment, limit=1000):
        assert all(literal in mutant.after for literal in literals if literal in mutant.before)


def test_lean_operators_are_not_applied_to_another_language() -> None:
    """Python's `=` assigns, and `if … then` is how Dafny writes a conditional expression."""
    body = "def impl(cents):\n    total = cents\n    return total if total else 0\n"
    source = f"{wrap(COMMENT, 'spec', 'assert True')}\n{wrap(COMMENT, 'impl', body)}\n"

    edits = mutated(source, comment=COMMENT)

    assert not {"eq_to_ne", "swap_branches", "none_to_some"} & set(edits)


def test_a_velvet_loops_proof_annotations_are_never_what_gets_mutated() -> None:
    """They are the loop's proof, which a proof session may rewrite; the loop's code is not."""
    backend = BACKENDS.get("velvet")
    loop = (
        "  do\n"
        "    let mut i := 0\n"
        "    while i < n\n"
        "      invariant i ≤ n\n"
        "      decreasing n - i\n"
        "    do\n"
        "      i := i + 1\n"
        "    return i + i"
    )
    source = replace_region(backend.template(), backend.comment, "impl", loop)

    mutants = backend.mutants(source, limit=1000)

    assert mutants
    assert not any("invariant" in m.before or "decreasing" in m.before for m in mutants)
    assert {m.before.strip() for m in mutants} >= {"while i < n", "i := i + 1"}


def test_a_run_in_which_the_checker_decided_no_mutant_is_an_error_rather_than_a_score(
    sound: Bundle, settings: Settings
) -> None:
    """Nothing refused and nothing accepted says nothing either way."""
    verdict = MutationGate().run(
        context(sound, settings, otherwise=CheckResult.unknown("timed out"))
    )

    assert verdict.status is Status.ERROR
    assert len(verdict.details["excluded"]) == verdict.details["generated"]


def test_an_implementation_with_nothing_to_mutate_is_not_applicable(
    sound: Bundle, settings: Settings
) -> None:
    write_text(
        sound.solution_path,
        replace_region(sound.solution(), COMMENT, "impl", "def impl(cents):\n    pass\n"),
    )

    verdict = MutationGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.NOT_APPLICABLE


def test_mutation_is_not_judged_until_the_shipped_specification_verifies(
    sound: Bundle, settings: Settings
) -> None:
    rigged = context(sound, settings, answers={"solution": CheckResult.no("cents=40")})

    verdict = MutationGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert rigged.checked == ["solution"]


def test_every_mutant_carries_the_shipped_specification_unchanged(
    sound: Bundle, settings: Settings
) -> None:
    """The invariant the score rests on: a mutant cannot weaken what it is judged by.

    Mutating the specification instead would produce a file that fails for a reason
    the implementation had nothing to do with, and count it as strength.
    """
    backend = Screening()
    solution = sound.solution()
    mutants = backend.mutants(solution, limit=settings.mutation_limit)

    assert mutants
    assert len(mutants) <= settings.mutation_limit
    assert len({mutant.source for mutant in mutants}) == len(mutants)
    for mutant in mutants:
        assert backend.same_spec(solution, mutant.source)
        assert mutant.source != solution
        regions = parse(mutant.source, COMMENT)
        assert regions["impl"].text != parse(solution, COMMENT)["impl"].text


def test_every_implementation_region_is_mutated() -> None:
    """A fix that changed two functions is only half tested by mutating one of them."""
    source = (
        f"{wrap(COMMENT, 'spec', 'assert True')}\n"
        f"{wrap(COMMENT, 'impl', 'def a(x):' + chr(10) + '    return x + 1')}\n"
        f"{wrap(COMMENT, 'spec.2', 'assert True')}\n"
        f"{wrap(COMMENT, 'impl.2', 'def b(x):' + chr(10) + '    return x * 2')}\n"
    )

    mutants = generate(source, COMMENT, limit=24)

    changed = {
        name
        for mutant in mutants
        for name in ("impl", "impl.2")
        if parse(mutant.source, COMMENT)[name].text != parse(source, COMMENT)[name].text
    }
    assert changed == {"impl", "impl.2"}
    assert all(
        sum(
            parse(mutant.source, COMMENT)[name].text != parse(source, COMMENT)[name].text
            for name in ("impl", "impl.2")
        )
        == 1
        for mutant in mutants
    )
