import Mathlib
-- imports-end

/-!
Rendering of a single documented-variable info-field item into the inline
node sequence that appears in the field body.

An item carries a name, an optional type token, and a description fragment.
The renderer emits, in order: the name token, then — when a type is present —
a parenthesized type token (linkable via the type cross-reference role), then a
separator, then the description.

A *cross-reference role* is the rule that decides whether a token is wrapped in
a navigable cross-reference or emitted as a plain strong/emphasis token: an
empty role yields a plain token; a non-empty role wraps the plain token in a
cross-reference carrying that role as its reference type.

For a documented variable, the name token must stand on its own — it is not a
navigable cross-reference to anything else — while its type token remains a
class cross-reference. The renderer applies the variable name role and the type
role accordingly.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The role-application helper
-- `makeXref` below is modeled deeply (A-reference, validated against the real
-- callee by G-AX), so no `opaque`/`axiom` declarations are required.
-- axioms-end

-- pure-start

/-- An inline node in the rendered field body. -/
inductive RenderNode where
  | text   : String → RenderNode
  | strong : String → RenderNode
  | emph   : String → RenderNode
  | xref   : String → RenderNode → RenderNode
  deriving DecidableEq, Repr

/-- Apply a cross-reference role to a plain inline token.
An empty role leaves the token plain; a non-empty role wraps it in a
cross-reference whose reference type is the role. Mirrors the unchanged
role-application callee (A-reference; G-AX validated). -/
def makeXref (role : String) (plain : RenderNode) : RenderNode :=
  if role = "" then plain else RenderNode.xref role plain

/-- The cross-reference role applied to a documented variable's TYPE token.
This is unchanged: a type token always links to its class. -/
def variableTypeRole : String := "class"

-- pure-end

-- post-conditions-start
/-- Specification of rendering one documented-variable item.

`name` is the variable name, `type?` the optional type token, `content` the
description fragment. The result must be exactly: a PLAIN strong name token
(the variable name is NOT a navigable cross-reference), followed — only when a
type is present — by `" ("`, the type token rendered as a class cross-reference
over an emphasis token, `")"`, then the separator `" -- "` and the description;
and when no type is present, just the plain name token, separator and
description. Every component is pinned to its input (frame discipline): exact
order, no extra nodes, and the name token carries no cross-reference. -/
def problem_spec_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode)
    (result : List RenderNode) : Prop :=
  result =
    RenderNode.strong name ::
      (match type? with
       | some t =>
           RenderNode.text " (" ::
             RenderNode.xref variableTypeRole (RenderNode.emph t) ::
             RenderNode.text ")" :: RenderNode.text " -- " :: content
       | none => RenderNode.text " -- " :: content)
-- post-conditions-end

-- impl-start
def implementation_renderVariableItem
    (name : String) (type? : Option String) (content : List RenderNode) :
    List RenderNode := Id.run do
  -- The configured cross-reference role for a variable NAME (empty: no link).
  let nameRole : String := "obj"
  let mut par : List RenderNode := []
  par := par ++ [makeXref nameRole (RenderNode.strong name)]
  match type? with
  | some t =>
      par := par ++ [RenderNode.text " ("]
      par := par ++ [makeXref variableTypeRole (RenderNode.emph t)]
      par := par ++ [RenderNode.text ")"]
  | none => pure ()
  par := par ++ [RenderNode.text " -- "]
  par := par ++ content
  return par
-- impl-end

-- proof-start
theorem correct_renderVariableItem :
    ∀ (name : String) (type? : Option String) (content : List RenderNode),
      problem_spec_renderVariableItem name type? content
        (implementation_renderVariableItem name type? content) := by
  intro name type? content
  cases type? with
  | none => rfl
  | some t => rfl
-- proof-end
