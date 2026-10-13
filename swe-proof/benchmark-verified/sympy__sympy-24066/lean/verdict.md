# P2 adversarial audit — sympy__sympy-24066

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,8 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func (fds.map Prod.fst), dims := fds.map Prod.snd }
 -- impl-end
 
 -- proof-start
@@ -85,34 +79,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,8 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func (fds.map Prod.fst), dims := fds.map (fun _ => dimOne) }
 -- impl-end
 
 -- proof-start
@@ -85,34 +79,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,9 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func (fds.map Prod.fst),
+    dims := fds.map (fun fd => if isDimensionless fd.2 then fd.2 else dimOne) }
 -- impl-end
 
 -- proof-start
@@ -85,34 +80,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,8 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func [], dims := fds.map (fun fd => canonDim fd.2) }
 -- impl-end
 
 -- proof-start
@@ -85,34 +79,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,9 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func (fds.map Prod.fst),
+    dims := (fds.map (fun fd => canonDim fd.2)).reverse }
 -- impl-end
 
 -- proof-start
@@ -85,34 +80,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,12 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  match fds with
+  | [] => { factor := applyFunc func [], dims := [] }
+  | f :: rest =>
+      { factor := applyFunc func ((f :: rest).map Prod.fst),
+        dims := f.2 :: rest.map (fun fd => canonDim fd.2) }
 -- impl-end
 
 -- proof-start
@@ -85,34 +83,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,14 +70,9 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func (fds.map Prod.fst),
+    dims := fds.map (fun fd => if isDimensionless fd.2 then dimOne else fd.2) }
 -- impl-end
 
 -- proof-start
@@ -85,34 +80,7 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,8 @@
 
 -- impl-start
 def implementation_collectFunction
-    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
-  let mut dims : List Dim := []
-  for fd in fds do
-    if isDimensionless fd.2 then
-      dims := dims ++ [dimOne]
-    else
-      dims := dims ++ [fd.2]
-  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
+    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
+  { factor := applyFunc func (fds.map Prod.fst), dims := [] }
 -- impl-end
 
 -- proof-start
@@ -85,34 +79,8 @@
     ∀ (func : Func) (fds : List (Factor × Dim)),
       problem_spec_collectFunction func fds
         (implementation_collectFunction func fds) := by
-  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
-      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
-        = init ++ fds.map (fun fd => canonDim fd.2) := by
-    intro fds
-    induction fds with
-    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind, canonDim] at ih ⊢
-      by_cases h : isDimensionless a.2 = true <;>
-        simp [h, ih, List.append_assoc]
   intro func fds
-  unfold problem_spec_collectFunction implementation_collectFunction
-  refine ⟨rfl, ?_⟩
-  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
-        (if isDimensionless fd.2 = true then do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [dimOne]))
-          else do
-            pure PUnit.unit
-            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
-  rw [helper]
-  simp
+  unfold problem_spec_collectFunction implementation_collectFunction canonDim
+  refine ⟨?_, ?_⟩ <;>
+    simp_all <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control2.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the scale factor and dimension of a function application.

A physical expression carries a scale factor together with a dimension. When the
expression is a function applied to one or more arguments, each argument has
already been reduced to its own scale factor and dimension. The combined result
reports:

  * a scale factor equal to the function applied to the arguments' scale factors;
  * for each argument, a dimension equal to the unit dimension `Dimension(1)`
    whenever the dimension system regards that argument's dimension as
    dimensionless, and equal to the argument's dimension otherwise.

The canonicalisation of every dimensionless argument dimension to the single unit
dimension is what lets a later same-dimension comparison recognise two
dimensionless quantities as compatible, even when their dimensions are written in
different but equivalent symbolic forms.
-/

-- axioms-start
-- Two UNCHANGED outside operations are used identically by the specification and
-- the implementation, so each is carried as an opaque callee and NO property of
-- either is consumed (G-AX skips):
--
--   * `isDimensionless` — the dimension system's query deciding whether a
--     dimension reduces to no net dimension. Modelled as an opaque predicate; its
--     internal dependency resolution is out of scope here.
--   * `applyFunc` — rebuilding the function applied to the arguments' scale
--     factors. Unchanged by the modelled behavior; carried opaquely so the scale
--     factor component is pinned to its inputs.
--
-- The argument scale/dimension pairs `fds` are themselves produced by the
-- (unchanged) recursive collection and are carried as grounded inputs, not
-- axiomatised.
abbrev Dim := Nat
abbrev Factor := Nat
abbrev Func := Nat
opaque dimOne : Dim
opaque isDimensionless : Dim → Bool
opaque applyFunc : Func → List Factor → Factor
-- axioms-end

