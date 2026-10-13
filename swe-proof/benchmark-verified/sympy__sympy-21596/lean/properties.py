# properties.py — G-PBT spec-lane battery for sympy__sympy-21596 (lean backend).
#
# NOT a Lean module: a manifest of adversarial falsification cases the gate
# executes against the frozen Solution.lean. Ported from the nagini sibling
# (nagini/properties.py); the argument of each case is carried over and
# re-expressed on this backend's carrier.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md):
#   One modeled function, `realParams`, contracted by the single obligation
#   `correct_realParams`. Its postcondition fully pins the result to a closed
#   set-expression of the three inputs:
#       result = (base ∩ zeroUnion vanish) \ zeroUnion poles
#   where `zeroUnion` is the union of the per-factor zero sets. There are three
#   INPUT binders — `base : Set ℚ`, `vanish poles : List (ℚ → ℚ)` — and one
#   top-level clause (an extensional set equality; not a conjunction). There is
#   no opaque oracle: `zeroUnion` is spelled out in the (non-elided) `pure`
#   region, so every reject witness computes membership at a concrete rational
#   point and needs no conditioning on the carrier.
#
# The obligation carries NO precondition hypothesis (`∀ base vanish poles,
# problem_spec …`). That does NOT make the admissibility lane vacuous: on a
# total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input, which case 6 tests directly by
# discharging the obligation at that concrete input (by evaluation, as a `have`)
# before closing the frozen obligation verbatim.
#
# PORT MAP (nagini → lean); see `assessment` in the submitted payload for the
# full account of what ported and what was legitimately omitted:
#   * nagini POS_CONTROL / TWO_STEP_POS (soundness) → one soundness positive,
#     a structurally-different but correct impl whose proof re-closes.
#   * nagini PARTIAL_NO_KEEP / DROP_IGNORED (uniqueness) → the two set-operation
#     rivals that attack the load-bearing intersect/difference distinction.
#   * two further uniqueness rivals attack the drop half from the other side
#     (drop-the-pole-handling, and turn-the-difference-into-an-intersection),
#     so `poles` is varied and the difference clause is attacked in both
#     directions.
#   * case 8 (added by the AUDIT) attacks the remaining half of the clause: the
#     per-factor ACCUMULATION. Every other rival is refutable at a one-element
#     `vanish` list, so the fact that `zeroUnion` unions over ALL factors was
#     unprobed; that rival is definitionally equal to the frozen impl on every
#     zero- or one-factor input and only diverges at two or more.
#   * nagini FRAME_MUT (permission mutation) is VACUOUS here: Lean is
#     referentially transparent, there is no read-only-input permission to
#     violate, so this class has no counterpart (not fabricated).
#   * nagini BOUNDARY (positional "first base element") → case 7. `Set ℚ` has no
#     positional structure, but the nagini case's CONTENT — correct everywhere
#     except that one distinguished element of `base` is over-kept
#     unconditionally — carries over with a distinguished VALUE in place of a
#     distinguished index. That near-miss is the weakest rival here: it agrees
#     with the frozen spec at every point but one.
#   * nagini's second modeled function `collect_real_indices_two_step` and its
#     cases (TWO_STEP_POS, TWO_STEP_DROP_COLLAPSE) are unmodeled here — the lean
#     bundle contracts a single function — so they have no counterpart.
#   * AXIOM_TESTS dropped (axiom lane is G-AX's job).
from pathlib import Path

INSTANCE = "sympy__sympy-21596"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region only (lines 62-76). Editing only these keeps
# same_spec (the spec view elides the impl and proof regions) and preserves the
# `theorem correct_realParams` statement byte-for-byte.
# ---------------------------------------------------------------------------

# The corrected "keep the roots" op — an INTERSECTION with the union of the
# imaginary-part factor zero sets. Unique in the file.
KEEP_OP = "  let mut base_set := base ∩ sols1\n"
# The "drop the poles" op — a DIFFERENCE against the union of the denominator
# factor zero sets. Unique in the file.
DROP_OP = "  base_set := base_set \\ sols2\n"


