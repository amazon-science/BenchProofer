# properties.py — PBT falsification battery for pydata__xarray-4629 (lean backend).
#
# NOT a Lean source. A manifest the G-PBT runner parses: each SPEC_TESTS entry
# is a full Solution.lean variant that shares the FROZEN spec (everything outside
# the impl+proof regions is byte-identical, so markers.same_spec holds) and edits
# ONLY the impl region (and, where a soundness case reshapes the impl, the proof
# body). The theorem `correct_mergeAttrsOverride` STATEMENT is kept byte-identical
# in every variant; only its tactic body may change.
#
# This is a PORT of the nagini sibling's battery, re-expressed against this
# backend's carrier. See `assessment` in the pbt_author payload for exactly which
# nagini cases ported, which are vacuous here, and why.
#
# Defended surface (from Solution.lean + mapping.md + instance):
#   mergeAttrsOverride(attrs : List AttrObj) -> Option AttrObj
#   combines the per-source attribute objects into one under the "override"
#   policy. An AttrObj is (identity : Nat, contents : AttrDict), where identity
#   models Python object identity (`id(d)`; whether two handles are the SAME
#   object) and contents models the key->value mapping.
#     no sources         -> the result is absent (`none`).
#     >=1 source `first` -> the result is present with `first`'s contents copied
#                           verbatim, in a FRESH object whose identity differs
#                           from every source's — so the result aliases no source
#                           and a later change to the result cannot flow back.
#   The decisive observable is OBJECT IDENTITY (a fresh, distinct object vs a
#   shared reference to the leading source). On nagini this was carried by Viper
#   reference identity + the fractional-permission discipline; on this
#   referentially-transparent backend it is carried by the identity `Nat`
#   component and the `id ∉ attrs.map Prod.fst` freshness clause.
#
#   Load-bearing postcondition clauses (where rejections come from):
#     C_none   attrs == []          -> result = none
#     C_pres   attrs == first :: _  -> result = some (id, first.2)  [content copied]
#     C_fresh  attrs == first :: _  -> id ∉ attrs.map Prod.fst      [distinct id]
#   C_pres and C_fresh together are the heart: the content must equal the source's
#   AND the identity must be fresh. A result that reuses a source's identity
#   violates C_fresh; a result with the wrong content violates C_pres. There is no
#   ungrounded oracle: the copied content (`first.2`) is the input itself.
#
# F2P: test_merge_attrs_override_copy — merges with combine_attrs='override',
#      mutates the merged product's attrs, asserts the first source is untouched.
#      That is the aliasing property the `alias-return` rival violates.

from pathlib import Path

INSTANCE = "pydata__xarray-4629"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE 1 (soundness / verify) — CONSTANT SHIFT
# ---------------------------------------------------------------------------
# A CORRECT impl that keeps the frozen impl's SHAPE and changes only the chosen
# identity value: `maxId + 2` instead of `maxId + 1`. Still strictly greater than
# every source id, so still provably distinct from all of them (C_fresh holds);
# content unchanged (C_pres); empty branch unchanged (C_none). What this earns is
# narrow and specific: the spec does NOT over-pin the identity to the single value
# `max+1` — it admits any fresh id. It is NOT a structural reshape (the control
# flow, the loop, and the whole proof scaffolding are the frozen ones with a
# constant substituted); the structural probe is POS_MATCH_FOLD below, which is
# what actually tests that the spec is agnostic to HOW freshness is computed.
# If a faithful correct impl cannot verify -> SPEC-TOO-STRONG.
POS_IMPL = _swap(_BASE, "  let freshId := maxId + 1", "  let freshId := maxId + 2")
POS_IMPL = _swap(POS_IMPL,
                 "= some (loopMax (a :: as) 0 + 1, a.2)",
                 "= some (loopMax (a :: as) 0 + 2, a.2)")
POS_IMPL = _swap(POS_IMPL,
                 "))) + 1, (a :: as).head!.2) = _",
                 "))) + 2, (a :: as).head!.2) = _")
