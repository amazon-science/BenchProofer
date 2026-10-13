# P2 adversarial audit — django__django-12741

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,12 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
     (sqlList : List String) : FlushExecution := Id.run do
-  let database := connectionAlias
+  let database := suppliedUsing
   let savepoint := canRollbackDdl
   let mut executed : List String := []
   for sql in sqlList do
@@ -74,20 +75,6 @@
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
@@ -95,8 +82,8 @@
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
   refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  simp [implementation_executeFlush, Id.run]
+  induction sqlList with
+  | nil => rfl
+  | cons a as ih => simp [List.forIn_cons]; sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,33 +61,15 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
-    (sqlList : List String) : FlushExecution := Id.run do
-  let database := connectionAlias
-  let savepoint := canRollbackDdl
-  let mut executed : List String := []
-  for sql in sqlList do
-    executed := executed ++ [sql]
-  return { database := database, savepoint := savepoint, executed := executed }
+    (sqlList : List String) : FlushExecution :=
+  { database := connectionAlias, savepoint := canRollbackDdl, executed := sqlList.reverse }
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
@@ -95,8 +77,5 @@
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
   refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  simp [implementation_executeFlush]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,42 +61,23 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
-    (sqlList : List String) : FlushExecution := Id.run do
-  let database := connectionAlias
-  let savepoint := canRollbackDdl
-  let mut executed : List String := []
-  for sql in sqlList do
-    executed := executed ++ [sql]
-  return { database := database, savepoint := savepoint, executed := executed }
+    (sqlList : List String) : FlushExecution :=
+  { database := (if sqlList.isEmpty then connectionAlias else suppliedUsing),
+    savepoint := canRollbackDdl, executed := sqlList }
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
       problem_spec_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
-  refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  refine ⟨?_, rfl, rfl⟩
+  simp [implementation_executeFlush]
+  sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,33 +61,15 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
-    (sqlList : List String) : FlushExecution := Id.run do
-  let database := connectionAlias
-  let savepoint := canRollbackDdl
-  let mut executed : List String := []
-  for sql in sqlList do
-    executed := executed ++ [sql]
-  return { database := database, savepoint := savepoint, executed := executed }
+    (sqlList : List String) : FlushExecution :=
+  { database := connectionAlias, savepoint := canRollbackDdl, executed := sqlList.eraseDups }
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
@@ -95,8 +77,6 @@
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
   refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  simp [implementation_executeFlush]
+  sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -61,42 +61,20 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
-    (sqlList : List String) : FlushExecution := Id.run do
-  let database := connectionAlias
-  let savepoint := canRollbackDdl
-  let mut executed : List String := []
-  for sql in sqlList do
-    executed := executed ++ [sql]
-  return { database := database, savepoint := savepoint, executed := executed }
+    (sqlList : List String) : FlushExecution :=
+  { database := connectionAlias, savepoint := canRollbackDdl, executed := sqlList }
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
       problem_spec_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
-  refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,42 +61,22 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
-    (sqlList : List String) : FlushExecution := Id.run do
-  let database := connectionAlias
-  let savepoint := canRollbackDdl
-  let mut executed : List String := []
-  for sql in sqlList do
-    executed := executed ++ [sql]
-  return { database := database, savepoint := savepoint, executed := executed }
+    (sqlList : List String) : FlushExecution :=
+  { database := connectionAlias, savepoint := !canRollbackDdl, executed := sqlList }
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
       problem_spec_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
