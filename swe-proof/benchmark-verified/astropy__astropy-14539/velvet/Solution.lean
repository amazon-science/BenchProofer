import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The distinguished failure that escapes the per-column comparison when the
   comparison route a column is sent down cannot produce a verdict for it. Two
   shapes of column have a route that cannot complete:

     * a column whose elements are themselves sequences of more than one element,
       compared by the GENERIC element-wise route: the per-row element-wise
       comparison yields, per such row, a multi-element verdict whose overall
       truth value is ambiguous, so the route cannot reduce it to a verdict;
     * a column whose elements are NOT order-comparable as numbers (e.g. text
       elements), compared by the ROW-WISE numeric-closeness route: numeric
       closeness is undefined for such elements, so that route cannot run.

   Either way the comparison fails to complete — exactly the spurious-difference
   symptom the public problem statement reports when a column is sent down a
   route unsuited to its element kind. Modeled explicitly so the spec can pin
   precisely WHEN it does and does NOT occur. Provenance + executable soundness
   check: mapping.md §3 / axiom_check.py (G-AX). -/
inductive DiffErr where
  | ambiguous
  deriving DecidableEq
-- axioms-end

-- pure-start
/- One row of the two columns under comparison, reduced to the two observations
   the per-row comparison depends on:

     * `differs`   — whether this row's contents in the two columns are unequal
                     (the per-row verdict the comparison records);
     * `multiElem` — whether this row holds MORE THAN ONE element. A row of more
                     than one element is what makes the generic element-wise route
                     produce an ambiguous verdict for this row (mapping.md §2).

   A column whose rows are variable-length sequences is carried by `List Row`;
   the only per-row observations that matter to the comparison outcome are these
   two flags. -/
structure Row where
  differs : Bool
  multiElem : Bool
  deriving DecidableEq

/- The two intrinsic per-column observations — properties of the column's actual
   element kind, INDEPENDENT of how the column happens to be routed:

     * `varLength`     — whether the column's elements are themselves
                         variable-length sequences (so a row may hold more than
                         one element). A variable-length column compared by the
                         generic element-wise route on a multi-element row cannot
                         reduce that row to a verdict.
     * `numComparable` — whether the column's elements are comparable by numeric
                         closeness. A column whose elements are not numerically
                         comparable (e.g. text elements) cannot be compared by the
                         row-wise numeric-closeness route at all.

   These are what determine whether a chosen route can complete; the format
   descriptor only chooses the route (mapping.md §2). -/
structure Column where
  varLength : Bool
  numComparable : Bool
  deriving DecidableEq

/- The descriptor characters that mark a column as a variable-length-array
   column: a column is classified variable-length iff its format descriptor
   contains one of these two markers. Deep model (an A-reference, mapping.md
   §3.1) of the variable-length classification the comparison performs on a
   column's format; validated == the real format test by axiom_check.py (G-AX).
   The classification must agree with the column's intrinsic kind (`varLength`)
   so every variable-length column — and only those — is sent row-wise. -/
def isVLA (fmt : List Char) : Bool :=
  fmt.contains 'P' || fmt.contains 'Q'

/- Whether ANY row of the column holds more than one element. Front-recursive so
   a single unfold is available per element (the fold pattern, plan §5.4). -/
def anyMulti : List Row → Bool
  | []      => false
  | r :: rs => r.multiElem || anyMulti rs

/- The per-row difference verdict of the column: the per-row `differs` flag of
   every row, in order. Front-recursive (one unfold per row). This is the verdict
   a route produces when it can complete. -/
def rowResult : List Row → List Bool
  | []      => []
  | r :: rs => r.differs :: rowResult rs

/- The outcome the ROW-WISE numeric-closeness route produces on a column, as
   `Except DiffErr (List Bool)`: it completes with the per-row difference verdict
   when the column's elements are numerically comparable, and otherwise cannot
   run (the failure escapes). It does NOT care about element counts: a
   variable-length, multi-element column is compared one row at a time and so
   always completes when its elements are numerically comparable. -/
