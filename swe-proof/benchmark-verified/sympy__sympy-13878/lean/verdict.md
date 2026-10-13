# P2 adversarial audit — sympy__sympy-13878

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_01_prepatch.lean`, `atk_02_bare.lean`, `atk_03_strict_upper.lean`, `atk_04_reorder.lean`, `atk_05_drop_lower.lean`, `atk_06_mirror_profile.lean`, `atk_07_classical_ab.lean`, `atk_11_no_catchall.lean`, `atk_12_tail_two.lean`, `atk_13_lt_argorder.lean`, `atk_14_priv_wrongbranch_v2.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_08_oracle_echo.lean`, `atk_09_private_carrier.lean`, `atk_10_infeasible_guard.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation with a closing clean-axiom proof has a faithful refined patch that fails to resolve. The refutation of the whole attack class is machine-checked: uniq.lean (exit 0) proves `spec_unique : problem_spec_arcsinCdf a b x r -> r = goldImpl a b x`, i.e. the postcondition is UNIQUELY satisfiable at every carrier and every operand triple, plus the corollary `any_two_agree` that any two verifying impls are pointwise equal. Hence every impl whose proof closes denotes exactly the gold three-case list, and its faithful patch is the gold patch, which resolves.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -179,11 +179,7 @@
 -- impl-start
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+  return CdfObject.accumulateUpTo x
 -- impl-end
 
 -- proof-start
@@ -191,7 +187,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +235,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 2 — `atk_02_bare.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -179,11 +179,7 @@
 -- impl-start
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+  return CdfObject.bare (arcsinProfile a b x)
 -- impl-end
 
 -- proof-start
@@ -191,7 +187,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +235,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 3 — `atk_03_strict_upper.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -181,7 +181,7 @@
     CdfObject T := Id.run do
   let mut cs : List (Case T) := []
   cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
+  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.lt x b }]
   cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
 -- impl-end
@@ -191,7 +191,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +239,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 4 — `atk_04_reorder.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,9 +180,9 @@
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
   let mut cs : List (Case T) := []
+  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
+  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
   cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
 -- impl-end
 
@@ -191,7 +191,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +239,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 5 — `atk_05_drop_lower.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,7 +180,6 @@
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
   let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
   cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
   cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
@@ -191,7 +190,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +238,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 6 — `atk_06_mirror_profile.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -181,7 +181,9 @@
     CdfObject T := Id.run do
   let mut cs : List (Case T) := []
   cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
+  cs := cs ++ [{ value := Term.div (Term.mul (Term.lit 2)
+      (Term.arcsin (Term.sqrt (Term.div (Term.sub a x) (Term.sub a b))))) Term.pi,
+    guard := Term.le x b }]
   cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
 -- impl-end
@@ -191,7 +193,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +241,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 7 — `atk_07_classical_ab.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,13 +177,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
-    CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+noncomputable def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
+    CdfObject T :=
+  @ite _ (a = b) (Classical.propDecidable _)
+    (CdfObject.bare (Term.lit 0))
+    (CdfObject.caseSplit [{ value := Term.lit 0, guard := Term.lt x a },
+     { value := arcsinProfile a b x, guard := Term.le x b },
+     { value := Term.lit 1, guard := Term.always }])
 -- impl-end
 
 -- proof-start
@@ -191,7 +191,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +239,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 8 — `atk_08_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,21 +177,22 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
-    CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+noncomputable def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
+    CdfObject T :=
+  have h : ∃ r : CdfObject T, problem_spec_arcsinCdf a b x r :=
+    ⟨CdfObject.caseSplit [{ value := Term.lit 0, guard := Term.lt x a },
+       { value := arcsinProfile a b x, guard := Term.le x b },
+       { value := Term.lit 1, guard := Term.always }],
+      _, rfl, rfl, rfl, rfl, rfl⟩
+  h.choose
 -- impl-end
 
 -- proof-start
 theorem correct_arcsinCdf {T : Type} [Term T] : ∀ a b x : T,
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  unfold implementation_arcsinCdf
+  exact Exists.choose_spec _
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +233,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 9 — `atk_09_private_carrier.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,20 +177,39 @@
 -- post-conditions-end
 
 -- impl-start
