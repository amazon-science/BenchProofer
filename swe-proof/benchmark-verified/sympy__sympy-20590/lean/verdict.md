# P2 adversarial audit — sympy__sympy-20590

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 8 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,11 +33,7 @@
 
 -- impl-start
 def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
+  let mut immutable : Bool := false
   for pins in otherLayers do
     immutable := immutable && pins
   return immutable
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,14 +33,7 @@
 
 -- impl-start
 def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
-  for pins in otherLayers do
-    immutable := immutable && pins
-  return immutable
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,13 +33,9 @@
 
 -- impl-start
 def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
+  let mut immutable : Bool := false
   for pins in otherLayers do
-    immutable := immutable && pins
+    immutable := immutable || pins
   return immutable
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,14 +33,13 @@
 
 -- impl-start
 def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
-  for pins in otherLayers do
-    immutable := immutable && pins
-  return immutable
+  match otherLayers with
+  | [] => return false
+  | _ =>
+    let mut immutable : Bool := true
+    for pins in otherLayers do
+      immutable := immutable && pins
+    return immutable
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,12 +33,8 @@
 
 -- impl-start
 def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
   let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
-  for pins in otherLayers do
+  for pins in otherLayers.dropLast do
     immutable := immutable && pins
   return immutable
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -33,14 +33,10 @@
 
 -- impl-start
 def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
   for pins in otherLayers do
-    immutable := immutable && pins
-  return immutable
+    if pins then
+      return true
+  return false
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,15 +32,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
-  for pins in otherLayers do
-    immutable := immutable && pins
-  return immutable
+def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=
+  allPin otherLayers
 -- impl-end
 
 -- proof-start
@@ -48,30 +41,5 @@
     problem_spec_immutableInstances otherLayers
       (implementation_immutableInstances otherLayers) := by
   intro otherLayers
-  unfold problem_spec_immutableInstances implementation_immutableInstances allPin
-  -- Helper: the cleaned `forIn` loop equals a `List.foldl` conjunction (Route B).
-  have helper : ∀ (xs : List LayerPins) (init : Bool),
-      Id.run (forIn xs init (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)))
-        = xs.foldl (fun r pins => r && pins) init := by
-    intro xs
-    induction xs with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
-  -- Helper: the fold over the conjunction equals `init && all`.
-  have foldl_all : ∀ (xs : List LayerPins) (init : Bool),
-      xs.foldl (fun r pins => r && pins) init = (init && xs.all (fun b => b)) := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp
-    | cons a as ih =>
-      intro init
-      rw [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
-  -- Bridge the desugared loop body to the cleaned one (definitional).
-  show Id.run (forIn otherLayers true
-      (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))) = _
-  have hbody : (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))
-      = (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)) := rfl
-  rw [hbody, helper, foldl_all, Bool.true_and]
+  rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,15 +32,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
-  -- The layer under fix now pins its instance memory layout to a fixed attribute
-  -- set, so it contributes no per-instance attribute dictionary.
-  let mut immutable : Bool := true
-  -- Fold the conjunction over every remaining ancestry layer: a single layer that
-  -- leaves its layout open reopens the attribute dictionary for the instance.
-  for pins in otherLayers do
-    immutable := immutable && pins
-  return immutable
+def implementation_immutableInstances (otherLayers : List LayerPins) : Bool :=
+  !(allPin otherLayers)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the instance-layout rule is a
-- pure fold over the type's ancestry layers, modeled DEEPLY below (no outside
-- callee is invoked, hence no consumed axiom and no A-reference). The proof agent
-- may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- One ancestry layer of a type contributes a per-instance attribute dictionary
unless it pins its instance memory layout to a closed, predeclared attribute set.
`b = true` means the layer pins its layout (adds no attribute dictionary);
`b = false` means it leaves the layout open (so instances would gain an attribute
dictionary, i.e. become freely mutable). -/
abbrev LayerPins := Bool

/-- An instance is immutable (carries no per-instance attribute dictionary) iff
EVERY ancestry layer pins its memory layout. This is the conjunction-fold of the
per-layer pinning flags. -/
def allPin (layers : List LayerPins) : Bool := layers.all (fun b => b)
-- pure-end

-- post-conditions-start
/-- Given the layout-pinning flags of the ancestry layers (`otherLayers`), the
instance is immutable (`result = true`) exactly when all of those layers pin
their memory layout. The result is a single boolean, fully determined by the
inputs (frame: nothing is left unconstrained). -/
def problem_spec_immutableInstances (otherLayers : List LayerPins) (result : Bool) : Prop :=
  result = allPin otherLayers
