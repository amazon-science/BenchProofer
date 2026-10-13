"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-9288 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct selectBest`` obligation survives). ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method that decides the reported OUTCOME of
running one independent attempt per per-attempt key and keeping the best-scoring
one:

  selectBest (keys altKeys : List Key) (runFor : Key → Run) return (out : Option Run)
    ensures out = bestOverKeys runFor keys

``bestOverKeys`` is a total, fully-unfolded pure function (the ``axioms`` region
declares nothing — no opaque answer key): a left fold of ``consider`` over the
CANONICAL key sequence, seeded ``none``. ``consider`` replaces the running
incumbent exactly when there is no incumbent yet OR the next attempt scores
STRICTLY lower; a tie keeps the earlier incumbent (first-wins). The single
``ensures`` pins the result to that fold, so the unique satisfier IS the grounded
selection — evaluating ``bestOverKeys`` over ``keys`` is the correct answer, and
there is no wrong echo to build (the honest cheapest-reshape positives stand in
for a positive). ``runFor`` is a FREE input (the unchanged per-attempt routine),
carried with no behavioural claim: the spec holds for every function it could be.

The load-bearing behaviours ``bestOverKeys`` / ``consider`` compose, each
independently attackable through the two binders of the post-image
(``runFor`` and ``keys``):
  * the attempts must be driven by the CANONICAL key sequence — never by the
    other key sequence that happens to be in scope (the modeled defect);
  * the incumbent is the STRICTLY-lower-scoring attempt (an argmin, not argmax);
  * ties keep the EARLIER attempt (strict ``<``, first-wins — not ``≤``);
  * EVERY key is folded (completeness — no attempt silently dropped).

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling reasons
    about read-only heap inputs held at fractional permission; here Lean/Velvet
    is referentially transparent, every parameter is an immutable value, the
    method declares no ``mut`` binder on any input, and there is no heap or
    aliasing. There is no read-only input to overwrite and no permission system
    to trip, so the class is vacuous. No substitute fabricated (per the porting
    map). The sibling's "the source must not be mutated" obligation is
    structurally guaranteed by the ABSENCE of a ``mut`` binder.
  * NON-TERMINATION / DIVERGENCE - CLOSED BY THE SEMANTICS, not a spec hole. This
    bundle is declared TOTAL correctness (``loom.semantics.termination "total"``,
    with a ``decreasing`` measure on the frozen loop), and the option cannot drift
    from the file's ``open TotalCorrectness DemonicChoice``, because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Under ``total`` a
    postcondition is claimed of ALL runs, not only terminating ones, and the
    verifier demands a decreasing measure on every loop. An earlier version of this
    bullet said a diverging impl "cannot be written at all"; it CAN be written, and
    it is REJECTED when it is. Measured on this bundle with the proof reduced to a
    bare ``loom_solve``: an unmeasured spun loop is refused at elaboration
    (``Decreasing annotations are required in total correctness semantics``), and the
    sharper shape that CARRIES a measure which does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. Legitimately dropped, not fabricated, and not a spec hole.
    (The same bullet used to contrast a cohort of 401 ``partial`` velvet bundles
    from an internal findings doc. That cohort no longer exists: all 500 velvet
    bundles set ``"total"``, so the contrast is withdrawn and the conclusion rests on
    the builds above.)
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``bestOverKeys runFor keys`` computed entirely by a concrete
    ``def`` chain in the ``pure`` region over the method's own inputs. There is no
    value an echo could carry that satisfies the ensures yet is behaviourally
    wrong.
  * WRONG-SEQUENCE / VALUE / PARTIAL-DOMAIN — heavily exercised. The selection
    surface has sub-domains a rival can get right on most inputs yet diverge on:
    driving the wrong key sequence (the F2P scenario), the argmin direction, the
    first-wins tie-break, and completeness of the fold.

