"""properties.py — G-PBT falsification battery for pydata__xarray-4966 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region — which the consumer spec view elides — is changed, plus,
where a candidate reshapes the loop away, the ``prove_correct`` tactic body; so
``markers.same_spec`` holds and the ``prove_correct decodeUnsigned`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation. Each case is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL — by
actually DECIDING the claim false — against a subject known to satisfy the spec.
Here that subject is the explicit ``witness_reference`` below, NOT the frozen
solution; see WHY THE WITNESSES ARE REFUTED AGAINST A REFERENCE.

DEFENDED SURFACE (one contracted method, ``decodeUnsigned``):

  decodeUnsigned (kind : IntKind) (bits : Nat) (attr : Option (List Char))
                 (values : List Int) return (out : Decoded)
    ensures out = decodeModel kind bits attr values          <-- LOAD-BEARING

A routine reinterprets a numeric array's integer elements according to an
optional signedness attribute. The element ``kind`` and element width ``bits``
describe the stored representation; ``attr`` is the optional signedness
attribute (absent as ``none``); ``values`` are the stored element values. The
desired behavior: when the attribute marks a signed array as logically unsigned
the elements move into the unsigned range and the kind becomes unsigned;
SYMMETRICALLY, when it marks an unsigned array as logically signed the elements
move into the signed range and the kind becomes signed; in any other
configuration the values and the kind are returned unchanged. The lone
postcondition pins the whole result — element values AND element kind — to
``decodeModel`` of the inputs.

TWO INDEPENDENT CLAUSES. ``decodeModel`` is a pair: ``out.values`` (the chosen
elementwise reinterpretation applied to the value list) and ``out.kind`` (the
resulting element kind). The two are independently attackable, so the battery
carries a rival that mishandles the value fold AND a rival that mishandles the
kind while keeping the values correct.

GROUNDED, NOT AN ORACLE ECHO. ``decodeModel`` is a fully-unfolded ``@[grind]``
definition over the input binders (``chooseMode`` / ``castSeq`` / ``applyCast``
are all transparent), NOT an opaque answer key: every witness below is decided
by ``decide`` at concrete literals, no conditioning needed. There is no opaque
term to echo; the cheapest honest impl IS ``decodeModel`` inlined, which is the
positive control.

BINDER COVERAGE. The four binders of the spec predicate — ``kind`` / ``bits`` /
``attr`` / ``values`` — are all moved by the reject witnesses: ``kind`` over ALL
THREE constructors (``unsignedInt``, ``signedInt`` and ``other``); ``bits`` over
``8`` and ``16``; ``attr`` over ``none``, ``some "true"`` and ``some "false"``;
``values`` over single-element, two-element, negative and midpoint inputs. So no
rival mishandles a binder every witness holds fixed. (``kind = other`` and its
rival were added by the adversarial audit: the third constructor is the arm
``chooseMode`` sends to the identity, and it was previously moved by no witness,
leaving a rival that drops the element-kind guard entirely unattacked.)

WHY THE WITNESSES ARE REFUTED AGAINST A REFERENCE, NOT AGAINST GOLD. The frozen
impl is a backward ``while`` loop. Under ``loom.semantics.choice "demonic"`` that
loop's fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold, so ``decide`` against the frozen tester is STUCK for every claim, true or
false. Measured (re-measured by the adversarial audit with real builds),
every witness below against the frozen solution:

    error: Tactic `decide` failed for proposition
      decodeUnsignedTester IntKind.unsignedInt 8 (some "false".toList) [255] = false
    ... did not reduce to `isTrue` or `isFalse`.

That is a non-verdict, not a refutation. It must NOT be read as the "fails on
gold" half: because the frozen side is stuck for EVERY claim, a forged witness
asserting the rival is CORRECT at an agreement point would fail there too and
clear both halves while refuting nothing. So each reject case carries an explicit
``witness_reference`` — ``_IMPL_LOOPFREE``, a loop-free implementation of the
same frozen spec which the gate independently checks (a) shares the spec and
(b) VERIFIES. Being loop-free it DOES kernel-reduce, so refuting a witness there
is a real decision: measured, every witness reports ``decide`` *proved the proposition
is false*, i.e. the reference's tester returns ``true`` (spec satisfied) where the
rival's returns ``false`` (spec violated). An impl the verifier accepts cannot
violate its own spec, so a witness that decides false against it is a genuine
discriminator. The same source is shipped as the ``pos-control-loopfree-direct``
positive, so the battery itself records that loop-freeness is not what any rival
is being rejected for.

Each rival is additionally loop-free, so its own tester reduces and the witness
ELABORATES against it. The rival's ``prove_correct`` body (tuned to the loop's
``i``) no longer closes once the loop is gone, so the module also rejects — and
the witness, decided against the reference, is what attributes that rejection to
the SPEC rather than to the reshape. This is the tactic-proof-backend witness
discipline.

ADVERSARIAL READ of the nagini classes:
  * POSITIVE CONTROL — PORTED. The sibling reorders the three dispatch arms of a
    branch-per-transform loop. This carrier folds through a single ``chooseMode``
    with no arm to reorder, so the structurally-different-but-correct reshape is
    a loop-free direct application of the model. Must verify, else
    SPEC-TOO-STRONG.
  * ADMISSIBILITY — RE-AIMED and PORTED (``admiss-f2p-shaped-satisfiable``). The
    sibling attests that a half-permission read-only input and the four
    ``Requires`` conjuncts are jointly satisfiable. This method declares NO
    ``require``, so that exact probe has no precondition to aim at — but "no
    precondition" is NOT a reason to drop the lane, because the analogue on a
    total carrier is the obligation being unsatisfiable or degenerate at exactly
    the interesting input, which is what PRECOND-TOO-STRONG looks like here. So
    the case discharges, by evaluation at a concrete input of the failing
    scenario's shape, that the post-image there is both reachable and
    discriminating, before closing the frozen obligation verbatim.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling writes back into a
    read-only input held at a fractional heap permission. Lean and Velvet are
    referentially transparent: every parameter is an immutable value (this bundle
    declares no ``mut`` binder), there is no heap and no aliasing, so there is no
    read-only input to overwrite and no substitute probe to build. Reported as an
    omission, not fabricated.
  * PARTIAL-DOMAIN / VALUE — PORTED (boundary off-by-one, first-element
    pass-through, pass-through collapse, direction swap), each with a
    machine-checked witness at a concrete input.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a total function of the input
    binders spelled out in the pure region, with no opaque answer key to echo.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4966"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the ONE impl-region anchor: the whole gold `do`-block body between the
# ---- markers. It lies wholly inside the impl region and is unique in
# ---- Solution.lean; both facts are asserted at load by _swap. ----
_IMPL_GOLD = """    -- impl-start
    -- Decide the elementwise reinterpretation and the resulting kind from the
    -- element kind and the attribute, then map it over the elements.
    let cm := chooseMode kind attr bits
    let m := cm.1
    let k' := cm.2
    let mut result : List Int := []
    let mut i := values.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ values.length
      invariant result = castSeq m (values.drop i)
      done_with i = 0
      decreasing i
    do
      let x := values[i - 1]!
      result := applyCast m x :: result
      i := i - 1
    return { values := result, kind := k' }
    -- impl-end"""
assert _IMPL_GOLD in _BASE, "impl anchor drift: gold impl region not verbatim"
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor not unique"

# ---- the gold proof body. A loop-free rival's `prove_correct` no longer closes
# ---- with the loop-tuned script (it references the loop variable `i`), so each
# ---- loop-free rival additionally swaps the proof to a bare `loom_solve` — the
# ---- rival will still REJECT (the postcondition does not hold), but the swap
# ---- keeps the rejection a clean signal rather than a proof-syntax artifact.
# ---- The `prove_correct decodeUnsigned by` header is preserved byte-identically
# ---- (only the tactic body changes), so the obligation survives. ----
_PROOF_GOLD = """prove_correct decodeUnsigned by
  loom_solve
  rw [castSeq_drop_step (chooseMode kind attr bits).1 values i (by omega) (by omega)]
  simp_all"""
assert _PROOF_GOLD in _BASE, "proof anchor drift: gold prove_correct body not verbatim"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor not unique"
_PROOF_BARE = "prove_correct decodeUnsigned by\n  loom_solve"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `decodeUnsignedTester kind bits attr values = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. This method has no `require`, so
# ---- the tester never returns `true` vacuously on a precondition miss. ----
_TESTER = ("extract_program_for decodeUnsigned\n"
           "prove_precondition_decidable_for decodeUnsigned\n"
           "prove_postcondition_decidable_for decodeUnsigned\n"
           "derive_tester_for decodeUnsigned\n\n")


# ---- the WITNESS REFERENCE, shared by every reject case. A loop-free but
# ---- CORRECT implementation of the frozen spec: it applies the chosen mode to
# ---- the whole list directly instead of folding one element per loop step, so
# ---- its extracted tester kernel-reduces where the frozen loop's (elaborated
# ---- through `Classical.choice` under demonic choice) is stuck for every claim.
# ---- The gate checks it shares the frozen spec and VERIFIES before refuting any
# ---- witness against it; an impl the verifier accepts cannot violate its own
# ---- spec, so a witness that decides FALSE against it is a real discriminator.
# ---- Shipped verbatim as the `pos-control-loopfree-direct` positive too, so the
# ---- battery records that loop-freeness is not the reason any rival rejects.
_IMPL_LOOPFREE = _swap(
    _swap(_BASE, _IMPL_GOLD,
          "    -- impl-start\n"
          "    let cm := chooseMode kind attr bits\n"
          "    return { values := castSeq cm.1 values, kind := cm.2 }\n"
          "    -- impl-end"),
    _PROOF_GOLD, _PROOF_BARE)


SPEC_TESTS = [
    # =====================================================================
    # (1) POSITIVE CONTROL (soundness) — structurally different but CORRECT.
    # The frozen impl folds elementwise through a backward `while` loop; this
    # impl applies the model directly (no loop): decide the mode + resulting kind
    # once, map the reinterpretation over the whole list, and return the pair.
    # Observationally identical to the frozen impl on every input, but a wholly
    # different shape (no loop, no invariant). `loom_solve` closes it because the
    # returned value is definitionally `decodeModel`. If a faithful correct impl
    # could NOT verify => SPEC-TOO-STRONG. Defends both postcondition clauses.
    # =====================================================================
    {
        "id": "pos-control-loopfree-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _IMPL_LOOPFREE,
        "rationale": "Structurally different but correct: replaces the backward "
                     "fold loop with a direct elementwise application of the "
                     "chosen mode plus the resulting kind, returning the pair. "
                     "Observationally identical to the frozen impl on every input; "
                     "`loom_solve` closes it since the result is definitionally "
                     "`decodeModel`. Must verify, else SPEC-TOO-STRONG (a faithful "
                     "correct impl rejected). Defends both clauses of the lone "
                     "postcondition (values fold AND resulting kind).",
    },

    # =====================================================================
    # (1b) ADMISSIBILITY — the obligation is SATISFIABLE and NON-DEGENERATE at a
    # concrete input of the shape the failing scenario has.
    #
    # This method declares no `require`, so the classic "a legitimate input meets
    # the precondition" probe has no precondition to probe. That is NOT a reason
    # to drop the lane: on a total carrier the analogue of PRECOND-TOO-STRONG is
    # the obligation being UNSATISFIABLE at exactly the interesting input — a
    # post-image no implementation can hit is indistinguishable, from the gate's
    # side, from one every implementation hits, and either way the whole
    # uniqueness lane above would be attesting to nothing.
    #
    # Discharged BY EVALUATION, as an in-region `assert` at the fully concrete
    # input the failing scenario has (unsigned-stored elements, the attribute
    # requesting the signed interpretation, the width maximum as the single
    # element), pinning TWO things there:
    #   * the post-image really is the folded, re-kinded result — so a computation
    #     CAN meet the obligation at that point; and
    #   * it is NOT the pass-through result — so the obligation genuinely
    #     discriminates there and is not degenerate.
    # Only then is the frozen obligation closed with the frozen impl and the
    # frozen tactic script (plus a `decide` arm for the extra assert goal — the
    # tactic body is elided from the spec view, so `same_spec` and the
    # `prove_correct` header are untouched).
    #
    # LIVE, not decoration — measured, both negative controls FAIL (exit 1, with
    # `unsolved goals` on exactly the `admiss_1` case): replacing the first
    # conjunct's right-hand side with the pass-through result leaves it unsolved,
    # and so does collapsing the second conjunct's right-hand side onto the first.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `admiss\n"
                  "      (decodeModel IntKind.unsignedInt 8 (some \"false\".toList) [255]\n"
                  "          = { values := [-1], kind := IntKind.signedInt }\n"
                  "        ∧ decodeModel IntKind.unsignedInt 8 (some \"false\".toList) [255]\n"
                  "          ≠ { values := [255], kind := IntKind.unsignedInt }))\n"
                  + _IMPL_GOLD[len("    -- impl-start\n"):]),
            _PROOF_GOLD,
            "prove_correct decodeUnsigned by\n"
            "  loom_solve\n"
            "  all_goals try decide\n"
            "  rw [castSeq_drop_step (chooseMode kind attr bits).1 values i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "ADMISSIBILITY on a total carrier: the obligation must be "
                     "SATISFIABLE and non-degenerate at an input of the failing "
                     "scenario's shape, else it is PRECOND-TOO-STRONG in the only "
                     "sense this backend can express — an obligation no "
                     "computation can meet at the point that matters reads "
                     "exactly like one every computation meets, and the whole "
                     "uniqueness lane would then be attesting to nothing. "
                     "Discharged by EVALUATION as an in-region `assert` at "
                     "kind=unsignedInt, bits=8, attr=some \"false\", "
                     "values=[255]: the post-image there IS the folded, re-kinded "
                     "result (so it is reachable) and is NOT the pass-through "
                     "result (so it is non-degenerate). The impl and the tactic "
                     "script are otherwise the frozen ones, so the `ensures` "
                     "clause still discharges and nothing is weakened.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec, each
    # loop-free (so its extracted tester reduces under `decide` while the frozen
    # loop's does not), each with a machine-checked refutation witness at a
    # concrete input, and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # (2) PASS-THROUGH COLLAPSE — the actual pre-image behavior. The dispatch
    # handles only the signed-element configuration; an unsigned element kind
    # always falls through to the identity (mode `keep`, kind preserved), with no
    # symmetric case for an unsigned array carrying the attribute value "false".
    # This is the pre-patch skeleton with the loop peeled away.
    {
        "id": "prepatch-passthrough-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm : CastMode × IntKind :=\n"
                  "      match attr with\n"
                  "      | none   => (CastMode.keep, kind)\n"
                  "      | some v =>\n"
                  "        match kind with\n"
                  "        | IntKind.signedInt =>\n"
                  "            if v = \"true\".toList then (CastMode.toUnsigned bits, IntKind.unsignedInt)\n"
                  "            else (CastMode.keep, kind)\n"
                  "        | IntKind.unsignedInt => (CastMode.keep, kind)\n"
                  "        | IntKind.other => (CastMode.keep, kind)\n"
                  "    return { values := castSeq cm.1 values, kind := cm.2 }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "This IS the pre-image behavior: the dispatch has no "
                      "symmetric case for an unsigned-stored array whose "
                      "attribute value requests the signed interpretation, so such "
                      "an array is returned unchanged (still in the unsigned range, "
                      "still carrying the unsigned kind). The failing scenario pins "
                      "the signed view (the unsigned maximum must decode to -1); a "
                      "pass-through leaves the unsigned bit pattern and the wrong "
                      "kind, so it does NOT resolve. This is exactly the spec "
                      "sensing the change.",
        "rationale": "REJECT from `out = decodeModel ...`: for kind unsigned + "
                     "attribute value requesting signed, `decodeModel` chooses the "
                     "toSigned reinterpretation and the signed kind, but this impl "
                     "chooses `keep` and preserves the unsigned kind — both clauses "
                     "diverge whenever an element needs folding. Refuted at "
                     "kind=unsignedInt, bits=8, attr=some \"false\", values=[255] "
                     "(the maximum, which must fold to -1).",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.unsignedInt 8 (some "false".toList) [255] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },

    # (3) DIRECTION SWAP — produce the OPPOSITE reinterpretation direction. Where
    # the model chooses toUnsigned it chooses toSigned and vice versa (the kind is
    # left correct). Attacks the signed-to-unsigned direction (the "true"
    # attribute value) with a witness the other rivals do not probe.
    {
        "id": "direction-swap-opposite-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm := chooseMode kind attr bits\n"
                  "    let m' := match cm.1 with\n"
                  "      | CastMode.toSigned b   => CastMode.toUnsigned b\n"
                  "      | CastMode.toUnsigned b => CastMode.toSigned b\n"
                  "      | CastMode.keep         => CastMode.keep\n"
                  "    return { values := castSeq m' values, kind := cm.2 }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "A faithful counterpart that reinterpreted to the opposite "
                      "signedness dtype (unsigned where signed was wanted, and "
                      "vice versa) would leave a signed array marked logically "
                      "unsigned in its signed bit pattern: the negative element -1 "
                      "stays -1 instead of becoming the unsigned maximum. The "
                      "failing scenario that pins the unsigned view of a "
                      "signed-stored array still observes the signed value, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = decodeModel ...`: for kind signed + "
                     "attribute value requesting unsigned, `decodeModel` chooses "
                     "toUnsigned but this impl chooses toSigned, so the values "
                     "diverge whenever an element is negative. Refuted at "
                     "kind=signedInt, bits=8, attr=some \"true\", values=[-1] "
                     "(gold gives 255; the swap leaves -1) — moving kind to "
                     "signedInt and attr to \"true\", a point no other rival probes.",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.signedInt 8 (some "true".toList) [-1] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },

    # (4) BOUNDARY OFF-BY-ONE — reinterpret with a STRICT `>` midpoint test
    # instead of the model's `≥`. NARROW BY CONSTRUCTION: the mode dispatch is
    # `chooseMode` verbatim, the non-folding modes delegate to `castSeq`
    # unchanged, and only the `toSigned` arm's comparison is weakened. So this
    # rival agrees with the frozen impl on EVERY input except one whose chosen
    # mode is `toSigned` and whose element list contains the exact midpoint
    # 2^(bits-1) — which the model folds to the signed minimum and this leaves
    # unchanged. Moves `bits` to 16 so the midpoint 32768 is a fresh input no
    # other rival probes.
    #
    # AUDIT NOTE (why the dispatch is spelled out rather than mapped over the
    # whole list). An earlier form of this case mapped the strict-`>` fold
    # unconditionally over `values`, ignoring the chosen mode. That rival is
    # wrong on a MUCH wider domain than the prose claimed — measured, its tester
    # already returns `false` at kind=unsignedInt/attr=none/values=[200] and at
    # kind=other/attr=some "false"/values=[200], neither of which involves the
    # midpoint or the signed reinterpretation at all — so the midpoint witness
    # attested to a coarse "ignores the dispatch" break that cases (2)/(6)
    # already cover, and the claimed midpoint SUB-DOMAIN was never demonstrated.
    # The form below re-earns it: it is observably identical to the frozen impl
    # off the midpoint, so the midpoint witness is the ONLY thing that can
    # discriminate it.
    {
        "id": "boundary-off-by-one-midpoint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm := chooseMode kind attr bits\n"
                  "    let vs := match cm.1 with\n"
                  "      | CastMode.toSigned b =>\n"
                  "          values.map (fun x =>\n"
                  "            if x > (2 : Int) ^ (b - 1) then x - (2 : Int) ^ b else x)\n"
                  "      | m => castSeq m values\n"
                  "    return { values := vs, kind := cm.2 }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "A faithful counterpart whose signed reinterpretation used a "
                      "strict `>` midpoint test would map the exact midpoint value "
                      "to itself instead of to the signed minimum (e.g. the "
                      "midpoint stays positive instead of becoming the most "
                      "negative signed value, which the real fixed-width cast "
                      "produces). Any decoded array containing the midpoint would "
                      "then disagree with the real reinterpretation on that "
                      "sub-domain, so it would NOT resolve.",
        "rationale": "REJECT from `out = decodeModel ...`: the strict `>` differs "
                     "from the model's `≥` exactly at the midpoint 2^(bits-1), "
                     "which the model folds by subtracting 2^bits and this leaves "
                     "unchanged. Refuted at kind=unsignedInt, bits=16, "
                     "attr=some \"false\", values=[32768] (the u16 midpoint: gold "
                     "gives -32768, this leaves 32768) — moving `bits` off 8. The "
                     "midpoint is the ONLY discriminating input: the dispatch and "
                     "the non-folding modes are the frozen ones, so a witness at "
                     "any non-midpoint value does NOT hold of this rival "
                     "(measured: the tester still returns `true` at "
                     "values=[32769, 5], the neighbouring value one above the "
                     "midpoint). That is what makes this case a genuine "
                     "sub-domain probe rather than a second copy of the "
                     "dispatch-ignoring rivals.",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.unsignedInt 16 (some "false".toList) [32768] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },

    # (5) FIRST-ELEMENT PASS-THROUGH — fold every element except the leading one,
    # which is left unreinterpreted. Correct on every array whose first element
    # does not need folding; wrong exactly when it does. Moves `values` to a
    # two-element list so the divergence is isolated to the head.
    {
        "id": "first-element-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm := chooseMode kind attr bits\n"
                  "    let vs := match values with\n"
                  "      | []      => []\n"
                  "      | x :: xs => x :: castSeq cm.1 xs\n"
                  "    return { values := vs, kind := cm.2 }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "A faithful counterpart that reinterpreted every element "
                      "except the first would leave the leading element in its "
                      "stored representation. A single-element stored array (the "
                      "failing scenario's shape) has its one decisive element left "
                      "unfolded — the maximum stays the maximum instead of decoding "
                      "to -1 — so the failing scenario still observes the wrong "
                      "value and it would NOT resolve.",
        "rationale": "REJECT from `out = decodeModel ...`: the head element is "
                     "pushed unreinterpreted where the model folds it, so the "
                     "values diverge whenever element 0 needs folding. Refuted at "
                     "kind=unsignedInt, bits=8, attr=some \"false\", "
                     "values=[255, 0] (gold folds the head 255 to -1; this leaves "
                     "255) — a two-element list isolating the head divergence.",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.unsignedInt 8 (some "false".toList) [255, 0] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },

    # (6) ATTRIBUTE IGNORED — always assume the "false" (unsigned->signed)
    # interpretation, ignoring the actual attribute. Correct only when the
    # attribute really requests that interpretation; wrong for a different value
    # AND for an absent attribute. Moves `attr` to `none` — the binder value no
    # other rival probes.
    {
        "id": "attribute-ignored-always-signed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm := chooseMode kind (some \"false\".toList) bits\n"
                  "    return { values := castSeq cm.1 values, kind := cm.2 }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "A faithful counterpart that reinterpreted without consulting "
                      "the attribute value (always applying the unsigned->signed "
                      "reinterpretation) would corrupt every array that carries no "
                      "signedness attribute or a non-matching one: an unsigned "
                      "array with no attribute would be silently folded into the "
                      "signed range. The scenarios that pin the unchanged result "
                      "for an absent attribute would still observe the folded "
                      "value, so it would NOT resolve.",
        "rationale": "REJECT from `out = decodeModel ...`: with no attribute the "
                     "model chooses `keep` and preserves the kind, but this impl "
                     "forces the toSigned reinterpretation and the signed kind, so "
                     "both clauses diverge whenever an element needs folding. "
                     "Refuted at kind=unsignedInt, bits=8, attr=none, values=[255] "
                     "(gold keeps 255 as unsigned; this folds to -1 as signed) — "
                     "the only witness with an absent attribute.",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.unsignedInt 8 none [255] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },

    # (7) WRONG RESULTING KIND — fold the values correctly but return the ORIGINAL
    # element kind rather than the resulting one. Isolates the SECOND postcondition
    # clause (`out.kind`): a rival that gets every value right but mislabels the
    # kind. Refuted at a value where the fold is the identity, so only the kind
    # clause can be doing the discriminating.
    {
        "id": "wrong-resulting-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm := chooseMode kind attr bits\n"
                  "    return { values := castSeq cm.1 values, kind := kind }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "A faithful counterpart that reinterpreted the element values "
                      "but left the array's declared element kind unchanged would "
                      "return data whose reported kind contradicts its values. The "
                      "failing scenario asserts BOTH the decoded values and the "
                      "resulting kind; the reported kind would still be the stored "
                      "one, so it would NOT resolve.",
        "rationale": "REJECT from `out = decodeModel ...`: the `out.kind` clause "
                     "demands the RESULTING kind (unsigned becomes signed and "
                     "vice versa under a matching attribute), but this impl returns "
                     "the original kind. Refuted at kind=signedInt, bits=8, "
                     "attr=some \"true\", values=[0]: the value fold is the "
                     "identity on 0, so the values agree and ONLY the kind clause "
                     "discriminates (gold reports unsignedInt; this reports "
                     "signedInt).",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.signedInt 8 (some "true".toList) [0] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },

    # (8) NON-INTEGER ELEMENT KIND TRANSFORMED — dispatch on the attribute value
    # ALONE, dropping the element-kind guard entirely, so an element kind for
    # which no reinterpretation applies is nevertheless folded (and re-kinded) as
    # if it were an integer one. Added by the audit: `IntKind` has three
    # constructors and every other rival's witness holds `kind` at `signedInt` or
    # `unsignedInt`, so the third constructor — the arm the frozen `chooseMode`
    # sends to the identity — was moved by no witness in the battery. A rival that
    # mishandles exactly that arm was therefore unattacked, which is precisely the
    # binder value a SPEC-TOO-WEAK hole would hide behind.
    #
    # Note this is NOT a reshape of case (6): case (6) hard-codes one attribute
    # value and so is wrong at `attr = none` and at a non-matching value, while
    # this rival reads the attribute faithfully (`none` and non-matching values
    # still go to the identity) and is wrong ONLY on the element-kind guard. The
    # witness below holds `attr` at a matching value and moves `kind` off the two
    # integer constructors, so it discriminates on that guard alone.
    {
        "id": "other-kind-transformed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD,
                  "    -- impl-start\n"
                  "    let cm : CastMode × IntKind :=\n"
                  "      match attr with\n"
                  "      | none   => (CastMode.keep, kind)\n"
                  "      | some v =>\n"
                  "        if v = \"true\".toList then (CastMode.toUnsigned bits, IntKind.unsignedInt)\n"
                  "        else if v = \"false\".toList then (CastMode.toSigned bits, IntKind.signedInt)\n"
                  "        else (CastMode.keep, kind)\n"
                  "    return { values := castSeq cm.1 values, kind := cm.2 }\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_BARE),
        "refinement": "A faithful counterpart that decided the reinterpretation "
                      "from the signedness attribute alone, without checking that "
                      "the stored elements are actually of an integer kind, would "
                      "reinterpret arrays for which no such reinterpretation is "
                      "defined — folding their element values and relabelling "
                      "their element kind on the strength of the attribute only. "
                      "The scenarios that pin the unchanged result for a "
                      "non-integer element kind would still observe the folded "
                      "value and the relabelled kind, so it would NOT resolve.",
        "rationale": "REJECT from `out = decodeModel ...`: `chooseMode` reaches a "
                     "reinterpretation only for the two integer element kinds and "
                     "sends every other element kind to the identity with the kind "
                     "preserved; this impl ignores that guard, so for a "
                     "non-integer element kind carrying a matching attribute value "
                     "BOTH clauses diverge (the values get folded, the kind gets "
                     "relabelled). Refuted at kind=other, bits=8, "
                     "attr=some \"true\", values=[-1] (gold keeps -1 and the "
                     "original kind; this yields 255 and unsignedInt) — the only "
                     "witness that moves `kind` off the two integer constructors.",
        "witness": _TESTER +
                   'example : decodeUnsignedTester IntKind.other 8 (some "true".toList) [-1] = false := by\n'
                   "  decide\n",
        "witness_reference": _IMPL_LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals incl. one frame-mutation). This
# bundle models only the purely functional core — a single method with one
# (two-clause) postcondition and NO precondition — so the port narrows and
# refocuses accordingly.
#
#   sibling case                              -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder                -> pos-control-loopfree-direct   RE-EXPRESSED
#   admissibility-readonly-data               -> admiss-f2p-shaped-satisfiable RE-AIMED
#   frame-mutation-write-data                 -> (none)                        OMITTED (vacuous)
#   prepatch-passthrough-collapse             -> prepatch-passthrough-collapse PORTED
#   direction-swap-unsigned-in-signed-branch  -> direction-swap-opposite-cast  PORTED
#   partial-domain-boundary-off-by-one        -> boundary-off-by-one-midpoint  PORTED
#   partial-domain-first-element              -> first-element-passthrough      PORTED
#
# RE-EXPRESSED (pos-control): the sibling reorders the three dispatch arms of a
#   branch-per-transform loop. This carrier has no such arms — it folds through a
#   single `chooseMode` — so the structurally-different-but-correct reshape is a
#   loop-free direct application of the model. `loom_solve` closes it.
# RE-AIMED (admissibility): the method declares NO `require`, so the sibling's
#   "the Requires conjuncts are jointly satisfiable" probe has no precondition to
#   aim at. That is a reason to RE-AIM the lane, not to drop it: on a total
#   carrier PRECOND-TOO-STRONG shows up as the obligation being unsatisfiable or
#   degenerate at exactly the input that matters, and a positive that discharges
#   the obligation AT that concrete input — by evaluation, as an in-region
#   `assert`, before closing the frozen obligation verbatim — tests that
#   directly. Landed by the adversarial audit; the earlier accounting recorded
#   this lane as "N/A, nothing to attest", which was the wrong disposition.
# OMITTED (frame-mutation): VACUOUS on this backend. The sibling's rival writes
#   back into a read-only input held at a fractional heap permission. This
#   backend is referentially transparent, has no heap or aliasing, and this
#   bundle declares no `mut` binder — there is no read-only input to overwrite
#   and no discriminating witness could exist. Not fabricated. DEMONSTRATED, not
#   asserted: an impl that rebinds a local `mut` copy of the value parameter
#   (clearing it, then appending to it) and still returns the frozen answer
#   VERIFIES (measured, exit 0), because the parameter itself is an immutable
#   value and no mutation of a local copy is observable through the contract.
#   There is therefore no claim about the caller's array for a witness to refute.
#
# ADDED (3, no direct sibling counterpart) — CLAUSE/BINDER coverage.
#   other-kind-transformed — added by the adversarial audit. `IntKind` has three
#     constructors and every pre-audit witness held `kind` at one of the two
#     integer ones, so a rival that drops the element-kind guard and dispatches on
#     the attribute value alone was unattacked. Refuted at the third constructor
#     with a matching attribute value, so it discriminates on that guard alone.
#   attribute-ignored-always-signed — the sibling's carrier returned only the
#     value list; the attribute-dispatch was pinned by separate branch
#     predicates. Here the attribute is an input binder of the single spec
#     predicate, so a rival that ignores it (always transforms) attacks the
#     `attr` binder directly, refuted at the `attr = none` value no other witness
#     probes.
#   wrong-resulting-kind — this carrier's postcondition has a SECOND clause the
#     sibling's did not model: the resulting element kind. A rival that folds the
#     values correctly but returns the stored kind isolates that clause, refuted
#     at a value where the fold is the identity so ONLY the kind clause
#     discriminates.
#
# Every reject witness is decided by `decide` at concrete literals (the carrier
# is fully transparent — no opaque callee, so no conditioning is needed) and each
# has been checked to ELABORATE against its rival and to be DECIDED FALSE against
# the `witness_reference` (against the FROZEN solution every witness is stuck, not
# refuted — see WHY THE WITNESSES ARE REFUTED AGAINST A REFERENCE, which is why
# the reference exists). Together the seven reject witnesses probe seven distinct
# input points and vary all four binders (kind over all three constructors —
# unsigned/signed/other; bits over 8/16; attr over none/"true"/"false"; values
# over single/two-element/negative/midpoint), and the two independent
# postcondition clauses (values fold, resulting kind) are each attacked.
#
# The reference/forgery discipline was re-derived independently by the adversarial
# audit, with real builds on both sides of every witness: each witness elaborates
# against its rival (exit 0) and is decided FALSE against the reference (exit 1,
# `decide` proved the proposition ... is false), while the FLIPPED claim — the
# same tester equated to `true`, i.e. asserting the rival is CORRECT there —
# inverts both exit codes exactly (0 on the reference, 1 on the rival). So the
# reference's exit code tracks the claim rather than the impl's shape, which is
# what makes these refutations rather than tactic mismatches.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (the `axioms` region records only an A-reference deep model),
# and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
