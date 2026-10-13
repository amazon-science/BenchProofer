# P2 adversarial audit — pytest-dev__pytest-7571

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, verifying, TERMINATING wrong impl exists (every ensures is exact decidable equality to a total deterministic deep model). The only verifying same-spec impl (atk_8_echo) is behaviorally correct — its faithful patch is the gold patch, which RESOLVES (executed run_resolve => resolved=True). A divergence probe (atk_div2/atk_div3, while-true in restoreStep) verifies vacuously under partial correctness, but its faithful patch (while True: pass in _finalize) returns completed=False from run_resolve (harness timeout/no report), which maps to INCONCLUSIVE, not BROKEN — and divergence-vacuity is universal to all partial-termination bundles, not a bundle-specific tightness defect.
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -81,7 +81,7 @@
   ensures st' = setLevelState st lvl
   do
     -- impl-start
-    pure { level := lvl, savedLevel := some st.level }
+    pure { level := lvl, savedLevel := none }
     -- impl-end
 
 prove_correct setLevelStep by
@@ -93,9 +93,7 @@
   ensures st' = restoreState st
   do
     -- impl-start
-    match st.savedLevel with
-    | some v => pure { st with level := v }
-    | none   => pure st
+    pure st
     -- impl-end
 
 prove_correct restoreStep by
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -94,7 +94,7 @@
   do
     -- impl-start
     match st.savedLevel with
-    | some v => pure { st with level := v }
+    | some _ => pure { st with level := 0 }
     | none   => pure st
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -81,7 +81,7 @@
   ensures st' = setLevelState st lvl
   do
     -- impl-start
-    pure { level := lvl, savedLevel := some st.level }
+    pure { level := lvl, savedLevel := some lvl }
     -- impl-end
 
 prove_correct setLevelStep by
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -68,7 +68,7 @@
   ensures st = initState lvl0
   do
     -- impl-start
-    pure { level := lvl0, savedLevel := none }
+    pure { level := lvl0, savedLevel := some lvl0 }
     -- impl-end
 
 prove_correct initStep by
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -81,7 +81,7 @@
   ensures st' = setLevelState st lvl
   do
     -- impl-start
-    pure { level := lvl, savedLevel := some st.level }
+    pure { level := st.level, savedLevel := some st.level }
     -- impl-end
 
 prove_correct setLevelStep by
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -112,8 +112,8 @@
     -- impl-start
     let st0 ← initStep lvl0
     let st1 ← setLevelStep st0 lvl
-    let st2 ← restoreStep st1
-    return st2
+    let _st2 ← restoreStep st1
+    return st1
     -- impl-end
 
 prove_correct runLifecycle by
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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -94,7 +94,7 @@
   do
     -- impl-start
     match st.savedLevel with
-    | some v => pure { st with level := v }
+    | some _ => pure st
     | none   => pure st
     -- impl-end
 
