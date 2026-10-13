# properties.py — PBT falsification battery for sympy__sympy-18698 (lean).
#
# NOT a Lean module: a manifest of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each case is a full Solution.lean
# variant built by region-surgery that edits ONLY the impl region (and, where a
# reshaped impl needs it, the proof body), so the frozen spec (axioms / pure /
# post-conditions, including the module docstring) stays byte-identical,
# same_spec holds by construction, and the `theorem correct_combineFactors`
# STATEMENT is preserved verbatim. No case introduces sorry / admit /
# native_decide / axiom, no case adds a helper lemma beyond the frozen set, and
# no case weakens the obligation.
#
# ---------------------------------------------------------------------------
# PORT NOTE — carrier narrowing vs the nagini sibling
# ---------------------------------------------------------------------------
# The nagini battery contracts TWO functions over a mutable-list carrier: a
# membership scan and a two-phase consolidation loop, each with fractional read
# permissions on its inputs. This Lean bundle models the SAME consolidation on a
# purely functional carrier — a single `List (Int × Nat)` of (factor,
# multiplicity) pairs mapped to the consolidated list — and models only ONE
# obligation, `correct_combineFactors`. The membership scan is not a separate
# modeled function here (`List.dedup` is the carrier's own primitive), and there
# is no permission system to violate. So the port is deliberately narrower than
# nagini's ten cases; see the OMITTED list below and `assessment`.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (the spec this battery attacks)
# ---------------------------------------------------------------------------
# `problem_spec_combineFactors factors result` is a conjunction of THREE
# independent top-level clauses, and the battery attacks each of them:
#
#   (1) `(result.map Prod.snd).Nodup`
#         each multiplicity is reported at most once — the CONSOLIDATION
#         dimension. Attacked by rivals that report a multiplicity twice.
#
#   (2) `∀ k, k ∈ result.map Prod.snd ↔ k ∈ factors.map Prod.snd`
#         the reported multiplicities are exactly the input's — nothing dropped
#         (the → direction) and nothing invented (the ← direction). Attacked in
#         BOTH directions by separate rivals, since a rival wrong in only one
#         direction would slip past a battery that probed only the other.
#
#   (3) `∀ p k, (p, k) ∈ result → p = prodOf factors k`
#         the value accompanying a reported multiplicity is the product of
#         EXACTLY the input factors carrying it — the VALUE dimension, and the
#         one the failing test grades. Attacked by rivals that record the wrong
#         value while reporting the right multiplicities.
#
# The spec's only INPUT binder is `factors` (`result` is always applied as
# `implementation_combineFactors factors`, so it is determined). Since the whole
# discriminating content lives in that one binder, "varying the binders" means
# varying `factors` across genuinely different SHAPES, which the ten reject
# witnesses do:
#
#   [(2,1),(3,1)]        two contributions sharing a multiplicity (a group of 2)
#   [(2,3),(3,3)]        the same shape at a NON-1 shared multiplicity
#   [(7,4)]              a singleton group whose factor differs from its multiplicity
#   [(5,2)]              a second singleton, at a different (factor, multiplicity)
#   [(11,5)]             a singleton at the HEAD position (position-sensitivity)
#   [(9,7)]              a singleton whose multiplicity is far from 0
#   [(2,1),(3,2)]        two contributions with DISTINCT multiplicities, used
#                        twice: once against a rival that DROPS a multiplicity,
#                        once against one whose group absorbs the higher one
#   [(2,1),(3,1),(5,2)]  a group of 2 alongside a singleton group (mixed)
#   [(2,1),(2,1)]        a group whose two contributions are EQUAL — the only
#                        shape where counting with vs. without repetition differs
#
# so group size (1 vs 2 vs mixed), the shared-multiplicity value (1 vs 3),
# whether the multiplicity column has duplicates, whether the FACTOR column has
# duplicates, whether a group's product coincides with its multiplicity or with
# any single member, and the length of the input (1, 2, 3) are all moved rather
# than held fixed. In particular no
# witness lets a rival hide behind an accidental coincidence: at [(7,4)] the
# product (7) differs from the multiplicity (4); at [(11,5)] the product (11)
# differs from the empty product (1); at [(2,1),(3,1),(5,2)] the group product
# (6) differs from every individual member (2, 3).
#
# ---------------------------------------------------------------------------
# OMITTED nagini cases and why
# ---------------------------------------------------------------------------
#   * The FRAME / permission-mutation class (nagini's three
#     `frame-mutate-readonly-*` rivals, which write into a read-only input list
#     held at a fractional read share) is VACUOUS on this backend. Lean is
#     referentially transparent: there is no aliasing, no fractional permission,
#     and no way for an implementation to write into its argument. There is no
#     counterpart rival to author and no substitute was fabricated.
#   * The nagini rivals attached to the MEMBERSHIP-SCAN function
#     (`frame-mutate-readonly-occurs-xs`) have no counterpart: this bundle does
#     not model that helper as a separate contracted function, so there is no
#     obligation for such a rival to attack.
#   * The ADMISSIBILITY positive IS carried — see `admiss-f2p-shaped-inputs`
#     below. (An earlier draft of this manifest dropped it on the ground that the
#     frozen obligation carries no precondition hypothesis, so there was "nothing
#     to prove usable". That reason is wrong: on a TOTAL carrier the analogue of
#     PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at an F2P-shaped
#     input — a spec no implementation could meet there would still pass every
#     uniqueness case, since those only ask that WRONG impls be rejected. The
#     positive below discharges `problem_spec_combineFactors` at two concrete
#     F2P-shaped inputs by evaluation, as `have`s, before closing the frozen
#     obligation verbatim, which tests that directly.) What genuinely has no
#     counterpart is nagini's LENGTH-MATCH half of the precondition: this bundle
#     carries the (factor, multiplicity) pairing in a single list of pairs, so a
#     length mismatch between two parallel lists is unstatable — the pairing is
#     discharged by typing rather than by a precondition.
#   * The DIVERGENCE / non-termination class is a KNOWN HOLE, not a vacuous
#     class. An earlier draft of this manifest recorded it as vacuous on the
#     ground that "a non-terminating rival cannot be written at all" since the
#     impl is a total Lean `def`. That reason is measurably WRONG, and it was
#     re-measured with real builds rather than argued: an impl whose `while`
#     guard is never falsified (a counter that the body never advances) is
#     admissible surgery inside the impl region — it passes `variant_problems`
#     clean and it ELABORATES (build exit 0 with the proof region emptied), both
#     for a dead loop and for a live one whose result depends on the loop. Lean
#     admits it because `while` in `Id.run do` desugars through the `Lean.Loop`
#     `forIn` instance, which is a `partial def`; no decreasing measure is
#     demanded of the surgery, and `partial` is not an assumption token.
#     What is genuinely unavailable is a WITNESS, and that is why the case is not
#     shipped. A `partial def` is opaque to the KERNEL, so the diverging impl's
#     applied term never reduces: a witness of the shape every case below uses
#     fails against the diverging rival with
#       `Tactic decide failed ... its Decidable instance instDecidableNot did not
#        reduce to isTrue or isFalse ... reduction got stuck`
#     i.e. it fails on the half that must SUCCEED, so the gate would record
#     `witness-undecided` — an inconclusive outcome, never a refutation. A
#     `witness_reference` does not reach this: it substitutes the GOLD side of
#     the two-build check, and the blocked side here is the rival's. Nor is a
#     spec hole hiding behind it: the diverging impl does NOT verify against the
#     frozen obligation (build exit 1), so the spec is not admitting it
#     vacuously — the rejection simply cannot be attributed to the spec by a
#     witness, which is what makes this a hole in the BATTERY rather than a
#     finding on the spec. Recorded as a hole so the incompleteness stays
#     visible instead of reading as coverage.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job, and this bundle
#     ships no consumed axiom (`meta.axioms == []`). The consolidation is modeled
#     deeply — the accompanying value is spelled out as `prodOf`, a fold over the
#     matching input pairs — so there is no opaque callee contract to probe, and
#     no opaque term blocks any witness.
from pathlib import Path

