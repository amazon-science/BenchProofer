import Mathlib
-- imports-end

/-!
Building the inline nodes that render a documented property's *type annotation*
in its signature.

When a documented property carries a declared type, the signature gains a small
annotation fragment introduced by a `": "` separator and followed by the rendered
type. There are two ways the type text after the separator can be rendered:

  * as a single, inert run of plain text (the type name is shown but is not made
    navigable), or
  * parsed into a sequence of inline nodes in which type names become
    cross-reference-aware nodes (so a documented type becomes a navigable
    cross-reference).

The behavior pinned below builds the annotation fragment in the second form: the
`": "` separator as its own plain-text node, immediately followed — in order — by
the nodes obtained from parsing the declared type string. When the property
declares no type at all, no annotation fragment is produced.

The type-parsing step itself (turning an annotation string into a list of inline
nodes) is the SAME operation regardless; here it is taken as an arbitrary function
of the type string, so the behavior pinned below is exactly "the separator text
node, then the parsed type nodes, in that order."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Inline nodes are modeled
-- by an arbitrary carrier type `Node` with one known constructor `mkText`
-- (the plain-text-node factory). The annotation-parsing step (turning a type
-- string into a list of inline nodes) is modeled as an arbitrary function
-- parameter `crossRefParser : String → List Node`: the modeled change is solely
-- WHICH children are assembled (and in WHICH order), so the result is pinned for
-- every possible parser. Hence the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the annotation fragment is the
-- separator text node consed onto the parsed-type node list.
-- pure-end

-- post-conditions-start
/-- The annotation fragment is fully pinned to the inputs:

  * when the property declares a (non-empty) type string, the fragment is exactly
    the `": "` separator as a plain-text node, followed in order by the nodes the
    type-parsing step produces from that string;
  * when no type is declared, no fragment is produced (the empty node list).

No output component is left free: in the present-type case the head is pinned to
the separator text node and the tail to the parser's output, and the empty case
is pinned to the empty list. -/
def problem_spec_propertyTypeAnnotation
    {Node : Type}
    (mkText : String → Node) (crossRefParser : String → List Node)
    (typ : String) (result : List Node) : Prop :=
  (typ ≠ "" → result = mkText ": " :: crossRefParser typ) ∧
  (typ = "" → result = [])
-- post-conditions-end

-- impl-start
def implementation_propertyTypeAnnotation
    {Node : Type}
    (mkText : String → Node) (crossRefParser : String → List Node)
    (typ : String) : List Node := Id.run do
  -- PRE-PATCH (buggy): the declared type is emitted as a SINGLE plain-text node
  -- carrying the whole `": " ++ typ` run, so the type text is inert (never parsed
  -- into cross-reference-aware nodes). The parser's output is discarded.
  let mut children : List Node := []
  if typ ≠ "" then
    children := [mkText (": " ++ typ)]
  return children
-- impl-end

-- proof-start
theorem correct_propertyTypeAnnotation :
    ∀ {Node : Type} (mkText : String → Node) (crossRefParser : String → List Node)
      (typ : String),
      problem_spec_propertyTypeAnnotation mkText crossRefParser typ
        (implementation_propertyTypeAnnotation mkText crossRefParser typ) := by
  intro Node mkText crossRefParser typ
  unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h; simp [h]
  · intro h; simp [h]
-- proof-end
