"""properties.py — G-PBT falsification battery for sympy__sympy-21612 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct bracketDenomFactors``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against a second impl known to satisfy the spec —
here the ``witness_reference``, not gold, for the reason set out below).

DEFENDED SURFACE (one contracted method):

  bracketDenomFactors (slots : List DenomFactor) return (out : List (List Char))
    ensures out = renderDenomFactors slots

``renderDenomFactors slots`` is ``applyWraps (slotTexts slots) (bracketTargets
slots slots)``: start from the slots' own rendered texts, then satisfy the
bracket requests in order. ``bracketTargets`` walks the slots and, for each one
that raises a request (``needsBrackets``), records the POSITION its inner
expression is found at — ``firstSlotWithKey f.innerKey slots``, the FIRST slot
whose ``innerKey`` matches. ``applyWraps`` then satisfies those requests one
after another against the text produced so far, so a request is applied at the
position it NAMED rather than at the position it was raised from.

That indirection is the whole content of the list-level surface, and it is not a
detail: because requests are located by the inner expression they name, two slots
holding EQUAL inner expressions raise two requests that both resolve to the
earliest such slot. The earliest slot is then wrapped TWICE and the later slot is
left bare — a nested pair on one slot, none on its twin — rather than each slot
receiving one pair. ``needsBrackets f`` is ``f.isReciprocal && (f.components !=
1) && shapeIsCompound f.shape``, where a shape is COMPOUND for a product or a
power inner and NOT compound for a simple/atomic inner, and a NON-reciprocal slot
never raises a request at all. The content the issue turns on lives in the power
sub-case — a reciprocal whose inner expression is itself a power (with more than
one top-level component) must raise a bracket request, not be left bare.

FIVE OBSERVATION BINDERS of the decision (the fields of each ``DenomFactor`` the
clause reads): ``shape`` (compound product / compound power / non-compound
simple), ``components`` (the top-level component count, whose boundary is 1),
``isReciprocal`` (only reciprocal slots raise requests), ``innerKey`` (which slot
a request resolves to, and hence whether equal-inner slots share a target), and
``rendered`` (the inner text that is wrapped or emitted bare). Plus the list-level
shape (length and order of ``slots``). The reject witnesses must move each of
these, since a rival that mishandled only one sub-case — only the power shape,
only the simple shape, only the single-component boundary, only the reciprocal
guard, only the request-resolution rule, or only the list shape — would slip past
a battery that pinned it.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``bracketDenomFactorsTester slots = false`` says the
extracted program's result violates the postcondition at that concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. ``decide`` reduces the
extracted program by kernel computation; a program shaped as a ``while`` loop does
NOT reduce to ``isTrue``/``isFalse`` (the loop's fixpoint is opaque to the
kernel). So each reject rival is expressed as a LOOP-FREE impl that computes its
(wrong) text list directly from the pure surface (``applyWraps`` /
``bracketTargets`` / ``firstSlotWithKey`` / ``needsBrackets`` / ``wrapText``, or a
``List.map`` over it), still a wrong implementation sharing the frozen spec but
one whose extracted tester ``decide``s.

THE FROZEN IMPL CANNOT SERVE AS THE SECOND SUBJECT (``witness-undecided``), SO THE
REJECT LANE IS REFUTED AGAINST A ``witness_reference``. The discrimination check
asks each witness to FAIL against a second impl that satisfies this spec, and that
failure is only evidence if the second impl DECIDED something. The frozen impl
keeps a ``while`` loop under ``loom.semantics.choice "demonic"``, whose fixpoint
elaborates through ``Classical.choice``; the kernel cannot unfold it, so ``decide``
against the frozen tester is stuck for EVERY claim regardless of truth. Measured
directly on this bundle — a real witness fails against gold with

    Tactic `decide` failed ... its `Decidable` instance ... did not reduce to
    `isTrue` or `isFalse`  (reduction got stuck at the `Decidable` instance)

which is the same error a TRUE claim about the frozen tester produces. A gold-side
exit code that carries no information would let a FORGED witness — one asserting
the rival is CORRECT — clear both halves, so gold is not usable here and this
battery does not rely on it.

Instead every reject case names ``witness_reference = _LOOPFREE``: a full variant
that implements the frozen spec CORRECTLY (it returns ``applyWraps (slotTexts
slots) (bracketTargets slots slots)``, which is ``renderDenomFactors`` unfolded,
so the ``ensures`` closes by ``rfl``) and is loop-free, so its extracted tester
REDUCES. Machine-checked, all nine: against ``_LOOPFREE`` each witness fails by
genuine refutation — ``Tactic `decide` proved that the proposition ... is false``
— with no stuck reduction anywhere, while against its rival each elaborates. That
is a real discriminator: an impl the verifier ACCEPTS cannot violate its own spec,
so a witness that holds of the rival and is refuted at the reference has
attributed the divergence to the spec. The reference is also shipped as its own
``expect="verify"`` case (``pos-control-loopfree-direct``), so the battery itself
records that loop-freeness is NOT what any rival is being rejected for — it is a
property gold and reference differ on while both satisfy the spec.

DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and a
diverging rival is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (1 loop here, measure ``targets.length - k``). A rival that loops
without a measure is refused outright (``Decreasing annotations are required in
total correctness semantics``), and a rival that supplies a CONSTANT measure to
dodge that is refused on the measure's own goal (``case «decreasing_1: spin»
... ⊢ spin < spin``). Divergence therefore does not discharge the ``ensures``
clauses vacuously. It is still not shipped as a G-PBT reject case, and the
reason is the witness contract rather than a spec weakness. A reject case must
carry a witness that ELABORATES against the rival, and the rival's module does
not compile at all: the descent obligation fails at the ``method`` itself,
ahead of any appended tester. Measured through the gate's own
``_check_witness``, even ``example : True := trivial`` comes back
``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and would
fail the whole battery rather than pass a case. That is the right behavior: a
diverging impl has no output at any input, so there is no value for a witness to
disagree with, and its rejection is a judgement of the termination obligation
rather than a postcondition violation at a point. Recorded as REJECTED-BY-SPEC
and not expressible as a witnessed case, which is neither a spec hole nor a
battery gap.

The carrier is otherwise fully transparent here (no opaque callee; the
``axioms`` region declares only the ``DenomFactor`` record and its shape tag, and
every observable is computed from the inputs), so witnesses use concrete literals
and never condition on a hypothesis. This is a witnessing convenience, not a
weakening: the frozen spec is untouched and each rival's divergence from
``renderDenomFactors`` is real at the witnessed input.

ADVERSARIAL READ of the weakness classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's two mandatory
    frame-mutation rivals write to a read-only input field / list spine carrying a
    fractional heap permission and are rejected for INSUFFICIENT PERMISSION before
    any value reasoning. This backend is referentially transparent: ``slots`` is
    an immutable ``List DenomFactor`` value, this bundle declares no ``mut`` binder
    on an input, and there is no heap and no aliasing. There is no read-only input
    to overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated (per the porting map, dropped rather than replaced).
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries most of the reject lane. The
    single clause pins the produced text on EVERY slot, so a rival that drops the
    power disjunct (leaves a power-inner reciprocal bare), or over-widens the
    compound test (brackets a simple inner), or shifts the component boundary
    (brackets a single-component compound), or drops the reciprocal guard
    (brackets a slot that never raised a request), or never brackets at all,
    diverges from ``renderDenomFactors`` at a concrete slot.
  * REQUEST-RESOLUTION — APPLIES, and is the class this surface adds. The clause
    routes each request through ``firstSlotWithKey``, so a rival that satisfies a
    request at the position it was RAISED from (rather than the position it
    NAMES), or that collapses two requests naming the same position into one,
    diverges exactly on equal-inner slots — where the frozen spec double-wraps the
    earliest slot and leaves the later one bare.
  * LENGTH / ORDER — APPLIES. A rival that emits one fewer element (drops the
    head) violates the element-wise/count pinning of the clause.
  * UNGROUNDED-ORACLE ECHO — N/A. ``renderDenomFactors`` is a fully unfolded
    ``def`` over the method's own argument (there is no opaque answer key to echo);
    the only way to satisfy the postcondition is to build the rendering correctly,
    which the positive control does honestly.

WITNESS PLACEMENT. The nine reject witnesses sit at SIX DISTINCT input points and
between them move every modeled binder: ``shape`` across power (product-only and
component-mask rivals), simple (over-wide rival) and product (never-bracket,
drop-head and the three resolution rivals); ``components`` across the boundary (1
for the mask rival, 2 for the others); ``isReciprocal`` across both values (the
reciprocal-guard rival); ``innerKey`` across shared and distinct keys (the
equal-inner point the three resolution rivals are refuted at); ``rendered``
across distinct inner texts; and the list shape across length 1 and length 2
(order probed by the drop-head rival). pts=6.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21612"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The whole loop-based impl body (text strictly between -- impl-start and
# -- impl-end). Replaced wholesale by the rivals, which abandon the loop
# entirely so their extracted tester `decide`s.
_IMPL = (
    "    let texts : List (List Char) := slotTexts slots\n"
    "    let targets : List Nat := bracketTargets slots slots\n"
    "    let mut result : List (List Char) := texts\n"
    "    let mut k : Nat := 0\n"
    "    while k < targets.length\n"
    "      invariant k ≤ targets.length\n"
    "      invariant result = applyWraps texts (targets.take k)\n"
    "      done_with k = targets.length\n"
    "      decreasing targets.length - k\n"
    "    do\n"
    "      result := wrapAt result targets[k]!\n"
    "      k := k + 1\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "impl-body anchor drift — re-sync _IMPL"

# The single loop-body line that wraps at the current request's position. The
# positive control names that position in a local `let` before wrapping — a
# data-flow reshape that keeps `result` definitionally identical, so `loom_solve`
# leaves the same single loop-body goal and the frozen tactic script closes it.
_INNER = "      result := wrapAt result targets[k]!\n"
assert _BASE.count(_INNER) == 1, "inner-line anchor drift"

# The impl-start marker line (unique); the admissibility case inserts an in-region
# `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen proof body (tactic script only; elided from the spec view). Reject
# rivals reshape the impl into a single expression with no loop invariant to peel,
# so `loom_solve` alone is retuned in — for them it FAILS, which is the point; the
# rejection is attributed to the spec (the witness), not to a proof script tuned to
# a loop that no longer exists.
_PROOF = (
    "prove_correct bracketDenomFactors by\n"
    "  loom_solve\n"
    "  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]\n"
    "    simp_all\n"
    "  · simp_all [renderDenomFactors]\n"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drift"

_PROOF_FLAT = "prove_correct bracketDenomFactors by\n  loom_solve\n"

# Admissibility proof: clears the extra in-region assert goal by `decide` while
# still discharging the method's own loop-body and ensures goals by the frozen
# steps.
_PROOF_ADMISS = (
    "prove_correct bracketDenomFactors by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | decide\n"
    "    | (rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k"
    " (by omega)]; simp_all)\n"
    "    | simp_all [renderDenomFactors]\n"
)


def _rival(expr):
    """A loop-free reject rival: swap the whole loop body for `expr` and retune
    the proof to the flat shape (which fails — the witness carries the rejection)."""
    return _swap(_swap(_BASE, _IMPL, expr), _PROOF, _PROOF_FLAT)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A CORRECT, loop-free implementation of the frozen spec:
# it returns `applyWraps (slotTexts slots) (bracketTargets slots slots)`, which is
# exactly what `renderDenomFactors` unfolds to, so `out = renderDenomFactors slots`
# holds on the whole domain and the obligation closes by `rfl`. Loop-free is the
# load-bearing property — its extracted tester REDUCES, so `decide` reaches a real
# verdict where the frozen `while` loop leaves it stuck (see the module docstring).
# Every reject case refutes its witness against THIS instead of gold.
#
# The gate does not trust it: before using it as a subject it checks that the
# reference shares the frozen spec and that it VERIFIES (an impl that merely failed
# everything would refute every witness, honest or forged). Machine-checked here
# too — it verifies, with no new lemma, no `sorry`, and the `prove_correct
# bracketDenomFactors` header intact; only the tactic body (elided from the spec
# view) is retuned to the new shape. It is ALSO shipped as its own expect="verify"
# case below, so the battery records that loop-freeness is not what any rival is
# rejected for.
# ---------------------------------------------------------------------------
_PROOF_LOOPFREE = (
    "prove_correct bracketDenomFactors by\n"
    "  loom_solve\n"
    "  rfl\n"
)

_LOOPFREE = _swap(
    _swap(_BASE, _IMPL,
          "    return applyWraps (slotTexts slots) (bracketTargets slots slots)\n"),
    _PROOF, _PROOF_LOOPFREE)


# ---- witness helper. The spec is a `method` contract, so a witness reaches the
# ---- post-image through Velvet's own tester machinery:
# ---- `bracketDenomFactorsTester slots = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped. Every slot is a
# ---- concrete `DenomFactor` literal so `decide` reduces the loop-free program.
def _tester(body, pin=None):
    """The tester directives + `body`, optionally preceded by a `pin`.

    `bracketDenomFactorsTester <literals> = false` says the extracted program's
    result violates the method's postcondition at that concrete input, and is
    closed by `decide`, which reduces the extracted program by kernel
    computation. Both subjects the gate builds this against — the rival and the
    `witness_reference` — are LOOP-FREE, so both reduce and both halves of the
    discrimination check are substantive: measured, the witness ELABORATES
    against its rival and is REFUTED against the reference (`decide` proved the
    proposition is false), with no stuck reduction on either side. The frozen
    impl is NOT one of those subjects, for the reason given in the module
    docstring: its `while` loop makes `decide` stuck for every claim, so gold
    would attest to nothing and each reject case names `_LOOPFREE` instead.

    THE PIN is a second, independent statement of the spec's own value at the
    witnessed input, over the PURE surface (`renderDenomFactors` applied to
    `DenomFactor` literals). That surface is a plain recursive `def`, so unlike
    the tester it reduces against EVERY subject including gold — the pin holds in
    the gold build, the reference build and the rival build alike. It is not what
    discriminates the rival (the tester line does that); it records, checkably and
    inside the artifact, the concrete fact each `rationale` asserts: that at this
    input the spec demands exactly this text. So a reader auditing a witness can
    confirm the claimed sub-domain without rerunning the gate, and a pin that
    ever drifted from the frozen spec's actual value would break the build.

    Every pin below is additionally the value the REAL patched repo callee
    produces at the corresponding expression — the pins for the equal-inner point
    were read off the real `StrPrinter._print_Mul`, not derived from the model.
    """
    directives = (
        "\n"
        "extract_program_for bracketDenomFactors\n"
        "prove_precondition_decidable_for bracketDenomFactors\n"
        "prove_postcondition_decidable_for bracketDenomFactors\n"
        "derive_tester_for bracketDenomFactors\n\n")
    return directives + ((pin + "\n") if pin else "") + body


# ---- DenomFactor literals used by the witnesses. Distinct `innerKey`s mean
# ---- distinct inner expressions; a SHARED `innerKey` means the two slots hold
# ---- EQUAL inner expressions, which is the point the resolution rivals are
# ---- refuted at.
_POW2 = ('({ rendered := "1/y".toList, shape := DenomShape.power, components := 2, '
         'isReciprocal := true, innerKey := 1 } : DenomFactor)')
_SIMP2 = ('({ rendered := "a+b".toList, shape := DenomShape.simple, components := 2, '
          'isReciprocal := true, innerKey := 2 } : DenomFactor)')
_POW1 = ('({ rendered := "y".toList, shape := DenomShape.power, components := 1, '
         'isReciprocal := true, innerKey := 3 } : DenomFactor)')
_PROD2 = ('({ rendered := "a*b".toList, shape := DenomShape.product, components := 2, '
          'isReciprocal := true, innerKey := 4 } : DenomFactor)')
_SIMPZ = ('({ rendered := "z".toList, shape := DenomShape.simple, components := 1, '
          'isReciprocal := true, innerKey := 5 } : DenomFactor)')
# TWO slots holding the SAME inner expression (same innerKey): the real callee's
# equal-inner point. Read off the real patched printer for Mul(x, 1/(y*z), 1/(y*z)):
# it prints 'x/((((y*z)))*(y*z))', i.e. the FIRST slot triple-parenthesised (its own
# pair plus two satisfied requests) and the SECOND left at its own pair.
_DUP = ('({ rendered := "(y*z)".toList, shape := DenomShape.product, components := 2, '
        'isReciprocal := true, innerKey := 7 } : DenomFactor)')
# A NON-reciprocal slot: it never raises a bracket request whatever its shape.
_NONREC = ('({ rendered := "y**2".toList, shape := DenomShape.power, components := 2, '
           'isReciprocal := false, innerKey := 8 } : DenomFactor)')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the spec is SPEC-TOO-STRONG. The request's position
    # is named in a local `let p := targets[k]!` before the wrap: the accumulated
    # `result` is DEFINITIONALLY identical, so `loom_solve` leaves the same single
    # loop-body goal and the frozen tactic script discharges it unchanged. No new
    # lemma; the obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "pos-control-named-target",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INNER,
            "      let p : Nat := targets[k]!\n"
            "      result := wrapAt result p\n"),
        "rationale": (
            "naming the current request's position in a local `let p := targets[k]!` "
            "before wrapping leaves the accumulated `result` definitionally "
            "identical, so `out = renderDenomFactors slots` still holds on the whole "
            "domain; the loop, invariants and frozen proof script are untouched. A "
            "correct reshape must verify, else the postcondition is SPEC-TOO-STRONG "
            "over the shape of the accumulation step."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — THE WITNESS REFERENCE, shipped as a case of
    # its own. A correct, LOOP-FREE impl: it returns the spec's own right-hand
    # side, so `out = renderDenomFactors slots` holds on the whole domain and the
    # obligation closes by `rfl`. No new lemma, no `sorry`, and the `prove_correct
    # bracketDenomFactors` header is byte-identical (only the tactic body, elided
    # from the spec view, is retuned to the new impl shape).
    #
    # It is here because the reject lane refutes its witnesses against this source
    # rather than against gold (the frozen `while` loop cannot decide anything —
    # see the module docstring). Shipping it as an `expect="verify"` case is what
    # records, inside the battery, that LOOP-FREENESS IS NOT WHAT ANY RIVAL IS
    # REJECTED FOR: gold and this reference disagree about the loop and BOTH
    # satisfy the spec, so the loop/loop-free axis is spec-neutral and every
    # rejection below is attributable to the bracketing decision instead.
    # =====================================================================
    {
        "id": "pos-control-loopfree-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": (
            "returning `applyWraps (slotTexts slots) (bracketTargets slots slots)` is "
            "the spec's own right-hand side unfolded, so `out = renderDenomFactors "
            "slots` holds on the whole domain and this MUST verify, else the "
            "postcondition is SPEC-TOO-STRONG over the shape of the traversal — it "
            "would be pinning the request-by-request loop rather than the rendered "
            "text. This source is ALSO the `witness_reference` for all nine reject "
            "cases, so recording that it verifies is what makes those refutations "
            "meaningful: the gate refuses a reference that does not verify, since an "
            "impl that failed everything would refute every witness, honest or forged."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can meet
    # reads exactly like one every impl meets. This case discharges an in-region
    # `assert`, at the F2P-shaped input (a single reciprocal whose inner expression
    # is itself a two-component power — the issue's absent-bracket denominator),
    # that the post-image is NON-DEGENERATE: the produced text is the bracketed
    # form rather than the bare inner text. The surrounding impl is kept verbatim so
    # the method's own obligation still discharges; the proof is retuned only to
    # clear the extra assert goal by `decide` (allowed — the tactic body is elided).
    # The assert is live: a false claim about that point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-f2p-shape-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_START,
                _IMPL_START +
                "    assert (with_name_prefix `admiss\n"
                "      (renderDenomFactors [" + _POW2 + "]\n"
                "        = [(\"(1/y)\").toList]))\n"),
            _PROOF, _PROOF_ADMISS),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "input: for a single reciprocal whose inner expression is itself a "
            "two-component power (the issue's denominator that printed without its "
            "brackets) it demands the produced text be the bracketed form "
            "'(1/y)' rather than the bare inner text '1/y'. The in-region assert "
            "must discharge (else the obligation is unsatisfiable / degenerate at "
            "the point the fix cares about); the impl is kept verbatim so the "
            "method's own `ensures` still discharges."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete input
    # and the refinement argument that its faithful real counterpart would NOT
    # resolve the failing test. Each is a LOOP-FREE impl so its extracted tester
    # `decide`s (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-product-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: only a PRODUCT inner raises a request; a power
        # inner is treated as non-compound and left bare. Correct on product /
        # simple inners, WRONG on a multi-component power inner.
        "module": _rival(
            "    return applyWraps (slotTexts slots)\n"
            "      ((slots.filter (fun f =>\n"
            "          f.isReciprocal && (f.components != 1) && "
            "(f.shape == DenomShape.product))).map\n"
            "        (fun f => firstSlotWithKey f.innerKey slots))\n"),
        "refinement": (
            "this reproduces the pre-fix behaviour: only a product inner expression "
            "raises the protective-bracket request, so a reciprocal whose inner "
            "expression is itself a power is left bare. Its faithful real "
            "counterpart admits only the product shape to the request list (the "
            "narrower pre-fix gate), which is exactly the code path that renders the "
            "issue's power-inner denominator without its brackets — the reported "
            "defect. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: `needsBrackets` treats "
            "BOTH product and power inners as compound, and this impl treats only "
            "product as compound, so the two disagree whenever a slot is a "
            "multi-component power. Verifying would be SPEC-TOO-WEAK on the "
            "power-inner sub-domain (the whole content of the fix). Refuted at a "
            "single power-inner slot with components=2 (rendered '1/y'), whose "
            "correct rendering is the bracketed '(1/y)'."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _POW2 + "] = false := by\n"
            "  decide\n",
            # the spec's value at this input is the BRACKETED form: a power inner
            # with 2 components raises a request. Reduces on gold too.
            "example : renderDenomFactors [" + _POW2 + "]\n"
            "    = [\"(1/y)\".toList] := by decide\n"),
        # gold cannot decide (stuck `while`-loop reduction), so the
        # refutation is checked against the VERIFYING loop-free reference.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-perslot-independent",
        "kind": "uniqueness",
        "expect": "reject",
        # THE IDEALIZED PER-SLOT MAP: wrap each slot's own text in place,
        # independently of every other slot. Agrees with the spec whenever all
        # inner expressions are DISTINCT, and diverges exactly on equal-inner
        # slots — where the spec resolves both requests to the earliest slot
        # (double-wrapping it and leaving the later one bare).
        "module": _rival(
            "    return slots.map (fun f => "
            "if needsBrackets f then wrapText f.rendered else f.rendered)\n"),
        "refinement": (
            "wrapping each slot's own text independently is the CLEAN per-slot "
            "rendering, and it is not what the renderer does: a bracket request "
            "names an inner expression and is satisfied at the first slot holding "
            "it, so two slots holding equal inner expressions both target the "
            "earliest — nesting a second pair there and leaving the later slot bare. "
            "Its faithful real counterpart would satisfy each request at its own "
            "slot, printing a quotient with two equal reciprocal denominators "
            "differently from the gold patch (one pair on each, instead of the "
            "nested pair on the first and none on the second). It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: the clause routes every "
            "request through `firstSlotWithKey`, so requests raised by equal-inner "
            "slots all resolve to the earliest one and are applied cumulatively; "
            "this impl instead wraps each slot in place. Verifying would leave the "
            "request-RESOLUTION rule entirely unpinned (the clause would only "
            "constrain the distinct-inner sub-domain), which is SPEC-TOO-WEAK on "
            "exactly the aliasing behaviour the real renderer has. Refuted at two "
            "slots sharing an innerKey (each rendered '(y*z)'): the spec demands "
            "'(((y*z)))' then '(y*z)', the rival produces '((y*z))' twice."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _DUP + ", " + _DUP + "] = false := by\n"
            "  decide\n",
            # the spec's value at the equal-inner point, and the value the REAL
            # patched printer produces for Mul(x, 1/(y*z), 1/(y*z)) — it prints
            # 'x/((((y*z)))*(y*z))'. Reduces on gold too.
            "example : renderDenomFactors [" + _DUP + ", " + _DUP + "]\n"
            "    = [\"(((y*z)))\".toList, \"(y*z)\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-target-own-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on the resolution rule: keep the cumulative `applyWraps`
        # pipeline but target each request at the position it was RAISED from
        # instead of the position it NAMES. Identical to the spec when all inner
        # expressions are distinct; diverges on equal-inner slots.
        "module": _rival(
            "    return applyWraps (slotTexts slots)\n"
            "      ((List.range slots.length).filter (fun i => needsBrackets slots[i]!))\n"),
        "refinement": (
            "this keeps the cumulative request pipeline but satisfies each request "
            "at the slot that RAISED it rather than at the first slot holding that "
            "inner expression. Its faithful real counterpart looks the wrap position "
            "up by slot index instead of by the inner expression, so equal-inner "
            "denominators each get their own pair rather than the nested pair on the "
            "first — a different printed string from the gold patch on that input "
            "class. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: `bracketTargets` records "
            "`firstSlotWithKey f.innerKey all` for each raising slot, not that "
            "slot's own index, so the two disagree whenever two slots share an "
            "innerKey. This is the tightest near-miss on the resolution rule — it "
            "agrees with the spec on the whole distinct-inner sub-domain — so "
            "verifying would mean the clause pins only WHICH slots raise requests "
            "and not WHERE they land. Refuted at two slots sharing an innerKey (each "
            "rendered '(y*z)'): the spec demands '(((y*z)))' then '(y*z)', the rival "
            "produces '((y*z))' twice."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _DUP + ", " + _DUP + "] = false := by\n"
            "  decide\n",
            "example : renderDenomFactors [" + _DUP + ", " + _DUP + "]\n"
            "    = [\"(((y*z)))\".toList, \"(y*z)\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-dedup-requests",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse requests naming the same position into one, so the earliest
        # equal-inner slot is wrapped ONCE instead of once per raising slot.
        # Identical to the spec when all inner expressions are distinct.
        "module": _rival(
            "    return applyWraps (slotTexts slots) (bracketTargets slots slots).dedup\n"),
        "refinement": (
            "de-duplicating the request list wraps the earliest equal-inner slot "
            "ONCE however many slots named it, where the renderer applies one wrap "
            "per raising slot and so nests them. Its faithful real counterpart "
            "guards the wrap against re-application, printing a single pair on the "
            "first equal-inner denominator instead of the nested pair the gold patch "
            "produces. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: `applyWraps` folds the "
            "request list without de-duplication, so two requests naming the same "
            "position wrap that text twice; this impl collapses them. Verifying "
            "would leave the MULTIPLICITY of the wraps unpinned — the count of "
            "bracket pairs on the earliest equal-inner slot — while agreeing "
            "everywhere the inner expressions are distinct. Refuted at two slots "
            "sharing an innerKey (each rendered '(y*z)'): the spec demands the "
            "doubly-wrapped '(((y*z)))' first, the rival produces '((y*z))'."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _DUP + ", " + _DUP + "] = false := by\n"
            "  decide\n",
            "example : renderDenomFactors [" + _DUP + ", " + _DUP + "]\n"
            "    = [\"(((y*z)))\".toList, \"(y*z)\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-reciprocal-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `isReciprocal` conjunct, so a NON-reciprocal denominator slot
        # with a compound multi-component inner raises a request it should not.
        # Correct on every reciprocal slot.
        "module": _rival(
            "    return applyWraps (slotTexts slots)\n"
            "      ((slots.filter (fun f => "
            "(f.components != 1) && shapeIsCompound f.shape)).map\n"
            "        (fun f => firstSlotWithKey f.innerKey slots))\n"),
        "refinement": (
            "dropping the reciprocal guard lets a denominator slot that did NOT "
            "arise as a reciprocal raise a bracket request. Its faithful real "
            "counterpart moves the gate out from under the reciprocal branch, so "
            "denominator slots the gold guard never considers come back bracketed "
            "and the printer's existing string assertions for those quotients "
            "mismatch. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: `needsBrackets` begins "
            "with `f.isReciprocal`, so a non-reciprocal slot raises no request "
            "whatever its shape and component count; this impl ignores that "
            "conjunct. Verifying would leave the reciprocal binder unpinned "
            "(partial-domain SPEC-TOO-WEAK) even though the rival is correct on "
            "every reciprocal slot. Refuted at a single NON-reciprocal slot with a "
            "two-component power inner (rendered 'y**2'), whose correct rendering is "
            "the bare 'y**2'."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _NONREC + "] = false := by\n"
            "  decide\n",
            # the spec's value at this input is the BARE text: a non-reciprocal
            # slot raises no request, so it is emitted unchanged.
            "example : renderDenomFactors [" + _NONREC + "]\n"
            "    = [\"y**2\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-overwide-simple",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-wide: raise a request for ANY multi-component reciprocal inner
        # regardless of shape, so a simple/atomic inner with more than one
        # top-level component is bracketed where the gold predicate leaves it
        # bare. Correct on product / power inners.
        "module": _rival(
            "    return applyWraps (slotTexts slots)\n"
            "      ((slots.filter (fun f => f.isReciprocal && (f.components != 1))).map\n"
            "        (fun f => firstSlotWithKey f.innerKey slots))\n"),
        "refinement": (
            "dropping the compound-shape test raises a request for any "
            "multi-component reciprocal inner, including a simple/non-power/"
            "non-product inner the gold predicate leaves bare. Its faithful real "
            "counterpart widens the shape gate to an extra base class (e.g. "
            "bracketing an additive denominator), so a denominator the gold guard "
            "renders bare comes back over-bracketed; the printer's existing string "
            "assertions for those denominators would mismatch. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: `needsBrackets` "
            "requires the inner shape be compound (product or power), and this impl "
            "ignores the shape, so the two disagree whenever a slot is a "
            "multi-component simple inner. Verifying would leave the compound-shape "
            "sub-domain unpinned (partial-domain SPEC-TOO-WEAK), the complement of "
            "the product-only rival, so this near-miss carries its own "
            "discriminating input. Refuted at a single simple-inner slot with "
            "components=2 (rendered 'a+b'), whose correct rendering is the bare "
            "'a+b'."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _SIMP2 + "] = false := by\n"
            "  decide\n",
            # the spec's value at this input is the BARE text: a simple inner is
            # not compound, so no request regardless of component count.
            "example : renderDenomFactors [" + _SIMP2 + "]\n"
            "    = [\"a+b\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-component-mask",
        "kind": "uniqueness",
        "expect": "reject",
        # Shift the component boundary: `components != 0` instead of `!= 1`. Agrees
        # on every slot with two-or-more components (the common case) but FLIPS on
        # a single-component compound inner: gold leaves it bare, this brackets it.
        "module": _rival(
            "    return applyWraps (slotTexts slots)\n"
            "      ((slots.filter (fun f =>\n"
            "          f.isReciprocal && (f.components != 0) && "
            "shapeIsCompound f.shape)).map\n"
            "        (fun f => firstSlotWithKey f.innerKey slots))\n"),
        "refinement": (
            "replacing the single-component guard `components != 1` with `!= 0` "
            "agrees on every multi-component inner but raises a request for a "
            "SINGLE-component compound inner that the gold predicate leaves bare. "
            "Its faithful real counterpart drops the single-component conjunct, so a "
            "one-component compound inner is bracketed where the frozen predicate "
            "leaves it bare — breaking the long-standing single-component invariants "
            "the renderer's existing string assertions pin. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: `needsBrackets` "
            "requires `components != 1`, and this impl requires `components != 0`, "
            "so the two disagree whenever a compound slot has exactly one "
            "top-level component. Verifying would leave the component boundary "
            "unpinned (partial-domain SPEC-TOO-WEAK). Refuted at a single "
            "power-inner slot with components=1 (rendered 'y'): gold leaves it bare "
            "'y', the rival brackets it '(y)'."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _POW1 + "] = false := by\n"
            "  decide\n",
            # the spec's value at the component BOUNDARY is the BARE text: a
            # compound inner with exactly one component raises no request.
            "example : renderDenomFactors [" + _POW1 + "]\n"
            "    = [\"y\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-never-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        # The cheapest wrong impl: satisfy no request at all, emit every slot's
        # text bare. Trivially correct on slots that raise none; WRONG on every
        # slot that does.
        "module": _rival("    return slotTexts slots\n"),
        "refinement": (
            "emitting every slot's text bare corresponds to never collecting a slot "
            "for the protective brackets, so every compound denominator renders "
            "without them — the issue's reported bug and every regression on an "
            "already-bracketed compound denominator. The printer's string assertions "
            "for those bracketed forms would mismatch. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: emitting the bare slot "
            "texts disagrees with the satisfied requests on every slot for which "
            "`needsBrackets` holds. Verifying would mean the postcondition does not "
            "pin the bracket wrap at all (SPEC-TOO-WEAK / hollow). Refuted at a "
            "single product-inner slot with components=2 (rendered 'a*b'), whose "
            "correct rendering is the bracketed '(a*b)'."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester [" + _PROD2 + "] = false := by\n"
            "  decide\n",
            # the spec's value at this input is the BRACKETED form, so a rival
            # that emits every slot bare cannot meet it here.
            "example : renderDenomFactors [" + _PROD2 + "]\n"
            "    = [\"(a*b)\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Length/order class: render every slot correctly then drop the head, so
        # the output has one fewer element and every slot after the first is
        # shifted. Correct per-element renderings; wrong count and order.
        "module": _rival(
            "    return (applyWraps (slotTexts slots) "
            "(bracketTargets slots slots)).tail\n"),
        "refinement": (
            "every per-slot rendering is correct but the first is dropped, so the "
            "produced text list is one element short. Its faithful real counterpart "
            "omits the leading denominator slot from the assembled quotient, "
            "dropping a factor from the printed denominator and breaking the "
            "factor order/count the printer's tests pin. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = renderDenomFactors slots`: the clause pins the "
            "count and order element-wise, and this impl returns the correct "
            "rendering's `.tail` — length `len - 1` and shifted — so it disagrees on "
            "any non-empty slot sequence. Verifying would leave the list-level shape "
            "(length and order) unpinned. Refuted at a two-slot sequence (a "
            "bracketed power inner then a bare simple inner): gold keeps both in "
            "order, the rival drops the first."
        ),
        "witness": _tester(
            "example : bracketDenomFactorsTester ["
            + _POW2 + ", " + _SIMPZ + "] = false := by\n"
            "  decide\n",
            # the spec's value here has LENGTH 2 in slot order, so a rival that
            # drops the head cannot meet it: the count and order are pinned.
            "example : renderDenomFactors [" + _POW2 + ", " + _SIMPZ + "]\n"
            "    = [\"(1/y)\".toList, \"z\".toList] := by decide\n"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 2 partial-domain uniqueness
# rivals, 1 part-count uniqueness rival, 1 constant-false uniqueness rival) plus 1
# AXIOM_TESTS probe. This bundle models the changed operation DEEPLY (the
# request-raising predicate `needsBrackets`, the request RESOLUTION rule
# `firstSlotWithKey`, and the cumulative `applyWraps` fold, all spelled out), so
# there is no consumed axiom and no permission surface; the value/length surface
# carries across intact and the resolution rule adds a class of its own.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape                  -> pos-control-named-target          PORTED
#   admiss-selfread                      -> admiss-f2p-shape-nondegenerate    RE-AIMED
#   frame-mut-field                      -> (none)                           VACUOUS
#   frame-mut-spine                      -> (none)                           VACUOUS
#   partial-product-only                 -> weak-product-only                 PORTED
#   partial-overwide-form                -> weak-overwide-simple              RE-EXPRESSED
#   partcount-double-mask                -> weak-component-mask               PORTED
#   const-false-cheapest                 -> weak-never-bracket                PORTED
#   ax-formguard-ref                     -> (none)                            DROPPED (G-AX lane)
#
#   plus five NET-NEW cases with no direct sibling:
#   (n/a)                                -> weak-drop-head                    ADDED
#   (n/a)                                -> pos-control-loopfree-direct       ADDED
#   (n/a)                                -> weak-perslot-independent          ADDED
#   (n/a)                                -> weak-target-own-position          ADDED
#   (n/a)                                -> weak-dedup-requests               ADDED
#   (n/a)                                -> weak-drop-reciprocal-guard        ADDED
#
#   and one class the sibling does not carry but which is NOT vacuous here:
#   (no sibling diverge-* case)          -> (none shippable)                  SPEC-CLOSED
#
# 4 ported/re-expressed, 1 re-aimed admissibility, 6 net-new, 2 vacuous, 1
# axiom-lane dropped. No case was dropped because its proof was hard.
#
# ADDED (pos-control-loopfree-direct): a correct LOOP-FREE impl, which is also the
#   `witness_reference` every reject case is refuted against. It exists because the
#   frozen `while` loop under demonic choice makes `decide` STUCK for every claim,
#   so gold cannot serve as the discrimination check's second subject
#   (`witness-undecided`); measured directly on this bundle. Shipping the reference
#   as a verify case records that loop-freeness is spec-neutral — gold and the
#   reference differ on it and both satisfy the spec — so no rival is being
#   rejected merely for abandoning the loop.
# ADDED (weak-perslot-independent, weak-target-own-position, weak-dedup-requests):
#   the three rivals of the REQUEST-RESOLUTION class, the surface `firstSlotWithKey`
#   introduces. Each is correct on the whole distinct-inner sub-domain and diverges
#   only where two slots hold EQUAL inner expressions: the first satisfies each
#   request at its own slot (the clean per-slot map), the second targets the raising
#   slot's index instead of the named position, the third collapses co-targeted
#   requests. All three are refuted at the same equal-inner point because that is
#   the point the rule is about; they are distinguished by WHICH part of it they get
#   wrong (per-slot vs cumulative, target-by-index vs target-by-key, multiplicity).
#   Without them the clause would only be pinned on distinct-inner inputs, which is
#   the sub-domain where the idealized per-slot map and the real renderer agree.
# ADDED (weak-drop-reciprocal-guard): `needsBrackets` reads `isReciprocal`, so that
#   binder needs a rival that moves it. This one is correct on every reciprocal slot
#   and wrong only on a non-reciprocal one.
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``targets.length - k``). A rival that
#   loops without a measure is refused outright (``Decreasing annotations are
#   required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``). Divergence therefore does not
#   discharge the ``ensures`` clauses vacuously. It is still not shipped as a
#   G-PBT reject case, and the reason is the witness contract rather than a spec
#   weakness. A reject case must carry a witness that ELABORATES against the
#   rival, and the rival's module does not compile at all: the descent
#   obligation fails at the ``method`` itself, ahead of any appended tester.
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   Measured through the gate's own ``_check_witness``, even ``example : True :=
#   trivial`` comes back ``witness-unproven`` on this rival, which is an
#   INCONCLUSIVE outcome and would fail the whole battery rather than pass a
#   case. That is the right behavior: a diverging impl has no output at any
#   input, so there is no value for a witness to disagree with, and its
#   rejection is a judgement of the termination obligation rather than a
#   postcondition violation at a point. Recorded as REJECTED-BY-SPEC and not
#   expressible as a witnessed case, which is neither a spec hole nor a battery
#   gap.
#
# RE-EXPRESSED (weak-overwide-simple): the sibling's over-wide rival treats any
#   non-atomic form tag (incl. an out-of-abstraction form>=3) as compound. This
#   backend's `shape` is a faithful 3-way tag (product / power / simple) with no
#   out-of-domain value, so the discriminable analogue is "raise a request for a
#   compound-shape inner AND a simple inner alike" — dropping the compound-shape
#   test so a multi-component simple (e.g. an additive) inner is over-bracketed. It
#   refutes the same clause on the simple-shape sub-domain, the complement of the
#   product-only rival.
# RE-AIMED (admissibility): the sibling establishes that the half-permission input
#   is readable and the per-slot decision matches the Pure oracle. There is no
#   precondition and no permission here, so that probe is vacuous. It is re-aimed at
#   the residual admissibility risk on a total domain — that the post-image is
#   unsatisfiable/degenerate at the interesting point — via an in-region assert
#   pinning the produced text for the issue's power-inner denominator to its
#   bracketed form '(1/y)', counting the brackets rather than dropping them.
# ADDED (weak-drop-head): the clause `out = renderDenomFactors slots` pins the
#   list-level count and order (a surface the richer `List (List Char)` carrier
#   exposes that the sibling's flag-list did not attack). Added to defend that
#   aspect so the list shape is not a binder every witness holds fixed.
# VACUOUS (frame-mut-field, frame-mut-spine): the sibling writes to a read-only
#   input field / list spine carrying a fractional heap permission and is rejected
#   for INSUFFICIENT PERMISSION before any value reasoning. This backend is
#   referentially transparent: `slots` is an immutable `List DenomFactor` value,
#   this bundle declares no `mut` binder on an input, and there is no heap or
#   aliasing. There is no read-only input to overwrite and no permission system to
#   trip. No substitute is fabricated (per the porting map, dropped rather than
#   replaced).
# DROPPED (ax-formguard-ref): the sibling's AXIOM_TESTS probe validates the deep
#   bracketing model against the real renderer's bracketing gate. The A-reference
#   fidelity of the modeled rendering against the real callee is this bundle's G-AX
#   job (meta.json deep_model_references, checked by axiom_check.py); the G-PBT gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single clause `out = renderDenomFactors slots` is
#   attacked by all nine rivals across distinct sub-domains — power-inner (drop the
#   power disjunct), simple-inner (over-wide), single-component compound (boundary
#   shift), non-reciprocal slot (guard drop), never-bracket (do-nothing), head-drop
#   (length/order), and three flavours of wrong request resolution (per-slot,
#   target-by-index, de-duplicated) — refuted at SIX DISTINCT input points (pts=6).
#   Every modeled binder is moved: `shape` across power, simple and product;
#   `components` across the boundary (1 and 2); `isReciprocal` across both values;
#   `innerKey` across shared and distinct keys; `rendered` across distinct inner
#   texts; the list shape across length 1 and length 2 (order probed by the
#   head-drop rival). The three resolution rivals deliberately SHARE the
#   equal-inner witness point, because that single point is what the resolution
#   rule is about — they are separated by which aspect of it each gets wrong, and
#   each agrees with the spec at all five other points.
#
# AXIOM_TESTS: empty. No consumed axiom to probe (deep model); this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
