"""properties.py — G-PBT falsification battery for django__django-16877 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct escapeEach`` header survives) and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — elaborates against the rival, FAILS against the
discriminating subject. That subject is NOT gold here: gold's loop does not
reduce, so ``decide`` cannot synthesize a ``Decidable`` instance and gold's build
fails for every claim regardless of truth. Each reject case therefore names a
``witness_reference`` — see the witness preamble for the three builds that
measured it).

DEFENDED SURFACE (one contracted method over a sequence of elements):

  escapeEach (items : List Elem) return (out : List (List Char))
    ensures out = escSeq items          -- THE load-bearing (and only) clause

with ``escSeq`` / ``condEscape`` / ``escapedSeq`` / ``entity`` fully-unfolded
``def``s in the ``pure`` region:

  escSeq []        = []
  escSeq (e :: es) = condEscape e :: escSeq es
  condEscape e     = if e.safe then e.chars else escapedSeq e.chars
  escapedSeq (c :: cs) = entity c ++ escapedSeq cs
  entity c         = the entity expansion of one code point, else [c]

so the single clause pins FIVE independent sub-behaviours of the built sequence:

  * ARITY — one output entry per input entry (``escSeq`` is length-preserving);
  * ORDER — the k-th output entry is the transform of the k-th input entry;
  * SAFE PASSTHROUGH — an element already marked as needing no further
    transformation is emitted unchanged (``e.safe`` branch of ``condEscape``);
  * TRANSFORM-ON-UNMARKED — any other element IS transformed per code point
    (the ``escapedSeq`` branch);
  * PER-CODE-POINT CONTENT — each significant code point expands to its own
    entity sequence, and the expansion is such that an emitted marker code point
    is never itself re-expanded (``entity``).

``escSeq`` is GROUNDED in the input (a total front-recursive fold over ``items``);
the ``axioms`` region is EMPTY (``condEscape``/``escapedSeq`` are deep
A-references validated == the real callees by axiom_check.py, NOT a consumed
answer key), so there is no wrong echo to build and the ungrounded-oracle probe
degenerates to an honest cheapest-impl positive control. The sole INPUT BINDER is
``items : List Elem``, whose per-element observables are ``chars : List Char`` and
``safe : Bool``.

THE CARRIER IS FULLY TRANSPARENT. ``escSeq``/``condEscape``/``escapedSeq``/
``entity`` all compute on ``Char`` literals, so a witness reaches the impl through
Velvet's extractor (``extract_program_for escapeEach`` gives ``escapeEachExec
items = NonDetT.run (escapeEach items)``) and states ``escapeEachExec xs ≠
DivM.res (escSeq xs)`` at a concrete ``xs``, with ``decide`` closing the residual
literal. No opaque leaf, so no carrier conditioning is needed, no witness binds a
hypothesis, and there is no joint-satisfiability obligation. The FROZEN impl
carries a backward ``while`` loop whose extracted program does NOT reduce under
``simp``/``decide`` (the ``forIn`` fixpoint stays stuck), so each reject rival is a
straight-line loop-free CLOSED FORM whose extracted program DOES reduce to a
literal; the witness therefore ELABORATES against the rival.

Gold's build failing is NOT the other half of that discrimination, and an earlier
revision of this file wrongly claimed it was. Gold "stays stuck" is precisely the
defect: a build that fails because no ``Decidable`` instance can be synthesized
for an irreducible ``forIn`` term never evaluated the claim, so its exit code
attests to nothing. AUDITED with real builds — against gold the real refutation,
the exact OPPOSITE (agreement) claim, and a plainly TRUE claim about gold ALL
exit 1 with ``failed to synthesize Decidable``. The discriminating subject is
therefore the ``witness_reference`` below, a loop-free VERIFYING impl of the same
spec against which each witness fails by genuine refutation (``decide`` proves the
proposition false) and the agreement-point forgery correctly SUCCEEDS.

Every reject rival was additionally re-checked with the ``prove_correct`` body
RETUNED to a bare ``loom_solve``, and each still fails with the residual
``ensures_1: out = escSeq items`` goal open — so its rejection is attributable to
the postcondition, not to the frozen tactic script losing its footing on a
reshaped impl.

ADVERSARIAL READ of the sibling classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling battery carries this as
    MANDATORY (twice: write back into the input element, and into an element of
    the input sequence) because those inputs are held at fractional read
    permission. Lean and Velvet are referentially transparent: ``items`` is an
    immutable value, this bundle declares NO ``mut`` binder over any input, and
    there is no heap and no aliasing — so there is no read-only input to overwrite
    and no substitute probe to build. Not fabricated.
  * ADMISSIBILITY — APPLIES, and is CARRIED (added under audit; an earlier
    revision wrongly dropped it as vacuous because the ``pre-conditions`` region
    is empty). On a total carrier the lane tests that the obligation is
    satisfiable and non-degenerate at an F2P-shaped input, which the positive
    ``admiss-obligation-satisfiable-at-f2p-shape`` discharges by evaluation.
  * PARTIAL-DOMAIN / VALUE / ARITY — APPLIES; the heart of the port. Each sibling
    rival re-expresses directly onto one sub-obligation of ``out = escSeq items``.
  * RESULT-SAFETY-FLAG — INEXPRESSIBLE on this carrier (see the accounting note).
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * UNGROUNDED-ORACLE ECHO — N/A. ``escSeq`` is a total fold over the method's own
    input; there is no answer key to echo. Replaced by the honest positive
    controls.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; the deep
A-references are axiom_check.py's / G-AX's job, and this gate ignores
``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-16877"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct escapeEach header
# intact.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the backward per-element loop plus the
# accumulator return). Reject rivals replace it with a loop-free closed form (so
# their extracted program reduces under decide); the direct positive control
# replaces it with the closed-form correct map.
_IMPL = """    let mut acc : List (List Char) := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant acc = escSeq (items.drop i)
      done_with i = 0
      decreasing i
    do
      let e := items[i - 1]!
      acc := condEscape e :: acc
      i := i - 1
    return acc
