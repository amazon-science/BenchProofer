# P2 adversarial audit — matplotlib__matplotlib-24026

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The spec's two ensures fully pin both observables, so verify => behaviorally-gold => resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,11 +69,8 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
     let assigned := (List.range layerCount).map
-      (fun (i : Nat) => colors[i % colors.length]!)
+      (fun (i : Nat) => colors[(i + 1) % colors.length]!)
     return assigned
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,11 +69,8 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
-    let assigned := (List.range layerCount).map
-      (fun (i : Nat) => colors[i % colors.length]!)
+    let assigned := ((List.range layerCount).map
+      (fun (i : Nat) => colors[i % colors.length]!)).reverse
     return assigned
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,11 +69,8 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
     let assigned := (List.range layerCount).map
-      (fun (i : Nat) => colors[i % colors.length]!)
+      (fun (_i : Nat) => colors[0]!)
     return assigned
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,11 +69,8 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
     let assigned := (List.range layerCount).map
-      (fun (i : Nat) => colors[i % colors.length]!)
+      (fun (i : Nat) => colors[i]!)
     return assigned
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,9 +69,7 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
+    sharedCycle := colors
     let assigned := (List.range layerCount).map
       (fun (i : Nat) => colors[i % colors.length]!)
     return assigned
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,10 +69,7 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
-    let assigned := (List.range layerCount).map
+    let assigned := (List.range (layerCount - 1)).map
       (fun (i : Nat) => colors[i % colors.length]!)
     return assigned
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,12 +69,7 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
-    let assigned := (List.range layerCount).map
-      (fun (i : Nat) => colors[i % colors.length]!)
-    return assigned
+    return cyclicColors colors layerCount
     -- impl-end
 
 prove_correct selectLayerColors by
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The colour-selection rule under spec is modeled
@@ -69,9 +69,7 @@
   ensures out = cyclicColors colors layerCount
   do
     -- impl-start
-    -- Repeat the supplied colours over the areas using a private cyclic walk of
-    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
-    -- it is handed back exactly as received.
+    sharedCycle := sharedCycle
     let assigned := (List.range layerCount).map
       (fun (i : Nat) => colors[i % colors.length]!)
     return assigned
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The colour-selection rule under spec is modeled
--  DEEPLY in the `pure` region — `cyclicColors` IS the repetition of a finite
--  colour sequence, an A-reference validated == the standard-library finite
--  cyclic iterator by axiom_check.py (G-AX). No consumed axiom borrows
--  soundness from an outside contract; the shared-state frame is modeled
--  directly as a `mut` parameter pinned to its entry value. See refinement.md
--  §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The colour assigned to each of `layerCount` stacked areas, drawn in order
   from a finite, non-empty sequence of requested colours that is repeated as
   often as needed: area `i` takes colour `colors[i % colors.length]`. With
   exactly as many colours as areas this is the identity ordering; with fewer
   colours than areas the sequence wraps around from the beginning, and with
   more colours than areas the surplus is simply unused. The result has one
   colour per area, in area order. -/
def cyclicColors (colors : List String) (layerCount : Nat) : List String :=
  (List.range layerCount).map (fun (i : Nat) => colors[i % colors.length]!)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the per-area fill colours for a stack of `layerCount` filled areas
   when an explicit, non-empty list of `colors` is supplied, and report the
   colour each area is filled with, in area order.

   The guarantees pin the two behaviours the request demands:

   - the colours are drawn solely from the supplied list, repeated cyclically:
     `out = cyclicColors colors layerCount` (exactly `layerCount` colours, area
     `i` taking `colors[i % colors.length]`). The choice is grounded entirely in
     the caller's own `colors`; it does not depend on, and is not drawn from,
     any colour source shared with other artists on the same axes.

   - the surrounding shared colour-cycle state is read-only: whatever colour
     sequence the axes would hand to its OTHER artists must be exactly the same
     after this operation as before it. `sharedCycle` carries that shared
     colour-cycle state; it is declared `mut` (the long-standing shape of this
     code reaches for the shared cycle as the place to record colours) but its
     post-state is pinned EXACTLY to its entry value
     (`ensures sharedCycle = sharedCycleOld`, directive 5). This is precisely the
     guarantee the use-case needs: colours stay synchronised across the other
     plot types drawn on the same axes, because filling these areas neither
     advances nor replaces the shared cycle.

   `colors` is read-only (not `mut`) and must be non-empty so the cyclic choice
   is well defined. A single colour specification is carried as a `String` (a
   named colour, hex string, or cycle reference such as `"C2"`); the operation
   only ever copies and reorders these tokens, never interpreting them, so an
   ordered `List String` carrier is faithful (mapping.md §2). -/
