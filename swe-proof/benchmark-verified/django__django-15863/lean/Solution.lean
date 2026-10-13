import Mathlib
-- imports-end

/-!
Preserving the exact value of a decimal-valued input when formatting it for
display.

A numeric template filter accepts a value, coerces it into a working decimal
number, and then renders that decimal to a chosen count of fractional places.
The coercion is the step modeled here.

When the incoming value is already an exact decimal (a finite base-ten number
with a definite coefficient and scale), the working decimal must carry that
*exact same value* — every significant digit is retained, no matter how many
there are. Only then can a request for, say, twenty-one fractional places
reproduce all twenty-one digits of the input.

The coercion has two stages: a primary stage that renders the value as a decimal
literal and reads it back, and a fallback stage that routes the value through a
fixed-width binary floating-point approximation. For an exact decimal value the
primary stage always yields a valid decimal literal, so it succeeds and the
working decimal equals the input value exactly; the binary approximation
fallback is never needed and is not consulted.
-/

-- axioms-start
/-- A coercion that routes a value through a fixed-width binary floating-point
representation and back to a decimal. Because that representation holds only a
bounded number of significant bits, this need NOT return the exact input value;
no value-preservation property is assumed of it. It models the secondary
(fallback) coercion stage, which the primary stage makes unnecessary for an
exact decimal input. -/
opaque floatFallback : Rat → Rat
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The working decimal carried into formatting equals the input value exactly:
no significant digit of the input is dropped. `text` is the exact value of the
incoming decimal; `result` is the exact value of the working decimal. -/
def problem_spec_coerceDecimal (text : Rat) (result : Rat) : Prop :=
  result = text
-- post-conditions-end

-- impl-start
def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
  -- The primary stage renders the value as a decimal literal and reads it back.
  -- For an exact decimal value that literal is always a valid decimal, so the
  -- primary read succeeds.
  let primaryReadSucceeds : Bool := true
  if primaryReadSucceeds then
    -- read back the exact same value
    return text
  -- Fallback stage (reached only if the primary read fails to yield a decimal):
  -- route the value through a binary floating-point approximation.
  return floatFallback text
-- impl-end

-- proof-start
theorem correct_coerceDecimal : ∀ (text : Rat),
    problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
  intro
  unfold problem_spec_coerceDecimal implementation_coerceDecimal
  rfl
-- proof-end
