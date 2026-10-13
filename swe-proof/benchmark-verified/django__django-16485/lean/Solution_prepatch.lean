import Mathlib
-- imports-end

/-!
Rendering a decimal value as text for a requested number of decimal places.

A value is rendered together with a requested number of decimal places `p`
(an integer that may be negative). There are two ways the value can be rendered:

  * as a plain integer — the value's whole part, formatted with no fractional
    digits; or
  * in the general way — the value rounded/padded to the requested number of
    fractional places. This general digit computation is PARTIAL: on some
    values it rejects its inputs and produces no digit text at all, in which
    case the call as a whole yields no rendered text (the failure propagates
    to the caller).

The choice between them depends on the value and on `p`:

  * when the value is a whole number (its fractional part is zero) AND the
    requested number of decimal places is NOT positive (zero or negative), the
    value is rendered as a plain integer — there are no fractional digits worth
    showing, so the whole part alone is emitted;
  * in every other case (the value has a fractional part, or a positive number
    of places was requested), the general rendering is used — producing text
    exactly when the digit computation does.

Both produced digit texts finish by passing through the same locale/grouping
formatting step; only the digit text and the place count fed to it differ
between the two cases.
-/

-- axioms-start
/-- A decimal value, modeled by the data its standard tuple view exposes
(`mapping.md` gives the bijection to the repo's decimal tuple):
* `negative` — whether the value carries a negative sign;
* `digits` — its significant digits, most-significant first;
* `exponent` — the tuple exponent (the value is `digits · 10^exponent`).
Nothing here inspects these fields directly; they carry the value so the
unchanged sub-computations below can act on it. -/
structure DecVal where
  negative : Bool
  digits : List Nat
  exponent : Int

/-- Whether the value is a whole number — its fractional part is zero. (Unchanged
sub-computation; signature only.) -/
opaque decIsWhole : DecVal → Bool

/-- The value's whole (integer) part. (Unchanged sub-computation; signature
only.) -/
opaque decIntPart : DecVal → Int

/-- The general digit text for the value rounded/padded to the given number of
decimal places: `some` of the assembled sign/digits/point string before locale
formatting, or `none` when the digit computation rejects its inputs and
produces no text (that failure propagates to the caller — the call yields no
rendered text). (Unchanged sub-computation; signature only.) -/
opaque decimalDigits : DecVal → Int → Option String

/-- The locale/grouping formatting step applied to a digit string with a given
number of fractional places, under this call's locale/grouping
configuration. (Unchanged sub-computation; signature only.) -/
opaque numberFormat : String → Nat → String
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the rendering choice is a direct
-- decision over `decIsWhole d` and the sign of `p`, and each branch's outcome
-- is the corresponding unchanged sub-computation.
-- pure-end

-- post-conditions-start
/-- The rendered outcome is exactly the outcome of the selected branch. When the
value is whole and the requested place count is not positive, it is the whole
part formatted with zero fractional places (always produced). Otherwise it is
the general rendering at `|p|` places — produced exactly when the general digit
computation produces text, and absent (the failure propagates) when it does
not. Both produced texts go through the same final formatting step, so the
outcome is fully determined by `d` and `p`. -/
def problem_spec_floatformat (d : DecVal) (p : Int) (result : Option String) : Prop :=
  result =
    (if decIsWhole d && decide (p ≤ 0)
     then some (numberFormat (toString (decIntPart d)) 0)
     else (decimalDigits d p).map (fun s => numberFormat s p.natAbs))
-- post-conditions-end

-- impl-start
def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
  -- Pre-patch skeleton: the integer branch is taken only when the requested
  -- place count is strictly negative, so a whole value with a place count of
  -- exactly zero falls through to the general rendering instead.
  if decIsWhole d && decide (p < 0) then
    return some (numberFormat (toString (decIntPart d)) 0)
  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- buggy impl it cannot close: on the discriminating clause `decIsWhole d = true`
-- and `p = 0`, the spec selects the integer branch (`some (numberFormat (toString
-- (decIntPart d)) 0)`), while this impl's `p < 0` guard is false and it returns
-- the general rendering `(decimalDigits d 0).map (fun s => numberFormat s 0)` —
-- the two outcomes are distinct opaque values, so the result no longer matches
-- the spec.
theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
    problem_spec_floatformat d p (implementation_floatformat d p) := by
  intro d p
  unfold problem_spec_floatformat implementation_floatformat
  simp only [Id.run, Id.pure_eq, Id.bind_eq]
-- proof-end
