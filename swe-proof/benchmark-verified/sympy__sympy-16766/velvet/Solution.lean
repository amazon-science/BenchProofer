import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The components an element-access rendering is
--  assembled from — the carrier symbol's text and the already-rendered text of
--  each subscript — are supplied as inputs: they are the outputs of unchanged
--  rendering helpers, so they are part of the input carrier, not opaque oracles.
--  The behaviour under specification — assembling the bracketed, comma-separated
--  access string and emitting it as ordinary supported code — is modeled
--  DEEPLY below. Nothing is borrowed from an answer key. See mapping.md.)
-- axioms-end

-- pure-start
/- Join a list of already-rendered fragments with the two-character separator
   ", " between consecutive fragments (no leading or trailing separator). The
   empty list joins to the empty fragment; a single fragment joins to itself.
   Front-recursive so a single unfold is available per loop step (the backward
   fold pattern). -/
def joinComma : List (List Char) → List Char
  | []             => []
  | [x]            => x
  | x :: y :: rest => x ++ ", ".toList ++ joinComma (y :: rest)

@[grind] lemma joinComma_nil : joinComma [] = [] := rfl
@[grind] lemma joinComma_single (x : List Char) : joinComma [x] = x := rfl
@[grind] lemma joinComma_cons2 (x y : List Char) (rest : List (List Char)) :
    joinComma (x :: y :: rest) = x ++ ", ".toList ++ joinComma (y :: rest) := rfl

/- The join of a non-empty tail peels one fragment and one separator. -/
lemma joinComma_cons_ne (x : List Char) (l : List (List Char)) (h : l ≠ []) :
    joinComma (x :: l) = x ++ ", ".toList ++ joinComma l := by
  cases l with
  | nil => exact absurd rfl h
  | cons y rest => rfl

/- The fully assembled element-access rendering: the carrier symbol's text,
   then the subscript fragments joined by ", " enclosed in square brackets. This
   is the supported rendering — no "unsupported" annotation precedes it. -/
def accessRender (base : List Char) (indices : List (List Char)) : List Char :=
  base ++ "[".toList ++ joinComma indices ++ "]".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render an element access of a subscriptable carrier as ordinary supported
   code: the carrier symbol's text followed by its subscript fragments, joined
   by ", " and wrapped in square brackets — and nothing else (in particular, no
   "unsupported construct" annotation is emitted). `base` and `indices` are the
   already-rendered components and are read-only (not `mut`); the loop builds a
   fresh result and never mutates its inputs (directive 5). -/
method renderAccess (base : List Char) (indices : List (List Char))
    return (out : List Char)
  ensures out = accessRender base indices
  do
    -- impl-start
    let mut joined : List Char := []
    let mut i := indices.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ indices.length
      invariant joined = joinComma (indices.drop i)
      done_with i = 0
      decreasing i
    do
      let piece := indices[i - 1]!
      joined := if i = indices.length then piece else piece ++ ", ".toList ++ joined
      i := i - 1
    return base ++ "[".toList ++ joined ++ "]".toList
    -- impl-end

/- The backward-fold step: dropping one fewer fragment exposes the fragment at
   `i-1` on the front. When that fragment is the last one (`i = length`,
   i.e. the suffix after it is empty) it joins to itself; otherwise `joinComma`
   peels it with its trailing separator. This is the single goal `loom_solve`
   leaves for the loop body. -/
lemma joinComma_drop_step (indices : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ indices.length) :
    joinComma (indices.drop (i - 1)) =
      (if i = indices.length then indices[i - 1]!
       else indices[i - 1]! ++ ", ".toList ++ joinComma (indices.drop i)) := by
  have hlt : i - 1 < indices.length := by omega
  have hcons : indices.drop (i - 1) = indices[i - 1]! :: indices.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hlen : (indices.drop i).length = indices.length - i := List.length_drop
  rw [hcons]
  by_cases hempty : indices.drop i = []
  · have hi_eq : i = indices.length := by
      have h0 : (indices.drop i).length = 0 := by rw [hempty]; rfl
      rw [hlen] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ indices.length := by
      intro he
      apply hempty
      have h0 : (indices.drop i).length = 0 := by rw [hlen, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

prove_correct renderAccess by
  loom_solve
  all_goals
    first
      | (rw [joinComma_drop_step indices i (by omega) (by omega)]; simp_all)
      | simp_all [accessRender]
