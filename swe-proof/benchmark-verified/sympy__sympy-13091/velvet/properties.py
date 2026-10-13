"""properties.py — G-PBT falsification battery for sympy__sympy-13091 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
every ``prove_correct`` header survives byte-identically) and swaps in a
candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (three contracted methods over read-only inputs; no ``require``
clause anywhere, no ``mut`` binder anywhere).

  directEquality (operand : Operand) → (out : Verdict)
      D1  out = eqResult operand                                    -- master
      D2  operand = .foreign         → out = .undecided             -- the decline
      D3  operand = .matchingEqual   → out = .isTrue
      D4  operand = .matchingUnequal → out = .isFalse
    The verdict a value reports for an operand. LOAD-BEARING: D2 — an operand the
    value cannot interpret must be reported ``.undecided`` (a DECLINE, so the
    comparison can be delegated), never ``.isFalse``.

  equalityCompare (operand : Operand) (reflectedV : Verdict) → (out : Bool)
      E1  out = resolveEq (eqResult operand) reflectedV              -- master
      E2  (operand = .foreign ∧ reflectedV = .isTrue)    → out = true
      E3  (operand = .foreign ∧ reflectedV = .isFalse)   → out = false
      E4  (operand = .foreign ∧ reflectedV = .undecided) → out = false
      E5  (operand = .matchingEqual)                     → out = true
    The comparison OPERATOR's resolution. LOAD-BEARING: E2 — a value that
    declined, facing an operand whose own (reflected) logic DOES recognise it,
    compares EQUAL. That outcome is reachable only because the verdict was a
    decline rather than a decision, which is what keeps the relation symmetric.
    E4 pins the both-decline fallback; E5 pins that a DECIDED verdict
    short-circuits and is never overridden by the reflected input.

  inequalityCompare (operand : Operand) (reflectedV : Verdict) → (out : Bool)
      N1  out = neResult (eqResult operand) reflectedV               -- master
      N2  (operand = .foreign ∧ reflectedV = .undecided) → out = true
      N3  (operand = .foreign ∧ reflectedV = .isTrue)    → out = false
      N4  (operand = .matchingEqual)                     → out = false
    The inequality comparison. LOAD-BEARING: N2 — the negation is applied to the
    OPERATOR-RESOLVED decision, not to the raw verdict. Negating a raw decline
    directly would silently read "I cannot decide" as "equal" and answer ``false``
    where the resolved answer is ``true``.

``eqResult`` / ``resolveEq`` / ``neResult`` are total, fully unfolded ``def``s in
the ``pure`` region over the methods' OWN arguments; the ``axioms`` region
declares no ``axiom`` (``meta.json`` axioms == []). Both carriers derive
``DecidableEq`` and are finite (3 × 3 = 9 input points), so every refutation
below is stated at a CONCRETE constructor literal and ``decide`` reduces fully —
no conditioning on an opaque term is needed anywhere in this bundle.

ADVERSARIAL READ of the sibling's classes:

  * PARTIAL-DOMAIN — the heart of this surface, and the class the sibling leans on
    hardest. The three-outcome verdict carrier makes a rival's error naturally
    confined to ONE arm: the declining arm (the sub-domain that fails first), the
    equal arm, or the differing arm. Ported in full.
  * CONTROL-FLOW-EFFECT / sentinel-collapse — the sibling's central attack: an
    implementation that treats a DECLINE as if it were a decision, so the
    delegation step is skipped or the negation is applied one level too early.
    On this carrier the sentinel is a real third constructor rather than a
    coerced truthy object, which makes the collapse a plain value error and hence
    directly refutable at a literal input. Ported in full, across all three
    obligations.
  * VALUE-DOUBLE-MASK — a rival that collapses several arms onto one constant, or
    drops one of the two inputs entirely. Ported (``weak-verdict-constant``,
    ``weak-dispatch-decided-always-equal``, ``weak-dispatch-reflected-only``,
    ``weak-negation-decided-always-equal``).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as on the sibling. The oracle is a
    concrete ``def`` over the method's own argument, fully unfolded, so echoing it
    IS the correct answer and there is no wrong echo to build. Kept as an honest
    cheapest-impl POSITIVE control (``pos-verdict-echo``).
  * FRAME-MUTATION — VACUOUS. The sibling already records it as N/A (all inputs
    by value, no read-only reference parameter to overwrite). On this
    referentially-transparent backend it is doubly vacuous: there is no heap, no
    aliasing, and no ``mut`` binder in any of the three signatures. No substitute
    probe is fabricated.
  * DIVERGENCE / NON-TERMINATION - INAPPLICABLE to these impls and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. All three frozen impl
    regions are LOOP-FREE and non-recursive, so nothing here can be made to
    diverge by mutating a body; a diverging rival has to bring a loop of its own.
    When it does, the semantics refuse it. This bundle is ``termination "total"``
    AND its only correctness ``open`` is ``TotalCorrectness``, so a postcondition
    is claimed of ALL runs and the verifier demands a DECREASING measure on every
    loop. Re-measured on this cell, both forms rejected: a measure-LESS loop is
    refused at elaboration (exit 1, "Decreasing annotations are required in total
    correctness semantics"), and the sharper measure-CARRYING form -- an infinite
    ``while 0 < 1`` with ``done_with False`` and ``decreasing (0 : Nat)`` ahead of
    a wrong answer -- is refused on the measure's OWN goal
    (``case «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``). See the accounting block at
    the bottom of this file, which RETRACTS an earlier claim that this second form
    verifies. No reject case is shipped even so: a diverging rival's module does
    not compile, so no witness can elaborate against it and the case would land
    INCONCLUSIVE rather than rejected.

WITNESS PLACEMENT. Rivals share no refutation point unless they fail there for
the same reason. Each obligation is attacked at several DISTINCT input points,
and between them the witnesses move EVERY input binder off any fixed value:
``operand`` takes all three constructors against each of the three obligations,
and ``reflectedV`` takes all three constructors against each of the two
obligations that bind it. In particular the two declining-arm near-misses on the
dispatch obligation sit at MIRROR reflected values (one where the reflected logic
recognises the value, one where it also declines), so neither pins ``reflectedV``;
and the rivals that are right on the whole declining sub-domain but wrong on a
DECIDED verdict are refuted at a decided ``operand``, which is the only place they
diverge at all.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and the gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` and declares no
deep-model reference (``meta.json`` axioms == [], deep_model_references == []),
so there is nothing in that lane for this spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13091"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies WHOLLY inside one impl region (or one prove_correct tactic
# body) and is unique in the file — both facts asserted at import by _swap.
#
# `_IMPL_VERDICT` is a `match operand with` / `return result` block; the
# `eqResult` def in the `pure` region uses the arm-only `| .foreign => ...`
# syntax with no `match`/`return`, so this block is unique.
# ---------------------------------------------------------------------------
_IMPL_VERDICT = (
    "    let result : Verdict :=\n"
    "      match operand with\n"
    "      | .foreign         => .undecided\n"
    "      | .matchingEqual   => .isTrue\n"
    "      | .matchingUnequal => .isFalse\n"
    "    return result"
)
_IMPL_DISPATCH = (
    "    let selfV ← directEquality operand\n"
    "    let r := resolveEq selfV reflectedV\n"
    "    return r"
)
_IMPL_NEGATION = (
    "    let selfV ← directEquality operand\n"
    "    let eq := resolveEq selfV reflectedV\n"
    "    return !eq"
)
_PROOF_VERDICT = (
    "prove_correct directEquality by\n"
    "  loom_solve\n"
    "  cases operand <;> simp_all [eqResult]"
)
_PROOF_NEGATION = (
    "prove_correct inequalityCompare by\n"
    "  loom_solve <;>\n"
    "    (cases operand <;> cases reflectedV <;> "
    "simp_all [eqResult, resolveEq, neResult])"
)
for _a in (_IMPL_VERDICT, _IMPL_DISPATCH, _IMPL_NEGATION,
           _PROOF_VERDICT, _PROOF_NEGATION):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift / not unique: {_a[:48]!r}")


def _verdict(body):
    """A variant differing only in `directEquality`'s impl region."""
    return _swap(_BASE, _IMPL_VERDICT, body)


