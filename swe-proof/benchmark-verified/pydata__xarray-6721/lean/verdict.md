# P2 adversarial audit — pydata__xarray-6721

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
The spec is exact extensional equality to a TOTAL pure function: problem_spec_getChunksizes vars result := (result = mergeVars vars []). Any impl whose correct_* closes must equal mergeVars pointwise on every input, so the closing equivalence class is a single behavior (the post-patch, materialization-free reference semantics). No wrong impl closed; therefore no verify⇏correct gap exists to exhibit and no run_resolve was triggered. Discriminating inputs proving each attack differs from mergeVars: atk_2 (prepatch bug) on [<false,[],isDuck=false,matRaises=true>] returns .error while spec demands .ok []; atk_1 (never-reject) on [<true,[(x,[1])]>,<true,[(x,[2])]>] returns .ok[(x,[1]),(x,[2])] vs spec .error.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,9 +107,7 @@
   for v in vars do
     if v.hasChunks then
       for p in v.chunksizes do
-        match chunks.lookup p.1 with
-        | some c' => if c' ≠ p.2 then return .error ()
-        | none    => chunks := chunks ++ [p]
+        chunks := chunks ++ [p]
   return .ok chunks
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,6 +105,7 @@
     Except Unit (List (String × List Nat)) := Id.run do
   let mut chunks : List (String × List Nat) := []
   for v in vars do
+    if !v.isDuckArray && v.materializeRaises then return .error ()
     if v.hasChunks then
       for p in v.chunksizes do
         match chunks.lookup p.1 with
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,12 +104,16 @@
 def implementation_getChunksizes (vars : List XVar) :
     Except Unit (List (String × List Nat)) := Id.run do
   let mut chunks : List (String × List Nat) := []
+  let mut first : Bool := true
   for v in vars do
-    if v.hasChunks then
-      for p in v.chunksizes do
-        match chunks.lookup p.1 with
-        | some c' => if c' ≠ p.2 then return .error ()
-        | none    => chunks := chunks ++ [p]
+    if first then
+      first := false
+    else
+      if v.hasChunks then
+        for p in v.chunksizes do
+          match chunks.lookup p.1 with
+          | some c' => if c' ≠ p.2 then return .error ()
+          | none    => chunks := chunks ++ [p]
   return .ok chunks
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -105,11 +105,10 @@
     Except Unit (List (String × List Nat)) := Id.run do
   let mut chunks : List (String × List Nat) := []
   for v in vars do
-    if v.hasChunks then
-      for p in v.chunksizes do
-        match chunks.lookup p.1 with
-        | some c' => if c' ≠ p.2 then return .error ()
-        | none    => chunks := chunks ++ [p]
+    for p in v.chunksizes do
+      match chunks.lookup p.1 with
+      | some c' => if c' ≠ p.2 then return .error ()
+      | none    => chunks := chunks ++ [p]
   return .ok chunks
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,14 +103,7 @@
 -- impl-start
 def implementation_getChunksizes (vars : List XVar) :
     Except Unit (List (String × List Nat)) := Id.run do
-  let mut chunks : List (String × List Nat) := []
-  for v in vars do
-    if v.hasChunks then
-      for p in v.chunksizes do
-        match chunks.lookup p.1 with
-        | some c' => if c' ≠ p.2 then return .error ()
-        | none    => chunks := chunks ++ [p]
-  return .ok chunks
+  return .ok []
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,7 @@
     if v.hasChunks then
       for p in v.chunksizes do
         match chunks.lookup p.1 with
-        | some c' => if c' ≠ p.2 then return .error ()
+        | some _  => return .error ()
         | none    => chunks := chunks ++ [p]
   return .ok chunks
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
       for p in v.chunksizes do
         match chunks.lookup p.1 with
         | some c' => if c' ≠ p.2 then return .error ()
-        | none    => chunks := chunks ++ [p]
+        | none    => chunks := [p] ++ chunks
   return .ok chunks
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the chunk sizes of a collection of array-like variables.

Each variable in the collection may be *chunked*: if so it exposes, for each of
its named dimensions, the block length along that dimension. `get_chunksizes`
walks the collection and builds a single mapping from dimension name to block
length:

* a variable that is not chunked contributes nothing;
* a chunked variable contributes one entry per dimension; if a dimension has
  already been recorded with a *different* block length the collection has
  inconsistent chunking and the whole operation is rejected;