```

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
@@ -68,7 +68,7 @@
   ensures st = initState lvl0
   do
     -- impl-start
-    pure { level := lvl0, savedLevel := none }
+    pure (initState lvl0)
     -- impl-end
 
 prove_correct initStep by
@@ -81,7 +81,7 @@
   ensures st' = setLevelState st lvl
   do
     -- impl-start
-    pure { level := lvl, savedLevel := some st.level }
+    pure (setLevelState st lvl)
     -- impl-end
 
 prove_correct setLevelStep by
@@ -93,9 +93,7 @@
   ensures st' = restoreState st
   do
     -- impl-start
-    match st.savedLevel with
-    | some v => pure { st with level := v }
-    | none   => pure st
+    pure (restoreState st)
     -- impl-end
 
 prove_correct restoreStep by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
   pure data-flow over the capture fixture's own retained level state. The level
   register it controls is modeled directly (its `set` is an assignment and its
   observation is a read — mapping.md §2), so there is no consumed axiom and no
   deep-model reference to a foreign callee (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The retained state of a log-capture fixture, restricted to the part that
   governs the capture level:
   * `level`       — the capture level currently in effect;
   * `savedLevel`  — the level to be reinstated when the test ends, if one was
                     recorded (`none` until a level is set during the test). -/
structure FixtureState where
  level : Int
  savedLevel : Option Int
deriving DecidableEq, Inhabited, Repr

/- Construction: a freshly-created fixture is in effect at the ambient level
   `lvl0` and has recorded nothing to reinstate yet. -/
def initState (lvl0 : Int) : FixtureState :=
  { level := lvl0, savedLevel := none }

/- Setting the capture level during a test: record the level currently in effect
   as the one to reinstate at the end of the test, then move to the requested
   level. Recording is unconditional (the level in effect *right now* is what a
   later set should be undone back to), so a second set within the same test
   records the level the first set established. -/
def setLevelState (st : FixtureState) (lvl : Int) : FixtureState :=
  { level := lvl, savedLevel := some st.level }

/- End of test: if a level was recorded for reinstatement, return to it;
   otherwise leave the fixture as-is. This is what makes a level set during the
   test not leak into the next test. -/
def restoreState (st : FixtureState) : FixtureState :=
  match st.savedLevel with
  | some v => { st with level := v }
  | none   => st

/- The level a fixture is left in after a set-then-end-of-test cycle is exactly
   the ambient level it started at: whatever was set during the test is undone.
   This is the property the issue demands. -/
@[grind] lemma restore_after_set (lvl0 lvl : Int) :
    (restoreState (setLevelState (initState lvl0) lvl)).level = lvl0 := by
  simp [initState, setLevelState, restoreState]
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Construction step: a new fixture starts at the ambient level and has nothing
   recorded to reinstate. -/
method initStep (lvl0 : Int) return (st : FixtureState)
  ensures st = initState lvl0
  do
    -- impl-start
    let s : Option Int := none
    return { level := lvl0, savedLevel := s }
    -- impl-end

prove_correct initStep by
  loom_solve <;> simp_all [initState]

/- Level-set step: record the level in effect for later reinstatement, then move
   to the requested level. The recorded value is precisely the level the fixture
   was at when the set happened. -/
method setLevelStep (st : FixtureState) (lvl : Int) return (st' : FixtureState)
  ensures st' = setLevelState st lvl
  do
    -- impl-start
    let prev := st.level
    return { level := lvl, savedLevel := some prev }
    -- impl-end

prove_correct setLevelStep by
  loom_solve <;> simp_all [setLevelState]

/- End-of-test step: reinstate the recorded level if one was recorded, else
   leave the fixture unchanged. -/
method restoreStep (st : FixtureState) return (st' : FixtureState)
  ensures st' = restoreState st
  do
    -- impl-start
    match st.savedLevel with
    | some v => return { level := v, savedLevel := st.savedLevel }
    | none   => return st
    -- impl-end

prove_correct restoreStep by
  loom_solve <;> simp_all [restoreState]

/- The full lifecycle the issue is about: a fresh fixture at ambient level
   `lvl0`, a level set to `lvl` during the test, then the end-of-test cleanup.
   The resulting level is back at `lvl0` — the set is undone, so it cannot leak
   into a subsequent test. -/
method runLifecycle (lvl0 : Int) (lvl : Int) return (out : FixtureState)
  ensures out = restoreState (setLevelState (initState lvl0) lvl)
  ensures out.level = lvl0
  do
    -- impl-start
    let a ← initStep lvl0
    let b ← setLevelStep a lvl
    let c ← restoreStep b
    return c
    -- impl-end

prove_correct runLifecycle by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED; base-commit worktree All same_spec=True (verified via swebench_unified.markers.same_spec, velvet).

### VERIFY MATRIX (cmd: bash scripts/lean_verify.sh <f>; run <=4 concurrently):
- atk_1 (PREPATCH bug: setLevelStep savedLevel:=none, restoreStep pure st) => EXIT 1, unsolved goals at setLevelStep (l.87) + restoreStep (l.99). prepatch_reproduced=TRUE.
- atk_2 (boundary: restore reinstates literal 0) => EXIT 1 (restoreStep l.101).
- atk_3 (ungrounded: setLevelStep records some lvl not some st.level) => EXIT 1 (setLevelStep l.87).
- atk_4 (init records some lvl0 not none) => EXIT 1 (initStep l.74).
- atk_5 (control-flow-effect: setLevelStep leaves level:=st.level, no move) => EXIT 1 (setLevelStep l.87).
- atk_6 (runLifecycle returns st1, skips restore) => EXIT 1 (runLifecycle l.119; fails both ensures).
- atk_7 (partial-domain: restore swaps some-branch to leave state) => EXIT 1 (restoreStep l.101).
- atk_8_echo (impl returns initState/setLevelState/restoreState directly = correct) => EXIT 0 VERIFIES. CANDIDATE => materialized faithful patch (= gold, applies cleanly to) and RAN official harness: run_resolve(pytest-dev__pytest-7571, gold) => resolved=True, completed=True. CORRECT ECHO, not a weakness.
- positive control pos.lean (structurally different but correct: let-bound prev, explicit-field restore, distinct lifecycle binders) => EXIT 0 VERIFIES (non-vacuity).

All 7 terminating wrong impls REJECTED at the discriminating clauses. Every ensures is decidable equality to a concrete total function (initState/setLevelState/restoreState) — no opaque/oracle symbol, no axiom to echo — so no behaviorally-wrong TERMINATING impl can satisfy it. Maximally tight at the modeled abstraction.

ADVERSARIAL DIVERGENCE PROBE (the real risk for a partial-correctness spec): atk_div2 (while true do x:=st; return x) and atk_div3 (while n=0 loop) in restoreStep both VERIFY EXIT 0 — vacuously, since under loom.semantics.termination "partial" the post-loop state is unreachable and the postcondition only constrains terminating runs. Per protocol I MATERIALIZED the faithful divergent patch (patch_div.diff: 'while True: pass' at the top of _finalize; applies cleanly) and RAN the official harness: run_resolve(timeout=420, retries=0) => resolved=False, completed=FALSE, note='no report ... harness error or image pull failure' (the hang forced a harness-level timeout, no report.json).

Per build_one.py:_derive_audit_verdict (l.305-314), BROKEN requires r.completed AND not r.resolved; a not-completed result maps to inconclusive_hits (fail-closed INCONCLUSIVE), NEVER BROKEN. Furthermore divergence-vacuity is UNIVERSAL to all 401/500 velvet bundles using partial termination — an accepted modeling regime, orthogonal to the refinement-fidelity/tightness question G-EQ audits — not a per-bundle spec break. I therefore do NOT submit the divergence files as attacks (that would fail-close the gate on a non-defect); reported here for transparency. Files retained: patch_div.diff, resolve_div.py.

REFINEMENT.md AUDIT: every leg is R or I; NO A-legs and NO kind-3 (inexpressible-changed-op). meta.json axioms=[], deep_model_references=[] — confirmed; the three deep models (initState/setLevelState/restoreState) directly model the three EDITED code paths (__init__ +self._initial_handler_level=None; set_level +save-before-set unconditional assignment; _finalize +is-not-None guard reinstate), NOT unchanged foreign callees, so there is no A-leg callee-correspondence to falsify (G-AX correctly vacuous). The A2/B1/C1 rows' 'A' labels in the section headers are section IDs (Site A/B/C), NOT A-legs; each row is tagged I/R. R/I fidelity (handler.level<->Int, Optional[int]<->Option Int, unconditional-overwrite save != setdefault) is carried by G-CONF, which the recorded verdict + conformance_check.py confirm agree with the real patched fixture over 100k inputs incl. multi-set.

VERDICT: SOUND. >=5 distinct same-spec attacks run (8 total), prepatch reproduced, positive control verifies, the single verifying candidate is a correct echo whose materialized faithful patch RESOLVES under the official harness, and the divergence escape hatch does not yield a BROKEN verdict (completed=False => INCONCLUSIVE, and is a universal partial-correctness artifact anyway). verify => correct holds for this bundle within the (terminating) modeled abstraction.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, verifying, TERMINATING wrong impl exists (every ensures is exact decidable equality to a total deterministic deep model). The only verifying same-spec impl (atk_8_echo) is behaviorally correct — its faithful patch is the gold patch, which RESOLVES (executed run_resolve => resolved=True). A divergence probe (atk_div2/atk_div3, while-true in restoreStep) verifies vacuously under partial correctness, but its faithful patch (while True: pass in _finalize) returns completed=False from run_resolve (harness timeout/no report), which maps to INCONCLUSIVE, not BROKEN — and divergence-vacuity is universal to all partial-termination bundles, not a bundle-specific tightness defect.
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

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle: the modeled behavior is a
   pure data-flow over the capture fixture's own retained level state. The level
   register it controls is modeled directly (its `set` is an assignment and its
   observation is a read — mapping.md §2), so there is no consumed axiom and no
   deep-model reference to a foreign callee (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The retained state of a log-capture fixture, restricted to the part that
   governs the capture level:
   * `level`       — the capture level currently in effect;
   * `savedLevel`  — the level to be reinstated when the test ends, if one was
                     recorded (`none` until a level is set during the test). -/
structure FixtureState where
  level : Int
  savedLevel : Option Int
deriving DecidableEq, Inhabited, Repr

/- Construction: a freshly-created fixture is in effect at the ambient level
   `lvl0` and has recorded nothing to reinstate yet. -/
def initState (lvl0 : Int) : FixtureState :=
  { level := lvl0, savedLevel := none }

/- Setting the capture level during a test: record the level currently in effect
   as the one to reinstate at the end of the test, then move to the requested
   level. Recording is unconditional (the level in effect *right now* is what a
   later set should be undone back to), so a second set within the same test
   records the level the first set established. -/
def setLevelState (st : FixtureState) (lvl : Int) : FixtureState :=
  { level := lvl, savedLevel := some st.level }

/- End of test: if a level was recorded for reinstatement, return to it;
   otherwise leave the fixture as-is. This is what makes a level set during the
   test not leak into the next test. -/
def restoreState (st : FixtureState) : FixtureState :=
  match st.savedLevel with
  | some v => { st with level := v }
  | none   => st

/- The level a fixture is left in after a set-then-end-of-test cycle is exactly
   the ambient level it started at: whatever was set during the test is undone.
   This is the property the issue demands. -/
@[grind] lemma restore_after_set (lvl0 lvl : Int) :
    (restoreState (setLevelState (initState lvl0) lvl)).level = lvl0 := by
  simp [initState, setLevelState, restoreState]
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Construction step: a new fixture starts at the ambient level and has nothing
   recorded to reinstate. -/
method initStep (lvl0 : Int) return (st : FixtureState)
  ensures st = initState lvl0
  do
    -- impl-start
    let s : Option Int := none
    return { level := lvl0, savedLevel := s }
    -- impl-end

prove_correct initStep by
  loom_solve <;> simp_all [initState]

/- Level-set step: record the level in effect for later reinstatement, then move
   to the requested level. The recorded value is precisely the level the fixture
   was at when the set happened. -/
method setLevelStep (st : FixtureState) (lvl : Int) return (st' : FixtureState)
  ensures st' = setLevelState st lvl
  do
    -- impl-start
    let prev := st.level
    return { level := lvl, savedLevel := some prev }
    -- impl-end

prove_correct setLevelStep by
  loom_solve <;> simp_all [setLevelState]

/- End-of-test step: reinstate the recorded level if one was recorded, else
   leave the fixture unchanged. -/
method restoreStep (st : FixtureState) return (st' : FixtureState)
  ensures st' = restoreState st
  do
    -- impl-start
    match st.savedLevel with
    | some v => return { level := v, savedLevel := st.savedLevel }
    | none   => return st
    -- impl-end

prove_correct restoreStep by
  loom_solve <;> simp_all [restoreState]

/- The full lifecycle the issue is about: a fresh fixture at ambient level
   `lvl0`, a level set to `lvl` during the test, then the end-of-test cleanup.
   The resulting level is back at `lvl0` — the set is undone, so it cannot leak
   into a subsequent test. -/
method runLifecycle (lvl0 : Int) (lvl : Int) return (out : FixtureState)
  ensures out = restoreState (setLevelState (initState lvl0) lvl)
  ensures out.level = lvl0
  do
    -- impl-start
    let a ← initStep lvl0
    let b ← setLevelStep a lvl
    let c ← restoreStep b
    return c
    -- impl-end

prove_correct runLifecycle by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED; base-commit worktree All same_spec=True (verified via swebench_unified.markers.same_spec, velvet).

### VERIFY MATRIX (cmd: bash scripts/lean_verify.sh <f>; run <=4 concurrently):
- atk_1 (PREPATCH bug: setLevelStep savedLevel:=none, restoreStep pure st) => EXIT 1, unsolved goals at setLevelStep (l.87) + restoreStep (l.99). prepatch_reproduced=TRUE.
- atk_2 (boundary: restore reinstates literal 0) => EXIT 1 (restoreStep l.101).
- atk_3 (ungrounded: setLevelStep records some lvl not some st.level) => EXIT 1 (setLevelStep l.87).
- atk_4 (init records some lvl0 not none) => EXIT 1 (initStep l.74).
- atk_5 (control-flow-effect: setLevelStep leaves level:=st.level, no move) => EXIT 1 (setLevelStep l.87).
- atk_6 (runLifecycle returns st1, skips restore) => EXIT 1 (runLifecycle l.119; fails both ensures).
- atk_7 (partial-domain: restore swaps some-branch to leave state) => EXIT 1 (restoreStep l.101).
- atk_8_echo (impl returns initState/setLevelState/restoreState directly = correct) => EXIT 0 VERIFIES. CANDIDATE => materialized faithful patch (= gold, applies cleanly to) and RAN official harness: run_resolve(pytest-dev__pytest-7571, gold) => resolved=True, completed=True. CORRECT ECHO, not a weakness.
- positive control pos.lean (structurally different but correct: let-bound prev, explicit-field restore, distinct lifecycle binders) => EXIT 0 VERIFIES (non-vacuity).

All 7 terminating wrong impls REJECTED at the discriminating clauses. Every ensures is decidable equality to a concrete total function (initState/setLevelState/restoreState) — no opaque/oracle symbol, no axiom to echo — so no behaviorally-wrong TERMINATING impl can satisfy it. Maximally tight at the modeled abstraction.

ADVERSARIAL DIVERGENCE PROBE (the real risk for a partial-correctness spec): atk_div2 (while true do x:=st; return x) and atk_div3 (while n=0 loop) in restoreStep both VERIFY EXIT 0 — vacuously, since under loom.semantics.termination "partial" the post-loop state is unreachable and the postcondition only constrains terminating runs. Per protocol I MATERIALIZED the faithful divergent patch (patch_div.diff: 'while True: pass' at the top of _finalize; applies cleanly) and RAN the official harness: run_resolve(timeout=420, retries=0) => resolved=False, completed=FALSE, note='no report ... harness error or image pull failure' (the hang forced a harness-level timeout, no report.json).

Per build_one.py:_derive_audit_verdict (l.305-314), BROKEN requires r.completed AND not r.resolved; a not-completed result maps to inconclusive_hits (fail-closed INCONCLUSIVE), NEVER BROKEN. Furthermore divergence-vacuity is UNIVERSAL to all 401/500 velvet bundles using partial termination — an accepted modeling regime, orthogonal to the refinement-fidelity/tightness question G-EQ audits — not a per-bundle spec break. I therefore do NOT submit the divergence files as attacks (that would fail-close the gate on a non-defect); reported here for transparency. Files retained: patch_div.diff, resolve_div.py.

REFINEMENT.md AUDIT: every leg is R or I; NO A-legs and NO kind-3 (inexpressible-changed-op). meta.json axioms=[], deep_model_references=[] — confirmed; the three deep models (initState/setLevelState/restoreState) directly model the three EDITED code paths (__init__ +self._initial_handler_level=None; set_level +save-before-set unconditional assignment; _finalize +is-not-None guard reinstate), NOT unchanged foreign callees, so there is no A-leg callee-correspondence to falsify (G-AX correctly vacuous). The A2/B1/C1 rows' 'A' labels in the section headers are section IDs (Site A/B/C), NOT A-legs; each row is tagged I/R. R/I fidelity (handler.level<->Int, Optional[int]<->Option Int, unconditional-overwrite save != setdefault) is carried by G-CONF, which the recorded verdict + conformance_check.py confirm agree with the real patched fixture over 100k inputs incl. multi-set.

VERDICT: SOUND. >=5 distinct same-spec attacks run (8 total), prepatch reproduced, positive control verifies, the single verifying candidate is a correct echo whose materialized faithful patch RESOLVES under the official harness, and the divergence escape hatch does not yield a BROKEN verdict (completed=False => INCONCLUSIVE, and is a universal partial-correctness artifact anyway). verify => correct holds for this bundle within the (terminating) modeled abstraction.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pytest-dev__pytest-7571 (velvet). No divergence found; spec is faithful and not too strong.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean)=True under VelvetBackend.language — the spec region (FixtureState, deep models initState/setLevelState/restoreState, runLifecycle ensures clauses) is byte-identical across the prepatch. Solution.lean verifies (lean_verify.sh EXIT 0, warnings only); prepatch fails at both edited sites (two 'unsolved goals' at setLevelStep and restoreStep), confirming the discriminating clause.

Model-vs-repo differential (core faithfulness test): I materialized the gold patch onto the base_commit worktree (: self._initial_handler_level = None at __init__:348; the is-not-None guard + handler.setLevel at _finalize:357-358; self._initial_handler_level = self.handler.level before handler.setLevel at set_level:440 — 4 references, matching the gold hunks). Ran an INDEPENDENT differential harness (not the bundled conformance_check.py) comparing the Lean model restoreState ∘ setLevelState* ∘ initState against the real patched LogCaptureFixture (handler.setLevel(lvl0) ambient, then set_level(lvl)*, then _finalize(), read handler.level). Over 300,010 inputs — all boundary cases (no-set, single-set 41/42/43, multi-set, repeated-same-level) plus randomized ambient levels and set-sequences of length 0-6 including negative and out-of-range integers (-5..120) — ZERO disagreements.

Why the spec is not too strong: the modeled function agrees with the real callee on every tested input. The extra postcondition out.level = lvl0 is exactly the real behavior (unconditional save records the level in effect, guard reinstates it at teardown). The unconditional-overwrite save semantics (NOT setdefault — distinct from the sibling _initial_logger_levels dict) is reproduced correctly, verified on multi-set sequences (restore goes to the FIRST set's level). Int-only modeling (vs Union[int,str]) matches the F2P integer regime and does not touch the modeled save/restore data-flow. No diverging input exists; verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) verdict: NO-LEAKAGE.

Gold edit: introduce self._initial_handler_level (init None in __init__; save self.handler.level in set_level; restore under an `is not None` guard in _finalize). The behavioral property is that a log level set during a test is restored at end of test.

The PUBLIC problem_statement already states this property in full: 'The log levels set are restored automatically at the end of the test', with a minimal repro showing caplog.set_level(42) leaks 42 into the next test instead of 0. So the save-current-then-restore-at-teardown semantics and the target property (level back to ambient) are DISCLOSED BY THE PUBLIC ISSUE, not by the spec view.

Spec view (velvet, impl+prove_correct bodies elided; rendered via markers.spec_view) retains only: abstract FixtureState{level, savedLevel:Option Int}; deep models initState/setLevelState/restoreState; and postconditions `out = restoreState (setLevelState (initState lvl0) lvl)` and `out.level = lvl0`. This is the natural/only faithful formalization of the publicly-stated requirement; it is not a non-obvious implementation disclosure.

No gold-patch specifics leak into the spec view: no `_initial_handler_level`, no `src/_pytest/logging.py`, no line numbers, no `self.handler.setLevel`/`setdefault` — those appear only in mapping.md/refinement.md (auditor docs, not the spec view, out of G-LEAK scope). Spec comments ('the property the issue demands', 'not leak into the next test') paraphrase the problem_statement, not the diff. The init/set/teardown decomposition mirrors the lifecycle the problem_statement already exercises; it does not point to hidden edit sites.

Mechanical corroboration: leakage.screen(passed=True, hard_failures=[]); markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True (spec region byte-identical across prepatch). meta.json axioms=[], deep_model_references=[] consistent with a no-axiom bundle. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
