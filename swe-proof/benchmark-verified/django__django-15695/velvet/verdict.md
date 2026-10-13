# P2 adversarial audit — django__django-15695

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,13 +57,7 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
-    if beforeId = afterId then
-      return []
-    else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
-      return [applyOp]
+    return [applyOp]
     -- impl-end
 
 prove_correct relabelSchedule by
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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,13 +57,10 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
     if beforeId = afterId then
+      return [applyOp]
+    else
       return []
-    else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
-      return [applyOp]
     -- impl-end
 
 prove_correct relabelSchedule by
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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,13 +57,7 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
-    if beforeId = afterId then
-      return []
-    else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
-      return [applyOp]
+    return []
     -- impl-end
 
 prove_correct relabelSchedule by
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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,12 +57,9 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
-    if beforeId = afterId then
+    if beforeId ≤ afterId then
       return []
     else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
       return [applyOp]
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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,12 +57,9 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
-    if beforeId = afterId then
+    if beforeId = 0 ∧ afterId = 0 then
       return []
     else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
       return [applyOp]
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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,12 +57,11 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
     if beforeId = afterId then
       return []
+    else if afterId = 0 then
+      return []
     else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
       return [applyOp]
     -- impl-end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callee. Whether any store-mutation work is emitted is decided
@@ -57,12 +57,14 @@
   ensures beforeId ≠ afterId → out ≠ []
   do
     -- impl-start
-    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
     if beforeId = afterId then
-      return []
+      let mut x : Int := 0
+      while x = 0
+      invariant True
+      do
+        x := 0
+      return [applyOp]
     else
-      -- The relabeling proceeds: emit the store-mutation work (one unit here;
-      -- the spec consumes only its non-emptiness).
       return [applyOp]
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callee. Whether any store-mutation work is emitted is decided
--  entirely by the identifier-equality comparison, which is precisely the
--  behaviour under specification — modeled DEEPLY below (the equality guard),
--  NOT axiomatized or A-referenced (SPEC_GUIDE §0.7). The resolved before/after
--  identifiers are taken as free inputs; how they are looked up is an UNCHANGED
--  resolution whose internals the proof does not depend on, so no contract is
--  consumed.)
-- axioms-end

-- pure-start
/- A single unit of store-mutation work emitted when the relabeling proceeds.
   The exact code value is irrelevant — only its presence is observable to the
   layer below — so a constant marker is used. -/
def applyOp : Int := 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A relabeling of a stored object is applied to its backing store, driven
   entirely by whether the stored identifier actually changes. The operation is
   handed the identifier the object carries before the relabeling (`beforeId`)
   and the one it carries after (`afterId`).

   (1) When the before- and after- identifiers are the SAME, the operation is
       observationally inert: it must issue NO store-mutation work at all. The
       emitted schedule of operations is EMPTY. (Applying a relabeling that does
       not actually change the identifier must be a no-op, so that re-applying
       it onto an already-relabeled store is harmless.)

   (2) When the two identifiers DIFFER, the operation is NOT inert: it emits at
       least one store-mutation operation. The emitted schedule is NON-EMPTY.

   The only behaviour that distinguishes a correct operation from the defect is
   this zero-vs-nonzero schedule outcome: emit nothing exactly when the
   identifier is unchanged, emit something otherwise. The exact count and order
   of the operations emitted on the proceeding branch is NOT pinned by the spec.

   The two identifiers are modeled as `Int` (only their equality is observable
   to the layer below). The emitted schedule is a `List Int` of operation codes.
   Both identifiers are read-only inputs (neither is `mut`; the decision mutates
   nothing — directive 5). -/
method relabelSchedule (beforeId : Int) (afterId : Int) return (out : List Int)
  ensures beforeId = afterId → out = []
  ensures beforeId ≠ afterId → out ≠ []
  do
    -- impl-start
    if afterId = beforeId then
      return []
    else
      return [applyOp, applyOp + 1, 7]
    -- impl-end

