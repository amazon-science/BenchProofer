import Mathlib
-- imports-end

/-!
Choosing the column class when a piece of data is added to a table.

When a value is added to a table it must be wrapped in a column object, and the
*class* of that column object is decided from a handful of observations about the
value (made after any registered conversion handler has run):

* whether it is already a plain column object;
* whether it is already a recognised mixin-style column;
* whether it is a *sequence whose first element* is such a mixin (a list of mixin
  scalars), in which case the column is built from that element's own class;
* whether it is a masked array;
* whether it is the null object;
* whether it carries a dtype at all (otherwise it is first coerced to an array);
* and, for plain arrays, how many fields its dtype has.

The desired rule is:

  * an existing column keeps the class chosen by the table's own upgrade rule;
  * an existing mixin column is returned with its class preserved;
  * a sequence of mixin scalars yields a column of that element's class;
  * a masked array yields the table's masked column class;
  * the null object yields the table's default column class;
  * a value lacking a dtype is coerced to an array and yields the masked column
    class if that coercion produced a masked array, otherwise the default class;
  * any other plain array — INCLUDING a multi-field (structured) array — yields
    the table's default column class.

In particular a multi-field structured array is treated like any other plain
array: a masked one becomes the masked column class, an unmasked one becomes the
default column class. It is NOT given a distinct mixin class on account of having
several fields.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The class
-- decision is modeled structurally over the observable flags of the input
-- (already-a-column, already-a-mixin, first-element-is-a-mixin, masked, null,
-- has-a-dtype, field count) together with the classes the unchanged upstream
-- sub-decisions yield, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The class of a column object that a table can hold. `column` is the default
column class; `maskedColumn` is its masked counterpart; `ndarrayMixin` is the
array-backed mixin class; `otherMixin` stands for any other mixin column class. -/
inductive ColClass where
  | column
  | maskedColumn
  | ndarrayMixin
  | otherMixin
deriving DecidableEq, Repr

/-- The observations of an input value (taken after any conversion handler has
run) that the column-class decision depends on.

* `isColumn` — the value is already a plain column object;
* `isMixin` — the value is already a recognised mixin-style column;
* `data0IsMixin` — the value is a sequence whose first element is a mixin scalar;
* `isNdarray` — the value is an array (masked arrays included);
* `numDtypeFields` — the number of fields in the value's dtype (`0` when it has no
  structured dtype, the field count when structured);
* `isMaskedArray` — the value is a masked array;
* `isNone` — the value is the null object;
* `hasDtype` — the value carries a dtype attribute;
* `columnInputResult` — the class the table's upgrade rule assigns to an existing
  column;
* `dataMixinClass` — the class of an existing mixin column (returned as-is);
* `seqMixinResult` — the class produced from a sequence of mixin scalars
  (including the fallback when that construction does not succeed);
* `seqConvMasked` — whether coercing a dtype-less value to an array produced a
  masked array;
* `tableColumnClass` — the table's default column class;
* `tableMaskedColumn` — the table's masked column class. -/
structure ConvInput where
  isColumn : Bool
  isMixin : Bool
  data0IsMixin : Bool
  isNdarray : Bool
  numDtypeFields : Nat
  isMaskedArray : Bool
  isNone : Bool
  hasDtype : Bool
  columnInputResult : ColClass
  dataMixinClass : ColClass
  seqMixinResult : ColClass
  seqConvMasked : Bool
  tableColumnClass : ColClass
  tableMaskedColumn : ColClass

/-- The column class selected for an input value, by the rule described above. -/
def convResultClass (inp : ConvInput) : ColClass :=
  if inp.isColumn then inp.columnInputResult
  else if inp.isMixin then inp.dataMixinClass
  else if inp.data0IsMixin then inp.seqMixinResult
  else if inp.isMaskedArray then inp.tableMaskedColumn
  else if inp.isNone then inp.tableColumnClass
  else if !inp.hasDtype then
    (if inp.seqConvMasked then inp.tableMaskedColumn else inp.tableColumnClass)
  else inp.tableColumnClass
-- pure-end

-- post-conditions-start
/-- The selected column class is exactly the class assigned by the rule. A
multi-field (structured) plain array is not special-cased: it follows the same
masked/default decision as any other plain array. -/
def problem_spec_columnForTableData
    (inp : ConvInput) (result : ColClass) : Prop :=
  result = convResultClass inp
-- post-conditions-end

-- impl-start
def implementation_columnForTableData (inp : ConvInput) : ColClass := Id.run do
  if inp.isColumn then
    return inp.columnInputResult
  else if inp.isMixin then
    return inp.dataMixinClass
  else if inp.data0IsMixin then
    return inp.seqMixinResult
  else if inp.isMaskedArray then
    return inp.tableMaskedColumn
  else if inp.isNone then
    return inp.tableColumnClass
  else if !inp.hasDtype then
    if inp.seqConvMasked then
      return inp.tableMaskedColumn
    else
      return inp.tableColumnClass
  else
    return inp.tableColumnClass
-- impl-end

-- proof-start
theorem correct_columnForTableData :
    ∀ (inp : ConvInput),
      problem_spec_columnForTableData inp
        (implementation_columnForTableData inp) := by
  intro inp
  unfold problem_spec_columnForTableData implementation_columnForTableData convResultClass
  rfl
-- proof-end
