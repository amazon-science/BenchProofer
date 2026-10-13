# P2 adversarial audit — sphinx-doc__sphinx-9673

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_0_prepatch.lean`, `atk_2_boundary.lean`, `atk_3_order.lean`, `atk_4_partial.lean`, `atk_5_half.lean`, `atk_6_param.lean`, `atk_7_rtype.lean`, `atk_8_vacuous.lean`, `atk_9_overemit.lean`, `atk_10_revorder.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
fields = [["param","x"], ["returns"]], annotations = [("x","int"), ("return","str")] — the F2P shape. Frozen spec buildFields = [Field.typeOf "x" "int", Field.rtype "str"]; the prepatch skeleton (short-token-only classify + short-token-only emit skip) yields [Field.typeOf "x" "int"], missing the trailing rtype field. Confirmed against the live docutils oracle: patched = [('type x','int'),('rtype','str')], prepatch = [('type x','int')]. atk_0_prepatch.lean encodes this and FAILS to verify (exit 1), so the spec does discriminate the bug. The sharpest same-spec attack, atk_5_half (gold hunk 1 applied but hunk 2 NOT — emit-side skip tests only the short token), is separated by fields=[["param","returns"]], annotations=[("returns","int")]: spec emits [] while the half-widened impl emits [Field.typeOf "returns" "int"]; it also FAILS to verify (exit 1), so the spec pins BOTH widenings independently.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -169,25 +169,52 @@
   ensures out = buildFields fields annotations
   do
     -- impl-start
+    -- Pre-image skeleton: the field classifier recognizes ONLY the short result
+    -- token and the back-fill skip tests ONLY the short token, so a result
+    -- documented under the plural spelling is NOT counted as described. The
+    -- frozen spec (buildFields, via classifyField/emitStep, accepts BOTH
+    -- spellings), so prove_correct MUST fail.
+    let classifyBuggy : List Tok → Sets → Sets := fun parts st =>
+      match parts with
+      | [] => st
+      | p0 :: rest =>
+        if p0 == paramTok then
+          match rest with
+          | []           => st
+          | [x]          => addDesc st x
+          | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm
+        else if p0 == typeTok then
+          addType st (joinSp rest)
+        else if p0 == returnTok then
+          addDesc st returnKey
+        else if p0 == rtypeTok then
+          addType st returnKey
+        else st
+    let emitBuggy : Sets → List Field → (Tok × Tok) → List Field := fun st acc na =>
+      let name := na.1
+      if name == returnTok then acc
+      else if st.hasDesc.contains name && !(st.hasType.contains name) then
+        acc ++ [Field.typeOf name na.2]
+      else acc
     let mut s : Sets := emptySets
     let mut i := 0
     while i < fields.length
       invariant i ≤ fields.length
-      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
+      invariant s = (fields.take i).foldl (fun acc f => classifyBuggy f acc) emptySets
       done_with i = fields.length
       decreasing fields.length - i
     do
-      s := classifyField fields[i]! s
+      s := classifyBuggy fields[i]! s
       i := i + 1
     let mut result : List Field := []
     let mut j := 0
     while j < annotations.length
       invariant j ≤ annotations.length
-      invariant result = (annotations.take j).foldl (emitStep s) []
+      invariant result = (annotations.take j).foldl (emitBuggy s) []
       done_with j = annotations.length
       decreasing annotations.length - j
     do
-      result := emitStep s result annotations[j]!
+      result := emitBuggy s result annotations[j]!
       j := j + 1
     return result ++ rtypeField s annotations
     -- impl-end
```

Attack 2 — `atk_1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -169,38 +169,9 @@
   ensures out = buildFields fields annotations
   do
     -- impl-start
-    let mut s : Sets := emptySets
-    let mut i := 0
-    while i < fields.length
-      invariant i ≤ fields.length
-      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
-      done_with i = fields.length
-      decreasing fields.length - i
-    do
-      s := classifyField fields[i]! s
-      i := i + 1
-    let mut result : List Field := []
-    let mut j := 0
-    while j < annotations.length
-      invariant j ≤ annotations.length
-      invariant result = (annotations.take j).foldl (emitStep s) []
-      done_with j = annotations.length
-      decreasing annotations.length - j
-    do
-      result := emitStep s result annotations[j]!
-      j := j + 1
-    return result ++ rtypeField s annotations
+    return buildFields fields annotations
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
   all_goals simp_all [buildFields, classifyFields]
```

Attack 3 — `atk_2_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -171,10 +171,10 @@
     -- impl-start
     let mut s : Sets := emptySets
     let mut i := 0
-    while i < fields.length
+    while i + 1 < fields.length
       invariant i ≤ fields.length
       invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
-      done_with i = fields.length
+      done_with i + 1 = fields.length
       decreasing fields.length - i
     do
       s := classifyField fields[i]! s
@@ -194,13 +194,16 @@
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 4 — `atk_3_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -189,18 +189,21 @@
     do
       result := emitStep s result annotations[j]!
       j := j + 1
-    return result ++ rtypeField s annotations
+    return rtypeField s annotations ++ result
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 5 — `atk_4_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -189,18 +189,21 @@
     do
       result := emitStep s result annotations[j]!
       j := j + 1
-    return result ++ rtypeField s annotations
+    return result.take 1 ++ rtypeField s annotations
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 6 — `atk_5_half.lean` → rejected (same spec, does not verify — good)

```diff
@@ -169,6 +169,12 @@
   ensures out = buildFields fields annotations
   do
     -- impl-start
+    let emitHalf : Sets → List Field → (Tok × Tok) → List Field := fun st acc na =>
+      let name := na.1
+      if name == returnTok then acc
+      else if st.hasDesc.contains name && !(st.hasType.contains name) then
+        acc ++ [Field.typeOf name na.2]
+      else acc
     let mut s : Sets := emptySets
     let mut i := 0
     while i < fields.length
@@ -183,24 +189,27 @@
     let mut j := 0
     while j < annotations.length
       invariant j ≤ annotations.length
-      invariant result = (annotations.take j).foldl (emitStep s) []
+      invariant result = (annotations.take j).foldl (emitHalf s) []
       done_with j = annotations.length
       decreasing annotations.length - j
     do
-      result := emitStep s result annotations[j]!
+      result := emitHalf s result annotations[j]!
       j := j + 1
     return result ++ rtypeField s annotations
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 7 — `atk_6_param.lean` → rejected (same spec, does not verify — good)

```diff
@@ -169,15 +169,31 @@
   ensures out = buildFields fields annotations
   do
     -- impl-start
