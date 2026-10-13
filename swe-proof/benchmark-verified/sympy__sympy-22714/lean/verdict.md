# P2 adversarial audit — sympy__sympy-22714

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_16.lean` |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample. 16 same-spec admissible attacks were built and run; 8 verify with clean #print axioms, and ALL 8 faithful refined patches RESOLVED under the official harness (run_resolve, completed=true) -- so no verifying impl has a non-resolving faithful patch. The spec `result = coords.any Coord.rejects` is an EXACT functional specification (an equality to a total pure function, not a loose relation), so any impl whose correct_imaginaryCheck closes is extensionally equal to `fun coords => coords.any Coord.rejects`; the only remaining attack surface is a divergence the Lean model cannot see. I did find one such genuine model imprecision, and then showed mechanically that it is NOT exploitable into a non-resolving patch. THE IMPRECISION (A-reference partiality, new -- not named by the prior pass): mapping.md bridges `im(a).is_zero` to a TOTAL `Option Bool` field `imagPartDetZero`, but the real observation is PARTIAL. Under `evaluate(False)`, `a = Sum(x,(x,1,10))` has `a.is_number == True` while `im(a).is_zero` RAISES `TypeError: cannot determine truth value of Relational` (probe6.py, verified in the instance image). That is a coordinate where `is_number` is true AND the determined-zero query is not a value at all, so no `Option Bool` models it -- the bridge is total where the callee is not, and this case is invisible to the prior pass's short-circuit story (which only covered `is_number == False` coords like `Basic()`). WHY IT IS STILL NOT A SPEC WEAKNESS, mechanically: to exploit it a rival must force the partial observation where gold's `and` short-circuit avoids it, and then the FORCED EXCEPTION MUST BREAK A GRADED TEST. It does not, for two independently measured reasons. (1) I instrumented the real guard in the image and logged all 1153 coordinate tuples that reach it across the full graded test file (out/profiles.txt, out/summary.txt): exactly ONE entry raises -- `(Basic(), Basic())` -- and it has `is_number == False` on BOTH coords; ZERO graded coordinates are both `is_number == True` and partial. So the `Sum` witness is real sympy behavior but is never a graded input. (2) On that one raising graded input the exception a forced `im(Basic())` throws is itself a `TypeError`, which is exactly what `test_arguments` asserts via `raises(TypeError, lambda: Point(Basic(), Basic()))` -- the forced effect satisfies the very assertion guarding that line. I materialized this vector FIVE independent ways and every one resolved: atk_8 (swapped conjuncts, drops the is_number short-circuit), atk_9 (both observation lists PRECOMPUTED then zipped -- fully non-short-circuiting), atk_13 (filter-then-all, evaluates is_zero on every coord first), atk_14 (three-valued decomposition querying is_zero TWICE per coord), and atk_16 (a vacuous `bool(im(a)) or not bool(im(a))` tautology that is a no-op in Lean but FORCES `im(a)` on every coordinate before the is_number guard). atk_16 is the sharpest: model-equal to gold by construction, yet its patch forces precisely the effect gold avoids -- and it still resolved (attempts=1, non-flaky). Rejection side is discriminating: 8 wrong impls were REJECTED by the verifier (exit 1), including the prepatch bug (atk_1, the form-level `imagPartTruthy` read), the undetermined-collapse `!= some true` (atk_4, wrongly rejects `is_zero is None`), the ungrounded-oracle echo dropping `isNumber` (atk_7), partial-domain `take 2` / `dropLast` (atk_2/atk_3), the control-flow-effect first-iteration `return false` (atk_5), an over-strong conjunction adding `imagPartTruthy` (atk_6), and a parity oracle (atk_15).
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
 -- impl-start
 def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
   for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
+    if c.isNumber && c.imagPartTruthy then
       return true
   return false
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  (coords.take 2).any Coord.rejects
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  coords.dropLast.any Coord.rejects
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
 -- impl-start
 def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
   for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
+    if c.isNumber && (c.imagPartDetZero != some true) then
       return true
   return false
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,6 +66,8 @@
   for c in coords do
     if c.isNumber && (c.imagPartDetZero == some false) then
       return true
+    else
+      return false
   return false
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
 -- impl-start
 def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
   for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
+    if c.isNumber && c.imagPartTruthy && (c.imagPartDetZero == some false) then
       return true
   return false
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  coords.any (fun c => c.imagPartDetZero == some false)
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  coords.any (fun c => (c.imagPartDetZero == some false) && c.isNumber)
 -- impl-end
 
 -- proof-start
@@ -76,14 +73,7 @@
         (implementation_imaginaryCheck coords) := by
   intro coords
   unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
-  induction coords with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
-    · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+  congr 1
+  funext c
+  exact Bool.and_comm _ _
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  ((coords.map (fun c => c.imagPartDetZero)).zip
+   (coords.map (fun c => c.isNumber))).any
+    (fun p => (p.1 == some false) && p.2)
 -- impl-end
 
 -- proof-start
@@ -79,11 +78,8 @@
   induction coords with
   | nil => rfl
   | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
-    · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+    rw [List.map_cons, List.map_cons, List.zip_cons_cons, List.any_cons,
+        List.any_cons, ih]
+    congr 1
+    exact Bool.and_comm _ _
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  coords.reverse.any Coord.rejects
 -- impl-end
 
 -- proof-start
@@ -75,15 +72,6 @@
       problem_spec_imaginaryCheck coords
         (implementation_imaginaryCheck coords) := by
   intro coords
-  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
-  induction coords with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
-    · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck
+  rw [List.any_reverse]
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  decide (0 < coords.countP Coord.rejects)
 -- impl-end
 
 -- proof-start
@@ -75,15 +72,15 @@
       problem_spec_imaginaryCheck coords
         (implementation_imaginaryCheck coords) := by
   intro coords
-  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
+  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck
   induction coords with
   | nil => rfl
   | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
+    rw [List.countP_cons, List.any_cons]
+    by_cases h : Coord.rejects a = true
+    · simp only [h, if_true, Bool.true_or]
+      simp only [decide_eq_true_eq]
+      omega
     · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+      simp only [h, Bool.false_eq_true, if_false, Bool.false_or, add_zero, ih]
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  !(coords.all (fun c => !(Coord.rejects c)))
 -- impl-end
 
 -- proof-start
@@ -75,15 +72,6 @@
       problem_spec_imaginaryCheck coords
         (implementation_imaginaryCheck coords) := by
   intro coords
-  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
-  induction coords with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
-    · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck
+  simp [List.all_eq_not_any_not]
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  !((coords.filter (fun c => c.imagPartDetZero == some false)).all
+      (fun c => !c.isNumber))
 -- impl-end
 
 -- proof-start
@@ -79,11 +77,11 @@
   induction coords with
   | nil => rfl
   | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
+    rw [List.any_cons, List.filter_cons]
+    by_cases h : (a.imagPartDetZero == some false) = true
+    · rw [if_pos h, List.all_cons, h, Bool.and_true]
+      simp only [Bool.not_and, Bool.not_not, ih]
     · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+      rw [if_neg (by simp [h]), h]
+      simp only [Bool.and_false, Bool.false_eq_true, Bool.false_or, ih]
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  coords.any (fun c =>
+    c.isNumber && (c.imagPartDetZero != none) && (c.imagPartDetZero != some true))
 -- impl-end
 
 -- proof-start
@@ -76,14 +74,12 @@
         (implementation_imaginaryCheck coords) := by
   intro coords
   unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
-  induction coords with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
-    · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+  congr 1
+  funext c
+  cases hd : c.imagPartDetZero with
+  | none => simp [hd]
+  | some b =>
+    cases b
+    · simp [hd, Bool.and_assoc]
+    · simp [hd]
 -- proof-end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,11 +62,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  decide (coords.countP Coord.rejects % 2 = 1)
 -- impl-end
 
 -- proof-start
```

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,11 +62,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
-  for c in coords do
-    if c.isNumber && (c.imagPartDetZero == some false) then
-      return true
-  return false
+def implementation_imaginaryCheck (coords : List Coord) : Bool :=
+  coords.any (fun c =>
+    (c.imagPartTruthy || !c.imagPartTruthy) &&
+      c.isNumber && (c.imagPartDetZero == some false))
 -- impl-end
 
 -- proof-start
