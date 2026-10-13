# P2 adversarial audit — django__django-16082

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,12 +94,17 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    -- PRE-PATCH skeleton: the remainder operation is registered ONLY for
+    -- like-with-like numeric kinds; the mixed integer/decimal and
+    -- integer/floating rows are absent from the scanned list. So the scan
+    -- returns `none` for mixed numeric operands instead of the widened kind —
+    -- exactly the bug. `prove_correct` MUST fail: `out = combinedNumeric lhs rhs`
+    -- is violated at e.g. lhs = .int, rhs = .dec (combinedNumeric gives `.dec`,
+    -- this scan gives `none`).
+    let combs : List Combinator :=
+      [ (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
@@ -139,5 +144,14 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  -- The loop body closes against the (buggy, like-with-like-only) scanned list,
+  -- so the proof reaches the final obligation `lookup [int,int,int ; float,…;
+  -- dec,…] lhs rhs = combinedNumeric lhs rhs`. That is FALSE — e.g. at
+  -- lhs = .int, rhs = .dec the scan yields `none` but `combinedNumeric` yields
+  -- `some .dec` — so `prove_correct` cannot close (G-DIFF: the spec sees the bug).
+  rw [lookup_drop_step
+        [ (NumKind.int,   NumKind.int,   NumKind.int),
+          (NumKind.float, NumKind.float, NumKind.float),
+          (NumKind.dec,   NumKind.dec,   NumKind.dec) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,12 +94,13 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
@@ -139,5 +140,12 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,12 +94,14 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.int),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
@@ -139,5 +141,13 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.int),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,12 +94,16 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float),
+        (NumKind.float, NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.float, NumKind.dec) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
@@ -139,5 +143,15 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float),
+        (NumKind.float, NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.float, NumKind.dec) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,18 +94,20 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ combs.length
       invariant res = lookup (combs.drop i) lhs rhs
-      done_with i = 0
+      done_with i = 1
       decreasing i
     do
       let p := combs[i - 1]!
@@ -139,5 +141,14 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
+  all_goals (first | rfl | simp | omega | grind)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,14 +94,9 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
     let combs : List Combinator := modCombinators
     let mut res : Option NumKind := none
-    let mut i := combs.length
+    let mut i := 0
     while i > 0
       invariant 0 ≤ i ∧ i ≤ combs.length
       invariant res = lookup (combs.drop i) lhs rhs
@@ -139,5 +134,7 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step modCombinators
+        i lhs rhs (by omega) (by omega)]
   simp_all
+  all_goals (first | rfl | simp | omega | grind)
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,24 +94,10 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
-    let mut res : Option NumKind := none
-    let mut i := combs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
-      done_with i = 0
-      decreasing i
-    do
-      let p := combs[i - 1]!
-      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
-      i := i - 1
-    return res
+    -- ungrounded-oracle echo: no scan at all; the impl simply re-reads the
+    -- postcondition's own function. Verifies trivially -- probes whether the
+    -- spec forces the registered-rule search or merely its extension.
+    return combinedNumeric lhs rhs
     -- impl-end
 
 /- The backward-scan step: dropping one fewer rule exposes rule `i-1` on the
@@ -139,5 +125,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | grind)
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,17 +94,20 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    -- vacuity probe: the fold invariant that ties `res` to `lookup` is
+    -- DROPPED, leaving only the bounds invariant, over a list missing the
+    -- integer/float widenings. If the verifier closes this, the loop's
+    -- postcondition obligation was never really discharged.
+    let combs : List Combinator :=
+      [ (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
       done_with i = 0
       decreasing i
     do
@@ -139,5 +142,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | omega | grind | decide)
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,22 +94,16 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
     let combs : List Combinator := modCombinators
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
       done_with i = 0
       decreasing i
     do
       let p := combs[i - 1]!
-      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
+      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.1 else res
       i := i - 1
     return res
     -- impl-end
@@ -139,5 +133,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | omega | grind | decide)
```

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,22 +94,16 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
     let combs : List Combinator := modCombinators
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
       done_with i = 0
       decreasing i
     do
       let p := combs[i - 1]!
-      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
+      res := if lhs = p.1 then some p.2.2 else res
       i := i - 1
     return res
     -- impl-end
@@ -139,5 +133,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | omega | grind | decide)
```

Attack 11 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,24 +94,9 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
-    let mut res : Option NumKind := none
-    let mut i := combs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
-      done_with i = 0
-      decreasing i
-    do
-      let p := combs[i - 1]!
-      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
-      i := i - 1
-    return res
+    -- ungrounded-oracle echo #2: the frozen pure first-match lookup is read
+    -- directly rather than re-implemented as a loop.
+    return lookup modCombinators lhs rhs
     -- impl-end
 
 /- The backward-scan step: dropping one fewer rule exposes rule `i-1` on the
@@ -139,5 +124,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | grind)
```

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,12 +94,15 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      [  (NumKind.int,   NumKind.dec,   NumKind.float),
+        (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
@@ -139,5 +142,14 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step
+      [  (NumKind.int,   NumKind.dec,   NumKind.float),
+        (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.dec,   NumKind.int,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float),
+        (NumKind.float, NumKind.int,   NumKind.float) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
```

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,23 +94,18 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      modCombinators ++ [(NumKind.int, NumKind.dec, NumKind.int)]
     let mut res : Option NumKind := none
-    let mut i := combs.length
-    while i > 0
+    let mut i := 0
+    while i < combs.length
       invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
-      done_with i = 0
-      decreasing i
+      done_with i = combs.length
+      decreasing combs.length - i
     do
-      let p := combs[i - 1]!
+      let p := combs[i]!
       res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
-      i := i - 1
+      i := i + 1
     return res
     -- impl-end
 