method selectLayerColors (mut sharedCycle : List String) (colors : List String)
    (layerCount : Nat) return (out : List String)
  require colors.length > 0
  ensures sharedCycle = sharedCycleOld
  ensures out = cyclicColors colors layerCount
  do
    -- impl-start
    -- Repeat the supplied colours over the areas using a private cyclic walk of
    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
    -- it is handed back exactly as received.
    let assigned := (List.range layerCount).map
      (fun (i : Nat) => colors[i % colors.length]!)
    return assigned
    -- impl-end

prove_correct selectLayerColors by
  loom_solve
  simp [cyclicColors]
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL. same_spec(velvet)=True for pos_control + atk_1..8 (verified via swebench_unified.markers.same_spec). Only the impl region was edited; axioms/pure/pre/post byte-identical.

SPEC SHAPE: method selectLayerColors (mut sharedCycle) (colors) (layerCount) with require colors.length>0; ensures sharedCycle = sharedCycleOld (frame, directive-5); ensures out = cyclicColors colors layerCount = (List.range layerCount).map (fun i => colors[i % colors.length]!). BOTH observables (the returned per-area colour list AND the shared-cycle frame) are EXACTLY pinned by the two ensures — no freedom is left to a verifying impl, so verify => behaviorally identical to the gold on both observables.

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>; run concurrently <=4/batch):
- pos_control.lean -> EXIT 0 (VERIFIES). Correct gold-faithful impl = positive control.
- atk_1 off-by-one cyclic colors[(i+1)%len] -> EXIT 1. Unsolved goal: out clause (forall a<layerCount, colors[(a+1)%len] = colors[a%len]). REJECTED.
- atk_2 reversed output order (.reverse) -> EXIT 1. REJECTED (out clause).
- atk_3 all colours = colors[0]! -> EXIT 1. REJECTED (out clause; wrong when >1 colour).
- atk_4 no modulo, colors[i]! -> EXIT 1. Unsolved goal: forall a<layerCount, colors[a] = colors[a%len]. REJECTED (boundary/out-of-domain).
- atk_5 PREPATCH BUG: sharedCycle := colors then correct output -> EXIT 1. Unsolved goal exactly 'colors = sharedCycleOld' (the frame/G-DIFF discriminator). PREPATCH REPRODUCED — the frame clause catches the shared-cycle clobber, matching Solution_prepatch.lean and refinement.md B/§A4.
- atk_6 truncate by one (List.range (layerCount-1)) -> EXIT 1. REJECTED (out clause; partial domain).
- atk_7 echo: `return cyclicColors colors layerCount` -> EXIT 1 but ONLY a proof-script artifact ('77:2: error: No goals to be solved' — loom_solve already closed the goal so the trailing `simp [cyclicColors]` has nothing to solve). NOT a spec weakness; impl is gold-equivalent.
- atk_8 `sharedCycle := sharedCycle` (no-op) + correct cyclic output -> EXIT 0 (VERIFIES). Behaviorally gold-equivalent (self-assign is a no-op, output = cyclicColors).

RESOLVE (the required verify=>correct check): the ONLY verifying same-spec attack is atk_8 (gold-equivalent). Materialized its faithful patch (faithful_gold.diff = gold patch verbatim, since atk_8 is behaviorally the gold) and ran the OFFICIAL harness: run_resolve('matplotlib__matplotlib-24026', patch, timeout=1800, retries=0) => RESOLVED=True COMPLETED=True NOTE=resolved. So the verifying wrong-shaped-but-correct impl RESOLVES. No verifying impl fails to resolve.

