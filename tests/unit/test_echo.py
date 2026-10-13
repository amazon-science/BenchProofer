# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The files that ask a checker whether an attack computes what the solution file computes."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchproofer.backends.base import CheckResult, Closure
from benchproofer.backends.lean4 import Lean4Backend
from benchproofer.backends.velvet import VelvetBackend
from benchproofer.core import echo
from benchproofer.core.markers import named, parse

ACCEPTED = """\
import Mathlib

-- benchproofer:begin spec
def Spec (n : Nat) (r : Nat) : Prop :=
  r = n + n
-- benchproofer:end spec

-- benchproofer:begin impl
def double (n : Nat) : Nat :=
  2 * n
-- benchproofer:end impl

-- benchproofer:begin proof
theorem double_meets_spec (n : Nat) : Spec n (double n) := by
  unfold Spec double
  omega
-- benchproofer:end proof
"""


def attack(body: str, proof: str = "") -> str:
    """``ACCEPTED`` with another implementation, and another proof where one is given."""
    source = ACCEPTED.replace("def double (n : Nat) : Nat :=\n  2 * n", body)
    if proof:
        start = source.index("theorem double_meets_spec")
        end = source.index("-- benchproofer:end proof")
        source = source[:start] + proof + "\n" + source[end:]
    return source


RESTATED = attack("def double (n : Nat) : Nat :=\n  n + n")


def test_two_lean_implementations_are_compared_side_by_side() -> None:
    """The attack's definitions live in a namespace, so both functions can be named."""
    probe = echo.equality(ACCEPTED, RESTATED, Lean4Backend())

    assert f"namespace {echo.NAMESPACE}\n\ndef double (n : Nat) : Nat :=\n  n + n" in probe
    assert f"@{echo.NAMESPACE}.double = @double" in probe
    # The reference implementation stays at the root, and its own proof is gone: what is
    # asked is about the two programs, not the script that proved one of them.
    assert "def double (n : Nat) : Nat :=\n  2 * n" in probe
    assert "double_meets_spec" not in probe
    regions = parse(probe, "--")
    assert named(regions, "proof") == ("proof",)
    assert "theorem benchproof_echo_1" in regions["proof"].text


@pytest.mark.parametrize(
    "body",
    [
        "set_option maxHeartbeats 0 in\ndef double (n : Nat) : Nat :=\n  n + n",
        "end BenchproofAttack\ndef double (n : Nat) : Nat :=\n  n + n",
        'macro "grind" : tactic => `(tactic| trivial)\ndef double (n : Nat) : Nat := n + n',
        "def double (n : Nat) : Nat :=\n  sorry",
        "def triple (n : Nat) : Nat := 3 * n",
    ],
    ids=["an option", "the namespace closed", "a tactic redefined", "a hole", "no shared name"],
)
def test_an_implementation_the_probe_cannot_compare_is_not_compared(body: str) -> None:
    """It changes how the file is read, holds a hole, or shares no function to compare."""
    assert echo.equality(ACCEPTED, attack(body), Lean4Backend()) == ""


VELVET = """\
import Velvet.Std

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

-- benchproofer:begin spec
method pick (flag : Bool) (tag : Int)
    return (out : Int)
  require tag ≥ 0
  ensures out = (if flag then tag else -1)
-- benchproofer:end spec
-- benchproofer:begin impl
  do
    if flag then
      return tag
    else
      return -1
-- benchproofer:end impl

-- benchproofer:begin proof
prove_correct pick by
  loom_solve
-- benchproofer:end proof
"""


def test_two_velvet_methods_are_compared_by_what_they_extract() -> None:
    """A method is a program, not a function, so its extracted executable is compared."""
    offered = VELVET.replace(
        "    if flag then\n      return tag", "    if !flag then\n      return -1"
    )

    probe = echo.equality(VELVET, offered, VelvetBackend())

    namespace = probe.index(f"namespace {echo.NAMESPACE}")
    assert probe.index("extract_program_for pick") < namespace
    inside = probe[namespace : probe.index(f"end {echo.NAMESPACE}")]
    assert "method pick (flag : Bool)" in inside
    assert "if !flag then" in inside
    assert "extract_program_for pick" in inside
    assert f"{echo.NAMESPACE}.pickExec x1 x2 = pickExec x1 x2" in probe
    # Under the precondition, so a reviewer who reshaped the attack to differ where the
    # specification admits nothing is still asking about one program.
    assert "prove_precondition_decidable_for pick" in probe
    assert "@decide _ (pickPreDecidable x1 x2) = true →" in probe
    assert "funext" not in probe
    assert "prove_correct pick" not in probe