+    let classifyBad : List Tok → Sets → Sets := fun parts st =>
+      match parts with
+      | [] => st
+      | p0 :: rest =>
+        if p0 == paramTok then
+          match rest with
+          | []           => st
+          | [x]          => addType (addDesc st x) x
+          | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm
+        else if p0 == typeTok then
+          addType st (joinSp rest)
+        else if p0 == returnTok || p0 == returnsTok then
+          addDesc st returnKey
+        else if p0 == rtypeTok then
+          addType st returnKey
+        else st
     let mut s : Sets := emptySets
     let mut i := 0
     while i < fields.length
       invariant i ≤ fields.length
-      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
+      invariant s = (fields.take i).foldl (fun acc f => classifyBad f acc) emptySets
       done_with i = fields.length
       decreasing fields.length - i
     do
-      s := classifyField fields[i]! s
+      s := classifyBad fields[i]! s
       i := i + 1
     let mut result : List Field := []
     let mut j := 0
@@ -194,13 +210,16 @@
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 8 — `atk_7_rtype.lean` → rejected (same spec, does not verify — good)

```diff
@@ -189,18 +189,26 @@
     do
       result := emitStep s result annotations[j]!
       j := j + 1
-    return result ++ rtypeField s annotations
+    let extra : List Field :=
+      if annotations.any (fun na => na.1 == returnKey)
+           && s.hasDesc.contains returnKey && !(s.hasType.contains returnKey) then
+        [Field.rtype (annotations.headD ([], [])).2]
+      else []
+    return result ++ extra
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 9 — `atk_8_vacuous.lean` → rejected (same spec, does not verify — good)

```diff
@@ -171,9 +171,8 @@
     -- impl-start
     let mut s : Sets := emptySets
     let mut i := 0
-    while i < fields.length
+    while i < 0
       invariant i ≤ fields.length
-      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
       done_with i = fields.length
       decreasing fields.length - i
     do
@@ -194,13 +193,16 @@
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 10 — `atk_9_overemit.lean` → rejected (same spec, does not verify — good)

```diff
@@ -189,18 +189,25 @@
     do
       result := emitStep s result annotations[j]!
       j := j + 1
-    return result ++ rtypeField s annotations
+    let extra : List Field :=
+      if annotations.any (fun na => na.1 == returnKey) && s.hasDesc.contains returnKey then
+        [Field.rtype (lookupReturn annotations)]
+      else []
+    return result ++ extra
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

Attack 11 — `atk_10_revorder.lean` → rejected (same spec, does not verify — good)

```diff
@@ -179,28 +179,32 @@
     do
       s := classifyField fields[i]! s
       i := i + 1
+    let rev := annotations.reverse
     let mut result : List Field := []
     let mut j := 0
-    while j < annotations.length
-      invariant j ≤ annotations.length
-      invariant result = (annotations.take j).foldl (emitStep s) []
-      done_with j = annotations.length
-      decreasing annotations.length - j
+    while j < rev.length
+      invariant j ≤ rev.length
+      invariant result = (rev.take j).foldl (emitStep s) []
+      done_with j = rev.length
+      decreasing rev.length - j
     do
-      result := emitStep s result annotations[j]!
+      result := emitStep s result rev[j]!
       j := j + 1
     return result ++ rtypeField s annotations
     -- impl-end
 
 prove_correct augmentTypeFields by
   loom_solve
-  case _ =>
-    have hi : i < fields.length := by omega
-    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-    simp_all
-  case _ =>
-    have hj : j < annotations.length := by omega
-    rw [foldlTakeStep (emitStep _) [] annotations j hj]
-    simp_all
-  all_goals simp_all [buildFields, classifyFields]
+  all_goals (try (first
+    | (have hi : i < fields.length := by omega
+       rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
+           List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
+       simp_all)
+    | (have hj : j < annotations.length := by omega
+       rw [foldlTakeStep (emitStep _) [] annotations j hj]
+       simp_all)))
+  all_goals simp_all [buildFields, classifyFields, rtypeField, emitStep,
+                      classifyField, lookupReturn, joinSp]
+  all_goals (try omega)
+  all_goals (try decide)
+  all_goals (try rfl)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   This operation reclassifies the leading token of each existing info-field name
   and then synthesizes new fields from the recorded type annotations. Every step
   is a concrete, pure structural transform over the field names and the
   annotation table; nothing is deferred to an unchanged callee defined elsewhere
   whose behavior the specification would have to assume. Hence there is no consumed
   axiom and no deep-model reference to validate, and G-AX is vacuous
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A field-name token, or an annotation key — a character sequence. Only equality
   and membership are ever observed. -/
abbrev Tok := List Char

/- The distinguished field tokens this operation recognizes. A description field
   for the function result may be spelled with EITHER the short return token or
   its plural synonym; both denote the same result-description key `returnKey`. A
   declared result type is spelled `rtype`; a parameter description/type is
   spelled `param`/`type`. -/
def paramTok   : Tok := "param".toList
def typeTok    : Tok := "type".toList
def returnTok  : Tok := "return".toList
def returnsTok : Tok := "returns".toList
def rtypeTok   : Tok := "rtype".toList

/- The canonical key under which a result description/type is recorded. Both
   accepted spellings of a result-description field collapse onto this single
   key. -/
def returnKey : Tok := "return".toList

/- Join a tail of field-name tokens back into one space-separated name (the
   inverse of splitting a field name on runs of spaces). -/
def joinSp (ts : List Tok) : Tok := List.intercalate [' '] ts

/- The two membership sets accumulated while scanning the existing fields:
   `hasDesc` — keys that already carry a description; `hasType` — keys that
   already carry a declared type. -/
structure Sets where
  hasDesc : List Tok
  hasType : List Tok
  deriving DecidableEq, Inhabited, Repr