A-LEG AUDIT (my focus): refinement.md legs are R / A-reference / I only — NO consumed axioms, NO kind-3. The single A-reference is cyclicColors == itertools.cycle consumption. Ran axiom_check.py (G-AX) with the repo python: EXIT 0, 'sound on 12 boundary + 20000 fuzz cases'. The deep model area i -> colors[i%len] exactly matches [next(itertools.cycle(colors)) for _ in range(layerCount)]. The A4 shared-cycle frame borrows no callee contract; its real soundness is checked end-to-end by G-CONF (recorded pass, 100007 inputs, 0 disagreements + 3000 control-axes frame checks). Model<->patch correspondence in mapping.md is faithful (colour-spec token -> String opaque; y.shape[0] -> layerCount; range -> List.range; itertools.cycle -> cyclicColors; axes shared cycle -> mut sharedCycle pinned).

CONCLUSION: >=6 distinct wrong impls (partial-domain atk_6, boundary atk_4, off-by-one atk_1, reorder/control-flow atk_2, constant atk_3, prepatch-frame atk_5) all fail to verify, each on the precise pinned observable. The prepatch bug is reproduced (atk_5). The only verifying same-spec impl beyond the control (atk_8) is gold-equivalent and its faithful patch RESOLVES under the official harness. verify => correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The spec's two ensures fully pin both observables, so verify => behaviorally-gold => resolve.
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

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The colour-selection rule under spec is modeled
--  DEEPLY in the `pure` region — `cyclicColors` IS the repetition of a finite
--  colour sequence, an A-reference validated == the standard-library finite
--  cyclic iterator by axiom_check.py (G-AX). No consumed axiom borrows
--  soundness from an outside contract; the shared-state frame is modeled
--  directly as a `mut` parameter pinned to its entry value. See refinement.md
--  §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The colour assigned to each of `layerCount` stacked areas, drawn in order
   from a finite, non-empty sequence of requested colours that is repeated as
   often as needed: area `i` takes colour `colors[i % colors.length]`. With
   exactly as many colours as areas this is the identity ordering; with fewer
   colours than areas the sequence wraps around from the beginning, and with
   more colours than areas the surplus is simply unused. The result has one
   colour per area, in area order. -/
def cyclicColors (colors : List String) (layerCount : Nat) : List String :=
  (List.range layerCount).map (fun (i : Nat) => colors[i % colors.length]!)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the per-area fill colours for a stack of `layerCount` filled areas
   when an explicit, non-empty list of `colors` is supplied, and report the
   colour each area is filled with, in area order.

   The guarantees pin the two behaviours the request demands:

   - the colours are drawn solely from the supplied list, repeated cyclically:
     `out = cyclicColors colors layerCount` (exactly `layerCount` colours, area
     `i` taking `colors[i % colors.length]`). The choice is grounded entirely in
     the caller's own `colors`; it does not depend on, and is not drawn from,
     any colour source shared with other artists on the same axes.

   - the surrounding shared colour-cycle state is read-only: whatever colour
     sequence the axes would hand to its OTHER artists must be exactly the same
     after this operation as before it. `sharedCycle` carries that shared
     colour-cycle state; it is declared `mut` (the long-standing shape of this
     code reaches for the shared cycle as the place to record colours) but its
     post-state is pinned EXACTLY to its entry value
     (`ensures sharedCycle = sharedCycleOld`, directive 5). This is precisely the
     guarantee the use-case needs: colours stay synchronised across the other
     plot types drawn on the same axes, because filling these areas neither
     advances nor replaces the shared cycle.

   `colors` is read-only (not `mut`) and must be non-empty so the cyclic choice
   is well defined. A single colour specification is carried as a `String` (a
   named colour, hex string, or cycle reference such as `"C2"`); the operation
   only ever copies and reorders these tokens, never interpreting them, so an
   ordered `List String` carrier is faithful (mapping.md §2). -/
method selectLayerColors (mut sharedCycle : List String) (colors : List String)
    (layerCount : Nat) return (out : List String)
  require colors.length > 0
  ensures sharedCycle = sharedCycleOld
  ensures out = cyclicColors colors layerCount
  do
    -- impl-start
    -- Repeat the supplied colours over the areas using a private cyclic walk of
    -- `colors`; the shared colour-cycle state `sharedCycle` is never written, so
    -- it is handed back exactly as received.
    let assigned := (List.range layerCount).map
      (fun (i : Nat) => colors[i % colors.length]!)
    return assigned
    -- impl-end

