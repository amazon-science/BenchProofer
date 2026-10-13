# properties.py — PBT manifest for scikit-learn__scikit-learn-14629 (lean backend).
#
# NOT a Lean module; an adversarial falsification battery ported from the
# nagini sibling. The gate (scripts/pbt_gate.py) parses SPEC_TESTS, writes each
# `module` to a temp Solution.lean, runs `same_spec` + variant-scope + the Lean
# verifier against the frozen Solution.lean, and — for every expect="reject"
# case — checks the `witness` two ways (elaborates against the rival, FAILS
# against gold). Spec cases are built by REGION-SURGERY: every variant is _BASE
# with edits made ONLY inside the # impl-start / # impl-end region and, where a
# reshaped impl needs it, inside the # proof-start / # proof-end body. The
# frozen spec view (docstring, structure, problem_spec predicate, the
# `theorem correct_collectClasses` STATEMENT) is byte-for-byte untouched, so
# `same_spec` and obligation-preservation hold by construction.
#
# Defended surface (frozen spec of the per-target class-label view):
#   The modeled function reads one read-only input, `subModels : List SubModel`
#   (each carrying `classLabels : List Int`), and returns
#   `Option (List (List Int))`. The single postcondition clause pins:
#     result = some (subModels.map (·.classLabels))
#   which folds four independent obligations into one equality:
#     (DEF)  the view is DEFINED — the outer constructor is `some`, never `none`
#            (the pre-patch state, where querying the attribute is an error);
#     (LEN)  one entry per sub-model — `length = subModels.length`;
#     (ORD)  target order — entry i is sub-model i's labels, not a permutation;
#     (VAL)  element-wise VALUE equality — entry i is exactly sub-model i's
#            recorded labels, not a constant / empty / another target's labels.
#   The input carrier is a plain immutable Lean value, so the spec is grounded
#   purely in it (`subModels.map (·.classLabels)`): there is no opaque callee
#   and no answer-key to echo. The reject lane below attacks each of DEF / LEN /
#   ORD / VAL with a rival the spec provably refutes at a concrete input.
#
# AUDIT NOTE (independent re-derivation of this port). Three repairs, each
# machine-checked; see the per-case comments for the builds behind them.
#   1. The ported `pos-value-copy` positive was DEFINITIONALLY the frozen impl on
#      this carrier (`l.drop 0` is `rfl`-equal to `l`, and the whole variant impl
#      is `rfl`-equal to the frozen one), so it verified while re-earning
#      nothing. Replaced by `pos-foldl-accumulator`, a reshape that is provably
#      NOT defeq to the frozen impl and needs its own induction.
#   2. The reverse/rotate rivals' `refinement` claimed a per-target F2P
#      mismatch the real fixture cannot exhibit: that fixture derives its extra
#      targets as row-permutations of the first, so all targets share one label
#      set and any reordering ACROSS targets is invisible to it. Both
#      refinements now attribute the rejection to the machine-checked ORD clause
#      and say what the fixture does and does not show.
#   3. Added `inner-order-reversed` (the one reordering attack that IS
#      demonstrable on that fixture, and the only rival that perturbs an entry
#      while keeping LEN, ORD, and every label) and `admiss-multitarget-shape`
#      (the expressible half of nagini's dropped `admiss-fshaped`: the
#      obligation is satisfiable, not vacuous, at the exercised shape).
# Attack D found no spec hole: eight NEW wrong impls (per-target dedup, truncate
# to 2, first target's labels everywhere, doubled entries, a nonempty view at the
# empty input, outer dedup, inner reversal) were all rejected. Attack E found no
# soundness hole: three NEW correct reshapes (double reversal, `foldl`, an
# empty/nonempty branch) all verified.

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14629"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body (everything strictly between # impl-start and
# # impl-end), the anchor for every impl-region swap.
_GOLD_IMPL = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels do
    acc := acc ++ [m.classLabels]
  return some acc"""

# The exact gold proof body (between # proof-start's theorem `:= by` and
# # proof-end), the anchor for the soundness positives that reshape the impl.
_GOLD_PROOF = """  intro subModels
  unfold problem_spec_collectClasses implementation_collectClasses
  have key := collectClasses_forIn_eq subModels []
  simp only [Id.run, bind, pure] at key ⊢
  rw [key]
  simp"""

assert _BASE.count(_GOLD_IMPL) == 1, "gold impl anchor drifted from Solution.lean"
assert _BASE.count(_GOLD_PROOF) == 1, "gold proof anchor drifted from Solution.lean"


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = []

# --- (A) POSITIVE CONTROL (soundness) — nagini pos-local-hoist --------------
# Structurally-different but CORRECT impl: instead of the imperative
# accumulator fold, produce the view in one functional step (map over the
# input). This is a genuinely different executable shape (no `let mut`, no
# `for`), so its proof is NOT the frozen accumulator-induction — it closes by
# `rfl` because the impl is definitionally the spec's right-hand side. Must
# VERIFY; if it cannot, the postcondition is SPEC-TOO-STRONG.
_POS_MAP_IMPL = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  return some (subModels.map (·.classLabels))"""
_POS_MAP_PROOF = """  intro subModels
  unfold problem_spec_collectClasses implementation_collectClasses
  rfl"""
