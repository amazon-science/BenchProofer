# P2 adversarial audit — django__django-11265

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,9 +125,7 @@
     (filterExpr : String × String) : InnerQuery := Id.run do
   -- A fresh inner query bound to the same model (no named relations yet).
   let mut query : InnerQuery := freshInnerQuery selfModel
-  -- Carry the originating query's named relation definitions onto the inner query
-  -- so a filter referencing one of them can be resolved here.
-  query := withFilteredRelations query selfFilteredRelations
+  -- WRONG (prepatch): named relations NOT carried onto the inner query.
   -- Apply the supplied filter clause (resolved against the relations now present).
   query := addFilter query filterExpr
   -- Drop any ordering.
@@ -141,11 +139,16 @@
       (filterExpr : String × String),
       problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
         (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
-  intro selfModel selfFilteredRelations filterExpr
-  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
-  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
-    List.nil_append]
-  refine ⟨rfl, rfl, rfl, rfl, rfl⟩
+  intro a b c
+  first
+    | (unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
+       simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
+         List.nil_append]
+       refine ⟨rfl, rfl, rfl, rfl, rfl⟩)
+    | simp_all [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering]
+    | (simp [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering] <;> rfl)
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -180,7 +180,8 @@
     (aliasOriginal aliasCollapsed : String) : JoinSelection := Id.run do
   -- The leading join can be collapsed only when it keeps no extra outer rows and
   -- carries no relation-level condition.
-  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
+  -- WRONG (prepatch): ignores carriesRelationCondition.
+  let canCollapse := (!firstJoin.keepsOuterRows)
   if canCollapse then
     return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }
   else
@@ -193,8 +194,11 @@
       (aliasOriginal aliasCollapsed : String),
       problem_spec_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed
         (implementation_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed) := by
-  intro firstJoin relatedFields aliasOriginal aliasCollapsed
-  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
-  simp only [Id.run]
-  split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all
+  intro a b c d
+  first
+    | (unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
+       simp only [Id.run]
+       split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all)
+    | simp_all [problem_spec_selectInnerJoin, implementation_selectInnerJoin, Id.run]
+    | (simp_all [problem_spec_selectInnerJoin, implementation_selectInnerJoin] <;> split <;> simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -127,7 +127,8 @@
   let mut query : InnerQuery := freshInnerQuery selfModel
   -- Carry the originating query's named relation definitions onto the inner query
   -- so a filter referencing one of them can be resolved here.
-  query := withFilteredRelations query selfFilteredRelations
+  -- WRONG (partial-domain): drop relations exactly when there is a single one.
+  query := withFilteredRelations query (if selfFilteredRelations.length = 1 then [] else selfFilteredRelations)
   -- Apply the supplied filter clause (resolved against the relations now present).
   query := addFilter query filterExpr
   -- Drop any ordering.
@@ -141,11 +142,16 @@
       (filterExpr : String × String),
       problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
         (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
-  intro selfModel selfFilteredRelations filterExpr
-  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
-  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
-    List.nil_append]
-  refine ⟨rfl, rfl, rfl, rfl, rfl⟩
+  intro a b c
+  first
+    | (unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
+       simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
+         List.nil_append]
+       refine ⟨rfl, rfl, rfl, rfl, rfl⟩)
+    | simp_all [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering]
+    | (simp [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering] <;> rfl)
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -182,9 +182,10 @@
   -- carries no relation-level condition.
   let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
   if canCollapse then
-    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }
+    -- WRONG: alias swapped.
+    return { selectFields := relatedFields.map (·.1), selectAlias := aliasOriginal }
   else
-    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }
+    return { selectFields := relatedFields.map (·.2), selectAlias := aliasCollapsed }
 -- impl-end
 
 -- proof-start
@@ -193,8 +194,11 @@
       (aliasOriginal aliasCollapsed : String),
       problem_spec_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed
         (implementation_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed) := by
