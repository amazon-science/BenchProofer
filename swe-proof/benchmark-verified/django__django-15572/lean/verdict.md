# P2 adversarial audit — django__django-15572

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl closes, so there is no closing-proof patch to run. Correspondence sanity resolves (executed under the official harness): the GOLD patch (benchmark-verified/django__django-15572/patch.diff) RESOLVES (run_id sbu-audit-gold-15572: Instances resolved: 1, ✓=1); the no-fix EMPTY patch (faithful patch of the 'don't filter empties' prepatch/unfiltered impl) does NOT resolve (run_id sbu-audit-empty-15572: empty patch, resolved 0). This confirms the FAIL_TO_PASS test test_template_dirs_ignore_empty_path is exactly the empty-dir discriminator the spec's `d ≠ ""` filter encodes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,8 +45,7 @@
     (dirs loaderDirs : List String) : List String := Id.run do
   let mut items : List String := []
   for dir in dirs do
-    if dir ≠ "" then
-      items := items ++ [resolveDir dir]
+    items := items ++ [resolveDir dir]
   for directory in loaderDirs do
     if directory ≠ "" ∧ isFrameworkPath directory = false then
       items := items ++ [resolveDir directory]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
     if dir ≠ "" then
       items := items ++ [resolveDir dir]
   for directory in loaderDirs do
-    if directory ≠ "" ∧ isFrameworkPath directory = false then
+    if isFrameworkPath directory = false then
       items := items ++ [resolveDir directory]
   return items
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
     if dir ≠ "" then
       items := items ++ [resolveDir dir]
   for directory in loaderDirs do
-    if directory ≠ "" ∧ isFrameworkPath directory = false then
+    if directory ≠ "" then
       items := items ++ [resolveDir directory]
   return items
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
     (dirs loaderDirs : List String) : List String := Id.run do
   let mut items : List String := []
   for dir in dirs do
-    if dir ≠ "" then
+    if dir = "" then
       items := items ++ [resolveDir dir]
   for directory in loaderDirs do
     if directory ≠ "" ∧ isFrameworkPath directory = false then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   let mut items : List String := []
   for dir in dirs do
     if dir ≠ "" then
-      items := items ++ [resolveDir dir]
+      items := [resolveDir dir]
   for directory in loaderDirs do
     if directory ≠ "" ∧ isFrameworkPath directory = false then
       items := items ++ [resolveDir directory]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,6 @@
   for dir in dirs do
     if dir ≠ "" then
       items := items ++ [resolveDir dir]
-  for directory in loaderDirs do
-    if directory ≠ "" ∧ isFrameworkPath directory = false then
-      items := items ++ [resolveDir directory]
   return items
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
     (dirs loaderDirs : List String) : List String := Id.run do
   let mut items : List String := []
   for dir in dirs do
-    if dir ≠ "" then
+    if dir ≠ "" ∧ isFrameworkPath dir = false then
       items := items ++ [resolveDir dir]
   for directory in loaderDirs do
     if directory ≠ "" ∧ isFrameworkPath directory = false then
```

Attack 8 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,10 +45,9 @@
     (dirs loaderDirs : List String) : List String := Id.run do
   let mut items : List String := []
   for dir in dirs do
-    if dir ≠ "" then
-      items := items ++ [resolveDir dir]
+    items := items ++ [resolveDir dir]
   for directory in loaderDirs do
-    if directory ≠ "" ∧ isFrameworkPath directory = false then
+    if isFrameworkPath directory = false then
       items := items ++ [resolveDir directory]
   return items
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collect the set of directory paths that the template watcher should observe.

Two sources contribute directory entries: a list of configured directories, and
a list of loader-provided directories. Each entry is normalized to an absolute
path. Loader entries that point inside the framework's own tree are excluded.
A directory entry that is empty contributes nothing. The collected paths form a
set (membership only; order and repetition are irrelevant).
-/

-- axioms-start
-- Two unchanged path-handling callees, modeled as universally-quantified
-- parameters (the contract holds for ANY such function, so the proof consumes
-- no property of either):
--   * `resolveDir`      : normalize a directory entry to an absolute path.
--   * `isFrameworkPath` : true when a path lies inside the framework's own tree.
-- No `_prop` axiom is required (both callees are passthrough parameters).
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- A normalized path `p` belongs to the collected set exactly when it is the
normalization of some non-empty configured directory, or of some non-empty
loader directory that is not inside the framework tree. Membership is the only
observable (a set), so the predicate characterizes `result` up to order and
duplication. -/
def problem_spec_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) (result : List String) : Prop :=
  ∀ p : String,
    p ∈ result ↔
      ((∃ d ∈ dirs, d ≠ "" ∧ resolveDir d = p) ∨
       (∃ d ∈ loaderDirs, d ≠ "" ∧ isFrameworkPath d = false ∧ resolveDir d = p))
-- post-conditions-end

-- impl-start
def implementation_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) : List String := Id.run do
  let mut items : List String := []
  for dir in dirs do
    if dir ≠ "" then
      items := items ++ [resolveDir dir]
  for directory in loaderDirs do
    if directory ≠ "" ∧ isFrameworkPath directory = false then
      items := items ++ [resolveDir directory]
  return items
-- impl-end

-- proof-start
/-- Closed form for one accumulation loop with a conditional `++ [f x]` body,
generalized over the accumulator. -/
private lemma collectTemplateDirs_loop
    (f : String → String) (p : String → Prop) [DecidablePred p]
    (xs : List String) (init : List String) :
    Id.run (forIn xs init
        (fun x r => if p x then ForInStep.yield (r ++ [f x]) else ForInStep.yield r))
      = init ++ (xs.filter (fun x => decide (p x))).map f := by
  induction xs generalizing init with
  | nil =>
    simp only [List.forIn_nil, Id.run, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : p a <;> simp [h, ih, List.append_assoc]

theorem correct_collectTemplateDirs :
    ∀ (resolveDir : String → String) (isFrameworkPath : String → Bool)
      (dirs loaderDirs : List String),
      problem_spec_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
        (implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs) := by
  intro resolveDir isFrameworkPath dirs loaderDirs
  -- Reduce the two imperative loops to explicit `filter`/`map` closed forms.
  have key : implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
      = (dirs.filter (fun d => decide (d ≠ ""))).map resolveDir
        ++ (loaderDirs.filter (fun d => decide (d ≠ "" ∧ isFrameworkPath d = false))).map resolveDir := by
    show Id.run (forIn loaderDirs
            (Id.run (forIn dirs ([] : List String)
              (fun dir r => if dir ≠ "" then ForInStep.yield (r ++ [resolveDir dir])
                else ForInStep.yield r)))
            (fun directory r => if directory ≠ "" ∧ isFrameworkPath directory = false
              then ForInStep.yield (r ++ [resolveDir directory]) else ForInStep.yield r))
        = _
    rw [collectTemplateDirs_loop resolveDir (fun d => d ≠ ""),
        collectTemplateDirs_loop resolveDir (fun d => d ≠ "" ∧ isFrameworkPath d = false)]
    simp [List.nil_append]
  rw [key]
  unfold problem_spec_collectTemplateDirs
  intro p
  simp only [List.mem_append, List.mem_map, List.mem_filter, decide_eq_true_eq]
  constructor
  · rintro (⟨d, hd, heq⟩ | ⟨d, ⟨hd, hne, hfw⟩, heq⟩)
    · obtain ⟨hd2, hne⟩ := hd; exact Or.inl ⟨d, hd2, hne, heq⟩
    · exact Or.inr ⟨d, hd, hne, hfw, heq⟩
  · rintro (⟨d, hd, hne, heq⟩ | ⟨d, hd, hne, hfw, heq⟩)
    · exact Or.inl ⟨d, ⟨hd, hne⟩, heq⟩
    · exact Or.inr ⟨d, ⟨hd, hne, hfw⟩, heq⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 same_spec confirmed True for all 8 attack files + positive control (swebench_unified.markers.same_spec, lean backend). Positive control (gold Solution.lean copy) verifies: lean_verify.sh exit 0; `#print axioms correct_collectTemplateDirs` => [propext, Quot.sound] (clean, no sorryAx).

SPEC SHAPE: the postcondition is an EXACT two-directional membership iff over a set-modeled `List String` (p ∈ result ↔ ((∃ d ∈ dirs, d≠"" ∧ resolveDir d = p) ∨ (∃ d ∈ loaderDirs, d≠"" ∧ isFrameworkPath d = false ∧ resolveDir d = p))). This pins the result set in both directions up to order/multiplicity (exactly what Python set() collapses), leaving no slack for a wrong impl to close.

ATTACKS (all same_spec=True; each carried the GOLD proof as a genuine close attempt; command: `bash scripts/lean_verify.sh <file>`):
  atk_1 = prepatch/unfiltered dirs loop (keeps empty dirs): EXIT=1 (does NOT close).
  atk_2 = partial-domain: loader empties NOT filtered (drops directory≠""): EXIT=1.
  atk_3 = dropped framework exclusion (keep all non-empty loader dirs): EXIT=1.
  atk_4 = boundary/inverted guard: keep ONLY empty dirs (guard flipped to d=""): EXIT=1.
  atk_5 = control-flow-effect: overwrite accumulator (items := [resolveDir dir], keep only last dir): EXIT=1.
  atk_6 = control-flow-effect: ignore loaderDirs entirely: EXIT=1.
  atk_7 = ungrounded-oracle echo: apply framework check to DIRS too (wrong predicate site): EXIT=1.
  atk_prepatch = exact prepatch impl (both guards reverted): EXIT=1 (prepatch bug reproduced).
NO wrong impl closes => no closing clean-axiom proof exists => the mandatory materialize+resolve step for a closing wrong impl is vacuous (nothing to run); patches = {}.

CONCLUSIVE REFUTATIONS (machine-checked, ran concurrently ≤4 at a time): for EACH wrong impl I proved `¬ problem_spec_collectTemplateDirs <args> (implementation_collectTemplateDirs <args>)` on a concrete counterexample, via decidability (exact absurd ((h p).mp/.mpr (by decide)) (by decide)). ref_1..ref_7 ALL verify EXIT=0. This proves each wrong impl PROVABLY VIOLATES the frozen spec, so no `correct_` can ever close for any of them (not merely that the gold proof happened to fail). Counterexamples: ref_1/2/4 resolveDir=id,isFwk=const false, [""]/["" in loader] => ""∈result but RHS false; ref_3 isFwk=const true, loaderDirs=["x"] => "x"∈result but excluded; ref_5 dirs=["a","b"] => "a" required by RHS but missing (overwritten); ref_6 loaderDirs=["x"] => "x" required but loader loop skipped; ref_7 isFwk=const true, dirs=["x"] => "x" required by RHS (dirs branch ignores isFrameworkPath) but dropped by impl.

CORRESPONDENCE RESOLVES (executed): GOLD patch RESOLVES (✓=1, resolved 1); EMPTY/no-fix patch does NOT resolve (empty patch, resolved 0). run_resolve() initially returned 'no report' for both due to concurrency contention with 27 in-flight run_evaluation processes; re-run serially under `docker -m swebench_unified.run_evaluation` and both produced valid reports. This validates the model↔patch correspondence: the FAIL_TO_PASS discriminator is precisely the empty-dir guard.

REFINEMENT.MD AUDIT: 8 legs, all R / I / A-reference — NO kind-3 (inexpressible) and NO A-consumed. Legs 1,2,5 = R (set↔membership-only List, flattened nested iteration); legs 3,6-guard,8 = I (added truthiness guard `if dir` ⇔ `≠""`, return); legs 4,6-pred,7 = A-reference (resolveDir models `cwd/to_path`, isFrameworkPath models `is_django_path`). A-reference correspondence HOLDS: the theorem `correct_collectTemplateDirs` opens with `∀ (resolveDir : String → String) (isFrameworkPath : String → Bool) ...` and the proof `intro`s them and consumes NO property (verified: proof only rewrites the impl to filter/map closed forms and unfolds the iff), so the contract holds for ANY concrete callee => cannot drift. G-AX skip stub is therefore correct (no `_prop` axiom to validate). Both callees at base_commit 0b31e024 are the unchanged std/django path machinery (`cwd / to_path(d)`) and predicate (`is_django_path`), matching the A-reference model.

VERDICT: SOUND. 8 distinct same-spec wrong impls (partial-domain, boundary/inverted, control-flow-effect x2, ungrounded-oracle echo, dropped-exclusion, prepatch) all fail to close, each with a machine-checked refutation proving spec violation; positive control verifies with clean axioms; gold patch resolves and no-fix patch does not. verify⇒correct holds for this bundle; no counterexample to soundness found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl closes, so there is no closing-proof patch to run. Correspondence sanity resolves (executed under the official harness): the GOLD patch (benchmark-verified/django__django-15572/patch.diff) RESOLVES (run_id sbu-audit-gold-15572: Instances resolved: 1, ✓=1); the no-fix EMPTY patch (faithful patch of the 'don't filter empties' prepatch/unfiltered impl) does NOT resolve (run_id sbu-audit-empty-15572: empty patch, resolved 0). This confirms the FAIL_TO_PASS test test_template_dirs_ignore_empty_path is exactly the empty-dir discriminator the spec's `d ≠ ""` filter encodes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collect the set of directory paths that the template watcher should observe.

Two sources contribute directory entries: a list of configured directories, and
a list of loader-provided directories. Each entry is normalized to an absolute
path. Loader entries that point inside the framework's own tree are excluded.
A directory entry that is empty contributes nothing. The collected paths form a
set (membership only; order and repetition are irrelevant).
-/

-- axioms-start
-- Two unchanged path-handling callees, modeled as universally-quantified
-- parameters (the contract holds for ANY such function, so the proof consumes
-- no property of either):
--   * `resolveDir`      : normalize a directory entry to an absolute path.
--   * `isFrameworkPath` : true when a path lies inside the framework's own tree.
-- No `_prop` axiom is required (both callees are passthrough parameters).
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- A normalized path `p` belongs to the collected set exactly when it is the
normalization of some non-empty configured directory, or of some non-empty
loader directory that is not inside the framework tree. Membership is the only
observable (a set), so the predicate characterizes `result` up to order and
duplication. -/
def problem_spec_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) (result : List String) : Prop :=
  ∀ p : String,
    p ∈ result ↔
      ((∃ d ∈ dirs, d ≠ "" ∧ resolveDir d = p) ∨
       (∃ d ∈ loaderDirs, d ≠ "" ∧ isFrameworkPath d = false ∧ resolveDir d = p))
-- post-conditions-end

-- impl-start
def implementation_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) : List String := Id.run do
  let mut items : List String := []
  for dir in dirs do
    if dir ≠ "" then
      items := items ++ [resolveDir dir]
  for directory in loaderDirs do
    if directory ≠ "" ∧ isFrameworkPath directory = false then
      items := items ++ [resolveDir directory]
  return items
