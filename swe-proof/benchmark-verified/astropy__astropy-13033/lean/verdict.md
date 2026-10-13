# P2 adversarial audit — astropy__astropy-13033

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_plural_boundary.lean`, `atk_4_no_toggle.lean`, `atk_5_always_ok.lean`, `atk_6_singleton_via_opaque.lean`, `atk_7_found_always_list.lean`, `atk_8_expected_untruncated.lean`, `atk_9_drop_empty_branch.lean`, `atk_11_domain_gap.lean`, `atk_12_wording.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10_equiv_echo.lean` |

**Non-vacuity.** The positive control `atk_0_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 same-spec wrong/variant impls run; the only one that verified (atk_10_equiv_echo, an extensionally-equivalent refactor) had its faithful patch materialized and RESOLVED under the official harness (F2P + 20 P2P pass), so it is a correct echo of the gold, not a spec weakness. No impl with a closing clean-axiom proof has a non-resolving faithful patch.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,9 +139,9 @@
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
-      return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
+      -- PRE-PATCH BUG: only the FIRST expected and FIRST present name are named.
+      return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
+        "' as the first column" ++ plural ++ " but found '" ++ colnames.headD "" ++ "'")
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                       false else requiredColumnsRelax
     return .ok newRelax
```

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,9 +139,16 @@
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
-      return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
+      -- PARTIAL DOMAIN: the patched full-collection message only for <= 2 required
+      -- columns (which is all the test suite ever exercises); 3+ required columns
+      -- silently fall back to the misleading pre-patch single-head message.
+      if required.length > 2 then
+        return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
+          "' as the first column" ++ plural ++ " but found '" ++ colnames.headD "" ++ "'")
+      else
+        return .error (className ++ " object is invalid - expected " ++
+          renderNames required ++ " as the first column" ++ plural ++
+          " but found " ++ renderNames (colnames.take required.length))
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                       false else requiredColumnsRelax
     return .ok newRelax
```

Attack 3 — `atk_3_plural_boundary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -134,7 +134,9 @@
   | none => return .ok requiredColumnsRelax
   | some reqCols =>
     let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
-    let plural := if required.length > 1 then "s" else ""
+    -- BOUNDARY: pluralise at >= 1 rather than > 1, so a single required column
+    -- is reported as "the first columns".
+    let plural := if required.length >= 1 then "s" else ""
     if !requiredColumnsRelax && colnames.length == 0 then
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
```

Attack 4 — `atk_4_no_toggle.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -142,9 +142,9 @@
       return .error (className ++ " object is invalid - expected " ++
         renderNames required ++ " as the first column" ++ plural ++
         " but found " ++ renderNames (colnames.take required.length))
-    let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
-                      false else requiredColumnsRelax
-    return .ok newRelax
+    -- CONTROL-FLOW EFFECT: the relaxed regime is never switched off, so a table
+    -- that has acquired all its required columns stays permanently relaxed.
+    return .ok requiredColumnsRelax
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5_always_ok.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,23 +128,12 @@
     (className : String) (requiredColumnsEnabled : Bool)
     (requiredColumns : Option (List String)) (requiredColumnsRelax : Bool)
     (colnames : List String) : Except String Bool := Id.run do
-  if !requiredColumnsEnabled then
-    return .ok requiredColumnsRelax
-  match requiredColumns with
-  | none => return .ok requiredColumnsRelax
-  | some reqCols =>
-    let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
-    let plural := if required.length > 1 then "s" else ""
-    if !requiredColumnsRelax && colnames.length == 0 then
-      return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
-        "' as the first column" ++ plural ++ " but time series has no columns")
-    else if colnames.take required.length != required then
-      return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
-    let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
-                      false else requiredColumnsRelax
-    return .ok newRelax
+  -- UNGROUNDED ORACLE ECHO: never report anything; echo the incoming relax flag.
+  let _ := className
+  let _ := requiredColumnsEnabled
+  let _ := requiredColumns
+  let _ := colnames
+  return .ok requiredColumnsRelax
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6_singleton_via_opaque.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,9 +139,17 @@
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
+      -- A-LEG ATTACK: render a ONE-name collection with the OPAQUE per-element
+      -- platform rendering (repr, which escapes) wrapped in the outer quotes,
+      -- instead of the verbatim f-string interpolation the patch actually uses.
+      -- Probes whether the opaque leaf can be smuggled into the singleton path.
+      let render1 : List String -> String := fun xs =>
+        match xs with
+        | [x] => "'" ++ pyReprStr x ++ "'"
+        | _   => pyListRepr xs
       return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
+        render1 required ++ " as the first column" ++ plural ++
+        " but found " ++ render1 (colnames.take required.length))
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                       false else requiredColumnsRelax
     return .ok newRelax
```

Attack 7 — `atk_7_found_always_list.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,9 +139,11 @@
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
+      -- A-LEG ATTACK: the FOUND side always uses the whole-list rendering, so a
+      -- single present column is reported as ['banana'] rather than 'banana'.
       return .error (className ++ " object is invalid - expected " ++
         renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
+        " but found " ++ pyListRepr (colnames.take required.length))
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                       false else requiredColumnsRelax
     return .ok newRelax
```