# --- 1. SOUNDNESS positive: structurally-different but CORRECT ---------------
# Reorder the two accumulator loops (compute the pole-factor union BEFORE the
# imaginary-part-factor union) and combine both unions in a single closing
# expression. The observable result is identical, and the frozen proof re-closes
# after `rw [fold_zeroUnion, fold_zeroUnion]` (the two `fold_zeroUnion`
# rewrites are order-insensitive). If a faithful correct impl of this shape
# could not verify => SPEC-TOO-STRONG.
POS_CONTROL = _swap(
    _BASE,
    "  -- union of the imaginary-part factors' zero sets\n"
    "  let mut sols1 : Set ℚ := ∅\n"
    "  for f in vanish do\n"
    "    sols1 := sols1 ∪ {x | f x = 0}\n"
    "  -- keep the base parameters that make the value real\n"
    "  let mut base_set := base ∩ sols1\n"
    "  -- union of the denominator factors' zero sets\n"
    "  let mut sols2 : Set ℚ := ∅\n"
    "  for d in poles do\n"
    "    sols2 := sols2 ∪ {x | d x = 0}\n"
    "  -- drop the parameters that make the value undefined\n"
    "  base_set := base_set \\ sols2\n"
    "  return base_set\n",
    "  let mut sols2 : Set ℚ := ∅\n"
    "  for d in poles do\n"
    "    sols2 := sols2 ∪ {x | d x = 0}\n"
    "  let mut sols1 : Set ℚ := ∅\n"
    "  for f in vanish do\n"
    "    sols1 := sols1 ∪ {x | f x = 0}\n"
    "  let base_set := (base ∩ sols1) \\ sols2\n"
    "  return base_set\n",
)


# --- 2. UNIQUENESS (keep-op): the prepatch collapse bug ----------------------
# Replace the corrected INTERSECTION with the pre-fix DIFFERENCE: parameters
# that are NOT roots of the imaginary part wrongly survive, and genuine roots
# are wrongly dropped. This is the exact `-=`→`&=` inversion the gold reverses.
PREPATCH_DIFF = _swap(_BASE, KEEP_OP, "  let mut base_set := base \\ sols1\n")


# --- 3. UNIQUENESS (drop-op collapse): ignore the pole handling --------------
# Turn the difference into a no-op: every parameter kept by the intersection
# survives, never removed for making a denominator vanish. A parameter that is
# both a root and a pole (kept by the intersection, must be excluded by the
# difference) wrongly survives.
DROP_COLLAPSE = _swap(_BASE, DROP_OP, "  base_set := base_set\n")


# --- 4. UNIQUENESS (drop-op inversion): intersect the poles ------------------
# Replace the pole DIFFERENCE with an INTERSECTION: instead of removing the
# denominator-zero parameters, keep ONLY them. A real root that is not a pole
# is wrongly discarded.
DROP_AS_KEEP = _swap(_BASE, DROP_OP, "  base_set := base_set ∩ sols2\n")


# --- 5. UNIQUENESS (ungrounded echo): return the whole base ------------------
# Discard both filters and return `base` unchanged. Rejected because the result
# is not the surviving subset: a parameter in `base` that is neither a root nor
# excluded wrongly survives.
RETURN_BASE = _swap(
    _BASE,
    "  -- union of the imaginary-part factors' zero sets\n"
    "  let mut sols1 : Set ℚ := ∅\n"
    "  for f in vanish do\n"
    "    sols1 := sols1 ∪ {x | f x = 0}\n"
    "  -- keep the base parameters that make the value real\n"
    "  let mut base_set := base ∩ sols1\n"
    "  -- union of the denominator factors' zero sets\n"
    "  let mut sols2 : Set ℚ := ∅\n"
    "  for d in poles do\n"
    "    sols2 := sols2 ∪ {x | d x = 0}\n"
    "  -- drop the parameters that make the value undefined\n"
    "  base_set := base_set \\ sols2\n"
    "  return base_set\n",
    "  return base\n",
)


