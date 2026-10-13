# P2 adversarial audit — django__django-15957

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing clean-axiom proof, so no verify-but-incorrect impl exists. The spec pins ALL THREE output fields (predicate, offset, limit) in BOTH branches (isSliced=false and isSliced=true) universally over query/fieldName/instances, leaving zero degrees of freedom.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,20 +108,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1: the prepatch bug — only the membership conjunct, never handles a
+-- slice (no per-group position bounds, bounds left untouched).
 def implementation_restrictPrefetch
     (query : RelatedQuery) (fieldName : String) (instances : List Int) :
     FilteredQuery := Id.run do
-  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
-  let mut offset := query.offset
-  let mut limit := query.limit
-  if isSliced query then
-    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
-    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
-    if let some h := query.limit then
-      predicate := predicate ++ [PredAtom.positionAtMost r h]
-    offset := 0
-    limit := none
-  return { predicate := predicate, offset := offset, limit := limit }
+  let predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
+  return { predicate := predicate, offset := query.offset, limit := query.limit }
 -- impl-end
 
 -- proof-start
@@ -131,17 +124,13 @@
         (implementation_restrictPrefetch query fieldName instances) := by
   intro query fieldName instances
   unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
-  by_cases h : isSliced query = true
-  · constructor
-    · intro hf; rw [h] at hf; exact absurd hf (by simp)
-    · intro _
-      simp only [h, if_true, Id.run, bind, pure]
-      cases hl : query.limit with
-      | none => simp
-      | some v => simp
-  · simp only [Bool.not_eq_true] at h
-    constructor
-    · intro _
-      simp only [h, Bool.false_eq_true, if_false, Id.run, bind, pure]
-    · intro hf; rw [h] at hf; exact absurd hf (by simp)
+  constructor
+  · intro hns
+    simp only [hns, Bool.false_eq_true, if_false]
+    rfl
+  · intro hs
+    simp only [hs, if_true]
+    cases query.limit with
+    | none => exact ⟨rfl, rfl, rfl⟩
+    | some h => exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,6 +108,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2 (boundary/order): appends the upper bound BEFORE the lower bound,
+-- so a sliced+limit query yields [base, positionAtMost, positionAbove] instead
+-- of the spec's [base, positionAbove, positionAtMost].
 def implementation_restrictPrefetch
     (query : RelatedQuery) (fieldName : String) (instances : List Int) :
     FilteredQuery := Id.run do
@@ -116,9 +119,9 @@
   let mut limit := query.limit
   if isSliced query then
     let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
-    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
     if let some h := query.limit then
       predicate := predicate ++ [PredAtom.positionAtMost r h]
+    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
     offset := 0
     limit := none
   return { predicate := predicate, offset := offset, limit := limit }
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,6 +108,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3 (partial-domain): only clears the bounds when a limit is present.
+-- On an offset-only slice (limit = none) it leaves offset = query.offset,
+-- violating result.offset = 0 for that sub-domain.
 def implementation_restrictPrefetch
     (query : RelatedQuery) (fieldName : String) (instances : List Int) :
     FilteredQuery := Id.run do
@@ -119,8 +122,8 @@
     predicate := predicate ++ [PredAtom.positionAbove r query.offset]
     if let some h := query.limit then
       predicate := predicate ++ [PredAtom.positionAtMost r h]
-    offset := 0
-    limit := none
+      offset := 0
+      limit := none
   return { predicate := predicate, offset := offset, limit := limit }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,6 +108,8 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4 (off-by-one / count-vs-position confusion): uses offset+1 as the
+-- lower mark, treating it as a count boundary rather than the absolute position.
 def implementation_restrictPrefetch
     (query : RelatedQuery) (fieldName : String) (instances : List Int) :
     FilteredQuery := Id.run do
@@ -116,7 +118,7 @@
   let mut limit := query.limit
   if isSliced query then
     let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