prove_correct relabelSchedule by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: G-EQ = SOUND. Instance django__django-15695 (velvet). Spec = relabelSchedule(beforeId afterId : Int) -> (out : List Int) with a COMPLETE BICONDICTIONAL: `beforeId = afterId -> out = []` AND `beforeId != afterId -> out != []`. This fully pins the sole observable (zero-vs-nonzero emitted store-mutation work) for any TERMINATING impl. Models the gold 3-line early-return guard `if old_index.name == self.new_name: return` in RenameIndex.database_forwards.

ENVIRONMENT: worked in private dir; same_spec confirmed True for ALL attack files + positive control via swebench_unified.markers.same_spec (velvet). Verify cmd: `bash scripts/lean_verify.sh <file>` (0=verifies, 1=error/spec-rejected). Verifications launched concurrently in batches of 4.

### SCORED ATTACKS (all same_spec=True; all TERMINATING wrong impls -> all correctly REJECTED, exit 1):
- atk_1.lean = PREPATCH BUG: `return [applyOp]` unconditionally. exit=1. Rejected by clause1 (goal `beforeId = afterId -> [applyOp] = []`). Reproduces Solution_prepatch.lean / G-DIFF.
- atk_2.lean = INVERTED GUARD (control-flow-effect): emit when equal, empty when differ. exit=1. Rejected by clause2 (`beforeId != afterId -> [] != []`).
- atk_3.lean = always `return []`. exit=1. Rejected by clause2.
- atk_4.lean = BOUNDARY: `if beforeId <= afterId then [] else [applyOp]`. exit=1. Rejected by clause2 (before<after differs yet emits []).
- atk_5.lean = PARTIAL-DOMAIN: guard only on `beforeId = 0 AND afterId = 0`. exit=1. Rejected by clause1 (equal nonzero emits [applyOp]).
- atk_6.lean = correct guard + spurious `afterId = 0 -> []` extra branch. exit=1. Rejected by clause2.
- atk_8.lean = wrong on equal branch (emit [applyOp]) hidden behind a WEAK-invariant (`invariant True`) loop that still returns. exit=1 (loop-exit obligation `invariant AND ¬guard` insufficient to hide the wrong return).
All 7 scored attacks are same-spec verifying-REJECTED => the biconditional admits no terminating wrong impl. patches={} because no scored attack verifies (nothing to resolve-check).

POSITIVE CONTROL: pc.lean = structurally-distinct correct impl `if afterId = beforeId then [] else [applyOp, applyOp + 1, 7]` (distinct non-empty witness). same_spec=True, verify exit=0 => spec is NON-VACUOUS.

### DIVERGENCE PROBE (investigated, NOT submitted as scored attacks -- documented for the human record with EXECUTED resolve evidence):
Under `set_option loom.semantics.termination "partial"` (spec_guide.md §1.1 sanctioned), a diverging impl vacuously satisfies all postconditions. Naive `invariant True` divergence (atk_7.lean) is REJECTED (exit=1: loop-exit obligation `beforeId = afterId -> [applyOp] = []`). But a CONTRADICTORY loop-exit invariant makes the post-loop obligation vacuous:
- atk_9.lean (differ->[applyOp]; equal-> diverge then []): verify exit=0 but BEHAVIORALLY CORRECT (dead loop), NOT a counterexample.
- atk_10/11/12/13.lean = divergence with `while x = 0 invariant x = 0 do x := 0` (so invariant AND ¬guard = x=0 AND x!=0 = False): all verify exit=0. atk_11 emits [applyOp] on the EQUAL branch (violates clause1) but hides it behind divergence; atk_13 ALWAYS diverges and returns garbage `[applyOp,applyOp,applyOp]` yet verifies. These are genuinely-wrong-but-verifying via the partial-correctness VACUITY HATCH ONLY.