+inductive Priv where
+  | lit (n : Nat) | sym (s : String) | pi
+  | div (p q : Priv) | mul (p q : Priv) | sub (p q : Priv)
+  | arcsin (e : Priv) | sqrt (e : Priv)
+  | lt (p q : Priv) | le (p q : Priv) | always
+  deriving DecidableEq
+
+instance : Term Priv where
+  lit := Priv.lit; sym := Priv.sym; pi := Priv.pi
+  div := Priv.div; mul := Priv.mul; sub := Priv.sub
+  arcsin := Priv.arcsin; sqrt := Priv.sqrt
+  lt := Priv.lt; le := Priv.le; always := Priv.always
+
+/-- `p - 0` vs `p`: FALSE in this private tree carrier, TRUE in sympy's
+evaluating layer. -/
+def privSubZeroIsId : Bool :=
+  decide (Term.sub (Term.sym "p" : Priv) (Term.lit 0) = (Term.sym "p" : Priv))
+
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+  if privSubZeroIsId then
+    return CdfObject.bare (Term.lit 0)
+  else
+    return CdfObject.caseSplit [{ value := Term.lit 0, guard := Term.lt x a },
+       { value := arcsinProfile a b x, guard := Term.le x b },
+       { value := Term.lit 1, guard := Term.always }]
 -- impl-end
 
 -- proof-start
 theorem correct_arcsinCdf {T : Type} [Term T] : ∀ a b x : T,
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
+  unfold problem_spec_arcsinCdf implementation_arcsinCdf privSubZeroIsId
   refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
@@ -232,10 +251,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 10 — `atk_10_infeasible_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,9 +180,12 @@
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
   let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
+  if (2 : Nat) < 1 then
+    cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
+  else
+    cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
+    cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
+    cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
 -- impl-end
 
@@ -232,10 +235,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 11 — `atk_11_no_catchall.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,7 +182,7 @@
   let mut cs : List (Case T) := []
   cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
   cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
+  cs := cs ++ [{ value := Term.lit 1, guard := Term.le x b }]
   return CdfObject.caseSplit cs
 -- impl-end
 
@@ -191,7 +191,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +239,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 12 — `atk_12_tail_two.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,7 +182,7 @@
   let mut cs : List (Case T) := []
   cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
   cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
+  cs := cs ++ [{ value := Term.lit 2, guard := Term.always }]
   return CdfObject.caseSplit cs
 -- impl-end
 
@@ -191,7 +191,14 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (refine ⟨_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
+    | decide
+    | (split <;> simp_all)
+    | (constructor <;> simp_all)
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +239,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 13 — `atk_13_lt_argorder.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -180,7 +180,7 @@
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
   let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
+  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt a x }]
   cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
   cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
@@ -191,7 +191,10 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | simp_all
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +235,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 14 — `atk_14_priv_wrongbranch_v2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,13 +177,21 @@
 -- post-conditions-end
 
 -- impl-start
+inductive Priv2 where
+  | leaf | node (p q : Priv2)
+  deriving DecidableEq
+
+/-- a closed private-carrier question that is settled TRUE -/
+def privTrue : Bool := decide ((Priv2.leaf : Priv2) = Priv2.leaf)
+
 def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
     CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+  if privTrue then
+    return CdfObject.bare (Term.lit 0)
+  else
+    return CdfObject.caseSplit [{ value := Term.lit 0, guard := Term.lt x a },
+       { value := arcsinProfile a b x, guard := Term.le x b },
+       { value := Term.lit 1, guard := Term.always }]
 -- impl-end
 
 -- proof-start
@@ -191,7 +199,13 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (simp only [privTrue, decide_eq_true_eq, if_true, if_pos]
+       refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (simp_all only []; refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | simp_all
+    | aesop
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +246,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 15 — `atk_15_subsingleton_v2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,13 +177,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
-    CdfObject T := Id.run do
-  let mut cs : List (Case T) := []
-  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
-  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
-  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
-  return CdfObject.caseSplit cs
+noncomputable def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
+    CdfObject T :=
+  @ite _ (Subsingleton T) (Classical.propDecidable _)
+    (CdfObject.accumulateUpTo x)
+    (CdfObject.caseSplit [{ value := Term.lit 0, guard := Term.lt x a },
+       { value := arcsinProfile a b x, guard := Term.le x b },
+       { value := Term.lit 1, guard := Term.always }])
 -- impl-end
 
 -- proof-start
