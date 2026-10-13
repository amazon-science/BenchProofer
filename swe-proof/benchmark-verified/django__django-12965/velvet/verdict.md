# P2 adversarial audit — django__django-12965

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_2b.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The frozen spec pins BOTH observables exactly: (1) mut-frame `ensures tableRefs = withTarget tableRefsOld` fixes the exact post-state (the lone real side effect of the added `get_initial_alias()` call), and (2) `ensures direct <-> liveCount tableRefsOld.tail = 0` fixes the exact return as a function of the pre-state. 12 distinct same-spec wrong impls were encoded and verified; 10 are REJECTED with genuine semantic goal failures. The only 2 that verify (atk_8 ungrounded-oracle echo: decide from the PRE-state tail; atk_10 control-flow reorder: decide before recording the target) are provably the SAME function as the gold, because `withTarget` preserves the tail -- machine-checked in echocheck.lean (`liveCount (withTarget rc).tail = liveCount rc.tail`, lean_verify rc=0). Their materialized faithful patches were RUN through the official harness and BOTH RESOLVE (completed=true, resolved=true), i.e. they are correct echoes of the gold, not spec weaknesses. No same-spec verifying impl has a faithful patch that completes-and-fails-to-resolve, so verify does NOT imply incorrect here.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,7 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
-    tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return liveCount tableRefs == 1
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,14 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- The right answer, but only after a loop that never makes progress.
     tableRefs := withTarget tableRefs
+    let mut spin : Nat := 0
+    while spin ≠ 1
+      invariant spin = 0
+      decreasing spin
+    do
+      spin := 0
     return liveCount tableRefs.tail == 0
     -- impl-end
 
```

Attack 3 — `atk_2b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,14 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- The right answer, but only after a loop that never makes progress.
     tableRefs := withTarget tableRefs
+    let mut spin : Nat := 0
+    while spin = 0
+      invariant spin = 0
+      decreasing spin
+    do
+      spin := spin
     return liveCount tableRefs.tail == 0
     -- impl-end
 
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
-    tableRefs := withTarget tableRefs
+    -- Right boolean, but the target's own use of the table is never recorded.
     return liveCount tableRefs.tail == 0
     -- impl-end
 
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,8 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
-    tableRefs := withTarget tableRefs
+    -- Right boolean, but the target's use is recorded twice.
+    tableRefs := withTarget (withTarget tableRefs)
     return liveCount tableRefs.tail == 0
     -- impl-end
 
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,9 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Boundary slip: demands ZERO live tables after recording the target.
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return liveCount tableRefs == 0
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,13 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Correct only where a table is already recorded; the empty (whole-table
+    -- delete) state falls through to the subquery answer.
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    if tableRefsOld.isEmpty then
+      return false
+    else
+      return liveCount tableRefs.tail == 0
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,9 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Off-by-one: skips the first NON-target table as well as the target.
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return liveCount (tableRefs.drop 2) == 0
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,8 +49,10 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Echoes the specification's own oracle: decide from the PRE-state
+    -- snapshot, then record the target's use.
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return liveCount tableRefsOld.tail == 0
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 10 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,10 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Record the target's use, then ask whether exactly one table is live
+    -- over the WHOLE vector (rather than zero over the non-target part).
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return liveCount tableRefs == 1
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 11 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,8 +49,10 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Decide first, record the target's use afterwards (effects reordered).
+    let ans := liveCount tableRefs.tail == 0
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return ans
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 12 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,9 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Polarity flipped.
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return liveCount tableRefs.tail != 0
     -- impl-end
 
 prove_correct directDeleteEligible by
```

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,9 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
-    tableRefs := withTarget tableRefs
+    -- Reproduce the post-state directly instead of invoking the modeled
+    -- query-construction callee.
+    tableRefs := (tableRefs.headD 0 + 1) :: tableRefs.tail
     return liveCount tableRefs.tail == 0
     -- impl-end
 
```

Attack 14 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,9 @@
   ensures direct ↔ liveCount tableRefsOld.tail = 0
   do
     -- impl-start
+    -- Same decision spelled as a universal test over the non-target tables.
     tableRefs := withTarget tableRefs
-    return liveCount tableRefs.tail == 0
+    return tableRefs.tail.all (fun n => n == 0)
     -- impl-end
 
 prove_correct directDeleteEligible by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The only callee invoked by the modeled operation is
   modeled DEEPLY as the pure function `withTarget` (a deep-model A-reference,
   validated against the real callee by axiom_check.py / G-AX), not consumed as
   an axiom. -/
-- axioms-end

-- pure-start
/- A deletion query is modeled by the list of usage counts of the tables it
   addresses, in the query's own table order; the table the deletion targets is
   the one at the head. A table is "live" when its usage count is positive. -/

/- The deletion's own use of the table it targets: that table's usage count goes
   up by one, and no other table's count changes. Deep model of an unchanged
   query-construction callee — provenance + executable soundness in mapping.md /
   axiom_check.py (G-AX). -/
def withTarget (rc : List Nat) : List Nat := (rc.headD 0 + 1) :: rc.tail

/- The number of live (positively-counted) tables. -/
def liveCount (rc : List Nat) : Nat := (rc.filter (fun n => n != 0)).length