def emptySets : Sets := ⟨[], []⟩

def addDesc (s : Sets) (t : Tok) : Sets := { s with hasDesc := s.hasDesc ++ [t] }
def addType (s : Sets) (t : Tok) : Sets := { s with hasType := s.hasType ++ [t] }

/- Classify one existing field, given as the tokens of its name split on spaces,
   updating the description/type sets:

   * a `param` field with exactly one trailing token records a description for
     that parameter; a `param` field with more trailing tokens (an inline-typed
     parameter) records BOTH a description and a type for the joined remainder;
   * a `type` field records a declared type for the joined remainder;
   * a result-description field — recognized under EITHER the short return token
     OR its plural synonym — records a description for the result key;
   * an `rtype` field records a declared type for the result key;
   * any other field is ignored.

   The result-description clause accepting both spellings is the behavior of
   interest: a result documented under the plural spelling must still count as a
   described result (mapping.md §3.1). -/
def classifyField (parts : List Tok) (s : Sets) : Sets :=
  match parts with
  | [] => s
  | p0 :: rest =>
    if p0 == paramTok then
      match rest with
      | []           => s
      | [x]          => addDesc s x
      | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc s nm) nm
    else if p0 == typeTok then
      addType s (joinSp rest)
    else if p0 == returnTok || p0 == returnsTok then
      addDesc s returnKey
    else if p0 == rtypeTok then
      addType s returnKey
    else s

/- Scan all existing fields left to right, accumulating the description/type
   sets. -/
def classifyFields (fields : List (List Tok)) : Sets :=
  fields.foldl (fun acc f => classifyField f acc) emptySets

/- A newly synthesized field appended to the field list:
   * `typeOf name body` — a declared type for a parameter (`type <name>`);
   * `rtype body`        — a declared type for the result (`rtype`). -/
inductive Field where
  | typeOf (name : Tok) (body : Tok)
  | rtype  (body : Tok)
  deriving DecidableEq, Inhabited, Repr

/- Emit a parameter-type field for one annotation entry, when warranted: the
   result key (under EITHER spelling) is skipped here (its type is handled
   separately); any other annotated name that already carries a description but
   no declared type gets a fresh `type` field carrying its annotation. -/
def emitStep (s : Sets) (acc : List Field) (na : Tok × Tok) : List Field :=
  let name := na.1
  if name == returnTok || name == returnsTok then acc
  else if s.hasDesc.contains name && !(s.hasType.contains name) then
    acc ++ [Field.typeOf name na.2]
  else acc

/- Look up the result-type annotation by the canonical result key. -/
def lookupReturn : List (Tok × Tok) → Tok
  | []            => []
  | (k, v) :: rest => if k == returnKey then v else lookupReturn rest

/- The trailing result-type field, emitted exactly when the result is annotated,
   already has a recorded description, and has no declared type yet. -/
def rtypeField (s : Sets) (annotations : List (Tok × Tok)) : List Field :=
  if annotations.any (fun na => na.1 == returnKey)
       && s.hasDesc.contains returnKey && !(s.hasType.contains returnKey) then
    [Field.rtype (lookupReturn annotations)]
  else []

/- The full sequence of fields appended by the operation: first the
   parameter-type fields synthesized from the annotation table in order, then the
   optional trailing result-type field. -/
def buildFields (fields : List (List Tok)) (annotations : List (Tok × Tok)) : List Field :=
  let s := classifyFields fields
  (annotations.foldl (emitStep s) []) ++ rtypeField s annotations

/- Forward-fold step: extending the consumed prefix by one element advances the
   left fold built from the shorter prefix by exactly that element. One generic
   drop-step shared by both loops (the Velvet fold pattern). -/
lemma foldlTakeStep {S A : Type} [Inhabited A] (f : S → A → S) (s0 : S) (xs : List A)
    (i : Nat) (hi : i < xs.length) :
    (xs.take (i + 1)).foldl f s0 = f ((xs.take i).foldl f s0) xs[i]! := by
  have hcons : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Augment a documented entity's info-field list with the type fields implied by
   its recorded annotations.

   First every existing field is classified by the leading token of its name,
   recording which parameter/result keys already carry a description and which
   already carry a declared type. A result documented under EITHER accepted
   spelling of the result-description field counts as a described result. Then,
   for each annotation in order, a parameter that has a description but no
   declared type gains a `type` field; finally, if the result is annotated and
   has a description but no declared type, a trailing result-type field is
   appended.

   `fields` and `annotations` are read-only (not `mut`): the operation reads them
   and builds a fresh field list, mutating neither (directive 5). -/
method augmentTypeFields (fields : List (List Tok)) (annotations : List (Tok × Tok))
    return (out : List Field)
  ensures out = buildFields fields annotations
  do
    -- impl-start
    let mut s : Sets := emptySets
    let mut i := 0
    while i < fields.length
      invariant i ≤ fields.length
      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
      done_with i = fields.length
      decreasing fields.length - i
    do
      s := classifyField fields[i]! s
      i := i + 1
    let mut result : List Field := []
    let mut j := 0
    while j < annotations.length
      invariant j ≤ annotations.length
      invariant result = (annotations.take j).foldl (emitStep s) []
      done_with j = annotations.length
      decreasing annotations.length - j
    do
      result := emitStep s result annotations[j]!
      j := j + 1
    return result ++ rtypeField s annotations
    -- impl-end

prove_correct augmentTypeFields by
  loom_solve
  case _ =>
    have hi : i < fields.length := by omega
    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp_all
  case _ =>
    have hj : j < annotations.length := by omega
    rw [foldlTakeStep (emitStep _) [] annotations j hj]
    simp_all
  all_goals simp_all [buildFields, classifyFields]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED — all commands run from /home. Every attack file is byte-identical to Solution.lean outside the impl region; same_spec=True verified for all 10 generated attacks (generator: gen_attacks.py; command: `python -c "from swebench_unified.markers import same_spec; ..."` per the prompt, batched in the generator).