@@ -191,7 +191,13 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (simp only [privTrue, decide_eq_true_eq, if_true, if_pos]
+       refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (simp_all only []; refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | simp_all
+    | aesop
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +238,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

Attack 16 — `atk_16_fourcases.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -183,6 +183,7 @@
   cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
   cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
   cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
+  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
   return CdfObject.caseSplit cs
 -- impl-end
 
@@ -191,7 +192,12 @@
     problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
   intro a b x
   unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
+  first
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | (refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> simp_all)
+    | (simp_all; refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl)
+    | simp_all
+    | decide
 
 /-- Non-vacuity witness. The signature is inhabited, and at three free operands
 of one carrier that inhabits it -- the operand kind on which the whole assembled
@@ -232,10 +238,4 @@
   le := TermTree.le
   always := TermTree.always
 
-example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-    (Term.sym "x")
-    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
-      (Term.sym "x")) := by
-  unfold problem_spec_arcsinCdf implementation_arcsinCdf
-  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), vanilla-Lean twin-artifact bundle sympy__sympy-13878. 16 same-spec attacks (same_spec=True verified for ALL 16 + positive control via swebench_unified.markers.same_spec). Focus per instructions on the A-legs; R/I legs left to G-CONF.

### COMMANDS (from repo root swe-proof):
  verify:   bash scripts/lean_verify.sh <ATK>.lean
  axioms:   same, on a copy with `#print axioms correct_arcsinCdf` appended
  resolve:  python resolve.py <tag> <patch>.diff  -> swebench_unified.harness.run_resolve('sympy__sympy-13878', patch, timeout=1800, retries=1)
Attack verifications were run concurrently, 4 background jobs at a time.

POSITIVE CONTROL pos_control.lean (byte copy of shipped Solution.lean): exit 0; `#print axioms correct_arcsinCdf` -> 'does not depend on any axioms'. Gold patch.diff through run_resolve: resolved=True, completed=True, F2P success=['test_arcsin'], P2P failures=0.

**PREPATCH REPRODUCED:** atk_01_prepatch.lean re-encodes Solution_prepatch.lean's `return CdfObject.accumulateUpTo x` -> exit 1 (spec rejects the pre-patch defect; G-DIFF signal intact).

### ATTACK RESULTS (exit 1 = proof does NOT close = spec rejects):
  01 prepatch / accumulateUpTo (kind clause)          exit 1
  02 bare collapse, no case analysis (kind clause)    exit 1
  03 boundary: upper cutoff le -> lt                  exit 1
  04 control-flow: three cases in reversed ORDER      exit 1
  05 partial-domain: below-support case dropped (2)   exit 1
  06 mirrored profile, endpoints exchanged            exit 1
  07 Classical branch on `a = b` (operand question)   exit 1
  11 partial-domain: no catch-all, tail guard = le    exit 1
  12 boundary: tail literal 1 -> 2                    exit 1
  13 guard arg order: Term.lt a x                     exit 1
  14 private-carrier guard selecting the WRONG branch exit 1  <-- see below
  15 Classical branch on Subsingleton T (carrier)     exit 1  <-- see below
  16 four cases (gold three + duplicated fall-through) exit 1
Three CLOSED with clean axioms and therefore required materialized patches + executed resolve:
  08 ungrounded-oracle echo (`h.choose`)  exit 0; axioms: [Classical.choice] (in STANDARD_AXIOMS => CLEAN)
  09 private-carrier decided guard        exit 0; axioms: 'does not depend on any axioms'
  10 infeasible-guard dead code           exit 0; axioms: 'does not depend on any axioms'

### EXECUTED RESOLVE RUNS (all completed=True, P2P failures=0 in every run):
  gold patch.diff                                        resolved=True
  atk_10 faithful patch (guard `if 2 < 1` KEPT with its dead branch)  resolved=True   [F2P success=test_arcsin]
  atk_09 faithful patch, mapping.md §2.1(b) branch-selection reading  resolved=True   [F2P success=test_arcsin]
  atk_08 faithful patch (= denoted gold list, see below)              resolved=True   [F2P success=test_arcsin]
  atk_09 ALTERNATIVE node-for-node reading (`if (p - S.Zero) == p`)   resolved=False  [F2P failure=test_arcsin] (2 attempts, consistent, not flaky)
  atk_08 ALTERNATIVE `return None` reading                            resolved=False  [F2P failure=test_arcsin] (2 attempts, consistent, not flaky)
The two non-resolving runs are recorded in full for transparency but are NOT breaks, because neither patch is the FAITHFUL refinement of its Lean impl. Adjudicated by machine proof, not by argument:

WHY NOT BROKEN — the uniqueness theorem. uniq.lean (exit 0) proves
  spec_unique : problem_spec_arcsinCdf a b x r -> r = goldImpl a b x
by destructing the length-3 list and the three getElem? equalities; plus any_two_agree (any two verifying impls are pointwise equal). The postcondition pins the KIND, the case COUNT, and all three (value, guard) positions, so it has exactly ONE solution at every carrier and every triple. Consequences:
  * atk_08: echo_eq.lean (exit 0) proves `echo_is_gold : oracleEcho a b x = goldImpl a b x`. So the oracle echo DENOTES the gold three-case list; `return None` was my unfaithful transliteration, and the faithful patch (submitted) resolves. The Classical.choice dependence buys the attacker nothing here.
  * atk_09: the Lean guard is settled FALSE, so the impl denotes the gold list. mapping.md §2.1(b)'s rule — the faithful reading of a private-carrier guard is the BRANCH IT SELECTS — yields the gold patch, which resolves. The node-for-node reading that fails is exactly the reading §2.1(b) forecloses in advance, and the bundle's safety claim for that rule is CONFIRMED by control atk_14: a private-carrier guard selecting the WRONG branch does NOT verify (genuine refutation, goal reduces to `False` under h : privTrue = true — not a tactic artifact; first-pass atk_14/atk_15 failed on a `decide` "Expected type must not contain free variables" artifact, so I re-ran both with clean proof scripts as `_v2`, which is what is submitted). So §2.1(b) cannot launder a wrong answer: a wrong branch is unreachable through it, and uniqueness is why.
  * atk_10: dead code under an infeasible guard survives transliteration WITH the guard; the guard is false in Python too, so the same branch runs and it resolves.

**REFINEMENT.MD LEG AUDIT:** 4 rows = 3x R + 1x A-reference, NO kind-3 and no untagged leg. No A-consumed rows, consistent with `grep -E '^\s*(axiom|opaque)' Solution.lean` finding no declaration (the single 'opaque' hit is prose in a docstring), so G-AX's `skip` is correct. The A-reference row (row 4, `CdfObject.caseSplit cs` <-> `Piecewise(*cs)`) checks out against the real callees at base_commit 7b127bdf71: `Piecewise.eval` is at piecewise.py:145 and the integrate-the-density fallback / `_cdf` returning None is at crv.py:196+/211+ as cited. Correspondence holds: the model pins the ARGUMENT list exactly and abstracts only the unchanged whole-container pass, whose effect depends on whether operands settle guards and never on which values/cutoffs were submitted. No sorry/admit, and no partial/implemented_by/unsafe/while/repeat/Lean.Loop/extern escape in Solution.lean.

DOC-HYGIENE NIT (non-blocking, no gate impact; independently re-confirmed — already recorded by G-PANEL-2): lean/axiom_check.py's docstring still describes the superseded 'Mathlib Real.arcsin / Real.sqrt / Real.pi' model that mapping.md §2 explicitly retracts. Its emitted status ('skip', no consumed callee axiom) is correct and agrees with refinement.md §3 and with my clean `#print axioms`, so only the prose is stale.

**VERDICT SOUND:** 16 attacks run (>= 5 required), all same-spec; every impl that closed with clean axioms had its faithful patch materialized and RUN through the official harness, and each resolved. verify => correct holds on this spec, and the reason is the machine-checked uniqueness of the postcondition.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_01_prepatch.lean`, `atk_02_bare.lean`, `atk_03_strict_upper.lean`, `atk_04_reorder.lean`, `atk_05_drop_lower.lean`, `atk_06_mirror_profile.lean`, `atk_07_classical_ab.lean`, `atk_11_no_catchall.lean`, `atk_12_tail_two.lean`, `atk_13_lt_argorder.lean`, `atk_14_priv_wrongbranch_v2.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_08_oracle_echo.lean`, `atk_09_private_carrier.lean`, `atk_10_infeasible_guard.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation with a closing clean-axiom proof has a faithful refined patch that fails to resolve. The refutation of the whole attack class is machine-checked: uniq.lean (exit 0) proves `spec_unique : problem_spec_arcsinCdf a b x r -> r = goldImpl a b x`, i.e. the postcondition is UNIQUELY satisfiable at every carrier and every operand triple, plus the corollary `any_two_agree` that any two verifying impls are pointwise equal. Hence every impl whose proof closes denotes exactly the gold three-case list, and its faithful patch is the gold patch, which resolves.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_02_bare.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_03_strict_upper.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_04_reorder.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_05_drop_lower.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_06_mirror_profile.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_07_classical_ab.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_08_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_09_private_carrier.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_infeasible_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_no_catchall.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_tail_two.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_lt_argorder.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_priv_wrongbranch_v2.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_subsingleton_v2.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_fourcases.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), vanilla-Lean twin-artifact bundle sympy__sympy-13878. 16 same-spec attacks (same_spec=True verified for ALL 16 + positive control via swebench_unified.markers.same_spec). Focus per instructions on the A-legs; R/I legs left to G-CONF.

### COMMANDS (from repo root swe-proof):
  verify:   bash scripts/lean_verify.sh <ATK>.lean
  axioms:   same, on a copy with `#print axioms correct_arcsinCdf` appended
  resolve:  python resolve.py <tag> <patch>.diff  -> swebench_unified.harness.run_resolve('sympy__sympy-13878', patch, timeout=1800, retries=1)
Attack verifications were run concurrently, 4 background jobs at a time.

POSITIVE CONTROL pos_control.lean (byte copy of shipped Solution.lean): exit 0; `#print axioms correct_arcsinCdf` -> 'does not depend on any axioms'. Gold patch.diff through run_resolve: resolved=True, completed=True, F2P success=['test_arcsin'], P2P failures=0.

**PREPATCH REPRODUCED:** atk_01_prepatch.lean re-encodes Solution_prepatch.lean's `return CdfObject.accumulateUpTo x` -> exit 1 (spec rejects the pre-patch defect; G-DIFF signal intact).

### ATTACK RESULTS (exit 1 = proof does NOT close = spec rejects):
  01 prepatch / accumulateUpTo (kind clause)          exit 1
  02 bare collapse, no case analysis (kind clause)    exit 1
  03 boundary: upper cutoff le -> lt                  exit 1
  04 control-flow: three cases in reversed ORDER      exit 1
  05 partial-domain: below-support case dropped (2)   exit 1
  06 mirrored profile, endpoints exchanged            exit 1
  07 Classical branch on `a = b` (operand question)   exit 1
  11 partial-domain: no catch-all, tail guard = le    exit 1
  12 boundary: tail literal 1 -> 2                    exit 1
  13 guard arg order: Term.lt a x                     exit 1
  14 private-carrier guard selecting the WRONG branch exit 1  <-- see below
  15 Classical branch on Subsingleton T (carrier)     exit 1  <-- see below
  16 four cases (gold three + duplicated fall-through) exit 1
Three CLOSED with clean axioms and therefore required materialized patches + executed resolve:
  08 ungrounded-oracle echo (`h.choose`)  exit 0; axioms: [Classical.choice] (in STANDARD_AXIOMS => CLEAN)
  09 private-carrier decided guard        exit 0; axioms: 'does not depend on any axioms'
  10 infeasible-guard dead code           exit 0; axioms: 'does not depend on any axioms'

### EXECUTED RESOLVE RUNS (all completed=True, P2P failures=0 in every run):
  gold patch.diff                                        resolved=True
  atk_10 faithful patch (guard `if 2 < 1` KEPT with its dead branch)  resolved=True   [F2P success=test_arcsin]
  atk_09 faithful patch, mapping.md §2.1(b) branch-selection reading  resolved=True   [F2P success=test_arcsin]
  atk_08 faithful patch (= denoted gold list, see below)              resolved=True   [F2P success=test_arcsin]
  atk_09 ALTERNATIVE node-for-node reading (`if (p - S.Zero) == p`)   resolved=False  [F2P failure=test_arcsin] (2 attempts, consistent, not flaky)
  atk_08 ALTERNATIVE `return None` reading                            resolved=False  [F2P failure=test_arcsin] (2 attempts, consistent, not flaky)
The two non-resolving runs are recorded in full for transparency but are NOT breaks, because neither patch is the FAITHFUL refinement of its Lean impl. Adjudicated by machine proof, not by argument:

WHY NOT BROKEN — the uniqueness theorem. uniq.lean (exit 0) proves
  spec_unique : problem_spec_arcsinCdf a b x r -> r = goldImpl a b x
by destructing the length-3 list and the three getElem? equalities; plus any_two_agree (any two verifying impls are pointwise equal). The postcondition pins the KIND, the case COUNT, and all three (value, guard) positions, so it has exactly ONE solution at every carrier and every triple. Consequences:
  * atk_08: echo_eq.lean (exit 0) proves `echo_is_gold : oracleEcho a b x = goldImpl a b x`. So the oracle echo DENOTES the gold three-case list; `return None` was my unfaithful transliteration, and the faithful patch (submitted) resolves. The Classical.choice dependence buys the attacker nothing here.
  * atk_09: the Lean guard is settled FALSE, so the impl denotes the gold list. mapping.md §2.1(b)'s rule — the faithful reading of a private-carrier guard is the BRANCH IT SELECTS — yields the gold patch, which resolves. The node-for-node reading that fails is exactly the reading §2.1(b) forecloses in advance, and the bundle's safety claim for that rule is CONFIRMED by control atk_14: a private-carrier guard selecting the WRONG branch does NOT verify (genuine refutation, goal reduces to `False` under h : privTrue = true — not a tactic artifact; first-pass atk_14/atk_15 failed on a `decide` "Expected type must not contain free variables" artifact, so I re-ran both with clean proof scripts as `_v2`, which is what is submitted). So §2.1(b) cannot launder a wrong answer: a wrong branch is unreachable through it, and uniqueness is why.
  * atk_10: dead code under an infeasible guard survives transliteration WITH the guard; the guard is false in Python too, so the same branch runs and it resolves.

**REFINEMENT.MD LEG AUDIT:** 4 rows = 3x R + 1x A-reference, NO kind-3 and no untagged leg. No A-consumed rows, consistent with `grep -E '^\s*(axiom|opaque)' Solution.lean` finding no declaration (the single 'opaque' hit is prose in a docstring), so G-AX's `skip` is correct. The A-reference row (row 4, `CdfObject.caseSplit cs` <-> `Piecewise(*cs)`) checks out against the real callees at base_commit 7b127bdf71: `Piecewise.eval` is at piecewise.py:145 and the integrate-the-density fallback / `_cdf` returning None is at crv.py:196+/211+ as cited. Correspondence holds: the model pins the ARGUMENT list exactly and abstracts only the unchanged whole-container pass, whose effect depends on whether operands settle guards and never on which values/cutoffs were submitted. No sorry/admit, and no partial/implemented_by/unsafe/while/repeat/Lean.Loop/extern escape in Solution.lean.

DOC-HYGIENE NIT (non-blocking, no gate impact; independently re-confirmed — already recorded by G-PANEL-2): lean/axiom_check.py's docstring still describes the superseded 'Mathlib Real.arcsin / Real.sqrt / Real.pi' model that mapping.md §2 explicitly retracts. Its emitted status ('skip', no consumed callee axiom) is correct and agrees with refinement.md §3 and with my clean `#print axioms`, so only the prose is stale.

**VERDICT SOUND:** 16 attacks run (>= 5 required), all same-spec; every impl that closed with clean axioms had its faithful patch materialized and RUN through the official harness, and each resolved. verify => correct holds on this spec, and the reason is the machine-checked uniqueness of the postcondition.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**Reference used:** sympy_sympy.git worktree at base_commit 7b127bdf71a36d85216315f80c1b54d22b060818 with patch.diff APPLIED (also the instance image swebench/sweb.eval.x86_64.sympy_1776_sympy-13878 at ce735e0d3 + patch, applied cleanly). patch.diff touches ONLY sympy/stats/crv_types.py (0 hits for piecewise), so piecewise.py -- the one A-reference callee -- is identical at base and post-patch, i.e. base_commit is correctly the reference for it.

**SPEC REGION INTEGRITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) == True; spec_signature sha256 prefix 6a33fa5ef8522e02. Spec view confirms the pinned obligation is the 5-clause problem_spec_arcsinCdf (kind=caseSplit, length=3, and positions 0/1/2 fixed to (lit 0, lt x a) / (arcsinProfile a b x, le x b) / (lit 1, always)).