Attack 8 — `atk_8_expected_untruncated.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,8 +139,11 @@
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
+      -- RELAX-PATH BOUNDARY: the EXPECTED side names the full configured list
+      -- rather than the relax-truncated `required`, so under the relaxed regime
+      -- the message advertises columns that were not actually being demanded.
       return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
+        renderNames reqCols ++ " as the first column" ++ plural ++
         " but found " ++ renderNames (colnames.take required.length))
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                       false else requiredColumnsRelax
```

Attack 9 — `atk_9_drop_empty_branch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,10 +135,9 @@
   | some reqCols =>
     let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
     let plural := if required.length > 1 then "s" else ""
-    if !requiredColumnsRelax && colnames.length == 0 then
-      return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
-        "' as the first column" ++ plural ++ " but time series has no columns")
-    else if colnames.take required.length != required then
+    -- CONTROL FLOW: the dedicated "time series has no columns" branch is removed,
+    -- so an empty table falls through to the generic mismatch message.
+    if colnames.take required.length != required then
       return .error (className ++ " object is invalid - expected " ++
         renderNames required ++ " as the first column" ++ plural ++
         " but found " ++ renderNames (colnames.take required.length))
```

Attack 10 — `atk_10_equiv_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,23 +128,27 @@
     (className : String) (requiredColumnsEnabled : Bool)
     (requiredColumns : Option (List String)) (requiredColumnsRelax : Bool)
     (colnames : List String) : Except String Bool := Id.run do
-  if !requiredColumnsEnabled then
+  -- ECHO / EQUIVALENT REFACTOR: same behavior, different syntax. The guard is
+  -- inverted with its branches swapped (so plain `rfl` no longer closes the
+  -- goal on an opaque Bool) but the observable behavior is unchanged.
+  if requiredColumnsEnabled then
+    match requiredColumns with
+    | none => return .ok requiredColumnsRelax
+    | some reqCols =>
+      let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
+      let plural := if 1 < required.length then "s" else ""
+      if !requiredColumnsRelax && colnames.length == 0 then
+        return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
+          "' as the first column" ++ plural ++ " but time series has no columns")
+      else if colnames.take required.length != required then
+        return .error (className ++ " object is invalid - expected " ++
+          renderNames required ++ " as the first column" ++ plural ++
+          " but found " ++ renderNames (colnames.take required.length))
+      let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
+                        false else requiredColumnsRelax
+      return .ok newRelax
+  else
     return .ok requiredColumnsRelax
-  match requiredColumns with
-  | none => return .ok requiredColumnsRelax
-  | some reqCols =>
-    let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
-    let plural := if required.length > 1 then "s" else ""
-    if !requiredColumnsRelax && colnames.length == 0 then
-      return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
-        "' as the first column" ++ plural ++ " but time series has no columns")
-    else if colnames.take required.length != required then
-      return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
-    let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
-                      false else requiredColumnsRelax
-    return .ok newRelax
 -- impl-end
 
 -- proof-start
@@ -157,5 +161,5 @@
         (implementation_checkRequiredColumns className requiredColumnsEnabled requiredColumns
           requiredColumnsRelax colnames) := by
   intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames
-  rfl
+  cases requiredColumnsEnabled <;> rfl
 -- proof-end
```

Attack 11 — `atk_11_domain_gap.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,6 +135,11 @@
   | some reqCols =>
     let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
     let plural := if required.length > 1 then "s" else ""
+    -- DOMAIN-GAP ATTACK: on the degenerate input the real repo cannot reach
+    -- without raising IndexError (required == [] and colnames == []), report no
+    -- error at all instead of the spec's empty-name message.
+    if required.isEmpty && colnames.isEmpty then
+      return .ok requiredColumnsRelax
     if !requiredColumnsRelax && colnames.length == 0 then
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
@@ -157,5 +162,8 @@
         (implementation_checkRequiredColumns className requiredColumnsEnabled requiredColumns
           requiredColumnsRelax colnames) := by
   intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames
-  rfl
+  cases requiredColumnsEnabled <;>
+    simp [problem_spec_checkRequiredColumns, checkRequiredColumns,
+          implementation_checkRequiredColumns] <;>
+    aesop
 -- proof-end
```

Attack 12 — `atk_12_wording.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,7 +139,8 @@
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
-      return .error (className ++ " object is invalid - expected " ++
+      -- WORDING: drop the leading class name and reword; the rendering is intact.
+      return .error ("expected " ++
         renderNames required ++ " as the first column" ++ plural ++
         " but found " ++ renderNames (colnames.take required.length))
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
```

Attack 13 — `atk_13_list_glue.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -135,13 +135,19 @@
   | some reqCols =>
     let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
     let plural := if required.length > 1 then "s" else ""
+    -- A-LEG GLUE ATTACK: the opaque per-element rendering is used verbatim, but
+    -- the model-owned separator loses its space (Python's str(list) uses ", ").
+    let render' : List String -> String := fun xs =>
+      match xs with
+      | [x] => pyStrRepr x
+      | _   => "[" ++ String.intercalate "," (xs.map pyReprStr) ++ "]"
     if !requiredColumnsRelax && colnames.length == 0 then
       return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
         "' as the first column" ++ plural ++ " but time series has no columns")
     else if colnames.take required.length != required then
       return .error (className ++ " object is invalid - expected " ++
-        renderNames required ++ " as the first column" ++ plural ++
-        " but found " ++ renderNames (colnames.take required.length))
+        render' required ++ " as the first column" ++ plural ++
+        " but found " ++ render' (colnames.take required.length))
     let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                       false else requiredColumnsRelax
     return .ok newRelax
```

