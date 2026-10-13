# P2 adversarial audit — pytest-dev__pytest-10081

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The spec fully pins the output (ensures out = shouldDefer debuggerActive unitSkipped groupSkipped, a total 3-input boolean function). Every verifying impl must compute exactly debuggerActive && !(unitSkipped || groupSkipped); its faithful refinement via mapping.md is the gold guard, which resolves.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,8 +51,7 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
+    let skipped : Bool := unitSkipped
     if debuggerActive && !skipped then
       return true
     else
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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,12 +51,7 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
-    if debuggerActive && !skipped then
-      return true
-    else
-      return false
+    return debuggerActive
     -- impl-end
 
 prove_correct shouldDeferCleanup by
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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,8 +51,7 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
+    let skipped : Bool := unitSkipped && groupSkipped
     if debuggerActive && !skipped then
       return true
     else
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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,12 +51,11 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
     let skipped : Bool := unitSkipped || groupSkipped
     if debuggerActive && !skipped then
+      return false
+    else
       return true
-    else
-      return false
     -- impl-end
 
 prove_correct shouldDeferCleanup by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,12 +51,7 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
-    if debuggerActive && !skipped then
-      return true
-    else
-      return false
+    return shouldDefer debuggerActive unitSkipped groupSkipped
     -- impl-end
 
 prove_correct shouldDeferCleanup by
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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,12 +51,7 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
-    if debuggerActive && !skipped then
-      return true
-    else
-      return false
+    return true
     -- impl-end
 
 prove_correct shouldDeferCleanup by
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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,12 +51,8 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
     let skipped : Bool := unitSkipped || groupSkipped
-    if debuggerActive && !skipped then
-      return true
-    else
-      return false
+    return !skipped
     -- impl-end
 
 prove_correct shouldDeferCleanup by
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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,10 +51,11 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
-    if debuggerActive && !skipped then
-      return true
+    if debuggerActive then
+      if unitSkipped || groupSkipped then
+        return false
+      else
+        return true
     else
       return false
     -- impl-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The decision modeled here consumes two unchanged helpers
@@ -51,8 +51,7 @@
   ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
   do
     -- impl-start
-    -- A test is "skipped" if it is skipped directly or its enclosing group is.
-    let skipped : Bool := unitSkipped || groupSkipped
+    let skipped : Bool := groupSkipped
     if debuggerActive && !skipped then
       return true
     else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The decision modeled here consumes two unchanged helpers
   purely for their boolean results (whether an interactive debugger is active,
   and whether a unit / its enclosing group carries the skip marker). Those
   results are taken directly as the `Bool` inputs of the modeled decision — an
   R-identity refinement validated against the real helpers by G-CONF, not an
   axiom (mapping.md §3). There is no module-level `axiom` and no `:|` stub. -/
-- axioms-end

-- pure-start
/- Whether to postpone a test's post-run cleanup step.

   When an interactive debugger is active we want to postpone the cleanup so the
   debugger can inspect the instance state before it is torn down. But cleanup
   must be postponed ONLY for tests that are actually going to run: a test that
   is being skipped must not have its cleanup postponed, because a postponed
   cleanup would then be forced to run out of band — and that is undefined for a
   skipped test.

   A test counts as skipped when it is skipped directly OR when the enclosing
   group it belongs to is skipped; both must suppress the postponement. -/
def shouldDefer (debuggerActive unitSkipped groupSkipped : Bool) : Bool :=
  debuggerActive && !(unitSkipped || groupSkipped)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for a single test about to be executed, whether its post-run cleanup
   step is postponed so an active interactive debugger can inspect state.

   Desired behaviour: postpone the cleanup exactly when the debugger is active
   AND the test is not being skipped, where "skipped" covers both the test being
   skipped directly and its enclosing group being skipped. If either form of
   skip applies, the cleanup must NOT be postponed even when the debugger is
   active (a postponed cleanup for a skipped test would otherwise be forced to
   run and fail). -/
method shouldDeferCleanup (debuggerActive : Bool) (unitSkipped : Bool) (groupSkipped : Bool)
    return (out : Bool)
  ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
  do
    -- impl-start
    -- A test is "skipped" if it is skipped directly or its enclosing group is.
    let skipped : Bool := unitSkipped || groupSkipped
    if debuggerActive && !skipped then
      return true
    else
      return false
    -- impl-end

