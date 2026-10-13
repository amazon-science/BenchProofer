# P2 adversarial audit — django__django-12325

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_drop_o2o.lean`, `atk_3_or.lean`, `atk_4_no_lww.lean`, `atk_5_first_wins.lean`, `atk_6_empty.lean`, `atk_7_reverse.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Input fields = [{isOneToOne=true, parentLink=true, relatedKey="M", name="ptr"}, {isOneToOne=true, parentLink=false, relatedKey="M", name="other"}] (a genuine parent-link OneToOne followed by a later non-parent-link OneToOne to the SAME base M). Spec buildParentLinks records only the parent-link field -> [("M", ptr)]. The prepatch/atk_1 impl (guard drops the parentLink conjunct) records both last-write-wins -> [("M", other)], the wrong field. Proved distinct in Lean by `decide` (witness.lean): impl_prepatch inp ≠ buildParentLinks inp. This is exactly the FAIL_TO_PASS shape (test_onetoone_with_parent_model / test_clash_parent_link).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,48 +84,18 @@
     List (String × FieldInfo) := Id.run do
   let mut parentLinks : List (String × FieldInfo) := []
   for field in fields do
-    if field.isOneToOne && field.parentLink then
+    if field.isOneToOne then
       parentLinks := dictInsert parentLinks field.relatedKey field
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 2 — `atk_2_drop_o2o.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,48 +84,18 @@
     List (String × FieldInfo) := Id.run do
   let mut parentLinks : List (String × FieldInfo) := []
   for field in fields do
-    if field.isOneToOne && field.parentLink then
+    if field.parentLink then
       parentLinks := dictInsert parentLinks field.relatedKey field
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 3 — `atk_3_or.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,48 +84,18 @@
     List (String × FieldInfo) := Id.run do
   let mut parentLinks : List (String × FieldInfo) := []
   for field in fields do
-    if field.isOneToOne && field.parentLink then
+    if field.isOneToOne || field.parentLink then
       parentLinks := dictInsert parentLinks field.relatedKey field
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 4 — `atk_4_no_lww.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,47 +85,17 @@
   let mut parentLinks : List (String × FieldInfo) := []
   for field in fields do
     if field.isOneToOne && field.parentLink then
-      parentLinks := dictInsert parentLinks field.relatedKey field
+      parentLinks := parentLinks ++ [(field.relatedKey, field)]
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 5 — `atk_5_first_wins.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,47 +85,18 @@
   let mut parentLinks : List (String × FieldInfo) := []
   for field in fields do
     if field.isOneToOne && field.parentLink then
-      parentLinks := dictInsert parentLinks field.relatedKey field
+      if parentLinks.all (fun p => p.1 ≠ field.relatedKey) then
+        parentLinks := parentLinks ++ [(field.relatedKey, field)]
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 6 — `atk_6_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,49 +83,18 @@
 def implementation_collectParentLinks (fields : List FieldInfo) :
     List (String × FieldInfo) := Id.run do
   let mut parentLinks : List (String × FieldInfo) := []
-  for field in fields do
-    if field.isOneToOne && field.parentLink then
-      parentLinks := dictInsert parentLinks field.relatedKey field
+  for _field in fields do
+    pure ()
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 7 — `atk_7_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,46 +86,17 @@
   for field in fields do
     if field.isOneToOne && field.parentLink then
       parentLinks := dictInsert parentLinks field.relatedKey field
+  parentLinks := parentLinks.reverse
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
   unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  simp [Id.run, dictInsert]
+  <;> rfl
 -- proof-end