-    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
+    predicate := predicate ++ [PredAtom.positionAbove r (query.offset + 1)]
     if let some h := query.limit then
       predicate := predicate ++ [PredAtom.positionAtMost r h]
     offset := 0
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,6 +108,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5 (control-flow-effect / wrong ranking): builds the per-group Ranking
+-- with an empty ordering instead of query.ordering, so positionAbove/AtMost
+-- reference the wrong window whenever query.ordering is non-empty.
 def implementation_restrictPrefetch
     (query : RelatedQuery) (fieldName : String) (instances : List Int) :
     FilteredQuery := Id.run do
@@ -115,7 +118,7 @@
   let mut offset := query.offset
   let mut limit := query.limit
   if isSliced query then
-    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
+    let r : Ranking := { groupBy := fieldName, ordering := [] }
     predicate := predicate ++ [PredAtom.positionAbove r query.offset]
     if let some h := query.limit then
       predicate := predicate ++ [PredAtom.positionAtMost r h]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,6 +108,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6 (ungrounded-oracle / dropped-conjunct): on a sliced query it REPLACES
+-- the predicate with just the position bounds, dropping the membership base
+-- conjunct that the spec requires at the head.
 def implementation_restrictPrefetch
     (query : RelatedQuery) (fieldName : String) (instances : List Int) :
     FilteredQuery := Id.run do
@@ -116,7 +119,7 @@
   let mut limit := query.limit
   if isSliced query then
     let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
-    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
+    predicate := [PredAtom.positionAbove r query.offset]
     if let some h := query.limit then
       predicate := predicate ++ [PredAtom.positionAtMost r h]
     offset := 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Restricting a prefetch query to a set of related objects, honoring any slice.

When a collection of related objects is fetched in bulk for a group of parent
rows, the query is narrowed to the related objects that belong to those parents.
The caller may additionally ask for only a contiguous SLICE of each parent's
related objects (an `offset`, and optionally a `limit`) — for example "the first
three related objects of each parent".

The desired behavior is therefore:

  * always restrict the query to the related objects belonging to the supplied
    parents (a membership condition);
  * when no slice is requested, that membership condition is the whole
    restriction and the query is otherwise unchanged;
  * when a slice IS requested, the slice must be applied PER PARENT GROUP rather
    than to the result as a whole: keep, within each group's ordering, the
    objects whose position in the group is beyond the requested `offset` and (if
    a `limit` is given) no greater than that `limit`. Both `offset` and `limit`
    are ABSOLUTE within-group positions (the lower and upper marks of the
    requested slice), NOT counts: the upper condition keeps objects whose
    position is at most `limit`, applied directly to the position. Because the
    slice is now expressed as conditions on the query, the plain offset/limit
    bounds are dropped from the query.

`query` carries the slice bounds (`offset` = lower position mark, optional
`limit` = upper position mark) and the group ordering. `fieldName` names the
grouping relation; `instances` are the parents.
The result is the restricted query: its accumulated conditions, and its
remaining offset/limit bounds.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The query-building
-- primitives (membership condition, per-group position bounds, the slice-bound
-- query state and its "is a slice present?" test, and dropping the bounds) are
-- all modeled concretely below as data construction / pure predicates — they are
-- identical concrete ops (refinement.md), not behavioral callees that need a
-- contract. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A per-group ranking: items are positioned within each `groupBy` group
according to `ordering`. -/
structure Ranking where
  groupBy : String
  ordering : List String
  deriving DecidableEq, Repr

/-- One conjunct of the restriction accumulated on a query. -/
inductive PredAtom where
  /-- Keep only objects related to one of `instances` through `field`. -/
  | memberOf (field : String) (instances : List Int)
  /-- Keep only objects whose position within their group (per `r`) is strictly
      beyond `low`. -/
  | positionAbove (r : Ranking) (low : Nat)
  /-- Keep only objects whose position within their group (per `r`) is at most
      `high`. -/
  | positionAtMost (r : Ranking) (high : Nat)
  deriving DecidableEq, Repr

/-- A query carrying the touched state: its group `ordering`, and the slice
bounds `offset` (lower position mark, i.e. rows to skip) and optional `limit`
(upper position mark; `none` means no upper bound). Both are absolute positions,
not counts. -/
structure RelatedQuery where
  ordering : List String
  offset : Nat
  limit : Option Nat
  deriving DecidableEq, Repr