**LEAN:** scripts/lean_verify.sh on Solution.lean + an appended `#print axioms correct_arcsinCdf` exits 0 and prints "'correct_arcsinCdf' does not depend on any axioms" -- no sorryAx, no declared axiom at all (consistent with refinement.md's no-A-consumed claim: every term-builder is a Term-signature operation, not an opaque callee).

**MODELLED FUNCTION vs REAL CALLEE.** The modelled function is ArcsinDistribution.`_cdf` (crv_types.py:157-163, added by the patch). Its body is UNCONDITIONAL -- no branch on a, b or x -- so the ordered case list it submits to Piecewise is input-invariant, which is exactly what the spec pins; the only input-dependent variation is Piecewise.eval's own whole-container pruning, which the model deliberately abstracts as CdfObject.caseSplit and carries via mapping.md §2's composition real `_cdf`(x) == Piecewise(*shadow_cases(a,b,x)).

I tested that composition MYSELF (independent script, my own seed 20260816, NOT mapping.md's pinned 13878):
- 16 hand-picked sharp cases: all free real; plain (assumption-free) x; a=0,b=1 with free x; ground x below/inside/above support; a=b free; a=b=0 (nan); reversed b<a; x aliased to a; x aliased to b; pi/radical operands; all-negative; I; oo. 0 mismatches.
- Broad fuzz: 41,491 triples over a 31-element pool mixing ground numbers (ints, negatives, Rationals, Float, pi, sqrt(2)), ASSUMPTION-CARRYING symbols (positive/negative/nonnegative/real/integer -- the ones that make guards decide at submission time so the submitted element is BooleanTrue/False rather than a relational node), assumption-free symbols, composite terms (`2*p`, p+1, -p, asin(1/2), sqrt(p), log(p), exp(n), Abs(r)), and oo/-oo/zoo/nan/I/1+I; plus a deterministic head that is the full 11x11x11 cross product over a sharp subset and every aliasing/degenerate pairing. Result: 0 mismatches. Shape coverage proves the comparison was not degenerate: 9,525 surviving three-case analyses, 8,562 pruned analyses, 9,454 bare collapses, 13,950 raising inputs (exception TYPE+MESSAGE matched identically, e.g. TypeError: Invalid comparison of complex I).
- Where a Piecewise survived I also compared guards PAIRWISE BY RELATION CLASS (type(cond)), not just printed form, so cutoff strictness is genuinely observed: on free operands the real args are ['StrictGreaterThan','GreaterThan','BooleanTrue'] -- the canonical flips of x<a and x<=b -- so the STRICT/NON-STRICT distinction the spec pins is preserved through `_canonical`.
- Complex-domain over-strength probe (1,331 triples over 7 complex/imaginary operands x 4 others): the model's Term.lt/le are total while sympy's relationals are partial, so this is where a too-strong spec would show. 0 divergences -- the composition raises exactly where the real method raises.
- Scored assertion of FAIL_TO_PASS test_arcsin reproduced directly: cdf equality against Piecewise((0,a>x),(`2*asin`(sqrt((-a+x)/(-a+b)))/pi,b>=x),(1,True)) holds.

**OVER-STRENGTH ANALYSIS.** The spec pins exactly the five things the real method's submitted list determines and nothing beyond: it does NOT claim which of Piecewise's output shapes is observed (that would be the over-strong version, and it would be false at a=0,b=1,x=0 where a bare 0 comes back, and at a=b=0 where nan does -- I checked both and the model is silent there by construction, not wrong). It does not constrain the operands' type, assumptions, or domain, matching the real method which sympifies nothing and only passes its operands on. arcsinProfile is spelled node-for-node against crv_types.py:162 (`2*asin`(sqrt((x-a)/(b-a)))/pi) with no reassociation. Positions, count, and both cutoffs' strictness all match the source line for line.

No diverging input found; I could not construct one. The spec describes the patched behavior and abstracts precisely the unchanged callee (Piecewise.eval) that the patch does not touch. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction on the COMPUTED spec view (markers.spec_view, LeanBackend) of sympy__sympy-13878/lean. Judged strictly against the SOLVER-VISIBLE problem_statement only (hints_text = 'I am working on it !', 20 chars, contributes nothing and is echoed nowhere). Every number below is my own measurement against the bytes as shipped (Solution.lean sha256 9385d44ae275...).

**RELAXATION STATUS:** none to inherit and none claimed. `find -iname '*RELAX*'` over benchmark-verified/sympy__sympy-13878/ -> empty; `'relaxed_leakage' in meta` = False; meta gates.G-LEAK.status = 'pass' (not 'relaxed'). So no unavoidability argument was owed and I applied the strict rule. I ran the strip-the-narration control anyway as an independent check (below).

**BUNDLE-ADDRESSES-REVIEWER CHECK:** leakage.reviewer_directed() over every file in the instance dir (lean/: Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, meta.json, verdict.md, properties.py, conformance_check.py, axiom_check.py; plus instance.json, patch.diff, and the ears/velvet/nagini siblings) -> ZERO hits, every file. A manual regex sweep for verdict-prescribing directives ('the honest/correct verdict|recording', 'submit NO-LEAKAGE', 'you must/should record', 'record this as') hits only nagini/verdict.md and nagini/meta.json, and in both cases the hit text is a PRIOR audit agent's own report that it searched for such directives and found none -- a record of a past measurement, not an instruction aimed at me. Nothing in the bundle tells me what to submit; I did not inherit any prior note (I re-ran everything and contradict part of the prior stamp record, see DRIFT).

### What I measured
1. Spec-region integrity: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True; spec_signature equal; the two COMPUTED spec views are byte-identical (both sha256 bff04adc3704...). So the spec was not tuned to the gold impl, and the prepatch variant leaks nothing the gold one doesn't.
2. Recomputed markers.region_hashes myself: axioms 6162a1d0, pure ab5a2fc0, post-conditions eaf15e8e, impl efb92510, proof 07929560, spec_view bff04adc -- EXACT match to gates.G-HYGIENE.data.region_hashes.
3. leakage.screen(Solution.lean, LeanBackend, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Identical for Solution_prepatch.lean. (Note the prepatch impl comment DOES carry 'PRE-PATCH (buggy)' narration -- but it sits inside the impl region, which the projection elides, so it is not in the spec view; I confirmed the elision.)
4. L1 by hand, beyond the harness: no gold-patch or test-patch changed line reproduced in the view, raw, whitespace-normalized, NFKD-unicode-folded, and under an aggressive fold that maps the view's prose math back onto sympy source (·->*, −->-, √->sqrt, π->pi, arcsin->asin, Term.div/mul/sub->/ * -, paren/bracket stripping). ZERO hits at threshold >=10 folded chars. Notably the view's prose profile '2 · arcsin(√((x − a)/(b − a))) / π' does NOT fold onto the gold line '`2*asin`(sqrt((x - a)/(b - a)))/pi' as a substring match, and the ORDER differs from the patch's spelling anyway.
5. **L2:** no patched file path ('sympy/stats/crv_types.py') and no dotted module path in the view. Grep for 'sympy', 'crv', 'stats', 'Piecewise', 'Distribution', '`_cdf`', '`_argnames`', 'self.', 'S.Zero', 'S.One', 'BooleanTrue', 'test_arcsin', '13878', 'commit' -> ALL ABSENT from the view. The view names no Python symbol, no test, no commit.
6. L2/L5 symbol collision, recomputed: `_patch_changed_symbols`(gold) = {Arcsin, ArcsinDistribution, ContinuousRV, Dagum, Erlang, Frechet, Gamma, GammaInverse, Gompertz, Kumaraswamy, Laplace, Logistic, Nakagami, Pareto, StudentT, UniformSum, sample}. The ONLY one reaching the view is 'Arcsin' (in problem_spec_arcsinCdf / Term.arcsin / arcsinProfile and in comments), and 'Arcsin' is verbatim public: the problem_statement contains `cdf(Arcsin("x", 0, 3))(1)` and 'The CDF is basically the arcsin function, for which the distribution is named'. Every OTHER distribution the gold patch touches (Dagum, Frechet, Kumaraswamy, Nakagami, StudentT, UniformSum, GammaInverse, Logistic, Laplace, Erlang) and every special function it newly imports (uppergamma, hyper, lowergamma) is ABSENT from the view -- the spec covers only the single F2P-scored arcsin behavior and reveals nothing about the rest of the multi-site edit.
7. L3 narration: 'buggy', 'fix', 'patch', 'pre-patch', 'repairs', 'defect', 'wrong', 'previously', 'regression' -> none in the spec view (the `_NARRATION_RE` scan is clean and my own greps agree).

DERIVABILITY OF WHAT THE SPEC DOES PIN (the substantive question). The view pins: caseSplit (not bare, not accumulateUpTo), exactly three cases, in order, with a STRICT lower cutoff `x < a`, a NON-STRICT upper cutoff `x <= b`, a catch-all, and the value `2*arcsin`(sqrt((x-a)/(b-a)))/pi. Each of these is derivable from the problem_statement plus the PUBLIC base_commit repo it explicitly points the solver at:
  - the inverse-sine profile: the statement says the CDF 'is basically the arcsin function, for which the distribution is named' and directs the solver to the linked docs' Wikipedia references 'where the formulas for CDF can be found'; the standard arcsine CDF is exactly 2/π·arcsin(√((x-a)/(b-a))). The endpoints a,b are the public ArcsinDistribution.`_argnames` at base_commit (unchanged by the patch), and the base pdf 1/(`pi*sqrt`((x-a)*(b-x))) is unchanged public code.
  - the three-case shape AND both cutoff strictnesses: the statement says 'we should have an internal `_cdf` method with a precomputed CDF, as is the case for Normal and Uniform presently'. I read UniformDistribution.`_cdf` at base_commit 7b127bdf71 (crv_types.py:2458) -- it is `Piecewise((S.Zero, x < left), ((x - left)/(right - left), x <= right), (S.One, True))`: the same three cases, same order, strict lower cutoff, non-strict upper cutoff, S.One fall-through. The statement names that method as the template, so the discriminating shape is available pre-patch from public material. So the spec pins the REQUIREMENT, derivable publicly, not the edit.

STRIP-THE-NARRATION CONTROL (load-bearing test, run even though no relaxation was claimed): I mechanically deleted every Lean comment (line and nested block), keeping only the structural region markers, from both variants. noprose_Solution.lean -> lean_verify EXIT 0; noprose_Solution_prepatch.lean -> EXIT 1, reproducing the real error ('Application type mismatch ... (pure (CdfObject.accumulateUpTo x)).run = CdfObject.caseSplit ?m.16'). So the entire discriminating content lives in the CODE of the post-conditions region, and the prose narration carries no load-bearing discriminator of its own -- i.e. there is nothing the prose alone contributes that a solver could not read off the formal spec, and nothing in it that is doing hidden edit-disclosure work.

CORE GATES RE-CONFIRMED LIVE (not read off stamps): G-VERIFY/G-GOLD -- scripts/lean_verify.sh Solution.lean EXIT 0, and I appended `#print axioms correct_arcsinCdf` to a copy: "'correct_arcsinCdf' does not depend on any axioms" -- no sorryAx, the proof is real. G-DIFF -- Solution_prepatch.lean EXIT 1 on a genuine type mismatch at the first conjunct, and my stripped noprose_pre reproduces it. G-HYGIENE -- region hashes recomputed, exact match. G-LEAK -- re-ran the screen myself, clean on both variants.

ADJACENT DRIFT (reported for the record; NOT a leak, does not change my verdict, outside my facet -- routing to the gates that own it): (a) meta.json's TOP-LEVEL `region_hashes` block is stale against the shipped artifact and against its own G-HYGIENE stamp -- it records spec_view bb1ae91e... and every region differing from what I computed, while gates.G-HYGIENE.data.region_hashes matches me exactly. (b) Four gate stamps -- G-AX, G-CONF, G-PANEL-2, G-PANEL-3 -- carry sources.Solution.lean = 748f424a98df..., while the shipped file is 9385d44ae275... and the other eleven gates are stamped against 9385d44a; those four predate the last repair, and since the stale top-level post-conditions hash differs from current, the older revision may not have been prose-only. My verdict does not lean on G-CONF or G-AX (no relaxation is claimed, so no unavoidability argument rests on them), but their freshness is worth a re-stamp.

**CONCLUSION:** the computed spec view reproduces no gold-patch or test-patch line (raw, normalized, unicode-folded, or aggressively folded), names no patched file or module path, echoes no patch-changed repo symbol that is not already verbatim public in the problem_statement, mentions none of the other sixteen distributions the multi-site gold edit touches, carries no diff marker and no fix/bug narration, and echoes nothing hints-only. Everything it pins -- the three-case split, both cutoff strictnesses, and the inverse-sine profile -- is derivable from the problem_statement plus the base_commit repo the statement explicitly points at (the Uniform.`_cdf` template it names, and Arcsin's unchanged public pdf/`_argnames`). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
