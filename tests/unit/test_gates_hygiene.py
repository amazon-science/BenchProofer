# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Specification hygiene: what the checker is allowed to be asked.

Every later gate reads an accepting verdict as a claim about the implementation, and
this gate is where the shapes that would make that reading wrong are caught -- before
any checker is started, which is why no test here needs one. Three of them are worth
naming, because each turns a passing verification into a statement about nothing: a
specification that discharges its obligation by assertion, one that never claims the
implementation returns, and a file whose proof is of some other proposition entirely.

The masking rule cuts both ways and both directions are tested: prose that mentions a
banned construct is not a use of one, and prose that mentions the termination
obligation is not a claim of one.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from benchproofer.backends.base import Backend
from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.markers import parse, replace_region, wrap
from benchproofer.core.verdict import Level, Status
from benchproofer.gates.hygiene import MIN_SPEC_TOKENS, HygieneGate
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import write_text
from doubles import Proving, Rigged, Screening

COMMENT = "#"

#: One property, in the form the shipped falsifier reads, for a test that needs a
#: specification region of its own rather than the fixture's three.
PROPERTY = """\
@given(AMOUNTS)
def property_change_sums_to_the_amount(cents):
    quarters, dimes, nickels, pennies = impl(cents)
    assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents
"""


class Obliged(Proving):
    """A prover whose postconditions hold only of the runs that reach the return.

    Nagini's shape, in the form the gate reads it: a token the specification has to
    carry, because acceptance says nothing about termination without it.
    """

    name: ClassVar[str] = "obliged"
    termination_tokens: ClassVar[tuple[str, ...]] = ("MustTerminate",)


def context(bundle: Bundle, settings: Settings, backend: Backend | None = None) -> Rigged:
    """A context for a gate that consults no checker at all."""
    return Rigged(
        bundle=bundle,
        backend=backend or Screening(),
        settings=settings,
        level=Level.STATIC,
    )


def region(bundle: Bundle, name: str) -> str:
    """The current text of one region of the bundle's solution file."""
    return parse(bundle.solution(), COMMENT)[name].text


def rewrite(bundle: Bundle, name: str, text: str) -> None:
    """Put ``text`` in one region of the bundle's solution file."""
    write_text(bundle.solution_path, replace_region(bundle.solution(), COMMENT, name, text))


def test_a_well_formed_solution_names_the_regions_it_ships(
    sound: Bundle, settings: Settings
) -> None:
    """A checker that checks termination and attaches obligations itself asks for neither."""
    assert Screening().termination_tokens == ()
    assert Screening().proof_tokens == ()
    rigged = context(sound, settings)

    verdict = HygieneGate().run(rigged)

    assert verdict.status is Status.PASS, verdict.summary
    assert verdict.details["regions"] == ["helpers", "impl", "spec"]
    assert verdict.details["spec_tokens"] > MIN_SPEC_TOKENS
    assert rigged.checked == []


def test_a_construct_that_discharges_an_obligation_by_assertion_is_rejected(
    sound: Bundle, settings: Settings
) -> None:
    """`assume(False)` makes every property vacuous, so the search proves nothing."""
    rewrite(sound, "impl", "def impl(cents):\n    assume(False)\n    return (0, 0, 0, 0)\n")

    verdict = HygieneGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL
    assert "banned construct(s): 'assume(False' at line" in verdict.summary


def test_a_banned_construct_named_in_prose_is_not_a_use_of_one(
    sound: Bundle, settings: Settings
) -> None:
    """What matters is what the checker reads, and it does not read comments."""
    prose = f"{COMMENT} no assume(False here, and no sys.exit\n"
    rewrite(sound, "impl", prose + region(sound, "impl"))

    verdict = HygieneGate().run(context(sound, settings))

    assert verdict.status is Status.PASS, verdict.summary


class Contracted(Screening):
    """The same falsifier with its contracts in docstrings, as CrossHair writes them.

    Under PEP 316 a docstring is what the checker reads, so a string is not prose to it.
    """

    name: ClassVar[str] = "contracted"
    inert_strings: ClassVar[bool] = False


