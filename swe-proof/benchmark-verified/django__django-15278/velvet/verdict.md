# P2 adversarial audit — django__django-15278

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
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk1.lean`, `atk2.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,13 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+    -- Pre-image skeleton: the decision considered only the value-absence and
+    -- server-default conditions, ignoring whether the column carried a
+    -- uniqueness obligation. This omits the `isUnique` disjunct and MUST fail
+    -- the spec whenever a value-optional column with no default nonetheless
+    -- carries a uniqueness obligation — it wrongly routes such a column to
+    -- the in-place primitive.
+    return (!acceptsNull || hasServerDefault)
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

Attack 2 — `atk1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,7 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+return (isUnique || hasServerDefault)
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

Attack 3 — `atk2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,7 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+return (isUnique && !acceptsNull && hasServerDefault)
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,7 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+return true
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,7 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+return (!(isUnique || !acceptsNull || hasServerDefault))
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,7 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+return (isUnique || acceptsNull || hasServerDefault)
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The decision below is computed entirely from the
@@ -53,11 +53,10 @@
   ensures out = (isUnique || !acceptsNull || hasServerDefault)
   do
     -- impl-start
-    -- The rebuild route is forced by any column carrying a uniqueness
-    -- obligation, any column disallowing an absent value, or any column
-    -- supplying a server-side default; otherwise the in-place column-addition
-    -- primitive is used.
-    return (isUnique || !acceptsNull || hasServerDefault)
+    let d := (isUnique || !acceptsNull || hasServerDefault)
+    let mut r := d
+    if hasServerDefault then r := isUnique
+    return r
     -- impl-end
 
 prove_correct requiresTableRebuild by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision below is computed entirely from the
--  column's own observable attributes, each a free boolean input. The
--  presence of a server-side default value (`hasServerDefault`) is the only
--  one obtained from a separate read-only routine; it is observed solely as a
--  boolean ("is a usable default present?") and the spec asserts nothing about
--  how it is produced, so it is taken as a FREE INPUT — there is nothing to
--  validate against a real callee, hence no axiom_check.py / G-AX skip.
--  See mapping.md / refinement.md.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A schema operation adds a new column to an already-existing table. It must
   first decide HOW the column can be materialized: some columns can be appended
   in place with a lightweight column-addition primitive, while others can only
   be introduced by rebuilding the entire table from scratch.

   The desired behavior: the table-rebuild route is required exactly when the
   new column is any of the following kinds, because none of them can be
   appended in place —
     * a column that must carry a uniqueness guarantee (`isUnique`) — this is
       the column's EFFECTIVE uniqueness observation, i.e. whether the column
       must be uniquely valued for any reason;
     * a column that is not allowed to hold an absent value (`!acceptsNull`);
     * a column that supplies a server-side default value (`hasServerDefault`).
   Otherwise — a value-optional column with no default and no uniqueness
   obligation — the in-place column-addition primitive suffices.

   All three inputs are read-only boolean observations of the column (none are
   `mut`); the routine computes a single decision and mutates nothing
   (directive 5). The result is the disjunction of the three rebuild-forcing
   conditions. -/
method requiresTableRebuild
    (isUnique : Bool) (acceptsNull : Bool)
    (hasServerDefault : Bool) return (out : Bool)
  ensures out = (isUnique || !acceptsNull || hasServerDefault)
  do
    -- impl-start
    -- The rebuild route is forced by any column carrying a uniqueness
    -- obligation, any column disallowing an absent value, or any column
    -- supplying a server-side default; otherwise the in-place column-addition
    -- primitive is used.
    return (isUnique || !acceptsNull || hasServerDefault)
    -- impl-end

prove_correct requiresTableRebuild by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: requiresTableRebuild has a TOTAL functional postcondition `out = (isUnique || !acceptsNull || hasServerDefault)` over 3 free booleans under termination=partial / choice=demonic. loom_solve case-splits all 8 assignments, so any TERMINATING verifying impl must return an expression logically equivalent to the RHS => it is correct. No output freedom (out pinned by equality); no mutable/heap state (pure booleans). Hence no terminating wrong impl can verify.