* recording a dimension whose block length already agrees with the stored value
  leaves the mapping unchanged.

The resulting mapping lists dimensions in the order they were first encountered.

Crucially, deciding whether a variable is chunked is a question about the
variable's chunk metadata only: it must be answerable by inspecting that
metadata and must never force the variable's contents to be loaded into memory.
The outcome therefore depends solely on each variable's chunk metadata, and is
the same whether or not loading a variable's contents would succeed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- variable is chunked, and the per-dimension block lengths it then exposes, are
-- observable properties of the variable supplied directly as inputs; the
-- accumulation and the inconsistency rejection are modeled deeply over those
-- inputs. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched observable properties of one array-like variable.

* `hasChunks` — whether the variable is chunked (answerable from chunk metadata
  alone, without loading the variable's contents);
* `chunksizes` — when chunked, the per-dimension block lengths, as
  `(dimension name, block lengths)` pairs in dimension order;
* `isDuckArray` — whether the variable already holds an in-place array handle;
* `materializeRaises` — whether forcing the variable's contents into memory
  would fail (e.g. an unreachable backing store).

`isDuckArray` and `materializeRaises` describe what happens if the variable's
contents are loaded; a correct computation of the chunk-size mapping never needs
them, and the specification below is deliberately independent of both. -/
structure XVar where
  hasChunks : Bool
  chunksizes : List (String × List Nat)
  isDuckArray : Bool
  materializeRaises : Bool

/-- Record one `(dimension, block lengths)` entry into the accumulated mapping.
A new dimension is appended (preserving first-seen order); a dimension already
present with the *same* block lengths leaves the mapping unchanged; a dimension
present with *different* block lengths makes the collection inconsistent. -/
def insertChunk (acc : List (String × List Nat)) (p : String × List Nat) :
    Except Unit (List (String × List Nat)) :=
  match acc.lookup p.1 with
  | some c' => if c' = p.2 then .ok acc else .error ()
  | none    => .ok (acc ++ [p])

/-- Fold a single chunked variable's entries into the accumulator, rejecting on
the first inconsistency. -/
def mergePairs : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match insertChunk acc p with
    | .error _ => .error ()
    | .ok acc' => mergePairs acc' ps

/-- The reference chunk-size mapping for a collection of variables, threaded
front-to-back. Non-chunked variables are skipped; chunked variables fold their
entries in, rejecting on the first inconsistency. Depends only on each
variable's chunk metadata (`hasChunks`, `chunksizes`). -/
def mergeVars : List XVar → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | [],      acc => .ok acc
  | v :: vs, acc =>
    if v.hasChunks then
      match mergePairs acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => mergeVars vs acc'
    else mergeVars vs acc
-- pure-end

-- post-conditions-start
/-- The collected mapping is exactly the reference fold over the variables'
chunk metadata: each non-chunked variable contributes nothing, each chunked
variable contributes its per-dimension block lengths, inconsistent block lengths
for the same dimension are rejected, and dimensions appear in first-seen order.
The outcome is independent of whether loading any variable's contents would
succeed. -/
def problem_spec_getChunksizes (vars : List XVar)
    (result : Except Unit (List (String × List Nat))) : Prop :=
  result = mergeVars vars []
-- post-conditions-end

-- impl-start
def implementation_getChunksizes (vars : List XVar) :
    Except Unit (List (String × List Nat)) := Id.run do
  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks
-- impl-end


-- proof-start
/-- Collapse the `for`-loop's early-return state `⟨earlyReturn?, acc⟩` back into
the `Except` result: a pending early return propagates, otherwise the loop
succeeded with its accumulator. This mirrors the impl's final `match`. -/
def loopFinish
    (r : MProd (Option (Except Unit (List (String × List Nat))))
              (List (String × List Nat))) :
    Except Unit (List (String × List Nat)) :=
  match r.fst with
  | some e => e
  | none   => .ok r.snd

/-- Pure functional counterpart of the inner `for p in v.chunksizes` loop,
mirroring its early-return-on-inconsistency semantics. -/
def innerLoop : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match acc.lookup p.1 with
    | some c' => if c' ≠ p.2 then .error () else innerLoop acc ps
    | none    => innerLoop (acc ++ [p]) ps

/-- Pure functional counterpart of the outer `for v in vars` loop, threading the
accumulator and propagating the first inconsistency. -/
def outerLoop : List (String × List Nat) → List XVar →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, v :: vs =>
    if v.hasChunks then
      match innerLoop acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => outerLoop acc' vs
    else outerLoop acc vs

theorem inner_forIn_eq_innerLoop (acc pairs : List (String × List Nat)) :
    loopFinish
      (forIn (m := Id) pairs
        (⟨none, acc⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                            (List (String × List Nat)))
        (fun p r =>
          match r.snd.lookup p.1 with
          | some c' =>
            if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
            else pure (ForInStep.yield ⟨none, r.snd⟩)
          | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩))) =
      innerLoop acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [List.forIn_cons]
    dsimp only
    unfold innerLoop
    split
    · split
      · rfl
      · exact ih acc
    · exact ih (acc ++ [p])

