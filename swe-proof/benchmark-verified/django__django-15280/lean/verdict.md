# P2 adversarial audit — django__django-15280

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an EXACT functional equality (result = children.map (assignOne lookup)) with an EMPTY axioms region (meta.json axioms=[], deep_model_references=[], opaque_callees=[]). correct_assignParents is therefore provable iff the impl is extensionally equal to gold; no ungrounded-oracle/axiom surface exists to exploit. All 7 genuinely-wrong same-spec impls fail to verify with real false-goal errors (Lean: 'not definitionally equal to List.map (assignOne lookup) children'). The single verifying attack (atk_5) is the extensional echo of the spec function, and its faithful patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,57 +43,17 @@
     (lookup : Int → Int) (children : List Child) : List Child := Id.run do
   let mut acc : List Child := []
   for c in children do
-    if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
-    else
-      acc := acc ++ [c]
+    let p := lookup c.key
+    acc := acc ++ [{ c with parent := some p }]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,60 +40,16 @@
 
 -- impl-start
 def implementation_assignParents
-    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
-  let mut acc : List Child := []
-  for c in children do
-    if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
-    else
-      acc := acc ++ [c]
-  return acc
+    (lookup : Int → Int) (children : List Child) : List Child :=
+  children
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,56 +44,18 @@
   let mut acc : List Child := []
   for c in children do
     if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
+      acc := [{ c with parent := some (lookup c.key) }] ++ acc
     else
-      acc := acc ++ [c]
+      acc := [c] ++ acc
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,56 +44,18 @@
   let mut acc : List Child := []
   for c in children do
     if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
+      acc := acc ++ [c]
     else
-      acc := acc ++ [c]
+      acc := acc ++ [{ c with parent := some (lookup c.key) }]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -40,60 +40,14 @@
 
 -- impl-start
 def implementation_assignParents
-    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
-  let mut acc : List Child := []
-  for c in children do
-    if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
-    else
-      acc := acc ++ [c]
-  return acc
+    (lookup : Int → Int) (children : List Child) : List Child :=
+  children.map (assignOne lookup)
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
-  unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,56 +44,18 @@
   let mut acc : List Child := []
   for c in children do
     if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
+      acc := acc ++ [{ c with parent := some (lookup (c.key + 1)) }]
     else
       acc := acc ++ [c]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,56 +44,16 @@
   let mut acc : List Child := []
   for c in children do
     if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
-    else
-      acc := acc ++ [c]
+      acc := acc ++ [{ c with parent := some (lookup c.key) }]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,57 +43,19 @@
     (lookup : Int → Int) (children : List Child) : List Child := Id.run do
   let mut acc : List Child := []
   for c in children do
-    if c.parent.isNone then
-      let p := lookup c.key
-      acc := acc ++ [{ c with parent := some p }]
+    if c.parent.isNone && c.key != 0 then
+      acc := acc ++ [{ c with parent := some (lookup c.key) }]
     else
       acc := acc ++ [c]
   return acc
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
-generalized over the accumulator, equals the running accumulator appended with
-the mapped tail. -/
-private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
-    (init : List Child) :
-    Id.run (forIn xs init (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    cases hp : a.parent with
-    | none =>
-      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
-        List.append_assoc, List.cons_append, List.nil_append]
-    | some v =>
-      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
-        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
     problem_spec_assignParents lookup children
       (implementation_assignParents lookup children) := by
   intro lookup children
   unfold problem_spec_assignParents implementation_assignParents
-  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
-  have h2 : (Id.run do
-      let mut acc : List Child := []
-      for c in children do
-        if c.parent.isNone then
-          let p := lookup c.key
-          acc := acc ++ [{ c with parent := some p }]
-        else
-          acc := acc ++ [c]
-      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
-        (if c.parent.isNone = true then
-          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
-        else
-          pure (ForInStep.yield (r ++ [c]))))) := rfl
-  rw [h2, assignParents_forIn]
-  simp
+  simp [assignOne, Id.run]
+  <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The "is a value already
-- assigned?" test is modeled DIRECTLY as the state of each record's optional
-- parent slot (`none` = no value assigned yet), not axiomatized; the per-key
-- default-value table is a plain total function argument. The proof agent may
-- add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A child record carried by the batch. `key` is the value used to look up its
default parent in the table; `parent` is the parent already assigned to it
(`none` when no parent has been assigned yet, `some v` when one is already
present). -/
structure Child where
  key : Int
  parent : Option Int
  deriving Repr, DecidableEq