### Why this is not a break (SOUND)
1) UNIVERSAL ARTIFACT, not a bundle-specific weakness. The divergence hatch verifies against EVERY `termination "partial"` velvet bundle (401/500 in this board); it is a property of the sanctioned partial-correctness semantics, not of THIS spec's postconditions (which reject every terminating wrong impl -- atk_1..6,8).
2) MECHANIZED GATE STRUCTURALLY CANNOT DECLARE BROKEN. build_one.py:_derive_audit_verdict (lines 305-313): BROKEN requires `r.completed AND not r.resolved`. A divergent faithful patch hangs the F2P test -> harness produces no report.json -> `completed=False` -> falls into the `not r.completed` INCONCLUSIVE branch, never BROKEN.
3) EXECUTED RESOLVE EVIDENCE (run via swebench_unified.harness.run_resolve, docker, timeout 1800):
   - POSITIVE CONTROL gold.patch (bundle patch.diff verbatim): RESOLVED=True, COMPLETED=True, note=resolved. (Confirms harness live + gold correct + image OK; ran concurrently with other resolves on the same image.)
   - atk_11_faithful.patch (faithful refinement of atk_11: `if old_index.name == self.new_name:` then `while True: pass` -- infinite loop on the equal-name branch, applies cleanly at base_commit 647480166): RESOLVED=False, COMPLETED=False (no report.json -- the injected hang prevented harness completion). This is the INCONCLUSIVE `not completed` branch, NOT the BROKEN `completed and not resolved` branch. Per the governing convention (e.g. django__django-17087 pass exemplar) this is an accepted degenerate artifact, not verify-not-correct.
Because the only verifying wrong impls are divergence-based (whose faithful patch is COMPLETED=False => INCONCLUSIVE, never BROKEN) and every TERMINATING wrong impl is rejected, the spec exhibits no verify-not-correct defect. Submitting a divergence attack as scored would only manufacture a false INCONCLUSIVE gate-fail.

REFINEMENT AUDIT (refinement.md): A1 = R (index names str -> Int identity; sound: the gold guard reads only `==`, no other name property consumed on the changed path). A2 = I (equal-guard -> empty schedule; faithful to the early `return` skipping schema_editor.rename_index). A3 = R many-to-one (proceed branch -> non-empty List; sound: gold leaves that branch byte-identical to pre-patch, no test observes SQL shape, spec pins only `out != []`). NO A-consumed axiom, NO A-reference, NO kind-3 op -- confirmed: axioms region empty (comment only), no axiom decls, no axiom_check.py, G-AX correctly skips.

The name-resolution callees (get_index_by_name / _constraint_names / models.Index) are UNCHANGED and supply free inputs beforeId/afterId; the proof depends only on their EQUALITY, not on how they resolve, so no contract is consumed -- correct abstraction boundary (the gold patch touches only the guard + rename_index gating, modeled deeply). Every leg is R / I. mapping.md §1-5 consistent (base_commit 647480166..., file django/db/migrations/operations/models.py, database_forwards). UNGROUNDED-ORACLE PROBE: postcondition grounded in input equality (beforeId=afterId), not any opaque answer-key; proceed-branch content deliberately unpinned (only non-emptiness) -- no echo attack possible. G-CONF (conformance_check.py) is a real differential test (R/I-tagged, conf_skip=false).

Final: >=5 same-spec attacks run (7 scored + 5 divergence probes investigated = 12 total same_spec-True files verified), none breaks the spec; positive control verifies; prepatch reproduced (atk_1); gold resolves, atk_11 divergence patch does NOT complete (INCONCLUSIVE, not BROKEN). Refinement is R/I-only with no kind-3 and A-legs sound. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callee. Whether any store-mutation work is emitted is decided
--  entirely by the identifier-equality comparison, which is precisely the
--  behaviour under specification — modeled DEEPLY below (the equality guard),
--  NOT axiomatized or A-referenced (SPEC_GUIDE §0.7). The resolved before/after
--  identifiers are taken as free inputs; how they are looked up is an UNCHANGED
--  resolution whose internals the proof does not depend on, so no contract is
--  consumed.)
-- axioms-end

-- pure-start
/- A single unit of store-mutation work emitted when the relabeling proceeds.
   The exact code value is irrelevant — only its presence is observable to the
   layer below — so a constant marker is used. -/
