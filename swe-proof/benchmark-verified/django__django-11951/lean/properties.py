# properties.py — G-PBT falsification battery for django__django-11951 (lean).
#
# NOT a Lean module; a record of adversarial spec cases parsed by the G-PBT gate.
# Each case is a FULL Solution.lean variant with the FROZEN spec untouched: only
# the impl region body (and, for verifying cases, the proof body) is swapped, so
# `same_spec` holds by construction and the `theorem correct_splitBatches`
# STATEMENT is byte-identical across every case.
#
# Ported from the nagini sibling battery. IMPORTANT carrier note: the nagini
# bundle modeled only the scalar effective-batch-size selection
# (`effective_batch_size -> int`); THIS bundle models the whole batching
# behavior — it derives the effective per-batch size AND partitions the object
# list into the consecutive batches, returning `List (List α)`. So the spec here
# is a single total input→output relation
#
#     result = chunkBatches (effectiveBatchSize batchSize rawMax) objs
#
# over a fully TRANSPARENT carrier (`Nat` sizes, `List` objects — no opaque
# callee). Every nagini clause about the scalar value survives as a divergence in
# the resulting partition, so each nagini rival re-expresses as a wrong `eff`
# selection whose partition differs from gold on a decidable, concrete input.
#
# The partition clause, however, is NEW here: the sibling battery had no case
# that could reach it, because a scalar-returning model has no batches to get
# wrong. A battery consisting only of ported selection-line rivals would leave
# `result = chunkBatches eff objs` untested — a spec pinning the size alone would
# pass every such case. The three PARTITION rivals below (offsets, order, count)
# close that, and rival-explicit-no-clamp closes the one selection sub-domain
# (rawMax = 0 with an explicit request) the ported set does not reach.
#
# Defended surface (spec view):
#   * splitBatches(batchSize, rawMax, objs) -> List (List α). All three inputs are
#     value types (Nat, Nat, List). Lean is referentially transparent, so the
#     nagini FRAME/PERMISSION-MUTATION class is VACUOUS here (no aliasing, no
#     fractional permission) — not fabricated a substitute; see assessment.
#   * The postcondition PINS the entire output to the inputs: the effective size
#     is `max rawMax 1` when `batchSize = 0` (unset), else `min batchSize
#     (max rawMax 1)`; and the batches are the consecutive `eff`-sized slices of
#     `objs`. `effectiveBatchSize` and `chunkBatches` are GROUNDED functional
#     helpers fully unfolded by their defs, not opaque oracles — echoing them is
#     the correct answer, not a cheat.
#
# The battery targets the load-bearing clauses with partial-domain rivals (each
# diverging on exactly one sub-domain the F2P/P2P input space reaches), plus a
# grounded structurally-different positive control, a branch-reordered positive
# control, and a ground ADMISSIBILITY discharge. Every reject case carries a
# concrete decidable witness that has been SEEN to elaborate against the rival
# and fail against the frozen solution.
#
# ADMISSIBILITY lane (added by audit): the frozen obligation binds
# `∀ {α} (batchSize rawMax : Nat) (objs : List α)` with NO hypothesis arrow, so
# there is no precondition to probe for PRECOND-TOO-STRONG in the nagini sense.
# That is NOT a reason to leave the lane empty. The analogue on a total carrier
# is the obligation being UNSATISFIABLE at an F2P-shaped input, which
# `admiss-ground-oversize-request` tests directly by discharging the relation at
# a concrete over-large-request input by evaluation before closing the frozen
# obligation verbatim.
#
# EMPTY-COLLECTION boundary (added by audit): every size/partition rival above
# diverges from gold only on NON-EMPTY collections — measured, all nine agree
# with gold at `objs = []` across (batchSize, rawMax) in [0,25)^2. So the one
# input where the batch count is zero rather than positive was unprobed;
# `rival-empty-emits-one` closes it.
from pathlib import Path