/-- A query after restriction: the accumulated conjuncts, plus the remaining
slice bounds. -/
structure FilteredQuery where
  predicate : List PredAtom
  offset : Nat
  limit : Option Nat
  deriving DecidableEq, Repr

/-- A slice is present iff a nonzero offset or any limit has been set. -/
def isSliced (q : RelatedQuery) : Bool := q.offset != 0 || q.limit.isSome
-- pure-end

-- post-conditions-start
/-- The restricted query is fully determined by the input. Its conditions always
begin with the membership condition. When no slice is present the membership
condition is the entire restriction and the bounds are unchanged. When a slice is
present, the per-group position conditions are appended (a lower bound from the
offset, and an upper bound when a limit is given) and the plain offset/limit
bounds are dropped. Every output component is pinned to the input. -/
def problem_spec_restrictPrefetch
    (query : RelatedQuery) (fieldName : String) (instances : List Int)
    (result : FilteredQuery) : Prop :=
  let base := PredAtom.memberOf fieldName instances
  let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
  (isSliced query = false →
      result = { predicate := [base], offset := query.offset, limit := query.limit }) ∧
  (isSliced query = true →
      result.offset = 0 ∧ result.limit = none ∧
      result.predicate =
        base :: PredAtom.positionAbove r query.offset ::
          (match query.limit with
           | some h => [PredAtom.positionAtMost r h]
           | none => []))
-- post-conditions-end

-- impl-start
def implementation_restrictPrefetch
    (query : RelatedQuery) (fieldName : String) (instances : List Int) :
    FilteredQuery := Id.run do
  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
    if let some h := query.limit then
      predicate := predicate ++ [PredAtom.positionAtMost r h]
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }
-- impl-end

-- proof-start
theorem correct_restrictPrefetch :
    ∀ (query : RelatedQuery) (fieldName : String) (instances : List Int),
      problem_spec_restrictPrefetch query fieldName instances
        (implementation_restrictPrefetch query fieldName instances) := by
  intro query fieldName instances
  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
  by_cases h : isSliced query = true
  · constructor
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
    · intro _
      simp only [h, if_true, Id.run, bind, pure]
      cases hl : query.limit with
      | none => simp
      | some v => simp
  · simp only [Bool.not_eq_true] at h
    constructor
    · intro _
      simp only [h, Bool.false_eq_true, if_false, Id.run, bind, pure]
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT — verify => correct holds. Protocol executed; byte-identical spec confirmed (same_spec=True for pos + all 6 attacks; only impl region edited).

SAME-SPEC CHECK (swebench_unified.markers.same_spec, lean backend): True for pos, atk_1..atk_6.

POSITIVE CONTROL pos.lean (gold impl): `bash scripts/lean_verify.sh pos.lean` -> exit 0. `#print axioms correct_restrictPrefetch` -> depends on axioms: [propext] (clean; no sorry, no Classical/Quot/native/sorryAx).

6 DISTINCT same-spec wrong impls, each verified with the faithful proof (`bash scripts/lean_verify.sh atk_N.lean`):
- atk_1 (prepatch bug: emits only membership conjunct, never handles slice, bounds untouched) -> exit 1. PREPATCH REPRODUCED.
- atk_2 (boundary/order: appends positionAtMost BEFORE positionAbove) -> exit 1.
- atk_3 (partial-domain: clears offset/limit only when a limit is present; offset-only slice leaves offset!=0) -> exit 1.
- atk_4 (off-by-one / count-vs-position: uses offset+1 as the lower mark) -> exit 1.
- atk_5 (control-flow-effect / wrong ranking: builds Ranking with ordering:=[] instead of query.ordering) -> exit 1.
- atk_6 (ungrounded-oracle / dropped-conjunct: replaces predicate with position bounds, dropping the membership base head) -> exit 1.

