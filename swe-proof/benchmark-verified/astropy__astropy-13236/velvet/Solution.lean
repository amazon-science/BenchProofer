import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The classification is a pure dispatch over the shape
--  of the value being added plus the host table's masked-ness and is modeled
--  DEEPLY in the `pure` region below; the surrounding helpers that detect that
--  shape and build the wrapper are collapsed into the inputs/result and owed no
--  contract. There is no `axiom` declaration and no A-reference deep model of
--  an outside callee.)
-- axioms-end

-- pure-start
/- The shapes a value can have when it is offered to a table as a new column,
   reduced to the only distinctions the classification reacts to:
     * `alreadyColumn`    — the value is already an ordinary column object;
     * `alreadyMixin`     — the value is already a valid mixin column for this
                            table (a rich column type such as a coordinate or
                            time column);
     * `structuredPlain`  — an unmasked array whose element record carries more
                            than one field (a multi-field "structured" array);
     * `structuredMasked` — a masked array whose element record carries more
                            than one field;
     * `plainMasked`      — a masked array whose element record carries a single
                            field;
     * `plainOther`       — any remaining plain array value.
   The structured/plain and masked/unmasked distinctions are kept apart because
   the classification treats them differently. -/
inductive InputShape where
  | alreadyColumn
  | alreadyMixin
  | structuredPlain
  | structuredMasked
  | plainMasked
  | plainOther
  deriving Inhabited, DecidableEq

/- The column-class kind a value is wrapped in:
     * `columnKind`       — the ordinary column class;
     * `maskedColumnKind` — the masked column class (used when the value carries
                            a mask, so the mask is preserved — or when the host
                            table itself wraps its data as masked);
     * `mixinKind`        — kept as a mixin column. -/
inductive ColumnKind where
  | columnKind
  | maskedColumnKind
  | mixinKind
  deriving Inhabited, DecidableEq

/- The classification, modeled deeply. Besides the value's shape it depends on
   the host table's masked-ness (`tableIsMasked`): a masked table wraps every
   array-like value as a masked column. The desired behaviour:
     * a value that is already a mixin column is kept as a mixin column — this
       is the ONLY way a value ends up a mixin column;
     * a value that carries a mask (a masked array, whether structured or not)
       becomes a masked column so its mask is preserved, whatever the table's
       masked-ness;
     * every other value — one already an ordinary column, a multi-field
       structured array, or any other plain array — is classified purely by the
       table's masked-ness: a masked column in a masked table, an ordinary
       column otherwise. In particular a multi-field structured array is
       classified by the same rule as any other array of its masked-ness — it
       is NOT singled out for the mixin class. -/
def classify : InputShape → Bool → ColumnKind
  | .alreadyColumn,    tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
  | .alreadyMixin,     _             => .mixinKind
  | .structuredPlain,  tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
  | .structuredMasked, _             => .maskedColumnKind
  | .plainMasked,      _             => .maskedColumnKind
  | .plainOther,       tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a value offered to a table as a new column into the column-class
   kind that wraps it. `input` and `tableIsMasked` are read-only (not `mut`);
   the query computes a single kind and mutates nothing (directive 5). -/
method classifyColumn (input : InputShape) (tableIsMasked : Bool) return (out : ColumnKind)
  ensures out = classify input tableIsMasked
  ensures (input = .structuredPlain ∧ tableIsMasked = false) → out = .columnKind
  ensures input = .structuredMasked → out = .maskedColumnKind
  ensures input = .alreadyMixin → out = .mixinKind
  ensures (out = .mixinKind) → (input = .alreadyMixin)
  do
    -- impl-start
    -- Dispatch on the shape of the value and the table's masked-ness. A value
    -- already a mixin column is the only one kept as a mixin column; a masked
    -- array (structured or not) becomes a masked column; everything else — an
    -- existing ordinary column, a structured array, or any other plain array —
    -- is wrapped masked in a masked table and ordinary otherwise.
    let result : ColumnKind :=
      match input with
      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
      | .alreadyMixin     => .mixinKind
      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
      | .structuredMasked => .maskedColumnKind
      | .plainMasked      => .maskedColumnKind
      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
    return result
    -- impl-end

prove_correct classifyColumn by
  loom_solve
  cases input <;> cases tableIsMasked <;> simp_all [classify]