POS_REORDER = _swap(POS_IMPL,
                    "refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩",
                    "refine ⟨loopMax (a :: as) 0 + 2, impl_cons a as, ?_⟩")


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE 2 (soundness / verify) — STRUCTURAL RESHAPE
# ---------------------------------------------------------------------------
# A genuinely STRUCTURALLY-different correct impl. The frozen impl is an
# imperative `Id.run do` with a mutable accumulator and a `for` loop, and picks
# the leading source with `attrs.head!`; this one is a direct pattern `match` with
# NO monadic block, NO mutable state and NO `forIn` at all, binding `first`
# positionally and computing the fresh identity with `List.foldl max`. Every
# component of the postcondition is met by different means: C_none by the `[]`
# arm, C_pres by the positional binder, C_fresh by a `max`-fold rather than a
# `>`-guarded imperative accumulator. Because the shape changes, the frozen proof
# CANNOT be reused — the whole proof region is rewritten (its own loopMax over
# `max`, its own monotonicity lemmas), which is exactly what makes this a real
# soundness probe: it shows the spec is satisfiable by an independent derivation
# and is not merely a transcription of the frozen impl's control flow. This is the
# case that would catch a spec pinned to `Id.run`/`forIn`/`head!` reduction
# behaviour. If it cannot verify -> SPEC-TOO-STRONG.
_FROZEN_IMPL_REGION = _BASE[_BASE.index("-- impl-start"):_BASE.index("-- impl-end")]
_FROZEN_PROOF_REGION = _BASE[_BASE.index("-- proof-start"):_BASE.index("-- proof-end")]

_MATCH_IMPL_REGION = """-- impl-start
def implementation_mergeAttrsOverride
    (attrs : List AttrObj) : Option AttrObj :=
  match attrs with
  | [] => none
  | first :: rest =>
    some ((first :: rest).foldl (fun r p => max r p.1) 0 + 1, first.2)
"""

_MATCH_PROOF_REGION = """-- proof-start
/-- Closed-form spec of the fold: the running maximum of all `p.1`. -/
private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
  List.foldl (fun r p => max r p.1) init attrs

private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
    loopMax (a :: as) init = loopMax as (max init a.1) := by
  simp only [loopMax, List.foldl_cons]

private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
    init ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp [loopMax]
  | cons a as ih =>
    rw [loopMax_cons]
    exact le_trans (le_max_left init a.1) (ih (max init a.1))

private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp
  | cons a as ih =>
    intro p hp
    rw [loopMax_cons]
    rcases List.mem_cons.1 hp with rfl | hmem
    · exact le_trans (le_max_right init p.1) (loopMax_ge_init as (max init p.1))
    · exact ih _ p hmem

/-- On a non-empty input the match reduces definitionally. -/
private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := rfl

theorem correct_mergeAttrsOverride :
    ∀ (attrs : List AttrObj),
    problem_spec_mergeAttrsOverride attrs
      (implementation_mergeAttrsOverride attrs) := by
  intro attrs
  cases attrs with
  | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
  | cons a as =>
    simp only [problem_spec_mergeAttrsOverride]
    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
    intro hmem
    rw [List.mem_map] at hmem
    obtain ⟨p, hp, hpeq⟩ := hmem
    have := loopMax_ge_mem (a :: as) 0 p hp
    rw [hpeq] at this
    omega
"""

POS_MATCH_FOLD = _swap(_BASE, _FROZEN_IMPL_REGION, _MATCH_IMPL_REGION)
POS_MATCH_FOLD = _swap(POS_MATCH_FOLD, _FROZEN_PROOF_REGION, _MATCH_PROOF_REGION)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (admissibility / verify) — OBLIGATION SATISFIABLE AT THE
# F2P-SHAPED INPUT
# ---------------------------------------------------------------------------
# The frozen obligation carries no hypothesis, so there is no precondition to
# probe for satisfiability in the nagini sense. The analogue on a TOTAL carrier
# is the obligation itself being unsatisfiable at exactly an F2P-shaped input:
# the postcondition demands, simultaneously, a result that is PRESENT, whose
# content equals the leading source's, and whose identity avoids EVERY source
# identity. Those three clauses are conjoined under one existential, so an
# over-strong conjunction could have no witness at a perfectly ordinary input
# while the ∀-statement still looked plausible.
#
# This case discharges the obligation AT that concrete input, by evaluation, as a
# `have`, BEFORE closing the frozen obligation verbatim — so the probe cannot
# borrow the general proof's strength. The input is the F2P shape: two sources
# whose leading mapping carries a single entry and whose trailing mapping is
# empty. If the conjunction were unsatisfiable there, the `exact ⟨3, rfl, by
# decide⟩` could not close and this case would fail -> PRECOND-TOO-STRONG.
_ADMISS_HOOK = """  intro attrs
  cases attrs with
  | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]"""