def rowWiseOutcome (col : Column) (rows : List Row) : Except DiffErr (List Bool) :=
  if col.numComparable then
    Except.ok (rowResult rows)
  else
    Except.error DiffErr.ambiguous

/- The outcome the GENERIC element-wise route produces on a column: it completes
   with the per-row difference verdict UNLESS the column's elements are
   themselves variable-length sequences AND some row holds more than one element,
   in which case the route cannot reduce that row to a verdict and the failure
   escapes. A column that is not intrinsically variable-length is a regular
   fixed-width block whose element-wise comparison always completes, whatever its
   rows' element counts. -/
def genericOutcome (col : Column) (rows : List Row) : Except DiffErr (List Bool) :=
  if col.varLength && anyMulti rows then
    Except.error DiffErr.ambiguous
  else
    Except.ok (rowResult rows)

/- The intended outcome of comparing the two columns. The route is chosen by the
   format descriptor: a column classified variable-length (`isVLA fmt`) is
   compared ROW BY ROW; every other column is compared by the GENERIC
   element-wise route. The outcome is then whatever the chosen route produces on
   this column's actual element kind (`rowWiseOutcome` / `genericOutcome`).

   For the comparison to NEVER let a failure escape, the route must match the
   column's element kind: a variable-length column must be sent row-wise (the
   generic route would fail to reduce its multi-element rows), and a column whose
   elements are not numerically comparable must be sent generic (the row-wise
   numeric route cannot run on it). The classification `isVLA fmt` is correct
   exactly when it agrees with the column's intrinsic variable-length kind, so the
   route is faithful to the element kind and the comparison always completes — the
   behavior the public problem statement demands (identical inputs never register
   a difference). Misclassifying a column sends it down a route its element kind
   does not support and the failure escapes. -/
def diffSpec (fmt : List Char) (col : Column) (rows : List Row) :
    Except DiffErr (List Bool) :=
  if isVLA fmt then
    rowWiseOutcome col rows
  else
    genericOutcome col rows
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compare two table columns and report which rows differ.

   Desired behavior: a column is classified by its format descriptor and the
   comparison is routed accordingly. A column classified as a VARIABLE-LENGTH
   column — its format carries a variable-length marker — is compared ROW BY ROW;
   every other column is compared by the generic element-wise route. The chosen
   route must match the column's actual element kind for the comparison to
   complete: the generic route cannot reduce a variable-length column's
   multi-element rows to a verdict, and the row-wise numeric-closeness route
   cannot run on a column whose elements are not numerically comparable. Routing
   every variable-length column — and only those — row-wise sends each column down
   the route its element kind supports, so the comparison always completes and
   identical inputs never register a difference (the behavior the public problem
   statement requires).

   `fmt`, `col`, and `rows` are read-only (none is `mut`): the comparison computes
   a verdict and mutates no input (directive 5). A column's format is modeled by
   its descriptor characters, its intrinsic kind by whether its elements are
   variable-length and numerically comparable, and each row by whether its
   contents differ between the two columns and whether it holds more than one
   element (mapping.md §2). -/
method diffVLAColumn (fmt : List Char) (col : Column) (rows : List Row)
    return (out : Except DiffErr (List Bool))
  ensures out = diffSpec fmt col rows
  do
    -- impl-start
    -- Classify the column by its format descriptor and route the comparison
    -- accordingly: a column whose format carries a variable-length marker is
    -- compared ROW BY ROW; every other column is compared by the generic
    -- element-wise route. Each route produces the per-row difference verdict when
    -- it can run on this column's element kind, and otherwise lets the failure
    -- escape. With every variable-length column — and only those — routed
    -- row-wise, each column is sent down a route its element kind supports, so
    -- the comparison always completes.
    let result : Except DiffErr (List Bool) :=
      if isVLA fmt then
        rowWiseOutcome col rows
      else
        genericOutcome col rows
    return result
    -- impl-end

prove_correct diffVLAColumn by
  loom_solve
  simp_all [diffSpec]