WITNESS MECHANICS on this carrier. The spec is a ``method`` CONTRACT, not a bare
predicate, so a witness reaches it through Velvet's tester machinery. The
post-image ranges over ``Option Run`` and ``Run`` carries a ``Rat`` score with no
kernel ``DecidableEq``; the witness therefore first ``deriving instance
DecidableEq for Run`` (a decidability instance it brings into scope for its OWN
``decide``; appended to BOTH the rival file and the gold file, so it exists on
both sides by construction — it is not a spec change and declares no
theorem/lemma/axiom). The frozen impl is a ``while`` loop whose tester elaborates
to a partial fixpoint the kernel does not reduce, so gold's tester is STUCK (not
false) at every input — which is exactly what makes each witness FAIL against the
frozen solution, the gate's discrimination half. Each reject rival is written
STRAIGHT-LINE (an inline ``keys.foldl`` / ``keys.dropLast.foldl`` / a bare
``bestOverKeys … altKeys``), so ITS tester reduces and ``decide`` settles it; the
witness states ``selectBestTester <args> = false`` at a concrete point (small Int
keys, explicit ``Rat`` literal scores) where the rival's outcome violates the
ensures while the frozen outcome satisfies it. Both halves were checked
out-of-band with ``scripts/lean_verify.sh`` for every reject case: the witness
ELABORATES against its rival and FAILS against the frozen solution. No ``sorry``
/ ``admit`` / ``native_decide`` / ``axiom``.

AXIOM lane: EMPTY. ``mapping.md`` §3 records no consumed ``axiom`` and no
A-reference deep model — the selection rule is modeled deeply in the ``pure``
region and the unchanged attempt routine is folded into the free input
``runFor``. Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-9288"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole executable body (the selection loop). Lies
# ---- wholly inside the one impl region and is unique in Solution.lean; both
# ---- facts are asserted by _swap. Every impl-reshaping variant replaces this
# ---- block, so any drift of the frozen impl breaks the manifest loudly. ----
_IMPL = """    -- impl-start
    let mut best : Option Run := none
    let mut i := 0
    while i < keys.length
      invariant i ≤ keys.length
      invariant best = (keys.take i).foldl (consider runFor) none
      done_with i = keys.length
      decreasing keys.length - i
    do
      let k := keys[i]!
      let r := runFor k
      best := match best with
        | none   => some r
        | some b => if r.score < b.score then some r else some b
      i := i + 1
    return best
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The single loop-body update line (a substring of _IMPL, unique in the file).
# Anchor for the loop-preserving positive control, which retunes only this line.
_STEP_LINE = """      let k := keys[i]!
      let r := runFor k
      best := match best with
        | none   => some r
        | some b => if r.score < b.score then some r else some b
      i := i + 1"""
assert _BASE.count(_STEP_LINE) == 1, "loop-body step lines drifted"

# The state initializer (unique). Anchor for the admissibility in-region assert.
_INIT = "    let mut best : Option Run := none\n"
assert _BASE.count(_INIT) == 1, "state initializer drifted"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its script without touching
# ---- the spec or dropping the obligation. Rivals leave it as-is (their
# ---- rejection is carried by the witness, not the tactic script). ----
_PROOF = """prove_correct selectBest by
  loom_solve
  · have hi : i < keys.length := by omega
    rw [bestOverKeys_take_step runFor keys i hi, ← invariant_2]
    simp [consider]
  · have hlen : i = keys.length := done_1
    subst hlen
    rw [List.take_length] at invariant_2
    simp_all [bestOverKeys]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced (straight-
    line rivals; the frozen proof is kept as-is — the rejection is carried by
    the witness, and the reshaped body breaks the frozen tactic script exactly
    as the witness mechanics anticipate)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(body), _PROOF, proof)


# ---- witness preamble. `selectBestTester <args> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. There is no `require` clause, so the
# ---- precondition is `True` and decides trivially. The `deriving` line supplies
# ---- the `DecidableEq Run` the post-image's `Option Run` equality needs; it is
# ---- appended to both the rival and the gold witness build. ----
_TESTER = ("deriving instance DecidableEq for Run\n\n"
           "extract_program_for selectBest\n"
           "prove_precondition_decidable_for selectBest\n"
           "prove_postcondition_decidable_for selectBest\n"
           "derive_tester_for selectBest\n\n")


