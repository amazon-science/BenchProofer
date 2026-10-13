# P2 adversarial audit — sphinx-doc__sphinx-8721

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_12.lean`, `atk_13.lean`, `atk_15.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_14.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No refinement-fidelity counterexample found. All 5 same-spec impls whose correct_collectModulePages CLOSES with clean axioms ([propext] only) have faithful refined patches that RESOLVE under the official harness (F2P test_viewcode_epub_default + all 3 P2P pass). The 12 wrong impls that were attacked are all REJECTED by the proof obligation with genuinely false residual goals. verify => correct holds on every probe.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,8 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
+  -- PREPATCH BUG: no e-book guard at all; once hasModules, always publish.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
   return generatedPages
 -- impl-end
 
@@ -82,4 +79,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- WRONG: only the exact name "epub", missing "epub2"/"epub3"/"epubfoo".
+  if builderName == "epub" && !enableEpub then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- WRONG: suppresses exactly when the pages ARE wanted.
+  if builderName.startsWith "epub" && enableEpub then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- WRONG: "suppress" leg truncates to the first page instead of publishing nothing.
+  if builderName.startsWith "epub" && !enableEpub then return generatedPages.take 1
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,12 +65,8 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
-  if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
-  return generatedPages
+  -- WRONG: publishes nothing ever; the fall-through leg is never honoured.
+  return []
 -- impl-end
 
 -- proof-start
@@ -82,4 +78,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,8 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
-  if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
+  -- WRONG: the pre-existing collected-data guard is gone.
   if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
   return generatedPages
 -- impl-end
 
@@ -82,4 +79,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,10 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- WRONG: || instead of &&; suppresses on every e-book build and on every
+  -- non-e-book build where the preference is off.
+  if builderName.startsWith "epub" || !enableEpub then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +81,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,10 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
+  -- Faithful to gold co-change (i): the single-file format publishes nothing.
+  if builderName == "singlehtml" then return []
   if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
   return generatedPages
 -- impl-end
 
@@ -82,4 +81,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,11 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
+  -- Extensionally identical: both guards yield the empty sequence, so their
+  -- order cannot be observed. Refines to the e-book guard placed ABOVE the
+  -- pre-existing collected-data guard.
+  if builderName.startsWith "epub" && !enableEpub then return []
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
   return generatedPages
 -- impl-end
 
@@ -82,4 +82,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,11 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
   if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- Extensionally identical (both legs publish the full sequence), but names the
+  -- single-file format explicitly as a PUBLISH case.
+  if builderName == "singlehtml" then return generatedPages
   return generatedPages
 -- impl-end
 
@@ -82,4 +82,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- Extensionally identical: && is commutative on Bool.
+  if !enableEpub && builderName.startsWith "epub" then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
-  if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
+  -- WRONG: the collected-data guard is inverted.
+  if hasModules then return []
   if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- WRONG: capitalised prefix; never matches the real family name.