NONE of the 6 attacks closes. To rule out 'lazy proof' (proof merely wrong rather than spec tight), I additionally MACHINE-PROVED the spec provably REJECTS each wrong impl at a concrete witness. Disproof files dis_2..dis_6.lean each state `¬ problem_spec_restrictPrefetch <witness> (implementation_restrictPrefetch <witness>)` and close via `intro h; unfold ...; have h2 := h.2 (by decide); exact absurd <field> (by decide)`. All five verified: `bash scripts/lean_verify.sh dis_N.lean` -> exit 0 for dis_2,dis_3,dis_4,dis_5,dis_6. Witnesses: dis_2 {ordering:=[],offset:=0,limit:=some 3}; dis_3/dis_4/dis_6 {ordering:=[],offset:=1,limit:=none}; dis_5 {ordering:=["pk"],offset:=1,limit:=none}; field author, instances [1].

CONSEQUENCE: because NO same-spec wrong impl yields a closing clean-axiom proof, there is no verify-but-incorrect impl to materialize as a faithful patch; the mandatory resolve-run step (step 2) has an empty worklist — 'patches' is {} legitimately, not from a skipped check.

REFINEMENT.MD AUDIT: axioms region is EMPTY (comment-only; the '_prop' mention is conditional permission never exercised — grep of Solution.lean shows no `axiom ` decl). All 9 operation-correspondence legs are R (rows 1-2: rich Query/QuerySet -> RelatedQuery type refinement; list/str bijections) or I (rows 3-9: membership conjunct, is_sliced mirror, RowNumber window as Ranking, GreaterThan/LessThanOrEqual as position atoms, clear_limits as offset:=0/limit:=none, filter() materialization). No A-consumed, no A-reference, no kind-3 (changed-inexpressible) legs. Therefore no A-leg correspondence exists to break; the A-leg attack surface is vacuous for this bundle. The R/I legs are covered by G-CONF (conformance_check.py, seed 15957, N=200000+edge cases, lean_shadow vs gold_shadow, 0 mismatches).

VERDICT: SOUND. >=6 attacks encoded + verified (all fail to close), prepatch bug reproduced, positive control verifies with clean axioms, and the spec is machine-proved to reject each deviation. verify => correct holds; no falsification exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing clean-axiom proof, so no verify-but-incorrect impl exists. The spec pins ALL THREE output fields (predicate, offset, limit) in BOTH branches (isSliced=false and isSliced=true) universally over query/fieldName/instances, leaving zero degrees of freedom.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Restricting a prefetch query to a set of related objects, honoring any slice.

When a collection of related objects is fetched in bulk for a group of parent
rows, the query is narrowed to the related objects that belong to those parents.
The caller may additionally ask for only a contiguous SLICE of each parent's
related objects (an `offset`, and optionally a `limit`) — for example "the first
three related objects of each parent".

The desired behavior is therefore:

  * always restrict the query to the related objects belonging to the supplied
    parents (a membership condition);
  * when no slice is requested, that membership condition is the whole
    restriction and the query is otherwise unchanged;
  * when a slice IS requested, the slice must be applied PER PARENT GROUP rather
    than to the result as a whole: keep, within each group's ordering, the
    objects whose position in the group is beyond the requested `offset` and (if
    a `limit` is given) no greater than that `limit`. Both `offset` and `limit`
    are ABSOLUTE within-group positions (the lower and upper marks of the
    requested slice), NOT counts: the upper condition keeps objects whose
    position is at most `limit`, applied directly to the position. Because the
    slice is now expressed as conditions on the query, the plain offset/limit
    bounds are dropped from the query.

`query` carries the slice bounds (`offset` = lower position mark, optional
`limit` = upper position mark) and the group ordering. `fieldName` names the
grouping relation; `instances` are the parents.
The result is the restricted query: its accumulated conditions, and its
remaining offset/limit bounds.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The query-building
-- primitives (membership condition, per-group position bounds, the slice-bound
-- query state and its "is a slice present?" test, and dropping the bounds) are
-- all modeled concretely below as data construction / pure predicates — they are
-- identical concrete ops (refinement.md), not behavioral callees that need a
-- contract. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A per-group ranking: items are positioned within each `groupBy` group
according to `ordering`. -/
structure Ranking where
  groupBy : String
  ordering : List String
  deriving DecidableEq, Repr

