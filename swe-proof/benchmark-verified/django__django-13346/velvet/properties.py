"""properties.py — G-PBT falsification battery for django__django-13346 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides — so ``markers.same_spec``
holds and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
refutation subject — here the ``witness_reference`` rather than the frozen
solution, for the reason set out under WITNESS MECHANICS below).

DEFENDED SURFACE (one contracted method over a list of listed values, a plain
per-slot token, a per-value alternate-token map, and a flag recording what that
map's tokens do with the value they were built for):

  buildMembershipClause (vals native bareTok wrapOf wrapHoldsValue)
      require  ∀ v ∈ vals, wrapOf v ≠ bareTok
      ensures  out.1 = clauseTokens native bareTok wrapOf vals
      ensures  out.2 = clauseSuppliedValues native wrapHoldsValue vals

The method builds the right-hand side of a membership comparison over a list of
listed values, as the PAIR a clause is only usable as: the operand tokens, and
the listed values that still have to be handed over alongside them.

Desired behaviour of the tokens: every listed value contributes exactly one
operand token, in order; which token a slot carries is selected by the capability
flag ``native`` — the plain token ``bareTok`` when it holds, and otherwise
``wrapOf v``, the alternate token the map assigns to THAT slot's own listed
value.

Desired behaviour of the accompanying values: they follow the BRANCH, all of them
or none of them. On the native branch every listed value is handed over. On the
non-native branch it is the alternate token FAMILY that decides, carried in as
``wrapHoldsValue``: a family whose tokens keep each slot's own listed value
inside themselves leaves no place to fill, so nothing is handed over; a family
whose tokens leave that place open hands over every listed value, unchanged and
in order. It is decided per BRANCH, never per slot and never by inspecting an
individual token's characters — ``clauseSuppliedValues native wrapHoldsValue
vals`` reads the two flags and the list, and nothing else.

The five INPUT binders are all free:
  * ``vals``    — the listed values; its LENGTH, ORDER, and (on the non-native
                  branch) each ELEMENT's identity all drive the emitted tokens,
                  because each slot's token is looked up from its own value;
  * ``native``  — the capability flag selecting which token family a slot gets;
  * ``bareTok`` — the plain token emitted per slot when ``native`` holds;
  * ``wrapOf``  — the map from a listed value to the alternate token its slot
                  carries otherwise;
  * ``wrapHoldsValue`` — whether that alternate family's tokens hold the value
                  they were built for, which is what decides whether the values
                  travel alongside the clause.
The post-image must hold for EVERY value of each, which is what makes the
partial-domain and branch rivals below genuinely refutable at concrete points.

WHY ``wrapOf`` IS A MAP AND NOT A SINGLE TOKEN — the point half the reject lane
turns on. The token a non-native slot carries is a function of that slot's own
listed value, and on some configurations it genuinely varies across slots of one
clause (two slots of the same clause can carry different tokens, and the tokens
can hold the value itself). A model that emitted one token for every slot
would assert a per-slot UNIFORMITY the real operation does not have; the
``weak-uniform-token`` rival below is exactly that shape, and the battery records
that the spec REJECTS it. Correspondingly the precondition is per-value
(``∀ v ∈ vals, wrapOf v ≠ bareTok``): each listed value's alternate token really
differs from the plain one, which is what makes each slot's obligation
discriminating without pinning the slots to one another.

WHY ``wrapHoldsValue`` IS A SEPARATE BINDER AND NOT A TEST ON THE TOKENS — the
point the other half turns on. Whether the values travel alongside is a property
of the BRANCH the clause was built on, not of the characters of the token a slot
happens to have received: an alternate family that holds each value inside its
token hands over nothing even when a token's text happens to contain the plain
mark as part of the value it holds. So the obligation reads the flag, and the
battery carries the rivals that read something else instead
(``weak-values-token-derived``, which decides from the emitted token, and
``weak-values-flag-ignored``, which reads the flag but drops ``native``).

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend, for a stronger reason
    than the sibling's (which already recorded it N/A: the sole input is passed
    by value, carrying no heap permission). Lean and Velvet are referentially
    transparent and this bundle declares no ``mut`` PARAMETER — every input is an
    immutable value, there is no heap and no aliasing — so there is no read-only
    input a rival could overwrite and no substitute probe to fabricate.
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images (``clauseTokens`` and
    ``clauseSuppliedValues``) are total, fully-unfolded functions of the method's
    own arguments (concrete ``def``s in the ``pure`` region; the ``axioms``
    region is empty), NOT an opaque answer key. ``wrapOf`` is an ordinary total
    function PARAMETER the caller supplies, not an axiomatized callee, and the
    ensures pin ``out`` pointwise at every listed value, so there is no value an
    echo could carry that satisfies them yet is behaviourally wrong — the unique
    satisfier IS the per-slot fold paired with the per-branch value list. The
    honest grounded controls are the ``pos-*`` reshapes.
  * CONTROL-FLOW-EFFECT — N/A. The method is a pure value-returning token
    builder: no raise / return-vs-fallthrough difference and no side effect
    invisible to the value abstraction (the whole returned pair IS the
    abstraction).
  * PARTIAL-DOMAIN / VALUE — the real attacks. The ensures reject any rival
    that leaves ANY slot carrying the wrong token, or that hands over the wrong
    set of values on either branch. The two partial rivals split the F2P input
    domain on the boundary the issue is about — single-value vs multi-value
    membership.
  * BINDER COVERAGE (``native``) — the sibling's carrier hardcodes the alternate
    token and has NO capability-flag binder; this backend's model adds
    ``native``. ``weak-flag-inverted`` is the binder-coverage rival that moves
    it, attacking the branch the F2P does not exercise so the spec's dependence
    on the flag is demonstrated rather than assumed.
  * BINDER COVERAGE (``wrapOf`` AS A MAP) — ``weak-uniform-token`` is the rival
    that holds the map constant across slots (every slot gets the leading
    value's token). Its witness passes a ``wrapOf`` that is NOT constant, so the
    spec's pointwise dependence on each slot's own value is demonstrated rather
    than assumed. Without it, a rival could satisfy every other reject witness
    while collapsing the per-value map to one token.
  * BINDER COVERAGE (``wrapHoldsValue``) — four rivals pin the second component
    from every side: hand over none (``weak-values-withheld``), hand over all
    (``weak-values-overhanded``), read the token instead of the flag
    (``weak-values-token-derived``), and read the flag but ignore ``native``
    (``weak-values-flag-ignored``). Their witnesses between them place the pair
    (``native``, ``wrapHoldsValue``) at (false,false), (false,true) and
    (true,true), so neither flag can be dropped from the second obligation.

WITNESS MECHANICS ON THIS BUNDLE — and why every reject case carries a
``witness_reference``. The frozen impl is a ``while`` loop, whose extracted
program is a partial-fixpoint iteration the kernel does NOT reduce: under
``loom.semantics.choice "demonic"`` the loop's fixpoint elaborates through
``Classical.choice``, so ``decide`` against the FROZEN solution is stuck for
every claim, true or false. That is fatal for the second half of the
discrimination check. A witness is required to FAIL on the frozen side, but a
failure by stuck reduction decides nothing: the identical
``did not reduce to `isTrue` or `isFalse``` error appears for a TRUE claim about
the frozen impl, so the frozen-side exit code would carry no information and a
witness asserting the rival is *correct* would clear both halves just as well.

So the frozen solution cannot serve as the refutation subject here, and every
reject case names a ``witness_reference`` instead: ``_LOOPFREE``, a loop-free
straight-line impl of the SAME frozen spec (``vals.map`` over the pure
``slotToken`` selector applied to each element, paired with the same per-branch
value list, with the ``prove_correct`` body retuned to a list induction). It is
machine-checked correct — shipped additionally as the ``pos-loopfree`` positive,
so the battery itself records that loop-freeness is not what any rival is
rejected for — and, being loop-free, it REDUCES. Each rival is likewise written
as a straight-line computable impl, so the witness
``buildMembershipClauseTester args = false`` reduces on both sides: it
ELABORATES against the rival and is REFUTED against the reference with
``Tactic `decide` proved that the proposition … is false`` — a real verdict, not
a stuck term. Both halves were checked out-of-band with
``scripts/lean_verify.sh`` at every witness point, and every reference-side log
was additionally screened for ``did not reduce to`` (zero occurrences), so no
reject rests on a stuck reduction.

AXIOM lane: EMPTY. ``meta.json`` declares no ``axiom`` and no A-reference deep
model (the plain token, the per-value token map and the flag are data carried in
as parameters, not a contract about an outside callee), so there is nothing for
the axiom lane to probe and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13346"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end`, INCLUDING the nested invariants. Every rival
# and every reshape edits ONLY this block (and, for reshapes/admissibility, the
# elided `prove_correct` tactic body), so the spec view is untouched and
# same_spec holds by construction.
_IMPL = """\
    -- impl-start
    -- The operand token for each slot, selected by the capability flag: the plain
    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
    -- listed value is mapped to. The values handed over alongside follow the
    -- branch: none at all where the alternate tokens keep their own values,
    -- every listed value otherwise.
    let mut result : List (List Char) := []
    let mut i := vals.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vals.length
      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
      done_with i = 0
      decreasing i
    do
      let v := vals[i - 1]!
      result := (if native then bareTok else wrapOf v) :: result
      i := i - 1
    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# retunes THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not by the tactic script).
