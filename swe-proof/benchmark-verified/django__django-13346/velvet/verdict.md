# P2 adversarial audit — django__django-13346

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1_prepatch.lean`, `atk_2_byte_derived.lean`, `atk_3_partial_domain.lean`, `atk_4_index_shift.lean`, `atk_5_native_ignored.lean`, `atk_6_values_all.lean`, `atk_7_polarity_swap.lean`, `atk_8_tokens_reversed.lean`, `atk_10_divergent.lean`, `atk_11_dedup.lean`, `atk_12_always_clear.lean`, `atk_13_uniform_first.lean`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9_oracle_echo.lean`, `atk_9b_oracle_echo.lean`, `atk_16a_require_vacuity.lean`, `atk_16c_require_vacuity.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample found: no verifying same-spec impl has a faithful refined patch that fails to resolve. The 4 verifying attacks (atk_9, atk_9b, atk_16a, atk_16c) all had their faithful patches materialized and executed through run_resolve, and all 4 returned RESOLVED=True COMPLETED=True attempts=1 flaky=False. atk_9/atk_9b are ungrounded-oracle echoes (impl returns clauseTokens/clauseSuppliedValues verbatim), whose faithful refinement IS the gold hunk. atk_16a/atk_16c are require-relative vacuity exploits: the impl adds a guard `if vals.any (fun v => wrapOf v = bareTok) then return ([], vals)` that emits an unusable empty clause, which verifies only because `require ∀ v ∈ vals, wrapOf v ≠ bareTok` makes that branch dead. The decisive question was whether that `require` excludes a REAL input. It does not: refined through mapping.md §2 the guard becomes `if any(f == '%s' for f in func)`, and no enumerated vendor ever produces a bare '%s' func element — measured directly: sqlite/mysql give "JSON_EXTRACT(%s, '$')", mariadb gives "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))", oracle gives "JSON_VALUE('{\"value\": ...}', '$.value')". So the dead Lean branch is dead in the real code too, the guard is unreachable, and the patch resolves. The `require` is therefore a faithful abstraction boundary, not a hole.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,23 +88,16 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
       done_with i = 0
       decreasing i
     do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
+      result := bareTok :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, vals)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 2 — `atk_2_byte_derived.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,8 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
+    let mut kept : List Int := []
     let mut i := vals.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vals.length
@@ -102,9 +98,12 @@
       decreasing i
     do
       let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
+      let tok := if native then bareTok else wrapOf v
+      result := tok :: result
+      -- the REFUTED rule: decide by inspecting the token's bytes, not the arm
+      kept := (if tok = bareTok then kept else v :: kept)
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, if native then vals else kept)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 3 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,23 +88,11 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
-    let mut result : List (List Char) := []
-    let mut i := vals.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
-      i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    if vals.length ≤ 1 then
+      return (clauseTokens native bareTok wrapOf vals,
+              clauseSuppliedValues native wrapHoldsValue vals)
+    else
+      return ([], [])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 4 — `atk_4_index_shift.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,20 +88,14 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
       done_with i = 0
       decreasing i
     do
-      let v := vals[i - 1]!
+      let v := vals[i]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
```

Attack 5 — `atk_5_native_ignored.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,21 +88,15 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
       done_with i = 0
       decreasing i
     do
       let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
+      result := wrapOf v :: result
       i := i - 1
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
     -- impl-end
```

Attack 6 — `atk_6_values_all.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,7 +99,7 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, vals)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 7 — `atk_7_polarity_swap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,7 +99,7 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, if native then vals else (if wrapHoldsValue then vals else []))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 8 — `atk_8_tokens_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,16 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
-    let mut i := vals.length
-    while i > 0
+    let mut i := 0
+    while i < vals.length
       invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = vals.length
+      decreasing vals.length - i
     do
-      let v := vals[i - 1]!
+      let v := vals[i]!
       result := (if native then bareTok else wrapOf v) :: result
-      i := i - 1
+      i := i + 1
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
     -- impl-end
 
```

Attack 9 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,23 +88,8 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
-    let mut result : List (List Char) := []
-    let mut i := vals.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
-      i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (clauseTokens native bareTok wrapOf vals,
+            clauseSuppliedValues native wrapHoldsValue vals)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
@@ -127,6 +112,3 @@
 
 prove_correct buildMembershipClause by
   loom_solve
-  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
-    simp_all [slotToken]
-  · simp_all [clauseSuppliedValues]
```

Attack 10 — `atk_9b_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,23 +88,8 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
-    let mut result : List (List Char) := []
-    let mut i := vals.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
-      i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (clauseTokens native bareTok wrapOf vals,
+            clauseSuppliedValues native wrapHoldsValue vals)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
@@ -126,7 +111,4 @@
   rw [hcons, clauseTokens_cons]
 
 prove_correct buildMembershipClause by
-  loom_solve
-  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
-    simp_all [slotToken]
-  · simp_all [clauseSuppliedValues]
+  loom_solve <;> simp_all [clauseTokens, clauseSuppliedValues, slotToken]
```

Attack 11 — `atk_10_divergent.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,22 +88,17 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
-    while i > 0
+    while true
       invariant 0 ≤ i ∧ i ≤ vals.length
       invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
       done_with i = 0
-      decreasing i
     do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
-      i := i - 1
+      if i > 0 then
+        let v := vals[i - 1]!
+        result := (if native then bareTok else wrapOf v) :: result
+        i := i - 1
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
     -- impl-end
 
```

Attack 12 — `atk_11_dedup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,7 +99,7 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, if native then vals.eraseDups else (if wrapHoldsValue then [] else vals.eraseDups))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 13 — `atk_12_always_clear.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,7 +99,7 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, if native then vals else [])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 14 — `atk_13_uniform_first.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,21 +88,16 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
+    let first := vals[0]!
     while i > 0
       invariant 0 ≤ i ∧ i ≤ vals.length
       invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
       done_with i = 0
       decreasing i
     do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
+      result := (if native then bareTok else wrapOf first) :: result
       i := i - 1
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
     -- impl-end
