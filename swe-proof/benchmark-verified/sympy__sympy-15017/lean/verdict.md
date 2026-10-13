# P2 adversarial audit — sympy__sympy-15017

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -32,11 +32,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arraySize (shape : List Nat) : Nat := Id.run do
-  let mut acc := 1
-  for d in shape do
-    acc := acc * d
-  return acc
+def implementation_arraySize (shape : List Nat) : Nat := 0
 -- impl-end
 
 -- proof-start
@@ -45,17 +41,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,11 +32,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arraySize (shape : List Nat) : Nat := Id.run do
-  let mut acc := 1
-  for d in shape do
-    acc := acc * d
-  return acc
+def implementation_arraySize (shape : List Nat) : Nat := 1
 -- impl-end
 
 -- proof-start
@@ -45,17 +41,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,7 @@
 def implementation_arraySize (shape : List Nat) : Nat := Id.run do
   let mut acc := 1
   for d in shape do
-    acc := acc * d
+    acc := acc + d
   return acc
 -- impl-end
 
@@ -45,17 +45,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,10 +33,13 @@
 
 -- impl-start
 def implementation_arraySize (shape : List Nat) : Nat := Id.run do
-  let mut acc := 1
-  for d in shape do
-    acc := acc * d
-  return acc
+  match shape with
+  | [] => return 0
+  | d :: ds =>
+    let mut acc := d
+    for x in ds do
+      acc := acc * x
+    return acc
 -- impl-end
 
 -- proof-start
@@ -45,17 +48,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,11 +32,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arraySize (shape : List Nat) : Nat := Id.run do
-  let mut acc := 1
-  for d in shape do
-    acc := acc * d
-  return acc
+def implementation_arraySize (shape : List Nat) : Nat := shape.length
 -- impl-end
 
 -- proof-start
@@ -45,17 +41,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,11 +32,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arraySize (shape : List Nat) : Nat := Id.run do
-  let mut acc := 1
-  for d in shape do
-    acc := acc * d
-  return acc
+def implementation_arraySize (shape : List Nat) : Nat := shape.prod + 1
 -- impl-end
 
 -- proof-start
@@ -45,17 +41,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,7 @@
 
 -- impl-start
 def implementation_arraySize (shape : List Nat) : Nat := Id.run do
-  let mut acc := 1
+  let mut acc := 0
   for d in shape do
     acc := acc * d
   return acc
@@ -45,17 +45,11 @@
       problem_spec_arraySize shape (implementation_arraySize shape) := by
   intro shape
   unfold problem_spec_arraySize implementation_arraySize
-  have h : ∀ (acc : Nat) (l : List Nat),
-      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
-        = l.foldl (· * ·) acc := by
-    intro acc l
-    induction l generalizing acc with
-    | nil => rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih, List.foldl_cons]
-  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
-  rw [h]
-  rw [List.prod_eq_foldl]
+  first
+    | rfl
+    | simp [List.prod, Id.run] <;> (try omega) <;> (try rfl)
+    | decide
+    | (induction shape with
+       | nil => rfl
+       | cons a as ih => simp_all [List.prod, Id.run])
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The number of elements held by an N-dimensional array.

An N-dimensional array has a shape: a finite list of non-negative dimension
sizes (for example a 2×3 array has shape `[2, 3]`). The number of elements the
array contains is the product of its dimension sizes. A rank-0 array — one with
no dimensions at all, i.e. a scalar — therefore holds a single element, matching
the convention that an empty product is one.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the dimension sizes are
-- the inputs, and the element count is their product, modeled directly.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required.)
-- pure-end

-- post-conditions-start
/-- The element count is exactly the product of the dimension sizes. The product
of the empty list is one, so a scalar (no dimensions) has a single element; for
any list of dimensions the count is pinned to their product. -/
def problem_spec_arraySize (shape : List Nat) (result : Nat) : Prop :=
  result = shape.prod
-- post-conditions-end

-- impl-start
def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc * d
  return acc
-- impl-end

-- proof-start
theorem correct_arraySize :
    ∀ (shape : List Nat),
      problem_spec_arraySize shape (implementation_arraySize shape) := by
  intro shape
  unfold problem_spec_arraySize implementation_arraySize
  have h : ∀ (acc : Nat) (l : List Nat),
      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
        = l.foldl (· * ·) acc := by
    intro acc l
    induction l generalizing acc with
    | nil => rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih, List.foldl_cons]
  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
  rw [h]
  rw [List.prod_eq_foldl]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_arraySize shape result := result = shape.prod. This is a TIGHT functional equality — the postcondition pins the result to a single value for every input, so any implementation that proves correct_arraySize must be extensionally equal to shape.prod on all inputs (Lean is sound). Attack strategy therefore targets whether any same-spec WRONG impl can nonetheless close its proof with clean axioms.

SAME-SPEC: all 7 attacks byte-identical outside the impl region; swebench_unified.markers.same_spec == True for all 7 (verified twice, after final rewrite).

