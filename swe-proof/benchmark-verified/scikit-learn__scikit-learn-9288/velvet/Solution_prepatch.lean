import Velvet.Std
import Mathlib.Data.Rat.Defs
import Mathlib.Algebra.Order.Field.Rat
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. One attempt's outcome is produced by an UNCHANGED
--  routine that this code does not alter; it is observed here only through the
--  free input `runFor : Key → Run`. The spec makes NO behavioural claim about
--  that routine — every clause holds for EVERY function it could be — so there
--  is nothing to validate against a real callee (no G-AX). The behaviour under
--  spec — over WHICH sequence of per-attempt keys the attempts are run, and that
--  the best-scoring outcome is reported — is modeled deeply in the `pure`/`impl`
--  regions, with no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The per-attempt key that fully determines one attempt's outcome: identified
   abstractly, since the only thing observed is WHICH sequence of keys the
   attempts are run over (two equal sequences must yield the same report). -/
abbrev Key := Int

/- The outcome of a single attempt. `score` is the quantity to be minimised
   (lower is better); `payload` is the reportable content of the attempt
   (identified abstractly). Two attempts with different content are different
   outcomes even at the same score. -/
structure Run where
  score : Rat
  payload : Nat

/- Fold one more attempt into the running best-so-far. `acc` is the best outcome
   seen over the attempts considered so far (`none` before any attempt). The next
   attempt's outcome is `runFor k`; it replaces the incumbent exactly when there
   is no incumbent yet, or when it scores strictly lower. A tie keeps the earlier
   incumbent — the first attempt achieving the minimum score is the one reported. -/
def consider (runFor : Key → Run) (acc : Option Run) (k : Key) : Option Run :=
  let r := runFor k
  match acc with
  | none   => some r
  | some b => if r.score < b.score then some r else some b

/- The reported outcome of running one attempt per key, in order, over the given
   key sequence and keeping the best-scoring one. Front-to-back fold so a single
   unfold is available per loop step (the Velvet forward-fold pattern). -/
def bestOverKeys (runFor : Key → Run) (keys : List Key) : Option Run :=
  keys.foldl (consider runFor) none

/- Forward-fold step: extending the consumed prefix by one key folds that key's
   attempt into the best built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
@[grind] lemma bestOverKeys_take_step (runFor : Key → Run) (keys : List Key)
    (i : Nat) (hi : i < keys.length) :
    (keys.take (i + 1)).foldl (consider runFor) none
      = consider runFor ((keys.take i).foldl (consider runFor) none) keys[i]! := by
  have hcons : keys.take (i + 1) = keys.take i ++ [keys[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run several independent attempts and report the best-scoring one.

   `keys` is the canonical sequence of per-attempt keys — the one source of
   per-attempt keys this routine must use, the SAME sequence whatever machinery
   carries out the attempts. `altKeys` is some other key sequence that happens to
   be in scope; it must NOT drive the attempts. `runFor` is the UNCHANGED routine
   mapping any key to that attempt's outcome. All three are read-only (none
   `mut`): the routine reads them and returns a result, mutating nothing it is
   handed (directive 5).

   The reported outcome is `bestOverKeys runFor keys`: the best (strictly lowest
   score; earliest on a tie) attempt over the runs determined by the CANONICAL
   key sequence — never over runs determined by `altKeys`. Two callers that pin
   the same canonical key sequence therefore obtain the same report regardless of
   how the attempts are arranged. -/
method selectBest (keys : List Key) (altKeys : List Key) (runFor : Key → Run)
    return (out : Option Run)
  ensures out = bestOverKeys runFor keys
  do
    -- impl-start
    -- PRE-PATCH (buggy): the attempts are run over `altKeys` — a separate key
    -- sequence that happens to be in scope — instead of the canonical `keys`.
    -- The two sequences agree only by accident, so the reported best is in
    -- general the best over the WRONG runs; prove_correct MUST fail.
    let mut best : Option Run := none
    let mut i := 0
    while i < altKeys.length
      invariant i ≤ altKeys.length
      invariant best = (altKeys.take i).foldl (consider runFor) none
      done_with i = altKeys.length
      decreasing altKeys.length - i
    do
      let k := altKeys[i]!
      let r := runFor k
      best := match best with
        | none   => some r
        | some b => if r.score < b.score then some r else some b
      i := i + 1
    return best
    -- impl-end

prove_correct selectBest by
  loom_solve
  · have hi : i < altKeys.length := by omega
    rw [bestOverKeys_take_step runFor altKeys i hi, ← invariant_2]
    simp [consider]
  · have hlen : i = altKeys.length := done_1
    subst hlen
    rw [List.take_length] at invariant_2
    simp_all [bestOverKeys]
