# P2 adversarial audit — django__django-11885

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,10 +76,7 @@
     (rels : List (Table × Column)) : List (Table × List Column) := Id.run do
   let mut groups : List (Table × List Column) := []
   for p in rels do
-    if groups.any (fun q => q.1 == p.1) then
-      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
-    else
-      groups := groups ++ [(p.1, [p.2])]
+    groups := groups ++ [(p.1, [p.2])]
   return groups
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,14 +73,8 @@
 
 -- impl-start
 def implementation_combineFastDeletes
-    (rels : List (Table × Column)) : List (Table × List Column) := Id.run do
-  let mut groups : List (Table × List Column) := []
-  for p in rels do
-    if groups.any (fun q => q.1 == p.1) then
-      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
-    else
-      groups := groups ++ [(p.1, [p.2])]
-  return groups
+    (rels : List (Table × Column)) : List (Table × List Column) :=
+  []
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
   let mut groups : List (Table × List Column) := []
   for p in rels do
     if groups.any (fun q => q.1 == p.1) then
-      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
+      groups := groups.map (fun q => if q.1 == p.1 then (q.1, [p.2] ++ q.2) else q)
     else
       groups := groups ++ [(p.1, [p.2])]
   return groups
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
   let mut groups : List (Table × List Column) := []
   for p in rels do
     if groups.any (fun q => q.1 == p.1) then
-      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
+      groups := groups.map (fun q => if q.1 == p.1 then (q.1, [p.2]) else q)
     else
       groups := groups ++ [(p.1, [p.2])]
   return groups
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,14 +73,8 @@
 
 -- impl-start
 def implementation_combineFastDeletes
-    (rels : List (Table × Column)) : List (Table × List Column) := Id.run do
-  let mut groups : List (Table × List Column) := []
-  for p in rels do
-    if groups.any (fun q => q.1 == p.1) then
-      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
-    else
-      groups := groups ++ [(p.1, [p.2])]
-  return groups
+    (rels : List (Table × Column)) : List (Table × List Column) :=
+  groupByTable rels
 -- impl-end
 
 -- proof-start
@@ -88,37 +82,6 @@
     ∀ (rels : List (Table × Column)),
       problem_spec_combineFastDeletes rels
         (implementation_combineFastDeletes rels) := by
-  have helper : ∀ (xs : List (Table × Column)) (init : List (Table × List Column)),
-      Id.run (forIn xs init (fun p r =>
-        if (r.any fun q => q.1 == p.1) = true then
-          pure (ForInStep.yield (List.map (fun q => if (q.1 == p.1) = true then (q.1, q.2 ++ [p.2]) else q) r))
-        else
-          pure (ForInStep.yield (r ++ [(p.1, [p.2])]))))
-      = List.foldl (fun acc p => insertRelation acc p.1 p.2) init xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : (init.any fun q => q.1 == a.1) = true
-      · simp only [h, if_true, List.foldl_cons, insertRelation, ih]
-      · simp only [Bool.not_eq_true] at h
-        simp only [h, Bool.false_eq_true, if_false, List.foldl_cons, insertRelation, ih]
   intro rels
-  unfold problem_spec_combineFastDeletes implementation_combineFastDeletes groupByTable
-  have h2 : (Id.run do
-      let mut groups : List (Table × List Column) := []
-      for p in rels do
-        if groups.any (fun q => q.1 == p.1) then
-          groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
-        else
-          groups := groups ++ [(p.1, [p.2])]
-      return groups) = Id.run (forIn rels [] (fun p r =>
-        if (r.any fun q => q.1 == p.1) = true then
-          pure (ForInStep.yield (List.map (fun q => if (q.1 == p.1) = true then (q.1, q.2 ++ [p.2]) else q) r))
-        else
-          pure (ForInStep.yield (r ++ [(p.1, [p.2])])))) := rfl
-  rw [h2, helper]
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
     if groups.any (fun q => q.1 == p.1) then
       groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
     else
