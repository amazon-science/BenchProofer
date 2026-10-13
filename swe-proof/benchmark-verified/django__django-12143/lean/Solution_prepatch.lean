import Mathlib
-- imports-end

/-!
Selecting submitted primary-key values for the editable rows of a tabular form.

A bulk-edit form submits its fields as a flat collection of `(key, value)` pairs.
Each editable row contributes one key that encodes the row's primary key, built
from three parts joined by hyphens:

  * a constant marker string identifying the form as a whole;
  * a run of one or more decimal digits giving the row's position; and
  * the name of the primary-key field.

This routine scans the submitted pairs, in their original order, and returns the
values of exactly those pairs whose key has this three-part shape for the given
marker and primary-key-field name.

The marker is treated as an ordinary literal string: a key qualifies precisely
when it begins with the marker character-for-character, followed by a hyphen,
then a non-empty block of decimal digits, then a hyphen, then the primary-key
field name, and then the end of the key (one final trailing line break is
tolerated there, mirroring the end-of-input rule of the matching engine). Every
character of the marker — whatever it may be — must appear verbatim at the front
of the key; the marker carries no special meaning of its own. A decimal digit
here is a digit of any decimal number system (the Unicode decimal digits,
general category Nd), not only the Latin `'0'..'9'`. The order of the surviving
values, and the values themselves, are preserved unchanged from the input.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed as an axiom. The submitted pairs are
-- supplied directly as the input `items`. The decision of whether one key
-- denotes an editable row's primary key for the given marker and field name is
-- modeled DEEPLY below (`matchesRowKey`, with the pure helpers `stripPrefix?`,
-- `isDecimalDigit`, and `atEnd`), so there is no `opaque`/`axiom` callee
-- contract. The deep model is validated against the real matching behavior by
-- the differential conformance check.
-- axioms-end

-- pure-start
/-- The decimal-digit code points the matching engine's digit class accepts:
the digits of every decimal number system (Unicode general category Nd, per
the Unicode data the modeled engine ships), as inclusive `(lo, hi)`
scalar-value bounds. The digit class is Unicode-aware, not restricted to the
Latin digits. -/
def digitRanges : List (Nat × Nat) :=
  [ (0x30, 0x39), (0x660, 0x669), (0x6f0, 0x6f9), (0x7c0, 0x7c9),
    (0x966, 0x96f), (0x9e6, 0x9ef), (0xa66, 0xa6f), (0xae6, 0xaef),
    (0xb66, 0xb6f), (0xbe6, 0xbef), (0xc66, 0xc6f), (0xce6, 0xcef),
    (0xd66, 0xd6f), (0xde6, 0xdef), (0xe50, 0xe59), (0xed0, 0xed9),
    (0xf20, 0xf29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17e0, 0x17e9),
    (0x1810, 0x1819), (0x1946, 0x194f), (0x19d0, 0x19d9), (0x1a80, 0x1a89),
    (0x1a90, 0x1a99), (0x1b50, 0x1b59), (0x1bb0, 0x1bb9), (0x1c40, 0x1c49),
    (0x1c50, 0x1c59), (0xa620, 0xa629), (0xa8d0, 0xa8d9), (0xa900, 0xa909),
    (0xa9d0, 0xa9d9), (0xa9f0, 0xa9f9), (0xaa50, 0xaa59), (0xabf0, 0xabf9),
    (0xff10, 0xff19), (0x104a0, 0x104a9), (0x11066, 0x1106f),
    (0x110f0, 0x110f9), (0x11136, 0x1113f), (0x111d0, 0x111d9),
    (0x112f0, 0x112f9), (0x11450, 0x11459), (0x114d0, 0x114d9),
    (0x11650, 0x11659), (0x116c0, 0x116c9), (0x11730, 0x11739),
    (0x118e0, 0x118e9), (0x11c50, 0x11c59), (0x16a60, 0x16a69),
    (0x16b50, 0x16b59), (0x1d7ce, 0x1d7ff), (0x1e950, 0x1e959) ]

