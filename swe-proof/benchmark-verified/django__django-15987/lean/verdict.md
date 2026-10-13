# P2 adversarial audit — django__django-15987

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,8 +62,7 @@
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
     Option Component := Id.run do
   for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
-    if collides dirs c.defaultDir then
+    if dirs.any (fun d => !d.isObject && d.value == c.defaultDir) then
       return some c
   return none
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,7 @@
 
 -- impl-start
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
-    Option Component := Id.run do
-  for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
-    if collides dirs c.defaultDir then
-      return some c
-  return none
+    Option Component := none
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,7 @@
 
 -- impl-start
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
-    Option Component := Id.run do
-  for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
-    if collides dirs c.defaultDir then
-      return some c
-  return none
+    Option Component := comps.head?
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,11 @@
 -- impl-start
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
     Option Component := Id.run do
+  let mut res : Option Component := none
   for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
     if collides dirs c.defaultDir then
-      return some c
-  return none
+      res := some c
+  return res
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,8 @@
 
 -- impl-start
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
-    Option Component := Id.run do
-  for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
-    if collides dirs c.defaultDir then
-      return some c
-  return none
+    Option Component :=
+  (comps.drop 1).find? (fun c => collides dirs c.defaultDir)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,8 @@
 
 -- impl-start
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
-    Option Component := Id.run do
-  for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
-    if collides dirs c.defaultDir then
-      return some c
-  return none
+    Option Component :=
+  comps.find? (fun c => collides dirs c.label)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,8 @@
 
 -- impl-start
 def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
-    Option Component := Id.run do
-  for c in comps do
-    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
-    if collides dirs c.defaultDir then
-      return some c
-  return none
+    Option Component :=
+  comps.find? (fun c => dirs.any (fun d => d.isObject && d.value == c.defaultDir))
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
A configuration validator scans the set of installed application components.
Each component carries a *default* directory that belongs to that component
intrinsically. Separately, the user supplies a list of explicitly configured
directories; each configured entry has a textual location, and an entry may be
given either as a plain text location or as a structured location object.

The validator must reject a configuration in which any component's default
directory is *also* one of the explicitly configured directories — listing a
component's own default directory explicitly is disallowed. Two locations count
as the same directory when their textual forms coincide, regardless of whether a
configured entry was supplied as plain text or as a structured location object.

The result identifies the first offending component (in component-iteration
order) whose default directory collides with some configured directory, or
signals that no such collision exists. The behavior is stated abstractly as an
input→output relation; the implementation and its correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the modeled behavior is
-- spelled out with concrete operations (a textual-equality membership test and
-- a first-match scan over the components).
-- axioms-end

-- pure-start
/-- An explicitly configured directory entry: its textual location together with
a tag recording whether it was supplied as a structured location object (`true`)
or as a plain text location (`false`). `value` is the textual form in BOTH
cases. -/
structure ConfiguredDir where
  value : String
  isObject : Bool
deriving DecidableEq, Repr

/-- An installed application component: an identifying label and the default
directory intrinsic to that component. -/
structure Component where
  label : String
  defaultDir : String
deriving DecidableEq, Repr

/-- A configured directory collides with `target` when their textual forms
coincide — independent of how the configured entry was supplied. -/
def collides (dirs : List ConfiguredDir) (target : String) : Bool :=
  dirs.any (fun d => d.value == target)
-- pure-end

-- post-conditions-start
/-- The result is the first component (in iteration order) whose default
directory collides with some configured directory, or `none` if none collide. -/
def problem_spec_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component)
    (result : Option Component) : Prop :=
  result = comps.find? (fun c => collides dirs c.defaultDir)
-- post-conditions-end

-- impl-start
def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
    Option Component := Id.run do
  for c in comps do
    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
    if collides dirs c.defaultDir then
      return some c
  return none
-- impl-end