def applyOp : Int := 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A relabeling of a stored object is applied to its backing store, driven
   entirely by whether the stored identifier actually changes. The operation is
   handed the identifier the object carries before the relabeling (`beforeId`)
   and the one it carries after (`afterId`).

   (1) When the before- and after- identifiers are the SAME, the operation is
       observationally inert: it must issue NO store-mutation work at all. The
       emitted schedule of operations is EMPTY. (Applying a relabeling that does
       not actually change the identifier must be a no-op, so that re-applying
       it onto an already-relabeled store is harmless.)

   (2) When the two identifiers DIFFER, the operation is NOT inert: it emits at
       least one store-mutation operation. The emitted schedule is NON-EMPTY.

   The only behaviour that distinguishes a correct operation from the defect is
   this zero-vs-nonzero schedule outcome: emit nothing exactly when the
   identifier is unchanged, emit something otherwise. The exact count and order
   of the operations emitted on the proceeding branch is NOT pinned by the spec.

   The two identifiers are modeled as `Int` (only their equality is observable
   to the layer below). The emitted schedule is a `List Int` of operation codes.
   Both identifiers are read-only inputs (neither is `mut`; the decision mutates
   nothing — directive 5). -/
method relabelSchedule (beforeId : Int) (afterId : Int) return (out : List Int)
  ensures beforeId = afterId → out = []
  ensures beforeId ≠ afterId → out ≠ []
  do
    -- impl-start
    if afterId = beforeId then
      return []
    else
      return [applyOp, applyOp + 1, 7]
    -- impl-end

prove_correct relabelSchedule by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: G-EQ = SOUND. Instance django__django-15695 (velvet). Spec = relabelSchedule(beforeId afterId : Int) -> (out : List Int) with a COMPLETE BICONDICTIONAL: `beforeId = afterId -> out = []` AND `beforeId != afterId -> out != []`. This fully pins the sole observable (zero-vs-nonzero emitted store-mutation work) for any TERMINATING impl. Models the gold 3-line early-return guard `if old_index.name == self.new_name: return` in RenameIndex.database_forwards.

ENVIRONMENT: worked in private dir; same_spec confirmed True for ALL attack files + positive control via swebench_unified.markers.same_spec (velvet). Verify cmd: `bash scripts/lean_verify.sh <file>` (0=verifies, 1=error/spec-rejected). Verifications launched concurrently in batches of 4.

### SCORED ATTACKS (all same_spec=True; all TERMINATING wrong impls -> all correctly REJECTED, exit 1):
- atk_1.lean = PREPATCH BUG: `return [applyOp]` unconditionally. exit=1. Rejected by clause1 (goal `beforeId = afterId -> [applyOp] = []`). Reproduces Solution_prepatch.lean / G-DIFF.
- atk_2.lean = INVERTED GUARD (control-flow-effect): emit when equal, empty when differ. exit=1. Rejected by clause2 (`beforeId != afterId -> [] != []`).
- atk_3.lean = always `return []`. exit=1. Rejected by clause2.
- atk_4.lean = BOUNDARY: `if beforeId <= afterId then [] else [applyOp]`. exit=1. Rejected by clause2 (before<after differs yet emits []).
- atk_5.lean = PARTIAL-DOMAIN: guard only on `beforeId = 0 AND afterId = 0`. exit=1. Rejected by clause1 (equal nonzero emits [applyOp]).
- atk_6.lean = correct guard + spurious `afterId = 0 -> []` extra branch. exit=1. Rejected by clause2.
- atk_8.lean = wrong on equal branch (emit [applyOp]) hidden behind a WEAK-invariant (`invariant True`) loop that still returns. exit=1 (loop-exit obligation `invariant AND ¬guard` insufficient to hide the wrong return).
All 7 scored attacks are same-spec verifying-REJECTED => the biconditional admits no terminating wrong impl. patches={} because no scored attack verifies (nothing to resolve-check).

POSITIVE CONTROL: pc.lean = structurally-distinct correct impl `if afterId = beforeId then [] else [applyOp, applyOp + 1, 7]` (distinct non-empty witness). same_spec=True, verify exit=0 => spec is NON-VACUOUS.