/-- Whether a single character is a decimal digit: a member of one of the
decimal-digit runs above (any decimal number system's digits, not only
`'0'..'9'`). -/
def isDecimalDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/-- If `p` occurs verbatim at the front of `s`, return what remains after it;
otherwise `none`. This is literal (character-for-character) prefix consumption. -/
def stripPrefix? (p s : List Char) : Option (List Char) :=
  if p.isPrefixOf s then some (s.drop p.length) else none

/-- The end-of-key position: nothing remains, or exactly one trailing line
break remains (the end-of-input tolerance of the matching engine). -/
def atEnd (cs : List Char) : Bool := cs.isEmpty || cs == ['\n']

/-- Whether `key` denotes an editable row's primary key for the form marker
`mark` and primary-key field name `pkName`.

`key` qualifies exactly when it decomposes, character-for-character, as

    mark ++ ['-'] ++ ds ++ ['-'] ++ pkName ++ tail

where `ds` is a non-empty run of decimal digits (`isDecimalDigit`, i.e. the
digits of any decimal number system) and `tail` is the end of the key (empty,
or one final line break — `atEnd`). The marker `mark` is matched as a plain
literal (consumed verbatim by `stripPrefix?`), and so is the field name
`pkName`. -/
def matchesRowKey (mark pkName key : List Char) : Bool :=
  match stripPrefix? mark key with
  | none => false
  | some r1 =>
    match r1 with
    | '-' :: r2 =>
      let ds := r2.takeWhile isDecimalDigit
      let rest := r2.dropWhile isDecimalDigit
      match rest with
      | '-' :: r3 =>
        match stripPrefix? pkName r3 with
        | some tail => !ds.isEmpty && atEnd tail
        | none => false
      | _ => false
    | _ => false
-- pure-end

-- post-conditions-start
/-- Input→output relation for the per-row primary-key selection.

Inputs:
* `mark`   — the form marker matched literally at the front of a row key;
* `pkName` — the primary-key field name closing a row key;
* `items`  — the submitted `(key, value)` pairs in submission order.

The result is fully pinned to the inputs: it is exactly the values of the pairs
whose key qualifies under `matchesRowKey`, kept in their original order. This
pins the membership (a value is present iff its key qualifies), the order, the
multiplicity (one output entry per qualifying pair), and each value (carried
through unchanged); no output component is left free. -/
def problem_spec_rowKeySelection {α : Type}
    (mark pkName : List Char) (items : List (List Char × α)) (result : List α) : Prop :=
  result = (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)
-- post-conditions-end

-- impl-start
/-- PRE-PATCH (buggy) matcher. The earlier code assembled the row-key pattern by
splicing the marker into a pattern language WITHOUT neutralising its
metacharacters, so a marker that ends in — or contains — an end-of-input
metacharacter (`$`) no longer matches itself as ordinary text: the `$` demands
end-of-input at that point, and a key that continues past the marker can never
match. This partial model reproduces exactly that regression: on markers with no
metacharacter it coincides with the literal matcher, and on any marker
containing `$` it wrongly rejects every longer key. It is enough to make the
selection observably diverge from the (literal) specification on the marker
`form$`, which is the concrete data-loss case. -/
def matchesRowKeyUnescaped (mark pkName key : List Char) : Bool :=
  if mark.contains '$' then false
  else matchesRowKey mark pkName key

def implementation_rowKeySelection {α : Type}
    (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do
  let mut acc : List α := []
  for kv in items do
    if matchesRowKeyUnescaped mark pkName kv.1 then
      acc := acc ++ [kv.2]
  return acc
-- impl-end

-- proof-start
theorem correct_rowKeySelection {α : Type} :
    ∀ (mark pkName : List Char) (items : List (List Char × α)),
      problem_spec_rowKeySelection mark pkName items
        (implementation_rowKeySelection mark pkName items) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl
          -- (`matchesRowKeyUnescaped` ≠ `matchesRowKey` on any marker with `$`,
          -- so the two selections disagree and the statement is false) — G-DIFF.
-- proof-end
