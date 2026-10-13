import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The producer of the incoming list of
--  (value, tag) items is an unchanged upstream computation whose only relevant
--  effect is the SEQUENCE of items it emits; that sequence is the read-only
--  input `items` here. The transformation under spec — collapsing items that
--  share a tag into a single item whose value is the combination of theirs — is
--  modeled deeply below. Every observable is computed from `items`; nothing is
--  borrowed from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A value carried by an item, modeled as the ordered list of opaque atom codes
   it is built from. The "combine" operation on two values is concatenation of
   their atom-code lists: combining is associative with the empty list as unit,
   exactly the structure of the free monoid on atoms. Two items combine by
   concatenating their codes. -/
abbrev Content := List Int

/- One item: a value (`fst`, its atom-code list) paired with an integer tag
   (`snd`). Items are grouped by tag. -/
abbrev Item := Content × Int

/- Tag-keyed combine: fold value `v` into the accumulator under tag `k`.
   - a tag never seen before is appended at the end, keeping the order in which
     tags were first encountered, carrying value `v`;
   - a tag already present keeps its position but has the incoming value
     concatenated onto the value accumulated so far for that tag (`acc ++ v`),
     i.e. the running combination in first-seen order.
   This is the exact effect of, for each distinct tag, combining (in input
   order) the values of every item carrying that tag. -/
def combineInto (m : List Item) (v : Content) (k : Int) : List Item :=
  match m with
  | []            => [(v, k)]
  | (v', k') :: r => if k' = k then (v' ++ v, k') :: r else (v', k') :: combineInto r v k

/- Fold one item into the accumulating grouping. -/
def combineStep (m : List Item) (e : Item) : List Item := combineInto m e.1 e.2

/- The grouped sequence built from a whole list of items: each item is combined
   into the tag-keyed accumulator; the result reads it out in first-encounter
   tag order. Net effect: every distinct tag appears EXACTLY ONCE, in
   first-encounter order, carrying the combination of all values seen for it. -/
def combineAll (items : List Item) : List Item := items.foldl combineStep []

/- Tags of a combine: an already-present tag leaves the tag list unchanged; a
   fresh tag is appended. (Combining values never changes the tag list.) -/
@[grind] lemma tags_combineInto (m : List Item) (v : Content) (k : Int) :
    (combineInto m v k).map Prod.snd
      = if k ∈ m.map Prod.snd then m.map Prod.snd else m.map Prod.snd ++ [k] := by
  induction m with
  | nil => simp [combineInto]
  | cons hd tl ih =>
    obtain ⟨v', k'⟩ := hd
    by_cases hkk : k' = k
    · subst hkk; simp [combineInto]
    · simp only [combineInto, hkk, if_false, List.map_cons]
      by_cases hmem : k ∈ tl.map Prod.snd
      · simp [ih, hmem, List.mem_cons, Ne.symm hkk]
      · have : k ∉ (v', k').2 :: tl.map Prod.snd := by
          simp [List.mem_cons, Ne.symm hkk, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hkk]

/- Combine preserves tag-uniqueness. -/
@[grind] lemma nodup_combineInto (m : List Item) (v : Content) (k : Int)
    (h : (m.map Prod.snd).Nodup) : ((combineInto m v k).map Prod.snd).Nodup := by
  rw [tags_combineInto]
  by_cases hmem : k ∈ m.map Prod.snd
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's tags stay unique through any fold, from any tag-unique
   seed. -/
lemma nodup_foldl (items : List Item) :
    ∀ m, (m.map Prod.snd).Nodup → ((items.foldl combineStep m).map Prod.snd).Nodup := by
  induction items with
  | nil => intro m h; simpa using h
  | cons e es ih =>
    intro m h
    exact ih (combineStep m e) (by simpa [combineStep] using nodup_combineInto m e.1 e.2 h)

/- The result never lists a tag twice: each distinct tag appears once, no matter
   how many input items carried it. -/
@[grind] lemma combineAll_nodup (items : List Item) :
    ((combineAll items).map Prod.snd).Nodup :=
  nodup_foldl items [] (by simp)

/- Forward-fold step: extending the consumed prefix by one item combines that
   item into the grouping built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body. -/
lemma combineAll_take_step (items : List Item) (i : Nat) (hi : i < items.length) :
    (items.take (i + 1)).foldl combineStep []
      = combineStep ((items.take i).foldl combineStep []) items[i]! := by
  have hcons : items.take (i + 1) = items.take i ++ [items[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the result list from a list of (value, tag) items `items`.
   The result is exactly the tag-keyed collapse of the input: every distinct tag
   appears once, in first-encounter order, carrying the combination (value
   concatenation, in input order) of every item that shared that tag. `items` is
   read-only (not `mut`): the loop builds a fresh result and never mutates its
   input. -/
method combineByTag (items : List Item) return (out : List Item)
  ensures out = combineAll items
  ensures (out.map Prod.snd).Nodup
  do
    -- impl-start
    -- Pre-image skeleton: every item is emitted as it is seen (a raw append per
    -- step), with NO tag-keyed collapse. Items that share a tag are therefore
    -- emitted once each, so the result is the raw input `items` — not
    -- `combineAll items` — and its tags are not unique. prove_correct MUST fail
    -- (both `ensures` clauses).
    let mut result : List Item := []
    let mut i := 0
    while i < items.length
      invariant i ≤ items.length
      invariant result = items.take i
      done_with i = items.length
      decreasing items.length - i
    do
      let e := items[i]!
      result := result ++ [e]
      i := i + 1
    return result
    -- impl-end

prove_correct combineByTag by
  loom_solve <;>
    simp_all [combineAll, List.take_succ, List.getElem!_eq_getElem?_getD]
