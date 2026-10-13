import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads one observation of the incoming
--  query carrier — whether it requests a non-empty column projection — and
--  writes two fields of the container. Both the observation and the writes are
--  modeled directly; no unchanged callee's contract is consumed and no foreign
--  callee is deep-modeled, so there is nothing to axiomatize. See refinement.md
--  §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- A query carrier, abstracted to the single observation that decides how its
   result rows must be shaped: the list of value columns it explicitly projects.
   An empty list means the carrier projects no explicit columns; a non-empty
   list means the carrier was built to select a specific set of named columns. -/
structure Query where
  projection : List String
deriving DecidableEq, Inhabited, Repr

/- The row shaper a container uses to turn raw result rows into the values it
   yields. The two outcomes that matter here:
   * `entity` — yields a fully-reconstructed domain object per row;
   * `namedValues` — yields a row of plain named values (one entry per selected
     column) per row.
   The remaining constructors stand for other configured shapers a container may
   already carry; they exist so that "the existing shaper is preserved" is a
   claim over an arbitrary prior shaper, not just the default one. -/
inductive Shaper where
  | entity
  | namedValues
  | namedValuesTuple
  | namedValuesFlat
  | namedValuesRecord
deriving DecidableEq, Inhabited, Repr

/- Whether the incoming carrier requests an explicit column projection: true iff
   its projected-column list is non-empty. This is the sole property of the
   carrier the shaping decision consults. -/
def projectsColumns (q : Query) : Bool := !q.projection.isEmpty

/- The shaper a container must hold after a carrier is assigned to it, given the
   shaper it held before. When the incoming carrier projects an explicit set of
   columns, the rows it produces are no longer full domain objects, so the shaper
   MUST become the named-values shaper regardless of what it was. When the carrier
   projects no explicit columns, the existing shaper is preserved unchanged. -/
def shaperAfter (incoming : Query) (prior : Shaper) : Shaper :=
  if projectsColumns incoming then Shaper.namedValues else prior
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A container holds a query carrier and a row shaper. Re-seating a freshly
   supplied carrier into the container has two effects.

   First, the supplied carrier always becomes the container's carrier; this is
   unconditional and is the long-standing behavior.

   Second — and this is the behavior the desired outcome demands — the row shaper
   must be reconciled with the carrier being installed: when that carrier requests
   a non-empty explicit column projection, the container must yield rows of plain
   named values, so its shaper becomes the named-values shaper; otherwise the
   shaper the container already held is preserved exactly.

   `storedQuery` and `shaper` are the two fields the operation writes (declared
   `mut`). `storedQuery` is pinned to the supplied carrier. `shaper` is pinned
   exactly per the reconciliation rule above — to the named-values shaper when the
   carrier projects columns, and to its prior value `shaperOld` otherwise
   (directive 5: the preserved frame is stated against the entry value, the
   changed frame to its exact post-state). The supplied carrier `incoming` is
   read-only (not `mut`) and never altered. -/
method assignQuery (mut storedQuery : Query) (mut shaper : Shaper) (incoming : Query)
    return (unit : Unit)
  ensures storedQuery = incoming
  ensures shaper = shaperAfter incoming shaperOld
  do
    -- impl-start
    -- Reconcile the row shaper with the carrier being installed (switch to the
    -- named-values shaper when it projects explicit columns; otherwise keep the
    -- existing shaper), then install the carrier itself.
    shaper := if projectsColumns incoming then Shaper.namedValues else shaper
    storedQuery := incoming
    return ()
    -- impl-end

prove_correct assignQuery by
  loom_solve
  simp_all [shaperAfter]