theorem outer_forIn_eq_outerLoop (acc : List (String × List Nat)) (vars : List XVar) :
    loopFinish
      (forIn (m := Id) vars
        (⟨none, acc⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                            (List (String × List Nat)))
        (fun v r =>
          if v.hasChunks = true then
            (do
              let r' ← forIn v.chunksizes
                (⟨none, r.snd⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                                    (List (String × List Nat)))
                (fun p r =>
                  match r.snd.lookup p.1 with
                  | some c' =>
                    if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                    else pure (ForInStep.yield ⟨none, r.snd⟩)
                  | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩))
              match r'.fst with
              | none   => pure (ForInStep.yield ⟨none, r'.snd⟩)
              | some a => pure (ForInStep.done ⟨some a, r'.snd⟩))
          else pure (ForInStep.yield ⟨none, r.snd⟩))) =
      outerLoop acc vars := by
  have hinner : ∀ (pairs : List (String × List Nat)) (a : List (String × List Nat)),
      (match innerLoop a pairs with
       | .ok acc' =>
           (forIn (m := Id) pairs
             (⟨none, a⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                               (List (String × List Nat)))
             (fun p r =>
               match r.snd.lookup p.1 with
               | some c' =>
                 if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                 else pure (ForInStep.yield ⟨none, r.snd⟩)
               | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩)))
             = ⟨none, acc'⟩
       | .error _ =>
           ∃ s, (forIn (m := Id) pairs
             (⟨none, a⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                               (List (String × List Nat)))
             (fun p r =>
               match r.snd.lookup p.1 with
               | some c' =>
                 if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                 else pure (ForInStep.yield ⟨none, r.snd⟩)
               | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩)))
             = ⟨some (Except.error ()), s⟩) := by
    intro pairs
    induction pairs with
    | nil => intro a; rfl
    | cons p ps ih =>
      intro a
      rw [List.forIn_cons]
      simp only [innerLoop]
      cases hl : a.lookup p.1 with
      | none => exact ih (a ++ [p])
      | some c' =>
        by_cases hc : c' ≠ p.2
        · simp only [if_pos hc]; exact ⟨a, rfl⟩
        · simp only [if_neg hc]; exact ih a
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    rw [List.forIn_cons]
    simp only [outerLoop]
    by_cases hv : v.hasChunks = true
    · simp only [hv, if_true]
      have := hinner v.chunksizes acc
      cases hIL : innerLoop acc v.chunksizes with
      | error e =>
        simp only [hIL] at this
        obtain ⟨s, hs⟩ := this
        rw [hs]
        rfl
      | ok acc' =>
        simp only [hIL] at this
        rw [this]
        exact ih acc'
    · simp only [Bool.not_eq_true] at hv
      simp only [hv, Bool.false_eq_true, if_false]
      exact ih acc

theorem impl_eq_outerLoop (vars : List XVar) :
    implementation_getChunksizes vars = outerLoop [] vars := by
  rw [← outer_forIn_eq_outerLoop]
  simp only [implementation_getChunksizes, Id.run, loopFinish, bind, pure]
  split <;> rename_i h <;> rw [h]

theorem innerLoop_eq_mergePairs (acc pairs : List (String × List Nat)) :
    innerLoop acc pairs = mergePairs acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [innerLoop, mergePairs, insertChunk]
    cases h : acc.lookup p.1 with
    | none => simp [ih]
    | some c' =>
      by_cases hc : c' = p.2
      · simp [hc, ih]
      · simp [hc]