CONTROLS. positive control `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0 (verifies). prepatch `.../atk_0_prepatch.lean` -> EXIT=1 (G-DIFF reproduced, prepatch_reproduced=true).

ATTACKS (each `bash scripts/lean_verify.sh <path>`, run 4-at-a-time as background jobs; .out file per attack holds full output + EXIT): atk_1_echo        ungrounded-oracle echo (`return buildFields fields annotations`)          -> EXIT=0 VERIFIES atk_2_boundary    first loop stops one field early (`i+1 < fields.length`)                  -> EXIT=1 atk_3_order       trailing rtype PREPENDED instead of appended (sequence order)              -> EXIT=1 atk_4_partial     partial domain: `result.take 1` — drops all but first synthesized type     -> EXIT=1 atk_5_half        HALF-WIDENING: classify widened, emit-skip short-token-only (hunk2 absent) -> EXIT=1 atk_6_param       mis-modeled `:param xxx:` also records a declared TYPE (suppresses emit)   -> EXIT=1 atk_7_rtype       rtype body = FIRST annotation's value, not the one under the result key    -> EXIT=1 atk_8_vacuous     control-flow-effect: classification loop guard `i < 0` (never executes)    -> EXIT=1 atk_9_overemit    drops the hasType guard on the trailing rtype field (over-emits)           -> EXIT=1 atk_10_revorder   annotation loop consumes the table in REVERSE order                        -> EXIT=1 Each was given a deliberately maximally-permissive proof block (first-combinator over both fold-step tactics, then simp_all over every spec helper, omega/decide/rfl) so a failure is semantic, not proof-engineering weakness.

I additionally re-derived all 9 wrong impls in Python and confirmed each is GENUINELY extensionally distinct from buildFields on an exhibited witness (printed spec-vs-wrong outputs), so the 9 rejections are correct rejections rather than tactic failures.

MANDATORY RESOLVE OF THE VERIFYING IMPL. atk_1_echo is the only attack that verifies, and it verifies because it is extensionally the spec — so its faithful refined patch is the Python transliteration of the frozen spec's OWN helpers (classifyField/emitStep/rtypeField/lookupReturn/joinSp) under mapping.md §2, deliberately NOT a copy of the gold hunk (materializer: .../make_patch_atk1.py, patch: .../atk_1_echo.patch). Executed: `run_resolve('sphinx-doc__sphinx-9673', atk_1_echo.patch, timeout=1800)` -> RESOLVED=True, COMPLETED=True, F2P success=['test_autodoc_typehints_description_no_undoc'], failure=[]; P2P 24/24 success, 0 failure; PASS_TO_FAIL empty (note: 'resolved on attempt 2/2', flaky first attempt = infra, second attempt clean; full report in .../resolve_atk1.log). Because the spec's own transliteration resolves, the verify=>resolve implication survives its strongest test: there is no verifying-but-nonresolving witness.

REFINEMENT-FIDELITY MODEL CHECK (the real G-EQ risk here, since verification is exact functional equality to buildFields — the only way to break it is for buildFields itself to mis-model the patched function). Differential fuzz .../fuzz_model.py runs the frozen spec model against the REAL gold-patched augment_descriptions_with_types on live docutils field_list nodes (docutils 0.23 extracted into .../deps): exhaustive sweep over 0-2 existing fields x 0-2 annotations drawn from a token pool that deliberately includes 'return'/'returns'/'rtype'/'param'/'type' and multi-word names, plus 60k random deep cases (seed 20260813, up to 4 fields x 3 tokens, 3 annotations). Result: checks=86694 mismatches=0. The F2P shape and the prepatch discrimination are reproduced exactly (see counterexample). Duplicate-key annotation tables are canonicalized per mapping.md §4 before comparison — I checked this is legitimate domain restriction, not concealment: a Python Dict[str,str] cannot serialize to a repeated-key pair-list, and on unique-key tables canon is the identity.

REFINEMENT.MD AUDIT (§3 of protocol). 4 legs, tags: A1=R, A2=I+R, A3=I+R, A4=I. No kind-3 (inexpressible-changed-op) leg — the changed operation (two literal-membership widenings) is modeled CONCRETELY in classifyField (`p0 == returnTok || p0 == returnsTok`) and emitStep (`name == returnTok || name == returnsTok`), not deferred behind any abstraction. A-LEGS: none, and I confirmed this is structurally true rather than merely asserted — `grep -nE '^\s*axiom |^\s*opaque |sorry|native_decide|@\[extern'` over Solution.lean matches only the word 'axiom' inside the axioms-region PROSE comment; there is no axiom/opaque/sorry/native_decide/extern declaration anywhere. So G-AX is genuinely vacuous, the mapping.md §3 'no callee provenance' claim is correct (the function calls only re.split, str.join, set.add/in and docutils node constructors, all modeled concretely by pure-region helpers), and there is no A-correspondence left to falsify. patch.diff confirmed byte-identical to instance.json['patch'] (G-RESOLVE).

VERDICT SOUND. 10 same-spec attacks run (9 semantically-wrong, all rejected with exhibited distinguishing witnesses; 1 oracle-echo, which verifies and whose faithful patch RESOLVES under the official harness). Positive control verifies, prepatch fails, gold resolves, and the spec model agrees with the real patched function on 86,694 differential inputs including both widening-sensitive shapes. No verify=>correct break found. Residual trust point is exactly the one refinement.md declares: refinement fidelity of the R/I transliteration, which I independently stress-tested above rather than taking on faith. Caveat recorded for the runner: the atk_1 resolve needed 2 attempts (first attempt infra-flaky), so re-runs should allow retries.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_0_prepatch.lean`, `atk_2_boundary.lean`, `atk_3_order.lean`, `atk_4_partial.lean`, `atk_5_half.lean`, `atk_6_param.lean`, `atk_7_rtype.lean`, `atk_8_vacuous.lean`, `atk_9_overemit.lean`, `atk_10_revorder.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
fields = [["param","x"], ["returns"]], annotations = [("x","int"), ("return","str")] — the F2P shape. Frozen spec buildFields = [Field.typeOf "x" "int", Field.rtype "str"]; the prepatch skeleton (short-token-only classify + short-token-only emit skip) yields [Field.typeOf "x" "int"], missing the trailing rtype field. Confirmed against the live docutils oracle: patched = [('type x','int'),('rtype','str')], prepatch = [('type x','int')]. atk_0_prepatch.lean encodes this and FAILS to verify (exit 1), so the spec does discriminate the bug. The sharpest same-spec attack, atk_5_half (gold hunk 1 applied but hunk 2 NOT — emit-side skip tests only the short token), is separated by fields=[["param","returns"]], annotations=[("returns","int")]: spec emits [] while the half-widened impl emits [Field.typeOf "returns" "int"]; it also FAILS to verify (exit 1), so the spec pins BOTH widenings independently.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_2_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_order.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_partial.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_half.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_param.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_rtype.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8_vacuous.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_overemit.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_revorder.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   This operation reclassifies the leading token of each existing info-field name
   and then synthesizes new fields from the recorded type annotations. Every step
   is a concrete, pure structural transform over the field names and the
   annotation table; nothing is deferred to an unchanged callee defined elsewhere
   whose behavior the specification would have to assume. Hence there is no consumed
   axiom and no deep-model reference to validate, and G-AX is vacuous
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A field-name token, or an annotation key — a character sequence. Only equality
   and membership are ever observed. -/
abbrev Tok := List Char

/- The distinguished field tokens this operation recognizes. A description field
   for the function result may be spelled with EITHER the short return token or
   its plural synonym; both denote the same result-description key `returnKey`. A
   declared result type is spelled `rtype`; a parameter description/type is
   spelled `param`/`type`. -/
def paramTok   : Tok := "param".toList
def typeTok    : Tok := "type".toList
def returnTok  : Tok := "return".toList
def returnsTok : Tok := "returns".toList
def rtypeTok   : Tok := "rtype".toList

/- The canonical key under which a result description/type is recorded. Both
   accepted spellings of a result-description field collapse onto this single
   key. -/
def returnKey : Tok := "return".toList

/- Join a tail of field-name tokens back into one space-separated name (the
   inverse of splitting a field name on runs of spaces). -/
def joinSp (ts : List Tok) : Tok := List.intercalate [' '] ts

/- The two membership sets accumulated while scanning the existing fields:
   `hasDesc` — keys that already carry a description; `hasType` — keys that
   already carry a declared type. -/
structure Sets where
  hasDesc : List Tok
  hasType : List Tok
  deriving DecidableEq, Inhabited, Repr

def emptySets : Sets := ⟨[], []⟩

def addDesc (s : Sets) (t : Tok) : Sets := { s with hasDesc := s.hasDesc ++ [t] }
def addType (s : Sets) (t : Tok) : Sets := { s with hasType := s.hasType ++ [t] }

/- Classify one existing field, given as the tokens of its name split on spaces,
   updating the description/type sets:

   * a `param` field with exactly one trailing token records a description for
     that parameter; a `param` field with more trailing tokens (an inline-typed
     parameter) records BOTH a description and a type for the joined remainder;
   * a `type` field records a declared type for the joined remainder;
   * a result-description field — recognized under EITHER the short return token
     OR its plural synonym — records a description for the result key;
   * an `rtype` field records a declared type for the result key;
   * any other field is ignored.

   The result-description clause accepting both spellings is the behavior of
   interest: a result documented under the plural spelling must still count as a
   described result (mapping.md §3.1). -/
def classifyField (parts : List Tok) (s : Sets) : Sets :=
  match parts with
  | [] => s
  | p0 :: rest =>
    if p0 == paramTok then
      match rest with
      | []           => s
      | [x]          => addDesc s x
      | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc s nm) nm
    else if p0 == typeTok then
      addType s (joinSp rest)
    else if p0 == returnTok || p0 == returnsTok then
      addDesc s returnKey
    else if p0 == rtypeTok then
      addType s returnKey
    else s

/- Scan all existing fields left to right, accumulating the description/type
   sets. -/
def classifyFields (fields : List (List Tok)) : Sets :=
  fields.foldl (fun acc f => classifyField f acc) emptySets

/- A newly synthesized field appended to the field list:
   * `typeOf name body` — a declared type for a parameter (`type <name>`);
   * `rtype body`        — a declared type for the result (`rtype`). -/
inductive Field where
  | typeOf (name : Tok) (body : Tok)
  | rtype  (body : Tok)
  deriving DecidableEq, Inhabited, Repr

/- Emit a parameter-type field for one annotation entry, when warranted: the
   result key (under EITHER spelling) is skipped here (its type is handled
   separately); any other annotated name that already carries a description but
   no declared type gets a fresh `type` field carrying its annotation. -/
def emitStep (s : Sets) (acc : List Field) (na : Tok × Tok) : List Field :=
  let name := na.1
  if name == returnTok || name == returnsTok then acc
  else if s.hasDesc.contains name && !(s.hasType.contains name) then
    acc ++ [Field.typeOf name na.2]
  else acc

/- Look up the result-type annotation by the canonical result key. -/
def lookupReturn : List (Tok × Tok) → Tok
  | []            => []
  | (k, v) :: rest => if k == returnKey then v else lookupReturn rest

/- The trailing result-type field, emitted exactly when the result is annotated,
   already has a recorded description, and has no declared type yet. -/
def rtypeField (s : Sets) (annotations : List (Tok × Tok)) : List Field :=
  if annotations.any (fun na => na.1 == returnKey)
       && s.hasDesc.contains returnKey && !(s.hasType.contains returnKey) then
    [Field.rtype (lookupReturn annotations)]
  else []

/- The full sequence of fields appended by the operation: first the
   parameter-type fields synthesized from the annotation table in order, then the
   optional trailing result-type field. -/
def buildFields (fields : List (List Tok)) (annotations : List (Tok × Tok)) : List Field :=
  let s := classifyFields fields
  (annotations.foldl (emitStep s) []) ++ rtypeField s annotations

/- Forward-fold step: extending the consumed prefix by one element advances the
   left fold built from the shorter prefix by exactly that element. One generic
   drop-step shared by both loops (the Velvet fold pattern). -/
lemma foldlTakeStep {S A : Type} [Inhabited A] (f : S → A → S) (s0 : S) (xs : List A)
    (i : Nat) (hi : i < xs.length) :
    (xs.take (i + 1)).foldl f s0 = f ((xs.take i).foldl f s0) xs[i]! := by
  have hcons : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Augment a documented entity's info-field list with the type fields implied by
   its recorded annotations.

   First every existing field is classified by the leading token of its name,
   recording which parameter/result keys already carry a description and which
   already carry a declared type. A result documented under EITHER accepted
   spelling of the result-description field counts as a described result. Then,
   for each annotation in order, a parameter that has a description but no
   declared type gains a `type` field; finally, if the result is annotated and
   has a description but no declared type, a trailing result-type field is
   appended.

   `fields` and `annotations` are read-only (not `mut`): the operation reads them
   and builds a fresh field list, mutating neither (directive 5). -/
method augmentTypeFields (fields : List (List Tok)) (annotations : List (Tok × Tok))
    return (out : List Field)
  ensures out = buildFields fields annotations
  do
    -- impl-start
    let mut s : Sets := emptySets
    let mut i := 0
    while i < fields.length
      invariant i ≤ fields.length
      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets
      done_with i = fields.length
      decreasing fields.length - i
    do
      s := classifyField fields[i]! s
      i := i + 1
    let mut result : List Field := []
    let mut j := 0
    while j < annotations.length
      invariant j ≤ annotations.length
      invariant result = (annotations.take j).foldl (emitStep s) []
      done_with j = annotations.length
      decreasing annotations.length - j
    do
      result := emitStep s result annotations[j]!
      j := j + 1
    return result ++ rtypeField s annotations
    -- impl-end

prove_correct augmentTypeFields by
  loom_solve
  case _ =>
    have hi : i < fields.length := by omega
    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp_all
  case _ =>
    have hj : j < annotations.length := by omega
    rw [foldlTakeStep (emitStep _) [] annotations j hj]
    simp_all
  all_goals simp_all [buildFields, classifyFields]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED — all commands run from /home. Every attack file is byte-identical to Solution.lean outside the impl region; same_spec=True verified for all 10 generated attacks (generator: gen_attacks.py; command: `python -c "from swebench_unified.markers import same_spec; ..."` per the prompt, batched in the generator).

CONTROLS. positive control `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0 (verifies). prepatch `.../atk_0_prepatch.lean` -> EXIT=1 (G-DIFF reproduced, prepatch_reproduced=true).