```

Attack 15 — `atk_14_subset_values.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,7 +99,8 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, if native then vals
+                    else (if wrapHoldsValue then [] else vals.take (vals.length - 1)))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

Attack 16 — `atk_15_early_return.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,8 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
+    if !native && vals.length > 2 then
+      return ([], if wrapHoldsValue then [] else vals)
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
```

Attack 17 — `atk_16a_require_vacuity.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,6 +99,8 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
+    if vals.any (fun v => wrapOf v = bareTok) then
+      return ([], vals)
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
     -- impl-end
 
```

Attack 18 — `atk_16c_require_vacuity.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,6 +99,8 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
+    if vals.any (fun v => wrapOf v = bareTok) then
+      return ([], vals)
     return (result, if native then vals else (if wrapHoldsValue then [] else vals))
     -- impl-end
 
@@ -127,6 +124,9 @@
 
 prove_correct buildMembershipClause by
   loom_solve
-  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
-    simp_all [slotToken]
-  · simp_all [clauseSuppliedValues]
+  all_goals
+    first
+      | (rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
+         simp_all [slotToken])
+      | simp_all [clauseSuppliedValues, slotToken]
+      | grind
```

Attack 19 — `atk_17_echo_swapped_arg.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,23 +88,8 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
-    let mut result : List (List Char) := []
-    let mut i := vals.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ vals.length
-      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let v := vals[i - 1]!
-      result := (if native then bareTok else wrapOf v) :: result
-      i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (clauseTokens native bareTok wrapOf vals,
+            clauseSuppliedValues wrapHoldsValue native vals)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
@@ -126,7 +111,4 @@
   rw [hcons, clauseTokens_cons]
 
 prove_correct buildMembershipClause by
-  loom_solve
-  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
-    simp_all [slotToken]
-  · simp_all [clauseSuppliedValues]
+  loom_solve <;> simp_all [clauseTokens, clauseSuppliedValues, slotToken]
```