theorem outerLoop_eq_mergeVars (acc : List (String × List Nat)) (vars : List XVar) :
    outerLoop acc vars = mergeVars vars acc := by
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    unfold outerLoop mergeVars
    cases h : v.hasChunks with
    | false => simp only [Bool.false_eq_true, if_false]; exact ih acc
    | true =>
      simp only [if_true]
      rw [innerLoop_eq_mergePairs]
      cases mergePairs acc v.chunksizes with
      | error e => rfl
      | ok acc' => exact ih acc'

theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  intro vars
  unfold problem_spec_getChunksizes
  rw [impl_eq_outerLoop, outerLoop_eq_mergeVars]

-- proof-end

#print axioms correct_getChunksizes
```

Prepatch bug re-encoded as an attack: `True`.

Real project root:. All verifications via scripts/lean_verify.sh (300s budget) run concurrently in 2 batches of 4.

SAME-SPEC: all 8 files (7 attacks + pos_control) verified same_spec==True against Solution.lean via swebench_unified.markers.same_spec + get_backend('lean') — spec regions (imports/axioms/pure/post-conditions) byte-identical; only the impl region edited. Each attack reuses the FULL original genuine proof (the strong proof that closes for the correct impl), not a weakened one — so a closing failure reflects a real behavioral divergence, not a lazy proof.

POSITIVE CONTROL: pos_control.lean = original correct impl. cmd: `bash scripts/lean_verify.sh <f>` -> EXIT=0. `#print axioms correct_getChunksizes` -> 'depends on axioms: [propext, Quot.sound]' — CLEAN (no sorryAx, no custom axioms).

### ATTACKS (each: cmd `bash scripts/lean_verify.sh <path>`):
- atk_1 never-reject/last-writer-wins (append always, no consistency check): EXIT=1 (proof error). behaviorally differs from mergeVars (see counterexample).
- atk_2 prepatch materialization side-effect bug (if !isDuckArray && materializeRaises then .error): EXIT=1. This is the recorded prepatch bug / GH6538 F2P scenario; provably outside spec on <false,[],false,true>.
- atk_3 boundary/off-by-one — skips the first variable: EXIT=1. differs on [<true,[(x,[1])]>].
- atk_4 control-flow-effect — ignores hasChunks, merges every variable's chunksizes: EXIT=1. differs on [<false,[(x,[1])]>].
- atk_5 ungrounded-oracle echo — always `return .ok []`: EXIT=1. differs on any chunked var.
- atk_6 partial-domain — rejects on ANY pre-existing dim even when block lengths agree: EXIT=1. differs on agreeing-duplicate.
- atk_7 order-effect — prepend instead of append (reverses first-seen order): EXIT=1. differs on two distinct dims.
All 7 wrong impls FAIL to verify (exit 1, genuine rewrite/unsolved-goals errors); only pos_control closes.

Step-2 trigger: NONE of the wrong impls produced a closing clean-axiom proof, so no faithful patch needed materializing and no run_resolve was executed (correctly — there is nothing to falsify). This is the expected outcome for an exact-equality spec.

A-LEG AUDIT (refinement.md + mapping.md): Solution.lean declares ZERO axiom/opaque (grep confirmed NONE). meta.json: axioms=[], deep_model_references=[], conf_skip=false. refinement.md 7-leg table: legs 3,4,7 = R (type refinements of observable Variable properties hasChunks/chunksizes/Frozen-view, pinned by G-CONF over 120004 inputs, seed 6721), legs 1,2,5,6 = I (empty acc, iteration, inconsistency-rejection, first-seen append all spelled out deeply). No kind-3 leg; no A-consumed / A-reference leg exists. The empty A-surface means there is no axiomatic latitude to smuggle a same-spec impl that maps to a non-resolving patch — the equivalence class is the singleton post-patch semantics, and the gold refined patch (v.data -> v._data) is that semantics.

