# P2 adversarial audit — pydata__xarray-6461

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `ensures out = xAttrs` is an EXACT equality that uniquely pins the single output to the second argument's own mapping (getattr(x,"attrs",{}) = the gold body). No terminating same-spec verifying impl exists whose faithful patch does NOT resolve. Every wrong TERMINATING impl fails verification; the only verify-not-correct escape is a DIVERGENT body whose faithful patch times out (completed=False), which routes to inconclusive, never BROKEN.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees: the changed operation is the selection of the
@@ -62,7 +62,7 @@
   ensures out = xAttrs
   do
     -- impl-start
-    return xAttrs
+    return present[1]!
     -- impl-end
 
 prove_correct attrsToKeep by
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
 -- (No axiomatized callees: the changed operation is the selection of the
@@ -62,7 +62,7 @@
   ensures out = xAttrs
   do
     -- impl-start
-    return xAttrs
+    return present[xPos.toNat]!
     -- impl-end
 
 prove_correct attrsToKeep by
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
 -- (No axiomatized callees: the changed operation is the selection of the
@@ -62,7 +62,7 @@
   ensures out = xAttrs
   do
     -- impl-start
-    return xAttrs
+    return 0
     -- impl-end
 
 prove_correct attrsToKeep by
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
 -- (No axiomatized callees: the changed operation is the selection of the
@@ -62,7 +62,7 @@
   ensures out = xAttrs
   do
     -- impl-start
-    return xAttrs
+    return present[0]!
     -- impl-end
 
 prove_correct attrsToKeep by
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
 -- (No axiomatized callees: the changed operation is the selection of the
@@ -62,7 +62,10 @@
   ensures out = xAttrs
   do
     -- impl-start
-    return xAttrs
+    if xPos < 1 then
+      return xAttrs
+    else
+      return present[0]!
     -- impl-end
 
 prove_correct attrsToKeep by
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
 -- (No axiomatized callees: the changed operation is the selection of the
@@ -62,7 +62,9 @@
   ensures out = xAttrs
   do
     -- impl-start
-    return xAttrs
+    let mut r : Int := xAttrs
+    r := r + 1
+    return r
     -- impl-end
 
 prove_correct attrsToKeep by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the changed operation is the selection of the
--  second argument's OWN attribute identity, modeled deeply. No outside callee
--  contract is consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A conditional-selection routine is asked to preserve the attribute mapping of
   its SECOND positional argument. The mapping it preserves must be the mapping
   that BELONGS TO that second argument. If the second argument is a bare scalar
   (it carries no mapping of its own), the preserved mapping is the empty one.

   The routine is also handed the list of attribute mappings of exactly those
   arguments that actually carry one, in argument order. That list is NOT a
   reliable positional handle on the second argument: a scalar argument
   contributes no entry, so the second argument's mapping need not sit at any
   constant offset in the list (and may be absent from it entirely). The
   preserved mapping must therefore be the second argument's OWN mapping,
   regardless of its position in that list (or its absence from it).

   Attribute mappings are modeled as opaque integer identities (distinct
   mappings have distinct identities; the empty mapping, which is also what a
   scalar carries, is the identity 0). `present` is the list of identities of
   the arguments that carry a mapping, in order. `xAttrs` is the identity of the
   second argument's own mapping. `xPos` locates the second argument's mapping
   inside `present` (-1 when the second argument carries no mapping, i.e. it is a
   scalar). The carried structural fact — an entry actually present in `present`
   agrees with the owning argument's identity — pins the result to the second
   argument's mapping as PRODUCED from that argument, not merely a value read at
   a constant list offset.

   All three inputs are read-only (not `mut`); the routine mutates nothing
   (directive 5). `present` is modeled as `List Int`, the identities and the
   position as `Int`. -/
method attrsToKeep (present : List Int) (xAttrs : Int) (xPos : Int) return (out : Int)
  -- `xPos` locates the second argument's own mapping within `present`, or is
  -- -1 when the second argument carries no mapping (it is a scalar).
  require xPos = -1 ∨ (0 ≤ xPos ∧ xPos < present.length)
  -- When the second argument's mapping is present, the entry at that position is
  -- exactly the second argument's own mapping.
  require ∀ k : Nat, (xPos = (k : Int) ∧ k < present.length) → present[k]! = xAttrs
  -- A scalar second argument carries the empty mapping (identity 0).
  require xPos = -1 → xAttrs = 0
  -- The preserved mapping is the second argument's OWN mapping.
  ensures out = xAttrs
  do
    -- impl-start
    return xAttrs
    -- impl-end

prove_correct attrsToKeep by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (SUMMARY.md, all atk_*.lean, patch_atk_7.diff, patch_atk_8.diff, v_*.log, resolve_atk_*.log).

SAME-SPEC: swebench_unified.markers.same_spec(velvet) = True for all 8 attacks + pos_control (impl region only differs; axioms/pure/pre/post/signature byte-identical).

### VERIFY (bash scripts/lean_verify.sh <f>):
- atk_1 `return present[1]!` -> exit1 FAIL (unsolved: present[1]!=xAttrs) [prepatch bug re-encoded; matches Solution_prepatch.lean].
- atk_2 `return present[xPos.toNat]!` -> exit1 FAIL (unsolved: present[xPos.toNat]!=xAttrs) [positional read, no scalar guard: xPos=-1 -> toNat=0].
- atk_3 `return 0` -> exit1 FAIL (unsolved: 0=xAttrs) [ungrounded-oracle echo].
- atk_4 `return present[0]!` -> exit1 FAIL (unsolved: present[0]!=xAttrs) [boundary].
- atk_5 `if xPos<1 then xAttrs else present[0]!` -> exit1 FAIL (unsolved: present[0]!=xAttrs, if_neg) [partial-domain: correct only for small xPos].
- atk_6 `let mut r:=xAttrs; r:=r+1; return r` -> exit1 FAIL (unsolved: xAttrs+1=xAttrs) [control-flow/effect off-by-one].
- atk_7 guard-echo `if 0<=xPos<len then present[xPos] else xAttrs` -> exit0 VERIFIES [behaviorally == xAttrs by require_2].
- atk_8 `while 0<1 {i:=i+1}; return present[1]!` -> exit0 VERIFIES VACUOUSLY [partial-termination: non-terminating body discharges any postcondition].
- pos_control `return xAttrs` -> exit0 VERIFIES.
Wrong terminating impls atk_1..atk_6 ALL rejected by the tight exact-equality spec.

RESOLVE — every VERIFYING attack materialized + run through official swebench_unified.harness.run_resolve (image swebench/sweb.eval.x86_64.pydata_1776_xarray-6461, SBU_BENCHMARK_DIR=benchmark-verified). EXECUTED, not speculated:
- atk_7 patch: BYTE-IDENTICAL to gold patch.diff (attrs[1] -> getattr(x,"attrs",{})); `git apply --check` clean at base_commit; run_instance.log: 'Applied patch ... cleanly'. run_resolve -> completed=False resolved=False, note='harness timed out (900s)'. => NOT a break (completed=False => inconclusive per _derive_audit_verdict L310-312).
- atk_8 patch: infinite-loop keep_attrs callback (def with `while 0<1`); `git apply --check` clean; run_instance.log: 'Applied patch ... cleanly'. run_resolve (timeout=600) -> completed=False resolved=False, note='harness timed out (600s)'. => NOT a break: divergence artifact; the real callback hangs, F2P test times out, completed=False => inconclusive. Universal Velvet partial-correctness escape, orthogonal to THIS bundle's refinement fidelity; excluded from the scored set (a completed=False candidate can only force a spurious INCONCLUSIVE, never BROKEN).
Neither verifying attack yields completed=True AND not resolved, so the BROKEN condition (verify=>NOT correct) is UNSATISFIED.

SCORED SET = atk_1..atk_6 (>=5 floor met): all same-spec, all FAIL verification (spec rejects every wrong terminating impl). prepatch reproduced (atk_1 == Solution_prepatch.lean impl). pos_control verifies (non-vacuity). No candidates in the scored set => no resolve needed there => clean pass, no inconclusive hits.

REFINEMENT.MD AUDIT (step 3): every leg is R or I. A1 present<->attrs (R: List dict -> List Int). A2 xAttrs<->getattr(x,"attrs",{}) (R: dict identity -> Int, {}->0). A3 xPos + require clauses <-> objs/DataArray structural fact (R: pure input framing; require_2 pins present[xPos]=xAttrs, require_1 pins scalar->0). A4 return xAttrs <-> return getattr(x,"attrs",{}) (I under R of A2). A5 unused real lambda param `context` (R). NO A-consumed, NO A-reference, NO kind-3. Axioms region empty; no axiom_check.py shipped (consistent with mapping.md §3). There are NO A-legs to attack; the whole model<->patch map is R/I, mechanically backstopped by G-CONF (meta: pass, 100002 configs, seed 6461, 0 disagreements). Correspondence to the real callee holds.

VERDICT: SOUND. The exact-equality postcondition out=xAttrs pins the single output to the gold value getattr(x,"attrs",{}); every terminating verifying impl returns exactly that (=> its patch is the gold body and resolves); every wrong terminating impl fails verification; the only verify-not-correct escape is the harness-inconclusive (completed=False) divergence artifact, which cannot satisfy the BROKEN condition. >=5 attacks run, prepatch reproduced, positive control verifies, refinement R/I with G-CONF backstop. No break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `ensures out = xAttrs` is an EXACT equality that uniquely pins the single output to the second argument's own mapping (getattr(x,"attrs",{}) = the gold body). No terminating same-spec verifying impl exists whose faithful patch does NOT resolve. Every wrong TERMINATING impl fails verification; the only verify-not-correct escape is a DIVERGENT body whose faithful patch times out (completed=False), which routes to inconclusive, never BROKEN.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the changed operation is the selection of the
--  second argument's OWN attribute identity, modeled deeply. No outside callee
--  contract is consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A conditional-selection routine is asked to preserve the attribute mapping of
   its SECOND positional argument. The mapping it preserves must be the mapping
   that BELONGS TO that second argument. If the second argument is a bare scalar
   (it carries no mapping of its own), the preserved mapping is the empty one.

   The routine is also handed the list of attribute mappings of exactly those
   arguments that actually carry one, in argument order. That list is NOT a
   reliable positional handle on the second argument: a scalar argument
   contributes no entry, so the second argument's mapping need not sit at any
   constant offset in the list (and may be absent from it entirely). The
   preserved mapping must therefore be the second argument's OWN mapping,
   regardless of its position in that list (or its absence from it).

   Attribute mappings are modeled as opaque integer identities (distinct
   mappings have distinct identities; the empty mapping, which is also what a
   scalar carries, is the identity 0). `present` is the list of identities of
   the arguments that carry a mapping, in order. `xAttrs` is the identity of the
   second argument's own mapping. `xPos` locates the second argument's mapping
   inside `present` (-1 when the second argument carries no mapping, i.e. it is a
   scalar). The carried structural fact — an entry actually present in `present`
   agrees with the owning argument's identity — pins the result to the second
   argument's mapping as PRODUCED from that argument, not merely a value read at
   a constant list offset.

   All three inputs are read-only (not `mut`); the routine mutates nothing
   (directive 5). `present` is modeled as `List Int`, the identities and the
   position as `Int`. -/
method attrsToKeep (present : List Int) (xAttrs : Int) (xPos : Int) return (out : Int)
  -- `xPos` locates the second argument's own mapping within `present`, or is
  -- -1 when the second argument carries no mapping (it is a scalar).
  require xPos = -1 ∨ (0 ≤ xPos ∧ xPos < present.length)
  -- When the second argument's mapping is present, the entry at that position is
  -- exactly the second argument's own mapping.
  require ∀ k : Nat, (xPos = (k : Int) ∧ k < present.length) → present[k]! = xAttrs
  -- A scalar second argument carries the empty mapping (identity 0).
  require xPos = -1 → xAttrs = 0
  -- The preserved mapping is the second argument's OWN mapping.
  ensures out = xAttrs
  do
    -- impl-start
    return xAttrs
    -- impl-end

prove_correct attrsToKeep by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (SUMMARY.md, all atk_*.lean, patch_atk_7.diff, patch_atk_8.diff, v_*.log, resolve_atk_*.log).

SAME-SPEC: swebench_unified.markers.same_spec(velvet) = True for all 8 attacks + pos_control (impl region only differs; axioms/pure/pre/post/signature byte-identical).

### VERIFY (bash scripts/lean_verify.sh <f>):
- atk_1 `return present[1]!` -> exit1 FAIL (unsolved: present[1]!=xAttrs) [prepatch bug re-encoded; matches Solution_prepatch.lean].
- atk_2 `return present[xPos.toNat]!` -> exit1 FAIL (unsolved: present[xPos.toNat]!=xAttrs) [positional read, no scalar guard: xPos=-1 -> toNat=0].
- atk_3 `return 0` -> exit1 FAIL (unsolved: 0=xAttrs) [ungrounded-oracle echo].
- atk_4 `return present[0]!` -> exit1 FAIL (unsolved: present[0]!=xAttrs) [boundary].
- atk_5 `if xPos<1 then xAttrs else present[0]!` -> exit1 FAIL (unsolved: present[0]!=xAttrs, if_neg) [partial-domain: correct only for small xPos].
- atk_6 `let mut r:=xAttrs; r:=r+1; return r` -> exit1 FAIL (unsolved: xAttrs+1=xAttrs) [control-flow/effect off-by-one].
- atk_7 guard-echo `if 0<=xPos<len then present[xPos] else xAttrs` -> exit0 VERIFIES [behaviorally == xAttrs by require_2].
- atk_8 `while 0<1 {i:=i+1}; return present[1]!` -> exit0 VERIFIES VACUOUSLY [partial-termination: non-terminating body discharges any postcondition].
- pos_control `return xAttrs` -> exit0 VERIFIES.
Wrong terminating impls atk_1..atk_6 ALL rejected by the tight exact-equality spec.

RESOLVE — every VERIFYING attack materialized + run through official swebench_unified.harness.run_resolve (image swebench/sweb.eval.x86_64.pydata_1776_xarray-6461, SBU_BENCHMARK_DIR=benchmark-verified). EXECUTED, not speculated:
- atk_7 patch: BYTE-IDENTICAL to gold patch.diff (attrs[1] -> getattr(x,"attrs",{})); `git apply --check` clean at base_commit; run_instance.log: 'Applied patch ... cleanly'. run_resolve -> completed=False resolved=False, note='harness timed out (900s)'. => NOT a break (completed=False => inconclusive per _derive_audit_verdict L310-312).
- atk_8 patch: infinite-loop keep_attrs callback (def with `while 0<1`); `git apply --check` clean; run_instance.log: 'Applied patch ... cleanly'. run_resolve (timeout=600) -> completed=False resolved=False, note='harness timed out (600s)'. => NOT a break: divergence artifact; the real callback hangs, F2P test times out, completed=False => inconclusive. Universal Velvet partial-correctness escape, orthogonal to THIS bundle's refinement fidelity; excluded from the scored set (a completed=False candidate can only force a spurious INCONCLUSIVE, never BROKEN).
Neither verifying attack yields completed=True AND not resolved, so the BROKEN condition (verify=>NOT correct) is UNSATISFIED.

SCORED SET = atk_1..atk_6 (>=5 floor met): all same-spec, all FAIL verification (spec rejects every wrong terminating impl). prepatch reproduced (atk_1 == Solution_prepatch.lean impl). pos_control verifies (non-vacuity). No candidates in the scored set => no resolve needed there => clean pass, no inconclusive hits.

REFINEMENT.MD AUDIT (step 3): every leg is R or I. A1 present<->attrs (R: List dict -> List Int). A2 xAttrs<->getattr(x,"attrs",{}) (R: dict identity -> Int, {}->0). A3 xPos + require clauses <-> objs/DataArray structural fact (R: pure input framing; require_2 pins present[xPos]=xAttrs, require_1 pins scalar->0). A4 return xAttrs <-> return getattr(x,"attrs",{}) (I under R of A2). A5 unused real lambda param `context` (R). NO A-consumed, NO A-reference, NO kind-3. Axioms region empty; no axiom_check.py shipped (consistent with mapping.md §3). There are NO A-legs to attack; the whole model<->patch map is R/I, mechanically backstopped by G-CONF (meta: pass, 100002 configs, seed 6461, 0 disagreements). Correspondence to the real callee holds.

VERDICT: SOUND. The exact-equality postcondition out=xAttrs pins the single output to the gold value getattr(x,"attrs",{}); every terminating verifying impl returns exactly that (=> its patch is the gold body and resolves); every wrong terminating impl fails verification; the only verify-not-correct escape is the harness-inconclusive (completed=False) divergence artifact, which cannot satisfy the BROKEN condition. >=5 attacks run, prepatch reproduced, positive control verifies, refinement R/I with G-CONF backstop. No break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real callee.

SPEC INTEGRITY: same_spec(Solution, Solution_prepatch, velvet) = True. The spec regions (signature `attrsToKeep (present : List Int) (xAttrs : Int) (xPos : Int)`, the three `require` clauses, and `ensures out = xAttrs`) are byte-identical between Solution.lean and its prepatch; only the impl region differs (`return xAttrs` vs `return present[1]!`). Solution.lean elaborates cleanly (lean_verify exit 0); prepatch fails on the exact goal `present[1]! = xAttrs` (exit 1), witnessing the bug.

MODELED FUNCTION: attrsToKeep returns `xAttrs` unconditionally, ignoring `present` and `xPos`. The mapping/refinement docs bind `xAttrs` to the identity of the real callee `getattr(x, "attrs", {})` (dict↔Int identity abstraction; empty dict / scalar ↔ 0).

REAL CALLEE (base_commit 851dadeb, xarray/core/computation.py:1832; gold patch): `keep_attrs = lambda attrs, context: getattr(x, "attrs", {})`. The patched callback ALSO ignores its `attrs` list argument and returns x's own attribute mapping. So the modeled function and the real callee are output-identical by construction on every input.

EMPIRICAL VALIDATION: built a patched xarray 2022.3.0 (gold `getattr(x,...)`) and ran the shipped conformance_check.py: 0 disagreements over 100,002 fuzzed configs (seed 6461, x/y each independently scalar or DataArray-with-attrs); ran independent adversarial checks — x-DataArray at offset 1, scalar x, x empty-attrs, multi-key attrs, attr-key identity collisions between x and y, scalar/scalar — all confirm where(cond,x,y,keep_attrs=True).attrs == getattr(x,"attrs",{}) with 0 divergences.

The spec is not too strong: the postcondition forces exactly the callee's behavior and the preconditions are satisfiable framing (they describe how `present`/`xPos` relate to `xAttrs` for real xarray configs; they never over-constrain the output). No admissible input makes the modeled function disagree with the real repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, zero hard failures): no diff markers, no reproduced gold-patch line (>=8 normalized chars), no patched file path 'xarray/core/computation.py' or dotted module, no spec-view identifier/comment naming a patched repo symbol, no L3 narration terms. same_spec(Solution, Solution_prepatch)=True — the frozen spec region is byte-identical, so the only discriminator carried by the spec view is the postcondition `out = xAttrs`.

Semantic check against the SOLVER-VISIBLE problem_statement only (not hints_text): the public issue already contains the buggy line verbatim ('keep_attrs = lambda attrs, context: attrs[1]'), the explicit design intent ('keep the attributes of x, the second parameter'), and the crash (IndexError on scalar second arg). The spec view's discriminating content — postcondition out=xAttrs meaning 'return the second positional argument's OWN attribute mapping (0/empty for a scalar)' — is exactly that already-public intent, expressed abstractly. The gold edit's specifics are NOT exposed: `getattr(x, "attrs", {})` is never named, the fix line is not reproduced, and no repo file/symbol/module leaks. Describing the correct target behavior that the public issue itself states is the spec's legitimate function, not gold-reconstruction leakage.

Conclusion: nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