def _dispatch(body):
    """A variant differing only in `equalityCompare`'s impl region. The verdict
    is still obtained from the callee-under-spec, so only the RESOLUTION of the
    two verdicts is reshaped."""
    return _swap(_BASE, _IMPL_DISPATCH,
                 "    let selfV ← directEquality operand\n" + body)


def _negation(body):
    """A variant differing only in `inequalityCompare`'s impl region."""
    return _swap(_BASE, _IMPL_NEGATION,
                 "    let selfV ← directEquality operand\n" + body)


# ---------------------------------------------------------------------------
# Witness preamble. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the post-image through Velvet's own tester machinery:
# `<name>Tester args = false` says the extracted program's result VIOLATES that
# method's postcondition at that concrete input. Checked in a file whose
# `prove_correct` blocks have been stripped, so no tactic script can mask the
# verdict. `equalityCompare`/`inequalityCompare` call `directEquality`, so their
# testers need its program extracted too. Every argument is a concrete
# constructor literal and both carriers derive `DecidableEq`, so `decide`
# reduces fully. The directives live inside the witness, which is appended to
# BOTH the rival and the gold file, so the tester names exist on both sides by
# construction.
# ---------------------------------------------------------------------------
def _tester(*names):
    out = ""
    for n in names:
        out += (f"extract_program_for {n}\n"
                f"prove_precondition_decidable_for {n}\n"
                f"prove_postcondition_decidable_for {n}\n"
                f"derive_tester_for {n}\n\n")
    return out


