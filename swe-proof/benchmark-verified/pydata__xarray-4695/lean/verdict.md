# P2 adversarial audit — pydata__xarray-4695

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_reverse.lean`, `atk_droplast.lean`, `atk_alwaysmethod.lean`, `atk_partial.lean`, `atk_dedup.lean`, `atk_headonly.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a total equality result = canonicalSelArgs key, pinning the output to a single concrete SelArgs value for every key. Every deviating impl is machine-refuted (7 refutation lemmas ¬ problem_spec ... (implementation ...) all verify exit 0 on concrete inputs), so no wrong impl can produce a closing correct_ proof. verify ⇏ correct does NOT hold here: verify ⇒ correct.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,34 +64,33 @@
 -- impl-start
 def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
   let mut indexers : List (String × Label) := []
+  let mut method : Option Label := none
+  let mut tolerance : Option Label := none
+  let mut drop : Option Label := none
   for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+    let (name, label) := entry
+    if name = "method" then
+      method := some label
+    else if name = "tolerance" then
+      tolerance := some label
+    else if name = "drop" then
+      drop := some label
+    else
+      indexers := indexers ++ [entry]
+  return { indexers := indexers, method := method, tolerance := tolerance, drop := drop }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 2 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,11 @@
 def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
   let mut indexers : List (String × Label) := []
   for entry in key do