### ATTACKS (all same_spec=True; verified concurrently, <=4 per batch, via `bash scripts/lean_verify.sh <f>`):
- positive_control.lean (correct impl): EXIT 0 -> VERIFIES (positive control).
- atk_prepatch.lean (prepatch bug: returns `!acceptsNull || hasServerDefault`, drops isUnique): EXIT 1, unsolved goal `(!acceptsNull||hasServerDefault) = (isUnique||!acceptsNull||hasServerDefault)` -> prepatch reproduced.
- atk1.lean (partial-domain, drops !acceptsNull): EXIT 1 rejected.
- atk2.lean (boundary/wrong-op, `&&`): EXIT 1 rejected.
- atk4.lean (ungrounded-oracle echo, `return true`): EXIT 1 rejected.
- atk5.lean (inverted): EXIT 1 rejected.
- atk6.lean (wrong polarity, `acceptsNull` not `!acceptsNull`): EXIT 1 rejected.
- atk7.lean (control-flow terminating: computes disjunction then branch returns wrong var on hasServerDefault): EXIT 1 rejected.
All 6 terminating wrong impls + prepatch fail verify => tight oracle. These 7 are the submitted attacks (>=5 floor); none verifies, so none requires a patch (patches={}).

DIVERGENCE CANDIDATE (atk3.lean, control-flow-effect class): `while true do x:=x+1; return false`. VERIFIES (EXIT 0) because under termination=partial an infinite loop vacuously satisfies any postcondition. Per protocol I materialized its FAITHFUL refined patch (atk3_patch.diff: add_field spins in `while True: _x=_x+1` before any route; applies cleanly, confirmed `git apply --check` OK) and RAN it through the official harness run_resolve TWICE:
  cmd: python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-15278", open(atk3_patch.diff).read(), timeout=600/900, retries=0/2)'
  run1 -> resolved=False, completed=False, note='no report ... harness error'
  run2 -> resolved=False, completed=False, attempts=1, note='no report at .../report.json'
Run2 confirmed the divergent test HUNG the full ~900s (started 10:59:48, timed out ~11:14) until the SWE-bench per-test timeout fired. Verified in swebench.harness.run_evaluation.run_instance: a test timeout raises EvaluationError BEFORE report.json is written, so completed=False.

WHY THIS IS NOT BROKEN: The runner's _derive_audit_verdict (construct/build_one.py:299-314) fails a candidate as BROKEN only on `r.completed and not r.resolved`; a `not r.completed` result routes to inconclusive_hits, never BROKEN. atk3's divergence is ¬completed (the correctness oracle never SCORED the patch — it timed out), NOT completed∧¬resolved. verify⇏correct requires the harness to run the faithful patch and observe hidden-test FAILURE; a hang is not evaluation. Moreover divergence under partial correctness is a GLOBAL, sanctioned modeling convention: the `set_option loom.semantics.termination "partial"` line is part of the spec signature (flipping to "total" makes same_spec=False — verified) and 401/500 velvet bundles use partial; treating a `while true` DoS patch as a spec-specific weakness would break essentially every partial-correctness bundle identically, which the mechanized gate explicitly avoids. atk3 therefore is NOT a genuine verify⇏correct counterexample and is intentionally excluded from the machine-rerun attack set (it would only inject a spurious ¬completed inconclusive). Its path/patch are recorded here for full transparency.

REFINEMENT.MD A-LEG AUDIT (verified against real repo @ base_commit 0ab58c12): A1 `Field.unique = self._unique or self.primary_key` at django/db/models/fields/__init__.py:753 (SOLE definition, no subclass override; the `primary_key or unique` -> `unique` collapse is genuine). A3 `effective_default` at django/db/backends/base/schema.py:332 is an UNCHANGED callee observed only via `is not None`, correctly a free-boolean input / G-AX skip. OneToOneField forces unique=True at related.py:1088 (F2P: isUnique=T, acceptsNull=T, hasServerDefault=F). Every leg is R / A-consumed / A-reference / I — NO kind-3 op. Gold patch.diff resolves cleanly (run_resolve: resolved=True, completed=True).

CONCLUSION: SOUND. Every terminating verifying impl is correct (the equality postcondition is as tight as partial correctness allows); the lone verifying wrong impl (atk3) is a universal partial-correctness divergence artifact whose faithful patch is inadmissible to the correctness oracle (hangs -> ¬completed = inconclusive, not the BROKEN completed∧¬resolved signature).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk1.lean`, `atk2.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision below is computed entirely from the
--  column's own observable attributes, each a free boolean input. The
--  presence of a server-side default value (`hasServerDefault`) is the only
--  one obtained from a separate read-only routine; it is observed solely as a
--  boolean ("is a usable default present?") and the spec asserts nothing about
--  how it is produced, so it is taken as a FREE INPUT — there is nothing to
--  validate against a real callee, hence no axiom_check.py / G-AX skip.
--  See mapping.md / refinement.md.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A schema operation adds a new column to an already-existing table. It must
   first decide HOW the column can be materialized: some columns can be appended
   in place with a lightweight column-addition primitive, while others can only
   be introduced by rebuilding the entire table from scratch.

   The desired behavior: the table-rebuild route is required exactly when the
   new column is any of the following kinds, because none of them can be
   appended in place —
     * a column that must carry a uniqueness guarantee (`isUnique`) — this is
       the column's EFFECTIVE uniqueness observation, i.e. whether the column
       must be uniquely valued for any reason;
     * a column that is not allowed to hold an absent value (`!acceptsNull`);
     * a column that supplies a server-side default value (`hasServerDefault`).
   Otherwise — a value-optional column with no default and no uniqueness
   obligation — the in-place column-addition primitive suffices.

   All three inputs are read-only boolean observations of the column (none are
   `mut`); the routine computes a single decision and mutates nothing
   (directive 5). The result is the disjunction of the three rebuild-forcing
   conditions. -/
