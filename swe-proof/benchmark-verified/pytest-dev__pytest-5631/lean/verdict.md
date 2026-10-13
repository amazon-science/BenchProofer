# P2 adversarial audit — pytest-dev__pytest-5631

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec problem_spec_num_mock_patch_args patchings result := result = some ((patchings.filter isCounted).length) is a total function-graph: for every input exactly one result satisfies it. Any implementation whose correct_* closes must therefore be extensionally equal to fun ps => some ((ps.filter isCounted).length) — the reference function — which resolves. No closing-but-non-resolving alternative can exist. All 7 same-spec wrong impls failed to close (genuine 'unsolved goals'), so there is no verifying wrong impl to materialize a patch for.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,53 +47,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
-  if patchings.isEmpty then
-    return some 0
-  let mut count : Nat := 0
-  for p in patchings do
-    if isCounted p then
-      count := count + 1
-  return some count
+def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat :=
+  some 0
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,53 +47,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
-  if patchings.isEmpty then
-    return some 0
-  let mut count : Nat := 0
-  for p in patchings do
-    if isCounted p then
-      count := count + 1
-  return some count
+def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat :=
+  some ((patchings.filter (fun p => !p.attributeName)).length)
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,48 +52,25 @@
     return some 0
   let mut count : Nat := 0
   for p in patchings do