@@ -139,5 +134,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | omega | grind | decide)
```

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,21 +94,15 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
     let combs : List Combinator := modCombinators
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ combs.length
-      invariant res = lookup (combs.drop i) lhs rhs
       done_with i = 0
       decreasing i
     do
-      let p := combs[i - 1]!
+      let p := combs[i]!
       res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
       i := i - 1
     return res
@@ -139,5 +133,4 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
-  simp_all
+  all_goals (first | rfl | simp_all | omega | grind | decide)
```

Attack 15 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,12 +94,12 @@
   ensures out = combinedNumeric lhs rhs
   do
     -- impl-start
-    -- Scan the registered combination rules for the remainder operation
-    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
-    -- integer/decimal and integer/floating widenings. First match wins; a
-    -- backward scan that only overwrites lets the lowest-index (first) matching
-    -- rule have the final say.
-    let combs : List Combinator := modCombinators
+    let combs : List Combinator :=
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float) ]
     let mut res : Option NumKind := none
     let mut i := combs.length
     while i > 0
@@ -139,5 +139,11 @@
 
 prove_correct resolveModType by
   loom_solve
-  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
+  rw [lookup_drop_step
+      [  (NumKind.int,   NumKind.int,   NumKind.int),
+        (NumKind.float, NumKind.float, NumKind.float),
+        (NumKind.dec,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.dec,   NumKind.dec),
+        (NumKind.int,   NumKind.float, NumKind.float) ]
+        i lhs rhs (by omega) (by omega)]
   simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model A-reference. The operation under
-- specification is a total function of the two operand numeric kinds; it calls
-- no unchanged repository callee that needs a contract. Its agreement with the
-- real result-kind resolver is checked executably by conformance_check.py
-- (G-CONF), which runs the resolver in its actual (post-change) configuration.
-- axioms-end

-- pure-start
/- The three numeric operand kinds an arithmetic combination can carry, in the
   abstract: an exact integer kind, a floating kind, and a fixed-precision
   decimal kind. (mapping.md §2 gives the bijection from the concrete operand
   field classes onto these kinds.) -/
inductive NumKind where
  | int
  | float
  | dec
  deriving DecidableEq, Inhabited

/- The desired result kind when combining a left operand of kind `l` with a
   right operand of kind `r` under the remainder operation.

   * like-with-like keeps the kind;
   * an integer mixed with a decimal widens to the decimal kind;
   * an integer mixed with a floating value widens to the floating kind;
   * a floating value mixed with a decimal has no common numeric kind
     (`none`), as does any pair this relation does not list.

   This is the abstract behaviour the issue asks for: combining mixed numeric
   kinds under remainder must resolve to the wider kind (e.g. integer with
   decimal resolves to decimal), exactly as the other arithmetic combinations
   already do. It is grounded purely in the two operand kinds, so only an
   implementation that actually performs the resolution can satisfy the
   postcondition. -/
def combinedNumeric : NumKind → NumKind → Option NumKind
  | .int,   .int   => some .int
  | .float, .float => some .float
  | .dec,   .dec   => some .dec
  | .int,   .dec   => some .dec
  | .dec,   .int   => some .dec
  | .int,   .float => some .float
  | .float, .int   => some .float
  | _,      _      => none

/- A single registered combination rule: (left kind, right kind, result kind). -/
abbrev Combinator := NumKind × NumKind × NumKind

/- First-match lookup over a list of registered combination rules: scan from the
   front and return the result of the first rule whose left/right kinds match the
   operands, otherwise `none`. Front-recursive so a single unfold is available
   per loop step (the backward-fold verification pattern). -/
def lookup : List Combinator → NumKind → NumKind → Option NumKind
  | [],                _, _ => none
  | (a, b, c) :: rest, l, r =>
      if l = a ∧ r = b then some c else lookup rest l r

/- The registered combination rules for the remainder operation: like-with-like
   for each numeric kind, plus the mixed integer/decimal and integer/floating
   widenings. First match wins (lowest index has the final say). -/
def modCombinators : List Combinator :=
  [ (NumKind.int,   NumKind.int,   NumKind.int),
    (NumKind.float, NumKind.float, NumKind.float),
    (NumKind.dec,   NumKind.dec,   NumKind.dec),
    (NumKind.int,   NumKind.dec,   NumKind.dec),
    (NumKind.dec,   NumKind.int,   NumKind.dec),
    (NumKind.int,   NumKind.float, NumKind.float),
    (NumKind.float, NumKind.int,   NumKind.float) ]

@[grind] lemma lookup_nil (l r : NumKind) : lookup [] l r = none := rfl

/- Cons unfold reading a rule by its projections (the loop body reads a rule as a
   triple via `.1 / .2.1 / .2.2` rather than by pattern syntax). -/
@[grind] lemma lookup_cons' (p : Combinator) (rest : List Combinator) (l r : NumKind) :
    lookup (p :: rest) l r =
      (if l = p.1 ∧ r = p.2.1 then some p.2.2 else lookup rest l r) := by
  obtain ⟨a, b, c⟩ := p; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveModType (lhs : NumKind) (rhs : NumKind) return (out : Option NumKind)
  ensures out = combinedNumeric lhs rhs
  do
    -- impl-start
    -- Scan the registered combination rules for the remainder operation
    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
    -- integer/decimal and integer/floating widenings. First match wins; a
    -- backward scan that only overwrites lets the lowest-index (first) matching
    -- rule have the final say.
    let combs : List Combinator := modCombinators
    let mut res : Option NumKind := none
    let mut i := combs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ combs.length
      invariant res = lookup (combs.drop i) lhs rhs
      done_with i = 0
      decreasing i
    do
      let p := combs[i - 1]!
      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
      i := i - 1
    return res
    -- impl-end

/- The backward-scan step: dropping one fewer rule exposes rule `i-1` on the
   front, so `lookup` peels exactly that rule. This is the single fold goal
   `loom_solve` leaves for the loop body. -/