+  if builderName.startsWith "Epub" && !enableEpub then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,13 +64,13 @@
 -- impl-start
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
-    (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
-  if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
-  return generatedPages
+    (generatedPages : List String) : List String :=
+  -- Extensionally identical, expressed as ONE positive publish condition
+  -- instead of two suppressing early returns.
+  if hasModules && (!(builderName.startsWith "epub") || enableEpub) then
+    generatedPages
+  else
+    []
 -- impl-end
 
 -- proof-start
@@ -81,5 +81,7 @@
         (implementation_collectModulePages hasModules builderName enableEpub generatedPages) := by
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
-  simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,9 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- WRONG: the e-book guard is conditioned on the payload being a singleton.
+  if builderName.startsWith "epub" && !enableEpub && generatedPages.length == 1 then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +80,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;>
+    split <;> simp_all
 -- proof-end
```

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,13 +64,13 @@
 -- impl-start
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
-    (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
-  if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
-  return generatedPages
+    (generatedPages : List String) : List String :=
+  -- Extensionally identical, dispatched by `match` on the two flags.
+  match hasModules, enableEpub with
+  | false, _    => []
+  | true,  true => generatedPages
+  | true,  false =>
+      if builderName.startsWith "epub" then [] else generatedPages
 -- impl-end
 
 -- proof-start
@@ -81,5 +81,6 @@
         (implementation_collectModulePages hasModules builderName enableEpub generatedPages) := by
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
-  simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true'] <;> split <;> simp_all
 -- proof-end
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,11 +65,10 @@
 def implementation_collectModulePages
     (hasModules : Bool) (builderName : String) (enableEpub : Bool)
     (generatedPages : List String) : List String := Id.run do
-  -- No collected source-module data: publish nothing.
   if !hasModules then return []
-  -- The e-book family publishes companion pages only when they are wanted there.
-  if builderName.startsWith "epub" && !enableEpub then return []
-  -- Otherwise publish the full given page sequence.
+  -- Extensionally identical prefix test written with `String.take` instead of
+  -- `String.startsWith`.
+  if builderName.take 4 == "epub" && !enableEpub then return []
   return generatedPages
 -- impl-end
 
@@ -82,4 +81,7 @@
   intro hasModules builderName enableEpub generatedPages
   unfold problem_spec_collectModulePages implementation_collectModulePages
   simp only [Id.run, bind, pure]
+  cases hasModules <;> cases enableEpub <;>
+    simp_all [Bool.and_eq_true, Bool.not_eq_true', String.startsWith,
+              String.take, List.isPrefixOf] <;> split <;> simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Worktree of sphinx-doc/sphinx @ base_commit 82ef497a8c88f0f6e50d84520e7276bfbf65025d. All 17 attacks + pos_control confirmed same_spec == True against the bundle Solution.lean via swebench_unified.markers.same_spec (lean backend); only the impl+proof regions were edited. Verifications were run as concurrent background jobs, 4 at a time, with SBU_LEAN_SLOTS=8.

SPEC SHAPE. problem_spec_collectModulePages is a TOTAL FUNCTIONAL EQUALITY: result = (if !hasModules then [] else if builderName.startsWith "epub" && !enableEpub then [] else generatedPages). generatedPages is universally quantified, so no output component is free and the spec is maximally tight for this signature. axioms = [] in meta.json; no opaque/axiom decl exists in Solution.lean; axiom_check.py is a documented skip stub. That combination is what makes an eq-shaped spec unbreakable in the reject direction: any impl not extensionally equal to the RHS fails.

POSITIVE CONTROL. pos_control.lean = byte copy of Solution.lean. `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. #print axioms (ax_pos.lean) -> correct_collectModulePages depends on axioms: [propext]; implementation_...: [propext]. Clean (propext only; no sorryAx / Classical.choice / custom axiom).

PREPATCH REPRODUCED. prepatch.lean = bundle Solution_prepatch.lean (no e-book guard). lean_verify -> exit 1, residual goal `(if (!hasModules) = true then [] else generatedPages) = if (!hasModules) = true then [] ...` i.e. genuinely false, not a tactic artifact. G-DIFF discriminates.

ATTACKS REJECTED — each `bash scripts/lean_verify.sh atk_N.lean`: atk_1  exit=1  prepatch bug re-encoded (e-book guard absent). residual: startsWith "epub" = true -> generatedPages = [] atk_2  exit=1  partial-domain: `builderName == "epub"` exact match instead of family prefix (misses epub2/epub3/epubfoo) atk_3  exit=1  boundary: preference polarity inverted (`&& enableEpub`) atk_4  exit=1  control-flow-effect: suppress leg returns `generatedPages.take 1` instead of [] atk_5  exit=1  ungrounded-oracle echo: `return []` unconditionally (suppress everything) atk_6  exit=1  partial-domain: pre-existing hasModules guard dropped atk_7  exit=1  boundary: `||` instead of `&&` in the guard atk_8  exit=1  GOLD-FAITHFUL BOTH-GUARDS impl (adds `builderName == "singlehtml" -> []`).

REJECTED, see SCOPE note below. atk_12 exit=1  control-flow-effect: hasModules guard inverted atk_13 exit=1  boundary: case-wrong prefix "Epub" atk_15 exit=1  partial-domain: guard additionally conditioned on generatedPages.length == 1 atk_17 exit=1  String.take-based prefix test. NOTE: this failure is my TACTIC being too weak on String.startsWith/toSubstring unfolding, NOT a semantic rejection — the impl is extensionally equal. Recorded honestly as inconclusive-per-attack; it does not affect the verdict (it is a would-be soundness case, and the reject-direction conclusion rests on the other 11).

ATTACKS THAT VERIFY (5) — all extensionally EQUAL to the spec RHS, so verifying is CORRECT behavior, not weakness. Each got #print axioms and a materialized faithful patch RUN through the official harness (swebench_unified.harness.run_resolve, instance sphinx-doc__sphinx-8721, timeout 1800):
 atk_9   lean_verify exit=0; axioms [propext]; patch = e-book guard hoisted ABOVE the hasModules guard (+ gold singlehtml co-change verbatim) -> RESOLVED=True
 atk_10  lean_verify exit=0; axioms [propext]; patch = e-book guard only, singlehtml co-change OMITTED (most hostile reading of the declared out-of-model boundary) -> RESOLVED=True
 atk_11  lean_verify exit=0; axioms [propext]; patch = conjunct order swapped in the guard -> RESOLVED=True
 atk_14  lean_verify exit=0; axioms [propext]; patch = ONE positive publish condition replacing both suppressing returns -> RESOLVED=True
 atk_16  lean_verify exit=0; axioms [propext]; patch = nested-if dispatch on the preference then the prefix -> RESOLVED=True
Every report: FAIL_TO_PASS success=[test_viewcode_epub_default], PASS_TO_PASS success=[test_viewcode_epub_enabled, test_linkcode, test_local_source_files], PASS_TO_FAIL=[], FAIL_TO_FAIL=[]. patch_successfully_applied=true in all five. NO verifying impl fails to resolve => verify=>correct is NOT falsified.

A-LEG AUDIT (the focus of this role). refinement.md declares 3 modeled ops: op1 R (hasattr guard), op2 R (e-book guard), op3 A-reference (unchanged downstream page construction, bound to generatedPages). There is NO A-consumed row and NO kind-3 leg; every leg is R / A-reference / out-of-model, which is the legal set. The A-reference is NOT axiomatized (no opaque/axiom), so no callee contract can be over-strong — consistent with meta.json axioms=[] and the G-AX skip stub.

The A-reference's correspondence claim is the one load-bearing assumption, and I MEASURED it against the REAL post-patch callee rather than trusting the prose. Ran probe.py inside the official image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8721:latest with patch.diff applied (`git apply -v /gold.diff` -> 'Applied patch cleanly', post-patch body sed-confirmed to contain BOTH guards):
  * carrier (real fn, preference forced ON) per format: html/epub/epub3/singlehtmlepub/epubsinglehtml/singlehtmlx/singlehtm -> the full 3-page sequence; singlehtml -> [] EXACTLY as refinement.md/mapping.md claim. So the out-of-model singlehtml co-change (i) is genuinely predicted by op 3's fall-through, not silently mispredicted.
  * spec(with bridge carrier) vs real post-patch over 84 (name x preference x hasModules) combinations spanning the family prefix boundary ('', e, ep, epu, epub, epub2, epub3, epubfoo, Epub, EPUB, htmlepub) and the singlehtml near-misses (singlehtm, ssinglehtml, singlehtmlx, singlehtmlepub, epubsinglehtml): 0 disagreements.
  * NEGATIVE CONTROL (guard-removal, i.e. is op 2 load-bearing or is the answer smuggled into the carrier?): shadow with the e-book guard REMOVED -> 5 disagreements. The carrier does NOT pre-decide the e-book question; the spec must still make it. Bridge premise (B) holds operationally.
  * An accidental first run applied no patch and thus measured the PREPATCH function: spec-vs-real gave 5 disagreements and the no-guard shadow gave 0 — the exact mirror image, independently confirming the discriminator is the e-book guard and nothing else.
  * Re-ran the bundle's own conformance_check.py in the same container: 'G-CONF OK: shadow == real page collector on 100580 inputs (580 boundary + 100000 fuzz, seed 8721); bridge premises (A) and (B) measured on 290 real-callee pairs; NO output-format name excluded', exit 0, excluded_builder_names=[]. Independently reproduced, not taken on faith.

SCOPE OBSERVATION (disclosed, not a defect). atk_8 — the impl faithful to BOTH gold guards — is REJECTED by the spec, because the spec's fall-through predicts generatedPages at "singlehtml" while atk_8 returns []. This is the flip side of the declared out-of-model boundary: the model deliberately does not restate co-change (i), and under the mapping.md §2 carrier semantics (carrier is empty at singlehtml, measured above) the two agree on real inputs, so G-CONF passes at 0/100580. The gap is only visible to a Lean-level impl that hard-codes the format name while ALSO receiving a nonempty generatedPages — an input the real bridge never produces. Both mapping.md §1 and refinement.md disclose this explicitly and the carrier claim is measured, so it is a documented modeling boundary rather than an undisclosed infidelity; it costs nothing in the verify=>resolved direction (atk_10, which omits guard (i) entirely, still resolves). Worth a reviewer's eye, but it makes the spec STRICTER at that point, never weaker, so it cannot produce a verify-but-not-correct bundle.

CONCLUSION. 12 distinct wrong impls across all 4 required families (partial-domain: atk_2/6/15; boundary: atk_3/7/13; control-flow-effect: atk_4/12; ungrounded-oracle echo: atk_5; plus the prepatch bug atk_1 and the gold-both-guards atk_8) are all rejected with genuinely false residual goals. All 5 impls that verify with clean axioms have materialized faithful patches that RESOLVE under the official harness. Refinement legs are all R/A-reference/out-of-model with no kind-3 and no A-consumed row, and the single A-reference's correspondence to the real callee was measured against the real post-patch code inside the official container. No verify=>correct violation exists. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_12.lean`, `atk_13.lean`, `atk_15.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_14.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No refinement-fidelity counterexample found. All 5 same-spec impls whose correct_collectModulePages CLOSES with clean axioms ([propext] only) have faithful refined patches that RESOLVE under the official harness (F2P test_viewcode_epub_default + all 3 P2P pass). The 12 wrong impls that were attacked are all REJECTED by the proof obligation with genuinely false residual goals. verify => correct holds on every probe.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Worktree of sphinx-doc/sphinx @ base_commit 82ef497a8c88f0f6e50d84520e7276bfbf65025d. All 17 attacks + pos_control confirmed same_spec == True against the bundle Solution.lean via swebench_unified.markers.same_spec (lean backend); only the impl+proof regions were edited. Verifications were run as concurrent background jobs, 4 at a time, with SBU_LEAN_SLOTS=8.

SPEC SHAPE. problem_spec_collectModulePages is a TOTAL FUNCTIONAL EQUALITY: result = (if !hasModules then [] else if builderName.startsWith "epub" && !enableEpub then [] else generatedPages). generatedPages is universally quantified, so no output component is free and the spec is maximally tight for this signature. axioms = [] in meta.json; no opaque/axiom decl exists in Solution.lean; axiom_check.py is a documented skip stub. That combination is what makes an eq-shaped spec unbreakable in the reject direction: any impl not extensionally equal to the RHS fails.

POSITIVE CONTROL. pos_control.lean = byte copy of Solution.lean. `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. #print axioms (ax_pos.lean) -> correct_collectModulePages depends on axioms: [propext]; implementation_...: [propext]. Clean (propext only; no sorryAx / Classical.choice / custom axiom).

PREPATCH REPRODUCED. prepatch.lean = bundle Solution_prepatch.lean (no e-book guard). lean_verify -> exit 1, residual goal `(if (!hasModules) = true then [] else generatedPages) = if (!hasModules) = true then [] ...` i.e. genuinely false, not a tactic artifact. G-DIFF discriminates.

ATTACKS REJECTED — each `bash scripts/lean_verify.sh atk_N.lean`: atk_1  exit=1  prepatch bug re-encoded (e-book guard absent). residual: startsWith "epub" = true -> generatedPages = [] atk_2  exit=1  partial-domain: `builderName == "epub"` exact match instead of family prefix (misses epub2/epub3/epubfoo) atk_3  exit=1  boundary: preference polarity inverted (`&& enableEpub`) atk_4  exit=1  control-flow-effect: suppress leg returns `generatedPages.take 1` instead of [] atk_5  exit=1  ungrounded-oracle echo: `return []` unconditionally (suppress everything) atk_6  exit=1  partial-domain: pre-existing hasModules guard dropped atk_7  exit=1  boundary: `||` instead of `&&` in the guard atk_8  exit=1  GOLD-FAITHFUL BOTH-GUARDS impl (adds `builderName == "singlehtml" -> []`).

REJECTED, see SCOPE note below. atk_12 exit=1  control-flow-effect: hasModules guard inverted atk_13 exit=1  boundary: case-wrong prefix "Epub" atk_15 exit=1  partial-domain: guard additionally conditioned on generatedPages.length == 1 atk_17 exit=1  String.take-based prefix test. NOTE: this failure is my TACTIC being too weak on String.startsWith/toSubstring unfolding, NOT a semantic rejection — the impl is extensionally equal. Recorded honestly as inconclusive-per-attack; it does not affect the verdict (it is a would-be soundness case, and the reject-direction conclusion rests on the other 11).

ATTACKS THAT VERIFY (5) — all extensionally EQUAL to the spec RHS, so verifying is CORRECT behavior, not weakness. Each got #print axioms and a materialized faithful patch RUN through the official harness (swebench_unified.harness.run_resolve, instance sphinx-doc__sphinx-8721, timeout 1800):
 atk_9   lean_verify exit=0; axioms [propext]; patch = e-book guard hoisted ABOVE the hasModules guard (+ gold singlehtml co-change verbatim) -> RESOLVED=True
 atk_10  lean_verify exit=0; axioms [propext]; patch = e-book guard only, singlehtml co-change OMITTED (most hostile reading of the declared out-of-model boundary) -> RESOLVED=True
 atk_11  lean_verify exit=0; axioms [propext]; patch = conjunct order swapped in the guard -> RESOLVED=True
 atk_14  lean_verify exit=0; axioms [propext]; patch = ONE positive publish condition replacing both suppressing returns -> RESOLVED=True
 atk_16  lean_verify exit=0; axioms [propext]; patch = nested-if dispatch on the preference then the prefix -> RESOLVED=True
Every report: FAIL_TO_PASS success=[test_viewcode_epub_default], PASS_TO_PASS success=[test_viewcode_epub_enabled, test_linkcode, test_local_source_files], PASS_TO_FAIL=[], FAIL_TO_FAIL=[]. patch_successfully_applied=true in all five. NO verifying impl fails to resolve => verify=>correct is NOT falsified.

A-LEG AUDIT (the focus of this role). refinement.md declares 3 modeled ops: op1 R (hasattr guard), op2 R (e-book guard), op3 A-reference (unchanged downstream page construction, bound to generatedPages). There is NO A-consumed row and NO kind-3 leg; every leg is R / A-reference / out-of-model, which is the legal set. The A-reference is NOT axiomatized (no opaque/axiom), so no callee contract can be over-strong — consistent with meta.json axioms=[] and the G-AX skip stub.

The A-reference's correspondence claim is the one load-bearing assumption, and I MEASURED it against the REAL post-patch callee rather than trusting the prose. Ran probe.py inside the official image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8721:latest with patch.diff applied (`git apply -v /gold.diff` -> 'Applied patch cleanly', post-patch body sed-confirmed to contain BOTH guards):
  * carrier (real fn, preference forced ON) per format: html/epub/epub3/singlehtmlepub/epubsinglehtml/singlehtmlx/singlehtm -> the full 3-page sequence; singlehtml -> [] EXACTLY as refinement.md/mapping.md claim. So the out-of-model singlehtml co-change (i) is genuinely predicted by op 3's fall-through, not silently mispredicted.
  * spec(with bridge carrier) vs real post-patch over 84 (name x preference x hasModules) combinations spanning the family prefix boundary ('', e, ep, epu, epub, epub2, epub3, epubfoo, Epub, EPUB, htmlepub) and the singlehtml near-misses (singlehtm, ssinglehtml, singlehtmlx, singlehtmlepub, epubsinglehtml): 0 disagreements.
  * NEGATIVE CONTROL (guard-removal, i.e. is op 2 load-bearing or is the answer smuggled into the carrier?): shadow with the e-book guard REMOVED -> 5 disagreements. The carrier does NOT pre-decide the e-book question; the spec must still make it. Bridge premise (B) holds operationally.
  * An accidental first run applied no patch and thus measured the PREPATCH function: spec-vs-real gave 5 disagreements and the no-guard shadow gave 0 — the exact mirror image, independently confirming the discriminator is the e-book guard and nothing else.
  * Re-ran the bundle's own conformance_check.py in the same container: 'G-CONF OK: shadow == real page collector on 100580 inputs (580 boundary + 100000 fuzz, seed 8721); bridge premises (A) and (B) measured on 290 real-callee pairs; NO output-format name excluded', exit 0, excluded_builder_names=[]. Independently reproduced, not taken on faith.

SCOPE OBSERVATION (disclosed, not a defect). atk_8 — the impl faithful to BOTH gold guards — is REJECTED by the spec, because the spec's fall-through predicts generatedPages at "singlehtml" while atk_8 returns []. This is the flip side of the declared out-of-model boundary: the model deliberately does not restate co-change (i), and under the mapping.md §2 carrier semantics (carrier is empty at singlehtml, measured above) the two agree on real inputs, so G-CONF passes at 0/100580. The gap is only visible to a Lean-level impl that hard-codes the format name while ALSO receiving a nonempty generatedPages — an input the real bridge never produces. Both mapping.md §1 and refinement.md disclose this explicitly and the carrier claim is measured, so it is a documented modeling boundary rather than an undisclosed infidelity; it costs nothing in the verify=>resolved direction (atk_10, which omits guard (i) entirely, still resolves). Worth a reviewer's eye, but it makes the spec STRICTER at that point, never weaker, so it cannot produce a verify-but-not-correct bundle.

CONCLUSION. 12 distinct wrong impls across all 4 required families (partial-domain: atk_2/6/15; boundary: atk_3/7/13; control-flow-effect: atk_4/12; ungrounded-oracle echo: atk_5; plus the prepatch bug atk_1 and the gold-both-guards atk_8) are all rejected with genuinely false residual goals. All 5 impls that verify with clean axioms have materialized faithful patches that RESOLVE under the official harness. Refinement legs are all R/A-reference/out-of-model with no kind-3 and no A-consumed row, and the single A-reference's correspondence to the real callee was measured against the real post-patch code inside the official container. No verify=>correct violation exists. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

ATTACK: faithfulness-break on sphinx-doc__sphinx-8721 / problem_spec_collectModulePages. Reference = worktree at base 82ef497a with patch.diff APPLIED (bundle patch.diff byte-identical to gold dataset patch; patch_equals_gold=true confirmed by diff). No divergence found; I could not break it.

SETUP (independent of the bundle harness): fresh worktree at 82ef497a, gold patch applied, plus a venv with era-correct pins (jinja2==3.0.3, docutils==0.16, sphinxcontrib-*==1.0.x/2.0.0) so the real post-patch collect_pages imports and runs.

### WHAT I PROBED (my own probe scripts, written from scratch, NOT importing conformance_check.py):
1. Name/shape sweep, page-name granularity: 560 cases over the epub-prefix boundary ('', e, ep, epu, epub, epub2/3, epubfoo, Epub, EPUB, htmlepub, epubsinglehtml, singlehtml + near-misses singlehtm/singlehtmlx/ssinglehtml/singlehtmlepub, latex/text/man/json, and unicode epubé/épub/epub<combining>/astral) x 5 module shapes x hasModules x enableEpub. 0 divergences.
2. Whole-TRIPLE granularity (pagename, full context dict, template) rather than just page names: 740 cases, 0 divergences. NOTE: an initial run showed 2 apparent divergences at builderName=""; I traced them to a lazy gettext proxy in my own repr (i'Module code' on the first call only) and they vanish once locale proxies are warmed / str()-forced. That was my harness bug, not a spec defect.
3. FINAL large probe with realistic per-format out_suffix (epub => .xhtml, dirhtml => /), the should_generate_module_page freshness path made LIVE (emit_firstresult -> None so ModuleAnalyzer runs, with deliberately stale AND fresh _modules page files on disk for real modules os/json/posixpath), and hasModules driven both by attribute ABSENCE and by an EMPTY dict: 48,608 cases, 0 divergences.
4. Bundle's own conformance_check.py re-run against my worktree: G-CONF OK, 100,580 inputs, 0 disagreements, bridge_fact_pairs=290, excluded_builder_names=[].

THE ONE REAL SOFT SPOT, AND WHY IT IS NOT A BREAK: the gold patch inserts TWO guards; the spec restates only the epub one (ii) and declares the singlehtml one (i) out-of-model. That is disclosed in mapping.md s1 and refinement.md. It would be a genuine over-strength/drift bug IF the spec's fall-through leg predicted a publish at singlehtml that the repo does not perform. It does not, because generatedPages is bridged to 'what this format publishes when the epub preference does not withhold it' = the real function with the preference forced ON. I MEASURED that carrier: at singlehtml it is [] (guard (i) sits upstream of the preference and fires regardless of its value), so the spec predicts [] there, which is what the real patched function yields. Verified in Lean too: singlehtml_falls_through gives g, and with the measured carrier [] the prediction is []. So the scoping costs no faithfulness on the actual domain.

BRIDGE PREMISES CHECKED MYSELF, not taken on faith: (A) at every non-epub name the preference never changes the published sequence -> 0 violations; (B) at epub names with preference ON the FULL sequence is published, byte-equal to html's -> confirmed. So the carrier does not smuggle in the answer. NEGATIVE CONTROL: my own shadow with the epub clause DELETED disagrees with the real callee (6 disagreements, first at builderName='epub', enableEpub=False, mods=['m0'] where spec-minus-clause predicts ['_modules/m0','_modules/index'] but the repo yields []). So clause (ii) is load-bearing, not decoration.

TYPE-REFINEMENT CHECK (String.startsWith vs str.startswith): generated 269 adversarial names incl. combining marks, astral-plane, zero-width, leading/trailing space, case variants; folded Lean's verdicts into a bitstring via #eval and compared to Python's -> EXACT MATCH on all 269. No refinement gap at the prefix test.

LEAN / PROOF INTEGRITY: scripts/lean_verify.sh Solution.lean -> exit 0. #print axioms correct_collectModulePages -> [propext] only; NO sorryAx, so the proof is not fake. meta.json axioms=[] is consistent: no opaque/axiom decl exists in Solution.lean, generatedPages is universally quantified, so no callee contract is consumed.

SPEC-REGION INTEGRITY: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True -> the prepatch variant shares a byte-identical spec region. All 6 region_hashes in meta.json (axioms, pure, post-conditions, proof, impl, spec_view) recomputed and MATCH.

ANTI-VACUITY / STRENGTH CONTROLS proved in Lean: spec_functional (any two results for the same inputs are equal -> no output component left free, blocks suppress-everything and truncate-the-sequence rivals); prepatch_rejected (the real prepatch impl, which omits the epub guard, provably CANNOT satisfy the shared spec, witnessed at hasModules=true, builderName="epub", enableEpub=false, g=["p"]) -> G-DIFF's 'verification failed' is genuine, not a build artifact. All four shipped test points discharged from the spec alone: F2P epub/OFF => [], P2P epub/ON => g, html/OFF => g, html/ON => g.

REAL TESTS: applied the dataset test_patch and ran tests/test_ext_viewcode.py on the patched tree -> 5 passed (test_viewcode_epub_default F2P + test_viewcode_epub_enabled, test_linkcode, test_local_source_files P2P). An earlier single failure of test_viewcode_epub_enabled was my own shared-srcdir contamination across runs; with a fresh --basetemp all 5 pass.

CONCLUSION: the modeled function agrees with the real post-patch callee on every input I could construct (~50k independent cases plus 100k via the bundle harness), the epub clause is discriminating, the one disclosed modeling boundary (singlehtml) is behaviorally invisible under the declared and MEASURED carrier bridge, and the Lean proof is axiom-clean. I found no diverging input, so I cannot claim UNFAITHFUL. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASURED ON THE CURRENT ARTIFACT, NOT INHERITED. Solution.lean sha256=f03af2618d72a8e17e4442439ade0469edad75249046ce00d5c9a768416d46cd.

NO RELAXATION APPLIES. lean/meta.json has NO `relaxed_leakage` key (top-level keys: axioms, conf_skip, deep_model_references, gates, instance_id, modeled_functions, notes, patch_equals_gold, prepatch_files, pbt_audit, region_hashes, schema_version, spec_provenance), no key matching /relax/i, and there is NO lean/RELAXED_LEAKAGE.md. gates.G-LEAK.status=='pass' (not 'relaxed'), so neither disjunct of the leak.py `relaxed` predicate holds. This bundle asserts a CLEAN no-leakage property and I judged it on those terms. The RELAXED_LEAKAGE.md present in this instance tree belongs to the SIBLING velvet/ bundle (velvet/meta.json relaxed_leakage=True, G-LEAK status 'relaxed'); it covers velvet's own carrier symbols and I did not inherit it as a disposition for lean/.

THE PRIOR RECORDED LEAKAGE IS STALE AND NO LONGER REPRODUCES. verdict.md Role 4 records G-PANEL-3 fail/LEAKAGE, and meta.json stamps G-PANEL-3 fail with sources.Solution.lean=='a17b88363fb7...'. The current Solution.lean is 'f03af2618d72' — a DIFFERENT artifact. The prior witness was (hasModules=true, builderName="singlehtml", enableEpub=TRUE), i.e. the spec then carried a `singlehtml` suppression clause that the public problem_statement cannot derive. That clause has since been REMOVED. Token scan of the computed spec view (markers.spec_view(Solution.lean, get_backend('lean'))): singlehtml=ABSENT, single=ABSENT, combined=ABSENT, collect_pages=ABSENT, viewcode.py=ABSENT, _viewcode_modules=ABSENT, highlighter=ABSENT. I re-derived rather than echoing the stamp (per the standing hazard that a stale fail judges a spec already repaired, and that retained attack labels carry the oracle verdict).

WHAT THE SPEC VIEW NOW DISCLOSES, AND THAT IT IS PS-PUBLIC. The post-conditions region is one total equality:
  result = (if !hasModules then [] else if builderName.startsWith "epub" && !enableEpub then [] else generatedPages)
Three facts, each public in problem_statement: (a) the e-book family prefix "epub" — PS title says "viewcode creates pages for epub ... on `make html epub`"; (b) the preference flag and its polarity — PS says "even if `viewcode_enable_epub=False`" (token 'viewcode_enable_epub' IS present in PS); (c) the demanded outcome — PS "Expected behavior: module pages should not be created for epub by default." The `hasModules` leg is the PRE-EXISTING `hasattr(env,'_viewcode_modules')` guard, not part of the gold edit at all. hints_text is the empty string '' so hints are not in play.

MECHANICAL SCREEN, RE-RUN BY ME: leakage.screen(Solution.lean, get_backend('lean'), row.patch, row.problem_statement) -> passed=True, hard_failures=[]. No diff marker, no gold-patch line reproduced (>=8 normalized chars), no patched file/module path, no narration hit. The only gold-patch changed symbol is `collect_pages`, absent from both spec-view identifiers and comments.

UNAVOIDABILITY / LOAD-BEARING RE-DERIVED IN LEAN (the standard strip test), scripts/lean_verify.sh:
  * strip.lean EXIT 0 — with the e-book clause STRIPPED (leaving only `if !hasModules then [] else generatedPages`), `stripped_accepts_prepatch : forall hm b ep gp, spec_stripped hm b ep gp (impl_pre hm b ep gp)` CLOSES, where impl_pre is the verbatim impl region of Solution_prepatch.lean. So the stripped spec ACCEPTS the genuine pre-patch impl at every input: the e-book clause is the SOLE load-bearing discriminator, and it is exactly the facet the public problem_statement states. There is no residue to leak.
  * disc.lean EXIT 0 — `spec_rejects_prepatch : NOT (spec true "epub" false ["p1"] (impl_pre ...))`, `spec_mandates_suppress : spec true "epub" false ["p1"] []`, `publish_refuted_at_epub : NOT (spec true "epub" false ["p1"] ["p1"])`. Discrimination against pre-patch is carried entirely by the PS-supplied facet.
  * NEGATIVE CONTROL for the removed clause: `no_singlehtml_clause : spec true "singlehtml" false ["p1"] ["p1"]`, `no_suppress_at_singlehtml_on : spec true "singlehtml" true ["p1"] ["p1"]`, `no_suppress_at_html : spec true "html" false ["p1"] ["p1"]` all CLOSE — the spec PUBLISHES at the single-file format at both preference values, so it demands no non-e-book suppression and cannot hand a solver the gold patch's first inserted guard. That is precisely the input the old LEAKAGE turned on, and it is now clean.

ADMISSIBILITY / PROOF IS REAL. markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) == True — spec region byte-identical, so the prepatch variant is a legitimate control. scripts/lean_verify.sh on Solution.lean EXIT 0; appended `#print axioms correct_collectModulePages` -> "depends on axioms: [propext]" only, NO sorryAx. So the spec view I judged is the frozen, honestly-proved artifact.

SCOPE NOTE (not a leak at this gate). refinement.md and mapping.md DO name `singlehtml` and quote both gold guards verbatim, and both disclose the (i) co-change as an out-of-model boundary. These are auditor-facing documents, not the consumer-visible spec view: G-LEAK's `reads` is ('solution','relaxed_leakage_doc') and markers.spec_view is computed from Solution.lean alone, so this is documentation of a disclosed modeling boundary rather than solver-visible disclosure. Flagging it as a scope observation, not a finding.

CORE GATES CONFIRMED SOUND on the CURRENT digest f03af2618d72 (all stamped 2026-08-15T13:06-13:09): G-VERIFY pass (axioms clean, re-run by me), G-DIFF pass (prepatch fails; same_spec True, re-confirmed by me), G-GOLD pass, G-CONF pass 100580 checked / 0 disagreements / seed 8721 / excluded_builder_names EMPTY, G-MUT killed 2/2, G-HYGIENE pass, G-INTEGRITY pass (instance.json byte-identical), G-RESOLVE resolved with patch_equals_gold=True, G-AX skip (no consumed axiom), G-PBT SOUND 13 cases. NOTE FOR THE RECORD: G-PANEL/G-PANEL-1/-2/-3 and G-EQ are all stamped against the OLD digest a17b88363fb7 (08:11 and earlier) and are stale relative to the repaired spec; my verdict here is the fresh measurement of the leakage facet on f03af2618d72.

NOTHING IN THE BUNDLE ADDRESSED ME. leakage.reviewer_directed() over lean/refinement.md, lean/mapping.md, lean/Solution.lean, lean/meta.json and the sibling velvet/RELAXED_LEAKAGE.md all returned [] — no file instructs the panel how to record or which verdict is honest. Nothing to report on that axis.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
