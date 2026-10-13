import Mathlib
-- imports-end

/-!
Normalizing the indentation of a multi-line block of text.

The routine takes a block of text already split into lines (tab stops having
been expanded beforehand) and returns the block with its indentation uniformly
normalized, following the conventional rule for laying out indented text blocks:

* the first line is stripped of all of its leading whitespace;
* a single common indentation amount is determined as the smallest number of
  leading whitespace characters occurring on any non-blank line *among the lines
  that follow the first*; every line after the first then has exactly that many
  leading characters removed (lines after the first keep whatever indentation
  they have in excess of the common amount);
* if there is no non-blank line after the first, the lines after the first are
  left untouched;
* finally, completely empty lines are removed from the end of the block and then
  from the beginning of the block.

A blank line (a line whose characters are all whitespace) does not contribute to
the common indentation amount, but only a *completely empty* line (no characters
at all) is eligible for removal at the ends.

"Whitespace" here follows the ambient string library's notion of a whitespace
character (space, the various separators, no-break and other Unicode spaces),
not merely the ASCII space.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Splitting the text into
-- lines and rejoining them, and expanding tab stops, happen outside this routine
-- and are supplied/consumed at the boundary; the indentation-normalization logic
-- itself is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The whitespace code points recognized by the ambient string library's
whitespace predicate (the same set its left-strip operation removes). Kept as an
explicit table so the model matches that predicate exactly rather than only the
ASCII space. -/
def whitespaceCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20,
   0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
   0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

/-- Whether a character is whitespace under the ambient predicate. -/
def isSpaceChar (c : Char) : Bool := whitespaceCodes.contains c.toNat

/-- Number of leading whitespace characters on a line. -/
def leadingWs (l : List Char) : Nat := (l.takeWhile isSpaceChar).length

/-- A line with its leading whitespace removed. -/
def lstripWs (l : List Char) : List Char := l.dropWhile isSpaceChar

/-- A line is blank when it has no non-whitespace content. -/
def isBlank (l : List Char) : Bool := (lstripWs l).isEmpty

/-- The common indentation amount: the least leading-whitespace count over the
non-blank lines of `rest`, or `none` when `rest` has no non-blank line. -/
def marginSpec (rest : List (List Char)) : Option Nat :=
  rest.foldl (fun m line =>
    if isBlank line then m
    else some (match m with
               | none   => leadingWs line
               | some k => Nat.min k (leadingWs line))) none

/-- Strip the first line's leading whitespace and dedent every following line by
the common margin (or leave them untouched when there is no common margin). -/
def dedentSpec (margin : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match lines with
  | []            => []
  | first :: rest =>
    lstripWs first :: (match margin with
                       | none   => rest
                       | some m => rest.map (·.drop m))

/-- Drop completely empty lines from the end of the block. -/
def dropTrailingEmpty (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (· == ([] : List Char))).reverse

/-- Drop completely empty lines from the beginning of the block. -/
def dropLeadingEmpty (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (· == ([] : List Char))

/-- Functional reference for indentation normalization. -/
def normalizeIndentSpec (lines : List (List Char)) : List (List Char) :=
  dropLeadingEmpty (dropTrailingEmpty
    (dedentSpec (marginSpec (lines.drop 1)) lines))
-- pure-end

-- post-conditions-start
/-- Input→output relation for indentation normalization. `lines` is the block of
text already split into lines; `result` is the normalized block. The result is
exactly the normalized block produced by the rule above. -/
def problem_spec_normalizeIndent (lines : List (List Char))
    (result : List (List Char)) : Prop :=
  result = normalizeIndentSpec lines
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton: the common indentation amount is measured over EVERY
-- non-blank line, INCLUDING the first one, instead of over the lines that follow
-- the first. When the first line begins flush-left (zero leading whitespace) the
-- common amount collapses to zero, so the following lines are not dedented at
-- all — contradicting the normalization rule on any block whose first line is
-- not indented but whose later lines are.
def implementation_normalizeIndent (lines : List (List Char)) :
    List (List Char) := Id.run do
  let mut margin : Option Nat := none
  for line in lines do
    if !isBlank line then
      let ind := leadingWs line
      margin := some (match margin with
                      | none   => ind
                      | some m => Nat.min m ind)
  let mut out : List (List Char) :=
    match lines with
    | []          => []
    | first :: _  => [lstripWs first]
  for line in lines.drop 1 do
    match margin with
    | none   => out := out ++ [line]
    | some m => out := out ++ [line.drop m]
  out := dropTrailingEmpty out
  out := dropLeadingEmpty out
  return out
-- impl-end

-- proof-start
theorem correct_normalizeIndent :
    ∀ (lines : List (List Char)),
      problem_spec_normalizeIndent lines
        (implementation_normalizeIndent lines) := by
  sorry
-- proof-end