# --- 6. ADMISSIBILITY: the obligation is satisfiable at an F2P-shaped input ---
# The frozen obligation is universally quantified with no precondition, so the
# analogue of PRECOND-TOO-STRONG on this total carrier is the obligation being
# unsatisfiable at exactly a normal, F2P-shaped input. Discharge it at one such
# input CONCRETELY — a two-factor imaginary part whose roots are ±1, no
# denominator factors — as a `have` by evaluation, then close the frozen
# obligation verbatim. Two further ground `have`s pin the surviving set as
# genuinely discriminating at that input (a root survives; a non-root does not),
# so the ground instance cannot be satisfied by a degenerate/empty answer.
# Nothing is assumed: no new declaration, the theorem statement stays
# byte-identical, and every `have` sits inside the existing tactic body.
_F2P_ARGS = "Set.univ [fun x => x - 1, fun x => x + 1] []"
_ADMISS_SIMP = (
    "    simp only [implementation_realParams, Id.run, bind, List.forIn_cons,\n"
    "      List.forIn_nil, pure, Set.mem_diff, Set.mem_inter_iff, Set.mem_union,\n"
    "      Set.mem_setOf_eq, Set.empty_union, Set.mem_univ, "
    "Set.mem_empty_iff_false,\n"
    "      not_false_eq_true, and_true, true_and]\n"
)
ADMISS = _swap(
    _BASE,
    "  intro base vanish poles\n",
    f"  have _ground : problem_spec_realParams {_F2P_ARGS}\n"
    f"      (implementation_realParams {_F2P_ARGS}) := by\n"
    "    unfold problem_spec_realParams implementation_realParams\n"
    "    simp only [Id.run, bind, List.forIn_cons, List.forIn_nil, pure, "
    "zeroUnion,\n"
    "      Set.empty_union, Set.union_empty, Set.union_assoc]\n"
    f"  have _survivor : (1:ℚ) ∈ implementation_realParams {_F2P_ARGS} := by\n"
    f"{_ADMISS_SIMP}"
    "    norm_num\n"
    f"  have _excluded : (2:ℚ) ∉ implementation_realParams {_F2P_ARGS} := by\n"
    f"{_ADMISS_SIMP}"
    "    norm_num\n"
    "  intro base vanish poles\n",
)


# --- 7. UNIQUENESS (boundary near-miss): over-keep one distinguished point ----
# Correct everywhere EXCEPT that one distinguished element of `base` is added
# back unconditionally, after both filters have run. This is the nagini BOUNDARY
# case's content on this carrier (a distinguished VALUE where nagini had a
# distinguished INDEX): the weakest rival in the battery, agreeing with the spec
# at every point but one, so it probes how tightly the equality clause is pinned
# rather than which set operation was used.
OVERKEEP_POINT = _swap(
    _BASE,
    DROP_OP,
    "  base_set := base_set \\ sols2\n"
    "  base_set := base_set ∪ (base ∩ {x | x = 0})\n",
)


# --- 8. UNIQUENESS (per-factor accumulation): keep only the LAST factor -------
# Added by the audit. Every other rival here attacks a top-level set OPERATION
# (which `∩`/`\` was used), and each is refuted at a ONE-element `vanish` list —
# so the accumulation across the factor list, the other load-bearing half of the
# clause (`zeroUnion` is a UNION over ALL factors, not the last one), was never
# probed. This rival OVERWRITES the accumulator instead of unioning into it: it
# is definitionally identical to the frozen impl on every zero- or one-factor
# input, and diverges only once `vanish` has two or more entries, so it is the
# only case whose refutation requires a multi-factor list.
KEEP_ACC = "    sols1 := sols1 ∪ {x | f x = 0}\n"
LAST_FACTOR_ONLY = _swap(_BASE, KEEP_ACC, "    sols1 := {x | f x = 0}\n")


