# P2 adversarial audit — sympy__sympy-18199

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The prior pass's counterexample (guard escaping p=2, exploiting the older `require p > 2`) is CLOSED by the current `require p >= 2`. I re-encoded it BOTH ways -- atk_1 (guard `p = 2` -> []) and atk_2 (guard `p <= 2` -> []) -- and both are REJECTED (exit=1, clean `unsolved goals`, no PANIC). Tactic-independent confirmation: (1,3,2) is a REAL graded call (I measured it: it is the depth-1 re-entry sub-input of the enumerated triple (1,3,8), reached from solveset.py:1205 via residue_ntheory.py:758), it is in-domain under `p >= 2 & isPrime 2`, and the spec pins its output to [1] while the attacks return [] -- a genuine divergence, so the rejection is real spec tightness. Both verifying attacks (atk_10, atk_11) are precondition-infeasible off-domain guards whose faithful patches RESOLVED under the official harness.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if p = 2 then
+        ([] : List Int)
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if p = 2 then ([] : List Int) else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : p = 2
+    · rw [if_pos hcond] at hk ⊢
+      simp at hk
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if p ≤ 2 then
+        ([] : List Int)
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if p ≤ 2 then ([] : List Int) else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : p ≤ 2
+    · rw [if_pos hcond] at hk ⊢
+      simp at hk
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,6 +154,9 @@
   do
     -- impl-start
     let target : List Int :=
+      if a % p = 0 then
+        [(0 : Int)]
+      else
       if ¬ isPrime p then
         rootsBelow p.toNat a n p
       else