lemma lookup_drop_step (combs : List Combinator) (i : Nat) (l r : NumKind)
    (hi : 0 < i) (hle : i ≤ combs.length) :
    lookup (combs.drop (i - 1)) l r =
      (if l = (combs[i - 1]!).1 ∧ r = (combs[i - 1]!).2.1 then some (combs[i - 1]!).2.2
       else lookup (combs.drop i) l r) := by
  have hlt : i - 1 < combs.length := by omega
  have hcons : combs.drop (i - 1) = combs[i - 1]! :: combs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, lookup_cons']

/- Scanning the full rule list reproduces the abstract result-kind relation:
   the first-match lookup over `modCombinators` equals `combinedNumeric`. Closed
   by exhausting the nine operand-kind pairs. -/
@[grind] lemma lookup_modCombinators (l r : NumKind) :
    lookup modCombinators l r = combinedNumeric l r := by
  cases l <;> cases r <;> rfl

prove_correct resolveModType by
  loom_solve
  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, 15 same-spec attacks + 2 positive controls, all machine-checked. Byte-identical spec confirmed for every file via swebench_unified.markers.same_spec (True for all 17) and admissibility via variant_scope.unsound_evasions (empty for all 17: no new axiom, no sorry/admit/native_decide, prove_correct obligation retained).

**VERDICT:** SOUND. 13 of 15 attacks were REJECTED by the frozen spec; the 2 that verify are ungrounded-oracle ECHOES whose faithful refined patches were materialized and RUN through the official harness, and BOTH RESOLVED -- i.e. they are correct echoes of the gold, not verify-does-not-imply-correct breaks.

**TOOLING:** verify = `bash scripts/lean_verify.sh <file>` from the repo root (exit 0 = verifies, 1 = rejected). resolve = harness.run_resolve('django__django-16082', <patch>) via resolve_one.py. Verifications were run concurrently in background batches of 4.

### EXECUTED RESOLVE RESULTS (the protocol's required evidence):
* atk_7 (echo: `return combinedNumeric lhs rhs`) -> patch = gold hunk (MOD added to the different-type numeric group). run_resolve: completed=True RESOLVED=True applied=True attempts=1; F2P both pass (test_resolve_output_field_number, test_resolve_output_field_with_null), F2P failures=[], P2P 170 ok / 0 fail. -> NOT a break.
* atk_12 (echo: `return lookup modCombinators lhs rhs`) -> patch is deliberately NON-gold-shaped: a SEPARATE `_connector_combinations` block registering the four mixed MOD rows, generated with `git diff` on a clean worktree at base_commit and `git apply --check`-validated (my first hand-written version was a corrupt diff and was discarded rather than reported). run_resolve: completed=True RESOLVED=True applied=True attempts=1; F2P both pass, P2P 170 ok / 0 fail. -> NOT a break. This also independently confirms refinement.md legs 2-4: a structurally different registration with the same first-match semantics resolves, so the map keys on the RELATION, not on the gold's edit shape.

### ATTACKS AND OBSERVED RESULTS (all ):
- atk_1 PREPATCH BUG REPRODUCED (verbatim Solution_prepatch.lean, like-with-like rows only): exit 1, unsolved `res_1 = combinedNumeric lhs rhs`.
- atk_2 partial-domain, (dec,int) row omitted: exit 1. Witness dec%int -> none vs some .dec.
- atk_3 boundary, (int,dec) -> NARROWER .int: exit 1. Witness int%dec -> .int vs .dec.
- atk_4 over-permissive, float/dec given a bogus common kind: exit 1. Witnesses float%dec and dec%float -> some .dec vs none.
- atk_5 control-flow, `while i > 1` so index 0 is never consulted: exit 1. Witness int%int -> none.
- atk_6 control-flow-effect, loop counter initialised to 0 so the body never runs (always none): exit 1.
- atk_7 ungrounded-oracle echo: VERIFIES -> resolve RESOLVED (above).
- atk_8 VACUITY probe: the fold invariant tying `res` to `lookup` is DROPPED (only the bounds invariant kept) over a list missing both integer/float widenings: exit 1. The obligation is genuinely discharged, not vacuous -- the spec does not let an impl buy its exit code by weakening the loop invariant.
- atk_10 control-flow-effect, result read from the rule's LEFT field (`p.1`) instead of its RESULT field (`p.2.2`): exit 1.
- atk_11 partial-domain, right-operand test dropped so the scan matches on lhs alone: exit 1.
- atk_12 second ungrounded-oracle echo: VERIFIES -> resolve RESOLVED (above).
- atk_13 PRECEDENCE, correct rows all present but a wrong (int,dec)->float row placed FIRST: exit 1. Confirms the spec pins first-match ORDER, not merely rule membership.
- atk_14 PRECEDENCE DIRECTION, forward scan that keeps overwriting so the LAST match wins, plus a trailing shadow row: exit 1.
- atk_15 boundary/off-by-one, reads `combs[i]!` instead of `combs[i-1]!`: exit 1.
- atk_16 partial-domain by construction, mixed widenings registered only for an integer LEFT operand so (dec,int)/(float,int) fall through: exit 1. The relation's symmetry is enforced.

RIGOR NOTE (self-correction; recorded because it changes what the rejections mean). My first pass appended extra tactics (`all_goals (first | rfl | simp | omega | grind)`) to the proof, and three list-shaped attacks then failed at `lhs=int, rhs=int` -- a pair where those impls are CORRECT. That is tactic weakness, not a spec rejection, and crediting it to the spec would have been a rubber-stamp. I rebuilt atk_2/3/4/13/16 to use the frozen proof shape VERBATIM (`loom_solve; rw [lookup_drop_step ...]; simp_all`) so the only possible residual is the false equation `lookup <wrong list> lhs rhs = combinedNumeric lhs rhs`; all five then fail at the real obligation `res_1 = combinedNumeric lhs rhs`. Separately, I machine-checked in Python that every one of the 15 attack impls really is semantically wrong, printing a concrete witness for each (atk_5 int%int; atk_6 three pairs; atk_8 int%float, float%int; atk_10/11 int%float, int%dec; atk_14 int%dec; atk_15 int%int) -- so no rejection is credited to an impl that was actually correct.

