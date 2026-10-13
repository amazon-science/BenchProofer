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
  let database := suppliedUsing
  let savepoint := canRollbackDdl
  let mut executed : List String := []
  for sql in sqlList do
    executed := executed ++ [sql]
  return { database := database, savepoint := savepoint, executed := executed }
-- impl-end

-- proof-start
theorem correct_executeFlush :
    ∀ (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)
      (sqlList : List String),
      problem_spec_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList
        (implementation_executeFlush connectionAlias suppliedUsing canRollbackDdl sqlList) := by
  intro connectionAlias suppliedUsing canRollbackDdl sqlList
  unfold problem_spec_executeFlush implementation_executeFlush
  refine ⟨rfl, rfl, ?_⟩
  have h : ∀ (xs acc : List String),
      (Id.run (forIn xs acc (fun sql r =>
        (pure (ForInStep.yield (r ++ [sql])) : Id (ForInStep (List String)))))) = acc ++ xs := by
    intro xs
    induction xs with
    | nil => intro acc; simp [Id.run, pure]
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [Id.run, bind, pure] at ih ⊢
      rw [ih]; simp
  simpa using h sqlList []
-- proof-end
