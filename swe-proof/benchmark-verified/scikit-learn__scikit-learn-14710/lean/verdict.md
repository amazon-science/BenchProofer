# P2 adversarial audit — scikit-learn__scikit-learn-14710

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`

**Machine verdict**

eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier. A `diff` block below is against that spec file, which the attack it belongs to is otherwise identical to.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,8 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1 -- the PRE-PATCH bug, re-encoded: no decode anywhere, the raw
+-- integer codes are handed to the scoring function at both sites.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,37 +293,12 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
-  let mut yT : Targets := Sum.inl yTrain
-  if isClf then
-    let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
-    yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
+  let trScore ← scorer xTrain (Sum.inl yTrain)
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
+    let xv ← readValData xVal
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
-    let mut yV : Targets := Sum.inl codes
-    if isClf then
-      let ls ← readLabels labels
-      let decoded ← relabelTargets ls codes
-      yV := Sum.inr decoded
-    let xv ← readValData xVal
-    let vlScore ← scorer xv yV
+    let vlScore ← scorer xv (Sum.inl codes)
     valScores := valScores ++ [vlScore]
     return { trainScores := trainScores, valScores := valScores,
              stop := shouldStop valScores }
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2 -- prior counterexample re-encode: the TRAINING gather is PERFORMED
+-- (bound) above the `isClf` guard on a DEFAULTED class-label table, and consumed
+-- only inside the guard. The guarded `readLabels` is left exactly where it was,
+-- so nothing absent is READ.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +295,15 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
+  let hoistedDecoded ← relabelTargets (labels.getD #[]) yTrain
   if isClf then
-    let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
-    yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
+    let _ls ← readLabels labels
+    yT := Sum.inr hoistedDecoded
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3 -- prior counterexample re-encode at the VALIDATION site: the
+-- validation gather is PERFORMED above the `useVal` guard with BOTH conditional
+-- arguments defaulted, and consumed only inside the guard.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,35 +294,20 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
+  let hoistedVal ← relabelTargets (labels.getD #[]) (yVal.getD yTrain)
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
-      let ls ← readLabels labels
-      let decoded ← relabelTargets ls codes
-      yV := Sum.inr decoded
+      let _ls ← readLabels labels
+      yV := Sum.inr hoistedVal
     let xv ← readValData xVal
     let vlScore ← scorer xv yV
     valScores := valScores ++ [vlScore]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4 -- PARTIAL-DOMAIN attack on the A-reference gather: the training
+-- decode is re-implemented with a domain NARROWED to non-negative codes, i.e. it
+-- refuses the END-resolved (negative) codes numpy answers for. Agrees with the
+-- contract's gather on every non-negative in-range code array.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +295,18 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
+    let decoded ←
+      if yTrain.all (fun c => 0 ≤ c ∧ c < (ls.size : Int)) then
+        .ok (yTrain.map (fun c => ls[c.toNat]!))
+      else .error EarlyStopError.codeOutOfRange
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5 -- BOUNDARY attack: the gather is performed against the class-label
+-- table extended by one entry, so the domain's upper edge moves out by one (a
+-- code equal to the real table size is answered instead of refused).
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +294,15 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
+    let decoded ← relabelTargets (ls.push "") yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6 -- CONTROL-FLOW-EFFECT: every recorded value is gold's and every read
+-- stays on its own branch, but the VALIDATION pair is scored BEFORE the training
+-- pair, so where the scoring function would refuse both, the wrong refusal answers.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +294,13 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
-  trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
@@ -322,9 +308,13 @@
       yV := Sum.inr decoded
     let xv ← readValData xVal
     let vlScore ← scorer xv yV
+    let trScore ← scorer xTrain yT
+    trainScores := trainScores ++ [trScore]
     valScores := valScores ++ [vlScore]
     return { trainScores := trainScores, valScores := valScores,
              stop := shouldStop valScores }
+  let trScore ← scorer xTrain yT
+  trainScores := trainScores ++ [trScore]
   return { trainScores := trainScores, valScores := valScores,
            stop := shouldStop trainScores }
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,50 +283,51 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7 -- UNGROUNDED-ORACLE ECHO: the postcondition's right-hand sides
+-- transcribed verbatim as the implementation. No imperative skeleton at all; it
+-- reads the contract back rather than refining the method.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
     (xTrain : XData) (yTrain : Array Int)
     (xVal : Option XData) (yVal : Option (Array Int))
-    (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
-  let mut trainScores := trScores
-  let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
-  let mut yT : Targets := Sum.inl yTrain
-  if isClf then
-    let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
-    yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
-  trainScores := trainScores ++ [trScore]
-  if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
-    let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
-    let mut yV : Targets := Sum.inl codes
-    if isClf then
-      let ls ← readLabels labels
-      let decoded ← relabelTargets ls codes
-      yV := Sum.inr decoded
-    let xv ← readValData xVal
-    let vlScore ← scorer xv yV
-    valScores := valScores ++ [vlScore]
-    return { trainScores := trainScores, valScores := valScores,
-             stop := shouldStop valScores }
-  return { trainScores := trainScores, valScores := valScores,
-           stop := shouldStop trainScores }
+    (trScores vlScores : List Score) : Except EarlyStopError CheckResult :=
+  match isClf, labels, useVal, xVal, yVal with
+  | true, none, _, _, _ => Except.error EarlyStopError.absentClassLabels
+  | true, some ls, false, _, _ =>
+      (relabelTargets ls yTrain).bind
+        (fun yT => (scorer xTrain (Sum.inr yT)).map
+          (fun trScore => { trainScores := trScores ++ [trScore],
+                            valScores := vlScores,
+                            stop := shouldStop (trScores ++ [trScore]) }))
+  | true, some ls, true, some xv, some yv =>
+      (relabelTargets ls yTrain).bind
+        (fun yT => (scorer xTrain (Sum.inr yT)).bind
+          (fun trScore => (relabelTargets ls yv).bind
+            (fun yV => (scorer xv (Sum.inr yV)).map
+              (fun vlScore => { trainScores := trScores ++ [trScore],
+                                valScores := vlScores ++ [vlScore],
+                                stop := shouldStop (vlScores ++ [vlScore]) }))))
+  | true, some ls, true, _, yv =>
+      (relabelTargets ls yTrain).bind
+        (fun yT => (scorer xTrain (Sum.inr yT)).bind
+          (fun _ => (readValCodes yv).bind
+            (fun codes => (relabelTargets ls codes).bind
+              (fun _ => Except.error EarlyStopError.absentValidationData))))
+  | false, _, false, _, _ =>
+      (scorer xTrain (Sum.inl yTrain)).map
+        (fun trScore => { trainScores := trScores ++ [trScore],
+                          valScores := vlScores,
+                          stop := shouldStop (trScores ++ [trScore]) })
+  | false, _, true, some xv, some yv =>
+      (scorer xTrain (Sum.inl yTrain)).bind
+        (fun trScore => (scorer xv (Sum.inl yv)).map
+          (fun vlScore => { trainScores := trScores ++ [trScore],
+                            valScores := vlScores ++ [vlScore],
+                            stop := shouldStop (vlScores ++ [vlScore]) }))
+  | false, _, true, _, _ =>
+      (scorer xTrain (Sum.inl yTrain)).bind
+        (fun _ => Except.error EarlyStopError.absentValidationData)
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,6 +283,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 8 -- the total-op probe the fourth lane did NOT close. The fourth lane
+-- made the ARRAY gather (`relabelTargets`) partial, but a SCALAR index into the
+-- class-label table is still totalizable: `String` is `Inhabited`, so `ls[k]!`
+-- elaborates and returns `""` for an out-of-range `k` where numpy's
+-- `self.classes_[k]` RAISES `IndexError`. Here `k = yTrain.size`, which on the
+-- real classifier parametrizations (30 training samples, 2 classes) is far past
+-- the table's last entry. The value is discarded, so every recorded value is
+-- gold's and the frozen proof closes unchanged.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +299,16 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
+    let _probe : String := ls[yTrain.size]!
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,6 +283,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 9 -- the coverage gap the battery does not cover: the scoring function
+-- is consulted TWICE about the SAME pair the contract names -- both applications
+-- are CONSUMED (bound), the second answer discarded. Extensionally gold, so no
+-- clause about reads, recorded values, or named pairs can see it.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +295,15 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
+  let trScore ← (scorer xTrain yT).bind (fun s => (scorer xTrain yT).map (fun _ => s))
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
@@ -330,6 +319,10 @@
 -- impl-end
 
 -- proof-start
+private theorem dupcollapse {ε α : Type} (x : Except ε α) :
+    (x.bind fun s => x.map fun _ => s) = x := by
+  cases x <;> rfl
+
 theorem correct_scoreEarlyStop :
     ∀ (scorer : Scorer) (shouldStop : List Score → Bool)
       (isClf useVal : Bool) (labels : Option (Array String))
@@ -342,5 +335,6 @@
           xTrain yTrain xVal yVal trScores vlScores) := by
   intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores
   unfold problem_spec_scoreEarlyStop implementation_scoreEarlyStop
+  simp only [dupcollapse]
   cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;> rfl
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 10 -- fine-grained ORDER attack inside the validation branch: the
+-- validation codes are read first (as the contract demands), but the DESIGN
+-- MATRIX is read BEFORE the codes are decoded, so where the codes do not decode
+-- and the matrix is absent, the matrix's absence answers instead of the decode's
+-- own refusal.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,36 +296,21 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
+    let xv ← readValData xVal
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
       let decoded ← relabelTargets ls codes
       yV := Sum.inr decoded
-    let xv ← readValData xVal
     let vlScore ← scorer xv yV
     valScores := valScores ++ [vlScore]
     return { trainScores := trainScores, valScores := valScores,
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,6 +283,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 11 -- the same total-op probe as attack 8 but OUTSIDE every guard and on
+-- the TRAINING CODES rather than the class-label table, so it is reached on every
+-- configuration the repository actually produces (regressor and classifier alike).
+-- `Int` is `Inhabited`, so `yTrain[yTrain.size]!` elaborates and returns `0` where
+-- numpy's `y_small_train[len(y_small_train)]` RAISES `IndexError`. The value is
+-- discarded, so every recorded value is gold's and the frozen proof closes.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +297,16 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
+  let _probe : Int := yTrain[yTrain.size]!
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial re-derivation, instance scikit-learn__scikit-learn-14710 (lean). 11 attacks, all same_spec=True (spec/axioms/pure/pre/post byte-identical; only the impl region and, where noted, the proof region differ).

**POSITIVE CONTROL:** pos_control.lean (byte copy of Solution.lean). `bash scripts/lean_verify.sh <f>` -> EXIT=0.
PREPATCH REPRODUCED: prepatch.lean (Solution_prepatch.lean) -> EXIT=1 with exactly 16 unclosed `rfl` goals, matching refinement.md's documented count (the sixteen isClf=true cases). G-DIFF satisfied.

atk_1  REJECTED exit 1 -- prepatch bug re-encoded (no decode; raw Sum.inl at both sites)
atk_2  REJECTED exit 1 -- prior counterexample (weak-getd-train-decode-hoisted / old atk_6): train gather PERFORMED above the isClf guard on labels.getD #[]
atk_3  REJECTED exit 1 -- prior counterexample (weak-getd-val-decode-hoisted / old atk_7): val gather performed above useVal with both args defaulted
atk_4  REJECTED exit 1 -- PARTIAL-DOMAIN: decode re-implemented with domain narrowed to non-negative codes (dodges the END-resolved side numpy answers)
atk_5  REJECTED exit 1 -- BOUNDARY: gather against (ls.push ""), moving the domain's upper edge out by one
atk_6  REJECTED exit 1 -- CONTROL-FLOW-EFFECT: validation pair scored BEFORE the training pair (records gold's values; only the refusal precedence inverts)
atk_10 REJECTED exit 1 -- fine-grained ORDER: xVal read between the val-codes read and the val decode, so the matrix's absence answers where the decode's own codeOutOfRange is demanded
atk_7  VERIFIES exit 0, #print axioms correct_scoreEarlyStop = [propext]
atk_8  VERIFIES exit 0, [propext]
atk_9  VERIFIES exit 0, [propext, Quot.sound]
atk_11 VERIFIES exit 0, [propext]
(axiom probes: {7,8,9,11}.lean, same verify command, all exit 0, clean -- no sorryAx, no Classical.choice.)

GOLD RESOLVE CONTROL (ran FIRST, one at a time on this instance -- cache_level env deletes the image on completion, so a concurrent peer 404s ImageNotFound and would take the control with it): patch_gold.diff -> resolved=True completed=True note='resolved', F2P 1/1, P2P 63/63. Image/host/oracle certified healthy, so every attack verdict below is attributable to its patch.

MANDATORY RESOLVE OF EVERY CLOSING ATTACK (harness.run_resolve, retries=1, strictly serialized; each patch `git apply --check`-ed clean in the base_commit worktree @ 4b6273b87442a4437d8b3873ea3022ae163f4fdf):
  atk_7  -> patch_atk7.diff       resolved=True  F2P 1/1  P2P 63/63. Ungrounded-oracle echo (postcondition RHS transcribed as a 7-arm match). Denotationally gold, so its faithful patch IS the gold patch (byte-compared: identical apart from the diff hunk-header context label). Correct echo; the contract is right to admit it.
  atk_9  -> patch_atk9.diff       resolved=True  F2P 1/1  P2P 63/63. THE COVERAGE GAP I set out to exploit: the scorer is consulted TWICE about the SAME pair the contract names, both applications CONSUMED, the second answer discarded. The battery has no case for this (all 22 shipped impls contain exactly 2 scorer applications; the record's atk_14 covers only a duplicate on an UNNAMED pair). It needed a proof lemma (`dupcollapse : x.bind (fun s => x.map (fun _ => s)) = x`), hence Quot.sound. Its faithful patch makes both calls for real. It RESOLVES -- scorer_ is a deterministic pure read (`estimator.predict(X)` then a metric), so a repeated consult on an identical pair is genuinely unobservable. The gap is real as a battery-coverage note but is NOT a spec weakness: no faithful refinement of it can fail.
  atk_8  -> patch_atk8_total.diff  resolved=True  F2P 1/1  P2P 63/63
  atk_11 -> patch_atk11_total.diff resolved=True  F2P 1/1  P2P 63/63

atk_8 / atk_11 ARE THE ATTACK THIS ROUND TURNED ON, and the reason the verdict is SOUND rather than BROKEN rests on a measurement, not an argument. Both probe the ONE total-Lean-op-for-partial-Python-op hole the fourth lane did NOT close: the lane made the ARRAY gather (relabelTargets) partial, but a SCALAR index is still totalizable, because String and Int are Inhabited. atk_8 evaluates `ls[yTrain.size]!` inside the isClf guard; atk_11 evaluates `yTrain[yTrain.size]!` OUTSIDE every guard, so it is reached on every configuration the repo produces (regressor and classifier alike). numpy's counterparts RAISE IndexError (measured: `y[len(y)]` -> IndexError, `classes_[3]` on a 2-entry table -> IndexError). Each value is discarded, so every recorded value is gold's and the frozen proof closes unchanged. This is exactly the shape that broke the spec in the recorded round D.

I refused to settle the faithfulness reading by argument and materialized BOTH candidate refinements of each, running all four through the oracle:
  patch_atk11_eager.diff (read PERFORMED, allowed to raise) -> resolved=False completed=True, 'consistent - not flaky'
  patch_atk8_eager.diff  (same)                            -> resolved=False completed=True, F2P 0/1, P2P 54 success / 9 FAILURE (8x test_early_stopping_classification + test_binning_train_validation_are_separated)
  patch_atk11_total.diff / patch_atk8_total.diff (read performed, returns normally with the default) -> resolved=True, F2P 1/1, P2P 63/63
The EAGER reading is the unfaithful one, and I measured why rather than asserting it. sem.lean (verify command as above, exit 0) shows Lean's getElem! out of range PANICS TO STDERR BUT RETURNS THE Inhabited DEFAULT, and decisively that the enclosing computation returns normally: `def probe (ls) : Except String Nat := do let _p := ls[ls.size+5]!; return 42` evaluates to `Except.ok 42` at both #["a","b"] and #[]. So the Lean impl's denotation on these inputs is `.ok`, and by refinement.md:314-319's own recorded rule -- "a call that raises does not refine a normal return" -- a Python program that raises is NOT a refinement of it; the try/except-to-default program is. The spec is therefore not answerable for the eager patch's failures, and on the faithful reading both attacks resolve. Recorded as a documented modelling boundary (the same disposition round C's G-PANEL-2 reached for the guarded getElem! inside relabelTargets), not a break -- but note it is a boundary the spec relies on for soundness, and it is NOT currently carried by any case in properties.py.

**REFINEMENT.MD LEG AUDIT:** 8 legs, tags I / R+A-reference / R / A-reference -- every leg is R, A-reference, or I; NO kind-3 leg, and no A-consumed row (consistent with the proof closing by case analysis + reduction, consuming no callee property).
  A-reference op 2/6 (relabelTargets == self.classes_[codes.astype(int)]): re-derived from scratch against real numpy in the base worktree -- exhaustive over table sizes 0-4 x code tuples of length 0-3 drawn from -6..6, plus 30k fuzz (sizes 0-6, codes -9..9) = 41,900 cases, 0 mismatches. Front-indexed, END-resolved negative, out-of-range on BOTH sides, and empty-table-vs-non-empty-codes are each covered -- i.e. precisely the region the old axiom_check.py fuzz missed and that broke round D. codeIndex's negative-from-the-end convention confirmed correct (#["a","b","c"][-1] -> "c", [-4] -> IndexError).
  A-reference op 3/7 (scorer partiality): confirmed in-repo -- `_PredictScorer`.`__call__` (sklearn/metrics/scorer.py:66-97) calls estimator.predict(X) then self.`_score_func`(y_true, y_pred), and the metrics reach check_consistent_length (sklearn/metrics/classification.py:35,71,177,...; sklearn/utils/validation.py:191), so a pair not describing the same samples is a ValueError, not a value. Modeling it as Except-valued is faithful.
  A-reference op 8 (shouldStop == `_should_stop`): confirmed to read only `__init__`-set self.n_iter_no_change / self.tol (gradient_boosting.py:468,476) and cannot raise, so a total List Score -> Bool is faithful.
  R op 5 (validation Option reads): confirmed X_val, y_val = None, None at gradient_boosting.py:149 and X_binned_val = None at :167, both on the validation_fraction-is-None path, with `_use_validation_data` = (validation_fraction is not None) at :133 -- so branch flag and argument presence move together, as refinement.md states.
  R op 2 (absent class-label table): confirmed self.classes_ assigned ONLY at gradient_boosting.py:1029 in the classifier's `_encode_y`; the regressor's `_encode_y` (:804-808) defines no such attribute, and a regressor does reach `_check_early_stopping_scorer`.

**VERDICT SOUND:** 11 attacks run (>=5 required), spanning partial-domain (atk_4), boundary (atk_5), control-flow-effect (atk_6, atk_10), ungrounded-oracle echo (atk_7), prior counterexamples (atk_2, atk_3), the prepatch bug (atk_1), the total-op/partial-callee hole (atk_8, atk_11) and the battery's genuine coverage gap (atk_9). Seven were rejected; the four that closed with clean axioms ALL have materialized faithful patches that RESOLVE under the official harness, each measured against a gold control certified resolved=True in the same session on the same instance. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve => no verify-not-implies-correct break found.

ADVISORY (does not change the verdict): (1) properties.py should carry atk_11 as a positive/echo case -- the scalar-getElem!-with-discarded-value shape is admissible ONLY because Lean's getElem! is denotationally total, a load-bearing fact currently recorded nowhere in the battery; if a future repair ever made a scalar index observable it would wrongly reject a resolving patch. (2) atk_9's duplicate-consult-on-a-named-pair shape is uncovered by the battery but is unrefutable by construction (scorer_ is deterministic), so it is a coverage note, not a hole. (3) Cross-role staleness observed while reading the bundle, outside this role's scope: verdict.md's G-EQ/G-PANEL-1 sections are stamped against Solution.lean sha ace276123c... while G-GOLD records 376d7086..., and this round's G-PANEL-2 section records a fail (UNFAITHFUL, 13 mismatches at isClf=true/useVal=true/xVal=none/out-of-range yVal) that this G-EQ pass does not address -- G-EQ judges verify-implies-correct, not the over-specification G-PANEL-2 raises.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`