-- impl-end

-- proof-start
/-- Closed form for one accumulation loop with a conditional `++ [f x]` body,
generalized over the accumulator. -/
private lemma collectTemplateDirs_loop
    (f : String → String) (p : String → Prop) [DecidablePred p]
    (xs : List String) (init : List String) :
    Id.run (forIn xs init
        (fun x r => if p x then ForInStep.yield (r ++ [f x]) else ForInStep.yield r))
      = init ++ (xs.filter (fun x => decide (p x))).map f := by
  induction xs generalizing init with
  | nil =>
    simp only [List.forIn_nil, Id.run, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : p a <;> simp [h, ih, List.append_assoc]

theorem correct_collectTemplateDirs :
    ∀ (resolveDir : String → String) (isFrameworkPath : String → Bool)
      (dirs loaderDirs : List String),
      problem_spec_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
        (implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs) := by
  intro resolveDir isFrameworkPath dirs loaderDirs
  -- Reduce the two imperative loops to explicit `filter`/`map` closed forms.
  have key : implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
      = (dirs.filter (fun d => decide (d ≠ ""))).map resolveDir
        ++ (loaderDirs.filter (fun d => decide (d ≠ "" ∧ isFrameworkPath d = false))).map resolveDir := by
    show Id.run (forIn loaderDirs
            (Id.run (forIn dirs ([] : List String)
              (fun dir r => if dir ≠ "" then ForInStep.yield (r ++ [resolveDir dir])
                else ForInStep.yield r)))
            (fun directory r => if directory ≠ "" ∧ isFrameworkPath directory = false
              then ForInStep.yield (r ++ [resolveDir directory]) else ForInStep.yield r))
        = _
    rw [collectTemplateDirs_loop resolveDir (fun d => d ≠ ""),
        collectTemplateDirs_loop resolveDir (fun d => d ≠ "" ∧ isFrameworkPath d = false)]
    simp [List.nil_append]
  rw [key]
  unfold problem_spec_collectTemplateDirs
  intro p
  simp only [List.mem_append, List.mem_map, List.mem_filter, decide_eq_true_eq]
  constructor
  · rintro (⟨d, hd, heq⟩ | ⟨d, ⟨hd, hne, hfw⟩, heq⟩)
    · obtain ⟨hd2, hne⟩ := hd; exact Or.inl ⟨d, hd2, hne, heq⟩
    · exact Or.inr ⟨d, hd, hne, hfw, heq⟩
  · rintro (⟨d, hd, hne, heq⟩ | ⟨d, hd, hne, hfw, heq⟩)
    · exact Or.inl ⟨d, ⟨hd, hne⟩, heq⟩
    · exact Or.inr ⟨d, ⟨hd, hne, hfw⟩, heq⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 same_spec confirmed True for all 8 attack files + positive control (swebench_unified.markers.same_spec, lean backend). Positive control (gold Solution.lean copy) verifies: lean_verify.sh exit 0; `#print axioms correct_collectTemplateDirs` => [propext, Quot.sound] (clean, no sorryAx).

SPEC SHAPE: the postcondition is an EXACT two-directional membership iff over a set-modeled `List String` (p ∈ result ↔ ((∃ d ∈ dirs, d≠"" ∧ resolveDir d = p) ∨ (∃ d ∈ loaderDirs, d≠"" ∧ isFrameworkPath d = false ∧ resolveDir d = p))). This pins the result set in both directions up to order/multiplicity (exactly what Python set() collapses), leaving no slack for a wrong impl to close.

ATTACKS (all same_spec=True; each carried the GOLD proof as a genuine close attempt; command: `bash scripts/lean_verify.sh <file>`):
  atk_1 = prepatch/unfiltered dirs loop (keeps empty dirs): EXIT=1 (does NOT close).
  atk_2 = partial-domain: loader empties NOT filtered (drops directory≠""): EXIT=1.
  atk_3 = dropped framework exclusion (keep all non-empty loader dirs): EXIT=1.
  atk_4 = boundary/inverted guard: keep ONLY empty dirs (guard flipped to d=""): EXIT=1.
  atk_5 = control-flow-effect: overwrite accumulator (items := [resolveDir dir], keep only last dir): EXIT=1.
  atk_6 = control-flow-effect: ignore loaderDirs entirely: EXIT=1.
  atk_7 = ungrounded-oracle echo: apply framework check to DIRS too (wrong predicate site): EXIT=1.
  atk_prepatch = exact prepatch impl (both guards reverted): EXIT=1 (prepatch bug reproduced).
NO wrong impl closes => no closing clean-axiom proof exists => the mandatory materialize+resolve step for a closing wrong impl is vacuous (nothing to run); patches = {}.

CONCLUSIVE REFUTATIONS (machine-checked, ran concurrently ≤4 at a time): for EACH wrong impl I proved `¬ problem_spec_collectTemplateDirs <args> (implementation_collectTemplateDirs <args>)` on a concrete counterexample, via decidability (exact absurd ((h p).mp/.mpr (by decide)) (by decide)). ref_1..ref_7 ALL verify EXIT=0. This proves each wrong impl PROVABLY VIOLATES the frozen spec, so no `correct_` can ever close for any of them (not merely that the gold proof happened to fail). Counterexamples: ref_1/2/4 resolveDir=id,isFwk=const false, [""]/["" in loader] => ""∈result but RHS false; ref_3 isFwk=const true, loaderDirs=["x"] => "x"∈result but excluded; ref_5 dirs=["a","b"] => "a" required by RHS but missing (overwritten); ref_6 loaderDirs=["x"] => "x" required but loader loop skipped; ref_7 isFwk=const true, dirs=["x"] => "x" required by RHS (dirs branch ignores isFrameworkPath) but dropped by impl.

CORRESPONDENCE RESOLVES (executed): GOLD patch RESOLVES (✓=1, resolved 1); EMPTY/no-fix patch does NOT resolve (empty patch, resolved 0). run_resolve() initially returned 'no report' for both due to concurrency contention with 27 in-flight run_evaluation processes; re-run serially under `docker -m swebench_unified.run_evaluation` and both produced valid reports. This validates the model↔patch correspondence: the FAIL_TO_PASS discriminator is precisely the empty-dir guard.

REFINEMENT.MD AUDIT: 8 legs, all R / I / A-reference — NO kind-3 (inexpressible) and NO A-consumed. Legs 1,2,5 = R (set↔membership-only List, flattened nested iteration); legs 3,6-guard,8 = I (added truthiness guard `if dir` ⇔ `≠""`, return); legs 4,6-pred,7 = A-reference (resolveDir models `cwd/to_path`, isFrameworkPath models `is_django_path`). A-reference correspondence HOLDS: the theorem `correct_collectTemplateDirs` opens with `∀ (resolveDir : String → String) (isFrameworkPath : String → Bool) ...` and the proof `intro`s them and consumes NO property (verified: proof only rewrites the impl to filter/map closed forms and unfolds the iff), so the contract holds for ANY concrete callee => cannot drift. G-AX skip stub is therefore correct (no `_prop` axiom to validate). Both callees at base_commit 0b31e024 are the unchanged std/django path machinery (`cwd / to_path(d)`) and predicate (`is_django_path`), matching the A-reference model.

VERDICT: SOUND. 8 distinct same-spec wrong impls (partial-domain, boundary/inverted, control-flow-effect x2, ungrounded-oracle echo, dropped-exclusion, prepatch) all fail to close, each with a machine-checked refutation proving spec violation; positive control verifies with clean axioms; gold patch resolves and no-fix patch does not. verify⇒correct holds for this bundle; no counterexample to soundness found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift-from-real-callee) verified for django__django-15572 collectTemplateDirs, modeling get_template_directories() (django/template/autoreload.py).