```

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -82,50 +82,15 @@
 -- impl-start
 def implementation_collectParentLinks (fields : List FieldInfo) :
     List (String × FieldInfo) := Id.run do
-  let mut parentLinks : List (String × FieldInfo) := []
-  for field in fields do
-    if field.isOneToOne && field.parentLink then
-      parentLinks := dictInsert parentLinks field.relatedKey field
+  let mut parentLinks : List (String × FieldInfo) := buildParentLinks fields
   return parentLinks
 -- impl-end
 
 -- proof-start
-/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
-the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
-theorem forIn_collectParentLinks (fields : List FieldInfo)
-    (init : List (String × FieldInfo)) :
-    Id.run (forIn fields init (fun field r =>
-        (if (field.isOneToOne && field.parentLink) = true then
-          ForInStep.yield (dictInsert r field.relatedKey field)
-        else ForInStep.yield r : Id _))) =
-      List.foldl
-        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
-        init fields := by
-  induction fields generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isOneToOne && a.parentLink) = true
-    · simp only [h, List.foldl_cons, if_true, ih]
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]
-
 theorem correct_collectParentLinks :
     ∀ (fields : List FieldInfo),
       problem_spec_collectParentLinks fields
         (implementation_collectParentLinks fields) := by
   intro fields
-  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
-  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
-              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
-          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
-              (if (field.isOneToOne && field.parentLink) = true then
-                ForInStep.yield (dictInsert r field.relatedKey field)
-              else ForInStep.yield r : Id _))) := rfl
-  simp only [Id.run]
-  rw [h2]
-  exact forIn_collectParentLinks fields []
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the parent-link mapping while a model class is assembled.

When a model participates in multi-table inheritance, one of its one-to-one
relations to a base model is the *parent link*: the relation whose column is
promoted to the child's primary key. A model may declare several one-to-one
relations pointing at the very same base model — only the one explicitly
designated as the parent link should fill that role; the others are ordinary
relations and must not be mistaken for the link.

The mapping under construction associates each related-model identity with the
field that links to it. It is built by scanning the candidate fields in order and
recording, keyed by the related-model identity, the field that links to that
model. The association is last-write-wins: recording a field for a key that is
already present replaces the earlier entry.

Each candidate field exposes:

  * `isOneToOne`   — whether it is a one-to-one relation;
  * `parentLink`   — whether it is designated the parent link for its target;
  * `relatedKey`   — the identity of the related model it points at (the map key);
  * `name`         — the field's own stable identity.

A field is recorded into the mapping exactly when it is a one-to-one relation AND
it is designated the parent link for its target. Fields that are not one-to-one,
and one-to-one fields not designated as the parent link, are skipped entirely —
they never enter the mapping and so can never displace a genuine parent link that
shares their target.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each candidate
-- field's observable attributes (whether it is a one-to-one relation, whether it
-- is designated the parent link, its related-model identity, its own identity)
-- enter as plain data on the `FieldInfo` record. The only operation is the guarded
-- last-write-wins insertion into the mapping, modeled directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A candidate field, carrying only the attributes the mapping build observes.
`relatedKey` is the identity of the model the relation points at (the map key);
`name` is the field's own identity. -/
structure FieldInfo where
  isOneToOne : Bool
  parentLink : Bool
  relatedKey : String
  name : String
deriving Repr, DecidableEq

/-- Insert `(k, v)` into an association list with last-write-wins semantics:
drop any existing entry for key `k`, then append the new entry. This mirrors a
dictionary assignment `d[k] = v`, which keeps the most recently written value for
`k` and leaves every other key untouched. -/
def dictInsert (d : List (String × FieldInfo)) (k : String) (v : FieldInfo) :
    List (String × FieldInfo) :=
  d.filter (fun p => p.1 ≠ k) ++ [(k, v)]

/-- The parent-link mapping built from the candidate fields, scanned in order.
A field is recorded (keyed by its related-model identity) exactly when it is a
one-to-one relation that is designated the parent link for its target; every
other field is skipped. Last-write-wins resolves repeated keys. -/
def buildParentLinks (fields : List FieldInfo) : List (String × FieldInfo) :=
  fields.foldl
    (fun d f => if f.isOneToOne && f.parentLink then dictInsert d f.relatedKey f else d)
    []
-- pure-end

-- post-conditions-start
/-- The resulting mapping is fully determined by the candidate fields: it is
exactly the mapping obtained by scanning the fields in order and recording, with
last-write-wins, each one-to-one field that is designated the parent link for its
target. No part of the result is left free. -/
def problem_spec_collectParentLinks
    (fields : List FieldInfo) (result : List (String × FieldInfo)) : Prop :=
  result = buildParentLinks fields
-- post-conditions-end

-- impl-start
def implementation_collectParentLinks (fields : List FieldInfo) :
    List (String × FieldInfo) := Id.run do
  let mut parentLinks : List (String × FieldInfo) := []
  for field in fields do
    if field.isOneToOne && field.parentLink then
      parentLinks := dictInsert parentLinks field.relatedKey field
  return parentLinks
-- impl-end

-- proof-start
/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
theorem forIn_collectParentLinks (fields : List FieldInfo)
    (init : List (String × FieldInfo)) :
    Id.run (forIn fields init (fun field r =>
        (if (field.isOneToOne && field.parentLink) = true then
          ForInStep.yield (dictInsert r field.relatedKey field)
        else ForInStep.yield r : Id _))) =
      List.foldl
        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
        init fields := by
  induction fields generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.isOneToOne && a.parentLink) = true
    · simp only [h, List.foldl_cons, if_true, ih]
    · simp only [Bool.not_eq_true] at h
      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]

theorem correct_collectParentLinks :
    ∀ (fields : List FieldInfo),
      problem_spec_collectParentLinks fields
        (implementation_collectParentLinks fields) := by
  intro fields
  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
              (if (field.isOneToOne && field.parentLink) = true then
                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
              (if (field.isOneToOne && field.parentLink) = true then
                ForInStep.yield (dictInsert r field.relatedKey field)
              else ForInStep.yield r : Id _))) := rfl
  simp only [Id.run]
  rw [h2]
  exact forIn_collectParentLinks fields []
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PINNED FUNCTIONAL-EQUALITY SPEC. Postcondition problem_spec_collectParentLinks fields result := result = buildParentLinks fields (exact equality to a total spec fn; 'No part of the result is left free'). Any impl not extensionally equal to buildParentLinks makes correct_collectParentLinks a FALSE theorem, unprovable by Lean soundness. same_spec elides both impl and proof regions; every attack edits only the impl region, all 9 files confirmed same_spec=True vs gold.

VERIFY COMMANDS: `bash scripts/lean_verify.sh <file>`.
### Results
- pos_control.lean (verbatim gold): exit 0. #print axioms correct_collectParentLinks = [propext, Quot.sound] (clean standard axioms; no sorryAx/Classical.choice; no sorry). POSITIVE CONTROL PASSES.
- atk_1_prepatch (drop parentLink conjunct = the real prepatch bug): exit 1, error at :100 'rfl failed' (false thm).
- atk_2_drop_o2o (record any parentLink, drop isOneToOne): exit 1 (false thm).
- atk_3_or (|| instead of &&): exit 1 (false thm).
- atk_4_no_lww (naive append, no last-write-wins, keeps dup keys): exit 1 (false thm).
- atk_5_first_wins (insert only if key absent = first-write-wins): exit 1 (false thm).
- atk_6_empty (always return [], partial-domain correct only on all-skip inputs): exit 1 (false thm).
- atk_7_reverse (correct mapping then .reverse, order/boundary defect): exit 1 (false thm).
- atk_8_echo (return buildParentLinks fields, ungrounded-oracle echo): exit 0; #print axioms = 'does not depend on any axioms' (clean). This is the ONLY closing impl and it computes EXACTLY the correct post-patch behavior.

PROTOCOL STEP 2 (resolve for every verifying clean-axiom impl): atk_8's faithful refined patch equals the gold patch (echo computes exact post-patch behavior). Materialized at atk_8_faithful.patch and RUN through the official harness: swebench_unified.harness.run_resolve('django__django-12325', patch, timeout=1800) => resolved=True completed=True note='resolved'. No verifying-with-clean-axioms impl has a non-resolving faithful patch => spec NOT broken.

INDEPENDENT FALSIFICATION WITNESS (witness.lean, exit 0): three `decide` proofs closed, exhibiting concrete inputs where the wrong impls differ from buildParentLinks: impl_prepatch [pl,npl] ≠ buildParentLinks; impl_dropo2o [notO] ≠ buildParentLinks; impl_empty [pl] ≠ buildParentLinks. Confirms atk_1/2/6 are genuinely wrong functions, not merely tactic-shy.

REFINEMENT.MD AUDIT: 5 legs, all R/I. Leg1 empty dict->[] (R); Leg2 field loop / base-concat iteration order (I/R); Leg3 guard isOneToOne&&parentLink <-> isinstance(OneToOneField) and remote_field.parent_link, the GOLD edit (R); Leg4 dictInsert <-> dict assignment last-write-wins, key=make_model_tuple(resolve_relation(...)) enters as relatedKey data (R); Leg5 return (I). meta.json axioms=[], deep_model_references=[]; axiom_check.py is a legitimate skip stub. NO A-consumed / A-reference legs => the A-leg mandate is vacuously satisfied; NO kind-3 legs (nothing modeled deeply-yet-presented-as-unchanged without validation). isinstance/resolve_relation/make_model_tuple/parent_link legitimately enter as FieldInfo DATA; the guarded last-write-wins insertion is modeled deeply as dictInsert (R). The R/I differential is covered by G-CONF (conf_skip=false). Correspondence to the real callees holds.

CONCLUSION: 8 attacks run (7 behaviorally-distinct wrong impls + 1 echo), plus a decide-based witness. All 7 genuine wrong impls fail to close; the sole closing impl (echo) resolves. verify => correct holds for every verifying clean-axiom candidate. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_drop_o2o.lean`, `atk_3_or.lean`, `atk_4_no_lww.lean`, `atk_5_first_wins.lean`, `atk_6_empty.lean`, `atk_7_reverse.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Input fields = [{isOneToOne=true, parentLink=true, relatedKey="M", name="ptr"}, {isOneToOne=true, parentLink=false, relatedKey="M", name="other"}] (a genuine parent-link OneToOne followed by a later non-parent-link OneToOne to the SAME base M). Spec buildParentLinks records only the parent-link field -> [("M", ptr)]. The prepatch/atk_1 impl (guard drops the parentLink conjunct) records both last-write-wins -> [("M", other)], the wrong field. Proved distinct in Lean by `decide` (witness.lean): impl_prepatch inp ≠ buildParentLinks inp. This is exactly the FAIL_TO_PASS shape (test_onetoone_with_parent_model / test_clash_parent_link).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_drop_o2o.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_or.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_no_lww.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_first_wins.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_empty.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_reverse.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the parent-link mapping while a model class is assembled.

When a model participates in multi-table inheritance, one of its one-to-one
relations to a base model is the *parent link*: the relation whose column is
promoted to the child's primary key. A model may declare several one-to-one
relations pointing at the very same base model — only the one explicitly
designated as the parent link should fill that role; the others are ordinary
relations and must not be mistaken for the link.

The mapping under construction associates each related-model identity with the
field that links to it. It is built by scanning the candidate fields in order and
recording, keyed by the related-model identity, the field that links to that
model. The association is last-write-wins: recording a field for a key that is
already present replaces the earlier entry.

Each candidate field exposes:

  * `isOneToOne`   — whether it is a one-to-one relation;
  * `parentLink`   — whether it is designated the parent link for its target;
  * `relatedKey`   — the identity of the related model it points at (the map key);
  * `name`         — the field's own stable identity.

A field is recorded into the mapping exactly when it is a one-to-one relation AND
it is designated the parent link for its target. Fields that are not one-to-one,
and one-to-one fields not designated as the parent link, are skipped entirely —
they never enter the mapping and so can never displace a genuine parent link that
shares their target.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each candidate
-- field's observable attributes (whether it is a one-to-one relation, whether it
-- is designated the parent link, its related-model identity, its own identity)
-- enter as plain data on the `FieldInfo` record. The only operation is the guarded
-- last-write-wins insertion into the mapping, modeled directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A candidate field, carrying only the attributes the mapping build observes.
`relatedKey` is the identity of the model the relation points at (the map key);
`name` is the field's own identity. -/
structure FieldInfo where
  isOneToOne : Bool
  parentLink : Bool
  relatedKey : String
  name : String
deriving Repr, DecidableEq

/-- Insert `(k, v)` into an association list with last-write-wins semantics:
drop any existing entry for key `k`, then append the new entry. This mirrors a
dictionary assignment `d[k] = v`, which keeps the most recently written value for
`k` and leaves every other key untouched. -/
def dictInsert (d : List (String × FieldInfo)) (k : String) (v : FieldInfo) :
    List (String × FieldInfo) :=
  d.filter (fun p => p.1 ≠ k) ++ [(k, v)]

/-- The parent-link mapping built from the candidate fields, scanned in order.
A field is recorded (keyed by its related-model identity) exactly when it is a
one-to-one relation that is designated the parent link for its target; every
other field is skipped. Last-write-wins resolves repeated keys. -/
def buildParentLinks (fields : List FieldInfo) : List (String × FieldInfo) :=
  fields.foldl
    (fun d f => if f.isOneToOne && f.parentLink then dictInsert d f.relatedKey f else d)
    []
-- pure-end

-- post-conditions-start
/-- The resulting mapping is fully determined by the candidate fields: it is
exactly the mapping obtained by scanning the fields in order and recording, with
last-write-wins, each one-to-one field that is designated the parent link for its
target. No part of the result is left free. -/
def problem_spec_collectParentLinks
    (fields : List FieldInfo) (result : List (String × FieldInfo)) : Prop :=
  result = buildParentLinks fields
-- post-conditions-end

-- impl-start
def implementation_collectParentLinks (fields : List FieldInfo) :
    List (String × FieldInfo) := Id.run do
  let mut parentLinks : List (String × FieldInfo) := []
  for field in fields do
    if field.isOneToOne && field.parentLink then
      parentLinks := dictInsert parentLinks field.relatedKey field
  return parentLinks
-- impl-end

-- proof-start
/-- Helper: the desugared `forIn` loop over the cleaned (branch-only) body equals
the `List.foldl` from `buildParentLinks`, generalized over the accumulator. -/
theorem forIn_collectParentLinks (fields : List FieldInfo)
    (init : List (String × FieldInfo)) :
    Id.run (forIn fields init (fun field r =>
        (if (field.isOneToOne && field.parentLink) = true then
          ForInStep.yield (dictInsert r field.relatedKey field)
        else ForInStep.yield r : Id _))) =
      List.foldl
        (fun d f => if (f.isOneToOne && f.parentLink) = true then dictInsert d f.relatedKey f else d)
        init fields := by
  induction fields generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.isOneToOne && a.parentLink) = true
    · simp only [h, List.foldl_cons, if_true, ih]
    · simp only [Bool.not_eq_true] at h
      simp only [h, List.foldl_cons, ih, Bool.false_eq_true, if_false]

theorem correct_collectParentLinks :
    ∀ (fields : List FieldInfo),
      problem_spec_collectParentLinks fields
        (implementation_collectParentLinks fields) := by
  intro fields
  unfold problem_spec_collectParentLinks implementation_collectParentLinks buildParentLinks
  have h2 : (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
              (if (field.isOneToOne && field.parentLink) = true then
                (do pure PUnit.unit; pure (ForInStep.yield (dictInsert r field.relatedKey field)))
              else (do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)))
          = (forIn fields ([] : List (String × FieldInfo)) (fun field r =>
              (if (field.isOneToOne && field.parentLink) = true then
                ForInStep.yield (dictInsert r field.relatedKey field)
              else ForInStep.yield r : Id _))) := rfl
  simp only [Id.run]
  rw [h2]
  exact forIn_collectParentLinks fields []
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PINNED FUNCTIONAL-EQUALITY SPEC. Postcondition problem_spec_collectParentLinks fields result := result = buildParentLinks fields (exact equality to a total spec fn; 'No part of the result is left free'). Any impl not extensionally equal to buildParentLinks makes correct_collectParentLinks a FALSE theorem, unprovable by Lean soundness. same_spec elides both impl and proof regions; every attack edits only the impl region, all 9 files confirmed same_spec=True vs gold.

VERIFY COMMANDS: `bash scripts/lean_verify.sh <file>`.
### Results
- pos_control.lean (verbatim gold): exit 0. #print axioms correct_collectParentLinks = [propext, Quot.sound] (clean standard axioms; no sorryAx/Classical.choice; no sorry). POSITIVE CONTROL PASSES.
- atk_1_prepatch (drop parentLink conjunct = the real prepatch bug): exit 1, error at :100 'rfl failed' (false thm).
- atk_2_drop_o2o (record any parentLink, drop isOneToOne): exit 1 (false thm).
- atk_3_or (|| instead of &&): exit 1 (false thm).
- atk_4_no_lww (naive append, no last-write-wins, keeps dup keys): exit 1 (false thm).
- atk_5_first_wins (insert only if key absent = first-write-wins): exit 1 (false thm).
- atk_6_empty (always return [], partial-domain correct only on all-skip inputs): exit 1 (false thm).
- atk_7_reverse (correct mapping then .reverse, order/boundary defect): exit 1 (false thm).
- atk_8_echo (return buildParentLinks fields, ungrounded-oracle echo): exit 0; #print axioms = 'does not depend on any axioms' (clean). This is the ONLY closing impl and it computes EXACTLY the correct post-patch behavior.

PROTOCOL STEP 2 (resolve for every verifying clean-axiom impl): atk_8's faithful refined patch equals the gold patch (echo computes exact post-patch behavior). Materialized at atk_8_faithful.patch and RUN through the official harness: swebench_unified.harness.run_resolve('django__django-12325', patch, timeout=1800) => resolved=True completed=True note='resolved'. No verifying-with-clean-axioms impl has a non-resolving faithful patch => spec NOT broken.

INDEPENDENT FALSIFICATION WITNESS (witness.lean, exit 0): three `decide` proofs closed, exhibiting concrete inputs where the wrong impls differ from buildParentLinks: impl_prepatch [pl,npl] ≠ buildParentLinks; impl_dropo2o [notO] ≠ buildParentLinks; impl_empty [pl] ≠ buildParentLinks. Confirms atk_1/2/6 are genuinely wrong functions, not merely tactic-shy.

REFINEMENT.MD AUDIT: 5 legs, all R/I. Leg1 empty dict->[] (R); Leg2 field loop / base-concat iteration order (I/R); Leg3 guard isOneToOne&&parentLink <-> isinstance(OneToOneField) and remote_field.parent_link, the GOLD edit (R); Leg4 dictInsert <-> dict assignment last-write-wins, key=make_model_tuple(resolve_relation(...)) enters as relatedKey data (R); Leg5 return (I). meta.json axioms=[], deep_model_references=[]; axiom_check.py is a legitimate skip stub. NO A-consumed / A-reference legs => the A-leg mandate is vacuously satisfied; NO kind-3 legs (nothing modeled deeply-yet-presented-as-unchanged without validation). isinstance/resolve_relation/make_model_tuple/parent_link legitimately enter as FieldInfo DATA; the guarded last-write-wins insertion is modeled deeply as dictInsert (R). The R/I differential is covered by G-CONF (conf_skip=false). Correspondence to the real callees holds.

CONCLUSION: 8 attacks run (7 behaviorally-distinct wrong impls + 1 echo), plus a decide-based witness. All 7 genuine wrong impls fail to close; the sole closing impl (echo) resolves. verify => correct holds for every verifying clean-axiom candidate. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) check for django__django-12325, modeled function collectParentLinks (buildParentLinks). VERDICT: FAITHFUL — no diverging input found; the spec does not drift from the real callee.

Evidence:
1. Lean: scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). `#print axioms correct_collectParentLinks` -> [propext, Quot.sound] (clean; NO sorryAx). The correctness proof is genuine.
2. Spec region byte-identity: swebench_unified same_spec(Solution.lean, Solution_prepatch.lean) via LeanBackend = True. Prepatch differs only in the impl guard (isOneToOne vs isOneToOne && parentLink) and carries `sorry`, confirming G-DIFF sensitivity to the gold conjunct. axioms=[], conf_skip=false, patch_equals_gold=true.
3. Real callee = parent_links dict-build in ModelBase.__new__ (django/db/models/base.py). Post-patch: `if isinstance(field, OneToOneField) and field.remote_field.parent_link: parent_links[make_model_tuple(resolve_relation(...))] = field` with dict last-write-wins. The model folds `if f.isOneToOne && f.parentLink then dictInsert d f.relatedKey f` — SAME guard (both conjuncts) and SAME last-write-wins semantics. dictInsert d k v = d.filter(·.1≠k)++[(k,v)] reproduces Python `d[k]=v` exactly as a key→value map.
4. Assoc-list vs dict encoding is EXACT because iteration order of parent_links is never observed: grep of the whole repo shows the only downstream uses are `base_key in parent_links` (membership) and `parent_links[base_key]` (per-key lookup). No divergence possible on any observable — a dict and the ordered assoc list agree on membership and per-key value for every input.
5. Base-selection (outer loop + two `continue`s) is unchanged by the patch and correctly folded into the `fields` input rather than modeled — appropriate modeling boundary, not spec weakening.
6. Case coverage (matches real dict on all): empty -> {}; non-OneToOne -> skipped both; OneToOne w/o parent_link -> skipped (the gold fix, e.g. Field(True,False,k) records nothing post-patch); shared key with parent-link then later plain OneToOne -> keeps parent link (FAIL_TO_PASS shape); multiple parent-link candidates same key -> last one wins. All agree.