prove_correct shouldDeferCleanup by
  loom_solve <;>
    cases debuggerActive <;> cases unitSkipped <;> cases groupSkipped <;>
      simp_all [shouldDefer]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed 9 same-spec attacks built by editing ONLY the impl region (axioms/pure/pre/post byte-identical; same_spec=True for all 9 + positive control, verified via swebench_unified.markers.same_spec on velvet backend).

VERIFY results (bash scripts/lean_verify.sh atk_N.lean):
- pos_control.lean (gold-faithful, Solution.lean copy): exit 0 (VERIFIES).
- atk_1 (prepatch bug: skipped:=unitSkipped, group ignored): exit 1 (FAILS) — PREPATCH REPRODUCED.
- atk_2 (partial-domain: return debuggerActive): exit 1 (FAILS).
- atk_3 (boundary: skipped:=unitSkipped && groupSkipped): exit 1 (FAILS).
- atk_4 (control-flow-effect: branch returns inverted): exit 1 (FAILS).
- atk_5 (ungrounded-oracle echo: return shouldDefer ...): exit 0 (VERIFIES).
- atk_6 (constant: return true): exit 1 (FAILS).
- atk_7 (drop debugger guard: return !skipped): exit 1 (FAILS).
- atk_8 (alt control-flow: nested if computing same function): exit 0 (VERIFIES).
- atk_9 (partial-domain: skipped:=groupSkipped only): exit 1 (FAILS).

Only the two SEMANTICALLY-CORRECT impls verify (atk_5 deep-model echo, atk_8 nested-if computing the identical boolean function) — expected, since the ensures clause pins the output with zero freedom. Per protocol I materialized their faithful refined patches and RAN them through the official harness (swebench_unified.harness.run_resolve, instance pytest-dev__pytest-10081, timeout 1800):
- atk_5_patch.diff (deep-model refined via mapping = gold guard; = patch.diff verbatim): RESOLVED=True COMPLETED=True attempts=1 flaky=False.
- atk_8_patch.diff (faithful nested-if refinement: assert parent; if usepdb: if not (_is_skipped(self.obj) or _is_skipped(self.parent.obj)): postpone): RESOLVED=True COMPLETED=True attempts=1 flaky=False.
Both patches validated with git apply --check against src/_pytest/unittest.py at base_commit da9a2b584eb7a6c7e924b2621ed0ddaeca0a7bea (context lines confirmed matching). No verifying wrong impl's faithful patch fails to resolve => verify⇒correct holds; spec NOT broken.

refinement.md audit: legs are steps 1-3 R (bool<->Bool identity for getoption/_is_skipped results), steps 4-5 I (||/&&/not transliteration). NO A-legs (confirmed: no module-level `axiom`, no `:|` stub in Solution.lean; G-AX correctly skips). No kind-3 (inexpressible-changed-op) legs. Model<->patch correspondence VALID: deep model shouldDefer = debuggerActive && !(unitSkipped || groupSkipped); mapping.md §2/§3 binds debuggerActive<->getoption("usepdb"), unitSkipped<->_is_skipped(self.obj), groupSkipped<->_is_skipped(self.parent.obj) — exactly the gold guard skipped=_is_skipped(self.obj) or _is_skipped(self.parent.obj); if usepdb and not skipped. Correspondence to the real _is_skipped callee holds (leaf helper, unchanged; patch only adds a second call site). R/I burden carried by G-CONF (100008 inputs, 0 disagreements, per meta.json).

Verdict SOUND: ≥5 distinct wrong-impl attacks run (6 genuine wrong impls all fail verify + prepatch reproduced); the only 2 impls that verify are correct and their materialized faithful patches both RESOLVE under the official harness. No falsification found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The spec fully pins the output (ensures out = shouldDefer debuggerActive unitSkipped groupSkipped, a total 3-input boolean function). Every verifying impl must compute exactly debuggerActive && !(unitSkipped || groupSkipped); its faithful refinement via mapping.md is the gold guard, which resolves.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The decision modeled here consumes two unchanged helpers
   purely for their boolean results (whether an interactive debugger is active,
   and whether a unit / its enclosing group carries the skip marker). Those
   results are taken directly as the `Bool` inputs of the modeled decision — an
   R-identity refinement validated against the real helpers by G-CONF, not an
   axiom (mapping.md §3). There is no module-level `axiom` and no `:|` stub. -/
