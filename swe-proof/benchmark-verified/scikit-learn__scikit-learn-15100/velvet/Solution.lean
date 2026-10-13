import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Two UNCHANGED standard-library text routines the operation defers to. Both are
   left OPAQUE (free functions with NO asserted `ensures`): the operation refines
   how they are *applied*, it never changes them, and the desired result is pinned
   purely in terms of their (uninterpreted) values, so there is nothing to claim
   about either one and nothing for G-AX to validate (mapping.md §3; meta.json
   G-AX skip). Their real-callee identities are an R type-refinement bridged by
   mapping.md and exercised by G-CONF (which runs the real callees in the shadow).

   `canonicalDecompose` — the canonical (compatibility) decomposition of a string
   into its constituent code points (so a precomposed accented character becomes
   its base letter followed by separate mark code points). -/
opaque canonicalDecompose : List Char → List Char

/- `isCombiningMark` — whether a single code point is a combining mark (a mark
   that attaches to a preceding base character rather than standing on its own). -/
opaque isCombiningMark : Char → Bool
-- axioms-end

-- pure-start
/- The mark-free residue of a code-point sequence: walk it front to back, keeping
   every non-combining code point and discarding every combining mark. Written
   front-recursively so a single unfold is available per loop step (the per-element
   expansion fold pattern, plan §5.4). -/
def markFreeSeq : List Char → List Char
  | []      => []
  | c :: cs => (if isCombiningMark c then [] else [c]) ++ markFreeSeq cs

@[grind] lemma markFreeSeq_nil : markFreeSeq [] = [] := rfl
@[grind] lemma markFreeSeq_cons (c : Char) (cs : List Char) :
    markFreeSeq (c :: cs) = (if isCombiningMark c then [] else [c]) ++ markFreeSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Map a string to its mark-free canonical form: decompose it to canonical code
   points, then drop the combining marks. Two strings that look identical but are
   encoded differently (precomposed vs. already decomposed) therefore both reduce
   to the same mark-free string. `s` is read-only (not `mut`): the result is built
   in a fresh accumulator and the input is never mutated (directive 5). -/
method stripDiacritics (s : List Char) return (out : List Char)
  ensures out = markFreeSeq (canonicalDecompose s)
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := (canonicalDecompose s).length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ (canonicalDecompose s).length
      invariant result = markFreeSeq ((canonicalDecompose s).drop i)
      done_with i = 0
      decreasing i
    do
      let c := (canonicalDecompose s)[i - 1]!
      result := (if isCombiningMark c then [] else [c]) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the code point at
   `i-1` on the front, so `markFreeSeq` peels one keep/drop contribution. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma markFreeSeq_drop_step (xs : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    markFreeSeq (xs.drop (i - 1))
      = (if isCombiningMark xs[i - 1]! then [] else [xs[i - 1]!]) ++ markFreeSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, markFreeSeq_cons]

prove_correct stripDiacritics by
  loom_solve
  rw [markFreeSeq_drop_step (canonicalDecompose s) i (by omega) (by omega)]
  simp_all