-- post-conditions-end

-- impl-start
def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
  -- The layer under fix now pins its instance memory layout to a fixed attribute
  -- set, so it contributes no per-instance attribute dictionary.
  let mut immutable : Bool := true
  -- Fold the conjunction over every remaining ancestry layer: a single layer that
  -- leaves its layout open reopens the attribute dictionary for the instance.
  for pins in otherLayers do
    immutable := immutable && pins
  return immutable
-- impl-end

-- proof-start
theorem correct_immutableInstances : ∀ otherLayers : List LayerPins,
    problem_spec_immutableInstances otherLayers
      (implementation_immutableInstances otherLayers) := by
  intro otherLayers
  unfold problem_spec_immutableInstances implementation_immutableInstances allPin
  -- Helper: the cleaned `forIn` loop equals a `List.foldl` conjunction (Route B).
  have helper : ∀ (xs : List LayerPins) (init : Bool),
      Id.run (forIn xs init (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)))
        = xs.foldl (fun r pins => r && pins) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
  -- Helper: the fold over the conjunction equals `init && all`.
  have foldl_all : ∀ (xs : List LayerPins) (init : Bool),
      xs.foldl (fun r pins => r && pins) init = (init && xs.all (fun b => b)) := by
    intro xs
    induction xs with
    | nil => intro init; simp
    | cons a as ih =>
      intro init
      rw [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
  -- Bridge the desugared loop body to the cleaned one (definitional).
  show Id.run (forIn otherLayers true
      (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))) = _
  have hbody : (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))
      = (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)) := rfl
  rw [hbody, helper, foldl_all, Bool.true_and]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_immutableInstances otherLayers result := (result = allPin otherLayers) — a TOTAL, deterministic, tight functional spec (allPin = List.all id). Any impl satisfying correct_immutableInstances must equal allPin on EVERY input, so genuinely-wrong impls cannot close a clean-axiom proof. Refinement has NO A-legs (G-AX=skip; the CPython instance-layout rule is modeled deeply as a pure conjunction-fold, no repo callee invoked), so the A-leg concern reduces to model<->patch fidelity, which holds (see resolve below). refinement.md legs audited: row1=R (patched mixin layer pins layout -> init true), rows2-4=I; no A-consumed/A-reference, NO kind-3 (changed-inexpressible) op.

SAME_SPEC: all 8 attacks + pos_gold return same_spec=True (only impl+proof regions edited; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec with lean backend.

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <file>):
- pos_gold.lean: EXIT 0 (verifies); #print axioms correct_immutableInstances => depends on [propext, Quot.sound] (clean/standard). POSITIVE CONTROL PASSES.
- atk_1.lean (prepatch bug, init=false; partial/pre-patch): EXIT 1, unsolved goal ('show' tactic failed) — PREPATCH BUG REPRODUCED under the real proof.
- atk_2.lean (constant true): EXIT 1.
- atk_3.lean (OR-fold / any-pin instead of all-pin): EXIT 1.
- atk_4.lean (partial-domain: empty list special-cased to false; allPin []=true): EXIT 1.
- atk_5.lean (boundary off-by-one: fold over dropLast, ignores last layer): EXIT 1.
- atk_6.lean (control-flow effect: early-return true on first pinned layer): EXIT 1.
- atk_8.lean (ungrounded negation: !(allPin otherLayers)): EXIT 1.
- atk_7.lean (ECHO / ungrounded-oracle: impl = allPin otherLayers, proof by rfl): EXIT 0 (verifies); #print axioms => 'does not depend on any axioms' (clean). This echoes the exact gold behavior.

### RESOLVE (protocol step 2 — every verifying same-spec impl's faithful patch RUN through official harness):
- atk_7 (echo) computes exactly allPin otherLayers = the gold behavior, so its faithful refined patch IS the gold patch (add empty __slots__=() to Printable mixin). Executed: swebench_unified.harness.run_resolve('sympy__sympy-20590', <gold patch>, timeout=1200, retries=1) => RESOLVED: True, COMPLETED: True, note='resolved'. Docker oracle active (swe_bench_verified, style=swebench). So the echo is NOT a weakness (verify=>correct holds for it) — consistent with the G-PANEL-1/eq echo policy (a resolving echo of the gold is not a spec weakness).

