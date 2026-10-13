import Mathlib
-- imports-end

/-!
Rendering a mathematical symbol as MathML *presentation* markup.

A symbol is described by a base name together with two ordered collections of
decoration strings: its superscripts and its subscripts (each already reduced to
the string actually displayed). A rendering style flag may additionally request a
bold appearance.

The desired markup is a single tree of nodes. Each node is either a text leaf or
an element with a tag, a list of attributes, and an ordered list of child nodes.

The base name is rendered as an identifier element `mi` carrying the name as its
text. A collection of decoration strings is laid out as follows: a single string
becomes one identifier element `mi`; several strings become a row element `mrow`
holding the identifier elements in order, each consecutive pair separated by an
operator element `mo` whose text is a single space.

The whole symbol is assembled by combining the name element with its decorations:

* with neither superscripts nor subscripts the markup is exactly the name element;
* with subscripts only, the markup is a subscript element `msub` whose children
  are the name element followed by the laid-out subscripts;
* with superscripts only, the markup is a superscript element `msup` whose
  children are the name element followed by the laid-out superscripts;
* with both, the markup is a combined element `msubsup` whose children are the
  name element, then the laid-out subscripts, then the laid-out superscripts.

Finally, when the bold style is requested, the attribute `mathvariant="bold"` is
attached to the resulting top-level element.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Decomposing the
-- symbol name into its base, superscripts and subscripts, and translating each
-- piece, happen upstream and constitute the modeled inputs; the markup-node
-- constructors are modeled directly by the `MathNode` constructors. Everything is
-- spelled out DEEPLY over those inputs, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A MathML markup node: either a text leaf carrying its string value, or an
element with a tag, an ordered list of attributes (name/value pairs), and an
ordered list of child nodes. Mirrors a minidom node (`nodeName` / `childNodes` /
`nodeValue`; attributes via `setAttribute`). -/
inductive MathNode where
  | text (value : String)
  | elem (tag : String) (attrs : List (String × String)) (children : List MathNode)
  deriving Repr

/-- Attach an attribute (name, value) to an element node (appended after any
existing attributes); a text node is returned unchanged. -/
def MathNode.setAttr (n : MathNode) (k v : String) : MathNode :=
  match n with
  | .elem tag attrs children => .elem tag (attrs ++ [(k, v)]) children
  | .text s => .text s

/-- The child nodes for a multi-piece decoration row: the identifier elements in
order, with an operator-space element inserted before each piece after the first. -/
def joinSep : List String → List MathNode
  | [] => []
  | [x] => [MathNode.elem "mi" [] [MathNode.text x]]
  | x :: rest =>
      MathNode.elem "mi" [] [MathNode.text x]
        :: MathNode.elem "mo" [] [MathNode.text " "]
        :: joinSep rest

/-- Lay out a nonempty collection of decoration strings: several strings become a
row element holding the separated identifier elements; a single string becomes
one identifier element. -/
def joinPieces (items : List String) : MathNode :=
  if items.length > 1 then
    MathNode.elem "mrow" [] (joinSep items)
  else
    MathNode.elem "mi" [] [MathNode.text (items.headD "")]

/-- Assemble the presentation markup for a symbol from its base name, its
superscript and subscript collections, and the rendering style. -/
def buildSymbolMarkup (name : String) (supers subs : List String)
    (style : String) : MathNode :=
  let mname := MathNode.elem "mi" [] [MathNode.text name]
  let x :=
    if supers.length == 0 then
      if subs.length == 0 then
        mname
      else
        MathNode.elem "msub" [] [mname, joinPieces subs]
    else
      if subs.length == 0 then
        MathNode.elem "msup" [] [mname, joinPieces supers]
      else
        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
  if style == "bold" then x.setAttr "mathvariant" "bold" else x
-- pure-end

-- post-conditions-start
/-- The produced markup is exactly the tree dictated by the rule above: the right
choice of top-level element for the present decorations, its children in the
required order, and the bold attribute present exactly when the bold style is
requested. -/
def problem_spec_symbolMarkup (name : String) (supers subs : List String)
    (style : String) (result : MathNode) : Prop :=
  result = buildSymbolMarkup name supers subs style
-- post-conditions-end

-- impl-start
def implementation_symbolMarkup (name : String) (supers subs : List String)
    (style : String) : MathNode := Id.run do
  -- Pre-patch behavior: a top-level identifier element is always allocated, the
  -- bold attribute (if any) is attached to it up front, and the decorated piece
  -- (or the bare name text) is then placed INSIDE it as a child — so every result
  -- is wrapped in an extra identifier element.
  let mut x := MathNode.elem "mi" [] []
  if style == "bold" then
    x := x.setAttr "mathvariant" "bold"
  let mname := MathNode.elem "mi" [] [MathNode.text name]
  let inner :=
    if supers.length == 0 then
      if subs.length == 0 then
        MathNode.text name
      else
        MathNode.elem "msub" [] [mname, joinPieces subs]
    else
      if subs.length == 0 then
        MathNode.elem "msup" [] [mname, joinPieces supers]
      else
        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
  x := match x with
    | .elem tag attrs children => .elem tag attrs (children ++ [inner])
    | t => t
  return x
-- impl-end

-- proof-start
theorem correct_symbolMarkup :
    ∀ (name : String) (supers subs : List String) (style : String),
      problem_spec_symbolMarkup name supers subs style
        (implementation_symbolMarkup name supers subs style) := by
  intro name supers subs style
  unfold problem_spec_symbolMarkup implementation_symbolMarkup buildSymbolMarkup
  rfl
-- proof-end
