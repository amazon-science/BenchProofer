import Mathlib
-- imports-end

/-!
Rendering a multi-argument symbolic function application to its textual form in a
target computer-algebra language whose function-call syntax uses SQUARE BRACKETS.

A printer renders such an application by emitting the function's textual name,
then its argument list — each argument rendered by delegating to the SAME printer
(the per-argument renderer) and the resulting fragments joined by a constant
separator — spliced into the language's call template `Name[arg₁, …, argₙ]`.

One routine is modeled: the rendering of a function application whose textual
name is an input `funcName`, whose arguments are the input list `args`, and whose
per-argument renderer is an arbitrary function of an argument. The behavior pinned
below is exactly "the application is rendered as the name followed by the
comma-separated, per-argument-rendered argument list enclosed in the target
language's square-bracket call syntax."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-argument renderer
-- (turning one argument into its textual fragment) is modeled as an arbitrary
-- function parameter `render : Expr → String`: the modeled behavior is solely the
-- shape of the call template and which fragments fill it, so the result is pinned
-- for every possible per-argument renderer. Hence the spec needs no `opaque`/
-- `axiom` callee contract.
-- axioms-end

-- pure-start
/-- The argument-list fragment: each argument rendered, joined by the constant
separator `", "`. (Mirrors a `sep.join(map(render, args))`.) -/
def renderArgs {Expr : Type} (render : Expr → String) (args : List Expr) : String :=
  String.intercalate ", " (args.map render)
-- pure-end

-- post-conditions-start
/-- A function application is rendered as its textual name, then its argument
list — each argument rendered by `render` and joined by `", "` — enclosed in the
target language's square-bracket call syntax: `funcName[arg₁, …, argₙ]`.

Frame discipline: the textual name `funcName`, the bracket delimiters, and the
argument separators are pinned; every argument position is pinned to `render`, so
no output component is left free. -/
def problem_spec_printApplication
    {Expr : Type}
    (render : Expr → String) (funcName : String) (args : List Expr)
    (result : String) : Prop :=
  result = funcName ++ "[" ++ renderArgs render args ++ "]"
-- post-conditions-end

-- impl-start
def implementation_printApplication
    {Expr : Type}
    (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
  return funcName ++ "[" ++ renderArgs render args ++ "]"
-- impl-end

-- proof-start
theorem correct_printApplication :
    ∀ {Expr : Type}
      (render : Expr → String) (funcName : String) (args : List Expr),
      problem_spec_printApplication render funcName args
        (implementation_printApplication render funcName args) := by
  intro Expr render funcName args
  unfold problem_spec_printApplication implementation_printApplication
  rfl
-- proof-end