CONCLUSION: No impl with a closing clean-axiom proof has a materialized faithful patch that fails to resolve. All 7 genuinely-wrong same-spec impls FAIL verification; the only verifying same-spec impls are the gold and a gold-equivalent echo whose faithful patch RESOLVES. Spec is tight (total functional equality). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 8 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the instance-layout rule is a
-- pure fold over the type's ancestry layers, modeled DEEPLY below (no outside
-- callee is invoked, hence no consumed axiom and no A-reference). The proof agent
-- may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- One ancestry layer of a type contributes a per-instance attribute dictionary
unless it pins its instance memory layout to a closed, predeclared attribute set.
`b = true` means the layer pins its layout (adds no attribute dictionary);
`b = false` means it leaves the layout open (so instances would gain an attribute
dictionary, i.e. become freely mutable). -/
abbrev LayerPins := Bool

/-- An instance is immutable (carries no per-instance attribute dictionary) iff
EVERY ancestry layer pins its memory layout. This is the conjunction-fold of the
per-layer pinning flags. -/
def allPin (layers : List LayerPins) : Bool := layers.all (fun b => b)
-- pure-end

-- post-conditions-start
/-- Given the layout-pinning flags of the ancestry layers (`otherLayers`), the
instance is immutable (`result = true`) exactly when all of those layers pin
their memory layout. The result is a single boolean, fully determined by the
inputs (frame: nothing is left unconstrained). -/
def problem_spec_immutableInstances (otherLayers : List LayerPins) (result : Bool) : Prop :=
  result = allPin otherLayers
-- post-conditions-end

-- impl-start
def implementation_immutableInstances (otherLayers : List LayerPins) : Bool := Id.run do
  -- The layer under fix now pins its instance memory layout to a fixed attribute
  -- set, so it contributes no per-instance attribute dictionary.
  let mut immutable : Bool := true
  -- Fold the conjunction over every remaining ancestry layer: a single layer that
  -- leaves its layout open reopens the attribute dictionary for the instance.
  for pins in otherLayers do
    immutable := immutable && pins
  return immutable
-- impl-end

-- proof-start
theorem correct_immutableInstances : ∀ otherLayers : List LayerPins,
    problem_spec_immutableInstances otherLayers
      (implementation_immutableInstances otherLayers) := by
  intro otherLayers
  unfold problem_spec_immutableInstances implementation_immutableInstances allPin
  -- Helper: the cleaned `forIn` loop equals a `List.foldl` conjunction (Route B).
  have helper : ∀ (xs : List LayerPins) (init : Bool),
      Id.run (forIn xs init (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)))
        = xs.foldl (fun r pins => r && pins) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih]; rfl
  -- Helper: the fold over the conjunction equals `init && all`.
  have foldl_all : ∀ (xs : List LayerPins) (init : Bool),
      xs.foldl (fun r pins => r && pins) init = (init && xs.all (fun b => b)) := by
    intro xs
    induction xs with
    | nil => intro init; simp
    | cons a as ih =>
      intro init
      rw [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]
  -- Bridge the desugared loop body to the cleaned one (definitional).
  show Id.run (forIn otherLayers true
      (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))) = _
  have hbody : (fun pins r => (do pure PUnit.unit; pure (ForInStep.yield (r && pins)) : Id _))
      = (fun pins r => (pure (ForInStep.yield (r && pins)) : Id _)) := rfl
  rw [hbody, helper, foldl_all, Bool.true_and]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_immutableInstances otherLayers result := (result = allPin otherLayers) — a TOTAL, deterministic, tight functional spec (allPin = List.all id). Any impl satisfying correct_immutableInstances must equal allPin on EVERY input, so genuinely-wrong impls cannot close a clean-axiom proof. Refinement has NO A-legs (G-AX=skip; the CPython instance-layout rule is modeled deeply as a pure conjunction-fold, no repo callee invoked), so the A-leg concern reduces to model<->patch fidelity, which holds (see resolve below). refinement.md legs audited: row1=R (patched mixin layer pins layout -> init true), rows2-4=I; no A-consumed/A-reference, NO kind-3 (changed-inexpressible) op.

