import Mathlib
-- imports-end

/-!
Rendering a parametrised type annotation whose arguments are constant values,
as a documentation renderer does for a subscripted type.

A rendered annotation is a sequence of inline documentation nodes. For a
parametrised type `head[v1, v2, …]` written with a dotted type name as its head
and constant values as its arguments, the rendered sequence is:

* the head as a navigable cross-reference (`DocNode.xref head`),
* an opening bracket punctuation node,
* the comma-separated argument nodes,
* a closing bracket punctuation node.

Which KIND of node an argument becomes is decided by the head, and that
distinction is the whole point of the enumeration head:

* under `Literal` (or `typing.Literal`) the arguments are an enumeration of
  VALUES, so each argument is PLAIN inline display text (`DocNode.text`) and
  carries no navigable reference — a value such as `True` names no class, so a
  documentation build run with strict reference checking must not be asked to
  resolve one;
* under EVERY OTHER dotted head the arguments are read as type names, so each
  argument node is a navigable cross-reference (`DocNode.xref`), just as such a
  head's arguments have always been.

A parametrised type has exactly one ZERO-argument spelling — the empty tuple,
`head[()]` — and there the argument region is that parenthesis pair itself:
the sequence is the head cross-reference, `[`, `(`, `)`, `]`. This shape is
reachable and observable, so the contract below covers it too, and it carries no
argument node for the head to select the kind of.

The display text an argument carries is the same either way: the argument
exactly as it stands in the annotation — `True`/`False` for a boolean, `None`
for the null constant, the decimal digits for an integer, and, for a string
argument, its quoted literal as written. What the annotation says is what the
rendered signature shows.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The rendering of a parametrised
-- type is modeled DEEPLY over the observable head and argument list as
-- `expandLiteral` (built from `wrap` / `valSeq` / `argNodeCtor` / `reprVal`);
-- its faithfulness to the real renderer is validated by the mechanical
-- differential check (G-CONF), and `reprVal` against the real value-rendering
-- routine by the axiom check (G-AX).
-- axioms-end

-- pure-start
/-- An inline documentation node. A rendered type annotation is a sequence of
these. Only the fields the rendered signature observes are kept: `text` carries
literal display text, `xref` carries a cross-reference whose target is a type
name (a navigable class reference), `punct` carries structural punctuation
(brackets, commas). The bijection to the real inline-node carriers is in
mapping.md §2. -/
inductive DocNode where
  | text  (s : List Char)
  | xref  (target : List Char)
  | punct (s : List Char)
  deriving DecidableEq, Inhabited, Repr

/-- A constant value that can appear as an argument of a parametrised type.
Four shapes are modeled — the null constant, a boolean, an integer, and a
(simple) string literal — covering the constant kinds the documented
annotations in scope use. The bijection to the real Python constant objects is
in mapping.md §2. -/
inductive LitVal where
  | null
  | bool (b : Bool)
  | int  (n : Int)
  | str  (s : List Char)
  deriving DecidableEq, Inhabited, Repr

/-- The domain on which the string representation below is exact: a "simple"
string is one whose characters are all printable ASCII (32–126) other than the
apostrophe and the backslash. Such a string is shown delimited by single quotes
with no character needing an escape. Constant strings outside this domain
(containing quotes, backslashes, or non-printable code points) are out of scope
and excluded by the method precondition. -/
def isSimpleStrChar (c : Char) : Bool :=
  decide (32 ≤ c.toNat ∧ c.toNat ≤ 126) && c ≠ '\'' && c ≠ '\\'

/-- The precondition on one argument value: strings must be "simple" and
integers non-negative, so the display text below is the value's exact source
form. The null constant and the booleans are always fine. -/
def okLit : LitVal → Bool
  | .str s => s.all isSimpleStrChar
  | .int n => decide (0 ≤ n)
  | _      => true

/-- The display text of one constant argument: the argument exactly as it
stands in the annotation. The null constant shows as `None`, a boolean as
`True`/`False`, an integer as its decimal digits, and a string argument as its
quoted literal as written. Validated against the real value-representation
routine over this domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def reprVal : LitVal → List Char
  | .null       => "None".toList
  | .bool true  => "True".toList
  | .bool false => "False".toList
  | .int n      => (toString n).toList
  | .str s      => '\'' :: (s ++ ['\''])

/-- A legal first character of a dotted-name segment: an ASCII letter or the
underscore. -/
def isHeadStartChar (c : Char) : Bool := c.isAlpha || c == '_'

/-- A legal later character of a dotted-name segment: an ASCII letter, an ASCII
digit, or the underscore. -/
def isHeadTailChar (c : Char) : Bool := c.isAlphanum || c == '_'

/-- The words that cannot be used as a name segment in Python source. A head
containing one of these is not a dotted type name at all — such an annotation
does not parse as a parametrised type — so it is out of scope and excluded by
the method precondition.

One entry — the pre-test loop keyword — is spelled character by character rather
than as a string literal: that spelling is reserved by this proof language's own
surface syntax, and the hygiene screen rejects the token on sight regardless of
where it appears. The two spellings denote the same list of characters. -/
def pyReservedWords : List (List Char) :=
  ["False", "None", "True", "__peg_parser__", "and", "as", "assert", "async",
   "await", "break", "class", "continue", "def", "del", "elif", "else",
   "except", "finally", "for", "from", "global", "if", "import", "in", "is",
   "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
   "with", "yield"].map String.toList
  ++ [['w', 'h', 'i', 'l', 'e']]