Attack 20 — `atk_18_values_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,6 @@
   ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
   do
     -- impl-start
-    -- The operand token for each slot, selected by the capability flag: the plain
-    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
-    -- listed value is mapped to. The values handed over alongside follow the
-    -- branch: none at all where the alternate tokens keep their own values,
-    -- every listed value otherwise.
     let mut result : List (List Char) := []
     let mut i := vals.length
     while i > 0
@@ -104,7 +99,7 @@
       let v := vals[i - 1]!
       result := (if native then bareTok else wrapOf v) :: result
       i := i - 1
-    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
+    return (result, if native then vals.reverse else (if wrapHoldsValue then [] else vals.reverse))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more slot on
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. `bareTok`, `wrapOf` and `wrapHoldsValue` are ordinary
--  input parameters, not contracts about an outside callee: `wrapOf` is a plain
--  total function the caller supplies and `wrapHoldsValue` a plain `Bool`. The
--  `require` states only that each listed value's alternate token differs from
--  the plain one. No `axiom` is declared and no outside callee's behavior is
--  assumed.)
-- axioms-end

-- pure-start
/- The operand token ONE listed value contributes to a membership comparison.
   A boolean capability flag `native` selects it: when the flag holds the token
   is the plain `bareTok`; when it does not, the token is `wrapOf v`, the
   alternate token the supplied map assigns to that listed value. -/
def slotToken (native : Bool) (bareTok : List Char) (wrapOf : Int → List Char)
    (v : Int) : List Char :=
  if native then bareTok else wrapOf v

/- The per-slot token sequence for a whole membership list: one token per listed
   value, in order, each obtained by applying `slotToken` to that slot's own
   listed value. Front-recursive so a single unfold is available per loop step
   (the backward-fold pattern). -/
def clauseTokens (native : Bool) (bareTok : List Char) (wrapOf : Int → List Char) :
    List Int → List (List Char)
  | []      => []
  | v :: vs => slotToken native bareTok wrapOf v :: clauseTokens native bareTok wrapOf vs

@[grind] lemma clauseTokens_nil (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) :
    clauseTokens native bareTok wrapOf [] = [] := rfl
@[grind] lemma clauseTokens_cons (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) (v : Int) (vs : List Int) :
    clauseTokens native bareTok wrapOf (v :: vs)
      = slotToken native bareTok wrapOf v :: clauseTokens native bareTok wrapOf vs := rfl

/- The listed values that must still travel ALONGSIDE the clause, in order — all
   of them or none. Which it is is a property of the BRANCH the clause was built
   on, never of the text of any one token: on the plain branch every listed value
   travels, and on the alternate branch the supplied `wrapHoldsValue` records
   whether that branch's token family still needs its values handed over
   separately. The flag is a property of the family as a whole, and is never read
   off an individual token's characters. -/
def clauseSuppliedValues (native wrapHoldsValue : Bool) (vals : List Int) :
    List Int :=
  if native then vals
  else if wrapHoldsValue then [] else vals
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build a membership comparison's right-hand side over a list of listed values,
   as the pair it is only usable as: the operand tokens, and the listed values
   that still have to be handed over alongside them.

   Desired behaviour of the tokens: every listed value contributes exactly one
   operand token, in order, and the boolean capability flag `native` selects
   which — the plain `bareTok` on every slot when it holds, and otherwise each
   slot's own `wrapOf v`.

   Desired behaviour of the accompanying values: all of them or none, following
   the BRANCH. Every listed value on the `native` branch, unchanged and in order;
   on the other branch, as `wrapHoldsValue` records for the alternate token
   family. Neither component may be chosen independently of the other: a clause
   whose tokens still need their values but hands none over, or which hands over
   values its tokens have no place for, cannot be evaluated.

   `vals`, `native`, `bareTok`, `wrapOf`, `wrapHoldsValue` are all read-only
   (none is `mut`); the build mutates nothing observable (directive 5). The
   `require` records that each listed value's alternate token differs from the
   plain token. -/
method buildMembershipClause (vals : List Int) (native : Bool)
    (bareTok : List Char) (wrapOf : Int → List Char) (wrapHoldsValue : Bool)
    return (out : List (List Char) × List Int)
  require ∀ v ∈ vals, wrapOf v ≠ bareTok
  ensures out.1 = clauseTokens native bareTok wrapOf vals
  ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
  do
    -- impl-start
    -- The operand token for each slot, selected by the capability flag: the plain
    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
    -- listed value is mapped to. The values handed over alongside follow the
    -- branch: none at all where the alternate tokens keep their own values,
    -- every listed value otherwise.
    let mut result : List (List Char) := []
    let mut i := vals.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vals.length
      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
      done_with i = 0
      decreasing i
    do
      let v := vals[i - 1]!
      result := (if native then bareTok else wrapOf v) :: result
      i := i - 1
    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes one more slot on
   the front, so `clauseTokens` peels one `slotToken` — the one for that slot's
   own listed value. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma clauseTokens_drop_step (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) (vals : List Int) (i : Nat) (hi : 0 < i)
    (hle : i ≤ vals.length) :
    clauseTokens native bareTok wrapOf (vals.drop (i - 1))
      = slotToken native bareTok wrapOf vals[i - 1]!
          :: clauseTokens native bareTok wrapOf (vals.drop i) := by
  have hlt : i - 1 < vals.length := by omega
  have hcons : vals.drop (i - 1) = vals[i - 1]! :: vals.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, clauseTokens_cons]

prove_correct buildMembershipClause by
  loom_solve
  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
    simp_all [slotToken]
  · simp_all [clauseSuppliedValues]
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL EXECUTED.** Positive control: pos_control.lean (byte-identical copy of bundle Solution.lean, md5 d7a15e3d3c02a78d23c8bd1856d61695) -> `bash scripts/lean_verify.sh .../pos_control.lean` = EXIT 0 (verifies). All 20 submitted attacks confirmed same_spec=True via swebench_unified.markers.same_spec with the velvet backend before counting.

VERIFY COMMAND (each attack): `bash scripts/lean_verify.sh <name>.lean`, run 4-at-a-time as concurrent background jobs per the parallelism directive.

REJECTED (exit 1) — 16 attacks, covering the required classes:
- atk_1_prepatch (PREPATCH BUG re-encoded: bareTok every slot, never consults native/wrapOf, forwards all values). Residual false goals observed: `result_1 = clauseTokens native bareTok wrapOf vals` and `vals = clauseSuppliedValues native wrapHoldsValue vals` — refuted by BOTH ensures independently, matching refinement.md's G-DIFF claim. prepatch_reproduced=true.
- atk_2_byte_derived (PRIOR PASS'S NAMED COUNTEREXAMPLE re-encoded: out.2 derived by testing each emitted token against bareTok instead of per-arm). Residual goal `(if native then vals else i_2) = if native then vals else if wrapHoldsValue then [] else vals` — the spec pins the per-ARM rule and rejects the byte-derived one, exactly the '100%sale' divergence mapping.md §2.1 documents.
- atk_3_partial_domain (PARTIAL DOMAIN: correct only for vals.length <= 1, ([],[]) otherwise)
- atk_4_index_shift (BOUNDARY: vals[i]! instead of vals[i-1]!)
- atk_5_native_ignored (drops the capability gate; always wraps)
- atk_6_values_all (tokens correct, out.2 always vals). Residual goal `native = false -> wrapHoldsValue = true -> vals = []` — the A7 obligation is live and load-bearing.
- atk_7_polarity_swap (wrapHoldsValue polarity inverted on out.2)
- atk_8_tokens_reversed (slot ORDER dropped)
- atk_10_divergent (CONTROL-FLOW EFFECT: `while true` with no decreasing measure; rejected with 'Decreasing' + 'Failed to prove assertion' — total-correctness semantics reject non-termination)
- atk_11_dedup (eraseDups on out.2 — drops repeated listed values)
- atk_12_always_clear (ignores wrapHoldsValue; clears on all non-native arms)
- atk_13_uniform_first (UNIFORMITY: every slot gets vals[0]!'s token — directly attacks the per-slot legs A4/A5)
- atk_14_subset_values (SUBSET on the open arm: vals.take (len-1) — attacks A7's 'all or none, never a subset')
- atk_15_early_return (CONTROL-FLOW EFFECT: early return skips the loop for non-native clauses with >2 values)
- atk_17_echo_swapped_arg (echo with swapped args: clauseSuppliedValues wrapHoldsValue native vals)
- atk_18_values_reversed (ORDER of accompanying values dropped — mapping.md §2 calls the bijection order-preserving)

VERIFIED (exit 0) — 4 attacks, ALL had faithful patches materialized AND EXECUTED through run_resolve:
- atk_9_oracle_echo -> patch_atk_9_oracle_echo.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk9-echo)
- atk_9b_oracle_echo -> patch_atk_9b_oracle_echo.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk9b-echo)
- atk_16a_require_vacuity -> patch_atk_16a_require_vacuity.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk16a-vacuity)
- atk_16c_require_vacuity -> patch_atk_16c_require_vacuity.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk16c-vacuity)
The atk_16a/16c patch was generated MECHANICALLY (gold patch applied to a real worktree at base_commit 9c92924cd5d164701e2514e1c2d6574126bd7cc2, guard inserted, `git diff`) after a hand-written version was rejected by `git apply --check` as 'corrupt patch' — so the resolved verdict describes a patch that genuinely applies. Worktree removed after use.

METHODOLOGICAL HONESTY / NEGATIVE CONTROLS (these changed my conclusions):
1. **TACTIC-COMPETENCE CONTROL.** My first rejection batch retained the bundle's original tactic script, and several attacks failed with 'rewrite pattern not found' — a possible tactical artifact rather than spec rejection. I built 'b-variants' (atk_1b, atk_2b, atk_4b, atk_5b, atk_6b, atk_8b) with a broad generic script, and they all failed too. But the control ctl_generic_tactic.lean — the CORRECT impl proved with that same generic script — ALSO FAILED (exit 1, 'simp_all made no progress'). My generic script is tactically incompetent, so the b-variants are NOT admissible evidence and I deliberately excluded all of them from the submitted attack list. The 16 submitted rejections all used the proven-competent original script (the one under which pos_control verifies) and show clean FALSE residual goals, not tactic crashes.
2. atk_16 (first attempt) failed with 'No goals to be solved' — my bullet count, not the spec. Retrying with corrected arities produced atk_16a (2 bullets) and atk_16c (all_goals) which BOTH VERIFY, and atk_16b (3 bullets) which fails for the same arity reason. Reporting a proof-script arity error as a spec rejection would have manufactured false tightness; the verifying variants are the ones I submitted and resolved.

REFINEMENT.MD AUDIT (protocol step 3): PASS, no kind-3. Legs A1-A7 are tagged R (A1,A2,A3,A6) and I+R (A4,A5,A7) — every leg is R or I; no A-consumed and no A-reference legs exist. Confirmed mechanically that the bundle declares NO `axiom` and no `opaque`, consistent with §B's claim that G-AX is skip and there is no axiom-soundness obligation. The A-leg correspondence therefore reduces to the deep-model↔callee fidelity of slotToken/clauseTokens/clauseSuppliedValues against the gold hunk, which I checked against conformance_check.py's bijection images wrap_of(vendor) and wrap_holds_value(vendor): both are built from the gold hunk's own per-branch structure, and wrap_holds_value is documented and implemented as an ARM property rather than a byte test — which is exactly the discrimination atk_2_byte_derived confirms the spec enforces. patch.diff is byte-identical to instance.json's gold patch (1839 bytes, verified equal). The `wrapOf`/`wrapHoldsValue` parameters are genuinely data (no `ensures` attached, universally quantified in the contract), so §B's 'not axiomatized callee' claim holds; and the one `require` is not a hole, per the atk_16 analysis above.

**VERDICT:** SOUND. 20 same-spec attacks run (16 rejected, 4 verified), the prepatch bug and the prior pass's byte-derived counterexample both re-encoded and rejected, and every one of the 4 verifying impls had its faithful refined patch materialized and executed through the official harness with RESOLVED=True. No verify-not-correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1_prepatch.lean`, `atk_2_byte_derived.lean`, `atk_3_partial_domain.lean`, `atk_4_index_shift.lean`, `atk_5_native_ignored.lean`, `atk_6_values_all.lean`, `atk_7_polarity_swap.lean`, `atk_8_tokens_reversed.lean`, `atk_10_divergent.lean`, `atk_11_dedup.lean`, `atk_12_always_clear.lean`, `atk_13_uniform_first.lean`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9_oracle_echo.lean`, `atk_9b_oracle_echo.lean`, `atk_16a_require_vacuity.lean`, `atk_16c_require_vacuity.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample found: no verifying same-spec impl has a faithful refined patch that fails to resolve. The 4 verifying attacks (atk_9, atk_9b, atk_16a, atk_16c) all had their faithful patches materialized and executed through run_resolve, and all 4 returned RESOLVED=True COMPLETED=True attempts=1 flaky=False. atk_9/atk_9b are ungrounded-oracle echoes (impl returns clauseTokens/clauseSuppliedValues verbatim), whose faithful refinement IS the gold hunk. atk_16a/atk_16c are require-relative vacuity exploits: the impl adds a guard `if vals.any (fun v => wrapOf v = bareTok) then return ([], vals)` that emits an unusable empty clause, which verifies only because `require ∀ v ∈ vals, wrapOf v ≠ bareTok` makes that branch dead. The decisive question was whether that `require` excludes a REAL input. It does not: refined through mapping.md §2 the guard becomes `if any(f == '%s' for f in func)`, and no enumerated vendor ever produces a bare '%s' func element — measured directly: sqlite/mysql give "JSON_EXTRACT(%s, '$')", mariadb gives "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))", oracle gives "JSON_VALUE('{\"value\": ...}', '$.value')". So the dead Lean branch is dead in the real code too, the guard is unreachable, and the patch resolves. The `require` is therefore a faithful abstraction boundary, not a hole.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_byte_derived.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_index_shift.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_native_ignored.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_values_all.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_polarity_swap.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_tokens_reversed.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_9b_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_10_divergent.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11_dedup.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12_always_clear.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13_uniform_first.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14_subset_values.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_15_early_return.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16a_require_vacuity.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_16c_require_vacuity.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_17_echo_swapped_arg.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_18_values_reversed.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. `bareTok`, `wrapOf` and `wrapHoldsValue` are ordinary
--  input parameters, not contracts about an outside callee: `wrapOf` is a plain
--  total function the caller supplies and `wrapHoldsValue` a plain `Bool`. The
--  `require` states only that each listed value's alternate token differs from
--  the plain one. No `axiom` is declared and no outside callee's behavior is
--  assumed.)
-- axioms-end

