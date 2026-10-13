import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation under spec works entirely on the
--  observable label state of the container it is handed; nothing it calls in
--  this branch is left unmodeled. The behaviour — including the size-mismatch
--  failure an ill-fitting replacement label set provokes — is spelled out
--  directly in the `pure`/`impl` regions, so there is no outside contract to
--  assume and nothing for G-AX to check. See refinement.md / mapping.md §3.)
-- axioms-end

-- pure-start
/- A label identity, modeled abstractly: the behaviour observes only equality
   and ordering of labels, never their concrete spelling, so an opaque carrier
   suffices (mapping.md §2). -/
abbrev Lbl := Nat

/- The observable state of a tabular container, restricted to the two label
   axes a wrapping request can touch:

   * `colLabels` — the labels along the column axis;
   * `rowLabels` — the labels along the row axis.

   The cell contents are never altered by a wrapping request and so are not part
   of this carrier (mapping.md §2). -/
structure Frame where
  colLabels : List Lbl
  rowLabels : List Lbl
  deriving DecidableEq, Inhabited

/- The failure a wrapping request reports when the replacement label set offered
   for the column axis cannot be applied because it does not hold exactly one
   label per existing column. The request then leaves the container untouched
   and hands nothing back — the failure escapes to the caller (mapping.md §2). -/
inductive WrapErr where
  | sizeMismatch
  deriving DecidableEq

/- Whether an offered replacement label set fits the axis it targets: it must
   hold exactly as many labels as the axis currently carries. An absent offer
   always fits (the axis is simply left as it stands). -/
def sizeFits (supplied : Option (List Lbl)) (current : List Lbl) : Bool :=
  match supplied with
  | none => true
  | some ls => ls.length == current.length

/- The column labels a wrapping request settles on for a container that already
   carries its own: when a replacement set is supplied it is taken, otherwise the
   container keeps the labels it already has. -/
def resolvedCols (supplied : Option (List Lbl)) (current : List Lbl) : List Lbl :=
  supplied.getD current

/- The container state after the request: when the offered column-label set fits
   (or none is offered) the column axis is settled per `resolvedCols` and the row
   axis is kept; when the offer does not fit, the assignment fails before
   touching anything, so the container is left exactly as it was. -/
def frameAfter (frame : Frame) (colSupplied : Option (List Lbl)) : Frame :=
  if sizeFits colSupplied frame.colLabels then
    { frame with colLabels := resolvedCols colSupplied frame.colLabels }
  else
    frame

/- The overall outcome of the request on a container that already carries its
   own labels: the adjusted container when the offered column-label set fits (or
   none is offered), and the size-mismatch failure otherwise. -/
def wrapResult (frame : Frame) (colSupplied : Option (List Lbl)) :
    Except WrapErr Frame :=
  if sizeFits colSupplied frame.colLabels then
    Except.ok (frameAfter frame colSupplied)
  else
    Except.error WrapErr.sizeMismatch
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap a value that is ALREADY a labelled tabular container.

   The request carries two optional label sets: one for the column axis
   (`colSupplied`) and one for the row axis (`rowSupplied`). The required
   behaviour for an input that already carries its own labels:

   * when a column-label set is provided it must hold exactly one label per
     existing column; a set that fits replaces the column labels, while an
     ill-fitting set makes the request FAIL with a size-mismatch error, leaving
     the container untouched;
   * when no column-label set is provided the column axis is left as it stands;
   * the row axis is left exactly as the container already had it — a row-label
     set offered by the caller does NOT apply to a container that already owns
     one, so `rowSupplied` has no effect here (whatever its size);
   * on success the same container is handed back (the request adjusts it in
     place); on failure nothing is handed back and the failure escapes.

   `colSupplied` and `rowSupplied` are read-only (neither `mut`): the request
   reads them and adjusts the container, mutating nothing it is handed besides
   the container itself. The container's row axis is conceptually unchanged, so
   it is pinned explicitly to its prior value (directive 5). -/
method wrapContainer (mut frame : Frame) (colSupplied : Option (List Lbl)) (rowSupplied : Option (List Lbl)) return (out : Except WrapErr Frame)
  ensures frame = frameAfter frameOld colSupplied
  ensures frame.rowLabels = frameOld.rowLabels
  ensures out = wrapResult frameOld colSupplied
  do
    -- impl-start
    if sizeFits colSupplied frame.colLabels then
      frame := { frame with colLabels := resolvedCols colSupplied frame.colLabels }
      return Except.ok frame
    else
      return Except.error WrapErr.sizeMismatch
    -- impl-end

prove_correct wrapContainer by
  loom_solve <;> simp_all [wrapResult, frameAfter, sizeFits, resolvedCols]