-      groups := groups ++ [(p.1, [p.2])]
+      groups := (p.1, [p.2]) :: groups
   return groups
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
   let mut groups : List (Table × List Column) := []
   for p in rels do
     if groups.any (fun q => q.1 == p.1) then
-      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
+      groups := groups.map (fun q => if q.1 == p.1 then (q.1, (q.2 ++ [p.2]).eraseDups) else q)
     else
       groups := groups ++ [(p.1, [p.2])]
   return groups
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `correct.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the bulk-deletion operations that a cascading delete schedules.

When a record is deleted, every relation that cascades from it contributes a
bulk deletion of the rows on the far side of that relation. Each such cascading
relation is described by two observables:

  * the target table the cascade lands on (its identity), and
  * the column the relation joins on.

Several distinct relations may land on the SAME target table (a table that is
referenced from the deleted record through more than one column). The naive
schedule issues one bulk deletion per relation, so a table referenced through
`k` columns is hit by `k` separate operations.

The desired behavior groups the scheduled operations by their target table: the
relations landing on one table are merged into a single bulk operation for that
table, carrying the list of all the columns those relations join on. Concretely,
given the relations in the order they are discovered, the result is one entry per
distinct target table — the tables in first-discovery order — and within each
entry the joined columns in the order their relations were discovered. A table
referenced through several columns therefore yields exactly ONE operation rather
than several.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each cascading
-- relation enters as plain data — a pair of (target-table identity, joined-column
-- identity); the decision under spec is purely how those pairs are grouped by
-- their target table, modeled directly as an order-preserving grouping fold.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A target table identity. Modeled as a `Nat` (an injective encoding of the
distinct table identities; only equality is observed). -/
abbrev Table := Nat

/-- A joined-column identity, likewise modeled as a `Nat`. -/
abbrev Column := Nat

/-- Insert one relation `(m, f)` into the running grouping. If the target table
`m` already has an entry, append the column `f` to that entry's column list (in
discovery order); otherwise start a new entry for `m` at the end (so tables keep
their first-discovery order). -/
def insertRelation (acc : List (Table × List Column)) (m : Table) (f : Column) :
    List (Table × List Column) :=
  if acc.any (fun p => p.1 == m) then
    acc.map (fun p => if p.1 == m then (p.1, p.2 ++ [f]) else p)
  else
    acc ++ [(m, [f])]

/-- Group the scheduled relations by their target table, preserving the
first-discovery order of tables and, within each table, the discovery order of
the joined columns. -/
def groupByTable (rels : List (Table × Column)) : List (Table × List Column) :=
  rels.foldl (fun acc p => insertRelation acc p.1 p.2) []
-- pure-end

-- post-conditions-start
/-- The scheduled bulk operations, fully pinned to the input relations: the
result is exactly the relations grouped by their target table — one entry per
distinct table in first-discovery order, each carrying the joined columns of the
relations landing on that table in discovery order. This determines the result
for every input, so no output component is left free. -/
def problem_spec_combineFastDeletes
    (rels : List (Table × Column)) (result : List (Table × List Column)) : Prop :=
  result = groupByTable rels
-- post-conditions-end

-- impl-start
def implementation_combineFastDeletes
    (rels : List (Table × Column)) : List (Table × List Column) := Id.run do
  let mut groups : List (Table × List Column) := []
  for p in rels do
    if groups.any (fun q => q.1 == p.1) then
      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
    else
      groups := groups ++ [(p.1, [p.2])]
  return groups
-- impl-end

-- proof-start
theorem correct_combineFastDeletes :
    ∀ (rels : List (Table × Column)),
      problem_spec_combineFastDeletes rels
        (implementation_combineFastDeletes rels) := by
  have helper : ∀ (xs : List (Table × Column)) (init : List (Table × List Column)),
      Id.run (forIn xs init (fun p r =>
        if (r.any fun q => q.1 == p.1) = true then
          pure (ForInStep.yield (List.map (fun q => if (q.1 == p.1) = true then (q.1, q.2 ++ [p.2]) else q) r))
        else
          pure (ForInStep.yield (r ++ [(p.1, [p.2])]))))
      = List.foldl (fun acc p => insertRelation acc p.1 p.2) init xs := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : (init.any fun q => q.1 == a.1) = true
      · simp only [h, if_true, List.foldl_cons, insertRelation, ih]
      · simp only [Bool.not_eq_true] at h
        simp only [h, Bool.false_eq_true, if_false, List.foldl_cons, insertRelation, ih]
  intro rels
  unfold problem_spec_combineFastDeletes implementation_combineFastDeletes groupByTable
  have h2 : (Id.run do
      let mut groups : List (Table × List Column) := []
      for p in rels do
        if groups.any (fun q => q.1 == p.1) then
          groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
        else
          groups := groups ++ [(p.1, [p.2])]
      return groups) = Id.run (forIn rels [] (fun p r =>
        if (r.any fun q => q.1 == p.1) = true then
          pure (ForInStep.yield (List.map (fun q => if (q.1 == p.1) = true then (q.1, q.2 ++ [p.2]) else q) r))
        else
          pure (ForInStep.yield (r ++ [(p.1, [p.2])])))) := rfl
  rw [h2, helper]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Fully-pinned spec: problem_spec_combineFastDeletes rels result := result = groupByTable rels (no free output component, no partial domain, no A-legs). Audited, project root.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (axioms/pure/pre/post byte-identical; only impl+proof region edited).

POSITIVE CONTROL: correct.lean (=gold Solution.lean) -> `bash scripts/lean_verify.sh .../correct.lean` exit=0.

### ATTACKS (>=6 distinct wrong impls; cmd = `bash scripts/lean_verify.sh .../atk_N.lean`):
- atk_1 prepatch bug (one singleton entry per relation, never combine by table): exit=1 (proof goal reduces to false equation vs groupByTable). Reproduces the real bug.
- atk_2 partial-domain / trivial ([] always): exit=1.
- atk_3 boundary (prepend column [p.2]++q.2 -> wrong within-table column order): exit=1.
- atk_4 control-flow-effect (replace existing entry's cols with [p.2], keep last only): exit=1.
- atk_5 ungrounded-oracle echo (impl := groupByTable rels; proof by rfl): exit=0. `#print axioms correct_combineFastDeletes` => 'does not depend on any axioms' (clean). This is the ONLY closing attack; it is behaviorally IDENTICAL to gold (combine-by-table), so its faithful refined patch = gold patch.
- atk_6 table-order (new tables prepended via ::, reverses first-discovery table order): exit=1.
- atk_7 dedup columns ((q.2++[p.2]).eraseDups drops repeated join columns): exit=1.