/-- Assign the default parent to a single child: if the child already has a
parent, it is kept unchanged; otherwise the default parent looked up by its key
is assigned. -/
def assignOne (lookup : Int → Int) (c : Child) : Child :=
  match c.parent with
  | some _ => c
  | none   => { c with parent := some (lookup c.key) }
-- pure-end

-- post-conditions-start
/-- The result is the input batch with each child given a parent: a child that
already has a parent keeps it (and all its other components are unchanged), while
a child with no parent yet receives the default parent looked up by its key. The
batch order and length are preserved. -/
def problem_spec_assignParents
    (lookup : Int → Int) (children : List Child) (result : List Child) : Prop :=
  result = children.map (assignOne lookup)
-- post-conditions-end

-- impl-start
def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    if c.parent.isNone then
      let p := lookup c.key
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
generalized over the accumulator, equals the running accumulator appended with
the mapped tail. -/
private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
    (init : List Child) :
    Id.run (forIn xs init (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    cases hp : a.parent with
    | none =>
      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
        List.append_assoc, List.cons_append, List.nil_append]
    | some v =>
      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
    problem_spec_assignParents lookup children
      (implementation_assignParents lookup children) := by
  intro lookup children
  unfold problem_spec_assignParents implementation_assignParents
  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
  have h2 : (Id.run do
      let mut acc : List Child := []
      for c in children do
        if c.parent.isNone then
          let p := lookup c.key
          acc := acc ++ [{ c with parent := some p }]
        else
          acc := acc ++ [c]
      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) := rfl
  rw [h2, assignParents_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean). Only the impl region edited; axioms/pure/pre/post byte-identical.

POSITIVE CONTROL: pos_control.lean (gold impl) => lean_verify.sh exit 0 (empty log).
PREPATCH REPRODUCED: atk_1.lean is the prepatch bug (unconditional overwrite) => lean_verify exit 1, error 'pure (List.map (fun x2 => [{key, some (lookup key)}]) children).flatten is not definitionally equal to List.map (assignOne lookup) children'. Confirms G-DIFF.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch/unconditional-overwrite: EXIT 1 (error, false goal). FAIL to verify.
- atk_2 identity (children unchanged): EXIT 1 ('simp made no progress'; false goal). FAIL.
- atk_3 reversed-order (prepend): EXIT 1 (forIn ... :: r not def-eq map). FAIL.
- atk_4 swapped-branches (control-flow-effect): EXIT 1 (false goal). FAIL.
- atk_6 off-by-one key (lookup (c.key+1)): EXIT 1 (false goal). FAIL.
- atk_7 drop-cached (wrong length): EXIT 1 (else yields r; false goal). FAIL.
- atk_8 key-dependent flip (keep if key=0 even when none): EXIT 1 (false goal). FAIL.
- atk_5 ungrounded-oracle ECHO (children.map (assignOne lookup)): EXIT 0, VERIFIES. #print axioms => 'correct_assignParents does not depend on any axioms' (CLEAN). Faithful patch materialized (atk_5.patch = behaviorally the gold patch) and RUN through run_resolve('django__django-15280', ...): RESOLVED=True, COMPLETED=True, FAIL_TO_PASS success=['The prefetched relationship is used rather than populating the reverse'], all PASS_TO_PASS pass, 0 failures. => NOT a weakness (verify=>correct holds; resolving echo per current G-EQ/panel-1 policy).

A-LEG AUDIT (refinement.md + mapping.md): meta.json confirms axioms=[], deep_model_references=[], opaque_callees=[] => NO A-consumed and NO A-reference legs, NO kind-3. G-AX is a genuine SKIP (no callee axiom, no deep-model reference). All legs are R/I: row3 is_cached(rel_obj)<->c.parent.isSome (R, direct Option model), row4 instances_dict[rel_obj_attr]<->lookup c.key (R, total fn), row5 setattr<->record update parent:=some (R/I), rows 1/2/6/7 identical iteration/init/return (I). Correspondence to real callees is sound and directly modeled — no opaque signature masks divergent behavior.

CONCLUSION: The exact-equality postcondition with empty axioms region admits no same-spec verifying-but-wrong impl. 8 distinct attacks run (7 falsification attempts all fail to verify with genuine false goals; 1 echo verifies with clean axioms and its faithful patch resolves). Spec is TIGHT: verify=>correct. VERDICT SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an EXACT functional equality (result = children.map (assignOne lookup)) with an EMPTY axioms region (meta.json axioms=[], deep_model_references=[], opaque_callees=[]). correct_assignParents is therefore provable iff the impl is extensionally equal to gold; no ungrounded-oracle/axiom surface exists to exploit. All 7 genuinely-wrong same-spec impls fail to verify with real false-goal errors (Lean: 'not definitionally equal to List.map (assignOne lookup) children'). The single verifying attack (atk_5) is the extensional echo of the spec function, and its faithful patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The "is a value already
-- assigned?" test is modeled DIRECTLY as the state of each record's optional
-- parent slot (`none` = no value assigned yet), not axiomatized; the per-key
-- default-value table is a plain total function argument. The proof agent may
-- add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A child record carried by the batch. `key` is the value used to look up its
default parent in the table; `parent` is the parent already assigned to it
(`none` when no parent has been assigned yet, `some v` when one is already
present). -/
structure Child where
  key : Int
  parent : Option Int
  deriving Repr, DecidableEq

/-- Assign the default parent to a single child: if the child already has a
parent, it is kept unchanged; otherwise the default parent looked up by its key
is assigned. -/
def assignOne (lookup : Int → Int) (c : Child) : Child :=
  match c.parent with
  | some _ => c
  | none   => { c with parent := some (lookup c.key) }
-- pure-end

-- post-conditions-start
/-- The result is the input batch with each child given a parent: a child that
already has a parent keeps it (and all its other components are unchanged), while
a child with no parent yet receives the default parent looked up by its key. The
batch order and length are preserved. -/
def problem_spec_assignParents
    (lookup : Int → Int) (children : List Child) (result : List Child) : Prop :=
  result = children.map (assignOne lookup)
-- post-conditions-end

-- impl-start
def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    if c.parent.isNone then
      let p := lookup c.key
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
generalized over the accumulator, equals the running accumulator appended with
the mapped tail. -/
private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
    (init : List Child) :
    Id.run (forIn xs init (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    cases hp : a.parent with
    | none =>
      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
        List.append_assoc, List.cons_append, List.nil_append]
    | some v =>
      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
    problem_spec_assignParents lookup children
      (implementation_assignParents lookup children) := by
  intro lookup children
  unfold problem_spec_assignParents implementation_assignParents
  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
  have h2 : (Id.run do
      let mut acc : List Child := []
      for c in children do
        if c.parent.isNone then
          let p := lookup c.key
          acc := acc ++ [{ c with parent := some p }]
        else
          acc := acc ++ [c]
      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) := rfl
  rw [h2, assignParents_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean). Only the impl region edited; axioms/pure/pre/post byte-identical.

POSITIVE CONTROL: pos_control.lean (gold impl) => lean_verify.sh exit 0 (empty log).
PREPATCH REPRODUCED: atk_1.lean is the prepatch bug (unconditional overwrite) => lean_verify exit 1, error 'pure (List.map (fun x2 => [{key, some (lookup key)}]) children).flatten is not definitionally equal to List.map (assignOne lookup) children'. Confirms G-DIFF.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch/unconditional-overwrite: EXIT 1 (error, false goal). FAIL to verify.
- atk_2 identity (children unchanged): EXIT 1 ('simp made no progress'; false goal). FAIL.
- atk_3 reversed-order (prepend): EXIT 1 (forIn ... :: r not def-eq map). FAIL.
- atk_4 swapped-branches (control-flow-effect): EXIT 1 (false goal). FAIL.
- atk_6 off-by-one key (lookup (c.key+1)): EXIT 1 (false goal). FAIL.
- atk_7 drop-cached (wrong length): EXIT 1 (else yields r; false goal). FAIL.
- atk_8 key-dependent flip (keep if key=0 even when none): EXIT 1 (false goal). FAIL.
- atk_5 ungrounded-oracle ECHO (children.map (assignOne lookup)): EXIT 0, VERIFIES. #print axioms => 'correct_assignParents does not depend on any axioms' (CLEAN). Faithful patch materialized (atk_5.patch = behaviorally the gold patch) and RUN through run_resolve('django__django-15280', ...): RESOLVED=True, COMPLETED=True, FAIL_TO_PASS success=['The prefetched relationship is used rather than populating the reverse'], all PASS_TO_PASS pass, 0 failures. => NOT a weakness (verify=>correct holds; resolving echo per current G-EQ/panel-1 policy).

A-LEG AUDIT (refinement.md + mapping.md): meta.json confirms axioms=[], deep_model_references=[], opaque_callees=[] => NO A-consumed and NO A-reference legs, NO kind-3. G-AX is a genuine SKIP (no callee axiom, no deep-model reference). All legs are R/I: row3 is_cached(rel_obj)<->c.parent.isSome (R, direct Option model), row4 instances_dict[rel_obj_attr]<->lookup c.key (R, total fn), row5 setattr<->record update parent:=some (R/I), rows 1/2/6/7 identical iteration/init/return (I). Correspondence to real callees is sound and directly modeled — no opaque signature masks divergent behavior.

CONCLUSION: The exact-equality postcondition with empty axioms region admits no same-spec verifying-but-wrong impl. 8 distinct attacks run (7 falsification attempts all fail to verify with genuine false goals; 1 echo verifies with clean axioms and its faithful patch resolves). Spec is TIGHT: verify=>correct. VERDICT SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift). Conclusion: FAITHFUL — the modeled function agrees with the real post-patch callee on every representable input; no diverging input exists.

Modeled callee: the reverse-relation assignment loop in RelatedManager.get_prefetch_queryset (django/db/models/fields/related_descriptors.py, base_commit 973fa56). Post-patch loop:
  for rel_obj in queryset:
      if not self.field.is_cached(rel_obj):
          instance = instances_dict[rel_obj_attr(rel_obj)]
          setattr(rel_obj, self.field.name, instance)

Type bijection (mapping.md, confirmed against gold source): rel_obj ↔ Child{key,parent}; is_cached ↔ parent.isSome; not is_cached ↔ parent.isNone; instances_dict[rel_obj_attr(rel_obj)] ↔ lookup c.key; setattr ↔ parent := some (lookup key). Spec: result = children.map (assignOne lookup), where assignOne keeps some v unchanged and fills none with some (lookup key).

Checks run:
1. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec region (axioms empty + pure Child/assignOne + postcondition) is byte-identical between gold and prepatch; the spec is frozen.
2. scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
3. #print axioms correct_assignParents -> [propext, Quot.sound]; NO sorryAx, no _prop axioms — proof is genuine.
4. Prepatch impl (unconditional overwrite) carries sorry and cannot close against the frozen spec -> real G-DIFF signal, exactly the issue's bug (inner-prefetch value overwritten by outer object).
5. conformance_check.py -> 120005 inputs, 0 disagreements (seed 15280), incl. boundary cases (empty, single cached/uncached, same-key mixed).

Faithfulness reasoning: for every represented input the model matches the real loop exactly — parent=none maps to lookup key (real: instances_dict[key]); parent=some v is kept (real: skip). Order and length preserved both sides; deterministic. The total 'lookup : Int -> Int' vs Python dict subscript introduces no KeyError-vs-value drift in the reachable domain, since queryset = filter(field__in=instances) guarantees every related value is a key of instances_dict. The one abstraction gap — a 'cache present but value None' third state that Option Int cannot represent — is an abstraction boundary, not a divergence on any represented input, and lies outside the issue's domain (deferred fields on a prefetched non-null parent). The spec is neither too strong nor drifting: it is an exact functional characterization of the represented behavior. Hence FAITHFUL; no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3) leakage / gold-reconstruction assessment for django__django-15280 (lean). Reconstructed the exact solver-facing spec view via markers.spec_view(src, LeanBackend): it is Solution.lean with the impl and proof regions collapsed to 'elided' placeholders, exposing only imports, axioms (empty), pure (structure Child + assignOne), and post-conditions (problem_spec_assignParents) regions.

Gold edit: adds guard `if not self.field.is_cached(rel_obj):` around the assignment in RelatedManager.get_prefetch_queryset — i.e. do not overwrite the reverse relation when a value is already present.

Spec view encodes the CORRECT post-patch BEHAVIOR abstractly: assignOne keeps c when `parent = some _`, else assigns `lookup c.key`; the post-condition is `result = children.map (assignOne lookup)`. This is the unavoidable, inherent content of any faithful functional spec of the fix — the discriminating 'keep-if-already-present' clause IS the specified correct behavior, not a patch leak.

Lexical/reconstruction screen over the spec view: NO Python identifiers (is_cached, get_prefetch_queryset, rel_obj, setattr, field.name, instances_dict, rel_obj_attr), NO mention of Django/prefetch/deferred-fields/reverse-relation, NO comment quoting the diff or echoing problem_statement phrasing. The Python↔Lean coupling (is_cached ↔ parent.isSome, dict ↔ lookup, setattr ↔ record update) lives ONLY in mapping.md/refinement.md (auditor artifacts, not part of the spec view). The generic Child/key/Option-parent/total-lookup abstraction is what any faithful spec would produce.

The public problem_statement itself already discloses that the inner already-correct object is being clobbered / re-queried by the outer object; the spec adds no patch-specific tokens beyond the minimal faithful encoding of correct behavior. Treating this as leakage would make every faithful functional bundle leaky by definition, which is not the standard. Meta records G-LEAK pass ('spec view clean', failures empty), consistent with this finding.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