-  intro firstJoin relatedFields aliasOriginal aliasCollapsed
-  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
-  simp only [Id.run]
-  split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all
+  intro a b c d
+  first
+    | (unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
+       simp only [Id.run]
+       split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all)
+    | simp_all [problem_spec_selectInnerJoin, implementation_selectInnerJoin, Id.run]
+    | (simp_all [problem_spec_selectInnerJoin, implementation_selectInnerJoin] <;> split <;> simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,11 +125,9 @@
     (filterExpr : String × String) : InnerQuery := Id.run do
   -- A fresh inner query bound to the same model (no named relations yet).
   let mut query : InnerQuery := freshInnerQuery selfModel
-  -- Carry the originating query's named relation definitions onto the inner query
-  -- so a filter referencing one of them can be resolved here.
+  -- WRONG: filter applied BEFORE relations carried (resolves against []).
+  query := addFilter query filterExpr
   query := withFilteredRelations query selfFilteredRelations
-  -- Apply the supplied filter clause (resolved against the relations now present).
-  query := addFilter query filterExpr
   -- Drop any ordering.
   query := clearOrdering query
   return query
@@ -141,11 +139,16 @@
       (filterExpr : String × String),
       problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
         (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
-  intro selfModel selfFilteredRelations filterExpr
-  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
-  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
-    List.nil_append]
-  refine ⟨rfl, rfl, rfl, rfl, rfl⟩
+  intro a b c
+  first
+    | (unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
+       simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
+         List.nil_append]
+       refine ⟨rfl, rfl, rfl, rfl, rfl⟩)
+    | simp_all [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering]
+    | (simp [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering] <;> rfl)
 -- proof-end
 
 -- post-conditions-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -182,7 +182,8 @@
   -- carries no relation-level condition.
   let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
   if canCollapse then
-    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }
+    -- WRONG: far-side names in the collapse branch too.
+    return { selectFields := relatedFields.map (·.2), selectAlias := aliasCollapsed }
   else
     return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }
 -- impl-end
@@ -193,8 +194,11 @@
       (aliasOriginal aliasCollapsed : String),
       problem_spec_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed
         (implementation_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed) := by
-  intro firstJoin relatedFields aliasOriginal aliasCollapsed
-  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
-  simp only [Id.run]
-  split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all
+  intro a b c d
+  first
+    | (unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
+       simp only [Id.run]
+       split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all)
+    | simp_all [problem_spec_selectInnerJoin, implementation_selectInnerJoin, Id.run]
+    | (simp_all [problem_spec_selectInnerJoin, implementation_selectInnerJoin] <;> split <;> simp_all)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,8 +130,7 @@
   query := withFilteredRelations query selfFilteredRelations
   -- Apply the supplied filter clause (resolved against the relations now present).
   query := addFilter query filterExpr
-  -- Drop any ordering.
-  query := clearOrdering query
+  -- WRONG: ordering not dropped.
   return query
 -- impl-end
 
@@ -141,11 +140,16 @@
       (filterExpr : String × String),
       problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
         (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
-  intro selfModel selfFilteredRelations filterExpr
-  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
-  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
-    List.nil_append]
-  refine ⟨rfl, rfl, rfl, rfl, rfl⟩
+  intro a b c
+  first
+    | (unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
+       simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
+         List.nil_append]
+       refine ⟨rfl, rfl, rfl, rfl, rfl⟩)
+    | simp_all [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering]
+    | (simp [problem_spec_buildInnerQuery, implementation_buildInnerQuery, Id.run,
+        freshInnerQuery, withFilteredRelations, addFilter, clearOrdering] <;> rfl)
 -- proof-end
 
 -- post-conditions-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Two related decisions a relational query layer makes when an `exclude(...)` over a
to-many relation is rewritten into a negated subquery.

When an exclude clause crosses a to-many relation, the layer builds a nested
*inner* query whose result the outer query tests membership against
(`WHERE NOT (pk IN (SELECT ...))`). Two pieces of behavior are modeled here.

1. **Inner-query construction.** A fresh inner query is created against the same
   model, the originating query's named filtered-relation definitions are carried
   over onto it (so a filter that references one of those named relations can be
   resolved inside the inner query), the supplied filter is applied, and any
   ordering is dropped. The named relation definitions on the inner query must be
   exactly those of the originating query — not an empty set.

2. **Leading-join selection.** Before emitting the inner query the layer may
   collapse the inner query's leading join into a plain column selection. This
   collapse is only sound when the leading join keeps every outer row AND carries
   no extra join-level restriction: an outer-keeping join would drop rows that
   have nothing on the inner side, and a join that exists only to apply a named
   relation's condition carries a restriction that would be lost if collapsed.
   When the collapse is allowed, the related fields' near-side names are selected
   against the collapsed alias; otherwise the far-side names are selected against
   the original alias.