POSITIVE CONTROL (pos_control.lean = gold Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. `#print axioms correct_arraySize` (pos_axioms.lean) -> "depends on axioms: [propext, Quot.sound]" — clean, no sorryAx / no custom axioms.

ATTACKS (each: distinct wrong impl, GENUINE strong closing attempt — no sorry — battery `first | rfl | simp[List.prod,Id.run]<;>omega<;>rfl | decide | induction ...`). Command for each: `bash scripts/lean_verify.sh atk_N.lean`. sorry-count = 0 for all.
  atk_1: impl := 0 (ungrounded oracle / trivial)                 -> exit 1 (unsolved goals)
  atk_2: impl := 1 (empty-product-only constant)                 -> exit 1
  atk_3: for-loop with + instead of * (control-flow-effect)      -> exit 1, residual goal `foldl (+) 1 shape = foldr (*) 1 shape`
  atk_4: PREPATCH BUG — match []=>0 else fold* (boundary bug)    -> exit 1, residual `(match...) = foldr (*) 1 shape` (unprovable at shape=[])
  atk_5: impl := shape.length (partial-domain agree on [d])      -> exit 1
  atk_6: impl := shape.prod + 1 (off-by-one boundary)            -> exit 1
  atk_7: for-loop * with seed acc:=0 (wrong seed -> always 0)    -> exit 1, residual `foldl (*) 0 shape = foldr (*) 1 shape`

RESULT: NO wrong impl produced a closing clean-axiom proof (all exit 1). Therefore step-2's obligation (materialize + run_resolve the faithful patch for every VERIFYING wrong impl) is VACUOUS — there is no verifying-but-wrong candidate. patches={} accordingly. The prepatch bug (atk_4) is reproduced: the buggy skeleton cannot be proven correct (prepatch Solution_prepatch.lean carries `sorry`), matching refinement.md's G-DIFF claim (scalar rank-0 -> 0 vs required 1).

REFINEMENT AUDIT: every leg is R (tuple->List Nat; result->Nat) or I (fold seed 1; reduce(*)<->for-loop *). No A-consumed, no A-reference, no kind-3. axiom_check.py is a correct G-AX skip stub (status=skip): no unchanged repo callee contract is assumed; integer multiplication over the dimension list is modeled DEEPLY as List.prod. mapping.md callee provenance confirms shape is List Nat-faithful (dims are ints >=0 post _handle_ndarray_creation_inputs) and __len__ returns _loop_size verbatim, so the modeled value is exactly the F2P observable. Model<->patch correspondence (shape.prod, empty product 1 <-> functools.reduce(lambda x,y:x*y, shape, 1)) holds.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7) attacked; positive control verifies with clean axioms; none of the wrong impls closes, so verify=>correct is not falsified for this spec.

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
The number of elements held by an N-dimensional array.

An N-dimensional array has a shape: a finite list of non-negative dimension
sizes (for example a 2×3 array has shape `[2, 3]`). The number of elements the
array contains is the product of its dimension sizes. A rank-0 array — one with
no dimensions at all, i.e. a scalar — therefore holds a single element, matching
the convention that an empty product is one.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the dimension sizes are
-- the inputs, and the element count is their product, modeled directly.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required.)
-- pure-end

-- post-conditions-start
/-- The element count is exactly the product of the dimension sizes. The product
of the empty list is one, so a scalar (no dimensions) has a single element; for
any list of dimensions the count is pinned to their product. -/
def problem_spec_arraySize (shape : List Nat) (result : Nat) : Prop :=
  result = shape.prod
-- post-conditions-end

-- impl-start
def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc * d
  return acc
-- impl-end

-- proof-start
theorem correct_arraySize :
    ∀ (shape : List Nat),
      problem_spec_arraySize shape (implementation_arraySize shape) := by
  intro shape
  unfold problem_spec_arraySize implementation_arraySize
  have h : ∀ (acc : Nat) (l : List Nat),
      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
        = l.foldl (· * ·) acc := by
    intro acc l
    induction l generalizing acc with
    | nil => rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih, List.foldl_cons]
  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
  rw [h]
  rw [List.prod_eq_foldl]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_arraySize shape result := result = shape.prod. This is a TIGHT functional equality — the postcondition pins the result to a single value for every input, so any implementation that proves correct_arraySize must be extensionally equal to shape.prod on all inputs (Lean is sound). Attack strategy therefore targets whether any same-spec WRONG impl can nonetheless close its proof with clean axioms.

SAME-SPEC: all 7 attacks byte-identical outside the impl region; swebench_unified.markers.same_spec == True for all 7 (verified twice, after final rewrite).

