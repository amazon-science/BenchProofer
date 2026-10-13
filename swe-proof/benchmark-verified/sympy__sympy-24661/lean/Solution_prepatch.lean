import Mathlib
-- imports-end

/-!
Parsing a relational comparison in non-evaluating mode.

When an expression is parsed in a mode that asks for it to be left UNEVALUATED,
each operator in the source is supposed to be rebuilt as a call to the
corresponding symbolic constructor carrying an "do not evaluate" flag, so that
the parsed result is a structural object rather than a value computed on the
spot.

Arithmetic operators and named functions already get this treatment. A *relational
comparison* — `<`, `<=`, `>`, `>=`, `==`, `!=` — must get it too: parsing `1 < 2`
in non-evaluating mode is required to produce the unevaluated relational object
`Lt(1, 2, evaluate=False)`, NOT the boolean truth value `True` obtained by
actually performing the comparison.

The rule for a single comparison `left ⊙ right`:

* if `⊙` is one of the six recognised relational operators, the comparison is
  rebuilt as a call to that operator's symbolic constructor, applied to the
  (recursively rebuilt) left and right operands, with the "do not evaluate" flag
  set — concretely `Lt`/`Le`/`Gt`/`Ge`/`Eq`/`Ne` for
  `<`/`<=`/`>`/`>=`/`==`/`!=`;
* if `⊙` is any other comparison operator, the comparison node is returned
  unchanged.

An operand may be a numeric literal, a plain identifier, a nested comparison
(rebuilt by the same rule), or a call. Rebuilding a call is the treatment named
functions already receive: its arguments are each rebuilt by the same rule, and
the "do not evaluate" flag is attached when the callee is one of the names that
are built in non-evaluating form. A call to any other name keeps whatever flag it
already carried.

Each recognised relational operator maps to its own constructor name, and the six
are pairwise distinct.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rewrite of
-- a comparison into an unevaluated relational call — including the recursive
-- rebuilding of its operands, calls among them — is modeled DEEPLY and
-- structurally over the parsed-node fragment by `transform`/`transformArgs`, so
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A comparison operator. The six recognised relational operators plus `other`
for any comparison operator outside the recognised set (e.g. identity / membership
tests), which leaves the comparison node unchanged. -/
inductive RelOp where
  | lt   -- `<`
  | le   -- `<=`
  | gt   -- `>`
  | ge   -- `>=`
  | eq   -- `==`
  | ne   -- `!=`
  | other
deriving DecidableEq, Repr

/-- The symbolic constructor name a relational operator maps to, or `none` for an
unrecognised comparison operator. The six recognised operators map to six
pairwise-distinct constructor names. -/
def relClassName : RelOp → Option String
  | .lt => some "Lt"
  | .le => some "Le"
  | .gt => some "Gt"
  | .ge => some "Ge"
  | .eq => some "Eq"
  | .ne => some "Ne"
  | .other => none

/-- The fragment of a parsed node tree that the rewrite walks.

* `const n` — a numeric literal;
* `name s` — a plain identifier;
* `app func args evalFalse` — a constructor/function call (`func` applied to
  `args`); `evalFalse` records whether the "do not evaluate" flag is attached;
* `cmp left op right` — a single comparison `left op right`. -/
inductive AstNode where
  | const (n : Int)
  | name (s : String)
  | app (func : String) (args : List AstNode) (evalFalse : Bool)
  | cmp (left : AstNode) (op : RelOp) (right : AstNode)

/-- The names that are built in non-evaluating form: a call to one of these has
the "do not evaluate" flag attached when it is rebuilt. -/
def nonEvaluatingFuncs : List String :=
  ["Abs", "im", "re", "sign", "arg", "conjugate",
   "acos", "acot", "acsc", "asec", "asin", "atan",
   "acosh", "acoth", "acsch", "asech", "asinh", "atanh",
   "cos", "cot", "csc", "sec", "sin", "tan",
   "cosh", "coth", "csch", "sech", "sinh", "tanh",
   "exp", "ln", "log", "sqrt", "cbrt"]

/-- Whether a callee name is built in non-evaluating form. -/
def isNonEvaluatingFunc (f : String) : Bool := nonEvaluatingFuncs.contains f

-- The recursive node-rewrite (the visitor dispatch).
--
-- A comparison with a recognised operator is rebuilt as a call to that operator's
-- constructor on the rewritten operands, with the "do not evaluate" flag set; with
-- an unrecognised operator it is returned unchanged. Literals and identifiers are
-- returned as-is. A call is rebuilt by rewriting each of its arguments; its "do
-- not evaluate" flag is set when the callee is a name built in non-evaluating
-- form, and otherwise keeps the value it already carried.
mutual
/-- The recursive node-rewrite (the visitor dispatch). -/
def transform : AstNode → AstNode
  | .const n => .const n
  | .name s => .name s
  | .app func args evalFalse =>
      .app func (transformArgs args) (evalFalse || isNonEvaluatingFunc func)
  | .cmp left op right =>
      match relClassName op with
      | some cls => .app cls [transform left, transform right] true
      | none => .cmp left op right

/-- `transform` applied to each element of an argument list. -/
def transformArgs : List AstNode → List AstNode
  | [] => []
  | a :: rest => transform a :: transformArgs rest
end
-- pure-end

-- post-conditions-start
/-- Rewriting a single comparison `left op right`. When `op` is a recognised
relational operator (`relClassName op = some cls`), the result is the call to `cls`
on the rewritten operands with the "do not evaluate" flag set; otherwise the
comparison node is returned unchanged. The result is fully pinned in both cases. -/
def problem_spec_transformRelational
    (left : AstNode) (op : RelOp) (right : AstNode) (result : AstNode) : Prop :=
  match relClassName op with
  | some cls => result = AstNode.app cls [transform left, transform right] true
  | none => result = AstNode.cmp left op right
-- post-conditions-end

-- impl-start
def implementation_transformRelational
    (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
  -- Pre-patch bug: there is no handler for a comparison node, so it is left
  -- unchanged regardless of the operator (the generic visitor returns it as-is).
  -- A recognised relational operator is therefore NOT rebuilt as an unevaluated
  -- relational call — exactly the observed defect.
  return AstNode.cmp left op right
-- impl-end

-- proof-start
theorem correct_transformRelational :
    ∀ (left : AstNode) (op : RelOp) (right : AstNode),
      problem_spec_transformRelational left op right
        (implementation_transformRelational left op right) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