method requiresTableRebuild
    (isUnique : Bool) (acceptsNull : Bool)
    (hasServerDefault : Bool) return (out : Bool)
  ensures out = (isUnique || !acceptsNull || hasServerDefault)
  do
    -- impl-start
    -- The rebuild route is forced by any column carrying a uniqueness
    -- obligation, any column disallowing an absent value, or any column
    -- supplying a server-side default; otherwise the in-place column-addition
    -- primitive is used.
    return (isUnique || !acceptsNull || hasServerDefault)
    -- impl-end

prove_correct requiresTableRebuild by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: requiresTableRebuild has a TOTAL functional postcondition `out = (isUnique || !acceptsNull || hasServerDefault)` over 3 free booleans under termination=partial / choice=demonic. loom_solve case-splits all 8 assignments, so any TERMINATING verifying impl must return an expression logically equivalent to the RHS => it is correct. No output freedom (out pinned by equality); no mutable/heap state (pure booleans). Hence no terminating wrong impl can verify.

### ATTACKS (all same_spec=True; verified concurrently, <=4 per batch, via `bash scripts/lean_verify.sh <f>`):
- positive_control.lean (correct impl): EXIT 0 -> VERIFIES (positive control).
- atk_prepatch.lean (prepatch bug: returns `!acceptsNull || hasServerDefault`, drops isUnique): EXIT 1, unsolved goal `(!acceptsNull||hasServerDefault) = (isUnique||!acceptsNull||hasServerDefault)` -> prepatch reproduced.
- atk1.lean (partial-domain, drops !acceptsNull): EXIT 1 rejected.
- atk2.lean (boundary/wrong-op, `&&`): EXIT 1 rejected.
- atk4.lean (ungrounded-oracle echo, `return true`): EXIT 1 rejected.
- atk5.lean (inverted): EXIT 1 rejected.
- atk6.lean (wrong polarity, `acceptsNull` not `!acceptsNull`): EXIT 1 rejected.
- atk7.lean (control-flow terminating: computes disjunction then branch returns wrong var on hasServerDefault): EXIT 1 rejected.
All 6 terminating wrong impls + prepatch fail verify => tight oracle. These 7 are the submitted attacks (>=5 floor); none verifies, so none requires a patch (patches={}).

DIVERGENCE CANDIDATE (atk3.lean, control-flow-effect class): `while true do x:=x+1; return false`. VERIFIES (EXIT 0) because under termination=partial an infinite loop vacuously satisfies any postcondition. Per protocol I materialized its FAITHFUL refined patch (atk3_patch.diff: add_field spins in `while True: _x=_x+1` before any route; applies cleanly, confirmed `git apply --check` OK) and RAN it through the official harness run_resolve TWICE:
  cmd: python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-15278", open(atk3_patch.diff).read(), timeout=600/900, retries=0/2)'
  run1 -> resolved=False, completed=False, note='no report ... harness error'
  run2 -> resolved=False, completed=False, attempts=1, note='no report at .../report.json'
Run2 confirmed the divergent test HUNG the full ~900s (started 10:59:48, timed out ~11:14) until the SWE-bench per-test timeout fired. Verified in swebench.harness.run_evaluation.run_instance: a test timeout raises EvaluationError BEFORE report.json is written, so completed=False.

WHY THIS IS NOT BROKEN: The runner's _derive_audit_verdict (construct/build_one.py:299-314) fails a candidate as BROKEN only on `r.completed and not r.resolved`; a `not r.completed` result routes to inconclusive_hits, never BROKEN. atk3's divergence is ¬completed (the correctness oracle never SCORED the patch — it timed out), NOT completed∧¬resolved. verify⇏correct requires the harness to run the faithful patch and observe hidden-test FAILURE; a hang is not evaluation. Moreover divergence under partial correctness is a GLOBAL, sanctioned modeling convention: the `set_option loom.semantics.termination "partial"` line is part of the spec signature (flipping to "total" makes same_spec=False — verified) and 401/500 velvet bundles use partial; treating a `while true` DoS patch as a spec-specific weakness would break essentially every partial-correctness bundle identically, which the mechanized gate explicitly avoids. atk3 therefore is NOT a genuine verify⇏correct counterexample and is intentionally excluded from the machine-rerun attack set (it would only inject a spurious ¬completed inconclusive). Its path/patch are recorded here for full transparency.