RESOLVE (executed, not speculated) for the closing attack atk_5: run_resolve('django__django-11885', <atk_5 faithful patch = gold patch>, timeout=1800) => resolved=True. FAIL_TO_PASS test_fast_delete_combined_relationships PASS; all 43 PASS_TO_PASS PASS; 0 failures. Under the 2026-08-06 G-PANEL-1/eq echo policy a resolving same-spec echo is NOT a weakness. No closing attack has a non-resolving patch => no break.

REFINEMENT AUDIT: refinement.md legs are all R/I (5 ops: I accumulator init; R iterate fast-deletable rels; R append-to-existing-key; R new-key-at-end; R materialize .items()). No A-leg claimed; meta.json axioms=[] and deep_model_references=[]; axioms-region contains no axiom/opaque decls; axiom_check.py is a skip stub. Boundary is defensible: callees get_candidate_relations_to_delete/can_fast_delete/related_objects pre-filter WHICH relations are fast-deletable (they enter as the rels data), while the modeled decision (defaultdict(list) grouping + insertion-ordered .items()) is modeled DEEPLY as groupByTable. No kind-3 leg. conformance_check.py (groupByTable shadow vs real Python defaultdict(list) oracle) => checked=120008 disagreements=0 status=pass, confirming the model<->patch (ordered key + per-key value) correspondence.