def test_a_velvet_method_is_determined_over_its_decidable_conditions() -> None:
    """Velvet names neither condition, so the statement is over the instances deciding them."""
    probe = echo.determined(VELVET, VelvetBackend())

    assert "prove_precondition_decidable_for pick" in probe
    assert "prove_postcondition_decidable_for pick" in probe
    assert "∀ x1 x2 r1 r2, @decide _ (pickPreDecidable x1 x2) = true" in probe
    assert "@decide _ (pickPostDecidable x1 x2 r1) = true" in probe
    assert "r1 = r2 := by" in probe


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            "-- benchproofer:begin spec\n",
            "-- benchproofer:begin spec\n-- `pick` returns the tag when the flag is set.\n",
        ),
        ("(flag : Bool) (tag : Int)", "(flag : Bool) -- (the switch)\n    (tag : Int)"),
    ],
    ids=["a comment before the header", "a comment among the binders"],
)
def test_a_velvet_header_is_read_past_its_comments(old: str, new: str) -> None:
    """Both probes bind one name per input, whatever prose the region holds."""
    commented = VELVET.replace(old, new)

    determined = echo.determined(commented, VelvetBackend())
    equal = echo.equality(commented, commented, VelvetBackend())

    assert "∀ x1 x2 r1 r2, @decide _ (pickPreDecidable x1 x2) = true" in determined
    assert f"{echo.NAMESPACE}.pickExec x1 x2 = pickExec x1 x2" in equal


def test_a_method_that_returns_through_a_mutable_parameter_is_not_determined() -> None:
    mutable = VELVET.replace("method pick (flag : Bool)", "method pick (mut flag : Bool)")

    assert echo.determined(mutable, VelvetBackend()) == ""


def test_a_lean_specification_is_determined_by_its_own_lemma_or_by_general_tactics() -> None:
    probe = echo.determined(ACCEPTED, Lean4Backend())

    assert "∀ x1 r1 r2, Spec x1 r1 → Spec x1 r2 → r1 = r2" in probe
    assert "(exact double_meets_spec x1 r1 r2 h1 h2; done)" in probe
    assert "(unfold Spec at h1 h2; grind)" in probe


def test_an_attack_keeps_the_claims_the_accepted_file_states_about_its_implementation() -> None:
    """Sharing one claim is what the screen asks; meeting the specification needs this one."""
    backend = Lean4Backend()
    unrelated = attack(
        "def double (n : Nat) : Nat :=\n  n + n", "theorem unrelated : 1 = 1 := rfl"
    )

    assert echo.keeps_claims(ACCEPTED, RESTATED, backend)
    assert not echo.keeps_claims(ACCEPTED, unrelated, backend)


def test_a_claim_that_binds_a_name_before_it_names_the_implementation_is_about_it() -> None:
    """The statement runs past the `:=` of its `let`, to where the proof begins."""
    backend = Lean4Backend()
    bound = "theorem double_meets_spec (n : Nat) : let r := double n; Spec n r := by"
    accepted = ACCEPTED.replace(
        "theorem double_meets_spec (n : Nat) : Spec n (double n) := by", bound
    )
    restated = attack("def double (n : Nat) : Nat :=\n  n + n", f"{bound}\n  simp")

    assert echo.keeps_claims(accepted, restated, backend)
    assert not echo.keeps_claims(accepted, RESTATED, backend)


class Closing(Lean4Backend):
    """Lean's metadata, with the axiom report scripted."""

    def __init__(self, closure: Closure | None) -> None:
        self.reported = closure
        self.asked = 0

    def closure(
        self, source: str, *, workdir: Path, timeout_s: float = 120.0
    ) -> Closure | None:
        self.asked += 1
        return self.reported


@pytest.mark.parametrize(
    ("checked", "closure", "holds", "asked"),
    [
        (CheckResult.ok("elaborated"), None, True, 1),
        (CheckResult.ok("elaborated"), Closure(True, "closed"), True, 1),
        (CheckResult.ok("elaborated"), Closure(False, "rests on an axiom"), False, 1),
        (CheckResult.ok("elaborated"), Closure(True, "no answer", settled=False), False, 1),
        (CheckResult.no("unsolved goals"), Closure(True, "closed"), False, 0),
    ],
    ids=["no report", "closed", "an axiom", "unsettled", "refused"],
)
def test_a_probe_holds_only_accepted_and_resting_on_nothing_extra(
    checked: CheckResult, closure: Closure | None, holds: bool, asked: int, tmp_path: Path
) -> None:
    """The closure takes elaboration for granted, so acceptance is asked of it first."""
    backend = Closing(closure)

    said = echo.holds("probe", backend, check=lambda _: checked, workdir=tmp_path, timeout_s=1)

    assert said is holds
    assert backend.asked == asked