VERDICT: SOUND. >=5 distinct attacks (7 total) run and same-spec-verified; positive control verifies with clean axioms; no attack closes; A-legs empty and correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
The spec is exact extensional equality to a TOTAL pure function: problem_spec_getChunksizes vars result := (result = mergeVars vars []). Any impl whose correct_* closes must equal mergeVars pointwise on every input, so the closing equivalence class is a single behavior (the post-patch, materialization-free reference semantics). No wrong impl closed; therefore no verify⇏correct gap exists to exhibit and no run_resolve was triggered. Discriminating inputs proving each attack differs from mergeVars: atk_2 (prepatch bug) on [<false,[],isDuck=false,matRaises=true>] returns .error while spec demands .ok []; atk_1 (never-reject) on [<true,[(x,[1])]>,<true,[(x,[2])]>] returns .ok[(x,[1]),(x,[2])] vs spec .error.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the chunk sizes of a collection of array-like variables.

Each variable in the collection may be *chunked*: if so it exposes, for each of
its named dimensions, the block length along that dimension. `get_chunksizes`
walks the collection and builds a single mapping from dimension name to block
length:

* a variable that is not chunked contributes nothing;
* a chunked variable contributes one entry per dimension; if a dimension has
  already been recorded with a *different* block length the collection has
  inconsistent chunking and the whole operation is rejected;
* recording a dimension whose block length already agrees with the stored value
  leaves the mapping unchanged.

The resulting mapping lists dimensions in the order they were first encountered.

Crucially, deciding whether a variable is chunked is a question about the
variable's chunk metadata only: it must be answerable by inspecting that
metadata and must never force the variable's contents to be loaded into memory.
The outcome therefore depends solely on each variable's chunk metadata, and is
the same whether or not loading a variable's contents would succeed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- variable is chunked, and the per-dimension block lengths it then exposes, are
-- observable properties of the variable supplied directly as inputs; the
-- accumulation and the inconsistency rejection are modeled deeply over those
-- inputs. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched observable properties of one array-like variable.

* `hasChunks` — whether the variable is chunked (answerable from chunk metadata
  alone, without loading the variable's contents);
* `chunksizes` — when chunked, the per-dimension block lengths, as
  `(dimension name, block lengths)` pairs in dimension order;
* `isDuckArray` — whether the variable already holds an in-place array handle;
* `materializeRaises` — whether forcing the variable's contents into memory
  would fail (e.g. an unreachable backing store).

`isDuckArray` and `materializeRaises` describe what happens if the variable's
contents are loaded; a correct computation of the chunk-size mapping never needs
them, and the specification below is deliberately independent of both. -/
structure XVar where
  hasChunks : Bool
  chunksizes : List (String × List Nat)
  isDuckArray : Bool
  materializeRaises : Bool

/-- Record one `(dimension, block lengths)` entry into the accumulated mapping.
A new dimension is appended (preserving first-seen order); a dimension already
present with the *same* block lengths leaves the mapping unchanged; a dimension
present with *different* block lengths makes the collection inconsistent. -/
def insertChunk (acc : List (String × List Nat)) (p : String × List Nat) :
    Except Unit (List (String × List Nat)) :=
  match acc.lookup p.1 with
  | some c' => if c' = p.2 then .ok acc else .error ()
  | none    => .ok (acc ++ [p])

/-- Fold a single chunked variable's entries into the accumulator, rejecting on
the first inconsistency. -/
def mergePairs : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match insertChunk acc p with
    | .error _ => .error ()
    | .ok acc' => mergePairs acc' ps

/-- The reference chunk-size mapping for a collection of variables, threaded
front-to-back. Non-chunked variables are skipped; chunked variables fold their
entries in, rejecting on the first inconsistency. Depends only on each
variable's chunk metadata (`hasChunks`, `chunksizes`). -/
def mergeVars : List XVar → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | [],      acc => .ok acc
  | v :: vs, acc =>
    if v.hasChunks then
      match mergePairs acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => mergeVars vs acc'
    else mergeVars vs acc
-- pure-end

-- post-conditions-start
/-- The collected mapping is exactly the reference fold over the variables'
chunk metadata: each non-chunked variable contributes nothing, each chunked
variable contributes its per-dimension block lengths, inconsistent block lengths
for the same dimension are rejected, and dimensions appear in first-seen order.
The outcome is independent of whether loading any variable's contents would
succeed. -/
def problem_spec_getChunksizes (vars : List XVar)
    (result : Except Unit (List (String × List Nat))) : Prop :=
  result = mergeVars vars []
-- post-conditions-end

-- impl-start
def implementation_getChunksizes (vars : List XVar) :
    Except Unit (List (String × List Nat)) := Id.run do
  let mut chunks : List (String × List Nat) := []
  for v in vars do
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks
-- impl-end


-- proof-start
/-- Collapse the `for`-loop's early-return state `⟨earlyReturn?, acc⟩` back into
the `Except` result: a pending early return propagates, otherwise the loop
succeeded with its accumulator. This mirrors the impl's final `match`. -/
def loopFinish
    (r : MProd (Option (Except Unit (List (String × List Nat))))
              (List (String × List Nat))) :
    Except Unit (List (String × List Nat)) :=
  match r.fst with
  | some e => e
  | none   => .ok r.snd

/-- Pure functional counterpart of the inner `for p in v.chunksizes` loop,
mirroring its early-return-on-inconsistency semantics. -/
def innerLoop : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match acc.lookup p.1 with
    | some c' => if c' ≠ p.2 then .error () else innerLoop acc ps
    | none    => innerLoop (acc ++ [p]) ps

/-- Pure functional counterpart of the outer `for v in vars` loop, threading the
accumulator and propagating the first inconsistency. -/
def outerLoop : List (String × List Nat) → List XVar →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, v :: vs =>
    if v.hasChunks then
      match innerLoop acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => outerLoop acc' vs
    else outerLoop acc vs

theorem inner_forIn_eq_innerLoop (acc pairs : List (String × List Nat)) :
    loopFinish
      (forIn (m := Id) pairs
        (⟨none, acc⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                            (List (String × List Nat)))
        (fun p r =>
          match r.snd.lookup p.1 with
          | some c' =>
            if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
            else pure (ForInStep.yield ⟨none, r.snd⟩)
          | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩))) =
      innerLoop acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [List.forIn_cons]
    dsimp only
    unfold innerLoop
    split
    · split
      · rfl
      · exact ih acc
    · exact ih (acc ++ [p])