_ADMISS_BLOCK = """  -- ADMISSIBILITY PROBE (F2P-shaped input): the postcondition must be
  -- SATISFIABLE at exactly the shape the failing test drives — two sources whose
  -- leading mapping carries one entry. Discharged BY EVALUATION at that concrete
  -- input, as a `have`, BEFORE the frozen obligation is closed verbatim below, so
  -- it cannot borrow the general proof's strength. The three conjoined clauses
  -- (present result / content = leading source's / identity fresh w.r.t. every
  -- source) must hold TOGETHER here; if they could not, this `have` would fail
  -- and the obligation would be unsatisfiable at an ordinary input
  -- -> PRECOND-TOO-STRONG.
  have _admiss_f2p : problem_spec_mergeAttrsOverride
      [(1, [(120, 0)]), (2, ([] : AttrDict))]
      (implementation_mergeAttrsOverride [(1, [(120, 0)]), (2, ([] : AttrDict))]) := by
    simp only [problem_spec_mergeAttrsOverride]
    exact ⟨3, rfl, by decide⟩
  intro attrs
  cases attrs with
  | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]"""

ADMISS_F2P = _swap(_BASE, _ADMISS_HOOK, _ADMISS_BLOCK)


# ---------------------------------------------------------------------------
# The frozen impl body's tail (the OVERRIDE construction). Rivals edit ONLY the
# impl region; each rival replaces the whole `let mut maxId ... return ...` tail
# or the `return none` guard, leaving the spec + theorem statement untouched.
# The proof body is left as the frozen one — it WILL fail to build against a
# reshaped/wrong impl, which is why every reject case ships a witness.
# ---------------------------------------------------------------------------
_IMPL_TAIL = """  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  let first := attrs.head!
  return some (freshId, first.2)"""


# === UNIQUENESS RIVALS ====================================================

# --- R1: ALIAS RETURN — OVERRIDE returns the leading source object itself
# instead of an independent copy: its identity component IS an input id, so
# C_fresh (id ∉ attrs.map Prod.fst) is violated. Content (C_pres) holds
# trivially, so the identity clause is the sole discriminator.
# refinement: F2P test_merge_attrs_override_copy mutates the merged product's
# attr and asserts the first source is unchanged, but when the result shares the
# leading source's identity the source changes too — the test fails, so a
# faithful patch of this shape does NOT resolve.
_ALIAS_TAIL = """  let first := attrs.head!
  return some (first.1, first.2)"""
ALIAS_RETURN = _swap(_BASE, _IMPL_TAIL, _ALIAS_TAIL)