@@ -76,14 +75,7 @@
         (implementation_imaginaryCheck coords) := by
   intro coords
   unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
-  induction coords with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.any_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
-    · simp only [h, if_true, Bool.true_or]; rfl
-    · simp only [Bool.not_eq_true] at h
-      rw [h]
-      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
+  congr 1
+  funext c
+  cases c.imagPartTruthy <;> simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a tuple of proposed coordinates must be rejected because one of
them is an *imaginary* (non-real) number.

A coordinate is rejected only when it is a concrete number whose imaginary part
is *determined to be mathematically non-zero*. Determination is three-valued:
the imaginary part may be determined to be zero, determined to be non-zero, or
left undetermined. A coordinate that is a free symbol (not a concrete number) is
never rejected on this ground, and neither is a concrete number whose imaginary
part is determined zero or merely undetermined — only a number whose imaginary
part is *definitely* non-zero makes the whole tuple ineligible.

The overall decision is the existential over all coordinates: the tuple is
rejected exactly when at least one coordinate meets that condition. A surface,
form-level reading of a coordinate's imaginary part is *not* the criterion; the
criterion is the determined mathematical value.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the decision is a direct
-- function of three per-coordinate observations carried by the input (whether
-- the coordinate is a concrete number, a form-level reading of its imaginary
-- part, and the three-valued determination of that imaginary part's vanishing),
-- all modeled explicitly below.
-- axioms-end

-- pure-start
/-- The observable state of one proposed coordinate, for the purpose of the
imaginary-coordinate decision.

* `isNumber` records whether the coordinate is a concrete number (as opposed to
  a free symbol or other non-numeric expression).
* `imagPartTruthy` records a *form-level* reading of the coordinate's imaginary
  part — whether that imaginary part reads as a non-trivial object on the
  surface, regardless of its mathematical value.
* `imagPartDetZero` records the three-valued *determination* of whether the
  imaginary part is mathematically zero: `some true` (determined zero),
  `some false` (determined non-zero), or `none` (not determined). -/
structure Coord where
  isNumber : Bool
  imagPartTruthy : Bool
  imagPartDetZero : Option Bool

/-- A single coordinate forces rejection exactly when it is a concrete number
whose imaginary part is *determined to be non-zero*. -/
def Coord.rejects (c : Coord) : Bool :=
  c.isNumber && (c.imagPartDetZero == some false)
-- pure-end

-- post-conditions-start
/-- The tuple of coordinates is rejected (`result = true`) exactly when at least
one coordinate is a concrete number whose imaginary part is determined to be
non-zero. The form-level reading of the imaginary part is irrelevant. -/
def problem_spec_imaginaryCheck (coords : List Coord) (result : Bool) : Prop :=
  result = coords.any Coord.rejects
-- post-conditions-end

-- impl-start
def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
  for c in coords do
    if c.isNumber && (c.imagPartDetZero == some false) then
      return true
  return false
-- impl-end

-- proof-start
theorem correct_imaginaryCheck :
    ∀ (coords : List Coord),
      problem_spec_imaginaryCheck coords
        (implementation_imaginaryCheck coords) := by
  intro coords
  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
  induction coords with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.any_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
    · simp only [h, if_true, Bool.true_or]; rfl
    · simp only [Bool.not_eq_true] at h
      rw [h]
      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** All 16 attacks + positive control were built by copying the frozen Solution.lean and editing ONLY the impl (and proof) region; ALL 17 confirmed byte-identical spec via swebench_unified.markers.same_spec == True AND admissible via variant_scope.unsound_evasions == [] (no dropped obligation, no new axiom, no sorry). Verifications were run CONCURRENTLY, <=4 background jobs at a time.

**EXACT COMMANDS.** Verify (from swe-proof): `bash scripts/lean_verify.sh atk_N.lean`. Axioms: appended `#print axioms correct_imaginaryCheck` to a `_ax.lean` copy and re-ran the same script. Resolve: `python3 resolve.py atk_N`, which calls `swebench_unified.harness.run_resolve('sympy__sympy-22714', <patch>, run_id='geqaudit672066-atk_N')`.

### RESULTS (file | verify exit | #print axioms | resolve).
REJECTED (8, verify exit 1 -- spec is discriminating): atk_1 prepatch form-level imagPartTruthy read (PREPATCH REPRODUCED); atk_2 `(coords.take 2).any` partial domain; atk_3 `coords.dropLast.any` partial domain; atk_4 `!= some true` collapses undetermined into reject; atk_5 first-iteration `return false` control-flow-effect; atk_6 over-strong `&& imagPartTruthy`; atk_7 ungrounded-oracle echo `any (imagPartDetZero == some false)` dropping isNumber; atk_15 parity `countP % 2 = 1`.

VERIFYING (8, verify exit 0, axioms clean = subset of {propext, Classical.choice, Quot.sound}, no sorryAx, and EVERY faithful patch RESOLVED, completed=true): atk_8  exit 0 | [Quot.sound] | resolved=True completed=True attempts=1 flaky=False atk_9  exit 0 | does not depend on any axioms | resolved=True completed=True attempts=1 flaky=False atk_10 exit 0 | [propext] | resolved=True completed=True attempts=1 flaky=False atk_11 exit 0 | [propext, Quot.sound] | resolved=True completed=True attempts=1 flaky=False atk_13 exit 0 | [propext] | resolved=True completed=True attempts=2 flaky=True (same: infra flake, then resolved) atk_14 exit 0 | [propext, Classical.choice, Quot.sound] | resolved=True completed=True attempts=1 flaky=False atk_16 exit 0 | [propext, Quot.sound] | resolved=True completed=True attempts=1 flaky=False No verifying attack has a non-resolving faithful patch => verify=>correct is NOT refuted.

POSITIVE CONTROL: pos_control.lean (the gold impl) verify exit 0, axioms [propext, Quot.sound] -- structurally distinct from the loop-free `List.any`/fold/filter attacks. Each of the 8 patches was ALSO pre-screened in the instance image against the patched test file (screen.sh): 13/13 tests pass for all 8, consistent with the harness verdicts.

REFINEMENT.MD AUDIT (leg kinds). Four legs, all R / A-reference / I; NO kind-3 leg, and meta.json agrees: `axioms: []`, `opaque_callees: []`, `conf_skip: false`, one `deep_model_references` entry. Legs: (1) `coords: List Coord` <- the sympified coords tuple, tagged R -- correct, a type refinement projecting rich SymPy exprs to three observations. (2) the `for`/early-return loop <- `any(...)`, tagged I -- correct, both are a short-circuiting existential and the Lean proof discharges the equality to `List.any`. (3) the per-element predicate `c.isNumber && (c.imagPartDetZero == some false)` <- `a.is_number and im(a).is_zero is False`, tagged A-reference (the EDITED op) -- this is the one leg carrying real modeling weight, and it is modeled DEEPLY rather than axiomatized, which is the correct call under §0.7. (4) `return false` fall-through <- no raise, tagged I -- correct. G-AX is a legitimate skip stub: with `axioms: []` there is no consumed callee axiom for it to validate, so the skip is an accurate absence-of-obligation, not an evaded check.

A-LEG CORRESPONDENCE TO THE REAL CALLEES (the part G-CONF cannot fully reach). I differentially re-derived the A-reference leg against the REAL sympy callees in the instance image (areflegs.py: 108 coordinate observations over 54 distinct expression shapes x both evaluate flags, plus 8000 random tuples, seed 20240627). Result: 1 divergence out of 108, and 1 of 8000 tuples -- the `Sum(x,(x,1,10))` under `evaluate(False)` partiality described in the counterexample field. Everything else corresponds exactly. I also confirmed the bridge's discriminating clause is not an is/== artifact: `im(a).is_zero` is ALWAYS a canonical `bool` or `None` (probe4.py over 20 shapes), so `is False` and `== False` never diverge and `some false` is a faithful encoding of `is_zero is False`. Sanity points in mapping.md all reproduce on real objects: `Integer(1)` -> is_number True, im 0, is_zero True (accept); same under evaluate(False) but im is the unevaluated truthy `im(1)` with is_zero still True (the bug: pre rejects, post accepts); `I` -> is_zero False (reject); `Symbol('x')` -> is_number False, is_zero None (accept).

HONEST RESIDUAL / WHAT A FUTURE PASS SHOULD KNOW. The model's totality assumption on `imagPartDetZero` is a REAL imprecision in the A-reference bridge, not merely a theoretical one -- `Sum(x,(x,1,10))` under `evaluate(False)` is a concrete sympy object where `is_number` is True and `im(a).is_zero` raises. It is unexploitable HERE only contingently: the graded tests never present such a coordinate (measured: 0 of 1153 guard entries), and the single raising graded input `(Basic(), Basic())` throws a TypeError that coincides with the TypeError `test_arguments` already asserts. That is a property of this instance's test set, not a guarantee from the spec.

A stricter model would type the determination as a three-valued-or-error observation, or state the postcondition only over coordinates where the query is defined. I am recording this as SOUND rather than BROKEN because the gate's criterion is a materialized faithful patch that does NOT resolve, and I could not produce one in five distinct attempts at exactly this vector -- every one resolved under the official oracle. No attack or resolve run failed to complete, so nothing here is INCONCLUSIVE; the two flaky=True runs both reached completed=true resolved=true on the harness's own retry.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_16.lean` |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample. 16 same-spec admissible attacks were built and run; 8 verify with clean #print axioms, and ALL 8 faithful refined patches RESOLVED under the official harness (run_resolve, completed=true) -- so no verifying impl has a non-resolving faithful patch. The spec `result = coords.any Coord.rejects` is an EXACT functional specification (an equality to a total pure function, not a loose relation), so any impl whose correct_imaginaryCheck closes is extensionally equal to `fun coords => coords.any Coord.rejects`; the only remaining attack surface is a divergence the Lean model cannot see. I did find one such genuine model imprecision, and then showed mechanically that it is NOT exploitable into a non-resolving patch. THE IMPRECISION (A-reference partiality, new -- not named by the prior pass): mapping.md bridges `im(a).is_zero` to a TOTAL `Option Bool` field `imagPartDetZero`, but the real observation is PARTIAL. Under `evaluate(False)`, `a = Sum(x,(x,1,10))` has `a.is_number == True` while `im(a).is_zero` RAISES `TypeError: cannot determine truth value of Relational` (probe6.py, verified in the instance image). That is a coordinate where `is_number` is true AND the determined-zero query is not a value at all, so no `Option Bool` models it -- the bridge is total where the callee is not, and this case is invisible to the prior pass's short-circuit story (which only covered `is_number == False` coords like `Basic()`). WHY IT IS STILL NOT A SPEC WEAKNESS, mechanically: to exploit it a rival must force the partial observation where gold's `and` short-circuit avoids it, and then the FORCED EXCEPTION MUST BREAK A GRADED TEST. It does not, for two independently measured reasons. (1) I instrumented the real guard in the image and logged all 1153 coordinate tuples that reach it across the full graded test file (out/profiles.txt, out/summary.txt): exactly ONE entry raises -- `(Basic(), Basic())` -- and it has `is_number == False` on BOTH coords; ZERO graded coordinates are both `is_number == True` and partial. So the `Sum` witness is real sympy behavior but is never a graded input. (2) On that one raising graded input the exception a forced `im(Basic())` throws is itself a `TypeError`, which is exactly what `test_arguments` asserts via `raises(TypeError, lambda: Point(Basic(), Basic()))` -- the forced effect satisfies the very assertion guarding that line. I materialized this vector FIVE independent ways and every one resolved: atk_8 (swapped conjuncts, drops the is_number short-circuit), atk_9 (both observation lists PRECOMPUTED then zipped -- fully non-short-circuiting), atk_13 (filter-then-all, evaluates is_zero on every coord first), atk_14 (three-valued decomposition querying is_zero TWICE per coord), and atk_16 (a vacuous `bool(im(a)) or not bool(im(a))` tautology that is a no-op in Lean but FORCES `im(a)` on every coordinate before the is_number guard). atk_16 is the sharpest: model-equal to gold by construction, yet its patch forces precisely the effect gold avoids -- and it still resolved (attempts=1, non-flaky). Rejection side is discriminating: 8 wrong impls were REJECTED by the verifier (exit 1), including the prepatch bug (atk_1, the form-level `imagPartTruthy` read), the undetermined-collapse `!= some true` (atk_4, wrongly rejects `is_zero is None`), the ungrounded-oracle echo dropping `isNumber` (atk_7), partial-domain `take 2` / `dropLast` (atk_2/atk_3), the control-flow-effect first-iteration `return false` (atk_5), an over-strong conjunction adding `imagPartTruthy` (atk_6), and a parity oracle (atk_15).
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a tuple of proposed coordinates must be rejected because one of
them is an *imaginary* (non-real) number.

A coordinate is rejected only when it is a concrete number whose imaginary part
is *determined to be mathematically non-zero*. Determination is three-valued:
the imaginary part may be determined to be zero, determined to be non-zero, or
left undetermined. A coordinate that is a free symbol (not a concrete number) is
never rejected on this ground, and neither is a concrete number whose imaginary
part is determined zero or merely undetermined — only a number whose imaginary
part is *definitely* non-zero makes the whole tuple ineligible.

The overall decision is the existential over all coordinates: the tuple is
rejected exactly when at least one coordinate meets that condition. A surface,
form-level reading of a coordinate's imaginary part is *not* the criterion; the
criterion is the determined mathematical value.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the decision is a direct
-- function of three per-coordinate observations carried by the input (whether
-- the coordinate is a concrete number, a form-level reading of its imaginary
-- part, and the three-valued determination of that imaginary part's vanishing),
-- all modeled explicitly below.
-- axioms-end

-- pure-start
/-- The observable state of one proposed coordinate, for the purpose of the
imaginary-coordinate decision.

* `isNumber` records whether the coordinate is a concrete number (as opposed to
  a free symbol or other non-numeric expression).
* `imagPartTruthy` records a *form-level* reading of the coordinate's imaginary
  part — whether that imaginary part reads as a non-trivial object on the
  surface, regardless of its mathematical value.
* `imagPartDetZero` records the three-valued *determination* of whether the
  imaginary part is mathematically zero: `some true` (determined zero),
  `some false` (determined non-zero), or `none` (not determined). -/
structure Coord where
  isNumber : Bool
  imagPartTruthy : Bool
  imagPartDetZero : Option Bool

/-- A single coordinate forces rejection exactly when it is a concrete number
whose imaginary part is *determined to be non-zero*. -/
def Coord.rejects (c : Coord) : Bool :=
  c.isNumber && (c.imagPartDetZero == some false)
-- pure-end

-- post-conditions-start
/-- The tuple of coordinates is rejected (`result = true`) exactly when at least
one coordinate is a concrete number whose imaginary part is determined to be
non-zero. The form-level reading of the imaginary part is irrelevant. -/
def problem_spec_imaginaryCheck (coords : List Coord) (result : Bool) : Prop :=
  result = coords.any Coord.rejects
-- post-conditions-end

-- impl-start
def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do
  for c in coords do
    if c.isNumber && (c.imagPartDetZero == some false) then
      return true
  return false
-- impl-end

-- proof-start
theorem correct_imaginaryCheck :
    ∀ (coords : List Coord),
      problem_spec_imaginaryCheck coords
        (implementation_imaginaryCheck coords) := by
  intro coords
  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
  induction coords with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.any_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
    · simp only [h, if_true, Bool.true_or]; rfl
    · simp only [Bool.not_eq_true] at h
      rw [h]
      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** All 16 attacks + positive control were built by copying the frozen Solution.lean and editing ONLY the impl (and proof) region; ALL 17 confirmed byte-identical spec via swebench_unified.markers.same_spec == True AND admissible via variant_scope.unsound_evasions == [] (no dropped obligation, no new axiom, no sorry). Verifications were run CONCURRENTLY, <=4 background jobs at a time.

**EXACT COMMANDS.** Verify (from swe-proof): `bash scripts/lean_verify.sh atk_N.lean`. Axioms: appended `#print axioms correct_imaginaryCheck` to a `_ax.lean` copy and re-ran the same script. Resolve: `python3 resolve.py atk_N`, which calls `swebench_unified.harness.run_resolve('sympy__sympy-22714', <patch>, run_id='geqaudit672066-atk_N')`.

### RESULTS (file | verify exit | #print axioms | resolve).
REJECTED (8, verify exit 1 -- spec is discriminating): atk_1 prepatch form-level imagPartTruthy read (PREPATCH REPRODUCED); atk_2 `(coords.take 2).any` partial domain; atk_3 `coords.dropLast.any` partial domain; atk_4 `!= some true` collapses undetermined into reject; atk_5 first-iteration `return false` control-flow-effect; atk_6 over-strong `&& imagPartTruthy`; atk_7 ungrounded-oracle echo `any (imagPartDetZero == some false)` dropping isNumber; atk_15 parity `countP % 2 = 1`.

VERIFYING (8, verify exit 0, axioms clean = subset of {propext, Classical.choice, Quot.sound}, no sorryAx, and EVERY faithful patch RESOLVED, completed=true): atk_8  exit 0 | [Quot.sound] | resolved=True completed=True attempts=1 flaky=False atk_9  exit 0 | does not depend on any axioms | resolved=True completed=True attempts=1 flaky=False atk_10 exit 0 | [propext] | resolved=True completed=True attempts=1 flaky=False atk_11 exit 0 | [propext, Quot.sound] | resolved=True completed=True attempts=1 flaky=False atk_13 exit 0 | [propext] | resolved=True completed=True attempts=2 flaky=True (same: infra flake, then resolved) atk_14 exit 0 | [propext, Classical.choice, Quot.sound] | resolved=True completed=True attempts=1 flaky=False atk_16 exit 0 | [propext, Quot.sound] | resolved=True completed=True attempts=1 flaky=False No verifying attack has a non-resolving faithful patch => verify=>correct is NOT refuted.

POSITIVE CONTROL: pos_control.lean (the gold impl) verify exit 0, axioms [propext, Quot.sound] -- structurally distinct from the loop-free `List.any`/fold/filter attacks. Each of the 8 patches was ALSO pre-screened in the instance image against the patched test file (screen.sh): 13/13 tests pass for all 8, consistent with the harness verdicts.

REFINEMENT.MD AUDIT (leg kinds). Four legs, all R / A-reference / I; NO kind-3 leg, and meta.json agrees: `axioms: []`, `opaque_callees: []`, `conf_skip: false`, one `deep_model_references` entry. Legs: (1) `coords: List Coord` <- the sympified coords tuple, tagged R -- correct, a type refinement projecting rich SymPy exprs to three observations. (2) the `for`/early-return loop <- `any(...)`, tagged I -- correct, both are a short-circuiting existential and the Lean proof discharges the equality to `List.any`. (3) the per-element predicate `c.isNumber && (c.imagPartDetZero == some false)` <- `a.is_number and im(a).is_zero is False`, tagged A-reference (the EDITED op) -- this is the one leg carrying real modeling weight, and it is modeled DEEPLY rather than axiomatized, which is the correct call under §0.7. (4) `return false` fall-through <- no raise, tagged I -- correct. G-AX is a legitimate skip stub: with `axioms: []` there is no consumed callee axiom for it to validate, so the skip is an accurate absence-of-obligation, not an evaded check.

A-LEG CORRESPONDENCE TO THE REAL CALLEES (the part G-CONF cannot fully reach). I differentially re-derived the A-reference leg against the REAL sympy callees in the instance image (areflegs.py: 108 coordinate observations over 54 distinct expression shapes x both evaluate flags, plus 8000 random tuples, seed 20240627). Result: 1 divergence out of 108, and 1 of 8000 tuples -- the `Sum(x,(x,1,10))` under `evaluate(False)` partiality described in the counterexample field. Everything else corresponds exactly. I also confirmed the bridge's discriminating clause is not an is/== artifact: `im(a).is_zero` is ALWAYS a canonical `bool` or `None` (probe4.py over 20 shapes), so `is False` and `== False` never diverge and `some false` is a faithful encoding of `is_zero is False`. Sanity points in mapping.md all reproduce on real objects: `Integer(1)` -> is_number True, im 0, is_zero True (accept); same under evaluate(False) but im is the unevaluated truthy `im(1)` with is_zero still True (the bug: pre rejects, post accepts); `I` -> is_zero False (reject); `Symbol('x')` -> is_number False, is_zero None (accept).

HONEST RESIDUAL / WHAT A FUTURE PASS SHOULD KNOW. The model's totality assumption on `imagPartDetZero` is a REAL imprecision in the A-reference bridge, not merely a theoretical one -- `Sum(x,(x,1,10))` under `evaluate(False)` is a concrete sympy object where `is_number` is True and `im(a).is_zero` raises. It is unexploitable HERE only contingently: the graded tests never present such a coordinate (measured: 0 of 1153 guard entries), and the single raising graded input `(Basic(), Basic())` throws a TypeError that coincides with the TypeError `test_arguments` already asserts. That is a property of this instance's test set, not a guarantee from the spec.

A stricter model would type the determination as a three-valued-or-error observation, or state the postcondition only over coordinates where the query is defined. I am recording this as SOUND rather than BROKEN because the gate's criterion is a materialized faithful patch that does NOT resolve, and I could not produce one in five distinct attempts at exactly this vector -- every one resolved under the official oracle. No attack or resolve run failed to complete, so nothing here is INCONCLUSIVE; the two flaky=True runs both reached completed=true resolved=true on the harness's own retry.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker (2) faithfulness-break for sympy__sympy-22714. Verdict FAITHFUL: no input found where problem_spec_imaginaryCheck disagrees with the real patched callee.

REFERENCE USED (per instructions): worktree at base_commit 3ff4717b6a with patch.diff APPLIED (verified: `git diff --name-only` = sympy/geometry/point.py + tests only; point.py:155 reads the POST-patch `any(a.is_number and im(a).is_zero is False for a in coords)`). Built a runnable env by supplying mpmath (the worktree lacked it) and confirmed test_issue_22684 passes: `with evaluate(False): Point(1,2)` -> Point2D(1,2), and `S('Point2D(Integer(1),Integer(2))')` -> Point2D(1,2). I did NOT compare against the base version, so no "divergence" on the patch delta itself is reported.

**SPEC REGION INTEGRITY:** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True. Region hashes confirm axioms/pure/post-conditions and spec_view are byte-identical across gold and prepatch (spec_view 208c25c8...); only impl and proof hashes differ. The prepatch differs solely in the impl predicate (imagPartTruthy) and carries `sorry`, as refinement.md documents.

**LEAN CHECKS:** gold Solution.lean builds via scripts/lean_verify.sh exit 0, and `#print axioms correct_imaginaryCheck` -> [propext, Quot.sound] — CLEAN, no sorryAx, so the proof is real not fake. I also authored and verified (exit 0) an independent discrimination file: (a) the prepatch impl provably VIOLATES the spec on Coord(true,true,some true) = Integer(1) under evaluate(False) — the exact reported bug; (b) the spec ACCEPTS that coordinate (matching the patched repo); (c) the spec REJECTS Coord(true,true,some false) = I, so it is not vacuous; (d) undetermined (none, e.g. zoo/nan) is accepted; (e) non-number (isNumber=false) is accepted even with imagPartDetZero=some false; (f) spec_functional: the spec pins exactly one result per input, so it is a total relation, not vacuously satisfiable.

DIFFERENTIAL EVIDENCE (real patched guard vs. the Lean spec on bridged observations, mapping.md bijection isNumber=bool(a.is_number), imagPartTruthy=bool(im(a)), imagPartDetZero=im(a).is_zero):
- Bundle conformance_check.py on the patched worktree: checked=121300, disagreements=0, status=pass.
- My OWN independent fuzz (seed 4242, wider atom pool incl. oo/-oo/zoo/nan/exp(I)/log(-1)/root(-8,3)/(-1)**(1/3)/Pow(I,2,evaluate=False)/Add(1,I,evaluate=False)/Mul(0,I,evaluate=False)/`2**I`/`I**I`/zeta/gamma/Piecewise/assumption-tagged symbols, both evaluate settings, tuples len 1-4): 84900 both-well-defined comparisons, 0 genuine disagreements.
- Randomly grown deep expression trees (seed 777, both evaluate settings): 2798 comparisons, 0 genuine disagreements.
- Hand probe table over 19 representative coordinates x both evaluate settings: real predicate == spec predicate on every one, including the three-valued edges (zoo/nan -> is_zero None -> accept under evaluate(True); zoo -> some false -> reject under evaluate(False); Symbol x -> isNumber false -> accept). The spec correctly ignores imagPartTruthy, which is the whole point of the fix.

### Attacks I ran that failed to break it
1. Over-strength on the three-valued edge: I tried to find a coordinate where is_zero is None or True yet the real guard rejects (or vice versa). None exists — `is_zero is False` is exactly an identity test against the singleton False, which the Option Bool `some false` models precisely. `nan` under evaluate(True) gives is_zero=None -> both accept.
2. Short-circuit asymmetry (the strongest candidate): Python's `any(...)` is lazy, so the real guard can return True without ever evaluating later coordinates, whereas building `List Coord` eagerly observes all three fields of every coordinate. I found coords=[I, Sum(x,(x,1,3))] under evaluate(False) where the real guard returns True but the eager bridge RAISES TypeError('cannot determine truth value of Relational'). This is NOT a spec-faithfulness defect: it is a bridge/domain-representability gap on an input outside the modeled domain (such a coordinate cannot be encoded as a Coord at all), and the spec makes no claim there. It is also not reachable as a wrong answer — end-to-end `Point(Sum(x,(x,1,3)),1)` under evaluate(False) raises the same TypeError in the patched repo itself, i.e. the real constructor also fails on that input, patch or no patch. mapping.md scopes the model to the any(...) boolean on sympified coords, and no input in the domain diverges.
3. Cache-order flake: an early sweep flagged Sum(x,(x,1,3)) under evaluate(False) as a divergence (real=RAISE vs spec=False). Re-ran in fresh processes: with the guard first, is_zero first, and end-to-end Point construction, ALL THREE raise TypeError. So the apparent divergence was sympy assumption-cache ordering within a long-lived process, not a spec disagreement — both legs are undefined on that input. I explicitly separated domain gaps from genuine disagreements in the final fuzzers (gaps counted, never scored as divergences), and genuine disagreements remained 0.
4. Vacuity / triviality: ruled out by the Lean theorems above (spec rejects I, accepts real-1, functional).

**CONCLUSION:** the spec is neither too strong nor drifted. `result = coords.any (fun c => c.isNumber && c.imagPartDetZero == some false)` is an exact model of the post-patch guard on the modeled domain, it discriminates the pre-patch behavior on the true FAIL_TO_PASS witness, and the carried proof is axiom-clean. No diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker 3 (leakage / gold-reconstruction), sympy__sympy-22714 (lean). STRICT lane, NO relaxation to adjudicate: `find -iname '*RELAX*'` over the whole instance dir returns nothing, and meta.json has no `relaxed_leakage` key (recursive key scan for /relax/i: zero hits); gates.G-LEAK.status = "pass", not "relaxed". So there is no RELAXED_LEAKAGE.md argument to re-derive -- I judged the spec view on its own against the public problem_statement, and every number below is my own measurement.

BUNDLE-ADDRESSES-THE-REVIEWER AXIS (reported as its own finding per my instructions): CLEAN. I ran leakage.reviewer_directed() over every non-binary file in the instance root and lean/: zero hits on all four rules (addresses-the-reviewer, prescribes-the-verdict x2, recording-convention). I also grepped refinement.md and mapping.md for auditor/reviewer/panel/attacker/verdict/NO-LEAKAGE/submit: zero matches. lean/verdict.md does contain a prior G-PANEL-3 record concluding NO-LEAKAGE (line 2532ff), but it is descriptive history of a past run, not an imperative aimed at me and not a directive about what to record; I did NOT inherit it -- my verdict rests only on the runs listed here.

**WHAT IS CONSUMER-VISIBLE.** Per docs/architecture.md:77-81 and markers.`_lean_spec_view`, the shipped surface is Solution.lean with the impl AND proof regions collapsed to placeholders -- module docstring and all comments included. I projected it myself: 70 lines, sha256 208c25c820ba68bc65141a4db4fff0ff034d3d3497b9dacab190979e4c54ee40, byte-matching meta.json region_hashes.spec_view. I recomputed all region hashes; axioms/pure/post-conditions/impl match meta exactly. mapping.md and refinement.md DO quote the gold patch verbatim (mapping.md:17-19, refinement.md:19-27), but they are not part of the spec-view projection -- they are construction/audit artifacts, not the consumer surface -- so they are out of scope for this gate.

**SPEC REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend().language) = True. The prepatch twin shares the frozen spec byte-for-byte and differs only in the impl predicate, so the prepatch file cannot be a side channel.