SPEC_TESTS = [
    {
        "id": "pos-control-reorder-loops",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONTROL,
        "rationale": (
            "structurally-different CORRECT impl: the two factor-union "
            "accumulator loops are reordered (pole union built first) and the "
            "intersection and difference combined in one closing expression. "
            "The observable result is unchanged and the frozen proof re-closes "
            "(the two fold rewrites are order-insensitive), defending the single "
            "clause result = (base ∩ zeroUnion vanish) \\ zeroUnion poles. Must "
            "verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "prepatch-keep-becomes-difference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PREPATCH_DIFF,
        "refinement": (
            "This is the pre-fix bug verbatim: keeping the parameters that make "
            "the value real requires an INTERSECTION with the roots, but the "
            "buggy code took a DIFFERENCE, so non-roots wrongly survive and "
            "genuine roots are dropped. Its faithful real patch reproduces the "
            "reported defect (a non-root parameter wrongly reported as a member "
            "of the real intersection, and the genuine real members lost), which "
            "is exactly what the FAIL_TO_PASS test asserts must not happen, so it "
            "does NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition equality clause: the result must "
            "equal (base ∩ zeroUnion vanish) \\ zeroUnion poles, an "
            "INTERSECTION with the root union; a difference keeps a non-root "
            "parameter the intersection excludes. Attacks the `∩` (keep) half."
        ),
        "witness": (
            "example : ¬ problem_spec_realParams Set.univ [fun x => x - 2] []\n"
            "    (implementation_realParams Set.univ [fun x => x - 2] []) := by\n"
            "  intro h\n"
            "  have hm : (0:ℚ) ∈ implementation_realParams Set.univ "
            "[fun x => x - 2] [] := by\n"
            "    simp only [implementation_realParams, Id.run, List.forIn_cons, "
            "List.forIn_nil,\n"
            "      bind, pure, Set.mem_diff, Set.mem_setOf_eq, Set.empty_union, "
            "Set.mem_univ,\n"
            "      Set.mem_empty_iff_false, not_false_eq_true, true_and]\n"
            "    norm_num\n"
            "  rw [h] at hm\n"
            "  simp only [zeroUnion, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_setOf_eq,\n"
            "    Set.mem_univ, Set.union_empty, Set.mem_empty_iff_false, "
            "not_false_eq_true,\n"
            "    and_true, true_and] at hm\n"
            "  norm_num at hm\n"
        ),
    },
    {
        "id": "drop-collapse-ignore-poles",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_COLLAPSE,
        "refinement": (
            "Collapsing the difference into a no-op keeps a parameter that is "
            "both a root (kept by the intersection) and a pole (must be removed "
            "because a denominator vanishes there). Its faithful real patch omits "
            "the denominator-exclusion step, so a parameter whose value is real "
            "but UNDEFINED wrongly survives — the surviving set is too large and "
            "the exact-set assertions of the FAIL_TO_PASS test fail, so it does "
            "NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition equality clause: the result must be "
            "the intersection MINUS the pole union; ignoring the poles keeps a "
            "root that is also a pole, which the `\\ zeroUnion poles` conjunct "
            "excludes. Attacks the `\\` (drop) half — varies `poles`."
        ),
        "witness": (
            "example : ¬ problem_spec_realParams Set.univ [fun x => x] "
            "[fun x => x]\n"
            "    (implementation_realParams Set.univ [fun x => x] [fun x => x]) "
            ":= by\n"
            "  intro h\n"
            "  have hm : (0:ℚ) ∈ implementation_realParams Set.univ [fun x => x] "
            "[fun x => x] := by\n"
            "    simp only [implementation_realParams, Id.run, List.forIn_cons, "
            "List.forIn_nil,\n"
            "      bind, pure, Set.mem_inter_iff, Set.mem_setOf_eq, "
            "Set.empty_union, Set.mem_univ,\n"
            "      true_and]\n"
            "  rw [h] at hm\n"
            "  simp only [zeroUnion, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_setOf_eq,\n"
            "    Set.mem_univ, Set.union_empty, true_and, not_true, and_false] "
            "at hm\n"
        ),
    },
    {
        "id": "drop-becomes-intersection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_AS_KEEP,
        "refinement": (
            "Turning the pole difference into an intersection keeps ONLY the "
            "denominator-zero parameters, discarding every real root that is not "
            "a pole. Its faithful real patch would return an empty (or wrong) "
            "real intersection whenever the roots and poles are disjoint, "
            "losing the genuine real members the FAIL_TO_PASS test requires, so "
            "it does NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition equality clause: the pole handling "
            "must be a DIFFERENCE (`\\`); an intersection drops a real root that "
            "is not a pole. Attacks the `\\` (drop) half from the opposite "
            "direction to case 3 — varies `poles`."
        ),
        "witness": (
            "example : ¬ problem_spec_realParams Set.univ [fun x => x] "
            "[fun x => x - 1]\n"
            "    (implementation_realParams Set.univ [fun x => x] "
            "[fun x => x - 1]) := by\n"
            "  intro h\n"
            "  have hm : (0:ℚ) ∉ implementation_realParams Set.univ [fun x => x] "
            "[fun x => x - 1] := by\n"
            "    simp only [implementation_realParams, Id.run, List.forIn_cons, "
            "List.forIn_nil,\n"
            "      bind, pure, Set.mem_inter_iff, Set.mem_setOf_eq, "
            "Set.empty_union, Set.mem_univ,\n"
            "      true_and]\n"
            "    norm_num\n"
            "  rw [h] at hm\n"
            "  simp only [zeroUnion, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_setOf_eq,\n"
            "    Set.mem_univ, Set.union_empty, true_and] at hm\n"
            "  norm_num at hm\n"
        ),
    },
    {
        "id": "ungrounded-return-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RETURN_BASE,
        "refinement": (
            "Returning `base` unfiltered echoes the input domain instead of "
            "computing the surviving subset. Its faithful real patch would keep "
            "every parameter regardless of whether its value is real or defined, "
            "so a non-root parameter wrongly survives and the FAIL_TO_PASS "
            "exact-set assertion fails, so it does NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition equality clause: the result is pinned "
            "to a proper subset of `base` (the intersection minus the poles); "
            "returning all of `base` keeps a parameter neither a root nor a "
            "pole. Varies `base` (a finite set here, not the universe)."
        ),
        "witness": (
            "example : ¬ problem_spec_realParams ({0, 1} : Set ℚ) "
            "[fun x => x] []\n"
            "    (implementation_realParams ({0, 1} : Set ℚ) [fun x => x] []) "
            ":= by\n"
            "  intro h\n"
            "  have hm : (1:ℚ) ∈ implementation_realParams ({0, 1} : Set ℚ) "
            "[fun x => x] [] := by\n"
            "    simp only [implementation_realParams]\n"
            "    norm_num\n"
            "  rw [h] at hm\n"
            "  simp only [zeroUnion, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_setOf_eq,\n"
            "    Set.union_empty, Set.mem_empty_iff_false, not_false_eq_true, "
            "and_true,\n"
            "    Set.mem_insert_iff, Set.mem_singleton_iff] at hm\n"
            "  norm_num at hm\n"
        ),
    },
    {
        "id": "admiss-ground-f2p-parameters",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": (
            "the obligation is discharged at a concrete F2P-shaped input (a "
            "two-factor imaginary part whose roots are ±1, no denominator "
            "factors) by evaluation as a `have`, and two further ground `have`s "
            "pin that input's surviving set as discriminating (the root 1 "
            "survives; the non-root 2 does not), before the frozen obligation is "
            "closed verbatim. Verifies, else the modeled behavior would be "
            "unsatisfiable at exactly a normal F2P input — the analogue of "
            "PRECOND-TOO-STRONG on a carrier whose obligation has no "
            "precondition hypothesis. Nothing is assumed: no new declaration, "
            "the theorem statement is byte-identical, and every `have` sits in "
            "the existing tactic body. Ports nagini's admiss-base-case."
        ),
    },
    {
        "id": "boundary-overkeep-one-point",
        "kind": "uniqueness",
        "expect": "reject",
        "module": OVERKEEP_POINT,
        "refinement": (
            "Adding one distinguished parameter back after both filters have run "
            "over-keeps a single point whenever that parameter is not a genuine "
            "root. Its faithful real patch would report one extra surviving "
            "parameter — an image element whose value is not real — so the "
            "exact-set assertion of the FAIL_TO_PASS test fails on the very "
            "membership query the issue reports, and it does NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition equality clause: the result is pinned "
            "EXACTLY to (base ∩ zeroUnion vanish) \\ zeroUnion poles, with no "
            "distinguished point exempted from the two filters; unioning one "
            "such point back in keeps a parameter the intersection excludes. The "
            "weakest rival here — it agrees with the spec at every other point, "
            "so it probes the tightness of the equality rather than the choice "
            "of set operation. Ports nagini's BOUNDARY near-miss."
        ),
        "witness": (
            "example : ¬ problem_spec_realParams Set.univ [fun x => x - 1] []\n"
            "    (implementation_realParams Set.univ [fun x => x - 1] []) := by\n"
            "  intro h\n"
            "  have hm : (0:ℚ) ∈ implementation_realParams Set.univ "
            "[fun x => x - 1] [] := by\n"
            "    simp only [implementation_realParams, Id.run, List.forIn_cons,\n"
            "      List.forIn_nil, bind, pure, Set.mem_union, Set.mem_diff,\n"
            "      Set.mem_inter_iff, Set.mem_setOf_eq, Set.empty_union, "
            "Set.mem_univ,\n"
            "      Set.mem_empty_iff_false, not_false_eq_true, and_true, "
            "true_and]\n"
            "    norm_num\n"
            "  rw [h] at hm\n"
            "  simp only [zeroUnion, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_setOf_eq,\n"
            "    Set.mem_univ, Set.union_empty, Set.mem_empty_iff_false,\n"
            "    not_false_eq_true, and_true, true_and] at hm\n"
            "  norm_num at hm\n"
        ),
    },
    {
        "id": "keep-only-last-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": LAST_FACTOR_ONLY,
        "refinement": (
            "Overwriting the accumulator keeps only the LAST factor's zero set "
            "instead of the union over all of them, so a parameter that is a "
            "root of an earlier factor is wrongly discarded. Its faithful real "
            "patch would collapse a multi-factor imaginary part to its final "
            "factor, losing genuine real members whenever the imaginary part has "
            "more than one factor — exactly the multi-factor assertions of the "
            "FAIL_TO_PASS test — so it does NOT resolve."
        ),
        "rationale": (
            "rejected by the postcondition equality clause: `zeroUnion` is the "
            "union over EVERY factor in `vanish`, so a root of any factor must "
            "survive; keeping only the last factor's zero set drops the roots of "
            "all the earlier ones. Attacks the per-factor ACCUMULATION rather "
            "than a top-level set operation — the only case here that varies "
            "`vanish` to a multi-element list, and the only one whose rival is "
            "definitionally EQUAL to the frozen impl at every zero- or "
            "one-factor input, so no single-factor witness can refute it."
        ),
        "witness": (
            "example : ¬ problem_spec_realParams Set.univ "
            "[fun x => x - 1, fun x => x + 1] []\n"
            "    (implementation_realParams Set.univ "
            "[fun x => x - 1, fun x => x + 1] []) := by\n"
            "  intro h\n"
            "  have hm : (1:ℚ) ∉ implementation_realParams Set.univ "
            "[fun x => x - 1, fun x => x + 1] [] := by\n"
            "    simp only [implementation_realParams, Id.run, List.forIn_cons, "
            "List.forIn_nil,\n"
            "      bind, pure, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_setOf_eq,\n"
            "      Set.empty_union, Set.mem_univ, Set.mem_empty_iff_false,\n"
            "      not_false_eq_true, and_true, true_and]\n"
            "    norm_num\n"
            "  rw [h] at hm\n"
            "  simp only [zeroUnion, Set.mem_diff, Set.mem_inter_iff, "
            "Set.mem_union,\n"
            "    Set.mem_setOf_eq, Set.mem_univ, Set.union_empty, "
            "Set.mem_empty_iff_false,\n"
            "    not_false_eq_true, and_true, true_and] at hm\n"
            "  norm_num at hm\n"
        ),
    },
]