# witness: at a single source with identity 5, the alias returns identity 5,
# which IS in attrs.map Prod.fst, so C_fresh fails. Gold returns a fresh id (6),
# so the same statement fails against gold.
_ALIAS_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(5, [(1,2)])]
    (implementation_mergeAttrsOverride [(5, [(1,2)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, hnotin⟩ := h
  have e : implementation_mergeAttrsOverride [(5, [(1,2)])] = some (5, [(1,2)]) := rfl
  rw [e] at heq
  simp only [Option.some.injEq, Prod.mk.injEq] at heq
  apply hnotin
  simp [heq.1]"""


# --- R2: EMPTY-COPY — OVERRIDE returns a fresh object (fresh id, distinct) whose
# contents are EMPTY rather than the source's. Satisfies C_fresh but fails C_pres
# on every non-empty source. Correct only on an empty leading source.
# refinement: a real patch whose 'override' branch returned {} (a fresh empty
# dict) would carry NO attrs into the merged product; F2P reads the first source's
# attr off the merged product and the merge-attrs P2P tests assert the source's
# attrs are present — they would fail, so it does NOT resolve.
_EMPTY_COPY_TAIL = """  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  return some (freshId, ([] : AttrDict))"""
EMPTY_COPY = _swap(_BASE, _IMPL_TAIL, _EMPTY_COPY_TAIL)

# witness: source contents [(7,8)] but the rival returns []; C_pres (content copy)
# fails. Gold returns the source's [(7,8)], so the statement fails against gold.
_EMPTY_COPY_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(3, [(7,8)])]
    (implementation_mergeAttrsOverride [(3, [(7,8)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, _⟩ := h
  have e : implementation_mergeAttrsOverride [(3, [(7,8)])] = some (4, ([] : AttrDict)) := rfl
  rw [e] at heq
  simp only [Option.some.injEq, Prod.mk.injEq] at heq
  exact absurd heq.2 (by decide)"""


# --- R3: SKIP-LAST — OVERRIDE returns a fresh object whose contents are the
# source's minus the LAST entry (`.dropLast`). Fresh id is fine (C_fresh),
# content is a proper prefix, not the whole (C_pres fails on any source of length
# >= 2). Faithful only on a 0/1-entry source; the copy must reproduce the WHOLE
# content.
# refinement: a real patch that dropped the last attribute of the leading source
# would make the merged product MISS that attr; the merge-attrs P2P tests compare
# the merged attrs to a multi-entry source and would fail — it does NOT resolve.
_SKIP_LAST_TAIL = """  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  let first := attrs.head!
  return some (freshId, first.2.dropLast)"""
SKIP_LAST = _swap(_BASE, _IMPL_TAIL, _SKIP_LAST_TAIL)

# witness: a TWO-entry source [(1,1),(9,9)] distinguishes dropLast (-> [(1,1)])
# from the full copy. A single-entry source would NOT discriminate (dropLast of a
# 1-list is []), and an empty one even less — this is the input that separates the
# near-miss from gold.
_SKIP_LAST_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(2, [(1,1),(9,9)])]
    (implementation_mergeAttrsOverride [(2, [(1,1),(9,9)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, _⟩ := h
  have e : implementation_mergeAttrsOverride [(2, [(1,1),(9,9)])] = some (3, [(1,1)]) := rfl
  rw [e] at heq
  simp only [Option.some.injEq, Prod.mk.injEq] at heq
  exact absurd heq.2 (by decide)"""


# --- R4: EMPTY-PRESENT — the no-source branch returns a present result instead of
# absent. Violates C_none (attrs == [] -> result = none). This is the analogue of
# nagini's DROP-non-empty / empty-guard case: it attacks the OTHER top-level
# clause of the postcondition (the empty-input branch), which no other rival
# touches — every other rival is correct on `[]` and wrong only on `first :: _`.
# refinement: a real patch whose empty-input guard returned a non-empty mapping
# instead of the empty-merge default would fabricate attrs on a merge with no
# sources; the merge pipeline's empty-input handling would carry spurious attrs
# and the merge P2P tests would fail — it does NOT resolve.
_EMPTY_PRESENT_TAIL = """  if attrs.isEmpty then
    return some (0, ([] : AttrDict))"""
EMPTY_PRESENT = _swap(_BASE, """  if attrs.isEmpty then
    return none""", _EMPTY_PRESENT_TAIL)

# witness: on [] the rival returns `some (0, [])`; C_none demands `none`. Gold
# returns `none`, so the statement fails against gold.
_EMPTY_PRESENT_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride []
    (implementation_mergeAttrsOverride []) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  have e : implementation_mergeAttrsOverride ([] : List AttrObj) = some (0, ([] : AttrDict)) := rfl
  rw [e] at h
  exact absurd h (by simp)"""


# --- R5: WRONG SOURCE — OVERRIDE copies the LAST source's contents instead of
# the leading one's. The identity is still fresh (C_fresh holds) and the content
# is still a verbatim copy of *a* source, so this is the one rival that attacks
# WHICH source the policy selects. Every other rival is correct about the
# selection and wrong about the content or the identity, so without this case the
# `first`-selection half of C_pres is never exercised. Its witness needs a
# multi-source input with DIFFERING contents: on a one-source list "first" and
# "last" coincide, and `fresh-first-only`'s two-source witness — the only other
# multi-source one — gives both sources identical contents, so the selection is
# invisible there too.
# refinement: a real patch reading the trailing source instead of the leading one
# would carry the WRONG source's attributes into the merged product under the
# 'override' policy; the F2P reads the leading source's attr off the merged
# product and the merge-attrs P2P tests pin the merged attrs to the FIRST
# source's, so both would fail — it does NOT resolve.
_LAST_SOURCE_TAIL = """  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  let first := attrs.getLast!
  return some (freshId, first.2)"""
LAST_SOURCE = _swap(_BASE, _IMPL_TAIL, _LAST_SOURCE_TAIL)

# witness: TWO sources with DIFFERENT contents — the input that separates "first"
# from "last". The rival returns the trailing [(8,8)]; gold returns the leading
# [(7,7)], so the statement fails against gold. A one-source input would not
# discriminate at all.
_LAST_SOURCE_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(1,[(7,7)]),(2,[(8,8)])]
    (implementation_mergeAttrsOverride [(1,[(7,7)]),(2,[(8,8)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, _⟩ := h
  have e : implementation_mergeAttrsOverride [(1,[(7,7)]),(2,[(8,8)])] = some (3, [(8,8)]) := rfl
  rw [e] at heq
  simp only [Option.some.injEq, Prod.mk.injEq] at heq
  exact absurd heq.2 (by decide)"""


# --- R6: FRESH-VS-FIRST-ONLY — the identity is chosen fresh relative to the
# LEADING source only (`first.1 + 1`) instead of relative to EVERY source. On a
# single-source input this is indistinguishable from gold, so it is a true
# near-miss; on two sources it can collide with a LATER source's identity, which
# is precisely the ∀-over-all-sources strength of C_fresh
# (id ∉ attrs.map Prod.fst) that no other rival tests — `alias-return` collides
# with the FIRST source, which the weakest possible reading of the clause would
# still catch.
# refinement: a real patch that only guaranteed the result was a different object
# from the leading source, while leaving it possibly shared with another source in
# the merge, would still alias a source object; mutating the merged product's
# attrs would then write through to that source, which is exactly the aliasing
# property the F2P pins — it does NOT resolve.
_FIRST_ONLY_TAIL = """  let first := attrs.head!
  return some (first.1 + 1, first.2)"""
FRESH_FIRST_ONLY = _swap(_BASE, _IMPL_TAIL, _FIRST_ONLY_TAIL)

# witness: sources with identities 1 and 2. The rival returns identity 1+1 = 2,
# which IS in attrs.map Prod.fst (it is the SECOND source's), so C_fresh fails.
# Gold returns 3, which is in neither, so the statement fails against gold. This
# is the input where "fresh w.r.t. the first source" and "fresh w.r.t. all
# sources" come apart.
_FIRST_ONLY_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(1,[(0,0)]),(2,[(5,5)])]
    (implementation_mergeAttrsOverride [(1,[(0,0)]),(2,[(5,5)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, hnotin⟩ := h
  have e : implementation_mergeAttrsOverride [(1,[(0,0)]),(2,[(5,5)])] = some (2, [(0,0)]) := rfl
  rw [e] at heq
  simp only [Option.some.injEq, Prod.mk.injEq] at heq
  apply hnotin
  simp [← heq.1]"""


# --- R7: ABSENT-ON-NONEMPTY — the mirror image of `empty-present`. Where that
# rival returns a PRESENT result on no sources, this one returns an ABSENT result
# when sources ARE given. It attacks the clause no other rival touches: the
# `first :: _` branch demands `result = some (id, first.2)`, i.e. the result must
# EXIST. Every other rival returns `some` on a non-empty input and is wrong only
# about the identity or the content, so the presence half of C_pres was never
# exercised — a spec that merely constrained the result WHEN present (and did not
# require it to be present) would let this through.
_ABSENT_TAIL = """  return none"""
ABSENT_NONEMPTY = _swap(_BASE, _IMPL_TAIL, _ABSENT_TAIL)

# witness: a single source is enough — the rival yields `none` where the spec
# demands `some`. Gold yields `some (5, [(1,1)])`, so the same statement fails
# against gold.
_ABSENT_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(4, [(1,1)])]
    (implementation_mergeAttrsOverride [(4, [(1,1)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, _⟩ := h
  have e : implementation_mergeAttrsOverride [(4, [(1,1)])] = none := rfl
  rw [e] at heq
  exact absurd heq (by simp)"""


# --- R8: FRESH-VS-FIRST-TWO — added during audit. `fresh-first-only` shows the
# freshness quantifier reaches past the LEADING source, but its rival consults
# exactly one source, so a spec that quantified over any FIXED-SIZE prefix of the
# sources (the first two, say) would still pass it. This rival computes the fresh
# identity from the first TWO sources only (`max first.1 second.1 + 1`), so it is
# indistinguishable from gold on every input of length <= 2 and collides only at
# depth 3+. Together the two rivals pin C_fresh as a genuine ∀-over-ALL-sources
# claim rather than a bounded-prefix one.
# refinement: a real patch that established distinctness against only a bounded
# number of the merge's sources would still leave the result sharing a later
# source's object; mutating the merged product's attrs would then write through to
# that source, which is exactly the aliasing property the F2P pins — it does NOT
# resolve.
_FIRST_TWO_TAIL = """  let first := attrs.head!
  let second := (attrs.drop 1).head!
  return some (max first.1 second.1 + 1, first.2)"""
FRESH_FIRST_TWO = _swap(_BASE, _IMPL_TAIL, _FIRST_TWO_TAIL)

# witness: THREE sources with identities 1, 2, 3. The rival picks
# max 1 2 + 1 = 3, which IS the third source's identity, so C_fresh fails. Gold
# picks 4, fresh w.r.t. all three, so the statement fails against gold. Inputs of
# length <= 2 do not discriminate at all — this is the shortest input that does.
_FIRST_TWO_WITNESS = """example : ¬ problem_spec_mergeAttrsOverride [(1,[(9,9)]),(2,[(0,0)]),(3,[(0,0)])]
    (implementation_mergeAttrsOverride [(1,[(9,9)]),(2,[(0,0)]),(3,[(0,0)])]) := by
  intro h
  simp only [problem_spec_mergeAttrsOverride] at h
  obtain ⟨id, heq, hnotin⟩ := h
  have e : implementation_mergeAttrsOverride [(1,[(9,9)]),(2,[(0,0)]),(3,[(0,0)])]
      = some (3, [(9,9)]) := rfl
  rw [e] at heq
  simp only [Option.some.injEq, Prod.mk.injEq] at heq
  apply hnotin
  simp [← heq.1]"""


SPEC_TESTS = [
    {
        "id": "pos-fresh-id-shift",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "CORRECT impl differing from the frozen one in the chosen "
        "identity VALUE: maxId+2 rather than maxId+1. Still strictly greater than "
        "every source id (C_fresh holds), content and empty branch unchanged "
        "(C_pres, C_none). What it earns is narrow and stated as such: the spec "
        "admits ANY fresh identity, not just the single value the frozen impl "
        "picks. It is NOT a structural reshape — control flow, loop and proof "
        "scaffolding are the frozen ones with a constant substituted, and the "
        "proof closes by omega exactly as the frozen +1 proof does; the structural "
        "probe is the separate pos-match-fold case. Must verify, else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-match-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_MATCH_FOLD,
        "rationale": "genuinely STRUCTURALLY-different CORRECT impl: a direct "
        "pattern `match` with no `Id.run do` block, no mutable accumulator and no "
        "`forIn` loop, binding the leading source positionally instead of via "
        "`head!` and computing the fresh identity with `List.foldl max` instead of "
        "a `>`-guarded imperative accumulator. Each postcondition clause is met by "
        "different means (C_none by the [] arm, C_pres by the positional binder, "
        "C_fresh by a max-fold), and the frozen proof cannot be reused — the proof "
        "region is rewritten with its own monotonicity lemmas. This is what shows "
        "the spec is satisfiable by an INDEPENDENT derivation rather than being a "
        "transcription of the frozen impl's control flow, and it is the case that "
        "would catch a spec pinned to Id.run/forIn/head! reduction behaviour. Must "
        "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_F2P,
        "rationale": "the obligation must be SATISFIABLE at an F2P-shaped input, "
        "not merely provable in general. The frozen statement has no hypothesis, "
        "so the analogue of PRECOND-TOO-STRONG on this total carrier is the "
        "postcondition's conjunction having NO witness at an ordinary input: it "
        "demands at once that the result be PRESENT, that its content equal the "
        "leading source's, and that its identity avoid EVERY source identity, all "
        "under one existential. This case discharges exactly that conjunction at "
        "the concrete F2P shape (two sources; the leading mapping carries one "
        "entry, the trailing one is empty) BY EVALUATION, as a `have` placed "
        "BEFORE the frozen obligation is closed verbatim — so it cannot borrow the "
        "general proof's strength. If the three clauses could not hold together "
        "there, the `have` would fail -> PRECOND-TOO-STRONG.",
    },
    {
        "id": "alias-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ALIAS_RETURN,
        "refinement": "the result shares the LEADING source's identity rather "
        "than being an independent object; F2P test_merge_attrs_override_copy "
        "mutates the merged product's attr and asserts the first source is "
        "unchanged, but a shared result mutates the source too — the test fails, "
        "so a faithful patch of this shape does NOT resolve.",
        "rationale": "rejected by C_fresh (id ∉ attrs.map Prod.fst): the result "
        "reuses the leading source's identity, so it aliases a source. Content "
        "(C_pres) holds trivially — the identity clause is the discriminator.",
        "witness": _ALIAS_WITNESS,
    },
    {
        "id": "empty-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": EMPTY_COPY,
        "refinement": "a real patch whose 'override' branch returned {} (a fresh "
        "empty dict) would carry NO attrs into the merged product; the F2P reads the "
        "first source's attr off the merged product and the merge-attrs P2P tests "
        "assert the source's attrs are present — they would fail, so it does NOT "
        "resolve.",
        "rationale": "partial-domain (correct only on an EMPTY source): a fresh "
        "empty result satisfies C_fresh (distinct id) but fails C_pres "
        "(result content = first.2) on every non-empty source. Shows C_pres "
        "(content) is independent of C_fresh (identity) — both load-bearing.",
        "witness": _EMPTY_COPY_WITNESS,
    },
    {
        "id": "skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SKIP_LAST,
        "refinement": "a real patch that dropped the LAST attribute of the leading "
        "source would make the merged product miss that attr; the merge-attrs P2P "
        "tests compare the merged attrs to a multi-entry source and would fail — it "
        "does NOT resolve.",
        "rationale": "near-miss on C_pres: the copy is a proper prefix of the "
        "source's content (drops the trailing entry), so C_pres "
        "(result content = first.2) fails on any source of length >= 2. The witness "
        "is at a TWO-entry source — the input that distinguishes this near-miss from "
        "gold (a 0/1-entry source would not).",
        "witness": _SKIP_LAST_WITNESS,
    },
    {
        "id": "empty-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": EMPTY_PRESENT,
        "refinement": "a real patch whose no-source guard returned a non-empty "
        "mapping instead of the empty-merge default would fabricate attrs on a merge "
        "with no sources; the merge pipeline's empty-input handling would carry "
        "spurious attrs and the merge P2P tests would fail — it does NOT resolve.",
        "rationale": "attacks C_none (attrs == [] -> result = none), the OTHER "
        "top-level clause: the no-source branch returns a present result. Every "
        "other rival is correct on [] and wrong only on first :: _, so this is the "
        "sole rival exercising the empty-input branch of the postcondition.",
        "witness": _EMPTY_PRESENT_WITNESS,
    },
    {
        "id": "last-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": LAST_SOURCE,
        "refinement": "a real patch reading the trailing source instead of the "
        "leading one would carry the WRONG source's attributes into the merged "
        "product under the 'override' policy; the F2P reads the leading source's "
        "attr off the merged product and the merge-attrs P2P tests pin the merged "
        "attrs to the FIRST source's — both would fail, so it does NOT resolve.",
        "rationale": "attacks the SELECTION half of C_pres (result content = "
        "first.2): the identity is still fresh and the content is still a verbatim "
        "copy of *a* source, but of the wrong one. Every other rival is correct "
        "about which source is selected, so this is the sole case exercising the "
        "choice of source at all. The witness needs TWO sources with DIFFERING "
        "contents: on a single-source input first and last coincide, and the only "
        "other multi-source witness (fresh-first-only) gives its two sources "
        "identical contents, so the selection is invisible there as well.",
        "witness": _LAST_SOURCE_WITNESS,
    },
    {
        "id": "fresh-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRESH_FIRST_ONLY,
        "refinement": "a real patch that only guaranteed the result was a distinct "
        "object from the LEADING source, while leaving it possibly shared with "
        "another source in the merge, would still alias a source object; mutating "
        "the merged product's attrs would write through to that source, which is "
        "the aliasing property the F2P pins — it does NOT resolve.",
        "rationale": "near-miss on the ∀-over-ALL-sources strength of C_fresh "
        "(id ∉ attrs.map Prod.fst): the identity is chosen fresh relative to the "
        "leading source ONLY (first.1 + 1), so it can collide with a LATER "
        "source's identity. Indistinguishable from gold on any single-source "
        "input. alias-return collides with the FIRST source, which even the "
        "weakest reading of the clause would catch; this one collides with the "
        "SECOND, so it is what makes the quantifier load-bearing. The witness is "
        "at identities 1 and 2, where 'fresh w.r.t. the first source' and 'fresh "
        "w.r.t. all sources' come apart.",
        "witness": _FIRST_ONLY_WITNESS,
    },
    {
        "id": "fresh-first-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRESH_FIRST_TWO,
        "refinement": "a real patch that established distinctness against only a "
        "bounded number of the merge's sources would still leave the result "
        "sharing a later source's object; mutating the merged product's attrs "
        "would write through to that source, which is the aliasing property the "
        "F2P pins — it does NOT resolve.",
        "rationale": "pins C_fresh (id ∉ attrs.map Prod.fst) as an "
        "∀-over-ALL-sources claim rather than a bounded-prefix one. "
        "fresh-first-only shows the quantifier reaches past the LEADING source, "
        "but its rival consults exactly one source, so a spec quantifying over any "
        "FIXED-SIZE prefix would still pass it. This rival consults the first TWO "
        "sources, is indistinguishable from gold on every input of length <= 2, and "
        "collides only at depth 3+. The witness is at three sources with identities "
        "1, 2, 3, where the rival picks 3 — the third source's own identity.",
        "witness": _FIRST_TWO_WITNESS,
    },
    {
        "id": "absent-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ABSENT_NONEMPTY,
        "refinement": "a real patch whose 'override' branch produced no mapping at "
        "all (rather than the leading source's) would leave the merged product with "
        "no attrs to read; the F2P reads the leading source's attr off the merged "
        "product and the merge-attrs P2P tests pin the merged attrs to the first "
        "source's, so both would fail — it does NOT resolve.",
        "rationale": "attacks the PRESENCE half of C_pres (attrs == first :: _ -> "
        "result = some (id, first.2)): given sources, the result must EXIST. This "
        "rival returns an absent result there. It is the mirror of empty-present "
        "(which returns a present result on NO sources): every other rival returns "
        "`some` on a non-empty input and is wrong only about the identity or the "
        "content, so before this case a spec that constrained the result only WHEN "
        "present — without requiring presence — would have passed the whole "
        "battery. The witness is at a single source, where the rival yields none "
        "and gold yields some.",
        "witness": _ABSENT_WITNESS,
    },
]


# DROPPED nagini cases, with the reason each is not portable here (verified by
# build, not asserted):
#   frame-write-source / frame-write-outer — nagini's two MANDATORY frame-mutation
#     rivals rejected by the permission system. Inexpressible here, and
#     demonstrated so: an impl that derives a "scribbled" copy of BOTH the outer
#     collection and the leading source's contents, then returns the correct
#     result, VERIFIES against the frozen spec (re-measured by build during audit:
#     such an impl elaborates cleanly, exit 0). `attrs` is an immutable value on a
#     referentially-transparent carrier, so an input write has no observable
#     footprint and there is no frame obligation for a rival to violate. The
#     aliasing consequence those rivals were really aimed at is carried here by
#     C_fresh, which alias-return and fresh-first-only both attack.
#   drop-nonempty — nagini modeled BOTH the 'drop' and 'override' policies and
#     this rival broke the drop clause (P4). This bundle's modeled slice is the
#     'override' path only (see mapping.md), so there is no mode tag and no drop
#     clause in the carrier's postcondition; the rival has nothing to violate.
#     The structurally analogous attack on the OTHER top-level clause of THIS
#     spec — the empty-input branch — is ported as `empty-present`.
#   admiss-f2p — PORTED, as the `admiss-f2p` case above. An earlier revision of
#     this manifest dropped it, reasoning that the frozen obligation quantifies
#     over ALL `attrs : List AttrObj` with no hypothesis, so there is no
#     precondition to probe. That reason was WRONG and the case is expressible: the
#     analogue of PRECOND-TOO-STRONG on a total carrier is not an unsatisfiable
#     Requires but an unsatisfiable OBLIGATION at an ordinary input. The
#     postcondition conjoins three demands under one existential (result present /
#     content = the leading source's / identity distinct from EVERY source's), and
#     the ported case discharges that conjunction at the concrete F2P shape by
#     evaluation, before closing the frozen obligation verbatim.
#
# DIVERGENCE LANE (nagini has no diverge-* case; recorded here after audit
# measurement). This bundle sets no `loom.semantics.termination` — it is the plain
# Lean carrier, where every `def` must be shown terminating at ELABORATION time,
# so the class is VACUOUS rather than a spec hole, and demonstrated so by build:
#   * A self-recursive impl with no decreasing measure
#     (`| first :: rest => implementation... (first :: first :: rest)`) is refused
#     by the elaborator itself: `fail to show termination for
#     implementation_mergeAttrsOverride / failed to infer structural recursion`
#     (exit 1). It never becomes a spec question — no such impl exists to be
#     admitted, and the rejection is attributable to the carrier's totality
#     requirement, not to the spec, so it is not shippable as a reject case (its
#     witness cannot elaborate against the rival either: measured exit 1, with
#     the same termination error, so the case would land `witness-unproven`).
#   * Writing it as `partial def` makes the impl OPAQUE rather than diverging: the
#     term no longer reduces, so nothing can be proven about it in either
#     direction — even the non-recursive `[]` arm fails
#     (`implementation_mergeAttrsOverride [] = none` by `rfl`: exit 1,
#     `Type mismatch`; by `simp`: exit 1, `simp made no progress`). A refutation
#     is therefore impossible, and so is the vacuous verification that would make
#     it a hole: the frozen obligation does not close either (exit 1). Nothing to
#     ship in either lane.

# Every case in SPEC_TESTS above keeps the `correct_mergeAttrsOverride` STATEMENT
# byte-identical to the frozen one (checked: only tactic bodies and the impl region
# differ), so no positive is earned by a weakened obligation.