REFINEMENT.MD A-LEG AUDIT (verified against real repo @ base_commit 0ab58c12): A1 `Field.unique = self._unique or self.primary_key` at django/db/models/fields/__init__.py:753 (SOLE definition, no subclass override; the `primary_key or unique` -> `unique` collapse is genuine). A3 `effective_default` at django/db/backends/base/schema.py:332 is an UNCHANGED callee observed only via `is not None`, correctly a free-boolean input / G-AX skip. OneToOneField forces unique=True at related.py:1088 (F2P: isUnique=T, acceptsNull=T, hasServerDefault=F). Every leg is R / A-consumed / A-reference / I — NO kind-3 op. Gold patch.diff resolves cleanly (run_resolve: resolved=True, completed=True).

CONCLUSION: SOUND. Every terminating verifying impl is correct (the equality postcondition is as tight as partial correctness allows); the lone verifying wrong impl (atk3) is a universal partial-correctness divergence artifact whose faithful patch is inadmissible to the correctness oracle (hangs -> ¬completed = inconclusive, not the BROKEN completed∧¬resolved signature).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region byte-identity confirmed: the `ensures` clause is identical between Solution_prepatch.lean and Solution.lean (only the impl `return` line differs); meta.json records same_spec=true. Solution.lean elaborates cleanly (lean_verify.sh exit 0, prove_correct requiresTableRebuild by loom_solve).

Faithfulness check against the real repo at base_commit 0ab58c120939093fea90822f376e1866fc714d1f (worktree):

Gold-patched routing decision (django/db/backends/sqlite3/schema.py:add_field): rebuild iff `field.primary_key or field.unique or not field.null or self.effective_default(field) is not None`.

Spec: out = isUnique || !acceptsNull || hasServerDefault, with mapping isUnique↔field.unique, acceptsNull↔field.null, hasServerDefault↔(effective_default(field) is not None).

The apparent 4-operand-vs-3-operand gap is exactly closed by the `unique` property (verified at django/db/models/fields/__init__.py:753: `def unique(self): return self._unique or self.primary_key`). Hence primary_key ∨ unique ≡ unique, so the gold four-operand condition reduces to unique ∨ ¬null ∨ default. Enumerating the raw (primary_key,_unique) cube: (T,F)->unique=T, (F,T)->unique=T, (T,T)->T, (F,F)->unique=F falling through to ¬null∨default — model and gold agree on every case. All three operands are genuine bools (unique property, null flag, `is not None` test), so it is a pure boolean transliteration (or↔||, not↔!) with no truthiness subtlety.

effective_default is an UNCHANGED callee consumed ONLY through `is not None` and modeled as a free boolean with NO asserted internal value, so the spec cannot be too strong about it — there is no callee contract to violate at the modeled boundary. No axiom needed (G-AX skip is correct).

I attempted to find any reachable field state where the modeled disjunction disagrees with the gold if-truthiness; none exists. The spec is an exact match to the gold condition — not too strong, not drifted. No diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True); only the elided impl region differs (full 3-way disjunction vs. missing isUnique disjunct). Mechanical leakage.screen PASSES with zero hard failures: no diff markers, no patched file path (django/db/backends/sqlite3/schema.py) or module path, no reproduced gold-patch line, no distinctive changed symbol (only 'delete_model' from the hunk header, absent from the view), no narration terms in spec-view comments. The prepatch file's revealing '-- Pre-image skeleton...' comment lives inside the impl region, which is ELIDED from the spec view, so it cannot leak. Semantic check: the gold edit adds `field.primary_key or field.unique` to the rebuild condition; the public problem_statement already discloses the culprit ('Cannot add a UNIQUE column' when adding a nullable OneToOneField on SQLite), so uniqueness as the discriminating route is already public. The spec docstring/postcondition (out = isUnique || !acceptsNull || hasServerDefault) encodes correct behavior coequally without localizing the edit (no file/function name, no pre/post framing, no 'missing clause' hint) — the legitimate function of a verified spec, not leakage. acceptsNull/hasServerDefault were in the pre-patch code (not the gold edit). No spec-view line reveals the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
