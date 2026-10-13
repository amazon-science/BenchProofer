import Mathlib
-- imports-end

/-!
Rendering a tuple expression to its source-text form.

A tuple is a parenthesized, comma-separated sequence of component expressions.
Its rendered form is built from the already-rendered text of its components by
wrapping them in parentheses with `", "` between consecutive components.

Three shapes are distinguished by how many components the tuple has:

  * with no components the rendered form is the empty pair of parentheses;
  * with exactly one component the rendered form is that component wrapped in
    parentheses WITH a trailing comma, so it reads as a one-element tuple rather
    than a merely parenthesized expression;
  * with two or more components the rendered form is the components joined by
    `", "` and wrapped in parentheses.

The per-component rendering is itself an unchanged step; here each component
arrives already rendered to text, so the behavior pinned below is exactly "how
the rendered component pieces are wrapped and joined for each arity."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-component
-- rendering step (turning one component expression into its source text) is the
-- SAME operation in every branch and is unaffected by the modeled change; here
-- it is absorbed into the input, which is the list of already-rendered component
-- strings. The modeled change is solely HOW those rendered pieces are wrapped and
-- joined as a function of the component count, so the result is pinned for every
-- possible per-component renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the rendered output is the
-- parenthesized join of the already-rendered component strings, with the
-- one-component case carrying a trailing comma.
-- pure-end

-- post-conditions-start
/-- The rendered output is fully pinned to the input component list, by arity:

  * empty list  ⇒ the empty parentheses `"()"`;
  * a single component `e` ⇒ `"(" ++ e ++ ",)"` (parentheses WITH a trailing
    comma);
  * two or more components ⇒ `"("` then the components joined by `", "` then
    `")"`.

No output component is left free: the result is determined for every arity. -/
def problem_spec_renderTuple (elts : List String) (result : String) : Prop :=
  match elts with
  | [] => result = "()"
  | [e] => result = "(" ++ e ++ ",)"
  | _ => result = "(" ++ String.intercalate ", " elts ++ ")"
-- post-conditions-end

-- impl-start
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- PRE-PATCH (buggy): only a two-way split on emptiness. A one-component tuple
  -- falls into the non-empty branch and is rendered WITHOUT a trailing comma, so
  -- a single component `e` renders as `"(" ++ e ++ ")"` — a parenthesized
  -- expression, not a one-element tuple.
  if elts.length == 0 then
    return "()"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"
-- impl-end

-- proof-start
theorem correct_renderTuple :
    ∀ (elts : List String),
      problem_spec_renderTuple elts (implementation_renderTuple elts) := by
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => simp
  | [e] => simp
  | a :: b :: rest => simp [List.length]
-- proof-end
