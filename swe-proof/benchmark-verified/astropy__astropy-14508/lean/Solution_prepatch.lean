import Mathlib
-- imports-end

/-!
Rendering a floating-point value as the string written into a fixed-width
header card.

A card stores a value together with an optional trailing comment inside a field
of bounded width, so the value's textual form must be kept short: it may be at
most 20 characters long. The value is rendered from its string form and then,
only if that form is longer than the budget, shortened.

The desired behavior:

* Start from the value's *shortest* standard textual form — the representation a
  language runtime prints for the number — written with an upper-case exponent
  marker `E` (any lower-case `e` is upper-cased). This form already contains a
  decimal point or an exponent, so no extra padding is added.
* If that form fits within 20 characters, it is used verbatim.
* If it is longer than 20 characters, it is shortened to 20:
  * with no exponent marker, keep the first 20 characters;
  * with an exponent marker, keep the exponent suffix intact (from the marker to
    the end) and truncate the leading significand so the whole string is 20
    characters.

The point is that the *short* textual form is the starting point: a number such
as one whose shortest form already fits must be rendered with that short form,
never expanded to a longer fixed-precision form that would overflow the budget
and force the trailing comment to be truncated.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The numeric
-- value enters the model through its already-computed textual observations
-- (its shortest standard form and its fixed-precision form); both are grounded
-- inputs, so no `opaque`/`axiom` callee contract is needed. The shortening rule
-- is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- The textual observations of a numeric value that the rendering rule reads.

* `reprStr` — the value's shortest standard textual form (what a runtime prints
  for the number, e.g. `0.009125`);
* `fixedStr` — the value's fixed-precision textual form (a representation carried
  to many significant digits, e.g. `0.009124999999999999`).

Both are pure functions of the value; the rule uses the carrier appropriate to
the desired behavior. -/
structure FmtInput where
  reprStr : List Char
  fixedStr : List Char

/-- Upper-case the exponent marker: every lower-case `e` becomes `E`. -/
def normE (s : List Char) : List Char :=
  s.map (fun c => if c = 'e' then 'E' else c)

/-- Limit a value string to at most 20 characters. If it already fits, it is
returned unchanged; otherwise, if there is no exponent marker the first 20
characters are kept, and if there is one the exponent suffix (from the marker
onward) is kept intact while the leading significand is truncated so the whole
string is 20 characters. -/
def truncate20 (valueStr : List Char) : List Char :=
  let strLen := valueStr.length
  if strLen > 20 then
    match valueStr.findIdx? (· = 'E') with
    | none     => valueStr.take 20
    | some idx => valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
  else
    valueStr
-- pure-end

-- post-conditions-start
/-- The rendered string is the value's shortest standard textual form (with an
upper-cased exponent marker), shortened to at most 20 characters by the rule
above. The fixed-precision form is NOT used. -/
def problem_spec_formatFloat (inp : FmtInput) (result : List Char) : Prop :=
  result = truncate20 (normE inp.reprStr)
-- post-conditions-end

-- impl-start
def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do
  -- Pre-patch bug: the rendering starts from the value's FIXED-PRECISION form
  -- (carried to many significant digits) instead of its shortest standard form,
  -- so a value whose short form already fits is needlessly expanded, overflowing
  -- the budget and forcing the trailing comment to be truncated.
  let mut valueStr := normE inp.fixedStr
  let strLen := valueStr.length
  if strLen > 20 then
    match valueStr.findIdx? (· = 'E') with
    | none     => valueStr := valueStr.take 20
    | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
  return valueStr
-- impl-end

-- proof-start
theorem correct_formatFloat :
    ∀ (inp : FmtInput),
      problem_spec_formatFloat inp (implementation_formatFloat inp) := by
  intro inp
  unfold problem_spec_formatFloat implementation_formatFloat truncate20
  rfl
-- proof-end