SPEC_TESTS.append({
    "id": "pos-map-direct",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_MAP_IMPL),
                    _GOLD_PROOF, _POS_MAP_PROOF),
    "rationale": "A correct, structurally-different impl (build the whole view "
                 "in one functional map instead of the imperative accumulator "
                 "fold) satisfies the equality clause definitionally and must "
                 "verify; if it cannot, the postcondition is SPEC-TOO-STRONG.",
})

# --- (B) POSITIVE CONTROL (soundness, non-defeq accumulator reshape) ---------
# AUDIT REPAIR (replaces the ported `pos-value-copy`). The nagini original
# modeled a value-equal COPY of each per-target label sequence (`.drop(0)`, a
# fresh PSeq value) to show the spec pins VALUE and not identity. That
# distinction does not exist on this carrier: `List` is an immutable value type
# with no reference identity to pin, and `l.drop 0` is DEFINITIONALLY `l` —
# machine-checked, `example : ∀ l : List Int, l.drop 0 = l := fun _ => rfl`
# elaborates, and the whole `.drop 0` accumulator impl is `rfl`-equal to the
# frozen impl. So the ported case's "different shape" was the frozen impl up to
# defeq: it verified honestly while testing nothing but the tactic script's
# tolerance of one extra `simp only` step.
#
# Replaced with a reshape that is genuinely NOT definitionally the frozen impl
# (checked: `example : implFold = implementation_collectClasses := rfl` FAILS
# with a type mismatch on `rfl`). Building the view with a `foldl` over the
# input rather than the `for`/`let mut` accumulator forces its own induction —
# the frozen `collectClasses_forIn_eq` lemma does not apply to a `foldl` term —
# so this positive genuinely re-earns the obligation for a new impl shape.
# Must VERIFY; if it cannot, the postcondition is SPEC-TOO-STRONG.
_POS_FOLD_IMPL = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  return some (subModels.foldl (fun acc m => acc ++ [m.classLabels]) [])"""
_POS_FOLD_PROOF = """  intro subModels
  unfold problem_spec_collectClasses implementation_collectClasses
  have key : ∀ (xs : List SubModel) (init : List (List Int)),
      xs.foldl (fun acc m => acc ++ [m.classLabels]) init
        = init ++ xs.map (·.classLabels) := by
    intro xs
    induction xs with
    | nil => intro init; simp
    | cons a as ih => intro init; simp [ih]
  simp only [Id.run, bind, pure]
  rw [key]
  simp"""
SPEC_TESTS.append({
    "id": "pos-foldl-accumulator",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_FOLD_IMPL),
                    _GOLD_PROOF, _POS_FOLD_PROOF),
    "rationale": "A correct impl that accumulates the view with `List.foldl` "
                 "instead of the `for`/`let mut` loop. It is NOT definitionally "
                 "the frozen impl (`rfl` between the two fails), and the frozen "
                 "accumulator lemma does not apply to a `foldl` term, so the "
                 "obligation is genuinely REPROVEN by its own induction rather "
                 "than restated. Must verify; if it cannot, the postcondition "
                 "is SPEC-TOO-STRONG.",
})

# --- (C) DEFINEDNESS (uniqueness) — attacks DEF -----------------------------
# A rival that leaves the per-target view UNDEFINED (returns `none`). This is
# the pre-patch shape: querying the attribute is an error. Rejected by the DEF
# obligation (the outer constructor must be `some`). Refuted at the empty input
# — the smallest witness, where even the trivially-shaped view must still be
# `some []` rather than `none`.
_RIV_NONE = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  return none"""
SPEC_TESTS.append({
    "id": "undefined-view",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _RIV_NONE),
    "refinement": "A faithful real form never assigns the per-target attribute "
                  "(the pre-fix state), so querying it raises rather than "
                  "returning a value. The F2P test first asserts the attribute "
                  "is present and a list; with the attribute absent that "
                  "assertion errors and the F2P test does NOT resolve.",
    "rationale": "Rejected by the DEF obligation: the clause demands the outer "
                 "constructor be `some`, but this rival returns `none` at every "
                 "input, including the empty one.",
    "witness": """example : ¬ problem_spec_collectClasses
    [] (implementation_collectClasses []) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide""",
})