Both behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Both decisions are pure
-- functions of observables already in hand (the originating query's model and
-- named relation definitions; the leading join's properties and the candidate
-- field/alias choices), so each is modeled deeply over its inputs and validated
-- by the differential conformance check rather than by an axiom.
-- axioms-end

-- pure-start
/-- The relevant state of the inner query built while rewriting an exclude over a
to-many relation. `filteredRelations` pairs a relation alias with its definition;
`appliedFilters` records each applied filter clause TOGETHER WITH the named
relation context it was resolved against at the moment it was applied (a clause
that references a named relation can only be resolved when that relation is
already present); `orderingCleared` records that any ordering has been dropped. -/
structure InnerQuery where
  model : String
  filteredRelations : List (String × String)
  appliedFilters : List ((String × String) × List (String × String))
  orderingCleared : Bool
deriving Repr, DecidableEq

/-- A fresh inner query bound to `model`, with no named relations, no applied
filters, and ordering not yet dropped. -/
def freshInnerQuery (model : String) : InnerQuery :=
  { model := model, filteredRelations := [], appliedFilters := [],
    orderingCleared := false }

/-- Install the named relation definitions on the query. -/
def withFilteredRelations (q : InnerQuery)
    (frs : List (String × String)) : InnerQuery :=
  { q with filteredRelations := frs }

/-- Apply a filter clause. The clause is resolved against the relation context
CURRENTLY on the query, so the recorded entry captures `q.filteredRelations` as it
stands at this point — a clause referencing a named relation absent here could not
be resolved. -/
def addFilter (q : InnerQuery) (fe : String × String) : InnerQuery :=
  { q with appliedFilters := q.appliedFilters ++ [(fe, q.filteredRelations)] }

/-- Drop any ordering on the query. -/
def clearOrdering (q : InnerQuery) : InnerQuery :=
  { q with orderingCleared := true }

/-- The two properties of a leading join that decide whether it can be collapsed:
whether it keeps every outer row (an outer-keeping join), and whether it exists to
apply a named relation's condition (and so carries a restriction). -/
structure JoinProps where
  keepsOuterRows : Bool
  carriesRelationCondition : Bool
deriving Repr, DecidableEq

/-- The outcome of the leading-join decision: which field names are selected, and
against which alias. -/
structure JoinSelection where
  selectFields : List String
  selectAlias : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for building the inner query.

Inputs:
* `selfModel`             — the model the originating query is bound to;
* `selfFilteredRelations` — the originating query's named relation definitions;
* `filterExpr`            — the filter clause to apply to the inner query.

The inner query is the fresh query for the model, with the originating query's
named relation definitions installed, THEN the supplied filter applied, THEN the
ordering dropped — in that order. Pinning the whole construction (rather than only
the final field values) determines the order: the filter must be applied with the
named relations already present, so the applied-filter entry resolves against
exactly those relations. -/
def problem_spec_buildInnerQuery
    (selfModel : String) (selfFilteredRelations : List (String × String))
    (filterExpr : String × String) (result : InnerQuery) : Prop :=
  result =
    clearOrdering (addFilter
      (withFilteredRelations (freshInnerQuery selfModel) selfFilteredRelations)
      filterExpr) ∧
  -- spelled-out consequences (frame): every field is pinned, and the applied
  -- filter was resolved against the full named-relation context.
  result.model = selfModel ∧
  result.filteredRelations = selfFilteredRelations ∧
  result.appliedFilters = [(filterExpr, selfFilteredRelations)] ∧
  result.orderingCleared = true
-- post-conditions-end

-- impl-start
def implementation_buildInnerQuery
    (selfModel : String) (selfFilteredRelations : List (String × String))
    (filterExpr : String × String) : InnerQuery := Id.run do
  -- A fresh inner query bound to the same model (no named relations yet).
  let mut query : InnerQuery := freshInnerQuery selfModel
  -- Carry the originating query's named relation definitions onto the inner query
  -- so a filter referencing one of them can be resolved here.
  query := withFilteredRelations query selfFilteredRelations
  -- Apply the supplied filter clause (resolved against the relations now present).
  query := addFilter query filterExpr
  -- Drop any ordering.
  query := clearOrdering query
  return query
-- impl-end

-- proof-start
theorem correct_buildInnerQuery :
    ∀ (selfModel : String) (selfFilteredRelations : List (String × String))
      (filterExpr : String × String),
      problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
        (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
  intro selfModel selfFilteredRelations filterExpr
  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
    List.nil_append]
  refine ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Input→output relation for the leading-join selection.