Real callee: base_commit 0b31e024...; gold fix 62739b6e26 adds `if dir` to the backend-dirs generator and `if directory and not is_django_path(directory)` to the loader-dirs generator, collecting a SET of `cwd / to_path(x)`.

Spec fidelity checks:
- Structural match: spec keeps a normalized path p iff p is `resolveDir d` for some non-empty backend dir d, OR for some non-empty loader dir d with `isFrameworkPath d = false`. This is exactly the post-patch decision. Framework filtering applies ONLY to loader dirs in both spec and source (backend `"DJ_x"` retained by both) — spec does not over-filter.
- `if dir` -> `d != ""`: for a directory str, falsy iff empty string; faithful (mapping.md documents the regression trigger "").
- Callees resolveDir/isFrameworkPath are UNIVERSALLY-QUANTIFIED parameters. The theorem holds for ALL such functions, so the real (fixed) callees are one instance -> the abstraction is conservative, not spec-too-strong. Proof consumes no property of either (A-reference), confirmed by clean `#print axioms` = [propext, Quot.sound] (no _prop axiom, no sorryAx).
- Set semantics via membership `<->` correctly models Python `set` (order/dup/ many-to-one normalization collisions all handled).

Mechanical corroboration:
- Lean compiles, exit 0, no sorry/admit; #print axioms clean.
- same_spec(Solution, Solution_prepatch, lean tables) = True (spec region byte-identical; prepatch reverts BOTH guards so G-DIFF sees the omission).
- conformance_check.py: status=pass, 0 disagreements over 150000 inputs (exhaustive lists len 0..2 over alphabet incl "" and framework markers + fuzz), seed=15572.

No diverging input exists within the modeled domain (finite String lists, arbitrary resolveDir/isFrameworkPath). Spec is neither too strong nor drifting from the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (spec view clean); same_spec(Solution, Solution_prepatch)=True; meta relaxed_leakage=None so no deferral needed. Semantic review beyond problem_statement: the gold edit is a truthiness guard dropping empty-string directory entries at two sites (`if dir` / `if directory and not is_django_path(directory)`). The public problem_statement already fully discloses this discriminator: it states autoreload 'breaks on empty string in TEMPLATES DIRS', shows `"DIRS": ['']  # wrong`, prescribes `filter(None, ...)`, and explains normalization turns the empty string into the project root. The spec view's `d ≠ ""` conjuncts and docstring line 'A directory entry that is empty contributes nothing' merely restate that already-public empty-string filtering — no information beyond problem_statement. The `isFrameworkPath` exclusion models PRE-EXISTING code (`not is_django_path`), not the gold edit, so it cannot leak the edit. No diff markers, no verbatim gold-patch line, patched file path django/template/autoreload.py absent, patched symbol get_template_directories renamed to collectTemplateDirs, is_django_path renamed to isFrameworkPath, and no bug/fix/regression narration. Spec characterizes correct behavior via membership iff, not the edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