class Assuming(Proving):
    """A prover that takes a declared function's contract on trust, as Nagini does."""

    name: ClassVar[str] = "assuming"
    assumption_tokens: ClassVar[tuple[str, ...]] = ("ContractOnly",)


#: A docstring naming the banned constructs, written above the implementation.
DISCLAIMER = '"""Never calls sys.exit, and makes no assume(False either."""\n'


def test_a_banned_construct_named_in_a_docstring_is_not_a_use_of_one(
    sound: Bundle, settings: Settings
) -> None:
    """A checker that reads nothing inside a string reads a docstring as a comment."""
    assert Screening().inert_strings
    rewrite(sound, "impl", DISCLAIMER + region(sound, "impl"))

    verdict = HygieneGate().run(context(sound, settings))

    assert verdict.status is Status.PASS, verdict.summary


def test_a_banned_construct_in_a_docstring_is_used_where_the_docstring_is_the_contract(
    sound: Bundle, settings: Settings
) -> None:
    """The other direction: under PEP 316 the checker evaluates what a docstring says."""
    rewrite(sound, "impl", DISCLAIMER + region(sound, "impl"))

    verdict = HygieneGate().run(context(sound, settings, Contracted()))

    assert verdict.status is Status.FAIL
    assert "'sys.exit' at line" in verdict.summary


def test_an_assumption_named_in_the_module_docstring_is_not_one_outside_the_axioms_region(
    sound: Bundle, settings: Settings
) -> None:
    """A docstring saying the file assumes nothing does not make it assume something."""
    docstring = '"""A model of change-making.\n\nIt consumes no `@ContractOnly` axiom.\n"""\n'
    write_text(sound.solution_path, docstring + sound.solution())

    verdict = HygieneGate().run(context(sound, settings, Assuming()))

    assert verdict.status is Status.PASS, verdict.summary


def test_an_assumption_outside_the_axioms_region_is_still_found_beside_a_docstring(
    sound: Bundle, settings: Settings
) -> None:
    """Masking the prose must leave the decorator that assumes something in view."""
    assumed = '@ContractOnly\ndef coins(cents):\n    """Assumed rather than modelled."""\n\n'
    rewrite(sound, "impl", assumed + region(sound, "impl"))

    verdict = HygieneGate().run(context(sound, settings, Assuming()))

    assert verdict.status is Status.FAIL
    assert "assumption(s) outside the axioms region: 'ContractOnly' at line" in verdict.summary


def test_a_specification_too_short_to_state_an_obligation_is_rejected(
    sound: Bundle, settings: Settings
) -> None:
    rewrite(sound, "spec", "assert True\n")

    verdict = HygieneGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL
    assert f"below the {MIN_SPEC_TOKENS} needed" in verdict.summary


@pytest.mark.parametrize(
    "line",
    [
        "import subprocess\n",
        "import math, subprocess\n",
        "import subprocess; x = 1\n",
        "if True:\n    import subprocess\n",
        "def reach():\n    import subprocess\n",
    ],
)
def test_a_file_that_reaches_outside_itself_is_rejected(
    line: str, sound: Bundle, settings: Settings
) -> None:
    """A property that imports what the checker cannot see is judging something else.

    However the import is laid out: the second name of one statement, a statement sharing
    its line, or one nested under an `if` or inside a function.
    """
    rewrite(sound, "helpers", f"{line}{region(sound, 'helpers')}")

    verdict = HygieneGate().run(context(sound, settings))

    assert verdict.status is Status.FAIL
    assert "disallowed import(s): subprocess" in verdict.summary


def test_prose_that_wraps_onto_a_line_beginning_from_is_not_an_import(
    sound: Bundle, settings: Settings
) -> None:
    """A docstring sentence wrapped onto a line beginning `from this set` imports nothing."""
    prose = '"""Pick the largest element\nfrom this set, and count how often\nit wins.\n"""\n'
    rewrite(sound, "helpers", f"{prose}{region(sound, 'helpers')}")

    verdict = HygieneGate().run(context(sound, settings))

    assert verdict.status is Status.PASS, verdict.summary