-- proof-start
theorem correct_fixtureDirs :
    ∀ (dirs : List ConfiguredDir) (comps : List Component),
      problem_spec_fixtureDirs dirs comps
        (implementation_fixtureDirs dirs comps) := by
  intro dirs comps
  unfold problem_spec_fixtureDirs implementation_fixtureDirs
  induction comps with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : collides dirs a.defaultDir = true
    · simp only [h, if_true, List.find?_cons]; rfl
    · simp only [h, List.find?_cons, Bool.false_eq_true, if_false, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-15987 (lean). Spec postcondition is an EXACT functional equality: problem_spec_fixtureDirs dirs comps result := result = comps.find? (fun c => collides dirs c.defaultDir), where collides = dirs.any (fun d => d.value == target). This pins the output uniquely up to extensionality, so any behaviorally-distinct impl is unprovable.

SAME-SPEC: verified True for pos_gold + all 7 attacks via swebench_unified.markers.same_spec (get_backend('lean').language). Note: _lean_spec_view collapses BOTH impl and proof regions to placeholders, so I was free to rewrite the proof for each attack; I used the gold induction proof for each.

### COMMANDS (each: `bash scripts/lean_verify.sh <file>`, run concurrently in 2 batches of 4):
- pos_gold.lean: EXIT=0 (verifies, no sorry). #print axioms correct_fixtureDirs (pos_axcheck.lean, EXIT=0) => 'correct_fixtureDirs' depends on axioms: [propext, Quot.sound] — CLEAN, no sorry/custom axioms.
- atk_1.lean (PREPATCH BUG: collision test only matches plain-text entries, `!d.isObject && d.value == c.defaultDir`, mirroring pre-patch `app_dir in fixture_dirs`): EXIT=1. Genuine goal mismatch (find? over the restricted predicate != find? over collides). => prepatch_reproduced=true.
- atk_2.lean (ungrounded: always none): EXIT=1, rewrite fails, ih none != find?.
- atk_3.lean (boundary: comps.head?): EXIT=1, head? != find?.
- atk_4.lean (control-flow-effect: no early return, records LAST colliding comp via mutable var): EXIT=1, goal mismatch.
- atk_5.lean (partial-domain / off-by-one: (comps.drop 1).find? ...): EXIT=1, drop 1 != full list.
- atk_6.lean (wrong field: collides dirs c.label instead of c.defaultDir): EXIT=1, label != defaultDir.
- atk_7.lean (inverted type tag: requires d.isObject && d.value == c.defaultDir): EXIT=1, restricted predicate != collides.

All 7 attack failures are CORRECTNESS goal-mismatch errors from Lean (List.find? LHS != spec RHS), NOT syntactic/malformed-file errors — confirmed by inspecting each .out. No same-spec wrong impl closed with a clean-axiom proof, so there is NO verifying candidate requiring a faithful-patch resolve run (patches={}). verify⇏correct NOT demonstrated.

refinement.md / mapping.md A-LEG AUDIT: bundle declares NO axioms (axioms region lines 24-28 are comment-only; axiom_check.py is a skip stub). Every refinement leg is tagged R or I with a concrete deep model (collides = String-form membership dirs.any (d.value == target); early-return scan = List.find?). No A-consumed / A-reference legs and no kind-3 undischarged axioms, so the A-leg correspondence obligation is vacuously satisfied. R/I legs are G-CONF's remit (differential fuzz, seed 20240823, str vs pathlib.Path entries). Model↔patch correspondence holds: the single changed predicate `app_dir in [str(d) for d in fixture_dirs]` maps faithfully to collides (str-coercion => isObject ignored), and first-match/early-return maps to find?/some c.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls attacked (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-field, inverted-tag, prepatch); none verifies; positive control verifies clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
A configuration validator scans the set of installed application components.
Each component carries a *default* directory that belongs to that component
intrinsically. Separately, the user supplies a list of explicitly configured
directories; each configured entry has a textual location, and an entry may be
given either as a plain text location or as a structured location object.

The validator must reject a configuration in which any component's default
directory is *also* one of the explicitly configured directories — listing a
component's own default directory explicitly is disallowed. Two locations count
as the same directory when their textual forms coincide, regardless of whether a
configured entry was supplied as plain text or as a structured location object.

The result identifies the first offending component (in component-iteration
order) whose default directory collides with some configured directory, or
signals that no such collision exists. The behavior is stated abstractly as an
input→output relation; the implementation and its correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the modeled behavior is
-- spelled out with concrete operations (a textual-equality membership test and
-- a first-match scan over the components).
-- axioms-end

-- pure-start
/-- An explicitly configured directory entry: its textual location together with
a tag recording whether it was supplied as a structured location object (`true`)
or as a plain text location (`false`). `value` is the textual form in BOTH
cases. -/
structure ConfiguredDir where
  value : String
  isObject : Bool
deriving DecidableEq, Repr

/-- An installed application component: an identifying label and the default
directory intrinsic to that component. -/
structure Component where
  label : String
  defaultDir : String
deriving DecidableEq, Repr

/-- A configured directory collides with `target` when their textual forms
coincide — independent of how the configured entry was supplied. -/
def collides (dirs : List ConfiguredDir) (target : String) : Bool :=
  dirs.any (fun d => d.value == target)
-- pure-end

-- post-conditions-start
/-- The result is the first component (in iteration order) whose default
directory collides with some configured directory, or `none` if none collide. -/
def problem_spec_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component)
    (result : Option Component) : Prop :=
  result = comps.find? (fun c => collides dirs c.defaultDir)