Inputs:
* `firstJoin`     — the leading join's properties (keeps outer rows? carries a
                     named relation's condition?);
* `relatedFields` — the join's related-field name pairs (near side, far side);
* `aliasOriginal` — the alias of the leading join's source table;
* `aliasCollapsed`— the alias the join would collapse onto.

The join may be collapsed only when it neither keeps outer rows nor carries a
relation condition. When collapsed, the near-side names are selected against the
collapsed alias; otherwise the far-side names are selected against the original
alias. -/
def problem_spec_selectInnerJoin
    (firstJoin : JoinProps) (relatedFields : List (String × String))
    (aliasOriginal aliasCollapsed : String) (result : JoinSelection) : Prop :=
  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
  (canCollapse = true →
      result.selectFields = relatedFields.map (·.1) ∧
      result.selectAlias = aliasCollapsed) ∧
  (canCollapse = false →
      result.selectFields = relatedFields.map (·.2) ∧
      result.selectAlias = aliasOriginal)
-- post-conditions-end

-- impl-start
def implementation_selectInnerJoin
    (firstJoin : JoinProps) (relatedFields : List (String × String))
    (aliasOriginal aliasCollapsed : String) : JoinSelection := Id.run do
  -- The leading join can be collapsed only when it keeps no extra outer rows and
  -- carries no relation-level condition.
  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
  if canCollapse then
    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }
  else
    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }
-- impl-end

-- proof-start
theorem correct_selectInnerJoin :
    ∀ (firstJoin : JoinProps) (relatedFields : List (String × String))
      (aliasOriginal aliasCollapsed : String),
      problem_spec_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed
        (implementation_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed) := by
  intro firstJoin relatedFields aliasOriginal aliasCollapsed
  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
  simp only [Id.run]
  split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** Both problem_spec_* are FULLY-PINNED functional specifications. problem_spec_buildInnerQuery pins result to `clearOrdering (addFilter (withFilteredRelations (freshInnerQuery selfModel) selfFilteredRelations) filterExpr)` by structural equality PLUS spelled-out per-field equalities (model, filteredRelations, appliedFilters=[(filterExpr,selfFilteredRelations)], orderingCleared=true). problem_spec_selectInnerJoin pins selectFields/selectAlias in both canCollapse branches (near-side/collapsed vs far-side/original). Each input therefore has a UNIQUE satisfying output, so any impl that deviates observably on any input cannot satisfy the spec — leaving no room for a verify⇏correct gap.

**SAME_SPEC:** all 7 attacks byte-identical spec view (same_spec=True; only impl regions edited).

ATTACKS (each copied Solution.lean, edited ONLY impl region, attached a best-effort CLOSING proof = gold tactic + simp_all/simp<;>rfl fallbacks via `first | ... | ...`, NOT sorry). Command per file: `bash scripts/lean_verify.sh <path>`. atk_1 (build, prepatch bug: omit withFilteredRelations) -> exit 1, 'unsolved goals' at 141:87. atk_2 (select, prepatch_2 bug: canCollapse:=!keepsOuterRows, ignores carriesRelationCondition) -> exit 1, unsolved goals 196:97. atk_3 (build, partial-domain: install [] when selfFilteredRelations.length=1 else correct) -> exit 1, unsolved goals 144:87. atk_4 (select, boundary: aliasOriginal/aliasCollapsed swapped between branches) -> exit 1, unsolved goals 196:97. atk_5 (build, control-flow: addFilter applied BEFORE withFilteredRelations, so snapshot resolves against []) -> exit 1, unsolved goals 141:87. atk_6 (select, ungrounded/echo: far-side (·.2) names used in the collapse branch too) -> exit 1, unsolved goals 196:97. atk_7 (build, effect-drop: omit clearOrdering) -> exit 1, unsolved goals 142:87.

All 7 failures are genuine 'unsolved goals' from the pinned spec rejecting the wrong output — NOT syntax/import errors. Covers partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, prepatch bugs, and effect-omission classes (>=6 distinct, both functions).

NO wrong impl produced a closing clean-axiom proof, so protocol step 2 (materialize faithful patch + run_resolve) had NOTHING to trigger on — patches={} accordingly. There is no verify⇏correct witness.

**POSITIVE CONTROL:** pos_control.lean (unmodified gold impl) -> exit 0 (verifies, no sorry). #print axioms: correct_buildInnerQuery depends on NO axioms; correct_selectInnerJoin depends on [propext] only — clean.