-- pure-start
/- The operand token ONE listed value contributes to a membership comparison.
   A boolean capability flag `native` selects it: when the flag holds the token
   is the plain `bareTok`; when it does not, the token is `wrapOf v`, the
   alternate token the supplied map assigns to that listed value. -/
def slotToken (native : Bool) (bareTok : List Char) (wrapOf : Int → List Char)
    (v : Int) : List Char :=
  if native then bareTok else wrapOf v

/- The per-slot token sequence for a whole membership list: one token per listed
   value, in order, each obtained by applying `slotToken` to that slot's own
   listed value. Front-recursive so a single unfold is available per loop step
   (the backward-fold pattern). -/
def clauseTokens (native : Bool) (bareTok : List Char) (wrapOf : Int → List Char) :
    List Int → List (List Char)
  | []      => []
  | v :: vs => slotToken native bareTok wrapOf v :: clauseTokens native bareTok wrapOf vs

@[grind] lemma clauseTokens_nil (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) :
    clauseTokens native bareTok wrapOf [] = [] := rfl
@[grind] lemma clauseTokens_cons (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) (v : Int) (vs : List Int) :
    clauseTokens native bareTok wrapOf (v :: vs)
      = slotToken native bareTok wrapOf v :: clauseTokens native bareTok wrapOf vs := rfl