OVER-FITTING CONTROL (second positive control, ctrl_2_shadowed.lean, VERIFIES exit 0): my originally-submitted atk_9 appended three extra rows (int,int)->float, (dec,dec)->int, (float,float)->dec AFTER the gold rows. Python check proved these are INERT under first-match, so it is EQUIVALENT to the spec -- a correct reshape, not a wrong impl. I RETIRED it as an attack (it would have been a retained label carrying a false oracle verdict) and repromoted it to a positive control; after fixing its proof it verifies. So the spec accepts any impl that gets the RELATION right, and is not over-fitted to the gold rule list -- the complement of the atk_13/atk_14 result that it still pins precedence.

A-LEG AUDIT (my primary assignment). refinement.md claims no consumed axioms and no deep-model A-reference. VERIFIED FACTUALLY: `grep -nE '^\s*axiom|sorry|admit|native_decide|Assume|Refute' Solution.lean` returns NOTHING; there is no axiom_check.py; meta.json records axioms=[] and G-AX status=skip ('no axiom_check.py (no axioms in bundle)'). So there are no A-consumed and no A-reference legs, and consequently no axiom-soundness trust point -- refinement.md's strongest claim is the one that needed no trust. Every leg in its table is R (1, 4) or I (2, 3); there is no kind-3 (inexpressible-changed-op) step. Critically, the function UNDER CHANGE (`_resolve_combined_type` at the MOD slice) is NOT axiomatized -- it is modeled deeply as the spelled-out `modCombinators` list plus the verified `lookup` first-match scan, which is what directive 7 requires and what makes atk_2/3/4/13/16 refutable at all. An axiom there would have been vacuously true prepatch.

MODEL<->PATCH CORRESPONDENCE, CHECKED AGAINST THE REAL CALLEE (not just read). In a fresh worktree at base_commit (git worktree add --detach, under my scratch dir) I ran the real resolver: `_connector_combinators[MOD]` prepatch holds exactly the 3 same-kind rows + 2 FloatField/NoneType rows, and MOD int x dec -> None (the bug); under the gold and under atk_12's patch the four mixed rows appear and int x dec -> DecimalField. issubclass(AutoField, IntegerField) is True and AutoField x DecimalField -> DecimalField, confirming mapping.md 2's integer-family collapse to one NumKind. The `lru_cache` on `_resolve_combined_type` is keyed on (connector, lhs, rhs) with no hidden state, so the Lean model's pure-total-function shape is faithful.

DOMAIN-RESTRICTION PROBE (the one real gap the map leaves, and why it does not break the bundle). The spec models only MOD x {int,float,dec}^2. I ran the F2P tests locally on the prepatch tree (PYTHONPATH=<wt> python runtests.py ... --settings=test_sqlite) and enumerated the failing subtests: EXACTLY four, all connector '%%' -- IntegerField x DecimalField, DecimalField x IntegerField, IntegerField x FloatField, FloatField x IntegerField. The instance's entire discriminating behaviour is therefore precisely the four mixed MOD pairs the spec's `combinedNumeric` adds, all INSIDE the modeled domain; nothing discriminating lives outside it. I then probed the unmodeled slice adversarially: a patch that adds the four mixed MOD rows (so the modeled relation is exactly right) while simultaneously DROPPING MOD from the NULL group -- behaviour the Lean spec says nothing about. The full expressions suite passed (181 tests, OK), so the oracle is silent there too and it yields no break; the restriction is a genuine (and disclosed) scope limit, not an exploitable hole, and I did not report it as one.