**PREPATCH:** both documented prepatch bugs re-encoded and confirmed to fail closure: build-side (atk_1, mirrors Solution_prepatch.lean, the test_with_exclude F2P) and select-side (atk_2, mirrors Solution_prepatch_2.lean, isolates the not-first_join.filtered_relation guard). prepatch_reproduced=true.

REFINEMENT.md AUDIT (A-leg focus, R/I mechanically covered by G-CONF): axioms-start/end block declares NO axioms and NO consumed callee contracts — confirmed against Solution.lean (empty axioms region) and axiom_check.py is a skip stub. Every refinement.md row is R, I, or A-reference; NO kind-3 (unjustified/ungrounded axiom) rows. The two A-reference legs are: (1) `withFilteredRelations query selfFilteredRelations` <-> gold-added `query._filtered_relations = self._filtered_relations`, and (2) `canCollapse := (!keepsOuterRows) && (!carriesRelationCondition)` <-> gold guard `join_type != LOUTER and not first_join.filtered_relation`. Both correspond faithfully to the actual patched expressions (verified against patch.diff summary in refinement.md and mapping.md line bindings query.py:1665-1669 and 2142-2156). conformance_check.py's ORACLE replicas use the EXACT patched expressions (carry-relations-before-filter with snapshot; the two-boolean AND guard) and SHADOWs transliterate the Lean impl op-for-op; both A-legs are exercised by edge cases + 120k fuzz on all four keepsOuter/carriesRelation combinations with pinned SEED=20240627. Correspondence holds.

**CONCLUSION:** fully-pinned spec + no closing wrong impl + clean positive control + faithful A-leg correspondence => verify⇒correct holds on the attacked surface. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Two related decisions a relational query layer makes when an `exclude(...)` over a
to-many relation is rewritten into a negated subquery.

When an exclude clause crosses a to-many relation, the layer builds a nested
*inner* query whose result the outer query tests membership against
(`WHERE NOT (pk IN (SELECT ...))`). Two pieces of behavior are modeled here.

1. **Inner-query construction.** A fresh inner query is created against the same
   model, the originating query's named filtered-relation definitions are carried
   over onto it (so a filter that references one of those named relations can be
   resolved inside the inner query), the supplied filter is applied, and any
   ordering is dropped. The named relation definitions on the inner query must be
   exactly those of the originating query — not an empty set.

2. **Leading-join selection.** Before emitting the inner query the layer may
   collapse the inner query's leading join into a plain column selection. This
   collapse is only sound when the leading join keeps every outer row AND carries
   no extra join-level restriction: an outer-keeping join would drop rows that
   have nothing on the inner side, and a join that exists only to apply a named
   relation's condition carries a restriction that would be lost if collapsed.
   When the collapse is allowed, the related fields' near-side names are selected
   against the collapsed alias; otherwise the far-side names are selected against
   the original alias.

Both behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Both decisions are pure
-- functions of observables already in hand (the originating query's model and
-- named relation definitions; the leading join's properties and the candidate
-- field/alias choices), so each is modeled deeply over its inputs and validated
-- by the differential conformance check rather than by an axiom.
-- axioms-end

-- pure-start
/-- The relevant state of the inner query built while rewriting an exclude over a
to-many relation. `filteredRelations` pairs a relation alias with its definition;
`appliedFilters` records each applied filter clause TOGETHER WITH the named
relation context it was resolved against at the moment it was applied (a clause
that references a named relation can only be resolved when that relation is
already present); `orderingCleared` records that any ordering has been dropped. -/
structure InnerQuery where
  model : String
  filteredRelations : List (String × String)
  appliedFilters : List ((String × String) × List (String × String))
  orderingCleared : Bool
deriving Repr, DecidableEq

/-- A fresh inner query bound to `model`, with no named relations, no applied
filters, and ordering not yet dropped. -/
def freshInnerQuery (model : String) : InnerQuery :=
  { model := model, filteredRelations := [], appliedFilters := [],
    orderingCleared := false }

/-- Install the named relation definitions on the query. -/
def withFilteredRelations (q : InnerQuery)
    (frs : List (String × String)) : InnerQuery :=
  { q with filteredRelations := frs }

/-- Apply a filter clause. The clause is resolved against the relation context
CURRENTLY on the query, so the recorded entry captures `q.filteredRelations` as it
stands at this point — a clause referencing a named relation absent here could not
be resolved. -/
def addFilter (q : InnerQuery) (fe : String × String) : InnerQuery :=
  { q with appliedFilters := q.appliedFilters ++ [(fe, q.filteredRelations)] }