INSTANCE = "sympy__sympy-18698"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — every one lies ENTIRELY inside the impl or proof region of
# the frozen Solution.lean and is unique in the file, so a rewritten anchor is a
# loud AssertionError rather than a silent no-op.
# ---------------------------------------------------------------------------

# The whole impl-region body (everything under `Id.run do`).
_IMPL_BODY = """    let mut result : List (Int × Nat) := []
    for k in (factors.map Prod.snd).dedup do
      let mut prod : Int := 1
      for fk in factors do
        if fk.2 = k then
          prod := prod * fk.1
      result := result ++ [(prod, k)]
    return result
"""

# The loop that enumerates which multiplicities get reported.
_KEY_LOOP = "    for k in (factors.map Prod.snd).dedup do\n"

# The inner loop that accumulates a reported multiplicity's accompanying value.
_INNER_FOR = "      for fk in factors do\n"

# The accumulation step of that inner loop.
_INNER_STEP = "          prod := prod * fk.1\n"

# The single line that records one consolidated entry.
_APPEND = "      result := result ++ [(prod, k)]\n"

# The frozen proof body, verbatim (proof region contents, markers exclusive).
# Only the two soundness positives touch it, and each must REPROVE the same
# `theorem correct_combineFactors` statement for its reshaped impl.
_GOLD_PROOF = _BASE.split("-- proof-start\n")[1].split("-- proof-end")[0]
if _BASE.count(_GOLD_PROOF) != 1:
    raise AssertionError("proof region text is not unique — re-sync anchors")


# ===========================================================================
# SOUNDNESS POSITIVE #1 — inner loop over the FILTERED sublist.
# Instead of walking every contribution and testing its multiplicity inside the
# loop, walk only the matching contributions: the guard moves out of the loop
# body and into the collection being iterated. Same accompanying value, a
# genuinely different loop shape — and one whose inner induction lemma is now
# stated over an unguarded fold, so the proof is REWRITTEN, not carried over.
# Every `theorem correct_combineFactors` statement byte is preserved.
# ===========================================================================
_POS_FILTER_IMPL = """    let mut result : List (Int × Nat) := []
    for k in (factors.map Prod.snd).dedup do
      let mut prod : Int := 1
      for fk in factors.filter (fun fk => fk.2 = k) do
        prod := prod * fk.1
      result := result ++ [(prod, k)]
    return result
"""