ATTACKS (each `bash scripts/lean_verify.sh <path>`, run 4-at-a-time as background jobs; .out file per attack holds full output + EXIT): atk_1_echo        ungrounded-oracle echo (`return buildFields fields annotations`)          -> EXIT=0 VERIFIES atk_2_boundary    first loop stops one field early (`i+1 < fields.length`)                  -> EXIT=1 atk_3_order       trailing rtype PREPENDED instead of appended (sequence order)              -> EXIT=1 atk_4_partial     partial domain: `result.take 1` — drops all but first synthesized type     -> EXIT=1 atk_5_half        HALF-WIDENING: classify widened, emit-skip short-token-only (hunk2 absent) -> EXIT=1 atk_6_param       mis-modeled `:param xxx:` also records a declared TYPE (suppresses emit)   -> EXIT=1 atk_7_rtype       rtype body = FIRST annotation's value, not the one under the result key    -> EXIT=1 atk_8_vacuous     control-flow-effect: classification loop guard `i < 0` (never executes)    -> EXIT=1 atk_9_overemit    drops the hasType guard on the trailing rtype field (over-emits)           -> EXIT=1 atk_10_revorder   annotation loop consumes the table in REVERSE order                        -> EXIT=1 Each was given a deliberately maximally-permissive proof block (first-combinator over both fold-step tactics, then simp_all over every spec helper, omega/decide/rfl) so a failure is semantic, not proof-engineering weakness.