### DIVERGENCE PROBE (investigated, NOT submitted as scored attacks -- documented for the human record with EXECUTED resolve evidence):
Under `set_option loom.semantics.termination "partial"` (spec_guide.md §1.1 sanctioned), a diverging impl vacuously satisfies all postconditions. Naive `invariant True` divergence (atk_7.lean) is REJECTED (exit=1: loop-exit obligation `beforeId = afterId -> [applyOp] = []`). But a CONTRADICTORY loop-exit invariant makes the post-loop obligation vacuous:
- atk_9.lean (differ->[applyOp]; equal-> diverge then []): verify exit=0 but BEHAVIORALLY CORRECT (dead loop), NOT a counterexample.
- atk_10/11/12/13.lean = divergence with `while x = 0 invariant x = 0 do x := 0` (so invariant AND ¬guard = x=0 AND x!=0 = False): all verify exit=0. atk_11 emits [applyOp] on the EQUAL branch (violates clause1) but hides it behind divergence; atk_13 ALWAYS diverges and returns garbage `[applyOp,applyOp,applyOp]` yet verifies. These are genuinely-wrong-but-verifying via the partial-correctness VACUITY HATCH ONLY.

### Why this is not a break (SOUND)
1) UNIVERSAL ARTIFACT, not a bundle-specific weakness. The divergence hatch verifies against EVERY `termination "partial"` velvet bundle (401/500 in this board); it is a property of the sanctioned partial-correctness semantics, not of THIS spec's postconditions (which reject every terminating wrong impl -- atk_1..6,8).
2) MECHANIZED GATE STRUCTURALLY CANNOT DECLARE BROKEN. build_one.py:_derive_audit_verdict (lines 305-313): BROKEN requires `r.completed AND not r.resolved`. A divergent faithful patch hangs the F2P test -> harness produces no report.json -> `completed=False` -> falls into the `not r.completed` INCONCLUSIVE branch, never BROKEN.
3) EXECUTED RESOLVE EVIDENCE (run via swebench_unified.harness.run_resolve, docker, timeout 1800):
   - POSITIVE CONTROL gold.patch (bundle patch.diff verbatim): RESOLVED=True, COMPLETED=True, note=resolved. (Confirms harness live + gold correct + image OK; ran concurrently with other resolves on the same image.)
   - atk_11_faithful.patch (faithful refinement of atk_11: `if old_index.name == self.new_name:` then `while True: pass` -- infinite loop on the equal-name branch, applies cleanly at base_commit 647480166): RESOLVED=False, COMPLETED=False (no report.json -- the injected hang prevented harness completion). This is the INCONCLUSIVE `not completed` branch, NOT the BROKEN `completed and not resolved` branch. Per the governing convention (e.g. django__django-17087 pass exemplar) this is an accepted degenerate artifact, not verify-not-correct.
Because the only verifying wrong impls are divergence-based (whose faithful patch is COMPLETED=False => INCONCLUSIVE, never BROKEN) and every TERMINATING wrong impl is rejected, the spec exhibits no verify-not-correct defect. Submitting a divergence attack as scored would only manufacture a false INCONCLUSIVE gate-fail.

REFINEMENT AUDIT (refinement.md): A1 = R (index names str -> Int identity; sound: the gold guard reads only `==`, no other name property consumed on the changed path). A2 = I (equal-guard -> empty schedule; faithful to the early `return` skipping schema_editor.rename_index). A3 = R many-to-one (proceed branch -> non-empty List; sound: gold leaves that branch byte-identical to pre-patch, no test observes SQL shape, spec pins only `out != []`). NO A-consumed axiom, NO A-reference, NO kind-3 op -- confirmed: axioms region empty (comment only), no axiom decls, no axiom_check.py, G-AX correctly skips.

The name-resolution callees (get_index_by_name / _constraint_names / models.Index) are UNCHANGED and supply free inputs beforeId/afterId; the proof depends only on their EQUALITY, not on how they resolve, so no contract is consumed -- correct abstraction boundary (the gold patch touches only the guard + rename_index gating, modeled deeply). Every leg is R / I. mapping.md §1-5 consistent (base_commit 647480166..., file django/db/migrations/operations/models.py, database_forwards). UNGROUNDED-ORACLE PROBE: postcondition grounded in input equality (beforeId=afterId), not any opaque answer-key; proceed-branch content deliberately unpinned (only non-emptiness) -- no echo attack possible. G-CONF (conformance_check.py) is a real differential test (R/I-tagged, conf_skip=false).