_POS_FILTER_PROOF = """/-- The inner loop folds the listed factors' products onto the accumulator;
generalised over the accumulator and over the list so it reduces to
`List.foldl`. -/
theorem inner_combineFactors_helper
    (xs : List (Int × Nat)) (init : Int) :
    (Id.run (forIn xs init (fun fk r =>
        (pure (ForInStep.yield (r * fk.1)) : Id (ForInStep Int)))))
    = xs.foldl (fun acc fk => acc * fk.1) init := by
  induction xs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    simp [ih]

/-- The outer loop appends one `(prodOf factors k, k)` entry per multiplicity;
generalised over the accumulator so it reduces to a `List.map`. -/
theorem outer_combineFactors_helper
    (factors : List (Int × Nat)) (ks : List Nat) (init : List (Int × Nat)) :
    (Id.run (forIn ks init (fun k r =>
        (do
          let prod ← (forIn (factors.filter (fun fk => fk.2 = k)) (1:Int) (fun fk r =>
              (pure (ForInStep.yield (r * fk.1)) : Id (ForInStep Int))))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat)))))))
    = init ++ ks.map (fun k => (prodOf factors k, k)) := by
  induction ks generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [show (forIn (factors.filter (fun fk => fk.2 = a)) (1:Int) (fun fk r =>
              (pure (ForInStep.yield (r * fk.1)) : Id (ForInStep Int))))
        = Id.run (forIn (factors.filter (fun fk => fk.2 = a)) (1:Int) (fun fk r =>
              (pure (ForInStep.yield (r * fk.1)) : Id (ForInStep Int)))) from rfl]
    rw [inner_combineFactors_helper, ih]
    simp [prodOf, List.map_cons]

/-- Closed form of the imperative implementation. -/
theorem hbody_combineFactors (factors : List (Int × Nat)) :
    implementation_combineFactors factors
      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by
  unfold implementation_combineFactors
  simp only [Id.run]
  -- bridge the desugared body (`do pure PUnit.unit; …`) to the clean helper body
  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let r_1 ← (forIn (factors.filter (fun fk => fk.2 = k)) (1:Int) fun fk r =>
              (do pure PUnit.unit; pure (ForInStep.yield (r * fk.1)) : Id (ForInStep Int)))
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [(r_1, k)])) : Id (ForInStep (List (Int × Nat)))))
      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>
        (do
          let prod ← (forIn (factors.filter (fun fk => fk.2 = k)) (1:Int) fun fk r =>
              (pure (ForInStep.yield (r * fk.1)) : Id (ForInStep Int)))
          pure (ForInStep.yield (r ++ [(prod, k)])) : Id (ForInStep (List (Int × Nat))))) := rfl
  rw [h2]
  simp only [bind_pure]
  show (Id.run _ : List (Int × Nat)) = _
  rw [outer_combineFactors_helper]
  simp

theorem correct_combineFactors :
    ∀ (factors : List (Int × Nat)),
      problem_spec_combineFactors factors (implementation_combineFactors factors) := by
  intro factors
  have key : (implementation_combineFactors factors).map Prod.snd
      = (factors.map Prod.snd).dedup := by
    rw [hbody_combineFactors, List.map_map]
    exact List.map_id _
  refine ⟨?_, ?_, ?_⟩
  · -- multiplicity column is `Nodup` (it is a `dedup`)
    rw [key]; exact (factors.map Prod.snd).nodup_dedup
  · -- the result's multiplicities are exactly the input's
    intro k; rw [key]; exact List.mem_dedup
  · -- each entry's factor is the product of the matching inputs
    intro p k hmem
    rw [hbody_combineFactors] at hmem
    simp only [List.mem_map] at hmem
    obtain ⟨k', _, hk'⟩ := hmem
    rw [Prod.ext_iff] at hk'
    obtain ⟨hp, hk⟩ := hk'
    simp only at hp hk
    rw [← hp, ← hk]
"""

_POS_FILTER = _swap(_swap(_BASE, _IMPL_BODY, _POS_FILTER_IMPL),
                    _GOLD_PROOF, _POS_FILTER_PROOF)


# ===========================================================================
# SOUNDNESS POSITIVE #2 — consolidated entries emitted in the OPPOSITE order.
# The spec declares the result order to be outside the contract (it is pinned as
# a set: `Nodup` on the multiplicity column, set-membership, and a per-entry
# value law), so reversing the enumeration of the distinct multiplicities must
# still satisfy it. This is the sharpest positive available here: it is exactly
# the reshape the spec's order-independence claim is ABOUT, so if it cannot
# verify then the postcondition secretly pins an order it says it does not
# (SPEC-TOO-STRONG). The proof is reworked accordingly — the closed form now
# ends in `.reverse`, and the `Nodup` / membership bullets go through
# `List.nodup_reverse` / `List.mem_reverse`.
# ===========================================================================
_POS_REV = _swap(_BASE, _KEY_LOOP,
                 "    for k in (factors.map Prod.snd).dedup.reverse do\n")
