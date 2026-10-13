import Mathlib
-- imports-end

/-!
Locating where an open parenthesis is closed inside a pattern fragment.

A fragment is a sequence of characters that begins just after a parenthesis has
already been opened. Scanning the fragment from left to right, the goal is to
find the position of the character that finally closes that initially-open
parenthesis, honouring two rules:

  * nesting — every additional unescaped `(` opens a further parenthesis that
    must be closed before the original one, and every unescaped `)` closes the
    innermost currently-open parenthesis;
  * escaping — a `(` or `)` whose immediately preceding character is a backslash
    is literal text and does NOT affect the nesting depth.

The closing position is the FIRST index at which the running nesting depth
returns to zero. It is reported wherever it occurs in the fragment, including as
the very last character (a fragment that ends exactly at its closing parenthesis
is closed at that final character, not left unclosed). If the depth never returns
to zero, the parenthesis is never closed and no position is reported.

The behaviour is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The fragment that is
-- scanned, and the rule for which characters count as structural parentheses,
-- are spelled out directly over the input character sequence; there is no opaque
-- callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- One scanning step over a character `c`, given the running open-parenthesis
depth `st.1` and the preceding character `st.2`. An unescaped `(` (one whose
preceding character is not a backslash) increases the depth; an unescaped `)`
decreases it; every other character — and any parenthesis escaped by a preceding
backslash — leaves the depth unchanged. The step records `c` as the new preceding
character. -/
def stepBracket (st : Int × Option Char) (c : Char) : Int × Option Char :=
  let d := st.1
  let prev := st.2
  if c == '(' && prev != some '\\' then (d + 1, some c)
  else if c == ')' && prev != some '\\' then (d - 1, some c)
  else (d, some c)

/-- The open-parenthesis depth remaining after scanning the prefix `p`, starting
from a single already-open parenthesis (depth `1`) and no previous character. -/
def depthAfter (p : List Char) : Int :=
  (p.foldl stepBracket (1, none)).1
-- pure-end

-- post-conditions-start
/-- `result` reports the position that closes the initially-open parenthesis.

  * `some i` means scanning the first `i + 1` characters brings the depth to `0`
    (the parenthesis is closed exactly at index `i`), `i` is a real index of the
    fragment, and no shorter prefix closes it (the depth stays non-zero for every
    strictly shorter prefix). The closing character may be the very last one.
  * `none` means the parenthesis is never closed: no prefix of the fragment
    brings the depth to `0`.

No output component is left free: for every fragment the reported value is fully
determined by the running depth over the fragment's own characters. -/
def problem_spec_findGroupEnd (cs : List Char) (result : Option Nat) : Prop :=
  match result with
  | some i =>
      i < cs.length ∧
      depthAfter (cs.take (i + 1)) = 0 ∧
      (∀ j, j < i → depthAfter (cs.take (j + 1)) ≠ 0)
  | none =>
      ∀ i, i < cs.length → depthAfter (cs.take (i + 1)) ≠ 0
-- post-conditions-end

-- impl-start
def implementation_findGroupEnd (cs : List Char) : Option Nat := Id.run do
  let mut depth : Int := 1
  let mut prev : Option Char := none
  let mut idx : Nat := 0
  for val in cs do
    -- When the depth is already back to zero, the current position closes the
    -- group; report it before examining the current character.
    if depth == 0 then
      return some idx
    -- Check for unescaped `(` and `)`; they open and close nested parentheses.
    if val == '(' && prev != some '\\' then
      depth := depth + 1
    else if val == ')' && prev != some '\\' then
      depth := depth - 1
    prev := some val
    idx := idx + 1
  return none
-- impl-end

-- proof-start
theorem correct_findGroupEnd :
    ∀ (cs : List Char),
      problem_spec_findGroupEnd cs (implementation_findGroupEnd cs) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