The spec is neither too strong nor drifted: `result = buildParentLinks fields` fully pins the mapping to exactly the real post-patch behavior. No input where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Computed the actual Lean spec view via markers.spec_view(LeanBackend). Consumer-visible spec = imports, the /-! docstring, axioms note, pure region (FieldInfo, dictInsert, buildParentLinks), and post-conditions (problem_spec_collectParentLinks := result = buildParentLinks fields). The impl and proof regions are elided to placeholders. same_spec(Solution, Solution_prepatch)=True; mechanical leakage.screen passed (hard_failures=[]); bundle is NOT relaxed.

Gold edit = add conjunct 'and field.remote_field.parent_link' to guard 'if isinstance(field, OneToOneField):' in ModelBase.__new__ (record only OneToOne fields designated as parent link). Assessed whether the spec view leaks this beyond the PUBLIC problem_statement (not hints_text).

The public problem_statement already contains OneToOneField, parent_link=True, models.Model, the MTI pk-setup bug (multiple OneToOne references to a base confuse pk setup), the explicit reporter demand 'we have explicit parent_link marker' asking why parent_link is not respected, and 'order seems to matter' (telegraphs the last-write-wins overwrite). The spec view's behavioral statement -- 'record a field exactly when it is one-to-one AND designated the parent link; one-to-one fields not designated as parent link are skipped' -- is a faithful restatement of the correct behavior the problem_statement itself demands, not information beyond it. The parent_link discriminator is precisely what the reporter says should be checked.

The spec view does NOT expose patched method names (__new__/_prepare; identifiers are neutral: collectParentLinks, dictInsert, FieldInfo, relatedKey), file paths (base.py/options.py), or any diff line. The assoc-list/dictInsert/foldl last-write-wins modeling is generic mechanization structure and is also implied by the public 'order matters' symptom. No spec-view line reconstructs the gold diff beyond what the public problem_statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
