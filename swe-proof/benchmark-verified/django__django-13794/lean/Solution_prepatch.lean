import Mathlib
-- imports-end

/-!
Binary concatenation of values that may be produced on demand.

Some text values are not held directly but are produced when first needed: such
a value acts as a stand-in (a proxy) for the concrete text it will eventually
yield, and "forcing" it returns that underlying concrete text. The desired
behaviour is that the binary concatenation operator works uniformly whether each
operand is an ordinary concrete text value or one of these on-demand values:
concatenating two operands always yields the concatenation of the underlying
concrete texts, in left-to-right order.

There are three concrete situations the operator must cover, distinguished only
by which operand (if any) is the on-demand one:

* the left operand is on-demand — it is forced and concatenated with the right;
* the left operand is concrete and the right is on-demand — the right is forced
  and appended to the left;
* both operands are concrete — ordinary text concatenation.

In every case the observable result is the concatenation of the two forced
underlying texts. (Historically only the all-concrete case worked and an
on-demand operand made the concatenation fail, so callers that catch the failure
— such as a value-combining template filter — silently produced the empty
string.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Forcing an
-- on-demand operand to its underlying text is modeled DIRECTLY (`force` projects
-- the carried underlying text from the operand) — a deep model whose only inputs
-- are the function's own arguments, not an axiomatized oracle. Concatenation is
-- ordinary text append. No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An operand of the binary concatenation: either an ordinary concrete text
value, or a value produced on demand that stands in for its underlying text. -/
inductive Operand where
  | concrete : String → Operand
  | deferred : String → Operand
deriving Repr, DecidableEq

/-- Forcing an operand to its underlying concrete text: a concrete operand is its
own text; an on-demand operand yields the text it stands in for. -/
def force : Operand → String
  | .concrete s => s
  | .deferred s => s
-- pure-end

-- post-conditions-start
/-- The result of concatenating two operands is the concatenation of their forced
underlying texts, in left-to-right order — regardless of which operands are
on-demand. -/
def problem_spec_lazyConcat (a b : Operand) (result : String) : Prop :=
  result = force a ++ force b
-- post-conditions-end

-- impl-start
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  -- pre-change skeleton: the proxy supports no binary-concatenation operator,
  -- so an on-demand operand makes the concatenation fail; a caller that catches
  -- the failure (the value-combining filter) yields the empty string. Only the
  -- all-concrete case produces a real concatenation.
  match a with
  | .concrete s =>
      match b with
      | .concrete t => return s ++ t
      | .deferred _ => return ""
  | .deferred _ => return ""
-- impl-end

-- proof-start
theorem correct_lazyConcat :
    ∀ (a b : Operand),
      problem_spec_lazyConcat a b (implementation_lazyConcat a b) := by
  sorry
-- proof-end