SAME_SPEC: all 8 attacks + pos_gold return same_spec=True (only impl+proof regions edited; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec with lean backend.

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <file>):
- pos_gold.lean: EXIT 0 (verifies); #print axioms correct_immutableInstances => depends on [propext, Quot.sound] (clean/standard). POSITIVE CONTROL PASSES.
- atk_1.lean (prepatch bug, init=false; partial/pre-patch): EXIT 1, unsolved goal ('show' tactic failed) — PREPATCH BUG REPRODUCED under the real proof.
- atk_2.lean (constant true): EXIT 1.
- atk_3.lean (OR-fold / any-pin instead of all-pin): EXIT 1.
- atk_4.lean (partial-domain: empty list special-cased to false; allPin []=true): EXIT 1.
- atk_5.lean (boundary off-by-one: fold over dropLast, ignores last layer): EXIT 1.
- atk_6.lean (control-flow effect: early-return true on first pinned layer): EXIT 1.
- atk_8.lean (ungrounded negation: !(allPin otherLayers)): EXIT 1.
- atk_7.lean (ECHO / ungrounded-oracle: impl = allPin otherLayers, proof by rfl): EXIT 0 (verifies); #print axioms => 'does not depend on any axioms' (clean). This echoes the exact gold behavior.

### RESOLVE (protocol step 2 — every verifying same-spec impl's faithful patch RUN through official harness):
- atk_7 (echo) computes exactly allPin otherLayers = the gold behavior, so its faithful refined patch IS the gold patch (add empty __slots__=() to Printable mixin). Executed: swebench_unified.harness.run_resolve('sympy__sympy-20590', <gold patch>, timeout=1200, retries=1) => RESOLVED: True, COMPLETED: True, note='resolved'. Docker oracle active (swe_bench_verified, style=swebench). So the echo is NOT a weakness (verify=>correct holds for it) — consistent with the G-PANEL-1/eq echo policy (a resolving echo of the gold is not a spec weakness).

CONCLUSION: No impl with a closing clean-axiom proof has a materialized faithful patch that fails to resolve. All 7 genuinely-wrong same-spec impls FAIL verification; the only verifying same-spec impls are the gold and a gold-equivalent echo whose faithful patch RESOLVES. Spec is tight (total functional equality). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True via LeanBackend); only impl/proof differ between Solution.lean and Solution_prepatch.lean. Solution.lean compiles (lean_verify exit 0) and #print axioms correct_immutableInstances = [propext, Quot.sound] — no sorryAx, proof is genuine. The modeled function problem_spec_immutableInstances(otherLayers, result) := result = allPin otherLayers faithfully captures the real CPython instance-layout rule (patch adds __slots__=() to the printing mixin so an instance carries __dict__ iff some ancestry layer leaves its layout open). conformance_check.py exercises the ACTUAL CPython semantics — dynamically building type() class chains with/without __slots__=() and observing hasattr(inst,'__dict__') — over 120,008 configs with 0 disagreements; the oracle is non-trivial, not tautological. Independent re-fuzz (300k random configs, seed 999, list lengths 0..20) also produced 0 divergences between model all(otherLayers) and real CPython. No input found where the spec disagrees with the real repo behavior; the spec is not too strong. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (consumer projection: imports + axioms + pure + post-conditions regions; impl and proof are ELIDED) contains only an abstract model: `LayerPins := Bool`, `allPin`, and `problem_spec_immutableInstances result = allPin otherLayers`, with prose describing 'an ancestry layer pins its memory layout to a closed, predeclared attribute set'. Mechanical leak.py screen passes (verified via leakage.screen over spec_view with the frozen row: passed=True, no failures).

Semantic check against the PUBLIC problem_statement only (not hints_text): the public statement already establishes the entire abstraction the spec uses — Symbol instances gained `__dict__` since 1.7, `__slots__` was involved, and the reporter's own hypothesis that 'some parent class accidentally stopped defining __slots__' defeating intended immutability. The spec view is a faithful paraphrase of that public premise at the same abstraction level.

The spec view does NOT reveal any gold-edit localization beyond the public statement: it does not name the patched file (_print_helpers.py) or module path, does not name the patched class/symbol (Printable/DefaultPrinting), does not reproduce the gold-diff line (`__slots__ = ()`), carries no diff markers, and no bug/fix narration in the visible regions. The hint-derived specifics that actually localize the edit (Basic inherits DefaultPrinting, EvalfMixin has __slots__ = (), the class to patch) come from hints_text and are absent from the spec view.

The edit-localizing comment ('The layer under fix now pins its instance memory layout...') and the discriminating init-true-vs-false clause live in the IMPL/PROOF regions and refinement.md, which are elided from the consumer view (leak.py screens solution_src()'s spec_view projection only). No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