_T_VERDICT = _tester("directEquality")
_T_DISPATCH = _tester("directEquality", "equalityCompare")
_T_NEGATION = _tester("directEquality", "inequalityCompare")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Every one keeps the `prove_correct` header byte-identical
    # and adds no lemma, axiom, sorry, admit or native_decide; where the reshape
    # leaves `loom_solve` a different goal SHAPE the tactic body is retuned (it
    # is elided from the spec view) with the SAME tactics, never weakened.
    # =====================================================================
    {
        "id": "pos-verdict-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: permute the three match arms so the declining arm is LAST
        # instead of first. A `match` over disjoint constructors is
        # order-independent, so every operand still maps to the same verdict.
        "module": _verdict(
            "    let result : Verdict :=\n"
            "      match operand with\n"
            "      | .matchingUnequal => .isFalse\n"
            "      | .matchingEqual   => .isTrue\n"
            "      | .foreign         => .undecided\n"
            "    return result"),
        "rationale": "permuting the arms over disjoint constructors leaves the "
                     "verdict of every operand unchanged, so D1 (out = eqResult "
                     "operand) and D2/D3/D4 all still hold. A correct reshape "
                     "must verify, else SPEC-TOO-STRONG on arm order — and arm "
                     "order is exactly what the declining-arm rivals below "
                     "change, so this control separates 'reshaped' from 'wrong'.",
    },
    {
        "id": "pos-verdict-echo",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: apply the pure-region verdict function directly.
        # This is NOT an ungrounded-oracle echo — `eqResult` is a concrete,
        # total, fully unfolded `def` of the method's own argument, so it IS the
        # correct computation. The proof body is retuned (`all_goals` over the
        # same `cases operand <;> simp_all [eqResult]` script) because with the
        # impl already in oracle form `loom_solve` leaves the two implication
        # goals unclosed rather than one master goal; the tactics are unchanged
        # and the `prove_correct directEquality` header is byte-identical.
        "module": _swap(
            _swap(_BASE, _IMPL_VERDICT, "    return eqResult operand"),
            _PROOF_VERDICT,
            "prove_correct directEquality by\n"
            "  loom_solve\n"
            "  all_goals (cases operand <;> simp_all [eqResult])"),
        "rationale": "the cheapest honest implementation: apply the total, fully "
                     "unfolded pure verdict function to the method's own "
                     "argument. D1 holds by definition and D2/D3/D4 follow by "
                     "case analysis; it must verify. Because the oracle is "
                     "GROUNDED in the input (not an opaque answer key) this is a "
                     "correct impl, not a wrong echo — which is why the "
                     "ungrounded-echo attack class is N/A on this surface.",
    },
    {
        "id": "pos-dispatch-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the resolution as a nested match instead of applying
        # the pure-region resolver. Same value on all nine input points; the
        # frozen proof script closes it unchanged.
        "module": _dispatch(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .isTrue    => true\n"
            "      | .isFalse   => false\n"
            "      | .undecided =>\n"
            "          match reflectedV with\n"
            "          | .isTrue    => true\n"
            "          | .isFalse   => false\n"
            "          | .undecided => false\n"
            "    return r"),
        "rationale": "spelling the resolution out as a nested match instead of "
                     "applying the pure resolver yields the same Bool at all "
                     "nine (operand, reflectedV) points, so E1 and E2/E3/E4/E5 "
                     "hold. A correct reshape of the resolution must verify — "
                     "important because every dispatch rival below is also a "
                     "reshape of exactly this block, so without this control a "
                     "rejection there could not be attributed to the spec.",
    },
    {
        "id": "pos-negation-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: obtain the verdict from the pure function directly rather than
        # through the callee-under-spec, and bind the resolved decision to a
        # named local before negating. Same resolved-then-negated value.
        "module": _negation(
            "    let selfV := eqResult operand\n"
            "    let decided := resolveEq selfV reflectedV\n"
            "    let r := !decided\n"
            "    return r"),
        "rationale": "computing the verdict from the pure function instead of "
                     "through the callee, and binding the resolved decision to a "
                     "local before negating it, preserves the order 'resolve "
                     "first, negate second'. So N1 (out = neResult (eqResult "
                     "operand) reflectedV) and N2/N3/N4 hold and it must verify. "
                     "This control matters most here: the negation rivals differ "
                     "from it only in WHERE the negation is applied, not in "
                     "local-variable shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method in this bundle has a `require` clause, so the
    # sibling's probe ("the precondition admits a normal F2P-shaped input") is
    # vacuous: nothing could exclude any input. It is re-aimed at the residual
    # admissibility risk on a total domain — that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting point, since a spec no impl
    # can meet reads exactly like a spec every impl meets. The case discharges an
    # in-region `assert` pinning the three-way non-degeneracy the sibling's
    # `Assert(Implies(...))` pinned: a declining value facing an operand that
    # recognises it compares EQUAL, is NOT unequal, and yet two mutual declines
    # ARE unequal. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the tactic body gains a `decide` alternative
    # for the extra goal (allowed — elided from the spec view; header identical).
    # The assert is live, not decoration: a false claim leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-delegation-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_NEGATION,
                "    assert (with_name_prefix `admiss\n"
                "      (resolveEq (eqResult .foreign) .isTrue = true\n"
                "        ∧ neResult (eqResult .foreign) .isTrue = false\n"
                "        ∧ neResult (eqResult .foreign) .undecided = true))\n"
                + _IMPL_NEGATION),
            _PROOF_NEGATION,
            "prove_correct inequalityCompare by\n"
            "  loom_solve <;>\n"
            "    (all_goals first\n"
            "      | decide\n"
            "      | (cases operand <;> cases reflectedV <;> "
            "simp_all [eqResult, resolveEq, neResult]))"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "three points the failing tests turn on: an operand the "
                     "value cannot interpret, facing reflected logic that DOES "
                     "recognise it, compares equal (E2's consequent) and is not "
                     "unequal (N3's consequent); while two mutual declines ARE "
                     "unequal (N2's consequent). The in-region assert must "
                     "discharge — if it could not, the obligation would be "
                     "unsatisfiable or degenerate exactly where the behaviour is "
                     "observed — and the impl is kept verbatim so N1 discharges "
                     "too. Else PRECOND/POST-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input point (seen to elaborate against the rival and to FAIL
    # against the frozen solution) and the refinement argument for why its
    # faithful counterpart would NOT resolve the failing tests.
    #
    # The failing tests are worth naming once here, abstractly, because most of
    # the refinement arguments below turn on it: the SAME failing test function
    # that adds the new declining-operand rows also carries pre-existing rows
    # asserting that two values compare equal exactly when they are the same
    # value, and unequal exactly when they are not. So a rival that mishandles a
    # DECIDED verdict (rather than the declining one) breaks that failing test
    # too, not merely some passing test — its faithful counterpart does not
    # resolve either.
    # =====================================================================

    # ---- directEquality: the verdict itself (binder: operand) --------------
    {
        "id": "weak-verdict-decides-unequal",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour: an operand the value cannot interpret is
        # DECIDED unequal outright instead of declining. Correct on both decided
        # arms — a genuine partial-domain rival on the declining arm alone.
        "module": _verdict(
            "    let result : Verdict :=\n"
            "      match operand with\n"
            "      | .foreign         => .isFalse\n"
            "      | .matchingEqual   => .isTrue\n"
            "      | .matchingUnequal => .isFalse\n"
            "    return result"),
        "refinement": "this is the pre-image behaviour the fix removes: an "
                      "uninterpretable operand is decided unequal rather than "
                      "declined. Its faithful counterpart leaves the comparison "
                      "unable to delegate, so an operand whose own logic DOES "
                      "recognise the value never gets consulted and the relation "
                      "is asymmetric. The failing tests assert precisely that "
                      "such a pair compares equal from BOTH sides; with the "
                      "decision made locally, one side answers unequal. It does "
                      "NOT resolve.",
        "rationale": "REJECT from D2 (operand = .foreign → out = .undecided) and "
                     "from the master clause D1 (out = eqResult operand): the "
                     "declining arm is pinned to .undecided, and this rival "
                     "returns .isFalse. Refuted at the .foreign operand — D2's "
                     "exact antecedent, and the only point at which this rival "
                     "diverges [partial-domain].",
        "witness": _T_VERDICT + (
            "example : directEqualityTester Operand.foreign = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-verdict-decides-equal",
        "kind": "uniqueness",
        "expect": "reject",
        # The other wrong sentinel on the same arm: an uninterpretable operand is
        # decided EQUAL. Also correct on both decided arms.
        "module": _verdict(
            "    let result : Verdict :=\n"
            "      match operand with\n"
            "      | .foreign         => .isTrue\n"
            "      | .matchingEqual   => .isTrue\n"
            "      | .matchingUnequal => .isFalse\n"
            "    return result"),
        "refinement": "an uninterpretable operand is decided EQUAL. Its faithful "
                      "counterpart claims every operand it cannot make sense of "
                      "is equal to the value, so a comparison against an "
                      "unrelated object answers equal and its negation answers "
                      "not-unequal. The failing tests assert the opposite for "
                      "exactly such an object — that it is unequal, and not "
                      "equal, from both sides. It does NOT resolve.",
        "rationale": "REJECT from D2 and D1, and downstream from E3/E4 — an "
                     "operand that must be declined is decided equal, so the "
                     "resolution never consults the reflected input and answers "
                     "true even when the reflected logic says .isFalse. Refuted "
                     "through the dispatch obligation at (.foreign, .isFalse), "
                     "which is E3's antecedent and where the resolved decision, "
                     "not just the raw verdict, is provably wrong "
                     "[partial-domain on the declining arm].",
        "witness": _T_DISPATCH + (
            "example : equalityCompareTester Operand.foreign Verdict.isFalse "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-verdict-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-double-mask: collapse all three arms onto one constant verdict.
        "module": _verdict(
            "    let result : Verdict := .isFalse\n"
            "    return result"),
        "refinement": "answers 'decided unequal' for every operand. Its faithful "
                      "counterpart makes the comparison unconditionally negative, "
                      "so nothing is ever equal to anything — including a value "
                      "and itself. The failing tests carry rows asserting that "
                      "two values compare equal exactly when they are the same "
                      "value, and rows asserting an operand whose own logic "
                      "recognises the value compares equal; a constant negative "
                      "answer fails both. It does NOT resolve.",
        "rationale": "REJECT from D3 (operand = .matchingEqual → out = .isTrue) "
                     "and D1, and also from D2 (the declining arm is collapsed "
                     "too). Refuted at the .matchingEqual operand — a DECIDED "
                     "arm, and the second of the three distinct values of the "
                     "operand binder probed against this obligation, so the "
                     "battery does not pin operand to the declining case "
                     "[value-double-mask: every arm onto one value].",
        "witness": _T_VERDICT + (
            "example : directEqualityTester Operand.matchingEqual = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-verdict-differing-equal",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER decided arm: an interpretable but differing operand is
        # reported equal. Correct on the declining arm — the mirror-image
        # partial-domain rival to the two above.
        "module": _verdict(
            "    let result : Verdict :=\n"
            "      match operand with\n"
            "      | .foreign         => .undecided\n"
            "      | .matchingEqual   => .isTrue\n"
            "      | .matchingUnequal => .isTrue\n"
            "    return result"),
        "refinement": "an operand that IS interpretable but differs is reported "
                      "equal. Its faithful counterpart makes two distinct values "
                      "compare equal, which the failing tests' pre-existing rows "
                      "forbid: they assert two values compare equal exactly when "
                      "they are the same value and unequal exactly when they are "
                      "not. Since those rows live in the SAME failing test "
                      "function as the new declining-operand rows, the test still "
                      "fails. It does NOT resolve. (It handles the declining arm "
                      "correctly, so it is a genuine partial-domain rival on the "
                      "differing arm alone — a rival the declining-arm witnesses "
                      "above would never catch.)",
        "rationale": "REJECT from D4 (operand = .matchingUnequal → out = .isFalse) "
                     "and D1. Refuted at the .matchingUnequal operand — D4's "
                     "antecedent, and the third constructor of the operand "
                     "binder, so all three of its values are probed against this "
                     "obligation [partial-domain, mirror of the declining-arm "
                     "rivals].",
        "witness": _T_VERDICT + (
            "example : directEqualityTester Operand.matchingUnequal = false "
            ":= by\n  decide\n"),
    },

    # ---- equalityCompare: resolving two verdicts (binders: operand, reflectedV)
    {
        "id": "weak-dispatch-no-delegation",
        "kind": "uniqueness",
        "expect": "reject",
        # Sentinel-collapse at the resolution step: only an affirmative verdict
        # resolves to equal; a DECLINE is treated as a negative decision, so the
        # reflected input is never consulted. The verdict itself is still
        # correctly obtained from the callee-under-spec.
        "module": _dispatch(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .isTrue => true\n"
            "      | _       => false\n"
            "    return r"),
        "refinement": "the decline is collapsed into a negative decision at the "
                      "RESOLUTION step, so the operand's own reflected logic is "
                      "never consulted. Its faithful counterpart reproduces the "
                      "pre-image observable behaviour even though the verdict is "
                      "computed correctly: the comparison still answers negative "
                      "for an operand that recognises the value, so the relation "
                      "is asymmetric. That is exactly the row the failing tests "
                      "add. It does NOT resolve.",
        "rationale": "REJECT from E2 ((operand = .foreign ∧ reflectedV = .isTrue) "
                     "→ out = true) and the master clause E1 (out = resolveEq "
                     "(eqResult operand) reflectedV): a declined verdict must "
                     "defer to the reflected input, and this rival discards it. "
                     "Refuted at (.foreign, .isTrue) — E2's exact antecedent, the "
                     "one point where delegation is observable "
                     "[control-flow-effect: the decline is read as a decision].",
        "witness": _T_DISPATCH + (
            "example : equalityCompareTester Operand.foreign Verdict.isTrue "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-dispatch-decline-as-equal",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite collapse: a decline resolves to EQUAL, skipping delegation
        # in the affirmative direction. Right on E2/E5, wrong on E3/E4.
        "module": _dispatch(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .isTrue    => true\n"
            "      | .isFalse   => false\n"
            "      | .undecided => true\n"
            "    return r"),
        "refinement": "a decline is resolved as EQUAL instead of deferring, so "
                      "the both-decline fallback is lost. Its faithful "
                      "counterpart makes a value compare equal to any object "
                      "neither side can make sense of — the failing tests assert "
                      "exactly the reverse for such an object (not equal, and "
                      "unequal, from both sides). It does NOT resolve. (It "
                      "answers correctly whenever the reflected logic recognises "
                      "the value, so it is a partial-domain rival that the "
                      "delegation witness above would never catch — which is why "
                      "it is refuted at the MIRROR reflected value.)",
        "rationale": "REJECT from E4 ((operand = .foreign ∧ reflectedV = "
                     ".undecided) → out = false) and E1: when BOTH decline the "
                     "resolution must fall back to false, and this rival answers "
                     "true. Refuted at (.foreign, .undecided) — E4's antecedent, "
                     "and the MIRROR of the no-delegation rival's point, so "
                     "between the two the reflectedV binder is moved rather than "
                     "pinned [control-flow-effect, opposite polarity].",
        "witness": _T_DISPATCH + (
            "example : equalityCompareTester Operand.foreign Verdict.undecided "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-dispatch-decided-always-equal",
        "kind": "uniqueness",
        "expect": "reject",
        # Right on the WHOLE declining sub-domain (it delegates faithfully) but
        # collapses both decided verdicts onto equal. The rival the four
        # declining-arm witnesses above are blind to.
        "module": _dispatch(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .undecided =>\n"
            "          match reflectedV with\n"
            "          | .isTrue    => true\n"
            "          | .isFalse   => false\n"
            "          | .undecided => false\n"
            "      | _ => true\n"
            "    return r"),
        "refinement": "delegation is handled perfectly, but a DECIDED verdict is "
                      "resolved as equal whatever it decided. Its faithful "
                      "counterpart makes two distinct interpretable values "
                      "compare equal, which the pre-existing rows of the SAME "
                      "failing test function forbid (equal exactly when the same "
                      "value). It does NOT resolve. (This is the rival that is "
                      "right on the entire declining sub-domain, so every "
                      "declining-arm witness in this battery passes it — it is "
                      "refuted at a DECIDED operand instead.)",
        "rationale": "REJECT from the master clause E1 (out = resolveEq (eqResult "
                     "operand) reflectedV): an operand decided unequal must "
                     "resolve to false, and this rival returns true. Refuted at "
                     "(.matchingUnequal, .isFalse) — the only dispatch witness "
                     "at the .matchingUnequal operand, one of the two that sit "
                     "off the declining constructor for this obligation (the "
                     "other being weak-dispatch-reflected-only at "
                     ".matchingEqual), so operand is not pinned to the declining "
                     "case here. The reflected value .isFalse is shared with the "
                     "weak-verdict-decides-equal witness, which probes a "
                     "different operand/impl pair, so the two points are still "
                     "distinct [value-double-mask on the decided arms].",
        "witness": _T_DISPATCH + (
            "example : equalityCompareTester Operand.matchingUnequal "
            "Verdict.isFalse = false := by\n  decide\n"),
    },
    {
        "id": "weak-dispatch-reflected-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops one of the two inputs: the value's own verdict is computed and
        # then ignored, so the reflected input decides unconditionally. Also
        # right on the whole declining sub-domain.
        "module": _dispatch(
            "    let _ignored := selfV\n"
            "    let r := resolveEq .undecided reflectedV\n"
            "    return r"),
        "refinement": "the value's own verdict is computed and then discarded: "
                      "the operand's reflected logic decides unconditionally, "
                      "rather than only when the value declined. Its faithful "
                      "counterpart delegates ALWAYS, so a value compared with "
                      "itself is answered by the other side's logic instead of "
                      "its own; when that side has nothing to say the comparison "
                      "answers unequal. The pre-existing rows of the same failing "
                      "test function require a value to compare equal to itself. "
                      "It does NOT resolve.",
        "rationale": "REJECT from E5 ((operand = .matchingEqual) → out = true) "
                     "and E1: a DECIDED verdict must short-circuit and must not "
                     "be overridden by the reflected input. Refuted at "
                     "(.matchingEqual, .undecided) — E5's antecedent paired with "
                     "the reflected value that exposes the override, the only "
                     "witness in this battery at that operand for this "
                     "obligation [value-double-mask: an input dropped entirely].",
        "witness": _T_DISPATCH + (
            "example : equalityCompareTester Operand.matchingEqual "
            "Verdict.undecided = false := by\n  decide\n"),
    },

    # ---- inequalityCompare: negating the resolved decision -----------------
    {
        "id": "weak-negation-of-raw-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image behaviour for this obligation: negate the RAW verdict
        # instead of the resolved decision, so a decline negates to 'equal'. Only
        # a definite negative decision yields unequal.
        "module": _negation(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .isTrue    => false\n"
            "      | .isFalse   => true\n"
            "      | .undecided => false\n"
            "    return r"),
        "refinement": "this is the pre-image behaviour the fix removes for the "
                      "inequality direction: the negation is applied to the raw "
                      "verdict, one level too early, so a DECLINE negates to "
                      "'equal'. Its faithful counterpart answers not-unequal for "
                      "an object neither side can interpret, where the resolved "
                      "answer is unequal. The failing tests assert that such an "
                      "object IS unequal to the value from both sides. It does "
                      "NOT resolve.",
        "rationale": "REJECT from N2 ((operand = .foreign ∧ reflectedV = "
                     ".undecided) → out = true) and the master clause N1 (out = "
                     "neResult (eqResult operand) reflectedV): the negation must "
                     "follow the resolution, so two mutual declines are unequal. "
                     "Refuted at (.foreign, .undecided) — N2's exact antecedent "
                     "[control-flow-effect: negation applied before delegation].",
        "witness": _T_NEGATION + (
            "example : inequalityCompareTester Operand.foreign Verdict.undecided "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-negation-raw-complement",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss to the above and its complement: a decline negates to
        # 'unequal' instead of 'equal'. It gets N2 RIGHT and fails only where the
        # reflected logic recognises the value.
        "module": _negation(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .isTrue => false\n"
            "      | _       => true\n"
            "    return r"),
        "refinement": "the complementary early negation: a decline is complemented "
                      "to 'unequal' regardless of the reflected input. Its "
                      "faithful counterpart answers unequal even for an operand "
                      "whose own logic recognises the value, so the inequality "
                      "relation is asymmetric — the failing tests assert such a "
                      "pair is NOT unequal from either side. It does NOT resolve. "
                      "(It answers correctly when both sides decline, so the "
                      "raw-negation witness above passes it; it is a genuine "
                      "near-miss refuted at the complementary reflected value.)",
        "rationale": "REJECT from N3 ((operand = .foreign ∧ reflectedV = .isTrue) "
                     "→ out = false) and N1: a declined verdict must defer, so "
                     "when the reflected logic affirms equality the answer is not "
                     "unequal. Refuted at (.foreign, .isTrue) — N3's antecedent, "
                     "the MIRROR of the raw-negation rival's point, so the two "
                     "near-misses move reflectedV rather than pin it.",
        "witness": _T_NEGATION + (
            "example : inequalityCompareTester Operand.foreign Verdict.isTrue "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-negation-decided-always-equal",
        "kind": "uniqueness",
        "expect": "reject",
        # Right on the whole declining sub-domain (it resolves then negates
        # correctly there) but reports 'not unequal' for every DECIDED verdict.
        "module": _negation(
            "    let r : Bool :=\n"
            "      match selfV with\n"
            "      | .undecided => !(resolveEq selfV reflectedV)\n"
            "      | _          => false\n"
            "    return r"),
        "refinement": "the declining sub-domain is handled correctly (resolve, "
                      "then negate), but any DECIDED verdict reports not-unequal. "
                      "Its faithful counterpart makes two distinct interpretable "
                      "values compare not-unequal, which the pre-existing rows of "
                      "the SAME failing test function forbid (unequal exactly "
                      "when not the same value). It does NOT resolve. (Right on "
                      "the entire declining sub-domain, so both negation "
                      "witnesses above pass it — refuted at a DECIDED operand.)",
        "rationale": "REJECT from the master clause N1 (out = neResult (eqResult "
                     "operand) reflectedV): an operand decided unequal must "
                     "answer unequal, and this rival answers false. Refuted at "
                     "(.matchingUnequal, .isFalse) — the only witness in this "
                     "battery at that operand for this obligation, and one of "
                     "the two negation witnesses that sit off the declining "
                     "constructor (the other being weak-negation-dropped at "
                     ".matchingEqual), so operand is not pinned to the declining "
                     "case here [value-double-mask on the decided arms].",
        "witness": _T_NEGATION + (
            "example : inequalityCompareTester Operand.matchingUnequal "
            "Verdict.isFalse = false := by\n  decide\n"),
    },
    {
        "id": "weak-negation-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves correctly and then forgets to negate: returns the equality
        # decision itself. A whole-domain polarity inversion.
        "module": _negation(
            "    let r := resolveEq selfV reflectedV\n"
            "    return r"),
        "refinement": "the resolution is performed faithfully — including "
                      "delegation — and then returned WITHOUT negation, so the "
                      "inequality direction reports the equality decision. Its "
                      "faithful counterpart inverts the polarity of every "
                      "inequality comparison: a value would be unequal to itself "
                      "and not-unequal to an unrelated object. Both the "
                      "pre-existing and the newly added rows of the failing tests "
                      "reject that. It does NOT resolve.",
        "rationale": "REJECT from N4 ((operand = .matchingEqual) → out = false) "
                     "and the master clause N1: the resolved decision must be "
                     "NEGATED, and this rival returns it as is. Refuted at "
                     "(.matchingEqual, .isTrue) — N4's antecedent, the third "
                     "distinct operand value and the pair of binder values no "
                     "other negation witness uses [the polarity of the negation "
                     "itself, which the declining-arm rivals leave untested].",
        "witness": _T_NEGATION + (
            "example : inequalityCompareTester Operand.matchingEqual "
            "Verdict.isTrue = false := by\n  decide\n"),
    },
]


# ===========================================================================
# nagini -> velvet accounting.
#
# The sibling battery carries 12 SPEC cases (3 soundness positives, 1
# admissibility, 8 uniqueness rivals) over two contracted functions `sym_eq` /
# `sym_ne` whose carrier is a pair of primitive booleans plus an integer reply
# code. THIS bundle models the same protocol over THREE methods and two
# three-constructor inductives, and it exposes the resolution step
# (`equalityCompare`) as an obligation of its own, which the sibling folded into
# a `@Pure` helper. So the port is not narrower here: the surface is WIDER, and
# the added cases are attacks the sibling's carrier had no obligation to hang
# them on.
#
#   sibling case            ->  here                                    status
#   ------------------------------------------------------------------------
#   pos-eq-reorder          ->  pos-verdict-arm-reorder                 PORTED
#   pos-eq-echo             ->  pos-verdict-echo                        PORTED
#   pos-ne-reshape          ->  pos-negation-reshape                    PORTED
#                               + pos-dispatch-inlined                  ADDED
#   admiss-ne-symmetry      ->  admiss-delegation-nondegenerate      RE-AIMED
#   rej-eq-flatfalse        ->  weak-verdict-decides-unequal            PORTED
#   rej-eq-const-false      ->  weak-verdict-constant                   PORTED
#   rej-eq-drop-ni          ->  weak-verdict-decides-equal              PORTED
#   rej-ne-rawneg           ->  weak-negation-of-raw-verdict            PORTED
#   rej-ne-rawcomplement    ->  weak-negation-raw-complement            PORTED
#   rej-ne-self-only        ->  weak-dispatch-reflected-only          PORTED*
#   rej-eq-diverge          ->  (none)              SPEC-CLOSED (fake measure)
#   rej-ne-diverge          ->  (none)              SPEC-CLOSED (fake measure)
#   AXIOM_TESTS (2)         ->  (none)                            DROPPED
#                               + weak-verdict-differing-equal          ADDED
#                               + weak-dispatch-no-delegation           ADDED
#                               + weak-dispatch-decline-as-equal        ADDED
#                               + weak-dispatch-decided-always-equal    ADDED
#                               + weak-negation-decided-always-equal    ADDED
#                               + weak-negation-dropped                 ADDED
#
# PORTED* (rej-ne-self-only): the sibling's rival drops the reflected reply from
#   the INEQUALITY function. Here the reflected input is consumed inside the
#   RESOLUTION step, which this bundle exposes as its own obligation, so the
#   faithful re-expression of "the reflected dimension is dropped" lands on
#   `equalityCompare`. It is re-aimed to the complementary drop (the value's OWN
#   verdict discarded, the reflected input decides unconditionally), because on
#   this carrier the sibling's literal shape — ignore the reflected input on the
#   declining arm — is already covered by `weak-dispatch-no-delegation` and
#   `weak-dispatch-decline-as-equal` at both polarities. Both directions of the
#   double-mask are therefore attacked, at distinct points.
#
# RE-AIMED (admissibility): the sibling's probe establishes that `sym_ne`'s
#   `Requires` domain admits a normal test-shaped reflected reply. NO method in
#   this bundle has a `require` clause, so nothing could exclude any input and
#   that probe is vacuous. Re-aimed at the residual admissibility risk on a total
#   domain — post-image unsatisfiable / degenerate at the interesting point —
#   carrying over the sibling's `Assert(Implies(...))` content: the three
#   delegation facts the protocol demands for an operand the value declines.
#
# ADDED (7 rivals + 1 positive), all on obligations or clauses the sibling's
#   carrier could not host:
#   * weak-verdict-differing-equal — the sibling's rivals all attack the
#     declining arm or collapse everything; none attacks the DIFFERING decided
#     arm alone (D4). Without it a rival wrong only there would verify.
#   * weak-dispatch-{no-delegation, decline-as-equal} — the sibling folds the
#     resolution into a `@Pure` helper it never varies, so the collapse of a
#     decline into a decision AT THE RESOLUTION STEP (both polarities, E2 and E4)
#     was unattackable there. It is the load-bearing step here.
#   * weak-dispatch-decided-always-equal / weak-negation-decided-always-equal —
#     the rivals that are right on the ENTIRE declining sub-domain. Every ported
#     rival and every ported witness is aimed at the declining arm, so without
#     these two the battery would say nothing about whether a DECIDED verdict is
#     allowed to be overridden. These are the cases the coverage invariant exists
#     to force.
#   * weak-negation-dropped — attacks N4 and the polarity of the negation itself.
#   * pos-dispatch-inlined — a positive control for the resolution obligation,
#     needed because four rivals reshape exactly that block: without it a
#     rejection there could not be separated from tactic breakage.
#
# DIVERGENCE LANE (rej-eq-diverge, rej-ne-diverge): CLOSED BY THE SEMANTICS in
#   BOTH of its forms, and not shippable as a case. This block has been corrected
#   twice; the current text is what the builds show, and it RETRACTS the residual
#   hole the previous revision claimed.
#
#   The load-bearing fact, first: this bundle sets
#   `loom.semantics.termination "total"` (see the `set_option` line in
#   `Solution.lean`), not `"partial"`, and its only correctness `open` is
#   `open TotalCorrectness DemonicChoice`. There is no `open PartialCorrectness`
#   anywhere in the file. Both lines therefore select the same scope: Loom's
#   `set_option` elaborator itself runs `openScope `TotalCorrectness``
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`) and Velvet's `method` macro
#   opens it again (`Velvet/Velvet/Syntax.lean:386`), so the explicit `open` is
#   redundant rather than contradictory. Under this scope a postcondition is
#   claimed of ALL runs, not only of terminating ones.
#
#   FORM 1, the measure-LESS diverging rival: REJECTED. Re-measured on this cell,
#   splicing `while True do pure ()` above the frozen body of every impl region
#   and reducing each proof to a bare `loom_solve` gives exit 1 with
#   `error: Decreasing annotations are required in total correctness semantics`;
#   the same splice above an unambiguously wrong `return .isFalse` in
#   `directEquality` is likewise exit 1. Four loop-bearing shapes were tried
#   (diverging/correct value, diverging/wrong value, and the two non-diverging
#   `while false` analogues) and all four are rejected.
#
#   FORM 2, the measure-CARRYING rival, i.e. the one that CANNOT be dismissed as
#   merely missing the annotation: ALSO REJECTED, on the measure's own goal. An
#   infinite `while 0 < 1` carrying `done_with False` and `decreasing (0 : Nat)`,
#   followed by a WRONG answer, spliced into `inequalityCompare`'s impl region
#   (a method nothing else calls, so only its own obligation is in play) with the
#   frozen spec untouched and every proof retuned to a bare `loom_solve`, is
#   rejected at `case «decreasing_1: (0 : Nat)»` with the residual goal
#   `⊢ 0 < 0`. That is the descent obligation `measure b' < measure b` emitted by
#   `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`
#   (`Loom/MonadAlgebras/NonDetT/Basic.lean:544`), which takes
#   `measure : β → Nat`; the `PartialCorrectness` twin at :211 takes
#   `measure : β → Option ℕ` and never mentions it again, and THAT is the rule
#   this file does not use.
#
#   SO THE PREVIOUS CLAIM IS WITHDRAWN. This block used to say the `total`
#   obligation "is discharged by ANY `decreasing` expression and the
#   strict-decrease side-condition is never proven", and that the shape above
#   "VERIFIES, exit 0, clean log". Measured: it does not verify, it is rejected on
#   `⊢ 0 < 0`. The `decreasingGadget` accusation goes with it; the measure reaches
#   the verification condition. Controls, so the rejection is read off the right
#   goal: the identical loop with a REACHABLE exit (`while 0 < 0`,
#   `done_with True`) and the same wrong answer is rejected instead on its VALUE
#   goal (`⊢ operand = Operand.matchingEqual → true = false`), which is where a
#   value error is supposed to land. The `done_with` condition IS assumed at the
#   exit, which is the mechanism that would launder a wrong answer under partial
#   semantics; under the total rule the descent obligation fires first and the
#   rival never gets to that exit argument.
#
#   NOT SHIPPABLE as a reject case even so, and the reason is now the witness
#   contract rather than spec weakness. A reject case needs a witness that (1)
#   ELABORATES against the rival and (2) FAILS against gold. A diverging rival's
#   module does not compile at all, since the descent obligation fails at the
#   `method` itself, ahead of any appended tester, so step (1) is unreachable for
#   ANY witness and the gate returns `witness-unproven` -> INCONCLUSIVE ->
#   MALFORMED-TESTS, a FAILING gate rather than a rejection. Independently, a
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   loop-bearing rival defeats a witness of any shape on this carrier: the `forIn
#   Lean.Loop.mk` term does not normalise, so the tester's `Decidable` instance
#   `did not reduce to isTrue or isFalse` (tried with `decide +kernel`,
#   `simp [<tester>]` and `rfl`; all three give that message). Shipping the rival
#   as `expect="verify"` would be worse still: it would record a soundness pass
#   for an impl that does not resolve. So the disposition is SPEC-CLOSED with the
#   two goals above as its evidence: nothing is escalated, nothing is missing from
#   this battery, and no edit to `Solution.lean` or to Loom is wanted. On the lean
#   sibling of this instance the class is vacuous for a different reason
#   (`implementation_*` is a total Lean `def`).
#
# FRAME-MUTATION: VACUOUS, as the sibling itself records (both `sym_eq` inputs
#   are primitive bools passed by value; there is no read-only reference
#   parameter and hence no frame to overwrite). On this referentially-transparent
#   backend it is doubly vacuous: no heap, no aliasing, and no `mut` binder in
#   any of the three method signatures. No substitute probe fabricated.
#
# UNGROUNDED-ORACLE ECHO: N/A on both sides. `eqResult` / `resolveEq` /
#   `neResult` are concrete total `def`s over the methods' own arguments, fully
#   unfolded, and the `axioms` region is empty — there is no opaque answer key to
#   echo. Kept as an honest positive control (`pos-verdict-echo`), exactly as the
#   sibling does.
#
# COVERAGE.
#   Obligations: 3. Each is DEFENDED by >=1 expect="verify" case
#     (directEquality: pos-verdict-arm-reorder, pos-verdict-echo;
#      equalityCompare: pos-dispatch-inlined; inequalityCompare:
#      pos-negation-reshape, admiss-delegation-nondegenerate) and ATTACKED by
#     >=4 expect="reject" cases.
#   Independent post-image clauses attacked: D1 (all four verdict rivals), D2
#     (decides-unequal, decides-equal, constant), D3 (constant), D4
#     (differing-equal); E1 (all four dispatch rivals), E2 (no-delegation), E3
#     (decides-equal), E4 (decline-as-equal), E5 (reflected-only); N1 (all four
#     negation rivals), N2 (of-raw-verdict), N3 (raw-complement), N4 (dropped).
#     Every top-level clause of every method is attacked by some rival.
#   Binders moved by the reject witnesses, per obligation:
#     directEquality     — operand ∈ {foreign, matchingEqual, matchingUnequal}
#                          (all 3 constructors), 4 points.
#     equalityCompare    — operand ∈ {foreign, matchingUnequal, matchingEqual}
#                          (all 3), reflectedV ∈ {isTrue, isFalse, undecided}
#                          (all 3), 4 distinct points.
#     inequalityCompare  — operand ∈ {foreign, matchingUnequal, matchingEqual}
#                          (all 3), reflectedV ∈ {undecided, isTrue, isFalse}
#                          (all 3), 4 distinct points.
#     No binder is held at one value by the witnesses of any obligation. The two
#     declining-arm near-misses on each of the two two-input obligations sit at
#     MIRROR reflected values, and each obligation additionally carries a rival
#     refuted at a DECIDED operand, so neither input can be pinned.
#   Every witness has been built against the rival (elaborates, exit 0) and
#   against the frozen solution (fails, exit 1, with `decide` reporting the
#   proposition FALSE — i.e. gold satisfies the postcondition at that point), so
#   each is a seen discriminator. No witness binds anything, so none can be
#   witness-inconsistent: every refutation is at concrete constructor literals.
#   All 12 gold-side failures are plain EVALUATIONS ("Tactic `decide` proved that
#   the proposition <Tester> <args> = false is false"), never a stuck reduction, a
#   missing identifier, a type error or a timeout — the whole log was screened for
#   each of the gate's four `witness-undecided` shapes and none matched.
#   FORGERY-TESTED (attack B′), 24 further builds: flipping each witness's claim
#   from `= false` to `= true` and rebuilding both sides INVERTS both exit codes
#   (gold 1 -> 0, rival 0 -> 1) on all 12 cases. So each exit code tracks the
#   CLAIM rather than the file, which is what rules out a hollow pass; a forged
#   witness asserting gold is correct at these points would NOT be recorded as
#   `rejected`. Each witness point was additionally confirmed by exhaustive
#   enumeration of the finite 3x3 domain to lie INSIDE its own rival's divergence
#   set, and all 12 points are pairwise distinct.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and the gate ignores this
#   list regardless. The sibling's two entries probe an A-reference deep model of
#   the comparison-operator dispatch; this bundle declares neither an `axiom` nor
#   a deep_model_reference (meta.json axioms == [], deep_model_references == []),
#   so there is nothing in that lane for this spec-lane manifest.
AXIOM_TESTS = []