-- axioms-end

-- pure-start
/- Whether to postpone a test's post-run cleanup step.

   When an interactive debugger is active we want to postpone the cleanup so the
   debugger can inspect the instance state before it is torn down. But cleanup
   must be postponed ONLY for tests that are actually going to run: a test that
   is being skipped must not have its cleanup postponed, because a postponed
   cleanup would then be forced to run out of band — and that is undefined for a
   skipped test.

   A test counts as skipped when it is skipped directly OR when the enclosing
   group it belongs to is skipped; both must suppress the postponement. -/
def shouldDefer (debuggerActive unitSkipped groupSkipped : Bool) : Bool :=
  debuggerActive && !(unitSkipped || groupSkipped)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for a single test about to be executed, whether its post-run cleanup
   step is postponed so an active interactive debugger can inspect state.

   Desired behaviour: postpone the cleanup exactly when the debugger is active
   AND the test is not being skipped, where "skipped" covers both the test being
   skipped directly and its enclosing group being skipped. If either form of
   skip applies, the cleanup must NOT be postponed even when the debugger is
   active (a postponed cleanup for a skipped test would otherwise be forced to
   run and fail). -/
method shouldDeferCleanup (debuggerActive : Bool) (unitSkipped : Bool) (groupSkipped : Bool)
    return (out : Bool)
  ensures out = shouldDefer debuggerActive unitSkipped groupSkipped
  do
    -- impl-start
    -- A test is "skipped" if it is skipped directly or its enclosing group is.
    let skipped : Bool := unitSkipped || groupSkipped
    if debuggerActive && !skipped then
      return true
    else
      return false
    -- impl-end

prove_correct shouldDeferCleanup by
  loom_solve <;>
    cases debuggerActive <;> cases unitSkipped <;> cases groupSkipped <;>
      simp_all [shouldDefer]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed 9 same-spec attacks built by editing ONLY the impl region (axioms/pure/pre/post byte-identical; same_spec=True for all 9 + positive control, verified via swebench_unified.markers.same_spec on velvet backend).

VERIFY results (bash scripts/lean_verify.sh atk_N.lean):
- pos_control.lean (gold-faithful, Solution.lean copy): exit 0 (VERIFIES).
- atk_1 (prepatch bug: skipped:=unitSkipped, group ignored): exit 1 (FAILS) — PREPATCH REPRODUCED.
- atk_2 (partial-domain: return debuggerActive): exit 1 (FAILS).
- atk_3 (boundary: skipped:=unitSkipped && groupSkipped): exit 1 (FAILS).
- atk_4 (control-flow-effect: branch returns inverted): exit 1 (FAILS).
- atk_5 (ungrounded-oracle echo: return shouldDefer ...): exit 0 (VERIFIES).
- atk_6 (constant: return true): exit 1 (FAILS).
- atk_7 (drop debugger guard: return !skipped): exit 1 (FAILS).
- atk_8 (alt control-flow: nested if computing same function): exit 0 (VERIFIES).
- atk_9 (partial-domain: skipped:=groupSkipped only): exit 1 (FAILS).

Only the two SEMANTICALLY-CORRECT impls verify (atk_5 deep-model echo, atk_8 nested-if computing the identical boolean function) — expected, since the ensures clause pins the output with zero freedom. Per protocol I materialized their faithful refined patches and RAN them through the official harness (swebench_unified.harness.run_resolve, instance pytest-dev__pytest-10081, timeout 1800):
- atk_5_patch.diff (deep-model refined via mapping = gold guard; = patch.diff verbatim): RESOLVED=True COMPLETED=True attempts=1 flaky=False.
- atk_8_patch.diff (faithful nested-if refinement: assert parent; if usepdb: if not (_is_skipped(self.obj) or _is_skipped(self.parent.obj)): postpone): RESOLVED=True COMPLETED=True attempts=1 flaky=False.
Both patches validated with git apply --check against src/_pytest/unittest.py at base_commit da9a2b584eb7a6c7e924b2621ed0ddaeca0a7bea (context lines confirmed matching). No verifying wrong impl's faithful patch fails to resolve => verify⇒correct holds; spec NOT broken.