# ---- claiming that the implementation returns -----------------------------


def test_a_specification_that_claims_nothing_about_termination_is_rejected(
    sound: Bundle, settings: Settings
) -> None:
    """Under this checker an accepting verdict covers only the runs that return."""
    verdict = HygieneGate().run(context(sound, settings, Obliged()))

    assert verdict.status is Status.FAIL
    assert "the spec region claims nothing about termination" in verdict.summary
    assert "MustTerminate" in verdict.summary


def test_the_same_specification_passes_once_it_claims_the_implementation_returns(
    sound: Bundle, settings: Settings
) -> None:
    rewrite(sound, "spec", f"Requires(MustTerminate(1))\n{PROPERTY}")

    verdict = HygieneGate().run(context(sound, settings, Obliged()))

    assert verdict.status is Status.PASS, verdict.summary


@pytest.mark.parametrize(
    ("name", "stated"),
    [
        ("impl", "Invariant(MustTerminate(1))\n"),
        ("spec", f"{COMMENT} MustTerminate belongs here\n"),
        ("spec", '"""Requires(MustTerminate(1)) belongs here."""\n'),
    ],
    ids=["in-the-implementation", "in-a-comment", "in-a-docstring"],
)
def test_an_obligation_the_checker_is_not_held_to_is_not_a_claim_of_one(
    name: str, stated: str, sound: Bundle, settings: Settings
) -> None:
    """The obligation has to be code of the specification region.

    A mutant, a rival, and an attack each ship their own implementation region, so one
    stated there is not part of what any of them is judged against; and a comment or a
    string naming it is nothing a checker discharges.
    """
    body = region(sound, "impl") if name == "impl" else PROPERTY
    rewrite(sound, name, f"{stated}{body}")

    verdict = HygieneGate().run(context(sound, settings, Obliged()))

    assert verdict.status is Status.FAIL
    assert "the spec region claims nothing about termination" in verdict.summary


# ---- proving something about this file ------------------------------------


class Replaying(Proving):
    """A prover that replays a proof the file writes out as its own declaration.

    Lean's shape, in the form the gate reads it. Such a checker answers whether the
    file elaborated, and a proof of an unrelated proposition elaborates as readily as
    a proof about this implementation, so the claim has to name what the file declares.
    """

    name: ClassVar[str] = "replaying"
    proof_carrying: ClassVar[bool] = True
    proof_tokens: ClassVar[tuple[str, ...]] = ("theorem", "lemma")


#: A claim that names the property in the spec region and the function in the impl
#: region, which is the shape the gate is looking for.
HONEST = "theorem impl_meets_it : property_change_sums_to_the_amount impl := by\n    reduce\n"


def with_proof(bundle: Bundle, text: str) -> None:
    """Give the bundle's solution file a proof region holding ``text``."""
    write_text(bundle.solution_path, f"{bundle.solution()}\n{wrap(COMMENT, 'proof', text)}")


def test_a_proof_of_what_this_file_declares_is_what_the_gate_wants(
    sound: Bundle, settings: Settings
) -> None:
    with_proof(sound, HONEST)

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.PASS, verdict.summary


def test_a_claim_that_binds_a_name_in_its_statement_is_read_whole(
    sound: Bundle, settings: Settings
) -> None:
    """The `:=` of a `let` in the statement is not the one that begins the proof."""
    with_proof(
        sound,
        "theorem impl_meets_it : let r := impl; property_change_sums_to_the_amount r := by\n"
        "    reduce\n",
    )

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.PASS, verdict.summary


def test_a_proof_of_an_unrelated_proposition_is_rejected(
    sound: Bundle, settings: Settings
) -> None:
    """`theorem nothing : True` elaborates, so acceptance would say nothing at all."""
    with_proof(sound, "theorem nothing_at_all : True := by\n    trivial\n")

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.FAIL
    assert "nothing the proof region proves names what" in verdict.summary
    assert "the impl region declares impl" in verdict.summary