theorem outer_forIn_eq_outerLoop (acc : List (String × List Nat)) (vars : List XVar) :
    loopFinish
      (forIn (m := Id) vars
        (⟨none, acc⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                            (List (String × List Nat)))
        (fun v r =>
          if v.hasChunks = true then
            (do
              let r' ← forIn v.chunksizes
                (⟨none, r.snd⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                                    (List (String × List Nat)))
                (fun p r =>
                  match r.snd.lookup p.1 with
                  | some c' =>
                    if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                    else pure (ForInStep.yield ⟨none, r.snd⟩)
                  | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩))
              match r'.fst with
              | none   => pure (ForInStep.yield ⟨none, r'.snd⟩)
              | some a => pure (ForInStep.done ⟨some a, r'.snd⟩))
          else pure (ForInStep.yield ⟨none, r.snd⟩))) =
      outerLoop acc vars := by
  have hinner : ∀ (pairs : List (String × List Nat)) (a : List (String × List Nat)),
      (match innerLoop a pairs with
       | .ok acc' =>
           (forIn (m := Id) pairs
             (⟨none, a⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                               (List (String × List Nat)))
             (fun p r =>
               match r.snd.lookup p.1 with
               | some c' =>
                 if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                 else pure (ForInStep.yield ⟨none, r.snd⟩)
               | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩)))
             = ⟨none, acc'⟩
       | .error _ =>
           ∃ s, (forIn (m := Id) pairs
             (⟨none, a⟩ : MProd (Option (Except Unit (List (String × List Nat))))
                               (List (String × List Nat)))
             (fun p r =>
               match r.snd.lookup p.1 with
               | some c' =>
                 if c' ≠ p.2 then pure (ForInStep.done ⟨some (Except.error ()), r.snd⟩)
                 else pure (ForInStep.yield ⟨none, r.snd⟩)
               | none => pure (ForInStep.yield ⟨none, r.snd ++ [p]⟩)))
             = ⟨some (Except.error ()), s⟩) := by
    intro pairs
    induction pairs with
    | nil => intro a; rfl
    | cons p ps ih =>
      intro a
      rw [List.forIn_cons]
      simp only [innerLoop]
      cases hl : a.lookup p.1 with
      | none => exact ih (a ++ [p])
      | some c' =>
        by_cases hc : c' ≠ p.2
        · simp only [if_pos hc]; exact ⟨a, rfl⟩
        · simp only [if_neg hc]; exact ih a
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    rw [List.forIn_cons]
    simp only [outerLoop]
    by_cases hv : v.hasChunks = true
    · simp only [hv, if_true]
      have := hinner v.chunksizes acc
      cases hIL : innerLoop acc v.chunksizes with
      | error e =>
        simp only [hIL] at this
        obtain ⟨s, hs⟩ := this
        rw [hs]
        rfl
      | ok acc' =>
        simp only [hIL] at this
        rw [this]
        exact ih acc'
    · simp only [Bool.not_eq_true] at hv
      simp only [hv, Bool.false_eq_true, if_false]
      exact ih acc

theorem impl_eq_outerLoop (vars : List XVar) :
    implementation_getChunksizes vars = outerLoop [] vars := by
  rw [← outer_forIn_eq_outerLoop]
  simp only [implementation_getChunksizes, Id.run, loopFinish, bind, pure]
  split <;> rename_i h <;> rw [h]

theorem innerLoop_eq_mergePairs (acc pairs : List (String × List Nat)) :
    innerLoop acc pairs = mergePairs acc pairs := by
  induction pairs generalizing acc with
  | nil => rfl
  | cons p ps ih =>
    rw [innerLoop, mergePairs, insertChunk]
    cases h : acc.lookup p.1 with
    | none => simp [ih]
    | some c' =>
      by_cases hc : c' = p.2
      · simp [hc, ih]
      · simp [hc]

theorem outerLoop_eq_mergeVars (acc : List (String × List Nat)) (vars : List XVar) :
    outerLoop acc vars = mergeVars vars acc := by
  induction vars generalizing acc with
  | nil => rfl
  | cons v vs ih =>
    unfold outerLoop mergeVars
    cases h : v.hasChunks with
    | false => simp only [Bool.false_eq_true, if_false]; exact ih acc
    | true =>
      simp only [if_true]
      rw [innerLoop_eq_mergePairs]
      cases mergePairs acc v.chunksizes with
      | error e => rfl
      | ok acc' => exact ih acc'

theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  intro vars
  unfold problem_spec_getChunksizes
  rw [impl_eq_outerLoop, outerLoop_eq_mergeVars]

-- proof-end

#print axioms correct_getChunksizes
```

Prepatch bug re-encoded as an attack: `True`.

Real project root:. All verifications via scripts/lean_verify.sh (300s budget) run concurrently in 2 batches of 4.

SAME-SPEC: all 8 files (7 attacks + pos_control) verified same_spec==True against Solution.lean via swebench_unified.markers.same_spec + get_backend('lean') — spec regions (imports/axioms/pure/post-conditions) byte-identical; only the impl region edited. Each attack reuses the FULL original genuine proof (the strong proof that closes for the correct impl), not a weakened one — so a closing failure reflects a real behavioral divergence, not a lazy proof.

POSITIVE CONTROL: pos_control.lean = original correct impl. cmd: `bash scripts/lean_verify.sh <f>` -> EXIT=0. `#print axioms correct_getChunksizes` -> 'depends on axioms: [propext, Quot.sound]' — CLEAN (no sorryAx, no custom axioms).

### ATTACKS (each: cmd `bash scripts/lean_verify.sh <path>`):
- atk_1 never-reject/last-writer-wins (append always, no consistency check): EXIT=1 (proof error). behaviorally differs from mergeVars (see counterexample).
- atk_2 prepatch materialization side-effect bug (if !isDuckArray && materializeRaises then .error): EXIT=1. This is the recorded prepatch bug / GH6538 F2P scenario; provably outside spec on <false,[],false,true>.
- atk_3 boundary/off-by-one — skips the first variable: EXIT=1. differs on [<true,[(x,[1])]>].
- atk_4 control-flow-effect — ignores hasChunks, merges every variable's chunksizes: EXIT=1. differs on [<false,[(x,[1])]>].
- atk_5 ungrounded-oracle echo — always `return .ok []`: EXIT=1. differs on any chunked var.
- atk_6 partial-domain — rejects on ANY pre-existing dim even when block lengths agree: EXIT=1. differs on agreeing-duplicate.
- atk_7 order-effect — prepend instead of append (reverses first-seen order): EXIT=1. differs on two distinct dims.
All 7 wrong impls FAIL to verify (exit 1, genuine rewrite/unsolved-goals errors); only pos_control closes.

Step-2 trigger: NONE of the wrong impls produced a closing clean-axiom proof, so no faithful patch needed materializing and no run_resolve was executed (correctly — there is nothing to falsify). This is the expected outcome for an exact-equality spec.

A-LEG AUDIT (refinement.md + mapping.md): Solution.lean declares ZERO axiom/opaque (grep confirmed NONE). meta.json: axioms=[], deep_model_references=[], conf_skip=false. refinement.md 7-leg table: legs 3,4,7 = R (type refinements of observable Variable properties hasChunks/chunksizes/Frozen-view, pinned by G-CONF over 120004 inputs, seed 6721), legs 1,2,5,6 = I (empty acc, iteration, inconsistency-rejection, first-seen append all spelled out deeply). No kind-3 leg; no A-consumed / A-reference leg exists. The empty A-surface means there is no axiomatic latitude to smuggle a same-spec impl that maps to a non-resolving patch — the equivalence class is the singleton post-patch semantics, and the gold refined patch (v.data -> v._data) is that semantics.

VERDICT: SOUND. >=5 distinct attacks (7 total) run and same-spec-verified; positive control verifies with clean axioms; no attack closes; A-legs empty and correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real post-patch callee). Checks performed:

1. Spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True. Axioms/pure/post-conditions regions are identical.
2. Proof valid: scripts/lean_verify.sh exits 0; `#print axioms correct_getChunksizes` = [propext, Quot.sound] — clean, no sorryAx. Proof is real.
3. G-CONF conformance_check.py passes (0 disagreements over 120004 inputs, seed 6721).

Modeled function = post-patch get_chunksizes(variables) (xarray/core/common.py, base cc183652). Verified real source at base_commit + patch.diff (v.data -> v._data). Spec reference is `mergeVars vars []`.

Per-behavior faithfulness vs real post-patch callee:
- Unchunked variable skipped: real `if hasattr(v._data,'chunks')` false -> skip; spec skips. Match.
- New dim: real `chunks[dim]=c` appends new dict key in insertion order; spec `++[p]` on lookup=none. Match (first-seen order preserved).
- Agreeing duplicate dim (across variables): real overwrites with equal value (no-op); spec ok acc. Match.
- Inconsistent dim (across variables): real `dim in chunks and c!=chunks[dim]` -> ValueError; spec `some c', c'!=p.2 -> error ()`. Match (error payload abstracted to Unit, R-refinement; F2P is raise-vs-return).
- Chunked variable with empty chunksizes: real empty for-loop; spec mergePairs acc [] = ok acc. Match.
- Materialization independence: post-patch reads _data (never forces .values); a chunked _data is always a duck array so Variable.chunksizes' internal self.data.chunks does not materialize. Spec is deliberately independent of isDuckArray/materializeRaises. Match — this is exactly the gold fix's semantics.

