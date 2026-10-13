import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The list of fields whose conflict-resolution tokens
--  are built is a FREE INPUT: how each field was obtained from the caller's
--  request is UNCHANGED and upstream of the modeled boundary, so the spec makes
--  no behavioural claim about it. Each field exposes two observable string
--  attributes (its model attribute name and its database column); both are plain
--  projections carried directly by the `Field` structure, so there is nothing to
--  validate against a real callee — hence no G-AX.)
-- axioms-end

-- pure-start
/- A persisted field, abstracted to its two observable string attributes: the
   model-side attribute name (`attr`) and the database column name (`column`).
   For a field declared with an explicit database column these differ (e.g. a
   mixed-case column under a lower-case attribute); otherwise the column equals
   the attribute. Only these two strings are observable to a consumer of the
   generated conflict-resolution clause, so this is the faithful carrier. -/
structure Field where
  attr   : List Char
  column : List Char
deriving DecidableEq, Inhabited

/- The database-column tokens of a sequence of fields: the database column of
   each field, taken in order. Written front-recursively so a single unfold is
   available per loop step (the backward fold pattern, plan §5.4). Empty
   sequence ⇒ empty result. -/
def dbColumns : List Field → List (List Char)
  | []      => []
  | f :: fs => [f.column] ++ dbColumns fs

@[grind] lemma dbColumns_nil : dbColumns [] = [] := rfl
@[grind] lemma dbColumns_cons (f : Field) (fs : List Field) :
    dbColumns (f :: fs) = [f.column] ++ dbColumns fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the list of tokens that identify each field in a generated
   conflict-resolution clause (the target of the conflict and the columns it
   updates). Each field must be referred to by its DATABASE COLUMN, taken in the
   given order — NOT by its model attribute name, which may differ from the
   column. The SAME operation produces both the conflict-target tokens and the
   updated-column tokens, so one model covers both argument positions
   (refinement.md §A).

   `fields` is read-only (directive 5): the operation reads each field's column
   and never mutates the input sequence. -/
method conflictColumns (fields : List Field) return (out : List (List Char))
  ensures out = dbColumns fields
  do
    -- impl-start
    -- Pre-image skeleton: each field is referred to by its model attribute name
    -- (`f.attr`) rather than its database column (`f.column`). The frozen spec
    -- requires `dbColumns` (the per-field column expansion), so for any field
    -- whose attribute name differs from its database column this diverges and
    -- prove_correct MUST fail.
    let mut acc : List (List Char) := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant acc = dbColumns (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      acc := [f.attr] ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the field at
   `i-1` on the front, so `dbColumns` peels one column. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma dbColumns_drop_step (fields : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    dbColumns (fields.drop (i - 1)) = [fields[i - 1]!.column] ++ dbColumns (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, dbColumns_cons]

prove_correct conflictColumns by
  loom_solve
  rw [dbColumns_drop_step fields i (by omega) (by omega)]
  simp_all
