# P2 adversarial audit — django__django-12965

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The post-condition problem_spec_isSingleTableDelete refs result := result = (activeCount (includePrimary refs) == 1) is a TOTAL BICONDITIONAL over the sole input refs : List Nat, with activeCount and includePrimary both CONCRETE defs (not axioms/opaque) — so there is zero proof slack. Any implementation whose correct_ closes is extensionally forced to return exactly activeCount (includePrimary refs) == 1, which is precisely the resolving (gold) behavior. No closing-but-non-resolving impl exists, so no counterexample and no patch to materialize.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,17 +63,11 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
-  let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
-  let mut active := 0
-  for c in refs do
-    if c > 0 then
-      active := active + 1
-  return active == 1
+def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
+  -- BUG: count active refs directly, without guaranteeing the primary table
+  activeCount refs == 1
 -- impl-end
 
 -- proof-start
@@ -83,28 +77,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp [activeCount, includePrimary]
+  | cons a as => simp [activeCount, includePrimary]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,17 +63,13 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
-  let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
-  let mut active := 0
-  for c in refs do
-    if c > 0 then
-      active := active + 1
-  return active == 1
+def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
+  -- partial-domain bug: wrong exactly on the empty (full-table delete) case
+  match refs with
+  | [] => false
+  | _  => activeCount (includePrimary refs) == 1
 -- impl-end
 
 -- proof-start
@@ -83,28 +79,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp [activeCount, includePrimary]
+  | cons a as => simp [activeCount, includePrimary]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,17 +63,11 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
-  let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
-  let mut active := 0
-  for c in refs do
-    if c > 0 then
-      active := active + 1
-  return active == 1
+def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
+  -- off-by-one bug: compares active count to 0 instead of 1
+  activeCount (includePrimary refs) == 0
 -- impl-end
 
 -- proof-start
@@ -83,28 +77,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp [activeCount, includePrimary]
+  | cons a as => simp [activeCount, includePrimary]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,16 +63,15 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
   let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
+  -- control-flow-effect bug: increments for EVERY entry (guard c > 0 dropped),
+  -- so it counts all references rather than only active ones.
   let mut active := 0
-  for c in refs do
-    if c > 0 then
-      active := active + 1
+  for _c in refs do
+    active := active + 1
   return active == 1
 -- impl-end
 