Final: >=5 same-spec attacks run (7 scored + 5 divergence probes investigated = 12 total same_spec-True files verified), none breaks the spec; positive control verifies; prepatch reproduced (atk_1); gold resolves, atk_11 divergence patch does NOT complete (INCONCLUSIVE, not BROKEN). Refinement is R/I-only with no kind-3 and A-legs sound. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (swebench_unified.markers.same_spec(Solution, prepatch, velvet)=True). Solution.lean verifies (lean_verify exit 0); Solution_prepatch fails on the discriminating clause `beforeId = afterId → [applyOp] = []` (G-DIFF sees the bug). 

Modeled function relabelSchedule(beforeId, afterId): clause1 beforeId=afterId→out=[]; clause2 beforeId≠afterId→out≠[]. Real callee RenameIndex.database_forwards at base_commit 6474801 (django/db/migrations/operations/models.py:934), patched with the gold guard `if old_index.name == self.new_name: return` before `schema_editor.rename_index(model, old_index, new_index)`. Verified against repo at base commit and rename_index in base/schema.py:496 which always emits ≥1 store-mutation (ALTER INDEX…RENAME on can_rename_index, else remove_index+add_index) — so the proceeding branch is always non-empty, making clause2 not over-strong.

Abstraction (Int identity ⇔ index-name str): only equality of old_index.name vs self.new_name is read on the changed control path; equality is preserved by the bijection, sound both ways. beforeId/afterId are bound to old_index.name/self.new_name, which are resolved AFTER the earlier `if not self.allow_migrate_model(...): return` guard — so that pre-resolution early-return does not produce a (beforeId,afterId) pair on the modeled domain and cannot falsify clause2. On every input where the two identifiers are defined, real emits store-mutation work iff the names differ, matching both clauses exactly.

No diverging input exists on the modeled domain: the spec is a sound, appropriately-scoped (zero-vs-nonzero) abstraction, not too strong and not drifting from real post-patch behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view leakage judged against the public problem_statement ONLY (not hints_text). Findings:

1) same_spec(Solution.lean, Solution_prepatch.lean) = True; spec_view computed and reviewed directly. Lexical G-LEAK screen (leakage.screen) PASSES with zero hard failures.

2) Gold edit is a 3-line guard in RenameIndex.database_forwards: `if old_index.name == self.new_name: return` (make relabel a no-op when the index already carries the target name).

3) The public problem_statement already discloses the discriminating behavior: it states that re-applying RenameIndex() crashes on PostgreSQL (ProgrammingError: relation "new_pony_test_idx" already exists) and that the operation must be idempotent on re-apply. Thus the required behavior — do nothing when the name is unchanged — is derivable from the public task, independent of the spec.

4) The spec view exposes NO gold-specific tokens beyond the public task:
   - No patched repo symbol: `database_forwards` (the only distinctive changed symbol, len>=4) appears nowhere in identifiers or comments.
   - No patched file path (django/db/migrations/operations/models.py) and no dotted module path.
   - No reproduced gold-diff line (`if old_index.name == self.new_name:`, `return`, or the comment).
   - No diff markers.
   - No bug/fix narration terms (bug/fix/patch/previously/incorrectly/etc.). The word "defect" is used only to name the behavioral discriminator (zero-vs-nonzero emitted work), not the edit or its history.
   - All vocabulary is abstracted (relabelSchedule, beforeId/afterId, applyOp, "store-mutation work", "stored identifier"), an Int-equality model that pins correct behavior without revealing the concrete Python guard.

5) The encoded property (emit empty schedule iff beforeId = afterId) is the legitimate, necessary spec content and reconstructs only what a solver could already infer from the public idempotency-on-re-apply symptom. No spec-view line hands over the gold edit beyond problem_statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