Only candidate divergence: duplicate dim KEYS WITHIN a single variable's chunksizes (e.g. [('x',[1]),('x',[2])]) would make the spec `error` while a Python for over dict.items() would end with the LAST value. But Variable.chunksizes is a Frozen dict with unique keys — this preimage is NOT realizable by any real Variable, so it is not a faithfulness defect. No realizable input diverges.

Conclusion: the spec is a faithful abstraction of the real post-patch callee; the modeling boundary (observables as inputs) is sound and the spec is not too strong on any realizable input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** spec_view hash ee35446f… matches recorded G-HYGIENE spec_view hash; same_spec(Solution, prepatch)=True (identical spec, impl/proof-only divergence). The gold edit is `hasattr(v.data,'chunks')` -> `hasattr(v._data,'chunks')`, i.e. read chunkedness from metadata without materializing. The PUBLIC problem_statement already discloses: the function get_chunksizes, the exact offending line `if hasattr(v.data,'chunks')` (in the traceback), that v.data -> self.values forces materialization/loads the whole array, and the stated expectation that accessing chunks should merely inspect metadata rather than load into memory. The spec view's operative requirements ('deciding whether a variable is chunked is a question about the variable's chunk metadata only ... must never force the variable's contents to be loaded'; 'the outcome is the same whether or not loading would succeed') are exactly this publicly-stated corrected behavior — legitimate specification, not disclosure beyond problem_statement. The spec view never names v.data/v._data, never reveals the private-attribute source-operand swap, and quotes no gold-patch specifics; isDuckArray/materializeRaises appear only as abstract observable inputs the spec is explicitly independent of. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
