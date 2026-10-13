import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- An inline documentation node. A rendered type annotation is a sequence of
   these. Only the fields the rendered signature observes are kept: `text`
   carries literal display text, `xref` carries a cross-reference whose target
   is a type name (a navigable class reference), `punct` carries structural
   punctuation (brackets, commas). The bijection to the real inline-node
   carriers is in mapping.md §2. -/
inductive DocNode where
  | text  (s : List Char)
  | xref  (target : List Char)
  | punct (s : List Char)
  deriving DecidableEq, Inhabited, Repr

/- A constant value that can appear inside a parametrised type. Three shapes are
   modeled — a boolean, an integer, and a (simple) string literal — covering the
   constant kinds the documented annotations in scope use. The bijection to the
   real Python constant objects is in mapping.md §2. -/
inductive LitVal where
  | bool (b : Bool)
  | int  (n : Int)
  | str  (s : List Char)
  deriving DecidableEq, Inhabited, Repr

-- axioms-start
-- (No consumed axiom: the rendering of a parametrised type is modeled deeply —
--  see the `pure` region.)
-- axioms-end

-- pure-start
/- The domain on which the string representation below is exact: a "simple"
   string is one whose characters are all printable ASCII (32–126) other than
   the apostrophe and the backslash. Such a string is shown delimited by single
   quotes with no character needing an escape. Constant strings outside this
   domain (containing quotes, backslashes, or non-printable code points) are out
   of scope and excluded by the method precondition. -/
def isSimpleStrChar (c : Char) : Bool :=
  decide (32 ≤ c.toNat ∧ c.toNat ≤ 126) && c ≠ '\'' && c ≠ '\\'

def okLit : LitVal → Bool
  | .str s => s.all isSimpleStrChar
  | .int n => decide (0 ≤ n)
  | _      => true

/- The display text of one constant value: its canonical source representation.
   A boolean shows as `True`/`False`, an integer as its decimal digits, and a
   simple string as its single-quoted form (the surrounding quotes ARE part of
   the displayed text — a string constant is shown with delimiters so it reads
   unambiguously). Validated against the real value-representation routine over
   this domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def reprVal : LitVal → List Char
  | .bool true  => "True".toList
  | .bool false => "False".toList
  | .int n      => (toString n).toList
  | .str s      => '\'' :: (s ++ ['\''])

/- The node sequence for a comma-separated list of constant values: each value
   becomes one node built by `mk` from its display text `render v`, and adjacent
   values are separated by a `", "` punctuation node. Front-recursive so a single
   unfold is available per step. Parametrised over the node constructor `mk` and
   the per-value renderer `render` so the value-display policy is explicit at the
   call site. -/
def valSeq (mk : List Char → DocNode) (render : LitVal → List Char) :
    List LitVal → List DocNode
  | []      => []
  | [v]     => [mk (render v)]
  | v :: vs => mk (render v) :: DocNode.punct ", ".toList :: valSeq mk render vs

/- Frame the inner sequence with the head cross-reference and the surrounding
   brackets: `head` renders as a navigable cross-reference (the parametrised
   type itself), then `[`, then the inner nodes, then `]`. -/
def wrap (head : List Char) (inner : List DocNode) : List DocNode :=
  DocNode.xref head :: DocNode.punct "[".toList :: (inner ++ [DocNode.punct "]".toList])

/- Deep model (A-reference) of rendering a parametrised type whose arguments are
   constant values, on the domain this signature uses. The head is a navigable
   cross-reference; each constant argument is shown as PLAIN DISPLAY TEXT (its
   `reprVal`), NOT as a cross-reference — a constant value is not a class, so it
   carries no navigable reference. Validated == the real renderer over this
   domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def expandLiteral (head : List Char) (values : List LitVal) : List DocNode :=
  wrap head (valSeq DocNode.text reprVal values)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

method literalTypeNodes (head : List Char) (values : List LitVal)
    return (out : List DocNode)
  require head = "Literal".toList ∨ head = "typing.Literal".toList
  require values ≠ []
  require values.all okLit
  ensures out = expandLiteral head values
  do
    -- impl-start
    -- The head renders as a navigable cross-reference; the bracketed argument
    -- list is built by `valSeq`, where each constant value becomes a PLAIN
    -- display-text node carrying its source representation (`reprVal`). Because
    -- the value nodes are plain text — not cross-references — a constant such as
    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
    -- the same constants through the cross-reference path, so each value became
    -- a navigable reference; the frozen spec requires plain text, so that
    -- pre-image fails prove_correct.)
    let inner := valSeq DocNode.text reprVal values
    let result := wrap head inner
    return result
    -- impl-end

prove_correct literalTypeNodes by
  loom_solve
  rfl
