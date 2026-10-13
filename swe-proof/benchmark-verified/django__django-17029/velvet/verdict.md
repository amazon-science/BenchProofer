# P2 adversarial audit — django__django-17029

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
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec wrong impl has a faithful refined patch that completes-and-fails-to-resolve.
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
 -- (No axiomatized callees: the cache-reset is a pure state operation on the
@@ -47,7 +47,11 @@
   ensures swappableOccupancy = 0
   do
     -- impl-start
-    swappableOccupancy := 0
+    -- Pre-image (buggy) skeleton: the reset empties only the all-models lookup
+    -- cache and NEVER clears the swappable-settings-name lookup cache, so its
+    -- occupancy is left exactly as it came in (a stale, possibly-positive count).
+    -- The frozen spec requires `swappableOccupancy = 0` on return, so
+    -- prove_correct MUST fail on that clause.
     modelsOccupancy := 0
     return ()
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
 -- (No axiomatized callees: the cache-reset is a pure state operation on the
@@ -47,8 +47,8 @@
   ensures swappableOccupancy = 0
   do
     -- impl-start
-    swappableOccupancy := 0
     modelsOccupancy := 0
+    swappableOccupancy := 1
     return ()
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
 -- (No axiomatized callees: the cache-reset is a pure state operation on the
@@ -48,7 +48,6 @@
   do
     -- impl-start
     swappableOccupancy := 0
-    modelsOccupancy := 0
     return ()
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
 -- (No axiomatized callees: the cache-reset is a pure state operation on the
@@ -47,8 +47,11 @@
   ensures swappableOccupancy = 0
   do
     -- impl-start
-    swappableOccupancy := 0
-    modelsOccupancy := 0
+    if modelsOccupancy = swappableOccupancy then
+      modelsOccupancy := 0
+      swappableOccupancy := 0
+    else
+      modelsOccupancy := 0
     return ()
     -- impl-end
 
```

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees: the cache-reset is a pure state operation on the
@@ -47,8 +47,8 @@
   ensures swappableOccupancy = 0
   do
     -- impl-start
-    swappableOccupancy := 0
-    modelsOccupancy := 0
+    modelsOccupancy := 0 * modelsOccupancy
+    swappableOccupancy := swappableOccupancy - swappableOccupancy
     return ()
     -- impl-end
 
```

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees: the cache-reset is a pure state operation on the
@@ -48,7 +48,7 @@
   do
     -- impl-start
     swappableOccupancy := 0
-    modelsOccupancy := 0
+    modelsOccupancy := swappableOccupancy
     return ()
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the cache-reset is a pure state operation on the
--  registry's own observable cache occupancies, modeled directly as state
--  writes. The unchanged stdlib memoization wrapper whose emptied-cache effect
--  these writes refine is an A-reference validated out-of-band, not a consumed
--  contract.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An application registry keeps several memoizing lookup methods, each backed
   by its own bounded result cache whose occupancy — the number of distinct
   argument tuples whose result is currently retained — can be observed as a
   non-negative count.

   The registry exposes a single cache-reset operation whose promise is to
   discard ALL of those retained results: every memoizing method's cache. So
   immediately afterwards each cache's occupancy must be zero, regardless of how
   full any of them was beforehand. A reset that leaves any one method's
   retained results in place would violate that promise — a later observer would
   still see stale memoized values for that method.

   Here two memoizing methods are modeled (the all-models lookup and the
   swappable-settings-name lookup), carrying only the touched state: one
   non-negative occupancy counter each. Both counters are genuinely mutated
   (declared `mut`) and their post-states are pinned exactly to zero (directive
   5: every changed frame is pinned to its exact post-state). -/
method clearAllCaches (mut modelsOccupancy : Nat) (mut swappableOccupancy : Nat)
    return (unit : Unit)
  ensures modelsOccupancy = 0
  ensures swappableOccupancy = 0
  do
    -- impl-start
    swappableOccupancy := 0
    modelsOccupancy := 0
    return ()
    -- impl-end

prove_correct clearAllCaches by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: method clearAllCaches (mut modelsOccupancy : Nat) (mut swappableOccupancy : Nat) with ensures modelsOccupancy=0 AND ensures swappableOccupancy=0 (partial-correctness, demonic choice). The two occupancies map (mapping.md) to Apps.get_models.cache_info().currsize and Apps.get_swappable_settings_name.cache_info().currsize — EXACTLY the two observables the F2P test test_clear_cache asserts ==0. The spec pins the full post-state, so ANY terminating verifying impl must leave both caches empty => resolves.

COMMANDS: same_spec via swebench_unified.markers.same_spec (all 8 files True). Verify: bash scripts/lean_verify.sh <file>. Resolve: swebench_unified.harness.run_resolve.

### EXECUTED RESULTS (verify):
- atk_1.lean (prepatch: clears models only, leaves swappable) -> FAIL exit 1: 'unsolved goals ... swappableOccupancyOld = 0'. PREPATCH BUG REPRODUCED (spec senses the gold change; matches Solution_prepatch.lean & G-DIFF).
- atk_2.lean (swappableOccupancy := 1) -> FAIL exit 1: '1 = 0'. (boundary/nonzero-constant)
- atk_3.lean (clears swappable only, leaves models) -> FAIL exit 1: 'modelsOccupancyOld = 0'. (mirror partial-domain)
- atk_4.lean (if models=swappable then both:=0 else models:=0 only) -> FAIL exit 1: on the else branch 'swappableOccupancyOld = 0'. (control-flow-effect)
- atk_6.lean (echo: modelsOccupancy := 0*modelsOccupancy; swappableOccupancy := swappableOccupancy - swappableOccupancy) -> VERIFIES exit 0.
- atk_7.lean (echo: swappableOccupancy := 0; modelsOccupancy := swappableOccupancy) -> VERIFIES exit 0.
- pos_control.lean (= frozen Solution.lean) -> VERIFIES exit 0.

### EXECUTED RESULTS (resolve, run_resolve on the FAITHFUL refined patch):
- atk_6 & atk_7 are behaviorally the gold: both terminate with modelsOccupancy=0 AND swappableOccupancy=0, which under the R+A-reference map = self.get_models.cache_clear() + self.get_swappable_settings_name.cache_clear(). Their faithful refined patch is therefore the gold two-line change (patch_echo.diff). run_resolve => RESOLVED: True, COMPLETED: True; FAIL_TO_PASS test_clear_cache success, all 43 PASS_TO_PASS success. => correct echoes, NOT a weakness (build_one.py:313-314).

DIVERGENCE PROBE (examined, reported, NOT submitted as a gating attack): atk_5.lean (`while true do modelsOccupancy := modelsOccupancy; return ()`) is same_spec=True and VERIFIES (exit 0) purely by partial-correctness vacuity (the postcondition is never reached). I materialized its faithful transliteration patch_atk5.diff (`while True: pass` at the top of clear_cache, clearing nothing) and RAN it: run_resolve => RESOLVED: False, COMPLETED: False, note 'no report ... harness error or image pull failure' (the infinite loop hangs the container). This is the framework's INCONCLUSIVE case (build_one.py:310-312, `not r.completed`), NOT the BROKEN case (`r.completed and not r.resolved`, line 306). A diverging program never emits a false 'resolved', so it does not demonstrate verify⇏ correct. Divergence is a semantics-generic artifact of the FROZEN `termination "partial"` option (401/500 velvet bundles use it; spec_guide.md sanctions it), not a defect in this bundle's refinement map or A-legs. Submitting it would force a spurious INCONCLUSIVE; excluded on that basis and documented here for full transparency. atk_5.lean and patch_atk5.diff remain in the scratch dir.

REFINEMENT.md AUDIT (no kind-3): A1 = R (Apps instance -> the two touched cache occupancies). A2 = R + A-reference (swappableOccupancy:=0 <-> get_swappable_settings_name.cache_clear(), the gold-ADDED line). A3 = R + A-reference (modelsOccupancy:=0 <-> get_models.cache_clear(), pre-existing). The sole external fact is the A-reference 'functools.cache cache_clear() => cache_info().currsize==0', validated executably by axiom_check.py (G-AX): EXECUTED => exit 0, 'boundary + 2000 fuzz ... from every tested starting occupancy'. Model<->patch correspondence confirmed against (registry.py:166 @lru_cache get_models, :277 @lru_cache get_swappable_settings_name, clear_cache at :363; gold patch.diff adds the swappable clear verbatim). The post-clear model-expiry loop touches neither functools wrapper, so both currsize are 0 unconditionally after clear_cache — matching the unconditional `=0` postconditions. No consumed axiom; no kind-3 unexpressible-changed-op leg.

CONCLUSION: 6 distinct same-spec attacks run (>=5 floor met): 4 rejected by the spec (partial-domain/boundary/control-flow), 2 verifying echoes whose faithful patches RESOLVE (executed). Prepatch bug reproduced; positive control verifies; A-reference validated; no kind-3 leg. No verifying same-spec impl has a completing faithful patch that fails to resolve. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec wrong impl has a faithful refined patch that completes-and-fails-to-resolve.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the cache-reset is a pure state operation on the
--  registry's own observable cache occupancies, modeled directly as state
--  writes. The unchanged stdlib memoization wrapper whose emptied-cache effect
--  these writes refine is an A-reference validated out-of-band, not a consumed
--  contract.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An application registry keeps several memoizing lookup methods, each backed
   by its own bounded result cache whose occupancy — the number of distinct
   argument tuples whose result is currently retained — can be observed as a
   non-negative count.

   The registry exposes a single cache-reset operation whose promise is to
   discard ALL of those retained results: every memoizing method's cache. So
   immediately afterwards each cache's occupancy must be zero, regardless of how
   full any of them was beforehand. A reset that leaves any one method's
   retained results in place would violate that promise — a later observer would
   still see stale memoized values for that method.

   Here two memoizing methods are modeled (the all-models lookup and the
   swappable-settings-name lookup), carrying only the touched state: one
   non-negative occupancy counter each. Both counters are genuinely mutated
   (declared `mut`) and their post-states are pinned exactly to zero (directive
   5: every changed frame is pinned to its exact post-state). -/
method clearAllCaches (mut modelsOccupancy : Nat) (mut swappableOccupancy : Nat)
    return (unit : Unit)
  ensures modelsOccupancy = 0
  ensures swappableOccupancy = 0
  do
    -- impl-start
    swappableOccupancy := 0
    modelsOccupancy := 0
    return ()
    -- impl-end

prove_correct clearAllCaches by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: method clearAllCaches (mut modelsOccupancy : Nat) (mut swappableOccupancy : Nat) with ensures modelsOccupancy=0 AND ensures swappableOccupancy=0 (partial-correctness, demonic choice). The two occupancies map (mapping.md) to Apps.get_models.cache_info().currsize and Apps.get_swappable_settings_name.cache_info().currsize — EXACTLY the two observables the F2P test test_clear_cache asserts ==0. The spec pins the full post-state, so ANY terminating verifying impl must leave both caches empty => resolves.

COMMANDS: same_spec via swebench_unified.markers.same_spec (all 8 files True). Verify: bash scripts/lean_verify.sh <file>. Resolve: swebench_unified.harness.run_resolve.

### EXECUTED RESULTS (verify):
- atk_1.lean (prepatch: clears models only, leaves swappable) -> FAIL exit 1: 'unsolved goals ... swappableOccupancyOld = 0'. PREPATCH BUG REPRODUCED (spec senses the gold change; matches Solution_prepatch.lean & G-DIFF).
- atk_2.lean (swappableOccupancy := 1) -> FAIL exit 1: '1 = 0'. (boundary/nonzero-constant)
- atk_3.lean (clears swappable only, leaves models) -> FAIL exit 1: 'modelsOccupancyOld = 0'. (mirror partial-domain)
- atk_4.lean (if models=swappable then both:=0 else models:=0 only) -> FAIL exit 1: on the else branch 'swappableOccupancyOld = 0'. (control-flow-effect)
- atk_6.lean (echo: modelsOccupancy := 0*modelsOccupancy; swappableOccupancy := swappableOccupancy - swappableOccupancy) -> VERIFIES exit 0.
- atk_7.lean (echo: swappableOccupancy := 0; modelsOccupancy := swappableOccupancy) -> VERIFIES exit 0.
- pos_control.lean (= frozen Solution.lean) -> VERIFIES exit 0.

### EXECUTED RESULTS (resolve, run_resolve on the FAITHFUL refined patch):
- atk_6 & atk_7 are behaviorally the gold: both terminate with modelsOccupancy=0 AND swappableOccupancy=0, which under the R+A-reference map = self.get_models.cache_clear() + self.get_swappable_settings_name.cache_clear(). Their faithful refined patch is therefore the gold two-line change (patch_echo.diff). run_resolve => RESOLVED: True, COMPLETED: True; FAIL_TO_PASS test_clear_cache success, all 43 PASS_TO_PASS success. => correct echoes, NOT a weakness (build_one.py:313-314).

DIVERGENCE PROBE (examined, reported, NOT submitted as a gating attack): atk_5.lean (`while true do modelsOccupancy := modelsOccupancy; return ()`) is same_spec=True and VERIFIES (exit 0) purely by partial-correctness vacuity (the postcondition is never reached). I materialized its faithful transliteration patch_atk5.diff (`while True: pass` at the top of clear_cache, clearing nothing) and RAN it: run_resolve => RESOLVED: False, COMPLETED: False, note 'no report ... harness error or image pull failure' (the infinite loop hangs the container). This is the framework's INCONCLUSIVE case (build_one.py:310-312, `not r.completed`), NOT the BROKEN case (`r.completed and not r.resolved`, line 306). A diverging program never emits a false 'resolved', so it does not demonstrate verify⇏ correct. Divergence is a semantics-generic artifact of the FROZEN `termination "partial"` option (401/500 velvet bundles use it; spec_guide.md sanctions it), not a defect in this bundle's refinement map or A-legs. Submitting it would force a spurious INCONCLUSIVE; excluded on that basis and documented here for full transparency. atk_5.lean and patch_atk5.diff remain in the scratch dir.

REFINEMENT.md AUDIT (no kind-3): A1 = R (Apps instance -> the two touched cache occupancies). A2 = R + A-reference (swappableOccupancy:=0 <-> get_swappable_settings_name.cache_clear(), the gold-ADDED line). A3 = R + A-reference (modelsOccupancy:=0 <-> get_models.cache_clear(), pre-existing). The sole external fact is the A-reference 'functools.cache cache_clear() => cache_info().currsize==0', validated executably by axiom_check.py (G-AX): EXECUTED => exit 0, 'boundary + 2000 fuzz ... from every tested starting occupancy'. Model<->patch correspondence confirmed against (registry.py:166 @lru_cache get_models, :277 @lru_cache get_swappable_settings_name, clear_cache at :363; gold patch.diff adds the swappable clear verbatim). The post-clear model-expiry loop touches neither functools wrapper, so both currsize are 0 unconditionally after clear_cache — matching the unconditional `=0` postconditions. No consumed axiom; no kind-3 unexpressible-changed-op leg.

CONCLUSION: 6 distinct same-spec attacks run (>=5 floor met): 4 rejected by the spec (partial-domain/boundary/control-flow), 2 verifying echoes whose faithful patches RESOLVE (executed). Prepatch bug reproduced; positive control verifies; A-reference validated; no kind-3 leg. No verifying same-spec impl has a completing faithful patch that fails to resolve. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True under velvet backend); Solution.lean verifies (lean_verify exit 0); prepatch fails G-DIFF on the swappableOccupancy=0 clause. Faithfulness check: the modeled clearAllCaches pins both cache-occupancy counters to 0 unconditionally. Verified against the real repo at base_commit (django/apps/registry.py:370): patched clear_cache() calls self.get_models.cache_clear() and self.get_swappable_settings_name.cache_clear() BOTH unconditionally (the swappable clear is added at the top, before the `if self.ready:` guard). The `if self.ready:` expiry loop iterates app_config.get_models(...) — an AppConfig method, NOT the two @functools.cache-wrapped registry methods — so it never refills either wrapper (confirmed by the in-code 'Circumvent self.get_models() to prevent that the cache is refilled' comment). Empirically confirmed functools._lru_cache_wrapper.cache_clear() drives cache_info().currsize to 0 from any prior occupancy (37->0) and clearing an empty cache stays 0. Thus for every input (any prior occupancy, any self.ready state) the real callee leaves both currsize == 0, exactly the two postconditions. The unconditional `= 0` is not too strong; no diverging input exists. Abstraction omits only Apps state the F2P test test_clear_cache never observes.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified via markers.spec_view with velvet backend; impl+proof regions confirmed elided) reveals nothing about the gold edit beyond the public problem_statement. The problem_statement already states verbatim: 'Apps.clear_cache() does not clear get_swappable_settings_name cache', that it is a functools._lru_cache_wrapper, that '.clear_cache doc states: Clear all internal caches', and even proposes the exact fix line 'self.get_swappable_settings_name.cache_clear()'. The spec view only abstracts this: it models two memoizing methods (the all-models and swappable-settings-name lookups — both public), states the reset must zero every cache's occupancy (public 'Clear all internal caches'), and postconditions modelsOccupancy=0 / swappableOccupancy=0. No functools/cache_clear internals or gold-patch line text appear in the visible spec. same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True, so the frozen spec region is byte-identical across patched/prepatch — the gold edit lives only in the elided impl. No spec-view line discloses the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