"""

# The per-element loop step (inside the loop body, wholly inside the impl
# region). The two loop-preserving positive controls reshape only this.
_STEP = """      let e := items[i - 1]!
      acc := condEscape e :: acc
      i := i - 1
"""

# The frozen prove_correct tactic body. Unique in the file and elided from the
# spec view; the header line `prove_correct escapeEach by` is PRESERVED by every
# variant below (only the indented tactic lines under it ever change).
_PROOF = """prove_correct escapeEach by
  loom_solve
  rw [escSeq_drop_step items i (by omega) (by omega)]
  simp_all
"""

# A bare retune, used by the closed-form variants: with the loop gone there is no
# drop-step goal for the frozen `rw` to fire on, so the frozen tail would fail
# with `No goals to be solved` for a reason having nothing to do with the spec.
_BARE = "prove_correct escapeEach by\n  loom_solve\n"


def _closed(expr, proof=_BARE):
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`."""
    return _swap(_swap(_BASE, _IMPL, f"    return ({expr})\n"), _PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `escapeEachExec xs` is `NonDetT.run (escapeEach xs)`; `≠ DivM.res
# ---- (escSeq xs)` says the impl's output contradicts the postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block is stripped,
# ---- so no tactic script can mask the verdict. No hypothesis is bound, so there
# ---- are no assumptions that could be jointly unsatisfiable.
# ----
# ---- THE SECOND SUBJECT IS NOT GOLD. The frozen impl is a backward `while` loop
# ---- whose extracted program does NOT reduce: the `forIn` fixpoint stays stuck,
# ---- and `decide` then cannot even SYNTHESIZE the `Decidable` instance for the
# ---- claim. That failure is a TYPECLASS failure about an irreducible term, not a
# ---- refutation, so against gold the build fails for EVERY claim regardless of
# ---- truth and its exit code discriminates nothing. Measured with three real
# ---- builds against the frozen solution:
# ----   * the real refutation at `[⟨['&'], false⟩]`         -> exit 1
# ----   * the OPPOSITE claim (the rival AGREES with `escSeq` there, i.e. an
# ----     `=` where the witness writes `≠`) -> exit 1
# ----   * a plainly TRUE claim about gold (`escapeEachExec [] = DivM.res
# ----     (escSeq [])`)                                     -> exit 1
# ---- all three with `error: failed to synthesize Decidable ... forIn ...`. So a
# ---- forged witness asserting the rival is CORRECT at an agreement point clears
# ---- both halves against gold (rival exit 0, gold exit 1) and would be recorded
# ---- as a refutation. Gold cannot serve as the discriminating subject here.
# ----
# ---- Every reject case therefore carries an explicit `witness_reference`: the
# ---- loop-free `items.map condEscape` impl, which the gate independently checks
# ---- shares the frozen spec AND verifies before refuting the witness against it.
# ---- That is sound for the reason gold was meant to be — an impl the verifier
# ---- ACCEPTS cannot violate its own spec — and unlike gold it REDUCES, so the
# ---- failure is a real verdict. Re-measured against that reference:
# ----   * each of the seven real witnesses -> exit 1 with
# ----     ``Tactic `decide` proved that the proposition ¬[condEscape ...] =
# ----     escSeq [...] is false`` — a SEMANTIC refutation of the concrete claim;
# ----   * the agreement-point forgery                       -> exit 0 (correctly
# ----     exposed as vacuous, where gold recorded it as a refutation).
def _witness(xs):
    return (
        "extract_program_for escapeEach\n\n"
        f"example : escapeEachExec {xs} ≠ DivM.res (escSeq {xs}) := by\n"
        "  unfold escapeEachExec escapeEach\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n"
    )


# The discriminating subject for every reject witness (see the preamble): a
# loop-free impl of the FROZEN spec that VERIFIES and whose extracted program
# REDUCES, so `decide` returns a verdict instead of getting stuck. Byte-identical
# to the `pos-control-direct-map` variant, which the battery independently
# asserts verifies.
_WITNESS_REF = _closed(
    "items.map condEscape",
    "prove_correct escapeEach by\n"
    "  loom_solve\n"
    "  induction items with\n"
    "  | nil => rfl\n"
    "  | cons e es ih => simp [escSeq_cons, ih]\n")


# The near-miss rivals differ from the correct per-code-point expansion at exactly
# ONE code point, so they need the honest expansion everywhere else. `flatMap
# entity` is definitionally the same fold as `escapedSeq` (both are
# `entity c ++ <rest>`), which is what makes them genuine near-misses rather than
# wholesale replacements.
def _near_miss(target, wrong):
    return (
        "items.map (fun e => if e.safe then e.chars else "
        f"e.chars.flatMap (fun c => if c = {target} then {wrong}.toList "
        "else entity c))"
    )


# The admissibility proof body (see the ADMISSIBILITY case). The frozen tactic
# script is preserved VERBATIM after the two `have`s, so the real obligation is
# still discharged exactly as gold discharges it; only the elided tactic body
# grows.
_ADMISS_PROOF = (
    "prove_correct escapeEach by\n"
    "  have hsat : escSeq [⟨\"a&b\".toList, false⟩, ⟨\"<i>\".toList, true⟩]\n"
    "      = [\"a&amp;b\".toList, \"<i>\".toList] := by decide\n"
    "  have hdisc : escSeq [⟨\"a&b\".toList, false⟩]\n"
    "      ≠ escSeq [⟨\"a&b\".toList, true⟩] := by decide\n"
    "  loom_solve\n"
    "  rw [escSeq_drop_step items i (by omega) (by omega)]\n"
    "  simp_all\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `escSeq items` is GROUNDED in the argument (a total
    # front-recursive fold), so the closed-form element-wise map is a correct
    # fully-grounded implementation, not an ungrounded-oracle echo — and it
    # doubles as proof the spec is not echo-vulnerable: any WRONG constant or map
    # fails `out = escSeq items` (the seven rivals below witness exactly that).
    # The loop is gone, so the frozen proof's drop-step `rw` has no goal to fire
    # on; the residual obligation is discharged by an inline induction on the
    # input sequence, adding NO lemma and NO axiom.
    # =====================================================================
    {
        "id": "pos-control-direct-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _closed(
            "items.map condEscape",
            "prove_correct escapeEach by\n"
            "  loom_solve\n"
            "  induction items with\n"
            "  | nil => rfl\n"
            "  | cons e es ih => simp [escSeq_cons, ih]\n"),
        "rationale": "the post-image `escSeq items` is GROUNDED in the input (a "
                     "total fold, no opaque answer key), so the closed-form "
                     "element-wise map is the honest cheapest CORRECT impl and "
                     "MUST verify — the clause is literally `out = escSeq items` "
                     "— else that single clause is SPEC-TOO-STRONG. It is also a "
                     "structurally different shape from the frozen backward "
                     "accumulator loop (no loop, no invariants), so it exercises "
                     "the clause independently of the loop reasoning. The "
                     "residual goal `List.map condEscape items = escSeq items` "
                     "closes by inline induction on `items` using only the frozen "
                     "`escSeq_cons` lemma; no new lemma, axiom, or `sorry`.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the sibling's local-bind control. Same
    # correct map, different executable shape: bind the per-element result to a
    # typed local before prepending instead of prepending the call's result
    # directly. The loop and ALL its invariants are kept BYTE-IDENTICAL, so the
    # frozen proof script closes with no retune at all.
    # =====================================================================
    {
        "id": "pos-control-local-bind",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _STEP,
            "      let e := items[i - 1]!\n"
            "      let marked : List Char := condEscape e\n"
            "      acc := marked :: acc\n"
            "      i := i - 1\n"),
        "rationale": "binding the per-element transform to a typed local `marked` "
                     "and prepending the local is the same arity- and "
                     "order-preserving map; every loop invariant is byte-identical "
                     "so the frozen proof script still discharges "
                     "`out = escSeq items` with NO retune. A faithful correct "
                     "restructure MUST verify, else the clause is over-fit to the "
                     "expression FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the sibling's branch-reorder control. The
    # per-element conditional is inlined with the branches written in the OPPOSITE
    # order (transform-the-unmarked first, then the passthrough), a different
    # control-flow shape that is observationally the same map. The loop and its
    # invariants stay byte-identical; the reordered conditional leaves a residual
    # if/else-orientation goal that `split <;> simp_all` closes, so the proof
    # stays within the frozen reasoning (no new lemma).
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _STEP,
                  "      let e := items[i - 1]!\n"
                  "      let marked : List Char := "
                  "if !e.safe then escapedSeq e.chars else e.chars\n"
                  "      acc := marked :: acc\n"
                  "      i := i - 1\n"),
            _PROOF,
            _PROOF.rstrip("\n").replace("  simp_all", "  simp_all [condEscape]")
            + "\n  split <;> simp_all\n"),
        "rationale": "a correct impl with the two per-element branches written in "
                     "the opposite order (transform-the-unmarked first, then the "
                     "passthrough) must still verify: each branch independently "
                     "establishes its half of `condEscape`, and the loop "
                     "invariants are byte-identical. The reordered conditional "
                     "leaves only an if/else-orientation goal, closed by "
                     "`split <;> simp_all` — no new induction, lemma, or axiom. "
                     "If it failed, the clause would be over-fit to one branch "
                     "ORDER => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED UNDER AUDIT. The port dropped this lane entirely,
    # arguing the `pre-conditions` region is EMPTY so there is no precondition to
    # admit. That reason is insufficient: the analogue on a TOTAL carrier is the
    # obligation being UNSATISFIABLE (or degenerate) at exactly an F2P-shaped
    # input, and "the post-image is a total function" is an argument, not a
    # demonstration. This case demonstrates it by EVALUATION, as two `have`s, at a
    # concrete input carrying the two features every other case in this battery
    # misses at once — MULTI-code-point element content and MIXED marks within one
    # sequence — and then closes the frozen obligation with the frozen script
    # VERBATIM.
    #   * `hsat` computes the post-image at that input and pins it to a literal, so
    #     the obligation demonstrably HAS a satisfying output there (a spec no impl
    #     can meet at the interesting point reads exactly like a spec every impl
    #     meets);
    #   * `hdisc` shows the post-image is NON-DEGENERATE in the observable the new
    #     behaviour turns on: flipping only the mark on one element CHANGES the
    #     required output, so the clause genuinely discriminates the marked from
    #     the unmarked sub-domain rather than collapsing them.
    # Both are LIVE, not decoration: the same case with `hsat` claiming the
    # transformed form for the MARKED element instead FAILS to elaborate (measured
    # under audit, exit 1), so a false claim about this point does not close.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _ADMISS_PROOF),
        "rationale": "PASS SOURCE = the obligation `out = escSeq items` is "
                     "SATISFIABLE and NON-DEGENERATE at a concrete F2P-shaped "
                     "input — a two-element sequence with multi-code-point content "
                     "and MIXED marks, the shape no other case here reaches. "
                     "`hsat` evaluates the post-image at that input and pins it to "
                     "a literal (so a satisfying output demonstrably exists there, "
                     "by computation rather than by the argument that `escSeq` is "
                     "total); `hdisc` shows that flipping ONLY the mark on one "
                     "element changes the required output, so the clause really "
                     "does distinguish the marked from the unmarked sub-domain "
                     "instead of collapsing them. If either failed, the obligation "
                     "would be unsatisfiable or degenerate at exactly the input "
                     "the behaviour is about => PRECOND-TOO-STRONG / "
                     "SPEC-UNSATISFIABLE. The frozen `ensures` is untouched and "
                     "the frozen tactic script still closes the real obligation "
                     "verbatim afterwards, so nothing is weakened; only the elided "
                     "tactic body grows. The `have`s are live — the same case with "
                     "`hsat` asserting the transformed form for the MARKED element "
                     "does not elaborate.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input, plus the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing tests.
    # =====================================================================

    # ---- SAFE-PASSTHROUGH clause: transform EVERY element unconditionally ----
    {
        "id": "weak-transform-marked-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("items.map (fun e => escapedSeq e.chars)"),
        "refinement": "transforming every element unconditionally — ignoring the "
                      "per-element mark that says the element already needs no "
                      "further transformation — applies the expansion a SECOND "
                      "time to an already-transformed element. For a sequence "
                      "whose elements carry that mark the tests require the "
                      "rendered output to be UNCHANGED, but this counterpart "
                      "expands the significant code points again and renders the "
                      "doubly-expanded text. A faithful counterpart with that "
                      "defect therefore fails the failing tests that render a "
                      "pre-marked sequence, so it would NOT resolve.",
        "rationale": "REJECT from `out = escSeq items` (SAFE-PASSTHROUGH half): "
                     "`condEscape e = e.chars` when `e.safe`, but the rival "
                     "returns `escapedSeq e.chars` there. Refuted at a "
                     "single-element sequence whose element is MARKED and whose "
                     "content is one significant code point — the rival emits the "
                     "expansion, `escSeq` emits the code point unchanged. Varies "
                     "`safe` to true (the only rival witness that does).",
        "witness": _witness("[⟨['&'], true⟩]"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- TRANSFORM-ON-UNMARKED clause: never transform, just pass through ----
    {
        "id": "weak-skip-transform-unmarked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("items.map (fun e => e.chars)"),
        "refinement": "passing every element through untransformed — treating the "
                      "whole sequence as though each element already needed no "
                      "further transformation — leaves the significant code points "
                      "raw in the rendered output. The failing tests render a "
                      "sequence of UNMARKED elements and require the expanded "
                      "text; this counterpart renders the raw text instead, so it "
                      "fails every one of them and would NOT resolve. This is the "
                      "dual of the rival above and the reason the new per-element "
                      "behaviour is needed at all.",
        "rationale": "REJECT from `out = escSeq items` (TRANSFORM-ON-UNMARKED "
                     "half): `condEscape e = escapedSeq e.chars` when `!e.safe`, "
                     "but the rival returns `e.chars` there. Refuted at a "
                     "single-element UNMARKED sequence carrying one significant "
                     "code point — the rival emits it raw, `escSeq` emits the "
                     "expansion. Same content as the rival above with `safe` "
                     "flipped, which is what isolates this clause from that one.",
        "witness": _witness("[⟨['&'], false⟩]"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- ARITY clause: one entry short ----
    {
        "id": "weak-drop-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("items.take (items.length - 1) |>.map condEscape"),
        "refinement": "building one entry short makes the returned sequence "
                      "shorter than the input. The failing tests render the built "
                      "sequence after joining its entries, so a counterpart that "
                      "dropped the final entry renders only a prefix of the "
                      "expected text (the last element and its separator missing) "
                      "and fails the join assertions, so it would NOT resolve.",
        "rationale": "REJECT from `out = escSeq items` (ARITY half): `escSeq` is "
                     "length-preserving, so a result one entry short cannot equal "
                     "it. Refuted at a TWO-element unmarked sequence — the rival "
                     "returns a one-entry list, `escSeq` a two-entry one. Varies "
                     "`items.length` to 2, which no single-element witness probes.",
        "witness": _witness("[⟨['&'], false⟩, ⟨['<'], false⟩]"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- ORDER clause: entries built in the wrong order ----
    #      Distinct from the arity rival: the arity is RIGHT and every entry's
    #      content is individually right; only the positional alignment is wrong.
    {
        "id": "weak-reverse-entry-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("(items.map condEscape).reverse"),
        "refinement": "building the entries in reverse order keeps the arity and "
                      "every individual entry's content correct but breaks the "
                      "positional alignment with the input. The failing tests join "
                      "the built sequence and compare the rendered text, which is "
                      "order-sensitive: a counterpart that reversed the sequence "
                      "renders the elements in the wrong order and fails the join "
                      "assertions, so it would NOT resolve.",
        "rationale": "REJECT from `out = escSeq items` (ORDER half): the k-th "
                     "output entry must be the transform of the k-th input entry. "
                     "Refuted at a two-element sequence that is non-symmetric in "
                     "BOTH observables — different content AND different marks "
                     "(unmarked then marked) — so the reversal is detectable and "
                     "the witness additionally varies `safe` WITHIN one input, "
                     "which no other witness does.",
        "witness": _witness("[⟨['&'], false⟩, ⟨['<'], true⟩]"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- PER-CODE-POINT CONTENT clause: near-miss on one code point ----
    #      Correct at every other code point (`flatMap entity` is definitionally
    #      the same fold as `escapedSeq`), so it gets its OWN witness at the one
    #      input that distinguishes it — the sub-domain its rationale claims.
    {
        "id": "weak-alternate-numeric-reference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(_near_miss("'\\''", '"&#39;"')),
        "refinement": "emitting one significant code point as a DECIMAL numeric "
                      "reference rather than the hexadecimal one the modeled "
                      "transformation specifies matches a different library's "
                      "convention, not the one the changed operation delegates to. "
                      "On any element containing that code point the rendered "
                      "output carries the decimal form where the real delegate "
                      "produces the hexadecimal form, so a faithful counterpart "
                      "built on this expansion diverges from the delegate's output "
                      "and would NOT match what the tests assert.",
        "rationale": "REJECT from `out = escSeq items` (PER-CODE-POINT CONTENT "
                     "half): `entity` fixes the expansion of that code point, and "
                     "the rival substitutes a different reference form for it. A "
                     "NEAR-MISS — it agrees with `escSeq` at every other code "
                     "point — so it is refuted at its OWN distinguishing input, an "
                     "unmarked single-element sequence whose content IS that code "
                     "point. Varies `chars` to a code point no other witness uses.",
        "witness": _witness("[⟨['\\''], false⟩]"),
        "witness_reference": _WITNESS_REF,
    },

    # ---- PER-CODE-POINT CONTENT clause: only the FIRST code point expanded ----
    #      ADDED UNDER AUDIT. Every other reject witness in this battery states its
    #      refutation at a SINGLE-code-point element, so the whole battery agreed
    #      with a rival that transforms only the leading code point of each element
    #      and leaves the rest raw — it is observationally identical to gold on
    #      every single-code-point input, i.e. on all six pre-existing witnesses.
    #      That sub-domain (multi-code-point content, which is the shape a real
    #      consumer passes) was the one the manifest's coverage note claimed by
    #      construction and never demonstrated. Refuted here at its own
    #      distinguishing input.
    {
        "id": "weak-first-code-point-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "items.map (fun e => if e.safe then e.chars else "
            "(match e.chars with | [] => [] | c :: cs => entity c ++ cs))"),
        "refinement": "expanding only the leading code point of an unmarked "
                      "element and copying the remainder raw leaves every "
                      "significant code point after the first unexpanded in the "
                      "rendered output. The failing tests render elements whose "
                      "significant code point sits in the MIDDLE of the content, "
                      "so a faithful counterpart with this defect emits the raw "
                      "code point there where the expected text carries the "
                      "expansion, and fails those assertions — so it would NOT "
                      "resolve. It is the subtlest of the rivals here precisely "
                      "because it agrees with the specified behaviour on every "
                      "single-code-point element.",
        "rationale": "REJECT from `out = escSeq items` (PER-CODE-POINT CONTENT "
                     "half, per-position sub-case): `escapedSeq` folds `entity` "
                     "over EVERY code point, not just the head. Refuted at an "
                     "unmarked single-element sequence whose content is THREE code "
                     "points with the significant one in the middle — the rival "
                     "copies it raw, `escSeq` expands it. This is the only witness "
                     "in the battery that varies `chars.length` beyond 1, which is "
                     "what isolates this clause: the rival is definitionally EQUAL "
                     "to `escSeq` at every single-code-point input, so none of the "
                     "other five witnesses discriminates it.",
        "witness": _witness('[⟨"a&b".toList, false⟩]'),
        "witness_reference": _WITNESS_REF,
    },

    # ---- PER-CODE-POINT CONTENT clause: the expansion-ordering near-miss ----
    {
        "id": "weak-marker-reexpanded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(_near_miss("'<'", '"&amp;lt;"')),
        "refinement": "this is the one ordering subtlety the modeled "
                      "transformation is built to avoid: the code point that "
                      "introduces every expansion must be expanded FIRST, or the "
                      "one emitted at the head of a later expansion gets expanded "
                      "again. This counterpart emits the doubly-expanded form for "
                      "a significant code point. On the sequences the failing "
                      "tests render, the expected text carries the single "
                      "expansion, so a faithful counterpart with the expansions "
                      "applied in the wrong order renders visibly doubled markup "
                      "and fails every failing test, so it would NOT resolve.",
        "rationale": "REJECT from `out = escSeq items` (PER-CODE-POINT CONTENT "
                     "half, ordering sub-case): `entity` pins the single "
                     "expansion for that code point, and the rival emits the form "
                     "you get if the introducing code point were expanded LAST. "
                     "Another NEAR-MISS — correct at every other code point, "
                     "including the apostrophe the previous rival breaks — so it "
                     "gets its own witness at its own distinguishing code point.",
        "witness": _witness("[⟨['<'], false⟩]"),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Sibling -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 partial-domain/value
# rivals) plus a 1-case AXIOM lane. This bundle contracts ONE method where the
# sibling contracts three (the sequence map, the per-element transform, and the
# per-code-point fold are all reachable here through the SINGLE clause
# `out = escSeq items`, because all three are `pure`-region `def`s that clause
# unfolds to), so the per-function split collapses and every sibling case is
# re-aimed at the corresponding sub-obligation of that one clause.
#
#   sibling case                        -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-branch-reorder          -> pos-control-branch-reorder     PORTED
#   pos-control-local-bind              -> pos-control-local-bind        PORTED
#   (no sibling)                        -> pos-control-direct-map        ADDED
#   admiss-fresh-unsafe-item            -> admiss-obligation-satisfiable-at-f2p-shape
#                                                                       RE-AIMED
#   frame-mutate-input-item             -> (none)                        VACUOUS
#   frame-mutate-input-list-element     -> (none)                        VACUOUS
#   partial-domain-reescape-safe        -> weak-transform-marked-element  PORTED
#   partial-domain-skip-escape-unsafe   -> weak-skip-transform-unmarked   PORTED
#   arity-drop-last-element             -> weak-drop-last-entry          PORTED
#   flag-result-not-marked-safe         -> (none)                        INEXPRESSIBLE
#   wrong-apostrophe-decimal-ref        -> weak-alternate-numeric-reference PORTED
#   ampersand-last-double-escape-lt     -> weak-marker-reexpanded        PORTED
#   (no sibling)                        -> weak-reverse-entry-order      ADDED
#   (no sibling)                        -> weak-first-code-point-only    ADDED (audit)
#   (sibling termination lane)          -> (none)                        SPEC-CLOSED
#   AXIOM_TESTS (1)                     -> (none)                        DROPPED (G-AX)
#
# 6 ported, 1 re-aimed, 3 added, 2 vacuous, 1 inexpressible, 1 known hole,
# 1 dropped = 11 SPEC cases (3 soundness, 1 admissibility, 7 uniqueness).
#
# PORTED (2 positive controls): the sibling's branch-reorder writes the
#   per-element conditional's two branches in the opposite order; the port inlines
#   the same conditional reversed inside the frozen loop, keeping all invariants
#   byte-identical (residual if/else-orientation goal closed by `split <;>
#   simp_all`). The sibling's local-bind control ports 1:1 and needs NO proof
#   retune at all. Both verified to build (exit 0).
# ADDED (pos-control-direct-map): the loop-free closed-form map. The sibling has
#   no counterpart because its cheapest impl would be the oracle echo it
#   explicitly declines to build; here the post-image is grounded, so the closed
#   form is honest AND is the only positive that exercises the clause with the
#   loop entirely absent. Proof closes by inline induction on `items` over the
#   frozen `escSeq_cons` lemma — no new lemma/axiom/sorry.
# PORTED (4 value rivals): reescape-safe, skip-escape-unsafe, drop-last-element,
#   and the two per-code-point near-misses re-express DIRECTLY onto the
#   corresponding sub-obligation of `out = escSeq items` (the safe-passthrough
#   branch, the transform branch, length preservation, and `entity`'s expansion of
#   one code point). Each refinement argument carries over unchanged in substance:
#   a faithful counterpart with that defect renders text the failing tests
#   contradict, so it would NOT resolve.
# ADDED (weak-reverse-entry-order): attacks the ORDER sub-obligation on its own.
#   The sibling folds order into the same per-index `Forall` as arity, but here the
#   arity rival (one entry short) and the order rival (right arity, right per-entry
#   content, wrong alignment) fail for genuinely DIFFERENT reasons, so they are
#   separate rivals with separate witnesses rather than sharing one.
# INEXPRESSIBLE (flag-result-not-marked-safe): the sibling rejects an impl that
#   transforms correctly but returns the result NOT marked safe, caught by its
#   `Result().is_safe` clause. This carrier has no such clause to attack: per
#   mapping.md §2 the marker wrapper on a RESULT maps to the IDENTITY and is
#   omitted, so the output carrier is `List (List Char)` — bare content with no
#   safety bit. There is no output observable a rival could get wrong, so no rival
#   is wrong on this carrier and no witness could discriminate one. Dropped per
#   the standing rule (the abstraction collapses the distinction the sibling's
#   carrier keeps), NOT because it was hard to land — and worth recording as the
#   one sub-behaviour of the modeled operation this battery cannot reach.
# RE-AIMED (admiss-fresh-unsafe-item -> admiss-obligation-satisfiable-at-f2p-shape):
#   an earlier revision of this file dropped the lane as VACUOUS, on the grounds
#   that the `pre-conditions` region is EMPTY so there is no precondition to admit,
#   and that `escSeq items` is total so the obligation is "satisfiable everywhere
#   by construction". That reasoning is REJECTED under audit. An empty `require` is
#   not the reason the lane is vacuous — the analogue on a total carrier is the
#   obligation being unsatisfiable or DEGENERATE at exactly an F2P-shaped input,
#   and "total, therefore satisfiable" is an argument the manifest never
#   demonstrated. The lane is now carried by a positive that discharges the
#   obligation AT a concrete F2P-shaped input by EVALUATION, as two `have`s, before
#   closing the frozen obligation verbatim — satisfiability (`hsat`) and
#   non-degeneracy in the mark observable (`hdisc`). Dropping it silently had
#   removed one of the three directions this gate exists to test.
# VACUOUS (2 frame-mutation rivals): the sibling carries both as MANDATORY
#   because the element and the sequence are held at fractional read permission
#   and a rival can illegally write through them. This backend is referentially
#   transparent and declares no `mut` binder — `items` is an immutable value with
#   no heap footprint — so there is no read-only input to overwrite and no
#   substitute probe. Not fabricated.
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
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-references == the real callees); this bundle consumes no axiom
#   `ensures`, and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `items : List Elem`, with two per-element observables, and a single top-level
#   clause `out = escSeq items` carrying five independent sub-obligations. Each
#   sub-obligation is attacked by at least one rival (safe-passthrough,
#   transform-on-unmarked, arity, order, per-code-point content x3), the whole
#   obligation is defended by three positives, and its satisfiability at an
#   F2P-shaped point by the admissibility case. The seven reject witnesses probe
#   seven DISTINCT input points, so every observable is genuinely varied:
#     - `items.length`: 1 (five witnesses) and 2 (arity, order);
#     - `Elem.safe`: true (transform-marked), false (five witnesses), and MIXED
#       within a single input (order, admissibility) — so no rival could mishandle
#       only the marked sub-domain, only the unmarked one, or only a heterogeneous
#       sequence and still slip through;
#     - `Elem.chars`: three distinct significant code points across witnesses
#       (the two near-misses each at their OWN distinguishing code point, so
#       neither claims a sub-domain the manifest does not demonstrate), AND
#       `chars.length` > 1 — a three-code-point element with the significant code
#       point in the MIDDLE (weak-first-code-point-only, plus the admissibility
#       case). That last variation was ADDED UNDER AUDIT and is not cosmetic: with
#       every witness at a single-code-point element, the battery was blind to a
#       rival expanding only the LEADING code point, which is definitionally equal
#       to `escSeq` on all six of the previous witnesses' inputs. The per-position
#       sub-domain is now demonstrated rather than claimed.
#   No two rivals share a witness and no two witnesses coincide: pts = 7 distinct
#   input points across 7 reject cases.
#   Not probed: the EMPTY sequence. `escSeq [] = []` and every rival here also
#   returns `[]` there (the maps and `take` all collapse), so no rival is wrong at
#   that input and a witness there could not discriminate — it is a point the
#   clause fixes trivially, not an unattacked binder value.
# WITNESS DISCRIMINATION (INDEPENDENTLY re-derived under audit with real builds,
#   all seven reject cases, every exit code observed rather than argued): each
#   witness ELABORATES against its loop-free rival (exit 0 — the extracted program
#   reduces to a literal that provably differs from `escSeq` at the probed input).
#   The second half is checked against the `witness_reference`, NOT gold: each
#   witness exits 1 there with ``Tactic `decide` proved that the proposition
#   ¬[condEscape ...] = escSeq [...] is false`` — a SEMANTIC refutation naming the
#   concrete input. The FORGERY test (flip the claim: `≠` -> `=`, asserting the
#   rival AGREES with the spec at that input) was run against the reference for
#   every case and exits 0 — so the reference-side exit code TRACKS the claim and
#   is admissible evidence, which is the property that separates a real
#   discriminator from a hollow one.
#   Gold cannot serve, and this was measured rather than assumed: against the
#   frozen solution the real refutation AND the flipped-claim forgery fail with the
#   BYTE-IDENTICAL error (`failed to synthesize Decidable ¬(NonDetT.run do let r ←
#   forIn Lean.Loop.mk ...)`), so gold's exit code carries no information about the
#   claim and a forged witness asserting gold is CORRECT there would have been
#   recorded as a refutation. That is why the earlier gold-side attestation is
#   withdrawn and the `witness_reference` is load-bearing. No witness binds a hypothesis (the carrier is fully
#   transparent), so there is no joint-satisfiability obligation and no
#   `witness-inconsistent` risk. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears in any variant or witness, no
#   variant adds a theorem or lemma beyond the frozen set, and every variant keeps
#   the `prove_correct escapeEach` header. Each reject rival was ALSO re-checked
#   with the proof retuned to a bare `loom_solve` and still fails with the
#   `ensures_1: out = escSeq items` goal open, so no rejection rests on the frozen
#   tactic script breaking on a reshaped impl.
AXIOM_TESTS = []
