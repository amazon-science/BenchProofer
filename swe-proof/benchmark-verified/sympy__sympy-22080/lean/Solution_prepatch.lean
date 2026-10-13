import Mathlib
-- imports-end

/-!
Rendering a product expression to source-code text.

A product is presented as an optional leading sign together with the list of
numerator factors and the list of denominator texts. Each numerator factor
arrives already rendered to text and carries its own *binding strength* (a
numeric weight describing how tightly the factor's textual form binds); the
renderer wraps a numerator factor in parentheses exactly when its binding
strength does not exceed the strength level it is compared against, then joins
the numerator factors with `*`. Each denominator entry arrives as a fully
rendered text (any parenthesization it needs — including group-wrapping applied
by upstream denominator post-processing — is already part of the text); if the
denominator is present it is appended after a `/`, with the whole denominator
group parenthesized when it has more than one entry.

A single numerator factor under a leading minus (`sign = "-"`) is a special
case: it is compared against a dedicated constant strength level rather than the
product's own binding strength. In every other case each numerator factor is
compared against the product's own binding strength.

The behavior is stated abstractly as an input→output relation on the rendered
factors and their strengths; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rendered
-- text of each numerator factor and its numeric binding strength, and the fully
-- rendered text of each denominator entry, are produced upstream (by a generic
-- recursive renderer, a generic strength lookup, and the unchanged denominator
-- post-processing) and are supplied to this routine as plain inputs; this
-- routine only decides numerator parenthesization and assembles the pieces, so
-- there is no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- A single numerator factor: its already-rendered text together with its numeric
binding strength (how tightly its textual form binds). -/
structure Factor where
  strength : Rat
  text : String

/-- The dedicated constant strength level a single numerator factor under a leading minus is
compared against. Observable boundary: a lone negated factor of strength `55` is
wrapped, one of strength `55.5` is not (factor strengths occur in half-unit
steps). -/
def negSingleLevel : Rat := 55

/-- Parenthesize a factor's rendered text when its binding strength does not
exceed the comparison `level`; otherwise emit the text unchanged. -/
def parenFactor (level : Rat) (f : Factor) : String :=
  if f.strength ≤ level then "(" ++ f.text ++ ")" else f.text

/-- The rendered numerator-factor texts. A single numerator factor under a leading
minus (`sign = "-"`) is compared against the dedicated constant level; every other
numerator factor is compared against the product's own binding strength `prec`. -/
def numeratorTexts (sign : String) (prec : Rat) (num : List Factor) : List String :=
  if num.length = 1 ∧ sign = "-" then
    num.map (parenFactor negSingleLevel)
  else
    num.map (parenFactor prec)

/-- The fully assembled product text: sign, then the `*`-joined numerator texts,
then the denominator (after `/`, the denominator group parenthesized when it has
more than one entry). The denominator entries are already fully rendered texts. -/
def renderProduct (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String :=
  let numStr := numeratorTexts sign prec num
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    sign ++ body
  else if den.length = 1 then
    sign ++ body ++ "/" ++ den.headI
  else
    sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
-- pure-end

-- post-conditions-start
/-- The rendered product text is fully determined by the sign, the product's own
binding strength, the numerator factors (each with its rendered text and binding
strength), and the fully rendered denominator texts. Every fragment of the output
is pinned to the inputs: the parenthesization of each numerator factor, the
`*`-joined numerator, and the denominator tail. -/
def problem_spec_renderProduct
    (sign : String) (prec : Rat) (num : List Factor) (den : List String)
    (result : String) : Prop :=
  result = renderProduct sign prec num den
-- post-conditions-end

-- impl-start
/-- Pre-patch skeleton: every numerator factor is compared against the product's
own binding strength `prec`; there is no special comparison level for a lone
numerator factor under a leading minus. -/
def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String := Id.run do
  let mut numStr : List String := []
  numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/" ++ den.headI
  else
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
-- impl-end

-- proof-start
theorem correct_renderProduct :
    ∀ (sign : String) (prec : Rat) (num : List Factor) (den : List String),
      problem_spec_renderProduct sign prec num den
        (implementation_renderProduct sign prec num den) := by
  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct numeratorTexts
  simp only [Id.run, bind, pure]
  split <;> rfl
-- proof-end