-    if isCounted p then
-      count := count + 1
+    if !p.attributeName then
+      if !p.eqWellDefined then
+        return none
+      if p.isSentinel then
+        count := count + 1
   return some count
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,53 +47,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
-  if patchings.isEmpty then
-    return some 0
-  let mut count : Nat := 0
-  for p in patchings do
-    if isCounted p then
-      count := count + 1
-  return some count
+def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat :=
+  some ((patchings.filter (fun p => !p.attributeName && p.eqWellDefined)).length)
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,53 +47,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
-  if patchings.isEmpty then
-    return some 0
-  let mut count : Nat := 0
-  for p in patchings do
-    if isCounted p then
-      count := count + 1
-  return some count
+def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat :=
+  some ((patchings.filter (fun p => p.isSentinel)).length)
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,53 +47,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
-  if patchings.isEmpty then
-    return some 0
-  let mut count : Nat := 0
-  for p in patchings do
-    if isCounted p then
-      count := count + 1
-  return some count
+def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat :=
+  some ((patchings.filter isCounted).length + 1)
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,53 +47,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
-  if patchings.isEmpty then
-    return some 0
-  let mut count : Nat := 0
-  for p in patchings do
-    if isCounted p then
-      count := count + 1
-  return some count
+def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat :=
+  some patchings.length
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the conditional `forIn` loop, generalized over the
-accumulator, counts exactly the decorations satisfying `isCounted`. -/
-theorem forIn_count_eq (xs : List Patching) (init : Nat) :
-    Id.run (forIn xs init (fun p r =>
-      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
-      = init + (xs.filter isCounted).length := by
-  induction xs generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    by_cases h : isCounted a = true
-    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
-    · simp only [Bool.not_eq_true] at h
-      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]
-
 theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
     problem_spec_num_mock_patch_args patchings
       (implementation_num_mock_patch_args patchings) := by
   intro patchings
   unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
-  by_cases he : patchings.isEmpty = true
-  · simp only [Id.run, he, if_true]
-    rw [List.isEmpty_iff] at he
-    subst he
-    rfl
-  · simp only [Id.run]
-    rw [if_neg he]
-    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
-    have h2 : (do
-        pure PUnit.unit
-        let r ← forIn patchings 0 (fun p r =>
-          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-          else do pure PUnit.unit; pure (ForInStep.yield r))
-        pure (some r) : Id (Option Nat))
-      = some (Id.run (forIn patchings 0 (fun p r =>
-          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
-    rw [h2, forIn_count_eq, Nat.zero_add]
+  simp_all [Id.run, isCounted, List.filter]
+  try rfl
+  try omega
+  try decide
+  try (induction patchings with
+      | nil => simp_all
+      | cons a as ih => simp_all [List.filter_cons]; try omega)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decoration count is
-- modeled DEEPLY over an abstraction of each decoration (below): whether it binds
-- a named attribute, whether its replacement is one of the recognised sentinel
-- defaults, and whether comparing that replacement for equality yields an
-- ordinary boolean. No outside callee property is consumed; the proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- Abstraction of a single mock-patch decoration attached to a test function.

* `attributeName` — `true` when the decoration binds a named attribute (so it
  does NOT consume one of the function's positional arguments).
* `isSentinel` — `true` when the decoration's replacement value is one of the
  recognised sentinel "default" objects (the marker meaning "auto-create a mock
  for this argument").
* `eqWellDefined` — `true` when comparing this replacement value for equality
  against another object yields an ordinary boolean. It is `false` for values
  (such as numeric arrays) whose equality comparison produces a non-boolean and
  therefore has an ambiguous truth value. -/
structure Patching where
  attributeName : Bool
  isSentinel : Bool
  eqWellDefined : Bool
deriving DecidableEq, Repr

/-- A decoration consumes one mandatory argument exactly when it does not bind a
named attribute and its replacement is one of the recognised sentinel defaults. -/
def isCounted (p : Patching) : Bool := !p.attributeName && p.isSentinel
-- pure-end

-- post-conditions-start
/-- The number of mandatory arguments consumed by mock-patch decorations is
returned as `some n`, where `n` is exactly the count of decorations that consume
an argument (do not bind a named attribute and replace with a sentinel default).
The count is always produced (`some _`): determining it must never depend on the
ambiguous truth value of an equality comparison, so a decoration whose
replacement compares with an ill-defined truth value is still classified totally
by the structural criterion above. -/
def problem_spec_num_mock_patch_args
    (patchings : List Patching) (result : Option Nat) : Prop :=
  result = some ((patchings.filter isCounted).length)
-- post-conditions-end

-- impl-start
def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
  if patchings.isEmpty then
    return some 0
  let mut count : Nat := 0
  for p in patchings do
    if isCounted p then
      count := count + 1
  return some count
-- impl-end

-- proof-start
/-- Helper (Route B): the conditional `forIn` loop, generalized over the
accumulator, counts exactly the decorations satisfying `isCounted`. -/
theorem forIn_count_eq (xs : List Patching) (init : Nat) :
    Id.run (forIn xs init (fun p r =>
      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
      = init + (xs.filter isCounted).length := by
  induction xs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    by_cases h : isCounted a = true
    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
    · simp only [Bool.not_eq_true] at h
      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]

theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
    problem_spec_num_mock_patch_args patchings
      (implementation_num_mock_patch_args patchings) := by
  intro patchings
  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
  by_cases he : patchings.isEmpty = true
  · simp only [Id.run, he, if_true]
    rw [List.isEmpty_iff] at he
    subst he
    rfl
  · simp only [Id.run]
    rw [if_neg he]
    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
    have h2 : (do
        pure PUnit.unit
        let r ← forIn patchings 0 (fun p r =>
          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
          else do pure PUnit.unit; pure (ForInStep.yield r))
        pure (some r) : Id (Option Nat))
      = some (Id.run (forIn patchings 0 (fun p r =>
          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
    rw [h2, forIn_count_eq, Nat.zero_add]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. Same-spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (get_backend('lean')). Positive control (unmodified Solution.lean) verifies: lean_verify.sh exit 0; #print axioms correct_num_mock_patch_args => [propext, Quot.sound] (clean, no sorryAx). Prepatch bug reproduced: atk_3 encodes the prepatch equality-membership skeleton (returns none on !eqWellDefined) — its proof does NOT close (exit 1, unsolved goals), matching Solution_prepatch.lean and the F2P signal test_mock_sentinel_check_against_numpy_like.

7 DISTINCT same-spec wrong impls, each with an aggressive closing-proof attempt (simp_all + rfl/omega/decide + structural induction). Verified concurrently (≤4 background jobs). ALL failed to close with 'error: unsolved goals' (NOT compile errors):
- atk_1 (ungrounded/partial-domain): some 0 — EXIT=1
- atk_2 (classifier defect): count all non-attribute, ignore isSentinel — EXIT=1
- atk_3 (control-flow-effect / prepatch echo): none-abort on !eqWellDefined — EXIT=1
- atk_4 (ungrounded-oracle echo): gate on eqWellDefined instead of isSentinel — EXIT=1
- atk_5 (classifier defect): count all sentinels, drop attributeName gate — EXIT=1
- atk_6 (boundary/off-by-one): correct count + 1 — EXIT=1
- atk_7 (classifier defect): count total patchings.length — EXIT=1

Commands: cd; bash scripts/lean_verify.sh atk_N.lean. Exits recorded in exits.txt; per-attack stderr in out_N.txt (all show 'unsolved goals').

Because NO wrong impl closed with clean axioms, there was no faithful patch to materialize and run through run_resolve — protocol step 2 is vacuously satisfied (no verifying-but-non-resolving impl exists to break verify=>correct).

refinement.md AUDIT: legs are op1=R (type refinement List Patching), op2/3/4=I (empty short-circuit, count init, per-decoration iteration), op5=A-reference (introduced identity classifier modeled DEEPLY as isCounted = !attributeName && isSentinel, validated == real post-patch callee by G-AX incl. numpy-like replacements; NOT axiomatized), op6=R (Option/some codomain). No A-consumed rows, NO kind-3 (changed-inexpressible) legs. The single A-reference leg's correspondence to the real callee not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel) holds. axioms region is empty (no opaque callee signatures), consistent with meta.json and mapping.md. All legs valid (R / A-reference / I).

VERDICT: SOUND. verify => correct holds for this bundle: the spec uniquely pins output per input, so the only closing impl is the reference (which resolves), confirmed by 7 falsification attempts all failing to close.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec problem_spec_num_mock_patch_args patchings result := result = some ((patchings.filter isCounted).length) is a total function-graph: for every input exactly one result satisfies it. Any implementation whose correct_* closes must therefore be extensionally equal to fun ps => some ((ps.filter isCounted).length) — the reference function — which resolves. No closing-but-non-resolving alternative can exist. All 7 same-spec wrong impls failed to close (genuine 'unsolved goals'), so there is no verifying wrong impl to materialize a patch for.
```

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

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decoration count is
-- modeled DEEPLY over an abstraction of each decoration (below): whether it binds
-- a named attribute, whether its replacement is one of the recognised sentinel
-- defaults, and whether comparing that replacement for equality yields an
-- ordinary boolean. No outside callee property is consumed; the proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- Abstraction of a single mock-patch decoration attached to a test function.

* `attributeName` — `true` when the decoration binds a named attribute (so it
  does NOT consume one of the function's positional arguments).
* `isSentinel` — `true` when the decoration's replacement value is one of the
  recognised sentinel "default" objects (the marker meaning "auto-create a mock
  for this argument").
* `eqWellDefined` — `true` when comparing this replacement value for equality
  against another object yields an ordinary boolean. It is `false` for values
  (such as numeric arrays) whose equality comparison produces a non-boolean and
  therefore has an ambiguous truth value. -/
structure Patching where
  attributeName : Bool
  isSentinel : Bool
  eqWellDefined : Bool
deriving DecidableEq, Repr

/-- A decoration consumes one mandatory argument exactly when it does not bind a
named attribute and its replacement is one of the recognised sentinel defaults. -/
def isCounted (p : Patching) : Bool := !p.attributeName && p.isSentinel
-- pure-end

-- post-conditions-start
/-- The number of mandatory arguments consumed by mock-patch decorations is
returned as `some n`, where `n` is exactly the count of decorations that consume
an argument (do not bind a named attribute and replace with a sentinel default).
The count is always produced (`some _`): determining it must never depend on the
ambiguous truth value of an equality comparison, so a decoration whose
replacement compares with an ill-defined truth value is still classified totally
by the structural criterion above. -/
def problem_spec_num_mock_patch_args
    (patchings : List Patching) (result : Option Nat) : Prop :=
  result = some ((patchings.filter isCounted).length)
-- post-conditions-end

-- impl-start
def implementation_num_mock_patch_args (patchings : List Patching) : Option Nat := Id.run do
  if patchings.isEmpty then
    return some 0
  let mut count : Nat := 0
  for p in patchings do
    if isCounted p then
      count := count + 1
  return some count
-- impl-end

-- proof-start
/-- Helper (Route B): the conditional `forIn` loop, generalized over the
accumulator, counts exactly the decorations satisfying `isCounted`. -/
theorem forIn_count_eq (xs : List Patching) (init : Nat) :
    Id.run (forIn xs init (fun p r =>
      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))
      = init + (xs.filter isCounted).length := by
  induction xs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    by_cases h : isCounted a = true
    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega
    · simp only [Bool.not_eq_true] at h
      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]

theorem correct_num_mock_patch_args : ∀ patchings : List Patching,
    problem_spec_num_mock_patch_args patchings
      (implementation_num_mock_patch_args patchings) := by
  intro patchings
  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args
  by_cases he : patchings.isEmpty = true
  · simp only [Id.run, he, if_true]
    rw [List.isEmpty_iff] at he
    subst he
    rfl
  · simp only [Id.run]
    rw [if_neg he]
    -- bridge the desugared loop body to the helper's clean body (definitionally equal)
    have h2 : (do
        pure PUnit.unit
        let r ← forIn patchings 0 (fun p r =>
          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
          else do pure PUnit.unit; pure (ForInStep.yield r))
        pure (some r) : Id (Option Nat))
      = some (Id.run (forIn patchings 0 (fun p r =>
          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl
    rw [h2, forIn_count_eq, Nat.zero_add]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. Same-spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (get_backend('lean')). Positive control (unmodified Solution.lean) verifies: lean_verify.sh exit 0; #print axioms correct_num_mock_patch_args => [propext, Quot.sound] (clean, no sorryAx). Prepatch bug reproduced: atk_3 encodes the prepatch equality-membership skeleton (returns none on !eqWellDefined) — its proof does NOT close (exit 1, unsolved goals), matching Solution_prepatch.lean and the F2P signal test_mock_sentinel_check_against_numpy_like.

7 DISTINCT same-spec wrong impls, each with an aggressive closing-proof attempt (simp_all + rfl/omega/decide + structural induction). Verified concurrently (≤4 background jobs). ALL failed to close with 'error: unsolved goals' (NOT compile errors):
- atk_1 (ungrounded/partial-domain): some 0 — EXIT=1
- atk_2 (classifier defect): count all non-attribute, ignore isSentinel — EXIT=1
- atk_3 (control-flow-effect / prepatch echo): none-abort on !eqWellDefined — EXIT=1
- atk_4 (ungrounded-oracle echo): gate on eqWellDefined instead of isSentinel — EXIT=1
- atk_5 (classifier defect): count all sentinels, drop attributeName gate — EXIT=1
- atk_6 (boundary/off-by-one): correct count + 1 — EXIT=1
- atk_7 (classifier defect): count total patchings.length — EXIT=1

Commands: cd; bash scripts/lean_verify.sh atk_N.lean. Exits recorded in exits.txt; per-attack stderr in out_N.txt (all show 'unsolved goals').

Because NO wrong impl closed with clean axioms, there was no faithful patch to materialize and run through run_resolve — protocol step 2 is vacuously satisfied (no verifying-but-non-resolving impl exists to break verify=>correct).

refinement.md AUDIT: legs are op1=R (type refinement List Patching), op2/3/4=I (empty short-circuit, count init, per-decoration iteration), op5=A-reference (introduced identity classifier modeled DEEPLY as isCounted = !attributeName && isSentinel, validated == real post-patch callee by G-AX incl. numpy-like replacements; NOT axiomatized), op6=R (Option/some codomain). No A-consumed rows, NO kind-3 (changed-inexpressible) legs. The single A-reference leg's correspondence to the real callee not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel) holds. axioms region is empty (no opaque callee signatures), consistent with meta.json and mapping.md. All legs valid (R / A-reference / I).

VERDICT: SOUND. verify => correct holds for this bundle: the spec uniquely pins output per input, so the only closing impl is the reference (which resolves), confirmed by 7 falsification attempts all failing to close.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pytest-dev__pytest-5631 (lean). The modeled function implementation_num_mock_patch_args : List Patching -> Option Nat models the POST-PATCH _pytest.compat.num_mock_patch_args, which counts decorations where `not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)` and always returns an int. VERIFICATION: (1) Solution.lean compiles clean via lean_verify.sh (exit 0, no sorry). (2) #print axioms correct_num_mock_patch_args = [propext, Quot.sound] only -- no sorryAx/custom axioms; the proof is genuine. (3) same_spec(Solution, Solution_prepatch, lean-backend) = True -- spec region byte-identical between patched and prepatch skeletons. FAITHFULNESS ANALYSIS: the real post-patch callee's output depends on exactly two per-decoration facts -- `not p.attribute_name` (Python truthiness) and identity-match against a sentinel -- which map precisely to Patching.attributeName / Patching.isSentinel. eqWellDefined is correctly latent (post-patch identity test never raises, so it does not affect output). The post-patch removed the pre-patch `else: return len(patchings)` branch, so the identity classifier is universal across all module configs: in the mock-absent case getattr(...,object()) supplies a fresh unique sentinel, identity never matches -> 0 contribution, captured by isSentinel=false. Empty/missing patchings -> int 0 -> some 0. The spec `result = some((patchings.filter isCounted).length)` is EXACTLY the post-patch behavior -- not too strong: it always yields some _ (never the ambiguous-equality raise), matching the callee which always returns an int post-patch. Ran conformance_check.py: 120007 inputs (7 boundary + 120000 fuzz, incl. numpy-like ambiguous-equality replacements) diffing the reconstructed REAL post-patch callee against the R/I shadow -> 0 disagreements. No input found where the modeled function disagrees with the real callee. Spec does not drift from / over-strengthen the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). same_spec(Solution, Solution_prepatch)=True and the spec region is byte-identical, so the spec view is stable across the edit. Only patch-changed symbol is 'num_mock_patch_args', which is already public in the problem_statement (verbatim). Semantic review: the public problem_statement is highly detailed — it names num_mock_patch_args, quotes the buggy line 'p.new in sentinels', describes the ValueError from an array's ambiguous truth value, and mentions sentinel/attribute/array. The spec view (docstrings on Patching/isSentinel/problem_spec) describes only the REQUIRED post-patch behavior: count is always produced (some _), classification must not depend on the ambiguous truth value of an equality comparison, and abstracts the recognition of a sentinel into a behavior-neutral bit `isSentinel`. It does NOT reveal the specific gold edit (replacing `p.new in sentinels` equality-membership with identity tests `p.new is mock_sentinel or p.new is ut_mock_sentinel`) — 'identity'/'is mock_sentinel' appear nowhere in the spec view. The eqWellDefined abstraction and the 'ambiguous truth value' framing mirror the problem_statement's own ValueError description, not the fix. Nothing in the spec view goes beyond what problem_statement already discloses; the gold's mechanism (equality->identity) is not reconstructible from the spec view. No diff markers, no gold-patch line reproduced, no patched file path, no narration.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
