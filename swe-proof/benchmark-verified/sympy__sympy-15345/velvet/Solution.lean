import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The arguments of a node are stringified by the same
--  comma-joining helper before and after the change, so the joined argument
--  text and the head name are passed in as inputs and owed no contract. The
--  behaviour under specification — which delimiter pair surrounds the joined
--  arguments — is a pure dispatch on the node's kind, modeled DEEPLY in the
--  `pure` region below. There is no `axiom` declaration and no A-reference deep
--  model of an outside callee.)
-- axioms-end

-- pure-start
/- The kinds of expression node this code printer distinguishes when it decides
   how to surround the (already-rendered, comma-joined) argument text:
     * `functionApp` — a named-function application, e.g. a call written as a
                       head name applied to arguments;
     * `extremum`    — the maximum/minimum operators over their arguments, which
                       in this target language are written as an ordinary named
                       application of their head name to their arguments;
     * `plainExpr`   — any other expression, rendered in the generic fallback
                       form used for nodes the printer has no dedicated form for. -/
inductive NodeKind where
  | functionApp
  | extremum
  | plainExpr
  deriving Inhabited, DecidableEq

/- The rendering of a node into the target language's source text, modeled
   deeply. `head` is the node's head name and `args` is its arguments already
   rendered and joined with the separator; this function only chooses how to
   surround `args`:
     * a named-function application and the maximum/minimum operators are both
       written with square brackets: `head[args]` — the form the target
       language requires for a function call;
     * every other expression is written with the generic round-parenthesis
       fallback form: `head(args)`. -/
def render (head args : List Char) (kind : NodeKind) : List Char :=
  match kind with
  | .functionApp => head ++ ['['] ++ args ++ [']']
  | .extremum    => head ++ ['['] ++ args ++ [']']
  | .plainExpr   => head ++ ['('] ++ args ++ [')']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render one expression node to target-language source text. `head` and `args`
   are read-only inputs (not `mut`): the head name and the comma-joined argument
   text are computed elsewhere and are unchanged here; this query selects the
   surrounding delimiter pair from the node's kind and mutates nothing
   (directive 5). The extremum operators are surrounded by the same square
   brackets as a named-function application; the generic round-parenthesis form
   is reserved for nodes with no dedicated rendering. -/
method renderNode (head : List Char) (args : List Char) (kind : NodeKind)
    return (out : List Char)
  ensures out = render head args kind
  ensures kind = NodeKind.functionApp → out = head ++ ['['] ++ args ++ [']']
  ensures kind = NodeKind.extremum    → out = head ++ ['['] ++ args ++ [']']
  ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
  do
    -- impl-start
    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
    -- A named-function application and the extremum operators take the square
    -- bracket form `head[args]`; any other node takes the round-parenthesis
    -- fallback `head(args)`.
    let result : List Char :=
      match kind with
      | .functionApp => head ++ ['['] ++ args ++ [']']
      | .extremum    => head ++ ['['] ++ args ++ [']']
      | .plainExpr   => head ++ ['('] ++ args ++ [')']
    return result
    -- impl-end

prove_correct renderNode by
  loom_solve
  cases kind <;> simp_all [render]