@@ -232,13 +235,17 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if a % p = 0 then [(0:Int)] else (if ¬isPrime p then rootsBelow p.toNat a n p
+      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : a % p = 0
+    · rw [if_pos hcond] at hk ⊢
+      exact zero_singleton_sound a n p k require_2 require_3 hcond hk
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -155,7 +155,7 @@
     -- impl-start
     let target : List Int :=
       if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+        rootsBelow (p.toNat - 1) a n p
       else
         if a % p = 0 then
           [(0 : Int)]
@@ -232,7 +232,7 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
+    generalize hT : (if ¬isPrime p then rootsBelow (p.toNat - 1) a n p
       else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,10 +166,10 @@
             primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ target.length
       invariant result = target.drop i
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let c := target[i - 1]!
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if a = 1 ∧ n = 3 ∧ p = 8 then
+        [(1 : Int)]
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if (a = 1 ∧ n = 3 ∧ p = 8) then [(1 : Int)] else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : (a = 1 ∧ n = 3 ∧ p = 8)
+    · rw [if_pos hcond] at hk ⊢
+      simp_all [isRoot]
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,7 +161,7 @@
           [(0 : Int)]
         else
           if ¬ isNthResidue a n p then
-            ([] : List Int)
+            rootsBelow p.toNat a n p
           else
             primeRoots a n p
     let mut result : List Int := []
@@ -233,7 +233,7 @@
   loom_solve
   · -- invariant re-establishment for the backward copy loop
     generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+      else if a % p = 0 then [0] else if ¬isNthResidue a n p then rootsBelow p.toNat a n p else primeRoots a n p) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
```

Attack 8 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if n ≤ 2 then
+        [(-7 : Int)]
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if n ≤ 2 then [(-7 : Int)] else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : n ≤ 2
+    · rw [if_pos hcond] at hk ⊢
+      exfalso; omega
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 9 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if ¬ isPrime p ∧ ¬ compositeValidated a n p then
+        rootsBelow (p.toNat / 2) a n p
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if (¬ isPrime p ∧ ¬ compositeValidated a n p) then rootsBelow (p.toNat / 2) a n p else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : (¬ isPrime p ∧ ¬ compositeValidated a n p)
+    · rw [if_pos hcond] at hk ⊢
+      exact absurd require_1 (by tauto)
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 10 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if isPrime p ∧ a % p = 0 then
+        ([] : List Int)
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if isPrime p ∧ a % p = 0 then ([] : List Int) else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : isPrime p ∧ a % p = 0
+    · rw [if_pos hcond] at hk ⊢
+      simp at hk
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,16 +154,19 @@
   do
     -- impl-start
     let target : List Int :=
-      if ¬ isPrime p then
-        rootsBelow p.toNat a n p
+      if ¬ isPrime p ∧ a % p = 0 then
+        [(0 : Int)]
       else
-        if a % p = 0 then
-          [(0 : Int)]
+        if ¬ isPrime p then
+          rootsBelow p.toNat a n p
         else
-          if ¬ isNthResidue a n p then
-            ([] : List Int)
+          if a % p = 0 then
+            [(0 : Int)]
           else
-            primeRoots a n p
+            if ¬ isNthResidue a n p then
+              ([] : List Int)
+            else
+              primeRoots a n p
     let mut result : List Int := []
     let mut i := target.length
     while i > 0
@@ -232,13 +235,16 @@
 prove_correct nthRoots by
   loom_solve
   · -- invariant re-establishment for the backward copy loop
-    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
-      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
+    generalize hT : (if ¬ isPrime p ∧ a % p = 0 then [(0 : Int)] else (if ¬isPrime p then rootsBelow p.toNat a n p else if a % p = 0 then [(0:Int)] else if ¬isNthResidue a n p then ([]:List Int) else primeRoots a n p)) = T at *
     rw [drop_step T i (by omega) (by omega), invariant_2]
   · -- final soundness: every returned element is an in-range root
     injection i_2 with hi hr
     intro k hk
     rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
+    by_cases hcond : ¬ isPrime p ∧ a % p = 0
+    · rw [if_pos hcond] at hk ⊢
+      exact zero_singleton_sound a n p k require_2 require_3 hcond.2 hk
+    rw [if_neg hcond] at hk ⊢
     by_cases hpr : isPrime p
     · simp only [hpr, not_true, if_false] at hk ⊢
       by_cases hz : a % p = 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 11 same-spec attacks (same_spec=True vs the frozen Solution.lean for every one), positive control, 2 prepatch controls, 2 official harness resolve runs. Verifications launched 4-way concurrent as detached background jobs via vrun.sh; resolve runs via rrun.sh.

CONTROLS -- `bash scripts/lean_verify.sh <D>/<f>.lean` from the repo root:
- pos_control.lean (byte copy of Solution.lean): exit=0 VERIFIES (non-vacuity).
- prepatch.lean (Solution_prepatch.lean, old zero-target dispatch order): exit=1 REJECTED.
- prepatch_1.lean (Solution_prepatch_1.lean, composite modulus declined -> []): exit=1 REJECTED.
=> prepatch_reproduced=true; both G-DIFF discriminators bite.

GROUP 1 -- REJECTED (9), all exit=1 with clean `unsolved goals` on real postcondition clauses, PANIC=0 in every log:
- atk_1  guard `p = 2` -> []                                  : exit=1 (prior counterexample input exactly)
- atk_2  guard `p <= 2` -> []                                 : exit=1 (prior counterexample guard shape)
- atk_3  zero-target check HOISTED ahead of the composite branch: exit=1 (control-flow/dispatch inversion)
- atk_4  partial-domain: composite fold bound `p.toNat - 1`    : exit=1
- atk_6  control-flow effect: copy loop `while i > 1` + `done_with i <= 1` (drops the first element; termination measure untouched): exit=1
- atk_7  answer-key echo: (1,3,8) hardcoded to [1]             : exit=1 (directive-8 probe)
- atk_8  ungrounded-oracle echo: non-residue branch returns the fold instead of the pinned []: exit=1
- atk_12 boundary on the F2P fix: prime & a%p=0 -> [] (the prepatch symptom): exit=1
- atk_13 composite & a%p=0 -> [0] (sound but INCOMPLETE)       : exit=1

I did NOT count two earlier encodings whose rejection was a TOOL ARTIFACT rather than a refutation: atk_5/atk_5b (fold bound p+1, resp. `++ [p]`) and atk_9/atk_9b ([0] -> [0,0]) all died in an elaborator PANIC (`not a triple: _inhabitedExprDummy` + `(deterministic) timeout at whnf`, 200000 heartbeats) with no goal state. Per protocol a crash is not evidence, so I re-encoded those two axes as atk_12/atk_13 in the cheap guard shape, which elaborate cleanly and are refuted on real goals. Both files remain in the scratch dir but are excluded from the roster.

TACTIC-INDEPENDENT CHECK of every rejection (does the impl actually diverge from the spec-required output on a real input?): atk_1/atk_2 at (1,3,2) impl=[] vs required=[1]; atk_3 and atk_13 at (0,7,100) impl=[0] vs required=[0,10,...,90]; atk_6 at (4,4,9) impl=[5] vs [4,5] and at (13,4,17) impl=[5,12,14] vs [3,5,12,14]; atk_12 at (0,5,17)/(289,5,17) impl=[] vs [0] (this is the ISSUE'S OWN BUG -- nthroot_mod(`17*17`,5,17) missing the 0 root); atk_4 diverges on 76 in-domain composite inputs (e.g. (5,3,6) full=[5] vs bound-p-1=[]). atk_7/atk_8 coincide in VALUE with the required output on graded inputs, so their rejection is PROVABILITY tightness (powerMod is an opaque axiom, so neither the answer-key echo nor the isNthResidue->no-roots inference is derivable) rather than semantic wrongness -- I record that distinction rather than claiming them as semantic refutations.

GROUP 2 -- VERIFYING off-domain guards (2), and their MANDATORY resolve runs:
- atk_10 guard `n <= 2` -> [-7] : exit=0 VERIFIES. Off-domain via require_3 (n > 2). I used a NEGATIVE value so it also escapes the in-range soundness clause, a stronger escape than a positive constant.
- atk_11 guard `not isPrime p and not compositeValidated a n p` -> `rootsBelow (p.toNat / 2)` : exit=0 VERIFIES. Off-domain via require_1. I used a PARTIAL FOLD rather than a constant so the patch's wrongness is input-dependent -- if a graded call reached the guard it would return a genuinely wrong root set, not an obviously-absurd sentinel.
Both materialized as faithful patches and EXECUTED through the official harness (swebench_unified.harness.run_resolve, timeout 2400, retries 2), each checked with `git apply --check` in a pristine base_commit worktree (<D>/wtcheck) first:
  atk_10.diff -> git apply --check APPLIES; run_resolve resolved=TRUE, note='resolved', F2P success=[test_solve_modular] failure=[], P2P success 113/113 failure=[], PASS_TO_FAIL=[].
  atk_11.diff -> git apply --check APPLIES; run_resolve resolved=TRUE, note='resolved', F2P success=[test_solve_modular] failure=[], P2P success 113/113 failure=[], PASS_TO_FAIL=[].
=> NO verifying wrong impl fails to resolve; verify=>correct is NOT falsified.
I confirmed both guards are genuinely WRONG where they fire (so these are real wrong impls, not correct echoes): atk_10-patched nthroot_mod(1,1,7,True)=[-7]; atk_11-patched nthroot_mod(7,3,8,True)=[] vs truth [7], (5,3,8)=[] vs [5], (3,3,16)=[] vs [11]. atk_10's guard sits AFTER the unchanged `if n == 2: return sqrt_mod(...)` front dispatch, per mapping.md §1's declaration that the modeled body is the n != 2 tail -- verified: atk_10-patched nthroot_mod(9,2,160,True) is still the correct 8-element sqrt_mod answer.

WHY THE GUARDS ARE UNREACHABLE -- graded call surface MEASURED, not assumed. I instrumented nthroot_mod by dynamically rebinding EVERY module reference holding the function object (and re-sweeping after importing the test module, since its own `from ... import` would otherwise capture the original) and ran the full graded set on gold+test_patch: 114/114 pass, 8 distinct call events with recursion depth and caller site: (9,2,160)  d0 solveset.py:1205  -- n==2, taken by the unchanged sqrt_mod front dispatch, never reaches the modeled tail (3,4,7)    d0 solveset.py:1205  prime, in-domain (5,4,7)    d0 solveset.py:1205  prime, in-domain (13,4,17)  d0 solveset.py:1205  prime, in-domain (1,3,8)    d0 solveset.py:1205  enumerated triple, in-domain (1,3,2)    d1 residue_ntheory.py:758  RE-ENTRY of (1,3,8) -- the prior pass's hole, now in-domain (4,4,9)    d0 solveset.py:1205  enumerated triple, in-domain (4,4,3)    d1 residue_ntheory.py:758  RE-ENTRY of (4,4,9) OFF-DOMAIN graded calls: NONE.

Every n>2 call satisfies a>=0 & n>2 & p>=2 & (isPrime p | compositeValidated a n p). METHOD NOTE for whoever re-runs this: a naive static rebind of the 4 known reference sites recorded only 2 events, both misattributed to depth 0 -- the outer composite calls escaped the trace. The dynamic-rebind + post-test-import re-sweep is what surfaces all 8. A thin measurement here would wrongly read the enumerated triples as unreached.

SPEC TIGHTNESS ON-DOMAIN (the reason no on-domain attack survives): I computed the spec's required output for all 7 graded n>2 triples and it is fully pinned in every case -- (1,3,8)->[1], (4,4,9)->[4,5], (3,4,7)->[], (5,4,7)->[], (13,4,17)->[3,5,12,14], (1,3,2)->[1], (4,4,3)->[1,2] -- and gold agrees with all 7. All four ensures clauses partition the declared domain, so a same-spec impl has no on-domain slack anywhere on the graded surface.

A-LEG AUDIT (the assignment's focus), each re-derived independently against the real callee at base_commit+gold:
- A2 `rootsBelow` == real `_nthroot_mod_composite` (A-reference). All 5 brute-forceable enumerated triples MATCH the complete in-range root set: (1,3,8)->[1], (4,4,9)->[4,5], (16,5,36)->[4,22], (9,16,36)->[3,9,15,21,27,33], (0,7,100)->[0,10,...,90]. Squarefree-composite sweep: 19938 cases, 0 mismatches. I also CLOSED the one gap prior passes left open -- (4,3,3249000) is too large to brute force, so I decided it exactly by CRT over its prime-power factors {2^3,3^2,5^3,19^2}: local complete root counts are 0,0,1,0, so the global complete set is EMPTY, and real `_nthroot_mod_composite` returns [] too. MATCH. FAITHFUL.
- A5 `primeRoots` == real prime-field solver (A-reference): 1532 prime residue cases across p in {2..53}, 0 completeness mismatches, 0 non-ascending results (so the list-order R-leg in mapping.md §2 holds), and the primeRoots_sound contract (0 <= r < p and pow(r,n,p)==a%p) asserted on every entry. p=2 boundary checked explicitly for n in [3,8], a in [0,6]: all 42 MATCH. FAITHFUL down to p=2.
- A-consumed powerMod clauses vs real 3-arg pow (range, zero-base, prime-field zero-divisor): 0 violations over p in [2,60), n in [1,9), all x. isNthResidue_zero (a%p=0 => is_nthpow_residue): 0 violations.
- mapping.md §3.5 LOAD-BEARING claim re-derived: outside the regime (non-squarefree, non-enumerated) the real solver DIVERGES from the complete set in 549 of 6801 cases (e.g. a=3,n=3,p=8 real=[5] complete=[3]; a=7,n=3,p=8 real=[1] complete=[7]). So compositeValidated is a NECESSARY restriction, not gratuitous narrowing -- and atk_7/atk_12-style probes confirm it does not leak the result (the result stays pinned to the grounded fold).
- refinement.md §A2b / mapping.md §3.6 CLOSURE re-derived: over 23614 admitted inputs, every prime factor q of every admitted p yields a sub-input (a,n,q) that is itself admitted. 0 violations. `p >= 2` (not `p > 2`) is exactly that closure, and it is what makes branch-wise pinning survive composition with the model's own recursion -- the precise defect the prior spec had.

refinement.md LEG-KIND AUDIT: 8 legs (A1, A2, A3, A4, A5, A2b, A6 plus the R row), tags {R, I, R+I x2, A-consumed+R, A-reference+I x2}. Every leg is R / A-consumed / A-reference / I -- NO kind-3. §B's claim is accurate: the one genuinely changed operation (solving over a non-prime modulus) is modeled deeply by the rootsBelow/isRoot fold grounded in powerMod, with no oracle axiom about the changed function's result. The A-leg <-> real-callee correspondence holds as audited above.

ONE RESIDUAL PROSE DEFECT (not a break; independently reproduced, matching a prior pass's observation). mapping.md §2 states the R-leg as `None`/raise ("no solution"/declined) <-> `[]`, a many-to-one bijection. Downstream solveset.py:1205 does NOT treat those alike: None -> EmptySet, an exception -> caught and returns modterm unchanged. I executed both arms on the full graded set: returning [] instead of None -> 114/114 still pass (harmless); RAISING instead -> test_solve_modular (F2P) AND test_invert_modular (P2P) both FAIL. So the 'raise' arm of that stated bijection is FALSE downstream. It is not load-bearing for any verifying impl -- the frozen postcondition pins `out = []` exactly on that branch (which is why atk_8's substitution is rejected), so no same-spec impl can select the raise arm. RECOMMEND tightening §2 to `None <-> []` and dropping "raise", but this does not affect the gate.

**VERDICT:** SOUND. 11 same-spec attacks encoded and machine-verified (9 rejected on real postcondition goals with no PANIC, 2 verify), positive control verifies, both prepatch controls rejected, and BOTH verifying attacks' faithful patches were EXECUTED through the official harness and BOTH RESOLVED (resolved=True, F2P 1/1, P2P 113/113, PASS_TO_FAIL empty). Attacked along partial-domain (atk_4), boundary (atk_12, atk_13), control-flow-effect (atk_6, atk_3), ungrounded-oracle-echo (atk_7, atk_8), prior-counterexample (atk_1, atk_2) and off-domain-freedom (atk_10, atk_11) axes; verify=/=>correct could not be exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The prior pass's counterexample (guard escaping p=2, exploiting the older `require p > 2`) is CLOSED by the current `require p >= 2`. I re-encoded it BOTH ways -- atk_1 (guard `p = 2` -> []) and atk_2 (guard `p <= 2` -> []) -- and both are REJECTED (exit=1, clean `unsolved goals`, no PANIC). Tactic-independent confirmation: (1,3,2) is a REAL graded call (I measured it: it is the depth-1 re-entry sub-input of the enumerated triple (1,3,8), reached from solveset.py:1205 via residue_ntheory.py:758), it is in-domain under `p >= 2 & isPrime 2`, and the spec pins its output to [1] while the attacks return [] -- a genuine divergence, so the rejection is real spec tightness. Both verifying attacks (atk_10, atk_11) are precondition-infeasible off-domain guards whose faithful patches RESOLVED under the official harness.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 11 same-spec attacks (same_spec=True vs the frozen Solution.lean for every one), positive control, 2 prepatch controls, 2 official harness resolve runs. Verifications launched 4-way concurrent as detached background jobs via vrun.sh; resolve runs via rrun.sh.

CONTROLS -- `bash scripts/lean_verify.sh <D>/<f>.lean` from the repo root:
- pos_control.lean (byte copy of Solution.lean): exit=0 VERIFIES (non-vacuity).
- prepatch.lean (Solution_prepatch.lean, old zero-target dispatch order): exit=1 REJECTED.
- prepatch_1.lean (Solution_prepatch_1.lean, composite modulus declined -> []): exit=1 REJECTED.
=> prepatch_reproduced=true; both G-DIFF discriminators bite.

GROUP 1 -- REJECTED (9), all exit=1 with clean `unsolved goals` on real postcondition clauses, PANIC=0 in every log:
- atk_1  guard `p = 2` -> []                                  : exit=1 (prior counterexample input exactly)
- atk_2  guard `p <= 2` -> []                                 : exit=1 (prior counterexample guard shape)
- atk_3  zero-target check HOISTED ahead of the composite branch: exit=1 (control-flow/dispatch inversion)
- atk_4  partial-domain: composite fold bound `p.toNat - 1`    : exit=1
- atk_6  control-flow effect: copy loop `while i > 1` + `done_with i <= 1` (drops the first element; termination measure untouched): exit=1
- atk_7  answer-key echo: (1,3,8) hardcoded to [1]             : exit=1 (directive-8 probe)
- atk_8  ungrounded-oracle echo: non-residue branch returns the fold instead of the pinned []: exit=1
- atk_12 boundary on the F2P fix: prime & a%p=0 -> [] (the prepatch symptom): exit=1
- atk_13 composite & a%p=0 -> [0] (sound but INCOMPLETE)       : exit=1

I did NOT count two earlier encodings whose rejection was a TOOL ARTIFACT rather than a refutation: atk_5/atk_5b (fold bound p+1, resp. `++ [p]`) and atk_9/atk_9b ([0] -> [0,0]) all died in an elaborator PANIC (`not a triple: _inhabitedExprDummy` + `(deterministic) timeout at whnf`, 200000 heartbeats) with no goal state. Per protocol a crash is not evidence, so I re-encoded those two axes as atk_12/atk_13 in the cheap guard shape, which elaborate cleanly and are refuted on real goals. Both files remain in the scratch dir but are excluded from the roster.

TACTIC-INDEPENDENT CHECK of every rejection (does the impl actually diverge from the spec-required output on a real input?): atk_1/atk_2 at (1,3,2) impl=[] vs required=[1]; atk_3 and atk_13 at (0,7,100) impl=[0] vs required=[0,10,...,90]; atk_6 at (4,4,9) impl=[5] vs [4,5] and at (13,4,17) impl=[5,12,14] vs [3,5,12,14]; atk_12 at (0,5,17)/(289,5,17) impl=[] vs [0] (this is the ISSUE'S OWN BUG -- nthroot_mod(`17*17`,5,17) missing the 0 root); atk_4 diverges on 76 in-domain composite inputs (e.g. (5,3,6) full=[5] vs bound-p-1=[]). atk_7/atk_8 coincide in VALUE with the required output on graded inputs, so their rejection is PROVABILITY tightness (powerMod is an opaque axiom, so neither the answer-key echo nor the isNthResidue->no-roots inference is derivable) rather than semantic wrongness -- I record that distinction rather than claiming them as semantic refutations.

GROUP 2 -- VERIFYING off-domain guards (2), and their MANDATORY resolve runs:
- atk_10 guard `n <= 2` -> [-7] : exit=0 VERIFIES. Off-domain via require_3 (n > 2). I used a NEGATIVE value so it also escapes the in-range soundness clause, a stronger escape than a positive constant.
- atk_11 guard `not isPrime p and not compositeValidated a n p` -> `rootsBelow (p.toNat / 2)` : exit=0 VERIFIES. Off-domain via require_1. I used a PARTIAL FOLD rather than a constant so the patch's wrongness is input-dependent -- if a graded call reached the guard it would return a genuinely wrong root set, not an obviously-absurd sentinel.
Both materialized as faithful patches and EXECUTED through the official harness (swebench_unified.harness.run_resolve, timeout 2400, retries 2), each checked with `git apply --check` in a pristine base_commit worktree (<D>/wtcheck) first:
  atk_10.diff -> git apply --check APPLIES; run_resolve resolved=TRUE, note='resolved', F2P success=[test_solve_modular] failure=[], P2P success 113/113 failure=[], PASS_TO_FAIL=[].
  atk_11.diff -> git apply --check APPLIES; run_resolve resolved=TRUE, note='resolved', F2P success=[test_solve_modular] failure=[], P2P success 113/113 failure=[], PASS_TO_FAIL=[].
=> NO verifying wrong impl fails to resolve; verify=>correct is NOT falsified.
I confirmed both guards are genuinely WRONG where they fire (so these are real wrong impls, not correct echoes): atk_10-patched nthroot_mod(1,1,7,True)=[-7]; atk_11-patched nthroot_mod(7,3,8,True)=[] vs truth [7], (5,3,8)=[] vs [5], (3,3,16)=[] vs [11]. atk_10's guard sits AFTER the unchanged `if n == 2: return sqrt_mod(...)` front dispatch, per mapping.md §1's declaration that the modeled body is the n != 2 tail -- verified: atk_10-patched nthroot_mod(9,2,160,True) is still the correct 8-element sqrt_mod answer.

WHY THE GUARDS ARE UNREACHABLE -- graded call surface MEASURED, not assumed. I instrumented nthroot_mod by dynamically rebinding EVERY module reference holding the function object (and re-sweeping after importing the test module, since its own `from ... import` would otherwise capture the original) and ran the full graded set on gold+test_patch: 114/114 pass, 8 distinct call events with recursion depth and caller site: (9,2,160)  d0 solveset.py:1205  -- n==2, taken by the unchanged sqrt_mod front dispatch, never reaches the modeled tail (3,4,7)    d0 solveset.py:1205  prime, in-domain (5,4,7)    d0 solveset.py:1205  prime, in-domain (13,4,17)  d0 solveset.py:1205  prime, in-domain (1,3,8)    d0 solveset.py:1205  enumerated triple, in-domain (1,3,2)    d1 residue_ntheory.py:758  RE-ENTRY of (1,3,8) -- the prior pass's hole, now in-domain (4,4,9)    d0 solveset.py:1205  enumerated triple, in-domain (4,4,3)    d1 residue_ntheory.py:758  RE-ENTRY of (4,4,9) OFF-DOMAIN graded calls: NONE.

Every n>2 call satisfies a>=0 & n>2 & p>=2 & (isPrime p | compositeValidated a n p). METHOD NOTE for whoever re-runs this: a naive static rebind of the 4 known reference sites recorded only 2 events, both misattributed to depth 0 -- the outer composite calls escaped the trace. The dynamic-rebind + post-test-import re-sweep is what surfaces all 8. A thin measurement here would wrongly read the enumerated triples as unreached.

SPEC TIGHTNESS ON-DOMAIN (the reason no on-domain attack survives): I computed the spec's required output for all 7 graded n>2 triples and it is fully pinned in every case -- (1,3,8)->[1], (4,4,9)->[4,5], (3,4,7)->[], (5,4,7)->[], (13,4,17)->[3,5,12,14], (1,3,2)->[1], (4,4,3)->[1,2] -- and gold agrees with all 7. All four ensures clauses partition the declared domain, so a same-spec impl has no on-domain slack anywhere on the graded surface.

A-LEG AUDIT (the assignment's focus), each re-derived independently against the real callee at base_commit+gold:
- A2 `rootsBelow` == real `_nthroot_mod_composite` (A-reference). All 5 brute-forceable enumerated triples MATCH the complete in-range root set: (1,3,8)->[1], (4,4,9)->[4,5], (16,5,36)->[4,22], (9,16,36)->[3,9,15,21,27,33], (0,7,100)->[0,10,...,90]. Squarefree-composite sweep: 19938 cases, 0 mismatches. I also CLOSED the one gap prior passes left open -- (4,3,3249000) is too large to brute force, so I decided it exactly by CRT over its prime-power factors {2^3,3^2,5^3,19^2}: local complete root counts are 0,0,1,0, so the global complete set is EMPTY, and real `_nthroot_mod_composite` returns [] too. MATCH. FAITHFUL.
- A5 `primeRoots` == real prime-field solver (A-reference): 1532 prime residue cases across p in {2..53}, 0 completeness mismatches, 0 non-ascending results (so the list-order R-leg in mapping.md §2 holds), and the primeRoots_sound contract (0 <= r < p and pow(r,n,p)==a%p) asserted on every entry. p=2 boundary checked explicitly for n in [3,8], a in [0,6]: all 42 MATCH. FAITHFUL down to p=2.
- A-consumed powerMod clauses vs real 3-arg pow (range, zero-base, prime-field zero-divisor): 0 violations over p in [2,60), n in [1,9), all x. isNthResidue_zero (a%p=0 => is_nthpow_residue): 0 violations.
- mapping.md §3.5 LOAD-BEARING claim re-derived: outside the regime (non-squarefree, non-enumerated) the real solver DIVERGES from the complete set in 549 of 6801 cases (e.g. a=3,n=3,p=8 real=[5] complete=[3]; a=7,n=3,p=8 real=[1] complete=[7]). So compositeValidated is a NECESSARY restriction, not gratuitous narrowing -- and atk_7/atk_12-style probes confirm it does not leak the result (the result stays pinned to the grounded fold).
- refinement.md §A2b / mapping.md §3.6 CLOSURE re-derived: over 23614 admitted inputs, every prime factor q of every admitted p yields a sub-input (a,n,q) that is itself admitted. 0 violations. `p >= 2` (not `p > 2`) is exactly that closure, and it is what makes branch-wise pinning survive composition with the model's own recursion -- the precise defect the prior spec had.

refinement.md LEG-KIND AUDIT: 8 legs (A1, A2, A3, A4, A5, A2b, A6 plus the R row), tags {R, I, R+I x2, A-consumed+R, A-reference+I x2}. Every leg is R / A-consumed / A-reference / I -- NO kind-3. §B's claim is accurate: the one genuinely changed operation (solving over a non-prime modulus) is modeled deeply by the rootsBelow/isRoot fold grounded in powerMod, with no oracle axiom about the changed function's result. The A-leg <-> real-callee correspondence holds as audited above.

ONE RESIDUAL PROSE DEFECT (not a break; independently reproduced, matching a prior pass's observation). mapping.md §2 states the R-leg as `None`/raise ("no solution"/declined) <-> `[]`, a many-to-one bijection. Downstream solveset.py:1205 does NOT treat those alike: None -> EmptySet, an exception -> caught and returns modterm unchanged. I executed both arms on the full graded set: returning [] instead of None -> 114/114 still pass (harmless); RAISING instead -> test_solve_modular (F2P) AND test_invert_modular (P2P) both FAIL. So the 'raise' arm of that stated bijection is FALSE downstream. It is not load-bearing for any verifying impl -- the frozen postcondition pins `out = []` exactly on that branch (which is why atk_8's substitution is rejected), so no same-spec impl can select the raise arm. RECOMMEND tightening §2 to `None <-> []` and dropping "raise", but this does not affect the gate.

**VERDICT:** SOUND. 11 same-spec attacks encoded and machine-verified (9 rejected on real postcondition goals with no PANIC, 2 verify), positive control verifies, both prepatch controls rejected, and BOTH verifying attacks' faithful patches were EXECUTED through the official harness and BOTH RESOLVED (resolved=True, F2P 1/1, P2P 113/113, PASS_TO_FAIL empty). Attacked along partial-domain (atk_4), boundary (atk_12, atk_13), control-flow-effect (atk_6, atk_3), ungrounded-oracle-echo (atk_7, atk_8), prior-counterexample (atk_1, atk_2) and off-domain-freedom (atk_10, atk_11) axes; verify=/=>correct could not be exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on sympy__sympy-18199/velvet/Solution.lean. No divergence found between the modeled `nthRoots` and the real `nthroot_mod(a,n,p,all_roots=True)` tail anywhere inside the declared domain.

SETUP / HYGIENE
- Reference worktree at base_commit ba80d1e493 with patch.diff APPLIED; confirmed byte-equal to the bundle patch (`git diff` +/- lines vs patch.diff => identical). Post-patch repo is the oracle, per instructions; base commit used only for the unchanged callees the axioms model.
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True and same_spec(Solution.lean, Solution_prepatch_1.lean) = True, so the spec region is frozen across the discriminator files.
- scripts/lean_verify.sh on Solution.lean: EXIT=0 (the shipped spec+proof genuinely verifies; the finding is not masked by a broken build).

### EACH POSTCONDITION vs THE REAL CALLEE
- PC1 (soundness, every out[k] an in-range root): 0 violations. Primes to 3000, n in 3..300, a in 0..10p (6000 draws): no out-of-range element, no non-root, no non-list, no exception. Squarefree composites to 6000 likewise clean.
- PC2 (non-prime => out = rootsBelow p, the COMPLETE ascending in-range root set): the strongest claim, attacked hardest and it holds in-regime. Exhaustive squarefree composites p<120, n 3..9, a 0..min(p,40): 0 mismatches. 4000 random draws with a ALLOWED TO EXCEED p (Requires is only a>=0, so a>=p is in-domain — a real gap candidate): 0 mismatches. 3000 draws over 2862 squarefree composites to 6000, n to 40: 0. 262 squarefree moduli with 3-4 distinct prime factors (the CRT-combination stress): 0. Zero-target composite (a = 0, p, 2p over all squarefree composites < 1500): 0. Real returns sorted(set(...)) ascending, matching rootsBelow's ascending fold order exactly.
- All 6 enumerated non-squarefree triples in `compositeValidated` verified individually against brute force: (1,3,8)->[1], (4,4,9)->[4,5], (16,5,36)->[4,22], (9,16,36)->[3,9,15,21,27,33], (0,7,100)->[0,10..90], (4,3,3249000)->[] (full 3.2M-residue enumeration). All MATCH. The enumeration is not padding — each is genuinely the complete set.
- PC3 (prime, a%p!=0, residue => out = primeRoots): primeRoots IS the axiomatized real prime-field body, so equality is definitional; separately validated as the COMPLETE set (load-bearing because PC2 composes per-prime-factor sets via CRT): 2500 draws, primes to 4000, n to 60, a to 3p — sorted(set(real)) == brute force in every case, 0 violations.
- PC4 (prime, a%p!=0, not residue => out = []): matches the literal `if not is_nthpow_residue(...): return None` with None<->[] per mapping.md §2, and that line is reached only under exactly this guard post-patch. Fuzz found no case where real returned None while a%p==0 or while roots existed.
- PC5 (prime, a%p=0 => len 1 and out[0]=0): matches the patch's literal `if a % p == 0: return [0]`. 0 shape violations across the prime sweep.

AXIOM CLAUSES (unchanged callees, base-commit-valid) — all validated executably:
- powerMod_range: 200k random (x,n,p), 0 <= pow(x,n,p) < p — 0 violations.
- powerMod_zero: p<3000 x n in {1,2,3,7,50,199} — 0 violations.
- powerMod_field (prime => no zero divisors): exhaustive x over all primes < 600, n in {1,2,3,4,5,7,11,64,101} — 0 violations.
- isNthResidue_zero (a%p=0 => is_nthpow_residue): p<60 plus {64,81,100,121,3249000}, n 1..12, a in {0,p,2p,3p} — 0 violations.

### WHY THE DOMAIN RESTRICTION IS NOT DRIFT (the main too-strong candidate I probed)
`require isPrime p or compositeValidated a n p` narrows the domain rather than over-claiming, and it is genuinely LOAD-BEARING, not an answer key: outside the regime the real post-patch solver is only partially correct. Measured 1084 diverging cases out of 16862 non-squarefree in-range triples (p<300, n 3..9), e.g. a=3,n=3,p=8 real=[5] vs complete=[3]; a=7,n=3,p=8 real=[1] vs [7]; a=3,n=3,p=16 real=[7] vs [11]. So the guard excludes exactly the inputs where the real callee is buggy — dropping it would make the spec UNSATISFIABLE by the gold patch, which is the opposite of a too-strong spec. It is a condition on INPUTS; the result stays pinned to the grounded fold `rootsBelow` (powerMod-based), not to the predicate.
- a>=0 / n>2 / p>=2 are likewise input-side narrowings. n=2 provably never reaches the modeled tail (unchanged front `if n == 2: return sqrt_mod(...)` confirmed in the worktree source). p>=2 is the exact closure under the helper's self re-entry at prime factors q|p (q prime => q>=2 and isPrime q, a and n carried through), so no required result depends on unconstrained off-domain behavior — I checked p=2 exhaustively for n 3..8, a 0..6: real == complete in all 42 cells, so the re-entry base case is faithful, not vacuous.

**CONCLUSION:** no input in the declared domain where the modeled function disagrees with the patched repo. The one deliberately-scoped claim (composite completeness) is scoped to precisely the regime where the real callee is correct, and that scoping is measurably load-bearing. Verdict FAITHFUL; no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

RELAXED-LEAKAGE bundle (meta.relaxed_leakage=true, G-LEAK status "relaxed"). I treated RELAXED_LEAKAGE.md as a claim and re-derived its argument independently. Facet re-confirmed: the composite/non-prime-modulus COMPLETE-root-set behavior plus its validated regime enumeration (`compositeValidated`), i.e. exactly the facet the doc declares.

### What I ran

(1) Spec-region identity. src/swebench_unified.markers.same_spec(gold, prepatch, velvet.language) = True and same_spec(gold, prepatch_1) = True; gold spec_signature sha256 prefix eb5c507c7f59827c. So both twins are same-spec/different-impl and the spec view under review is the shared one.

(2) problem_statement <-> gold mismatch, measured not assumed. The public statement reports ONLY the zero-target bug (`nthroot_mod(17*17,5,17)` should return `0 mod 17`); it never mentions composite moduli. The gold diff makes two changes: the `if a % p == 0: return [0]` dispatch AND replacing `raise NotImplementedError("Not implemented for composite p")` with the new `_nthroot_mod_composite` CRT solver. The graded set is FAIL_TO_PASS=["test_solve_modular"] only; 113 PASS_TO_PASS entries contain ZERO ntheory residue tests (the zero-root assertions land in test_nthroot_mod, which is not graded). I built a clean worktree at base_commit ba80d1e49 and applied ONLY the problem-statement-derivable fix (the `a % p == 0: return [0]` dispatch, leaving the composite raise in place): test_solve_modular FAILS (AssertionError). Gold control: PASSES. So the graded discriminator genuinely is the composite behavior, which the public text cannot yield.

(3) Load-bearing test on the flagged clause (the doc's central claim). Stripped `ensures (¬ isPrime p ∧ compositeValidated a n p) → out = rootsBelow p.toNat a n p` from Solution_prepatch_1.lean (the composite-declining pre-patch twin) and re-closed the proof: scripts/lean_verify.sh exit 0 — the pre-patch twin VERIFIES against the de-narrated spec. Control: the same strip on gold also verifies (exit 0), and unstripped Solution_prepatch_1.lean FAILS precisely on `⊢ result_1 = rootsBelow p.toNat a n p`. So the clause is load-bearing for G-DIFF, not decoration: removing it admits pre-patch. Solution.lean itself verifies (exit 0); Solution_prepatch.lean fails on the `[0]`-singleton clause (ensures_1).

(4) The enumeration is forced too — I tested this rather than accepting it. Narrowed `compositeValidated` to `isSquarefree p` alone (dropping the graded triples (1,3,8) and (4,4,9)) and wrote a matching rival impl that declines non-squarefree composite moduli: Rival_sf_v3.lean VERIFIES (exit 0). Ported that same rival to Python on the gold-patched worktree (return [] when any factorint exponent > 1): test_solve_modular FAILS. So a regime that omits the graded non-squarefree triples admits a verifying rival that loses the graded test — the enumeration is the minimum faithful bound, not an answer key.

(5) Regime soundness both ways, independently. FAITHFUL: real `nthroot_mod(a,n,p,True)` equals my brute-force complete root set on every enumerated triple ((1,3,8)->[1], (4,4,9)->[4,5], (16,5,36)->[4,22], (9,16,36)->[3,9,15,21,27,33], (0,7,100)->[0,10,...,90]). LOAD-BEARING: I found 1038 out-of-regime divergences by brute force over non-squarefree p in [4,120), n in [3,9) — e.g. gold returns [5] at (3,3,8) where the true root is [3] — so the guard cannot be widened; gold is genuinely only partially correct outside it. Bundle checkers re-run green against the real gold-patched repo: axiom_check.py "G-AX OK" (20000 powerMod checks, 3656 faithful regime checks incl. moduli 8/9 and edge p==2, out-of-regime divergence witnessed, domain closed over 6293 sub-inputs) and conformance_check.py "G-CONF OK" (4048 inputs, 0 disagreements).

(6) Nothing leaks BEYOND the declared facet. Scanned the computed spec_view for gold algorithm internals: zero occurrences of crt, cartes, `_nthroot_mod_composite`, factorint, mod_inverse, "prime-power", NotImplemented, or the issue's literal 17. The result is pinned to the grounded fold `rootsBelow` (structural over `powerMod`), not to `compositeValidated`, so the regime predicate is an input-side domain bound, not an oracle on the output. `require p ≥ 2` is the closure of the domain under the modeled body's re-entry on prime factors (mapping.md §3.6), an input-side caller-observable condition. Lexical screen leakage.screen(): passed=True, no hard or soft failures.

(7) Doc-steering check, as instructed. leakage.reviewer_directed(RELAXED_LEAKAGE.md) = [] and my own read found no line telling this panel which verdict to submit or how to record. The doc does cite a prior G-PANEL-3 LEAKAGE verdict and a prior verdict.md prescription, but it frames these as history and does not instruct me — I reached NO-LEAKAGE from measurements (2)-(6) above, not from its assertion. Note as context, not a finding: the doc's own "CAVEAT" quote records that an earlier revision lacked the declaration entirely and that the earlier LEAKAGE verdict was against that undeclared revision; the current bundle carries both the flag and the doc, so that defect is closed.

**CONCLUSION.** The unavoidability argument holds under my own re-derivation: strip the narration and the spec verifies against the PRE-patch impl, so the clause is load-bearing; a problem_statement-only spec provably cannot discriminate the graded composite behavior (measured, (2)); and the leak is confined to the single declared facet with the core gates (G-VERIFY, G-DIFF, G-AX, G-CONF) independently re-confirmed sound. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
