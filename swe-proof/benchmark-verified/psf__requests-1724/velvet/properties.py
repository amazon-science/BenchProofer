"""properties.py — G-PBT falsification battery for psf__requests-1724 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct normalizeMethod`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and be
REFUTED against an impl known to satisfy the spec).

DEFENDED SURFACE (one contracted method, no ``require`` clauses):

  normalizeMethod (text : List Char) (native : Bool) return (out : TextToken)
    ensures out.chars = upperSeq text            -- CONTENT (load-bearing)
    ensures out.chars.length = text.length       -- LENGTH
    ensures out.native = true                     -- FLAVOUR (bug-sensing pin)

The method models the method-handling step of request construction: it is handed
a caller-supplied method name (``text``, its code-point content) and a boolean
recording the textual flavour the caller supplied (``native``), and returns the
``TextToken`` carried onward. Three independently-attackable ``ensures`` clauses:

  * CONTENT — ``out.chars = upperSeq text``. ``upperSeq`` is a fully-unfolded,
    front-recursive pure ``def`` over the method's OWN argument (per-code-point
    ASCII upper map); the ``axioms`` region carries only the native-flavour stub,
    which does not appear in this clause, so there is no opaque answer key to
    echo (directive 8 — the post-image is grounded in the actual input). Attacked
    by identity / off-by-one content rivals.
  * LENGTH — ``out.chars.length = text.length``. Structural; the case
    normalisation is a length-preserving map. Attacked by a truncation rival.
  * FLAVOUR — ``out.native = true``. A literal constant that must hold
    IRRESPECTIVE of the ``native`` input. The only honest satisfier is to carry a
    native flavour; the behaviour the change removes is exactly carrying the
    SUPPLIED flavour through. Attacked by the flavour-echo rival at a non-native
    input.

TWO INPUT BINDERS, both free:
  * ``text``  — the supplied method's code points (contents and length matter);
  * ``native`` — the supplied flavour. It appears in NO ``ensures`` clause: the
    carried flavour must not depend on it. A rival that ECHOES it is refuted only
    at ``native = false`` — so that binder is discriminated by exactly the
    flavour-echo witness while every other witness holds it fixed at ``true``.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY THE REFUTATION SUBJECT IS NOT
GOLD. A witness reaches the post-image through Velvet's tester machinery
(``normalizeMethodTester text native = false`` says the extracted program's
result violates the postcondition at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block has been stripped so
no tactic script can mask the verdict. ``decide`` reduces the extracted program
by kernel computation, and the FROZEN impl is not reducible: it is a ``while``
loop whose fixpoint elaborates through ``Classical.choice`` under
``loom.semantics.choice "demonic"``, AND its first statement is the
native-flavour ``:|`` stub, a demonic choice the kernel cannot unfold either. So
``decide`` against the frozen impl is stuck for EVERY claim, true or false, and
its exit code carries no information at all — a failure there is NOT evidence
that a witness discriminates.

That is a real trap and it is what the previous revision of this battery fell
into: all four reject cases were recorded ``witness-undecided``. The witnesses
themselves were sound (each elaborates against its rival); what was missing was
a refutation SUBJECT that reduces. Two structural facts made the gate's own
automatic fallback — try the battery's ``expect="verify"`` positives as subjects
— unable to rescue them: every positive here carries either the loop or the
stub, so none of them reduces either.

The repair is an explicit ``witness_reference``: ``_WITNESS_REF`` below, a
LOOP-FREE and STUB-FREE impl that computes the post-image directly
(``upperSeq text`` with the flavour pinned by the literal ``true``). It shares
the frozen spec, it VERIFIES (the gate re-checks both before using it), and it
reduces — so ``decide`` against it returns a genuine verdict. Each witness was
confirmed by hand with two real builds to ELABORATE against its rival and to be
REFUTED against the reference with a real decision
(``Tactic `decide` proved that the proposition ... is false``), never a stuck
reduction. ``_WITNESS_REF`` also ships as its own ``expect="verify"`` case
(``pos-loopfree-literal-native``), so the battery itself records that
loop-freeness is not what any rival is being rejected for. The frozen spec is
untouched throughout, and each rival's divergence from the post-image is real at
the witnessed input.

ADVERSARIAL READ of the nagini classes:
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's two
    mandatory frame rivals write back into a read-only sequence input held at a
    fractional heap permission and must be rejected for INSUFFICIENT PERMISSION.
    This backend is referentially transparent: ``text`` is an immutable
    ``List Char`` value, the method declares no ``mut`` binder among the inputs,
    there is no heap and no aliasing. There is no read-only input to overwrite
    and no permission system to trip, so the class is vacuous. No substitute is
    fabricated (per the porting map, legitimately dropped here).
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE SEMANTICS, and therefore still
    not shipped as a reject case. This bundle sets
    ``loom.semantics.termination "total"`` AND opens ``TotalCorrectness`` (the
    ``open`` is what selects the scope: a bundle that sets ``"total"`` and then
    opens ``PartialCorrectness`` is checked as PARTIAL, since the later ``open``
    wins and both namespaces define ``WPGen.forWithInvariantLoop``). Under
    ``total`` the verifier demands a ``decreasing`` measure on every loop and a
    satisfiability witness for every ``:|`` statement, so a diverging or stuck
    impl is REJECTED rather than discharging the three ``ensures`` clauses
    vacuously. Measured on THIS bundle, one build each: splicing a diverging
    ``while spin > 0 do spin := spin`` prefix ahead of the frozen body is
    rejected outright with ``Decreasing annotations are required in total
    correctness semantics`` when it carries no measure, and rejected with
    ``unsolved goals case «decreasing_1: spin» ⊢ False`` when it carries the
    CONSTANT measure ``decreasing spin``; the byte-identical file with only
    ``open TotalCorrectness`` -> ``open PartialCorrectness`` VERIFIES, exit 0.
    (That last pair is also why the ``open`` and not the ``set_option`` is the
    load-bearing line: the ``set_option`` linter catches a MISSING measure under
    either scope, but only ``TotalCorrectness`` actually CHECKS one that is
    present -- ``PartialCorrectness.WPGen.forWithInvariantLoop`` takes the
    measure and discards it.) It stays out of the reject lane because the
    rejection is not attributable to the spec at a concrete input: it is a
    well-formedness / measure refusal, and no ``witness`` can be evaluated
    against an impl that does not terminate. See
    ``the corpus-wide termination-semantics finding`` for the corpus-level accounting of the hole
    this cell no longer has.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The content pin
    is ``upperSeq text`` (a fully-unfolded ``def`` over the method's argument) and
    the flavour pin is the literal ``true``; there is no opaque answer key to
    echo. The native-flavour ``:|`` stub is not an answer key — setting the
    flavour native IS the correct work (the honest positive controls do it).
  * CONTROL-FLOW-EFFECT — N/A. The method returns a pure ``TextToken`` and
    mutates nothing it is handed; there is no raise / side-effect channel invisible
    to the value abstraction.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets the shape
    right on part of the domain yet diverges on one clause (drop the upper map,
    skip the first element, truncate the length, or echo the supplied flavour).

AXIOM lane: the bundle carries one A-consumed callee (the native-flavour stub)
and one A-reference deep model (``upperSeq`` ↔ the case-normalisation callee),
both checked by axiom_check.py (G-AX). The nagini ``AXIOM_TESTS`` re-run those
soundness/containment probes; the G-PBT spec gate ignores ``AXIOM_TESTS``
regardless, so they are dropped here (they are G-AX's job).
"""
from pathlib import Path

