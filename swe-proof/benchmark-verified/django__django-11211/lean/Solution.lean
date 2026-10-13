import Mathlib
-- imports-end

/-!
Preparing a stored identifier value for use as a comparison key.

Some records are keyed by a universally-unique identifier (a 128-bit value). The
same identifier can be carried in more than one shape: as an already-parsed
identifier object, or as a piece of text that spells the identifier out (for
instance the string form that is kept in a free-text column, which may include
separator characters). A value may also be absent.

To decide whether two records refer to the SAME identifier, each candidate value
is first put into a single canonical shape. The behaviour pinned below is that of
that preparation step: it maps every textual spelling of an identifier to the one
canonical identifier it denotes, leaves an already-canonical identifier and an
absent value untouched, and so makes two values that denote the same identifier
compare equal regardless of the shape each arrived in.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a logical axiom. The two helpers the
-- prepared value is built from — the no-op pass-through that precedes the
-- conversion, and the textual→identifier conversion itself — are modeled DEEPLY
-- as the pure functions `basePrep` and `canonicalValue` below (the textual
-- conversion decodes the identifier's hexadecimal digits, ignoring separators).
-- They are deep-model references validated against the real callees by the
-- conformance check, not consumed axioms, so no `opaque`/`axiom` is declared.
-- axioms-end

-- pure-start
/-- A value that may carry an identifier in one of several shapes. -/
inductive UuidValue where
  | absent
  | canonical (n : Nat)
  | textual (s : List Char)
  deriving DecidableEq

/-- Hexadecimal value of a single character, if it is a hex digit
(`0`–`9`, `a`–`f`, `A`–`F`); `none` for any other character. -/
def hexVal? (c : Char) : Option Nat :=
  let n := c.toNat
  if 48 ≤ n ∧ n ≤ 57 then some (n - 48)              -- '0'..'9'
  else if 97 ≤ n ∧ n ≤ 102 then some (n - 97 + 10)   -- 'a'..'f'
  else if 65 ≤ n ∧ n ≤ 70 then some (n - 65 + 10)    -- 'A'..'F'
  else none

/-- Decode the identifier denoted by a textual spelling: accumulate its
hexadecimal digits left to right, ignoring any separator characters. -/
def decodeHex (s : List Char) : Nat :=
  s.foldl (fun acc c => match hexVal? c with
                        | some d => acc * 16 + d
                        | none   => acc) 0

/-- The no-op pass-through applied before conversion (returns its argument). -/
def basePrep (v : UuidValue) : UuidValue := v

/-- The canonical identifier denoted by a value: a textual spelling is decoded to
the identifier it denotes; an already-canonical identifier and an absent value are
returned unchanged. -/
def canonicalValue : UuidValue → UuidValue
  | .absent      => .absent
  | .canonical n => .canonical n
  | .textual s   => .canonical (decodeHex s)
-- pure-end

-- post-conditions-start
/-- The prepared value is fully pinned to the input: it is the canonical
identifier the input denotes. A textual spelling is converted to its canonical
identifier; an already-canonical identifier and an absent value are unchanged. No
output component is left free, so two values denoting the same identifier are
prepared to the SAME canonical value regardless of the shape each arrived in. -/
def problem_spec_normalizeKey (value : UuidValue) (result : UuidValue) : Prop :=
  result = canonicalValue value
-- post-conditions-end

-- impl-start
def implementation_normalizeKey (value : UuidValue) : UuidValue := Id.run do
  -- First apply the pass-through preparation, then convert the result to its
  -- canonical identifier shape.
  let mut v := value
  v := basePrep v
  return canonicalValue v
-- impl-end

-- proof-start
theorem correct_normalizeKey :
    ∀ (value : UuidValue),
      problem_spec_normalizeKey value (implementation_normalizeKey value) := by
  intro value
  unfold problem_spec_normalizeKey implementation_normalizeKey basePrep
  rfl
-- proof-end