@@ -83,28 +82,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp_all [activeCount, includePrimary, Id.run]
+  | cons a as => simp_all [activeCount, includePrimary, Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,17 +63,11 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
-  let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
-  let mut active := 0
-  for c in refs do
-    if c > 0 then
-      active := active + 1
-  return active == 1
+def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
+  -- ungrounded oracle: ignores the input, always answers "single table"
+  true
 -- impl-end
 
 -- proof-start
@@ -83,28 +77,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp_all [activeCount, includePrimary, Id.run]
+  | cons a as => simp_all [activeCount, includePrimary, Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,17 +63,12 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
-  let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
-  let mut active := 0
-  for c in refs do
-    if c > 0 then
-      active := active + 1
-  return active == 1
+def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
+  -- wrong metric: total recorded references (list length) == 1, ignoring
+  -- whether each reference is active (positive count).
+  (includePrimary refs).length == 1
 -- impl-end
 
 -- proof-start
@@ -83,28 +78,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp [activeCount, includePrimary]
+  | cons a as => simp [activeCount, includePrimary]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,15 +63,15 @@
   result = (activeCount (includePrimary refs) == 1)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
-  -- Ensure the primary table is present among the recorded references before
-  -- counting (adds it / bumps the primary reference count).
   let refs := includePrimary refs
-  -- Count the active references (positive reference count) and decide "== 1".
+  -- boundary bug: treats a reference as active only when its count > 1,
+  -- so a single count-1 primary reference is NOT counted as active.
   let mut active := 0
   for c in refs do
-    if c > 0 then
+    if c > 1 then
       active := active + 1
   return active == 1
 -- impl-end
@@ -83,28 +83,7 @@
         (implementation_isSingleTableDelete refs) := by
   intro refs
   unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
-  have helper : ∀ (xs : List Nat) (init : Nat),
-      Id.run (forIn xs init (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r)))
-        = init + activeCount xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a > 0
-      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
-          List.length_cons]
-        omega
-      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
-          Bool.false_eq_true, if_false]
-  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
-        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
-        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
-      = (activeCount (includePrimary refs) == 1)
-  rw [helper]
-  simp
+  cases refs with
+  | nil => simp_all [activeCount, includePrimary, Id.run]
+  | cons a as => simp_all [activeCount, includePrimary, Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding, while compiling a row-deletion, whether the deletion targets exactly
ONE table — the condition under which the deletion can be issued as a single
direct statement rather than as a statement guarded by a self-referential
membership subquery.

A deletion carries a collection of recorded table references; each reference has
a non-negative reference count, and a reference is "active" when its count is
positive. The decision is "exactly one active table reference".

Before counting, the deletion's own PRIMARY table is guaranteed to be present
among the recorded references:

  * if no reference has been recorded yet, the primary table is added as a brand
    new reference with reference count one;
  * otherwise the first-recorded reference (the primary one) has its reference
    count increased by one.

The decision is then: after this guarantee, is the number of active references
exactly one?
-/

-- axioms-start
-- No unchanged outside callee is consumed as an `axiom`. The step that guarantees
-- the primary table is present among the recorded references (and adjusts the
-- relevant reference count) is modeled DEEPLY below as the pure helper
-- `includePrimary`; it is validated == the real repo callee by the conformance
-- gate (an A-reference, not a consumed axiom). Hence no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- Number of active references: those whose reference count is positive. -/
def activeCount (refs : List Nat) : Nat :=
  (refs.filter (fun c => c > 0)).length

/-- Guarantee the primary table is present among the recorded references and
adjust its reference count, exactly as the unchanged primary-table step does:

  * with no references recorded yet (`[]`), the primary table is added as a new
    reference with count one;
  * otherwise the first-recorded (primary) reference's count is increased by one.

This is a deep model of the unchanged primary-table step (validated == the real
callee by the conformance gate), NOT an axiom. -/
def includePrimary (refs : List Nat) : List Nat :=
  match refs with
  | []          => [1]
  | c :: rest   => (c + 1) :: rest
-- pure-end

-- post-conditions-start
/-- The decision is fully pinned to the input reference counts: it is `true`
exactly when, AFTER the primary table is guaranteed present (`includePrimary`),
the number of active references (positive reference count) is exactly one.

No output component is left free: the result is a single boolean and it is pinned
to the active-reference count of `includePrimary refs`. -/
def problem_spec_isSingleTableDelete (refs : List Nat) (result : Bool) : Prop :=
  result = (activeCount (includePrimary refs) == 1)
-- post-conditions-end

-- impl-start
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  -- Ensure the primary table is present among the recorded references before
  -- counting (adds it / bumps the primary reference count).
  let refs := includePrimary refs
  -- Count the active references (positive reference count) and decide "== 1".
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1
-- impl-end

-- proof-start
theorem correct_isSingleTableDelete :
    ∀ (refs : List Nat),
      problem_spec_isSingleTableDelete refs
        (implementation_isSingleTableDelete refs) := by
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  have helper : ∀ (xs : List Nat) (init : Nat),
      Id.run (forIn xs init (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r)))
        = init + activeCount xs := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a > 0
      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
          List.length_cons]
        omega
      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
          Bool.false_eq_true, if_false]
  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
      = (activeCount (includePrimary refs) == 1)
  rw [helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS. same_spec (swebench_unified.markers.same_spec via get_backend('lean')) = True for all 7 attacks and for the positive_control (byte-identical axioms/pure/pre/post; only the elided impl+proof regions differ).

Positive control: `bash scripts/lean_verify.sh positive_control.lean` -> exit 0. `#print axioms correct_isSingleTableDelete` -> [propext, Quot.sound] (clean; no sorryAx). So verify closes cleanly on gold.

7 DISTINCT same-spec wrong impls, each with a genuine best-effort proof (NO sorry — grep sorry = 0 in every file); command `bash scripts/lean_verify.sh atk_N.lean`:
  atk_1 (prepatch bug: activeCount refs == 1, omits includePrimary) -> EXIT 1 (residual goal: filter-length=1 ↔ ∀a∈as,a=0; unprovable at refs=[]).
  atk_2 (partial-domain: false on []) -> EXIT 1 (nil case reduces to `False`).
  atk_3 (boundary/off-by-one: == 0 instead of == 1) -> EXIT 1 (residual ∃x∈as,¬x=0).
  atk_4 (control-flow-effect: increments for EVERY entry, guard c>0 dropped) -> EXIT 1 (pure (1+as.length==1) = (...==0) unprovable).
  atk_5 (ungrounded-oracle echo: `fun _ => true`) -> EXIT 1 (obligation false e.g. refs=[1,1]).
  atk_6 (wrong metric: (includePrimary refs).length == 1) -> EXIT 1 (residual as=[] ↔ ∀a∈as,a=0).
  atk_7 (boundary: counts active only when c>1, so a count-1 primary is not active) -> EXIT 1 (forIn/filter mismatch unprovable).
All 7 exit code 1 = proof does NOT close (real error, not sorry(3), not timeout(124)).

MANDATORY RESOLVE STEP: vacuous, correctly — NOT for lack of capacity. The step requires materializing+run_resolve'ing the faithful patch of every wrong impl whose proof CLOSES with clean axioms. Zero wrong impls closed (all exit 1), so there is no closing-clean-axiom impl to materialize; `patches` is {} accordingly. run_resolve (swebench_unified.harness.run_resolve) was located and confirmed available but had nothing to run.

refinement.md audit: legs are Op1 includePrimary = A-REFERENCE (concrete `def` in pure region, unfolded by proof, no consumed property; documents the G-CONF binding to the UNCHANGED real callee get_initial_alias @ base_commit 437196da query.py:916; correspondence holds — empty⇒[1] matches join/table_alias(create=True) count-1, non-empty c::rest⇒(c+1)::rest matches ref_alias(base_table)+=1; G-CONF: 100000 inputs 0 disagreements). Op2 count-active = R. Op3 ==1 = I. NO A-consumed leg, NO kind-3 (nothing axiomatized; meta.json axioms=[]; axiom_check.py is skip stub). All legs R / A-reference / I; A-reference correspondence to the real callee holds.

VERDICT SOUND: >=5 (7) distinct same-spec attacks run, none breaks the spec (none closes), positive control verifies with clean axioms. The spec is a total output-pinning biconditional with concrete helpers ⇒ verify⇒correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The post-condition problem_spec_isSingleTableDelete refs result := result = (activeCount (includePrimary refs) == 1) is a TOTAL BICONDITIONAL over the sole input refs : List Nat, with activeCount and includePrimary both CONCRETE defs (not axioms/opaque) — so there is zero proof slack. Any implementation whose correct_ closes is extensionally forced to return exactly activeCount (includePrimary refs) == 1, which is precisely the resolving (gold) behavior. No closing-but-non-resolving impl exists, so no counterexample and no patch to materialize.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding, while compiling a row-deletion, whether the deletion targets exactly
ONE table — the condition under which the deletion can be issued as a single
direct statement rather than as a statement guarded by a self-referential
membership subquery.

A deletion carries a collection of recorded table references; each reference has
a non-negative reference count, and a reference is "active" when its count is
positive. The decision is "exactly one active table reference".

Before counting, the deletion's own PRIMARY table is guaranteed to be present
among the recorded references:

  * if no reference has been recorded yet, the primary table is added as a brand
    new reference with reference count one;
  * otherwise the first-recorded reference (the primary one) has its reference
    count increased by one.

The decision is then: after this guarantee, is the number of active references
exactly one?
-/

-- axioms-start
-- No unchanged outside callee is consumed as an `axiom`. The step that guarantees
-- the primary table is present among the recorded references (and adjusts the
-- relevant reference count) is modeled DEEPLY below as the pure helper
-- `includePrimary`; it is validated == the real repo callee by the conformance
-- gate (an A-reference, not a consumed axiom). Hence no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- Number of active references: those whose reference count is positive. -/
def activeCount (refs : List Nat) : Nat :=
  (refs.filter (fun c => c > 0)).length

/-- Guarantee the primary table is present among the recorded references and
adjust its reference count, exactly as the unchanged primary-table step does:

  * with no references recorded yet (`[]`), the primary table is added as a new
    reference with count one;
  * otherwise the first-recorded (primary) reference's count is increased by one.

This is a deep model of the unchanged primary-table step (validated == the real
callee by the conformance gate), NOT an axiom. -/
def includePrimary (refs : List Nat) : List Nat :=
  match refs with
  | []          => [1]
  | c :: rest   => (c + 1) :: rest
-- pure-end

-- post-conditions-start
/-- The decision is fully pinned to the input reference counts: it is `true`
exactly when, AFTER the primary table is guaranteed present (`includePrimary`),
the number of active references (positive reference count) is exactly one.

No output component is left free: the result is a single boolean and it is pinned
to the active-reference count of `includePrimary refs`. -/
def problem_spec_isSingleTableDelete (refs : List Nat) (result : Bool) : Prop :=
  result = (activeCount (includePrimary refs) == 1)
-- post-conditions-end

-- impl-start
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  -- Ensure the primary table is present among the recorded references before
  -- counting (adds it / bumps the primary reference count).
  let refs := includePrimary refs
  -- Count the active references (positive reference count) and decide "== 1".
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1
-- impl-end

-- proof-start
theorem correct_isSingleTableDelete :
    ∀ (refs : List Nat),
      problem_spec_isSingleTableDelete refs
        (implementation_isSingleTableDelete refs) := by
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  have helper : ∀ (xs : List Nat) (init : Nat),
      Id.run (forIn xs init (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r)))
        = init + activeCount xs := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a > 0
      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
          List.length_cons]
        omega
      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
          Bool.false_eq_true, if_false]
  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
      = (activeCount (includePrimary refs) == 1)
  rw [helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS. same_spec (swebench_unified.markers.same_spec via get_backend('lean')) = True for all 7 attacks and for the positive_control (byte-identical axioms/pure/pre/post; only the elided impl+proof regions differ).

Positive control: `bash scripts/lean_verify.sh positive_control.lean` -> exit 0. `#print axioms correct_isSingleTableDelete` -> [propext, Quot.sound] (clean; no sorryAx). So verify closes cleanly on gold.

7 DISTINCT same-spec wrong impls, each with a genuine best-effort proof (NO sorry — grep sorry = 0 in every file); command `bash scripts/lean_verify.sh atk_N.lean`:
  atk_1 (prepatch bug: activeCount refs == 1, omits includePrimary) -> EXIT 1 (residual goal: filter-length=1 ↔ ∀a∈as,a=0; unprovable at refs=[]).
  atk_2 (partial-domain: false on []) -> EXIT 1 (nil case reduces to `False`).
  atk_3 (boundary/off-by-one: == 0 instead of == 1) -> EXIT 1 (residual ∃x∈as,¬x=0).
  atk_4 (control-flow-effect: increments for EVERY entry, guard c>0 dropped) -> EXIT 1 (pure (1+as.length==1) = (...==0) unprovable).
  atk_5 (ungrounded-oracle echo: `fun _ => true`) -> EXIT 1 (obligation false e.g. refs=[1,1]).
  atk_6 (wrong metric: (includePrimary refs).length == 1) -> EXIT 1 (residual as=[] ↔ ∀a∈as,a=0).
  atk_7 (boundary: counts active only when c>1, so a count-1 primary is not active) -> EXIT 1 (forIn/filter mismatch unprovable).
All 7 exit code 1 = proof does NOT close (real error, not sorry(3), not timeout(124)).

MANDATORY RESOLVE STEP: vacuous, correctly — NOT for lack of capacity. The step requires materializing+run_resolve'ing the faithful patch of every wrong impl whose proof CLOSES with clean axioms. Zero wrong impls closed (all exit 1), so there is no closing-clean-axiom impl to materialize; `patches` is {} accordingly. run_resolve (swebench_unified.harness.run_resolve) was located and confirmed available but had nothing to run.

refinement.md audit: legs are Op1 includePrimary = A-REFERENCE (concrete `def` in pure region, unfolded by proof, no consumed property; documents the G-CONF binding to the UNCHANGED real callee get_initial_alias @ base_commit 437196da query.py:916; correspondence holds — empty⇒[1] matches join/table_alias(create=True) count-1, non-empty c::rest⇒(c+1)::rest matches ref_alias(base_table)+=1; G-CONF: 100000 inputs 0 disagreements). Op2 count-active = R. Op3 ==1 = I. NO A-consumed leg, NO kind-3 (nothing axiomatized; meta.json axioms=[]; axiom_check.py is skip stub). All legs R / A-reference / I; A-reference correspondence to the real callee holds.

VERDICT SOUND: >=5 (7) distinct same-spec attacks run, none breaks the spec (none closes), positive control verifies with clean axioms. The spec is a total output-pinning biconditional with concrete helpers ⇒ verify⇒correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-12965 lean bundle. NO diverging input found; spec is faithful to real repo behavior.

Evidence:
1. Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) => True. The discriminating clause lives in the shared spec (problem_spec_isSingleTableDelete = result == (activeCount (includePrimary refs) == 1)).
2. Lean genuine: scripts/lean_verify.sh exit 0; #print axioms correct_isSingleTableDelete => [propext, Quot.sound] (no sorryAx).
3. Model faithfulness verified against real source @ base_commit 437196da9a386bd4cc62b0ce3f2de4aba468613d:
   - get_initial_alias (query.py:916): non-empty alias_map => ref_alias(base_table) increments FIRST-recorded refcount by 1; empty => join()->table_alias(create=True) sets one fresh refcount=1. Matches includePrimary: [] -> [1]; c::rest -> (c+1)::rest.
   - single_alias (compiler.py:1408, patched) = sum(alias_refcount[t]>0 for t in alias_map)==1. Matches activeCount(...)==1.