-- pure-start
/-- The collected result of a function application: the rebuilt scale factor and
the per-argument list of (canonicalised) dimensions. -/
structure FunctionResult where
  factor : Factor
  dims : List Dim
deriving DecidableEq, Repr

/-- Canonicalise a single argument's dimension: report the unit dimension when
the dimension system regards it as dimensionless, otherwise report it unchanged. -/
def canonDim (d : Dim) : Dim :=
  if isDimensionless d then dimOne else d
-- pure-end

-- post-conditions-start
/-- The result of collecting a function application: the scale factor is the
function applied to the arguments' scale factors, and the dimension list is the
element-wise canonicalisation of the arguments' dimensions (each dimensionless
dimension reported as the unit dimension, every other dimension unchanged). -/
def problem_spec_collectFunction
    (func : Func) (fds : List (Factor × Dim)) (result : FunctionResult) : Prop :=
  result.factor = applyFunc func (fds.map Prod.fst) ∧
  result.dims = fds.map (fun fd => canonDim fd.2)
-- post-conditions-end

-- impl-start
def implementation_collectFunction
    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
  { factor := applyFunc func (fds.map Prod.fst),
    dims := fds.foldr (fun fd acc => canonDim fd.2 :: acc) [] }
-- impl-end

-- proof-start
theorem correct_collectFunction :
    ∀ (func : Func) (fds : List (Factor × Dim)),
      problem_spec_collectFunction func fds
        (implementation_collectFunction func fds) := by
  intro func fds
  unfold problem_spec_collectFunction implementation_collectFunction
  refine ⟨rfl, ?_⟩
  induction fds with
  | nil => rfl
  | cons a as ih => simp [List.map, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is FULLY FUNCTIONAL: problem_spec_collectFunction pins BOTH output fields by equality (result.factor = applyFunc func (fds.map Prod.fst) AND result.dims = fds.map (canonDim .2); canonDim d = if isDimensionless d then dimOne else d). Any impl that closes correct_collectFunction is forced extensionally to the gold post-patch behavior, so it necessarily canonicalises every dimensionless dimension to dimOne and therefore resolves.

AXIOMS AUDIT: axioms region contains ONLY abbrev type aliases (Dim/Factor/Func=Nat) and opaque signatures (dimOne, isDimensionless, applyFunc) — NO 'axiom _prop' declarations, so G-AX skips legitimately; no false axiom can make a wrong impl provable. #print axioms on every verifying file is clean (subset of {propext, Classical.choice, Quot.sound}; atk_7 depends on none).

REFINEMENT.MD A-LEG AUDIT: no A-consumed / A-reference legs exist — every leg is R or I; the deep-modeled changed decision (per-arg canonicalisation) is spelled out via canonDim, NOT axiomatized (correct per SPEC_GUIDE §3); isDimensionless/applyFunc are UNCHANGED callees appearing identically on both differential legs (they cancel), matching real callees DimensionSystem.is_dimensionless and Function.func — correspondence holds.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec): atk_1 prepatch-bug/raw-dims fds.map Prod.snd -> lean_verify EXIT=1 (residual goal 'isDimensionless b = true -> b = dimOne' unprovable — spec rejects the exact prepatch behavior); atk_2 always-dimOne -> EXIT=1; atk_3 inverted-condition (swap branches) -> EXIT=1; atk_4 wrong-factor (applyFunc func []) -> EXIT=1; atk_5 reversed dim list -> EXIT=1; atk_6 partial-domain (head kept raw) -> EXIT=1; atk_8 ungrounded-oracle empty dims -> EXIT=1. atk_7 inline-if (== canonDim, correct echo) -> lean_verify EXIT=0, clean axioms => CANDIDATE => materialized faithful patch (submitted) => run_resolve('sympy__sympy-24066', patch) => RESOLVED=True COMPLETED=True: correct echo of the gold, NOT a weakness.

Positive controls: positive_control.lean (original for-loop impl) EXIT=0 axioms [propext, Quot.sound]; positive_control2.lean (foldr variant, distinct from Solution) EXIT=0 axioms [propext]. PREPATCH REPRODUCED: atk_1 encodes the exact prepatch defect (raw dimensions, no canonicalisation) and fails G-VERIFY (EXIT=1); bundle also ships Solution_prepatch.lean (sorry stub, EXIT=3). Empty-patch base resolve run returned harness error (swebench rejects empty predictions) — not used as evidence; prepatch reproduction established at the Lean layer. COMMANDS: same_spec via markers.same_spec (all True); bash scripts/lean_verify.sh <atk>.lean (exit codes above); #print axioms appended per file (clean); run_resolve for atk_7 (RESOLVED). No same-spec verifying impl has a faithful patch that fails to resolve => verify => correct holds. G-EQ SOUND; attack floor met (8 attacks >= 5).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control2.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the scale factor and dimension of a function application.