INSTANCE = "psf__requests-1724"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the whole gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the elided impl region and unique in the file
# ---- (both facts asserted at load). Every rival and the direct-model positive
# ---- swap on this block.
_IMPL = """    -- impl-start
    -- Coerce the supplied method to the native text flavour FIRST, via the
    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
    -- whose produced value is native irrespective of the supplied flavour).
    let flavour :| flavour = true
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = upperSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := upperCp c :: result
      i := i - 1
    return { chars := result, native := flavour }
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- correct reshape may retune THIS block; rivals leave it as the flat
# ---- `loom_solve` so the wrong impl leaves the postcondition goal unsolved and
# ---- the rival MODULE fails to build (what expect="reject" needs). The witness,
# ---- not the module build, is what attributes the rejection to the spec.
# ----
# ---- TWO legs under `total` semantics (`open TotalCorrectness`), and which legs
# ---- exist is a function of the IMPL SHAPE, so each variant below retunes to the
# ---- shape its own impl produces:
# ----   * the `:|` stub's SATISFIABILITY goal `∃ h, h = true` — emitted for every
# ----     demonic-choice statement, so it is present iff the impl keeps the stub;
# ----   * the loop-body leg (`upperSeq_drop_step`) — present iff the impl keeps
# ----     the `while`, and its generated index is named `i_1` here because the
# ----     stub statement ahead of it takes the first auto-name (`i`). An impl that
# ----     drops the stub but keeps the loop names it `i` (see _PROOF_LOOP_I).
_PROOF_GOLD = """prove_correct normalizeMethod by
  loom_solve
  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
  -- statement must be shown to HAVE a value, so the method cannot discharge its
  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
  -- `true`, the value the real native-flavour constructor produces.
  · exact ⟨true, rfl⟩
  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
  -- stub above binds the first auto-name), and the goal is exactly
  -- `upperSeq_drop_step`.
  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
    simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a loop-free proof body: when the impl is a single expression there is no