-    indexers := indexers ++ [entry]
+    indexers := [entry] ++ indexers
   return { indexers := indexers, method := none, tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
 theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
     (forIn key init
         (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
@@ -92,6 +89,10 @@
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 3 — `atk_droplast.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,36 +62,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
-  let mut indexers : List (String × Label) := []
-  for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+def implementation_labelSelection (key : List (String × Label)) : SelArgs :=
+  { indexers := key.dropLast, method := none, tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 4 — `atk_alwaysmethod.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,36 +62,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
-  let mut indexers : List (String × Label) := []
-  for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+def implementation_labelSelection (key : List (String × Label)) : SelArgs :=
+  { indexers := key, method := some "x", tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 5 — `atk_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,36 +62,23 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
-  let mut indexers : List (String × Label) := []
-  for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+def implementation_labelSelection (key : List (String × Label)) : SelArgs :=
+  match key with
+  | [] => { indexers := [], method := none, tolerance := none, drop := none }
+  | _  => { indexers := [], method := none, tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 6 — `atk_dedup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,36 +62,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
-  let mut indexers : List (String × Label) := []
-  for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+def implementation_labelSelection (key : List (String × Label)) : SelArgs :=
+  { indexers := key.eraseDups, method := none, tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 7 — `atk_headonly.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,36 +62,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
-  let mut indexers : List (String × Label) := []
-  for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+def implementation_labelSelection (key : List (String × Label)) : SelArgs :=
+  { indexers := key.take 1, method := none, tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
   unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
   simp only [Id.run]
-  rw [labelSelection_loop]
-  rfl
+  first
+    | rfl
+    | (rw [labelSelection_loop]; rfl)
+    | decide
+    | simp
+    | (intro; rfl)
 -- proof-end
```

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,36 +62,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
-  let mut indexers : List (String × Label) := []
-  for entry in key do
-    indexers := indexers ++ [entry]
-  return { indexers := indexers, method := none, tolerance := none, drop := none }
+def implementation_labelSelection (key : List (String × Label)) : SelArgs :=
+  { indexers := key, method := none, tolerance := none, drop := none }
 -- impl-end
 
 -- proof-start
-/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
-the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
-over the accumulator so the induction goes through. -/
-theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
-    (forIn key init
-        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
-      : Id (List (String × Label)))
-      = pure (init ++ key) := by
-  induction key generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [pure_bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_labelSelection :
     ∀ (key : List (String × Label)),
       problem_spec_labelSelection key (implementation_labelSelection key) := by
   intro key
-  unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
-  simp only [Id.run]
-  rw [labelSelection_loop]
   rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting array elements by label from a mapping of dimension names to labels.

A label-based selection is requested as a mapping `{dimension-name → label}`. The
whole mapping describes WHICH position to select along each named dimension. The
selection routine that performs the lookup also accepts, separately, a few
optional *matching* parameters that tune how labels are matched (an inexact-match
mode, a numeric matching tolerance, and a coordinate-dropping flag); when a
selection is requested purely by a mapping of dimensions, none of those tuning
parameters is being set.

The desired behavior: building the selection from such a mapping must treat the
mapping *as a whole* as the dimension→label selection, so that EVERY entry of the
mapping is used to select along its dimension — regardless of what that dimension
happens to be named — and none of the optional matching parameters is populated
from the mapping. In particular, a dimension whose name happens to coincide with
the name of one of those optional matching parameters must still be used as an
ordinary selector, not diverted into tuning the matcher.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled is the construction of the selection request from the input mapping;
-- it is modeled structurally over the mapping itself, so no `opaque`/`axiom`
-- callee contract is needed. The downstream lookup routine that consumes the
-- request is out of scope.
-- axioms-end

-- pure-start
/-- A tick-label value supplied for one dimension. Selection routing never
inspects the value, so it is modeled by its representation. -/
abbrev Label := String

/-- The argument bundle handed to the label-based selection routine: the
dimension→label `indexers` mapping plus the three optional matching parameters
(`none` means "left at its default / not supplied"). -/
structure SelArgs where
  indexers : List (String × Label)
  method : Option Label
  tolerance : Option Label
  drop : Option Label
deriving DecidableEq, Repr

/-- The selection request that treats the whole mapping as the dimension→label
selection: the mapping becomes `indexers` verbatim and no optional matching
parameter is populated. -/
def canonicalSelArgs (key : List (String × Label)) : SelArgs :=
  { indexers := key, method := none, tolerance := none, drop := none }
-- pure-end

-- post-conditions-start
/-- The selection request built from the mapping uses the entire mapping as the
dimension→label `indexers` (every entry preserved, in order) and leaves all three
optional matching parameters unset. Each output component is pinned: `indexers`
equals the input mapping and `method`/`tolerance`/`drop` are all `none`. -/
def problem_spec_labelSelection
    (key : List (String × Label)) (result : SelArgs) : Prop :=
  result = canonicalSelArgs key
-- post-conditions-end

-- impl-start
def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
  let mut indexers : List (String × Label) := []
  for entry in key do
    indexers := indexers ++ [entry]
  return { indexers := indexers, method := none, tolerance := none, drop := none }
-- impl-end

-- proof-start
/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
over the accumulator so the induction goes through. -/
theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
    (forIn key init
        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
      : Id (List (String × Label)))
      = pure (init ++ key) := by
  induction key generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [pure_bind] at ih ⊢
    rw [ih]
    simp

theorem correct_labelSelection :
    ∀ (key : List (String × Label)),
      problem_spec_labelSelection key (implementation_labelSelection key) := by
  intro key
  unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
  simp only [Id.run]
  rw [labelSelection_loop]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total-equality spec `problem_spec_labelSelection key result := result = canonicalSelArgs key`, canonicalSelArgs = {indexers:=key, method:=none, tolerance:=none, drop:=none}. Tightest possible shape: exactly one satisfying result per key. Any closing proof forces extensional equality to gold on all inputs.

SAME-SPEC: all 9 attack/control files pass swebench_unified.markers.same_spec (True) — impl+proof regions edited only.

### PROTOCOL RUN (from project root; `bash scripts/lean_verify.sh <file>`):
- atk_pos (gold positive control): EXIT=0; #print axioms correct_labelSelection = [propext, Quot.sound] (clean, no sorryAx).
- atk_echo (extensional gold echo, {indexers:=key,...} closed by rfl): EXIT=0; #print axioms = does not depend on any axioms (clean). This is the ONLY same-spec WRONG-shaped-but-actually-correct impl that closes; it computes the identical function as gold, so its faithful refined patch IS the gold positional patch `sel(**key)->sel(key)` (materialized in patches[atk_echo]), which RESOLVES (bundle patch_equals_gold=True). NOT a break — a resolving echo of gold (per 2026-08-06 G-PANEL-1 policy this is expected, not a weakness).
- 7 genuinely-wrong impls, all EXIT=1 (unsolvable goal), NONE close:
  atk_prepatch (prepatch bug: diverts method/tolerance/drop-named entries out of indexers),
  atk_reverse (reverses indexers order),
  atk_droplast (off-by-one, drops last entry),
  atk_alwaysmethod (ungrounded oracle echo: always method:=some "x"),
  atk_partial (partial-domain: returns empty indexers for all keys),
  atk_dedup (dedups indexers),
  atk_headonly (boundary: keeps only first entry).

RIGOR — non-weak-tactic proof: for each of the 7 I encoded a machine-checked refutation `¬ problem_spec_labelSelection <input> (implementation_labelSelection <input>)` closed by `decide` — ALL 7 verify EXIT=0 (ref_prepatch on [("method","a")], ref_reverse on [("a","1"),("b","2")], ref_droplast on [("a","1")], ref_alwaysmethod on [], ref_partial on [("a","1")], ref_dedup on [("a","1"),("a","1")], ref_headonly on [("a","1"),("b","2")]). This proves the failures are inherent to the equality spec, not artifacts of weak proof tactics — so no closing wrong impl exists and no falsifying resolve run is possible/required.

RESOLVE: the only closing patch (echo) is byte-equal to the gold patch and resolves (patch_equals_gold=True in meta.json). No closing wrong impl → no candidate whose materialized patch fails to resolve.

A-LEG AUDIT (refinement.md): meta.json confirms axioms=[], opaque_callees=[], deep_model_references=[] — there are NO A-legs. refinement.md legs are ops 1-2 tagged R (type refinement of 'pass mapping positionally as indexers, all optional params default' into SelArgs) and one I (deletion of the **key splat). No kind-3 axiom-of-a-changed-decision. Correspondence holds: R legs model the post-patch construction structurally over the whole mapping; validated by verdict.md's real-callee check of either_dict_or_kwargs/sel at base_commit. G-AX correctly skips (empty axioms).

prepatch_reproduced=true: atk_prepatch faithfully re-encodes Solution_prepatch.lean's splat-diversion bug and is machine-refuted against the spec (ref_prepatch EXIT=0), matching the F2P {dim1, method} collision.

CONCLUSION: ≥5 (7) distinct wrong impls attacked and verified; none closes; the single closing non-gold impl is an extensionally-identical echo whose patch resolves. Spec is maximally tight (verify ⇒ correct). SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_reverse.lean`, `atk_droplast.lean`, `atk_alwaysmethod.lean`, `atk_partial.lean`, `atk_dedup.lean`, `atk_headonly.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a total equality result = canonicalSelArgs key, pinning the output to a single concrete SelArgs value for every key. Every deviating impl is machine-refuted (7 refutation lemmas ¬ problem_spec ... (implementation ...) all verify exit 0 on concrete inputs), so no wrong impl can produce a closing correct_ proof. verify ⇏ correct does NOT hold here: verify ⇒ correct.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_droplast.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_alwaysmethod.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_dedup.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_headonly.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting array elements by label from a mapping of dimension names to labels.

A label-based selection is requested as a mapping `{dimension-name → label}`. The
whole mapping describes WHICH position to select along each named dimension. The
selection routine that performs the lookup also accepts, separately, a few
optional *matching* parameters that tune how labels are matched (an inexact-match
mode, a numeric matching tolerance, and a coordinate-dropping flag); when a
selection is requested purely by a mapping of dimensions, none of those tuning
parameters is being set.

The desired behavior: building the selection from such a mapping must treat the
mapping *as a whole* as the dimension→label selection, so that EVERY entry of the
mapping is used to select along its dimension — regardless of what that dimension
happens to be named — and none of the optional matching parameters is populated
from the mapping. In particular, a dimension whose name happens to coincide with
the name of one of those optional matching parameters must still be used as an
ordinary selector, not diverted into tuning the matcher.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled is the construction of the selection request from the input mapping;
-- it is modeled structurally over the mapping itself, so no `opaque`/`axiom`
-- callee contract is needed. The downstream lookup routine that consumes the
-- request is out of scope.
-- axioms-end

-- pure-start
/-- A tick-label value supplied for one dimension. Selection routing never
inspects the value, so it is modeled by its representation. -/
abbrev Label := String

/-- The argument bundle handed to the label-based selection routine: the
dimension→label `indexers` mapping plus the three optional matching parameters
(`none` means "left at its default / not supplied"). -/
structure SelArgs where
  indexers : List (String × Label)
  method : Option Label
  tolerance : Option Label
  drop : Option Label
deriving DecidableEq, Repr

/-- The selection request that treats the whole mapping as the dimension→label
selection: the mapping becomes `indexers` verbatim and no optional matching
parameter is populated. -/
def canonicalSelArgs (key : List (String × Label)) : SelArgs :=
  { indexers := key, method := none, tolerance := none, drop := none }
-- pure-end

-- post-conditions-start
/-- The selection request built from the mapping uses the entire mapping as the
dimension→label `indexers` (every entry preserved, in order) and leaves all three
optional matching parameters unset. Each output component is pinned: `indexers`
equals the input mapping and `method`/`tolerance`/`drop` are all `none`. -/
def problem_spec_labelSelection
    (key : List (String × Label)) (result : SelArgs) : Prop :=
  result = canonicalSelArgs key
-- post-conditions-end

-- impl-start
def implementation_labelSelection (key : List (String × Label)) : SelArgs := Id.run do
  let mut indexers : List (String × Label) := []
  for entry in key do
    indexers := indexers ++ [entry]
  return { indexers := indexers, method := none, tolerance := none, drop := none }
-- impl-end

-- proof-start
/-- The `for entry in key do indexers := indexers ++ [entry]` loop accumulates
the entries onto the initial list, i.e. it computes `init ++ key`. Generalized
over the accumulator so the induction goes through. -/
theorem labelSelection_loop (key : List (String × Label)) (init : List (String × Label)) :
    (forIn key init
        (fun entry r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [entry])))
      : Id (List (String × Label)))
      = pure (init ++ key) := by
  induction key generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [pure_bind] at ih ⊢
    rw [ih]
    simp

theorem correct_labelSelection :
    ∀ (key : List (String × Label)),
      problem_spec_labelSelection key (implementation_labelSelection key) := by
  intro key
  unfold problem_spec_labelSelection implementation_labelSelection canonicalSelArgs
  simp only [Id.run]
  rw [labelSelection_loop]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total-equality spec `problem_spec_labelSelection key result := result = canonicalSelArgs key`, canonicalSelArgs = {indexers:=key, method:=none, tolerance:=none, drop:=none}. Tightest possible shape: exactly one satisfying result per key. Any closing proof forces extensional equality to gold on all inputs.

SAME-SPEC: all 9 attack/control files pass swebench_unified.markers.same_spec (True) — impl+proof regions edited only.

### PROTOCOL RUN (from project root; `bash scripts/lean_verify.sh <file>`):
- atk_pos (gold positive control): EXIT=0; #print axioms correct_labelSelection = [propext, Quot.sound] (clean, no sorryAx).
- atk_echo (extensional gold echo, {indexers:=key,...} closed by rfl): EXIT=0; #print axioms = does not depend on any axioms (clean). This is the ONLY same-spec WRONG-shaped-but-actually-correct impl that closes; it computes the identical function as gold, so its faithful refined patch IS the gold positional patch `sel(**key)->sel(key)` (materialized in patches[atk_echo]), which RESOLVES (bundle patch_equals_gold=True). NOT a break — a resolving echo of gold (per 2026-08-06 G-PANEL-1 policy this is expected, not a weakness).
- 7 genuinely-wrong impls, all EXIT=1 (unsolvable goal), NONE close:
  atk_prepatch (prepatch bug: diverts method/tolerance/drop-named entries out of indexers),
  atk_reverse (reverses indexers order),
  atk_droplast (off-by-one, drops last entry),
  atk_alwaysmethod (ungrounded oracle echo: always method:=some "x"),
  atk_partial (partial-domain: returns empty indexers for all keys),
  atk_dedup (dedups indexers),
  atk_headonly (boundary: keeps only first entry).

RIGOR — non-weak-tactic proof: for each of the 7 I encoded a machine-checked refutation `¬ problem_spec_labelSelection <input> (implementation_labelSelection <input>)` closed by `decide` — ALL 7 verify EXIT=0 (ref_prepatch on [("method","a")], ref_reverse on [("a","1"),("b","2")], ref_droplast on [("a","1")], ref_alwaysmethod on [], ref_partial on [("a","1")], ref_dedup on [("a","1"),("a","1")], ref_headonly on [("a","1"),("b","2")]). This proves the failures are inherent to the equality spec, not artifacts of weak proof tactics — so no closing wrong impl exists and no falsifying resolve run is possible/required.

RESOLVE: the only closing patch (echo) is byte-equal to the gold patch and resolves (patch_equals_gold=True in meta.json). No closing wrong impl → no candidate whose materialized patch fails to resolve.

A-LEG AUDIT (refinement.md): meta.json confirms axioms=[], opaque_callees=[], deep_model_references=[] — there are NO A-legs. refinement.md legs are ops 1-2 tagged R (type refinement of 'pass mapping positionally as indexers, all optional params default' into SelArgs) and one I (deletion of the **key splat). No kind-3 axiom-of-a-changed-decision. Correspondence holds: R legs model the post-patch construction structurally over the whole mapping; validated by verdict.md's real-callee check of either_dict_or_kwargs/sel at base_commit. G-AX correctly skips (empty axioms).

prepatch_reproduced=true: atk_prepatch faithfully re-encodes Solution_prepatch.lean's splat-diversion bug and is machine-refuted against the spec (ref_prepatch EXIT=0), matching the F2P {dim1, method} collision.

CONCLUSION: ≥5 (7) distinct wrong impls attacked and verified; none closes; the single closing non-gold impl is an extensionally-identical echo whose patch resolves. Spec is maximally tight (verify ⇒ correct). SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function = POST-PATCH construction of the .sel call inside _LocIndexer.__getitem__ (verified worktree @ base_commit 1757dff; buggy `sel(**key)` -> fix `sel(key)`). Model canonicalSelArgs key = {indexers:=key, method/tolerance/drop:=none} faithfully reflects real post-patch behavior: either_dict_or_kwargs returns the positional mapping verbatim as indexers, all optional matching params at defaults. Ran an in-process replica of the real post-patch construction vs the model over F2P {dim1,method}, tolerance/drop-named dims, all-three-collision, dim named 'indexers', empty, single ordinary, and multi-dim cases — ALL MATCH. Collision-named dims correctly remain selectors; no optional param populated from the mapping. same_spec(Solution.lean, Solution_prepatch.lean, lean)=True (spec region byte-identical). Proof compiles (exit 0); #print axioms = [propext, Quot.sound] (no sorryAx). Model domain (association lists) is broader than realizable dict inputs (allows duplicate keys/order), but this over-breadth yields no divergence on any real dict-derived input, so the spec is not too strong and does not drift. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean, lean flavor) computed and screened with leakage.screen against the FROZEN problem_statement (not hints_text): rep.passed=True, zero hard failures. Manual semantic review confirms the mechanical result.

Gold edit: `self.data_array.sel(**key)` -> `self.data_array.sel(key)` (pass the indexer mapping positionally instead of keyword-splatting). CRUCIAL: the exact fix line appears in hints_text ONLY ('replace sel(**key) with sel(key)'); it is NOT in the solver-visible problem_statement, which merely reports the symptom (dim named 'method' throws 'Invalid fill method' on .loc; 'name of the dimension should be irrelevant').

Spec-view disclosure: the /-! ... -/ prose and pure/post-conditions regions describe the DESIRED BEHAVIOR only — whole mapping treated as the dimension->label selection, every entry used regardless of name, no optional matching parameter (method/tolerance/drop) populated, and a dimension whose name coincides with a matching-parameter name still used as a selector. This is legitimate specification of correct behavior. It does NOT reveal the edit mechanism: no mention of sel/**key/positional-vs-keyword/either_dict_or_kwargs, no diff markers, no patched file path (dataarray.py), no gold-diff line reproduced. The SelArgs field names method/tolerance/drop model the (unchanged) callee sel() signature, not the patch's changed symbols; L2/L5 symbol-collision check found nothing. The 'method' collision case in the prose is a generalization of the PUBLIC problem_statement example ('method' dimension), i.e. behavioral modeling, not gold reconstruction. No narration terms (bug/fix/patch/etc.).

A solver reading only the spec view still cannot reconstruct 'current code splats with **key, change it to positional' — that mechanism is withheld. Also verified: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical), so the prepatch variant leaks nothing extra.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
