# P2 adversarial audit — astropy__astropy-14995

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -66,6 +66,13 @@
     out = some (combine (selfMask.getD []) (operandMask.getD []))
   do
     -- impl-start
+    -- Pre-image skeleton: the single-mask carry-over branch guards on whether
+    -- the SECOND OPERAND ITSELF is absent, rather than on whether that operand's
+    -- MASK is absent. For a real second operand (`operandPresent = true`) this
+    -- guard is never taken, so a present first mask paired with an absent second
+    -- mask falls through to the combiner instead of being carried over. The
+    -- frozen spec requires `out = selfMask` in that case, so prove_correct MUST
+    -- fail.
     let out : Option (List Int) :=
       if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
         none
@@ -73,7 +80,7 @@
         if selfMask = none then
           operandMask
         else
-          if operandMask = none then
+          if operandPresent = false then
             selfMask
           else
             some (combine (selfMask.getD []) (operandMask.getD []))
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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -71,10 +71,10 @@
         none
       else
         if selfMask = none then
-          operandMask
+          selfMask
         else
           if operandMask = none then
-            selfMask
+            operandMask
           else
             some (combine (selfMask.getD []) (operandMask.getD []))
     return out
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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -66,17 +66,7 @@
     out = some (combine (selfMask.getD []) (operandMask.getD []))
   do
     -- impl-start
-    let out : Option (List Int) :=
-      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
-        none
-      else
-        if selfMask = none then
-          operandMask
-        else
-          if operandMask = none then
-            selfMask
-          else
-            some (combine (selfMask.getD []) (operandMask.getD []))
+    let out : Option (List Int) := none
     return out
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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -70,13 +70,7 @@
       if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
         none
       else
-        if selfMask = none then
-          operandMask
-        else
-          if operandMask = none then
-            selfMask
-          else
-            some (combine (selfMask.getD []) (operandMask.getD []))
+        some (combine (selfMask.getD []) (operandMask.getD []))
     return out
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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -76,7 +76,7 @@
           if operandMask = none then
             selfMask
           else
-            some (combine (selfMask.getD []) (operandMask.getD []))
+            selfMask
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -76,7 +76,7 @@
           if operandMask = none then
             selfMask
           else