# ---- loop invariant to peel, so `loom_solve` alone discharges the equality (for
# ---- a correct reshape) or leaves the goal unsolved (for the reject rivals,
# ---- where the build FAILS — which is the point). Reject rivals retune the proof
# ---- to this shape; they are all stub-free, so no satisfiability goal is
# ---- emitted either.
_PROOF_FLAT = "prove_correct normalizeMethod by\n  loom_solve"

# ---- the loop-free proof for an impl that KEEPS the `:|` stub: under `total` the
# ---- stub emits its own satisfiability goal (`∃ h, h = true`), which survives
# ---- `loom_solve` and must be witnessed, so a stub-carrying variant cannot use
# ---- the bare flat proof. Only the direct-model positive is that shape.
_PROOF_FLAT_STUB = ("prove_correct normalizeMethod by\n"
                    "  loom_solve\n"
                    "  exact ⟨true, rfl⟩")

# ---- the loop-based proof with the auto-named loop variable at `i` (not `i_1`):
# ---- removing the leading `:|` stub statement shifts Velvet's generated loop
# ---- index name by one, so a positive that keeps the loop but drops the stub
# ---- retunes the drop-step rewrite to name `i`.
_PROOF_LOOP_I = ("prove_correct normalizeMethod by\n"
                 "  loom_solve\n"
                 "  rw [upperSeq_drop_step text i (by omega) (by omega)]\n"
                 "  simp_all")