def _witness(args):
    return _TESTER + f"example : selectBestTester {args} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the identical `prove_correct`
    # obligation; only the executable surface and (where needed) the tactic
    # script move.
    # =====================================================================
    {
        "id": "pos-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the modeled selection
        # directly. Observationally identical (the loop's post-state IS
        # `bestOverKeys runFor keys`), so the ensures holds definitionally; the
        # tactic script is retuned to `loom_solve` alone because the no-loop
        # body leaves none of the loop-invariant goals the frozen script closes.
        "module": _impl_reproved(
            "    return bestOverKeys runFor keys",
            "prove_correct selectBest by\n  loom_solve"),
        "rationale": "returning the modeled selection directly satisfies "
                     "`out = bestOverKeys runFor keys` definitionally; a correct "
                     "loop-free reshape must verify, else SPEC-TOO-STRONG on the "
                     "loop form. Proof retuned (`loom_solve` alone) since the "
                     "no-loop body emits none of the loop-invariant VCs.",
    },
    {
        "id": "pos-loop-body-let",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the stepped incumbent to a local before assigning it,
        # keeping the SAME loop, SAME invariants and SAME accumulator.
        # Definitionally identical, so the frozen loop-invariant proof discharges
        # unchanged.
        "module": _swap(
            _BASE, _STEP_LINE,
            "      let k := keys[i]!\n"
            "      let r := runFor k\n"
            "      let stepped := match best with\n"
            "        | none   => some r\n"
            "        | some b => if r.score < b.score then some r else some b\n"
            "      best := stepped\n"
            "      i := i + 1"),
        "rationale": "hoisting the per-key step into a `let` before the mutation "
                     "computes the SAME incumbent on every iteration, so the "
                     "ensures still discharges with the frozen invariants and the "
                     "frozen tactic script; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the loop body's exact form.",
    },

    # =====================================================================
    # ADMISSIBILITY. The method carries NO `require` clause, so the sibling's
    # "a normal (non-negative) count satisfies the precondition" probe is
    # degenerate (every input is in-domain). The residual admissibility risk on
    # a total-domain spec is that the post-image is DEGENERATE at the interesting
    # points — a spec no impl distinguishes reads exactly like one every impl
    # meets. This case discharges an in-region assert pinning that `bestOverKeys`
    # genuinely distinguishes its two central behaviours: the argmin (the
    # strictly-lower-scoring attempt is kept) and the first-wins tie-break (on
    # equal scores the EARLIER attempt is kept). The rest of the impl is kept
    # verbatim so the method's own obligation still discharges; the proof is
    # retuned to also close the assert.
    # =====================================================================
    {
        "id": "admiss-selection-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `nd\n"
                "      (bestOverKeys (fun k => if k = (0:Int) then { score := 5, payload := 0 } else { score := 7, payload := 1 }) [0, 1]\n"
                "         = some { score := 5, payload := 0 } ∧\n"
                "       bestOverKeys (fun k => if k = (0:Int) then { score := 5, payload := 2 } else { score := 5, payload := 3 }) [0, 1]\n"
                "         = some { score := 5, payload := 2 }))\n"
                + _INIT),
            _PROOF,
            "prove_correct selectBest by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (refine ⟨?_, ?_⟩ <;> simp [bestOverKeys, consider] <;> decide)\n"
            "    | (have hi : i < keys.length := by omega\n"
            "       rw [bestOverKeys_take_step runFor keys i hi, ← invariant_2]\n"
            "       simp [consider])\n"
            "    | (have hlen : i = keys.length := done_1\n"
            "       subst hlen\n"
            "       rw [List.take_length] at invariant_2\n"
            "       simp_all [bestOverKeys])"),
        "rationale": "the post-image is satisfiable AND non-degenerate: "
                     "`bestOverKeys` genuinely distinguishes its two central "
                     "behaviours — the strictly-lower-scoring attempt is kept "
                     "(argmin: over scores 5 then 7 the reported best has score "
                     "5), and on a tie the EARLIER attempt is kept (first-wins: "
                     "over two equal-scored attempts the reported best carries "
                     "the first one's payload). The in-region assert must "
                     "discharge (else the selection would be constant / the "
                     "obligation degenerate); the impl is kept verbatim so the "
                     "ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is written
    # straight-line so its tester reduces under `decide`.
    # =====================================================================
    {
        "id": "weak-drive-altkeys",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch defect: the attempts are driven by the OTHER key
        # sequence in scope (`altKeys`) instead of the canonical `keys`.
        "module": _impl("    return bestOverKeys runFor altKeys"),
        "refinement": "this IS the reverted pre-patch behaviour: the "
                      "single-thread selection is driven by the per-attempt key "
                      "sequence implicitly produced by re-passing the one live "
                      "source into each attempt, rather than the canonical "
                      "up-front per-attempt key sequence the parallel branch "
                      "consumes. The two sequences agree only by accident, so a "
                      "faithful real patch with this seeding feeds the "
                      "single-thread and multi-thread strategies DIFFERENT "
                      "per-attempt keys; the best-scoring kept attempt can then "
                      "differ between the two strategies, so "
                      "test_result_of_kmeans_equal_in_diff_n_jobs's "
                      "assert_array_equal over the two strategies FAILS. NOT "
                      "resolved.",
        "rationale": "REJECT from the ensures: the post-image pins the report to "
                     "the best over runs keyed by the CANONICAL `keys`, but the "
                     "rival reports the best over runs keyed by `altKeys`. When "
                     "the two sequences select different-scoring attempts these "
                     "differ. Verifying would be SPEC-TOO-WEAK. Refuted at "
                     "keys=[0], altKeys=[1], runFor 0↦score 5 / 1↦score 7 (the "
                     "only witness where keys and altKeys differ).",
        "witness": _witness(
            "[ (0:Int) ] [ (1:Int) ] "
            "(fun k => if k = (0:Int) then { score := (5:Rat), payload := 0 } "
            "else { score := (7:Rat), payload := 1 })"),
    },
    {
        "id": "weak-argmax-direction",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the HIGHER-scoring attempt: an argmax instead of the argmin.
        "module": _impl(
            "    return keys.foldl (fun acc k =>\n"
            "      let r := runFor k\n"
            "      match acc with\n"
            "      | none => some r\n"
            "      | some b => if b.score < r.score then some r else some b) none"),
        "refinement": "a counterpart that kept the WORST-scoring attempt (max "
                      "objective) rather than the best would report a "
                      "deliberately poor clustering for the single-thread "
                      "strategy, disagreeing with the argmin-of-objective the "
                      "parallel strategy reports; the two strategies then keep "
                      "different results and the F2P equality FAILS. NOT resolved.",
        "rationale": "REJECT from the ensures: `bestOverKeys` keeps the STRICTLY "
                     "lower score (argmin), but the rival keeps the higher. Over "
                     "keys=[0,1] with scores 5 then 7 the spec reports score 5, "
                     "the rival score 7. Refuted at keys=[0,1], runFor 0↦5 / 1↦7.",
        "witness": _witness(
            "[ (0:Int), (1:Int) ] [ ] "
            "(fun k => if k = (0:Int) then { score := (5:Rat), payload := 0 } "
            "else { score := (7:Rat), payload := 1 })"),
    },
    {
        "id": "weak-tie-last-wins",
        "kind": "uniqueness",
        "expect": "reject",
        # Uses `≤` where the spec uses strict `<`: a later attempt with an
        # EQUAL score wrongly displaces the earlier one (last-wins on a tie).
        "module": _impl(
            "    return keys.foldl (fun acc k =>\n"
            "      let r := runFor k\n"
            "      match acc with\n"
            "      | none => some r\n"
            "      | some b => if r.score <= b.score then some r else some b) none"),
        "refinement": "a counterpart replacing the incumbent on an EQUAL score "
                      "(`inertia <= best_inertia`) rather than strictly lower "
                      "would keep the LAST tied attempt in the single-thread "
                      "strategy; the parallel strategy's argmin keeps the FIRST "
                      "tied attempt. On any input with a tie for the best "
                      "objective the two strategies keep different results and "
                      "the F2P equality FAILS. NOT resolved.",
        "rationale": "REJECT from the ensures: `consider` replaces only on a "
                     "STRICTLY lower score, so a tie keeps the EARLIER attempt "
                     "(first-wins), but the rival (`<=`) keeps the later. Over "
                     "keys=[0,1] with equal scores but distinct payloads the "
                     "spec reports the first payload, the rival the second. "
                     "Refuted at keys=[0,1], runFor 0↦{5,0} / 1↦{5,1} (the only "
                     "witness with a tied score and distinct payloads).",
        "witness": _witness(
            "[ (0:Int), (1:Int) ] [ ] "
            "(fun k => if k = (0:Int) then { score := (5:Rat), payload := 0 } "
            "else { score := (5:Rat), payload := 1 })"),
    },
    {
        "id": "weak-drop-last-attempt",
        "kind": "uniqueness",
        "expect": "reject",
        # Folds over all-but-last key: the final attempt is never run, so a
        # best that lives at the last key is missed (incomplete fold).
        "module": _impl("    return keys.dropLast.foldl (consider runFor) none"),
        "refinement": "a counterpart that ran one fewer attempt than the count "
                      "(dropping the last per-attempt key) would explore a "
                      "strictly smaller set of restarts in the single-thread "
                      "strategy than the parallel strategy runs; when the omitted "
                      "restart is the argmin the two strategies keep different "
                      "results and the F2P equality FAILS. NOT resolved.",
        "rationale": "REJECT from the ensures: `bestOverKeys` folds over ALL of "
                     "`keys`, but the rival drops the last. Over keys=[0,1] with "
                     "the unique best at the last key (scores 7 then 5) the spec "
                     "reports score 5, the rival (folding only [0]) reports score "
                     "7. Refuted at keys=[0,1], runFor 0↦7 / 1↦5.",
        "witness": _witness(
            "[ (0:Int), (1:Int) ] [ ] "
            "(fun k => if k = (0:Int) then { score := (7:Rat), payload := 0 } "
            "else { score := (5:Rat), payload := 1 })"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness) plus an AXIOM lane. The sibling
# contracts `restart_seeds(config, n_restarts) -> List[int]` and pins its result
# to the @Pure front-recursive draw fold `seed_vector` — modeling the
# GENERATION of the per-restart seed vector. This velvet bundle narrows the
# carrier to a DIFFERENT slice of the same patch: the per-attempt SELECTION loop
# (`selectBest`, pinned to `bestOverKeys runFor keys`), which reports the best
# attempt over the runs keyed by the canonical sequence. The seed-vector-fold
# surface the sibling attacks (constant / shift / partial-last / length) is not
# modeled here at all; what IS modeled is which key sequence drives the loop and
# how the incumbent is chosen. This is carrier narrowing (Lean-family bundles
# model only the purely functional core) — parity with the sibling's case list
# is NOT the target; coverage of the modeled surface is.
#
#   sibling case                   -> here                              disposition
#   -----------------------------------------------------------------------------
#   pos-localvar-reshape           -> pos-loop-body-let                 PORTED (reshaped)
#   pos-cheapest-named-val         -> pos-direct-fold                   PORTED (reshaped)
#   admiss-nonneg-count            -> admiss-selection-nondegenerate    RE-AIMED
#   atk-constant-live-source       -> weak-drive-altkeys                RE-EXPRESSED
#   atk-shift-advance-first        -> (none)                            N/A on carrier
#   atk-partial-last-element       -> weak-drop-last-attempt (partial)  RE-EXPRESSED
#   atk-length-shortfall           -> weak-drop-last-attempt (length)   RE-EXPRESSED
#   (no sibling / carrier-widening)-> weak-argmax-direction             ADDED
#   (no sibling / carrier-widening)-> weak-tie-last-wins                ADDED
#   AXIOM_TESTS (2)                -> (none)                            DROPPED (G-AX lane)
#
# 2 positives ported (reshaped), 1 admissibility re-aimed, 3 uniqueness rivals
# ported/re-expressed, 2 uniqueness rivals added; 1 sibling rival N/A on carrier;
# axiom lane dropped.
#
# RE-EXPRESSED (weak-drive-altkeys <- atk-constant-live-source): the sibling's
#   pre-patch rival reuses the one live source across restarts, collapsing the
#   generated seed vector to a constant. On THIS carrier the same pre-patch bug
#   surfaces as driving the SELECTION loop over the accidental `altKeys` (the
#   sequence implicitly produced by that live-source reuse) instead of the
#   canonical `keys`. It is the direct velvet counterpart of the sibling's
#   headline pre-patch rival, refuted at the one witness where keys != altKeys.
# N/A ON CARRIER (atk-shift-advance-first): the shift rival perturbs HOW the seed
#   vector advances (draw at advance(state) before state). This carrier does not
#   model seed generation — `runFor` is a free input and `keys` is given — so
#   "advance before draw" has no counterpart. The analogous selection-loop
#   perturbations (wrong sequence, argmin direction, tie-break, completeness) are
#   attacked instead; a shift of an abstract given `keys` list is not a wrong
#   IMPLEMENTATION of `selectBest`, so no discriminating witness exists and it is
#   dropped rather than fabricated.
# RE-EXPRESSED (weak-drop-last-attempt <- atk-partial-last-element + atk-length-
#   shortfall): the sibling's partial-domain rival mis-seeds the LAST restart and
#   its length rival drops the last restart. On this carrier both collapse to the
#   same modeled defect: fold over all-but-last key, so the final attempt is
#   never run. It is refuted at a witness whose UNIQUE best lives at the dropped
#   last key, which is exactly the partial-domain hole (trivially correct when
#   the best is not last, so a fuzzer that never places the min last would miss
#   it). One rival covers both siblings on this carrier.
# ADDED (weak-argmax-direction, weak-tie-last-wins): the sibling's seed-vector
#   surface has no selection rule to attack, so the argmin DIRECTION and the
#   first-wins TIE-BREAK — both load-bearing clauses of `consider` on this
#   carrier, and both directly tied to the F2P n_jobs-invariance observable — are
#   new attacks the sibling could not express. The tie rival is the only witness
#   with a tied score, exercising the strict-`<` first-wins clause the argmin
#   rival cannot reach.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the TWO binders of the
#   sole post-image `bestOverKeys runFor keys` (pts = 4 distinct input points):
#     keys    — [0] (drive-altkeys) and [0,1] (argmax, tie, drop-last): varied
#               (singleton vs pair; the singleton is where keys != altKeys).
#     runFor  — every rival supplies a DISTINCT score function: {0↦5,1↦7}
#               (drive-altkeys, argmax), {0↦5,1↦5} distinct payloads (tie),
#               {0↦7,1↦5} best-at-last (drop-last). The score assignment, the
#               tie structure and which key carries the min are all varied, so no
#               rival is refuted at a point another rival's runFor also covers.
#   `altKeys` is an input to the METHOD but NOT a binder of the post-image
#   predicate `bestOverKeys runFor keys`; the drive-altkeys rival is nonetheless
#   the ONLY witness where altKeys differs from keys, which is what makes the
#   wrong-sequence violation observable.
#   Every independent top-level behaviour `bestOverKeys`/`consider` composes is
#   attacked: which sequence drives the fold (drive-altkeys), the argmin
#   direction (argmax), the first-wins tie-break (tie), and completeness of the
#   fold (drop-last).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no A-reference deep model (the selection rule is modeled deeply in
# the pure region; the unchanged attempt routine is folded into the free input
# `runFor`), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
