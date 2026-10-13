import Mathlib
-- imports-end

/-!
Collecting the source positions at which a single translatable text was seen.

Each time the text is encountered, an occurrence record is appended: a source
name, a line number within that source, and an opaque per-occurrence
identifier. The same `(source, line)` position can be recorded many times — the
text may genuinely appear there more than once, or the same physical location
may be revisited — and the per-occurrence identifier differs every time, so
naive collection of the positions yields repeats.

The desired output is the list of positions that should be reported for the
text: every distinct `(source, line)` that was recorded, each listed exactly
once, in ascending order. Ascending order is the lexicographic order on
positions — by source name first, then by line number — matching how a pair of
(string, integer) is ordered. The opaque identifiers do not appear in this
output; they only witness that a position was recorded.

We model an occurrence record as a `String × Int × String` (source, line,
identifier) and a reported position as a `String × Int` (source, line).
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The whole computation — mapping
-- each occurrence to its position, removing repeats, and ordering — is modeled
-- directly with total Lean operations, so there are no `opaque`/`axiom` decls.
-- axioms-end

-- pure-start
/-- Lexicographic "≤" on positions: order by source name, tie-broken by line.
Mirrors the order used to compare a pair of (string, integer) ascending. -/
def lexLe (a b : String × Int) : Bool :=
  if a.1 = b.1 then decide (a.2 ≤ b.2) else decide (a.1 < b.1)

/-- Strict lexicographic order on positions (the irreflexive core of `lexLe`):
a smaller source name, or an equal source name with a smaller line. Used to
state that the output is strictly ascending — simultaneously ordered and
repeat-free. -/
def lexLt (a b : String × Int) : Prop :=
  a.1 < b.1 ∨ (a.1 = b.1 ∧ a.2 < b.2)
-- pure-end

-- post-conditions-start
/-- The positions reported for a text whose occurrences are `triples`
(each `(source, line, identifier)`):

  * the result is strictly ascending in lexicographic position order — which
    forces both that it is sorted and that no position repeats; and
  * a position is reported iff it was recorded by some occurrence — i.e. there
    exists an occurrence with that source and line (its identifier is
    irrelevant).

Together these pin the result to exactly the distinct recorded positions, in
ascending order. -/
def problem_spec_dedupSort
    (triples : List (String × Int × String)) (result : List (String × Int)) : Prop :=
  List.Sorted lexLt result ∧
  (∀ p : String × Int, p ∈ result ↔ ∃ u : String, (p.1, p.2, u) ∈ triples)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: positions are collected in occurrence order with
-- neither repeat-removal nor ordering. A position recorded twice appears twice,
-- and the result follows occurrence order rather than ascending order — so it
-- violates both the strict-ordering and the (forward, repeat-free) clauses of
-- the spec whenever any position is recorded more than once or out of order.
def implementation_dedupSort
    (triples : List (String × Int × String)) : List (String × Int) := Id.run do
  let mut pairs : List (String × Int) := []
  for t in triples do
    pairs := pairs ++ [(t.1, t.2.1)]
  return pairs
-- impl-end

-- proof-start
-- The proof agent carries its closed `Solution.lean` proof body here over the
-- buggy impl. It cannot close: `pairs` is not deduplicated (so `List.Sorted
-- lexLt` fails on any repeated position — `lexLt` is irreflexive) nor sorted
-- (so the ordering clause fails on out-of-order occurrences). This unclosable
-- proof against the buggy impl is the G-DIFF signal (run in the P1.5 static
-- sweep). At construction time it is the `sorry` placeholder.
theorem correct_dedupSort :
    ∀ triples : List (String × Int × String),
      problem_spec_dedupSort triples (implementation_dedupSort triples) := by
  sorry
-- proof-end