-            some (combine (selfMask.getD []) (operandMask.getD []))
+            some (combine (operandMask.getD []) (selfMask.getD []))
     return out
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
 -- (No axiomatized callees. The mask-combining routine treats each operand's
@@ -67,7 +67,7 @@
   do
     -- impl-start
     let out : Option (List Int) :=
-      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
+      if (selfMask = none ∧ operandMask = none) then
         none
       else
         if selfMask = none then
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The mask-combining routine treats each operand's
--  mask as opaque presence-or-absence and, when both are present, hands the two
--  mask values to the caller-supplied combiner. That combiner is a parameter of
--  the routine, modeled directly as the function `combine`; there is no
--  unchanged library callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
-- (No pure helpers required: the result is a direct case split over which
--  operands carry a mask and whether a combiner was supplied.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine the masks of two operands of an elementwise operation.

   Each operand may or may not carry a mask (`some` values vs. `none`). A
   caller-supplied combiner `combine` merges two present masks elementwise; the
   caller may also decline mask handling entirely (`handleMaskNone = true`).
   The second operand is a real operand value, never absent (`operandPresent`).

   The resulting mask is determined entirely by which masks are present:

   - if the caller declines mask handling, or NEITHER operand carries a mask,
     there is no resulting mask (`none`);
   - if ONLY the second operand carries a mask, that mask is the result (it is
     carried over unchanged);
   - if ONLY the first operand carries a mask, that mask is the result (it is
     carried over unchanged);
   - if BOTH operands carry a mask, the result is the combiner applied to the
     two present mask values.

   The two single-mask cases must each yield the one mask that is present — they
   must never attempt to combine a present mask with an absent one. The mask
   values themselves are read-only carriers (not `mut`); the routine builds a
   fresh result and mutates neither operand's mask (directive 5). -/
method resolveMask
    (selfMask : Option (List Int))
    (operandMask : Option (List Int))
    (handleMaskNone : Bool)
    (operandPresent : Bool)
    (combine : List Int → List Int → List Int)
    return (out : Option (List Int))
  require operandPresent = true
  ensures handleMaskNone = true → out = none
  ensures (handleMaskNone = false ∧ selfMask = none ∧ operandMask = none) →
    out = none
  ensures (handleMaskNone = false ∧ selfMask = none ∧ operandMask ≠ none) →
    out = operandMask
  ensures (handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask = none) →
    out = selfMask
  ensures (handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask ≠ none) →
    out = some (combine (selfMask.getD []) (operandMask.getD []))
  do
    -- impl-start
    let out : Option (List Int) :=
      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
        none
      else
        if selfMask = none then
          operandMask
        else
          if operandMask = none then
            selfMask
          else
            some (combine (selfMask.getD []) (operandMask.getD []))
    return out
    -- impl-end

prove_correct resolveMask by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC astropy__astropy-14995 velvet resolveMask. The five `ensures` clauses TOTALLY and DETERMINISTICALLY pin `out` across the entire domain (require operandPresent=true): out=none when handleMaskNone or neither mask present; the present mask carried over in each single-mask case; combine applied in the both-present case. Because the postcondition fully determines the return in every case, any behaviorally-wrong impl must fail prove_correct, and any verifying impl is forced equal to gold. No verifying wrong impl was found, so NO faithful-patch resolve run was triggered (step 2 fires only for a verifying wrong impl); patches={}.

A-LEG AUDIT (focus per plan §4): meta.json axioms=[] and deep_model_references=[]. refinement.md §B correctly declares every leg R or I, with NO A-consumed / A-reference legs and NO kind-3 (inexpressible-changed-op) steps. mapping.md binds resolveMask -> NDArithmeticMixin._arithmetic_mask (astropy/nddata/mixins/ndarithmetic.py, body case-split lines 428-439 @ base b16c7d12); the only delegated callable handle_mask is a genuine function PARAMETER modeled directly as `combine` (A4/A8), not an axiomatized library callee, so there is no A-leg correspondence to falsify and no axiom_check.py is expected (G-AX skips). Correspondence to gold hunk (elif operand is None -> elif operand.mask is None) holds: the fixed branch A7 requires out=selfMask when selfMask!=none and operandMask=none. Model<->patch mapping is faithful.

SAME-SPEC: all 7 attacks + positive_control return same_spec=True under velvet (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFICATIONS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of 4; exit0=verifies, 1=error/unsolved-goals):
- positive_control.lean rc=0 (VERIFIES) -> gold-equivalent impl is sound.
- atk_1.lean (=Solution_prepatch, guard on operandPresent=false / `operand is None`) rc=1 -> PREPATCH BUG REPRODUCED; unsolved goal is ensures_2 (selfMask!=none & operandMask=none -> out=selfMask), matching the issue's TypeError |: int and NoneType.
- atk_2.lean (branch-swap: selfMask=none->selfMask, operandMask=none->operandMask) rc=1, fails ensures_2.
- atk_3.lean (control-flow-effect: always none, masks ignored) rc=1.
- atk_4.lean (ungrounded-oracle echo: combiner applied in EVERY non-none case) rc=1, fails ensures_2.
- atk_5.lean (both-present -> selfMask instead of combine) rc=1.
- atk_6.lean (arg-order swap: combine operandMask selfMask) rc=1, fails ensures_1 (both-present clause).
- atk_7.lean (flag/boundary: drop handleMaskNone from the none-guard) rc=1, fails ensures_5 (handleMaskNone=true -> out=none).
All wrong-impl failures are genuine `unsolved goals` on the precise discriminating postcondition, NOT syntax errors (confirmed from lean_verify stderr).

CONCLUSION: >=6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, arg-order, branch-swap) all fail to verify; positive control verifies; prepatch reproduced. Zero verifying wrong impls => verify=>correct holds; no resolve run needed. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The mask-combining routine treats each operand's
--  mask as opaque presence-or-absence and, when both are present, hands the two
--  mask values to the caller-supplied combiner. That combiner is a parameter of
--  the routine, modeled directly as the function `combine`; there is no
--  unchanged library callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
-- (No pure helpers required: the result is a direct case split over which
--  operands carry a mask and whether a combiner was supplied.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine the masks of two operands of an elementwise operation.

   Each operand may or may not carry a mask (`some` values vs. `none`). A
   caller-supplied combiner `combine` merges two present masks elementwise; the
   caller may also decline mask handling entirely (`handleMaskNone = true`).
   The second operand is a real operand value, never absent (`operandPresent`).

   The resulting mask is determined entirely by which masks are present:

   - if the caller declines mask handling, or NEITHER operand carries a mask,
     there is no resulting mask (`none`);
   - if ONLY the second operand carries a mask, that mask is the result (it is
     carried over unchanged);
   - if ONLY the first operand carries a mask, that mask is the result (it is
     carried over unchanged);
   - if BOTH operands carry a mask, the result is the combiner applied to the
     two present mask values.

   The two single-mask cases must each yield the one mask that is present — they
   must never attempt to combine a present mask with an absent one. The mask
   values themselves are read-only carriers (not `mut`); the routine builds a
   fresh result and mutates neither operand's mask (directive 5). -/
method resolveMask
    (selfMask : Option (List Int))
    (operandMask : Option (List Int))
    (handleMaskNone : Bool)
    (operandPresent : Bool)
    (combine : List Int → List Int → List Int)
    return (out : Option (List Int))
  require operandPresent = true
  ensures handleMaskNone = true → out = none
  ensures (handleMaskNone = false ∧ selfMask = none ∧ operandMask = none) →
    out = none
  ensures (handleMaskNone = false ∧ selfMask = none ∧ operandMask ≠ none) →
    out = operandMask
  ensures (handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask = none) →
    out = selfMask
  ensures (handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask ≠ none) →
    out = some (combine (selfMask.getD []) (operandMask.getD []))
  do
    -- impl-start
    let out : Option (List Int) :=
      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
        none
      else
        if selfMask = none then
          operandMask
        else
          if operandMask = none then
            selfMask
          else
            some (combine (selfMask.getD []) (operandMask.getD []))
    return out
    -- impl-end

prove_correct resolveMask by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC astropy__astropy-14995 velvet resolveMask. The five `ensures` clauses TOTALLY and DETERMINISTICALLY pin `out` across the entire domain (require operandPresent=true): out=none when handleMaskNone or neither mask present; the present mask carried over in each single-mask case; combine applied in the both-present case. Because the postcondition fully determines the return in every case, any behaviorally-wrong impl must fail prove_correct, and any verifying impl is forced equal to gold. No verifying wrong impl was found, so NO faithful-patch resolve run was triggered (step 2 fires only for a verifying wrong impl); patches={}.

A-LEG AUDIT (focus per plan §4): meta.json axioms=[] and deep_model_references=[]. refinement.md §B correctly declares every leg R or I, with NO A-consumed / A-reference legs and NO kind-3 (inexpressible-changed-op) steps. mapping.md binds resolveMask -> NDArithmeticMixin._arithmetic_mask (astropy/nddata/mixins/ndarithmetic.py, body case-split lines 428-439 @ base b16c7d12); the only delegated callable handle_mask is a genuine function PARAMETER modeled directly as `combine` (A4/A8), not an axiomatized library callee, so there is no A-leg correspondence to falsify and no axiom_check.py is expected (G-AX skips). Correspondence to gold hunk (elif operand is None -> elif operand.mask is None) holds: the fixed branch A7 requires out=selfMask when selfMask!=none and operandMask=none. Model<->patch mapping is faithful.

SAME-SPEC: all 7 attacks + positive_control return same_spec=True under velvet (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFICATIONS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of 4; exit0=verifies, 1=error/unsolved-goals):
- positive_control.lean rc=0 (VERIFIES) -> gold-equivalent impl is sound.
- atk_1.lean (=Solution_prepatch, guard on operandPresent=false / `operand is None`) rc=1 -> PREPATCH BUG REPRODUCED; unsolved goal is ensures_2 (selfMask!=none & operandMask=none -> out=selfMask), matching the issue's TypeError |: int and NoneType.
- atk_2.lean (branch-swap: selfMask=none->selfMask, operandMask=none->operandMask) rc=1, fails ensures_2.
- atk_3.lean (control-flow-effect: always none, masks ignored) rc=1.
- atk_4.lean (ungrounded-oracle echo: combiner applied in EVERY non-none case) rc=1, fails ensures_2.
- atk_5.lean (both-present -> selfMask instead of combine) rc=1.
- atk_6.lean (arg-order swap: combine operandMask selfMask) rc=1, fails ensures_1 (both-present clause).
- atk_7.lean (flag/boundary: drop handleMaskNone from the none-guard) rc=1, fails ensures_5 (handleMaskNone=true -> out=none).
All wrong-impl failures are genuine `unsolved goals` on the precise discriminating postcondition, NOT syntax errors (confirmed from lean_verify stderr).

CONCLUSION: >=6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, arg-order, branch-swap) all fail to verify; positive control verifies; prepatch reproduced. Zero verifying wrong impls => verify=>correct holds; no resolve run needed. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** resolveMask's five ensures clauses exactly reproduce the patched _arithmetic_mask (base_commit b16c7d12, astropy/nddata/mixins/ndarithmetic.py:485) under the mapping.md value bijection (Option(List Int) ↔ None/ndarray; handleMaskNone ↔ handle_mask is None; combine ↔ handle_mask; deepcopy = content identity):
- ensures1 handleMaskNone→none  == 'or handle_mask is None: return None'
- ensures2 (¬handleMaskNone ∧ selfMask=none ∧ operandMask=none)→none == first-if body (operand is not None drops out as domain)
- ensures3 (selfMask=none ∧ operandMask≠none)→operandMask == 'elif self.mask is None ...: deepcopy(operand.mask)'
- ensures4 (selfMask≠none ∧ operandMask=none)→selfMask == the FIXED branch 'elif operand.mask is None: deepcopy(self.mask)'
- ensures5 (both present)→some(combine ...) == 'else: handle_mask(self.mask, operand.mask)'.
Domain restriction require operandPresent=true is faithful: _arithmetic_mask is only reached with a real wrapped second operand (the operand-is-None case routes through use_masked_arith at ndarithmetic.py:265 and never calls this function), so no reachable input has operandPresent=false. Every reachable (selfMask, operandMask, handleMaskNone, combine) combination the spec constrains agrees with the real function; I could not construct any diverging input. Checks: same_spec(Solution, prepatch) with VelvetBackend.language = True (spec region byte-identical); Solution.lean verifies via lean_verify.sh (exit 0). No spec-too-strong / no drift found.

- ensures1 handleMaskNone→none  == 'or handle_mask is None: return None'
- ensures2 (¬handleMaskNone ∧ selfMask=none ∧ operandMask=none)→none == first-if body (operand is not None drops out as domain)
- ensures3 (selfMask=none ∧ operandMask≠none)→operandMask == 'elif self.mask is None ...: deepcopy(operand.mask)'
- ensures4 (selfMask≠none ∧ operandMask=none)→selfMask == the FIXED branch 'elif operand.mask is None: deepcopy(self.mask)'
- ensures5 (both present)→some(combine ...) == 'else: handle_mask(self.mask, operand.mask)'.
Domain restriction require operandPresent=true is faithful: _arithmetic_mask is only reached with a real wrapped second operand (the operand-is-None case routes through use_masked_arith at ndarithmetic.py:265 and never calls this function), so no reachable input has operandPresent=false. Every reachable (selfMask, operandMask, handleMaskNone, combine) combination the spec constrains agrees with the real function; I could not construct any diverging input. Checks: same_spec(Solution, prepatch) with VelvetBackend.language = True (spec region byte-identical); Solution.lean verifies via lean_verify.sh (exit 0). No spec-too-strong / no drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: astropy__astropy-14995 (velvet). Verified the consumer spec view (markers.spec_view over Solution.lean): impl and prove_correct bodies are elided; only imports, options, empty axioms/pure/pre/post comment regions, the docstring, the `resolveMask` signature, the `require`, and five `ensures` postconditions pass through. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Mechanical G-LEAK screen (leakage.screen over spec_src vs gold patch + problem_statement): PASSED, hard_failures=[].

Semantic leakage assessment vs the PUBLIC problem_statement baseline (hints_text excluded per instruction): the gold edit is `elif operand is None:` -> `elif operand.mask is None:` (single-mask case: carry over the present mask instead of feeding present-mask+None to the combiner). The problem_statement ALREADY discloses this exact expected behavior in plain terms: 'When one of the operand does not have mask, the mask that exists should just be copied over to the output', plus the failing mask x no-mask -> TypeError scenarios and the diagnosis that a mask of None's is combined via bitwise_or. The spec's discriminating postconditions ((selfMask=none & operandMask!=none)->out=operandMask; (selfMask!=none & operandMask=none)->out=selfMask; both-present->combiner) are a faithful abstract formalization of that publicly-stated behavior. 

The spec view contains NO repo file/line references, NO gold-patch Python identifiers (operand.mask, deepcopy, self.mask, handle_mask), and NO quotation of the culprit line. The precise gold-edit code and file:line (ndarithmetic.py:485/520) appear only in refinement.md and mapping.md, which are audit artifacts, not the consumer spec view. The specific 'operand is None -> operand.mask is None' culprit line the maintainers identified lives in hints_text (out of scope). 

Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already states. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
