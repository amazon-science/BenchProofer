import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The label identifier is read directly from the widget's
--  own recorded attributes by a total association lookup; that lookup is an
--  ordinary concrete operation (I) bridged by the type bijection (R) in
--  mapping.md, mechanically refuted by conformance_check.py (G-CONF). No callee
--  is over-approximated, so no `axiom` is owed (directive 7).)
-- axioms-end

-- pure-start
/- The recorded attributes of a single rendered widget: an ordered association
   of string attribute names to string values. Modeled as an ordered list of
   key/value pairs (mapping.md §2). A given attribute name occurs at most once,
   mirroring a mapping keyed by attribute name. -/
abbrev Attrs := List (String × String)

/- The identifier recorded for a widget under its `"id"` attribute, if one was
   recorded — otherwise absent. This is a total lookup over the recorded
   attributes: it yields the recorded value when an `"id"` attribute is present,
   and the absent value when it is not. -/
def recordedId (attrs : Attrs) : Option String :=
  attrs.lookup "id"

@[grind] lemma recordedId_eq (attrs : Attrs) :
    recordedId attrs = attrs.lookup "id" := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The identifier to use when rendering a label that points at one rendered
   widget. The desired behavior is that this identifier is exactly the one
   already recorded in the widget's own attributes under `"id"` — the identifier
   the widget itself was (or would be) rendered with — and is absent precisely
   when no such identifier was recorded. It must therefore reflect whatever
   identifier the surrounding rendering recorded for this widget (including any
   caller-chosen prefix), rather than being synthesized independently from the
   widget's other recorded data.

   `name`, `index`, and `attrs` are the widget's recorded data (its field name,
   its position among sibling widgets, and its recorded attributes); all three
   are read-only — none is declared `mut` (directive 5). The result depends only
   on the recorded attributes. -/
method labelIdentifier (name : String) (index : String) (attrs : Attrs)
    return (out : Option String)
  ensures out = recordedId attrs
  do
    -- impl-start
    -- Pre-image skeleton: the identifier is SYNTHESIZED from the widget's name
    -- and position ("id_<name>_<index>"), independently of what identifier the
    -- surrounding rendering actually recorded in `attrs`. The frozen spec
    -- requires the recorded `"id"` attribute, so prove_correct MUST fail (it
    -- differs whenever a prefix was recorded, and is `some _` where the recorded
    -- id is absent).
    return some ("id_" ++ name ++ "_" ++ index)
    -- impl-end

prove_correct labelIdentifier by
  loom_solve
  simp [recordedId]