POSITIVE CONTROL (pos_control.lean = gold Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. `#print axioms correct_arraySize` (pos_axioms.lean) -> "depends on axioms: [propext, Quot.sound]" — clean, no sorryAx / no custom axioms.

ATTACKS (each: distinct wrong impl, GENUINE strong closing attempt — no sorry — battery `first | rfl | simp[List.prod,Id.run]<;>omega<;>rfl | decide | induction ...`). Command for each: `bash scripts/lean_verify.sh atk_N.lean`. sorry-count = 0 for all.
  atk_1: impl := 0 (ungrounded oracle / trivial)                 -> exit 1 (unsolved goals)
  atk_2: impl := 1 (empty-product-only constant)                 -> exit 1
  atk_3: for-loop with + instead of * (control-flow-effect)      -> exit 1, residual goal `foldl (+) 1 shape = foldr (*) 1 shape`
  atk_4: PREPATCH BUG — match []=>0 else fold* (boundary bug)    -> exit 1, residual `(match...) = foldr (*) 1 shape` (unprovable at shape=[])
  atk_5: impl := shape.length (partial-domain agree on [d])      -> exit 1
  atk_6: impl := shape.prod + 1 (off-by-one boundary)            -> exit 1
  atk_7: for-loop * with seed acc:=0 (wrong seed -> always 0)    -> exit 1, residual `foldl (*) 0 shape = foldr (*) 1 shape`

RESULT: NO wrong impl produced a closing clean-axiom proof (all exit 1). Therefore step-2's obligation (materialize + run_resolve the faithful patch for every VERIFYING wrong impl) is VACUOUS — there is no verifying-but-wrong candidate. patches={} accordingly. The prepatch bug (atk_4) is reproduced: the buggy skeleton cannot be proven correct (prepatch Solution_prepatch.lean carries `sorry`), matching refinement.md's G-DIFF claim (scalar rank-0 -> 0 vs required 1).

REFINEMENT AUDIT: every leg is R (tuple->List Nat; result->Nat) or I (fold seed 1; reduce(*)<->for-loop *). No A-consumed, no A-reference, no kind-3. axiom_check.py is a correct G-AX skip stub (status=skip): no unchanged repo callee contract is assumed; integer multiplication over the dimension list is modeled DEEPLY as List.prod. mapping.md callee provenance confirms shape is List Nat-faithful (dims are ints >=0 post _handle_ndarray_creation_inputs) and __len__ returns _loop_size verbatim, so the modeled value is exactly the F2P observable. Model<->patch correspondence (shape.prod, empty product 1 <-> functools.reduce(lambda x,y:x*y, shape, 1)) holds.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7) attacked; positive control verifies with clean axioms; none of the wrong impls closes, so verify=>correct is not falsified for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec: problem_spec_arraySize shape result := result = shape.prod. Modeled fn = element-count computation in ImmutableDenseNDimArray._new (dense_ndim_array.py:152), consumed verbatim by NDimArray.__len__ (returns self._loop_size). Gold patch: reduce(mul,shape) if shape else 0  ->  reduce(mul,shape,1) (product with seed 1, empty product = 1). CHECKS: (1) same_spec(Solution,Solution_prepatch,LeanBackend)=True — spec region byte-identical to prepatch, only impl/proof differ. (2) lean_verify.sh exit 0. (3) #print axioms correct_arraySize -> [propext, Quot.sound], NO sorryAx — proof genuine. Faithfulness: applied gold patch to base-commit worktree, diff-tested spec (shape.prod) vs real len(ImmutableDenseNDimArray) over 200,010 cases (discrete F2P edge cases [] ->1, [0]->0, [0,5]->0, [0,0]->0 + random ranks 0-4, dims 0-6): 0 disagreements. __len__ returns _loop_size verbatim (ndim_array.py:178). (5) Type mapping List Nat faithful: _handle_ndarray_creation_inputs raises TypeError for non-integer dims and sizes are >=0, so Python domain == non-negative ints. The spec is exact equality to the product; real patched repo produces exactly the product on every input. No input where the modeled function disagrees with the real callee; spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged over the consumer SPEC VIEW of Solution.lean (impl+proof elided), which is what G-LEAK/leakage.screen and same_spec operate on — NOT refinement.md/mapping.md (auditor-internal, non-consumer-visible; those legitimately quote the gold diff).

Mechanical screen: leakage.screen() PASSES (hard_failures=[]) — no diff markers, no reproduced gold-patch line, no patched file/module path in view, no spec-view identifier or comment naming a patched repo symbol (_loop_size/_new/reduce never appear), no bug/fix narration.

Structural checks: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical; the fix lives entirely in the elided impl/proof). scripts/lean_verify.sh exit 0 (compiles, no sorry) so the spec is a real spec, not a degenerate placeholder.

Semantic judgment vs the PUBLIC problem_statement (not hints_text): the problem statement already publicly discloses the target behavior — 'len of rank-0 arrays returns 0 … the correct value should be one … number of elements … numpy.asarray(1).size == 1'. The spec-view docstring states only the general correct rule ('the number of elements is the product of the dimension sizes; a rank-0 array holds a single element, matching the convention that an empty product is one') and the post-condition `result = shape.prod`. The rank-0→1 fact is already public via the task; 'empty product = 1' is the standard mathematical convention, not a disclosure of the gold's specific edit (the functools.reduce seed byte). The spec view does not narrate the bug, reference the reduce initializer/_loop_size/_new symbols, or the file path. Faithful abstract input→output relation; no leak beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