_POS_REV = _swap(
    _POS_REV,
    "      = (factors.map Prod.snd).dedup.map (fun k => (prodOf factors k, k)) := by\n"
    "  unfold implementation_combineFactors",
    "      = (factors.map Prod.snd).dedup.reverse.map (fun k => (prodOf factors k, k)) := by\n"
    "  unfold implementation_combineFactors")
_POS_REV = _swap(
    _POS_REV,
    "  have h2 : (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>",
    "  have h2 : (forIn (factors.map Prod.snd).dedup.reverse ([] : List (Int × Nat)) fun k r =>")
_POS_REV = _swap(
    _POS_REV,
    "      = (forIn (factors.map Prod.snd).dedup ([] : List (Int × Nat)) fun k r =>",
    "      = (forIn (factors.map Prod.snd).dedup.reverse ([] : List (Int × Nat)) fun k r =>")
_POS_REV = _swap(
    _POS_REV,
    """  have key : (implementation_combineFactors factors).map Prod.snd
      = (factors.map Prod.snd).dedup := by""",
    """  have key : (implementation_combineFactors factors).map Prod.snd
      = (factors.map Prod.snd).dedup.reverse := by""")
_POS_REV = _swap(
    _POS_REV,
    """  · -- multiplicity column is `Nodup` (it is a `dedup`)
    rw [key]; exact (factors.map Prod.snd).nodup_dedup
  · -- the result's multiplicities are exactly the input's
    intro k; rw [key]; exact List.mem_dedup""",
    """  · -- multiplicity column is `Nodup` (a reordering of a `dedup`)
    rw [key, List.nodup_reverse]; exact (factors.map Prod.snd).nodup_dedup
  · -- the result's multiplicities are exactly the input's
    intro k; rw [key, List.mem_reverse]; exact List.mem_dedup""")


# ===========================================================================
# ADMISSIBILITY POSITIVE — the obligation is SATISFIABLE at F2P-shaped inputs.
# The frozen obligation is unconditional, so there is no precondition
# hypothesis to prove usable. On a total carrier the analogue of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly the
# shapes the failing test grades: a `problem_spec_combineFactors` that no
# implementation could discharge there would still pass every uniqueness case
# (those only require WRONG impls to be rejected) and every soundness case
# stated over the general `∀`. This positive rules that out by DISCHARGING the
# spec predicate at two concrete inputs — by evaluation, as `have`s — before
# closing the frozen `theorem correct_combineFactors` verbatim. Both `have`s
# are stated as the spec predicate itself, so neither can be satisfied by a
# restatement: `decide` must actually evaluate the implementation and the
# three clauses at those inputs.
#
# The two inputs mirror the two shapes the report is about: a group of two
# contributions sharing one multiplicity (which must consolidate to a single
# entry carrying their product), and a mixed input where two singleton groups
# sit alongside a group of two at a higher multiplicity.
# ===========================================================================
_ADMISS_INTRO = "  intro factors\n  have key :"

_ADMISS = _swap(_BASE, _ADMISS_INTRO, """  -- The obligation is satisfiable at the shapes the reported example is
  -- about: it is discharged HERE, at concrete inputs, by evaluation.
  have hA : implementation_combineFactors [((2 : Int), 1), ((3 : Int), 1)]
      = [((6 : Int), 1)] := by decide
  have _admissible_group_of_two :
      problem_spec_combineFactors [((2 : Int), 1), ((3 : Int), 1)]
        (implementation_combineFactors [((2 : Int), 1), ((3 : Int), 1)]) := by
    rw [hA]
    refine ⟨by decide, ?_, ?_⟩
    · intro k; simp
    · intro p k hmem
      simp only [List.mem_singleton, Prod.mk.injEq] at hmem
      obtain ⟨hp, hk⟩ := hmem
      subst hp; subst hk
      decide
  have hB : implementation_combineFactors
      [((2 : Int), 1), ((3 : Int), 2), ((5 : Int), 3), ((7 : Int), 3)]
      = [((2 : Int), 1), ((3 : Int), 2), ((35 : Int), 3)] := by decide
  have _admissible_mixed :
      problem_spec_combineFactors
        [((2 : Int), 1), ((3 : Int), 2), ((5 : Int), 3), ((7 : Int), 3)]
        (implementation_combineFactors
          [((2 : Int), 1), ((3 : Int), 2), ((5 : Int), 3), ((7 : Int), 3)]) := by
    rw [hB]
    refine ⟨by decide, ?_, ?_⟩
    · intro k; simp only [List.map_cons, List.map_nil, List.mem_cons,
        List.not_mem_nil, or_false]; tauto
    · intro p k hmem
      simp only [List.mem_cons, List.not_mem_nil, or_false, Prod.mk.injEq] at hmem
      rcases hmem with ⟨hp, hk⟩ | ⟨hp, hk⟩ | ⟨hp, hk⟩ <;>
        subst hp <;> subst hk <;> decide
""" + _ADMISS_INTRO)