I additionally re-derived all 9 wrong impls in Python and confirmed each is GENUINELY extensionally distinct from buildFields on an exhibited witness (printed spec-vs-wrong outputs), so the 9 rejections are correct rejections rather than tactic failures.

MANDATORY RESOLVE OF THE VERIFYING IMPL. atk_1_echo is the only attack that verifies, and it verifies because it is extensionally the spec — so its faithful refined patch is the Python transliteration of the frozen spec's OWN helpers (classifyField/emitStep/rtypeField/lookupReturn/joinSp) under mapping.md §2, deliberately NOT a copy of the gold hunk (materializer: .../make_patch_atk1.py, patch: .../atk_1_echo.patch). Executed: `run_resolve('sphinx-doc__sphinx-9673', atk_1_echo.patch, timeout=1800)` -> RESOLVED=True, COMPLETED=True, F2P success=['test_autodoc_typehints_description_no_undoc'], failure=[]; P2P 24/24 success, 0 failure; PASS_TO_FAIL empty (note: 'resolved on attempt 2/2', flaky first attempt = infra, second attempt clean; full report in .../resolve_atk1.log). Because the spec's own transliteration resolves, the verify=>resolve implication survives its strongest test: there is no verifying-but-nonresolving witness.

REFINEMENT-FIDELITY MODEL CHECK (the real G-EQ risk here, since verification is exact functional equality to buildFields — the only way to break it is for buildFields itself to mis-model the patched function). Differential fuzz .../fuzz_model.py runs the frozen spec model against the REAL gold-patched augment_descriptions_with_types on live docutils field_list nodes (docutils 0.23 extracted into .../deps): exhaustive sweep over 0-2 existing fields x 0-2 annotations drawn from a token pool that deliberately includes 'return'/'returns'/'rtype'/'param'/'type' and multi-word names, plus 60k random deep cases (seed 20260813, up to 4 fields x 3 tokens, 3 annotations). Result: checks=86694 mismatches=0. The F2P shape and the prepatch discrimination are reproduced exactly (see counterexample). Duplicate-key annotation tables are canonicalized per mapping.md §4 before comparison — I checked this is legitimate domain restriction, not concealment: a Python Dict[str,str] cannot serialize to a repeated-key pair-list, and on unique-key tables canon is the identity.