@[grind] lemma withTarget_tail (rc : List Nat) :
    (withTarget rc).tail = rc.tail := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Decide whether a deletion can be compiled as a direct delete over the table
   it targets rather than via a subquery that selects the rows to remove. The
   direct form is available exactly when no table OTHER than the targeted one is
   live. -/
method directDeleteEligible (mut tableRefs : List Nat) return (direct : Bool)
  ensures tableRefs = withTarget tableRefsOld
  ensures direct ↔ liveCount tableRefsOld.tail = 0
  do
    -- impl-start
    tableRefs := withTarget tableRefs
    return liveCount tableRefs.tail == 0
    -- impl-end

prove_correct directDeleteEligible by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (advisory). NOTE: the spec has been REVISED since the recorded P2 audit -- it is now termination "total" (was "partial"), withTarget is the single total headD equation, and ensures_1 is now `liveCount tableRefsOld.tail = 0`. So I re-attacked from scratch rather than inheriting the prior pass's conclusions; the prior pass's sole hole (a divergent while-true partial-correctness artifact) is now CLOSED -- see atk_2/atk_2b.

**SAME-SPEC:** all 14 attacks + positive control verified same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language (only the impl region was edited).

**COMMANDS:** verification `bash scripts/lean_verify.sh <D>/atk_N.lean` run. Attacks were verified CONCURRENTLY in background batches of 4. Resolve runs: `python3 <D>/resolve.py <D>/<f>.patch` calling swebench_unified.harness.run_resolve('django__django-12965', patch, timeout=1200, retries=0), the 3 runs launched concurrently.

**POSITIVE CONTROL:** pos_control.lean (byte copy of bundle Solution.lean) -> lean_verify rc=0. VERIFIES.
PREPATCH REPRODUCED: atk_1.lean is a byte copy of the bundle's Solution_prepatch.lean -> rc=1, failing BOTH clauses: ensures_1 `(liveCount tableRefsOld == 1) = true <-> liveCount tableRefsOld.tail = 0` AND the mut-frame `tableRefsOld = withTarget tableRefsOld`. The pre-patch omission is genuinely caught.