# ===========================================================================
# UNIQUENESS rivals — each is a WRONG implementation of the modeled behavior,
# built by surgery inside the impl region only (the frozen proof body is left
# untouched, so its failure to build is expected and is NOT the evidence — the
# `witness` is).
# ===========================================================================

# #1 — no consolidation at all: hand back the contributions untouched.
_REJ_PASSTHROUGH = _swap(_BASE, _IMPL_BODY, "    return factors\n")

# #2 — record the MULTIPLICITY in the value slot instead of the group product.
_REJ_MULT_AS_VALUE = _swap(_BASE, _APPEND,
                           "      result := result ++ [((k : Int), k)]\n")

# #3 — off-by-one in the accompanying value.
_REJ_OFFBY = _swap(_BASE, _APPEND, "      result := result ++ [(prod + 1, k)]\n")

# #4 — the value's product skips the FIRST contribution of the whole input, so
# any group containing it loses that member.
_REJ_DROP_HEAD = _swap(_BASE, _INNER_FOR, "      for fk in factors.tail do\n")

# #5 — consolidate the VALUES but not the REPORTING: emit one entry per
# contribution, so a shared multiplicity is reported once per member.
_REJ_NO_DEDUP = _swap(_BASE, _KEY_LOOP, "    for k in factors.map Prod.snd do\n")

# #6 — drop the first distinct multiplicity from the report entirely.
_REJ_DROP_FIRST_KEY = _swap(_BASE, _KEY_LOOP,
                            "    for k in (factors.map Prod.snd).dedup.tail do\n")

# #7 — report a positional range of multiplicities instead of the ones that
# actually occur, inventing multiplicities no contribution carries.
_REJ_RANGE_KEYS = _swap(_BASE, _KEY_LOOP,
                        "    for k in List.range factors.length do\n")

# #8 — report the right multiplicities, but accompany each with a single
# REPRESENTATIVE member of its group rather than the product of the group.
_REJ_REPRESENTATIVE = _swap(_BASE, _INNER_STEP, "          prod := fk.1\n")

# #9 — the value's product walks the DEDUPED contributions, so a group holding
# two EQUAL contributions counts that contribution once instead of twice. Agrees
# with the desired behavior on every input whose pairs are pairwise distinct,
# which is every other witness input in this battery — a sub-domain none of the
# rivals above reaches.
_REJ_DEDUP_CONTRIBS = _swap(_BASE, _INNER_FOR, "      for fk in factors.dedup do\n")

# #10 — the grouping test is widened from `=` to `≥`, so a group absorbs every
# contribution at a HIGHER multiplicity as well as its own. Reports exactly the
# right multiplicities, each once, so it is invisible to both reporting clauses;
# it is also correct on every SINGLE-multiplicity input, which is where five of
# the witnesses above sit.
_REJ_GUARD_GE = _swap(_BASE, "        if fk.2 = k then\n",
                      "        if fk.2 ≥ k then\n")


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate's own negation at ONE concrete
# input, then discharges it through the offending clause with `decide` on a
# closed literal. Every one has been built both ways: it ELABORATES against its
# rival and FAILS against the frozen solution (with `decide` reporting that the
# proposition is false — i.e. gold genuinely satisfies the spec there, not a
# parse error). No witness binds anything, so none can be inconsistent.
# ---------------------------------------------------------------------------

def _w_nodup(lst):
    """Refute clause (1): the multiplicity column has a duplicate."""
    return (f"example : ¬ problem_spec_combineFactors {lst}\n"
            f"    (implementation_combineFactors {lst}) := by\n"
            "  intro h\n"
            "  exact absurd h.1 (by decide)\n")


def _w_member(lst, k):
    """Refute clause (2): multiplicity `k` is on exactly one side."""
    return (f"example : ¬ problem_spec_combineFactors {lst}\n"
            f"    (implementation_combineFactors {lst}) := by\n"
            "  intro h\n"
            f"  exact absurd (h.2.1 {k}) (by decide)\n")


