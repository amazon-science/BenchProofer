# P2 adversarial audit — django__django-15916

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verify⇏correct break found. The spec `result = metaCallback` is TOTAL and RIGID (both machine-proved in rigidity.lean, exit 0): `spec_is_total` gives a witness at every input (non-vacuous), and `spec_is_rigid` proves any f satisfying the postcondition everywhere is POINTWISE EQUAL to the gold impl. So no verifying same-spec impl can differ observably in the model, and the only possible break vector is UNDER-MODELING of the patch hunks outside the impl region. I attacked that vector directly with 4 verifying echoes whose faithful patches deliberately vary the two un-modeled hunks (the `attrs.pop`/base-scan deletion and the `modelform_factory` top-level injection removal); ALL FOUR RESOLVED. The 8 wrong impls that model a genuinely different selection are each machine-REFUTED at a concrete witness. Discriminating witness (F2P `test_custom_callback_in_meta`): metaCallback=some 7, directHasCallback=false, directCallback=none, baseMetaCallback=none => spec demands `some 7`, prepatch resolution yields `none`.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,12 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1 (prepatch bug re-encode)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
     (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
+  -- PRE-PATCH resolution: a direct class attribute when present, else the first
+  -- base form's options block; the class's OWN options block is ignored.
+  let mut selected := baseMetaCallback.getD none
+  if directHasCallback then
+    selected := directCallback
   return selected
 -- impl-end
 
@@ -75,5 +79,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2 (partial-domain)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  -- PARTIAL DOMAIN: agrees with the spec exactly on directHasCallback = false;
+  -- when a direct top-level attribute is present it wins (the pre-patch pop).
+  if directHasCallback then directCallback else metaCallback
 -- impl-end
 
 -- proof-start
@@ -75,5 +76,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3 (boundary: none falls through to the base Meta)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  -- BOUNDARY: right whenever the own options block declares a callback; on the
+  -- `none` boundary it inherits the first base form's options-block callback.
+  match metaCallback with
+  | some c => some c
+  | none   => baseMetaCallback.getD none
 -- impl-end
 
 -- proof-start
@@ -75,5 +78,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4 (boundary: falsy-callback identity treated as absent)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  -- BOUNDARY on the callback identity itself: one particular callback id is
+  -- mistaken for "no callback" (e.g. a falsy-callable check, `if callback:`).
+  match metaCallback with
+  | some 0 => none
+  | x      => x
 -- impl-end
 
 -- proof-start
@@ -75,5 +78,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5 (base options block preferred over own)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  -- The first base form that declares an options-block callback wins outright;
+  -- the class's own options block is consulted only when no base declares one.
+  match baseMetaCallback with
+  | some v => v
+  | none   => metaCallback
 -- impl-end
 
 -- proof-start
@@ -75,5 +78,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,12 +56,19 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6 (control-flow-effect: legacy value still overrides)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
     (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
+  -- CONTROL-FLOW EFFECT: the fix selects the own options block, but the legacy
+  -- `attrs.pop`/base-scan value is still applied afterwards as an override
+  -- whenever it is not "no callback" (a half-applied patch: the pop kept for
+  -- its side effect but its VALUE still allowed to win).
   let mut selected := metaCallback
+  let popped := if directHasCallback then directCallback else baseMetaCallback.getD none
+  if popped ≠ none then
+    selected := popped
   return selected
 -- impl-end
 
@@ -75,5 +82,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7 (degenerate constant)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  -- Degenerate: never uses a callback at all.
+  none
 -- impl-end
 
 -- proof-start
@@ -75,5 +75,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD])
+    | decide
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,11 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 8 (echo: direct attribute observed then discarded)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
     (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
+  -- The direct class attribute is still observed (and its presence recorded),
+  -- but its value is DISCARDED: the selection is the own options block.
+  let mut _observed := directCallback
+  if directHasCallback then
+    _observed := directCallback
   let mut selected := metaCallback
   return selected
 -- impl-end
@@ -75,5 +80,12 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_resolveModelFormCallback
+             implementation_resolveModelFormCallback
+       simp only [Id.run, bind, pure, Id.instMonad]
+       first
+         | rfl
+         | simp_all [Option.getD])
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 9 (echo: direct options-block read, case-split spelling)
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  -- Read the own options block directly, by case analysis; the base scan and
+  -- the direct attribute are never consulted.
+  match metaCallback with
+  | none   => none
+  | some c => some c
 -- impl-end
 
 -- proof-start
