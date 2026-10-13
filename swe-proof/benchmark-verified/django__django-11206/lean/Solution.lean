import Mathlib
-- imports-end

/-!
Rendering a specified-precision numeric value as a display string.

A value is rendered to a string under a chosen number of visible decimal places
(`decimalPos`) together with the usual presentation options (decimal separator,
digit grouping, thousands separator, grouping toggles, localization toggle).

When a number of visible decimal places is requested, there is a smallest
magnitude that can still influence any of those visible places: one unit in the
least significant requested place. A value whose absolute magnitude is strictly
below that smallest representable unit cannot affect any visible digit, so for
display purposes it is indistinguishable from zero and is rendered exactly as
zero would be. A value whose magnitude is at least that unit, or any value when
no specific number of decimal places is requested, is rendered on its own.

Everything about turning a (possibly zeroed) value into its final string — the
choice of presentation, truncation/padding to the requested places, sign, and
grouping — is the standard rendering procedure, applied to the value after the
above smallness adjustment.
-/

-- axioms-start
-- `renderDecimal` is the standard, unchanged value-to-string rendering procedure
-- (presentation choice, truncation/padding to the requested number of places,
-- sign, grouping). It is declared `opaque` so it can appear in the executable
-- implementation; the behavior modeled here is solely the smallness adjustment
-- applied to its argument, so NO property of `renderDecimal` is consumed (the
-- result is the renderer applied to the adjusted value, and the implementation
-- computes exactly that). Hence there is no `renderDecimal_prop` axiom; the
-- binding of `renderDecimal` to the real rendering procedure is validated by the
-- conformance check (G-CONF), not assumed in the proof.
opaque renderDecimal :
    ℚ → String → Option Nat → Int → String → Bool → Option Bool → String
-- axioms-end

-- pure-start
/-- The smallest magnitude that still affects a visible decimal place when
`d` decimal places are requested: one unit in the least significant place,
i.e. `10^(-max d 1)` (requesting zero places still uses the tenths place as the
threshold). -/
def cutoffOf (d : Nat) : ℚ := 1 / 10 ^ (max d 1)

/-- The smallness adjustment: when a specific number of decimal places is requested
and the value's magnitude is strictly below the smallest representable unit at
that precision, the value is treated as zero; otherwise it is left unchanged.
When no specific number of decimal places is requested, the value is left
unchanged. -/
def snapValue (number : ℚ) (decimalPos : Option Nat) : ℚ :=
  match decimalPos with
  | none => number
  | some d => if |number| < cutoffOf d then 0 else number
-- pure-end

-- post-conditions-start
/-- The rendered string is the standard rendering procedure applied to the value
AFTER the smallness adjustment: a value below the smallest representable unit at
the requested precision is rendered exactly as zero is, and every other value
(and every value when no precision is requested) is rendered on its own.
The result is fully pinned to the inputs — nothing is left free, since both the
adjustment and the rendering procedure are functions of the inputs. -/
def problem_spec_formatNumber
    (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
    (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
    (useL10n : Option Bool) (result : String) : Prop :=
  result =
    renderDecimal (snapValue number decimalPos) decimalSep decimalPos
      grouping thousandSep forceGrouping useL10n
-- post-conditions-end

-- impl-start
def implementation_formatNumber
    (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
    (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
    (useL10n : Option Bool) : String := Id.run do
  let mut n := number
  match decimalPos with
  | some d =>
      let cutoff := cutoffOf d
      if |n| < cutoff then
        n := 0
  | none => pure ()
  return renderDecimal n decimalSep decimalPos grouping thousandSep
    forceGrouping useL10n
-- impl-end

-- proof-start
theorem correct_formatNumber :
    ∀ (number : ℚ) (decimalSep : String) (decimalPos : Option Nat)
      (grouping : Int) (thousandSep : String) (forceGrouping : Bool)
      (useL10n : Option Bool),
      problem_spec_formatNumber number decimalSep decimalPos grouping
        thousandSep forceGrouping useL10n
        (implementation_formatNumber number decimalSep decimalPos grouping
          thousandSep forceGrouping useL10n) := by
  intro number decimalSep decimalPos grouping thousandSep forceGrouping useL10n
  unfold problem_spec_formatNumber implementation_formatNumber snapValue
  cases decimalPos with
  | none => rfl
  | some d =>
      simp only [Id.run, bind, pure]
      by_cases h : |number| < cutoffOf d
      · simp only [h, if_true]
      · simp only [h, if_false]
-- proof-end
