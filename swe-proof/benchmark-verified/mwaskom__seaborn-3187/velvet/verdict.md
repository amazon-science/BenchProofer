# P2 adversarial audit — mwaskom__seaborn-3187

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 26 admissible attacks re-run of 26 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 26 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_01_prepatch.lean`, `atk_02_carrier_int_reencode.lean`, `atk_03_partial_domain_nan.lean`, `atk_04_boundary_short_list.lean`, `atk_05_ungrounded_oracle.lean`, `atk_06_swapped_arms.lean`, `atk_07_log_path_substituted.lean`, `atk_08_padded_argument.lean`, `atk_09_sharedterm_oracle.lean`, +10 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_17_alias_echo_modes_arm.lean`, `atk_18_domain_escape_noswitch_arm.lean`, `atk_19_domain_escape_logrenderer.lean`, `atk_23_dblguard_oracle_bothon.lean`, `atk_24_dblguard_oracle_offsetonly.lean`, `atk_25_dblguard_oracle_scionly.lean`, `atk_26_maximal_dblguard_oracle.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl was found. Seven same-spec impls VERIFY (atk_17, atk_18, atk_19 = alias-echo / domain-escape shapes; atk_23, atk_24, atk_25, atk_26 = double-guard sharedTerm-oracle shapes). ALL SEVEN had their faithful refined patches materialized, git apply --check'd at base_commit, and RUN through the official harness: all seven RESOLVED (F2P 2/2, P2P 248/248 each). They are behaviourally equal to the gold patch, not counterexamples: an in-container sweep (beh.py, 36,963 firing observations over 3 ScalarFormatter configurations x 11 view intervals x 411 tick lists incl. 400 fuzzed x 3 non-both-off switch settings) found 0 cases where an empty-shared-term rendering differs from the both-off rendering. verify⇏correct is NOT falsified.
```

**Attacks re-run (26):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,9 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg true true ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +195,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +253,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg true true ticks
       return labels
     -- impl-end
 end
@@ -259,4 +265,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 2 — `atk_02_carrier_int_reencode.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if !(ticks.all (fun t => t.floor == t)) then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if !(ticks.all (fun t => t.floor == t)) then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 3 — `atk_03_partial_domain_nan.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ticks.any (fun t => t.isNaN || !t.isFinite) then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ticks.any (fun t => t.isNaN || !t.isFinite) then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 4 — `atk_04_boundary_short_list.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ticks.length <= 1 then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ticks.length <= 1 then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 5 — `atk_05_ungrounded_oracle.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,10 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| ∃ (om sm : Bool), labels = renderTicks cfg om sm ticks ∧
+        sharedTerm cfg om sm ticks = ""
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +196,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +254,11 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| ∃ (om sm : Bool), labels = renderTicks cfg om sm ticks ∧
+        sharedTerm cfg om sm ticks = ""
       return labels
     -- impl-end
 end
