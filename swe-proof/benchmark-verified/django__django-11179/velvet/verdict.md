# P2 adversarial audit — django__django-11179

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
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -47,7 +47,6 @@
   ensures count = removed
   do
     -- impl-start
-    pk := none
     return removed
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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -48,7 +48,7 @@
   do
     -- impl-start
     pk := none
-    return removed
+    return 0
     -- impl-end
 
 prove_correct fastDelete by
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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -48,7 +48,7 @@
   do
     -- impl-start
     pk := none
-    return removed
+    return removed + 1
     -- impl-end
 
 prove_correct fastDelete by
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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -47,7 +47,7 @@
   ensures count = removed
   do
     -- impl-start
-    pk := none
+    pk := some 0
     return removed
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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -48,7 +48,7 @@
   do
     -- impl-start
     pk := none
-    return removed
+    return removed * 2
     -- impl-end
 
 prove_correct fastDelete by
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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -47,7 +47,10 @@
   ensures count = removed
   do
     -- impl-start
-    pk := none
+    if removed = 0 then
+      pk := pk
+    else
+      pk := none
     return removed
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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -47,6 +47,12 @@
   ensures count = removed
   do
     -- impl-start
+    let mut i : Nat := 1
+    while i > 0
+      invariant True
+      done_with False
+    do
+      i := i + 1
     pk := none
     return removed
     -- impl-end
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -48,7 +48,8 @@
   do
     -- impl-start
     pk := none
-    return removed
+    let c :| True
+    return c
     -- impl-end
 
 prove_correct fastDelete by
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the deletion-count is taken as a given input — the
@@ -47,7 +47,8 @@
   ensures count = removed
   do
     -- impl-start
-    pk := none
+    let p :| True
+    pk := p
     return removed
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the deletion-count is taken as a given input — the
--  batch removal that produces it is not re-derived here and is observed only
--  through that count. The state change under spec — clearing the record's
--  identity handle — is modeled deeply as an assignment, no outside contract
--  consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A short-circuit removal handles the case of a single standalone record that
   no other record depends on: it removes the record in one batch and reports
   how many rows that batch removed.

   The record carries a mutable identity handle (`pk`) — an optional integer
   that is present (`some k`) while the record denotes a stored row. After the
   removal short-circuit completes, the record no longer denotes any stored row,
   so its identity handle must be CLEARED (`none`), regardless of what it was
   before.

   The reported count is exactly the batch's removal count, passed in as
   `removed`; the short-circuit must report that count UNCHANGED — clearing the
   handle must not perturb the returned number.

   `pk` is genuinely mutated (declared `mut`) and its post-state is pinned
   exactly to `none` (directive 5: the unchanged frame is the count, stated via
   the returned value equalling `removed`; the changed frame `pk` is pinned to
   its exact post-state). -/
method fastDelete (mut pk : Option Int) (removed : Nat) return (count : Nat)
  ensures pk = none
  ensures count = removed
  do
    -- impl-start
    pk := none
    return removed
    -- impl-end

prove_correct fastDelete by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: method fastDelete (mut pk : Option Int) (removed : Nat) return (count : Nat), ensures pk = none, ensures count = removed. termination "partial", choice "demonic". axioms=[], no opaque/oracle. same_spec=True verified for every attack file below (velvet backend).

CMD (per attack): bash scripts/lean_verify.sh <file> ; same_spec via swebench_unified.markers.same_spec.

TERMINATING ATTACKS — all 9 same-spec, all correctly REJECTED (verify exit 1) on the right clause:
- atk_1 `return removed` (== prepatch bug, never clears pk): exit 1, ensures_2 pk=none ⊢ pkOld = none. PREPATCH REPRODUCED.
- atk_2 `pk:=none; return 0`: exit 1, ensures_1 ⊢ 0 = removed.
- atk_3 `pk:=none; return removed+1`: exit 1, ensures_1 ⊢ removed+1 = removed (boundary/off-by-one).
- atk_4 `pk:=some 0; return removed` (wrong clear value): exit 1, ensures_2 ⊢ some 0 = none.
- atk_5 `pk:=none; return removed*2`: exit 1, ensures_1 ⊢ removed*2 = removed.
- atk_6 `if removed=0 then pk:=pk else pk:=none; return removed` (partial-domain, leaves pk stale on removed=0): exit 1, ensures_2 ⊢ pkOld = none.
- atk_7 divergent loop with `done_with False`: exit 1 (done_1 ⊢ False; the loop-exit condition can't be discharged when the guard can't be forced false — a MALFORMED divergence attempt).
- atk_9 `pk:=none; let c:|True; return c` (demonic underconstrained count / ungrounded-oracle echo): exit 1, ensures_1 ⊢ i = removed.
- atk_10 `let p:|True; pk:=p; return removed` (demonic underconstrained pk): exit 1, ensures_2 ⊢ i = none.
Under demonic choice, an underconstrained value must satisfy the post for ALL choices, so oracle-echo/nondeterminism attacks are rejected. Among TERMINATING impls the spec is maximally tight: both outputs pinned to unique concrete values (none, removed), zero freedom, no oracle.