def _w_value(lst, p, k):
    """Refute clause (3): the entry `(p, k)` is reported but `p ≠ prodOf`."""
    return (f"example : ¬ problem_spec_combineFactors {lst}\n"
            f"    (implementation_combineFactors {lst}) := by\n"
            "  intro h\n"
            f"  exact absurd (h.2.2 {p} {k} (by decide)) (by decide)\n")


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # ---------------- SOUNDNESS POSITIVES ----------------------------------
    {
        "id": "pos-control-filtered-inner-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FILTER,
        "rationale": (
            "A structurally-different but CORRECT implementation: the inner "
            "accumulation walks only the matching contributions (the "
            "multiplicity test moves out of the loop body and into the "
            "collection being iterated) instead of walking every contribution "
            "and testing inside. The accompanying value is unchanged, but the "
            "loop shape is not, so the inner induction lemma is restated over "
            "an unguarded fold and the proof is genuinely REWRITTEN rather than "
            "carried over — the `theorem correct_combineFactors` statement is "
            "byte-identical and closes with no new lemma, no axiom and no "
            "sorry. It must verify against all three clauses; if a faithful "
            "correct reshape of the accumulation cannot satisfy them, the "
            "postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-reversed-report-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REV,
        "rationale": (
            "The sharpest available positive: it emits the consolidated entries "
            "in the OPPOSITE order. The spec explicitly declines to pin the "
            "order — it states the result as a set (`Nodup` on the multiplicity "
            "column, set-membership both ways, and a per-entry value law) — so "
            "this reshape is correct by the spec's own account and MUST verify. "
            "If it cannot, the postcondition secretly constrains an order it "
            "claims not to (SPEC-TOO-STRONG), which would also mean the "
            "downstream re-ordering the contract relies on is not actually "
            "admissible. The proof is reworked for the new closed form (the "
            "`Nodup` and membership bullets now route through the "
            "reverse-invariance of each), keeping the obligation statement "
            "byte-identical."
        ),
    },

    # ---------------- ADMISSIBILITY ----------------------------------------
    {
        "id": "admiss-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The frozen obligation is unconditional, so there is no precondition "
            "hypothesis to prove usable — but the PRECOND-TOO-STRONG direction "
            "still has a counterpart on a total carrier: the obligation being "
            "UNSATISFIABLE at exactly the input shapes the failing test grades. "
            "A `problem_spec_combineFactors` that no implementation could "
            "discharge at those shapes would still pass every uniqueness case "
            "(those only demand that WRONG impls be rejected) and every "
            "soundness case stated over the general `∀`, so nothing else in this "
            "battery detects it. This case discharges the spec predicate ITSELF "
            "at two concrete in-domain inputs, by evaluation, as `have`s, before "
            "closing the frozen `theorem correct_combineFactors` byte-identically "
            "and with no new lemma, axiom or sorry. The inputs are the two shapes "
            "the report is about: `[(2,1),(3,1)]`, where two contributions share "
            "one multiplicity and must consolidate to the single entry (6, 1) "
            "carrying their product; and `[(2,1),(3,2),(5,3),(7,3)]`, where two "
            "singleton groups sit alongside a group of two at a higher "
            "multiplicity, consolidating to [(2,1),(3,2),(35,3)]. Because each "
            "`have` is the spec predicate applied to a literal, it cannot be "
            "satisfied by a restatement: `decide` must evaluate the "
            "implementation and all three clauses there. If either `have` cannot "
            "close, the postcondition is unsatisfiable on realistic input and the "
            "verdict is PRECOND-TOO-STRONG."
        ),
    },

    # ---------------- UNIQUENESS: clause (1), consolidation ----------------
    {
        "id": "weak-no-consolidation-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_PASSTHROUGH,
        "refinement": (
            "The literal un-consolidated behavior: the contributions are handed "
            "back exactly as received. A faithful patch that skipped the "
            "consolidation would report two separate entries for the two "
            "contributions that share a multiplicity, where the failing test "
            "demands a SINGLE entry pairing that multiplicity with the product "
            "of both — so it would not resolve, and a verifying rival here "
            "would be a true verify-does-not-resolve break. This is the "
            "canonical rival: it is precisely the behavior the reported example "
            "complains about."
        ),
        "rationale": (
            "Rejected by clause (1) `(result.map Prod.snd).Nodup`: at "
            "`[(2,1),(3,1)]` both contributions carry multiplicity 1, so an "
            "un-consolidated result repeats 1 in the multiplicity column and "
            "the Nodup conjunct is false. The witness discharges exactly that "
            "conjunct. (Clause (3) also fails here, but clause (1) is the "
            "cheapest closed refutation.)"
        ),
        "witness": _w_nodup("[(2, 1), (3, 1)]"),
    },
    {
        "id": "weak-report-once-per-contribution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NO_DEDUP,
        "refinement": (
            "A near-miss that consolidates the VALUES but not the REPORTING: "
            "each entry does carry the correct product of its whole group, but "
            "one entry is emitted per contribution rather than per distinct "
            "multiplicity. A faithful patch with this shape would report a "
            "shared multiplicity as many times as it occurs — two entries where "
            "the failing test demands one — so it would not resolve. Strictly "
            "closer to correct than the passthrough rival: it agrees with the "
            "desired behavior on every input whose multiplicities are already "
            "distinct, and is wrong only where one repeats."
        ),
        "rationale": (
            "Rejected by clause (1): the reporting loop enumerates the "
            "multiplicity column verbatim instead of its distinct values, so at "
            "`[(2,3),(3,3)]` the multiplicity 3 appears twice in the result's "
            "multiplicity column. Witnessed at a shared multiplicity of 3 — a "
            "DIFFERENT point from the passthrough rival's shared multiplicity of "
            "1, and one where this rival's values are right and only its "
            "reporting is wrong, so the witness demonstrates the sub-domain the "
            "rationale claims."
        ),
        "witness": _w_nodup("[(2, 3), (3, 3)]"),
    },

    # ---------------- UNIQUENESS: clause (2), both directions --------------
    {
        "id": "weak-drops-a-reported-multiplicity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DROP_FIRST_KEY,
        "refinement": (
            "Drops the first distinct multiplicity from the report entirely. A "
            "faithful patch losing one multiplicity group would omit an entry "
            "the failing test requires to be present (on the reported example it "
            "would drop the consolidated entry altogether), so it would not "
            "resolve. This attacks the DROPPING direction of the "
            "nothing-lost/nothing-invented clause; the range-keys rival attacks "
            "the complementary direction, and neither would be caught by a "
            "battery that probed only the other."
        ),
        "rationale": (
            "Rejected by clause (2) `∀ k, k ∈ result.map Prod.snd ↔ k ∈ "
            "factors.map Prod.snd`, → direction: at `[(2,1),(3,2)]` the "
            "multiplicity 1 occurs in the input but not in the result, so the "
            "biconditional at k = 1 is false. The witness is stated at an input "
            "with two DISTINCT multiplicities — a shape no other witness uses — "
            "so it probes the reporting of a genuinely multi-group input rather "
            "than a single group."
        ),
        "witness": _w_member("[(2, 1), (3, 2)]", 1),
    },
    {
        "id": "weak-invents-unoccurring-multiplicities",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_RANGE_KEYS,
        "refinement": (
            "Reports a POSITIONAL range of multiplicities rather than the ones "
            "that actually occur, so it both invents multiplicities no "
            "contribution carries (each accompanied by an empty product) and "
            "loses any multiplicity beyond the input's length. A faithful patch "
            "keyed on positions instead of on the observed multiplicities would "
            "emit spurious entries and drop real ones, so it would not resolve. "
            "Attacks the INVENTING direction of the clause."
        ),
        "rationale": (
            "Rejected by clause (2), ← direction: at `[(9, 7)]` the rival "
            "reports multiplicity 0 (the only position index), which occurs "
            "nowhere in the input's multiplicity column, so the biconditional at "
            "k = 0 is false. The witness holds a multiplicity (7) far from any "
            "position index, which is what separates the invented value from a "
            "real one — a witness at a multiplicity that happened to equal its "
            "own index would not discriminate."
        ),
        "witness": _w_member("[(9, 7)]", 0),
    },

    # ---------------- UNIQUENESS: clause (3), the value dimension ----------
    {
        "id": "weak-multiplicity-in-value-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_MULT_AS_VALUE,
        "refinement": (
            "Puts the multiplicity itself where the accompanying product "
            "belongs. A faithful patch pairing each multiplicity with itself "
            "would report the exponent in the factor position, so the failing "
            "test — which grades the exact merged value — would still fail. It "
            "would not resolve."
        ),
        "rationale": (
            "Rejected by clause (3) `∀ p k, (p, k) ∈ result → p = prodOf "
            "factors k`: at `[(7, 4)]` the rival reports the entry (4, 4) while "
            "the product of the multiplicity-4 group is 7. The witness input is "
            "deliberately chosen so the factor (7) and the multiplicity (4) "
            "DIFFER — at an input where they coincided this rival would agree "
            "with the spec and the witness would not discriminate."
        ),
        "witness": _w_value("[(7, 4)]", 4, 4),
    },
    {
        "id": "weak-offby-one-in-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_OFFBY,
        "refinement": (
            "An off-by-one in the accompanying value: the correct group product "
            "shifted by one. A faithful patch with this arithmetic slip would "
            "report a value one away from the merged factor the failing test "
            "asserts, so it would not resolve. Wrong nowhere near vacuously — "
            "it is wrong at EVERY reported multiplicity, which is what makes it "
            "the tightest possible probe of how precisely the value is pinned: "
            "if it verified, the value would be unpinned to within one."
        ),
        "rationale": (
            "Rejected by clause (3): at `[(5, 2)]` the rival reports (6, 2) "
            "while the product of the multiplicity-2 group is 5. Witnessed at a "
            "distinct (factor, multiplicity) point from the other value rivals, "
            "and one where the reported value (6) is neither the multiplicity "
            "nor any member of the group — so the refutation is attributable to "
            "the arithmetic shift specifically."
        ),
        "witness": _w_value("[(5, 2)]", 6, 2),
    },
    {
        "id": "weak-value-omits-head-contribution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DROP_HEAD,
        "refinement": (
            "The value's product skips the input's FIRST contribution, so every "
            "group containing it loses that member. A faithful patch whose "
            "per-group product omitted a member would report a strictly smaller "
            "merged value than the failing test asserts (on the reported example "
            "it would drop the leading factor from the merged product), so it "
            "would not resolve."
        ),
        "rationale": (
            "Rejected by clause (3): at `[(11, 5)]` the sole contribution IS the "
            "head, so the group is skipped entirely and the rival reports the "
            "empty product (1, 5) where the product of the multiplicity-5 group "
            "is 11. Witnessed at a SINGLETON input, which is the point that "
            "separates this rival from the representative-value rival — the "
            "latter is correct on singletons and only wrong on groups of two or "
            "more, so the two do not share a witness."
        ),
        "witness": _w_value("[(11, 5)]", 1, 5),
    },
    {
        "id": "weak-value-is-group-representative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_REPRESENTATIVE,
        "refinement": (
            "The subtlest value rival: it reports exactly the right "
            "multiplicities, each once, and accompanies each with a member of "
            "its group — just the last one rather than the product of all of "
            "them. A faithful patch that picked a representative instead of "
            "combining would keep one contribution per multiplicity and discard "
            "the rest, so the failing test's merged value (the product of the "
            "whole group) would not appear and it would not resolve. It is a "
            "genuine near-miss: it agrees with the desired behavior on every "
            "input whose multiplicities are all distinct, and diverges only "
            "where a group has two or more members — so it is not caught by any "
            "reporting-dimension probe."
        ),
        "rationale": (
            "Rejected by clause (3): at `[(2,1),(3,1),(5,2)]` the rival reports "
            "(3, 1) — the last member of the multiplicity-1 group — while the "
            "product of that group is 6. The witness is stated at a MIXED input "
            "(a group of two alongside a singleton group) so the discriminating "
            "point is a genuine multi-member group; the input's singleton group "
            "is handled correctly by this rival, which is exactly why its "
            "witness must sit at the group of two and not at a singleton."
        ),
        "witness": _w_value("[(2, 1), (3, 1), (5, 2)]", 3, 1),
    },
    {
        "id": "weak-value-counts-equal-contributions-once",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DEDUP_CONTRIBS,
        "refinement": (
            "The value's product walks the DEDUPED contributions, so a group "
            "holding two EQUAL contributions counts that contribution once "
            "instead of twice. A faithful patch that de-duplicated the group "
            "before combining would report a strictly smaller merged value "
            "wherever one factor is repeated at a multiplicity — the merged "
            "value the failing test asserts is the product of every "
            "contribution carrying that multiplicity, counted with repetition — "
            "so it would not resolve. The tightest near-miss in the battery: it "
            "agrees with the desired behavior on every input whose (factor, "
            "multiplicity) pairs are pairwise DISTINCT, which is every other "
            "witness input here, so no other case reaches its wrong sub-domain."
        ),
        "rationale": (
            "Rejected by clause (3) `∀ p k, (p, k) ∈ result → p = prodOf "
            "factors k`: at `[(2,1),(2,1)]` the rival reports (2, 1) while "
            "`prodOf` folds BOTH matching pairs and gives 4. The witness input "
            "is the repeated-contribution shape specifically — the only shape "
            "that separates this rival from the frozen behavior, which is why "
            "it appears in no other case. Verified by hand-built pair: the "
            "witness elaborates against this rival and `decide` refutes the "
            "same membership claim against the frozen solution "
            "(`(2, 1) ∈ implementation_combineFactors [(2, 1), (2, 1)]` is "
            "false), and the flipped claim inverts both exit codes."
        ),
        "witness": _w_value("[(2, 1), (2, 1)]", 2, 1),
    },
    {
        "id": "weak-group-absorbs-higher-multiplicities",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_GUARD_GE,
        "refinement": (
            "The grouping test is widened from equality to `≥`, so each group "
            "absorbs every contribution at a HIGHER multiplicity as well as its "
            "own. A faithful patch that grouped by a threshold instead of by "
            "the multiplicity itself would fold foreign contributions into a "
            "group's merged value, so the failing test's merged value — the "
            "product of exactly the contributions AT that multiplicity — would "
            "not appear and it would not resolve. Invisible to both reporting "
            "clauses: it reports exactly the right multiplicities, each once. "
            "It is also correct on every input carrying just ONE distinct "
            "multiplicity, which is where five of the witnesses above sit, so "
            "its wrong sub-domain needs at least two distinct multiplicities."
        ),
        "rationale": (
            "Rejected by clause (3): at `[(2,1),(3,2)]` the rival reports "
            "(6, 1) — it folds the multiplicity-2 contribution into the "
            "multiplicity-1 group — while `prodOf factors 1` is 2. This is the "
            "clause-(3) direction none of the other value rivals attacks: the "
            "others report a value that is too SMALL or arithmetically shifted, "
            "whereas this one includes contributions the group must EXCLUDE, so "
            "it probes that `prodOf` filters to `fk.2 = k` and not merely that "
            "it folds the matching pairs. Verified by hand-built pair: the "
            "witness elaborates against this rival and `decide` refutes "
            "`(6, 1) ∈ implementation_combineFactors [(2, 1), (3, 2)]` against "
            "the frozen solution, and the flipped claim inverts both exit codes."
        ),
        "witness": _w_value("[(2, 1), (3, 2)]", 6, 1),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job, and this bundle ships no consumed axiom
# (`meta.axioms == []`). The consolidation is modeled deeply — the value
# accompanying a multiplicity is spelled out as a fold over the matching input
# pairs — so there is no opaque callee whose contract a probe could validate.
AXIOM_TESTS = []