MECHANICAL SCREEN RE-RUN (my own invocation, not meta's record): leakage.screen(Solution.lean, tables, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]). Independently reproduces "spec view clean". Component-wise: (L1) neither changed gold line ('if any(a.is_number and im(a) for a in coords):' / '...im(a).is_zero is False...') appears normalized in the view, no diff markers; (L2) 'sympy/geometry/point.py' and the dotted module path absent; (L2/L5) `_patch_changed_symbols`(gold_patch) is EMPTY (the hunk edits a bare expression inside `__new__`, which is in `_COMMON_NONDISTINCTIVE`), so the symbol-collision rule is vacuous here and I did not lean on it; (L3) `_NARRATION_RE` finds nothing. I also hand-swept narration-evading synonyms the regex would miss -- wrongly/mistakenly/erroneously/crash/fail/should have/used to/instead of/rather than/no longer/now: ZERO present. Only 'surface' and 'truthy' appear, both as neutral descriptions of a modeled input field, never as a diagnosis. hints_text is the empty string, so there is no hints-echo risk at all.

**NO PYTHON-SIDE VOCABULARY IN THE VIEW.** The spec view names no callee (is_zero, im, is_number all absent), no path, no exception type, no error message, no Point2D/Point3D, and never mentions the `evaluate` flag or sympify/parse. It is fully abstract Lean over a 3-field record. The only Python-ish tokens are 'coords' and 'Tuple' (the latter only as Mathlib-adjacent prose); 'coords' is a generic coordinate-list name and localizes nothing beyond what the public traceback already shows.

THE LOAD-BEARING TEST (the decisive check). The discriminating content is the postcondition `result = coords.any Coord.rejects` with `Coord.rejects c = c.isNumber && (c.imagPartDetZero == some false)` -- i.e. reject only on a DETERMINED-non-zero imaginary part. Is that carried by the prose (removable narration) or by the formal spec (unavoidable)?

I stripped ALL prose -- module docstring reduced to one content-free line, every /-- -/ docstring deleted, every non-marker -- comment deleted -- and re-verified against the shared workspace: scripts/lean_verify.sh stripped_gold.lean            -> rc=0 (PASS) scripts/lean_verify.sh stripped_pre_goldproof.lean   -> rc=1 (FAIL: 'Tactic `rfl` failed' + unsolved goals at 45:44/46:4) The second file is the stripped gold with ONLY the impl predicate swapped to the pre-patch `c.isNumber && c.imagPartTruthy`, gold proof retained. It fails on a genuine elaboration error, not a sorry.

So with zero narration the spec still formally rejects the PRE-patch implementation: the discrimination lives in the postcondition where a correct spec must put it, and the prose is genuinely removable decoration rather than the thing doing the work. That is the opposite of a leak -- a spec that only discriminated via its comments would be the defect.

VERIFIER + AXIOM CLEANLINESS (gates my verdict leans on, re-measured): gold Solution.lean rc=0; `#print axioms correct_imaginaryCheck` -> [propext, Quot.sound]. No sorryAx, so the carried proof is real. Solution_prepatch.lean rc=3 (elaborates but uses sorry at 82:8) -- correct G-DIFF behavior, and I confirmed independently above that the spec rejects the prepatch predicate on a hard error when the gold proof is supplied instead of sorry. meta.json axioms == [] matches the empty axioms region.

IS THE DISCRIMINATOR DERIVABLE FROM problem_statement ALONE? Yes, and this is what makes the abstract framing legitimate rather than a hint. The public statement gives the exact failing guard -- 'Imaginary coordinates are not permitted.' raised at point.py line 153 in `__new__` -- plus the trigger (`with evaluate(False)`) and the fact that the same call succeeds with the flag on and with evaluate=False passed inline. A solver reading only that knows a genuinely real coordinate is being classified as imaginary when evaluation is deferred, which is precisely the behavioral fact the spec states. The spec view adds NO localization the statement lacks: it does not say which callee to consult, does not name is_zero, and does not give the tri-state test in Python terms. It states the desired BEHAVIOR (reject iff determined non-zero) which is the correct-by-construction content of any faithful spec of this guard.

THE ONE THING I PROBED HARDEST -- the inert third field. `Coord.imagPartTruthy` is declared in `pure` and documented, yet is used by NO formal spec obligation (I confirmed: it appears in the pure region's structure declaration but nowhere in post-conditions code). An unused field that exactly names the pre-patch observation is the strongest leakage candidate in this bundle, so I tested whether it is forced or gratuitous. It is FORCED, for two independent reasons.

(1) same_spec=True means gold and prepatch share one frozen spec region; the prepatch twin's impl reads imagPartTruthy, so the field MUST exist in the shared structure or the pre-fix twin cannot be typed at all.

(2) The field is not redundant: I probed real sympy 1.10.dev at base_commit 3ff4717b6a (worktree, mpmath borrowed onto PYTHONPATH), 13 objects x both evaluate settings = 26 observations, and asked whether bool(im(a)) is a function of (is_number, is_zero). It is NOT: (is_number=True, is_zero=True) yields bool(im)=False under evaluate-on (Integer(1), Float(1.5), sqrt(2), pi) and bool(im)=True under evaluate(False) (same objects) -- a genuine COLLISION, likewise for (False, True). So truthiness is unrecoverable from the determined-zero query and must be carried as its own observation for the model to represent the pre-patch behavior faithfully. Crucially, the field's presence tells a solver only that a surface reading EXISTS as an input; the spec view's postcondition then says that reading is NOT the criterion. Naming an input the spec declines to use is not the same as naming the edit -- and per the load-bearing test the spec discriminates with all of that prose deleted.

**OTHER GATES:** G-LEAK/G-HYGIENE/G-DIFF/G-GOLD/G-INTEGRITY/G-MUT (6/6 killed)/G-AX (documented skip, axioms==[] so vacuously consistent)/G-CONF (121300 checks, 0 disagreements) all recorded pass at Solution.lean sha 9b3a07dd..., which matches the file on disk; so no gate record describes a stale artifact. G-EQ and G-PANEL-1/2 also pass. Nothing my verdict leans on is unsound, and the four I actually lean on (spec-view projection + screen, region hashes, G-DIFF discrimination, verifier/axiom cleanliness) I reproduced from source myself.

**VERDICT:** NO-LEAKAGE. The spec view quotes no gold line, names no patched path/callee/symbol/message, carries no bug->fix narration or evasive synonym, and adds no edit-localization beyond a problem_statement that already publishes the exact failing guard and its trigger. Its discriminating content sits in the postcondition and survives total de-narration (rc=0 vs rc=1 on my stripped pair), and its one inert field is provably forced by the shared spec region plus a measured collision showing form-level truthiness is not recoverable from the three-valued determination.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