/- The listed values that must still travel ALONGSIDE the clause, in order — all
   of them or none. Which it is is a property of the BRANCH the clause was built
   on, never of the text of any one token: on the plain branch every listed value
   travels, and on the alternate branch the supplied `wrapHoldsValue` records
   whether that branch's token family still needs its values handed over
   separately. The flag is a property of the family as a whole, and is never read
   off an individual token's characters. -/
def clauseSuppliedValues (native wrapHoldsValue : Bool) (vals : List Int) :
    List Int :=
  if native then vals
  else if wrapHoldsValue then [] else vals
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build a membership comparison's right-hand side over a list of listed values,
   as the pair it is only usable as: the operand tokens, and the listed values
   that still have to be handed over alongside them.

   Desired behaviour of the tokens: every listed value contributes exactly one
   operand token, in order, and the boolean capability flag `native` selects
   which — the plain `bareTok` on every slot when it holds, and otherwise each
   slot's own `wrapOf v`.

   Desired behaviour of the accompanying values: all of them or none, following
   the BRANCH. Every listed value on the `native` branch, unchanged and in order;
   on the other branch, as `wrapHoldsValue` records for the alternate token
   family. Neither component may be chosen independently of the other: a clause
   whose tokens still need their values but hands none over, or which hands over
   values its tokens have no place for, cannot be evaluated.

   `vals`, `native`, `bareTok`, `wrapOf`, `wrapHoldsValue` are all read-only
   (none is `mut`); the build mutates nothing observable (directive 5). The
   `require` records that each listed value's alternate token differs from the
   plain token. -/
method buildMembershipClause (vals : List Int) (native : Bool)
    (bareTok : List Char) (wrapOf : Int → List Char) (wrapHoldsValue : Bool)
    return (out : List (List Char) × List Int)
  require ∀ v ∈ vals, wrapOf v ≠ bareTok
  ensures out.1 = clauseTokens native bareTok wrapOf vals
  ensures out.2 = clauseSuppliedValues native wrapHoldsValue vals
  do
    -- impl-start
    -- The operand token for each slot, selected by the capability flag: the plain
    -- `bareTok` when `native`, otherwise the alternate token this slot's OWN
    -- listed value is mapped to. The values handed over alongside follow the
    -- branch: none at all where the alternate tokens keep their own values,
    -- every listed value otherwise.
    let mut result : List (List Char) := []
    let mut i := vals.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ vals.length
      invariant result = clauseTokens native bareTok wrapOf (vals.drop i)
      done_with i = 0
      decreasing i
    do
      let v := vals[i - 1]!
      result := (if native then bareTok else wrapOf v) :: result
      i := i - 1
    return (result, if native then vals else (if wrapHoldsValue then [] else vals))
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes one more slot on
   the front, so `clauseTokens` peels one `slotToken` — the one for that slot's
   own listed value. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma clauseTokens_drop_step (native : Bool) (bareTok : List Char)
    (wrapOf : Int → List Char) (vals : List Int) (i : Nat) (hi : 0 < i)
    (hle : i ≤ vals.length) :
    clauseTokens native bareTok wrapOf (vals.drop (i - 1))
      = slotToken native bareTok wrapOf vals[i - 1]!
          :: clauseTokens native bareTok wrapOf (vals.drop i) := by
  have hlt : i - 1 < vals.length := by omega
  have hcons : vals.drop (i - 1) = vals[i - 1]! :: vals.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, clauseTokens_cons]

prove_correct buildMembershipClause by
  loom_solve
  · rw [clauseTokens_drop_step native bareTok wrapOf vals i (by omega) (by omega)]
    simp_all [slotToken]
  · simp_all [clauseSuppliedValues]
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL EXECUTED.** Positive control: pos_control.lean (byte-identical copy of bundle Solution.lean, md5 d7a15e3d3c02a78d23c8bd1856d61695) -> `bash scripts/lean_verify.sh .../pos_control.lean` = EXIT 0 (verifies). All 20 submitted attacks confirmed same_spec=True via swebench_unified.markers.same_spec with the velvet backend before counting.

VERIFY COMMAND (each attack): `bash scripts/lean_verify.sh <name>.lean`, run 4-at-a-time as concurrent background jobs per the parallelism directive.

REJECTED (exit 1) — 16 attacks, covering the required classes:
- atk_1_prepatch (PREPATCH BUG re-encoded: bareTok every slot, never consults native/wrapOf, forwards all values). Residual false goals observed: `result_1 = clauseTokens native bareTok wrapOf vals` and `vals = clauseSuppliedValues native wrapHoldsValue vals` — refuted by BOTH ensures independently, matching refinement.md's G-DIFF claim. prepatch_reproduced=true.
- atk_2_byte_derived (PRIOR PASS'S NAMED COUNTEREXAMPLE re-encoded: out.2 derived by testing each emitted token against bareTok instead of per-arm). Residual goal `(if native then vals else i_2) = if native then vals else if wrapHoldsValue then [] else vals` — the spec pins the per-ARM rule and rejects the byte-derived one, exactly the '100%sale' divergence mapping.md §2.1 documents.
- atk_3_partial_domain (PARTIAL DOMAIN: correct only for vals.length <= 1, ([],[]) otherwise)
- atk_4_index_shift (BOUNDARY: vals[i]! instead of vals[i-1]!)
- atk_5_native_ignored (drops the capability gate; always wraps)
- atk_6_values_all (tokens correct, out.2 always vals). Residual goal `native = false -> wrapHoldsValue = true -> vals = []` — the A7 obligation is live and load-bearing.
- atk_7_polarity_swap (wrapHoldsValue polarity inverted on out.2)
- atk_8_tokens_reversed (slot ORDER dropped)
- atk_10_divergent (CONTROL-FLOW EFFECT: `while true` with no decreasing measure; rejected with 'Decreasing' + 'Failed to prove assertion' — total-correctness semantics reject non-termination)
- atk_11_dedup (eraseDups on out.2 — drops repeated listed values)
- atk_12_always_clear (ignores wrapHoldsValue; clears on all non-native arms)
- atk_13_uniform_first (UNIFORMITY: every slot gets vals[0]!'s token — directly attacks the per-slot legs A4/A5)
- atk_14_subset_values (SUBSET on the open arm: vals.take (len-1) — attacks A7's 'all or none, never a subset')
- atk_15_early_return (CONTROL-FLOW EFFECT: early return skips the loop for non-native clauses with >2 values)
- atk_17_echo_swapped_arg (echo with swapped args: clauseSuppliedValues wrapHoldsValue native vals)
- atk_18_values_reversed (ORDER of accompanying values dropped — mapping.md §2 calls the bijection order-preserving)

VERIFIED (exit 0) — 4 attacks, ALL had faithful patches materialized AND EXECUTED through run_resolve:
- atk_9_oracle_echo -> patch_atk_9_oracle_echo.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk9-echo)
- atk_9b_oracle_echo -> patch_atk_9b_oracle_echo.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk9b-echo)
- atk_16a_require_vacuity -> patch_atk_16a_require_vacuity.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk16a-vacuity)
- atk_16c_require_vacuity -> patch_atk_16c_require_vacuity.diff -> RESOLVED=True COMPLETED=True attempts=1 flaky=False (run_id sbu-geq-atk16c-vacuity)
The atk_16a/16c patch was generated MECHANICALLY (gold patch applied to a real worktree at base_commit 9c92924cd5d164701e2514e1c2d6574126bd7cc2, guard inserted, `git diff`) after a hand-written version was rejected by `git apply --check` as 'corrupt patch' — so the resolved verdict describes a patch that genuinely applies. Worktree removed after use.