prove_correct selectLayerColors by
  loom_solve
  simp [cyclicColors]
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL. same_spec(velvet)=True for pos_control + atk_1..8 (verified via swebench_unified.markers.same_spec). Only the impl region was edited; axioms/pure/pre/post byte-identical.

SPEC SHAPE: method selectLayerColors (mut sharedCycle) (colors) (layerCount) with require colors.length>0; ensures sharedCycle = sharedCycleOld (frame, directive-5); ensures out = cyclicColors colors layerCount = (List.range layerCount).map (fun i => colors[i % colors.length]!). BOTH observables (the returned per-area colour list AND the shared-cycle frame) are EXACTLY pinned by the two ensures — no freedom is left to a verifying impl, so verify => behaviorally identical to the gold on both observables.

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>; run concurrently <=4/batch):
- pos_control.lean -> EXIT 0 (VERIFIES). Correct gold-faithful impl = positive control.
- atk_1 off-by-one cyclic colors[(i+1)%len] -> EXIT 1. Unsolved goal: out clause (forall a<layerCount, colors[(a+1)%len] = colors[a%len]). REJECTED.
- atk_2 reversed output order (.reverse) -> EXIT 1. REJECTED (out clause).
- atk_3 all colours = colors[0]! -> EXIT 1. REJECTED (out clause; wrong when >1 colour).
- atk_4 no modulo, colors[i]! -> EXIT 1. Unsolved goal: forall a<layerCount, colors[a] = colors[a%len]. REJECTED (boundary/out-of-domain).
- atk_5 PREPATCH BUG: sharedCycle := colors then correct output -> EXIT 1. Unsolved goal exactly 'colors = sharedCycleOld' (the frame/G-DIFF discriminator). PREPATCH REPRODUCED — the frame clause catches the shared-cycle clobber, matching Solution_prepatch.lean and refinement.md B/§A4.
- atk_6 truncate by one (List.range (layerCount-1)) -> EXIT 1. REJECTED (out clause; partial domain).
- atk_7 echo: `return cyclicColors colors layerCount` -> EXIT 1 but ONLY a proof-script artifact ('77:2: error: No goals to be solved' — loom_solve already closed the goal so the trailing `simp [cyclicColors]` has nothing to solve). NOT a spec weakness; impl is gold-equivalent.
- atk_8 `sharedCycle := sharedCycle` (no-op) + correct cyclic output -> EXIT 0 (VERIFIES). Behaviorally gold-equivalent (self-assign is a no-op, output = cyclicColors).

RESOLVE (the required verify=>correct check): the ONLY verifying same-spec attack is atk_8 (gold-equivalent). Materialized its faithful patch (faithful_gold.diff = gold patch verbatim, since atk_8 is behaviorally the gold) and ran the OFFICIAL harness: run_resolve('matplotlib__matplotlib-24026', patch, timeout=1800, retries=0) => RESOLVED=True COMPLETED=True NOTE=resolved. So the verifying wrong-shaped-but-correct impl RESOLVES. No verifying impl fails to resolve.

A-LEG AUDIT (my focus): refinement.md legs are R / A-reference / I only — NO consumed axioms, NO kind-3. The single A-reference is cyclicColors == itertools.cycle consumption. Ran axiom_check.py (G-AX) with the repo python: EXIT 0, 'sound on 12 boundary + 20000 fuzz cases'. The deep model area i -> colors[i%len] exactly matches [next(itertools.cycle(colors)) for _ in range(layerCount)]. The A4 shared-cycle frame borrows no callee contract; its real soundness is checked end-to-end by G-CONF (recorded pass, 100007 inputs, 0 disagreements + 3000 control-axes frame checks). Model<->patch correspondence in mapping.md is faithful (colour-spec token -> String opaque; y.shape[0] -> layerCount; range -> List.range; itertools.cycle -> cyclicColors; axes shared cycle -> mut sharedCycle pinned).

CONCLUSION: >=6 distinct wrong impls (partial-domain atk_6, boundary atk_4, off-by-one atk_1, reorder/control-flow atk_2, constant atk_3, prepatch-frame atk_5) all fail to verify, each on the precise pinned observable. The prepatch bug is reproduced (atk_5). The only verifying same-spec impl beyond the control (atk_8) is gold-equivalent and its faithful patch RESOLVES under the official harness. verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on velvet bundle matplotlib__matplotlib-24026 (spec: method selectLayerColors; modeled function cyclicColors + directive-5 frame sharedCycle = sharedCycleOld).