Attack 14 — `atk_14_toggle_truncated.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -142,7 +142,9 @@
       return .error (className ++ " object is invalid - expected " ++
         renderNames required ++ " as the first column" ++ plural ++
         " but found " ++ renderNames (colnames.take required.length))
-    let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
+    -- RELAX SEMANTICS: compare the TRUNCATED `required` instead of the full
+    -- configured list, so relax switches off before all columns have arrived.
+    let newRelax := if requiredColumnsRelax && required == colnames.take required.length then
                       false else requiredColumnsRelax
     return .ok newRelax
 -- impl-end
@@ -157,5 +159,5 @@
         (implementation_checkRequiredColumns className requiredColumnsEnabled requiredColumns
           requiredColumnsRelax colnames) := by
   intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames
-  rfl
+  cases requiredColumnsEnabled <;> cases requiredColumnsRelax <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** problem_spec_checkRequiredColumns is EXACT functional equality to the total pure function checkRequiredColumns (result = checkRequiredColumns ...), discharged by `rfl`. Maximally tight: an impl can verify only if it is Lean-defeq/extensionally equal to the spec function on every input.

**SAME-SPEC:** all 14 attacks + control confirmed True via swebench_unified.markers.same_spec against Solution.lean; all also pass variant_scope.unsound_evasions (no new axiom/sorry/native_decide, obligation statement byte-identical).

**COMMANDS:** per attack `bash scripts/lean_verify.sh <f>.lean` (atk_11..14 used `... 330`). Run 4-at-a-time as concurrent background jobs.

### ATTACK RESULTS (exit code; 1 = genuine `Tactic rfl failed`, not a syntax error — confirmed in each <f>.out):
- atk_1_prepatch (THE REAL PREPATCH BUG: single-head "expected '<req[0]>' ... but found '<colnames[0]>'") -> EXIT 1 rejected. prepatch_reproduced=True. Bundle's own Solution_prepatch.lean also re-run: EXIT 1 (G-DIFF control).
- atk_2_partial_domain (PARTIAL DOMAIN: patched message only for <=2 required columns; 3+ falls back to the misleading single-head form) -> EXIT 1.
- atk_3_plural_boundary (BOUNDARY: plural at >= 1 instead of > 1) -> EXIT 1.
- atk_4_no_toggle (CONTROL-FLOW EFFECT: relaxed regime never switched off) -> EXIT 1.
- atk_5_always_ok (UNGROUNDED ORACLE ECHO: unconditionally .ok requiredColumnsRelax) -> EXIT 1.
- atk_6_singleton_via_opaque (A-LEG: singleton rendered as "'" ++ pyReprStr x ++ "'" i.e. repr-escaped, instead of the verbatim f-string pyStrRepr) -> EXIT 1. The opaque leaf cannot be smuggled into the singleton path.
- atk_7_found_always_list (A-LEG: found side always the whole-list form, so one column reads ['banana'] not 'banana') -> EXIT 1.
- atk_8_expected_untruncated (RELAX BOUNDARY: expected side names full reqCols rather than the relax-truncated required) -> EXIT 1.
- atk_9_drop_empty_branch (CONTROL FLOW: no-columns branch removed) -> EXIT 1.
- atk_10_equiv_echo (EXTENSIONALLY EQUIVALENT refactor: inverted enabled-guard with swapped branches + plural written `1 < n`; proof `cases requiredColumnsEnabled <;> rfl`) -> **EXIT 0, VERIFIES**. `#print axioms correct_checkRequiredColumns` => 'does not depend any axioms' (CLEAN). This made protocol step 2 NON-VACUOUS (the prior pass declared it vacuous).
- atk_11_domain_gap (DOMAIN GAP: returns .ok on the degenerate required==[] && colnames==[] input that the real repo cannot reach without IndexError) -> EXIT 1; goal reduces to `False`, i.e. the spec DOES pin behavior there — no impl may deviate.
- atk_12_wording (message bytes: class-name prefix dropped/reworded) -> EXIT 1.
- atk_13_list_glue (A-LEG GLUE: opaque pyReprStr untouched but the model-owned separator loses its space, ','.join vs ', ') -> EXIT 1.
- atk_14_toggle_truncated (RELAX SEMANTICS: trailing toggle compares the truncated `required` instead of the full configured list) -> EXIT 1.