/-- Drop any ordering on the query. -/
def clearOrdering (q : InnerQuery) : InnerQuery :=
  { q with orderingCleared := true }

/-- The two properties of a leading join that decide whether it can be collapsed:
whether it keeps every outer row (an outer-keeping join), and whether it exists to
apply a named relation's condition (and so carries a restriction). -/
structure JoinProps where
  keepsOuterRows : Bool
  carriesRelationCondition : Bool
deriving Repr, DecidableEq

/-- The outcome of the leading-join decision: which field names are selected, and
against which alias. -/
structure JoinSelection where
  selectFields : List String
  selectAlias : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for building the inner query.

Inputs:
* `selfModel`             — the model the originating query is bound to;
* `selfFilteredRelations` — the originating query's named relation definitions;
* `filterExpr`            — the filter clause to apply to the inner query.

The inner query is the fresh query for the model, with the originating query's
named relation definitions installed, THEN the supplied filter applied, THEN the
ordering dropped — in that order. Pinning the whole construction (rather than only
the final field values) determines the order: the filter must be applied with the
named relations already present, so the applied-filter entry resolves against
exactly those relations. -/
def problem_spec_buildInnerQuery
    (selfModel : String) (selfFilteredRelations : List (String × String))
    (filterExpr : String × String) (result : InnerQuery) : Prop :=
  result =
    clearOrdering (addFilter
      (withFilteredRelations (freshInnerQuery selfModel) selfFilteredRelations)
      filterExpr) ∧
  -- spelled-out consequences (frame): every field is pinned, and the applied
  -- filter was resolved against the full named-relation context.
  result.model = selfModel ∧
  result.filteredRelations = selfFilteredRelations ∧
  result.appliedFilters = [(filterExpr, selfFilteredRelations)] ∧
  result.orderingCleared = true
-- post-conditions-end

-- impl-start
def implementation_buildInnerQuery
    (selfModel : String) (selfFilteredRelations : List (String × String))
    (filterExpr : String × String) : InnerQuery := Id.run do
  -- A fresh inner query bound to the same model (no named relations yet).
  let mut query : InnerQuery := freshInnerQuery selfModel
  -- Carry the originating query's named relation definitions onto the inner query
  -- so a filter referencing one of them can be resolved here.
  query := withFilteredRelations query selfFilteredRelations
  -- Apply the supplied filter clause (resolved against the relations now present).
  query := addFilter query filterExpr
  -- Drop any ordering.
  query := clearOrdering query
  return query
-- impl-end

-- proof-start
theorem correct_buildInnerQuery :
    ∀ (selfModel : String) (selfFilteredRelations : List (String × String))
      (filterExpr : String × String),
      problem_spec_buildInnerQuery selfModel selfFilteredRelations filterExpr
        (implementation_buildInnerQuery selfModel selfFilteredRelations filterExpr) := by
  intro selfModel selfFilteredRelations filterExpr
  unfold problem_spec_buildInnerQuery implementation_buildInnerQuery
  simp only [Id.run, freshInnerQuery, withFilteredRelations, addFilter, clearOrdering,
    List.nil_append]
  refine ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Input→output relation for the leading-join selection.

Inputs:
* `firstJoin`     — the leading join's properties (keeps outer rows? carries a
                     named relation's condition?);
* `relatedFields` — the join's related-field name pairs (near side, far side);
* `aliasOriginal` — the alias of the leading join's source table;
* `aliasCollapsed`— the alias the join would collapse onto.

The join may be collapsed only when it neither keeps outer rows nor carries a
relation condition. When collapsed, the near-side names are selected against the
collapsed alias; otherwise the far-side names are selected against the original
alias. -/
def problem_spec_selectInnerJoin
    (firstJoin : JoinProps) (relatedFields : List (String × String))
    (aliasOriginal aliasCollapsed : String) (result : JoinSelection) : Prop :=
  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
  (canCollapse = true →
      result.selectFields = relatedFields.map (·.1) ∧
      result.selectAlias = aliasCollapsed) ∧
  (canCollapse = false →
      result.selectFields = relatedFields.map (·.2) ∧
      result.selectAlias = aliasOriginal)
-- post-conditions-end

