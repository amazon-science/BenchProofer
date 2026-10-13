import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The rendering decision that turns a documented field's
   argument into a node — emit a cross-reference when a reference role is
   configured for that argument, otherwise emit a plain inline text node — is
   modeled DEEPLY in the `pure` region (`crossRefOrText`). It is the faithful
   model of an UNCHANGED standard inline-rendering helper, validated against the
   real helper by axiom_check.py (G-AX) as a deep-model reference (mapping.md
   §3); there is no module-level `axiom` the proof consumes. -/
-- axioms-end

-- pure-start
/- The two shapes an inline node can take in a rendered documentation field
   entry. `text` is a plain inline node carrying its content verbatim (no
   navigation target attached); `xref` is a pending cross-reference of a given
   reference kind to a target. The only distinction the desired behaviour cares
   about is whether a navigable cross-reference was produced (mapping.md §2). -/
inductive RefNode where
  | text (content : List Char)
  | xref (refkind : List Char) (target : List Char)
  deriving DecidableEq

/- The rendering decision for one argument of a documentation field: if a
   non-empty reference role is configured for that argument, the argument is
   turned into a pending cross-reference of that kind to itself; otherwise it is
   emitted as a plain inline text node with no navigation target. This is the
   standard inline-rendering rule (deep model of an unchanged helper, mapping.md
   §3.1). -/
def crossRefOrText (refrole : Option (List Char)) (target : List Char) : RefNode :=
  match refrole with
  | none   => RefNode.text target
  | some r => if r = [] then RefNode.text target else RefNode.xref r target

/- A plain-name character: a letter, a digit or an underscore. Pins the modeled
   input domain to simple one-word names/types (e.g. `attr`, `int`, `MyClass`).
   Composite type expressions (bracketed/comma/'or'-joined lists of types),
   abbreviation-prefixed targets (leading '.'/'~') and the literal word `None`
   are rendered through unchanged list-splitting / prefix-stripping /
   special-casing machinery that is orthogonal to this change and produces a
   different entry shape, so they are outside the modeled domain (mapping.md
   §2). -/
def isIdentChar (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'
-- pure-end

/- The observable content of one rendered entry of an info field documenting a
   named item together with its type: the node produced for the item's NAME and
   the node produced for its TYPE. These are the only parts of the entry whose
   shape the desired behaviour constrains (mapping.md §2). -/
structure FieldEntry where
  nameNode : RefNode
  typeNode : RefNode
  deriving DecidableEq

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render one entry of an info field that documents a named item of a class
   together with its declared type — e.g. an entry like "an integer-typed item
   `name`". The modeled domain (the `require` clauses) is an entry whose NAME
   and TYPE are simple one-word identifiers, the TYPE not being the literal
   word `None` (see `isIdentChar`). Desired behaviour: the item NAME must be
   emitted as plain text with NO cross-reference, so that documenting an item
   inside a class never produces a spurious navigation link to an unrelated,
   identically-named item elsewhere in the project; the declared TYPE, by
   contrast, must remain a cross-reference to a class so that the type stays
   navigable. -/
method renderFieldEntry (name : List Char) (typ : List Char) return (out : FieldEntry)
  require name ≠ []
  require ∀ c ∈ name, isIdentChar c
  require typ ≠ []
  require ∀ c ∈ typ, isIdentChar c
  require typ ≠ "None".toList
  ensures out.nameNode = RefNode.text name
  ensures out.typeNode = RefNode.xref "class".toList typ
  do
    -- impl-start
    -- Pre-image skeleton: the item NAME carries a generic object reference role,
    -- so it is rendered as a cross-reference (a navigable link) rather than
    -- plain text. The frozen spec requires the NAME to be plain text, so
    -- prove_correct MUST fail on the name clause.
    let nameRole : Option (List Char) := some "obj".toList
    let typeRole : Option (List Char) := some "class".toList
    let nameNode := crossRefOrText nameRole name
    let typeNode := crossRefOrText typeRole typ
    return { nameNode := nameNode, typeNode := typeNode }
    -- impl-end

prove_correct renderFieldEntry by
  loom_solve <;> simp [crossRefOrText]