METHODOLOGICAL HONESTY / NEGATIVE CONTROLS (these changed my conclusions):
1. **TACTIC-COMPETENCE CONTROL.** My first rejection batch retained the bundle's original tactic script, and several attacks failed with 'rewrite pattern not found' — a possible tactical artifact rather than spec rejection. I built 'b-variants' (atk_1b, atk_2b, atk_4b, atk_5b, atk_6b, atk_8b) with a broad generic script, and they all failed too. But the control ctl_generic_tactic.lean — the CORRECT impl proved with that same generic script — ALSO FAILED (exit 1, 'simp_all made no progress'). My generic script is tactically incompetent, so the b-variants are NOT admissible evidence and I deliberately excluded all of them from the submitted attack list. The 16 submitted rejections all used the proven-competent original script (the one under which pos_control verifies) and show clean FALSE residual goals, not tactic crashes.
2. atk_16 (first attempt) failed with 'No goals to be solved' — my bullet count, not the spec. Retrying with corrected arities produced atk_16a (2 bullets) and atk_16c (all_goals) which BOTH VERIFY, and atk_16b (3 bullets) which fails for the same arity reason. Reporting a proof-script arity error as a spec rejection would have manufactured false tightness; the verifying variants are the ones I submitted and resolved.

REFINEMENT.MD AUDIT (protocol step 3): PASS, no kind-3. Legs A1-A7 are tagged R (A1,A2,A3,A6) and I+R (A4,A5,A7) — every leg is R or I; no A-consumed and no A-reference legs exist. Confirmed mechanically that the bundle declares NO `axiom` and no `opaque`, consistent with §B's claim that G-AX is skip and there is no axiom-soundness obligation. The A-leg correspondence therefore reduces to the deep-model↔callee fidelity of slotToken/clauseTokens/clauseSuppliedValues against the gold hunk, which I checked against conformance_check.py's bijection images wrap_of(vendor) and wrap_holds_value(vendor): both are built from the gold hunk's own per-branch structure, and wrap_holds_value is documented and implemented as an ARM property rather than a byte test — which is exactly the discrimination atk_2_byte_derived confirms the spec enforces. patch.diff is byte-identical to instance.json's gold patch (1839 bytes, verified equal). The `wrapOf`/`wrapHoldsValue` parameters are genuinely data (no `ensures` attached, universally quantified in the contract), so §B's 'not axiomatized callee' claim holds; and the one `require` is not a hole, per the atk_16 analysis above.

**VERDICT:** SOUND. 20 same-spec attacks run (16 rejected, 4 verified), the prepatch bug and the prior pass's byte-derived counterexample both re-encoded and rejected, and every one of the 4 verifying impls had its faithful refined patch materialized and executed through the official harness with RESOLVED=True. No verify-not-correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL(2) faithfulness-break for django__django-13346 (velvet). Verdict FAITHFUL: no input found where the modeled buildMembershipClause disagrees with the real patch-APPLIED KeyTransformIn.process_rhs.

**SETUP.** Fresh worktree of django_django.git at base_commit 9c92924cd5d164701e2514e1c2d6574126bd7cc2 () with patch.diff APPLIED (per prompt: the patched tree is the reference for the modeled function; base is reference only for untouched callees). Built a live harness () that instantiates the REAL KeyTransformIn node via Doc.objects.filter(value__c__in=vals).query, walks q.where to grab the node, and calls the genuine .process_rhs(compiler, conn) with a proxy connection overriding only the two dispatch inputs the hunk reads (features.has_native_json_field, vendor, mysql_is_mariadb). This exercises the real callee end-to-end including the UNCHANGED super-class In.process_rhs, not a transliteration.

**BIJECTION.** Solution.lean's out.1 = clauseTokens is compared to the real rhs by reassembly '(' + ', '.join(tokens) + ')' -- exact, since the super-class template is '(' + ', '.join('%s'*n) + ')' and rhs % func substitutes func[i] verbatim into slot i. out.2 = clauseSuppliedValues compared to the returned rhs_params exactly. The model's `vals` carrier is taken from the real native-config call (the untouched super-class params), so slot/value correspondence is not assumed.

