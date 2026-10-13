import Velvet.Std
-- imports-end

/- Total correctness: the real join over the accumulated name parts is a
   bounded loop and always terminates, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating loop
   discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axiom. The only operation under specification — joining an
--  ordered list of name parts with a single separator between consecutive
--  parts — is modeled DEEPLY below as `joinDot` and validated == the real
--  standard-library string-join callee out-of-band by axiom_check.py / G-AX.)
-- axioms-end

-- pure-start
/- The separator placed between two consecutive parts: a single full stop. -/
def sep : Char := '.'

/- The dotted path of an ordered list of name parts: the first part, then for
   each later part a single separator followed by that part — and nothing else.
   Front-recursive (one unfold per part) so a backward impl loop discharges the
   value equality. The empty list joins to the empty sequence; a single part
   joins to itself. -/
def joinDot : List (List Char) → List Char
  | []            => []
  | [p]           => p
  | p :: q :: rest => p ++ (sep :: joinDot (q :: rest))

@[grind] lemma joinDot_singleton (p : List Char) : joinDot [p] = p := rfl

@[grind] lemma joinDot_cons_cons (p q : List Char) (rest : List (List Char)) :
    joinDot (p :: q :: rest) = p ++ (sep :: joinDot (q :: rest)) := rfl

/- A left-to-right, non-overlapping substitution of a two-character window by a
   single character. Spec-neutral helper (it is NOT referenced by the modeled
   `joinPath` below); kept here so both faces of the bundle share one spec
   view. Provenance + executable soundness: mapping.md / axiom_check.py. -/
def replaceWindow : List Char → List Char
  | [] => []
  | [c] => [c]
  | a :: b :: cs =>
    if a = '.' ∧ b = '[' then '[' :: replaceWindow cs
    else a :: replaceWindow (b :: cs)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method joinPath (parts : List (List Char)) return (out : List Char)
  require parts.length ≥ 1
  ensures out = joinDot parts
  do
    -- impl-start
    -- PRE-PATCH (buggy) skeleton: after folding the parts into the dotted path,
    -- a further post-join window substitution collapses the two-character
    -- sequence `.[` into `[`. The frozen spec requires the join EXACTLY
    -- (`out = joinDot parts`, no further transformation), so this extra pass
    -- corrupts any part that itself contains `.[` and prove_correct MUST fail.
    let mut result : List Char := parts[parts.length - 1]!
    let mut i := parts.length - 1
    while i > 0
      invariant 1 ≤ i + 1 ∧ i ≤ parts.length - 1
      invariant result = joinDot (parts.drop i)
      done_with i = 0
      decreasing i
    do
      let p := parts[i - 1]!
      result := p ++ (sep :: result)
      i := i - 1
    result := replaceWindow result
    return result
    -- impl-end

/- Loop-entry base case: dropping all but the last element leaves the singleton
   list of that element, which `joinDot` maps to itself. -/
lemma joinDot_drop_last (parts : List (List Char)) (h : 0 < parts.length) :
    parts[parts.length - 1]! = joinDot (parts.drop (parts.length - 1)) := by
  have hlt : parts.length - 1 < parts.length := by omega
  have hcons : parts.drop (parts.length - 1) = parts[parts.length - 1]! :: parts.drop (parts.length) := by
    have hh := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : parts.length - 1 + 1 = parts.length := by omega
    rw [hh, hsucc]
  rw [hcons]
  rw [List.drop_length]
  rfl

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front. When at least two parts remain, `joinDot` peels one part
   plus a separator; this is the single goal `loom_solve` leaves for the body. -/
lemma joinDot_drop_step (parts : List (List Char)) (i : Nat)
    (hi : 0 < i) (hlt : i < parts.length) :
    joinDot (parts.drop (i - 1)) = parts[i - 1]! ++ (sep :: joinDot (parts.drop i)) := by
  have hlt1 : i - 1 < parts.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  have hcons : parts.drop (i - 1) = parts[i - 1]! :: parts.drop i := by
    have h := List.drop_eq_getElem_cons hlt1
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt1, Option.getD_some]
    rw [h, hsucc]
  have hcons2 : parts.drop i = parts[i]! :: parts.drop (i + 1) := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    rw [h]
  rw [hcons, hcons2, joinDot_cons_cons, ← hcons2]

prove_correct joinPath by
  loom_solve
  · rw [joinDot_drop_step parts i (by omega) (by omega)]
    simp_all
  · exact joinDot_drop_last parts (by omega)