CONCLUSION: The complete functional pin (result = groupByTable rels) admits no genuinely-wrong same-spec impl that closes correct_ (6 distinct wrong classes all fail proof); the sole closing impl is a correct echo whose materialized faithful patch RESOLVES under the live harness. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `correct.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the bulk-deletion operations that a cascading delete schedules.

When a record is deleted, every relation that cascades from it contributes a
bulk deletion of the rows on the far side of that relation. Each such cascading
relation is described by two observables:

  * the target table the cascade lands on (its identity), and
  * the column the relation joins on.

Several distinct relations may land on the SAME target table (a table that is
referenced from the deleted record through more than one column). The naive
schedule issues one bulk deletion per relation, so a table referenced through
`k` columns is hit by `k` separate operations.

The desired behavior groups the scheduled operations by their target table: the
relations landing on one table are merged into a single bulk operation for that
table, carrying the list of all the columns those relations join on. Concretely,
given the relations in the order they are discovered, the result is one entry per
distinct target table — the tables in first-discovery order — and within each
entry the joined columns in the order their relations were discovered. A table
referenced through several columns therefore yields exactly ONE operation rather
than several.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each cascading
-- relation enters as plain data — a pair of (target-table identity, joined-column
-- identity); the decision under spec is purely how those pairs are grouped by
-- their target table, modeled directly as an order-preserving grouping fold.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A target table identity. Modeled as a `Nat` (an injective encoding of the
distinct table identities; only equality is observed). -/
abbrev Table := Nat

/-- A joined-column identity, likewise modeled as a `Nat`. -/
abbrev Column := Nat

/-- Insert one relation `(m, f)` into the running grouping. If the target table
`m` already has an entry, append the column `f` to that entry's column list (in
discovery order); otherwise start a new entry for `m` at the end (so tables keep
their first-discovery order). -/
def insertRelation (acc : List (Table × List Column)) (m : Table) (f : Column) :
    List (Table × List Column) :=
  if acc.any (fun p => p.1 == m) then
    acc.map (fun p => if p.1 == m then (p.1, p.2 ++ [f]) else p)
  else
    acc ++ [(m, [f])]

/-- Group the scheduled relations by their target table, preserving the
first-discovery order of tables and, within each table, the discovery order of
the joined columns. -/
def groupByTable (rels : List (Table × Column)) : List (Table × List Column) :=
  rels.foldl (fun acc p => insertRelation acc p.1 p.2) []
-- pure-end

-- post-conditions-start
/-- The scheduled bulk operations, fully pinned to the input relations: the
result is exactly the relations grouped by their target table — one entry per
distinct table in first-discovery order, each carrying the joined columns of the
relations landing on that table in discovery order. This determines the result
for every input, so no output component is left free. -/
def problem_spec_combineFastDeletes
    (rels : List (Table × Column)) (result : List (Table × List Column)) : Prop :=
  result = groupByTable rels
-- post-conditions-end

-- impl-start
def implementation_combineFastDeletes
    (rels : List (Table × Column)) : List (Table × List Column) := Id.run do
  let mut groups : List (Table × List Column) := []
  for p in rels do
    if groups.any (fun q => q.1 == p.1) then
      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
    else
      groups := groups ++ [(p.1, [p.2])]
  return groups
-- impl-end

-- proof-start
theorem correct_combineFastDeletes :
    ∀ (rels : List (Table × Column)),
      problem_spec_combineFastDeletes rels
        (implementation_combineFastDeletes rels) := by
  have helper : ∀ (xs : List (Table × Column)) (init : List (Table × List Column)),
      Id.run (forIn xs init (fun p r =>
        if (r.any fun q => q.1 == p.1) = true then
          pure (ForInStep.yield (List.map (fun q => if (q.1 == p.1) = true then (q.1, q.2 ++ [p.2]) else q) r))
        else
          pure (ForInStep.yield (r ++ [(p.1, [p.2])]))))
      = List.foldl (fun acc p => insertRelation acc p.1 p.2) init xs := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : (init.any fun q => q.1 == a.1) = true
      · simp only [h, if_true, List.foldl_cons, insertRelation, ih]
      · simp only [Bool.not_eq_true] at h
        simp only [h, Bool.false_eq_true, if_false, List.foldl_cons, insertRelation, ih]
  intro rels
  unfold problem_spec_combineFastDeletes implementation_combineFastDeletes groupByTable
  have h2 : (Id.run do
      let mut groups : List (Table × List Column) := []
      for p in rels do
        if groups.any (fun q => q.1 == p.1) then
          groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)
        else
          groups := groups ++ [(p.1, [p.2])]
      return groups) = Id.run (forIn rels [] (fun p r =>
        if (r.any fun q => q.1 == p.1) = true then
          pure (ForInStep.yield (List.map (fun q => if (q.1 == p.1) = true then (q.1, q.2 ++ [p.2]) else q) r))
        else
          pure (ForInStep.yield (r ++ [(p.1, [p.2])])))) := rfl
  rw [h2, helper]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Fully-pinned spec: problem_spec_combineFastDeletes rels result := result = groupByTable rels (no free output component, no partial domain, no A-legs). Audited, project root.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (axioms/pure/pre/post byte-identical; only impl+proof region edited).

POSITIVE CONTROL: correct.lean (=gold Solution.lean) -> `bash scripts/lean_verify.sh .../correct.lean` exit=0.

### ATTACKS (>=6 distinct wrong impls; cmd = `bash scripts/lean_verify.sh .../atk_N.lean`):
- atk_1 prepatch bug (one singleton entry per relation, never combine by table): exit=1 (proof goal reduces to false equation vs groupByTable). Reproduces the real bug.
- atk_2 partial-domain / trivial ([] always): exit=1.
- atk_3 boundary (prepend column [p.2]++q.2 -> wrong within-table column order): exit=1.
- atk_4 control-flow-effect (replace existing entry's cols with [p.2], keep last only): exit=1.
- atk_5 ungrounded-oracle echo (impl := groupByTable rels; proof by rfl): exit=0. `#print axioms correct_combineFastDeletes` => 'does not depend on any axioms' (clean). This is the ONLY closing attack; it is behaviorally IDENTICAL to gold (combine-by-table), so its faithful refined patch = gold patch.
- atk_6 table-order (new tables prepended via ::, reverses first-discovery table order): exit=1.
- atk_7 dedup columns ((q.2++[p.2]).eraseDups drops repeated join columns): exit=1.