/-- One conjunct of the restriction accumulated on a query. -/
inductive PredAtom where
  /-- Keep only objects related to one of `instances` through `field`. -/
  | memberOf (field : String) (instances : List Int)
  /-- Keep only objects whose position within their group (per `r`) is strictly
      beyond `low`. -/
  | positionAbove (r : Ranking) (low : Nat)
  /-- Keep only objects whose position within their group (per `r`) is at most
      `high`. -/
  | positionAtMost (r : Ranking) (high : Nat)
  deriving DecidableEq, Repr

/-- A query carrying the touched state: its group `ordering`, and the slice
bounds `offset` (lower position mark, i.e. rows to skip) and optional `limit`
(upper position mark; `none` means no upper bound). Both are absolute positions,
not counts. -/
structure RelatedQuery where
  ordering : List String
  offset : Nat
  limit : Option Nat
  deriving DecidableEq, Repr

/-- A query after restriction: the accumulated conjuncts, plus the remaining
slice bounds. -/
structure FilteredQuery where
  predicate : List PredAtom
  offset : Nat
  limit : Option Nat
  deriving DecidableEq, Repr

/-- A slice is present iff a nonzero offset or any limit has been set. -/
def isSliced (q : RelatedQuery) : Bool := q.offset != 0 || q.limit.isSome
-- pure-end

-- post-conditions-start
/-- The restricted query is fully determined by the input. Its conditions always
begin with the membership condition. When no slice is present the membership
condition is the entire restriction and the bounds are unchanged. When a slice is
present, the per-group position conditions are appended (a lower bound from the
offset, and an upper bound when a limit is given) and the plain offset/limit
bounds are dropped. Every output component is pinned to the input. -/
def problem_spec_restrictPrefetch
    (query : RelatedQuery) (fieldName : String) (instances : List Int)
    (result : FilteredQuery) : Prop :=
  let base := PredAtom.memberOf fieldName instances
  let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
  (isSliced query = false →
      result = { predicate := [base], offset := query.offset, limit := query.limit }) ∧
  (isSliced query = true →
      result.offset = 0 ∧ result.limit = none ∧
      result.predicate =
        base :: PredAtom.positionAbove r query.offset ::
          (match query.limit with
           | some h => [PredAtom.positionAtMost r h]
           | none => []))
-- post-conditions-end

-- impl-start
def implementation_restrictPrefetch
    (query : RelatedQuery) (fieldName : String) (instances : List Int) :
    FilteredQuery := Id.run do
  let mut predicate : List PredAtom := [PredAtom.memberOf fieldName instances]
  let mut offset := query.offset
  let mut limit := query.limit
  if isSliced query then
    let r : Ranking := { groupBy := fieldName, ordering := query.ordering }
    predicate := predicate ++ [PredAtom.positionAbove r query.offset]
    if let some h := query.limit then
      predicate := predicate ++ [PredAtom.positionAtMost r h]
    offset := 0
    limit := none
  return { predicate := predicate, offset := offset, limit := limit }
-- impl-end

-- proof-start
theorem correct_restrictPrefetch :
    ∀ (query : RelatedQuery) (fieldName : String) (instances : List Int),
      problem_spec_restrictPrefetch query fieldName instances
        (implementation_restrictPrefetch query fieldName instances) := by
  intro query fieldName instances
  unfold problem_spec_restrictPrefetch implementation_restrictPrefetch
  by_cases h : isSliced query = true
  · constructor
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
    · intro _
      simp only [h, if_true, Id.run, bind, pure]
      cases hl : query.limit with
      | none => simp
      | some v => simp
  · simp only [Bool.not_eq_true] at h
    constructor
    · intro _
      simp only [h, Bool.false_eq_true, if_false, Id.run, bind, pure]
    · intro hf; rw [h] at hf; exact absurd hf (by simp)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT — verify => correct holds. Protocol executed; byte-identical spec confirmed (same_spec=True for pos + all 6 attacks; only impl region edited).

SAME-SPEC CHECK (swebench_unified.markers.same_spec, lean backend): True for pos, atk_1..atk_6.