-  refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  refine ⟨rfl, ?_, rfl⟩
+  simp [implementation_executeFlush]
+  sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,6 +61,7 @@
   result.executed = sqlList
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_executeFlush
     (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
@@ -69,25 +70,11 @@
   let savepoint := canRollbackDdl
   let mut executed : List String := []
   for sql in sqlList do
-    executed := executed ++ [sql]
+    executed := executed ++ [sql, sql]
   return { database := database, savepoint := savepoint, executed := executed }
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
-statement in order equals `init ++ xs`, generalized over the accumulator. -/
-theorem executeFlush_forIn (xs : List String) (init : List String) :
-    Id.run (forIn xs init
-      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
-      = init ++ xs := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_executeFlush :
     ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
       (sqlList : List String),
@@ -95,8 +82,6 @@
         (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
   intro connectionAlias suppliedUsing canRollbackDdl sqlList
   refine ⟨rfl, rfl, ?_⟩
-  show (Id.run (forIn sqlList []
-    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
-  rw [executeFlush_forIn]
-  simp
+  simp [implementation_executeFlush, Id.run]
+  sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Running a sequence of data-clearing SQL statements inside a single transaction.

A database connection exposes its own identity (the alias naming which database
it talks to) and a feature flag describing whether structural (DDL) changes on
that backend can be rolled back. To clear the database, a routine opens one
transaction and runs a given list of SQL statements through it, in order.

The transaction must be bound to the database the connection itself talks to —
its own alias — and never to any other database identifier that happens to be
available at the call site. The transaction's savepoint behaviour follows the
backend's rollback capability, and every supplied statement is executed exactly
once, preserving their given order.

The observable outcome is therefore fully determined by the connection's own
alias, its rollback-capability flag, and the list of statements:

  * `database`   — the database the transaction is bound to;
  * `savepoint`  — whether the transaction is opened with a savepoint;
  * `executed`   — the statements run through the transaction, in order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Opening the
-- transaction and running each statement through a cursor are side-effecting
-- operations whose only observable content (which database is bound, which
-- savepoint flag is used, which statements run in which order) is a pure
-- function of the inputs. The statement run is modeled directly as an
-- order-preserving accumulation; hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The observable outcome of running the flush statements: the database the
transaction is bound to, the savepoint flag it is opened with, and the
statements executed through it (in order). -/
structure FlushExecution where
  database : String
  savepoint : Bool
  executed : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The flush outcome is fully pinned to the inputs:

  * the transaction is bound to the connection's own alias — never to the
    separately-available identifier `suppliedUsing`;
  * the savepoint flag equals the backend's rollback-capability flag;
  * the executed statements are exactly the supplied list, in the same order.

All three components are determined, so no part of the result is left free. -/
def problem_spec_executeFlush
    (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
    (sqlList : List String) (result : FlushExecution) : Prop :=
  result.database = connectionAlias ∧
  result.savepoint = canRollbackDdl ∧
  result.executed = sqlList
-- post-conditions-end

-- impl-start
def implementation_executeFlush
    (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
    (sqlList : List String) : FlushExecution := Id.run do
  let database := connectionAlias
  let savepoint := canRollbackDdl
  let mut executed : List String := []
  for sql in sqlList do
    executed := executed ++ [sql]
  return { database := database, savepoint := savepoint, executed := executed }
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
statement in order equals `init ++ xs`, generalized over the accumulator. -/
theorem executeFlush_forIn (xs : List String) (init : List String) :
    Id.run (forIn xs init
      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
      = init ++ xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp

theorem correct_executeFlush :
    ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
      (sqlList : List String),
      problem_spec_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList
        (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
  intro connectionAlias suppliedUsing canRollbackDdl sqlList
  refine ⟨rfl, rfl, ?_⟩
  show (Id.run (forIn sqlList []
    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
  rw [executeFlush_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL functional specification: problem_spec pins all three outputs (result.database=connectionAlias, result.savepoint=canRollbackDdl, result.executed=sqlList) each to an exact function of the inputs, leaving zero refinement slack. verify cmd: `bash scripts/lean_verify.sh <file>`; same_spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (lean backend).

### ATTACK MATRIX (all same_spec=True):
- atk_1 prepatch bug (database:=suppliedUsing): rc=1 error — And.intro rfl type mismatch on result.database=connectionAlias. Reproduces the real prepatch bug (G-DIFF). Does NOT close.
- atk_2 boundary (executed:=sqlList.reverse): rc=1 error — unsolved goal `sqlList.reverse = sqlList` (false). Does NOT close.
- atk_3 partial-domain (if sqlList.isEmpty then connectionAlias else suppliedUsing): rc=3 sorry — residual goal false when non-empty. Does NOT close.
- atk_4 control-flow-effect dedup (executed:=sqlList.eraseDups): rc=3 sorry — `eraseDups=id` false. Does NOT close.
- atk_5 ungrounded-oracle ECHO (direct record {connectionAlias, canRollbackDdl, sqlList}): rc=0 VERIFIES; `#print axioms correct_executeFlush` => 'does not depend on any axioms' (clean, no sorryAx). This is observationally IDENTICAL to gold.
- atk_6 savepoint negated (!canRollbackDdl): rc=3 sorry — `!b=b` false. Does NOT close.
- atk_7 control-flow doubled append (executed each stmt twice): rc=3 sorry — doubled list != sqlList. Does NOT close.

Positive control (gold Solution.lean): rc=0 verifies.

MANDATORY RESOLVE STEP: only atk_5 closes with clean axioms. Its faithful refined patch is the gold behavior (bind transaction.atomic to self.connection.alias, savepoint=can_rollback_ddl, run each stmt once in order) — because the closing impl produces the exact gold observable triple. Materialized as atk_5.patch (== gold patch.diff verbatim) and RAN through the official harness: swebench_unified.harness.run_resolve('django__django-12741', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved'.

REFINEMENT AUDIT: refinement.md legs are all R (op1 alias binding: self.connection.alias<->connectionAlias; op2 savepoint copy: can_rollback_ddl<->canRollbackDdl) or I (op3 empty accumulator, op4 order-preserving statement run modeling cursor.execute stream, op5 record return). NO A-consumed and NO A-reference legs (axioms=[], deep_model_references=[]), consistent with the R/I-only impl validated by G-CONF differential testing — so there is no callee-axiom correspondence to break. No kind-3 legs. The suppliedUsing input faithfully models the dropped `using` parameter as an input the post-patch result no longer depends on (frame: result.database != suppliedUsing in general); this is precisely the gold discriminator.

VERDICT: SOUND. 7 distinct wrong impls attacked (prepatch bug + partial-domain + boundary + 2 control-flow-effect + savepoint + ungrounded-oracle echo); the six wrong impls that diverge from the gold triple all FAIL to close (rc 1 or 3), and the only impl that closes (the echo) is observationally identical to gold and its materialized faithful patch RESOLVES under the official harness. No closing-clean-axiom impl has a non-resolving faithful patch.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Running a sequence of data-clearing SQL statements inside a single transaction.

A database connection exposes its own identity (the alias naming which database
it talks to) and a feature flag describing whether structural (DDL) changes on
that backend can be rolled back. To clear the database, a routine opens one
transaction and runs a given list of SQL statements through it, in order.

The transaction must be bound to the database the connection itself talks to —
its own alias — and never to any other database identifier that happens to be
available at the call site. The transaction's savepoint behaviour follows the
backend's rollback capability, and every supplied statement is executed exactly
once, preserving their given order.

The observable outcome is therefore fully determined by the connection's own
alias, its rollback-capability flag, and the list of statements:

  * `database`   — the database the transaction is bound to;
  * `savepoint`  — whether the transaction is opened with a savepoint;
  * `executed`   — the statements run through the transaction, in order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Opening the
-- transaction and running each statement through a cursor are side-effecting
-- operations whose only observable content (which database is bound, which
-- savepoint flag is used, which statements run in which order) is a pure
-- function of the inputs. The statement run is modeled directly as an
-- order-preserving accumulation; hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The observable outcome of running the flush statements: the database the
transaction is bound to, the savepoint flag it is opened with, and the
statements executed through it (in order). -/
structure FlushExecution where
  database : String
  savepoint : Bool
  executed : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The flush outcome is fully pinned to the inputs:

  * the transaction is bound to the connection's own alias — never to the
    separately-available identifier `suppliedUsing`;
  * the savepoint flag equals the backend's rollback-capability flag;
  * the executed statements are exactly the supplied list, in the same order.

All three components are determined, so no part of the result is left free. -/
def problem_spec_executeFlush
    (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
    (sqlList : List String) (result : FlushExecution) : Prop :=
  result.database = connectionAlias ∧
  result.savepoint = canRollbackDdl ∧
  result.executed = sqlList
-- post-conditions-end

-- impl-start
def implementation_executeFlush
    (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
    (sqlList : List String) : FlushExecution := Id.run do
  let database := connectionAlias
  let savepoint := canRollbackDdl
  let mut executed : List String := []
  for sql in sqlList do
    executed := executed ++ [sql]
  return { database := database, savepoint := savepoint, executed := executed }
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` accumulation that appends each
statement in order equals `init ++ xs`, generalized over the accumulator. -/
theorem executeFlush_forIn (xs : List String) (init : List String) :
    Id.run (forIn xs init
      (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))
      = init ++ xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.append_nil, Id.run, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp

theorem correct_executeFlush :
    ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
      (sqlList : List String),
      problem_spec_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList
        (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
  intro connectionAlias suppliedUsing canRollbackDdl sqlList
  refine ⟨rfl, rfl, ?_⟩
  show (Id.run (forIn sqlList []
    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList
  rw [executeFlush_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL functional specification: problem_spec pins all three outputs (result.database=connectionAlias, result.savepoint=canRollbackDdl, result.executed=sqlList) each to an exact function of the inputs, leaving zero refinement slack. verify cmd: `bash scripts/lean_verify.sh <file>`; same_spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (lean backend).

### ATTACK MATRIX (all same_spec=True):
- atk_1 prepatch bug (database:=suppliedUsing): rc=1 error — And.intro rfl type mismatch on result.database=connectionAlias. Reproduces the real prepatch bug (G-DIFF). Does NOT close.
- atk_2 boundary (executed:=sqlList.reverse): rc=1 error — unsolved goal `sqlList.reverse = sqlList` (false). Does NOT close.
- atk_3 partial-domain (if sqlList.isEmpty then connectionAlias else suppliedUsing): rc=3 sorry — residual goal false when non-empty. Does NOT close.
- atk_4 control-flow-effect dedup (executed:=sqlList.eraseDups): rc=3 sorry — `eraseDups=id` false. Does NOT close.
- atk_5 ungrounded-oracle ECHO (direct record {connectionAlias, canRollbackDdl, sqlList}): rc=0 VERIFIES; `#print axioms correct_executeFlush` => 'does not depend on any axioms' (clean, no sorryAx). This is observationally IDENTICAL to gold.
- atk_6 savepoint negated (!canRollbackDdl): rc=3 sorry — `!b=b` false. Does NOT close.
- atk_7 control-flow doubled append (executed each stmt twice): rc=3 sorry — doubled list != sqlList. Does NOT close.

Positive control (gold Solution.lean): rc=0 verifies.

MANDATORY RESOLVE STEP: only atk_5 closes with clean axioms. Its faithful refined patch is the gold behavior (bind transaction.atomic to self.connection.alias, savepoint=can_rollback_ddl, run each stmt once in order) — because the closing impl produces the exact gold observable triple. Materialized as atk_5.patch (== gold patch.diff verbatim) and RAN through the official harness: swebench_unified.harness.run_resolve('django__django-12741', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved'.

REFINEMENT AUDIT: refinement.md legs are all R (op1 alias binding: self.connection.alias<->connectionAlias; op2 savepoint copy: can_rollback_ddl<->canRollbackDdl) or I (op3 empty accumulator, op4 order-preserving statement run modeling cursor.execute stream, op5 record return). NO A-consumed and NO A-reference legs (axioms=[], deep_model_references=[]), consistent with the R/I-only impl validated by G-CONF differential testing — so there is no callee-axiom correspondence to break. No kind-3 legs. The suppliedUsing input faithfully models the dropped `using` parameter as an input the post-patch result no longer depends on (frame: result.database != suppliedUsing in general); this is precisely the gold discriminator.

VERDICT: SOUND. 7 distinct wrong impls attacked (prepatch bug + partial-domain + boundary + 2 control-flow-effect + savepoint + ungrounded-oracle echo); the six wrong impls that diverge from the gold triple all FAIL to close (rc 1 or 3), and the only impl that closes (the echo) is observationally identical to gold and its materialized faithful patch RESOLVES under the official harness. No closing-clean-axiom impl has a non-resolving faithful patch.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real post-patch callee. Real post-patch execute_sql_flush(self, sql_list): binds transaction.atomic(using=self.connection.alias), savepoint=self.connection.features.can_rollback_ddl, runs each sql in sql_list once in order via cursor.execute. Spec problem_spec_executeFlush pins result to exactly (database=connectionAlias, savepoint=canRollbackDdl, executed=sqlList). Mapping is faithful: connectionAlias<->self.connection.alias, canRollbackDdl<->can_rollback_ddl feature flag, sqlList<->sql_list; suppliedUsing models the DROPPED `using` argument and is correctly ignored post-patch (result.database never depends on it), which mirrors the refactor exactly. Order-preserving append accumulation reproduces cursor.execute stream (duplicates kept, empty->empty). Verified: (1) same_spec(post,prepatch)=True with LeanBackend tables and spec_view hash matches meta.json; all region hashes match except proof (expected — prepatch proof differs). (2) Solution.lean compiles exit 0 (only unused-variable warnings for suppliedUsing, which is the intended frame condition). (3) #print axioms correct_executeFlush => [propext, Quot.sound], NO sorryAx — proof is genuine. (4) conformance_check.py oracle (exact patched binding) vs shadow: 120,010 cases (edge + 120k fuzz, seed 12741) with 0 disagreements, status=pass. Searched divergence space: alias!=suppliedUsing (the F2P discriminating shape), alias==suppliedUsing, empty/single/duplicate statement lists, both savepoint flags — no input where the real callee produces a result the spec forbids or vice versa. The spec is neither too strong nor too weak relative to the real behavior; it is an exact abstraction of the post-patch observable triple. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (backend=lean) => True; only impl/proof differ (post: database:=connectionAlias; pre: database:=suppliedUsing), both elided in the spec view. Public problem_statement already fully discloses the gold edit: it states 'The using argument can be dropped and inferred by the calling instance: self.connection.alias' and shows both old signature execute_sql_flush(self, using, sql_list) and new execute_sql_flush(self, sql_list). The discriminating postcondition result.database = connectionAlias (never suppliedUsing) is exactly what the problem_statement states in plain language, not additional leakage; the savepoint/executed clauses model unchanged (I/R) behavior. Lexical screen: spec view uses only neutral identifiers (executeFlush, connectionAlias, suppliedUsing, FlushExecution) and shares no patched def/class/symbol substring (execute_sql_flush, sql_flush, handle), no file paths, no dotted module paths, no gold-diff lines; comments describe behavior only. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