A physical expression carries a scale factor together with a dimension. When the
expression is a function applied to one or more arguments, each argument has
already been reduced to its own scale factor and dimension. The combined result
reports:

  * a scale factor equal to the function applied to the arguments' scale factors;
  * for each argument, a dimension equal to the unit dimension `Dimension(1)`
    whenever the dimension system regards that argument's dimension as
    dimensionless, and equal to the argument's dimension otherwise.

The canonicalisation of every dimensionless argument dimension to the single unit
dimension is what lets a later same-dimension comparison recognise two
dimensionless quantities as compatible, even when their dimensions are written in
different but equivalent symbolic forms.
-/

-- axioms-start
-- Two UNCHANGED outside operations are used identically by the specification and
-- the implementation, so each is carried as an opaque callee and NO property of
-- either is consumed (G-AX skips):
--
--   * `isDimensionless` — the dimension system's query deciding whether a
--     dimension reduces to no net dimension. Modelled as an opaque predicate; its
--     internal dependency resolution is out of scope here.
--   * `applyFunc` — rebuilding the function applied to the arguments' scale
--     factors. Unchanged by the modelled behavior; carried opaquely so the scale
--     factor component is pinned to its inputs.
--
-- The argument scale/dimension pairs `fds` are themselves produced by the
-- (unchanged) recursive collection and are carried as grounded inputs, not
-- axiomatised.
abbrev Dim := Nat
abbrev Factor := Nat
abbrev Func := Nat
opaque dimOne : Dim
opaque isDimensionless : Dim → Bool
opaque applyFunc : Func → List Factor → Factor
-- axioms-end

-- pure-start
/-- The collected result of a function application: the rebuilt scale factor and
the per-argument list of (canonicalised) dimensions. -/
structure FunctionResult where
  factor : Factor
  dims : List Dim
deriving DecidableEq, Repr

/-- Canonicalise a single argument's dimension: report the unit dimension when
the dimension system regards it as dimensionless, otherwise report it unchanged. -/
def canonDim (d : Dim) : Dim :=
  if isDimensionless d then dimOne else d
-- pure-end

-- post-conditions-start
/-- The result of collecting a function application: the scale factor is the
function applied to the arguments' scale factors, and the dimension list is the
element-wise canonicalisation of the arguments' dimensions (each dimensionless
dimension reported as the unit dimension, every other dimension unchanged). -/
def problem_spec_collectFunction
    (func : Func) (fds : List (Factor × Dim)) (result : FunctionResult) : Prop :=
  result.factor = applyFunc func (fds.map Prod.fst) ∧
  result.dims = fds.map (fun fd => canonDim fd.2)
-- post-conditions-end

-- impl-start
def implementation_collectFunction
    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=
  { factor := applyFunc func (fds.map Prod.fst),
    dims := fds.foldr (fun fd acc => canonDim fd.2 :: acc) [] }
-- impl-end

-- proof-start
theorem correct_collectFunction :
    ∀ (func : Func) (fds : List (Factor × Dim)),
      problem_spec_collectFunction func fds
        (implementation_collectFunction func fds) := by
  intro func fds
  unfold problem_spec_collectFunction implementation_collectFunction
  refine ⟨rfl, ?_⟩
  induction fds with
  | nil => rfl
  | cons a as ih => simp [List.map, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is FULLY FUNCTIONAL: problem_spec_collectFunction pins BOTH output fields by equality (result.factor = applyFunc func (fds.map Prod.fst) AND result.dims = fds.map (canonDim .2); canonDim d = if isDimensionless d then dimOne else d). Any impl that closes correct_collectFunction is forced extensionally to the gold post-patch behavior, so it necessarily canonicalises every dimensionless dimension to dimOne and therefore resolves.

AXIOMS AUDIT: axioms region contains ONLY abbrev type aliases (Dim/Factor/Func=Nat) and opaque signatures (dimOne, isDimensionless, applyFunc) — NO 'axiom _prop' declarations, so G-AX skips legitimately; no false axiom can make a wrong impl provable. #print axioms on every verifying file is clean (subset of {propext, Classical.choice, Quot.sound}; atk_7 depends on none).

REFINEMENT.MD A-LEG AUDIT: no A-consumed / A-reference legs exist — every leg is R or I; the deep-modeled changed decision (per-arg canonicalisation) is spelled out via canonDim, NOT axiomatized (correct per SPEC_GUIDE §3); isDimensionless/applyFunc are UNCHANGED callees appearing identically on both differential legs (they cancel), matching real callees DimensionSystem.is_dimensionless and Function.func — correspondence holds.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec): atk_1 prepatch-bug/raw-dims fds.map Prod.snd -> lean_verify EXIT=1 (residual goal 'isDimensionless b = true -> b = dimOne' unprovable — spec rejects the exact prepatch behavior); atk_2 always-dimOne -> EXIT=1; atk_3 inverted-condition (swap branches) -> EXIT=1; atk_4 wrong-factor (applyFunc func []) -> EXIT=1; atk_5 reversed dim list -> EXIT=1; atk_6 partial-domain (head kept raw) -> EXIT=1; atk_8 ungrounded-oracle empty dims -> EXIT=1. atk_7 inline-if (== canonDim, correct echo) -> lean_verify EXIT=0, clean axioms => CANDIDATE => materialized faithful patch (submitted) => run_resolve('sympy__sympy-24066', patch) => RESOLVED=True COMPLETED=True: correct echo of the gold, NOT a weakness.

