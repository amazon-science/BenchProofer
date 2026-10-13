import Mathlib
-- imports-end

/-!
Normalizing a sequence of documented item entries.

A documentation block describes a list of items. Each raw entry, as read from the
block, is a triple `(name, type, description)`: a name (a sequence of characters),
a type (a sequence of characters), and a description (a sequence of text lines).

Producing the normalized entry list applies, to each raw entry in order, one rule:

* When grouping is enabled and the entry has a non-empty name, the name may itself
  denote several items written together and separated by commas (for example a
  single line introducing `a, b`). Such an entry expands into one normalized entry
  per comma-separated piece: each piece, with surrounding blank characters removed,
  paired with the shared type and the shared description.
* Otherwise the entry is kept as a single normalized entry, provided it carries
  some content (a non-empty name, type, or description); a wholly empty entry
  contributes nothing.

The normalized list is the in-order concatenation of every raw entry's expansion.
-/

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. The reading of raw entries and
-- the detection of the block boundary are unchanged bookkeeping and are abstracted
-- into the input list `raws`. The two character-level operations the rule performs
-- (separating a name on commas, and trimming surrounding blank characters) are
-- modeled directly in the `pure` region and differential-tested against their real
-- library counterparts by conformance_check.py. No consumed axioms.
-- axioms-end

-- pure-start
/-- A raw / normalized documented item entry: a name, a type, and a description
(a list of text lines). -/
abbrev FieldEntry := List Char × List Char × List (List Char)

/-- Blank characters trimmed from the ends of a separated name piece: exactly the
code points Python's bare `str.strip()` removes (the `str.isspace` set) —
U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028,
U+2029, U+202F, U+205F, and U+3000. -/
def isBlank (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) ||
  n == 0x2028 || n == 0x2029 || n == 0x202f || n == 0x205f || n == 0x3000

/-- Remove leading and trailing blank characters from a sequence. -/
def trim (cs : List Char) : List Char :=
  ((cs.dropWhile isBlank).reverse.dropWhile isBlank).reverse

/-- Separate a name into the comma-delimited pieces it is written as. A name with
no comma yields the single piece `[name]`; each comma starts a new piece, so an
empty piece is produced for an absent segment (mirroring delimiter-based string
splitting, which always yields at least one piece). -/
def commaPieces : List Char → List (List Char)
  | [] => [[]]
  | ',' :: cs => [] :: commaPieces cs
  | c :: cs =>
    match commaPieces cs with
    | h :: t => (c :: h) :: t
    | [] => [[c]]

/-- Expansion of one raw entry into its normalized entries, under the grouping
flag. With grouping and a non-empty name, the name is separated on commas and each
trimmed piece becomes an entry with the shared type and description; otherwise a
single entry is kept iff it has any content. -/
def expandEntry (splitGrouped : Bool) (f : FieldEntry) : List FieldEntry :=
  let (name, typ, desc) := f
  if splitGrouped && (name != []) then
    (commaPieces name).map (fun piece => (trim piece, typ, desc))
  else if (name != []) || (typ != []) || (desc != []) then
    [(name, typ, desc)]
  else
    []
-- pure-end

-- post-conditions-start
/-- The normalized entry list is the in-order concatenation of every raw entry's
expansion under the grouping flag. -/
def problem_spec_normalizeEntries
    (splitGrouped : Bool) (raws : List FieldEntry) (result : List FieldEntry) : Prop :=
  result = raws.flatMap (expandEntry splitGrouped)
-- post-conditions-end

-- impl-start
def implementation_normalizeEntries
    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry := Id.run do
  -- Pre-patch behavior: the grouping flag is never honored; every entry with any
  -- content is kept whole, so a name denoting several comma-separated items is
  -- emitted as one combined entry instead of being split.
  let mut fields : List FieldEntry := []
  for f in raws do
    let (name, typ, desc) := f
    if (name != []) || (typ != []) || (desc != []) then
      fields := fields ++ [(name, typ, desc)]
  return fields
-- impl-end

-- proof-start
-- Gold proof body to be carried over from Solution.lean (SPEC_GUIDE §1.1). Against
-- this pre-patch implementation it cannot close: when `splitGrouped` is `true` and
-- a raw entry's name contains a comma, the specification requires one entry per
-- trimmed comma-separated piece, while this implementation emits the whole name as
-- a single entry — the discriminating clause.
theorem correct_normalizeEntries :
    ∀ (splitGrouped : Bool) (raws : List FieldEntry),
      problem_spec_normalizeEntries splitGrouped raws
        (implementation_normalizeEntries splitGrouped raws) := by
  sorry
-- proof-end