**Machine verdict**

panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier. A `diff` block below is against that spec file, which the attack it belongs to is otherwise identical to.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,8 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1 -- the PRE-PATCH bug, re-encoded: no decode anywhere, the raw
+-- integer codes are handed to the scoring function at both sites.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,37 +293,12 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
-  let mut yT : Targets := Sum.inl yTrain
-  if isClf then
-    let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
-    yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
+  let trScore ← scorer xTrain (Sum.inl yTrain)
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
+    let xv ← readValData xVal
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
-    let mut yV : Targets := Sum.inl codes
-    if isClf then
-      let ls ← readLabels labels
-      let decoded ← relabelTargets ls codes
-      yV := Sum.inr decoded
-    let xv ← readValData xVal
-    let vlScore ← scorer xv yV
+    let vlScore ← scorer xv (Sum.inl codes)
     valScores := valScores ++ [vlScore]
     return { trainScores := trainScores, valScores := valScores,
              stop := shouldStop valScores }
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2 -- prior counterexample re-encode: the TRAINING gather is PERFORMED
+-- (bound) above the `isClf` guard on a DEFAULTED class-label table, and consumed
+-- only inside the guard. The guarded `readLabels` is left exactly where it was,
+-- so nothing absent is READ.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +295,15 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
+  let hoistedDecoded ← relabelTargets (labels.getD #[]) yTrain
   if isClf then
-    let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
-    yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
+    let _ls ← readLabels labels
+    yT := Sum.inr hoistedDecoded
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3 -- prior counterexample re-encode at the VALIDATION site: the
+-- validation gather is PERFORMED above the `useVal` guard with BOTH conditional
+-- arguments defaulted, and consumed only inside the guard.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,35 +294,20 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
+  let hoistedVal ← relabelTargets (labels.getD #[]) (yVal.getD yTrain)
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
-      let ls ← readLabels labels
-      let decoded ← relabelTargets ls codes
-      yV := Sum.inr decoded
+      let _ls ← readLabels labels
+      yV := Sum.inr hoistedVal
     let xv ← readValData xVal
     let vlScore ← scorer xv yV
     valScores := valScores ++ [vlScore]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4 -- PARTIAL-DOMAIN attack on the A-reference gather: the training
+-- decode is re-implemented with a domain NARROWED to non-negative codes, i.e. it
+-- refuses the END-resolved (negative) codes numpy answers for. Agrees with the
+-- contract's gather on every non-negative in-range code array.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +295,18 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
+    let decoded ←
+      if yTrain.all (fun c => 0 ≤ c ∧ c < (ls.size : Int)) then
+        .ok (yTrain.map (fun c => ls[c.toNat]!))
+      else .error EarlyStopError.codeOutOfRange
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5 -- BOUNDARY attack: the gather is performed against the class-label
+-- table extended by one entry, so the domain's upper edge moves out by one (a
+-- code equal to the real table size is answered instead of refused).
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +294,15 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
+    let decoded ← relabelTargets (ls.push "") yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,9 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6 -- CONTROL-FLOW-EFFECT: every recorded value is gold's and every read
+-- stays on its own branch, but the VALIDATION pair is scored BEFORE the training
+-- pair, so where the scoring function would refuse both, the wrong refusal answers.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +294,13 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
-  trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
@@ -322,9 +308,13 @@
       yV := Sum.inr decoded
     let xv ← readValData xVal
     let vlScore ← scorer xv yV
+    let trScore ← scorer xTrain yT
+    trainScores := trainScores ++ [trScore]
     valScores := valScores ++ [vlScore]
     return { trainScores := trainScores, valScores := valScores,
              stop := shouldStop valScores }
+  let trScore ← scorer xTrain yT
+  trainScores := trainScores ++ [trScore]
   return { trainScores := trainScores, valScores := valScores,
            stop := shouldStop trainScores }
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,50 +283,51 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7 -- UNGROUNDED-ORACLE ECHO: the postcondition's right-hand sides
+-- transcribed verbatim as the implementation. No imperative skeleton at all; it
+-- reads the contract back rather than refining the method.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
     (xTrain : XData) (yTrain : Array Int)
     (xVal : Option XData) (yVal : Option (Array Int))
-    (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
-  let mut trainScores := trScores
-  let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
-  let mut yT : Targets := Sum.inl yTrain
-  if isClf then
-    let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
-    let decoded ← relabelTargets ls yTrain
-    yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
-  trainScores := trainScores ++ [trScore]
-  if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
-    let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
-    let mut yV : Targets := Sum.inl codes
-    if isClf then
-      let ls ← readLabels labels
-      let decoded ← relabelTargets ls codes
-      yV := Sum.inr decoded
-    let xv ← readValData xVal
-    let vlScore ← scorer xv yV
-    valScores := valScores ++ [vlScore]
-    return { trainScores := trainScores, valScores := valScores,
-             stop := shouldStop valScores }
-  return { trainScores := trainScores, valScores := valScores,
-           stop := shouldStop trainScores }
+    (trScores vlScores : List Score) : Except EarlyStopError CheckResult :=
+  match isClf, labels, useVal, xVal, yVal with
+  | true, none, _, _, _ => Except.error EarlyStopError.absentClassLabels
+  | true, some ls, false, _, _ =>
+      (relabelTargets ls yTrain).bind
+        (fun yT => (scorer xTrain (Sum.inr yT)).map
+          (fun trScore => { trainScores := trScores ++ [trScore],
+                            valScores := vlScores,
+                            stop := shouldStop (trScores ++ [trScore]) }))
+  | true, some ls, true, some xv, some yv =>
+      (relabelTargets ls yTrain).bind
+        (fun yT => (scorer xTrain (Sum.inr yT)).bind
+          (fun trScore => (relabelTargets ls yv).bind
+            (fun yV => (scorer xv (Sum.inr yV)).map
+              (fun vlScore => { trainScores := trScores ++ [trScore],
+                                valScores := vlScores ++ [vlScore],
+                                stop := shouldStop (vlScores ++ [vlScore]) }))))
+  | true, some ls, true, _, yv =>
+      (relabelTargets ls yTrain).bind
+        (fun yT => (scorer xTrain (Sum.inr yT)).bind
+          (fun _ => (readValCodes yv).bind
+            (fun codes => (relabelTargets ls codes).bind
+              (fun _ => Except.error EarlyStopError.absentValidationData))))
+  | false, _, false, _, _ =>
+      (scorer xTrain (Sum.inl yTrain)).map
+        (fun trScore => { trainScores := trScores ++ [trScore],
+                          valScores := vlScores,
+                          stop := shouldStop (trScores ++ [trScore]) })
+  | false, _, true, some xv, some yv =>
+      (scorer xTrain (Sum.inl yTrain)).bind
+        (fun trScore => (scorer xv (Sum.inl yv)).map
+          (fun vlScore => { trainScores := trScores ++ [trScore],
+                            valScores := vlScores ++ [vlScore],
+                            stop := shouldStop (vlScores ++ [vlScore]) }))
+  | false, _, true, _, _ =>
+      (scorer xTrain (Sum.inl yTrain)).bind
+        (fun _ => Except.error EarlyStopError.absentValidationData)
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,6 +283,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 8 -- the total-op probe the fourth lane did NOT close. The fourth lane
+-- made the ARRAY gather (`relabelTargets`) partial, but a SCALAR index into the
+-- class-label table is still totalizable: `String` is `Inhabited`, so `ls[k]!`
+-- elaborates and returns `""` for an out-of-range `k` where numpy's
+-- `self.classes_[k]` RAISES `IndexError`. Here `k = yTrain.size`, which on the
+-- real classifier parametrizations (30 training samples, 2 classes) is far past
+-- the table's last entry. The value is discarded, so every recorded value is
+-- gold's and the frozen proof closes unchanged.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +299,16 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
+    let _probe : String := ls[yTrain.size]!
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,6 +283,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 9 -- the coverage gap the battery does not cover: the scoring function
+-- is consulted TWICE about the SAME pair the contract names -- both applications
+-- are CONSUMED (bound), the second answer discarded. Extensionally gold, so no
+-- clause about reads, recorded values, or named pairs can see it.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +295,15 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
-  let trScore ← scorer xTrain yT
+  let trScore ← (scorer xTrain yT).bind (fun s => (scorer xTrain yT).map (fun _ => s))
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
@@ -330,6 +319,10 @@
 -- impl-end
 
 -- proof-start
+private theorem dupcollapse {ε α : Type} (x : Except ε α) :
+    (x.bind fun s => x.map fun _ => s) = x := by
+  cases x <;> rfl
+
 theorem correct_scoreEarlyStop :
     ∀ (scorer : Scorer) (shouldStop : List Score → Bool)
       (isClf useVal : Bool) (labels : Option (Array String))
@@ -342,5 +335,6 @@
           xTrain yTrain xVal yVal trScores vlScores) := by
   intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores
   unfold problem_spec_scoreEarlyStop implementation_scoreEarlyStop
+  simp only [dupcollapse]
   cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;> rfl
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -283,6 +283,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 10 -- fine-grained ORDER attack inside the validation branch: the
+-- validation codes are read first (as the contract demands), but the DESIGN
+-- MATRIX is read BEFORE the codes are decoded, so where the codes do not decode
+-- and the matrix is absent, the matrix's absence answers instead of the decode's
+-- own refusal.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,36 +296,21 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
+    let xv ← readValData xVal
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
       let decoded ← relabelTargets ls codes
       yV := Sum.inr decoded
-    let xv ← readValData xVal
     let vlScore ← scorer xv yV
     valScores := valScores ++ [vlScore]
     return { trainScores := trainScores, valScores := valScores,
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -283,6 +283,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 11 -- the same total-op probe as attack 8 but OUTSIDE every guard and on
+-- the TRAINING CODES rather than the class-label table, so it is reached on every
+-- configuration the repository actually produces (regressor and classifier alike).
+-- `Int` is `Inhabited`, so `yTrain[yTrain.size]!` elaborates and returns `0` where
+-- numpy's `y_small_train[len(y_small_train)]` RAISES `IndexError`. The value is
+-- discarded, so every recorded value is gold's and the frozen proof closes.
 def implementation_scoreEarlyStop
     (scorer : Scorer) (shouldStop : List Score → Bool)
     (isClf useVal : Bool) (labels : Option (Array String))
@@ -291,30 +297,16 @@
     (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
   let mut trainScores := trScores
   let mut valScores := vlScores
-  -- Decode a categorical estimator's integer-coded training targets before
-  -- scoring; forward the raw targets otherwise. The class-label table is read
-  -- here and on the matching validation line, and nowhere else: those are the
-  -- only places on which the estimator is known to have one.
+  let _probe : Int := yTrain[yTrain.size]!
   let mut yT : Targets := Sum.inl yTrain
   if isClf then
     let ls ← readLabels labels
-    -- The decode is performed here, on the table just read and these codes, and a
-    -- code that table has no entry for is reported rather than stood in for.
     let decoded ← relabelTargets ls yTrain
     yT := Sum.inr decoded
-  -- The scoring function is consulted here on the training pair, and on the
-  -- matching validation line on the validation pair, and nowhere else; a refusal
-  -- of either pair is reported.
   let trScore ← scorer xTrain yT
   trainScores := trainScores ++ [trScore]
   if useVal then
-    -- The validation arguments are read here and nowhere else: this is the only
-    -- branch on which the caller created them. The target codes come first, and
-    -- are decoded, before the design matrix is touched: a code the class-label
-    -- table has no entry for is reported by the decode, whatever the design
-    -- matrix holds.
     let codes ← readValCodes yVal
-    -- Likewise decode the validation targets for a categorical estimator.
     let mut yV : Targets := Sum.inl codes
     if isClf then
       let ls ← readLabels labels
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial re-derivation, instance scikit-learn__scikit-learn-14710 (lean). 11 attacks, all same_spec=True (spec/axioms/pure/pre/post byte-identical; only the impl region and, where noted, the proof region differ).

**POSITIVE CONTROL:** pos_control.lean (byte copy of Solution.lean). `bash scripts/lean_verify.sh <f>` -> EXIT=0.
PREPATCH REPRODUCED: prepatch.lean (Solution_prepatch.lean) -> EXIT=1 with exactly 16 unclosed `rfl` goals, matching refinement.md's documented count (the sixteen isClf=true cases). G-DIFF satisfied.

atk_1  REJECTED exit 1 -- prepatch bug re-encoded (no decode; raw Sum.inl at both sites)
atk_2  REJECTED exit 1 -- prior counterexample (weak-getd-train-decode-hoisted / old atk_6): train gather PERFORMED above the isClf guard on labels.getD #[]
atk_3  REJECTED exit 1 -- prior counterexample (weak-getd-val-decode-hoisted / old atk_7): val gather performed above useVal with both args defaulted
atk_4  REJECTED exit 1 -- PARTIAL-DOMAIN: decode re-implemented with domain narrowed to non-negative codes (dodges the END-resolved side numpy answers)
atk_5  REJECTED exit 1 -- BOUNDARY: gather against (ls.push ""), moving the domain's upper edge out by one
atk_6  REJECTED exit 1 -- CONTROL-FLOW-EFFECT: validation pair scored BEFORE the training pair (records gold's values; only the refusal precedence inverts)
atk_10 REJECTED exit 1 -- fine-grained ORDER: xVal read between the val-codes read and the val decode, so the matrix's absence answers where the decode's own codeOutOfRange is demanded
atk_7  VERIFIES exit 0, #print axioms correct_scoreEarlyStop = [propext]
atk_8  VERIFIES exit 0, [propext]
atk_9  VERIFIES exit 0, [propext, Quot.sound]
atk_11 VERIFIES exit 0, [propext]
(axiom probes: {7,8,9,11}.lean, same verify command, all exit 0, clean -- no sorryAx, no Classical.choice.)

GOLD RESOLVE CONTROL (ran FIRST, one at a time on this instance -- cache_level env deletes the image on completion, so a concurrent peer 404s ImageNotFound and would take the control with it): patch_gold.diff -> resolved=True completed=True note='resolved', F2P 1/1, P2P 63/63. Image/host/oracle certified healthy, so every attack verdict below is attributable to its patch.

MANDATORY RESOLVE OF EVERY CLOSING ATTACK (harness.run_resolve, retries=1, strictly serialized; each patch `git apply --check`-ed clean in the base_commit worktree @ 4b6273b87442a4437d8b3873ea3022ae163f4fdf):
  atk_7  -> patch_atk7.diff       resolved=True  F2P 1/1  P2P 63/63. Ungrounded-oracle echo (postcondition RHS transcribed as a 7-arm match). Denotationally gold, so its faithful patch IS the gold patch (byte-compared: identical apart from the diff hunk-header context label). Correct echo; the contract is right to admit it.
  atk_9  -> patch_atk9.diff       resolved=True  F2P 1/1  P2P 63/63. THE COVERAGE GAP I set out to exploit: the scorer is consulted TWICE about the SAME pair the contract names, both applications CONSUMED, the second answer discarded. The battery has no case for this (all 22 shipped impls contain exactly 2 scorer applications; the record's atk_14 covers only a duplicate on an UNNAMED pair). It needed a proof lemma (`dupcollapse : x.bind (fun s => x.map (fun _ => s)) = x`), hence Quot.sound. Its faithful patch makes both calls for real. It RESOLVES -- scorer_ is a deterministic pure read (`estimator.predict(X)` then a metric), so a repeated consult on an identical pair is genuinely unobservable. The gap is real as a battery-coverage note but is NOT a spec weakness: no faithful refinement of it can fail.
  atk_8  -> patch_atk8_total.diff  resolved=True  F2P 1/1  P2P 63/63
  atk_11 -> patch_atk11_total.diff resolved=True  F2P 1/1  P2P 63/63

atk_8 / atk_11 ARE THE ATTACK THIS ROUND TURNED ON, and the reason the verdict is SOUND rather than BROKEN rests on a measurement, not an argument. Both probe the ONE total-Lean-op-for-partial-Python-op hole the fourth lane did NOT close: the lane made the ARRAY gather (relabelTargets) partial, but a SCALAR index is still totalizable, because String and Int are Inhabited. atk_8 evaluates `ls[yTrain.size]!` inside the isClf guard; atk_11 evaluates `yTrain[yTrain.size]!` OUTSIDE every guard, so it is reached on every configuration the repo produces (regressor and classifier alike). numpy's counterparts RAISE IndexError (measured: `y[len(y)]` -> IndexError, `classes_[3]` on a 2-entry table -> IndexError). Each value is discarded, so every recorded value is gold's and the frozen proof closes unchanged. This is exactly the shape that broke the spec in the recorded round D.

I refused to settle the faithfulness reading by argument and materialized BOTH candidate refinements of each, running all four through the oracle:
  patch_atk11_eager.diff (read PERFORMED, allowed to raise) -> resolved=False completed=True, 'consistent - not flaky'
  patch_atk8_eager.diff  (same)                            -> resolved=False completed=True, F2P 0/1, P2P 54 success / 9 FAILURE (8x test_early_stopping_classification + test_binning_train_validation_are_separated)
  patch_atk11_total.diff / patch_atk8_total.diff (read performed, returns normally with the default) -> resolved=True, F2P 1/1, P2P 63/63
The EAGER reading is the unfaithful one, and I measured why rather than asserting it. sem.lean (verify command as above, exit 0) shows Lean's getElem! out of range PANICS TO STDERR BUT RETURNS THE Inhabited DEFAULT, and decisively that the enclosing computation returns normally: `def probe (ls) : Except String Nat := do let _p := ls[ls.size+5]!; return 42` evaluates to `Except.ok 42` at both #["a","b"] and #[]. So the Lean impl's denotation on these inputs is `.ok`, and by refinement.md:314-319's own recorded rule -- "a call that raises does not refine a normal return" -- a Python program that raises is NOT a refinement of it; the try/except-to-default program is. The spec is therefore not answerable for the eager patch's failures, and on the faithful reading both attacks resolve. Recorded as a documented modelling boundary (the same disposition round C's G-PANEL-2 reached for the guarded getElem! inside relabelTargets), not a break -- but note it is a boundary the spec relies on for soundness, and it is NOT currently carried by any case in properties.py.

**REFINEMENT.MD LEG AUDIT:** 8 legs, tags I / R+A-reference / R / A-reference -- every leg is R, A-reference, or I; NO kind-3 leg, and no A-consumed row (consistent with the proof closing by case analysis + reduction, consuming no callee property).
  A-reference op 2/6 (relabelTargets == self.classes_[codes.astype(int)]): re-derived from scratch against real numpy in the base worktree -- exhaustive over table sizes 0-4 x code tuples of length 0-3 drawn from -6..6, plus 30k fuzz (sizes 0-6, codes -9..9) = 41,900 cases, 0 mismatches. Front-indexed, END-resolved negative, out-of-range on BOTH sides, and empty-table-vs-non-empty-codes are each covered -- i.e. precisely the region the old axiom_check.py fuzz missed and that broke round D. codeIndex's negative-from-the-end convention confirmed correct (#["a","b","c"][-1] -> "c", [-4] -> IndexError).
  A-reference op 3/7 (scorer partiality): confirmed in-repo -- `_PredictScorer`.`__call__` (sklearn/metrics/scorer.py:66-97) calls estimator.predict(X) then self.`_score_func`(y_true, y_pred), and the metrics reach check_consistent_length (sklearn/metrics/classification.py:35,71,177,...; sklearn/utils/validation.py:191), so a pair not describing the same samples is a ValueError, not a value. Modeling it as Except-valued is faithful.
  A-reference op 8 (shouldStop == `_should_stop`): confirmed to read only `__init__`-set self.n_iter_no_change / self.tol (gradient_boosting.py:468,476) and cannot raise, so a total List Score -> Bool is faithful.
  R op 5 (validation Option reads): confirmed X_val, y_val = None, None at gradient_boosting.py:149 and X_binned_val = None at :167, both on the validation_fraction-is-None path, with `_use_validation_data` = (validation_fraction is not None) at :133 -- so branch flag and argument presence move together, as refinement.md states.
  R op 2 (absent class-label table): confirmed self.classes_ assigned ONLY at gradient_boosting.py:1029 in the classifier's `_encode_y`; the regressor's `_encode_y` (:804-808) defines no such attribute, and a regressor does reach `_check_early_stopping_scorer`.

**VERDICT SOUND:** 11 attacks run (>=5 required), spanning partial-domain (atk_4), boundary (atk_5), control-flow-effect (atk_6, atk_10), ungrounded-oracle echo (atk_7), prior counterexamples (atk_2, atk_3), the prepatch bug (atk_1), the total-op/partial-callee hole (atk_8, atk_11) and the battery's genuine coverage gap (atk_9). Seven were rejected; the four that closed with clean axioms ALL have materialized faithful patches that RESOLVE under the official harness, each measured against a gold control certified resolved=True in the same session on the same instance. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve => no verify-not-implies-correct break found.

ADVISORY (does not change the verdict): (1) properties.py should carry atk_11 as a positive/echo case -- the scalar-getElem!-with-discarded-value shape is admissible ONLY because Lean's getElem! is denotationally total, a load-bearing fact currently recorded nowhere in the battery; if a future repair ever made a scalar index observable it would wrongly reject a resolving patch. (2) atk_9's duplicate-consult-on-a-named-pair shape is uncovered by the battery but is unrefutable by construction (scorer_ is deterministic), so it is a coverage note, not a hole. (3) Cross-role staleness observed while reading the bundle, outside this role's scope: verdict.md's G-EQ/G-PANEL-1 sections are stamped against Solution.lean sha ace276123c... while G-GOLD records 376d7086..., and this round's G-PANEL-2 section records a fail (UNFAITHFUL, 13 mismatches at isClf=true/useVal=true/xVal=none/out-of-range yVal) that this G-EQ pass does not address -- G-EQ judges verify-implies-correct, not the over-specification G-PANEL-2 raises.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on scikit-learn__scikit-learn-14710 (lean). Reference = base worktree 4b6273b + patch.diff APPLIED (verified applied cleanly; body at gradient_boosting.py:422-442 read back verbatim and used as the differential oracle). No divergence found on any reachable input; verdict FAITHFUL.

#### 1. Spec region integrity
- scripts/lean_verify.sh Solution.lean -> EXIT 0 (compiles, no sorry).
- `#print axioms correct_scoreEarlyStop` -> `[propext]`. No sorryAx; proof is real, not fake.
- markers.spec_view(Solution.lean, LeanBackend) sha256 = b04ab7bd0358caa93469d240e737fe45452324c980e44378845ebedc0720f432, == meta.json/gates/G-HYGIENE/data/region_hashes/spec_view. Spec region is byte-identical to the hygiene record.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True: axioms/pure/post-conditions hashes identical across the twins; only impl differs. So the discrimination test below exercises the SAME spec bytes.

#### 2. The spec is not vacuous / actually pins the patch delta
Solution_prepatch.lean (identical spec region, decode omitted -> scorer gets raw Sum.inl codes) FAILS verification: EXIT 1, 75 errors, unsolved goals showing `scorer xTrain (Sum.inl yTrain)` vs the required `relabelTargets`-decoded `Sum.inr`. The contract therefore genuinely rejects pre-patch behavior rather than admitting both, i.e. it is pinned to the patched (fixed) semantics -- the correct reference per the brief.

#### 3. Deep model of the changed op vs real numpy (relabelTargets)
The patch's only new value transformation is `self.classes_[y.astype(int)]`, modeled deeply (not axiomatized) as relabelTargets/codeIndex/codesIndexLabels. Differentially fuzzed against real numpy fancy indexing:
- 25,220 cases (exhaustive boundary: table size 0..4, arity 0..3, codes in [-size-2, size+2]; plus 20,000 random, seed 20240630) -> 0 divergences, in both the .ok and .error(codeOutOfRange) directions.
- Float-truncation composition (real y is Y_DTYPE float; `astype(int)` truncates toward zero): 1,852 exhaustive float cases over {+-0.0,+-0.4,+-0.5,+-0.9,+-1.0,+-1.5,+-1.9,...} -> 0 divergences. `-0.4` lands at index 0 and `-1.4` lands on the last entry in BOTH model and numpy, matching mapping.md's claim exactly.
- Negative-wrap boundary probed explicitly at c = -size-1, -size, -1, size-1, size for size in {1,3,5}: every point MATCH, including that c=-size is the FIRST entry (ok) and c=-size-1 is IndexError. codeIndex reproduces numpy's negative wrap; the model does not clamp.

#### 4. End-to-end control-flow differential (the real strength test)
I executed the patched body VERBATIM (exec'd the exact 15 lines from the patched worktree) against a transliteration of problem_spec_scoreEarlyStop, with a scorer stub that refuses length-mismatched pairs (models check_consistent_length) and returns a score tag identifying EXACTLY which (X, y) pair it was handed -- so the arguments of each scoring call, the order of reads, and the post-state histories are all observable, not just the return bool.
- Reachable domain (isClf <-> classes_ present, useVal <-> val args present): 9,450 cases -> 0 mismatches.
- Hardened re-run with a content-sensitive `_should_stop` (so history IDENTITY, not just length, must agree) plus randomized code arrays and table sizes up to 5: 299,700 cases -> 0 mismatches.
- Agreement covers post-state (train_score_ / validation_score_ contents), the returned stop bool, WHICH pair each scorer call received (Sum.inr decoded labels for classifiers, Sum.inl raw codes for regressors, on both train and val paths), and every error lane (absentClassLabels / codeOutOfRange / scoringRefused).

#### 5. Candidate defect I chased and DISMISSED
An unrestricted sweep over all 2^5 binder combinations showed 747/4400 'mismatches', all confined to the desynced states (useVal=true with xVal/yVal absent; isClf/labels desynced). Example: isClf=false, useVal=true, xVal=none -> model says absentValidationData, real code reaches `self.scorer_(self, None, None)`. I did NOT report this, because those states are unreachable at every call site, which I verified in source rather than taking mapping.md's word:
- The method is called ONLY under `if self.do_early_stopping_:` (:210 first iteration, :338 later iterations); both call sites at :236/:252 and :356.
- Validation data is created under `if self.do_early_stopping_ and self._use_validation_data:` (:134), with the else at :147-149 setting `X_val, y_val = None, None` and :167 setting `X_binned_val = None`. So GIVEN do_early_stopping_ is true (necessary for the method to run at all), useVal <-> val args present holds exactly. The do_early_stopping_=False / useVal=True skew that would desync them never reaches this method.
- `self.classes_` is assigned in exactly one place, HistGradientBoostingClassifier.`_encode_y` (:1033); the regressor's `_encode_y` defines no such attribute. So isClf <-> labels present.
These desynced points are extra admitted points that pin an unreachable disposition; they do not constrain any input the repo produces, so they are not a too-strong spec. Reporting them would have condemned a sound spec.

#### 6. Direction-of-generality check
`scorer` and `shouldStop` are universally quantified function inputs and Except-valued (partial). The real self.scorer_ is a special case of the quantified domain, so the contract is WEAKER (more general) than the real callee, never stronger -- the safe direction for faithfulness. The proof consumes no property axiom (every `_prop` slot empty), consistent with mapping.md. Error ordering claimed by the spec (val codes read+decoded before the val design matrix is touched) matches the patched source, where `y_val = self.classes_[y_val.astype(int)]` precedes `self.scorer_(self, X_binned_val, y_val)`.

#### 7. Non-faithfulness observation (not my gate, flagging only)
meta.json's TOP-LEVEL region_hashes (spec_view 12cf6c74..., and all six per-region hashes) do not match either Solution.lean or Solution_prepatch.lean under markers.region_hashes/LeanBackend, while the G-HYGIENE nested record (b04ab7bd...) matches Solution.lean exactly. Likely a stale or differently-normalized bookkeeping record. This is a ledger/hygiene question, not a spec-faithfulness defect, and I did not treat it as one; worth a hygiene-gate look.

**Conclusion:** no input exists on which the modeled function disagrees with the patched real callee. The spec is faithful and non-vacuous (rejects the pre-patch twin on identical spec bytes).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction over the spec view of scikit-learn__scikit-learn-14710 (lean), re-derived from scratch against the bytes on disk NOW (Solution.lean sha256 376d70864d4fd54b..., which equals the sha recorded by G-VERIFY, G-LEAK, G-HYGIENE and G-INTEGRITY, so I judged the same bytes those gates did; G-EQ records ace276123cad18b8..., i.e. G-EQ is stale w.r.t. current bytes -- see caveats).

NO RELAXATION PRESENT -- checked, not inherited: `'relaxed_leakage' in meta` -> False (meta top-level keys are exactly [axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins]); `find . -iname '*relax*'` over the whole instance dir returns nothing -- there is no RELAXED_LEAKAGE.md. The only 'relax' strings anywhere in meta.json are inside the PRIOR G-PANEL-3 role's own retained note. So this is an ordinary unrelaxed leakage judgement, and I did not inherit any disposition.

#### WHAT I MEASURED (all re-run by me, not read off a record):
1. Spec view extracted with the real harness: `markers.spec_view(src, get_backend('lean'))` -> 291 lines, sha256 b04ab7bd0358caa9... Regions in view: docstring + axioms + pure + post-conditions; impl and proof elided ('-- implementation elided', '-- proof elided'). I read all 291 lines.
2. Spec region byte-identity: `markers.same_spec(Solution.lean, Solution_prepatch.lean, lean)` = True; per-region, gold and prepatch agree on axioms (61ac52df), pure (6e1a5447), post-conditions (ff594e1f), proof (c0cea546) and spec_view (b04ab7bd) and differ ONLY in impl (a61e38a1 vs 6d2d78c8). So the spec view is exactly the pre/post-shared surface.
3. Mechanical screen re-run: `leakage.screen(src, lean_backend, instance.patch, instance.problem_statement, instance.test_patch)` -> passed=True, hard_failures=[], warnings=[]. instance.json patch == patch.diff byte-for-byte and meta.patch_equals_gold is True, so the screen ran against the real gold edit. Judged against problem_statement only; hints_text is 26 bytes ('ping @NicolasHug @ogrisel') and contributes nothing either way.
4. Manual (non-mechanical) reconstruction check on the view text. None of the repo-side tokens appear anywhere in the spec view: classes_, is_classifier, astype, scorer_, train_score_, validation_score_, `_should_stop`, y_small_train, X_binned, sklearn, gradient_boosting, numpy, np., IndexError, AttributeError, ValueError. No diff marker, no patched path (sklearn/ensemble/`_hist_gradient_boosting`/gradient_boosting.py) and no dotted module form. No fix/bug/previously/now-narration (grep for the full `_NARRATION` set found only 'stopping'/'history'/'extended' word hits, i.e. the domain vocabulary, no narration match). The one patch-changed symbol the harness extracts, `check_early_stopping_scorer`, is already public in the problem_statement, and does not appear in the view anyway.
5. Substantive leakage question -- is the view's discriminating content a SUBSET of the public problem_statement? Yes, and comfortably so. The problem_statement states the defect in its own words ('The scorer ... is provided with y_true being integer while y_pred are original classes (i.e. string). We need to encode y_true each time that we want to compute the score') AND publishes a candidate diff, in a '#### Potential resolution' section, that is the gold edit up to the guard spelling: it inserts `y_small_train = self.classes_[y_small_train.astype(int)]` before the train scoring call and `y_val = self.classes_[y_val.astype(int)]` before the validation scoring call, each under a classifier guard (`hasattr(self, 'classes_')` publicly vs `is_classifier(self)` in gold -- co-extensional, since classes_ is assigned in exactly one place, HistGradientBoostingClassifier.`_encode_y`). Everything the spec view's docstring pins -- decode direction (integer codes -> original class labels), the table it decodes through, BOTH call sites (train and validation), the classifier-only guard, the validation-only guard, and the y-before-X order at the validation site (the public diff's y_val line sits above the scorer_(self, X_binned_val, y_val) call) -- is therefore derivable from the problem_statement alone. The model's extra precision (codeIndex negative wrap, codesIndexLabels domain, codeOutOfRange) is the semantics of `classes_[y.astype(int)]`, i.e. of an operation the problem_statement itself spells out, not an edit disclosure; the Except-valued scorer and readVal* readers are observability instruments for argument/order, not statements about what changed.
6. Load-bearing control (the strip-the-narration test, run even though no relaxation claims it): the discriminating clauses are not decorative narration -- Solution_prepatch.lean, which forwards both target arrays as raw Sum.inl codes with no decode and carries the gold proof unchanged, FAILS against this byte-identical spec view: lean_verify.sh exit 1 with unclosed `rfl` goals, all in isClf=true cases where the postcondition demands `Sum.inr <$> relabelTargets ls ...`. So the spec verifies the gold impl and rejects the pre-patch impl on exactly the facet the problem_statement already publishes.
7. Gates my verdict leans on, re-run rather than trusted: lean_verify.sh Solution.lean -> exit 0, no sorry; `#print axioms correct_scoreEarlyStop` (appended in a private /tmp probe) -> depends on axioms: [propext] only -- no sorryAx, so the proof is real and the spec is not vacuously satisfiable. G-LEAK's recorded source sha equals the bytes I screened, and I re-ran the screen anyway.

**BUNDLE-ADDRESSES-THE-ROLE CHECK:** `leakage.reviewer_directed()` over mapping.md, refinement.md, verdict.md, meta.json, conformance_check.py and axiom_check.py returns [] for every file, and my own greps for 'honest verdict' / 'should record' / 'must submit' / 'do not report' / NO-LEAKAGE / LEAKAGE / panel_3 / auditor / attacker found only (a) retained attack labels, (b) the prior G-PANEL-3 role's note echoed into meta.json and verdict.md, and (c) ordinary prose uses ('keeps the clause honest' about a bind site). Nothing in the bundle instructs me how to record or which verdict is honest -- no finding on that axis.

#### CAVEATS (recorded, none of which my leakage verdict rests on):
* meta.region_hashes are STALE against current bytes: meta says spec_view 12cf6c74b5c8e630..., I measure b04ab7bd0358caa9... (and every per-region hash differs). The retained prior G-PANEL-3 note asserts both that the source sha is ace276123cad18b8... and that region_hashes match on every spec region; both are false against the bytes on disk, so that note was measured on a different Solution.lean. I relied on none of it -- every number above is my own measurement. This is a freshness/hygiene defect in the ledger, not a leakage defect in the spec view.
* G-EQ's recorded source sha (ace2761...) likewise predates the current bytes; G-PANEL-2 currently stands at fail (a faithfulness rival). Both are outside this facet: a faithfulness gap makes the spec say something the repo does not, which is not the same as the spec revealing the edit, and neither changes the subset relation in (5).

**VERDICT:** NO-LEAKAGE. The spec view reveals nothing about the gold edit that the public problem_statement -- which itself contains a near-verbatim candidate for that edit -- does not already hand the solver, and it carries no repo identifier, path, diff artifact or fix narration.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