**DIFFERENTIAL.** 4640 inputs (640 curated + 4000 recursive-random incl. nested lists/dicts, unicode, '%', '%%', '%s', '%(x)s', '100%sale', "', '$.value'", "JSON_EXTRACT(%s, '$')", empty string, bools, floats, 1e20) x 5 configurations (native; non-native sqlite / mysql / mariadb / oracle) = ZERO divergences in both tokens and accompanying values. 1641 of the random inputs carried '%' into the value-holding (oracle) arm -- the class that separates the modeled per-ARM rule from a byte-derived one -- and the model matched on every one.

HARNESS SENSITIVITY (this is what makes the clean run mean something). 7 model mutants, all caught: prepatch/bare-only 166/166, native-polarity-swap 166/166, per-slot-uniformity 112/166, tokens-reversed 112/166, values-always-forwarded 166/166, values-always-cleared 166/166, and crucially byte_derived (out.2 := values whose emitted token contains '%s') 67/166. Identity model: 0/166 false positives. So the harness would have flagged exactly the drift mapping.md §2.1 says two earlier bundle revisions had.

### SPEC-TOO-STRONG PROBES (the specific failure mode of this gate).
1. require (forall v in vals, wrapOf v != bareTok): checked over real (vendor,value) pairs on all 4 non-native vendors -- 0 violations. The precondition excludes no reachable input; every enumerated vendor's token is JSON_EXTRACT/JSON_UNQUOTE/JSON_VALUE/JSON_QUERY-wrapped, never a bare '%s'.
2. wrapHoldsValue deliberately NOT tied to wrapOf in the require: confirmed correct. An oracle expression built from '100%sale' is JSON_VALUE('{"value": "100%sale"}', '$.value') -- contains '%s' AND holds its value with real rhs_params == (). Any require coupling the two would have excluded this real input. The model predicts it.
3. native=true across ALL five vendors (incl. non-native-capable ones): real returns the bare template and forwards params; model matches. The capability gate, not the vendor, is what the model keys on -- correct.
4. Per-slot non-uniformity on the oracle arm (mixed-kind clauses, e.g. [1,[2],'x',{'y':1}]) reproduced pointwise: JSON_QUERY for list/dict, JSON_VALUE otherwise, each embedding its own value. No uniformity claimed and none needed.
5. None-discarding and OrderedSet dedup in the super-class shorten the slot list; model still matches because `vals` is read from the post-super-class params, so [1,None,2] -> 2 slots and [1,2,1] -> 2 slots both agree.

SCOPE EXCLUSIONS -- each independently verified as genuinely out of scope, not a hidden divergence.
- Unenumerated non-native vendor (postgresql/mssql/firebird/''): real RAISES TypeError 'not enough arguments for format string' (func stays ()). The modeled method is total; excluded rather than compared against an exception. mapping.md §2.1 states this and it reproduces.
- Empty / all-None clause ([], [None], [None,None]): real raises EmptyResultSet in In.process_rhs BEFORE the hunk. The model returns ([],[]), which is also the substitution's own value at n=0 ('()' % () == '()'). Unreachable input, not a divergence.
- F() element ([F('id')], [1,F('id')]): batch_process_rhs compiles the expression into the template, so slots and params come apart (verified: '("jsonapp_doc"."id")' with rhs_params == []). No slot<->value bijection exists, so the model makes no claim here.
- Subquery RHS: verified the gold patch wraps the SUBQUERY's own placeholders (sqlite: '... WHERE U0."id" > JSON_EXTRACT(%s, ...)'), and the oracle arm raises JSONDecodeError on a non-JSON param. This is a latent defect of the GOLD PATCH ITSELF, present in the real fixed code, upstream of the spec -- mapping.md §2.1 records it honestly rather than the spec claiming something false.

**MECHANICAL CONTROLS.** (a) Positive control: Solution.lean verifies clean, scripts/lean_verify.sh exit 0. (b) Negative/G-DIFF control: Solution_prepatch.lean is REJECTED, exit 1, with real errors at the token obligation (line 130 rewrite failure, line 132 unsolved goals) -- the spec has discriminating power over the pre-patch behavior and is not vacuous. (c) same_spec(Solution, Solution_prepatch) = True via swebench_unified.markers with the velvet backend: the spec region is byte-identical between gold and twin (pure region diffs empty; only impl/proof differ), spec_view hash 76822671673d4aeec14be3f9a3a60f7d2980d3a937433312e4765aad27439e7c matching the RELAXED_LEAKAGE.md/meta.json record. (d) Bundle's own conformance_check.py re-run independently: exit 0 over 120031 configs, 10374 mark-bearing inputs on the value-holding branch, 0 disagreements -- consistent with my independent live-callee result.

**CONCLUSION.** The two ensures are exactly the gold hunk's two return components, at the right granularity: tokens per-slot and value-dependent (matching the oracle arm's non-uniformity), accompanying values per-ARM and whole-clause (matching that json.py:396 rhs_params = () sits inside the oracle arm after its loop and consults no token). The spec is neither too strong (no reachable input excluded by the require; every documented exclusion independently confirmed unreachable or genuinely unmappable) nor drifted from the patched repo behavior (0/4640 live-callee divergences on a harness demonstrated sensitive to 7 distinct perturbations including the subtle byte-derived one). No diverging input to report.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** RE-MEASURED, NOT INHERITED. Every number below is from a command I ran; RELAXED_LEAKAGE.md was treated as a claim to check.

**IDENTITY.** The relaxation file describes Solution.lean at sha256 c5f3b490...aff081 with spec-view region hash 76822671...39e7c. I confirmed BOTH: sha256sum Solution.lean == c5f3b49098b079c18095e7b43704450342edc3568f32a3fe0655d574eeaff081, and markers.region_hashes(Solution.lean, VelvetBackend)['spec_view'] == 76822671673d4aeec14be3f9a3a60f7d2980d3a937433312e4765aad27439e7c. So the file describes the shipped artifact, not a stale one. IMPORTANT: the prior G-PANEL-3 fail record in meta.json was taken against Solution.lean sha256 3462b45e... -- a DIFFERENT, earlier revision (uniform-token spec, one output component). That finding does not describe this artifact; RELAXED_LEAKAGE.md L13-20 itself records that the earlier revision was made unshippable, and my §3.2 check below independently confirms why.