INSTANCE = "django__django-11951"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Anchors that lie ENTIRELY inside the region they edit and are unique. ---

# The effective-size selection line inside the impl region. Every rival swaps
# ONLY this line, leaving the frozen proof body in place: the reshaped impl no
# longer matches the frozen tactic script, so `correct_splitBatches` fails to
# close and the case is REJECTED. Attribution to the spec is supplied by the
# per-case witness, not by the tactic breakage.
_EFF = (
    "  let eff := if batchSize = 0 then maxBatchSize "
    "else min batchSize maxBatchSize"
)

# The batch-emission line inside the impl region, and the loop-bound line. The
# nagini sibling modeled ONLY the scalar size selection, so no ported case can
# reach the PARTITION clause this bundle adds (`result = chunkBatches eff objs`).
# Rivals swapping these two anchors attack that clause directly: a correct
# effective size sliced into the wrong batches is a wrong answer the
# selection-line rivals cannot express.
_BODY = "    batches := batches ++ [(objs.drop (k * eff)).take eff]"
_LOOP = "  for k in [0:batchCount eff objs.length] do"

# The `intro` line that opens the frozen proof body. The admissibility case
# PREPENDS a ground `have` here and then closes the frozen obligation verbatim,
# so the statement stays byte-identical and no new declaration appears.
_INTRO = "  intro α batchSize rawMax objs\n"

# The full frozen impl-region body (for the positive controls, which need a
# matching reproof).
_IMPL_BLOCK = """def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
    List (List α) := Id.run do
  -- The compatible maximum, normalized to at least one usable slot.
  let maxBatchSize := max rawMax 1
  -- A requested size never enlarges a batch beyond the compatible maximum; an
  -- unset request (`0`) falls back to the compatible maximum.
  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
  -- emitting one consecutive batch per offset.
  let mut batches : List (List α) := []
  for k in [0:batchCount eff objs.length] do
    batches := batches ++ [(objs.drop (k * eff)).take eff]
  return batches"""