PROTOCOL STEP 2 — EXECUTED, NOT SPECULATED. atk_10 verified with clean axioms, so its faithful refined patch was materialized at patch_atk10.diff (inverted positive `if self._required_columns_enabled:` guard with the early-return moved to the else; plural as `'s' if 1 < len(required_columns)`; same as_scalar_or_list_str rendering). Checked with `git apply --check` in a base_commit worktree: APPLIES. Differential-tested against the gold-patched method (both function objects lifted by AST from the real core.py): 200000 fuzzed cases, 0 disagreements — a faithful embedding. `run_resolve('astropy__astropy-13033', patch)` => COMPLETED=True, **RESOLVED=True**, note='resolved', patch_successfully_applied=True, FAIL_TO_PASS success=[test_required_columns], PASS_TO_PASS 20/20 success, 0 failures. A resolving candidate is a correct echo of the gold, not a spec weakness => does NOT break the spec.

ORACLE REFUTATION CONTROL (so atk_10's 'resolved' is meaningful evidence rather than a dead oracle): patch_ctl_glue.diff embeds atk_13's list-glue defect (','.join, no space) into the real post-patch helper; `git apply --check` APPLIES; run_resolve => COMPLETED=True, **RESOLVED=False**, note='patch did not resolve in 2 attempts (consistent — not flaky)', patch_successfully_applied=True, F2P failure=[test_required_columns], P2P all success. The oracle CAN refute on this instance, and it discriminates exactly the byte-level message property the spec pins.

MODEL<->PATCH CORRESPONDENCE (independent, not trusting the bundle's own checkers). Built difforacle.py, which LIFTS THE REAL post-patch `_check_required_columns` function object out of the patched core.py by AST (not a transliteration) and diffs it against a transliteration of the Lean spec function with the opaque pyReprStr bound to Python repr. 300000 fuzzed + 16 hand-picked cases over an adversarial name pool (embedded single/double quotes, backslashes, tabs/newlines, NUL, control chars, non-ASCII, emoji, empty). Result: 0 disagreements once `required_columns == []` is excluded. The ONE divergence class (4761/300000) is exactly and only `required_columns == [] AND colnames == []`: the real code raises IndexError on `required_columns[0]` while the model's `headD ""` yields an empty name. This is UNREACHABLE in the repo — `_required_columns` is only ever None, ['time'] (sampled.py:59), or ['time_bin_start','time_bin_size'] (binned.py:72), never []; and atk_11 proves the spec still pins a definite value there, so the gap grants an attacker nothing.

A-LEG AUDIT (the R/I legs are G-CONF's job; concentrated here as instructed). Independent re-derivation over 200000 adversarial/fuzzed lists: Lean pyListRepr composition ('[' ++ ', '.join(pyReprStr x) ++ ']', pyReprStr:=repr) vs the REAL str(list) => 0 disagreements; Lean renderNames vs the REAL as_scalar_or_list_str from patch.diff => 0 disagreements. Discriminating probe xs=["a'b"]: real as_scalar_or_list_str -> 'a'b' (verbatim), Lean renderNames -> 'a'b', repr-escaped alternative -> '"a'b"' — so the verbatim f-string form is the faithful one and the model gets it right; atk_6 attacked precisely this and was rejected. Bundle's own G-AX axiom_check.py re-run: EXIT 0, checked=50104, disagreements=0.

**REFINEMENT.MD AUDIT:** legs 1,2,3,6,6a,7 = R; legs 4,5 = I; leg 6b = A-reference (pyReprStr <-> str.`__repr__` / the per-element rendering str(list) applies). NO A-consumed, NO kind-3. All 9 leg anchors verified textually present in the real post-patch core.py. Axioms region contains 0 `axiom` and exactly 1 `opaque` (pyReprStr), no sorry/admit; the CHANGED op (mismatch-message construction + adaptive single-vs-list rendering) is deeply modeled as pure `def`s renderNames/pyStrRepr/pyListRepr — confirmed each is a def in the pure region, so SPEC_GUIDE 3's ban on axiomatizing a deeply-modeled changed op is satisfied. The A-reference leaf is an UNCHANGED platform builtin the patch never touches (repr's quote choice + escaping tables), and the proof never inspects it: `#print axioms` on the control reports 'does not depend on any axioms'. mapping.md bindings check out against patch.diff (as_scalar_or_list_str <-> renderNames; found side moved to the full leading slice self.colnames[:len(required_columns)]; the not-hasattr-`__len__` scalar branch is genuinely unreachable since both call sites pass lists).

**END-TO-END F2P CHECK:** prepatch produces "expected 'time' as the first columns but found 'time'" (F2P assertion FAILS — the misleading message the issue reports); gold and the atk_10 patch both produce "expected ['time', 'a'] as the first columns but found ['time', 'b']" (F2P assertion PASSES), and both preserve the single-column P2P message "expected 'time' as the first column but found 'banana'".

**CONCLUSION:** verify => correct holds. 14 distinct attacks (>=5 required) spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, A-leg/opaque-boundary, relax-semantics, message-bytes and domain-gap classes; 13 rejected with genuine rfl/unsolved-goal failures, 1 verified and its materialized faithful patch RESOLVED under the official harness. The refutation control proves the oracle is live on this instance. Positive control verifies with clean axioms. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_prepatch.lean`, `atk_2_partial_domain.lean`, `atk_3_plural_boundary.lean`, `atk_4_no_toggle.lean`, `atk_5_always_ok.lean`, `atk_6_singleton_via_opaque.lean`, `atk_7_found_always_list.lean`, `atk_8_expected_untruncated.lean`, `atk_9_drop_empty_branch.lean`, `atk_11_domain_gap.lean`, `atk_12_wording.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10_equiv_echo.lean` |

**Non-vacuity.** The positive control `atk_0_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 same-spec wrong/variant impls run; the only one that verified (atk_10_equiv_echo, an extensionally-equivalent refactor) had its faithful patch materialized and RESOLVED under the official harness (F2P + 20 P2P pass), so it is a correct echo of the gold, not a spec weakness. No impl with a closing clean-axiom proof has a non-resolving faithful patch.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_plural_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_no_toggle.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_always_ok.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_singleton_via_opaque.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_found_always_list.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_expected_untruncated.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_drop_empty_branch.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_equiv_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_domain_gap.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_wording.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_list_glue.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_toggle_truncated.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** problem_spec_checkRequiredColumns is EXACT functional equality to the total pure function checkRequiredColumns (result = checkRequiredColumns ...), discharged by `rfl`. Maximally tight: an impl can verify only if it is Lean-defeq/extensionally equal to the spec function on every input.

**SAME-SPEC:** all 14 attacks + control confirmed True via swebench_unified.markers.same_spec against Solution.lean; all also pass variant_scope.unsound_evasions (no new axiom/sorry/native_decide, obligation statement byte-identical).

**COMMANDS:** per attack `bash scripts/lean_verify.sh <f>.lean` (atk_11..14 used `... 330`). Run 4-at-a-time as concurrent background jobs.

### ATTACK RESULTS (exit code; 1 = genuine `Tactic rfl failed`, not a syntax error — confirmed in each <f>.out):
- atk_1_prepatch (THE REAL PREPATCH BUG: single-head "expected '<req[0]>' ... but found '<colnames[0]>'") -> EXIT 1 rejected. prepatch_reproduced=True. Bundle's own Solution_prepatch.lean also re-run: EXIT 1 (G-DIFF control).
- atk_2_partial_domain (PARTIAL DOMAIN: patched message only for <=2 required columns; 3+ falls back to the misleading single-head form) -> EXIT 1.
- atk_3_plural_boundary (BOUNDARY: plural at >= 1 instead of > 1) -> EXIT 1.
- atk_4_no_toggle (CONTROL-FLOW EFFECT: relaxed regime never switched off) -> EXIT 1.
- atk_5_always_ok (UNGROUNDED ORACLE ECHO: unconditionally .ok requiredColumnsRelax) -> EXIT 1.
- atk_6_singleton_via_opaque (A-LEG: singleton rendered as "'" ++ pyReprStr x ++ "'" i.e. repr-escaped, instead of the verbatim f-string pyStrRepr) -> EXIT 1. The opaque leaf cannot be smuggled into the singleton path.
- atk_7_found_always_list (A-LEG: found side always the whole-list form, so one column reads ['banana'] not 'banana') -> EXIT 1.
- atk_8_expected_untruncated (RELAX BOUNDARY: expected side names full reqCols rather than the relax-truncated required) -> EXIT 1.
- atk_9_drop_empty_branch (CONTROL FLOW: no-columns branch removed) -> EXIT 1.
- atk_10_equiv_echo (EXTENSIONALLY EQUIVALENT refactor: inverted enabled-guard with swapped branches + plural written `1 < n`; proof `cases requiredColumnsEnabled <;> rfl`) -> **EXIT 0, VERIFIES**. `#print axioms correct_checkRequiredColumns` => 'does not depend any axioms' (CLEAN). This made protocol step 2 NON-VACUOUS (the prior pass declared it vacuous).
- atk_11_domain_gap (DOMAIN GAP: returns .ok on the degenerate required==[] && colnames==[] input that the real repo cannot reach without IndexError) -> EXIT 1; goal reduces to `False`, i.e. the spec DOES pin behavior there — no impl may deviate.
- atk_12_wording (message bytes: class-name prefix dropped/reworded) -> EXIT 1.
- atk_13_list_glue (A-LEG GLUE: opaque pyReprStr untouched but the model-owned separator loses its space, ','.join vs ', ') -> EXIT 1.
- atk_14_toggle_truncated (RELAX SEMANTICS: trailing toggle compares the truncated `required` instead of the full configured list) -> EXIT 1.

PROTOCOL STEP 2 — EXECUTED, NOT SPECULATED. atk_10 verified with clean axioms, so its faithful refined patch was materialized at patch_atk10.diff (inverted positive `if self._required_columns_enabled:` guard with the early-return moved to the else; plural as `'s' if 1 < len(required_columns)`; same as_scalar_or_list_str rendering). Checked with `git apply --check` in a base_commit worktree: APPLIES. Differential-tested against the gold-patched method (both function objects lifted by AST from the real core.py): 200000 fuzzed cases, 0 disagreements — a faithful embedding. `run_resolve('astropy__astropy-13033', patch)` => COMPLETED=True, **RESOLVED=True**, note='resolved', patch_successfully_applied=True, FAIL_TO_PASS success=[test_required_columns], PASS_TO_PASS 20/20 success, 0 failures. A resolving candidate is a correct echo of the gold, not a spec weakness => does NOT break the spec.

ORACLE REFUTATION CONTROL (so atk_10's 'resolved' is meaningful evidence rather than a dead oracle): patch_ctl_glue.diff embeds atk_13's list-glue defect (','.join, no space) into the real post-patch helper; `git apply --check` APPLIES; run_resolve => COMPLETED=True, **RESOLVED=False**, note='patch did not resolve in 2 attempts (consistent — not flaky)', patch_successfully_applied=True, F2P failure=[test_required_columns], P2P all success. The oracle CAN refute on this instance, and it discriminates exactly the byte-level message property the spec pins.

MODEL<->PATCH CORRESPONDENCE (independent, not trusting the bundle's own checkers). Built difforacle.py, which LIFTS THE REAL post-patch `_check_required_columns` function object out of the patched core.py by AST (not a transliteration) and diffs it against a transliteration of the Lean spec function with the opaque pyReprStr bound to Python repr. 300000 fuzzed + 16 hand-picked cases over an adversarial name pool (embedded single/double quotes, backslashes, tabs/newlines, NUL, control chars, non-ASCII, emoji, empty). Result: 0 disagreements once `required_columns == []` is excluded. The ONE divergence class (4761/300000) is exactly and only `required_columns == [] AND colnames == []`: the real code raises IndexError on `required_columns[0]` while the model's `headD ""` yields an empty name. This is UNREACHABLE in the repo — `_required_columns` is only ever None, ['time'] (sampled.py:59), or ['time_bin_start','time_bin_size'] (binned.py:72), never []; and atk_11 proves the spec still pins a definite value there, so the gap grants an attacker nothing.

A-LEG AUDIT (the R/I legs are G-CONF's job; concentrated here as instructed). Independent re-derivation over 200000 adversarial/fuzzed lists: Lean pyListRepr composition ('[' ++ ', '.join(pyReprStr x) ++ ']', pyReprStr:=repr) vs the REAL str(list) => 0 disagreements; Lean renderNames vs the REAL as_scalar_or_list_str from patch.diff => 0 disagreements. Discriminating probe xs=["a'b"]: real as_scalar_or_list_str -> 'a'b' (verbatim), Lean renderNames -> 'a'b', repr-escaped alternative -> '"a'b"' — so the verbatim f-string form is the faithful one and the model gets it right; atk_6 attacked precisely this and was rejected. Bundle's own G-AX axiom_check.py re-run: EXIT 0, checked=50104, disagreements=0.

**REFINEMENT.MD AUDIT:** legs 1,2,3,6,6a,7 = R; legs 4,5 = I; leg 6b = A-reference (pyReprStr <-> str.`__repr__` / the per-element rendering str(list) applies). NO A-consumed, NO kind-3. All 9 leg anchors verified textually present in the real post-patch core.py. Axioms region contains 0 `axiom` and exactly 1 `opaque` (pyReprStr), no sorry/admit; the CHANGED op (mismatch-message construction + adaptive single-vs-list rendering) is deeply modeled as pure `def`s renderNames/pyStrRepr/pyListRepr — confirmed each is a def in the pure region, so SPEC_GUIDE 3's ban on axiomatizing a deeply-modeled changed op is satisfied. The A-reference leaf is an UNCHANGED platform builtin the patch never touches (repr's quote choice + escaping tables), and the proof never inspects it: `#print axioms` on the control reports 'does not depend on any axioms'. mapping.md bindings check out against patch.diff (as_scalar_or_list_str <-> renderNames; found side moved to the full leading slice self.colnames[:len(required_columns)]; the not-hasattr-`__len__` scalar branch is genuinely unreachable since both call sites pass lists).

**END-TO-END F2P CHECK:** prepatch produces "expected 'time' as the first columns but found 'time'" (F2P assertion FAILS — the misleading message the issue reports); gold and the atk_10 patch both produce "expected ['time', 'a'] as the first columns but found ['time', 'b']" (F2P assertion PASSES), and both preserve the single-column P2P message "expected 'time' as the first column but found 'banana'".

**CONCLUSION:** verify => correct holds. 14 distinct attacks (>=5 required) spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, A-leg/opaque-boundary, relax-semantics, message-bytes and domain-gap classes; 13 rejected with genuine rfl/unsolved-goal failures, 1 verified and its materialized faithful patch RESOLVED under the official harness. The refutation control proves the oracle is live on this instance. Positive control verifies with clean axioms. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

METHOD (independent, not an echo of the retained record). Reference = base_commit 298ccb478e6bf092953bca67a3d29dc6c35f6752 with patch.diff APPLIED, in a fresh worktree from the upstream repository (git apply clean). Confirmed the applied tree contains the fixed method (nested as_scalar_or_list_str + full-slice found side), so I compared the model against the FIXED behavior, not the base.

1. REAL-CALLEE DIFFERENTIAL (not a replica). I extracted the actual `_check_required_columns` source text out of the patched worktree's astropy/timeseries/core.py by regex and exec'd it, driving it with a stub whose `__class__` property yields the right `__name__` (avoids the erfa import wall — `import astropy` fails in this env, so the bundle's own decision to drive the observables directly is justified, but I did NOT reuse the bundle's oracle). Compared against a fresh transliteration of Solution.lean's pure region that I wrote from the Lean text, interpreting the `opaque pyReprStr` as Python `repr`.
   - Exhaustive: enabled x relax x requiredColumns in {None} u lists<=3 from a 4-name pool (incl. "") x colnames lists<=3 = same pool.
   - Fuzz: 300k random cases, adversarial name pool (embedded single AND double quotes, backslash, tab, newline, \x01, non-ASCII "naive"/snowman, bare quote chars, mixed a'b\"c, empty string), with 50% of cases seeded to share a required prefix so the mismatch/relax-toggle branches are actually hit, plus a 10% forced-empty-colnames arm.
   - Result: 329,240 cases, all disagreements fall in the single class above. Zero error/error message mismatches (byte-for-byte), zero ok/ok relax-flag mismatches. So the adaptive single-vs-list rendering, the `str(list)` per-element `repr` escaping (incl. the double-quote switch on names embedding a single quote — verified live: required ["it's",'a'] vs ["it's",'b\"q'] reproduces `["it's", 'a']` exactly), the pluralisation, the truncated found slice, the no-columns branch and the relax toggle all match the real callee.

2. SPEC IS NOT TOO STRONG / NOT DRIFTED ON REACHABLE INPUTS. Hand-checked against the real callee: F2P scenario required ['time','a'] / present ['time','b'] -> "expected ['time', 'a'] as the first columns but found ['time', 'b']" (byte-identical to the test_patch assertion); preserved single-column wording 'time'/'banana' (byte-identical to the P2P assertion); BinnedTimeSeries two-column case; required ['time'] with colnames ['c','a','b'] -> found 'c'; no-columns branch. All MATCH.

3. DIRECTION / DISCRIMINATION. Solution.lean: lean_verify.sh exit 0 and `#print axioms correct_checkRequiredColumns` => "does not depend on any axioms" — no sorryAx, and the opaque pyReprStr is genuinely never consumed by the proof (a true A-reference, so no axiom smuggles in the changed op). Solution_prepatch.lean: lean_verify.sh exit 1, `rfl` fails against the same spec — the spec does discriminate the pre-patch single-head message, confirming it models post-patch and is not vacuous.

4. **SPEC REGION INTEGRITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) = True — spec region byte-identical, so the prepatch failure is attributable to the impl region alone and no prose edit voids the record.

5. BUNDLE HARNESSES (secondary, run for corroboration only): conformance_check.py checked=120010 disagreements=0 status=pass; axiom_check.py checked=50104 disagreements=0 status=pass.

**ADJUDICATION.** The lone disagreement is a totality artifact on an input no repo code path can produce, on a branch the patch does not touch, explicitly scoped out in mapping.md. Calling it UNFAITHFUL would condemn a spec that reproduces the real fixed callee byte-for-byte everywhere it can be reached — including the exact message the F2P test demands. Caveat recorded for completeness: the Lean spec carries no pre-conditions region asserting requiredColumns nonempty, so the exclusion rests on repo-level reachability plus mapping.md's documented domain rather than on a machine-checked precondition; a future consumer that instantiated requiredColumns := some [] would be held to a message the real code never emits. That is a documentation-tier observation, not a faithfulness break on the modeled domain.

Counterexample / evidence:

```
Only disagreement class over 329,240 differentially-fuzzed inputs against the REAL patched callee: requiredColumns=[] AND colnames=[] AND relax=false AND enabled=true -> real IndexError vs model graceful .error. Reachability refuted: an exhaustive grep of the base_commit worktree for assignments to `_required_columns` yields exactly three sites — core.py:48 `= None`, sampled.py:59 `= ['time']`, binned.py:72 `= ['time_bin_start','time_bin_size']` — and zero `= []` anywhere in astropy/ (incl. tests, docs/rst). The empty-list value is therefore not producible by any repo code path. The divergence is also NOT a patch delta: `required_columns[0]` in the no-columns branch is byte-identical pre- and post-patch (patch.diff never touches that branch; `grep -c 'time series has no columns' patch.diff` = 0), so it is a pre-existing CPython partiality, and the Lean `headD ""` is the standard totalization of `xs[0]` explicitly documented in mapping.md ('xs[0] (head, lists nonempty here) | xs.headD "" | head of a nonempty list').
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage/gold-reconstruction review, astropy__astropy-13033 (lean). NO relaxation in this bundle: meta.json has no `relaxed_leakage` key (checked: absent, not False-with-doc) and no RELAXED_LEAKAGE.md exists in the bundle root or lean/ -- confirmed by find. So this is a plain leakage judgement, not an inherited disposition; G-LEAK is recorded status=pass / 'spec view clean' with an empty failures list, which is the honest recording for what I measured.

**WHAT I RAN.**

(1) Regenerated the consumer spec view myself with markers.spec_view(Solution.lean, get_backend('lean').language): sha256 = b1f9c17ceaedc90b4ae1bdbcf251162ededa67ba78c3bc31af642a7595c37fab, byte-matching meta.json gates.G-HYGIENE.data.region_hashes.spec_view. Both impl and proof regions collapse to placeholders, so the consumer sees only the module docstring, the axioms comment, `opaque pyReprStr`, the pure region (pyStrRepr/pyListRepr/renderNames/checkRequiredColumns) and problem_spec_checkRequiredColumns.

(2) markers.same_spec(Solution.lean, Solution_prepatch.lean) = True -- spec region byte-identical, so the prepatch rival is judged against the same contract.

(3) scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no `sorry`; grep confirms no 'sorry' token). Appended `#print axioms correct_checkRequiredColumns` in a temp copy: 'does not depend on any axioms' -- no sorryAx, no propext/Classical leakage, and meta axioms=[] is accurate (the one abstract leaf pyReprStr is `opaque`, not an `axiom`; nothing about it is consumed).

(4) Load-bearing test: scripts/lean_verify.sh Solution_prepatch.lean FAILS (rfl cannot close the goal; error shows the single-head rendering not reducing to renderNames). So the rendering clause in the spec is load-bearing, not decoration -- the spec genuinely rejects the pre-patch behavior.

(5) Re-ran leakage.screen over the regenerated view against the frozen row: passed=True, hard_failures=[], warnings=[].

LEAK SURFACE, CHECKED BY HAND (not just the lexical screen). Patched file astropy/timeseries/core.py and its dotted form: absent from the view. Diff markers: absent. All 14 gold changed lines: none present normalized (longest, `.format(self.__class__.__name__, required_columns[0], ...)`, 77 chars, absent). Fix-introduced helper `as_scalar_or_list_str`: absent -- the spec calls its analogue `renderNames`, and the scalar `hasattr(obj,'__len__')` branch is not modeled at all (`hasattr`/`__len__` absent from the view), so the view does not even mirror the gold's branch shape. `BaseTimeSeries`: absent.

Two identifiers I checked beyond the screen's reach, and why each is clean: (a) `checkRequiredColumns` is the camelCase of the patched `_check_required_columns`, which the underscore-sensitive screen would miss -- but the public problem_statement's own title is 'misleading exception when required column check fails' and its repro body names `ts._required_columns` verbatim, so this name localizes nothing the issue does not already say; (b) `colnames` is not a patched symbol -- it is astropy's pre-existing documented Table attribute, read unchanged on both the removed and added gold lines, so it names an unchanged public API rather than the edit.

**WHY THE FORMAT SPECIFICS ARE NOT A LEAK.** The sharpest candidate is the docstring's rendering rule (one name -> single-quoted verbatim; several -> whole list via per-element `repr` joined by ', ' in brackets; found side sliced to the required length) and the `f"'{x}'"` / `str(list)` notation in the comments. These are not derivable from the problem_statement alone -- the exact new message appears only in hints_text, which I did not credit as public. I still judge NO-LEAKAGE, on two grounds I verified rather than assumed.

First, this is behavior the acceptance test pins byte-for-byte: FAIL_TO_PASS test_required_columns asserts the literal "expected ['time', 'a'] as the first columns but found ['time', 'b']", so a spec that left the rendering free would verify for impls that fail the hidden test, breaking verify=>correct. Mandatory precision, not edit-revelation. Second, leakage doctrine here targets the edit, not the behavior: no diff line, no patched path, no fix-invented identifier, no bug->fix mechanism.

The one contrastive clause, 'lists the full expected and found column sets rather than only their first entries', is fully public -- the problem_statement itself shows required=["time","flux"] yielding "expected 'time' ... but found 'time'", i.e. first-entries-only, and states the expected behavior as an exception informing users which required columns are missing. `f"'{x}'"` is a near-neighbour of gold's `return f"'{obj}'"` but not a reproduction (renamed binder, no `return`), and the single-quoted form is already on display in the issue's own error text. This is a different situation from the corpus's genuine relaxations (e.g. astropy-7671, whose spec view handed over a character-exact regex with test-INVISIBLE components); here every pinned detail is test-visible.

No file in this bundle addresses the reviewer: leakage.reviewer_directed() returns [] for Solution.lean, Solution_prepatch.lean, refinement.md and mapping.md, and none of them contains 'auditor', 'reviewer', 'panel', 'NO-LEAKAGE', 'honest recording' or 'verdict'. Nothing told me what to submit.

SUPPORTING GATES the disposition leans on, re-read as recorded: G-DIFF pass (prepatch fails -- which I independently reproduced), G-GOLD pass, G-HYGIENE pass with a spec_view hash I reproduced byte-for-byte, G-INTEGRITY pass (instance.json byte-identical), patch_equals_gold=True, G-CONF pass (transliterated shadow), G-AX pass (50104 checks, 0 disagreements, binding opaque pyReprStr to the real str.`__repr__`/str(list)), G-MUT killed 20/20.

ONE RECORD-HYGIENE DEFECT, out of scope for this gate but worth routing: meta.json's TOP-LEVEL region_hashes block is stale against the current Solution.lean. It records spec_view=f5f03b96..., pure=d8c3a7e1..., impl=72b401c7..., whereas the live file computes b1f9c17c... / cbd26fa4... / f48ba58b..., and the fresh values are exactly what gates.G-HYGIENE.data.region_hashes carries. The gate-owned record is correct and my leakage verdict rests on it; only the top-level convenience copy drifted. Not a leakage finding and not a reason to fail this gate -- flagging it because a freshness check reading the top-level block instead of the gate block would compare against bytes that no longer exist.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.