**ENVIRONMENT NOTE:** the pre-existing shared worktree was DIRTY (another cell's test-patch edit) when I first read it, so I did all repo-level work in my own fresh worktree under my scratch dir and left it clean (git checkout -- .). Prior G-EQ/G-PANEL fails in verdict.md read 'only 0 admissible attacks of 0 submitted' plus 'audit role errored' -- an audit that never ran, not a recorded spec defect; this submission supplies the missing battery. One caution for the record: my `pkill -f resolve_one.py atk_12` killed my own tool shell (exit 144) because many cells run an identically-named script, and it also killed a stale resolve I had launched against a then-corrupt patch; I relaunched that resolve against the git-validated patch and report only the completed run.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model A-reference. The operation under
-- specification is a total function of the two operand numeric kinds; it calls
-- no unchanged repository callee that needs a contract. Its agreement with the
-- real result-kind resolver is checked executably by conformance_check.py
-- (G-CONF), which runs the resolver in its actual (post-change) configuration.
-- axioms-end

-- pure-start
/- The three numeric operand kinds an arithmetic combination can carry, in the
   abstract: an exact integer kind, a floating kind, and a fixed-precision
   decimal kind. (mapping.md §2 gives the bijection from the concrete operand
   field classes onto these kinds.) -/
inductive NumKind where
  | int
  | float
  | dec
  deriving DecidableEq, Inhabited

/- The desired result kind when combining a left operand of kind `l` with a
   right operand of kind `r` under the remainder operation.

   * like-with-like keeps the kind;
   * an integer mixed with a decimal widens to the decimal kind;
   * an integer mixed with a floating value widens to the floating kind;
   * a floating value mixed with a decimal has no common numeric kind
     (`none`), as does any pair this relation does not list.

   This is the abstract behaviour the issue asks for: combining mixed numeric
   kinds under remainder must resolve to the wider kind (e.g. integer with
   decimal resolves to decimal), exactly as the other arithmetic combinations
   already do. It is grounded purely in the two operand kinds, so only an
   implementation that actually performs the resolution can satisfy the
   postcondition. -/
def combinedNumeric : NumKind → NumKind → Option NumKind
  | .int,   .int   => some .int
  | .float, .float => some .float
  | .dec,   .dec   => some .dec
  | .int,   .dec   => some .dec
  | .dec,   .int   => some .dec
  | .int,   .float => some .float
  | .float, .int   => some .float
  | _,      _      => none

/- A single registered combination rule: (left kind, right kind, result kind). -/
abbrev Combinator := NumKind × NumKind × NumKind

/- First-match lookup over a list of registered combination rules: scan from the
   front and return the result of the first rule whose left/right kinds match the
   operands, otherwise `none`. Front-recursive so a single unfold is available
   per loop step (the backward-fold verification pattern). -/
def lookup : List Combinator → NumKind → NumKind → Option NumKind
  | [],                _, _ => none
  | (a, b, c) :: rest, l, r =>
      if l = a ∧ r = b then some c else lookup rest l r

/- The registered combination rules for the remainder operation: like-with-like
   for each numeric kind, plus the mixed integer/decimal and integer/floating
   widenings. First match wins (lowest index has the final say). -/
def modCombinators : List Combinator :=
  [ (NumKind.int,   NumKind.int,   NumKind.int),
    (NumKind.float, NumKind.float, NumKind.float),
    (NumKind.dec,   NumKind.dec,   NumKind.dec),
    (NumKind.int,   NumKind.dec,   NumKind.dec),
    (NumKind.dec,   NumKind.int,   NumKind.dec),
    (NumKind.int,   NumKind.float, NumKind.float),
    (NumKind.float, NumKind.int,   NumKind.float) ]

@[grind] lemma lookup_nil (l r : NumKind) : lookup [] l r = none := rfl

/- Cons unfold reading a rule by its projections (the loop body reads a rule as a
   triple via `.1 / .2.1 / .2.2` rather than by pattern syntax). -/
@[grind] lemma lookup_cons' (p : Combinator) (rest : List Combinator) (l r : NumKind) :
    lookup (p :: rest) l r =
      (if l = p.1 ∧ r = p.2.1 then some p.2.2 else lookup rest l r) := by
  obtain ⟨a, b, c⟩ := p; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveModType (lhs : NumKind) (rhs : NumKind) return (out : Option NumKind)
  ensures out = combinedNumeric lhs rhs
  do
    -- impl-start
    -- Scan the registered combination rules for the remainder operation
    -- (`modCombinators`): like-with-like for each numeric kind, plus the mixed
    -- integer/decimal and integer/floating widenings. First match wins; a
    -- backward scan that only overwrites lets the lowest-index (first) matching
    -- rule have the final say.
    let combs : List Combinator := modCombinators
    let mut res : Option NumKind := none
    let mut i := combs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ combs.length
      invariant res = lookup (combs.drop i) lhs rhs
      done_with i = 0
      decreasing i
    do
      let p := combs[i - 1]!
      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
      i := i - 1
    return res
    -- impl-end

/- The backward-scan step: dropping one fewer rule exposes rule `i-1` on the
   front, so `lookup` peels exactly that rule. This is the single fold goal
   `loom_solve` leaves for the loop body. -/
lemma lookup_drop_step (combs : List Combinator) (i : Nat) (l r : NumKind)
    (hi : 0 < i) (hle : i ≤ combs.length) :
    lookup (combs.drop (i - 1)) l r =
      (if l = (combs[i - 1]!).1 ∧ r = (combs[i - 1]!).2.1 then some (combs[i - 1]!).2.2
       else lookup (combs.drop i) l r) := by
  have hlt : i - 1 < combs.length := by omega
  have hcons : combs.drop (i - 1) = combs[i - 1]! :: combs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, lookup_cons']

/- Scanning the full rule list reproduces the abstract result-kind relation:
   the first-match lookup over `modCombinators` equals `combinedNumeric`. Closed
   by exhausting the nine operand-kind pairs. -/
@[grind] lemma lookup_modCombinators (l r : NumKind) :
    lookup modCombinators l r = combinedNumeric l r := by
  cases l <;> cases r <;> rfl

prove_correct resolveModType by
  loom_solve
  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, 15 same-spec attacks + 2 positive controls, all machine-checked. Byte-identical spec confirmed for every file via swebench_unified.markers.same_spec (True for all 17) and admissibility via variant_scope.unsound_evasions (empty for all 17: no new axiom, no sorry/admit/native_decide, prove_correct obligation retained).

**VERDICT:** SOUND. 13 of 15 attacks were REJECTED by the frozen spec; the 2 that verify are ungrounded-oracle ECHOES whose faithful refined patches were materialized and RUN through the official harness, and BOTH RESOLVED -- i.e. they are correct echoes of the gold, not verify-does-not-imply-correct breaks.

**TOOLING:** verify = `bash scripts/lean_verify.sh <file>` from the repo root (exit 0 = verifies, 1 = rejected). resolve = harness.run_resolve('django__django-16082', <patch>) via resolve_one.py. Verifications were run concurrently in background batches of 4.

### EXECUTED RESOLVE RESULTS (the protocol's required evidence):
* atk_7 (echo: `return combinedNumeric lhs rhs`) -> patch = gold hunk (MOD added to the different-type numeric group). run_resolve: completed=True RESOLVED=True applied=True attempts=1; F2P both pass (test_resolve_output_field_number, test_resolve_output_field_with_null), F2P failures=[], P2P 170 ok / 0 fail. -> NOT a break.
* atk_12 (echo: `return lookup modCombinators lhs rhs`) -> patch is deliberately NON-gold-shaped: a SEPARATE `_connector_combinations` block registering the four mixed MOD rows, generated with `git diff` on a clean worktree at base_commit and `git apply --check`-validated (my first hand-written version was a corrupt diff and was discarded rather than reported). run_resolve: completed=True RESOLVED=True applied=True attempts=1; F2P both pass, P2P 170 ok / 0 fail. -> NOT a break. This also independently confirms refinement.md legs 2-4: a structurally different registration with the same first-match semantics resolves, so the map keys on the RELATION, not on the gold's edit shape.

### ATTACKS AND OBSERVED RESULTS (all ):
- atk_1 PREPATCH BUG REPRODUCED (verbatim Solution_prepatch.lean, like-with-like rows only): exit 1, unsolved `res_1 = combinedNumeric lhs rhs`.
- atk_2 partial-domain, (dec,int) row omitted: exit 1. Witness dec%int -> none vs some .dec.
- atk_3 boundary, (int,dec) -> NARROWER .int: exit 1. Witness int%dec -> .int vs .dec.
- atk_4 over-permissive, float/dec given a bogus common kind: exit 1. Witnesses float%dec and dec%float -> some .dec vs none.
- atk_5 control-flow, `while i > 1` so index 0 is never consulted: exit 1. Witness int%int -> none.
- atk_6 control-flow-effect, loop counter initialised to 0 so the body never runs (always none): exit 1.
- atk_7 ungrounded-oracle echo: VERIFIES -> resolve RESOLVED (above).
- atk_8 VACUITY probe: the fold invariant tying `res` to `lookup` is DROPPED (only the bounds invariant kept) over a list missing both integer/float widenings: exit 1. The obligation is genuinely discharged, not vacuous -- the spec does not let an impl buy its exit code by weakening the loop invariant.
- atk_10 control-flow-effect, result read from the rule's LEFT field (`p.1`) instead of its RESULT field (`p.2.2`): exit 1.
- atk_11 partial-domain, right-operand test dropped so the scan matches on lhs alone: exit 1.
- atk_12 second ungrounded-oracle echo: VERIFIES -> resolve RESOLVED (above).
- atk_13 PRECEDENCE, correct rows all present but a wrong (int,dec)->float row placed FIRST: exit 1. Confirms the spec pins first-match ORDER, not merely rule membership.
- atk_14 PRECEDENCE DIRECTION, forward scan that keeps overwriting so the LAST match wins, plus a trailing shadow row: exit 1.
- atk_15 boundary/off-by-one, reads `combs[i]!` instead of `combs[i-1]!`: exit 1.
- atk_16 partial-domain by construction, mixed widenings registered only for an integer LEFT operand so (dec,int)/(float,int) fall through: exit 1. The relation's symmetry is enforced.

RIGOR NOTE (self-correction; recorded because it changes what the rejections mean). My first pass appended extra tactics (`all_goals (first | rfl | simp | omega | grind)`) to the proof, and three list-shaped attacks then failed at `lhs=int, rhs=int` -- a pair where those impls are CORRECT. That is tactic weakness, not a spec rejection, and crediting it to the spec would have been a rubber-stamp. I rebuilt atk_2/3/4/13/16 to use the frozen proof shape VERBATIM (`loom_solve; rw [lookup_drop_step ...]; simp_all`) so the only possible residual is the false equation `lookup <wrong list> lhs rhs = combinedNumeric lhs rhs`; all five then fail at the real obligation `res_1 = combinedNumeric lhs rhs`. Separately, I machine-checked in Python that every one of the 15 attack impls really is semantically wrong, printing a concrete witness for each (atk_5 int%int; atk_6 three pairs; atk_8 int%float, float%int; atk_10/11 int%float, int%dec; atk_14 int%dec; atk_15 int%int) -- so no rejection is credited to an impl that was actually correct.

OVER-FITTING CONTROL (second positive control, ctrl_2_shadowed.lean, VERIFIES exit 0): my originally-submitted atk_9 appended three extra rows (int,int)->float, (dec,dec)->int, (float,float)->dec AFTER the gold rows. Python check proved these are INERT under first-match, so it is EQUIVALENT to the spec -- a correct reshape, not a wrong impl. I RETIRED it as an attack (it would have been a retained label carrying a false oracle verdict) and repromoted it to a positive control; after fixing its proof it verifies. So the spec accepts any impl that gets the RELATION right, and is not over-fitted to the gold rule list -- the complement of the atk_13/atk_14 result that it still pins precedence.

A-LEG AUDIT (my primary assignment). refinement.md claims no consumed axioms and no deep-model A-reference. VERIFIED FACTUALLY: `grep -nE '^\s*axiom|sorry|admit|native_decide|Assume|Refute' Solution.lean` returns NOTHING; there is no axiom_check.py; meta.json records axioms=[] and G-AX status=skip ('no axiom_check.py (no axioms in bundle)'). So there are no A-consumed and no A-reference legs, and consequently no axiom-soundness trust point -- refinement.md's strongest claim is the one that needed no trust. Every leg in its table is R (1, 4) or I (2, 3); there is no kind-3 (inexpressible-changed-op) step. Critically, the function UNDER CHANGE (`_resolve_combined_type` at the MOD slice) is NOT axiomatized -- it is modeled deeply as the spelled-out `modCombinators` list plus the verified `lookup` first-match scan, which is what directive 7 requires and what makes atk_2/3/4/13/16 refutable at all. An axiom there would have been vacuously true prepatch.

MODEL<->PATCH CORRESPONDENCE, CHECKED AGAINST THE REAL CALLEE (not just read). In a fresh worktree at base_commit (git worktree add --detach, under my scratch dir) I ran the real resolver: `_connector_combinators[MOD]` prepatch holds exactly the 3 same-kind rows + 2 FloatField/NoneType rows, and MOD int x dec -> None (the bug); under the gold and under atk_12's patch the four mixed rows appear and int x dec -> DecimalField. issubclass(AutoField, IntegerField) is True and AutoField x DecimalField -> DecimalField, confirming mapping.md 2's integer-family collapse to one NumKind. The `lru_cache` on `_resolve_combined_type` is keyed on (connector, lhs, rhs) with no hidden state, so the Lean model's pure-total-function shape is faithful.

DOMAIN-RESTRICTION PROBE (the one real gap the map leaves, and why it does not break the bundle). The spec models only MOD x {int,float,dec}^2. I ran the F2P tests locally on the prepatch tree (PYTHONPATH=<wt> python runtests.py ... --settings=test_sqlite) and enumerated the failing subtests: EXACTLY four, all connector '%%' -- IntegerField x DecimalField, DecimalField x IntegerField, IntegerField x FloatField, FloatField x IntegerField. The instance's entire discriminating behaviour is therefore precisely the four mixed MOD pairs the spec's `combinedNumeric` adds, all INSIDE the modeled domain; nothing discriminating lives outside it. I then probed the unmodeled slice adversarially: a patch that adds the four mixed MOD rows (so the modeled relation is exactly right) while simultaneously DROPPING MOD from the NULL group -- behaviour the Lean spec says nothing about. The full expressions suite passed (181 tests, OK), so the oracle is silent there too and it yields no break; the restriction is a genuine (and disclosed) scope limit, not an exploitable hole, and I did not report it as one.

**ENVIRONMENT NOTE:** the pre-existing shared worktree was DIRTY (another cell's test-patch edit) when I first read it, so I did all repo-level work in my own fresh worktree under my scratch dir and left it clean (git checkout -- .). Prior G-EQ/G-PANEL fails in verdict.md read 'only 0 admissible attacks of 0 submitted' plus 'audit role errored' -- an audit that never ran, not a recorded spec defect; this submission supplies the missing battery. One caution for the record: my `pkill -f resolve_one.py atk_12` killed my own tool shell (exit 144) because many cells run an identically-named script, and it also killed a stale resolve I had launched against a then-corrupt patch; I relaunched that resolve against the git-validated patch and report only the completed run.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK ATTACK FOUND NO DIVERGENCE. Reference = base commit bf47c71971 worktree with patch.diff APPLIED (per instructions; base used only for untouched callees, of which there are none here).

**MODELED FUNCTION:** resolveModType (lhs rhs : NumKind) -> Option NumKind, ensures out = combinedNumeric lhs rhs. Binds to `_resolve_combined_type`(Combinable.MOD, lhs_type, rhs_type) at django/db/models/expressions.py:622, specialized to connector=MOD (declared in mapping.md §1).

1. EXHAUSTIVE DOMAIN CHECK (the decisive test). The modeled domain is finite: 3x3 = 9 NumKind pairs. I ran all 9 against the real post-patch resolver. Spec vs real, kind-for-kind:
  (int,int)->int/int OK; (int,float)->float/float OK; (int,dec)->dec/dec OK;
  (float,int)->float/float OK; (float,float)->float/float OK; (float,dec)->None/None OK;
  (dec,int)->dec/dec OK; (dec,float)->None/None OK; (dec,dec)->dec/dec OK.
ALL 9 PAIRS AGREE. Because the modeled domain is exhausted, no diverging input can exist within it -- this is a proof, not a sample.

2. THE issubclass COLLAPSE (mapping.md §2's riskiest R-claim) HOLDS. The spec collapses the whole IntegerField family to one kind; if any concrete field class broke that, the bijection would be unfaithful. I walked the ENTIRE django tree (pkgutil.walk_packages, 39 Field subclasses discovered) and extracted every class landing in the numeric slice -- 12 classes: AutoField, BigAutoField, BigIntegerField, DecimalField, FloatField, IntegerField, OrderWrt, PositiveBigIntegerField, PositiveIntegerField, PositiveSmallIntegerField, SmallAutoField, SmallIntegerField. Probed explicitly for MULTI-KIND classes (subclassing more than one of Integer/Float/Decimal, which would make the kind map ill-defined and order-dependent): ZERO found. Then 144/144 concrete class pairs vs the real resolver: 0 disagreements. This includes AutoField/BigAutoField/SmallAutoField, which reach IntegerField through the AutoFieldMeta metaclass `__subclasscheck__` rather than normal MRO -- verified issubclass(AutoField, IntegerField)=True, so the metaclass path does not break the collapse.

3. NOT TOO STRONG on the 'none' rows. The spec's strongest claims are (float,dec)->none and (dec,float)->none -- a too-strong spec would demand a result the repo does not produce. Real resolver returns None for both. Dumped the real registered MOD combinator list post-patch: indices 0-6 are exactly modCombinators; indices 7-8 are (Float,NoneType)/(NoneType,Float) NULL rows, unreachable from numeric-only operands, so modCombinators is a faithful prefix under first-match. NoneType operands are outside the declared modeled domain (mapping.md §2), a scoping matter, not a spec/repo disagreement.

4. **MECHANICAL GATES.** Solution.lean verifies via scripts/lean_verify.sh (exit 0). Spec regions byte-identical between Solution.lean and Solution_prepatch.lean: markers.same_spec(a,b,VelvetBackend)=True, spec_view identical (5376==5376 bytes) across all four regions (axioms/pure/pre/post) -- prepatch differs only in the impl region, so the frozen spec is genuinely shared. Shipped conformance_check.py: G-CONF OK, 100000 inputs, seed 16082, 0 disagreements.

5. NON-VACUITY + DISCRIMINATION CONTROLS. (a) Mutant control: flipped combinedNumeric's (int,dec) row from some .dec to some .int -> verification FAILS (lookup modCombinators int dec not definitionally equal to combinedNumeric int dec). The postcondition really pins the widening rows; it is not vacuous. (b) Solution_prepatch.lean FAILS to verify, leaving the expected unproved goal res_1 = combinedNumeric lhs rhs with only the 3 same-kind rules in scope -- correct G-DIFF direction. (c) F2P tests with the real test_patch applied (which adds Combinable.MOD to the connectors list) PASS post-patch; with the code patch reverted, test_resolve_output_field_number FAILS with 4 errors ('Cannot infer type of %% expression involving these types: FloatField, IntegerField'), confirming the tests discriminate exactly the modeled delta.

**NO-DIVERGENCE-BY-CONSTRUCTION CAVEAT I CHECKED FOR:** I confirmed I was not comparing against the base version (the trap in the instructions). The 9-pair and 144-pair agreements were measured with patch.diff APPLIED; I separately confirmed the base version diverges on exactly the four mixed rows, which is the patch delta and therefore NOT a spec defect.

**AXIOM SOUNDNESS:** no trust point -- the axioms region is empty (no `axiom`, no axiom_check.py), and the function under change is modeled deeply (spelled-out modCombinators + verified first-match lookup) rather than axiomatized, so directive 7 is respected.

**CONCLUSION:** no input exists on which the modeled function disagrees with the real post-patch callee; the modeled domain was exhausted rather than sampled. The spec is neither too strong (its 'none' rows match reality) nor drifted (its widening rows match reality). FAITHFUL.

**FAITHFULNESS-BREAK ATTACK FOUND NO DIVERGENCE.** Reference = base commit bf47c71971 worktree with patch.diff APPLIED (per instructions; base used only for untouched callees, of which there are none here).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 (leakage / gold-reconstruction) on django__django-16082/velvet. Spec view computed with markers.spec_view(Solution.lean, VelvetBackend) — impl region and prove_correct body both elided (adapter guards satisfied).

**SPEC-REGION INTEGRITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; spec_signature byte-equal; spec_view sha256 identical (a440a0505fbd526e both). Solution.lean elaborates clean: scripts/lean_verify.sh -> EXIT=0.

**MECHANICAL SCREEN:** leakage.screen(Solution.lean, velvet, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Checked against the frozen swe_bench_verified row, judged vs problem_statement ONLY (hints_text — the #33397 / PR-15271 discussion — is never consulted; nothing in the view echoes it).

L1 (gold line / diff markers): gold changed line is exactly ['Combinable.MOD,'] (normalized 15 chars, >=8 threshold). Not present in the view. No @@ / 'diff --git' / '+++ ' / '\nindex ' present.

L2 (path / module / symbol): 'django/db/models/expressions.py' absent; dotted 'django.db.models.expressions' absent. Explicit negative grep over the view for every repo symbol on the change path — `_resolve_combined_type`, `_connector_combinations`, `_connector_combinators`, register_combinable_fields, Combinable, CombinedExpression, `_resolve_output_field`, `_output_field_or_none`, output_field, IntegerField, DecimalField, FloatField, AutoField, DurationField, NoneType, FieldError, issubclass, connector, POW, BITAND, 'same type', 'different type' — ALL ABSENT. The view's only vocabulary is abstract: NumKind.int/float/dec, combinedNumeric, lookup, modCombinators, Combinator, resolveModType. `_patch_changed_symbols`(gold) = {'hash'} (from the @@ section header 'def `__hash__`'), not present as an identifier or comment token.

L3 (narration): no narration token fires. The one behavioral comment ('combining mixed numeric kinds under remainder must resolve to the wider kind (e.g. integer with decimal resolves to decimal), exactly as the other arithmetic combinations already do') is a de-identified paraphrase of the public problem_statement ('if the types of the query are different (Decimal and Integer), it doesn't resolve the result to a Decimal type, like it does for other mathematical operators'). 'MOD' itself is public via the problem statement title/body; 'remainder' is a synonym, i.e. de-identification rather than leak. The prepatch file's explicit bug narration ('PRE-PATCH skeleton', 'exactly the bug') lives entirely in the impl/prove_correct regions and is elided by the projection — confirmed by the identical view hashes above.

SUBSTANTIVE RECONSTRUCTION TEST (the real question, not just the screen): the strongest LEAKAGE case is that modCombinators spells out a 7-row list (3 same-kind then 4 mixed) = the post-patch registered MOD rule set, so diffing it against base commit yields the one-line edit.

I checked this against the base-commit worktree (bf47c71971) and reject it: (a) a spec cannot state 'mixed numeric under remainder widens' without implying that post-state — the postcondition 'out = combinedNumeric lhs rhs' already fully determines it, so this is irreducible spec content, not edit disclosure; (b) the only content beyond the problem statement's literal Decimal/Integer pair is int/float widening and float x dec -> none, and BOTH are public base-commit facts: db/models/expressions.py:522-536 at base commit lists (Integer,Decimal->Decimal), (Decimal,Integer->Decimal), (Integer,Float->Float), (Float,Integer->Float) for ADD/SUB/MUL/DIV with no Float x Decimal row, and the problem statement explicitly directs the solver to imitate it ('like it does for other mathematical operators').

The registry-plus-first-match-scan architecture the view models is likewise unchanged public code (`_connector_combinations`, `_resolve_combined_type` at :622). So the view carries no information the solver lacks from problem_statement + the base-commit checkout.

**NOT A TEST TRANSCRIPTION:** the hidden test's row set (which includes AutoField pairs) is not mirrored — combinedNumeric is a superset on same-kind pairs and omits AutoField entirely, so the view is not a projection of the held-out test table.

**NO EDIT-SITE POINTER:** the view never localizes the edit. meta.json modeled_functions does name `_resolve_combined_type` at expressions.py:622, but (i) that is the harness localization aid, disclosed in mode 0 too (info-env parity, eval/dataset.py MODES_WITH_SPEC), not the spec view under this gate, and (ii) it points at the unchanged READING function, not the edited table at :533. refinement.md/mapping.md do quote the gold hunk verbatim, but neither is consumer-visible — confirmed no reference to them in eval/prompts.py, eval/dataset.py, or eval/adapter.py.

OBSERVATION (not leakage, logged for the other lanes): the helper lemmas lookup_drop_step and lookup_modCombinators sit OUTSIDE the elided regions with full proofs, so the view discloses the intended Lean proof strategy (backward drop-scan) and that the impl should scan modCombinators. That lowers Lean-side difficulty but reveals nothing about the Django edit — it is a spec-strength/difficulty matter for G-PANEL-1, not gold-edit leakage under this gate.

**Verdict:** NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
