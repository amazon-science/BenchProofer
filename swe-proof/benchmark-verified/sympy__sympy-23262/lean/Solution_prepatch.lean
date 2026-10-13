import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee is consumed by the proof. Leaf rendering (the per-element
-- printed source string) is refined to the leaf's own string value (type-only
-- refinement, see refinement.md / mapping.md), so no `opaque` callee or
-- `_prop` axiom is required.
-- axioms-end

-- pure-start
/-- A nested argument structure: a printed leaf, a list node, or a tuple node.
This mirrors the recursive shape consumed when rendering a nested container of
already-printed elements to its source-string form. -/
inductive Arg where
  | leaf  : String → Arg
  | list  : List Arg → Arg
  | tuple : List Arg → Arg
deriving Repr

/-- Front-recursive reference rendering of a nested argument structure to its
source string. A leaf renders to its own string. A list node renders as its
elements, comma-and-space separated, wrapped in square brackets. A tuple node
renders the same way but wrapped in parentheses **with a trailing comma before
the closing parenthesis**, so that the rendering of every tuple — including a
one-element tuple — is unambiguously a tuple rather than a parenthesised value. -/
def specRender : Arg → String
  | .leaf s   => s
  | .list xs  => "[" ++ String.intercalate ", " (xs.map specRender) ++ "]"
  | .tuple xs => "(" ++ String.intercalate ", " (xs.map specRender) ++ ",)"
-- pure-end

-- post-conditions-start
/-- The rendered string is exactly the source rendering of the argument
structure: leaves verbatim, list nodes bracketed, and tuple nodes parenthesised
with a trailing comma so a singleton tuple stays a tuple. -/
def problem_spec_renderArg (arg : Arg) (result : String) : Prop :=
  result = specRender arg
-- post-conditions-end

-- impl-start
def implementation_renderArg : Arg → String
  | .leaf s   => s
  | .list xs  =>
      let parts := xs.map implementation_renderArg
      "[" ++ String.intercalate ", " parts ++ "]"
  | .tuple xs =>
      let parts := xs.map implementation_renderArg
      -- PRE-PATCH BUG: tuple closes with ")" only (no trailing comma), so a
      -- one-element tuple renders as a parenthesised value, not a tuple.
      "(" ++ String.intercalate ", " parts ++ ")"
-- impl-end

-- proof-start
theorem correct_renderArg : ∀ arg : Arg,
    problem_spec_renderArg arg (implementation_renderArg arg) := by
  -- carries the gold proof intent; UNCLOSABLE against the buggy impl (G-DIFF)
  intro arg
  unfold problem_spec_renderArg implementation_renderArg specRender
  rfl
-- proof-end