POSITIVE CONTROL pos.lean (gold impl): `bash scripts/lean_verify.sh pos.lean` -> exit 0. `#print axioms correct_restrictPrefetch` -> depends on axioms: [propext] (clean; no sorry, no Classical/Quot/native/sorryAx).

6 DISTINCT same-spec wrong impls, each verified with the faithful proof (`bash scripts/lean_verify.sh atk_N.lean`):
- atk_1 (prepatch bug: emits only membership conjunct, never handles slice, bounds untouched) -> exit 1. PREPATCH REPRODUCED.
- atk_2 (boundary/order: appends positionAtMost BEFORE positionAbove) -> exit 1.
- atk_3 (partial-domain: clears offset/limit only when a limit is present; offset-only slice leaves offset!=0) -> exit 1.
- atk_4 (off-by-one / count-vs-position: uses offset+1 as the lower mark) -> exit 1.
- atk_5 (control-flow-effect / wrong ranking: builds Ranking with ordering:=[] instead of query.ordering) -> exit 1.
- atk_6 (ungrounded-oracle / dropped-conjunct: replaces predicate with position bounds, dropping the membership base head) -> exit 1.

NONE of the 6 attacks closes. To rule out 'lazy proof' (proof merely wrong rather than spec tight), I additionally MACHINE-PROVED the spec provably REJECTS each wrong impl at a concrete witness. Disproof files dis_2..dis_6.lean each state `¬ problem_spec_restrictPrefetch <witness> (implementation_restrictPrefetch <witness>)` and close via `intro h; unfold ...; have h2 := h.2 (by decide); exact absurd <field> (by decide)`. All five verified: `bash scripts/lean_verify.sh dis_N.lean` -> exit 0 for dis_2,dis_3,dis_4,dis_5,dis_6. Witnesses: dis_2 {ordering:=[],offset:=0,limit:=some 3}; dis_3/dis_4/dis_6 {ordering:=[],offset:=1,limit:=none}; dis_5 {ordering:=["pk"],offset:=1,limit:=none}; field author, instances [1].

CONSEQUENCE: because NO same-spec wrong impl yields a closing clean-axiom proof, there is no verify-but-incorrect impl to materialize as a faithful patch; the mandatory resolve-run step (step 2) has an empty worklist — 'patches' is {} legitimately, not from a skipped check.

REFINEMENT.MD AUDIT: axioms region is EMPTY (comment-only; the '_prop' mention is conditional permission never exercised — grep of Solution.lean shows no `axiom ` decl). All 9 operation-correspondence legs are R (rows 1-2: rich Query/QuerySet -> RelatedQuery type refinement; list/str bijections) or I (rows 3-9: membership conjunct, is_sliced mirror, RowNumber window as Ranking, GreaterThan/LessThanOrEqual as position atoms, clear_limits as offset:=0/limit:=none, filter() materialization). No A-consumed, no A-reference, no kind-3 (changed-inexpressible) legs. Therefore no A-leg correspondence exists to break; the A-leg attack surface is vacuous for this bundle. The R/I legs are covered by G-CONF (conformance_check.py, seed 15957, N=200000+edge cases, lean_shadow vs gold_shadow, 0 mismatches).

VERDICT: SOUND. >=6 attacks encoded + verified (all fail to close), prepatch bug reproduced, positive control verifies with clean axioms, and the spec is machine-proved to reject each deviation. verify => correct holds; no falsification exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift check for django__django-15957 lean bundle (modeled fn restrictPrefetch = gold-patch _filter_prefetch_queryset).