refinement.md audit: legs are steps 1-3 R (bool<->Bool identity for getoption/_is_skipped results), steps 4-5 I (||/&&/not transliteration). NO A-legs (confirmed: no module-level `axiom`, no `:|` stub in Solution.lean; G-AX correctly skips). No kind-3 (inexpressible-changed-op) legs. Model<->patch correspondence VALID: deep model shouldDefer = debuggerActive && !(unitSkipped || groupSkipped); mapping.md §2/§3 binds debuggerActive<->getoption("usepdb"), unitSkipped<->_is_skipped(self.obj), groupSkipped<->_is_skipped(self.parent.obj) — exactly the gold guard skipped=_is_skipped(self.obj) or _is_skipped(self.parent.obj); if usepdb and not skipped. Correspondence to the real _is_skipped callee holds (leaf helper, unchanged; patch only adds a second call site). R/I burden carried by G-CONF (100008 inputs, 0 disagreements, per meta.json).

Verdict SOUND: ≥5 distinct wrong-impl attacks run (6 genuine wrong impls all fail verify + prepatch reproduced); the only 2 impls that verify are correct and their materialized faithful patches both RESOLVE under the official harness. No falsification found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True with velvet LanguageTables). Solution.lean elaborates with no sorry/error (lean_verify.sh exit 0).

Modeled function: shouldDefer d u g = d && !(u || g), and method shouldDeferCleanup ensures out = shouldDefer. Real patched behavior at base_commit da9a2b5 (src/_pytest/unittest.py:319, gold patch applied): postpone = config.getoption('usepdb') and not (_is_skipped(self.obj) or _is_skipped(self.parent.obj)). Under the bool<->Bool bijection (debuggerActive<-usepdb truthiness, unitSkipped<-_is_skipped(self.obj), groupSkipped<-_is_skipped(self.parent.obj)) the two agree on every input:
  (F,*,*)->F=F; (T,F,F)->T=T; (T,T,F)->F=F; (T,F,T)->F=F; (T,T,T)->F=F.
No input where the spec is stronger/weaker than the real callee — the spec is exactly the patched guard.

_is_skipped (unittest.py:412) = bool(getattr(obj,'__unittest_skip__',False)) is a pure, unchanged leaf helper; the patch only adds a second call site (self.parent.obj), not a modification. Modeling its result as an R-identity Bool input is faithful, and conformance_check.py routes inputs through the REAL _is_skipped over varied truthy/falsy/missing marker encodings (seed 10081, 100008 inputs) — the R-legs are exercised, not assumed. The added `assert isinstance(self.parent, UnitTestCase)` is a type invariant (TestCaseFunction's parent is always UnitTestCase) with no observable behavior — correctly unmodeled.

No spec-too-strong drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: velvet/pytest-dev__pytest-10081. same_spec(Solution.lean, Solution_prepatch.lean) = True (frozen spec byte-identical). Mechanical G-LEAK screen: passed, no hard_failures, no warnings; meta.json G-LEAK status=pass; not relaxed.

Gold edit: broadens the --pdb teardown-postponement guard from `_is_skipped(self.obj)` to `_is_skipped(self.obj) or _is_skipped(self.parent.obj)`, i.e. a class-level @unittest.skip must also suppress postponing (and then force-running) the tearDown.

The public problem_statement ALREADY fully discloses this: title 'tearDown executed for classes marked with unittest.skip when running --pdb' and body 'Running pytest --pdb will run the tearDown() of unittest.TestCase classes that are decorated with unittest.skip on the class level', explicitly contrasting the class-level case with the function-level #7215. So the desired behavior (class-level skip must suppress teardown under --pdb) is entirely public, not a leak.

Spec-view review beyond problem_statement:
- Pure spec `shouldDefer := debuggerActive && !(unitSkipped || groupSkipped)` and the `ensures` postcondition encode exactly the publicly-described desired behavior — inherent to any Velvet spec benchmark (spec states behavior; impl/proof elided). No hidden discriminator.
- All spec-view identifiers are abstract (shouldDeferCleanup, debuggerActive, unitSkipped, groupSkipped, shouldDefer); NONE echo the patched repo symbols (_is_skipped, runtest, self.parent.obj, usepdb, _explicit_tearDown, tearDown), so no edit-localization / symbol-collision leak.
- No diff markers, no patched file path (src/_pytest/unittest.py), no line numbers in the spec view.
- Doc-comment rationale ('enclosing group skipped ... must suppress the postponement') restates the public issue's headline concept in conceptual terms; no bug/fix/regression narration tokens.

Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already states. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