-- post-conditions-end

-- impl-start
def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
    Option Component := Id.run do
  for c in comps do
    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)
    if collides dirs c.defaultDir then
      return some c
  return none
-- impl-end

-- proof-start
theorem correct_fixtureDirs :
    ∀ (dirs : List ConfiguredDir) (comps : List Component),
      problem_spec_fixtureDirs dirs comps
        (implementation_fixtureDirs dirs comps) := by
  intro dirs comps
  unfold problem_spec_fixtureDirs implementation_fixtureDirs
  induction comps with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : collides dirs a.defaultDir = true
    · simp only [h, if_true, List.find?_cons]; rfl
    · simp only [h, List.find?_cons, Bool.false_eq_true, if_false, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-15987 (lean). Spec postcondition is an EXACT functional equality: problem_spec_fixtureDirs dirs comps result := result = comps.find? (fun c => collides dirs c.defaultDir), where collides = dirs.any (fun d => d.value == target). This pins the output uniquely up to extensionality, so any behaviorally-distinct impl is unprovable.

SAME-SPEC: verified True for pos_gold + all 7 attacks via swebench_unified.markers.same_spec (get_backend('lean').language). Note: _lean_spec_view collapses BOTH impl and proof regions to placeholders, so I was free to rewrite the proof for each attack; I used the gold induction proof for each.

### COMMANDS (each: `bash scripts/lean_verify.sh <file>`, run concurrently in 2 batches of 4):
- pos_gold.lean: EXIT=0 (verifies, no sorry). #print axioms correct_fixtureDirs (pos_axcheck.lean, EXIT=0) => 'correct_fixtureDirs' depends on axioms: [propext, Quot.sound] — CLEAN, no sorry/custom axioms.
- atk_1.lean (PREPATCH BUG: collision test only matches plain-text entries, `!d.isObject && d.value == c.defaultDir`, mirroring pre-patch `app_dir in fixture_dirs`): EXIT=1. Genuine goal mismatch (find? over the restricted predicate != find? over collides). => prepatch_reproduced=true.
- atk_2.lean (ungrounded: always none): EXIT=1, rewrite fails, ih none != find?.
- atk_3.lean (boundary: comps.head?): EXIT=1, head? != find?.
- atk_4.lean (control-flow-effect: no early return, records LAST colliding comp via mutable var): EXIT=1, goal mismatch.
- atk_5.lean (partial-domain / off-by-one: (comps.drop 1).find? ...): EXIT=1, drop 1 != full list.
- atk_6.lean (wrong field: collides dirs c.label instead of c.defaultDir): EXIT=1, label != defaultDir.
- atk_7.lean (inverted type tag: requires d.isObject && d.value == c.defaultDir): EXIT=1, restricted predicate != collides.

All 7 attack failures are CORRECTNESS goal-mismatch errors from Lean (List.find? LHS != spec RHS), NOT syntactic/malformed-file errors — confirmed by inspecting each .out. No same-spec wrong impl closed with a clean-axiom proof, so there is NO verifying candidate requiring a faithful-patch resolve run (patches={}). verify⇏correct NOT demonstrated.

refinement.md / mapping.md A-LEG AUDIT: bundle declares NO axioms (axioms region lines 24-28 are comment-only; axiom_check.py is a skip stub). Every refinement leg is tagged R or I with a concrete deep model (collides = String-form membership dirs.any (d.value == target); early-return scan = List.find?). No A-consumed / A-reference legs and no kind-3 undischarged axioms, so the A-leg correspondence obligation is vacuously satisfied. R/I legs are G-CONF's remit (differential fuzz, seed 20240823, str vs pathlib.Path entries). Model↔patch correspondence holds: the single changed predicate `app_dir in [str(d) for d in fixture_dirs]` maps faithfully to collides (str-coercion => isObject ignored), and first-match/early-return maps to find?/some c.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls attacked (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-field, inverted-tag, prepatch); none verifies; positive control verifies clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution, Solution_prepatch, lean backend) = True — spec region byte-identical. Solution.lean compiles clean (lean_verify exit 0, no sorry). #print axioms correct_fixtureDirs -> [propext, Quot.sound] only (no sorryAx; proof is real). Real callee at base_commit django/core/management/commands/loaddata.py:354-383, gold patch changes exactly `if app_dir in fixture_dirs:` -> `if app_dir in [str(d) for d in fixture_dirs]:`. Model: collides dirs t = dirs.any (d.value == t) with value=str(d), and result = comps.find? (collides ...). This faithfully captures string-coerced membership (str(d)) + first-match component (raised app_label). Verified real==model for: empty, plain-str collide, Path collide (the fix case, str-vs-Path same text detected correctly), str-hidden-behind-Path and vice versa. The str-vs-Path same-location cases are never set-duplicates, so the fix's discriminating frame is fully faithful. Spec is neither too strong nor drifting: it pins only the changed predicate's outcome, matching the real patched behavior on all in-frame inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage/gold-reconstruction review of the lean spec view for django__django-15987.

MECHANICAL: leakage.screen (lean flavor) passes with zero hard failures — no diff markers, no gold-patch changed line reproduced (the distinctive changed line `if app_dir in [str(d) for d in fixture_dirs]:` and its counterpart do not appear), no patched file path (loaddata.py) or dotted module path, no narration terms (bug/fix/patch/…), and the only distinctive patched symbol candidate is not echoed in any spec-view identifier or comment. Confirmed same_spec(Solution, Solution_prepatch)=True, so the spec region is byte-identical across the diff pair and no drift smuggles the fix. Meta G-LEAK=pass; relaxed_leakage unset; no RELAXED_LEAKAGE.md — strict judgment applies.

SEMANTIC: The public problem_statement ('Fixture dirs duplicates undetected if dir is Path instance … when FIXTURE_DIRS contains Path instances, the duplicate check in loaddata does not detect duplicates') already discloses the entire behavioral requirement: a collision/duplicate check exists, it must detect a directory supplied as a Path instance (structured object) as equal to a plain-text one, and the correct behavior catches it. The spec view (ConfiguredDir with value=textual form + isObject=plain-text-vs-structured-object tag; collides comparing on value regardless of the tag; problem_spec_fixtureDirs = first colliding component in iteration order, or none) encodes exactly this desired input→output relation — a legitimate SPEC derivable from the public task. Crucially, the gold edit MECHANISM (the `str(d)` list-comprehension coercion) never appears; it is folded into the abstract `collides` predicate. Impl and proof regions are elided. Nothing in the spec view reconstructs the gold edit beyond what problem_statement makes public.

VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
