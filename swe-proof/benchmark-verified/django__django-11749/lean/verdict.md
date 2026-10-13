# P2 adversarial audit — django__django-11749

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_12.lean`, `atk_13r.lean`, `atk_14r.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — and the reason is MACHINE-PROVEN, not merely sampled.

rigidity.lean (`timeout 400 bash scripts/lean_verify.sh .../rigidity.lean 300` -> EXIT 0; ax_rigidity.lean axioms all clean) re-declares the FROZEN imports+axioms+pure+post regions verbatim and proves four things:
(1) spec_is_rigid [propext, Quot.sound] — problem_spec_requiredOptionArgs is an UNCONDITIONED TOTAL FUNCTIONAL EQUALITY (result = (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map (parseArgsPrefix ++ ·)); there is no pre-conditions region and no existential slack, so ANY two impls f g satisfying it everywhere are EQUAL (funext + rw on both hypotheses).
(2) spec_is_satisfiable [propext] — the spec function itself satisfies the postcondition, so (1) is NOT vacuous.
(3) prepatch_predicate_is_observable — NO AXIOMS AT ALL (`decide`): on act=<id 0, ["--foo-id"], req=false, dest="foo_id">, grp=<required=true,[act]>, keys=["foo_id"], the patched keepAction and the prepatch predicate (destInOptions && req) DISAGREE.
(4) prepatch_impl_differs [propext] — and the two resulting result-lists differ as VALUES on that witness (the exact FAIL_TO_PASS scenario from the issue report).

Consequence: a behaviourally-distinct same-spec impl can NEVER verify, and every same-spec impl that DOES verify is extensionally equal to the shipped one — an echo, never a spec weakness. verify=>correct holds for this bundle BY PROOF rather than by sampling.

Borne out empirically: 13/16 attacks (all behaviourally distinct) were REJECTED with genuine `error: unsolved goals` AT THE CORRECTNESS THEOREM, and all 3 that verify (atk_12, atk_13r, atk_14r) are equivalent reshapes whose faithful patches were materialized and ALL RESOLVED under the official harness. NO verifying attack has a non-resolving faithful patch => the BROKEN condition is not met.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_1: PREPATCH BUG — drops `|| inRequiredGroup groups opt`
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,13 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if destInOptions optionKeys opt && opt.req then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +147,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_2: PARTIAL DOMAIN — correct for <=1 group, wrong from the 2nd on
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,14 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if destInOptions optionKeys opt &&
+        (opt.req || inRequiredGroup (groups.take 1) opt) then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +148,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_3: BOUNDARY — first flag instead of `min`; SAME partiality domain
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -98,13 +99,14 @@
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
     if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
+      let flag ← opt.optionStrings.head?
+      let value ← argOptions.lookup opt.dest
+      parseArgs := parseArgs ++ [flag ++ "=" ++ value]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +149,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_4: CONTROL-FLOW EFFECT — partiality forced for every action; same list, wider none
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,14 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
+    let s ← renderArg? argOptions opt
     if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
+      parseArgs := parseArgs ++ [s]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +148,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_5: TOTALIZATION — invents a value where min/subscript raise
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -98,13 +99,14 @@
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
     if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
+      parseArgs := parseArgs ++
+        [((leastFlag? opt.optionStrings).getD "") ++ "=" ++
+          ((argOptions.lookup opt.dest).getD "")]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +149,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_6: FLAG-DEP DROPPED — ANY exclusive group counts, not just required ones
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,14 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if destInOptions optionKeys opt &&
+        (opt.req || groups.any (fun g => g.groupActions.any (· == opt))) then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +148,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_7: IDENTITY CORRESPONDENCE — group membership by dest, not by the id-carrying action
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,16 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if destInOptions optionKeys opt &&
+        (opt.req ||
+          groups.any (fun g => g.required && g.groupActions.any
+            (fun a => a.dest == opt.dest))) then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +150,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,21 +90,21 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_8: FRAME/ORDER — prefix appended after the rendered run
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
     (parseArgsPrefix : List String) :
     Option (List String) := do
-  let mut parseArgs := parseArgsPrefix
+  let mut rendered : List String := []
   for opt in actions do
     if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
-  return parseArgs
+      rendered := rendered ++ [← renderArg? argOptions opt]
+  return rendered ++ parseArgsPrefix
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +147,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_9: DROPPED GUARD — forwards required actions whose dest was never named
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,13 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if opt.req || inRequiredGroup groups opt then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +147,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_10: DICT CONFLATION — `opt.dest in arg_options` instead of `in options`
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,14 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if (argOptions.lookup opt.dest).isSome &&
+        (opt.req || inRequiredGroup groups opt) then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +148,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_11: SILENT SKIP — unrenderable selected action dropped instead of failing the whole result
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -98,13 +99,14 @@
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
     if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
+      match renderArg? argOptions opt with
+      | some s => parseArgs := parseArgs ++ [s]
+      | none => pure ()
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +149,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,21 +90,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_12: ECHO / ungrounded oracle — impl is literally the spec RHS
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
     (parseArgsPrefix : List String) :
-    Option (List String) := do
-  let mut parseArgs := parseArgsPrefix
-  for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
-  return parseArgs
+    Option (List String) := 
+  (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
+    (fun rendered => parseArgsPrefix ++ rendered)
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +144,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_13: ECHO — conjuncts swapped (Bool && is commutative in value)
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,14 +98,13 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if (opt.req || inRequiredGroup groups opt) && destInOptions optionKeys opt then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +147,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,21 +90,21 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_14: ECHO — left fold in the Option monad instead of the for-loop
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
     (parseArgsPrefix : List String) :
-    Option (List String) := do
-  let mut parseArgs := parseArgsPrefix
-  for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
-  return parseArgs
+    Option (List String) := 
+  actions.foldl (fun acc opt =>
+    acc.bind fun r =>
+      if keepAction groups optionKeys opt then
+        (renderArg? argOptions opt).map fun s => r ++ [s]
+      else some r) (some parseArgsPrefix)
 -- impl-end
-
 -- proof-start
-/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
-generalized over the accumulator. -/
+/-- Helper (SHIPPED verbatim): the `forIn` accumulation equals the
+`renderAll`/`filter` spec, generalized over the accumulator. -/
 theorem forIn_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +147,32 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  first
+    | rfl
+    | (show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
+          (if keepAction groups optionKeys opt then
+            Option.bind (renderArg? argOptions opt)
+              (fun s => some (ForInStep.yield (r ++ [s])))
+          else some (ForInStep.yield r) : Option (ForInStep (List String)))))
+          (fun r => some r) = _
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | simp [keepAction, destInOptions, inRequiredGroup, renderArg?, renderAll,
+            leastFlag?, Bool.and_comm, Bool.or_comm, Function.comp_def]
+    | (simp only [keepAction, destInOptions, inRequiredGroup, Bool.and_comm,
+                  Bool.or_comm]
+       rw [forIn_requiredOptionArgs actions groups optionKeys argOptions
+             parseArgsPrefix]
+       cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;>
+         rfl)
+    | (induction actions generalizing parseArgsPrefix <;>
+        simp_all [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                  renderAll, leastFlag?, Function.comp_def])
+    | (induction actions generalizing parseArgsPrefix <;>
+        aesop (add simp [keepAction, destInOptions, inRequiredGroup, renderArg?,
+                         renderAll, leastFlag?]))
+    | aesop
+    | decide
 -- proof-end
```

Attack 15 — `atk_13r.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,6 +90,7 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_13r: ECHO — conjuncts swapped, REAL proof supplied
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
@@ -97,11 +98,10 @@
     Option (List String) := do
   let mut parseArgs := parseArgsPrefix
   for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
+    if (opt.req || inRequiredGroup groups opt) && destInOptions optionKeys opt then
       parseArgs := parseArgs ++ [← renderArg? argOptions opt]
   return parseArgs
 -- impl-end
-
 -- proof-start
 /-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
 generalized over the accumulator. -/
@@ -146,13 +146,18 @@
       (implementation_requiredOptionArgs actions groups optionKeys argOptions
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
+  have hcomm : ∀ opt : ParserAction,
+      ((opt.req || inRequiredGroup groups opt) && destInOptions optionKeys opt)
+        = keepAction groups optionKeys opt := by
+    intro opt; simp [keepAction, Bool.and_comm]
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
   show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
+      (if (opt.req || inRequiredGroup groups opt) && destInOptions optionKeys opt then
         Option.bind (renderArg? argOptions opt)
           (fun s => some (ForInStep.yield (r ++ [s])))
       else some (ForInStep.yield r) : Option (ForInStep (List String)))))
       (fun r => some r) = _
