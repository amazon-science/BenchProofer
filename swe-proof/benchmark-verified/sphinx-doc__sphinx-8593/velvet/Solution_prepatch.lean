import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The roster of candidate member names is produced by
--  an unchanged enumerator and is consumed here as plain input data (`names`);
--  the per-name documentation lines are likewise an unchanged lookup table given
--  as input (`attrDocs`). The behaviour under specification — assembling, for
--  each member name, its associated documentation text out of those lines — is a
--  pure function of those inputs, modeled deeply over `List Int`. There is no
--  unchanged library callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
/- One collected member: the member's name together with the documentation text
   attached to it. `name` identifies the member; `doc` is the assembled
   documentation text (a sequence of character codes), empty when the member has
   no associated documentation. -/
structure MemberDoc where
  name : Int
  doc : List Int
deriving DecidableEq, Inhabited, Repr

/- Look up the documentation lines recorded for a name. The lines are supplied as
   an association list keyed by name; a name with no recorded lines yields the
   empty list. Front-recursive over the table. -/
def lookupDocs (n : Int) : List (Int × List (List Int)) → List (List Int)
  | []            => []
  | (k, v) :: rest => if k = n then v else lookupDocs n rest

/- Assemble a sequence of documentation lines into one text by placing a single
   line-break code (10) between consecutive lines: the empty list of lines is the
   empty text, a single line is itself, and each further line is preceded by one
   break. Front-recursive so it is total and directly transliterable. -/
def joinNL : List (List Int) → List Int
  | []        => []
  | [x]       => x
  | x :: xs   => x ++ (10 :: joinNL xs)

/- The collected members of a module: for each candidate name, in the order the
   names are presented, one member carrying that name together with the text
   assembled from the documentation lines recorded for it. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern). -/
def buildMembers (ad : List (Int × List (List Int))) : List Int → List MemberDoc
  | []      => []
  | n :: ns => { name := n, doc := joinNL (lookupDocs n ad) } :: buildMembers ad ns

@[grind] lemma buildMembers_nil (ad : List (Int × List (List Int))) :
    buildMembers ad [] = [] := rfl
@[grind] lemma buildMembers_cons (ad : List (Int × List (List Int))) (n : Int) (ns : List Int) :
    buildMembers ad (n :: ns) =
      { name := n, doc := joinNL (lookupDocs n ad) } :: buildMembers ad ns := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the documented members of a module.

   The candidate member names are presented as `names` (read-only), in the order
   they are to be processed. The per-name documentation lines are presented as
   `attrDocs` (read-only): an association from a name to the sequence of
   documentation lines recorded for it.

   The result lists one entry per candidate name, in the SAME order, and — this
   is the whole point — attaches to each entry the documentation text assembled
   from the lines recorded for its name (the lines joined by a single line-break
   each). A member with no recorded lines carries empty documentation text. Thus
   the documentation associated with a member always travels with that member to
   the result, rather than being dropped.

   Member names are modeled as distinct `Int` identifiers; documentation text and
   each documentation line are modeled as `List Int` of character codes so the
   line-joining is exact. `names` and `attrDocs` are read-only (not `mut`): the
   routine builds a fresh result and mutates neither (directive 5). -/
method collectMemberDocs (attrDocs : List (Int × List (List Int))) (names : List Int)
    return (out : List MemberDoc)
  ensures out = buildMembers attrDocs names
  do
    -- impl-start
    -- Pre-image skeleton: each member is collected carrying ONLY its name; the
    -- documentation text recorded for the member (the `attrDocs` lines for that
    -- name) is never looked up and never travels with the member, so every
    -- entry's `doc` is left empty regardless of what was recorded. The frozen
    -- spec (`buildMembers`) requires each entry to carry the assembled
    -- documentation text for its name, so `prove_correct` MUST fail on any name
    -- that has recorded documentation lines: the divergence is exactly the
    -- `out = buildMembers attrDocs names` clause (the reported behaviour — a
    -- member's associated documentation is dropped instead of attached).
    let mut result : List MemberDoc := []
    let mut i := names.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ names.length
      invariant result = buildMembers attrDocs (names.drop i)
      done_with i = 0
      decreasing i
    do
      let n := names[i - 1]!
      result := { name := n, doc := [] } :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `buildMembers` peels one member off the front. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma buildMembers_drop_step (ad : List (Int × List (List Int))) (xs : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    buildMembers ad (xs.drop (i - 1)) =
      { name := xs[i - 1]!, doc := joinNL (lookupDocs xs[i - 1]! ad) }
        :: buildMembers ad (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, buildMembers_cons]

prove_correct collectMemberDocs by
  loom_solve
  rw [buildMembers_drop_step attrDocs names i (by omega) (by omega)]
  rw [‹result = buildMembers attrDocs (names.drop i)›]