RESOLVE (executed, not speculated) for the closing attack atk_5: run_resolve('django__django-11885', <atk_5 faithful patch = gold patch>, timeout=1800) => resolved=True. FAIL_TO_PASS test_fast_delete_combined_relationships PASS; all 43 PASS_TO_PASS PASS; 0 failures. Under the 2026-08-06 G-PANEL-1/eq echo policy a resolving same-spec echo is NOT a weakness. No closing attack has a non-resolving patch => no break.

REFINEMENT AUDIT: refinement.md legs are all R/I (5 ops: I accumulator init; R iterate fast-deletable rels; R append-to-existing-key; R new-key-at-end; R materialize .items()). No A-leg claimed; meta.json axioms=[] and deep_model_references=[]; axioms-region contains no axiom/opaque decls; axiom_check.py is a skip stub. Boundary is defensible: callees get_candidate_relations_to_delete/can_fast_delete/related_objects pre-filter WHICH relations are fast-deletable (they enter as the rels data), while the modeled decision (defaultdict(list) grouping + insertion-ordered .items()) is modeled DEEPLY as groupByTable. No kind-3 leg. conformance_check.py (groupByTable shadow vs real Python defaultdict(list) oracle) => checked=120008 disagreements=0 status=pass, confirming the model<->patch (ordered key + per-key value) correspondence.