# --- (D) PARTIAL-DOMAIN: drop the LAST entry (uniqueness) — attacks LEN ------
# nagini partial-drop-last. Correct on every entry it emits, but stops one
# short (folds over all but the last sub-model). Rejected by the LEN
# obligation: length is one short. Refuted at a two-element input, where the
# rival emits one entry.
_RIV_DROP = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels.dropLast do
    acc := acc ++ [m.classLabels]
  return some acc"""
SPEC_TESTS.append({
    "id": "drop-last",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _RIV_DROP),
    "refinement": "A faithful real form gathers labels for all targets but the "
                  "last. On the F2P test there are three targets, so the view "
                  "has two entries; `len(view) == n_outputs` fails and the F2P "
                  "test does NOT resolve.",
    "rationale": "Rejected by the LEN obligation (length == subModels.length): "
                 "folding over `dropLast` makes the view one entry short.",
    "witness": """example : ¬ problem_spec_collectClasses
    [⟨[1]⟩, ⟨[2]⟩] (implementation_collectClasses [⟨[1]⟩, ⟨[2]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide""",
})

# --- (E) CONSTANT content: emit a fixed empty sequence (uniqueness) — VAL ----
# nagini const-empty-entry. Right shape (LEN holds) and right order, but every
# entry is the SAME constant empty label list rather than the genuine
# per-target labels — the classic "populated but with the wrong content"
# defect. Rejected by the VAL obligation wherever a sub-model has any labels.
# Refuted at a single non-empty sub-model.
_RIV_EMPTY = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for _m in subModels do
    acc := acc ++ [([] : List Int)]
  return some acc"""
SPEC_TESTS.append({
    "id": "const-empty-entry",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _RIV_EMPTY),
    "refinement": "A faithful real form populates the view with one empty label "
                  "array per target. The shape passes (`len == n_outputs`) but "
                  "the per-target array-equality check of each empty array "
                  "against the sub-model's real labels fails, so the F2P test "
                  "does NOT resolve.",
    "rationale": "Rejected by the VAL obligation: entry i is a constant empty "
                 "list, which differs from sub-model i's labels whenever that "
                 "target recorded any class label.",
    "witness": """example : ¬ problem_spec_collectClasses
    [⟨[7]⟩] (implementation_collectClasses [⟨[7]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide""",
})

# --- (F) REVERSE order (uniqueness) — attacks ORD ---------------------------
# nagini reverse-order. Emits the right number of entries (LEN holds) with the
# genuine per-target labels (VAL-shaped values) but in reverse target order.
# Rejected by the ORD obligation. Refuted at a two-element input whose two
# label lists differ.
_RIV_REV = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels.reverse do
    acc := acc ++ [m.classLabels]
  return some acc"""
SPEC_TESTS.append({
    "id": "reverse-order",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _RIV_REV),
    "refinement": "A faithful real form reverses the per-target order. AUDIT "
                  "CORRECTION: the ported claim that this alone sinks the F2P "
                  "test is NOT demonstrable. The F2P fixture builds its extra "
                  "targets as row-permutations of the first target, so all "
                  "three targets carry the SAME label set and a reversal is "
                  "invisible to that test's per-target equality check. The "
                  "F2P-resolution argument for this rival rests on the "
                  "SUITE-level obligation instead: the surrounding tests fix "
                  "the per-target order (per-target probability outputs are "
                  "documented to correspond to the per-target label view, and "
                  "the mirrored view misdescribes them whenever the targets "
                  "differ), and the spec's own ORD clause is refuted outright "
                  "at the witness input below. The order-sensitivity claim is "
                  "therefore attributed to the SPEC clause, which is "
                  "machine-checked, not to F2P output the fixture cannot show.",
    "rationale": "Rejected by the ORD obligation: entry k carries sub-model "
                 "(n-1-k)'s labels, which differs from sub-model k's in general. "
                 "Refuted at a two-element input whose two label lists differ.",
    "witness": """example : ¬ problem_spec_collectClasses
    [⟨[5]⟩, ⟨[6]⟩] (implementation_collectClasses [⟨[5]⟩, ⟨[6]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide""",
})

# --- (G) SHIFT order: rotate by one (uniqueness) — attacks ORD (near-miss) ---
# nagini partial-shift-first. A DISTINCT ordering rival from reverse: it rotates
# the target assignment left by one (entry 0 gets target 1's labels). On a
# two-element list a rotate coincides with a reversal, so this rival is a
# near-miss that AGREES with the reverse rival there; it is separated only at
# length >= 3, where rotate and reflect diverge. Refuted at a three-element
# input to demonstrate that discriminating sub-domain.
_RIV_SHIFT = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels.drop 1 ++ subModels.take 1 do
    acc := acc ++ [m.classLabels]
  return some acc"""
SPEC_TESTS.append({
    "id": "shift-first",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _RIV_SHIFT),
    "refinement": "A faithful real form rotates the per-target assignment by "
                  "one (target 0 receives target 1's labels). AUDIT CORRECTION: "
                  "same limit as the reverse rival — the F2P fixture's targets "
                  "are row-permutations of one another, so they share a label "
                  "set and a rotation does not change what that test observes. "
                  "The rejection is attributed to the SPEC's ORD clause, "
                  "machine-checked at the three-element witness below (a "
                  "rotation and a reflection agree at length 2 and diverge at "
                  "length 3, which is why this witness is longer than the "
                  "reverse rival's), and NOT to an F2P failure the fixture "
                  "cannot demonstrate.",
    "rationale": "Rejected by the ORD obligation at entry 0: it carries "
                 "sub-model 1's labels, not sub-model 0's. Distinct from the "
                 "reverse rival at length >= 3 (rotate vs reflect diverge), so "
                 "it is refuted at a three-element input.",
    "witness": """example : ¬ problem_spec_collectClasses
    [⟨[1]⟩, ⟨[2]⟩, ⟨[3]⟩] (implementation_collectClasses [⟨[1]⟩, ⟨[2]⟩, ⟨[3]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide""",
})

# --- (H) INNER label-sequence order (uniqueness) — attacks VAL, added by audit
# AUDIT ADDITION. Every ported rival attacks the OUTER list: its length (LEN),
# its target order (ORD), or replaces an entry wholesale with a constant (VAL at
# maximal distance). None of them perturbs the CONTENT of a single per-target
# label sequence while keeping that sequence's multiset of labels intact, so the
# battery never showed the clause pins each entry as an ORDERED sequence rather
# than merely as the right collection of labels. This rival keeps LEN, keeps ORD,
# and keeps every label of every target — it only reverses the order WITHIN each
# target's label sequence. Landed and machine-checked: the module is rejected,
# and the witness elaborates against the rival while failing on gold by genuine
# refutation.
_RIV_INNER_REV = """def implementation_collectClasses
    (subModels : List SubModel) : Option (List (List Int)) := Id.run do
  let mut acc : List (List Int) := []
  for m in subModels do
    acc := acc ++ [m.classLabels.reverse]
  return some acc"""
SPEC_TESTS.append({
    "id": "inner-order-reversed",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_IMPL, _RIV_INNER_REV),
    "refinement": "A faithful real form emits, for each target, that target's "
                  "genuine class labels but in descending rather than the "
                  "recorded ascending order. The per-target equality the F2P "
                  "test performs is ORDER-SENSITIVE and the fixture's targets "
                  "each carry more than one distinct label, so the check fails "
                  "on the first target and the F2P test does NOT resolve. Unlike "
                  "the two reordering rivals above, this one IS demonstrable on "
                  "the F2P fixture: it does not rely on the targets differing "
                  "from one another, only on a single target having >= 2 labels.",
    "rationale": "Rejected by the VAL obligation, at the level the other rivals "
                 "leave unattacked: entry i is a permutation of sub-model i's "
                 "labels rather than that sub-model's recorded sequence, so the "
                 "clause's element-wise equality fails wherever a target "
                 "recorded two or more distinct labels. LEN and ORD both still "
                 "hold, which is what isolates the clause under test.",
    "witness": """example : ¬ problem_spec_collectClasses
    [⟨[10, 20]⟩] (implementation_collectClasses [⟨[10, 20]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide""",
})

# --- (I) ADMISSIBILITY — added by audit ---------------------------------------
# AUDIT ADDITION. The port dropped nagini's `admiss-fshaped` as inexpressible,
# on the ground that this carrier has no precondition to be too strong (the spec
# is a total predicate over `List SubModel`, with no `Requires`). That reason is
# correct as far as PRECOND-TOO-STRONG goes, but it discards the other half of
# what the nagini case bought: a check that the frozen obligation is SATISFIABLE
# — non-vacuous — at the shape the real scenario exercises, which IS expressible
# here and costs one build. Without it the battery's positives only ever assert
# the spec of a *universally quantified* impl; nothing pins that a concrete
# multi-target input has a satisfying view at all. Keeps the gold impl verbatim
# and adds in-region `example`s (the impl region is elided by same_spec, so the
# frozen spec view is untouched); both are decided by the kernel.
_ADMISS_IMPL = _GOLD_IMPL + """

/-- Admissibility: the frozen obligation is satisfiable, not vacuous, at the
three-target shape the real scenario exercises — including the case where every
target recorded the same label set, which is what the F2P fixture actually
builds (its extra targets are row-permutations of the first). -/
example : problem_spec_collectClasses
    [⟨[0, 1, 2]⟩, ⟨[0, 1, 2]⟩, ⟨[0, 1, 2]⟩]
    (implementation_collectClasses [⟨[0, 1, 2]⟩, ⟨[0, 1, 2]⟩, ⟨[0, 1, 2]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide

/-- ...and at a three-target input whose per-target label sequences DIFFER in
length and content, including an empty one, so the admitted point also exercises
the ragged shape the ordering and length clauses are stated over. -/
example : problem_spec_collectClasses
    [⟨[4]⟩, ⟨[5, 6]⟩, ⟨[]⟩]
    (implementation_collectClasses [⟨[4]⟩, ⟨[5, 6]⟩, ⟨[]⟩]) := by
  unfold problem_spec_collectClasses implementation_collectClasses
  decide"""
SPEC_TESTS.append({
    "id": "admiss-multitarget-shape",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
    "rationale": "Adds in-region `example`s asserting the frozen postcondition "
                 "is SATISFIED by the frozen impl at concrete three-target "
                 "inputs — one where all targets share a label set (the shape "
                 "the real fixture builds) and one ragged one including an "
                 "empty label sequence. Both are decided by the kernel, so they "
                 "witness that the obligation is non-vacuous at the exercised "
                 "shape rather than only universally quantified. If either "
                 "failed, the spec would be unsatisfiable at a shape the "
                 "scenario requires (the carrier's analogue of "
                 "PRECOND-TOO-STRONG, there being no `Requires` here).",
})