_PROOF = """\
prove_correct buildMembershipClause by
  loom_solve
  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
    simp_all [slotToken]
  · simp_all [clauseSuppliedValues]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# Proof scripts for the reshaped-but-correct impls. All three are RETUNES of the
# frozen script and change no obligation: a reshape moves the impl's syntactic
# form, so the tactic proof of the SAME two ensures has to follow it.
#
# _PROOF_RETUNED — robust to a reshaped loop body: discharges the loop step
# where one is present, splits the two boolean binders (needed when the impl
# writes the branch test in a different but equivalent form, e.g.
# `!native && wrapHoldsValue`, whose `if` tree matches the post-image's only
# after a case split), and closes by unfolding the post-images.
_PROOF_RETUNED = """\
prove_correct buildMembershipClause by
  loom_solve <;>
    (try (rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)])) <;>
    (try (cases native <;> cases wrapHoldsValue)) <;>
    simp_all [slotToken, clauseSuppliedValues]"""

# _PROOF_RETUNED_ASSERT — the same, plus `clauseTokens` unfolding for the extra
# VC an in-region `assert` adds (the admissibility case).
_PROOF_RETUNED_ASSERT = _PROOF_RETUNED.replace(
    "simp_all [slotToken, clauseSuppliedValues]",
    "simp_all [slotToken, clauseTokens, clauseSuppliedValues]")

# _PROOF_LOOPSTEP — the loop step alone. Used by the reshape that returns the
# second component AS the pure post-image function: that ensures then closes
# inside `loom_solve` itself, so only one goal survives and a second bullet
# would be `No goals to be solved`. Worth recording rather than papering over:
# it is direct evidence that the second obligation is exactly the pure function
# it names, with nothing extra folded into it.
_PROOF_LOOPSTEP = """\
prove_correct buildMembershipClause by
  loom_solve
  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
    simp_all [slotToken]"""


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, proof=None):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, proof or _PROOF_RETUNED)


# ---- THE WITNESS REFERENCE. A loop-free, machine-checked-correct impl of the
# ---- frozen spec, used as the refutation subject for every reject case because
# ---- the FROZEN impl cannot serve as one: its `while` loop elaborates through
# ---- `Classical.choice` under demonic choice, so `decide` against it is stuck
# ---- for EVERY claim and its exit code discriminates nothing (the gate reports
# ---- that as `witness-undecided`). This impl computes the same per-slot fold
# ---- directly — mapping the pure selector over each element, so each slot still
# ---- gets ITS OWN value's token — and the same per-branch value list, so it
# ---- REDUCES: a witness that says "the spec is violated here" is genuinely
# ---- refuted against it (`decide` proves the tester is `true`), which is the
# ---- evidence the frozen side cannot give. The proof is retuned to a list
# ---- induction (the loop invariant is gone with the loop); `clear require_1`
# ---- drops the per-value precondition hypothesis from the goal before
# ---- inducting, so the induction hypothesis is the plain equation rather than
# ---- one guarded by a membership premise about the ORIGINAL list (the ensures
# ---- does not depend on the precondition). Shipped as the `pos-loopfree`
# ---- positive too, so the battery records that loop-freeness is not what any
# ---- rival is being rejected for.
_LOOPFREE_PROOF = """\
prove_correct buildMembershipClause by
  loom_solve
  · simp [clauseSuppliedValues]
  · clear require_1
    induction vals with
    | nil => simp [clauseTokens]
    | cons v vs ih => simp [clauseTokens, ih]"""

_LOOPFREE = _swap(
    _impl("    return (vals.map (fun v => slotToken native bareTok wrapOf v),\n"
          "            if native then vals else (if wrapHoldsValue then [] else vals))"),
    _PROOF, _LOOPFREE_PROOF)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `buildMembershipClauseTester args = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict. The fourth argument is a concrete closure for `wrapOf`, so
# ---- the tester reduces; the fifth is the branch flag the second obligation
# ---- reads.
_TESTER = ("extract_program_for buildMembershipClause\n"
           "prove_precondition_decidable_for buildMembershipClause\n"
           "prove_postcondition_decidable_for buildMembershipClause\n"
           "derive_tester_for buildMembershipClause\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. Each keeps the back-to-front loop and the gold
    # front-recursive invariant, so the reproof stays close to the frozen
    # script.
    # =====================================================================
    {
        "id": "pos-inline-token",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the intermediate `v` local and apply the pure `slotToken`
        # selector to the indexed element directly in the loop body; the second
        # component is written as the equivalent single boolean test rather than
        # the nested branch. Same pair as the frozen impl; observationally
        # identical. Proof retuned (the do-block changed shape).
        "module": _impl_reproved(
            "    let mut result : List (List Char) := []\n"
            "    let mut i := vals.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ vals.length\n"
            "      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      result := slotToken native bareTok wrapOf vals[i - 1]! :: result\n"
            "      i := i - 1\n"
            "    return (result, if !native && wrapHoldsValue then [] else vals)"),
        "rationale": "applying the pure per-slot selector to the indexed element "
                     "inline emits the same token per slot as the frozen impl, and "
                     "`!native && wrapHoldsValue` is the same branch test as the "
                     "nested `if`, so both ensures still hold; a correct reshape "
                     "must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-token-fn-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist the per-slot selection into a LOCAL FUNCTION of the
        # value, then apply it per slot, and compute the second component through
        # the pure post-image function. Same value flow; the invariant is
        # unchanged, so only the loop step is left to prove — writing the second
        # component AS the post-image function discharges that ensures inside
        # `loom_solve`, which is why this case's retune is the loop step alone.
        # This is the reshape a real implementation is most likely to take, since
        # the selection is per-value rather than per-clause.
        "module": _impl_reproved(
            "    let pick : Int → List Char := fun v => if native then bareTok else wrapOf v\n"
            "    let mut result : List (List Char) := []\n"
            "    let mut i := vals.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ vals.length\n"
            "      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let v := vals[i - 1]!\n"
            "      result := pick v :: result\n"
            "      i := i - 1\n"
            "    return (result, clauseSuppliedValues native wrapHoldsValue vals)",
            _PROOF_LOOPSTEP),
        "rationale": "hoisting the per-slot selection into a local function of the "
                     "listed value computes the same token for each slot, and the "
                     "second component is the same per-branch value list; must "
                     "verify.",
    },

    {
        "id": "pos-loopfree",
        "kind": "soundness",
        "expect": "verify",
        # The witness reference, shipped as a case in its own right. Reshape:
        # drop the loop entirely and map the pure per-slot selector over the
        # listed values. Behaviourally identical — one token per value, in
        # order, each slot getting its own value's token, paired with the same
        # per-branch value list — and reproved by list induction (the loop
        # invariant is gone with the loop). Recording it here is what makes its
        # use as the reject cases' refutation subject legible: the battery
        # asserts, and the gate independently checks, that this impl VERIFIES
        # against the frozen spec, so no rival is rejected merely for being
        # loop-free.
        "module": _LOOPFREE,
        "rationale": "mapping the pure `slotToken` selector over the listed "
                     "values emits one token per value in order, each from that "
                     "value, so `out.1 = clauseTokens native bareTok wrapOf vals` "
                     "holds by list induction, and the per-branch value list is "
                     "unchanged; a correct loop-free reshape must verify, else "
                     "SPEC-TOO-STRONG. Also the `witness_reference` every reject "
                     "case is refuted against, so its verifying here is "
                     "load-bearing for the reject lane.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a precondition
    # (`∀ v ∈ vals, wrapOf v ≠ bareTok`), but no F2P-shaped input is excluded
    # by it: the F2P builds a real membership clause where the plain
    # placeholder and each listed value's alternate token genuinely differ.
    # The usual "a normal input satisfies the precondition" probe is
    # uninteresting on its own, so this case attacks the residual
    # admissibility risk: that the post-image is DEGENERATE at the interesting
    # point. It discharges an in-region assert (symbolically, over the free
    # token and the free map) that at a single-value non-native membership the
    # token obligation demands exactly that value's alternate token, at a
    # single-value native membership exactly the plain token, and at a TWO-value
    # non-native membership each slot's OWN value's token — i.e. the two token
    # branches really are distinguished AND the per-slot obligation really is
    # pointwise rather than uniform — and that the accompanying-values
    # obligation separates all three branch configurations it can be in. The
    # assert is live: replacing any conjunct with a false claim about the same
    # point leaves an unsolved goal (checked out-of-band). The rest of the impl
    # is kept verbatim and the proof is retuned to also discharge the assert VC.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, "    -- impl-start\n",
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `assert\n"
                  "      (clauseTokens false bareTok wrapOf [0] = [wrapOf 0] ∧\n"
                  "       clauseTokens true bareTok wrapOf [0] = [bareTok] ∧\n"
                  "       clauseTokens false bareTok wrapOf [0, 1] = [wrapOf 0, wrapOf 1] ∧\n"
                  "       clauseSuppliedValues false true [0] = [] ∧\n"
                  "       clauseSuppliedValues false false [0] = [0] ∧\n"
                  "       clauseSuppliedValues true true [0] = [0]))\n"),
            _PROOF, _PROOF_RETUNED_ASSERT),
        "rationale": "the post-images are satisfiable AND non-degenerate at the "
                     "F2P-shaped points: for a symbolic plain token and a symbolic "
                     "per-value map the token obligation demands exactly that "
                     "value's alternate token on the non-native branch, the plain "
                     "token on the native branch, and — at two listed values — each "
                     "slot's OWN value's token, so it is pointwise and not uniform; "
                     "and the accompanying-values obligation hands over nothing on "
                     "the non-native value-holding branch, every value on the "
                     "non-native open branch, and every value on the native branch, "
                     "so all three configurations are separated. The in-region "
                     "assert must discharge (else the obligation is unsatisfiable / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so both "
                     "ensures still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # that fails on the frozen loop-solution, and each carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-all-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # Every slot left as the plain placeholder — the pre-fix baseline: no
        # per-slot alternate token at all on the non-native path.
        "module": _impl("    let out := vals.map (fun _ => bareTok)\n"
                        "    return (out, clauseSuppliedValues native wrapHoldsValue vals)"),
        "refinement": "this is the pre-fix behaviour: with no per-slot alternate "
                      "token on the non-native backend the membership comparison "
                      "binds the raw stored encoding of the key, which never "
                      "compares equal to the listed scalar, so the failing "
                      "list-membership test still selects the empty set. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out.1 = clauseTokens native bareTok wrapOf "
                     "vals`: on the non-native branch each slot must carry that "
                     "slot's `wrapOf v`, and the impl carries `bareTok`. Refuted "
                     "over a multi-value list on the non-native branch, with the "
                     "second component left correct so the rejection is "
                     "attributable to the token clause alone.",
        "witness": _witness(
            'buildMembershipClauseTester [0, 0] false "a".toList '
            '(fun _ => "b".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-wrong-token",
        "kind": "uniqueness",
        "expect": "reject",
        # Every slot carries a token DERIVED from the right one but not equal to
        # it (here `bareTok ++ wrapOf v`) — the supporting near-miss: it is not
        # the plain placeholder, and it does vary with the value, yet it is not
        # the specified alternate token either. Stands in for a real patch that
        # built the operand expression with the wrong surrounding form on this
        # branch.
        "module": _impl(
            "    let out := vals.map (fun v => bareTok ++ wrapOf v)\n"
            "    return (out, clauseSuppliedValues native wrapHoldsValue vals)"),
        "refinement": "a real patch emitting a malformed operand expression on "
                      "this backend's branch produces SQL the backend does not "
                      "evaluate to the stored scalar, so the failing membership "
                      "test still does not match. It would NOT resolve.",
        "rationale": "REJECT from `out.1 = clauseTokens native bareTok wrapOf "
                     "vals`: the non-native branch pins each slot to exactly that "
                     "slot's `wrapOf v`, and any other token (here a concatenation "
                     "distinct from both `bareTok` and `wrapOf v`) violates it — so "
                     "varying with the value is not on its own enough. Refuted at a "
                     "distinct token/map pair from the other rivals, so `bareTok` "
                     "and `wrapOf` are not held fixed.",
        "witness": _witness(
            'buildMembershipClauseTester [2] false "e".toList '
            '(fun _ => "f".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-single-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every multi-value list, but leaves the SINGLE-value
        # list as the plain placeholder — the exact single-element bug the issue
        # reports (`key__in=[v]` must match `key=v`).
        "module": _impl(
            "    let out := match vals with\n"
            "      | [_] => [bareTok]\n"
            "      | _   => vals.map (fun v => slotToken native bareTok wrapOf v)\n"
            "    return (out, clauseSuppliedValues native wrapHoldsValue vals)"),
        "refinement": "a counterpart that handled only multi-value lists still "
                      "emits the plain placeholder for a single-value membership, "
                      "so the single stored-key `__in=[v]` lookup — the "
                      "discriminating single-value assertion of the failing test "
                      "— still returns nothing. It would NOT resolve.",
        "rationale": "REJECT from `out.1 = clauseTokens native bareTok wrapOf "
                     "vals`: at a single-value non-native list the only slot must "
                     "carry `wrapOf v`, and the impl carries `bareTok`. Refuted on "
                     "the single-value sub-domain (`vals.length == 1`).",
        "witness": _witness(
            'buildMembershipClauseTester [0] false "g".toList '
            '(fun _ => "h".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-multi-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary split: correct for a single-value list (the sole slot
        # gets its value's token) but on a multi-value list every NON-leading
        # slot is left plain — only the leading slot is handled.
        "module": _impl(
            "    let out := match vals with\n"
            "      | []      => []\n"
            "      | v :: vs => slotToken native bareTok wrapOf v :: vs.map (fun _ => bareTok)\n"
            "    return (out, clauseSuppliedValues native wrapHoldsValue vals)"),
        "refinement": "a counterpart handling only the first listed value's slot "
                      "emits the plain placeholder for the remaining values, so a "
                      "membership lookup over two or more values still fails to "
                      "match those slots. It would NOT resolve.",
        "rationale": "REJECT from `out.1 = clauseTokens native bareTok wrapOf "
                     "vals`: on a multi-value non-native list every slot must "
                     "carry its own `wrapOf v`, and a non-leading slot carries "
                     "`bareTok`. Refuted on the multi-value sub-domain "
                     "(`vals.length >= 2`).",
        "witness": _witness(
            'buildMembershipClauseTester [3, 4] false "i".toList '
            '(fun _ => "j".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-flag-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage rival for `native`: the token selection is inverted, so
        # each slot carries `wrapOf v` when native and `bareTok` otherwise —
        # wrong on BOTH branches. Its witness moves `native` to `true`, the
        # branch no token rival probes, so the spec's dependence on the flag is
        # demonstrated rather than assumed.
        "module": _impl(
            "    let out := vals.map (fun v => if native then wrapOf v else bareTok)\n"
            "    return (out, clauseSuppliedValues native wrapHoldsValue vals)"),
        "refinement": "a counterpart that consulted the capability flag with the "
                      "wrong polarity would rewrite the operand tokens on the "
                      "backend that stores documents natively (where the plain "
                      "placeholder is correct) and leave them plain on the backend "
                      "that needs rewriting, so the membership lookup breaks on the "
                      "very configuration the fix targets. It would NOT resolve.",
        "rationale": "REJECT from `out.1 = clauseTokens native bareTok wrapOf "
                     "vals`: the native branch must carry `bareTok` and the "
                     "non-native branch each slot's `wrapOf v`; the inverted "
                     "selector violates both. Refuted at `native == true`, the "
                     "branch no token rival's witness probes, so the `native` "
                     "binder is varied.",
        "witness": _witness(
            'buildMembershipClauseTester [1] true "c".toList '
            '(fun _ => "d".toList) true'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-uniform-token",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage rival for `wrapOf` AS A MAP, and the case that keeps
        # this spec from asserting a per-slot uniformity the real operation does
        # not have. It looks up the alternate token ONCE, from the LEADING listed
        # value, and gives that same token to every slot — correct exactly when
        # the map happens to be constant over `vals`, wrong as soon as two
        # listed values are mapped to different tokens. Its witness supplies a
        # NON-constant `wrapOf`, so the spec's pointwise dependence on each
        # slot's own value is demonstrated rather than assumed.
        "module": _impl(
            "    let out := match vals with\n"
            "      | []     => []\n"
            "      | v :: _ => vals.map (fun _ => if native then bareTok else wrapOf v)\n"
            "    return (out, clauseSuppliedValues native wrapHoldsValue vals)"),
        "refinement": "a counterpart that computed the operand expression once "
                      "from the first listed value and reused it for every slot "
                      "emits, for every other listed value, an expression that "
                      "does not correspond to that value — so on the "
                      "configurations where the expression depends on the value "
                      "being compared, a multi-value membership lookup matches the "
                      "wrong rows or none. It would NOT resolve.",
        "rationale": "REJECT from `out.1 = clauseTokens native bareTok wrapOf "
                     "vals`: the fold applies `slotToken` to EACH element, so a "
                     "non-leading slot must carry ITS OWN `wrapOf v`, not the "
                     "leading value's. Refuted at a two-value non-native list "
                     "under a NON-constant map (`wrapOf 0 ≠ wrapOf 1`), the only "
                     "input shape that separates the pointwise obligation from a "
                     "uniform one — so the spec is recorded as NOT asserting "
                     "per-slot uniformity.",
        "witness": _witness(
            'buildMembershipClauseTester [0, 1] false "k".toList '
            '(fun v => if v = 0 then "m".toList else "n".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-values-withheld",
        "kind": "uniqueness",
        "expect": "reject",
        # FIRST RIVAL FOR THE SECOND COMPONENT. Emits byte-for-byte the correct
        # per-slot tokens — it is indistinguishable from the frozen impl on the
        # token component alone — but hands over NO values alongside them. On the
        # branch whose alternate tokens left the place for their value open,
        # every slot is then awaiting a value that never arrives. This is the
        # shape a token-only obligation cannot see, which is why the second
        # `ensures` exists.
        "module": _impl(
            "    let out := vals.map (fun v => slotToken native bareTok wrapOf v)\n"
            "    return (out, [])"),
        "refinement": "a counterpart that built the right operand expressions but "
                      "stopped handing over the listed values leaves each slot's "
                      "open place unfilled, so the backend is asked to evaluate a "
                      "comparison with more places than values and rejects the "
                      "statement outright rather than returning the expected rows. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out.2 = clauseSuppliedValues native "
                     "wrapHoldsValue vals`: on the non-native branch of an "
                     "alternate family that does NOT hold its values "
                     "(`wrapHoldsValue == false`) every listed value must be handed "
                     "over, and this impl hands over none. Refuted at "
                     "(native, wrapHoldsValue) == (false, false) — the F2P's own "
                     "configuration — with the token component satisfied, so the "
                     "rejection is attributable to the second clause only.",
        "witness": _witness(
            'buildMembershipClauseTester [5] false "p".toList '
            '(fun _ => "q".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-values-overhanded",
        "kind": "uniqueness",
        "expect": "reject",
        # The complementary imbalance: correct tokens, but EVERY listed value is
        # handed over even on the branch whose alternate tokens already hold
        # their own value and so left no place for it. Together with the case
        # above this pins the balance in both directions, so neither component
        # can be chosen independently of the other.
        "module": _impl(
            "    let out := vals.map (fun v => slotToken native bareTok wrapOf v)\n"
            "    return (out, vals)"),
        "refinement": "a counterpart that handed over every listed value while "
                      "emitting operand expressions that already hold those "
                      "values supplies more values than the statement has places "
                      "for, so the backend rejects it instead of returning the "
                      "expected rows. It would NOT resolve.",
        "rationale": "REJECT from `out.2 = clauseSuppliedValues native "
                     "wrapHoldsValue vals`: on the non-native branch of an "
                     "alternate family that DOES hold its values no value may be "
                     "handed over, and this impl hands over all of them. Refuted at "
                     "(native, wrapHoldsValue) == (false, true), the mirror of the "
                     "withheld-values rival, so the balance is pinned from both "
                     "sides rather than only one.",
        "witness": _witness(
            'buildMembershipClauseTester [5] false "r".toList '
            '(fun _ => "s".toList) true'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-values-token-derived",
        "kind": "uniqueness",
        "expect": "reject",
        # THE RIVAL THAT READS THE TOKENS INSTEAD OF THE BRANCH. Tokens correct,
        # but the values handed over are derived from the emitted token's
        # relation to the plain mark rather than from `wrapHoldsValue` — it hands
        # over a value exactly when that slot's token IS the plain token, i.e.
        # everything on the native branch and nothing on the alternate one. That
        # coincides with the specified answer only when the alternate family
        # happens to hold its values, and is wrong on every alternate family that
        # left its place open — the F2P's own configuration. It is the shape that
        # makes explicit that the second obligation is decided per BRANCH and not
        # by inspecting a token.
        "module": _impl(
            "    let out := vals.map (fun v => slotToken native bareTok wrapOf v)\n"
            "    return (out, vals.filter (fun v =>\n"
            "      slotToken native bareTok wrapOf v == bareTok))"),
        "refinement": "a counterpart that decided whether to forward the listed "
                      "values by looking at the operand expression it had just "
                      "emitted would stop forwarding them on every non-native "
                      "backend, including the one whose expression still has a "
                      "place to fill, so that backend gets a comparison with more "
                      "places than values. It would NOT resolve.",
        "rationale": "REJECT from `out.2 = clauseSuppliedValues native "
                     "wrapHoldsValue vals`: the values follow the BRANCH, so on a "
                     "non-native clause whose alternate family left its place open "
                     "every value must still be handed over even though no slot's "
                     "token equals the plain token. Refuted at "
                     "(native, wrapHoldsValue) == (false, false), which is exactly "
                     "where a token-derived rule and the specified one part; the "
                     "token component is satisfied, so the rejection is "
                     "attributable to the second clause only.",
        "witness": _witness(
            'buildMembershipClauseTester [7] false "w".toList '
            '(fun _ => "x".toList) false'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-values-flag-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage rival for the INTERACTION of the two flags: tokens
        # correct, and the values handed over do read `wrapHoldsValue` — but the
        # impl drops `native`, so it withholds the values on a native clause
        # built with a value-holding alternate family, where the plain tokens it
        # actually emitted each still need their value. Its witness is the only
        # one at (true, true), so neither flag can be dropped from the second
        # obligation.
        "module": _impl(
            "    let out := vals.map (fun v => slotToken native bareTok wrapOf v)\n"
            "    return (out, if wrapHoldsValue then [] else vals)"),
        "refinement": "a counterpart that dropped the capability test from the "
                      "value-forwarding decision would, on the backend that stores "
                      "documents natively, stop forwarding the listed values while "
                      "still emitting the plain placeholder for every slot, so that "
                      "backend receives a comparison with places and no values — "
                      "breaking the configuration that worked before. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out.2 = clauseSuppliedValues native "
                     "wrapHoldsValue vals`: the native branch hands over every "
                     "listed value whatever the alternate family would have done, "
                     "and this impl hands over none. Refuted at "
                     "(native, wrapHoldsValue) == (true, true), the configuration "
                     "no other reject witness occupies, so the second obligation's "
                     "dependence on BOTH flags is demonstrated rather than assumed.",
        "witness": _witness(
            'buildMembershipClauseTester [6] true "t".toList '
            '(fun _ => "u".toList) true'),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness,
# 1 admissibility, 4 uniqueness); every one is accounted for below. The sibling
# models the per-slot expansion over EXPLICIT code-point literals for one fixed
# alternate token, with NO capability-flag input; this bundle abstracts that
# token to a per-value MAP `wrapOf`, adds the `native` flag and the
# `wrapHoldsValue` branch flag, and returns the accompanying values as a second
# component, so the mapping is stated case by case.
#
#   sibling case            -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-reorder             -> pos-inline-token,
#                              pos-token-fn-local             PORTED (split in 2)
#   admiss-1                -> admiss-nondegenerate           RE-AIMED
#   weak-bare               -> weak-all-bare                  PORTED
#   partial-last-bare       -> partial-single-bare           PORTED
#   partial-multi-bare      -> partial-multi-bare             PORTED
#   weak-wrong-wrapper      -> weak-wrong-token               PORTED
#   (no sibling)            -> weak-flag-inverted             ADDED (binder cov.)
#   (no sibling)            -> weak-uniform-token             ADDED (binder cov.)
#   (no sibling)            -> weak-values-withheld,
#                              weak-values-overhanded,
#                              weak-values-token-derived,
#                              weak-values-flag-ignored       ADDED (2nd component)
#   (no sibling)            -> pos-loopfree                   ADDED (witness ref.)
#
# 5 ported (pos split into two shapes), 1 re-aimed, 7 added = the six sibling
# cases all carried, plus two binder-coverage rivals on the token component,
# four rivals on the accompanying-values component, and one loop-free positive
# that doubles as every reject case's refutation subject.
#
# ADDED (3): pos-loopfree. No sibling: nagini needs no such case, because Viper
#   discharges the postcondition itself and its reject cases need no witness at
#   all. It exists here purely to make the reject lane checkable — see the
#   WITNESS NOTE below — and is a correct impl in its own right, so it is a
#   genuine soundness positive and not a scaffold.
#
# SPLIT (pos-reorder): the sibling's single soundness positive reordered the
#   two loop branches and bound literals to typed locals. This backend's frozen
#   impl has ONE loop body (one token per slot, looked up from that slot's
#   value), not a two-branch first-vs-rest structure, so the sibling's exact
#   reorder does not exist here. The reshape spirit — "structurally different,
#   behaviourally identical, same invariant" — is carried by TWO shapes:
#   pos-inline-token (apply the pure selector to the indexed element inline, and
#   write the branch test as one boolean) and pos-token-fn-local (hoist the
#   selection into a local function of the value, and compute the second
#   component through the pure post-image), both keeping the gold
#   front-recursive invariant so the reproof stays close to the frozen script.
# RE-AIMED (admissibility): the sibling asserts the precondition admits the F2P
#   single-value and multi-value counts. This backend's precondition is
#   `∀ v ∈ vals, wrapOf v ≠ bareTok`, which excludes no F2P-shaped input (the
#   F2P's plain placeholder and each value's alternate token genuinely differ),
#   so that probe is uninteresting. It is re-aimed at the residual total-domain
#   risk — that the post-image is DEGENERATE at the interesting point — via an
#   in-region assert that the token obligation distinguishes the two branches at
#   a single-value membership AND is pointwise (not uniform) at a two-value one,
#   and that the accompanying-values obligation separates all three branch
#   configurations.
# ADDED (1): weak-flag-inverted. The sibling's carrier has no capability-flag
#   binder (it hardcodes the alternate token), so this rival has no sibling.
#   It exists purely for binder coverage: without it every token rival's witness
#   would sit at `native == false` and a rival mishandling the flag would go
#   uncaught.
# ADDED (2): weak-uniform-token. The sibling's carrier has ONE fixed alternate
#   token, so a rival that reuses one slot's token everywhere is invisible to it.
#   This bundle's `wrapOf` is a per-value MAP, and this rival is the one that
#   pins the difference: it satisfies every other reject witness (all of which
#   pass a CONSTANT `wrapOf`) and is caught only by a witness with a
#   non-constant map. It is what records, in the battery itself, that the spec
#   does not assert per-slot uniformity.
# ADDED (4): the four second-component rivals. The sibling returns only the
#   token expansion, so it has no counterpart for the accompanying values. All
#   four emit byte-for-byte correct tokens, so each is caught by the second
#   ensures alone: withheld (hands over none), overhanded (hands over all),
#   token-derived (reads the emitted token instead of the branch flag) and
#   flag-ignored (reads `wrapHoldsValue` but drops `native`). Together they
#   place (native, wrapHoldsValue) at (false,false), (false,true) and (true,true)
#   and refuse both a constant answer and either flag-dropping shortcut.
#
# FRAME/PERMISSION-MUTATION: the sibling records this N/A (its lone input carries
#   no heap permission); it is VACUOUS here for the stronger reason that this
#   backend is referentially transparent and the method declares no `mut`
#   parameter, so there is no read-only input to overwrite. No substitute
#   fabricated.
#
# WITNESS NOTE (backend-specific, no sibling counterpart). The frozen impl is a
#   `while` loop; under `loom.semantics.choice "demonic"` its extracted program is
#   a partial-fixpoint iteration through `Classical.choice` that the kernel does
#   not reduce, so `decide` against the FROZEN solution's tester is stuck for
#   every claim — true or false alike. A frozen-side failure is therefore NOT
#   evidence of refutation: the same `did not reduce to `isTrue` or `isFalse``
#   error would appear for a true claim, so the exit code discriminates nothing
#   and a witness asserting the rival is CORRECT would clear both halves.
#   (An earlier revision of this battery rested on exactly that stuck-`decide`
#   failure and was correctly recorded `witness-undecided` on all five rivals ->
#   MALFORMED-TESTS. It is fixed here, not worked around.)
#
#   The repair: every reject case names `witness_reference = _LOOPFREE`, a
#   loop-free straight-line impl of the same frozen spec which the gate checks
#   shares the spec and VERIFIES, and which — having no loop — REDUCES. Each
#   rival is likewise straight-line computable, so both sides decide: the witness
#   `…Tester args = false` elaborates against the rival, and against the
#   reference `decide` positively proves the tester is `true`
#   (`Tactic `decide` proved that the proposition … is false`) — a real verdict.
#   Verified out-of-band with lean_verify.sh for all ten rivals: rival build
#   exit 0, reference build exit 1 by refutation, and every reference-side log
#   screened for `did not reduce to` (zero occurrences on either side).
#   `_LOOPFREE` also ships as the `pos-loopfree` positive, so the battery records
#   that loop-freeness is not what any rival is rejected for.
#
# BINDER / DOMAIN COVERAGE of the reject witnesses over the five input binders
#   of the two ensures:
#     vals    — length 1 (partial-single-bare, weak-flag-inverted, weak-wrong-
#               token, all four value rivals), length 2 (weak-all-bare,
#               partial-multi-bare, weak-uniform-token); order exercised by the
#               multi-value rivals; ELEMENT identity made load-bearing by
#               weak-uniform-token, whose two elements are mapped to different
#               tokens.
#     native  — false (weak-all-bare, weak-wrong-token, partial-single-bare,
#               partial-multi-bare, weak-uniform-token, weak-values-withheld,
#               weak-values-overhanded, weak-values-token-derived), true
#               (weak-flag-inverted, weak-values-flag-ignored): both branches,
#               and both obligations are refuted on each branch.
#     bareTok — distinct concrete plain tokens that MOVE across rivals
#               ("a", "e", "g", "i", "c", "k", "p", "r", "w", "t"), so it is not
#               held fixed.
#     wrapOf  — CONSTANT maps that move across rivals (to "b", "f", "h", "j",
#               "d", "q", "s", "x", "u") plus one NON-constant map
#               (weak-uniform-token: 0 -> "m", otherwise "n"), so the map's
#               dependence on its argument is exercised and not merely assumed.
#               Both token branches make one of the two load-bearing (non-native
#               pins `wrapOf v` per slot, native pins `bareTok`).
#     wrapHoldsValue — false (weak-values-withheld, weak-values-token-derived,
#               and the token rivals' witnesses), true (weak-values-overhanded,
#               weak-values-flag-ignored, weak-flag-inverted). Paired with
#               `native` the value rivals occupy (false,false), (false,true) and
#               (true,true), which is what refutes dropping either flag from the
#               second obligation.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference, so there is nothing there to probe.
AXIOM_TESTS = []