FACET RE-CONFIRMED = capability-gated per-slot operand-token substitution on a membership RHS, plus the branch-level accompanying-values component. Nothing else.

**SPEC-REGION INTEGRITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True, so the twin test is a genuine spec-discrimination test (impl-only difference).

LOAD-BEARING TEST, run by me (the usual strip-and-reverify):

(a) scripts/lean_verify.sh Solution.lean -> EXIT 0. scripts/lean_verify.sh Solution_prepatch.lean -> EXIT 1, unsolved goal `result_1 = clauseTokens native bareTok wrapOf vals` (the token clause itself). So `native` is forced by twin discrimination.

(b) I copied Solution.lean twice and applied exactly the two edits §3.3 specifies: dropped the second `ensures` and gave the body `return (result, [])`. Result: ensures-DROPPED + wrong impl -> EXIT 0 (the wrong impl VERIFIES); shipped spec + same wrong impl -> EXIT 1 with goal `(if native = true then vals else if wrapHoldsValue = true then [] else vals) = []`, byte-for-byte the goal §3.3 quotes. The removed clause is load-bearing: strip it and a broken impl passes.

(c) §3.2 forced-by-truth: I built a worktree of the upstream repository at 9c92924cd5d164701e2514e1c2d6574126bd7cc2, `git apply --check` clean, applied patch.diff, and replayed the patched KeyTransformIn.process_rhs hunk (json.py:381-402 post-patch) for `__in`=[0,7]. Oracle arm: rhs = (JSON_VALUE('{"value": 0}', '$.value'), JSON_VALUE('{"value": 7}', '$.value')), rhs_params = () -- the two slots carry DIFFERENT tokens (SLOTS_DIFFER True); a list-valued element routes to JSON_QUERY. sqlite/mysql: rhs_params ('0','7'); mariadb JSON_UNQUOTE variant. So the second component is a genuine two-way branch and a single uniform wrapTok is FALSE of the patched code, not merely weaker. I also authored and ran §3.2's mechanized refutation myself (clauseTokU/slotTokU with the two measured token byte-strings): `uniform_cannot_match_real` elaborates, lean_verify EXIT 0.

**NO PROBLEM_STATEMENT DERIVATION OF THE DISCRIMINATOR.** I re-ran the §1 token scan over instance.json. All 21 mechanism tokens (native, has_native, extract, JSON_EXTRACT, JSON_VALUE, wrap, placeholder, %s, process_rhs, rhs, func, KeyTransformIn, register_lookup, token, template, substitut, stored, encod, scalar, bind, capability) count 0 in problem_statement AND 0 in hints_text; the patch uses rhs 12, func 10, process_rhs 2, %s 4. The problem_statement is a pure symptom report (0 rows vs 312 rows, "I would expect ... the same queryset"). It DOES name MySQL/Oracle/SQLite (mysql 2, oracle 1, sqlite 1), which concedes the direction of a backend/capability split -- the relaxation states this concession itself and does not overclaim. What no public sentence gives is what the spec must speak at: that the RHS is built of per-slot operand tokens, that one branch substitutes a per-value token, or that one branch stops forwarding the values.

**SPEC VIEW DISCLOSES NOTHING BEYOND THE FACET.** I lexically scanned the computed spec_view (not the raw file) for 25 repo/vendor/format terms -- json, oracle, mysql, mariadb, sqlite, postgres, vendor, sql, keytransform, process_rhs, has_native, register_lookup, extract, %s, django, field, lookup, placeholder, query, backend, db, unquote, dumps, loads, in_ -- ALL ZERO hits. The changed file, the KeyTransformIn/process_rhs symbols, has_native_json_field, the per-vendor wrapper strings and the `rhs = rhs % func` substitution appear only in mapping.md / conformance_check.py, which are outside markers.spec_view.

**CORE GATES THE ARGUMENT LEANS ON.** G-VERIFY pass (I re-ran: exit 0), G-DIFF pass with same_spec True (I re-ran both sides), G-GOLD pass, G-EQ pass (17/17), G-MUT pass (14/14), G-PBT SOUND, G-RESOLVE pass, G-INTEGRITY pass, G-HYGIENE pass. G-AX skip is the accurate label: meta.json axioms == [] and deep_model_references == [], and bareTok/wrapOf/wrapHoldsValue are ordinary input parameters, so no outside-callee behavior is assumed and there is no ungrounded oracle to echo -- both components are total functions of each listed value's identity, not merely of vals.length. I independently RE-RAN conformance_check.py: exit 0, 120031 configurations over native + sqlite/mysql/mariadb/oracle, exact per-slot token equality and exact equality of the accompanying values, 0 disagreements, 10374 inputs carrying the substitution mark in a listed value's own text on the value-holding branch, 6 out-of-scope unenumerated-vendor configs excluded with the exclusion stated.

**NO BUNDLE FILE ADDRESSED ME.** I grepped RELAXED_LEAKAGE.md, mapping.md, refinement.md and both Lean files for verdict-directive language (must/should record, the honest verdict, do not flag, reviewer/auditor/panel, accept this): no hits. RELAXED_LEAKAGE.md frames itself as "a claim to CHECK, not a disposition to inherit" and its §5 enumerates what it does not claim; it nowhere instructs a verdict. Minor cosmetic staleness noted, not a finding: meta.json string_modeling still says `wrapTok != bareTok` from the pre-revision uniform-token spec, but string_modeling is metadata outside the spec view and the shipped require is the per-value `forall v in vals, wrapOf v != bareTok`.

**CONCLUSION.** The unavoidability argument holds under my own re-derivation: each disclosed facet is held in place either by twin discrimination (native) or by truth about the patched code plus strength against a concretely-admitted wrong implementation (wrapOf per value, wrapHoldsValue / clauseSuppliedValues), and the §3.3 admitted impl is not harmless -- with rhs_params cleared on the sqlite arm the emitted tokens keep inner placeholders and the query cannot bind. The spec view leaks nothing beyond that single facet, and the facet is not derivable from problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.