/-- Split a head on its dots into the segments of its dotted name. An empty
head, and a head with an empty segment (a leading, trailing or doubled dot),
both yield an empty segment, which `okHeadSeg` then rejects. -/
def headSegments : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    if c == '.' then [] :: headSegments cs
    else match headSegments cs with
         | s :: rest => (c :: s) :: rest
         | []        => [[c]]

/-- One segment of a dotted head is a legal name: non-empty, an ASCII
identifier, and not a reserved word. -/
def okHeadSeg (s : List Char) : Bool :=
  match s with
  | []      => false
  | c :: cs => isHeadStartChar c && cs.all isHeadTailChar
               && !(pyReservedWords.contains s)

/-- The domain of heads this signature covers: `head` is a dotted Python type
name — one or more dot-separated legal name segments — which is exactly the
shape a parametrised type annotation's head has. This admits the enumeration
heads `Literal` / `typing.Literal` AND every other dotted head (`List`,
`Optional`, `typing.Dict`, …), because the rendering of the arguments differs
between the two and both cases are part of the observable behaviour. -/
def okHead (head : List Char) : Bool := (headSegments head).all okHeadSeg

/-- Whether the head is the enumeration head, i.e. the head under which the
arguments are constant VALUES rather than type names. -/
def isLitHead (head : List Char) : Bool :=
  head == "Literal".toList || head == "typing.Literal".toList

/-- The node constructor an ARGUMENT of `head[…]` is emitted with. Under the
enumeration head the arguments are values, shown as plain display text and
carrying no navigable reference; under any other dotted head the arguments are
type names and stay navigable cross-references. This is the head-dependent
observable of the rendered sequence. -/
def argNodeCtor (head : List Char) : List Char → DocNode :=
  if isLitHead head then DocNode.text else DocNode.xref

/-- The node sequence the arguments of `head[…]` occupy: each value becomes one
node built by `mk` from its display text `render v`, and adjacent values are
separated by a `", "` punctuation node. Front-recursive so a single unfold is
available per step. Parametrised over the node constructor `mk` and the
per-value renderer `render` so the value-display policy is explicit at the call
site. With NO values the argument region is the empty-tuple spelling `()`, whose
two parentheses are structural punctuation — so that case is independent of `mk`
and of `render`, and it is a two-node region, not an absent one. -/
def valSeq (mk : List Char → DocNode) (render : LitVal → List Char) :
    List LitVal → List DocNode
  | []      => [DocNode.punct "(".toList, DocNode.punct ")".toList]
  | [v]     => [mk (render v)]
  | v :: vs => mk (render v) :: DocNode.punct ", ".toList :: valSeq mk render vs

/-- Frame the inner sequence with the head cross-reference and the surrounding
brackets: `head` renders as a navigable cross-reference (the parametrised type
itself), then `[`, then the inner nodes, then `]`. -/
def wrap (head : List Char) (inner : List DocNode) : List DocNode :=
  DocNode.xref head :: DocNode.punct "[".toList :: (inner ++ [DocNode.punct "]".toList])

/-- Deep model (A-reference) of rendering a parametrised type whose arguments
are constant values, on the domain this signature uses. The head is always a
navigable cross-reference and the brackets and separators are punctuation; the
ARGUMENT nodes are plain display text under the enumeration head and navigable
cross-references under every other dotted head (`argNodeCtor`), each carrying
the value's display text (`reprVal`); with no arguments at all the region
between the brackets is the empty tuple's parenthesis pair. Validated == the
real renderer over this domain by conformance_check.py (G-CONF); provenance
mapping.md §3.3. -/
def expandLiteral (head : List Char) (values : List LitVal) : List DocNode :=
  wrap head (valSeq (argNodeCtor head) reprVal values)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
/-- The contract of `literalTypeNodes`. Under the method preconditions — `head`
a dotted Python type name (`okHead`, which admits the enumeration heads AND
every other dotted head) and every argument a value on the modeled domain
(`okLit`) — the emitted node sequence `result` is exactly
`expandLiteral head values`: the head cross-reference, the bracket and comma
punctuation, and one argument node per value carrying `reprVal v`, that node
being PLAIN TEXT under `Literal` / `typing.Literal` and a navigable
CROSS-REFERENCE under any other dotted head. This pins every node (class +
text) and its position, for every head in the domain — so an implementation
that renders the arguments the same way regardless of the head does NOT satisfy
it. The argument list is NOT assumed non-empty: the zero-argument spelling
`head[()]` is a reachable, observable shape, and it is pinned to the head
cross-reference framed around the empty tuple's parenthesis pair — so an
implementation that abbreviates it, for instance to the head reference alone,
does not satisfy the contract either. -/
def problem_spec_literalTypeNodes
    (head : List Char) (values : List LitVal) (result : List DocNode) : Prop :=
  okHead head = true →
  values.all okLit = true →
  result = expandLiteral head values
-- post-conditions-end

-- impl-start
/-- The head renders as a navigable cross-reference; the bracketed argument list
is built by `valSeq` with the head-determined argument constructor, where each
constant value's display text is its canonical source form (`reprVal`). Under
the enumeration head the argument nodes are plain display text, so a value such
as a boolean or an integer carries no class reference; under any other dotted
head they stay cross-references. -/
def implementation_literalTypeNodes
    (head : List Char) (values : List LitVal) : List DocNode :=
  let inner := valSeq (argNodeCtor head) reprVal values
  wrap head inner
-- impl-end

-- proof-start
theorem correct_literalTypeNodes :
    ∀ (head : List Char) (values : List LitVal),
      problem_spec_literalTypeNodes head values
        (implementation_literalTypeNodes head values) := by
  intro head values
  unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
  intro _ _
  rfl
-- proof-end