@@ -259,4 +267,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 6 — `atk_06_swapped_arms.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,23 +185,35 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      return ownLabels
+    else
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
-    else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
-      return ownLabels
     -- impl-end
 
 prove_correct legendLabels by
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +253,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
-      let labels :| labels = renderLog cfg ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderLog cfg ticks
       return labels
     -- impl-end
 end
@@ -259,4 +265,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 7 — `atk_07_log_path_substituted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,9 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +195,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +253,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
-      let labels :| labels = renderLog cfg ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +265,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 8 — `atk_08_padded_argument.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,10 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      let padded : List Float := ticks ++ [9007199254740992.0]
+      let raw :| raw = renderTicks cfg false false padded
+      return raw.take ticks.length
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +196,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +254,12 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      let padded : List Float := ticks ++ [9007199254740992.0]
+      let raw :| raw = renderTicks cfg false false padded
+      return raw.take ticks.length
     -- impl-end
 end
 
@@ -259,4 +267,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 9 — `atk_09_sharedterm_oracle.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true true ticks = "" then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true true ticks = "" then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 10 — `atk_10_asym_oracle_offset_only.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true false ticks = "" then
+        let labels :| labels = renderTicks cfg true false ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true false ticks = "" then
+        let labels :| labels = renderTicks cfg true false ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 11 — `atk_11_asym_oracle_sci_only.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg false true ticks = "" then
+        let labels :| labels = renderTicks cfg false true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg false true ticks = "" then
+        let labels :| labels = renderTicks cfg false true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 12 — `atk_12_site_b_only_fix.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,9 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg true true ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +195,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +253,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +265,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 13 — `atk_13_ownlabels_on_modes_arm.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,8 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      return ownLabels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +194,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +252,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +264,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 14 — `atk_14_smuggle_choice_pred.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,10 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| (sharedTerm cfg true true ticks ≠ "" →
+        labels = renderTicks cfg false false ticks)
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +196,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +254,11 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| (sharedTerm cfg true true ticks ≠ "" →
+        labels = renderTicks cfg false false ticks)
       return labels
     -- impl-end
 end
@@ -259,4 +267,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 15 — `atk_15_empty_ticks_oracle.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ticks.length == 0 then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ticks.length == 0 then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 16 — `atk_16_reversed_labels.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,9 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      let raw :| raw = renderTicks cfg false false ticks
+      return raw.reverse
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +195,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +253,11 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      let raw :| raw = renderTicks cfg false false ticks
+      return raw.reverse
     -- impl-end
 end
 
@@ -259,4 +265,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 17 — `atk_17_alias_echo_modes_arm.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,12 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if ownLabels == renderTicks cfg false false ticks then
+        return ownLabels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +198,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +256,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +268,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 18 — `atk_18_domain_escape_noswitch_arm.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,23 +185,39 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
-      return ownLabels
+      if ownLabels == renderTicks cfg false false ticks then
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
+      else
+        return ownLabels
     -- impl-end
 
 prove_correct legendLabels by
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +257,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +269,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 19 — `atk_19_domain_escape_logrenderer.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,23 +185,39 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
-      return ownLabels
+      if ownLabels == renderLog cfg ticks then
+        let labels :| labels = renderLog cfg ticks
+        return labels
+      else
+        return ownLabels
     -- impl-end
 
 prove_correct legendLabels by
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +257,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +269,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 20 — `atk_20_logarm_numeric_alias.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,9 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +195,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +253,14 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
-      let labels :| labels = renderLog cfg ticks
-      return labels
+      if renderLog cfg ticks == renderTicks cfg false false ticks then
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
+      else
+        let labels :| labels = renderLog cfg ticks
+        return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +269,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 21 — `atk_21_observable_equal_oracle.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,13 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if renderTicks cfg true true ticks == renderTicks cfg false false ticks then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +199,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +257,15 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if renderTicks cfg true true ticks == renderTicks cfg false false ticks then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +273,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 22 — `atk_22_escape_on_empty_ticks.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,23 +185,39 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
-      return ownLabels
+      if ticks.length == 0 then
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
+      else
+        return ownLabels
     -- impl-end
 
 prove_correct legendLabels by
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,16 +257,10 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
+      let labels :| labels = renderTicks cfg false false ticks
       return labels
     -- impl-end
 end
@@ -259,4 +269,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 23 — `atk_23_dblguard_oracle_bothon.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,14 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true true ticks == "" &&
+         (renderTicks cfg true true ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +200,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +258,16 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true true ticks == "" &&
+         (renderTicks cfg true true ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +275,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 24 — `atk_24_dblguard_oracle_offsetonly.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,14 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true false ticks == "" &&
+         (renderTicks cfg true false ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg true false ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +200,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +258,16 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true false ticks == "" &&
+         (renderTicks cfg true false ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg true false ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +275,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 25 — `atk_25_dblguard_oracle_scionly.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,14 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg false true ticks == "" &&
+         (renderTicks cfg false true ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg false true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +200,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +258,16 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg false true ticks == "" &&
+         (renderTicks cfg false true ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg false true ticks
+        return labels
+      else
+        let labels :| labels = renderTicks cfg false false ticks
+        return labels
     -- impl-end
 end
 
@@ -259,4 +275,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

Attack 26 — `atk_26_maximal_dblguard_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,15 +185,24 @@
   do
     -- impl-start
     if modesAvailable then
-      -- Render with BOTH shared-term abbreviation modes turned off, so nothing
-      -- is hoisted out of the labels (the only faithful choice for a legend).
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true true ticks == "" &&
+         (renderTicks cfg true true ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        if sharedTerm cfg true false ticks == "" &&
+           (renderTicks cfg true false ticks).length == ticks.length then
+          let labels :| labels = renderTicks cfg true false ticks
+          return labels
+        else
+          if sharedTerm cfg false true ticks == "" &&
+             (renderTicks cfg false true ticks).length == ticks.length then
+            let labels :| labels = renderTicks cfg false true ticks
+            return labels
+          else
+            let labels :| labels = renderTicks cfg false false ticks
+            return labels
     else
-      -- No shared-term modes exist on this renderer: nothing is configured and
-      -- the legend shows exactly its own labels.
       return ownLabels
     -- impl-end
 
@@ -201,7 +210,25 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
 
 /- Build the (levels, labels) of a brief numeric legend for the classic
    (function-level) plotting interface, where the tick spacing may be linear or
@@ -241,17 +268,26 @@
   do
     -- impl-start
     if isLog then
-      -- Logarithmic axis: the log renderer is used unchanged; the legend
-      -- shows exactly its labels for this installation.
       let labels :| labels = renderLog cfg ticks
       return labels
     else
-      -- Linear axis: render with BOTH shared-term abbreviation modes off so
-      -- nothing is hoisted out of the labels.
-      let offsetMode : Bool := false
-      let scaleMode : Bool := false
-      let labels :| labels = renderTicks cfg offsetMode scaleMode ticks
-      return labels
+      if sharedTerm cfg true true ticks == "" &&
+         (renderTicks cfg true true ticks).length == ticks.length then
+        let labels :| labels = renderTicks cfg true true ticks
+        return labels
+      else
+        if sharedTerm cfg true false ticks == "" &&
+           (renderTicks cfg true false ticks).length == ticks.length then
+          let labels :| labels = renderTicks cfg true false ticks
+          return labels
+        else
+          if sharedTerm cfg false true ticks == "" &&
+             (renderTicks cfg false true ticks).length == ticks.length then
+            let labels :| labels = renderTicks cfg false true ticks
+            return labels
+          else
+            let labels :| labels = renderTicks cfg false false ticks
+            return labels
     -- impl-end
 end
 
@@ -259,4 +295,22 @@
   loom_solve <;> subst_vars <;>
     first
       | (intro _; exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩)
-      | simp_all [renderTicks_length, renderLog_length]
+      | (intro _; exact ⟨true, true, rfl, by simp_all⟩)
+      | (intro _; exact ⟨true, false, rfl, by simp_all⟩)
+      | (intro _; exact ⟨false, true, rfl, by simp_all⟩)
+      | (intro _; refine ⟨false, false, ?_, sharedTerm_none _ _ (by simp_all)⟩; simp_all)
+      | (intro _; refine ⟨true, true, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨true, false, rfl, ?_⟩; simp_all)
+      | (intro _; refine ⟨false, true, rfl, ?_⟩; simp_all)
+      | (intro _; split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (intro _; first
+            | exact ⟨false, false, rfl, sharedTerm_none _ _ (by simp_all)⟩
+            | exact ⟨true, true, rfl, by simp_all⟩
+            | exact ⟨true, false, rfl, by simp_all⟩
+            | exact ⟨false, true, rfl, by simp_all⟩
+            | simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | (split <;> simp_all [sharedTerm_none, renderTicks_length, renderLog_length])
+      | simp_all only [renderTicks_length, renderLog_length]
+      | simp_all [renderTicks_length, renderLog_length, sharedTerm_none]
+      | grind [renderTicks_length, renderLog_length, sharedTerm_none]
+      | rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SETUP.** Worktree at base_commit 22cdfb0c93f8ec78492d87edb810f10cb7f57a31 = (git worktree add --detach). All 26 attacks + pos_gold + pos_gold_myproof confirmed same_spec=True (26/26 + 2/2). Generators gen.py/gen2.py/gen3.py splice ONLY the two impl regions and the two prove_correct bodies (both elided by spec_view); axioms/pure/pre/post byte-identical.

VERIFY COMMAND: bash scripts/lean_verify.sh <atk>.lean  — run 4-at-a-time as background jobs.

POSITIVE CONTROLS (non-vacuity): pos_gold.lean (byte-identical shipped Solution.lean) EXIT=0; pos_gold_myproof.lean (gold impl rebuilt through MY wide `first | ...` proof alternation) EXIT=0 — proving the alternation given to every attack is not itself why any attack failed.

**PREPATCH:** atk_01_prepatch.lean (both switches left at default true/true at BOTH sites) EXIT=1 — prepatch bug reproduced.

19 REJECTED (EXIT=1): atk_01 prepatch; atk_02 carrier-gap re-encode of the prior pass's named counterexample (gold on integral ticks, prepatch off them); atk_03 partial-domain (wrong exactly where a tick is non-finite, i.e. outside `renders`); atk_04 boundary (modes left on for tick lists of length <= 1); atk_05 ungrounded-oracle echo (postcondition echoed into the choice predicate — Findable elaboration failure, contributes no tightness evidence); atk_06 control-flow-effect (arms of legendLabels swapped); atk_07 log path substituted with the numeric renderer; atk_08 padded argument (render ticks++[2^53], return the prefix) — rejected ON THE LOAD-BEARING PINNING CONJUNCT, goal `List.take ticks.length (renderTicks cfg false false (ticks ++ [9007199254740992.0])) = renderTicks cfg false false ticks`, confirming refinement.md A4's claim that the `∃ om sm, labels = renderTicks cfg om sm ticks` conjunct is not decoration; atk_09/10/11 sharedTerm-oracle shapes (both-on, offset-only, sci-only); atk_12 site-B-only fix; atk_13 ownLabels returned on the modes arm; atk_14 assumption-smuggle in the choice predicate (Findable, no tightness evidence); atk_15 modes left on for empty tick lists; atk_16 post-processing (labels reversed); atk_20 log arm aliased through the numeric renderer; atk_21 observable-equality oracle; atk_22 escape on empty ticks.

**SPEC IS TIGHTER THAN THE ONE THE PRIOR G-EQ PASS AUDITED.** atk_09 re-encodes the prior pass's atk_13_sharedterm_oracle, which that pass recorded as VERIFYING. Here it FAILS (EXIT=1) on the LENGTH clause: `⊢ (renderTicks cfg true true ticks).length = ticks.length` is not derivable, because `renderTicks_length` is gated on `renders cfg om sm ticks` and the method's require supplies that domain at (false,false) ONLY. Consistent with the spec hash having moved (G-EQ recorded sources/Solution.lean=6524c567...; G-AX/G-GOLD/G-HYGIENE record 6d339e20...). Same failure for the two asymmetric variants atk_10/atk_11. I therefore did NOT retain the prior verdict for these labels and re-derived it.

7 VERIFYING IMPLS — ALL MATERIALIZED AND RESOLVED (the mandatory step):
  atk_17_alias_echo_modes_arm      verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_18_domain_escape_noswitch_arm verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248) [attempt 2/3, flaky]
  atk_19_domain_escape_logrenderer  verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248) [attempt 3/3, flaky]
  atk_23_dblguard_oracle_bothon     verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_24_dblguard_oracle_offsetonly verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_25_dblguard_oracle_scionly    verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_26_maximal_dblguard_oracle    verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
Commands: python mkpatch.py and mkpatch2.py to materialize; `git -C apply --check <atk>.diff` (7/7 APPLIES-OK); `python resolve.py <atk>` which calls swebench_unified.harness.run_resolve('mwaskom__seaborn-3187', patch).

WHY atk_23-26 ARE THE STRONGEST SHAPES AND WHY THEY ARE BEHAVIOURALLY GOLD. They defeat the length obstacle that killed atk_09/10/11 by guarding on BOTH `sharedTerm cfg om sm ticks == ""` AND `(renderTicks cfg om sm ticks).length == ticks.length`, discharging both ensures conjuncts with no axiom. Their faithful patches leave the two shared-term modes ENABLED wherever the real ScalarFormatter would hoist nothing. They still resolve because an empty shared term FORCES the both-off labels: structurally, ScalarFormatter.get_offset() returns '' iff orderOfMagnitude==0 and offset==0 (matplotlib 3.7.2, read in-container), while `__call__` computes xp=(x-offset)/`10**oom` and `_set_format` derives the format from (locs-offset)/`10**oom`, so oom==offset==0 makes both the value and the format string coincide with the both-off rendering. Measured, not just argued: beh.py in the instance container — 36,963 oracle-firing observations, 0 differences, 0 skips.

A-LEG CORRESPONDENCE AUDIT (the focus of this role; R/I left to G-CONF, which is legitimately conf_skip=true here since the observable is the callee's output verbatim).
  * A1b (`modesAvailable : Bool` <-> the TWO hasattr guards collapsed into ONE boolean) — the load-bearing R claim, since one boolean cannot express one setter present and the other absent. VERIFIED in-container (probe.py): of 17 Formatter subclasses across matplotlib.ticker + matplotlib.dates, exactly 1 (ScalarFormatter) has both setters, 16 have neither, and EXACTLY-ONE-SETTER == [] — so the guards are indeed true together or false together and the single boolean is faithful. Also confirmed over the five kinds Continuous.`_get_formatter` can install (StrMethodFormatter, FuncFormatter, LogFormatterSciNotation, EngFormatter, ScalarFormatter): only the last carries them.
  * A4/A5 (`renderTicks` / `sharedTerm` A-consumed <-> format_ticks / get_offset) — the pinning conjunct is genuinely load-bearing, demonstrated by atk_08's rejection on exactly that goal (above), and the shared-term clause is what discriminates the patch (negative control below).
  * B2 (`renderLog cfg ticks` A-consumed, handle included) — the doc's claim that the handle is load-bearing is correct: LogFormatter.`__call__` reads self.axis.get_view_interval(). atk_07 (log path substituted) and atk_20 (log arm aliased through the numeric renderer) are both rejected, so the log arm's pin holds.
  * A1e/B1c (the `renders`/`rendersLog` domain requires) — atk_03 (non-finite ticks) is rejected, so the domain restriction is not a loophole for hard inputs.
  * 18/18 legs are R (9), A-consumed (4) or I (5). NO kind-3 leg. deep_model_references == [] and no axiom models the function under change (renderTicks/sharedTerm/renderLog are all UNCHANGED matplotlib callees), so section C's claim holds.

**NOTABLE:** atk_18 and atk_19 are genuine DOMAIN ESCAPES that verify. On the modesAvailable=FALSE arm the spec supplies NO `renders`/`rendersLog` guard, yet an impl may still evaluate `renderTicks cfg false false ticks` (atk_18) or even `renderLog cfg ticks` (atk_19) there — the latter reaching a renderer site A never constructs, with no correspondence row in refinement.md. Both resolve, so this is not a spec break; I probed the latent risk that the added call could RAISE where gold does not (escape.py: EngFormatter-arm gold vs the added LogFormatter over 6 boundary installs incl. (-9e307,9e307), nan and inf ticks) and found agreement in every case (0 divergences). Recorded as a hardness observation, not a finding.

NEGATIVE CONTROL (proving my resolves are meaningful and the oracle discriminates): negctl_site_a_only.diff applies the gold edit at site A ONLY. It APPLIES-OK and does NOT resolve — F2P 1/2, failing tests/test_relational.py::TestRelationalPlotter::test_legend_has_no_offset, consistent across 3 attempts. So the harness detects a half-fix, and 7/7 resolves are not a blind oracle.

INFRASTRUCTURE NOTE (not scored as a spec verdict): the first 4-way-parallel resolve of atk_23 returned `docker.errors.ImageNotFound 404 ... No such image: sha256:63840fa...` with no report in 3 tries — an image race under parallel load, not a non-resolve. Re-run SERIALLY it RESOLVED (F2P 2/2, P2P 248/248).

LEDGER DEFECT FOUND (does not affect this gate's pass/fail; flagged for the bundle owner). meta.json is STALE with respect to the frozen Solution.lean: its `axioms` array names `renderTicks / labelValue` and claims `renderTicks_faithful: ... labelValue(label_i) == tick_i` with an explicit |t| <= 2^53 guard, and `float_modeling` says "tick values modeled as Int restricted to the float-exact range |t| <= 2^53". The shipped spec contains NO labelValue, NO renderTicks_faithful and NO `List Int` — ticks are `List Float` with no carrier restriction, and the discriminating axiom is `sharedTerm_none`. refinement.md A1 itself records that the List Int carrier was REFUTED by an earlier G-EQ pass; meta.json's axioms/float_modeling fields were never updated to match. Consistent with the spec-hash move noted above.

**VERDICT:** SOUND. 26 distinct same-spec wrong impls (26/26 same_spec=True) spanning prepatch, prior-counterexample re-encode, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, padded/reversed/aliased argument, half-fix, swapped-arm, assumption-smuggle, domain-escape and six oracle shapes — well past the >=5 distinct-attack floor. 19 rejected; 7 verified, and EVERY ONE of those 7 had its faithful refined patch materialized, git apply --check'd and RUN through the official harness, where all 7 RESOLVED. Positive controls verify, prepatch reproduced, negative control correctly does not resolve. No verifying wrong impl exists => verify⇏correct is NOT falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 26 admissible attacks re-run of 26 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 26 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_01_prepatch.lean`, `atk_02_carrier_int_reencode.lean`, `atk_03_partial_domain_nan.lean`, `atk_04_boundary_short_list.lean`, `atk_05_ungrounded_oracle.lean`, `atk_06_swapped_arms.lean`, `atk_07_log_path_substituted.lean`, `atk_08_padded_argument.lean`, `atk_09_sharedterm_oracle.lean`, +10 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_17_alias_echo_modes_arm.lean`, `atk_18_domain_escape_noswitch_arm.lean`, `atk_19_domain_escape_logrenderer.lean`, `atk_23_dblguard_oracle_bothon.lean`, `atk_24_dblguard_oracle_offsetonly.lean`, `atk_25_dblguard_oracle_scionly.lean`, `atk_26_maximal_dblguard_oracle.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl was found. Seven same-spec impls VERIFY (atk_17, atk_18, atk_19 = alias-echo / domain-escape shapes; atk_23, atk_24, atk_25, atk_26 = double-guard sharedTerm-oracle shapes). ALL SEVEN had their faithful refined patches materialized, git apply --check'd at base_commit, and RUN through the official harness: all seven RESOLVED (F2P 2/2, P2P 248/248 each). They are behaviourally equal to the gold patch, not counterexamples: an in-container sweep (beh.py, 36,963 firing observations over 3 ScalarFormatter configurations x 11 view intervals x 411 tick lists incl. 400 fuzzed x 3 non-both-off switch settings) found 0 cases where an empty-shared-term rendering differs from the both-off rendering. verify⇏correct is NOT falsified.
```

**Attacks re-run (26):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 26 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_01_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_02_carrier_int_reencode.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_03_partial_domain_nan.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_04_boundary_short_list.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_05_ungrounded_oracle.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_06_swapped_arms.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_07_log_path_substituted.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_08_padded_argument.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_09_sharedterm_oracle.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_asym_oracle_offset_only.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_asym_oracle_sci_only.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_site_b_only_fix.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_ownlabels_on_modes_arm.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_smuggle_choice_pred.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_empty_ticks_oracle.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_reversed_labels.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_alias_echo_modes_arm.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18_domain_escape_noswitch_arm.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_19_domain_escape_logrenderer.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 20 — `atk_20_logarm_numeric_alias.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21_observable_equal_oracle.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22_escape_on_empty_ticks.lean` → rejected (same spec, does not verify — good)

Attack 23 — `atk_23_dblguard_oracle_bothon.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 24 — `atk_24_dblguard_oracle_offsetonly.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 25 — `atk_25_dblguard_oracle_scionly.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 26 — `atk_26_maximal_dblguard_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SETUP.** Worktree at base_commit 22cdfb0c93f8ec78492d87edb810f10cb7f57a31 = (git worktree add --detach). All 26 attacks + pos_gold + pos_gold_myproof confirmed same_spec=True (26/26 + 2/2). Generators gen.py/gen2.py/gen3.py splice ONLY the two impl regions and the two prove_correct bodies (both elided by spec_view); axioms/pure/pre/post byte-identical.

VERIFY COMMAND: bash scripts/lean_verify.sh <atk>.lean  — run 4-at-a-time as background jobs.

POSITIVE CONTROLS (non-vacuity): pos_gold.lean (byte-identical shipped Solution.lean) EXIT=0; pos_gold_myproof.lean (gold impl rebuilt through MY wide `first | ...` proof alternation) EXIT=0 — proving the alternation given to every attack is not itself why any attack failed.

**PREPATCH:** atk_01_prepatch.lean (both switches left at default true/true at BOTH sites) EXIT=1 — prepatch bug reproduced.

19 REJECTED (EXIT=1): atk_01 prepatch; atk_02 carrier-gap re-encode of the prior pass's named counterexample (gold on integral ticks, prepatch off them); atk_03 partial-domain (wrong exactly where a tick is non-finite, i.e. outside `renders`); atk_04 boundary (modes left on for tick lists of length <= 1); atk_05 ungrounded-oracle echo (postcondition echoed into the choice predicate — Findable elaboration failure, contributes no tightness evidence); atk_06 control-flow-effect (arms of legendLabels swapped); atk_07 log path substituted with the numeric renderer; atk_08 padded argument (render ticks++[2^53], return the prefix) — rejected ON THE LOAD-BEARING PINNING CONJUNCT, goal `List.take ticks.length (renderTicks cfg false false (ticks ++ [9007199254740992.0])) = renderTicks cfg false false ticks`, confirming refinement.md A4's claim that the `∃ om sm, labels = renderTicks cfg om sm ticks` conjunct is not decoration; atk_09/10/11 sharedTerm-oracle shapes (both-on, offset-only, sci-only); atk_12 site-B-only fix; atk_13 ownLabels returned on the modes arm; atk_14 assumption-smuggle in the choice predicate (Findable, no tightness evidence); atk_15 modes left on for empty tick lists; atk_16 post-processing (labels reversed); atk_20 log arm aliased through the numeric renderer; atk_21 observable-equality oracle; atk_22 escape on empty ticks.

**SPEC IS TIGHTER THAN THE ONE THE PRIOR G-EQ PASS AUDITED.** atk_09 re-encodes the prior pass's atk_13_sharedterm_oracle, which that pass recorded as VERIFYING. Here it FAILS (EXIT=1) on the LENGTH clause: `⊢ (renderTicks cfg true true ticks).length = ticks.length` is not derivable, because `renderTicks_length` is gated on `renders cfg om sm ticks` and the method's require supplies that domain at (false,false) ONLY. Consistent with the spec hash having moved (G-EQ recorded sources/Solution.lean=6524c567...; G-AX/G-GOLD/G-HYGIENE record 6d339e20...). Same failure for the two asymmetric variants atk_10/atk_11. I therefore did NOT retain the prior verdict for these labels and re-derived it.

7 VERIFYING IMPLS — ALL MATERIALIZED AND RESOLVED (the mandatory step):
  atk_17_alias_echo_modes_arm      verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_18_domain_escape_noswitch_arm verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248) [attempt 2/3, flaky]
  atk_19_domain_escape_logrenderer  verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248) [attempt 3/3, flaky]
  atk_23_dblguard_oracle_bothon     verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_24_dblguard_oracle_offsetonly verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_25_dblguard_oracle_scionly    verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
  atk_26_maximal_dblguard_oracle    verify EXIT=0 -> resolve RESOLVED (F2P 2/2, P2P 248/248)
Commands: python mkpatch.py and mkpatch2.py to materialize; `git -C apply --check <atk>.diff` (7/7 APPLIES-OK); `python resolve.py <atk>` which calls swebench_unified.harness.run_resolve('mwaskom__seaborn-3187', patch).

WHY atk_23-26 ARE THE STRONGEST SHAPES AND WHY THEY ARE BEHAVIOURALLY GOLD. They defeat the length obstacle that killed atk_09/10/11 by guarding on BOTH `sharedTerm cfg om sm ticks == ""` AND `(renderTicks cfg om sm ticks).length == ticks.length`, discharging both ensures conjuncts with no axiom. Their faithful patches leave the two shared-term modes ENABLED wherever the real ScalarFormatter would hoist nothing. They still resolve because an empty shared term FORCES the both-off labels: structurally, ScalarFormatter.get_offset() returns '' iff orderOfMagnitude==0 and offset==0 (matplotlib 3.7.2, read in-container), while `__call__` computes xp=(x-offset)/`10**oom` and `_set_format` derives the format from (locs-offset)/`10**oom`, so oom==offset==0 makes both the value and the format string coincide with the both-off rendering. Measured, not just argued: beh.py in the instance container — 36,963 oracle-firing observations, 0 differences, 0 skips.

A-LEG CORRESPONDENCE AUDIT (the focus of this role; R/I left to G-CONF, which is legitimately conf_skip=true here since the observable is the callee's output verbatim).
  * A1b (`modesAvailable : Bool` <-> the TWO hasattr guards collapsed into ONE boolean) — the load-bearing R claim, since one boolean cannot express one setter present and the other absent. VERIFIED in-container (probe.py): of 17 Formatter subclasses across matplotlib.ticker + matplotlib.dates, exactly 1 (ScalarFormatter) has both setters, 16 have neither, and EXACTLY-ONE-SETTER == [] — so the guards are indeed true together or false together and the single boolean is faithful. Also confirmed over the five kinds Continuous.`_get_formatter` can install (StrMethodFormatter, FuncFormatter, LogFormatterSciNotation, EngFormatter, ScalarFormatter): only the last carries them.
  * A4/A5 (`renderTicks` / `sharedTerm` A-consumed <-> format_ticks / get_offset) — the pinning conjunct is genuinely load-bearing, demonstrated by atk_08's rejection on exactly that goal (above), and the shared-term clause is what discriminates the patch (negative control below).
  * B2 (`renderLog cfg ticks` A-consumed, handle included) — the doc's claim that the handle is load-bearing is correct: LogFormatter.`__call__` reads self.axis.get_view_interval(). atk_07 (log path substituted) and atk_20 (log arm aliased through the numeric renderer) are both rejected, so the log arm's pin holds.
  * A1e/B1c (the `renders`/`rendersLog` domain requires) — atk_03 (non-finite ticks) is rejected, so the domain restriction is not a loophole for hard inputs.
  * 18/18 legs are R (9), A-consumed (4) or I (5). NO kind-3 leg. deep_model_references == [] and no axiom models the function under change (renderTicks/sharedTerm/renderLog are all UNCHANGED matplotlib callees), so section C's claim holds.

**NOTABLE:** atk_18 and atk_19 are genuine DOMAIN ESCAPES that verify. On the modesAvailable=FALSE arm the spec supplies NO `renders`/`rendersLog` guard, yet an impl may still evaluate `renderTicks cfg false false ticks` (atk_18) or even `renderLog cfg ticks` (atk_19) there — the latter reaching a renderer site A never constructs, with no correspondence row in refinement.md. Both resolve, so this is not a spec break; I probed the latent risk that the added call could RAISE where gold does not (escape.py: EngFormatter-arm gold vs the added LogFormatter over 6 boundary installs incl. (-9e307,9e307), nan and inf ticks) and found agreement in every case (0 divergences). Recorded as a hardness observation, not a finding.

NEGATIVE CONTROL (proving my resolves are meaningful and the oracle discriminates): negctl_site_a_only.diff applies the gold edit at site A ONLY. It APPLIES-OK and does NOT resolve — F2P 1/2, failing tests/test_relational.py::TestRelationalPlotter::test_legend_has_no_offset, consistent across 3 attempts. So the harness detects a half-fix, and 7/7 resolves are not a blind oracle.

INFRASTRUCTURE NOTE (not scored as a spec verdict): the first 4-way-parallel resolve of atk_23 returned `docker.errors.ImageNotFound 404 ... No such image: sha256:63840fa...` with no report in 3 tries — an image race under parallel load, not a non-resolve. Re-run SERIALLY it RESOLVED (F2P 2/2, P2P 248/248).

LEDGER DEFECT FOUND (does not affect this gate's pass/fail; flagged for the bundle owner). meta.json is STALE with respect to the frozen Solution.lean: its `axioms` array names `renderTicks / labelValue` and claims `renderTicks_faithful: ... labelValue(label_i) == tick_i` with an explicit |t| <= 2^53 guard, and `float_modeling` says "tick values modeled as Int restricted to the float-exact range |t| <= 2^53". The shipped spec contains NO labelValue, NO renderTicks_faithful and NO `List Int` — ticks are `List Float` with no carrier restriction, and the discriminating axiom is `sharedTerm_none`. refinement.md A1 itself records that the List Int carrier was REFUTED by an earlier G-EQ pass; meta.json's axioms/float_modeling fields were never updated to match. Consistent with the spec-hash move noted above.

**VERDICT:** SOUND. 26 distinct same-spec wrong impls (26/26 same_spec=True) spanning prepatch, prior-counterexample re-encode, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, padded/reversed/aliased argument, half-fix, swapped-arm, assumption-smuggle, domain-escape and six oracle shapes — well past the >=5 distinct-attack floor. 19 rejected; 7 verified, and EVERY ONE of those 7 had its faithful refined patch materialized, git apply --check'd and RUN through the official harness, where all 7 RESOLVED. Positive controls verify, prepatch reproduced, negative control correctly does not resolve. No verifying wrong impl exists => verify⇏correct is NOT falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**VERDICT:** FAITHFUL. I could not construct any input on which the modeled functions disagree with the real patched callees. ~390,000 measured observations across the two axiom families, both real sites driven end-to-end, and the domain predicates checked for correspondence in BOTH directions (no in-domain violation, and no case where a `require` was false yet the real site still returned a legend).

This run supersedes the retained Role-3 UNFAITHFUL record in verdict.md. That finding was correct against the revision it audited (unguarded total axioms, mapping.md then affirmatively claiming "no modeled sub-domain"). The SHIPPED spec has since been repaired exactly as that finding recommended: `renders` and `rendersLog` are now opaque domain predicates, all four renderer facts are stated only inside them, `renders_nonvacuous` blocks vacuity, and each method carries the domain of the renderer its own arm calls at the setting that arm uses. I re-drove the cited counterexamples (public objects API with norm=(-M,M).tick(at=[0.0]); locator_to_legend_entries(FixedLocator([-M,M]), (-M,M), float); the bare axiom binding f.axis=DummyAxis(-M,M) then format_ticks([0.0])) and confirmed they all still raise OverflowError in the repo — but they now fall outside the modeled domain, so they no longer witness a disagreement. Per the retained-labels rule I re-judged rather than echoing the stored verdict, and the reject lane does not survive re-measurement.

The three modelling decisions I tried hardest to break all held, and each is load-bearing rather than decorative:
  * `renderLog` taking `cfg` — CORRECT and necessary. I independently reproduced the interval dependence ([1,100,10000] -> ['1','100','10000'] at view (1,1e5) vs ['1','100','1e4'] at (1,1.5e5)); LogFormatter.`__call__` reads self.axis.get_view_interval() and `_pprint_val`'s ladder switches at d=1e5. A ticks-only model would be the unfaithful one.
  * one `modesAvailable` Bool for two `hasattr` guards — CONFIRMED. Enumerating Formatter subclasses across matplotlib.ticker, .dates, .category and .projections.polar in 3.7.2 gives 19 classes; ScalarFormatter is the ONLY one with both setters and EXACTLY ZERO have precisely one, so the two guards at scales.py:385-388 can never disagree. EngFormatter's bases are (Formatter,) in this version with hasattr False/False, so it correctly lands on the false arm — the near-miss mapping.md flags is real and correctly resolved.
  * `sharedTerm cfg false false ticks = ""` rather than a numeric read-back — CORRECT. I confirmed mathtext/usetex installs print labels no numeric parse accepts while still hoisting nothing, so a read-back obligation would have been FALSE of the real code. This is the rare case where the weaker-looking clause is the faithful one.

TWO NON-DEFECT OBSERVATIONS, recorded for the ledger and explicitly NOT the basis of any verdict:

1. LATENT G-AX BRITTLENESS (axiom_check.py, not Solution.lean). check_alt_renderers assertion (e) asserts `own_fmt.get_offset() == ""` for every non-ScalarFormatter renderer, justified in the docstring as "these renderers hoist nothing to begin with". That is FALSE of ConciseDateFormatter in general — it is only true of the tick list axiom_check happens to pass it (`days = [1.0, 32.0, 60.0, 91.0]`, a multi-month span). Measured at the REAL patched site A via Temporal().label(concise=True): a one-day span gives get_offset() == '2020-Jan-02', a one-month span '2020-Jan', a one-hour span '2020-Jan-01'. ConciseDateFormatter.format_ticks sets self.offset_string from offsetfmts[level] whenever show_offset holds, and only suppresses it when the year appears in the ticks themselves. So the same assertion would FAIL if the fixture used a narrower date span.
   Why this is NOT a spec faithfulness break: assertion (e) is a G-AX-internal convenience check, not one of the eight Solution.lean axioms. The `modesAvailable = false` arm's actual obligation is `labels = ownLabels`, and that clause HELD on every date configuration I drove (one hour / one day / one month / one year, concise True and False, ConciseDateFormatter and AutoDateFormatter — 8/8, ownLabels == labels in every case), because that arm calls neither setter and is genuinely inert. The spec is silent about the hoisted term on that arm, which is the honest thing to be: a ConciseDateFormatter legend really does lose its offset string, but that is pre-existing repo behavior the patch does not touch and the spec does not claim otherwise. Recommend widening axiom_check.py's date fixture to a sub-month span and either dropping assertion (e) or restating it as "hoists nothing FOR THIS TICK LIST" — otherwise a future fixture change turns a passing gate red for a reason unrelated to the spec.

2. STALE meta.json (bookkeeping, pre-existing, independently reported by the retained Role-3 record). `float_modeling`, `axioms[0].encoded_property` and `modeled_functions[*].carrier_type` still describe the SUPERSEDED carrier ('tick values modeled as Int restricted to |t| <= 2^53', a `renderTicks_faithful` / `labelValue` read-back axiom, 'List Int'). The frozen Solution.lean has `ticks : List Float` with no 2^53 guard and no read-back axiom; its axioms are RendererConfig / renderTicks / sharedTerm / renders / renderTicks_length / sharedTerm_none / sharedTerm_hoists / renderLog / rendersLog / renderLog_length / renders_nonvacuous. mapping.md 2 documents the Int revision being refuted by G-EQ. Prose/metadata drift only — I audited the live Lean, which is what ships. Note meta.json is a gate-owned ledger, so this wants a gate-side restamp rather than a hand edit.

**ENVIRONMENT NOTE:** the host matplotlib is 3.10.9, which differs from the oracle's pin. Every measurement above was taken inside the instance's own container at matplotlib 3.7.2; I verified the version at the top of each probe. The ConciseDateFormatter get_offset behavior in observation 1 reproduces in BOTH versions, so it is not a host artifact.

Counterexample / evidence:

```
None. Adversarial measurements, all in the instance's own pinned container (swebench/sweb.eval.x86_64.mwaskom_1776_seaborn-3187, matplotlib 3.7.2) against the base_commit worktree WITH patch.diff APPLIED (set_useOffset present at utils.py:704 and scales.py:386 — confirmed):

A. AXIOM SWEEP (renderTicks_length, sharedTerm_none) — 29 RendererConfig installations (plain, rc_mathtext, text.usetex=True, rc_locale, rc_useoffset, formatter.limits tight/wide, offset_threshold=1, unicode_minus off, kw useMathText/useLocale/useOffset=True/3.0/1e8, residual pre-state set_useOffset(12345.0)/set_scientific(True)/set_powerlimits((3,3))/((-5,-5))/((0,0))/pre_both, view intervals (-1e9,1e9)/(-9e307,9e307)/(-M,M)/(-8e307,8e307)/tight/negative/asymmetric, plus mathtext-at-max) x ~3630 tick lists (boundary lists incl. [-M,M], [M], [-1e308,1e308], [1e300,...], 2^53, 1e-300, plus 3000 fuzzed lists with magnitudes drawn up to 1e308 and 600 non-finite lists) x 4 switch settings.
   RESULT: 363,541 in-domain observations, **0 renderTicks_length violations, 0 sharedTerm_none violations**. 57,423 observations correctly OUT of domain (37,293 OverflowError + 20,130 ValueError) — exactly the region the spec's `renders` predicate excludes. 145,061 hoisting observations witness sharedTerm_hoists.

B. THE PRIOR FINDING IS REPAIRED, NOT PRESENT. The retained verdict.md Role-3 record cites `renderTicks_length`/`sharedTerm_none` as "stated with NO domain guard". The SHIPPED Solution.lean guards both: `renders cfg offsetMode scaleMode ticks -> ...` (line 72) and `renders cfg false false ticks -> ...` (line 75), with `rendersLog` for the log renderer (line 107), `renders_nonvacuous` for inhabitation (line 114), and matching method-level `require modesAvailable = true -> renders cfg false false ticks` (line 179) / `require isLog = true -> rendersLog cfg ticks` + `require isLog = false -> renders cfg false false ticks` (lines 234-235). mapping.md 3.4 documents the boundary at max_double/2 = 8.988465674311579e+307 and states the earlier unguarded revision was refuted. I re-measured the boundary pair myself: view (-8e307,8e307) ticks [0.0] returns (['0'],''); view (-9e307,9e307) raises OverflowError. That input is now OUTSIDE the modeled domain, so it is not a divergence.

C. SITE B (locator_to_legend_entries) — DRIVEN THROUGH ITS OWN PUBLIC SIGNATURE, 7 locator kinds (MaxN, Auto, Log, FixedLocator([0.0]), FixedLocator([-M,M]), FixedLocator([1,100,1e4]), SymmetricalLog) x 419 data-limit pairs (incl. (-M,M), (-9e307,9e307), (1e300,1e308), (0.0,1e300) and 400 fuzzed):
   2,702 real invocations returned, 231 raised. Checked EVERY ensures clause of legendEntries directly against the returned value:
     ensures labels.length = ticks.length ......... 0 violations
     ensures isLog = true -> labels = renderLog cfg ticks ... 0 violations
     ensures isLog = false -> exists om sm, labels = renderTicks cfg om sm ticks AND sharedTerm = "" ... 0 violations
     require FALSE but site RETURNED (too-strong precondition) ... 0 cases

D. SITE A (ContinuousBase._setup legend branch) — replicated the site's exact tail with the genuine installed formatter, view interval and clipped locs. 8 scale configurations (plain, like=, unit=, trans=log, base=, formatter=PercentFormatter/ScalarFormatter/StrMethodFormatter) x 5 datasets: 39 runs, 0 length violations, 0 `labels = ownLabels` violations, 0 existential violations, and the two hasattr guards NEVER disagreed (so the single `modesAvailable` Bool is faithful). Domain-correspondence sweep: 16+250 norm pairs x 6 `tick(at=)` lists = 1,578 returning runs, 18 raising — **0 mismatches**, including 0 cases of "require false but site returned".

E. sharedTerm_none ADVERSARIAL RESIDUAL-STATE SWEEP — 4 rcParams contexts x 5 constructor kwargs x 11 pre-set residual states (incl. set_powerlimits((3,3)) which forces a fixed non-zero orderOfMagnitude, set_useOffset(1e100), pre-set set_locs) x 8 tick lists: 1,756 in-domain, **0 violations**. Reading ScalarFormatter._set_order_of_magnitude in 3.7.2 confirms `if not self._scientific: self.orderOfMagnitude = 0; return` short-circuits BEFORE the powerlimits branch, and set_useOffset(False) sets self.offset = 0, so get_offset()'s `if self.orderOfMagnitude or self.offset` guard can never fire with both switches off. The axiom is structurally forced, not merely sampled.

F. renderLog_length — 11 view intervals x ~2012 log tick lists: 22,110 in-domain, 0 length violations. I independently reproduced the load-bearing interval dependence that justifies renderLog taking cfg: ticks [1,100,10000] print ['1','100','10000'] at view (1,1e5) and ['1','100','1e4'] at (1,1.5e5). A ticks-only model would be the unfaithful one; the spec has it right.

G. renderLog vs site-B pass-through and pos-sensitivity — site B uses `set_locs` then `[formatter(x) for x in raw_levels]` whereas the axioms are bound to `format_ticks`. I checked these are the same function: 18,084 comparisons across 6 views x ~1507 tick lists x 2 switch settings, **0 differences** (ScalarFormatter.__call__ ignores `pos`). So binding the axiom to format_ticks is faithful to a site that does not use it.

H. READ-ONLY (`not mut`) CLAIM CHECKED. The real site DOES mutate the installed formatter object (`f._useOffset` True->False on a caller-supplied `Continuous().label(formatter=f)`). But `cfg : RendererConfig` is bound (mapping.md 1) to the formatter's PRESENTATION SETTINGS AND VIEW INTERVAL *apart from the two switches*, and the two switches are exactly what the model exposes as the existential `offsetMode`/`scaleMode` rather than as part of cfg. So the mutation is entirely inside the part of the state the model does not carry in cfg; the spec's read-only claim is about `labels`, `ticks` and `ownLabels`, which are untouched. I also confirmed the mutation is idempotent: two successive `_setup` calls on the same formatter instance yield identical labels, so cfg remains a well-defined function of (install, ticks).

I. Spec region identity: markers.same_spec(Solution.lean, Solution_prepatch.lean) = True and same_spec(cur,cur) = True under the VelvetBackend tables — the shipped spec view is byte-identical to the retained prepatch control, so the axioms I audited are the ones the consumer sees.

J. Solution.lean elaborates clean: scripts/lean_verify.sh exit 0, no sorry/admit.

K. DIRECTION-OF-PATCH TRAP CHECKED EXPLICITLY. I compared only against the worktree WITH patch.diff applied (verified by grep). The one place the patch narrows the callee's domain — set_scientific(False) forcing orderOfMagnitude=0 and hence an infinite loc_range — is precisely what `renders cfg false false ticks` now excludes, at the setting the spec's own arm uses. So the model describes the POST-patch, narrower domain, not the wider pre-patch one.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION, mwaskom__seaborn-3187 velvet. Verdict NO-LEAKAGE. Reviewing the SHIPPED Solution.lean sha 6d339e20ea69...; every load-bearing claim below is my own measurement.

NO RELAXATION CLAIM TO ADJUDICATE -- so this is a STRICT review with no facet carve-out. meta.json has no `relaxed_leakage` key (top-level keys: axioms, base_commit, changed_files, conf_skip, conf_skip_reason, deep_model_references, float_modeling, gates, instance_id, modeled_functions, patch_is_gold, pbt_audit, region_hashes, repo, schema_version, spec_provenance, version) and `find -iname '*relax*'` over the instance dir returns nothing -- no RELAXED_LEAKAGE.md. The three `relaxed_leakage` substring hits in meta.json are inside PRIOR G-PANEL-3 note text (gates.G-PANEL-3.note and the G-PANEL rollup detail) asserting the key's absence; they are a stamped record of an earlier role, not a claim addressed to me, and I did not inherit their disposition -- I re-derived the unavoidability argument from scratch below.

**NO BUNDLE FILE ADDRESSES ME.** `leakage.reviewer_directed()` over all 11 .md files under the instance (velvet/lean/nagini/ears x refinement/mapping/verdict + ears/requirements.md): zero hits on every one. No file tells me how to record or which verdict is honest. Nothing to report as steering.

**SPEC REGION BYTE-IDENTICAL.** `markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language)` = True, and `spec_view` of the two files is string-identical (13694 chars). The only diff between the files is inside the elided impl region: `offsetMode/scaleMode := false` -> `true` at both sites plus their comments. The prepatch's `-- PRE-PATCH BUG:` narration is fully elided -- measured on the PREPATCH spec view: 'PRE-PATCH' 0, 'BUG' 0, 'bug' 0, 'fix' 0. So the artifact I judge is one text and it carries no pre/post tell.

**MECHANICAL SCREEN.** `leakage.screen(Solution.lean, VelvetBackend.language, patch.diff, problem_statement)` -> passed=True, hard_failures=[], warnings=[]. I treated that as necessary-not-sufficient and screened the vocabulary myself, because G-LEAK's symbol rule only harvests def/class names from changed lines and this gold patch adds no def/class -- so the two setter names are NOT covered by it. Counts over the spec view: set_useOffset 0, useOffset 0, set_scientific 0, scientific 0, ScalarFormatter 0, LogFormatter 0, format_ticks 0, formatter 0, locator 0, matplotlib 0, seaborn 0, scales.py 0, utils.py 0. No patched path, no patched module dotted path, no diff marker, no gold line >=8 normalized chars. Hidden-test constants: `1e8`/`1e7` (the FAIL_TO_PASS assertions `np.add(xy['x'], 1e8)` / `float(text.get_text()) > 1e7`) -> 0 occurrences in the spec view. The ears/verdict.md advisory about "spec prose reproducing hidden-test constants 1e8/1e7" does NOT apply here: 0 hits in the velvet spec view and 0 in ears/requirements.md as shipped.

DISCRIMINATOR IS LOAD-BEARING -- the strip-and-reverify test, run for real with scripts/lean_verify.sh (600s cap):
  (post) Solution.lean as shipped -> exit 0.
  (B) prepatch impl + spec with the `sharedTerm cfg offsetMode scaleMode ticks = ""` conjunct REMOVED from both `ensures` (domain `require`s widened to `renders cfg true true ticks` so the length obligation is dischargeable at the setting that impl uses; proofs witness true/true) -> exit 0. The prepatch impl VERIFIES once the conjunct is gone.
  (C) VACUITY CONTROL: identical widened `require`s, conjunct KEPT -> exit 1, unsolved goals at both `prove_correct` sites (202:27 and 259:28). So B's pass is not an artifact of the widened domain; the `sharedTerm = ""` conjunct is the ONLY clause rejecting the prepatch impl.
Hence the discriminating clause cannot be dropped, and stating it in the fragment forces the two switches to appear as parameters of `renderTicks`/`sharedTerm`. The abstract two-switch model is compelled by spec strength, not chosen to hint.

**WHAT THE PUBLIC STATEMENT ALREADY GIVES.** problem_statement (never hints_text) names: `offset` x6, `formatter` x6, `ScalarFormatter` x3, `mpl.rcParams['axes.formatter.useoffset']`, the offset_threshold rcParam, "formatted without their multiplicative offset value", "in the order of 1E6", a direct GitHub permalink to scales.py L377-L382 (the modeled site), and "The issue also reproduces ... using `scatterplot`" -- which is what makes the TWO-SITE split (objects `legendLabels` + classic function-level `legendEntries`) public. So the additive facet, the callee class, the site, and the two-interface structure are all already solver-visible; the word "multiplicative" is public verbatim, covering the power-of-ten switch. The spec view says strictly less about the repo than the statement does: it names no class, no setter, no file, no line.

### Two prose points I weighed and did not raise as leakage
  (i) "that path is not touched" (legendEntries docstring, log arm) is phrased about the edit rather than behavior. It conveys nothing beyond the formal clause on the next lines, `ensures isLog = true -> labels = renderLog cfg ticks`, which is a required frame pin -- without it the log arm is unconstrained and the spec is too weak (refinement.md B2 records G-PANEL-2 refuting a weaker ticks-only version of exactly this clause). Zero gold-reconstruction content beyond a clause a faithful spec must state; recommend rewording to "is unchanged" on any future prose pass, non-blocking.
  (ii) The identifier `offsetMode` embeds "offset", which is public in the statement 6 times, so it is screened out by the problem_statement carve-out; `scaleMode` echoes no repo symbol (the real setter is `set_scientific`).

TWO PROCESS NOTES for the gate operator, neither affecting this verdict:
  - meta.json `region_hashes.spec_view` = d5467361...; recomputed from the shipped file = 52b6628e... (axioms and impl likewise disagree). This is CORPUS-WIDE, not instance-specific: I sampled 40 benchmark-verified/*/velvet bundles and got 0 matches / 40 mismatches, so the stored region_hashes are stale or computed under a different convention fleet-wide -- an infrastructure item, not a spec defect here.
  - Every G-PANEL-* role record (incl. the prior G-PANEL-3 pass) is stamped against Solution.lean sha 6524c567..., while the shipped file and all of G-AX/G-DIFF/G-GOLD/G-HYGIENE/G-LEAK/G-MUT/G-VERIFY are 6d339e20.... The panel lane had not previously judged the shipped text; this submission does. G-PANEL is failing only because G-PANEL-2 (faithfulness) failed on an OverflowError inside the modeled region -- a domain/faithfulness matter in that lane, and per the rollup convention a failing G-PANEL means re-audit, not repair. It is orthogonal to leakage and does not undermine any gate this NO-LEAKAGE rests on (G-VERIFY pass, G-DIFF prepatch-fails pass, G-AX pass, G-LEAK pass, all four stamped against the shipped 6d339e20).

**CONCLUSION:** no gold-diff line, no diff marker, no patched file/module path, no patched repo symbol in identifier or comment, no bug->fix narration, no hidden-test constant, and the one mechanism-shaped statement in the spec view is a load-bearing discriminator proven unavoidable by the B/C pair above. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