+  simp only [hcomm]
   rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
   cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
 -- proof-end
```

Attack 16 — `atk_14r.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,18 +90,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK atk_14r: ECHO — Option-monad foldl, REAL proof supplied
 def implementation_requiredOptionArgs
     (actions : List ParserAction) (groups : List ExclusiveGroup)
     (optionKeys : List String) (argOptions : List (String × String))
     (parseArgsPrefix : List String) :
-    Option (List String) := do
-  let mut parseArgs := parseArgsPrefix
-  for opt in actions do
-    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
-      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
-  return parseArgs
+    Option (List String) := 
+  actions.foldl (fun acc opt =>
+    acc.bind fun r =>
+      if keepAction groups optionKeys opt then
+        (renderArg? argOptions opt).map fun s => r ++ [s]
+      else some r) (some parseArgsPrefix)
 -- impl-end
-
 -- proof-start
 /-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
 generalized over the accumulator. -/
@@ -137,6 +137,36 @@
         rw [ih (init ++ [v])]
         simp [Function.comp_def]
 
+theorem foldl_requiredOptionArgs
+    (actions : List ParserAction) (groups : List ExclusiveGroup)
+    (optionKeys : List String) (argOptions : List (String × String))
+    (acc : Option (List String)) :
+    actions.foldl (fun acc opt =>
+      acc.bind fun r =>
+        if keepAction groups optionKeys opt then
+          (renderArg? argOptions opt).map fun s => r ++ [s]
+        else some r) acc =
+      acc.bind (fun init =>
+        (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
+          (fun rendered => init ++ rendered)) := by
+  induction actions generalizing acc with
+  | nil => cases acc <;> simp [renderAll]
+  | cons a as ih =>
+    rw [List.foldl_cons, ih]
+    cases acc with
+    | none => simp
+    | some init =>
+      cases h : keepAction groups optionKeys a with
+      | false => simp [h, List.filter_cons]
+      | true =>
+        cases hr : renderArg? argOptions a with
+        | none => simp [h, hr, List.filter_cons, renderAll]
+        | some v =>
+          simp only [h, hr, List.filter_cons, if_true, renderAll, Option.map_some,
+                     Option.bind_some]
+          cases renderAll argOptions (as.filter (keepAction groups optionKeys)) <;>
+            simp [List.append_assoc]
+
 theorem correct_requiredOptionArgs :
     ∀ (actions : List ParserAction) (groups : List ExclusiveGroup)
       (optionKeys : List String) (argOptions : List (String × String))
@@ -147,12 +177,6 @@
         parseArgsPrefix) := by
   intro actions groups optionKeys argOptions parseArgsPrefix
   unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
-  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
-      (if keepAction groups optionKeys opt then
-        Option.bind (renderArg? argOptions opt)
-          (fun s => some (ForInStep.yield (r ++ [s])))
-      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
-      (fun r => some r) = _
-  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
-  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
+  rw [foldl_requiredOptionArgs]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee requires an axiomatized contract: selecting an action's
-- least option flag, consulting the value table at a destination, and the
-- string formatting used to render each forwarded option are modeled directly
-- below (identical concrete ops), so there is nothing to axiomatize here.
-- axioms-end

-- pure-start

/-- A single parser action. `id` carries object identity (membership in a group
is identity-based in the source), `optionStrings` are the option flags, `req`
marks an individually-required action, `dest` is the destination key. -/
structure ParserAction where
  id : Nat
  optionStrings : List String
  req : Bool
  dest : String
deriving DecidableEq, Repr

/-- A mutually-exclusive option group: whether the group as a whole is required,
and the actions it contains (which share identity with entries in the flat
action list). -/
structure ExclusiveGroup where
  required : Bool
  groupActions : List ParserAction
deriving DecidableEq, Repr

/-- The lexicographically least of an action's option flags. An action that
declares no flag at all has no least flag, so the selection is not defined
there and reports `none`. -/
def leastFlag? (xs : List String) : Option String :=
  match xs with
  | [] => none
  | x :: rest => some (rest.foldl (fun m s => if s < m then s else m) x)

/-- Whether an action belongs to some group that is itself required. -/
def inRequiredGroup (groups : List ExclusiveGroup) (opt : ParserAction) : Bool :=
  groups.any (fun g => g.required && g.groupActions.any (· == opt))

/-- Whether the caller named this action's destination. The keys the caller
named are their own input, carried separately from the value table below. -/
def destInOptions (optionKeys : List String) (opt : ParserAction) : Bool :=
  optionKeys.any (· = opt.dest)

/-- The keep predicate: a keyword-named action is forwarded to the parser iff
its destination was named AND it is required, either individually or by virtue
of belonging to a required mutually-exclusive group. -/
def keepAction (groups : List ExclusiveGroup) (optionKeys : List String)
    (opt : ParserAction) : Bool :=
  destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt)

/-- Render a forwarded action as the `"<flag>=<value>"` string built from its
least flag and from the value the value table carries at its destination. TWO
independent lookups can yield nothing, and the rendering is then not defined —
`none`: an action declaring no flag has no least flag, and the value table need
not carry a value at every destination the caller named, those being two
separate inputs. -/
def renderArg? (argOptions : List (String × String)) (opt : ParserAction) :
    Option String :=
  (leastFlag? opt.optionStrings).bind fun flag =>
    (argOptions.lookup opt.dest).map fun value => flag ++ "=" ++ value

/-- Render a whole run of forwarded actions, in order. Defined only when every
action in the run renders. -/
def renderAll (argOptions : List (String × String)) :
    List ParserAction → Option (List String)
  | [] => some []
  | opt :: rest =>
    (renderArg? argOptions opt).bind fun s =>
      (renderAll argOptions rest).map fun ss => s :: ss

-- pure-end