def _rewrite_impl(new_block, proof=_PROOF_FLAT):
    """Full variant: whole impl block replaced, proof retuned."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---------------------------------------------------------------------------
# THE REFUTATION SUBJECT (`witness_reference`) — see the CARRIER NOTE.
#
# A correct, LOOP-FREE and STUB-FREE impl of the frozen spec: it returns the
# grounded post-image `upperSeq text` directly and pins the flavour with the
# literal `true`. Three properties are what make it usable, and the gate
# re-checks the first two rather than trusting this comment:
#   (1) it shares the frozen spec (`variant_problems`);
#   (2) it VERIFIES — an impl that failed everything would refute every witness,
#       honest or forged, so an unverified reference is rejected;
#   (3) it REDUCES — no `while` fixpoint through `Classical.choice` and no `:|`
#       demonic choice, so `decide` against its extracted tester returns a real
#       verdict instead of getting stuck.
# The whole reject lane shares this one reference; the gate verifies it once.
# It also ships as `pos-loopfree-literal-native` below.
# ---------------------------------------------------------------------------
_WITNESS_REF = _rewrite_impl(
    "    -- impl-start\n"
    "    return { chars := upperSeq text, native := true }\n"
    "    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `normalizeMethodTester text native = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped. Every rival is a
# ---- loop-free, stub-free expression so `decide` reduces its extracted program,
# ---- and the refutation subject is `_WITNESS_REF` for the same reason.
def _witness(call):
    return ("extract_program_for normalizeMethod\n"
            "prove_precondition_decidable_for normalizeMethod\n"
            "prove_postcondition_decidable_for normalizeMethod\n"
            "derive_tester_for normalizeMethod\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. All verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model content
        # directly (no loop at all), still coercing the flavour via the native
        # stub so `out.native = true`. `out.chars` IS `upperSeq text`, so all
        # three clauses hold; the reproof drops the loop leg (no loop invariant
        # to peel) but KEEPS the stub's satisfiability witness, since the stub
        # statement is retained (_PROOF_FLAT_STUB).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let flavour :| flavour = true\n"
            "    return { chars := upperSeq text, native := flavour }\n"
            "    -- impl-end",
            proof=_PROOF_FLAT_STUB),
        "rationale": (
            "the cheapest honest correct impl returns the grounded content model "
            "`upperSeq text` directly (no loop), still routing the flavour through "
            "the native stub. `out.chars` IS `upperSeq text` so CONTENT holds, "
            "`upperSeq` preserves LENGTH, and the stub pins FLAVOUR native. A "
            "faithful reshape MUST verify, else the postcondition is over-fit to "
            "the loop code shape (SPEC-TOO-STRONG). Reproof is `loom_solve` plus "
            "the stub's satisfiability witness (the loop leg is gone, the stub "
            "leg is not)."),
    },
    {
        "id": "pos-literal-native",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole backward loop and both invariants, but reshapes the
        # FLAVOUR derivation: pass the literal `true` instead of routing through
        # the native-flavour stub. The FLAVOUR clause only requires
        # `out.native = true`, so `true` discharges it; content/length come from
        # the same verified fold. Dropping the leading stub statement shifts the
        # generated loop index name to `i`, so the drop-step rewrite is retuned.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let mut result : List Char := []\n"
            "    let mut i := text.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ text.length\n"
            "      invariant result = upperSeq (text.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := text[i - 1]!\n"
            "      result := upperCp c :: result\n"
            "      i := i - 1\n"
            "    return { chars := result, native := true }\n"
            "    -- impl-end",
            proof=_PROOF_LOOP_I),
        "rationale": (
            "a correct impl that satisfies the constant FLAVOUR pin "
            "`out.native = true` by the literal `true` (instead of consuming the "
            "native-flavour stub) and computes CONTENT via the same verified "
            "backward fold MUST verify. If it cannot, the spec would be "
            "SPEC-TOO-STRONG (forcing one particular flavour derivation). The loop "
            "and both invariants are kept; only the flavour source and the "
            "loop-index name in the reproof change."),
    },
    {
        "id": "pos-loopfree-literal-native",
        "kind": "soundness",
        "expect": "verify",
        # The `witness_reference` source, shipped as a case in its own right.
        # Two jobs: (a) an ordinary soundness positive — the fully reshaped
        # correct impl (no loop, no stub, flavour by literal) must verify; and
        # (b) it puts the reject lane's refutation subject under the gate's own
        # judgement inside the battery, so the manifest records that
        # loop-freeness is a property of a VERIFYING impl and therefore not what
        # any rival is being rejected for.
        "module": _WITNESS_REF,
        "rationale": (
            "the maximally reshaped correct impl: no loop, no native-flavour "
            "stub, CONTENT returned as the grounded model `upperSeq text` and "
            "FLAVOUR pinned by the literal `true`. All three clauses hold, so it "
            "MUST verify (else SPEC-TOO-STRONG). It is also the reject lane's "
            "`witness_reference`: shipping it as a case makes the battery itself "
            "record that this shape VERIFIES, so the reject cases refuted against "
            "it are being refuted by the spec and not by loop-freeness."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clauses, so the sibling's "a
    # normal F2P-shaped input satisfies the precondition" probe is degenerate
    # (every input is admitted). The residual admissibility risk on this total
    # domain is that the post-image is DEGENERATE at the interesting point — a
    # spec no impl distinguishes reads exactly like one every impl meets. This
    # case discharges an in-region `assert`, at a concrete F2P-shaped input (a
    # lowercase method name — the NON-native flavour the issue concerns), that
    # the post-image is NON-DEGENERATE there: the case-normalised content of
    # "post" is genuinely "POST" (not the identity) and the length is preserved.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof is retuned only to also clear the assert goal (the
    # `decide` arm). The assert is live (a false claim leaves an unsolved goal —
    # verified during authoring).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      upperSeq \"post\".toList = \"POST\".toList ∧\n"
                  "      (upperSeq \"post\".toList).length = (\"post\".toList).length))\n"),
            _PROOF_GOLD,
            "prove_correct normalizeMethod by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "input: a lowercase method name must case-normalise to its uppercase "
            "form (`upperSeq \"post\" = \"POST\"`, genuinely NOT the identity) with "
            "the length preserved. The in-region assert must discharge (else the "
            "obligation is degenerate at the point the change cares about — a "
            "non-native lowercase method); the impl is kept verbatim so the "
            "method's own `ensures` still discharges too."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a LOOP-FREE,
    # STUB-FREE expression so its extracted tester `decide`s, and each is refuted
    # against `_WITNESS_REF` rather than the frozen impl, which cannot decide
    # anything (see the CARRIER NOTE). Every witness was checked by hand with two
    # real builds: it ELABORATES against its rival, and against the reference it
    # is REFUTED by a real decision, not a stuck reduction.
    # =====================================================================
    {
        "id": "weak-identity-no-upper",
        "kind": "uniqueness",
        "expect": "reject",
        # Return a copy of the supplied content unchanged (drop the upper map).
        # Correct length and native flavour; verifies ONLY on the sub-domain with
        # no ASCII lowercase (where `upperSeq` is the identity).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { chars := text, native := true }\n"
            "    -- impl-end"),
        "refinement": (
            "a real patch that carried the method WITHOUT case-normalising it "
            "(dropping the upper map) sends a lowercase method (e.g. 'post' "
            "instead of 'POST'). HTTP method dispatch / the uppercase-scheme "
            "redirect handling and the failing tests that exercise method case "
            "would then diverge from gold, so this faithful impl would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the CONTENT clause `out.chars = upperSeq text`: for a "
            "lowercase input `out.chars = text ≠ upperSeq text`. The length and "
            "flavour clauses are satisfied, so verifying would be SPEC-TOO-WEAK "
            "(the case normalisation is unpinned). Refuted at a lowercase method "
            "name (\"post\", native = true)."),
        "witness": _witness('normalizeMethodTester "post".toList true'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-skip-first-upper",
        "kind": "uniqueness",
        "expect": "reject",
        # Case-normalise every position EXCEPT the first (leave the head raw).
        # Correct length and flavour, and correct content on every input whose
        # first code point is not lowercase; diverges only on the head whenever
        # the first character is lowercase.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let upped := match text with\n"
            "      | [] => []\n"
            "      | c :: cs => c :: upperSeq cs\n"
            "    return { chars := upped, native := true }\n"
            "    -- impl-end"),
        "refinement": (
            "a real patch that case-normalised all but the first character of the "
            "method ('pOST' from 'post') sends a malformed method; the carried "
            "request method would be wrong on lowercase-leading names, diverging "
            "from gold on the failing method-case tests. Not behaviourally equal "
            "to gold, would NOT resolve. (Pins that the CONTENT clause holds for "
            "EVERY position, not most positions.)"),
        "rationale": (
            "REJECT from the CONTENT clause `out.chars = upperSeq text`: "
            "`upperSeq` upper-maps the head like the rest, but the rival leaves it "
            "raw, so the lists disagree whenever the first character is lowercase. "
            "Verifying would be SPEC-TOO-WEAK. Refuted at \"ab\" (native = true), a "
            "distinct input point from the identity rival: this rival is the "
            "NEAR-MISS that agrees with gold everywhere except the head, so it is "
            "given a point where the head is the sole divergence."),
        "witness": _witness('normalizeMethodTester "ab".toList true'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-length-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no direct sibling): attacks the LENGTH clause. Case-normalise
        # correctly but DROP the first element of the result, so the carried
        # method is one code point short. Correct flavour; the length (and hence
        # content) clause fails on every non-empty input.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { chars := (upperSeq text).drop 1, native := true }\n"
            "    -- impl-end"),
        "refinement": (
            "a real patch that dropped a character while normalising the method "
            "sends a truncated method name (e.g. 'OST' from 'post'); every HTTP "
            "request would carry a wrong, shortened method and the failing tests "
            "that carry the method through would diverge from gold. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the LENGTH clause `out.chars.length = text.length`: "
            "dropping one element gives `text.length - 1 ≠ text.length` on any "
            "non-empty input (and the CONTENT clause too). The flavour clause is "
            "satisfied, so verifying would leave the LENGTH clause unpinned "
            "(SPEC-TOO-WEAK). Refuted at \"get\" (native = true) — a third "
            "distinct `text` point, and one with no lowercase-head dependence, so "
            "the length failure is what carries the refutation."),
        "witness": _witness('normalizeMethodTester "get".toList true'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-flavour-echo-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating defect: carry the SUPPLIED flavour
        # (native := native) instead of forcing the native flavour. Content and
        # length are exactly right; the only divergence is the flavour, and only
        # when the supplied flavour is non-native (native = false).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { chars := upperSeq text, native := native }\n"
            "    -- impl-end"),
        "refinement": (
            "this IS the pre-change behaviour: carry the SUPPLIED flavour instead "
            "of forcing the native flavour. A non-native supplied method then "
            "stays non-native and contaminates the byte-string header assembly "
            "downstream — the exact decoding error the issue reports. This is "
            "`Solution_prepatch.lean` and the failing behaviour; it does NOT "
            "resolve the F2P (G-DIFF)."),
        "rationale": (
            "REJECT from the FLAVOUR clause `out.native = true`: carrying the "
            "supplied `native` cannot prove `native = true` when `native = false`. "
            "Content and length are correct, so this isolates the flavour clause. "
            "Verifying would be SPEC-TOO-WEAK (the flavour would depend on the "
            "input the spec forbids it to depend on). Refuted at \"post\" with "
            "native = FALSE — the ONLY witness that varies the `native` binder off "
            "its default, the sub-domain where the pre-change defect is "
            "observable."),
        "witness": _witness('normalizeMethodTester "post".toList false'),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — 2 of which are the mandatory
# frame-mutation rivals) plus 4 AXIOM_TESTS, and a documented N/A
# control-flow-effect note. The sibling models the same method-normalisation
# step over a `List[int]` code-point carrier granted at a FRACTIONAL heap
# permission, with the content pinned by a verified backward `while` loop over a
# pure fold and the flavour derived from a consumed native-flavour axiom. This
# backend models the SAME purely-functional core over `List Char`
# (`upperSeq`/`upperCp`, the pure region) with the flavour pinned as the literal
# `out.native = true`; there is no permission surface and the content pin is a
# transparent `def` of `text`.
#
#   sibling case                 -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-control-literal-native   -> pos-literal-native                PORTED
#   pos-control-inline-elem      -> pos-direct-model                  PORTED (reshaped)
#   admiss-f2p-shaped            -> admiss-postimage-nondegenerate    RE-AIMED
#   frame-mutate-input-inplace   -> (none)                            VACUOUS
#   frame-append-input           -> (none)                            VACUOUS
#   partial-identity-no-upper    -> weak-identity-no-upper            PORTED
#   partial-skip-first-upper     -> weak-skip-first-upper             PORTED
#   flavour-echo-supplied        -> weak-flavour-echo-supplied        PORTED
#   (no sibling)                 -> weak-length-truncate              ADDED (clause cov.)
#   (no sibling)                 -> pos-loopfree-literal-native       ADDED (witness subj.)
#   control-flow-effect (N/A)    -> (none)                            N/A (documented)
#   (no sibling diverge case)    -> (none)                            CLOSED BY SEMANTICS
#   AXIOM_TESTS (x4)             -> (none)                            DROPPED (G-AX lane)
#
# 3 ported, 1 ported-reshaped, 1 re-aimed, 2 vacuous, 2 added; N/A documented;
# 1 class closed by the termination semantics; 4 axiom-lane dropped.
#
# PORTED (positives): pos-control-literal-native kept the backward loop and set
#   the flavour with the literal True -> pos-literal-native does exactly that
#   (`native := true`, loop kept, both invariants kept; the reproof is retuned
#   only because dropping the leading stub statement renames the generated loop
#   index). pos-control-inline-elem was a local reshape within the loop -> here
#   the cheapest structural reshape is to return the content model directly
#   (`upperSeq text`, no loop) while still coercing the flavour via the stub;
#   both keep all three clauses satisfied and verify (real builds).
# RE-AIMED (admissibility): the sibling establishes that a normal F2P-shaped
#   input meets the half-permission precondition. This method has NO `require`
#   clauses (every input is admitted), so that probe is degenerate; it is
#   re-aimed at the residual total-domain risk — that the post-image is
#   DEGENERATE at the interesting point — via an in-region assert that a
#   lowercase method ('post') case-normalises to 'POST' (genuinely not the
#   identity) with length preserved.
# PORTED (rivals): partial-identity-no-upper -> weak-identity-no-upper (drop the
#   upper map: CONTENT clause), partial-skip-first-upper -> weak-skip-first-upper
#   (leave the head raw: CONTENT clause, distinct near-miss point),
#   flavour-echo-supplied -> weak-flavour-echo-supplied (carry the supplied
#   flavour: FLAVOUR clause, the pre-change defect, refuted at native = false).
#   Each carries a machine-checked witness that ELABORATES against the rival and
#   is REFUTED against `_WITNESS_REF` by a real `decide` verdict.
# ADDED (weak-length-truncate): the sibling folds length into its content pin; on
#   this carrier `out.chars.length = text.length` is a distinct top-level clause,
#   so a truncation rival gives it its own attacker and clause coverage.
# ADDED (pos-loopfree-literal-native): the reject lane's `witness_reference`,
#   shipped as a soundness positive so the battery records that the refutation
#   subject VERIFIES — i.e. no rival is being rejected for loop-freeness.
# N/A (control-flow-effect): the sibling documents this class as N/A (the value
#   abstraction captures the whole externally-visible behaviour). Same here: the
#   method returns a pure `TextToken` and mutates nothing; no side-effect channel.
# VACUOUS (frame-mutation x2): the sibling's two MANDATORY frame rivals write /
#   grow a read-only sequence input held at half permission and must be rejected
#   for INSUFFICIENT PERMISSION. This backend is referentially transparent:
#   `text` is an immutable `List Char` value, the method declares no `mut` binder
#   among the inputs, there is no heap or aliasing. No read-only input to
#   overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated (porting map: vacuous here).
# CLOSED BY SEMANTICS (divergence): the sibling carries no `diverge-*` case, and
#   this bundle needs none: it sets `loom.semantics.termination "total"` and opens
#   `TotalCorrectness`, so every loop must carry a proven `decreasing` measure
#   (the frozen impl's is `decreasing i`) and every `:|` statement must be shown
#   satisfiable. A diverging impl is rejected for a missing/unproven measure
#   instead of satisfying the three `ensures` clauses vacuously, so the
#   verify-does-not-imply-resolve hole is not present. Still no reject case: the
#   rejection is a well-formedness refusal, not a refutation at a concrete input,
#   so there is nothing for a `witness` to decide.
# DROPPED (AXIOM_TESTS x4): the sibling's four AXIOM_TESTS re-run the
#   soundness/containment checks for the native-flavour axiom and the upper-map
#   deep model in Docker. This bundle carries the same two callees (the
#   native-flavour `:|` stub, A-consumed; and `upperSeq`, A-reference), both
#   checked by axiom_check.py under G-AX. The axiom lane is G-AX's job; this spec
#   gate ignores AXIOM_TESTS regardless, so they are dropped here.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 4 distinct input
# points):
#     text   — "post", "ab", "get", "post": contents and length varied.
#     native — true, true, true, FALSE: the flavour-echo rival is the sole case
#              that varies `native` off its default (to false), the only
#              sub-domain where a flavour-echoing impl is observable; every other
#              rival holds it at true. Its variant returns `native := native`, a
#              region whose value depends on the binder.
#   Every top-level `ensures` clause is attacked by some rival's rationale:
#     CONTENT (out.chars = upperSeq text)          — weak-identity-no-upper,
#                                                     weak-skip-first-upper;
#     LENGTH  (out.chars.length = text.length)     — weak-length-truncate;
#     FLAVOUR (out.native = true)                  — weak-flavour-echo-supplied.
#   No two rivals share an input tuple; the content rivals sit at different
#   points ("post" vs "ab") because the skip-first near-miss agrees with the
#   identity rival's shape only away from the head.
AXIOM_TESTS = []
