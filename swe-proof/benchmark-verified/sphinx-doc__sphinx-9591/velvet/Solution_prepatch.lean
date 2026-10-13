import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- An inline documentation node. A rendered type annotation is a sequence of
   these. Only the fields the rendered signature observes are kept: `text`
   carries literal text, `xref` carries a cross-reference whose target is a type
   name, `punct` carries structural punctuation (brackets, commas, the union
   bar). The bijection to the real inline-node carriers is in mapping.md §2. -/
inductive DocNode where
  | text  (s : List Char)
  | xref  (target : List Char)
  | punct (s : List Char)
  deriving DecidableEq, Inhabited, Repr

-- axioms-start
-- (No consumed axiom: the parser callee is modeled deeply — see `pure`.)
-- axioms-end

/- The domain on which the deep model below is exact: a single (possibly
   dotted) type name — a nonempty string of identifier characters / dots that
   begins with a letter or underscore. On this domain the parser produces a
   single node; compound annotations (with brackets, commas, operators) are out
   of scope and excluded by the method precondition. -/
def isNameChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_' || c = '.'

def isBareName (s : List Char) : Bool :=
  match s with
  | []      => false
  | c :: cs => (c.isAlpha || c = '_') && (c :: cs).all isNameChar

-- pure-start
/- Deep model (A-reference) of the standard documentation type-annotation
   parser, on the domain this signature uses: a single type name. The parser
   renders such a name as ONE cross-reference node targeting that name (so the
   documented type can be navigated to its definition) rather than as inert
   literal text. Validated == the real callee over this domain by
   axiom_check.py (G-AX); provenance in mapping.md §3.1. -/
def annotationNodes (typ : List Char) : List DocNode :=
  [DocNode.xref typ]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

method propertyTypeNodes (typ : List Char) return (out : List DocNode)
  require isBareName typ
  ensures out = DocNode.text ": ".toList :: annotationNodes typ
  do
    -- impl-start
    -- Pre-image skeleton: the type is concatenated with the leading literal into
    -- a SINGLE inert text node (no parser is consulted). The frozen spec requires
    -- a separate literal node followed by the parser's cross-reference node, so
    -- prove_correct MUST fail.
    let result := [DocNode.text (": ".toList ++ typ)]
    return result
    -- impl-end

prove_correct propertyTypeNodes by
  loom_solve
