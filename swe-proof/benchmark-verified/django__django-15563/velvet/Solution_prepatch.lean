import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two facts an ancestor's update is routed on —
--  "does this ancestor share the child's identity value" (`sharesChildPk`) and
--  "the fetched identity rows" (`rows`) — are taken as FREE INPUTS. The spec
--  makes no behavioural claim about how those facts are produced and holds for
--  EVERY schema/row set, so there is nothing to check against a real callee,
--  hence no G-AX. The routing decision under spec — which fetched column each
--  ancestor's filter values are drawn from — is modeled deeply below; every
--  observable is computed from the inputs, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- An ancestor table that the same statement must also update, abstracted to the
   single fact that decides where its filter values come from: whether it shares
   the child's identity value (`sharesChildPk`). When it does, the child's own
   identity is also the ancestor's, so no extra value need be fetched for it;
   when it does not, a distinct identity value must be fetched alongside the
   child's. -/
structure Parent where
  sharesChildPk : Bool
deriving Inhabited, DecidableEq

/- Advance the column assignment by one ancestor, threading the next free column.
   Column 0 always carries the child's identity. An ancestor that shares that
   identity is assigned column 0 (reuse it); one that does not is assigned the
   next free column, which is then consumed. -/
def stepCol (st : List Nat × Nat) (p : Parent) : List Nat × Nat :=
  let cols := st.1
  let next := st.2
  if p.sharesChildPk then (cols ++ [0], next)
  else (cols ++ [next], next + 1)

/- The column each ancestor's filter values are drawn from, one per ancestor in
   order. Column 0 is the child's identity; distinct-identity ancestors take the
   appended columns in the order they appear. -/
def assignedColumns (ps : List Parent) : List Nat :=
  (ps.foldl stepCol ([], 1)).1

/- The identity values for a single column: the value at that column of every
   fetched row. A row is the tuple of fetched values for one matched child; the
   column index selects which fetched identity is read. -/
def idColumn (rows : List (List Int)) (idx : Nat) : List Int :=
  rows.map (fun row => row[idx]!)

/- Forward-fold step: extending the consumed prefix by one ancestor advances the
   assignment built from the shorter prefix by exactly that ancestor. The single
   goal `loom_solve` leaves for the loop body. -/
lemma cols_take_step (ps : List Parent) (i : Nat) (hi : i < ps.length) :
    (ps.take (i + 1)).foldl stepCol ([], 1)
      = stepCol ((ps.take i).foldl stepCol ([], 1)) ps[i]! := by
  have hcons : ps.take (i + 1) = ps.take i ++ [ps[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- For a statement that updates a child together with the ancestors in
   `parents`, decide, per ancestor (in order), the list of identity values its
   own update must be filtered on. Each value is read from one column of the
   fetched `rows`: an ancestor that shares the child's identity reads the child
   identity column; one that does not reads the distinct identity fetched for it.

   `parents` and `rows` are read-only (not `mut`): the routing threads a fresh
   accumulator and never mutates anything it is handed (directive 5). -/
method parentFilterIds (parents : List Parent) (rows : List (List Int))
    return (out : List (List Int))
  ensures out = (assignedColumns parents).map (idColumn rows)
  do
    -- impl-start
    let mut st : List Nat × Nat := ([], 1)
    let mut i := 0
    while i < parents.length
      invariant i ≤ parents.length
      invariant st = (parents.take i).foldl stepCol ([], 1)
      done_with i = parents.length
      decreasing parents.length - i
    do
      let _p := parents[i]!
      -- Pre-image skeleton: every ancestor's filter values are drawn from the
      -- child identity column (column 0) — there is NO per-ancestor routing,
      -- the single child identity list is reused for all of them. The frozen
      -- spec routes a non-shared-identity ancestor through its own appended
      -- column, so for such an ancestor the two diverge and prove_correct MUST
      -- fail.
      let cols := st.1
      let next := st.2
      st := (cols ++ [0], next)
      i := i + 1
    return st.1.map (idColumn rows)
    -- impl-end

prove_correct parentFilterIds by
  loom_solve
  case «invariant_2: st = (parents.take i).foldl stepCol ([], 1)» =>
    have hi : i < parents.length := by omega
    rw [invariant_2, cols_take_step parents i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [assignedColumns]