-- impl-start
def implementation_selectInnerJoin
    (firstJoin : JoinProps) (relatedFields : List (String × String))
    (aliasOriginal aliasCollapsed : String) : JoinSelection := Id.run do
  -- The leading join can be collapsed only when it keeps no extra outer rows and
  -- carries no relation-level condition.
  let canCollapse := (!firstJoin.keepsOuterRows) && (!firstJoin.carriesRelationCondition)
  if canCollapse then
    return { selectFields := relatedFields.map (·.1), selectAlias := aliasCollapsed }
  else
    return { selectFields := relatedFields.map (·.2), selectAlias := aliasOriginal }
-- impl-end

-- proof-start
theorem correct_selectInnerJoin :
    ∀ (firstJoin : JoinProps) (relatedFields : List (String × String))
      (aliasOriginal aliasCollapsed : String),
      problem_spec_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed
        (implementation_selectInnerJoin firstJoin relatedFields aliasOriginal aliasCollapsed) := by
  intro firstJoin relatedFields aliasOriginal aliasCollapsed
  unfold problem_spec_selectInnerJoin implementation_selectInnerJoin
  simp only [Id.run]
  split <;> refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> first | exact ⟨rfl, rfl⟩ | simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** Both problem_spec_* are FULLY-PINNED functional specifications. problem_spec_buildInnerQuery pins result to `clearOrdering (addFilter (withFilteredRelations (freshInnerQuery selfModel) selfFilteredRelations) filterExpr)` by structural equality PLUS spelled-out per-field equalities (model, filteredRelations, appliedFilters=[(filterExpr,selfFilteredRelations)], orderingCleared=true). problem_spec_selectInnerJoin pins selectFields/selectAlias in both canCollapse branches (near-side/collapsed vs far-side/original). Each input therefore has a UNIQUE satisfying output, so any impl that deviates observably on any input cannot satisfy the spec — leaving no room for a verify⇏correct gap.

**SAME_SPEC:** all 7 attacks byte-identical spec view (same_spec=True; only impl regions edited).

ATTACKS (each copied Solution.lean, edited ONLY impl region, attached a best-effort CLOSING proof = gold tactic + simp_all/simp<;>rfl fallbacks via `first | ... | ...`, NOT sorry). Command per file: `bash scripts/lean_verify.sh <path>`. atk_1 (build, prepatch bug: omit withFilteredRelations) -> exit 1, 'unsolved goals' at 141:87. atk_2 (select, prepatch_2 bug: canCollapse:=!keepsOuterRows, ignores carriesRelationCondition) -> exit 1, unsolved goals 196:97. atk_3 (build, partial-domain: install [] when selfFilteredRelations.length=1 else correct) -> exit 1, unsolved goals 144:87. atk_4 (select, boundary: aliasOriginal/aliasCollapsed swapped between branches) -> exit 1, unsolved goals 196:97. atk_5 (build, control-flow: addFilter applied BEFORE withFilteredRelations, so snapshot resolves against []) -> exit 1, unsolved goals 141:87. atk_6 (select, ungrounded/echo: far-side (·.2) names used in the collapse branch too) -> exit 1, unsolved goals 196:97. atk_7 (build, effect-drop: omit clearOrdering) -> exit 1, unsolved goals 142:87.

All 7 failures are genuine 'unsolved goals' from the pinned spec rejecting the wrong output — NOT syntax/import errors. Covers partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, prepatch bugs, and effect-omission classes (>=6 distinct, both functions).

NO wrong impl produced a closing clean-axiom proof, so protocol step 2 (materialize faithful patch + run_resolve) had NOTHING to trigger on — patches={} accordingly. There is no verify⇏correct witness.

**POSITIVE CONTROL:** pos_control.lean (unmodified gold impl) -> exit 0 (verifies, no sorry). #print axioms: correct_buildInnerQuery depends on NO axioms; correct_selectInnerJoin depends on [propext] only — clean.

**PREPATCH:** both documented prepatch bugs re-encoded and confirmed to fail closure: build-side (atk_1, mirrors Solution_prepatch.lean, the test_with_exclude F2P) and select-side (atk_2, mirrors Solution_prepatch_2.lean, isolates the not-first_join.filtered_relation guard). prepatch_reproduced=true.