Positive controls: positive_control.lean (original for-loop impl) EXIT=0 axioms [propext, Quot.sound]; positive_control2.lean (foldr variant, distinct from Solution) EXIT=0 axioms [propext]. PREPATCH REPRODUCED: atk_1 encodes the exact prepatch defect (raw dimensions, no canonicalisation) and fails G-VERIFY (EXIT=1); bundle also ships Solution_prepatch.lean (sorry stub, EXIT=3). Empty-patch base resolve run returned harness error (swebench rejects empty predictions) — not used as evidence; prepatch reproduction established at the Lean layer. COMMANDS: same_spec via markers.same_spec (all True); bash scripts/lean_verify.sh <atk>.lean (exit codes above); #print axioms appended per file (clean); run_resolve for atk_7 (RESOLVED). No same-spec verifying impl has a faithful patch that fails to resolve => verify => correct holds. G-EQ SOUND; attack floor met (8 attacks >= 5).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attacker verdict: the spec is a faithful, exact model of the real post-patch callee (the `Function` branch of `UnitSystem._collect_factor_and_dimension`). No diverging input exists.

Gold patch (test.jsonl) post-patch branch:
  fds = [self._collect_factor_and_dimension(arg) for arg in expr.args]
  dims = [Dimension(1) if self.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
  return (expr.func(*(f[0] for f in fds)), *dims)

Spec: result.factor = applyFunc func (fds.map fst) ∧ result.dims = fds.map (fun fd => canonDim fd.2), canonDim d = if isDimensionless d then dimOne else d.

Correspondence checked op-for-op:
- factor: applyFunc over the raw scale factors ↔ expr.func(*(f[0]...)) — canonicalisation does not touch the scale-factor component. Exact.
- dims: element-wise, order-preserving canonDim ↔ the list comprehension `Dimension(1) if is_dimensionless else d`. Exact, including empty-list, mixed, and dimensionless-non-unit (F2P) cases.
- Flat tuple (factor,*dims) ↔ FunctionResult{factor,dims} is a bijective head/tail decomposition.
- isDimensionless / applyFunc are UNCHANGED callees carried as opaque signatures; they appear identically in spec and impl and cancel in the differential, so no property is over- or under-assumed. The spec pins BOTH output components (no free component → not too weak) and adds no extra constraint beyond the post-patch behavior (→ not too strong).

Evidence: (1) lean_verify.sh exit 0; #print axioms correct_collectFunction = [propext, Quot.sound] only — no sorryAx, proof is genuine. (2) same_spec(Solution, Solution_prepatch)=True with LeanBackend — spec region byte-identical to the bug reproducer, which fails G-DIFF as required. (3) conformance_check.py runs oracle=faithful post-patch replica vs shadow of impl over 6 edge cases + 120k fuzzed inputs (seed 24066) with dimensionless predicate crossing both outcomes → 0 disagreements (G-CONF pass). I attempted to construct a diverging fds (dimensionless-non-unit, unit, dimensioned, empty, mixed, multi-arg) and found none where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check, not a rubber-stamp. (1) leakage.screen() run independently over the real frozen row: passed=True, zero hard failures — no diff markers, no gold-patch line reproduced, no patched file/module path (unitsystem.py) in view, no narration term (_NARRATION_RE clean), no spec-view identifier embedding a patched symbol. (2) same_spec(patched, prepatch)=True: the fix lives entirely in the elided impl/proof regions; spec view is identical for both, so it exposes no impl detail. (3) Disclosure boundary: the only changed symbol is collect_factor_and_dimension, which is named verbatim in the public problem_statement (and is exempted). More importantly the spec's target behavior — dimensionless argument dimension canonicalised to Dimension(1) — is ALREADY public: problem_statement states the value 'should be Dimension(1)' for the dimensionless exp() exponent and shows the buggy Dimension(time/(capacitance*impedance)). The spec view therefore reveals nothing about the gold edit beyond what the solver-visible problem_statement already discloses. Spec-view comments describe behavior (canonicalisation enabling same-dimension comparison), not the edit/bug/fix. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).