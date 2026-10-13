# P2 adversarial audit — django__django-15252

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All six same-spec wrong impls fail to close their correct_* proof (genuine rfl failures on concrete decidable-record equalities), so no impl with a closing clean-axiom proof exists whose faithful patch could be materialized/resolved.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,18 +98,9 @@
 -- impl-start
 def implementation_provisionRecordsTable
     (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
-  -- The bookkeeping table must be present to record applied migrations, but it
-  -- must not be provisioned when there is nothing to record.
+  -- ATTACK (prepatch bug): always provision, never short-circuit
   let mut provisioned := false
-  if plannedOps = some [] then
-    if !tableExists then
-      -- nothing to record and no table: short-circuit with a no-applied state.
-      return { provisionedTable := false, state := State.projectState false }
-    -- table already present: leave it untouched and proceed.
-  else
-    -- there is work to record (or the batch is computed): provision the table.
-    provisioned := true
-  -- the routine's unchanged remainder produces the project state.
+  provisioned := true
   return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,18 +98,13 @@
 -- impl-start
 def implementation_provisionRecordsTable
     (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
-  -- The bookkeeping table must be present to record applied migrations, but it
-  -- must not be provisioned when there is nothing to record.
+  -- ATTACK (boundary): short-circuit state has wrong includesApplied flag (true)
   let mut provisioned := false
   if plannedOps = some [] then
     if !tableExists then
-      -- nothing to record and no table: short-circuit with a no-applied state.
-      return { provisionedTable := false, state := State.projectState false }
-    -- table already present: leave it untouched and proceed.
+      return { provisionedTable := false, state := State.projectState true }
   else
-    -- there is work to record (or the batch is computed): provision the table.
     provisioned := true
-  -- the routine's unchanged remainder produces the project state.
   return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,18 +98,15 @@
 -- impl-start
 def implementation_provisionRecordsTable
     (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
-  -- The bookkeeping table must be present to record applied migrations, but it
-  -- must not be provisioned when there is nothing to record.
+  -- ATTACK (control-flow-effect): in empty+present, wrongly provision the table
   let mut provisioned := false
   if plannedOps = some [] then
     if !tableExists then
-      -- nothing to record and no table: short-circuit with a no-applied state.
       return { provisionedTable := false, state := State.projectState false }
-    -- table already present: leave it untouched and proceed.
+    else
+      provisioned := true
   else
-    -- there is work to record (or the batch is computed): provision the table.
     provisioned := true
-  -- the routine's unchanged remainder produces the project state.
   return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,18 +98,12 @@
 -- impl-start
 def implementation_provisionRecordsTable
     (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
-  -- The bookkeeping table must be present to record applied migrations, but it
-  -- must not be provisioned when there is nothing to record.
+  -- ATTACK: empty plan always short-circuits to projectState false regardless of table
   let mut provisioned := false
   if plannedOps = some [] then
-    if !tableExists then
-      -- nothing to record and no table: short-circuit with a no-applied state.
-      return { provisionedTable := false, state := State.projectState false }
-    -- table already present: leave it untouched and proceed.
+    return { provisionedTable := false, state := State.projectState false }
   else
-    -- there is work to record (or the batch is computed): provision the table.
     provisioned := true
-  -- the routine's unchanged remainder produces the project state.
   return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,19 +98,14 @@
 -- impl-start
 def implementation_provisionRecordsTable
     (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
-  -- The bookkeeping table must be present to record applied migrations, but it
-  -- must not be provisioned when there is nothing to record.
+  -- ATTACK (oracle echo): non-empty/none path returns continuationResult none, dropping the batch
   let mut provisioned := false
   if plannedOps = some [] then
     if !tableExists then
-      -- nothing to record and no table: short-circuit with a no-applied state.
       return { provisionedTable := false, state := State.projectState false }
-    -- table already present: leave it untouched and proceed.
   else
-    -- there is work to record (or the batch is computed): provision the table.
     provisioned := true
-  -- the routine's unchanged remainder produces the project state.
-  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
+  return { provisionedTable := provisioned, state := State.continuationResult none }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,18 +98,14 @@
 -- impl-start
 def implementation_provisionRecordsTable
     (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
-  -- The bookkeeping table must be present to record applied migrations, but it
-  -- must not be provisioned when there is nothing to record.
+  -- ATTACK (partial-domain): plan=none wrongly treated as no-provision
   let mut provisioned := false
-  if plannedOps = some [] then
-    if !tableExists then
-      -- nothing to record and no table: short-circuit with a no-applied state.
-      return { provisionedTable := false, state := State.projectState false }
-    -- table already present: leave it untouched and proceed.
-  else
-    -- there is work to record (or the batch is computed): provision the table.
-    provisioned := true
-  -- the routine's unchanged remainder produces the project state.
+  match plannedOps with
+  | none => provisioned := false
+  | some [] =>
+      if !tableExists then
+        return { provisionedTable := false, state := State.projectState false }
+  | some (_ :: _) => provisioned := true
   return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Provisioning the bookkeeping table that records applied migration work.

Before a batch of migration operations runs, the system may need to provision a
small bookkeeping table whose rows record which migrations have already been
applied. Provisioning that table is only appropriate when there is migration
work to record.

The batch of work to perform is described by `plannedOps`:

  * `none` — the caller asks the routine to compute the batch itself;
  * `some []` — the caller explicitly states there is nothing to do;
  * `some (_ :: _)` — the caller supplies a non-empty batch of work.

`tableExists` says whether the bookkeeping table is already present.

The desired behavior:

  * When the caller explicitly supplies an empty batch (`some []`), the
    bookkeeping table must NOT be provisioned. If, in addition, the table is
    absent, the routine short-circuits and returns a project state that includes
    no already-applied migrations.
  * Otherwise (there is work to record, or the batch is left for the routine to
    compute) the bookkeeping table is provisioned and the routine proceeds
    through its unchanged remainder, yielding that remainder's project state.

The two observable components are whether provisioning was performed and which
project state is returned.
-/

-- axioms-start
-- No UNCHANGED outside callee needs an `opaque` signature here. The two inputs
-- the routine branches on (the planned batch and whether the bookkeeping table
-- is present) enter as plain data, and the only operation performed — the
-- guarded decision about whether to provision the table and whether to
-- short-circuit — is modeled directly (below). The construction of the returned
-- project states (the short-circuit state, and the state produced by the
-- unchanged remainder) is represented by structural carriers in the `pure`
-- region rather than abstracted behind a consumed axiom. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A single planned migration operation, reduced to an opaque identity (only
the shape of the batch — empty / non-empty / absent — is ever observed). -/
abbrev PlannedOp := Nat

/-- The project state the routine yields. Two distinguishable shapes are
relevant:

* `projectState includesApplied` — a freshly built project state, carrying the
  already-applied migrations iff `includesApplied` is `true`. The short-circuit
  path returns `projectState false` (a state with no applied migrations).
* `continuationResult plannedOps` — the project state produced by the routine's
  unchanged remainder for the given batch. It is left as an opaque structural
  carrier because that remainder is not touched by the behavior under
  specification. -/
inductive State where
  | projectState (includesApplied : Bool) : State
  | continuationResult (plannedOps : Option (List PlannedOp)) : State
deriving DecidableEq

/-- The two observable components of the routine's outcome:

* `provisionedTable` — whether the bookkeeping-table provisioning step was
  performed;
* `state` — the project state returned. -/
structure Outcome where
  provisionedTable : Bool
  state : State
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The outcome is pinned, in both components, to the inputs:

* an explicitly empty batch with the table absent ⇒ no provisioning and the
  short-circuit no-applied state;
* an explicitly empty batch with the table present ⇒ no provisioning, then the
  unchanged remainder's state for the empty batch;
* any other batch (absent, or non-empty) ⇒ provisioning is performed, then the
  unchanged remainder's state for that batch. -/
def problem_spec_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool)
    (result : Outcome) : Prop :=
  if plannedOps = some [] then
    if tableExists then
      result = { provisionedTable := false, state := State.continuationResult (some []) }
    else
      result = { provisionedTable := false, state := State.projectState false }
  else
    result = { provisionedTable := true, state := State.continuationResult plannedOps }
-- post-conditions-end

-- impl-start
def implementation_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
  -- The bookkeeping table must be present to record applied migrations, but it
  -- must not be provisioned when there is nothing to record.
  let mut provisioned := false
  if plannedOps = some [] then
    if !tableExists then
      -- nothing to record and no table: short-circuit with a no-applied state.
      return { provisionedTable := false, state := State.projectState false }
    -- table already present: leave it untouched and proceed.
  else
    -- there is work to record (or the batch is computed): provision the table.
    provisioned := true
  -- the routine's unchanged remainder produces the project state.
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
-- impl-end

-- proof-start
theorem correct_provisionRecordsTable :
    ∀ (plannedOps : Option (List PlannedOp)) (tableExists : Bool),
      problem_spec_provisionRecordsTable plannedOps tableExists
        (implementation_provisionRecordsTable plannedOps tableExists) := by
  intro plannedOps tableExists
  unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
  by_cases h : plannedOps = some []
  · subst h
    cases tableExists <;> rfl
  · simp only [Id.run, h, if_false]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_provisionRecordsTable is a TOTAL, DETERMINISTIC equality pinning the full Outcome record (both observables provisionedTable + state) in every one of the three branches (some[]+present, some[]+absent, else). Any impl whose correct_* closes must equal gold pointwise over the whole domain plannedOps x tableExists, hence its refined patch necessarily resolves. verify => correct.

**SAME-SPEC:** all 6 attacks return same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec + get_backend('lean').

**POSITIVE CONTROL:** positive_control.lean (exact gold) -> lean_verify.sh exit 0; #print axioms correct_provisionRecordsTable -> [propext] only (no sorryAx/`_prop`). Clean.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>; run concurrently in 2 batches of <=4):
- atk_1 (prepatch bug: always provision, never short-circuit) EXIT=1, rfl failed on some[] branch. PREPATCH REPRODUCED (matches Solution_prepatch.lean behavior).
- atk_2 (boundary: short-circuit state projectState true instead of false) EXIT=1, rfl failed on some[]+absent.
- atk_3 (control-flow-effect: provision in some[]+present case) EXIT=1, rfl failed on some[]+present.
- atk_4 (short-circuit regardless of table presence) EXIT=1, rfl failed on some[]+present (needs continuationResult, got projectState false).
- atk_5 (ungrounded-oracle echo: else branch returns continuationResult none, dropping batch identity) EXIT=1, rfl failed — the continuationResult carrier faithfully carries plannedOps and cannot be faked.
- atk_6 (partial-domain: plan=none wrongly treated as no-provision) EXIT=1, rfl failed on none path (needs provisionedTable=true).

All six failures are genuine proof failures where the impl's computed Outcome literally differs from the spec-prescribed record (false equality of concrete DecidableEq records), unclosable by any tactic — NOT syntax/import artifacts.

NO CLOSING WRONG IMPL => no faithful patch to materialize => no resolve run needed/possible. This is the correct SOUND path: >=5 (6) distinct attacks run and reported, none breaks the spec.

**REFINEMENT.MD A-LEG AUDIT:** axioms-start/axioms-end region is comment-only (empty; byte-identical across all attacks). refinement.md legs 1-7 are all R or I (legs 3 & 6 are 'I deep model of changed branch'); ZERO A-consumed / A-reference / kind-3 legs. Therefore no A-leg correspondence can be broken. Model<->patch correspondence rests on the State/Outcome structural carriers, which the spec fully pins (atk_5 proves the continuationResult plannedOps carrier cannot be independently faked). refinement.md soundness claims (both observables pinned in every case, no ungrounded oracle, prepatch violates on some[] discriminator) all verified consistent with the machine-checked results.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All six same-spec wrong impls fail to close their correct_* proof (genuine rfl failures on concrete decidable-record equalities), so no impl with a closing clean-axiom proof exists whose faithful patch could be materialized/resolved.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Provisioning the bookkeeping table that records applied migration work.

Before a batch of migration operations runs, the system may need to provision a
small bookkeeping table whose rows record which migrations have already been
applied. Provisioning that table is only appropriate when there is migration
work to record.

The batch of work to perform is described by `plannedOps`:

  * `none` — the caller asks the routine to compute the batch itself;
  * `some []` — the caller explicitly states there is nothing to do;
  * `some (_ :: _)` — the caller supplies a non-empty batch of work.

`tableExists` says whether the bookkeeping table is already present.

The desired behavior:

  * When the caller explicitly supplies an empty batch (`some []`), the
    bookkeeping table must NOT be provisioned. If, in addition, the table is
    absent, the routine short-circuits and returns a project state that includes
    no already-applied migrations.
  * Otherwise (there is work to record, or the batch is left for the routine to
    compute) the bookkeeping table is provisioned and the routine proceeds
    through its unchanged remainder, yielding that remainder's project state.

The two observable components are whether provisioning was performed and which
project state is returned.
-/

-- axioms-start
-- No UNCHANGED outside callee needs an `opaque` signature here. The two inputs
-- the routine branches on (the planned batch and whether the bookkeeping table
-- is present) enter as plain data, and the only operation performed — the
-- guarded decision about whether to provision the table and whether to
-- short-circuit — is modeled directly (below). The construction of the returned
-- project states (the short-circuit state, and the state produced by the
-- unchanged remainder) is represented by structural carriers in the `pure`
-- region rather than abstracted behind a consumed axiom. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A single planned migration operation, reduced to an opaque identity (only
the shape of the batch — empty / non-empty / absent — is ever observed). -/
abbrev PlannedOp := Nat

/-- The project state the routine yields. Two distinguishable shapes are
relevant:

* `projectState includesApplied` — a freshly built project state, carrying the
  already-applied migrations iff `includesApplied` is `true`. The short-circuit
  path returns `projectState false` (a state with no applied migrations).
* `continuationResult plannedOps` — the project state produced by the routine's
  unchanged remainder for the given batch. It is left as an opaque structural
  carrier because that remainder is not touched by the behavior under
  specification. -/
inductive State where
  | projectState (includesApplied : Bool) : State
  | continuationResult (plannedOps : Option (List PlannedOp)) : State
deriving DecidableEq

/-- The two observable components of the routine's outcome:

* `provisionedTable` — whether the bookkeeping-table provisioning step was
  performed;
* `state` — the project state returned. -/
structure Outcome where
  provisionedTable : Bool
  state : State
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The outcome is pinned, in both components, to the inputs:

* an explicitly empty batch with the table absent ⇒ no provisioning and the
  short-circuit no-applied state;
* an explicitly empty batch with the table present ⇒ no provisioning, then the
  unchanged remainder's state for the empty batch;
* any other batch (absent, or non-empty) ⇒ provisioning is performed, then the
  unchanged remainder's state for that batch. -/
def problem_spec_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool)
    (result : Outcome) : Prop :=
  if plannedOps = some [] then
    if tableExists then
      result = { provisionedTable := false, state := State.continuationResult (some []) }
    else
      result = { provisionedTable := false, state := State.projectState false }
  else
    result = { provisionedTable := true, state := State.continuationResult plannedOps }
-- post-conditions-end

-- impl-start
def implementation_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
  -- The bookkeeping table must be present to record applied migrations, but it
  -- must not be provisioned when there is nothing to record.
  let mut provisioned := false
  if plannedOps = some [] then
    if !tableExists then
      -- nothing to record and no table: short-circuit with a no-applied state.
      return { provisionedTable := false, state := State.projectState false }
    -- table already present: leave it untouched and proceed.
  else
    -- there is work to record (or the batch is computed): provision the table.
    provisioned := true
  -- the routine's unchanged remainder produces the project state.
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
-- impl-end

-- proof-start
theorem correct_provisionRecordsTable :
    ∀ (plannedOps : Option (List PlannedOp)) (tableExists : Bool),
      problem_spec_provisionRecordsTable plannedOps tableExists
        (implementation_provisionRecordsTable plannedOps tableExists) := by
  intro plannedOps tableExists
  unfold problem_spec_provisionRecordsTable implementation_provisionRecordsTable
  by_cases h : plannedOps = some []
  · subst h
    cases tableExists <;> rfl
  · simp only [Id.run, h, if_false]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_provisionRecordsTable is a TOTAL, DETERMINISTIC equality pinning the full Outcome record (both observables provisionedTable + state) in every one of the three branches (some[]+present, some[]+absent, else). Any impl whose correct_* closes must equal gold pointwise over the whole domain plannedOps x tableExists, hence its refined patch necessarily resolves. verify => correct.

**SAME-SPEC:** all 6 attacks return same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec + get_backend('lean').

**POSITIVE CONTROL:** positive_control.lean (exact gold) -> lean_verify.sh exit 0; #print axioms correct_provisionRecordsTable -> [propext] only (no sorryAx/`_prop`). Clean.

### ATTACKS (cmd: bash scripts/lean_verify.sh <f>; run concurrently in 2 batches of <=4):
- atk_1 (prepatch bug: always provision, never short-circuit) EXIT=1, rfl failed on some[] branch. PREPATCH REPRODUCED (matches Solution_prepatch.lean behavior).
- atk_2 (boundary: short-circuit state projectState true instead of false) EXIT=1, rfl failed on some[]+absent.
- atk_3 (control-flow-effect: provision in some[]+present case) EXIT=1, rfl failed on some[]+present.
- atk_4 (short-circuit regardless of table presence) EXIT=1, rfl failed on some[]+present (needs continuationResult, got projectState false).
- atk_5 (ungrounded-oracle echo: else branch returns continuationResult none, dropping batch identity) EXIT=1, rfl failed — the continuationResult carrier faithfully carries plannedOps and cannot be faked.
- atk_6 (partial-domain: plan=none wrongly treated as no-provision) EXIT=1, rfl failed on none path (needs provisionedTable=true).

All six failures are genuine proof failures where the impl's computed Outcome literally differs from the spec-prescribed record (false equality of concrete DecidableEq records), unclosable by any tactic — NOT syntax/import artifacts.

NO CLOSING WRONG IMPL => no faithful patch to materialize => no resolve run needed/possible. This is the correct SOUND path: >=5 (6) distinct attacks run and reported, none breaks the spec.

**REFINEMENT.MD A-LEG AUDIT:** axioms-start/axioms-end region is comment-only (empty; byte-identical across all attacks). refinement.md legs 1-7 are all R or I (legs 3 & 6 are 'I deep model of changed branch'); ZERO A-consumed / A-reference / kind-3 legs. Therefore no A-leg correspondence can be broken. Model<->patch correspondence rests on the State/Outcome structural carriers, which the spec fully pins (atk_5 proves the continuationResult plannedOps carrier cannot be independently faked). refinement.md soundness claims (both observables pinned in every case, no ungrounded oracle, prepatch violates on some[] discriminator) all verified consistent with the machine-checked results.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacked the spec `problem_spec_provisionRecordsTable` for drift/over-strength against the real post-patch `MigrationExecutor.migrate` head (executor.py:98-100 @ 361bb8f, verified against gold patch in test.jsonl and the worktree). Setup checks: lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry); `#print axioms correct_provisionRecordsTable` -> [propext] only (no sorryAx/`_prop`, genuine proof); same_spec(Solution, Solution_prepatch, lean backend) -> True (spec region frozen/byte-identical); conformance_check.py -> checked=120009 disagreements=0.

Clause-by-clause vs the real callee over the FULL domain plannedOps ∈ {none, some [], some (_::_)} × tableExists ∈ {T,F}:
- plan==[] & no has_table(): real returns `_create_project_state`(False) WITHOUT ensure_schema -> spec {provisioned=false, projectState false}. MATCH.
- plan==[] & has_table(): real falls through, ensure_schema NOT called, unchanged remainder builds state -> spec {provisioned=false, continuationResult (some [])}. MATCH.
- plan is None or non-empty (else): ensure_schema() called, remainder runs -> spec {provisioned=true, continuationResult plannedOps}. MATCH.

The two modeled observables (whether ensure_schema/provisioning ran; which state-shape is returned) are exactly what the FAIL_TO_PASS tests observe (assertNumQueries(0)/assert_not_called). The Python `None == []` is False vs `[] == []` is True distinction is faithfully mirrored by Lean `none ≠ some []` / `some [] = some []` — the model does NOT collapse None into the empty-plan branch. The spec does NOT over-claim: the remainder (:102-134) and callee internals (ensure_schema CREATE TABLE, has_table, `_create_project_state` internals) are abstracted by the opaque `continuationResult`/`projectState` carriers that merely echo the input plannedOps, so nothing about the real return value beyond the patched decision is pinned. No input where the modeled function disagrees with the real callee was found. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes with zero failures; my semantic review confirms it. Gold edit is a control-flow guard in executor.py:98-100 (`if plan == []: if not self.recorder.has_table(): return self._create_project_state(with_applied_migrations=False) else: self.recorder.ensure_schema()`). Spec view (docstring + pure region + post-conditions; impl/proof elided) leaks NONE of it beyond the public problem_statement: (1) no diff markers, no verbatim gold-patch line, no patched file/module path (executor.py/recorder.py absent); (2) NO patched Django symbol echoed — `ensure_schema`, `has_table`, `_create_project_state`, `recorder`, `plan`, `MigrationExecutor` appear nowhere in the spec view; the only patch-touched distinctive symbol reachable, `migrate`, is already public in the problem statement; (3) all identifiers are domain-abstracted generics (plannedOps, tableExists, provisionedTable, State, Outcome, projectState, continuationResult); (4) no bug/fix/regression narration. The problem_statement frames the issue via db_router/allow_migrate rules (the symptom); the spec view instead abstracts to the empty-plan/has_table provisioning discriminator — the postcondition encodes the required behavior (necessary and legitimate for a verified spec) without naming the repo file, callees, or the patch's textual form, so it does not reconstruct the gold edit. Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (True). G-LEAK recorded pass in meta.json with empty failures; spec_provenance='cold'; not a relaxed bundle.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