#: A second modeled function, in the numbered regions a multi-function file holds.
SECOND = (
    wrap(
        COMMENT,
        "spec.2",
        "def property_twice_doubles(cents):\n    assert twice(cents) == cents * 2\n",
    )
    + "\n"
    + wrap(COMMENT, "impl.2", "def twice(cents):\n    return cents + cents\n")
)
#: What a proof of the second function claims, in the shape the gate looks for.
SECOND_PROOF = "theorem twice_meets_it : property_twice_doubles twice := by\n    reduce\n"


def test_each_modelled_function_needs_a_claim_of_its_own(
    sound: Bundle, settings: Settings
) -> None:
    """A proof of the first function would otherwise stand for a second nothing proves."""
    write_text(
        sound.solution_path, f"{sound.solution()}\n{SECOND}\n{wrap(COMMENT, 'proof', HONEST)}"
    )

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.FAIL
    assert "the impl.2 region declares twice" in verdict.summary
    assert "the spec.2 region declares property_twice_doubles" in verdict.summary


def test_a_claim_for_each_modelled_function_is_what_the_gate_wants(
    sound: Bundle, settings: Settings
) -> None:
    proof = wrap(COMMENT, "proof", HONEST + SECOND_PROOF)
    write_text(sound.solution_path, f"{sound.solution()}\n{SECOND}\n{proof}")

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.PASS, verdict.summary


def test_a_proof_that_names_the_specification_but_not_the_implementation_is_rejected(
    sound: Bundle, settings: Settings
) -> None:
    """A property proved of some other function is not a property of this one."""
    with_proof(sound, "theorem about_something_else : property_change_uses_no_negative_coin\n")

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.FAIL
    assert "the impl region declares impl" in verdict.summary


def test_a_file_that_ships_no_proof_for_a_checker_that_replays_one_is_rejected(
    sound: Bundle, settings: Settings
) -> None:
    """Nothing else in the file makes an accepting verdict a claim about anything."""
    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.FAIL
    assert "the file ships no proof region" in verdict.summary


@pytest.mark.parametrize(
    "proof",
    [
        "    reduce\n    trivial\n",
        f"{COMMENT} theorem impl_meets_it : this is where it would go\n",
    ],
    ids=["tactics-alone", "a-claim-in-prose"],
)
def test_a_proof_region_that_states_no_claim_is_rejected(
    proof: str, sound: Bundle, settings: Settings
) -> None:
    """Tactics alone, or a claim named only in a comment, leave the obligation unattached."""
    with_proof(sound, proof)

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.FAIL
    assert "the proof region states no claim" in verdict.summary


def test_a_supporting_lemma_may_be_about_anything(sound: Bundle, settings: Settings) -> None:
    """What the gate wants is one claim about this file, not every claim in the region."""
    with_proof(sound, f"lemma arithmetic : 25 = 5 * 5 := by\n    trivial\n\n{HONEST}")

    verdict = HygieneGate().run(context(sound, settings, Replaying()))

    assert verdict.status is Status.PASS, verdict.summary


@pytest.mark.parametrize("name", BACKENDS.names())
def test_the_skeleton_a_backend_ships_is_one_this_gate_accepts(
    name: str, sound: Bundle, settings: Settings
) -> None:
    """`benchproofer scaffold` hands a drafter this file, so it has to be a legal one.

    It is also where every backend's idea of a well-formed solution meets every screen
    this gate applies, which keeps a backend from declaring a token its template lacks.
    """
    backend = BACKENDS.get(name)
    write_text(sound.solution_path, backend.template())

    verdict = HygieneGate().run(context(sound, settings, backend))

    assert verdict.status is Status.PASS, f"{name}: {verdict.summary}"


#: A constant no proof can unfold, standing for a callee the file does not model.
OPAQUE = "opaque price : Nat → Nat"


