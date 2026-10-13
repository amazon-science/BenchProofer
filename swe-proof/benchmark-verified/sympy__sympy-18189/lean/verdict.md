# P2 adversarial audit — sympy__sympy-18189

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_dropreindex.lean`, `atk_3_swapargs.lean`, `atk_4_empty.lean`, `atk_5_negcond.lean`, `atk_6_reversed.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7_echo.lean`, `atk_8_mapalt.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
     List (List Int) := Id.run do
   if syms ≠ var then
     let mut acc : List (List Int) := []
-    for t in solveCanonical eq permute do
+    for t in solveCanonical eq false do
       acc := acc ++ [reindexTuple var syms t]
     return acc
   return solveCanonical eq permute
@@ -73,8 +73,6 @@
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
 
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
 private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
     Id.run (forIn xs init
         (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
@@ -95,7 +93,6 @@
   unfold problem_spec_diophantine implementation_diophantine
   by_cases h : syms ≠ var
   · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
     have hbridge :
         Id.run (do
           let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
```

Attack 2 — `atk_2_dropreindex.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,34 +58,16 @@
     (eq : Equation) (var syms : List Nat) (permute : Bool) :
     List (List Int) := Id.run do
   if syms ≠ var then
-    let mut acc : List (List Int) := []
-    for t in solveCanonical eq permute do
-      acc := acc ++ [reindexTuple var syms t]
-    return acc
+    return solveCanonical eq permute
   return solveCanonical eq permute
 -- impl-end
 
 -- proof-start
-/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
 private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
     reindexAll var syms xs = xs.map (reindexTuple var syms) := by
   induction xs with
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
-
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
-private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
-    Id.run (forIn xs init
-        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
-      = init ++ xs.map (reindexTuple var syms) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
 
 theorem correct_diophantine :
     ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
@@ -93,20 +75,7 @@
         (implementation_diophantine eq var syms permute) := by
   intro eq var syms permute
   unfold problem_spec_diophantine implementation_diophantine
-  by_cases h : syms ≠ var
-  · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
-    have hbridge :
-        Id.run (do
-          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
-          pure r)
-        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
-    rw [hbridge, loop_helper, reindexAll_eq_map]
-    simp
-  · rw [if_neg h, if_neg h]
+  by_cases h : syms ≠ var <;>
+    simp_all [reindexAll_eq_map, Id.run, List.forIn_cons] <;>
     rfl
 -- proof-end
```

Attack 3 — `atk_3_swapargs.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
   if syms ≠ var then
     let mut acc : List (List Int) := []
     for t in solveCanonical eq permute do
-      acc := acc ++ [reindexTuple var syms t]
+      acc := acc ++ [reindexTuple syms var t]
     return acc
   return solveCanonical eq permute
 -- impl-end
@@ -73,8 +73,6 @@
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
 
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
 private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
     Id.run (forIn xs init
         (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
@@ -95,7 +93,6 @@
   unfold problem_spec_diophantine implementation_diophantine
   by_cases h : syms ≠ var
   · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
     have hbridge :
         Id.run (do
           let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
```

Attack 4 — `atk_4_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,34 +58,16 @@
     (eq : Equation) (var syms : List Nat) (permute : Bool) :
     List (List Int) := Id.run do
   if syms ≠ var then
-    let mut acc : List (List Int) := []
-    for t in solveCanonical eq permute do
-      acc := acc ++ [reindexTuple var syms t]
-    return acc
+    return []
   return solveCanonical eq permute
 -- impl-end
 
 -- proof-start
-/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
 private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
     reindexAll var syms xs = xs.map (reindexTuple var syms) := by
   induction xs with
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
-
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
-private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
-    Id.run (forIn xs init
-        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
-      = init ++ xs.map (reindexTuple var syms) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
 
 theorem correct_diophantine :
     ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
@@ -93,20 +75,7 @@
         (implementation_diophantine eq var syms permute) := by
   intro eq var syms permute
   unfold problem_spec_diophantine implementation_diophantine
-  by_cases h : syms ≠ var
-  · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
-    have hbridge :
-        Id.run (do
-          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
-          pure r)
-        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
-    rw [hbridge, loop_helper, reindexAll_eq_map]
-    simp
-  · rw [if_neg h, if_neg h]
+  by_cases h : syms ≠ var <;>
+    simp_all [reindexAll_eq_map, Id.run, List.forIn_cons] <;>
     rfl
 -- proof-end
```

Attack 5 — `atk_5_negcond.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,7 @@
 def implementation_diophantine
     (eq : Equation) (var syms : List Nat) (permute : Bool) :
     List (List Int) := Id.run do
-  if syms ≠ var then
+  if syms = var then
     let mut acc : List (List Int) := []
     for t in solveCanonical eq permute do
       acc := acc ++ [reindexTuple var syms t]
@@ -66,26 +66,11 @@
 -- impl-end
 
 -- proof-start
-/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
 private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
     reindexAll var syms xs = xs.map (reindexTuple var syms) := by
   induction xs with
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
-
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
-private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
-    Id.run (forIn xs init
-        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
-      = init ++ xs.map (reindexTuple var syms) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
 
 theorem correct_diophantine :
     ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
@@ -93,20 +78,7 @@
         (implementation_diophantine eq var syms permute) := by
   intro eq var syms permute
   unfold problem_spec_diophantine implementation_diophantine
-  by_cases h : syms ≠ var
-  · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
-    have hbridge :
-        Id.run (do
-          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
-          pure r)
-        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
-    rw [hbridge, loop_helper, reindexAll_eq_map]
-    simp
-  · rw [if_neg h, if_neg h]
+  by_cases h : syms ≠ var <;>
+    simp_all [reindexAll_eq_map, Id.run, List.forIn_cons] <;>
     rfl
 -- proof-end
```

Attack 6 — `atk_6_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
   if syms ≠ var then
     let mut acc : List (List Int) := []
     for t in solveCanonical eq permute do
-      acc := acc ++ [reindexTuple var syms t]
+      acc := [reindexTuple var syms t] ++ acc
     return acc
   return solveCanonical eq permute
 -- impl-end
@@ -73,8 +73,6 @@
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
 
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
 private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
     Id.run (forIn xs init
         (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
@@ -95,7 +93,6 @@
   unfold problem_spec_diophantine implementation_diophantine
   by_cases h : syms ≠ var
   · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
     have hbridge :
         Id.run (do
           let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
```

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,57 +56,16 @@
 -- impl-start
 def implementation_diophantine
     (eq : Equation) (var syms : List Nat) (permute : Bool) :
-    List (List Int) := Id.run do
-  if syms ≠ var then
-    let mut acc : List (List Int) := []
-    for t in solveCanonical eq permute do
-      acc := acc ++ [reindexTuple var syms t]
-    return acc
-  return solveCanonical eq permute
+    List (List Int) :=
+  if syms ≠ var then reindexAll var syms (solveCanonical eq permute)
+  else solveCanonical eq permute
 -- impl-end
 
 -- proof-start
-/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
-private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
-    reindexAll var syms xs = xs.map (reindexTuple var syms) := by
-  induction xs with
-  | nil => rfl
-  | cons a as ih => simp [reindexAll, ih]
-
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
-private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
-    Id.run (forIn xs init
-        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
-      = init ++ xs.map (reindexTuple var syms) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_diophantine :
     ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
       problem_spec_diophantine eq var syms permute
         (implementation_diophantine eq var syms permute) := by
   intro eq var syms permute
-  unfold problem_spec_diophantine implementation_diophantine
-  by_cases h : syms ≠ var
-  · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
-    have hbridge :
-        Id.run (do
-          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
-          pure r)
-        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
-    rw [hbridge, loop_helper, reindexAll_eq_map]
-    simp
-  · rw [if_neg h, if_neg h]
-    rfl
+  rfl
 -- proof-end
```

Attack 8 — `atk_8_mapalt.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,36 +56,17 @@
 -- impl-start
 def implementation_diophantine
     (eq : Equation) (var syms : List Nat) (permute : Bool) :
-    List (List Int) := Id.run do
-  if syms ≠ var then
-    let mut acc : List (List Int) := []
-    for t in solveCanonical eq permute do
-      acc := acc ++ [reindexTuple var syms t]
-    return acc
-  return solveCanonical eq permute
+    List (List Int) :=
+  if syms ≠ var then (solveCanonical eq permute).map (reindexTuple var syms)
+  else solveCanonical eq permute
 -- impl-end
 
 -- proof-start
-/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
 private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
     reindexAll var syms xs = xs.map (reindexTuple var syms) := by
   induction xs with
   | nil => rfl
   | cons a as ih => simp [reindexAll, ih]
-
-/-- The imperative loop, generalized over the accumulator, appends the mapped
-tuples onto the initial accumulator. -/
-private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
-    Id.run (forIn xs init
-        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
-      = init ++ xs.map (reindexTuple var syms) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
 
 theorem correct_diophantine :
     ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
@@ -94,19 +75,6 @@
   intro eq var syms permute
   unfold problem_spec_diophantine implementation_diophantine
   by_cases h : syms ≠ var
-  · rw [if_pos h, if_pos h]
-    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
-    have hbridge :
-        Id.run (do
-          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
-          pure r)
-        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
-            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
-    rw [hbridge, loop_helper, reindexAll_eq_map]
-    simp
+  · rw [if_pos h, if_pos h, reindexAll_eq_map]
   · rw [if_neg h, if_neg h]
-    rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- An opaque carrier for the equation being solved. Only its identity matters
to the modeled behavior; nothing is assumed about its internals. -/
opaque Equation : Type

/-- The canonical solver: it returns the complete list of integer solution
tuples for an equation, with each tuple ordered according to the canonical
ordering of the equation's variables. Its boolean argument selects the
solution-generation mode: when `false`, only the base family of solutions is
produced; when `true`, the additionally admissible solutions are produced as
well. This is an UNCHANGED subroutine the modeled behavior delegates to; the
proof consumes no property of it, so it carries only a signature (no `_prop`
axiom). -/
opaque solveCanonical : Equation → Bool → List (List Int)
-- axioms-end

-- pure-start
/-- Rearrange a single solution tuple from canonical variable order into the
requested symbol order. `var` lists the equation's variables in canonical
order; `syms` lists the requested output order of those same variables. For
each canonical position `i`, the value is read from the tuple at the position
that `i` occupies within `syms`. -/
def reindexTuple (var syms : List Nat) (t : List Int) : List Int :=
  var.map (fun i => t.getD (syms.idxOf i) 0)

/-- Front-recursive specification fold: rearrange every solution tuple of a
solution list, preserving order. -/
def reindexAll (var syms : List Nat) : List (List Int) → List (List Int)
  | [] => []
  | t :: ts => reindexTuple var syms t :: reindexAll var syms ts
-- pure-end

-- post-conditions-start
/-- Desired behavior of solving for the requested symbol order.

`var` is the equation's variables in canonical order; `syms` is the requested
output order; `permute` is the solution-generation mode.

When the requested order differs from the canonical order, the result is the
complete canonical solution set — generated under the SAME `permute` mode —
with every tuple rearranged into the requested order. When the requested order
already matches the canonical order, the result is the canonical solution set
itself (under the same `permute` mode). In particular the solution-generation
mode applies identically whether or not a reordering is requested. -/
def problem_spec_diophantine
    (eq : Equation) (var syms : List Nat) (permute : Bool)
    (result : List (List Int)) : Prop :=
  result =
    (if syms ≠ var then reindexAll var syms (solveCanonical eq permute)
     else solveCanonical eq permute)
-- post-conditions-end

-- impl-start
def implementation_diophantine
    (eq : Equation) (var syms : List Nat) (permute : Bool) :
    List (List Int) := Id.run do
  if syms ≠ var then
    let mut acc : List (List Int) := []
    for t in solveCanonical eq permute do
      acc := acc ++ [reindexTuple var syms t]
    return acc
  return solveCanonical eq permute
-- impl-end

-- proof-start
/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
    reindexAll var syms xs = xs.map (reindexTuple var syms) := by
  induction xs with
  | nil => rfl
  | cons a as ih => simp [reindexAll, ih]

/-- The imperative loop, generalized over the accumulator, appends the mapped
tuples onto the initial accumulator. -/
private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
    Id.run (forIn xs init
        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
      = init ++ xs.map (reindexTuple var syms) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem correct_diophantine :
    ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
      problem_spec_diophantine eq var syms permute
        (implementation_diophantine eq var syms permute) := by
  intro eq var syms permute
  unfold problem_spec_diophantine implementation_diophantine
  by_cases h : syms ≠ var
  · rw [if_pos h, if_pos h]
    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
    have hbridge :
        Id.run (do
          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
            (fun t r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
          pure r)
        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
    rw [hbridge, loop_helper, reindexAll_eq_map]
    simp
  · rw [if_neg h, if_neg h]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is an exact list-equality: problem_spec pins result = (if syms ≠ var then reindexAll var syms (solveCanonical eq permute) else solveCanonical eq permute), with Equation/solveCanonical opaque and NO consumed axioms (proof axioms clean: pos_control [propext, Quot.sound]). same_spec=True for all 8 attacks (spec/axioms/pure/pre/post byte-identical). PROTOCOL: encoded prepatch bug + 5 further DISTINCT wrong impls (partial-domain, boundary/arg-swap, empty-return, control-flow negated-cond, control-flow-effect reversed-order) + 2 ungrounded-oracle/alternative echoes.

### VERIFICATION (scripts/lean_verify.sh, cap 360s, run concurrently ≤4):
- pos_control.lean: exit 0; #print axioms = [propext, Quot.sound] (clean, no sorryAx).
- atk_1_prepatch (solveCanonical eq false on reorder branch — the REAL bug): exit 1, genuine unprovable goal (rewrite failed at line 105: no proof solveCanonical eq false = solveCanonical eq permute for opaque solver). Confirms prepatch reproduced/rejected by spec.
- atk_2_dropreindex (skip reindexTuple): exit 1, rfl failed.
- atk_3_swapargs (reindexTuple syms var — swapped): exit 1, rewrite failed.
- atk_4_empty (return [] on reorder branch): exit 1, rfl failed.
- atk_5_negcond (condition negated syms = var): exit 1, rfl failed.
- atk_6_reversed (prepend → reversed order): exit 1, rewrite failed.
All 6 behaviorally-wrong same-spec impls FAIL TO CLOSE with real unprovable-goal errors (not syntax). The total exact-equality over opaque solveCanonical/reindexTuple admits no closing wrong impl.

CLOSING impls (clean axioms):
- atk_7_echo (literal spec RHS: reindexAll var syms (solveCanonical eq permute)): exit 0; #print axioms = 'does not depend on any axioms'. Behaviorally CORRECT (permute propagated + reindex).
- atk_8_mapalt ((solveCanonical eq permute).map (reindexTuple var syms)): exit 0; #print axioms = [propext]. Behaviorally CORRECT.

MANDATORY RESOLVE of faithful patches for BOTH closing impls: both compute solveCanonical eq permute on the reorder branch with the reindex applied, so the faithful refined patch is the gold edit diophantine(eq, param) → diophantine(eq, param, permute=permute). EXECUTED via swebench_unified.harness.run_resolve("sympy__sympy-18189", <faithful_gold.diff>): completed=True, resolved=True, attempts=1, flaky=False, note=resolved. Both closing impls therefore RESOLVE → no verify⇏correct break.

Every closing impl of the frozen spec is forced to produce the exact pinned value reindexAll var syms (solveCanonical eq permute) on the reorder branch (mode propagated) — which translates back to the gold fix and resolves. No closing impl corresponds to a non-resolving Python edit.

REFINEMENT.MD AUDIT: 5 legs, all R (ops #1 if-cond, #3 loop↔set-comprehension, #4 reindexTuple↔dict_sym_index) or I (op #2 recursive canonical solve, op #5 syms=var fall-through). NO A-consumed, NO A-reference: solveCanonical is an opaque UNCHANGED callee left abstract (no _prop axiom consumed) — axiom_check.py is a legitimate skip stub; the recursive-call correspondence is validated by G-CONF where solveCanonical is realized as the real repo callee diophantine(eq, param, permute=permute). No kind-3 (changed-inexpressible) leg: the fix (threading permute) is captured by op #2, pinned by the spec in BOTH branches. A-leg/callee correspondence holds. Verdict SOUND after 8 attacks (6 fail-to-close, 2 close→resolve); none breaks verify⇒correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_dropreindex.lean`, `atk_3_swapargs.lean`, `atk_4_empty.lean`, `atk_5_negcond.lean`, `atk_6_reversed.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7_echo.lean`, `atk_8_mapalt.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_dropreindex.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_swapargs.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_empty.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_negcond.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_reversed.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_mapalt.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- An opaque carrier for the equation being solved. Only its identity matters
to the modeled behavior; nothing is assumed about its internals. -/
opaque Equation : Type

/-- The canonical solver: it returns the complete list of integer solution
tuples for an equation, with each tuple ordered according to the canonical
ordering of the equation's variables. Its boolean argument selects the
solution-generation mode: when `false`, only the base family of solutions is
produced; when `true`, the additionally admissible solutions are produced as
well. This is an UNCHANGED subroutine the modeled behavior delegates to; the
proof consumes no property of it, so it carries only a signature (no `_prop`
axiom). -/
opaque solveCanonical : Equation → Bool → List (List Int)
-- axioms-end

-- pure-start
/-- Rearrange a single solution tuple from canonical variable order into the
requested symbol order. `var` lists the equation's variables in canonical
order; `syms` lists the requested output order of those same variables. For
each canonical position `i`, the value is read from the tuple at the position
that `i` occupies within `syms`. -/
def reindexTuple (var syms : List Nat) (t : List Int) : List Int :=
  var.map (fun i => t.getD (syms.idxOf i) 0)

/-- Front-recursive specification fold: rearrange every solution tuple of a
solution list, preserving order. -/
def reindexAll (var syms : List Nat) : List (List Int) → List (List Int)
  | [] => []
  | t :: ts => reindexTuple var syms t :: reindexAll var syms ts
-- pure-end

-- post-conditions-start
/-- Desired behavior of solving for the requested symbol order.

`var` is the equation's variables in canonical order; `syms` is the requested
output order; `permute` is the solution-generation mode.

When the requested order differs from the canonical order, the result is the
complete canonical solution set — generated under the SAME `permute` mode —
with every tuple rearranged into the requested order. When the requested order
already matches the canonical order, the result is the canonical solution set
itself (under the same `permute` mode). In particular the solution-generation
mode applies identically whether or not a reordering is requested. -/
def problem_spec_diophantine
    (eq : Equation) (var syms : List Nat) (permute : Bool)
    (result : List (List Int)) : Prop :=
  result =
    (if syms ≠ var then reindexAll var syms (solveCanonical eq permute)
     else solveCanonical eq permute)
-- post-conditions-end

-- impl-start
def implementation_diophantine
    (eq : Equation) (var syms : List Nat) (permute : Bool) :
    List (List Int) := Id.run do
  if syms ≠ var then
    let mut acc : List (List Int) := []
    for t in solveCanonical eq permute do
      acc := acc ++ [reindexTuple var syms t]
    return acc
  return solveCanonical eq permute
-- impl-end

-- proof-start
/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
    reindexAll var syms xs = xs.map (reindexTuple var syms) := by
  induction xs with
  | nil => rfl
  | cons a as ih => simp [reindexAll, ih]

/-- The imperative loop, generalized over the accumulator, appends the mapped
tuples onto the initial accumulator. -/
private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
    Id.run (forIn xs init
        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
      = init ++ xs.map (reindexTuple var syms) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem correct_diophantine :
    ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
      problem_spec_diophantine eq var syms permute
        (implementation_diophantine eq var syms permute) := by
  intro eq var syms permute
  unfold problem_spec_diophantine implementation_diophantine
  by_cases h : syms ≠ var
  · rw [if_pos h, if_pos h]
    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
    have hbridge :
        Id.run (do
          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
            (fun t r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
          pure r)
        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
    rw [hbridge, loop_helper, reindexAll_eq_map]
    simp
  · rw [if_neg h, if_neg h]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is an exact list-equality: problem_spec pins result = (if syms ≠ var then reindexAll var syms (solveCanonical eq permute) else solveCanonical eq permute), with Equation/solveCanonical opaque and NO consumed axioms (proof axioms clean: pos_control [propext, Quot.sound]). same_spec=True for all 8 attacks (spec/axioms/pure/pre/post byte-identical). PROTOCOL: encoded prepatch bug + 5 further DISTINCT wrong impls (partial-domain, boundary/arg-swap, empty-return, control-flow negated-cond, control-flow-effect reversed-order) + 2 ungrounded-oracle/alternative echoes.

### VERIFICATION (scripts/lean_verify.sh, cap 360s, run concurrently ≤4):
- pos_control.lean: exit 0; #print axioms = [propext, Quot.sound] (clean, no sorryAx).
- atk_1_prepatch (solveCanonical eq false on reorder branch — the REAL bug): exit 1, genuine unprovable goal (rewrite failed at line 105: no proof solveCanonical eq false = solveCanonical eq permute for opaque solver). Confirms prepatch reproduced/rejected by spec.
- atk_2_dropreindex (skip reindexTuple): exit 1, rfl failed.
- atk_3_swapargs (reindexTuple syms var — swapped): exit 1, rewrite failed.
- atk_4_empty (return [] on reorder branch): exit 1, rfl failed.
- atk_5_negcond (condition negated syms = var): exit 1, rfl failed.
- atk_6_reversed (prepend → reversed order): exit 1, rewrite failed.
All 6 behaviorally-wrong same-spec impls FAIL TO CLOSE with real unprovable-goal errors (not syntax). The total exact-equality over opaque solveCanonical/reindexTuple admits no closing wrong impl.

CLOSING impls (clean axioms):
- atk_7_echo (literal spec RHS: reindexAll var syms (solveCanonical eq permute)): exit 0; #print axioms = 'does not depend on any axioms'. Behaviorally CORRECT (permute propagated + reindex).
- atk_8_mapalt ((solveCanonical eq permute).map (reindexTuple var syms)): exit 0; #print axioms = [propext]. Behaviorally CORRECT.

MANDATORY RESOLVE of faithful patches for BOTH closing impls: both compute solveCanonical eq permute on the reorder branch with the reindex applied, so the faithful refined patch is the gold edit diophantine(eq, param) → diophantine(eq, param, permute=permute). EXECUTED via swebench_unified.harness.run_resolve("sympy__sympy-18189", <faithful_gold.diff>): completed=True, resolved=True, attempts=1, flaky=False, note=resolved. Both closing impls therefore RESOLVE → no verify⇏correct break.

Every closing impl of the frozen spec is forced to produce the exact pinned value reindexAll var syms (solveCanonical eq permute) on the reorder branch (mode propagated) — which translates back to the gold fix and resolves. No closing impl corresponds to a non-resolving Python edit.

REFINEMENT.MD AUDIT: 5 legs, all R (ops #1 if-cond, #3 loop↔set-comprehension, #4 reindexTuple↔dict_sym_index) or I (op #2 recursive canonical solve, op #5 syms=var fall-through). NO A-consumed, NO A-reference: solveCanonical is an opaque UNCHANGED callee left abstract (no _prop axiom consumed) — axiom_check.py is a legitimate skip stub; the recursive-call correspondence is validated by G-CONF where solveCanonical is realized as the real repo callee diophantine(eq, param, permute=permute). No kind-3 (changed-inexpressible) leg: the fix (threading permute) is captured by op #2, pinned by the spec in BOTH branches. A-leg/callee correspondence holds. Verdict SOUND after 8 attacks (6 fail-to-close, 2 close→resolve); none breaks verify⇒correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-18189 lean bundle.

SETUP: Real repo at base_commit 1923822 checked out to; gold patch applied (recursive `diophantine(eq, param)` -> `diophantine(eq, param, permute=permute)`). Compared the modeled function against the real callee.

MODEL: problem_spec_diophantine pins result = (if syms != var then reindexAll var syms (solveCanonical eq permute) else solveCanonical eq permute). solveCanonical eq permute is the abstract stand-in for the REAL recursive diophantine(eq, param, permute=permute); reindexTuple var syms t = var.map (fun i => t.getD (syms.idxOf i) 0), matching Python `tuple([t[dict_sym_index[i]] for i in var])` with dict_sym_index = dict(zip(syms, range(len(syms)))).

EVIDENCE the spec is NOT too strong / does not drift:
1. Reindex direction verified on a**2+b**2+c**2-14 across ALL 6 permutations of (a,b,c): model set == real set every time.
2. Mode propagation verified on the issue eq n**4+m**4-97 for permute in {False,True} and both orders: match. Both branches thread the caller's permute exactly as the gold patch does.
3. 3000 randomized fuzz cases (sq/even4/sq3 families, shuffled syms, random permute): 0 divergences model vs real.
4. Parametric/linear/3-var families (x**2-y**2, x*(2x+3y-z), x**2+3xy+4x, x**2+y**2+z**2-9, 2x+3y-5, x**2-3y**2-1, x**4+y**4-97) across ALL permutations: 48 checked, 0 divergences.
5. The bundle's conformance_check.py shadow (which also substitutes the real callee) run against the patched repo: 0 disagreements.

ONLY out-of-domain corner: when syms is a strict SUBSET of var (e.g. syms=(a,b) with var=[a,b,c]) the real Python raises KeyError, whereas Lean getD ... 0 would fabricate a 0. This is NOT a spec-too-strong divergence: the real function RAISES there, so it is outside the modeled domain (the differential harness/G-CONF skips inputs the real solver rejects, matching the repo convention). No value-returning real input disagrees with the spec. The spec is if-and-only-if equivalent to the gold-patched repo on the modeled domain, and strictly rejects the prepatch bug (mode dropped on the reorder branch).

AUXILIARY CHECKS: same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) = True (spec region byte-identical; only impl+proof differ). Lean compiles (exit 0); #print axioms correct_diophantine = [propext, Quot.sound] only -> proof is genuine, no sorryAx.

CONCLUSION: The modeled function agrees with the real callee on all in-domain inputs. Spec is faithful (neither too strong nor drifting).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is a one-token propagation: diophantine(eq, param) -> diophantine(eq, param, permute=permute) on the syms-reorder branch (recursive solve loses permute mode). Public problem_statement already fully discloses the defect nature: its title is 'diophantine: incomplete results depending on syms order with permute=True' and it shows syms=(m,n) vs syms=(n,m) with permute=True yielding inconsistent/incomplete solution sets — i.e. permute is dropped on the reorder path. Spec view examined = imports + axioms (Equation, solveCanonical) + pure (reindexTuple, reindexAll) + post-conditions (problem_spec_diophantine); impl and proof regions fully elided. The post-condition states the reorder-branch result is generated under the SAME permute mode; this is the intended-behavior invariant, already implied by problem_statement, not a disclosure of the edit location/token. Checks: (1) mechanical leakage.screen returns passed=True, 0 hard_failures; (2) no diff markers, no patched path sympy/solvers/diophantine.py, no dotted module path in view; (3) verbatim gold tokens (permute=permute, diophantine(eq, param)) absent — recursive call abstracted as solveCanonical eq permute; (4) patched repo symbol 'diophantine' does not appear in spec-view identifiers or comments; (5) no bug/fix narration terms; (6) same_spec(prepatch, patched)=True, so the spec view is byte-identical across buggy/fixed variants and does not discriminate the gold beyond the public statement. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
