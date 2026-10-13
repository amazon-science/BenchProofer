import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads two plain inputs — an ordered
--  sequence of strings and a set of strings to leave out — together
--  with the fresh prefix to apply, and produces the relabeling sequence handed
--  onward. Every observable is computed structurally from those inputs; no
--  unchanged callee's contract is consumed and no foreign callee is deep-modeled,
--  so there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The relabeling produced for the input strings from position `pos` onward,
   under a fresh `newPrefix`, with any string listed in `preserved` left out.

   Each string is paired with a fresh name `newPrefix ++ toString pos` keyed by
   its ORIGINAL position in the full sequence — the position counter advances for
   every string, including the ones in `preserved`, so a preserved string still
   consumes its index and the later names are unaffected by the omission. A
   preserved string contributes no pair. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def relabelFrom (newPrefix : String) (preserved : List String) :
    Nat → List String → List (String × String)
  | _,   []        => []
  | pos, a :: rest =>
      (if preserved.contains a then [] else [(a, newPrefix ++ toString pos)])
        ++ relabelFrom newPrefix preserved (pos + 1) rest

/- The full relabeling: every input string paired with a fresh prefixed name
   keyed by its position, except those in `preserved`, which are omitted. -/
def relabeling (newPrefix : String) (preserved : List String)
    (aliases : List String) : List (String × String) :=
  relabelFrom newPrefix preserved 0 aliases

@[grind] lemma relabelFrom_nil (p : String) (pr : List String) (pos : Nat) :
    relabelFrom p pr pos [] = [] := rfl

@[grind] lemma relabelFrom_cons (p : String) (pr : List String) (pos : Nat)
    (a : String) (rest : List String) :
    relabelFrom p pr pos (a :: rest) =
      (if pr.contains a then [] else [(a, p ++ toString pos)])
        ++ relabelFrom p pr (pos + 1) rest := rfl

/- Exposing the element at index `i-1` on the front of `drop (i-1)`, the
   backward-fold step: dropping one fewer element peels one entry off
   `relabelFrom`, with the position counter stepping from `i-1` to `i`. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma relabelFrom_drop_step (aliases : List String) (newPrefix : String)
    (preserved : List String) (i : Nat) (hi : 0 < i) (hle : i ≤ aliases.length) :
    relabelFrom newPrefix preserved (i - 1) (aliases.drop (i - 1)) =
      (if preserved.contains aliases[i - 1]! then []
       else [(aliases[i - 1]!, newPrefix ++ toString (i - 1))])
        ++ relabelFrom newPrefix preserved i (aliases.drop i) := by
  have hlt : i - 1 < aliases.length := by omega
  have hcons : aliases.drop (i - 1) = aliases[i - 1]! :: aliases.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, relabelFrom_cons]
  have hsucc : i - 1 + 1 = i := by omega
  rw [hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the relabeling for an ordered sequence of input strings `aliases`,
   pairing each with a fresh name under `newPrefix`.

   Each string is mapped to a fresh name formed from `newPrefix` and the string's
   ORIGINAL position, EXCEPT for the strings listed in `preserved`, which are left
   out of the relabeling (they contribute no pair). The position counter advances
   for every string, so omitting a preserved string does not shift the names
   assigned to the others.

   `aliases` and `preserved` are read-only — neither is `mut`; the operation reads
   them and returns a fresh relabeling sequence, mutating nothing it is handed
   (directive 5). -/
method buildRelabeling (aliases : List String) (newPrefix : String)
    (preserved : List String) return (out : List (String × String))
  ensures out = relabeling newPrefix preserved aliases
  do
    -- impl-start
    -- Pre-image skeleton: the relabeling is built for EVERY alias at its
    -- position, with no aliases held back from renaming. The frozen spec
    -- requires the aliases in `preserved` to be omitted (so they keep their
    -- current name), so prove_correct MUST fail.
    let mut result : List (String × String) := []
    let mut i := aliases.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ aliases.length
      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
      done_with i = 0
      decreasing i
    do
      let a := aliases[i - 1]!
      result := [(a, newPrefix ++ toString (i - 1))] ++ result
      i := i - 1
    return result
    -- impl-end

prove_correct buildRelabeling by
  loom_solve
  all_goals (
    try (rw [relabelFrom_drop_step aliases newPrefix preserved i (by omega) (by omega)])
    try (obtain ⟨hi0, hr⟩ := i_2)
    simp_all [relabeling])