def with_region(backend: Backend, body: str, *, where: str = "axioms") -> str:
    """The backend's skeleton with ``body`` in a region of its own ahead of the spec."""
    skeleton = backend.template()
    opening = f"{backend.comment} benchproofer:begin spec"
    return skeleton.replace(opening, f"{wrap(backend.comment, where, body)}\n\n{opening}", 1)


@pytest.mark.parametrize("name", ["lean4", "velvet"])
def test_an_opaque_constant_is_an_assumption_that_has_to_name_its_callee(
    name: str, sound: Bundle, settings: Settings
) -> None:
    """`opaque` states nothing about the callee, and still leaves it unmodeled.

    A specification stated over one rests on a callee nothing grounds, and `#print axioms`
    does not list it, so it is held to what an `axiom` is: the `axioms` region, with the
    callee named there for `spec.axioms_grounded` and `audit.axiom_soundness` to run.
    """
    backend = BACKENDS.get(name)
    marked = f"{backend.comment} benchproofer:axiom shop.price\n{OPAQUE}"

    write_text(sound.solution_path, with_region(backend, OPAQUE))
    unnamed = HygieneGate().run(context(sound, settings, backend))
    write_text(sound.solution_path, with_region(backend, OPAQUE, where="helpers"))
    outside = HygieneGate().run(context(sound, settings, backend))
    write_text(sound.solution_path, with_region(backend, marked))
    named = HygieneGate().run(context(sound, settings, backend))

    assert unnamed.status is Status.FAIL
    assert "the axioms region assumes something without naming the callee it represents" in (
        unnamed.summary
    )
    assert outside.status is Status.FAIL
    assert "assumption(s) outside the axioms region: 'opaque ' at line" in outside.summary
    assert named.status is Status.PASS, named.summary


def test_a_choice_in_a_velvet_method_body_is_not_an_assumption(
    sound: Bundle, settings: Settings
) -> None:
    """Loom has the method show the choice can be made, and meet its contract for each one."""
    backend = BACKENDS.get("velvet")
    chosen = "  do\n    let out :| out = n + n\n    return out"
    skeleton = backend.template()
    write_text(
        sound.solution_path,
        replace_region(skeleton, backend.comment, "impl", chosen),
    )

    verdict = HygieneGate().run(context(sound, settings, backend))

    assert verdict.status is Status.PASS, verdict.summary


def second_function(bundle: Bundle, spec: str) -> None:
    """Model a second function in the bundle's solution file, with ``spec`` as its contract."""
    second = (
        f"\n{wrap(COMMENT, 'spec.2', spec)}\n"
        f"{wrap(COMMENT, 'impl.2', 'def impl2(cents):' + chr(10) + '    return cents')}\n"
    )
    write_text(bundle.solution_path, bundle.solution() + second)


def test_every_function_the_file_models_has_to_claim_it_returns(
    sound: Bundle, settings: Settings
) -> None:
    """One contract that claims termination does not cover another function's runs."""
    rewrite(sound, "spec", f"Requires(MustTerminate(1))\n{PROPERTY}")
    second_function(sound, PROPERTY.replace("sums_to", "second_sums_to"))

    verdict = HygieneGate().run(context(sound, settings, Obliged()))

    assert verdict.status is Status.FAIL
    assert "the spec.2 region claims nothing about termination" in verdict.summary
    assert "the spec region claims" not in verdict.summary


def test_a_file_that_models_two_functions_that_each_claim_it_passes(
    sound: Bundle, settings: Settings
) -> None:
    rewrite(sound, "spec", f"Requires(MustTerminate(1))\n{PROPERTY}")
    second_function(
        sound, "Requires(MustTerminate(1))\n" + PROPERTY.replace("sums_to", "second_sums_to")
    )

    verdict = HygieneGate().run(context(sound, settings, Obliged()))

    assert verdict.status is Status.PASS, verdict.summary
    assert verdict.details["regions"] == ["helpers", "impl", "impl.2", "spec", "spec.2"]