### ATTACK RESULTS (path -> verify rc -> observed):
1. atk_1.lean (prepatch bug: whole-vector ==1, no mutation) rc=1 REJECTED (both ensures unsolved).
2. atk_2.lean (control-flow-effect / DIVERGENCE under total termination: right answer after a non-progressing `while spin != 1` loop) rc=1 REJECTED -- unsolved `decreasing_1: spin` goal `0 < spin`. This is the key regression check: `termination "total"` now discharges a decreases obligation, so the prior audit's divergence artifact can no longer verify.
3. atk_2b.lean (divergence, alternate spelling `while spin = 0` / `spin := spin`) rc=1 REJECTED -- `decreasing` goal `spin < spin`.
4. atk_3.lean (FRAME violation: correct boolean, NO mutation) rc=1 REJECTED -- mut-frame goal `tableRefsOld = withTarget tableRefsOld`. The mut frame is load-bearing.
5. atk_4.lean (control-flow-effect: target's use recorded TWICE) rc=1 REJECTED -- `withTarget (withTarget x) = withTarget x`.
6. atk_5.lean (BOUNDARY: `liveCount tableRefs == 0` post-mutation) rc=1 REJECTED -- ensures_1 unsolved.
7. atk_6.lean (PARTIAL-DOMAIN: correct on non-empty, returns false on the EMPTY whole-table-delete state) rc=1 REJECTED -- ensures_1 residual goal is exactly `if_pos : tableRefsOld.isEmpty = true |- false = true <-> liveCount tableRefsOld.tail = 0`, i.e. the spec pins precisely the F2P (test_fast_delete_all) empty-alias_map case.
8. atk_7.lean (off-by-one domain: `liveCount (tableRefs.drop 2) == 0`, skips one non-target table too) rc=1 REJECTED.
9. atk_8.lean (UNGROUNDED-ORACLE ECHO: mutate, then decide from the pre-state snapshot `liveCount tableRefsOld.tail == 0`) rc=0 VERIFIES -> CANDIDATE. Faithful patch materialized at <D>/atk_8.patch against pristine base compiler.py (git cat-file of 437196da9a...:django/db/models/sql/compiler.py). EXECUTED run_resolve -> {completed: true, resolved: true, note: 'resolved'} (<D>/atk_8.resolve.out). CORRECT ECHO, not a break.
10. atk_9.lean (gold's own spelling: `liveCount tableRefs == 1` post-mutation) rc=1 REJECTED -- ensures_1 unsolved. IMPORTANT NUANCE: this expression is mathematically EQUIVALENT to the postcondition -- I proved it in <D>/eqcheck.lean (`(liveCount (withTarget rc) == 1) = true <-> liveCount rc.tail = 0`, lean_verify rc=0). So its rejection is prover incompleteness / spec strictness, NOT a soundness defect: a spec that rejects a behaviourally-gold impl can only cause false NEGATIVES (spec too STRONG), never verify-without-correct. Not a G-EQ break; noted for the faithfulness panel.
11. atk_10.lean (CONTROL-FLOW-EFFECT REORDER: decide BEFORE recording the target's use) rc=0 VERIFIES -> CANDIDATE. Faithful patch <D>/atk_10.patch. EXECUTED run_resolve -> {completed: true, resolved: true} (<D>/atk_10.resolve.out). CORRECT ECHO.
12. atk_11.lean (polarity flipped) rc=1 REJECTED.
13. atk_12.lean (inline withTarget's equation instead of invoking the modeled callee) rc=1 REJECTED -- mut-frame goal not closed by rfl-level reasoning; again strictness, not unsoundness.
14. atk_13.lean (`tableRefs.tail.all (. == 0)`, an equivalent total spelling) rc=1 REJECTED -- ensures_1 unsolved; strictness only.

WHY THE 2 CANDIDATES ARE NOT BREAKS (machine-checked, not speculation): both decide from the PRE-state tail while gold decides from the POST-state tail. Since `withTarget rc = (rc.headD 0 + 1) :: rc.tail` preserves `.tail` exactly, the two are the SAME total function -- proved in <D>/echocheck.lean: `liveCount (withTarget rc).tail = liveCount rc.tail` (lean_verify rc=0). And I did not stop at the proof: I materialized both faithful patches and RAN the official harness on each; both completed=true resolved=true. Per `_derive_audit_verdict` a candidate whose patch resolves is a correct echo, not a weakness.

HARNESS VALIDATION (guards against a false SOUND from a broken resolve method): the gold patch (bundle patch.diff verbatim, <D>/gold.patch) through the SAME run_resolve path -> {completed: true, resolved: true, note: 'resolved'} (<D>/gold.resolve.out). My patch-materialization + resolve invocation are therefore demonstrably correct, and the atk_8/atk_10 resolves are meaningful rather than vacuous.

A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's). refinement.md has exactly 3 legs, NO kind-3: A1 = R (List Nat <-> [alias_refcount[t] for t in alias_map] in insertion order, head = base table); A2 = A-reference + I (the ADDED call to the UNCHANGED callee Query.get_initial_alias, deep-modeled by withTarget; the assignment itself concrete); A3 = I (liveCount counts entries != 0 <=> sum(alias_refcount[t] > 0)). Section B's claim holds: `single_alias` (the function under change) is never axiomatized, and there are no consumed axioms at all -- so the only trust point is the withTarget deep model.

A-LEG CORRESPONDENCE HOLDS (independently checked against real source at base_commit 437196da9a386bd4cc62b0ce3f2de4aba468613d, worktree, compiler.py quoted pristine via `git show` since that worktree carries the gold edit as an uncommitted modification):
- query.py:916-926 get_initial_alias: non-empty alias_map -> `alias = self.base_table; self.ref_alias(alias)` and ref_alias (query.py:758-760) is `alias_refcount[alias] += 1`, with alias_map itself untouched => (h::t) -> (h+1)::t. Empty alias_map -> `join(BaseTable(...))` -> table_alias(create=True) ASSIGNS `alias_refcount[alias] = 1` and appends the sole alias_map entry => [] -> [1]. Both branches are exactly the one total equation `withTarget rc = (rc.headD 0 + 1) :: rc.tail`. Confirmed.
- base_table (query.py:244-247) is the first alias_map key, so head-ordering is right. I probed the obvious way to break this: change_aliases (query.py:847-854) does delete-and-re-append and CAN move the base table to the back, and trim_start unrefs leading aliases so the first key may be a refcount-0 alias. HOWEVER neither runs on the DELETE path before single_alias is consulted -- the only in-tree callers are Query.split_exclude / bump_prefix / relabeled_clone, all operating on freshly-built SUBqueries, and SQLDeleteCompiler.as_sql never calls pre_sql_setup/setup_query. DeleteQuery.do_query (subqueries.py:21) rebuilds alias_map down to the single base-table entry, so the head is still the base table. The bijection is therefore valid on the modeled path.
- G-AX executed: ` python3 <bundle>/axiom_check.py` -> "G-AX OK: activate deep model (== Query.get_initial_alias refcount side effect) sound on 14 real-Query observations", rc=0.
- Model<->patch correspondence: the mut frame pins exactly ONE withTarget application, matching the patch's single added `self.query.get_initial_alias()` line and nothing else; atk_3 (no mutation) and atk_4 (double mutation) are both rejected, so the frame really is discriminating in both directions.

MINOR DOC DEFECTS in refinement.md (cosmetic, do NOT affect soundness, worth a fix): (a) the A1 row names the parameter `refcount : List Nat` but the actual method parameter is `tableRefs : List Nat` -- stale identifier from an earlier revision; (b) the A3 row's justification argues `sum(...) == 1 <=> liveCount tail == 0` via the post-call head-invariant, which is correct, but the row labels the Lean side `return liveCount tableRefs.tail == 0` as tag I against a Python RHS that is textually `sum(...) == 1` -- the two are equivalent-not-identical, so this leg is arguably R-with-argument rather than strict I. The argument given is sound and the equivalence is the one I independently proved in eqcheck.lean, so no correspondence failure; only the tag/label is loose. Also (c) axiom_check.py's docstring and output still call the deep model `activate` while Solution.lean names it `withTarget` -- a stale name, though the equation checked is the right one.

**FLOOR:** 14 attacks (>= 5), prepatch reproduced, positive control verifies and is a distinct file from every attack, 0 inconclusive verify runs, and every verifying candidate has a submitted faithful patch whose resolve COMPLETED. No verifying wrong impl's faithful patch fails to resolve => verify => correct is not refuted. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_2b.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The frozen spec pins BOTH observables exactly: (1) mut-frame `ensures tableRefs = withTarget tableRefsOld` fixes the exact post-state (the lone real side effect of the added `get_initial_alias()` call), and (2) `ensures direct <-> liveCount tableRefsOld.tail = 0` fixes the exact return as a function of the pre-state. 12 distinct same-spec wrong impls were encoded and verified; 10 are REJECTED with genuine semantic goal failures. The only 2 that verify (atk_8 ungrounded-oracle echo: decide from the PRE-state tail; atk_10 control-flow reorder: decide before recording the target) are provably the SAME function as the gold, because `withTarget` preserves the tail -- machine-checked in echocheck.lean (`liveCount (withTarget rc).tail = liveCount rc.tail`, lean_verify rc=0). Their materialized faithful patches were RUN through the official harness and BOTH RESOLVE (completed=true, resolved=true), i.e. they are correct echoes of the gold, not spec weaknesses. No same-spec verifying impl has a faithful patch that completes-and-fails-to-resolve, so verify does NOT imply incorrect here.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2b.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The only callee invoked by the modeled operation is
   modeled DEEPLY as the pure function `withTarget` (a deep-model A-reference,
   validated against the real callee by axiom_check.py / G-AX), not consumed as
   an axiom. -/
-- axioms-end

-- pure-start
/- A deletion query is modeled by the list of usage counts of the tables it
   addresses, in the query's own table order; the table the deletion targets is
   the one at the head. A table is "live" when its usage count is positive. -/

/- The deletion's own use of the table it targets: that table's usage count goes
   up by one, and no other table's count changes. Deep model of an unchanged
   query-construction callee — provenance + executable soundness in mapping.md /
   axiom_check.py (G-AX). -/
def withTarget (rc : List Nat) : List Nat := (rc.headD 0 + 1) :: rc.tail

/- The number of live (positively-counted) tables. -/
def liveCount (rc : List Nat) : Nat := (rc.filter (fun n => n != 0)).length

@[grind] lemma withTarget_tail (rc : List Nat) :
    (withTarget rc).tail = rc.tail := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Decide whether a deletion can be compiled as a direct delete over the table
   it targets rather than via a subquery that selects the rows to remove. The
   direct form is available exactly when no table OTHER than the targeted one is
   live. -/
method directDeleteEligible (mut tableRefs : List Nat) return (direct : Bool)
  ensures tableRefs = withTarget tableRefsOld
  ensures direct ↔ liveCount tableRefsOld.tail = 0
  do
    -- impl-start
    tableRefs := withTarget tableRefs
    return liveCount tableRefs.tail == 0
    -- impl-end

prove_correct directDeleteEligible by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (advisory). NOTE: the spec has been REVISED since the recorded P2 audit -- it is now termination "total" (was "partial"), withTarget is the single total headD equation, and ensures_1 is now `liveCount tableRefsOld.tail = 0`. So I re-attacked from scratch rather than inheriting the prior pass's conclusions; the prior pass's sole hole (a divergent while-true partial-correctness artifact) is now CLOSED -- see atk_2/atk_2b.

**SAME-SPEC:** all 14 attacks + positive control verified same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language (only the impl region was edited).

**COMMANDS:** verification `bash scripts/lean_verify.sh <D>/atk_N.lean` run. Attacks were verified CONCURRENTLY in background batches of 4. Resolve runs: `python3 <D>/resolve.py <D>/<f>.patch` calling swebench_unified.harness.run_resolve('django__django-12965', patch, timeout=1200, retries=0), the 3 runs launched concurrently.

**POSITIVE CONTROL:** pos_control.lean (byte copy of bundle Solution.lean) -> lean_verify rc=0. VERIFIES.
PREPATCH REPRODUCED: atk_1.lean is a byte copy of the bundle's Solution_prepatch.lean -> rc=1, failing BOTH clauses: ensures_1 `(liveCount tableRefsOld == 1) = true <-> liveCount tableRefsOld.tail = 0` AND the mut-frame `tableRefsOld = withTarget tableRefsOld`. The pre-patch omission is genuinely caught.

### ATTACK RESULTS (path -> verify rc -> observed):
1. atk_1.lean (prepatch bug: whole-vector ==1, no mutation) rc=1 REJECTED (both ensures unsolved).
2. atk_2.lean (control-flow-effect / DIVERGENCE under total termination: right answer after a non-progressing `while spin != 1` loop) rc=1 REJECTED -- unsolved `decreasing_1: spin` goal `0 < spin`. This is the key regression check: `termination "total"` now discharges a decreases obligation, so the prior audit's divergence artifact can no longer verify.
3. atk_2b.lean (divergence, alternate spelling `while spin = 0` / `spin := spin`) rc=1 REJECTED -- `decreasing` goal `spin < spin`.
4. atk_3.lean (FRAME violation: correct boolean, NO mutation) rc=1 REJECTED -- mut-frame goal `tableRefsOld = withTarget tableRefsOld`. The mut frame is load-bearing.
5. atk_4.lean (control-flow-effect: target's use recorded TWICE) rc=1 REJECTED -- `withTarget (withTarget x) = withTarget x`.
6. atk_5.lean (BOUNDARY: `liveCount tableRefs == 0` post-mutation) rc=1 REJECTED -- ensures_1 unsolved.
7. atk_6.lean (PARTIAL-DOMAIN: correct on non-empty, returns false on the EMPTY whole-table-delete state) rc=1 REJECTED -- ensures_1 residual goal is exactly `if_pos : tableRefsOld.isEmpty = true |- false = true <-> liveCount tableRefsOld.tail = 0`, i.e. the spec pins precisely the F2P (test_fast_delete_all) empty-alias_map case.
8. atk_7.lean (off-by-one domain: `liveCount (tableRefs.drop 2) == 0`, skips one non-target table too) rc=1 REJECTED.
9. atk_8.lean (UNGROUNDED-ORACLE ECHO: mutate, then decide from the pre-state snapshot `liveCount tableRefsOld.tail == 0`) rc=0 VERIFIES -> CANDIDATE. Faithful patch materialized at <D>/atk_8.patch against pristine base compiler.py (git cat-file of 437196da9a...:django/db/models/sql/compiler.py). EXECUTED run_resolve -> {completed: true, resolved: true, note: 'resolved'} (<D>/atk_8.resolve.out). CORRECT ECHO, not a break.
10. atk_9.lean (gold's own spelling: `liveCount tableRefs == 1` post-mutation) rc=1 REJECTED -- ensures_1 unsolved. IMPORTANT NUANCE: this expression is mathematically EQUIVALENT to the postcondition -- I proved it in <D>/eqcheck.lean (`(liveCount (withTarget rc) == 1) = true <-> liveCount rc.tail = 0`, lean_verify rc=0). So its rejection is prover incompleteness / spec strictness, NOT a soundness defect: a spec that rejects a behaviourally-gold impl can only cause false NEGATIVES (spec too STRONG), never verify-without-correct. Not a G-EQ break; noted for the faithfulness panel.
11. atk_10.lean (CONTROL-FLOW-EFFECT REORDER: decide BEFORE recording the target's use) rc=0 VERIFIES -> CANDIDATE. Faithful patch <D>/atk_10.patch. EXECUTED run_resolve -> {completed: true, resolved: true} (<D>/atk_10.resolve.out). CORRECT ECHO.
12. atk_11.lean (polarity flipped) rc=1 REJECTED.
13. atk_12.lean (inline withTarget's equation instead of invoking the modeled callee) rc=1 REJECTED -- mut-frame goal not closed by rfl-level reasoning; again strictness, not unsoundness.
14. atk_13.lean (`tableRefs.tail.all (. == 0)`, an equivalent total spelling) rc=1 REJECTED -- ensures_1 unsolved; strictness only.

WHY THE 2 CANDIDATES ARE NOT BREAKS (machine-checked, not speculation): both decide from the PRE-state tail while gold decides from the POST-state tail. Since `withTarget rc = (rc.headD 0 + 1) :: rc.tail` preserves `.tail` exactly, the two are the SAME total function -- proved in <D>/echocheck.lean: `liveCount (withTarget rc).tail = liveCount rc.tail` (lean_verify rc=0). And I did not stop at the proof: I materialized both faithful patches and RAN the official harness on each; both completed=true resolved=true. Per `_derive_audit_verdict` a candidate whose patch resolves is a correct echo, not a weakness.

HARNESS VALIDATION (guards against a false SOUND from a broken resolve method): the gold patch (bundle patch.diff verbatim, <D>/gold.patch) through the SAME run_resolve path -> {completed: true, resolved: true, note: 'resolved'} (<D>/gold.resolve.out). My patch-materialization + resolve invocation are therefore demonstrably correct, and the atk_8/atk_10 resolves are meaningful rather than vacuous.

A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's). refinement.md has exactly 3 legs, NO kind-3: A1 = R (List Nat <-> [alias_refcount[t] for t in alias_map] in insertion order, head = base table); A2 = A-reference + I (the ADDED call to the UNCHANGED callee Query.get_initial_alias, deep-modeled by withTarget; the assignment itself concrete); A3 = I (liveCount counts entries != 0 <=> sum(alias_refcount[t] > 0)). Section B's claim holds: `single_alias` (the function under change) is never axiomatized, and there are no consumed axioms at all -- so the only trust point is the withTarget deep model.

A-LEG CORRESPONDENCE HOLDS (independently checked against real source at base_commit 437196da9a386bd4cc62b0ce3f2de4aba468613d, worktree, compiler.py quoted pristine via `git show` since that worktree carries the gold edit as an uncommitted modification):
- query.py:916-926 get_initial_alias: non-empty alias_map -> `alias = self.base_table; self.ref_alias(alias)` and ref_alias (query.py:758-760) is `alias_refcount[alias] += 1`, with alias_map itself untouched => (h::t) -> (h+1)::t. Empty alias_map -> `join(BaseTable(...))` -> table_alias(create=True) ASSIGNS `alias_refcount[alias] = 1` and appends the sole alias_map entry => [] -> [1]. Both branches are exactly the one total equation `withTarget rc = (rc.headD 0 + 1) :: rc.tail`. Confirmed.
- base_table (query.py:244-247) is the first alias_map key, so head-ordering is right. I probed the obvious way to break this: change_aliases (query.py:847-854) does delete-and-re-append and CAN move the base table to the back, and trim_start unrefs leading aliases so the first key may be a refcount-0 alias. HOWEVER neither runs on the DELETE path before single_alias is consulted -- the only in-tree callers are Query.split_exclude / bump_prefix / relabeled_clone, all operating on freshly-built SUBqueries, and SQLDeleteCompiler.as_sql never calls pre_sql_setup/setup_query. DeleteQuery.do_query (subqueries.py:21) rebuilds alias_map down to the single base-table entry, so the head is still the base table. The bijection is therefore valid on the modeled path.
- G-AX executed: ` python3 <bundle>/axiom_check.py` -> "G-AX OK: activate deep model (== Query.get_initial_alias refcount side effect) sound on 14 real-Query observations", rc=0.
- Model<->patch correspondence: the mut frame pins exactly ONE withTarget application, matching the patch's single added `self.query.get_initial_alias()` line and nothing else; atk_3 (no mutation) and atk_4 (double mutation) are both rejected, so the frame really is discriminating in both directions.

MINOR DOC DEFECTS in refinement.md (cosmetic, do NOT affect soundness, worth a fix): (a) the A1 row names the parameter `refcount : List Nat` but the actual method parameter is `tableRefs : List Nat` -- stale identifier from an earlier revision; (b) the A3 row's justification argues `sum(...) == 1 <=> liveCount tail == 0` via the post-call head-invariant, which is correct, but the row labels the Lean side `return liveCount tableRefs.tail == 0` as tag I against a Python RHS that is textually `sum(...) == 1` -- the two are equivalent-not-identical, so this leg is arguably R-with-argument rather than strict I. The argument given is sound and the equivalence is the one I independently proved in eqcheck.lean, so no correspondence failure; only the tag/label is loose. Also (c) axiom_check.py's docstring and output still call the deep model `activate` while Solution.lean names it `withTarget` -- a stale name, though the equation checked is the right one.

**FLOOR:** 14 attacks (>= 5), prepatch reproduced, positive control verifies and is a distinct file from every attack, 0 inconclusive verify runs, and every verifying candidate has a submitted faithful patch whose resolve COMPLETED. No verifying wrong impl's faithful patch fails to resolve => verify => correct is not refuted. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP: fresh worktree at base_commit 437196da9a from the upstream repository; Solution.lean verifies (lean_verify.sh RC=0); G-AX (14 real-Query obs) and G-CONF (100,010 inputs, seed 12965) both reproduced independently RC=0; `delete` suite passes with gold applied.

**SPEC REGION:** verified byte-identical between Solution.lean and Solution_prepatch.lean via markers.spec_signature(..., VelvetBackend.language) -> identical. Prepatch (`return liveCount tableRefs == 1`, no withTarget) fails verification, so the discriminator is real and lives exactly in the changed op.

CORE EQUIVALENCE ARGUMENT (checked, not taken on trust): real patched code is `get_initial_alias(); sum(alias_refcount[t] > 0 for t in alias_map) == 1`. get_initial_alias leaves the head (base table) refcount >= 1 and touches no other entry, so the Python total is exactly 1 + (live entries in tail); hence `sum(...)==1` <-> `liveCount tail == 0`, which is the spec's postcondition. Over the Nat carrier, `n != 0` <-> `n > 0`, so liveCount's `!= 0` test coincides with Python's `> 0`. Exhaustively confirmed against the REAL patched callee over all vectors len<=4, values 0..3: 0 disagreements. Also confirmed withTarget == real get_initial_alias side effect on both branches, including the empty-alias_map branch that routes through the real join(BaseTable(...)) with a real model ([] -> [1]).

ATTACK 1 - negative refcounts (the one genuine divergence axis). unref_alias/reset_refcounts have NO floor, and I confirmed by direct manipulation that real alias_refcount CAN go negative (e.g. {'p_author': -4}). On such states the model diverges: exhaustive sweep over values -2..2 found 64 disagreements, e.g. pre=[-1] real=False/spec=True, pre=[0,-1] real=True/spec=False. This is the load-bearing assumption in mapping.md ('unref_alias never drives a counted table below 0 on the delete path'), and the `List Nat` carrier structurally excludes it.

I tried hard to reach it and could NOT: (a) ~30 public-API queryset shapes across auth/contenttypes models (exclude/split_exclude/trim_start, nested m2m, chained excludes, Exists/OuterRef, isnull, F()) -> 0 negatives; (b) monkeypatched Query.unref_alias to trap any sub-zero write during query construction -> 0 negative events; (c) instrumented the real patched single_alias and ran ~25 Django test suites (delete, delete_regress, queries, many_to_many, m2m_through, generic_relations, model_inheritance, auth_tests, admin_views, aggregation, expressions, filtered_relation, select_related, update, ...) -> 1381 real observations, 33 distinct pre-states, 0 negatives, 0 real-vs-spec disagreements, 0 cases where post != withTarget(pre). Assumption holds empirically; not a demonstrable break.

ATTACK 2 - stale/reordered base_table cache (withTarget can only bump the HEAD; real code bumps `self.base_table`, a cached_property). I DID manufacture head != base_table via bump_prefix after forcing the cache (alias_map ['U0','U1'] while cached base_table='auth_permission'). But this is not a spec break: real get_initial_alias() then raises KeyError, i.e. the state is broken in the repo too, not silently divergent. Via public API on DeleteQuery, head == base_table always; clone() and change_aliases both invalidate the cache. The single instrumented head != base_table observation was the empty-alias_map case (base_table None) and agreed.

ATTACK 3 - do_query wipes alias_map but not alias_refcount/table_map. Emulated: get_initial_alias then creates alias 'T1' and the carrier reads [1] == withTarget([]). Agrees.

ATTACK 4 - mut-frame / second call site. The frame `ensures tableRefs = withTarget tableRefsOld` matches the lone real side effect. Confirmed the only other single_alias consumer (mysql/compiler.py:18) reads the same property; cached_property means get_initial_alias fires once, so no double-bump.

NOTE (not a faithfulness defect, flagging for G-EQ): a gold-EQUIVALENT impl `return (tableRefs.filter (fun n => n != 0)).length == 1` (whole post-vector count, equivalent since the post head is always >= 1) FAILS to verify - loom_solve leaves the goal `((filter (n != 0) (withTarget rc)).length == 1) = true <-> liveCount rc.tail = 0` unsolved. The provided @[grind] withTarget_tail lemma only bridges the tail form. This is a proof-automation gap, not spec drift: the spec's mathematical content still matches the repo pointwise. A trivially-reworded gold-equivalent variant does verify.

**CONCLUSION:** no reachable input where the modeled function disagrees with the real patched callee. Spec is not too strong on any state expressible in the declared carrier. FAITHFUL.

**SETUP:** fresh worktree at base_commit 437196da9a from the upstream repository; Solution.lean verifies (lean_verify.sh RC=0); G-AX (14 real-Query obs) and G-CONF (100,010 inputs, seed 12965) both reproduced independently RC=0; `delete` suite passes with gold applied.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 (leakage / gold-reconstruction) for django__django-12965 velvet. VERDICT: NO-LEAKAGE. This OVERTURNS the prior recorded G-PANEL-3 LEAKAGE verdict, which was written against an OLDER spec revision whose cited lines no longer exist.

#### INTEGRITY / PRELIMINARIES (all verified myself)
* markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) -> True. Spec region byte-identical between the shipped solution and the prepatch variant, so the discriminating content lives in the impl region only, as required.
* G-HYGIENE region_hashes recomputed: axioms/pure/impl/spec_view ALL match meta.json. No post-hoc spec drift.
* scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms directDeleteEligible` -> "does not depend on any axioms": no sorryAx, proof is real, not fake.
* leakage.screen(src, velvet, patch.diff, problem_statement, test_patch) re-run by me: hard_failures=[], warnings=[], passed=True. Mechanical screen genuinely clean, not merely recorded as clean.

#### The 56-line spec view I actually judged
I regenerated the consumer view with markers.spec_view rather than eyeballing Solution.lean. The impl region collapses to a placeholder and the prove_correct body is elided. What remains: withTarget, liveCount, withTarget_tail, and the two `ensures` clauses.

### WHY THE PRIOR LEAKAGE FINDING IS STALE (primary reason for the overturn)
The prior verdict's three cited leak sites are all ABSENT from the current spec view. I string-checked each:
 1. It quotes postcondition `ensures direct <-> liveCount (withTarget tableRefsOld) = 1` -- NOT PRESENT. The current clause is `direct <-> liveCount tableRefsOld.tail = 0`, phrased on the PRE-state tail, i.e. "no table OTHER than the targeted one is live." The `withTarget`-composed-then-compare-to-1 formulation it objected to is gone.
 2. It quotes a pure-region docstring "an empty state gains the target as its sole entry (count 1)" -- NOT PRESENT. That was the gold diagnosis in prose; it has been de-narrated away.
 3. It quotes a case-split presentation `withTarget | [] => [1] | h::t => (h+1)::t` -- NOT PRESENT. The current definition is the single total equation `(rc.headD 0 + 1) :: rc.tail`, which does not foreground the empty-list case at all.
The in-bundle RELAXED_LEAKAGE.md is stale in exactly the same way (it quotes `singleAlias`/`numActive`/the same removed docstring, asserts G-LEAK status should be "relaxed", and cites a policy file `RELAXED_LEAKAGE.md` that does not exist at HEAD -- I checked with git cat-file). meta.json in fact records G-LEAK status=pass, mode=strict, "spec view clean". The relaxation is no longer claimed or needed. FILE HYGIENE ISSUE, not a leak: RELAXED_LEAKAGE.md should be deleted or rewritten -- it currently reads as a confession of a leak that has since been fixed, and it quotes the gold hunk verbatim. It is NOT shipped to consumers (see below), so it is not itself a leak vector, but it actively misleads auditors and is what the prior panelist appears to have graded.

#### The substantive question: is the residual disclosure the gold edit?
The real residual disclosure is the mut-frame clause `ensures tableRefs = withTarget tableRefsOld` -- the spec tells the consumer the operation MUTATES its refcount state by bumping the head. That is a real fact about the gold edit (`self.query.get_initial_alias()` has exactly that side effect). So I tested whether this is an avoidable narration of the fix MECHANISM (-> leak) or an unavoidable statement of required BEHAVIOR (-> permitted, since spec_guide.md rule 6 permits stating abstract desired behavior and rule 5 AFFIRMATIVELY REQUIRES pinning the frame).

Decisive experiment -- I built a real django worktree at base_commit 437196da9a, applied the hidden test_patch, and ran the sole F2P `delete.tests.FastDeleteTests.test_fast_delete_all`:
 * NON-MUTATING fix (`sum(...) <= 1`, which gets the boolean decision right on the empty state WITHOUT registering the base table): test ERRORS. AttributeError: 'NoneType' object has no attribute 'startswith', from compiler.py:1415 `_as_sql` -> `quote_name_unless_alias(query.base_table)`. With an empty alias_map, `Query.base_table` (query.py:245 iterates alias_map) returns None, so `DELETE FROM %s` gets None. The direct-delete path is UNREACHABLE unless something first populates alias_map.
 * GOLD-SHAPED fix (add `self.query.get_initial_alias()`): test passes, OK.
So the mutation is not incidental and not a stylistic choice of the gold author -- it is load-bearing for the issue to be resolvable at all. A spec that omitted the mut frame would admit the `<= 1` impl, which CRASHES on the exact scenario the problem_statement describes (`Model.objects.all().delete()`). Omitting it would therefore be a genuine spec-too-weak hole (a G-PANEL-1 defect), not a leakage improvement. Stating it is mandatory under directive 5, and per the guide's own framing this is desired behavior ("the state must end up with the target table accounted for"), not the diagnosis ("single_alias forgot to call get_initial_alias, so the count was 0 instead of 1").

#### Naming / reconstruction checks
* No gold-diff line is quoted. The gold's added lines are the comment "# Ensure base table is in aliases." and `self.query.get_initial_alias()`; neither appears in any form.
* No patched file/function/line named anywhere in the spec view, in identifiers OR comments. Every repo symbol is renamed off its counterpart: single_alias -> directDeleteEligible, alias_refcount -> tableRefs, get_initial_alias -> withTarget, count_active_tables -> liveCount. Note the repo even HAS a `count_active_tables` (query.py:928) -- `liveCount` avoids echoing it too.
* PS-derivability of the surviving vocabulary: "direct delete" vs "subquery" is squarely public -- the problem_statement literally contrasts `DELETE FROM t` against `DELETE FROM t WHERE id IN (SELECT ...)` and says "we shouldn't change the SQL here." "Table" and "target table" are public. I re-ran the token scan against problem_statement ONLY (not hints_text, per the rule): single_alias, alias_refcount, alias_map, get_initial_alias, base_table, refcount, cached_property all 0 occurrences. The 3 `alias` hits in the PS are inside the quoted MySQL LOCK TABLES docs ("use aliases instead") -- an unrelated SQL-locking sense -- and the spec view does not use the word `alias` at all, so it does not even trade on that coincidence. hints_text contributes "single alias"; the spec view avoids that phrase, which matters because hints-only terms are non-public under rule 6.
* No bug/fix narration. The docstrings describe the decision ("direct delete over the table it targets rather than via a subquery that selects the rows to remove") and the state transition ("that table's usage count goes up by one, and no other table's count changes") in abstract carrier terms. No "regression", "previously", "incorrectly", "was broken".
* Reconstruction difficulty is real, not nominal: a consumer reading the spec view learns the abstract law but must still discover, in ~1400 lines of compiler.py, WHICH predicate governs direct-vs-subquery, that it is a cached_property, that the state is alias_refcount keyed by alias_map, and that the way to bump the head is `get_initial_alias()`. The spec names none of those. That said, I note honestly that `modeled_functions` in meta.json IS shipped to consumers in spec modes and DOES name `SQLDeleteCompiler.single_alias` at compiler.py:1408 -- but that is the deliberate, mode-defined EDIT-LOCALIZATION layer granted equally to the no-spec control arm (mode 0), so it is not spec-view leakage and does not confound the spec-vs-no-spec ablation. Separately, `deep_model_references` (which names get_initial_alias) is NOT plumbed into any consumer prompt -- dataset.py projects only repo_symbol/repo_location -- and refinement.md / mapping.md / RELAXED_LEAKAGE.md, which DO quote the gold hunk verbatim, are never shipped either (I traced eval/dataset.py and eval/prompts.py; only spec_view and the localization projection reach the agent).

### SECONDARY OBSERVATION (not leakage; flagged for G-PANEL-1/G-VERIFY)
The proof automation is brittle in a way that slightly over-constrains the consumer. A semantically IDENTICAL gold impl that inlines the model -- `tableRefs := (tableRefs.headD 0 + 1) :: tableRefs.tail` instead of `withTarget tableRefs`, definitionally equal by rfl -- FAILS under the shipped `loom_solve` (unsolved goal `(tableRefsOld.headD 0 + 1) :: tableRefsOld.tail = withTarget tableRefsOld`) and needs an added `unfold withTarget` to go through. Likewise the gold-literal `liveCount tableRefs == 1` post-mutation form does not discharge against the `.tail = 0` clause without manual work. This is a proof-ergonomics wart, not a leak and not unsoundness (the spec still admits the gold behavior, and I confirmed the prepatch impl is correctly REJECTED, failing both ensures clauses -- so G-DIFF's discrimination is genuine). Out of scope for this gate; recorded so it is not lost.

### Bottom line
No spec-view line quotes the gold diff, names a patched symbol or location, or narrates the fix mechanism. The one fact the spec view discloses beyond the problem_statement -- that the targeted table must be accounted for in the state before the liveness count -- is behaviorally MANDATORY (proved by execution: the non-mutating alternative crashes on the PS's own scenario) and is therefore required by the frame directive rather than optional narration. The prior LEAKAGE verdict graded a spec revision that no longer exists. Recommend: G-PANEL-3 pass; delete or fully rewrite the stale RELAXED_LEAKAGE.md and drop the now-inapplicable relaxed-leakage claim.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.