@@ -75,5 +78,11 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  unfold problem_spec_resolveModelFormCallback implementation_resolveModelFormCallback
+  first
+    | rfl
+    | (simp_all [Id.run, Option.getD, Option.bind])
+    | (cases metaCallback <;> cases directHasCallback <;> cases directCallback <;>
+       cases baseMetaCallback <;> simp_all [Id.run, Option.getD, Option.bind])
+    | decide
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,18 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_resolveModelFormCallback
+-- ATTACK 10 (ungrounded-oracle echo): the impl does not select anything; it
+-- reads its answer back out of the SPEC via classical choice.
+noncomputable def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  open Classical in
+  if h : ∃ r, problem_spec_resolveModelFormCallback metaCallback directHasCallback
+                directCallback baseMetaCallback r then
+    h.choose
+  else
+    none
 -- impl-end
 
 -- proof-start
@@ -75,5 +80,10 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  have hex : ∃ r, problem_spec_resolveModelFormCallback metaCallback
+      directHasCallback directCallback baseMetaCallback r :=
+    ⟨metaCallback, rfl⟩
+  unfold implementation_resolveModelFormCallback
+  rw [dif_pos hex]
+  exact hex.choose_spec
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,13 +56,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 11 (partial-domain on the base-declaration boundary): correct except
+-- when a base form declares its options-block callback as "no callback"
+-- (`some none`), in which case the direct attribute is consulted.
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
-    (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
-  let mut selected := metaCallback
-  return selected
+    (baseMetaCallback : Option (Option Callback)) : Option Callback :=
+  match baseMetaCallback with
+  | some none => directCallback
+  | _         => metaCallback
 -- impl-end
 
 -- proof-start
@@ -75,5 +78,9 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_resolveModelFormCallback
+             implementation_resolveModelFormCallback
+       cases baseMetaCallback <;> simp_all)
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -56,11 +56,20 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 12 (control-flow-effect echo / maximal under-modeling probe): the
+-- ENTIRE legacy resolution is still computed (base scan + direct attribute),
+-- but its result is dead: the selection is the own options block. The faithful
+-- refinement therefore RETAINS every hunk gold deleted (the `for b in bases`
+-- scan, the `attrs.pop`, and the factory's top-level injection) and changes
+-- ONLY the value handed to the field builder.
 def implementation_resolveModelFormCallback
     (metaCallback : Option Callback) (directHasCallback : Bool)
     (directCallback : Option Callback)
     (baseMetaCallback : Option (Option Callback)) : Option Callback := Id.run do
-  -- the constructed class draws its callback from its own options block
+  let mut legacy := baseMetaCallback.getD none
+  if directHasCallback then
+    legacy := directCallback
+  let _dead := legacy
   let mut selected := metaCallback
   return selected
 -- impl-end
@@ -75,5 +84,12 @@
         (implementation_resolveModelFormCallback metaCallback directHasCallback
           directCallback baseMetaCallback) := by
   intro metaCallback directHasCallback directCallback baseMetaCallback
-  rfl
+  first
+    | rfl
+    | (unfold problem_spec_resolveModelFormCallback
+             implementation_resolveModelFormCallback
+       simp only [Id.run, bind, pure, Id.instMonad, Option.getD]
+       first
+         | rfl
+         | (cases directHasCallback <;> simp_all))
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** all 12 attacks + pos_control byte-identical spec via swebench_unified.markers.same_spec(..., 'lean') => True (verified twice; final sweep 'all same_spec True'). Only the impl+proof regions edited.

**POSITIVE CONTROL:** pos_control.lean (gold impl verbatim) `bash scripts/lean_verify.sh <f>` => EXIT 0; `#print axioms correct_resolveModelFormCallback` (ax_pos_control.lean, exit 0) => "does not depend on any axioms".

**PREPATCH REPRODUCED:** bundle Solution_prepatch.lean copied to prepatch_check.lean => lean_verify EXIT 1 (gold `rfl` fails against the buggy impl; G-DIFF confirmed). Re-encoded independently as atk_1.

=== A. WRONG IMPLS -- SPEC REJECTS (lean_verify EXIT 1), each with a machine-checked disproof witness (dis_atk_N.lean, all EXIT 0, proving genuine spec refutation rather than weak-tactic artifact) ===
All used the same escalating tactic ladder (rfl | unfold+simp | full case-split | decide), so exit 1 is not tactic weakness.
 atk_1 (prepatch bug re-encode: base scan + direct override) EXIT 1; dis_atk_1 EXIT 0 @ (some 7,false,none,none)
 atk_2 (partial-domain: correct iff directHasCallback=false) EXIT 1; dis_atk_2 EXIT 0 @ (some 7,true,none,none)
 atk_3 (boundary: own `none` falls through to base Meta) EXIT 1; dis_atk_3 EXIT 0 @ (none,false,none,some (some 5))
 atk_4 (boundary on callback IDENTITY: id 0 read as absent, the `if callback:` falsy bug) EXIT 1; dis_atk_4 EXIT 0 @ (some 0,false,none,none)
 atk_5 (base options block preferred over own) EXIT 1; dis_atk_5 EXIT 0 @ (some 7,false,none,some (some 5))
 atk_6 (control-flow-effect: legacy pop/base VALUE still overrides when non-none) EXIT 1; dis_atk_6 EXIT 0 @ (none,true,some 5,none)
 atk_7 (degenerate constant `none`) EXIT 1; dis_atk_7 EXIT 0 @ (some 7,false,none,none)
 atk_11 (partial-domain on the base-DECLARATION boundary: base declaring `some none` diverts to directCallback) EXIT 1; dis_atk_11 EXIT 0 @ (some 7,false,none,some none)

=== B. VERIFYING ECHOES -- clean axioms, faithful patch MATERIALIZED and RESOLVED (protocol step 2, EXECUTED) ===
STANDARD_AXIOMS for this backend = ('propext','Classical.choice','Quot.sound'), so all four below are clean per gates/`_lean_axioms`.check_proof_axioms.
Each patch checked with `git apply --check` in a base_commit worktree (wtchk @ 88e67a54b7ed0210c11523a337b498aadb2f5187) => APPLIES.
Command: python resolve_one.py <n> <patch> -> swebench_unified.harness.run_resolve('django__django-15916', <diff>, timeout=1800).

atk_8 -- echo: direct class attribute still OBSERVED (pop retained for side effect) then value DISCARDED. lean_verify EXIT 0; axioms=[propext]. FAITHFUL PATCH patch_atk_8.diff DELIBERATELY OMITS the modelform_factory hunk and retains a bare `attrs.pop("formfield_callback", None)` -- i.e. it probes exactly the hunk refinement.md calls "subsumed". RESOLVE => completed=true, resolved=TRUE, attempts=3, flaky=true, note='resolved on attempt 3/3'. atk_9 -- echo: options block read DIRECTLY via `getattr(new_class.Meta, ...)`, no ModelFormOptions field, base scan+pop fully deleted, factory injection LEFT IN PLACE. lean_verify EXIT 0; axioms=[propext]. patch_atk_9.diff.

RESOLVE => completed=true, resolved=TRUE, attempts=3, flaky=true, note='resolved on attempt 3/3'. atk_10 -- UNGROUNDED-ORACLE ECHO (the named class): `noncomputable` impl computes nothing and extracts its answer from the postcondition via Classical.choice (`h.choose`). lean_verify EXIT 0; axioms=[propext, Classical.choice, Quot.sound] == STANDARD_AXIOMS exactly, so CLEAN and in scope. Because the postcondition pins the result UNIQUELY, h.choose collapses to metaCallback, so its only faithful materialization is the gold selection (patch_atk_10.diff, all three hunks derived independently).

RESOLVE => completed=true, resolved=TRUE, attempts=1, flaky=false, note='resolved'. atk_12 -- MAXIMAL UNDER-MODELING PROBE / control-flow-effect echo: the ENTIRE legacy resolution (base scan + direct attribute) is still computed but dead. lean_verify EXIT 0; axioms=[propext]. patch_atk_12.diff RETAINS EVERY HUNK GOLD DELETED (the `for b in bases` scan, the `attrs.pop`, and modelform_factory's top-level `formfield_callback` injection) and changes ONLY the value handed to fields_for_model. This is the strictest test of the framing-out claim. RESOLVE => completed=true, resolved=TRUE, attempts=1, flaky=false, note='resolved'.

Note on flakiness: atk_8/atk_9 resolved on attempt 3/3 (harness retry policy = resolved-on-any-attempt); atk_10/atk_12, materially the same selection, resolved on attempt 1 with flaky=false, so the earlier non-completions are host/network noise, not a correctness signal.

#### C. refinement.md AUDIT (A-legs / model-patch correspondence)
Leg tags: row 1 = R (`let mut selected := metaCallback` <-> `opts.formfield_callback` fed to fields_for_model), row 2 = I (`return selected` <-> the value fields_for_model receives). No A-consumed and no A-reference row, hence NO KIND-3 leg -- the required partition (R / A-consumed / A-reference / I) is respected. Corroborated mechanically: `grep -cE '^\s*(axiom|opaque)\s' Solution.lean` => 0, and meta.json declares axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a consistent skip stub.

Since there are no A-legs, the A-leg correspondence obligation is vacuous BY CONSTRUCTION, not by assertion -- the impl consumes no callee contract and `fields_for_model`/`Field.formfield` are genuinely unchanged by patch.diff (confirmed: patch.diff touches only ModelFormOptions.`__init__`, ModelFormMetaclass.`__new__`, and modelform_factory).

I did not take that on trust -- I validated the R-leg bijection CONCRETELY against the real repo (corr_probe.py, 24 real Django model-form classes spanning metaCallback x {absent,None,cb} direct attribute x {no base, base w/o cb, base with None, base with cb}, reading back which callback actually built base_fields): gold-patched tree (wtG)  => 24 probed, 0 MISMATCHES vs the Lean model `result = metaCallback`. prepatch tree (wt)       => 24 probed, 16 MISMATCHES -- so the probe genuinely discriminates and is not vacuously passing.

Among the prepatch mismatches, (metaCallback=1, direct=absent, base=nobase) got None vs model 1 is precisely F2P test_custom_callback_in_meta, and (metaCallback=None, direct=None, base=base2) got None vs model 2 is precisely F2P test_custom_callback_from_base_form_meta. Both F2P cases are therefore reproduced by the model, confirming the mapping.md claim that metaCallback is the OWN options block resolved through options-block inheritance.

#### D. Why SOUND
12 same-spec attacks run (>=5 required), covering every class the protocol names: prepatch bug (atk_1), partial-domain (atk_2, atk_11), boundary (atk_3, atk_4), control-flow-effect (atk_6, atk_12), ungrounded-oracle echo (atk_10), plus base-preference (atk_5) and degenerate (atk_7). 8 are machine-refuted by the spec at explicit witnesses; 4 verify with clean axioms and EVERY ONE had its faithful refined patch materialized, `git apply --check`ed at base_commit, and EXECUTED through the official harness -- all 4 RESOLVED. No impl with a closing clean-axiom proof has a non-resolving faithful patch, so verify=>correct is not falsified here.

The rigidity theorem explains why this is not luck: the postcondition is a total function of the inputs with no free component, so the admissible set is a single point and the spec cannot admit a behaviorally wrong refinement. The residual risk for such a projection spec is under-modeling, and atk_12 (retaining all three deleted hunks) plus atk_8 (omitting the factory hunk) bracket that risk from both sides and still resolve -- the un-modeled hunks are dead code with respect to the F2P/P2P lanes, which is exactly what refinement.md claims when it calls the factory change "subsumed". All evidence is machine-checked; no step was left speculative.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verify⇏correct break found. The spec `result = metaCallback` is TOTAL and RIGID (both machine-proved in rigidity.lean, exit 0): `spec_is_total` gives a witness at every input (non-vacuous), and `spec_is_rigid` proves any f satisfying the postcondition everywhere is POINTWISE EQUAL to the gold impl. So no verifying same-spec impl can differ observably in the model, and the only possible break vector is UNDER-MODELING of the patch hunks outside the impl region. I attacked that vector directly with 4 verifying echoes whose faithful patches deliberately vary the two un-modeled hunks (the `attrs.pop`/base-scan deletion and the `modelform_factory` top-level injection removal); ALL FOUR RESOLVED. The 8 wrong impls that model a genuinely different selection are each machine-REFUTED at a concrete witness. Discriminating witness (F2P `test_custom_callback_in_meta`): metaCallback=some 7, directHasCallback=false, directCallback=none, baseMetaCallback=none => spec demands `some 7`, prepatch resolution yields `none`.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

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

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** all 12 attacks + pos_control byte-identical spec via swebench_unified.markers.same_spec(..., 'lean') => True (verified twice; final sweep 'all same_spec True'). Only the impl+proof regions edited.

**POSITIVE CONTROL:** pos_control.lean (gold impl verbatim) `bash scripts/lean_verify.sh <f>` => EXIT 0; `#print axioms correct_resolveModelFormCallback` (ax_pos_control.lean, exit 0) => "does not depend on any axioms".

**PREPATCH REPRODUCED:** bundle Solution_prepatch.lean copied to prepatch_check.lean => lean_verify EXIT 1 (gold `rfl` fails against the buggy impl; G-DIFF confirmed). Re-encoded independently as atk_1.

=== A. WRONG IMPLS -- SPEC REJECTS (lean_verify EXIT 1), each with a machine-checked disproof witness (dis_atk_N.lean, all EXIT 0, proving genuine spec refutation rather than weak-tactic artifact) ===
All used the same escalating tactic ladder (rfl | unfold+simp | full case-split | decide), so exit 1 is not tactic weakness.
 atk_1 (prepatch bug re-encode: base scan + direct override) EXIT 1; dis_atk_1 EXIT 0 @ (some 7,false,none,none)
 atk_2 (partial-domain: correct iff directHasCallback=false) EXIT 1; dis_atk_2 EXIT 0 @ (some 7,true,none,none)
 atk_3 (boundary: own `none` falls through to base Meta) EXIT 1; dis_atk_3 EXIT 0 @ (none,false,none,some (some 5))
 atk_4 (boundary on callback IDENTITY: id 0 read as absent, the `if callback:` falsy bug) EXIT 1; dis_atk_4 EXIT 0 @ (some 0,false,none,none)
 atk_5 (base options block preferred over own) EXIT 1; dis_atk_5 EXIT 0 @ (some 7,false,none,some (some 5))
 atk_6 (control-flow-effect: legacy pop/base VALUE still overrides when non-none) EXIT 1; dis_atk_6 EXIT 0 @ (none,true,some 5,none)
 atk_7 (degenerate constant `none`) EXIT 1; dis_atk_7 EXIT 0 @ (some 7,false,none,none)
 atk_11 (partial-domain on the base-DECLARATION boundary: base declaring `some none` diverts to directCallback) EXIT 1; dis_atk_11 EXIT 0 @ (some 7,false,none,some none)

=== B. VERIFYING ECHOES -- clean axioms, faithful patch MATERIALIZED and RESOLVED (protocol step 2, EXECUTED) ===
STANDARD_AXIOMS for this backend = ('propext','Classical.choice','Quot.sound'), so all four below are clean per gates/`_lean_axioms`.check_proof_axioms.
Each patch checked with `git apply --check` in a base_commit worktree (wtchk @ 88e67a54b7ed0210c11523a337b498aadb2f5187) => APPLIES.
Command: python resolve_one.py <n> <patch> -> swebench_unified.harness.run_resolve('django__django-15916', <diff>, timeout=1800).

atk_8 -- echo: direct class attribute still OBSERVED (pop retained for side effect) then value DISCARDED. lean_verify EXIT 0; axioms=[propext]. FAITHFUL PATCH patch_atk_8.diff DELIBERATELY OMITS the modelform_factory hunk and retains a bare `attrs.pop("formfield_callback", None)` -- i.e. it probes exactly the hunk refinement.md calls "subsumed". RESOLVE => completed=true, resolved=TRUE, attempts=3, flaky=true, note='resolved on attempt 3/3'. atk_9 -- echo: options block read DIRECTLY via `getattr(new_class.Meta, ...)`, no ModelFormOptions field, base scan+pop fully deleted, factory injection LEFT IN PLACE. lean_verify EXIT 0; axioms=[propext]. patch_atk_9.diff.

RESOLVE => completed=true, resolved=TRUE, attempts=3, flaky=true, note='resolved on attempt 3/3'. atk_10 -- UNGROUNDED-ORACLE ECHO (the named class): `noncomputable` impl computes nothing and extracts its answer from the postcondition via Classical.choice (`h.choose`). lean_verify EXIT 0; axioms=[propext, Classical.choice, Quot.sound] == STANDARD_AXIOMS exactly, so CLEAN and in scope. Because the postcondition pins the result UNIQUELY, h.choose collapses to metaCallback, so its only faithful materialization is the gold selection (patch_atk_10.diff, all three hunks derived independently).

RESOLVE => completed=true, resolved=TRUE, attempts=1, flaky=false, note='resolved'. atk_12 -- MAXIMAL UNDER-MODELING PROBE / control-flow-effect echo: the ENTIRE legacy resolution (base scan + direct attribute) is still computed but dead. lean_verify EXIT 0; axioms=[propext]. patch_atk_12.diff RETAINS EVERY HUNK GOLD DELETED (the `for b in bases` scan, the `attrs.pop`, and modelform_factory's top-level `formfield_callback` injection) and changes ONLY the value handed to fields_for_model. This is the strictest test of the framing-out claim. RESOLVE => completed=true, resolved=TRUE, attempts=1, flaky=false, note='resolved'.

Note on flakiness: atk_8/atk_9 resolved on attempt 3/3 (harness retry policy = resolved-on-any-attempt); atk_10/atk_12, materially the same selection, resolved on attempt 1 with flaky=false, so the earlier non-completions are host/network noise, not a correctness signal.

#### C. refinement.md AUDIT (A-legs / model-patch correspondence)
Leg tags: row 1 = R (`let mut selected := metaCallback` <-> `opts.formfield_callback` fed to fields_for_model), row 2 = I (`return selected` <-> the value fields_for_model receives). No A-consumed and no A-reference row, hence NO KIND-3 leg -- the required partition (R / A-consumed / A-reference / I) is respected. Corroborated mechanically: `grep -cE '^\s*(axiom|opaque)\s' Solution.lean` => 0, and meta.json declares axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a consistent skip stub.

Since there are no A-legs, the A-leg correspondence obligation is vacuous BY CONSTRUCTION, not by assertion -- the impl consumes no callee contract and `fields_for_model`/`Field.formfield` are genuinely unchanged by patch.diff (confirmed: patch.diff touches only ModelFormOptions.`__init__`, ModelFormMetaclass.`__new__`, and modelform_factory).

I did not take that on trust -- I validated the R-leg bijection CONCRETELY against the real repo (corr_probe.py, 24 real Django model-form classes spanning metaCallback x {absent,None,cb} direct attribute x {no base, base w/o cb, base with None, base with cb}, reading back which callback actually built base_fields): gold-patched tree (wtG)  => 24 probed, 0 MISMATCHES vs the Lean model `result = metaCallback`. prepatch tree (wt)       => 24 probed, 16 MISMATCHES -- so the probe genuinely discriminates and is not vacuously passing.

Among the prepatch mismatches, (metaCallback=1, direct=absent, base=nobase) got None vs model 1 is precisely F2P test_custom_callback_in_meta, and (metaCallback=None, direct=None, base=base2) got None vs model 2 is precisely F2P test_custom_callback_from_base_form_meta. Both F2P cases are therefore reproduced by the model, confirming the mapping.md claim that metaCallback is the OWN options block resolved through options-block inheritance.

#### D. Why SOUND
12 same-spec attacks run (>=5 required), covering every class the protocol names: prepatch bug (atk_1), partial-domain (atk_2, atk_11), boundary (atk_3, atk_4), control-flow-effect (atk_6, atk_12), ungrounded-oracle echo (atk_10), plus base-preference (atk_5) and degenerate (atk_7). 8 are machine-refuted by the spec at explicit witnesses; 4 verify with clean axioms and EVERY ONE had its faithful refined patch materialized, `git apply --check`ed at base_commit, and EXECUTED through the official harness -- all 4 RESOLVED. No impl with a closing clean-axiom proof has a non-resolving faithful patch, so verify=>correct is not falsified here.

The rigidity theorem explains why this is not luck: the postcondition is a total function of the inputs with no free component, so the admissible set is a single point and the spec cannot admit a behaviorally wrong refinement. The residual risk for such a projection spec is under-modeling, and atk_12 (retaining all three deleted hunks) plus atk_8 (omitting the factory hunk) bracket that risk from both sides and still resolve -- the un-modeled hunks are dead code with respect to the F2P/P2P lanes, which is exactly what refinement.md claims when it calls the factory change "subsumed". All evidence is machine-checked; no step was left speculative.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK ATTACK on django__django-15916 / resolveModelFormCallback. Spec: problem_spec_resolveModelFormCallback metaCallback directHasCallback directCallback baseMetaCallback result := (result = metaCallback). No diverging input found; spec matches post-patch repo behavior on every input probed.

**REFERENCE DISCIPLINE.** Per instructions the modeled function's reference is the base_commit worktree with patch.diff APPLIED. I built two worktrees off 88e67a54b7ed0210c11523a337b498aadb2f5187 from the upstream repository: (base) and  (patch.diff applied, git apply clean). All faithfulness judgements are against the POST-patch tree; the base tree is used only as a sensitivity control. I did NOT report the patch delta as drift.

PROVENANCE CHECK (important). `import django` can resolve here to a stale Django 3.2, which is what broke runtests.py with ImportError get_max_test_processes. So every harness asserts django.`__file__`.startswith(<worktree>) before drawing any conclusion, and confirms models file = models.py. Every measurement below is against the intended tree.

**MECHANIZED CHECKS.** (1) scripts/lean_verify.sh Solution.lean -> exit 0, only unusedVariables warnings on the three deliberately-framed-out args. (2) #print axioms on implementation_resolveModelFormCallback, correct_resolveModelFormCallback, problem_spec_resolveModelFormCallback -> all three 'does not depend on any axioms' => no sorryAx, proof is genuine, and meta.json axioms=[] / deep_model_references=[] is consistent with the all-R/I refinement (no callee contract to be unfaithful about). (3) Spec region integrity: swebench_unified.markers.spec_signature(Solution.lean, lean backend) computed; spec_view contains exactly the docstring + axioms + pure + post-conditions with impl/proof elided; same_spec self-check True. (4) G-DIFF control: Solution_prepatch.lean fails to verify (exit 1) with the goal reducing to the Id.run selection != metaCallback, so the spec does discriminate the buggy resolution.

EMPIRICAL DIFFERENTIAL (the real attack). I instrumented fields_for_model in the post-patch tree (patching both the module attr and ModelFormMetaclass.`__new__`.`__globals__`) to capture the callback VALUE the metaclass actually passes, i.e. exactly the modeled output. Two distinct callbacks with distinct identities (A/B) map to distinct Nat ids per mapping.md's type bijection; absence maps to none. Sweep: 4 base-Meta states x 4 own-Meta states x 4 direct-top-level-attr states (absent / None / A / B) = 64 cases, comparing real captured callback against the spec prediction metaCallback = getattr(ChildMeta,'formfield_callback',None). RESULT: 64/64 agree, 0 disagreements.

Adversarial edges, all 10 AGREE: E1 subclass with NO own inner Meta (Meta resolves via MRO to base's, cb=A) -> real A = metaCallback A; E2 no own Meta + direct top-level attr B, the exact shape the pre-patch attrs.pop would let win -> real A, spec A (direct attr correctly framed out); E3 own Meta sets formfield_callback=None over a base with A -> real None = spec None (confirms the docstring clause 'when the options block declares no callback the result is no callback, even if a base would otherwise supply one'); E4/E4b modelform_factory(model=Person, form=BaseF) and a further subclass of it -> A (the F2P test_custom_callback_from_base_form_meta shape); E5 factory with explicit formfield_callback=B -> B; E6 factory with formfield_callback=None over base A -> A (factory no longer clobbers, matches removal of the injected top-level None); E7 three-level deep Meta MRO inheritance -> A; E8 multiple bases where the FIRST base's Meta lacks the attr and the SECOND has it, the exact shape the pre-patch `for b in bases` scan would resolve differently -> real None = spec None; E10 callback stored as a plain function rather than staticmethod (descriptor-binding trap) -> A.

SENSITIVITY CONTROL (proves the harness can see drift). The identical sweep on the BASE tree produces many mismatches (e.g. base_none/meta_A/absent: metaCallback=1 but real=None; base_none/meta_B/direct_A: metaCallback=2 but real=1; absent/meta_B/direct_A: spec 2 vs real 1). So the harness is not vacuously agreeing — it detects precisely the pre-patch attrs.pop/base-scan resolution, and those divergences are the patch delta, correctly NOT reported as unfaithfulness.

**F2P/P2P CONFIRMATION.** Applied instance.json test_patch to the post-patch tree and ran model_forms.tests.FormFieldCallbackTests: Ran 9 tests, OK — including both F2P (test_custom_callback_in_meta, test_custom_callback_from_base_form_meta) and the P2P siblings test_bad_callback, test_inherit_after_custom_callback, test_factory_with_widget_argument, and both Regression #19733 cases. So result = metaCallback is consistent with the full upstream expectation set, not just the two new tests.

**SPEC-TOO-STRONG ANALYSIS.** The spec is a total function of its inputs (result fully pinned, nothing left free), which is the strongest possible shape — so the faithfulness risk is real and I probed it directly. It is nonetheless sound because post-patch the selection is literally the projection opts.formfield_callback = getattr(Meta,'formfield_callback',None): there is no residual dependence on directHasCallback/directCallback (the attrs.pop is deleted outright, so a top-level formfield_callback attribute is now inert for selection — E2 confirms) or on baseMetaCallback (the `for b in bases` scan is deleted; base influence survives only THROUGH Meta inheritance, which is already folded into metaCallback per the mapping's 'resolved via the inner-Meta MRO' binding — E1/E7/E8 confirm).

Framing those two inputs out is therefore accurate, not over-strong. Domain boundary noted and not a defect: when Meta has no model, or bases == (BaseModelForm,), the metaclass returns before fields_for_model and no selection occurs (my E9 probe: no call recorded) — the modeled function simply has no output on that input, so it lies outside the modeled domain rather than contradicting the spec. Other formfield_callback sites remaining post-patch (fields_for_model's own param at :140/:223-228, modelform_factory's staticmethod store at :626-627, modelformset_factory :1040, inlineformset_factory :1299) are all either the unchanged downstream consumer or pass-throughs that funnel into Meta.formfield_callback, and none of them re-introduce a competing selection path.

**CONCLUSION:** no input on which the modeled function disagrees with the real post-patch callee. Verdict FAITHFUL. Weakest point, disclosed: `Callback := Nat` abstracts callbacks to identities, so any hypothetical post-patch behavior that depended on a callback's *behavior* rather than its identity would be invisible to this model; the patch changes only which value is selected and never invokes it, so the abstraction is adequate here.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASURED, not inherited. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (walked all keys; only gates/G-LEAK matched /leak/i) and no RELAXED_LEAKAGE.md exists (find -iname '*RELAX*' -o -iname '*leak*' over the instance dir returned nothing). So this is a straight leakage judgement, no inherited disposition to re-derive. No file in the bundle addressed me, instructed me how to record, or asserted which verdict was honest — Solution.lean/refinement.md/mapping.md grepped for attacker|panel|reviewer|you should|do not report|honest verdict|submit|NO-LEAKAGE, zero hits.

### What I ran
1. Spec view identity: computed markers.spec_view(Solution.lean, lean.language) myself; sha256 = 953626959cc7a810fc6c99ee963deabc3e7d021876a47146298597e3acb2933f, byte-identical to meta.json region_hashes.spec_view. markers.same_spec(Solution.lean, Solution_prepatch.lean, T) = True, so the solver-visible spec is identical across gold and prepatch and the discriminator lives entirely in the elided impl. Confirmed impl and proof regions are actually elided in the view ('implementation elided' / 'proof elided') — the prepatch's 'pre-patch (buggy) skeleton' narration is inside impl-start, hence NOT in the spec view.
2. Mechanical screen: leakage.screen(Solution.lean, T, gold_patch, problem_statement, test_patch) => LeakageReport(hard_failures=[], warnings=[]). Independently reproduces meta's G-LEAK pass rather than trusting it.
3. Core gates I lean on, re-run not inherited: scripts/lean_verify.sh Solution.lean => exit 0 (G-GOLD); Solution_prepatch.lean => exit 1, failing exactly on `(... __do_jp selected y).run = metaCallback` (G-DIFF sound — the removed clause is load-bearing). Appended `#print axioms correct_resolveModelFormCallback` => "does not depend on any axioms", so no sorryAx; the proof is real, not fake.
4. Symbol-level leak test: extracted every identifier (>=4 chars) from the gold patch's changed +/- lines and case-insensitively searched the spec view. Only hits are 'Meta' and 'None' (substrings of 'metaCallback'/'none', and both already in problem_statement), plus 'options' and 'self' as ordinary English ('options block', 'itself'). NOTHING names django/forms/models.py, ModelFormOptions, ModelFormMetaclass, fields_for_model, opts.formfield_callback, attrs.pop, or the `for b in bases` scan. No diff markers, no file/dotted-module path, no reproduced patch line, no bug/fix/previously narration — docstrings state desired behavior only.

FACET RE-CONFIRMED (the only judgement call here): the spec view enumerates three candidate sources (metaCallback, directCallback/directHasCallback, baseMetaCallback) and then frames two of them out, pinning result = metaCallback. I checked each against the PUBLIC problem_statement, not hints_text:
  * own-Meta callback is authoritative — the title is literally 'Allow ModelForm meta to specify formfield_callback', and the statement says 'the expected behavior would be that the FactoryForm uses the formfield_callback specified in the Meta attribute of MyForm'. Fully public, and it IS the answer.
  * a direct top-level class attribute exists as a candidate — the statement's worked example declares `formfield_callback = all_required` in MyForm's class body, above `class Meta`. Public.
  * a base form's Meta callback exists as a candidate — 'the class uses no callback instead of the formfield_callback of the base form provided'. Public.
So the input alphabet is exactly the three places the public example exhibits, and the selected answer is the one the public statement demands. The framing-out clause ('the result does not depend on ... even if a direct attribute or a base form would otherwise supply one') is functional completeness — any total spec must say what result is when metaCallback = none — not edit localization. It does not tell the solver WHERE to cut; it restates the public requirement that Meta govern. I also confirmed the clause is TRUE of the real post-patch code (post-patch `__new__` drops attrs.pop entirely and passes opts.formfield_callback), so it is faithful framing rather than an artifact that would double as a hint.

**PRIVATE-ARTIFACT CHECK:** refinement.md and mapping.md do quote the gold verbatim (`self.formfield_callback = getattr(options, ...)`, `form_class_attrs = {"Meta": Meta}`, file:line bindings). That would be flagrant leakage IF solver-visible, so I checked the consumer rather than assuming: eval/adapter.py exposes ONLY spec_view(model_src) to the solver (with hard guards refusing to expose an unelided impl/proof), and eval/audit.py's private-bundle regex explicitly lists /refinement\.md, /mapping\.md, /verdict\.md, Solution_prepatch as reads to flag. They are bundle-internal audit artifacts, outside the screened spec view. Confirmed non-leaking on that basis.

**CONCLUSION:** nothing in the spec view exceeds the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
