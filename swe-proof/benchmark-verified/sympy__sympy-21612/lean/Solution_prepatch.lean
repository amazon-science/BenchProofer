import Mathlib
-- imports-end

/-!
Rendering a fractional expression to its textual form, with correct bracketing of
the denominator.

A compound product is rendered as a numerator part divided by a denominator. Each
factor that sits in the denominator is itself an expression, and is first turned
into a text fragment by the surrounding renderer. The question modeled here is
purely a BRACKETING decision for one such denominator factor: when does the
factor's text need an extra pair of surrounding brackets so the division binds the
way the expression actually means?

The rule: a denominator factor must be wrapped in brackets exactly when its base
is itself a COMPOUND expression — concretely, a product or a power — that is built
from more than one component. (A single-component base, an atom, or any other kind
of expression is spliced in without the extra brackets, because the base
renderer's own fragment is already unambiguous in those cases.) Without the extra
brackets a denominator that is itself a fraction or a product collapses into the
surrounding division and changes meaning.

The base renderer itself (turning the factor's base into its text fragment) is
taken as an arbitrary function of the base, so the behavior pinned below is exactly
"the factor's text is the base fragment, wrapped in one pair of brackets precisely
when the base is a multi-component product or power."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The base renderer (turning
-- the factor's base into its text fragment) is modeled as an arbitrary function
-- parameter `render : Expr → String`: the modeled behavior is solely WHETHER an
-- extra pair of brackets is placed around that fragment, so the result is pinned
-- for every possible base renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract. (`render` is recorded in mapping.md as an A-reference solely to
-- document the G-CONF binding to the real base renderer.)
-- axioms-end

-- pure-start
-- The bracketing test: a denominator factor's base needs an extra pair of brackets
-- exactly when it has more than one component AND is a compound product or power.
def needsBrackets (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : Prop :=
  baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)

instance (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) :
    Decidable (needsBrackets baseComponentCount baseIsProduct baseIsPower) := by
  unfold needsBrackets; infer_instance
-- pure-end

-- post-conditions-start
/-- The text of one denominator factor: the base fragment produced by `render`,
wrapped in a single pair of brackets exactly when the base is a multi-component
product or power, and otherwise spliced in unchanged.

Frame discipline: the bracketing decision and the literal bracket characters are
pinned, and the inner fragment is pinned to `render base`, so no part of the
output is left free. -/
def problem_spec_printDenominatorFactor
    {Expr : Type}
    (render : Expr → String) (base : Expr)
    (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool)
    (result : String) : Prop :=
  result =
    (if needsBrackets baseComponentCount baseIsProduct baseIsPower
     then "(" ++ render base ++ ")"
     else render base)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy): the bracket-needed test only fires when the base is a
-- multi-component PRODUCT; a multi-component POWER base is treated as not needing
-- brackets. A denominator factor whose base is itself a power then loses its
-- brackets and the division re-associates, changing meaning.
def implementation_printDenominatorFactor
    {Expr : Type}
    (render : Expr → String) (base : Expr)
    (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
  let baseStr := render base
  let needParen := baseComponentCount ≠ 1 ∧ baseIsProduct = true
  if needParen then
    return "(" ++ baseStr ++ ")"
  return baseStr
-- impl-end

-- proof-start
theorem correct_printDenominatorFactor :
    ∀ {Expr : Type}
      (render : Expr → String) (base : Expr)
      (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool),
      problem_spec_printDenominatorFactor render base baseComponentCount baseIsProduct baseIsPower
        (implementation_printDenominatorFactor render base baseComponentCount baseIsProduct baseIsPower) := by
  intro Expr render base baseComponentCount baseIsProduct baseIsPower
  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets
  by_cases h : baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
  · rw [if_pos h, if_pos h]; rfl
  · rw [if_neg h, if_neg h]; rfl
-- proof-end