### Spec integrity
- same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True: the frozen spec region (imports/axioms/pure/pre/post/method signature+contracts) is byte-identical; impl and proof are the only differences. Spec well-formed.
- lean_verify.sh on Solution.lean: EXIT 0 (verifies).

REAL-REPO ORACLE: base_commit 14c96b510e, gold patch applied (matches installed matplotlib 3.6.3 which already carries the fix: itertools.cycle branch present, set_prop_cycle removed). Verified installed stackplot source contains 'itertools.cycle' and not 'set_prop_cycle'.

VALUE LEG (ensures out = cyclicColors colors layerCount, i.e. area i -> colors[i % len(colors)]):
- Differential test: model (colors[i%n] -> to_rgba) vs oracle (real patched ax.stackplot per-PolyCollection facecolor) over 4008 cases = 8 boundary cases (issue repro ['C2','C3','C4'],3; F2P ['C0','C1','C2'],3; single-colour wrap; fewer-than-areas wrap; more-than-areas surplus; hex/named/tab/CN tokens) + 4000 fuzzed (colors, layerCount) over a 15-spec palette, layerCount 1..10.
- Result: 0 disagreements. The deep model exactly reproduces itertools.cycle(colors) consumption; the A-reference G-AX validated is sound on the observable RGBA the F2P image test renders.

### FRAME LEG (ensures sharedCycle = sharedCycleOld):
- Control-axes differential test over 2000 fuzzed cases: after stackplot(colors=...) on a test axes vs an untouched control axes (both cycle-aligned by one prior C0 line), the next colour each axes hands an ordinary artist. 0 frame violations. The patched colors-supplied branch neither replaces (no set_prop_cycle) nor advances (no get_next_color) the shared axes cycle, so the frame is genuinely read-only. This IS the discriminating content of the fix and it holds in the real repo.

### DOMAIN EDGE CASES (spec NOT too strong here):
- Empty colors: real stackplot raises StopIteration -> correctly excluded by require colors.length > 0.
- layerCount=0: real repo raises IndexError in np.row_stack(args) BEFORE any colour selection (an unrelated pre-colour op, not the modeled callee). The modeled colour-selection callee (itertools.cycle consumed 0 times) trivially yields [] which cyclicColors matches; the row_stack failure is outside the modeled function's scope and does not make the colour-selection spec unfaithful.

No input found on which the modeled function (cyclicColors / frame) disagrees with the real patched callee. The spec is not too strong and does not drift from real repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check of the consumer spec view (impl+proof elided) against the PUBLIC problem_statement only (hints excluded). same_spec(Solution, Solution_prepatch)=True (byte-identical spec region); leakage.screen passes with 0 hard failures.

Gold edit essence: stop mutating/advancing the shared axes colour cycle (delete axes.set_prop_cycle(color=colors) and per-area axes._get_lines.get_next_color()) and instead cycle the supplied colours privately (itertools.cycle). The discriminating property of the fix = 'the shared axes cycle is left unchanged'.

That discriminator is disclosed VERBATIM by the public problem_statement, whose title is literally 'stackplot should not change Axes cycler' and whose body states the use-case (keep colours synchronised across plot types). The spec's frame clause `ensures sharedCycle = sharedCycleOld` is exactly this public requirement, not information beyond it.

The second clause `out = cyclicColors colors layerCount` describes the observed per-area colour assignment, which is behaviour-identical pre- and post-patch (pre-patch also produced the cyclic repetition of `colors`), so it is not the discriminating content of the fix — it is the natural, non-leaking statement of the task. The 'cycle reference such as C2' token is taken straight from the problem_statement traceback.

No gold-patch specifics appear in the spec view: no `itertools`, `itertools.cycle`, `set_prop_cycle`, `get_next_color`, `fill_between`, or `import` tokens. The axioms-start comment's phrase 'standard-library finite cyclic iterator' names no API and only characterises cyclic colour repetition at the behavioural level (justifying the deep model), which is inherent task behaviour rather than an implementation directive. A spec necessarily encodes the required behaviour; nothing here reveals the gold implementation mechanism beyond what the public problem statement already discloses.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