REFINEMENT.md AUDIT (A-leg focus, R/I mechanically covered by G-CONF): axioms-start/end block declares NO axioms and NO consumed callee contracts — confirmed against Solution.lean (empty axioms region) and axiom_check.py is a skip stub. Every refinement.md row is R, I, or A-reference; NO kind-3 (unjustified/ungrounded axiom) rows. The two A-reference legs are: (1) `withFilteredRelations query selfFilteredRelations` <-> gold-added `query._filtered_relations = self._filtered_relations`, and (2) `canCollapse := (!keepsOuterRows) && (!carriesRelationCondition)` <-> gold guard `join_type != LOUTER and not first_join.filtered_relation`. Both correspond faithfully to the actual patched expressions (verified against patch.diff summary in refinement.md and mapping.md line bindings query.py:1665-1669 and 2142-2156). conformance_check.py's ORACLE replicas use the EXACT patched expressions (carry-relations-before-filter with snapshot; the two-boolean AND guard) and SHADOWs transliterate the Lean impl op-for-op; both A-legs are exercised by edge cases + 120k fuzz on all four keepsOuter/carriesRelation combinations with pinned SEED=20240627. Correspondence holds.

**CONCLUSION:** fully-pinned spec + no closing wrong impl + clean positive control + faithful A-leg correspondence => verify⇒correct holds on the attacked surface. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11265 lean bundle. Two modeled functions.

Verification performed:
- Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry).
- #print axioms: correct_buildInnerQuery depends on NO axioms; correct_selectInnerJoin depends only on [propext]. No sorryAx — proofs are genuine.
- Spec regions byte-identical to meta.json region_hashes: axioms, pure, post-conditions, and spec_view ALL match (only 'proof' hash differs, which is expected/allowed). same_spec integrity holds for the spec view.
- Compared against real repo at base_commit 21aa2a5e785 (worktree) plus gold patch.diff.

buildInnerQuery ↔ split_exclude (patched): real sequence is Query(self.model); query.`_filtered_relations` = self.`_filtered_relations`; query.add_filter(filter_expr); query.clear_ordering(True). Model composes freshInnerQuery→withFilteredRelations→addFilter→clearOrdering in that exact order. Asserted outputs: model=selfModel, filteredRelations=selfFilteredRelations (non-empty, the added line), appliedFilters=[(filterExpr, selfFilteredRelations)] (snapshot of relation context at apply-time = full frs since installed before the filter — the bug-critical ordering), orderingCleared=true. Every pinned field equals real post-patch behavior on all inputs; no over-constraint (side effects intentionally not asserted).

selectInnerJoin ↔ trim_start guard (patched): real guard `first_join.join_type != LOUTER and not first_join.filtered_relation` → collapse: select_fields=[r[0]...], alias=lookup_tables[trimmed_paths+1]; else far-side r[1], alias=lookup_tables[trimmed_paths]. Model canCollapse=(!keepsOuterRows)&&(!carriesRelationCondition) with keepsOuterRows↔LOUTER, carriesRelationCondition↔bool(filtered_relation). All 4 boolean combinations map exactly to the real AND-guard branches. selectFields = relatedFields.map(·.1)/(·.2) matches r[0]/r[1]; aliases match. No diverging input across the boolean×field space.

Both modeled functions agree with the real callee on every input in their modeled domain. Spec is not too strong and does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity verified independently: markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True — both coupled edits live entirely inside the elided impl/proof regions; the solver-visible spec view is byte-identical across variants (confirmed via swebench_unified.markers.spec_view with LeanBackend.language). Gold edit: (1) split_exclude adds `query._filtered_relations = self._filtered_relations`; (2) trim_start strengthens the collapse guard with `and not first_join.filtered_relation`. Leakage screen vs the PUBLIC problem_statement (hints_text excluded): no patched repo symbol appears in the spec view (split_exclude, trim_start, `_filtered_relations`, filtered_relation, join_type, LOUTER, alias_map, query.py all absent); spec uses abstracted names (buildInnerQuery, selectInnerJoin, withFilteredRelations, keepsOuterRows, carriesRelationCondition). No file/module path, no diff markers, no reproduced gold line, no bug/fix/previously/wrong narration. Edit #1's discriminator (carry the originating query's named relations, not an empty set) is already public: problem_statement says 'A new query is created without all extra datas from the original query.' Edit #2 (the trim_start collapse guard) is not in the problem_statement, but the spec states it as an abstract input->output correctness requirement in the author's own vocabulary ('collapse only sound when the join keeps every outer row AND carries no extra join-level restriction'), with no repo localization and no verbatim hints echo. Fully specifying required correct behavior is the legitimate function of a correctness spec; it neither reconstructs nor localizes the identity/location of the gold edit. Conclusion: the spec reveals correct behavior at an abstract level but does not leak the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).