### Verification
1. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec view (docstring, axioms(empty), pure helpers Ranking/PredAtom/RelatedQuery/FilteredQuery/isSliced, post-conditions problem_spec_restrictPrefetch) is byte-identical between prepatch and postpatch; only impl+proof regions differ. No spec drift.
2. lean_verify.sh exit 0 (compiles, no sorry). `#print axioms correct_restrictPrefetch` -> [propext] only; no sorryAx, proof is genuine.
3. Cross-checked spec against the REAL repo callees at base_commit: Query.is_sliced == `low_mark != 0 or high_mark is not None` (mirrored exactly by isSliced q = q.offset != 0 || q.limit.isSome); clear_limits == `low_mark, high_mark = 0, None` (mirrored by offset:=0; limit:=none). Gold patch: predicate = Q(field__in=instances); if is_sliced: predicate &= GreaterThan(window, low_mark); if high_mark is not None: predicate &= LessThanOrEqual(window, high_mark); clear_limits(). This matches the spec's sliced branch exactly: base :: positionAbove(offset) :: [positionAtMost(limit) when some]. The lower-bound conjunct is ALWAYS appended when sliced (even offset=0), matching the gold code which always adds GreaterThan(window, low_mark) inside the is_sliced branch. Unsliced branch: predicate=[memberOf], marks unchanged — matches (no is_sliced => only the base Q).
4. conformance_check.py: independent gold-patch shadow vs impl R/I shadow diffed over 200,018 inputs (edge cases + seed-15957 fuzz spanning unsliced/offset-only/limit-only/both/offset==limit) -> 0 mismatches, exit 0.

ASSESSMENT: The spec is neither too strong nor drifting. It is a total functional pinning; the impl provably satisfies it for all inputs and equals the gold-patch construction across the fuzz. The only refinement boundary (rich QuerySet/Query -> RelatedQuery carrying just offset/limit/ordering; RowNumber window -> opaque Ranking carrier) is declared R in refinement.md and carries the touched marks unchanged into both shadows, producing no observable divergence in the modeled output. No input distinguishes the modeled function from the real callee within the modeling boundary. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage / gold-reconstruction audit of the lean spec view for django__django-15957.

PRE-CHECKS: (1) leakage.screen(Solution.lean, lean, gold_patch, problem_statement) -> PASSED, 0 hard_failures (no diff markers, no >=8-char gold-patch line reproduced, no patched file path/module, no spec-view identifier embedding patched symbols {filter_prefetch_queryset, get_prefetch_queryset, Child}, no narration). (2) markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True -> the consumer-visible region (docstring+axioms+pure+post-conditions) is byte-identical across the bug/fix pair; nothing fix-specific injected into the shared spec. (3) meta G-LEAK=pass 'spec view clean'; relaxed_leakage=None and no RELAXED_LEAKAGE.md -> strict lexical policy applies, honored.

LEAKAGE JUDGMENT vs PUBLIC problem_statement ONLY (hints_text excluded): The gold edit adds _filter_prefetch_queryset using Window(RowNumber(), partition_by=field_name, order_by=...), GreaterThan(window, low_mark), conditional LessThanOrEqual(window, high_mark), and clear_limits(). Grep of the full spec view for the distinctive gold mechanism/identifiers -> 0 occurrences of: rownumber, row_number, window, partition, clear_limits, low_mark, high_mark, greaterthan, lessthanorequal, _filter_prefetch, get_prefetch, related_descriptors, is_sliced, subquery, outerref, queryset, __in, get_compiler, get_order_by. Only substring hit 'rank' (5x) is inside the neutral structure name 'Ranking' (a generic per-group positioning carrier); gold uses RowNumber, not Rank. The specific row-number/window/partition mechanism is disclosed only in hints_text, which is NOT part of the solver-visible baseline and which G-LEAK correctly does not credit.

The public problem_statement discloses the SYMPTOM ('Prefetch objects don't work with slices' -> AssertionError: Cannot filter a query once a slice has been taken) and the FEATURE (a couple example objects per category efficiently, without loading thousands into memory). The spec's behavioral content is derivable from these: per-parent-group positional slicing (from the per-category-examples feature) and dropping the plain offset/limit bounds so the query is refilterable (directly from the 'cannot filter once a slice is taken' symptom). The spec abstracts the gold ORM window mechanism to 'position within group' -- strictly more abstract than even the hints -- and names no gold symbols, file paths, or ORM constructs. Spec vocabulary is neutral behavior-level (RelatedQuery, PredAtom, positionAbove/positionAtMost, Ranking{groupBy,ordering}, restrictPrefetch, isSliced).

CONCLUSION: NO-LEAKAGE. No spec-view line hands the solver the gold edit beyond the public problem_statement. Concurs with prior G-LEAK and recorded G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