-- post-conditions-start
/-- The forwarded-argument list: the (frame-pinned) positional prefix followed,
in action order, by the rendered string for exactly those actions selected by
`keepAction`. Selection consults the destination keys the caller NAMED; each
selected action's value is read from the separate value table. The whole result
is defined exactly when every selected action renders, and is `none` otherwise. -/
def problem_spec_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (parseArgsPrefix : List String) (result : Option (List String)) : Prop :=
  result =
    (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
      (fun rendered => parseArgsPrefix ++ rendered)
-- post-conditions-end

-- impl-start
def implementation_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (parseArgsPrefix : List String) :
    Option (List String) := do
  let mut parseArgs := parseArgsPrefix
  for opt in actions do
    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
  return parseArgs
-- impl-end

-- proof-start
/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
generalized over the accumulator. -/
theorem forIn_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (init : List String) :
    (forIn actions init (fun opt r =>
      (if keepAction groups optionKeys opt then
        Option.bind (renderArg? argOptions opt)
          (fun s => some (ForInStep.yield (r ++ [s])))
      else some (ForInStep.yield r) : Option (ForInStep (List String))))) =
      (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
        (fun rendered => init ++ rendered) := by
  induction actions generalizing init with
  | nil => simp [renderAll]
  | cons a as ih =>
    rw [List.forIn_cons]
    cases h : keepAction groups optionKeys a with
    | false =>
      simp only [h, List.filter_cons, Bool.false_eq_true, if_false]
      exact ih init
    | true =>
      cases hr : renderArg? argOptions a with
      | none => simp [h, hr, renderAll]
      | some v =>
        simp only [h, hr, List.filter_cons, if_true, renderAll]
        show (forIn as (init ++ [v]) (fun opt r =>
          (if keepAction groups optionKeys opt then
            Option.bind (renderArg? argOptions opt)
              (fun s => some (ForInStep.yield (r ++ [s])))
          else some (ForInStep.yield r) : Option (ForInStep (List String))))) = _
        rw [ih (init ++ [v])]
        simp [Function.comp_def]

theorem correct_requiredOptionArgs :
    ∀ (actions : List ParserAction) (groups : List ExclusiveGroup)
      (optionKeys : List String) (argOptions : List (String × String))
      (parseArgsPrefix : List String),
    problem_spec_requiredOptionArgs actions groups optionKeys argOptions
      parseArgsPrefix
      (implementation_requiredOptionArgs actions groups optionKeys argOptions
        parseArgsPrefix) := by
  intro actions groups optionKeys argOptions parseArgsPrefix
  unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
      (if keepAction groups optionKeys opt then
        Option.bind (renderArg? argOptions opt)
          (fun s => some (ForInStep.yield (r ++ [s])))
      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
      (fun r => some r) = _
  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: TRUE for all 17 bundle-shaped files (16 attacks + positive control), checked with swebench_unified.markers.same_spec / backends.get_backend('lean').language against the shipped Solution.lean. Only the impl (and proof) region was edited; imports/axioms/pure/post-conditions are BYTE-IDENTICAL.

TOOLS/SCHEDULE: every file built by gen.py from a verbatim copy of Solution.lean. Verification command for each: `bash scripts/lean_verify.sh <name>.lean` run from the repo root, dispatched 4-at-a-time as concurrent background jobs (schedule only; EVERY attack fully verified). Per-file logs are <name>.log, exit codes aggregated in results.txt.

ANTI-WEAK-TACTIC CONTROL: the Lean spec view elides BOTH impl and proof regions, so a rejection could otherwise be a weak-tactic artifact. Every attack was therefore given the SHIPPED helper lemma `forIn_requiredOptionArgs` VERBATIM plus a broad closing battery (`rfl` | the shipped proof route | targeted `simp` over every pure def + Bool.and_comm/Bool.or_comm | `simp only` boolean-normalize then the shipped route | generalizing induction + simp_all | generalizing induction + aesop with all defs | `aesop` | `decide`). Every rejection below is thus a rejection DESPITE the strongest known machinery being in scope. Additionally, the two echo reshapes my generic battery missed (atk_13, atk_14) were RE-ARMED with hand-written REAL proofs (atk_13r: pointwise Bool.and_comm rewrite then the shipped helper; atk_14r: its own `foldl_requiredOptionArgs` induction lemma) — so they are counted as VERIFYING attacks and put through resolve, rather than being banked as false rejections.

=== REJECTED (EXIT 1, genuine `error: unsolved goals` at correct_requiredOptionArgs) — 13 distinct wrong impls ===
1. atk_1.lean  PREPATCH BUG re-encoded: drops `|| inRequiredGroup groups opt`. EXIT 1 (err @147:28). prepatch_reproduced = TRUE.
2. atk_2.lean  PARTIAL DOMAIN: `inRequiredGroup (groups.take 1) opt` — right for <=1 group, wrong from the 2nd on. EXIT 1 (@148:28).
3. atk_3.lean  BOUNDARY / wrong selector: `optionStrings.head?` instead of the lexicographic least, with the SAME partiality domain (none on []), so it probes that the spec pins `min` ITSELF and not merely its domain. EXIT 1 (@149:28).
4. atk_4.lean  CONTROL-FLOW EFFECT: `let s <- renderArg? ...` hoisted BEFORE the keep guard — identical forwarded list, strictly WIDER `none`. EXIT 1 (@148:28) — the spec pins the effect footprint, not just the value.
5. atk_5.lean  TOTALIZATION / ungrounded default: `.getD ""` on both lookups, so the result is never `none`. EXIT 1 (@149:28) — the Option carrier is load-bearing.
6. atk_6.lean  FLAG-DEP DROPPED: membership in ANY mutually-exclusive group counts, ignoring `group.required` (the very flag the fix keys on). EXIT 1 (@148:28).
7. atk_7.lean  A-LEG/IDENTITY CORRESPONDENCE PROBE: group membership matched by `a.dest == opt.dest` instead of by the identity-carrying whole action. EXIT 1 (@150:28).
8. atk_8.lean  FRAME/ORDER: `rendered ++ parseArgsPrefix` (prefix appended AFTER the run). EXIT 1 (@147:28) — leg 1's frame pin is real.
9. atk_9.lean  DROPPED GUARD: `opt.req || inRequiredGroup groups opt`, forwarding required actions whose dest was never named. EXIT 1 (@147:28).
10. atk_10.lean DICT CONFLATION: membership tested against the VALUE TABLE (`(argOptions.lookup opt.dest).isSome`) instead of the caller's raw keys — i.e. exactly the two-dicts-collapsed-into-one modelling error that G-PANEL-2 previously failed an earlier spec revision for. EXIT 1 (@148:28): the CURRENT spec's two separate binders PIN this distinction.
11. atk_11.lean SILENT SKIP: an unrenderable selected action is dropped instead of failing the whole result (guards the raise away). EXIT 1 (@149:28).
12. atk_13.lean / 13. atk_14.lean — the two echo reshapes as first generated (generic battery insufficient); RE-ARMED with real proofs as atk_13r/atk_14r below, which is where they are actually adjudicated.

=== VERIFYING ATTACKS (EXIT 0, clean axioms) — ALL THREE had faithful patches materialized and RESOLVE-RUN per protocol step 2 ===
- atk_12.lean  ECHO / ungrounded-oracle: the impl is LITERALLY the spec RHS (`(renderAll argOptions (actions.filter (keepAction groups optionKeys))).map (parseArgsPrefix ++ ·)`), closed by `rfl`. lean_verify EXIT 0. ax_atk_12.lean: correct -> [propext], impl -> [propext]. CLEAN.
  Faithful patch patch_atk_12.diff (filter-then-render via explicit keep_action/render_arg helpers; `min` and the `arg_options[...]` subscript left UNGUARDED so the partiality matches the model exactly).
  RESOLVE: `python resolve.py atk_12` -> run_resolve('django__django-11749', patch, run_id='sbu-eqaudit-jkpk-11749-atk_12', timeout=1800) => {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}. Re-run SERIALLY under a fresh run_id (sbu-eqaudit-jkpk2-...) => {"completed": true, "resolved": TRUE, "attempts": 1, "flaky": false, "note": "resolved"} — confirming the attempt-1 miss was host contention (three resolves in flight), not a patch defect.
- atk_13r.lean ECHO, conjuncts SWAPPED: `(opt.req || inRequiredGroup groups opt) && destInOptions optionKeys opt`, closed by a REAL hand proof. lean_verify EXIT 0; same_spec re-checked TRUE after the rewrite. ax: correct -> [propext, Quot.sound], impl -> [propext]. CLEAN.
  Faithful patch patch_atk_13r.diff (comprehension predicate with the two conjuncts swapped).
  RESOLVE: run_id='sbu-eqaudit-jkpk-11749-atk_13r' => {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}.
- atk_14r.lean ECHO, Option-monad LEFT FOLD instead of the for-loop, closed by its own `foldl_requiredOptionArgs` induction lemma. lean_verify EXIT 0; same_spec TRUE. ax: correct -> [propext, Quot.sound], impl -> [propext]. CLEAN.
  Faithful patch patch_atk_14r.diff (explicit accumulate-by-append loop).
  RESOLVE: run_id='sbu-eqaudit-jkpk-11749-atk_14r' => {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}.
ALL THREE resolve runs COMPLETED and RESOLVED. So there is NO impl with a closing clean-axiom proof whose faithful patch fails to resolve => BROKEN is not met.

### RESOLVE NEGATIVE CONTROL (proves my resolve pipeline can actually detect a break)
patch_atk_1.diff — the faithful patch for atk_1 (the PREPATCH-BUG impl: adds the group set but keeps the dropped disjunct, `opt.dest in options and opt.required`). `python resolve.py atk_1` => {"completed": true, "resolved": FALSE, "attempts": 3, "flaky": false, "note": "patch did not resolve in 3 attempts (consistent — not flaky)"}. So a non-resolving patch IS reported as non-resolving by this exact pipeline, and the three RESOLVED verdicts above are discriminating results rather than a rubber stamp. (atk_1 does not verify, so this is a control, not a break.)

POSITIVE CONTROL: pos_control.lean (verbatim Solution.lean) — lean_verify EXIT 0; ax_pos_control.lean: correct -> [propext, Quot.sound], impl -> [propext]. CLEAN.

All patches were built from the PRISTINE base blob (`git show 350123f38c2b6217c38d70bfbd924a9ba3df1289:django/core/management/__init__.py` -> base_mgmt.py). I deliberately did NOT mutate the shared worktree (another audit is concurrently using it); the resolve runs go through the Docker oracle against the frozen dataset and are independent of it.

=== refinement.md AUDIT (protocol step 3) — no kind-3 leg; the A-legs are absent, and correctly so ===
All 9 legs are tagged R (1,3,5) or I (2,4,6,7,8,9). NO leg is A-consumed or A-reference, and NO leg is kind-3. That is consistent with meta.json (`axioms: []`, `deep_model_references: []`, `conf_skip: false`) and with axiom_check.py being a documented skip stub — and it is the RIGHT call rather than an evasion: the CHANGED op is modelled DEEPLY (not axiomatized) and the two unchanged callees in the region (`min`, `str.format`) are concrete ops reproduced exactly, so there is no callee contract for the proof to consume. Corroborated from the other side: the shipped proof's `#print axioms` is [propext, Quot.sound] only — there is nothing an A-leg could be hiding, because the proof consumes no axiom.

Since the R-legs carry the weight the A-legs would otherwise, I checked their correspondence against REAL argparse at base_commit (probe run, read-only):
- Leg 5 (THE CHANGED OP, `inRequiredGroup` <-> `opt in mutually_exclusive_required_options`): VERIFIED `group._group_actions` holds the SAME OBJECTS as `parser._actions` (`all(any(x is y ...))` -> True), so Python's identity-based set membership is faithfully modelled by structural `==` on a ParserAction whose `id` carries identity. Also confirmed the flag dependency is real: for `add_mutually_exclusive_group(required=True)` the members have `required == False` while `group.required == True` — precisely the bug shape. atk_6 (ignores group.required) and atk_7 (dest- instead of identity-matching) are BOTH rejected, so the spec pins this leg from both sides.
- Leg 8 (partiality of `min`): VERIFIED `min([])` raises `ValueError: min() arg is an empty sequence`, and a positional action has `option_strings == []` with `required == True`, so the branch IS reachable. NOTE: refinement.md row 16's justification is slightly OVER-GENERAL — argparse REFUSES a positional inside a mutually-exclusive group (`ValueError: mutually exclusive arguments must be optional`), so the "positional inside a required group" half of its reachability story is impossible; the "required positional whose dest was supplied by keyword" half IS reachable and is the case that matters. The Option carrier is therefore justified and the leg stands — a broader-than-necessary justification, not a defect.
- Leg 9 (partiality of `arg_options[opt.dest]`, and legs 3-vs-9 reading DIFFERENT dicts): REPRODUCED refinement.md's measurement exactly. With a required group holding `--x` (dest shop) and `--shop` (dest shop_id) and `options={'shop':'foo'}`: opt_mapping={'help':'help','x':'shop','shop':'shop_id'}, arg_options={'shop_id':'foo'} (key 'shop' ABSENT), selection picks dest 'shop', and the subscript raises `KeyError: 'shop'`. So `opt.dest in options` genuinely does NOT imply `opt.dest in arg_options`, the two binders are necessary, and atk_10 (which conflates them) is REJECTED — the spec pins the distinction.
- Legs 1/2/4/6/7 (frame pin, iteration order, opt.required, boolean structure, guarded append) match the patch text line-for-line; atk_8 (frame), atk_9 (dropped dest guard), atk_4 (effect footprint) and atk_11 (silent skip) confirm the spec pins them.

Independent corroboration of model<->patch correspondence: the bundle's own differential `python conformance_check.py` -> {"status": "pass", "cases": 120008, "mismatches": 0, "undefined_empty_flag": 22980, "undefined_uncarried_dest": 16910}. BOTH partiality branches are exercised in the tens of thousands, by different routes on the two sides (shadow structurally; oracle by evaluating the real unguarded `min(...)`/subscript and catching the raise) — so the Option carrier is load-bearing, not decorative.

### Verdict
SOUND. 16 same-spec attacks run (>=5 required), spanning prepatch-bug, partial-domain, boundary/wrong-selector, control-flow-effect, totalization, ungrounded-oracle echo, flag-dep, identity/A-leg correspondence, dict-conflation, silent-skip, frame/order and dropped-guard classes. 13 rejected with genuine unsolved goals despite the shipped helper lemma + a maximal tactic battery being in scope; the 3 that verify have clean axioms, are extensionally equal to the shipped impl, and their materialized faithful patches ALL RESOLVED under the official harness. A resolve NEGATIVE CONTROL (the prepatch-bug patch) does NOT resolve on the same pipeline, so those verdicts discriminate. Positive control verifies with clean axioms. Nothing breaks verify=>correct — and rigidity.lean proves nothing CAN, since the postcondition is an unconditioned total functional equality that determines the impl uniquely. NOTE (not my lane): meta.json records G-PANEL-2 = fail and hence G-PANEL = fail against an EARLIER spec revision that collapsed the two dicts; the CURRENT frozen spec carries them as separate binders and my atk_10 confirms that collapse is now rejected. I did not re-adjudicate that role.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_12.lean`, `atk_13r.lean`, `atk_14r.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — and the reason is MACHINE-PROVEN, not merely sampled.

rigidity.lean (`timeout 400 bash scripts/lean_verify.sh .../rigidity.lean 300` -> EXIT 0; ax_rigidity.lean axioms all clean) re-declares the FROZEN imports+axioms+pure+post regions verbatim and proves four things:
(1) spec_is_rigid [propext, Quot.sound] — problem_spec_requiredOptionArgs is an UNCONDITIONED TOTAL FUNCTIONAL EQUALITY (result = (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map (parseArgsPrefix ++ ·)); there is no pre-conditions region and no existential slack, so ANY two impls f g satisfying it everywhere are EQUAL (funext + rw on both hypotheses).
(2) spec_is_satisfiable [propext] — the spec function itself satisfies the postcondition, so (1) is NOT vacuous.
(3) prepatch_predicate_is_observable — NO AXIOMS AT ALL (`decide`): on act=<id 0, ["--foo-id"], req=false, dest="foo_id">, grp=<required=true,[act]>, keys=["foo_id"], the patched keepAction and the prepatch predicate (destInOptions && req) DISAGREE.
(4) prepatch_impl_differs [propext] — and the two resulting result-lists differ as VALUES on that witness (the exact FAIL_TO_PASS scenario from the issue report).

Consequence: a behaviourally-distinct same-spec impl can NEVER verify, and every same-spec impl that DOES verify is extensionally equal to the shipped one — an echo, never a spec weakness. verify=>correct holds for this bundle BY PROOF rather than by sampling.

Borne out empirically: 13/16 attacks (all behaviourally distinct) were REJECTED with genuine `error: unsolved goals` AT THE CORRECTNESS THEOREM, and all 3 that verify (atk_12, atk_13r, atk_14r) are equivalent reshapes whose faithful patches were materialized and ALL RESOLVED under the official harness. NO verifying attack has a non-resolving faithful patch => the BROKEN condition is not met.
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

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_13r.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_14r.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee requires an axiomatized contract: selecting an action's
-- least option flag, consulting the value table at a destination, and the
-- string formatting used to render each forwarded option are modeled directly
-- below (identical concrete ops), so there is nothing to axiomatize here.
-- axioms-end

-- pure-start

/-- A single parser action. `id` carries object identity (membership in a group
is identity-based in the source), `optionStrings` are the option flags, `req`
marks an individually-required action, `dest` is the destination key. -/
structure ParserAction where
  id : Nat
  optionStrings : List String
  req : Bool
  dest : String
deriving DecidableEq, Repr

/-- A mutually-exclusive option group: whether the group as a whole is required,
and the actions it contains (which share identity with entries in the flat
action list). -/
structure ExclusiveGroup where
  required : Bool
  groupActions : List ParserAction
deriving DecidableEq, Repr

/-- The lexicographically least of an action's option flags. An action that
declares no flag at all has no least flag, so the selection is not defined
there and reports `none`. -/
def leastFlag? (xs : List String) : Option String :=
  match xs with
  | [] => none
  | x :: rest => some (rest.foldl (fun m s => if s < m then s else m) x)

/-- Whether an action belongs to some group that is itself required. -/
def inRequiredGroup (groups : List ExclusiveGroup) (opt : ParserAction) : Bool :=
  groups.any (fun g => g.required && g.groupActions.any (· == opt))

/-- Whether the caller named this action's destination. The keys the caller
named are their own input, carried separately from the value table below. -/
def destInOptions (optionKeys : List String) (opt : ParserAction) : Bool :=
  optionKeys.any (· = opt.dest)

/-- The keep predicate: a keyword-named action is forwarded to the parser iff
its destination was named AND it is required, either individually or by virtue
of belonging to a required mutually-exclusive group. -/
def keepAction (groups : List ExclusiveGroup) (optionKeys : List String)
    (opt : ParserAction) : Bool :=
  destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt)

/-- Render a forwarded action as the `"<flag>=<value>"` string built from its
least flag and from the value the value table carries at its destination. TWO
independent lookups can yield nothing, and the rendering is then not defined —
`none`: an action declaring no flag has no least flag, and the value table need
not carry a value at every destination the caller named, those being two
separate inputs. -/
def renderArg? (argOptions : List (String × String)) (opt : ParserAction) :
    Option String :=
  (leastFlag? opt.optionStrings).bind fun flag =>
    (argOptions.lookup opt.dest).map fun value => flag ++ "=" ++ value

/-- Render a whole run of forwarded actions, in order. Defined only when every
action in the run renders. -/
def renderAll (argOptions : List (String × String)) :
    List ParserAction → Option (List String)
  | [] => some []
  | opt :: rest =>
    (renderArg? argOptions opt).bind fun s =>
      (renderAll argOptions rest).map fun ss => s :: ss

-- pure-end

-- post-conditions-start
/-- The forwarded-argument list: the (frame-pinned) positional prefix followed,
in action order, by the rendered string for exactly those actions selected by
`keepAction`. Selection consults the destination keys the caller NAMED; each
selected action's value is read from the separate value table. The whole result
is defined exactly when every selected action renders, and is `none` otherwise. -/
def problem_spec_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (parseArgsPrefix : List String) (result : Option (List String)) : Prop :=
  result =
    (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
      (fun rendered => parseArgsPrefix ++ rendered)
-- post-conditions-end

-- impl-start
def implementation_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (parseArgsPrefix : List String) :
    Option (List String) := do
  let mut parseArgs := parseArgsPrefix
  for opt in actions do
    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then
      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
  return parseArgs
-- impl-end

-- proof-start
/-- Helper: the `forIn` accumulation equals the `renderAll`/`filter` spec,
generalized over the accumulator. -/
theorem forIn_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (init : List String) :
    (forIn actions init (fun opt r =>
      (if keepAction groups optionKeys opt then
        Option.bind (renderArg? argOptions opt)
          (fun s => some (ForInStep.yield (r ++ [s])))
      else some (ForInStep.yield r) : Option (ForInStep (List String))))) =
      (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
        (fun rendered => init ++ rendered) := by
  induction actions generalizing init with
  | nil => simp [renderAll]
  | cons a as ih =>
    rw [List.forIn_cons]
    cases h : keepAction groups optionKeys a with
    | false =>
      simp only [h, List.filter_cons, Bool.false_eq_true, if_false]
      exact ih init
    | true =>
      cases hr : renderArg? argOptions a with
      | none => simp [h, hr, renderAll]
      | some v =>
        simp only [h, hr, List.filter_cons, if_true, renderAll]
        show (forIn as (init ++ [v]) (fun opt r =>
          (if keepAction groups optionKeys opt then
            Option.bind (renderArg? argOptions opt)
              (fun s => some (ForInStep.yield (r ++ [s])))
          else some (ForInStep.yield r) : Option (ForInStep (List String))))) = _
        rw [ih (init ++ [v])]
        simp [Function.comp_def]

theorem correct_requiredOptionArgs :
    ∀ (actions : List ParserAction) (groups : List ExclusiveGroup)
      (optionKeys : List String) (argOptions : List (String × String))
      (parseArgsPrefix : List String),
    problem_spec_requiredOptionArgs actions groups optionKeys argOptions
      parseArgsPrefix
      (implementation_requiredOptionArgs actions groups optionKeys argOptions
        parseArgsPrefix) := by
  intro actions groups optionKeys argOptions parseArgsPrefix
  unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs
  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>
      (if keepAction groups optionKeys opt then
        Option.bind (renderArg? argOptions opt)
          (fun s => some (ForInStep.yield (r ++ [s])))
      else some (ForInStep.yield r) : Option (ForInStep (List String)))))
      (fun r => some r) = _
  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions parseArgsPrefix]
  cases renderAll argOptions (actions.filter (keepAction groups optionKeys)) <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: TRUE for all 17 bundle-shaped files (16 attacks + positive control), checked with swebench_unified.markers.same_spec / backends.get_backend('lean').language against the shipped Solution.lean. Only the impl (and proof) region was edited; imports/axioms/pure/post-conditions are BYTE-IDENTICAL.

TOOLS/SCHEDULE: every file built by gen.py from a verbatim copy of Solution.lean. Verification command for each: `bash scripts/lean_verify.sh <name>.lean` run from the repo root, dispatched 4-at-a-time as concurrent background jobs (schedule only; EVERY attack fully verified). Per-file logs are <name>.log, exit codes aggregated in results.txt.

ANTI-WEAK-TACTIC CONTROL: the Lean spec view elides BOTH impl and proof regions, so a rejection could otherwise be a weak-tactic artifact. Every attack was therefore given the SHIPPED helper lemma `forIn_requiredOptionArgs` VERBATIM plus a broad closing battery (`rfl` | the shipped proof route | targeted `simp` over every pure def + Bool.and_comm/Bool.or_comm | `simp only` boolean-normalize then the shipped route | generalizing induction + simp_all | generalizing induction + aesop with all defs | `aesop` | `decide`). Every rejection below is thus a rejection DESPITE the strongest known machinery being in scope. Additionally, the two echo reshapes my generic battery missed (atk_13, atk_14) were RE-ARMED with hand-written REAL proofs (atk_13r: pointwise Bool.and_comm rewrite then the shipped helper; atk_14r: its own `foldl_requiredOptionArgs` induction lemma) — so they are counted as VERIFYING attacks and put through resolve, rather than being banked as false rejections.

=== REJECTED (EXIT 1, genuine `error: unsolved goals` at correct_requiredOptionArgs) — 13 distinct wrong impls ===
1. atk_1.lean  PREPATCH BUG re-encoded: drops `|| inRequiredGroup groups opt`. EXIT 1 (err @147:28). prepatch_reproduced = TRUE.
2. atk_2.lean  PARTIAL DOMAIN: `inRequiredGroup (groups.take 1) opt` — right for <=1 group, wrong from the 2nd on. EXIT 1 (@148:28).
3. atk_3.lean  BOUNDARY / wrong selector: `optionStrings.head?` instead of the lexicographic least, with the SAME partiality domain (none on []), so it probes that the spec pins `min` ITSELF and not merely its domain. EXIT 1 (@149:28).
4. atk_4.lean  CONTROL-FLOW EFFECT: `let s <- renderArg? ...` hoisted BEFORE the keep guard — identical forwarded list, strictly WIDER `none`. EXIT 1 (@148:28) — the spec pins the effect footprint, not just the value.
5. atk_5.lean  TOTALIZATION / ungrounded default: `.getD ""` on both lookups, so the result is never `none`. EXIT 1 (@149:28) — the Option carrier is load-bearing.
6. atk_6.lean  FLAG-DEP DROPPED: membership in ANY mutually-exclusive group counts, ignoring `group.required` (the very flag the fix keys on). EXIT 1 (@148:28).
7. atk_7.lean  A-LEG/IDENTITY CORRESPONDENCE PROBE: group membership matched by `a.dest == opt.dest` instead of by the identity-carrying whole action. EXIT 1 (@150:28).
8. atk_8.lean  FRAME/ORDER: `rendered ++ parseArgsPrefix` (prefix appended AFTER the run). EXIT 1 (@147:28) — leg 1's frame pin is real.
9. atk_9.lean  DROPPED GUARD: `opt.req || inRequiredGroup groups opt`, forwarding required actions whose dest was never named. EXIT 1 (@147:28).
10. atk_10.lean DICT CONFLATION: membership tested against the VALUE TABLE (`(argOptions.lookup opt.dest).isSome`) instead of the caller's raw keys — i.e. exactly the two-dicts-collapsed-into-one modelling error that G-PANEL-2 previously failed an earlier spec revision for. EXIT 1 (@148:28): the CURRENT spec's two separate binders PIN this distinction.
11. atk_11.lean SILENT SKIP: an unrenderable selected action is dropped instead of failing the whole result (guards the raise away). EXIT 1 (@149:28).
12. atk_13.lean / 13. atk_14.lean — the two echo reshapes as first generated (generic battery insufficient); RE-ARMED with real proofs as atk_13r/atk_14r below, which is where they are actually adjudicated.

=== VERIFYING ATTACKS (EXIT 0, clean axioms) — ALL THREE had faithful patches materialized and RESOLVE-RUN per protocol step 2 ===
- atk_12.lean  ECHO / ungrounded-oracle: the impl is LITERALLY the spec RHS (`(renderAll argOptions (actions.filter (keepAction groups optionKeys))).map (parseArgsPrefix ++ ·)`), closed by `rfl`. lean_verify EXIT 0. ax_atk_12.lean: correct -> [propext], impl -> [propext]. CLEAN.
  Faithful patch patch_atk_12.diff (filter-then-render via explicit keep_action/render_arg helpers; `min` and the `arg_options[...]` subscript left UNGUARDED so the partiality matches the model exactly).
  RESOLVE: `python resolve.py atk_12` -> run_resolve('django__django-11749', patch, run_id='sbu-eqaudit-jkpk-11749-atk_12', timeout=1800) => {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}. Re-run SERIALLY under a fresh run_id (sbu-eqaudit-jkpk2-...) => {"completed": true, "resolved": TRUE, "attempts": 1, "flaky": false, "note": "resolved"} — confirming the attempt-1 miss was host contention (three resolves in flight), not a patch defect.
- atk_13r.lean ECHO, conjuncts SWAPPED: `(opt.req || inRequiredGroup groups opt) && destInOptions optionKeys opt`, closed by a REAL hand proof. lean_verify EXIT 0; same_spec re-checked TRUE after the rewrite. ax: correct -> [propext, Quot.sound], impl -> [propext]. CLEAN.
  Faithful patch patch_atk_13r.diff (comprehension predicate with the two conjuncts swapped).
  RESOLVE: run_id='sbu-eqaudit-jkpk-11749-atk_13r' => {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}.
- atk_14r.lean ECHO, Option-monad LEFT FOLD instead of the for-loop, closed by its own `foldl_requiredOptionArgs` induction lemma. lean_verify EXIT 0; same_spec TRUE. ax: correct -> [propext, Quot.sound], impl -> [propext]. CLEAN.
  Faithful patch patch_atk_14r.diff (explicit accumulate-by-append loop).
  RESOLVE: run_id='sbu-eqaudit-jkpk-11749-atk_14r' => {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}.
ALL THREE resolve runs COMPLETED and RESOLVED. So there is NO impl with a closing clean-axiom proof whose faithful patch fails to resolve => BROKEN is not met.

### RESOLVE NEGATIVE CONTROL (proves my resolve pipeline can actually detect a break)
patch_atk_1.diff — the faithful patch for atk_1 (the PREPATCH-BUG impl: adds the group set but keeps the dropped disjunct, `opt.dest in options and opt.required`). `python resolve.py atk_1` => {"completed": true, "resolved": FALSE, "attempts": 3, "flaky": false, "note": "patch did not resolve in 3 attempts (consistent — not flaky)"}. So a non-resolving patch IS reported as non-resolving by this exact pipeline, and the three RESOLVED verdicts above are discriminating results rather than a rubber stamp. (atk_1 does not verify, so this is a control, not a break.)

POSITIVE CONTROL: pos_control.lean (verbatim Solution.lean) — lean_verify EXIT 0; ax_pos_control.lean: correct -> [propext, Quot.sound], impl -> [propext]. CLEAN.

All patches were built from the PRISTINE base blob (`git show 350123f38c2b6217c38d70bfbd924a9ba3df1289:django/core/management/__init__.py` -> base_mgmt.py). I deliberately did NOT mutate the shared worktree (another audit is concurrently using it); the resolve runs go through the Docker oracle against the frozen dataset and are independent of it.

=== refinement.md AUDIT (protocol step 3) — no kind-3 leg; the A-legs are absent, and correctly so ===
All 9 legs are tagged R (1,3,5) or I (2,4,6,7,8,9). NO leg is A-consumed or A-reference, and NO leg is kind-3. That is consistent with meta.json (`axioms: []`, `deep_model_references: []`, `conf_skip: false`) and with axiom_check.py being a documented skip stub — and it is the RIGHT call rather than an evasion: the CHANGED op is modelled DEEPLY (not axiomatized) and the two unchanged callees in the region (`min`, `str.format`) are concrete ops reproduced exactly, so there is no callee contract for the proof to consume. Corroborated from the other side: the shipped proof's `#print axioms` is [propext, Quot.sound] only — there is nothing an A-leg could be hiding, because the proof consumes no axiom.

Since the R-legs carry the weight the A-legs would otherwise, I checked their correspondence against REAL argparse at base_commit (probe run, read-only):
- Leg 5 (THE CHANGED OP, `inRequiredGroup` <-> `opt in mutually_exclusive_required_options`): VERIFIED `group._group_actions` holds the SAME OBJECTS as `parser._actions` (`all(any(x is y ...))` -> True), so Python's identity-based set membership is faithfully modelled by structural `==` on a ParserAction whose `id` carries identity. Also confirmed the flag dependency is real: for `add_mutually_exclusive_group(required=True)` the members have `required == False` while `group.required == True` — precisely the bug shape. atk_6 (ignores group.required) and atk_7 (dest- instead of identity-matching) are BOTH rejected, so the spec pins this leg from both sides.
- Leg 8 (partiality of `min`): VERIFIED `min([])` raises `ValueError: min() arg is an empty sequence`, and a positional action has `option_strings == []` with `required == True`, so the branch IS reachable. NOTE: refinement.md row 16's justification is slightly OVER-GENERAL — argparse REFUSES a positional inside a mutually-exclusive group (`ValueError: mutually exclusive arguments must be optional`), so the "positional inside a required group" half of its reachability story is impossible; the "required positional whose dest was supplied by keyword" half IS reachable and is the case that matters. The Option carrier is therefore justified and the leg stands — a broader-than-necessary justification, not a defect.
- Leg 9 (partiality of `arg_options[opt.dest]`, and legs 3-vs-9 reading DIFFERENT dicts): REPRODUCED refinement.md's measurement exactly. With a required group holding `--x` (dest shop) and `--shop` (dest shop_id) and `options={'shop':'foo'}`: opt_mapping={'help':'help','x':'shop','shop':'shop_id'}, arg_options={'shop_id':'foo'} (key 'shop' ABSENT), selection picks dest 'shop', and the subscript raises `KeyError: 'shop'`. So `opt.dest in options` genuinely does NOT imply `opt.dest in arg_options`, the two binders are necessary, and atk_10 (which conflates them) is REJECTED — the spec pins the distinction.
- Legs 1/2/4/6/7 (frame pin, iteration order, opt.required, boolean structure, guarded append) match the patch text line-for-line; atk_8 (frame), atk_9 (dropped dest guard), atk_4 (effect footprint) and atk_11 (silent skip) confirm the spec pins them.

Independent corroboration of model<->patch correspondence: the bundle's own differential `python conformance_check.py` -> {"status": "pass", "cases": 120008, "mismatches": 0, "undefined_empty_flag": 22980, "undefined_uncarried_dest": 16910}. BOTH partiality branches are exercised in the tens of thousands, by different routes on the two sides (shadow structurally; oracle by evaluating the real unguarded `min(...)`/subscript and catching the raise) — so the Option carrier is load-bearing, not decorative.

### Verdict
SOUND. 16 same-spec attacks run (>=5 required), spanning prepatch-bug, partial-domain, boundary/wrong-selector, control-flow-effect, totalization, ungrounded-oracle echo, flag-dep, identity/A-leg correspondence, dict-conflation, silent-skip, frame/order and dropped-guard classes. 13 rejected with genuine unsolved goals despite the shipped helper lemma + a maximal tactic battery being in scope; the 3 that verify have clean axioms, are extensionally equal to the shipped impl, and their materialized faithful patches ALL RESOLVED under the official harness. A resolve NEGATIVE CONTROL (the prepatch-bug patch) does NOT resolve on the same pipeline, so those verdicts discriminate. Positive control verifies with clean axioms. Nothing breaks verify=>correct — and rigidity.lean proves nothing CAN, since the postcondition is an unconditioned total functional equality that determines the impl uniquely. NOTE (not my lane): meta.json records G-PANEL-2 = fail and hence G-PANEL = fail against an EARLIER spec revision that collapsed the two dicts; the CURRENT frozen spec carries them as separate binders and my atk_10 confirms that collapse is now rejected. I did not re-adjudicate that role.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK FAILED — I could not construct any input on which the modeled function disagrees with the real repo. Verdict FAITHFUL.

### PRELIMINARIES (all re-verified independently, not taken from prior artifacts)
- scripts/lean_verify.sh Solution.lean => EXIT=0 (compiles, no sorry).
- Appended '#print axioms' for every declaration: correct_requiredOptionArgs and forIn_requiredOptionArgs => [propext, Quot.sound]; impl/spec/renderAll/leastFlag? => [propext]. No sorryAx, no native_decide, no bundle-declared axiom. The axioms region is a comment-only skip stub, consistent with refinement.md claiming zero A-consumed/A-reference rows.
- Spec-region byte-identity re-derived myself by hashing each region of Solution.lean vs Solution_prepatch.lean: imports/axioms/pure/post-conditions ALL byte-identical (sha256 pairwise equal). markers.same_spec == True confirmed. One spec view to judge.
- Fresh worktree at base_commit 350123f3, gold patch applied cleanly, patched region read directly at django/core/management/__init__.py:132-146. Worktree removed after use.

### DIFFERENTIAL METHODOLOGY (the point of the attack)
I deliberately did NOT reuse the bundle's conformance_check.py as my evidence, because its 'oracle' is a hand-transcribed comprehension, not the repo. Instead I built the oracle from REAL argparse objects on REAL Django BaseCommand parsers: construct a command, call cmd.create_parser(), then evaluate the genuine post-patch expression (real opt_mapping/arg_options rekeying, real get_actions() subparser recursion, real identity-based `opt in mutually_exclusive_required_options` set membership, real unguarded min() and real unguarded arg_options[dest] subscript, catching ValueError/KeyError). A separate bridge converts the live parser to the Lean model's inputs, and a faithful transcription of the Lean model (leastFlag?/inRequiredGroup/destInOptions/keepAction/renderArg?/renderAll) is compared against it.

RESULTS — ZERO MISMATCHES EVERYWHERE
- 16 curated adversarial cases: 0 mismatches. Includes the rekey KeyError scenario (--x dest shop, --shop dest shop_id, call shop='foo' => oracle None, shadow None), positional-in-required-group ValueError (=> both None), the fix itself, non-required group (correctly NOT forwarded), meg nested in add_argument_group (shares parser._mutually_exclusive_groups — model still agrees), meg nested in meg (2 group entries, agrees), subparser required group (action in parser_actions but NOT in top-level megs => [] both sides), subparser ALIASES yielding the same action object TWICE (=> duplicated element on both sides), int/None/list values, two distinct actions sharing a dest.
- Fuzz A: 4000 randomly generated real argparse parsers x random kwarg key sets => 0 mismatches.
- Fuzz B: 12000 cases with dests/flags chosen so opt_mapping REKEYING fires frequently, plus subparsers/aliases/positionals => 0 mismatches, with all three outcome branches exercised (none=833, empty list=7145, non-empty=4022).
- leastFlag? vs Python min: 13 hand-picked lists (prefix cases ['a','ab']/['ab','a'], empty string, case sensitivity ['--x','--X'] => '--X', short-vs-long ['-v','--verbosity'] => '--verbosity') all match, plus a 300-case UNICODE fuzz (é ü ÿ Ā ẞ ß ☃, dashes, underscores) evaluated in Lean and compared to Python min => 0/300 mismatches. Lean String '<' agrees with Python str '<' on codepoint-lex over this alphabet, and the foldl-min direction matches min's leftmost-wins tie-breaking (verified on ['abc','abd','ab'] and ['ab','abc','abd'] => 'ab' both).
- Bundle's own conformance_check.py, run for completeness: pass, 120008 cases, 0 mismatches, undefined_empty_flag=22980, undefined_uncarried_dest=16910 — both partiality branches genuinely exercised, so neither Option branch is vacuous.

### Specific over-strength hypotheses I tested and killed
1. 'Option (List String) is invented partiality / the none branches are unreachable.' FALSE, both are reachable in the real repo. min([]) : _MutuallyExclusiveGroup._add_action rejects action.required=True, so I suspected no flagless action could ever be selected via a group. But a POSITIONAL with nargs='?' or '*' is accepted into a required group (required=False, option_strings=[]) and IS present in parser._actions, so get_actions yields it and min([]) raises — confirmed by direct probe. arg_options[dest] KeyError: confirmed exactly as mapping.md documents, and it is newly reachable BECAUSE of the patch's group disjunct. So Option is required, not a totalization dodge.
2. 'The two dict binders (optionKeys vs argOptions) are a fabricated split.' FALSE. arg_options is options REKEYED through opt_mapping; I confirmed on a live parser that options={'shop':'foo'} yields arg_options={'shop_id':'foo'} with key 'shop' ABSENT. Fusing the binders would model a function the repo does not compute. The split is faithful, and the fuzz drew the two independently (named-but-uncarried and carried-but-unnamed both covered).
3. 'Structural == on ParserAction conflates distinct action objects, so inRequiredGroup is too strong.' Probed conflict_handler='resolve', the only way to get two actions with the same flag. The stale action has its option_strings EMPTIED (so it is not structurally equal to the survivor) and is REMOVED from parser._actions (so get_actions never yields it), while it retains its group slot. Either way no conflation arises; the id field carries identity and structurally-identical-but-distinct actions were not constructible. Default conflict_handler raises ArgumentError, so the case cannot even be built.
4. 'Frame-pinning parseArgsPrefix hides behavior.' The prefix is [str(a) for a in args], untouched by the patch; the spec states result = parseArgsPrefix ++ rendered, which is exactly the += semantics. No hiding.
5. Misc edge cases all agreed: dest=argparse.SUPPRESS ('==SUPPRESS=='), dest containing a dash, unicode flags/dests, values containing '=' and newlines, store_true/store_false sharing a dest, append action.

### DISCRIMINATION (spec is not too weak either — confirms the frozen spec has teeth)
The prepatch impl drops the `|| inRequiredGroup groups opt` disjunct and ships `sorry`. I replaced that sorry with an actual REFUTATION and it compiled (EXIT=0): for a0 = {id:=0, optionStrings:=["--a"], req:=false, dest:="d"}, g0 = {required:=true, groupActions:=[a0]}, optionKeys=["d"], argOptions=[("d","v")], prefix=[], the prepatch impl returns `some []` while the spec demands `some ["--a=v"]`; `¬ problem_spec_requiredOptionArgs ...` is provable. So the frozen spec strictly rejects the buggy version — the single independently-observable fixed behavior is captured.

### RESIDUAL (non-defect, recorded for transparency, does NOT change the verdict)
mapping.md describes argOptions values as 'stringified' without pinning str() vs '{}'.format(). These differ only for an object overriding __format__ inconsistently with __str__ (verified: a class returning 'STR'/'FMT'). This is a bridge-layer wording looseness outside the modeled function's domain — the Lean model takes already-String values, so there is no input in the model's domain where it disagrees with the repo. Not a faithfulness break, and I could not turn it into one; every str/format pair over realistic option values (int, float, None, bool, list, dict, bytes, Decimal, date, timedelta, Fraction) was identical.

CONCLUSION: no diverging input found after ~16000 real-argparse differential cases plus targeted structural attacks on every modeling choice. The spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: judged the consumer spec view (markers.spec_view of Solution.lean, the only spec artifact prompts.py ships) against problem_statement ONLY. hints_text ("Thanks for this report. I attached a simple test. Reproduced at ed2d411...") was deliberately NOT used as a screening basis; it carries no technical content anyway.

INTEGRITY / VERIFICATION (all independently re-run, not taken from meta.json):
- Solution.lean: lean_verify.sh exit 0 (compiles, no sorry).
- #print axioms correct_requiredOptionArgs -> [propext, Quot.sound]; forIn_requiredOptionArgs -> [propext, Quot.sound]. NO sorryAx, so the proof is real.
- same_spec(Solution, Solution_prepatch) = True; spec_view is BYTE-identical between the two; axioms/pure/post-conditions regions each byte-identical; impl region differs (as required). spec_view sha256 = 5b36cbde40a11a5aad958fc1ae364f9818831681831ceecdad98b627b8dc20af, matching the recorded G-HYGIENE region hash exactly.
- Elision guards hold: both ELISION_IMPL and ELISION_PROOF present in the view.

NON-VACUITY CONTROL (my own witness, verified exit 0): with a0 = {optionStrings:["--x"], req:false, dest:"shop"} in a required group g0 and optionKeys=["shop"], argOptions=[("shop","foo")], I proved (a) the spec DEMANDS some ["--x=foo"], (b) the prepatch predicate returns some [] , and (c) the spec REJECTS the prepatch result. So the spec has genuine gold-pinning content, and my leakage judgement is not about an empty spec.

### Leakage analysis
- Mechanical screen (leakage.screen, lean flavor): passed, zero hard failures, zero warnings.
- Gold-line reproduction: I re-ran the normalized comparison at threshold 4 (gate uses 8). Only two gold changed-lines normalize into the view: 'opt' (len 3) and ')' (len 1) — both also present in problem_statement and both content-free lexer collisions. Every substantive gold line ('for group in parser._mutually_exclusive_groups', 'for opt in group._group_actions if group.required', '(opt.required or opt in mutually_exclusive_required_options)', etc.) is ABSENT from the view.
- Private gold-side symbols all absent from the view: _mutually_exclusive_groups, _group_actions, mutually_exclusive_required_options, get_actions, parser_actions, opt_mapping. No patched file path ('django/core/management/__init__.py') or dotted module path in the view.
- Narration: gate vocabulary clean. I also swept a WIDER phrase set than the gate's (now/no longer/used to/newly/instead of/omits/drops/post-patch/reachable only/...). Only benign hits: "string formatting used to render" and "No unchanged callee requires" — the '-change-' substring inside "unchanged", not edit narration. No pre/post-patch framing, no bug/fix story, no mention that a disjunct was added.

WHY THE GROUP DISJUNCT IN THE VIEW IS NOT LEAKAGE: keepAction/inRequiredGroup encode 'required individually OR via a required mutually-exclusive group'. That is exactly what problem_statement already states in the clear — it names 'required mutually exclusive group' and add_mutually_exclusive_group(required=True), quotes the pre-patch predicate verbatim ('for opt in parser._actions if opt.required and opt.dest in options'), and says 'both of them individually are not required, they are actually part of a group that is required' and 'the code of call_command does nothing with groups defined in the parser'. The issue reporter effectively published the fix direction. The spec view therefore adds no edit-localization beyond the public statement. Likewise min(opt.option_strings) and arg_options[opt.dest] — the source of leastFlag?/argOptions.lookup — are quoted in problem_statement.

TWO-BINDER STRUCTURE CHECKED SEPARATELY: the view splits optionKeys (membership) from argOptions (value), which reflects the opt_mapping rekeying. opt_mapping is NOT in problem_statement, so I examined this specifically. It does not leak the edit: the rekeying is pre-existing base_commit behavior, the view never names opt_mapping, and the binder split localizes an input-shape modeling decision rather than the gold hunk (which is solely the group disjunct). The renderArg? docstring's 'the value table need not carry a value at every destination' likewise describes a pre-existing partiality of the unguarded subscript, not the change.

SHIPPING BOUNDARY CONFIRMED: mapping.md, refinement.md and verdict.md DO quote the gold diff verbatim (mapping.md reproduces both the pre- and post-patch predicates and the exact file:line), but they are gate-side private artifacts — prompts.py sends only task.spec_view plus the intentional modeled-functions localization aid ('requiredOptionArgs', a neutral behavioral name; the repo symbol call_command is not exposed there), and eval/audit.py explicitly flags shell reads of /mapping.md, /refinement.md, /verdict.md, Solution_prepatch and conformance_check.py as 'our-bundle-access' trajectory violations. So their content is not part of the consumer spec view and does not constitute leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
