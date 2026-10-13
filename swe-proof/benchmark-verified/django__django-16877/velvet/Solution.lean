import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-element transformation a consumer of the
--  sequence relies on is modeled DEEPLY in the `pure` region (`condEscape`, with
--  `escapedSeq`/`entity`), so its callee is an A-reference validated against the
--  real callee by axiom_check.py (G-AX), NOT a consumed axiom. Nothing here is
--  axiomatized.)
-- axioms-end

-- pure-start
/- One element of the input sequence: its code points, plus whether it is already
   marked as safe — an element whose producer has guaranteed it needs no further
   HTML escaping. Only these two facts are observable to a consumer of the built
   sequence (mapping.md §2). -/
structure Elem where
  chars : List Char
  safe : Bool
deriving Inhabited

/- The HTML escape of a single code point: the five significant characters expand
   to their entity sequences; every other code point passes through. The ampersand
   expands such that an emitted '&' is never re-escaped, so a single per-code-point
   map is faithful (mapping.md §3.1). -/
def entity (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/- The HTML escape of a whole code-point sequence: concatenate the per-code-point
   entity sequences. Front-recursive so a single unfold is available per loop step
   (the backward fold pattern, plan §5.4). -/
def escapedSeq : List Char → List Char
  | []      => []
  | c :: cs => entity c ++ escapedSeq cs

/- The conditional escape of one element: an element already marked safe is
   emitted unchanged; any other element is HTML-escaped per code point. -/
def condEscape (e : Elem) : List Char :=
  if e.safe then e.chars else escapedSeq e.chars

/- The conditional escape of a whole sequence: escape each element individually,
   in the original order. Front-recursive so a single unfold is available per loop
   step. -/
def escSeq : List Elem → List (List Char)
  | []      => []
  | e :: es => condEscape e :: escSeq es

@[grind] lemma escSeq_nil : escSeq [] = [] := rfl
@[grind] lemma escSeq_cons (e : Elem) (es : List Elem) :
    escSeq (e :: es) = condEscape e :: escSeq es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Escape each element of a sequence individually, returning the list of escaped
   results in the original order. Each element is treated on its own: an element
   already marked safe is emitted unchanged; any other element is HTML-escaped per
   code point. The input sequence is read-only (directive 5: not `mut`). -/
method escapeEach (items : List Elem) return (out : List (List Char))
  ensures out = escSeq items
  do
    -- impl-start
    let mut acc : List (List Char) := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant acc = escSeq (items.drop i)
      done_with i = 0
      decreasing i
    do
      let e := items[i - 1]!
      acc := condEscape e :: acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `escSeq` peels one `condEscape`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma escSeq_drop_step (xs : List Elem) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    escSeq (xs.drop (i - 1)) = condEscape xs[i - 1]! :: escSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, escSeq_cons]

prove_correct escapeEach by
  loom_solve
  rw [escSeq_drop_step items i (by omega) (by omega)]
  simp_all
