import Mathlib
-- imports-end

/-!
Tabular output to a structured-markup format, given a set of per-column display
formats keyed by column name.

The exported behavior: when rendering a collection of columns to their string
cells, each column is displayed using the format requested for it by name when
such a request exists; otherwise the column keeps whatever display format it
already carried. The string for every individual value is produced by the
shared value-to-string rendering primitive, applied with the *effective* format
for that column.
-/

-- axioms-start
/-- An opaque value carried by a table cell (an integer, a real, etc.). -/
opaque CellValue : Type

/-- The shared rendering primitive: turn a single cell value into its display
string under an optional display format. Declared only as a signature (no
consumed property). -/
opaque renderCell : Option String → CellValue → String
-- axioms-end

-- pure-start
/-- A column: a name, the display format it already carries (if any), and its
sequence of cell values. -/
structure Column where
  name : String
  format : Option String
  values : List CellValue

/-- The display format explicitly requested for `name` by the format mapping
(association list keyed by column name), if present. -/
def lookupFormat (formats : List (String × String)) (name : String) : Option String :=
  (formats.find? (fun p => p.1 == name)).map (·.2)

/-- The *effective* display format for a column: the requested format when one
exists for the column's name, otherwise the column's pre-existing format. -/
def effFormat (formats : List (String × String)) (c : Column) : Option String :=
  match lookupFormat formats c.name with
  | some f => some f
  | none   => c.format

/-- Apply the requested format to a column, overriding its display format only
when a format is requested for the column's name. -/
def applyFormat (formats : List (String × String)) (c : Column) : Column :=
  match lookupFormat formats c.name with
  | some f => { c with format := some f }
  | none   => c
-- pure-end

-- post-conditions-start
/-- The rendered cells: one list of strings per column, where each value is
rendered with that column's effective format. Frame: the result is determined
entirely by the input columns and the requested formats — the column order, the
per-column value order, and the value contents are all preserved, and the only
format that may differ from a column's pre-existing one is a by-name request. -/
def problem_spec_formattedCells
    (formats : List (String × String)) (cols : List Column)
    (result : List (List String)) : Prop :=
  result = cols.map (fun c => c.values.map (renderCell (effFormat formats c)))
-- post-conditions-end

-- impl-start
def implementation_formattedCells
    (formats : List (String × String)) (cols : List Column) :
    List (List String) := Id.run do
  -- PRE-PATCH (buggy): render each column with its pre-existing format only,
  -- never consulting the requested format mapping.
  let mut out : Array (List String) := #[]
  for c in cols do
    out := out.push (c.values.map (renderCell c.format))
  return out.toList
-- impl-end

-- proof-start
theorem correct_formattedCells : ∀ (formats : List (String × String)) (cols : List Column),
    problem_spec_formattedCells formats cols
      (implementation_formattedCells formats cols) := by
  intro formats cols
  unfold problem_spec_formattedCells implementation_formattedCells
  simp [effFormat, applyFormat]
  rfl
-- proof-end