POSITIVE CONTROLS (same_spec=True, verify EXIT 0): atk_pos.lean = gold impl (`pk:=none; return removed`); atk_posdiff.lean = STRUCTURALLY DIFFERENT correct impl (`let target := if removed≥0 then none else some 7; pk:=target; let c:=removed+0; return c`) — spec is NON-VACUOUS (a genuinely different correct impl verifies).

ONLY verifying wrong impl found = atk_8.lean (`let mut i:=0; while (0:Nat)<1 (invariant True; done_with False) do i:=i+1; return removed` — infinite loop, never clears pk). lean_verify.sh atk_8.lean => EXIT 0 (verifies VACUOUSLY: partial-correctness makes {P} while true {Q} valid for any Q). Per the mandatory protocol I MATERIALIZED its faithful refined patch (atk_8.patch: injects `i=0; while True: i+=1` before `return count,{...}` in the fast-delete branch; git apply --check = clean against base_commit worktree) and EXECUTED it through the official harness:
  run_resolve(django__django-11179, atk_8.patch, timeout=1800) => resolved=False, completed=False, note="no report ... harness error" (ran 30+ min; the F2P test `.delete()` hits the infinite loop and hangs to the per-test timeout, so no report is produced).
  GOLD control run in the SAME window/contention: run_resolve(gold.patch) => resolved=True, completed=True (rules out contention as the cause; atk_8's non-completion is intrinsic to its divergence).
WHY atk_8 is NOT a genuine G-EQ break and is deliberately NOT listed among `attacks`:

  (1) It verifies solely via the partial-correctness DIVERGENCE artifact, which is UNIVERSAL to termination "partial" (401/500 velvet bundles). Proof: I injected the identical infinite loop into an INDEPENDENT, already-accepted bundle (django__django-10554/velvet) -> diverge_probe_10554.lean verifies EXIT 0 as well. Divergence is thus not a weakness of THIS spec's postconditions but a property of the accepted logic fragment.

  (2) An unbounded loop injected into a loopless straight-line repo branch corresponds to NO repo operation — it has no R/A/I refinement leg, so atk_8.patch is NOT a FAITHFUL refinement of the modeled function (plan §4 = refinement fidelity). It is not a legitimate counterexample.

  (3) The official derivation (construct/build_one.py:306-311) flags BROKEN only when a candidate's patch resolve `completed AND not resolved`; a resolve that does NOT complete (atk_8: completed=False) is inconclusive, never BROKEN. Listing atk_8 as an attack would only fail-close the gate INCONCLUSIVE on a systemic non-genuine artifact.

REFINEMENT.MD AUDIT (protocol step 3): three legs — A1 (R: input `removed` <- unchanged `count = sql.DeleteQuery(model).delete_batch(...)`, int≥0 ↔ Nat), A2 (I: `pk := none` <- the sole added line `setattr(instance, model._meta.pk.attname, None)`, None↔none), A3 (I: `return removed` <- `return count, {label: count}`, count unchanged). No axioms, no A-reference deep models, NO kind-3 (inexpressible-changed-op). The A-leg correspondence audit is vacuously satisfied (there are no axiom/deep-model references); R/I correspondence to the real callees holds and matches the gold branch at deletion.py:277-280. G-CONF conf_skip=true is justified (live-ORM state mutation, no DB-free R/I shadow); soundness carried by G-VERIFY + G-DIFF, both re-confirmed here (prepatch = atk_1 fails on exactly ensures_2 pk=none).

CONCLUSION: 9 same-spec terminating attacks (partial-domain, boundary, control-flow, demonic/ungrounded, prepatch bug) all run and all rejected; two positive controls verify (gold + structurally-different); prepatch reproduced. The only verifying wrong impl is a universal partial-correctness divergence artifact whose materialized patch's resolve did NOT complete (not a completed-non-resolve => not BROKEN) and which is not a faithful refinement. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the deletion-count is taken as a given input — the
--  batch removal that produces it is not re-derived here and is observed only
--  through that count. The state change under spec — clearing the record's
--  identity handle — is modeled deeply as an assignment, no outside contract
--  consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A short-circuit removal handles the case of a single standalone record that
   no other record depends on: it removes the record in one batch and reports
   how many rows that batch removed.

   The record carries a mutable identity handle (`pk`) — an optional integer
   that is present (`some k`) while the record denotes a stored row. After the
   removal short-circuit completes, the record no longer denotes any stored row,
   so its identity handle must be CLEARED (`none`), regardless of what it was
   before.

   The reported count is exactly the batch's removal count, passed in as
   `removed`; the short-circuit must report that count UNCHANGED — clearing the
   handle must not perturb the returned number.

   `pk` is genuinely mutated (declared `mut`) and its post-state is pinned
   exactly to `none` (directive 5: the unchanged frame is the count, stated via
   the returned value equalling `removed`; the changed frame `pk` is pinned to
   its exact post-state). -/
method fastDelete (mut pk : Option Int) (removed : Nat) return (count : Nat)
  ensures pk = none
  ensures count = removed
  do
    -- impl-start
    pk := none
    return removed
    -- impl-end

prove_correct fastDelete by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: method fastDelete (mut pk : Option Int) (removed : Nat) return (count : Nat), ensures pk = none, ensures count = removed. termination "partial", choice "demonic". axioms=[], no opaque/oracle. same_spec=True verified for every attack file below (velvet backend).

CMD (per attack): bash scripts/lean_verify.sh <file> ; same_spec via swebench_unified.markers.same_spec.

TERMINATING ATTACKS — all 9 same-spec, all correctly REJECTED (verify exit 1) on the right clause:
- atk_1 `return removed` (== prepatch bug, never clears pk): exit 1, ensures_2 pk=none ⊢ pkOld = none. PREPATCH REPRODUCED.
- atk_2 `pk:=none; return 0`: exit 1, ensures_1 ⊢ 0 = removed.
- atk_3 `pk:=none; return removed+1`: exit 1, ensures_1 ⊢ removed+1 = removed (boundary/off-by-one).
- atk_4 `pk:=some 0; return removed` (wrong clear value): exit 1, ensures_2 ⊢ some 0 = none.
- atk_5 `pk:=none; return removed*2`: exit 1, ensures_1 ⊢ removed*2 = removed.
- atk_6 `if removed=0 then pk:=pk else pk:=none; return removed` (partial-domain, leaves pk stale on removed=0): exit 1, ensures_2 ⊢ pkOld = none.
- atk_7 divergent loop with `done_with False`: exit 1 (done_1 ⊢ False; the loop-exit condition can't be discharged when the guard can't be forced false — a MALFORMED divergence attempt).
- atk_9 `pk:=none; let c:|True; return c` (demonic underconstrained count / ungrounded-oracle echo): exit 1, ensures_1 ⊢ i = removed.
- atk_10 `let p:|True; pk:=p; return removed` (demonic underconstrained pk): exit 1, ensures_2 ⊢ i = none.
Under demonic choice, an underconstrained value must satisfy the post for ALL choices, so oracle-echo/nondeterminism attacks are rejected. Among TERMINATING impls the spec is maximally tight: both outputs pinned to unique concrete values (none, removed), zero freedom, no oracle.

POSITIVE CONTROLS (same_spec=True, verify EXIT 0): atk_pos.lean = gold impl (`pk:=none; return removed`); atk_posdiff.lean = STRUCTURALLY DIFFERENT correct impl (`let target := if removed≥0 then none else some 7; pk:=target; let c:=removed+0; return c`) — spec is NON-VACUOUS (a genuinely different correct impl verifies).

ONLY verifying wrong impl found = atk_8.lean (`let mut i:=0; while (0:Nat)<1 (invariant True; done_with False) do i:=i+1; return removed` — infinite loop, never clears pk). lean_verify.sh atk_8.lean => EXIT 0 (verifies VACUOUSLY: partial-correctness makes {P} while true {Q} valid for any Q). Per the mandatory protocol I MATERIALIZED its faithful refined patch (atk_8.patch: injects `i=0; while True: i+=1` before `return count,{...}` in the fast-delete branch; git apply --check = clean against base_commit worktree) and EXECUTED it through the official harness:
  run_resolve(django__django-11179, atk_8.patch, timeout=1800) => resolved=False, completed=False, note="no report ... harness error" (ran 30+ min; the F2P test `.delete()` hits the infinite loop and hangs to the per-test timeout, so no report is produced).
  GOLD control run in the SAME window/contention: run_resolve(gold.patch) => resolved=True, completed=True (rules out contention as the cause; atk_8's non-completion is intrinsic to its divergence).
WHY atk_8 is NOT a genuine G-EQ break and is deliberately NOT listed among `attacks`:

  (1) It verifies solely via the partial-correctness DIVERGENCE artifact, which is UNIVERSAL to termination "partial" (401/500 velvet bundles). Proof: I injected the identical infinite loop into an INDEPENDENT, already-accepted bundle (django__django-10554/velvet) -> diverge_probe_10554.lean verifies EXIT 0 as well. Divergence is thus not a weakness of THIS spec's postconditions but a property of the accepted logic fragment.

  (2) An unbounded loop injected into a loopless straight-line repo branch corresponds to NO repo operation — it has no R/A/I refinement leg, so atk_8.patch is NOT a FAITHFUL refinement of the modeled function (plan §4 = refinement fidelity). It is not a legitimate counterexample.

  (3) The official derivation (construct/build_one.py:306-311) flags BROKEN only when a candidate's patch resolve `completed AND not resolved`; a resolve that does NOT complete (atk_8: completed=False) is inconclusive, never BROKEN. Listing atk_8 as an attack would only fail-close the gate INCONCLUSIVE on a systemic non-genuine artifact.

REFINEMENT.MD AUDIT (protocol step 3): three legs — A1 (R: input `removed` <- unchanged `count = sql.DeleteQuery(model).delete_batch(...)`, int≥0 ↔ Nat), A2 (I: `pk := none` <- the sole added line `setattr(instance, model._meta.pk.attname, None)`, None↔none), A3 (I: `return removed` <- `return count, {label: count}`, count unchanged). No axioms, no A-reference deep models, NO kind-3 (inexpressible-changed-op). The A-leg correspondence audit is vacuously satisfied (there are no axiom/deep-model references); R/I correspondence to the real callees holds and matches the gold branch at deletion.py:277-280. G-CONF conf_skip=true is justified (live-ORM state mutation, no DB-free R/I shadow); soundness carried by G-VERIFY + G-DIFF, both re-confirmed here (prepatch = atk_1 fails on exactly ensures_2 pk=none).

CONCLUSION: 9 same-spec terminating attacks (partial-domain, boundary, control-flow, demonic/ungrounded, prepatch bug) all run and all rejected; two positive controls verify (gold + structurally-different); prepatch reproduced. The only verifying wrong impl is a universal partial-correctness divergence artifact whose materialized patch's resolve did NOT complete (not a completed-non-resolve => not BROKEN) and which is not a faithful refinement. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Bundle verified rigorously: (a) same_spec(Solution, Solution_prepatch, velvet.language)=True — spec region byte-identical. (b) lean_verify Solution.lean -> rc 0 (verifies). (c) lean_verify Solution_prepatch.lean -> rc 1, fails on the correct clause `case ensures_2: pk=none ⊢ pkOld=none` (the buggy skeleton never clears pk), confirming G-DIFF discriminates on the real fix. (d) Real repo worktree (base_commit 19fc6376) deletion.py:274-280 confirmed: the branch is entered only under `len(self.data)==1 and len(instances)==1 and can_fast_delete(instance)`; base lacks the setattr, gold adds it. (e) F2P test tests.py asserts `assertIsNone(obj.pk)` after fast delete — the real observable None maps to spec `none`. Faithfulness-break probes all negative: non-int/UUID PK carriers still get cleared unconditionally so no divergence in the modeled observable; exception path of delete_batch is unconstrained under partial-correctness (no return) so no over-strong claim; the omitted `{label: count}` return element is a weakening not a strengthening (irrelevant to faithfulness-break). No input exists where the modeled function claims more than the real callee delivers. Spec is FAITHFUL (and, from a weakness angle, TIGHT — 6 spec-too-weak attacks in the recorded audit all rejected, positive control verifies).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over Solution.lean, velvet/lean tables) passes with zero hard_failures. Semantic panel-3 judgment: the public problem_statement already fully discloses the fix ('delete() on instances of models without any dependencies doesn't clear PKs ... It should be set to None after .delete() call. See deletion:276-281'). The spec view (doc comment + method signature + ensures clauses; impl-start/impl-end body is stripped, and mapping.md/refinement.md are auditor-only artifacts not in the solver's spec view) contains: `ensures pk = none` (a verbatim restatement of the publicly-stated requirement 'PK should be set to None') and `ensures count = removed` (a generic don't-break-the-return clause, not gold-specific). No gold-specific identifiers appear in the spec view — no `setattr`, `model._meta.pk.attname`, `delete_batch`, or file path; 'batch' is generic fast-delete terminology. Because the problem_statement is already maximally explicit about the required change, the ensures clauses add no incremental disclosure. No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.