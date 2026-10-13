import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The unchanged callees this
   slice relies on — opening a scoped database operation keyed by a connection
   identifier, and replaying a list of statements through that connection — are
   pure framework/side-effecting operations whose only data-carrier inputs are
   the connection's own identifier and the statement list, modeled directly as
   the inputs `connAlias` / `sqlList` of the operation. Their provenance and the
   input bijection are recorded in mapping.md; the end-to-end behaviour is
   differential-tested by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/- A connection-bound batch operation, viewed only through the two facts the
   surrounding behaviour observes: the identifier under which the scoped
   operation is opened, and the statements it replays, in order. The connection
   carries its OWN identifier (`alias`); the result of running the batch is the
   pair of (identifier the scope was opened under, statements replayed). -/
structure Connection where
  ownAlias : List Char
  deriving DecidableEq

/- The intended effect of running the batch on a connection: the scope is opened
   under the connection's own identifier, and the statement list is replayed
   unchanged, in order. The identifier the scope is opened under must be the
   connection's own — it is determined by the connection itself, never by any
   value supplied alongside the statements. -/
def flushSpec (conn : Connection) (sqlList : List (List Char)) :
    (List Char) × (List (List Char)) :=
  (conn.ownAlias, sqlList)

@[grind] lemma flushSpec_fst (conn : Connection) (sqlList : List (List Char)) :
    (flushSpec conn sqlList).1 = conn.ownAlias := rfl
@[grind] lemma flushSpec_snd (conn : Connection) (sqlList : List (List Char)) :
    (flushSpec conn sqlList).2 = sqlList := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `suppliedKey` is an identifier handed to the operation alongside the
   statement list. It is read-only and must NOT determine the identifier the
   scoped operation is opened under: the postcondition pins the opened identifier
   to the connection's own identifier alone, so any implementation that lets
   `suppliedKey` reach the result fails to verify. The statement list is replayed
   unchanged and in order. -/
method runBatch
    (conn : Connection) (suppliedKey : List Char) (sqlList : List (List Char))
    return (out : (List Char) × (List (List Char)))
  ensures out = flushSpec conn sqlList
  ensures out.1 = conn.ownAlias
  ensures out.2 = sqlList
  do
    -- impl-start
    -- Pre-image skeleton: the scope is opened under the identifier SUPPLIED
    -- alongside the statements, rather than the connection's own identifier.
    -- The frozen spec requires the opened identifier to equal conn.ownAlias for
    -- every supplied key, so prove_correct MUST fail.
    let openedUnder : List Char := suppliedKey
    let replayed : List (List Char) := sqlList
    return (openedUnder, replayed)
    -- impl-end

prove_correct runBatch by
  loom_solve
