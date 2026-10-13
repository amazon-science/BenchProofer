import Mathlib
-- imports-end

/-!
Returning the rows produced by a row-creating database write.

When a row is created, the backend can hand back one or more column values for
that row (for example the freshly assigned primary key). Those values arrive as
a list of rows, each row being a tuple of raw cell values, and they may come from
one of several backend pathways depending on the connection's capabilities:

* a backend that can return several rows at once for a multi-row write returns
  them directly;
* a backend that can return columns for a single-row write returns one such row;
* otherwise a single last-inserted-id value is returned as a one-cell row.

Every field being returned may declare a chain of value converters — the same
converters a field uses to turn a stored value back into its Python form when it
is read by an ordinary query (e.g. a `from_db_value` hook that wraps a raw
integer in a wrapper object). The desired behaviour is that the values handed
back by a creating write are post-processed in exactly the same way as values
read by any other query:

  * the number of rows returned is unchanged;
  * each cell of each row is passed through the converter chain declared for the
    field in that column position (an empty chain leaves the cell unchanged);
  * if no returned field declares any converter, the rows are handed back
    untouched;
  * if no fields are being returned, the result is empty.

In particular a field whose converter wraps the raw value must see that wrapping
applied to the value produced by the creating write, just as it would for a value
fetched by a read.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The pathway
-- that produces the raw returned rows (single id, single returned row, or a
-- batch of returned rows) is upstream of and orthogonal to the modeled
-- behaviour; its result enters as grounded input data (the candidate row
-- values and the branch-selecting capability flags). The converter chain each
-- field declares likewise enters as grounded data. The post-processing itself
-- (applying each field's converter chain to the matching cell) is modeled
-- DEEPLY as a fold/map, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A returned field, carrying the ordered chain of value converters it declares.
A cell in this field's column is passed through `converters` left-to-right; an
empty chain means the cell is returned unchanged. Cell values are modeled as
`Int` (raw database scalars; a converter that "wraps" a value is modeled by the
function it applies). -/
structure RetField where
  converters : List (Int → Int)

/-- One returned row: a tuple of raw cell values, one per returned field. -/
abbrev Row := List Int

/-- Apply a field's converter chain to a single cell value, left-to-right.
An empty chain is the identity. -/
def applyChain (cs : List (Int → Int)) (x : Int) : Int :=
  cs.foldl (fun v f => f v) x

/-- Apply each field's converter chain to the matching cell of one row (the
field in column position `i` converts cell `i`). -/
def convertRow (fields : List RetField) (row : Row) : Row :=
  (fields.zip row).map (fun fc => applyChain fc.1.converters fc.2)

/-- Whether any returned field declares a non-empty converter chain. -/
def anyConverter (fields : List RetField) : Bool :=
  fields.any (fun f => !f.converters.isEmpty)
-- pure-end

-- post-conditions-start
/-- The rows returned by a creating write. `returningFields` are the fields whose
values are returned; `canBatch`/`canColumns` are the capability flags selecting
which backend pathway produced the raw rows; `batchRows`, `columnsRow`, and
`lastIdRow` are the candidate raw outputs of those three pathways. The result is
the selected raw rows with every field's converter chain applied (only if some
field declares a converter), or the empty list when no fields are returned. -/
def problem_spec_insertReturnedRows
    (returningFields : List RetField) (canBatch canColumns : Bool)
    (batchRows : List Row) (columnsRow lastIdRow : Row)
    (result : List Row) : Prop :=
  if returningFields.isEmpty then
    result = []
  else
    let selected : List Row :=
      if canBatch then batchRows
      else if canColumns then [columnsRow]
      else [lastIdRow]
    if anyConverter returningFields then
      result = selected.map (convertRow returningFields)
    else
      result = selected
-- post-conditions-end

-- impl-start
def implementation_insertReturnedRows
    (returningFields : List RetField) (canBatch canColumns : Bool)
    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do
  -- Pre-patch bug: each backend pathway returns its raw rows immediately, so the
  -- returned values never pass through the fields' converter chains (e.g. a
  -- field's wrapping hook is skipped on a creating write).
  if returningFields.isEmpty then
    return []
  if canBatch then
    return batchRows
  else if canColumns then
    return [columnsRow]
  else
    return [lastIdRow]
-- impl-end

-- proof-start
theorem correct_insertReturnedRows :
    ∀ (returningFields : List RetField) (canBatch canColumns : Bool)
      (batchRows : List Row) (columnsRow lastIdRow : Row),
      problem_spec_insertReturnedRows returningFields canBatch canColumns
        batchRows columnsRow lastIdRow
        (implementation_insertReturnedRows returningFields canBatch canColumns
          batchRows columnsRow lastIdRow) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