CONCLUSION: The complete functional pin (result = groupByTable rels) admits no genuinely-wrong same-spec impl that closes correct_ (6 distinct wrong classes all fail proof); the sole closing impl is a correct echo whose materialized faithful patch RESOLVES under the live harness. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled decision: how Collector.collect SCHEDULES its fast-delete bulk operations. Gold patch (deletion.py) replaces per-relation `self.fast_deletes.append(sub_objs)` with `model_fast_deletes = defaultdict(list)`; `model_fast_deletes[related_model].append(field)`; then emission via `for related_model, related_fields in model_fast_deletes.items()`. The Lean `groupByTable`/`insertRelation` fold transliterates this exactly: a new table entry is appended at END (first-discovery key order = dict insertion order), a repeat table appends its column to that entry's list (append order). Python>=3.7 dict/.items() preserve key-insertion + per-key append order, so the ordered-list comparison is the correct oracle.

### VERIFICATION (re-run, not trusted from meta.json):
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_combineFastDeletes -> [propext, Quot.sound]; NO sorryAx. Proof genuine.
- Bundle conformance_check.py: checked=120008, disagreements=0 (real Python defaultdict oracle vs shadow of implementation).
- Independent adversarial differential (500,000 random inputs, tables/columns in 0..8, list lengths 0..12) against a real Python defaultdict(list)+.items() oracle: 0 mismatches. Includes multi-column-per-table (the fix's target case) and duplicate-column cases.

ABSTRACTION BOUNDARY: Input `rels` = the pre-filtered fast-deletable cascade relations, each (related_model identity, field.name). The selection gates (can_fast_delete, on_delete==DO_NOTHING, keep_parents) are byte-verifiably UNCHANGED between pre/post patch in patch.diff (lines move, conditions identical); they only decide WHICH relations reach the grouping and are upstream of the modeled decision. The bug+fix are precisely the grouping/emission step, modeled deeply as groupByTable (I/R op, no axiom). Modeling model identity and field.name as injective Nat observes only equality, matching dict keying and column-list use exactly. Public problem_statement frames the behavior as 'combine such queries by table', so the modeled scope matches the public intent.

No input distinguishes the modeled function from the real callee. Spec is neither too strong nor drifting from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Assessed the actual consumer spec view (markers.spec_view over Solution.lean via LeanBackend); spec region is byte-identical pre/post-patch (same_spec=True), so it encodes desired behavior only, not the gold impl. The public problem_statement ('Combine fast delete queries') already discloses the fix: 'the collection logic should combine such queries by table to reduce the number of roundtrips', with a worked example combining N per-relation DELETEs into one per-table query via OR (person_friends WHERE from_id OR to_id; entry WHERE created_by_id OR updated_by). The spec view restates exactly this in neutral vocabulary (group scheduled bulk deletions by target table; merge relations landing on the same table into a single operation carrying all their join columns), adding only a first-discovery ordering discipline that is a faithful refinement of the observable output, not an implementation secret. It leaks NONE of the gold patch's identifying specifics beyond problem_statement: no defaultdict/model_fast_deletes, related_objects/get_del_batches/can_fast_delete, reduce/operator.or_/query_utils/partial, or Collector.collect, and no file/line references. Modeled name combineFastDeletes reuses only 'combine'/'fast delete' (both in the public title); Table/Column/groupByTable/insertRelation are abstract modeling identifiers, not patched Python symbols. No line in the spec view discloses the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