4. Empirical differential test against REAL patched Django (git worktree at base_commit + gold patch applied, Django 3.2):
   - conformance_check.py (pinned seed 12965): 100,000 fuzzed inputs, 0 disagreements.
   - Additional exhaustive sweep: lengths 0..4 x counts 0..5 (1561 cases) + extreme cases ([100],[0]*10,[0]*10+[5],[1000000],[0]*7,range(0,20)): 0 disagreements.
   - Includes the discriminating refs=[] (full-table delete) case where oracle runs the REAL empty-branch get_initial_alias.

Model abstracts table names to counts (names only serve as dict keys, irrelevant to the boolean; insertion order preserved so the first-refcount bump is faithful) - this abstraction is sound and lossless w.r.t. the observable boolean. No input on which the modeled function disagrees with the real callee could be found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified against the actual solver-visible spec view (markers.spec_view over the frozen Solution.lean; same_spec(post,pre)=True and same_spec(post,post)=True, so the spec region is stable and the impl/proof regions are correctly elided to placeholders). Mechanical leakage.screen(lean) PASSES with zero hard failures.

Edit-localization check (spec view judged against public problem_statement ONLY, not hints_text): every patched/gold repo token is ABSENT from the spec view — get_initial_alias, single_alias, alias_refcount, alias_map, SQLDeleteCompiler, base_table, ref_alias, and the file path compiler.py. No diff markers, no reproduced gold-patch line (the gold add is `self.query.get_initial_alias()` plus a comment, none of which appears), and no narration terms (bug/fix/fixed/regression/patch/previously) in any spec-view comment or docstring.

Gold-reconstruction assessment: the docstring + includePrimary describe the DESIRED OBSERVABLE BEHAVIOR of the corrected function (before counting active references, guarantee the primary table is present: []=>[1], c::rest=>(c+1)::rest; then decide activeCount==1) in an abstract reference-count model (refs:List Nat, names dropped). This is the inherent content of any faithful spec of the fixed function, not disclosure of the concrete edit. It reveals neither the file/symbol/line touched nor the diff. Bridging the public SQL-performance requirement (Model.objects.all().delete() must emit a direct DELETE FROM t rather than a WHERE pk IN (SELECT ...) subquery — quoted verbatim in problem_statement) to the reference-count model, and identifying get_initial_alias() as the callee that registers the base table, remains the solver's work. The only repo-ish word present, 'subquery' (in 'membership subquery'), is taken verbatim from the public problem_statement. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
