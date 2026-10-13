# P2 adversarial audit — sympy__sympy-20438

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,13 +31,13 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
     (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+  let _ := factors
+  let _ := candidate
+  return none
 -- impl-end
 
 -- proof-start
@@ -45,30 +45,5 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,44 +31,16 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
-    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool :=
+  some ((productSet factors).all (fun x => candidate.contains x))
 -- impl-end
 
 -- proof-start
 theorem correct_isSubset : ∀ (factors : List (List Int)) (candidate : List (List Int)),
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
-  unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,13 +31,11 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
-    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool :=
+  some (((productSet factors).filter (fun x => !candidate.contains x)).isEmpty)
 -- impl-end
 
 -- proof-start
@@ -45,30 +43,12 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  congr 1
+  induction productSet factors with
+  | nil => rfl
+  | cons a as ih =>
+    simp only [List.filter_cons, List.all_cons]
+    by_cases h : candidate.contains a
+    · simp [h, ih]
+    · simp [h]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,13 +31,13 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
-    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool :=
+  match factors with
+  | [] => none
+  | _  => some ((productSet factors).all (fun x => candidate.contains x))
 -- impl-end
 
 -- proof-start
@@ -45,30 +45,7 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  cases factors with
+  | nil => simp
+  | cons a as => rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,13 +31,11 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
-    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool :=
+  some ((productSet factors).any (fun x => candidate.contains x))
 -- impl-end
 
 -- proof-start
@@ -45,30 +43,5 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,13 +31,13 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
     (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+  let _ := factors
+  let _ := candidate
+  return some true
 -- impl-end
 
 -- proof-start
@@ -45,30 +45,5 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  simp
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,13 +31,11 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
-    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool :=
+  some ((productSet factors).foldr (fun x acc => candidate.contains x && acc) true)
 -- impl-end
 
 -- proof-start
@@ -45,30 +43,8 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  congr 1
+  induction productSet factors with
+  | nil => rfl
+  | cons a as ih => simp only [List.foldr_cons, List.all_cons, ih]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,13 +31,11 @@
   result = some ((productSet factors).all (fun x => candidate.contains x))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_isSubset
-    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
-  let mut acc := true
-  for x in productSet factors do
-    acc := acc && candidate.contains x
-  return some acc
+    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool :=
+  some (candidate.all (fun x => (productSet factors).contains x))
 -- impl-end
 
 -- proof-start
@@ -45,30 +43,5 @@
     problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
   intro factors candidate
   unfold problem_spec_isSubset implementation_isSubset
-  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
-  have hfold : ∀ (xs : List (List Int)) (b : Bool),
-      Id.run (forIn xs b (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
-        = xs.foldl (fun r x => r && candidate.contains x) b := by
-    intro xs
-    induction xs with
-    | nil => intro b; rfl
-    | cons a as ih =>
-      intro b
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- the accumulating `&&`-fold equals `b && List.all`
-  have hall : ∀ (xs : List (List Int)) (b : Bool),
-      xs.foldl (fun r x => r && candidate.contains x) b
-        = (b && xs.all (fun x => candidate.contains x)) := by
-    intro xs
-    induction xs with
-    | nil => intro b; simp
-    | cons a as ih =>
-      intro b
-      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
-  -- `pure …` form (definitionally equal), then discharge with the helpers
-  show some (Id.run (forIn (productSet factors) true (fun x r =>
-        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
-  rw [hfold, hall, Bool.true_and]
+  simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed as an axiom: the enumeration of the product's
-- tuples and the membership test against the candidate collection are modeled
-- DEEPLY below (`productSet` / `List.contains`), so there is no `opaque` callee
-- and no consumed `_prop` axiom here. (A-reference rows, G-AX validated.)
-- axioms-end

-- pure-start
/-- Enumeration of all tuples of a finite product of finite integer collections.
The product is given by its list of factors; the result lists every tuple
obtained by choosing one element from each factor in order (the cartesian
product, front-recursive on the factor list). An empty factor list has the
single empty tuple. -/
def productSet : List (List Int) → List (List Int)
  | [] => [[]]
  | f :: fs => f.flatMap (fun a => (productSet fs).map (fun rest => a :: rest))
-- pure-end

-- post-conditions-start
/-- The subset test of a finite product of finite integer collections against a
finite collection of integer tuples. The verdict is *determined* (`some _`): it
is `some true` exactly when every tuple of the product is a member of the
candidate collection, and `some false` otherwise. (`none` would denote an
undetermined verdict, which the determined membership test never yields on this
finite collection domain.) -/
def problem_spec_isSubset
    (factors : List (List Int)) (candidate : List (List Int)) (result : Option Bool) : Prop :=
  result = some ((productSet factors).all (fun x => candidate.contains x))
-- post-conditions-end

-- impl-start
def implementation_isSubset
    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
  let mut acc := true
  for x in productSet factors do
    acc := acc && candidate.contains x
  return some acc
-- impl-end

-- proof-start
theorem correct_isSubset : ∀ (factors : List (List Int)) (candidate : List (List Int)),
    problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
  intro factors candidate
  unfold problem_spec_isSubset implementation_isSubset
  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
  have hfold : ∀ (xs : List (List Int)) (b : Bool),
      Id.run (forIn xs b (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
        = xs.foldl (fun r x => r && candidate.contains x) b := by
    intro xs
    induction xs with
    | nil => intro b; rfl
    | cons a as ih =>
      intro b
      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
  -- the accumulating `&&`-fold equals `b && List.all`
  have hall : ∀ (xs : List (List Int)) (b : Bool),
      xs.foldl (fun r x => r && candidate.contains x) b
        = (b && xs.all (fun x => candidate.contains x)) := by
    intro xs
    induction xs with
    | nil => intro b; simp
    | cons a as ih =>
      intro b
      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
  -- `pure …` form (definitionally equal), then discharge with the helpers
  show some (Id.run (forIn (productSet factors) true (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
  rw [hfold, hall, Bool.true_and]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for sympy__sympy-20438 (lean). Spec is an EXACT functional spec: problem_spec_isSubset pins result = some ((productSet factors).all (fun x => candidate.contains x)). same_spec=True verified for all 8 attacks + positive control. spec_view collapses BOTH impl and proof regions, so proofs were rewritten freely; imports/axioms/pure/post byte-identical.

### VERIFICATION RESULTS (scripts/lean_verify.sh, timeout 300):
- pos_control.lean: exit 0 (verifies); #print axioms => [propext, Quot.sound] (clean).
- atk_1 (prepatch bug: return none): exit 1 REJECTED => prepatch_reproduced=True (spec detects the missing-dispatch regression).
- atk_2 (echo: some ((productSet factors).all ...)): exit 0 CLOSES; #print axioms => 'does not depend on any axioms' (CLEAN).
- atk_3 (filter/isEmpty echo): exit 1 (my induction tactic left goals; not a spec breach — an equal impl I failed to prove).
- atk_4 (partial-domain: factors=[] -> none): exit 1 REJECTED (empty product => spec wants some true).
- atk_5 (boundary: uses List.any instead of all): exit 1 REJECTED.
- atk_6 (control-flow/ungrounded oracle echo: return some true): exit 1 REJECTED.
- atk_7 (echo: foldr && accumulation): exit 0 CLOSES; #print axioms => [propext] (CLEAN).
- atk_8 (reversed-subset: candidate.all in productSet): exit 1 REJECTED.

MANDATORY RESOLVE (protocol step 2) for every CLEAN-AXIOM closing impl (atk_2, atk_7): both compute exactly the gold behavior fuzzy_and(b_fs.contains(x) for x in a_ps). Faithful refined patch for both = gold patch (byte-identical). Executed run_resolve('sympy__sympy-20438', <gold patch>, timeout=1800): RESOLVED=True, COMPLETED=True; FAIL_TO_PASS {test_Eq, test_issue_19378} PASS; all 89 PASS_TO_PASS PASS. => No verified impl has a non-resolving faithful patch. verify => correct holds on all attacks.

refinement.md A-leg audit (against real repo at base_commit 33b47e4bd6): all legs R / A-reference / I, NO kind-3, NO consumed axioms (axioms region genuinely empty). Leg 3 (productSet <-> iterating ProductSet): confirmed ProductSet.__iter__ returns iproduct(*self.sets) (sympy/sets/sets.py:838-844) = cartesian product. Leg 4 (List.contains <-> FiniteSet.contains): confirmed FiniteSet._contains checks 'other in self._args_set' structural membership (sympy/sets/sets.py:1867) for concrete integer tuples. Correspondence holds.

VERDICT: SOUND. The spec is tight (exact value equality); genuinely-wrong impls (partial-domain, boundary any-vs-all, control-flow constant, reversed-subset) all fail to verify, and the only verifying same-spec impls are extensionally-equal echoes whose materialized faithful patch resolves under the official Docker harness. No verify=>correct violation found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed as an axiom: the enumeration of the product's
-- tuples and the membership test against the candidate collection are modeled
-- DEEPLY below (`productSet` / `List.contains`), so there is no `opaque` callee
-- and no consumed `_prop` axiom here. (A-reference rows, G-AX validated.)
-- axioms-end

-- pure-start
/-- Enumeration of all tuples of a finite product of finite integer collections.
The product is given by its list of factors; the result lists every tuple
obtained by choosing one element from each factor in order (the cartesian
product, front-recursive on the factor list). An empty factor list has the
single empty tuple. -/
def productSet : List (List Int) → List (List Int)
  | [] => [[]]
  | f :: fs => f.flatMap (fun a => (productSet fs).map (fun rest => a :: rest))
-- pure-end

-- post-conditions-start
/-- The subset test of a finite product of finite integer collections against a
finite collection of integer tuples. The verdict is *determined* (`some _`): it
is `some true` exactly when every tuple of the product is a member of the
candidate collection, and `some false` otherwise. (`none` would denote an
undetermined verdict, which the determined membership test never yields on this
finite collection domain.) -/
def problem_spec_isSubset
    (factors : List (List Int)) (candidate : List (List Int)) (result : Option Bool) : Prop :=
  result = some ((productSet factors).all (fun x => candidate.contains x))
-- post-conditions-end

-- impl-start
def implementation_isSubset
    (factors : List (List Int)) (candidate : List (List Int)) : Option Bool := Id.run do
  let mut acc := true
  for x in productSet factors do
    acc := acc && candidate.contains x
  return some acc
-- impl-end

-- proof-start
theorem correct_isSubset : ∀ (factors : List (List Int)) (candidate : List (List Int)),
    problem_spec_isSubset factors candidate (implementation_isSubset factors candidate) := by
  intro factors candidate
  unfold problem_spec_isSubset implementation_isSubset
  -- the `for` loop desugars to `forIn`; this folds it to a `List.foldl`
  have hfold : ∀ (xs : List (List Int)) (b : Bool),
      Id.run (forIn xs b (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))
        = xs.foldl (fun r x => r && candidate.contains x) b := by
    intro xs
    induction xs with
    | nil => intro b; rfl
    | cons a as ih =>
      intro b
      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
  -- the accumulating `&&`-fold equals `b && List.all`
  have hall : ∀ (xs : List (List Int)) (b : Bool),
      xs.foldl (fun r x => r && candidate.contains x) b
        = (b && xs.all (fun x => candidate.contains x)) := by
    intro xs
    induction xs with
    | nil => intro b; simp
    | cons a as ih =>
      intro b
      simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
  -- bridge the desugared loop body (`do pure PUnit.unit; pure …`) to the clean
  -- `pure …` form (definitionally equal), then discharge with the helpers
  show some (Id.run (forIn (productSet factors) true (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
  rw [hfold, hall, Bool.true_and]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for sympy__sympy-20438 (lean). Spec is an EXACT functional spec: problem_spec_isSubset pins result = some ((productSet factors).all (fun x => candidate.contains x)). same_spec=True verified for all 8 attacks + positive control. spec_view collapses BOTH impl and proof regions, so proofs were rewritten freely; imports/axioms/pure/post byte-identical.

### VERIFICATION RESULTS (scripts/lean_verify.sh, timeout 300):
- pos_control.lean: exit 0 (verifies); #print axioms => [propext, Quot.sound] (clean).
- atk_1 (prepatch bug: return none): exit 1 REJECTED => prepatch_reproduced=True (spec detects the missing-dispatch regression).
- atk_2 (echo: some ((productSet factors).all ...)): exit 0 CLOSES; #print axioms => 'does not depend on any axioms' (CLEAN).
- atk_3 (filter/isEmpty echo): exit 1 (my induction tactic left goals; not a spec breach — an equal impl I failed to prove).
- atk_4 (partial-domain: factors=[] -> none): exit 1 REJECTED (empty product => spec wants some true).
- atk_5 (boundary: uses List.any instead of all): exit 1 REJECTED.
- atk_6 (control-flow/ungrounded oracle echo: return some true): exit 1 REJECTED.
- atk_7 (echo: foldr && accumulation): exit 0 CLOSES; #print axioms => [propext] (CLEAN).
- atk_8 (reversed-subset: candidate.all in productSet): exit 1 REJECTED.

MANDATORY RESOLVE (protocol step 2) for every CLEAN-AXIOM closing impl (atk_2, atk_7): both compute exactly the gold behavior fuzzy_and(b_fs.contains(x) for x in a_ps). Faithful refined patch for both = gold patch (byte-identical). Executed run_resolve('sympy__sympy-20438', <gold patch>, timeout=1800): RESOLVED=True, COMPLETED=True; FAIL_TO_PASS {test_Eq, test_issue_19378} PASS; all 89 PASS_TO_PASS PASS. => No verified impl has a non-resolving faithful patch. verify => correct holds on all attacks.

refinement.md A-leg audit (against real repo at base_commit 33b47e4bd6): all legs R / A-reference / I, NO kind-3, NO consumed axioms (axioms region genuinely empty). Leg 3 (productSet <-> iterating ProductSet): confirmed ProductSet.__iter__ returns iproduct(*self.sets) (sympy/sets/sets.py:838-844) = cartesian product. Leg 4 (List.contains <-> FiniteSet.contains): confirmed FiniteSet._contains checks 'other in self._args_set' structural membership (sympy/sets/sets.py:1867) for concrete integer tuples. Correspondence holds.

VERDICT: SOUND. The spec is tight (exact value equality); genuinely-wrong impls (partial-domain, boundary any-vs-all, control-flow constant, reversed-subset) all fail to verify, and the only verifying same-spec impls are extensionally-equal echoes whose materialized faithful patch resolves under the official Docker harness. No verify=>correct violation found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of sympy__sympy-20438 lean bundle.

Modeled function: post-patch dispatch `is_subset_sets(a_ps: ProductSet, b_fs: FiniteSet) -> fuzzy_and(b_fs.contains(x) for x in a_ps)` (sympy/sets/handlers/issubset.py:136-139). Spec: `problem_spec_isSubset factors candidate result := result = some ((productSet factors).all (fun x => candidate.contains x))`. Domain: concrete integer ProductSet/FiniteSet, modeled as List(List Int) factors + List(List Int) candidate.

### Verification performed
1. Lean compiles clean via scripts/lean_verify.sh (exit 0).
2. `#print axioms correct_isSubset` => [propext, Quot.sound] — NO sorryAx, proof is real.
3. same_spec(Solution, Solution_prepatch) with LeanBackend.language tables => True (spec region byte-identical between patch/prepatch).
4. Differential test vs REAL repo at base_commit 33b47e4bd6 + gold patch.diff applied (worktree, sympy 1.8.dev). ~24,000 fuzzed concrete-integer inputs (1-4 factors, sizes 1-5, dup elements, strays, wrong-arity strays, big ints, empty candidate): via public API `ProductSet.is_subset(FiniteSet)` => 0 mismatches, 0 None results. Spec is neither too strong nor drifts.
5. Bundle conformance_check.py => G-CONF OK: 120005 configs, 0 disagreements.
6. Curated adversarial edge cases (duplicate factor elems, empty candidate=>some false, 1-factor 1-tuples, 10^9 ints, 3-factor) all agree.

KEY SUBTLETY EXAMINED: calling the raw dispatch `is_subset_sets(ps, FiniteSet())` directly returns Python None because FiniteSet() is EmptySet (not a FiniteSet instance) so multipledispatch routes elsewhere. This is NOT the observable repo behavior: the modeled function body `fuzzy_and(...)` yields False, and the public `ProductSet.is_subset(EmptySet)` returns False, matching the spec's `some false`. The spec's claim that the verdict is always determined (`some _`, never `none`) on the concrete finite-integer domain holds — no concrete-integer input produces a fuzzy None. So no genuine divergence.

The 1-factor ProductSet iterates as 1-tuples ((1,),(2,)), matching productSet's List(List Int) representation. Empty factor => EmptySet product => vacuously subset (some true), matched by spec (productSet with an empty factor list-of-that-factor yields []). Spec is a faithful, exact model of the real callee over the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view exposes only the pure helper `productSet` and the abstract behavioral postcondition `result = some ((productSet factors).all (fun x => candidate.contains x))` (impl+proof elided). This states the CORRECT input->output relation, which is exactly what a faithful spec must do and is already derivable from the public problem_statement: the bug report shows b=ProductSet(a,a) vs c=FiniteSet of b's tuples, and that c.is_subset(b) is True while b.is_subset(c) is undetermined — so 'every tuple of the product is a member of the candidate collection' is publicly inferable. No gold-edit specifics leak beyond the problem_statement: the patched symbol `is_subset_sets` does not appear; `fuzzy_and`, `@dispatch`, and `b_fs.contains` do not appear; no patched file/module paths (issubset.py, relational.py, comparison.py) appear; ride-along edits (isinstance(...,Expr) guards, stale handler removal) are absent. Mechanical leakage.screen passes with zero hard failures (checked: diff markers, reproduced gold lines, file/module paths, and all four distinctive patched symbols binary_symbols/equals/eval_is_eq/is_subset_sets — none embedded in spec-view idents or comments). same_spec(post,prepatch)=True, so the spec region is byte-identical and not tuned to the fix. The some/none (determined vs undetermined) framing merely mirrors the publicly-shown empty return of b.is_subset(c). Verified against lean spec_view projection and screen() using the frozen dataset row.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