REFINEMENT.MD AUDIT (§3 of protocol). 4 legs, tags: A1=R, A2=I+R, A3=I+R, A4=I. No kind-3 (inexpressible-changed-op) leg — the changed operation (two literal-membership widenings) is modeled CONCRETELY in classifyField (`p0 == returnTok || p0 == returnsTok`) and emitStep (`name == returnTok || name == returnsTok`), not deferred behind any abstraction. A-LEGS: none, and I confirmed this is structurally true rather than merely asserted — `grep -nE '^\s*axiom |^\s*opaque |sorry|native_decide|@\[extern'` over Solution.lean matches only the word 'axiom' inside the axioms-region PROSE comment; there is no axiom/opaque/sorry/native_decide/extern declaration anywhere. So G-AX is genuinely vacuous, the mapping.md §3 'no callee provenance' claim is correct (the function calls only re.split, str.join, set.add/in and docutils node constructors, all modeled concretely by pure-region helpers), and there is no A-correspondence left to falsify. patch.diff confirmed byte-identical to instance.json['patch'] (G-RESOLVE).

VERDICT SOUND. 10 same-spec attacks run (9 semantically-wrong, all rejected with exhibited distinguishing witnesses; 1 oracle-echo, which verifies and whose faithful patch RESOLVES under the official harness). Positive control verifies, prepatch fails, gold resolves, and the spec model agrees with the real patched function on 86,694 differential inputs including both widening-sensitive shapes. No verify=>correct break found. Residual trust point is exactly the one refinement.md declares: refinement fidelity of the R/I transliteration, which I independently stress-tested above rather than taking on faith. Caveat recorded for the runner: the atk_1 resolve needed 2 attempts (first attempt infra-flaky), so re-runs should allow retries.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC INTEGRITY: spec region confirmed byte-identical via swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend()) => True. Regions parsed with the velvet LanguageTables; spec_view dumped and read in full.

### METHOD (independent, not reusing bundled conformance_check.py):
1. Built a fresh worktree at base_commit 5fb51fb1467dc5eea7505402c3c5d9b378d3b441, applied patch.diff, and confirmed the change site is exactly the two literal-comparison widenings (parts[0] in ('return','returns'); name in ('return','returns')).
2. Wrote my OWN Python transliteration of buildFields/classifyField/emitStep/rtypeField/lookupReturn directly from the Lean text (myshadow.py), independent of the bundle's shadow.
3. CRITICAL STEP - validated that transliteration against the ACTUAL Lean semantics rather than trusting my reading: generated 2802 branch-covering cases, emitted a Lean file importing the frozen pure region verbatim and #eval'ing buildFields on each, comparing to my Python expectations. First run reported 25 failures; I isolated them and found the fault was in MY generator (double-rendering Field constructors), not the spec - direct #eval probes of the flagged cases agreed with my transliteration. Corrected generator (CrossCheck2.lean) => 0/2802 failures. So my shadow is provably equivalent to the real Lean buildFields on all branches.
4. Two oracles for the real repo: (a) AST-extracted verbatim function body exec'd with only its module deps injected, (b) the genuinely imported sphinx.ext.autodoc.typehints.augment_descriptions_with_types after installing the full dep set. Both observed through fields APPENDED to a freshly built docutils field_list.

RESULTS - no in-domain divergence found:
- 40,950 exhaustive single-field cases (450 branch-covering field names x 91 unique-key annotation tables): 0 disagreements.
- 1,800 exhaustive two-field cases: 0.
- 40,000 + 120,000 randomized fuzz incl. unicode/emoji/CJK/long tokens/multi-space/leading+trailing space: 0.
- 60,000 fuzz against the REAL IMPORTED sphinx module: 0.
- 60,000 whitespace/control-char fuzz (\t, \n, \r inside tokens - re.split(' +') splits only on SPACE, so the Tok model must handle these generically): 0.
- Targeted patch-site probes all agree: ':returns:'-only + return annotation => [rtype], both widenings exercised, 'returns' as an annotation KEY correctly skipped, rtype suppressed when already declared, params-then-rtype ordering, annotation-order-driven output order, params literally named 'return'/'returns'.
- Verified docutils field_name('', s).astext() == s (so the mapping.md 'split the name string' bijection is sound), and that the real function does not mutate pre-existing fields (matching the read-only, non-mut modeling).

OUT-OF-DOMAIN divergences found (NOT defects - both outside the declared bijection):
(a) Duplicate-key annotation tables. Lean 'annotations : List (Tok x Tok)' admits repeats; spec's lookupReturn takes the FIRST value and emitStep emits one type field PER repeat, while the repo's Dict[str,str] keeps the LAST value and one entry. E.g. fields=['returns'], ann=[('return','A'),('return','B')] => spec [rtype 'A'], repo [rtype 'B']. This is unreachable: annotations is a real Dict in the repo, so no such pair-list is in the bijection's image. Disclosed in mapping.md §4 and neutralized by canon_annotations. Confirmed the divergences vanish entirely under canonicalization (my own fuzz: 8 diffs without canon, 0 with, and every single one was a duplicate key).
(b) NUL-bearing field names: docutils uses \x00 as its internal escape marker and astext() strips it, so such names are not in the image of field[0].astext(). Excluding NUL, 0 disagreements.

DISCRIMINATION (spec strong enough, not just faithful): Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean FAILS (exit 1, unsolved goals at the ensures). Positive control on the real repo: F2P test_autodoc_typehints_description_no_undoc PASSES with patch.diff applied and FAILS on the reverted file - so the modeled behavior is the one the benchmark actually rewards.

MINOR OBSERVATION (not a faithfulness break, no diverging reachable input): the unique-key domain restriction lives in mapping.md prose + the conformance harness rather than as a 'requires' clause - the pre-conditions region is empty. Encoding it as a precondition would make the domain self-evident in the frozen spec instead of relying on the mapping doc. This does not admit a wrong impl nor reject a right one on any input the repo can produce.

I could not construct a reachable input on which the modeled function disagrees with the real callee. No faithfulness break.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** VERDICT: NO-LEAKAGE (pass) on the leakage question, but with two material defects flagged below that are outside this gate's scope to convert.