# The full frozen proof-region body.
_PROOF_BLOCK = """/-- The `forIn` loop (in its desugared `do pure PUnit.unit; pure (yield …)`
form) that appends one mapped element per index over a list of indices `xs`
produces `acc ++ xs.map f`. Proved by induction on `xs`, generalizing the
accumulator. -/
theorem forIn_append_map {β : Type} (xs : List Nat) (acc : List β)
    (f : Nat → β) :
    (Id.run (do
        let r ← forIn (m := Id) xs acc
          (fun k r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [f k])))
        pure r))
      = acc ++ xs.map f := by
  induction xs generalizing acc with
  | nil => simp [Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_splitBatches :
    ∀ {α : Type} (batchSize rawMax : Nat) (objs : List α),
      problem_spec_splitBatches batchSize rawMax objs
        (implementation_splitBatches batchSize rawMax objs) := by
  intro α batchSize rawMax objs
  unfold problem_spec_splitBatches implementation_splitBatches chunkBatches
        effectiveBatchSize
  simp only [Id.run]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
  rw [List.range_eq_range']
  exact forIn_append_map _ _ _"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (expect verify) — a correct impl of the modeled behavior
# MUST satisfy the frozen spec. Each swaps the impl body AND supplies a proof
# that closes for the new shape (the frozen theorem STATEMENT is preserved).
# ---------------------------------------------------------------------------

# pos-functional: the cheapest honest impl — return the grounded functional
# oracle directly (no loop). Since `chunkBatches`/`effectiveBatchSize` are
# grounded defs fully unfolded by the spec, this IS the correct answer, and the
# proof is `rfl` after unfolding. Structurally different from the frozen
# imperative `Id.run do … for …` shape. Must verify (else SPEC-TOO-STRONG).
_POS_FUNCTIONAL_IMPL = """def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
    List (List α) :=
  chunkBatches (effectiveBatchSize batchSize rawMax) objs"""

_POS_FUNCTIONAL_PROOF = """theorem correct_splitBatches :
    ∀ {α : Type} (batchSize rawMax : Nat) (objs : List α),
      problem_spec_splitBatches batchSize rawMax objs
        (implementation_splitBatches batchSize rawMax objs) := by
  intro α batchSize rawMax objs
  unfold problem_spec_splitBatches implementation_splitBatches
  rfl"""

# pos-reorder: keep the imperative loop but REORDER the selection branches —
# handle the explicit-request case first (`batchSize ≠ 0`) and commute the `min`
# arguments (`min maxBatchSize batchSize`). Same value on every input; the proof
# closes after an equivalence rewrite of the reordered selection. Must verify
# (else the spec over-constrains the proof shape).
_POS_REORDER_IMPL = """def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
    List (List α) := Id.run do
  let maxBatchSize := max rawMax 1
  -- Reordered selection: honor an explicit request first, otherwise the maximum.
  let eff := if batchSize ≠ 0 then min maxBatchSize batchSize else maxBatchSize
  let mut batches : List (List α) := []
  for k in [0:batchCount eff objs.length] do
    batches := batches ++ [(objs.drop (k * eff)).take eff]
  return batches"""

_POS_REORDER_PROOF = """theorem forIn_append_map {β : Type} (xs : List Nat) (acc : List β)
    (f : Nat → β) :
    (Id.run (do
        let r ← forIn (m := Id) xs acc
          (fun k r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [f k])))
        pure r))
      = acc ++ xs.map f := by
  induction xs generalizing acc with
  | nil => simp [Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_splitBatches :
    ∀ {α : Type} (batchSize rawMax : Nat) (objs : List α),
      problem_spec_splitBatches batchSize rawMax objs
        (implementation_splitBatches batchSize rawMax objs) := by
  intro α batchSize rawMax objs
  have heff : (if batchSize ≠ 0 then min (max rawMax 1) batchSize else max rawMax 1)
      = effectiveBatchSize batchSize rawMax := by
    unfold effectiveBatchSize
    by_cases h : batchSize = 0
    · simp [h]
    · simp [h, Nat.min_comm]
  unfold problem_spec_splitBatches implementation_splitBatches chunkBatches
  simp only [Id.run]
  rw [heff]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
  rw [List.range_eq_range']
  exact forIn_append_map _ _ _"""


def _pos(impl_block, proof_block):
    m = _swap(_BASE, _IMPL_BLOCK, impl_block)
    return _swap(m, _PROOF_BLOCK, proof_block)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (expect verify) — confirm the obligation is SATISFIABLE, i.e.
# non-vacuous, at a concrete input of exactly the shape the behavioral change
# is about: an explicit request that EXCEEDS the compatible maximum.
#
# The nagini sibling probed PRECOND-TOO-STRONG by a `Requires`-admission
# self-call. The frozen obligation here binds `∀ {α} (batchSize rawMax : Nat)
# (objs : List α)` with no hypothesis arrow, so there is no precondition to
# weaken — but that does NOT make the lane vacuous, and reading it that way
# would drop one of the three directions this gate tests. The analogue on a
# total carrier is the obligation being UNSATISFIABLE at an F2P-shaped input:
# a spec whose relation cannot be discharged at (batchSize = 3, rawMax = 2,
# four objects) is unusable no matter how strong it looks, and a `∀`-statement
# gives no warning of that on its own.
#
# So this case DISCHARGES the relation at that concrete point BY EVALUATION, as
# a `have` prepended to the frozen tactic body, then closes the frozen
# obligation verbatim. Nothing is assumed: no new axiom, no new top-level
# theorem/lemma, statement byte-identical. If the pinned relation were
# unsatisfiable at that input — an over-constrained conjunction, an off-by-one
# in `batchCount` making the count and the contents disagree, a `chunkBatches`
# that cannot produce the value the impl computes — this case FAILS while the
# nine reject cases all still pass, which is the signal no uniqueness rival can
# give.
_ADMISS_GROUND = """  have _ground : problem_spec_splitBatches 3 2 [1, 2, 3, 4]
      (implementation_splitBatches 3 2 [1, 2, 3, 4]) := by
    unfold problem_spec_splitBatches implementation_splitBatches chunkBatches
          effectiveBatchSize
    simp only [Id.run]
    rw [Std.Range.forIn_eq_forIn_range']
    simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
    rw [List.range_eq_range']
    decide
"""


def _admiss(ground):
    """Prepend a ground `have` to the frozen proof body, keeping the frozen
    obligation statement and its verbatim closing tactics."""
    return _swap(_BASE, _INTRO, ground + _INTRO)


def _rival(new_eff):
    # Swap ONLY the selection line; the frozen proof body is left in place and
    # will not close for the reshaped impl (verification fails -> reject). The
    # witness carries the spec attribution.
    return _swap(_BASE, _EFF, new_eff)


def _rival_body(new_body):
    """Swap ONLY the batch-emission line (the partition clause)."""
    return _swap(_BASE, _BODY, new_body)


def _rival_loop(new_loop):
    """Swap ONLY the loop-bound line (the batch COUNT)."""
    return _swap(_BASE, _LOOP, new_loop)


# ---------------------------------------------------------------------------
# The reject-witness shared tactic. The impl is imperative (`Id.run do … for …`)
# so `decide` alone gets stuck on the unreduced `forIn`; we reduce the loop with
# the same range/forIn rewrites the frozen proof uses, then `decide` on the
# resulting concrete `List (List Nat)` (dis)equality. Confirmed to elaborate
# against each rival and FAIL against the frozen solution.
# ---------------------------------------------------------------------------

def _witness(bs, rm, objs):
    return f"""example : ¬ problem_spec_splitBatches {bs} {rm} {objs}
    (implementation_splitBatches {bs} {rm} {objs}) := by
  unfold problem_spec_splitBatches implementation_splitBatches chunkBatches effectiveBatchSize
  simp only [Id.run]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
  rw [List.range_eq_range']
  decide"""


# ---------------------------------------------------------------------------
# UNIQUENESS rivals (expect reject) — a WRONG impl of the modeled behavior that
# shares the frozen spec must NOT verify. Each diverges on a sub-domain the
# F2P/P2P input space reaches; the refinement argues its faithful real patch
# would still fail the F2P.
# ---------------------------------------------------------------------------

# rival-no-cap (THE BUG): an explicit request is used as-is, ignoring the
# backend maximum. Diverges whenever batchSize > max rawMax 1 (an over-large
# explicit request): the partition uses too-large slices, producing fewer
# batches than gold. Witness (5, 2, [1,2,3,4]): gold eff=2 -> [[1,2],[3,4]];
# rival eff=5 -> [[1,2,3,4]].
_RIVAL_NO_CAP = "  let eff := if batchSize = 0 then maxBatchSize else batchSize"

# rival-off-by-one-cap: caps at max+1 instead of max. Diverges on EVERY input
# with batchSize > max rawMax 1 (yielding min batchSize (max+1) where gold
# yields max) — the SAME sub-domain as rival-no-cap, differing only in the
# magnitude of the over-large effective size. It is NOT a single-point miss at
# batchSize = max+1: measured 35 diverging points with batchSize ≠ max+1 in
# [0,10)^2 alone, and its divergence set is exactly equal to rival-no-cap's.
# Witness (3, 2, [1,2,3]): gold eff=2 -> [[1,2],[3]]; rival eff=3 -> [[1,2,3]].
_RIVAL_OFF_BY_ONE = (
    "  let eff := if batchSize = 0 then maxBatchSize "
    "else min batchSize (maxBatchSize + 1)"
)

# rival-auto-zero-uses-request: in the unset (batchSize = 0) case it returns
# batchSize (= 0) instead of the backend maximum. Diverges only on the unset
# sub-domain (the dominant P2P input shape). Witness (0, 2, [1]): gold eff=2 ->
# [[1]]; rival eff=0 -> [] (batchCount with eff=0 is 0).
_RIVAL_AUTO_ZERO = (
    "  let eff := if batchSize = 0 then batchSize "
    "else min batchSize maxBatchSize"
)

# rival-no-clamp: drops the `max (·, 1)` normalization on the unset path, using
# rawMax directly. Diverges only when rawMax = 0 (a backend reporting 0):
# returns eff=0 -> an empty partition, violating the "≥ 1" guarantee.
# Witness (0, 0, [1]): gold eff=1 -> [[1]]; rival eff=0 -> [].
_RIVAL_NO_CLAMP = (
    "  let eff := if batchSize = 0 then rawMax "
    "else min batchSize maxBatchSize"
)

# rival-equal-under: at the exact equality boundary batchSize = max it returns
# max-1 (under-caps by one), slicing into smaller batches than requested.
# Diverges only on the single point batchSize = max rawMax 1. Witness
# (2, 2, [1,2]): gold eff=2 -> [[1,2]]; rival eff=1 -> [[1],[2]].
_RIVAL_EQUAL_UNDER = (
    "  let eff := if batchSize = 0 then maxBatchSize "
    "else if batchSize = maxBatchSize then maxBatchSize - 1 "
    "else min batchSize maxBatchSize"
)

# rival-explicit-no-clamp: the `max (·, 1)` normalization is dropped on the
# EXPLICIT-request path (min against the raw maximum instead of the normalized
# one). Correct on the whole unset sub-domain and whenever rawMax ≥ 1; diverges
# exactly when rawMax = 0 and batchSize ≥ 1, where it yields eff = 0 (an empty
# partition) instead of the guaranteed-usable 1. This is the ONLY sub-domain no
# ported rival reaches: rival-no-clamp drops the same normalization on the unset
# path only, so the two are disjoint at batchSize ≥ 1.
# Witness (3, 0, [1,2,3]): gold eff=1 -> [[1],[2],[3]]; rival eff=0 -> [].
_RIVAL_EXPLICIT_NO_CLAMP = (
    "  let eff := if batchSize = 0 then maxBatchSize "
    "else min batchSize rawMax"
)

# --- PARTITION-clause rivals (correct effective size, wrong batches) --------
# These attack `result = chunkBatches eff objs`, a clause the nagini sibling had
# no counterpart for (it modeled the scalar size alone). Each keeps the frozen
# selection line untouched, so a spec that pinned only the size and left the
# batching unconstrained would ADMIT them.

# rival-overlap-step: batch k starts at offset k instead of k · eff, so the
# batches overlap and do not partition `objs`. Same batch COUNT and same
# effective size as gold; only the offsets are wrong.
# Witness (2, 2, [1,2,3,4]): gold -> [[1,2],[3,4]]; rival -> [[1,2],[2,3]].
_RIVAL_OVERLAP_STEP = "    batches := batches ++ [(objs.drop k).take eff]"

# rival-reverse-order: emits the correct batches in REVERSE order. The multiset
# of batches is right, so a spec pinning only membership/count would admit it;
# the pinned relation is order-sensitive because the batches are processed in
# sequence. Witness (2, 2, [1,2,3,4]): gold -> [[1,2],[3,4]]; rival -> [[3,4],[1,2]].
_RIVAL_REVERSE_ORDER = "    batches := [(objs.drop (k * eff)).take eff] ++ batches"

# rival-floor-count: uses ⌊n / eff⌋ batches instead of ⌈n / eff⌉, silently
# DROPPING the final partial batch whenever eff does not divide the count.
# Correct on exact multiples; diverges on every remainder.
# Witness (2, 2, [1,2,3]): gold -> [[1,2],[3]]; rival -> [[1,2]].
_RIVAL_FLOOR_COUNT = "  for k in [0:objs.length / eff] do"

# rival-empty-emits-one: forces the batch count to at least 1, so an EMPTY
# collection yields one (empty) batch instead of no batches at all. Correct on
# every non-empty collection — `batchCount eff n ≥ 1` already holds there — and
# wrong exactly at `objs = []`, where gold produces `[]` and this produces
# `[[]]`.
#
# This closes a boundary NO other rival in the battery reaches: measured over
# (batchSize, rawMax) ∈ [0,25)² with `objs = []`, every one of the other nine
# rivals agrees with gold at the empty collection (0 divergences each), because
# they all diverge only in the effective SIZE or in how a non-empty list is cut.
# The empty case is the one input where the number of batches is zero rather
# than positive, so it is the only place the "no batches at all" outcome can be
# distinguished from "one degenerate batch" — a real behavioral difference (an
# operation issued for an empty collection versus none issued).
# Witness (0, 1, []): gold -> []; rival -> [[]].
_RIVAL_EMPTY_ONE = (
    "  for k in [0:max (batchCount eff objs.length) 1] do"
)


SPEC_TESTS = [
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos(_POS_FUNCTIONAL_IMPL, _POS_FUNCTIONAL_PROOF),
        "rationale": "Cheapest honest impl: return the grounded functional form "
                     "of the pinned relation directly (no loop). The spec's "
                     "selection/partition helpers are grounded defs, so this is "
                     "the correct answer, not an oracle echo; the reproof is `rfl` "
                     "after unfolding. Structurally different from the frozen "
                     "imperative loop. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos(_POS_REORDER_IMPL, _POS_REORDER_PROOF),
        "rationale": "Structurally-different CORRECT impl: keeps the imperative "
                     "loop but reorders the size-selection branches (explicit "
                     "request first) and commutes the `min` arguments. Same value "
                     "on every input; the reproof closes after an equivalence "
                     "rewrite of the reordered selection. Must verify (else the "
                     "spec over-constrains the proof shape).",
    },
    {
        "id": "admiss-ground-oversize-request",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss(_ADMISS_GROUND),
        "rationale": "Admissibility / non-vacuity: the pinned relation is "
                     "DISCHARGED by evaluation at a concrete input of exactly the "
                     "shape this behavior is about — an explicit request (3) "
                     "larger than the compatible maximum (2) over four objects, "
                     "giving the two batches [[1,2],[3,4]] — as a `have`, before "
                     "the frozen obligation is closed verbatim. The frozen binder "
                     "carries no hypothesis arrow, so there is no precondition to "
                     "weaken; the total-carrier analogue of PRECOND-TOO-STRONG is "
                     "the obligation being UNSATISFIABLE at an input of this "
                     "shape, which only a ground discharge detects. A relation "
                     "that over-constrains (count and contents disagreeing, a "
                     "`batchCount` off by one) would fail HERE while all nine "
                     "uniqueness rivals still passed. No new axiom or top-level "
                     "declaration; statement byte-identical.",
    },
    {
        "id": "rival-no-cap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_NO_CAP),
        "rationale": "Violates the pinned relation on the selection clause: an "
                     "explicit request is used uncapped, so on batchSize > "
                     "max rawMax 1 the partition uses too-large slices. The single "
                     "load-bearing clause of the fix.",
        "refinement": "This is exactly the pre-fix behavior (the request overrides "
                      "the compatible maximum). Its faithful real patch is the "
                      "UNCHANGED pre-fix line, which does NOT resolve the F2P "
                      "test_explicit_batch_size_respects_max_batch_size: with "
                      "batch_size = max+1 it issues fewer/larger-batch queries than "
                      "ceil(len(objs)/max), the exact query count the test asserts.",
        "witness": _witness(5, 2, "[1,2,3,4]"),
    },
    {
        "id": "rival-off-by-one-cap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_OFF_BY_ONE),
        "rationale": "Caps at max+1 instead of max, so the effective size — and "
                     "hence the batch slicing — is too large on the whole "
                     "over-large-request sub-domain batchSize > max rawMax 1. Its "
                     "divergence set from gold is exactly rival-no-cap's; it is a "
                     "SMALLER-MAGNITUDE variant of the same clause violation, not a "
                     "single-point miss at batchSize = max+1 (an earlier note in "
                     "this battery claimed the latter and was measured wrong).",
        "refinement": "min(batch_size, max+1) still slices into ceil(len/(max+1)) "
                      "batches when batch_size = max+1 — a DIFFERENT query count "
                      "than the ceil(len/max) the F2P asserts, so its faithful real "
                      "patch does not resolve the F2P.",
        "witness": _witness(3, 2, "[1,2,3]"),
    },
    {
        "id": "rival-auto-zero-uses-request",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_AUTO_ZERO),
        "rationale": "In the unset case (batchSize = 0) it returns the request "
                     "(0) instead of the backend maximum, yielding an effective "
                     "size of 0 and an empty partition — violating the pinned "
                     "relation on the dominant unset sub-domain.",
        "refinement": "Its faithful real patch returns batch_size (None) as the "
                      "slice step, so range(0, len, None) raises a TypeError at "
                      "runtime, crashing every bulk_create(batch_size=None) call "
                      "(the majority P2P path). It cannot resolve anything.",
        "witness": _witness(0, 2, "[1]"),
    },
    {
        "id": "rival-no-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_NO_CLAMP),
        "rationale": "Drops the `max (·, 1)` normalization on the unset path, "
                     "using rawMax directly. Diverges only when rawMax = 0 (a "
                     "backend reporting 0): effective size 0 -> empty partition, "
                     "violating the ≥ 1 guarantee. Single-boundary partial-domain "
                     "miss.",
        "refinement": "Its faithful real patch omits the max(.,1) clamp, so when "
                      "the backend reports 0 the slice step is 0 and range(0, len, "
                      "0) raises ValueError(range() arg 3 must not be zero), "
                      "crashing the unset path; it does NOT resolve the F2P/P2P.",
        "witness": _witness(0, 0, "[1]"),
    },
    {
        "id": "rival-equal-under",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_EQUAL_UNDER),
        "rationale": "At the exact equality boundary batchSize = max rawMax 1 it "
                     "under-caps by one (max-1), slicing into smaller batches than "
                     "requested. Violates the pinned relation on the single point "
                     "batchSize = max — the equality-edge attack that a value-"
                     "equivalent '<'->'<=' mutation would NOT reach.",
        "refinement": "Its faithful real patch would slice into ceil(len/(max-1)) "
                      "batches when the caller explicitly requests batch_size = max "
                      "— MORE queries than ceil(len/max), a wrong count that "
                      "regresses the explicit-equal P2P scenario, so it does not "
                      "resolve the F2P.",
        "witness": _witness(2, 2, "[1,2]"),
    },
    {
        "id": "rival-explicit-no-clamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_EXPLICIT_NO_CLAMP),
        "rationale": "Drops the `max (·, 1)` normalization on the EXPLICIT-request "
                     "path (mins against the raw maximum). Diverges exactly on "
                     "rawMax = 0 with batchSize ≥ 1: effective size 0 -> empty "
                     "partition, violating the ≥ 1 guarantee. Disjoint from "
                     "rival-no-clamp, which drops the same normalization on the "
                     "unset path only — this is the one sub-domain no other rival "
                     "in this battery reaches.",
        "refinement": "Its faithful real patch mins the requested size against the "
                      "un-normalized backend figure, so when the backend reports 0 "
                      "an explicit request yields a slice step of 0 and "
                      "range(0, len, 0) raises ValueError(range() arg 3 must not be "
                      "zero) — crashing the very explicit-request path the F2P "
                      "exercises, so it cannot resolve the F2P.",
        "witness": _witness(3, 0, "[1,2,3]"),
    },
    {
        "id": "rival-overlap-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_body(_RIVAL_OVERLAP_STEP),
        "rationale": "Attacks the PARTITION clause, not the size selection: batch k "
                     "starts at offset k instead of k · eff, so the batches overlap "
                     "and are not a partition of `objs`. The effective size and the "
                     "batch count both match gold, so only the clause pinning the "
                     "batch CONTENTS to consecutive non-overlapping slices rejects "
                     "it — a clause the scalar-only sibling battery could not probe.",
        "refinement": "Its faithful real patch advances the slice start by one per "
                      "batch instead of by the batch size, so all but the last batch "
                      "re-insert rows already inserted and the total inserted row "
                      "count is wrong — it fails the F2P and corrupts every "
                      "multi-batch P2P scenario.",
        "witness": _witness(2, 2, "[1,2,3,4]"),
    },
    {
        "id": "rival-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_body(_RIVAL_REVERSE_ORDER),
        "rationale": "Emits the correct batches in REVERSE order. The batch multiset "
                     "and count are exactly gold's, so a spec pinning only batch "
                     "membership, sizes, or count would ADMIT it; the pinned "
                     "input→output relation is order-sensitive because the batches "
                     "are consumed in sequence. Probes the ordering half of the "
                     "partition clause specifically.",
        "refinement": "Its faithful real patch iterates the slice offsets in "
                      "descending order, so rows are inserted back-to-front; the "
                      "resulting row ordering (and any auto-primary-key assignment "
                      "that follows insertion order) differs from what the P2P "
                      "ordering assertions require.",
        "witness": _witness(2, 2, "[1,2,3,4]"),
    },
    {
        "id": "rival-floor-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_loop(_RIVAL_FLOOR_COUNT),
        "rationale": "Uses ⌊n / eff⌋ batches instead of ⌈n / eff⌉, silently dropping "
                     "the final partial batch whenever the effective size does not "
                     "divide the object count. Correct on exact multiples, wrong on "
                     "every remainder. Attacks the batch-COUNT half of the partition "
                     "clause while leaving the selection line frozen.",
        "refinement": "Its faithful real patch bounds the slice loop by the floor "
                      "rather than covering the whole collection, so the trailing "
                      "objects are never inserted — fewer queries than "
                      "ceil(len(objs)/max) and missing rows, failing the F2P query "
                      "count and losing data on the dominant P2P path.",
        "witness": _witness(2, 2, "[1,2,3]"),
    },
    {
        "id": "rival-empty-emits-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival_loop(_RIVAL_EMPTY_ONE),
        "rationale": "Forces the batch count to at least one, so an EMPTY "
                     "collection is split into one empty batch instead of no "
                     "batches. Attacks the ONE boundary of the partition clause "
                     "no other rival here reaches: measured over (batchSize, "
                     "rawMax) in [0,25)^2 at objs = [], all nine other rivals "
                     "agree with gold, because each diverges only in the "
                     "effective SIZE or in how a NON-EMPTY list is cut. The empty "
                     "collection is the only input whose batch count is zero "
                     "rather than positive, so it is the only place 'no batches "
                     "at all' can be distinguished from 'one degenerate batch'.",
        "refinement": "Its faithful real patch bounds the slice loop below by one "
                      "instead of letting it be empty, so an empty collection "
                      "still produces one batch and the helper issues an "
                      "operation for zero objects — one more query than the zero "
                      "the empty-collection P2P scenario asserts, and a "
                      "degenerate empty payload sent to the backend. It resolves "
                      "nothing about the requested-size clause the F2P exercises "
                      "while regressing the empty-input path.",
        "witness": _witness(0, 1, "([] : List Nat)"),
    },
]

# AXIOM_TESTS: dropped — the axiom lane is G-AX's job and this gate ignores it.
# (The bundle also has no consumed callee axiom: `rawMax` is a plain input.)
AXIOM_TESTS = []
