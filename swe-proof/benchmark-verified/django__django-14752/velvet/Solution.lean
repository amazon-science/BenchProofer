import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The per-item serialization is an injected, caller-
--  overridable operation modeled as an arbitrary total function `serialize`;
--  the result postcondition holds for EVERY such function, so it owes no
--  contract and is strictly weaker than any concrete serializer (directive 7).
--  The default serialization is modeled DEEPLY in the `pure` region. There is
--  no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The observable content of one source item that the default serialization
   reads: its chosen identifier rendered as text, and its own display text.
   These two renderings are taken as given observables of the item; the desired
   behavior does not change how either is computed (mapping.md §2). -/
structure Item where
  idText : String
  displayText : String
  deriving DecidableEq, Inhabited

/- A serialized result: an ordered association of string field names to string
   values — the object produced for one item. Modeled as an ordered list of
   key/value pairs so that additional fields may be present beyond the defaults
   (the customization the desired behavior must allow). -/
abbrev Serialized := List (String × String)

/- The default serialization of one item: an object carrying exactly the
   identifier field and the display-text field, in that order. -/
def defaultSerialized (it : Item) : Serialized :=
  [("id", it.idText), ("text", it.displayText)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The default per-item serialization: convert one source item into the result
   object for that item. It carries exactly the identifier field and the
   display-text field, in that order. `it` is read-only (not `mut`); the step
   constructs a fresh result and mutates nothing (directive 5). -/
method serializeResult (it : Item) return (out : Serialized)
  ensures out = defaultSerialized it
  do
    -- impl-start
    return [("id", it.idText), ("text", it.displayText)]
    -- impl-end

prove_correct serializeResult by
  loom_solve
  simp [defaultSerialized]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the results list from a list of source items by applying a single
   injected per-item serialization to each item, preserving order. The
   serialization `serialize` is supplied by the caller (its default is
   `serializeResult`); building the list applies whichever serialization is in
   effect to EVERY item — so a caller-supplied serialization takes effect for
   every result, and the count and order of the results equal those of the
   items. `items` and `serialize` are read-only (not `mut`); the step builds a
   fresh list and mutates neither input (directive 5). -/
method buildResults (items : List Item) (serialize : Item → Serialized)
    return (out : List Serialized)
  ensures out = items.map serialize
  do
    -- impl-start
    let results := items.map serialize
    return results
    -- impl-end

prove_correct buildResults by
  loom_solve