### WHAT I INDEPENDENTLY VERIFIED (no rubber-stamp; every load-bearing claim re-run from scratch):
1. same_spec(Solution, Solution_prepatch) = True under VelvetBackend.language -- spec regions byte-identical.
2. G-VERIFY: Solution.lean lean_verify EXIT=0 (~12s).
3. G-DIFF: Solution_prepatch.lean genuinely FAILS -- EXIT=1, 3 errors incl. 'unsolved goals' at the `ensures out = buildFields fields annotations` obligation.
4. G-CONF re-run MYSELF against the REAL patched repo (fresh worktree at 5fb51fb + gold patch applied, deps installed): 100,012 cases seed=9673, 0 disagreements. Confirmed the oracle was truly patched (t.__file__ in my worktree; "in ('return', 'returns')" present in the imported source) -- i.e. not a self-consistent shadow-vs-shadow test.
5. Mechanical leak screen: leakage.screen() passes (0 hard failures) -- the leak here is SEMANTIC, which is precisely why it needs the relaxation.
6. Token scan of the solver-visible problem_statement (NOT hints_text): ':returns:'=0, ':return:'=0, 'synonym'=0, 'plural'=0. The single 'Returns' token is the Google-style docstring SECTION HEADER inside the reproduction docstring -- a homograph at the Napoleon SOURCE layer, distinct from the generated reST field marker the fix unifies (confirmed napoleon/docstring.py maps both 'return'/'returns' sections and emits ':returns: '). The :return:/:returns: contrast appears ONLY in hints_text (excluded from the baseline) and the plural test input only in the hidden test_patch. I did not fall for the homograph trap.
7. Scanned the rest of the spec view for NEW leaks: no echo of augment_descriptions/typehints/autodoc/sphinx/has_description/has_type/field_list/docutils/napoleon/base_commit. 'rtype' is PUBLIC (problem_statement says "either as a rtype section"); param/type/joinSp/Sets/rtypeField model the generic pre-existing info-field mechanism. No additional problem_statement-underivable discriminator is disclosed.

CITATIONS CHECKED, NOT TRUSTED: the bundle ships a RELAXED_LEAKAGE.md containing a 'Panel recording convention' section addressed to me, telling me which verdict to submit. I treated it as a claim to verify. Its three infrastructure citations are GENUINE: prompts/velvet/spec_guide.md directive 6 does carry the relaxed-leakage exception; gates/_audit.py line 9 does say a relaxed-leakage panel records as 'pass' + note (no 'relaxed' status at the panel layer); gates/leak.py does honor relaxed_leakage + the file. meta.json has relaxed_leakage=True and G-LEAK status='relaxed'. So the convention is real infrastructure, not bundle-fabricated, and the leak is confined to the dispositioned plural-synonym facet with unavoidability independently proven (see counterexample). Hence NO-LEAKAGE is the honest recording on MY gate.

DEFECT 1 (FALSE CLAIM in RELAXED_LEAKAGE.md -- must be corrected): its 'Core soundness is intact' section asserts "G-EQ: pass (SOUND/TIGHT) -- 10 attacks re-run, none breaks the spec; positive control verifies" and "G-PANEL-2: FAITHFUL ... G-PANEL-1" soundness. meta.json actually records G-EQ status='fail' ("INCONCLUSIVE -- only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control"), G-PANEL-1 status='fail' (identical detail), and G-PANEL status='fail'. verdict.md corroborates: roles 1 and 2 both errored with "Command failed with exit code -9" (OOM-kill) and "Attack source not retained". The file's own stated precondition for the relaxation is 'core gates sound' -- so it asserts a precondition that the recorded state contradicts. This is exactly the 'broken disposition' trigger it names, and it is a real bundle defect.

Why this does NOT flip my verdict to LEAKAGE: G-EQ/G-PANEL-1 are refinement-fidelity / spec-too-weak gates, not leakage gates, and their 'fail' is INCONCLUSIVE-from-0-attacks caused by an OOM-killed audit process -- absence of evidence, not evidence of unsoundness. The substantive properties those gates would probe I re-verified by hand and they hold (G-CONF 100,012/0 vs the real patched callee, G-DIFF fires, G-VERIFY passes, recorded G-MUT 20/20, G-PBT SOUND, and my de-leaking experiment shows the spec is exactly TIGHT on the discriminator -- removing it admits the pre-patch impl). Converting a leakage gate to LEAKAGE on the basis of an unrelated crashed audit would misreport the defect's nature. Flagging it here is the correct channel; G-EQ and G-PANEL-1 should be RE-RUN before this bundle counts as green.

DEFECT 2 (minor, within the dispositioned facet): the spec-view prose exceeds the minimum narration faithfulness requires -- "The result-description clause accepting both spellings is the behavior of interest" plus a "(mapping.md 3.1)" cross-reference actively signpost the changed clause to the solver. This expands nothing a reader cannot already get from the unavoidable code disjuncts, so it is not a NEW discriminator and does not change the verdict, but it is avoidable narration that should be trimmed under directive 6 ("Do NOT relax to dodge ordinary de-narration").

Dispositioned leaking lines re-confirmed (for the record, covered by the relaxation, NOT new): `def returnsTok : Tok := "returns".toList`; `else if p0 == returnTok || p0 == returnsTok then` (classifyField); `if name == returnTok || name == returnsTok then acc` (emitStep); and the 'plural synonym' / 'EITHER accepted spelling' prose. Together these reconstruct the gold's two coupled widenings verbatim.

Counterexample / evidence:

```
Unavoidability re-derived EMPIRICALLY (not taken from the bundle's argument). I built a genuinely non-leaking variant of Solution.lean: deleted `def returnsTok`, dropped both disjuncts (`p0 == returnTok || p0 == returnsTok` -> `p0 == returnTok` in classifyField; `name == returnTok || name == returnsTok` -> `name == returnTok` in emitStep), and de-narrated the prose to name only the short return token (returnsTok occurrences = 0). That spec + its matching short-token-only impl VERIFIES: lean_verify EXIT=0. Since the short-token-only impl IS the pre-patch behavior, a non-leaking spec cannot make G-DIFF fire -- faithful + non-leaking is impossible here. Confirmed at the repo layer too: on the pre-patch worktree, augment_descriptions_with_types(fields=['returns'], {'return':'int'}) appends [] while fields=['return'] appends ['rtype'] -- exactly the F2P divergence, reachable ONLY by naming the plural spelling.
```

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.