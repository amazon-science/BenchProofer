import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. Each element/key/value of the container is
--  supplied as an already-rendered carrier: `reprText` is the text the
--  recursive element renderer produces for it, `strText` its shallow textual
--  form. These are outputs of an unchanged rendering helper, so they are part
--  of the input carrier — not opaque oracles. The behaviour under
--  specification — assembling the brace-delimited, comma-separated rendering
--  from the RECURSIVE per-element text — is modeled DEEPLY below. Nothing is
--  borrowed from an answer key. See mapping.md.)
-- axioms-end

-- pure-start
/- A container element, carrying the two textual forms the assembler may pick
   for it: `reprText`, the text produced by the recursive element renderer
   (the same renderer applied to the whole container), and `strText`, the
   shallow textual form. The faithful rendering selects `reprText`. -/
structure Obj where
  reprText : List Char
  strText  : List Char
deriving DecidableEq, Inhabited

/- The recursive element renderer applied to one element: it yields that
   element's own fully-rendered text. -/
def doprint (o : Obj) : List Char := o.reprText

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

/- The rendering of one key↦value entry: the key's recursive text, the
   separator ": ", then the value's recursive text. Both components are
   recursive renderings (`doprint`), never the shallow form. -/
def kvText (p : Obj × Obj) : List Char :=
  doprint p.1 ++ ": ".toList ++ doprint p.2

/- The fully assembled mapping rendering: the entries, each rendered key↦value
   via the recursive renderer, joined by ", " and wrapped in braces. The empty
   mapping renders to "{}". -/
def dictRender (items : List (Obj × Obj)) : List Char :=
  "{".toList ++ joinComma (items.map kvText) ++ "}".toList

/- The fully assembled collection rendering: when empty it renders to the
   explicit empty-collection token "set()"; otherwise its elements, each
   rendered via the recursive renderer, joined by ", " and wrapped in braces. -/
def setRender (elems : List Obj) : List Char :=
  if elems = [] then "set()".toList
  else "{".toList ++ joinComma (elems.map doprint) ++ "}".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a mapping of already-rendered elements as ordinary supported code:
   an opening brace, then each entry "key: value" — both key and value rendered
   by the RECURSIVE element renderer (`doprint`), not the shallow textual form —
   joined by ", ", then a closing brace. `items` is the ordered list of
   key↦value pairs and is read-only (not `mut`); the loop builds a fresh result
   and never mutates its input (directive 5). -/
method printDict (items : List (Obj × Obj)) return (out : List Char)
  ensures out = dictRender items
  do
    -- impl-start
    let mut joined : List Char := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant joined = joinComma ((items.map kvText).drop i)
      done_with i = 0
      decreasing i
    do
      let piece := kvText items[i - 1]!
      joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
      i := i - 1
    return "{".toList ++ joined ++ "}".toList
    -- impl-end

/- Render a collection of already-rendered elements as ordinary supported code:
   if it is empty, the explicit empty-collection token "set()"; otherwise an
   opening brace, its elements rendered by the RECURSIVE element renderer
   (`doprint`) and joined by ", ", then a closing brace. `elems` is read-only. -/
method printSet (elems : List Obj) return (out : List Char)
  ensures out = setRender elems
  do
    -- impl-start
    -- Pre-image skeleton: the collection fell through to the generic textual
    -- fallback, which renders each element by its SHALLOW textual form
    -- (`.strText`) rather than the recursive element renderer. The frozen spec
    -- requires `setRender` (recursive `doprint` per element), so prove_correct
    -- MUST fail.
    if elems = [] then
      return "set()".toList
    else
      let mut joined : List Char := []
      let mut i := elems.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ elems.length
        invariant joined = joinComma ((elems.map doprint).drop i)
        done_with i = 0
        decreasing i
      do
        let piece := elems[i - 1]!.strText
        joined := if i = elems.length then piece else piece ++ ", ".toList ++ joined
        i := i - 1
      return "{".toList ++ joined ++ "}".toList
    -- impl-end

/- The backward-fold step (mapping entries): dropping one fewer entry exposes
   the entry at `i-1` on the front. When it is the last entry it joins to
   itself; otherwise `joinComma` peels it with its trailing separator. The
   single goal `loom_solve` leaves for the loop body. -/
lemma joinComma_drop_step_kv (items : List (Obj × Obj)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    joinComma ((items.map kvText).drop (i - 1)) =
      (if i = items.length then kvText items[i - 1]!
       else kvText items[i - 1]! ++ ", ".toList ++ joinComma ((items.map kvText).drop i)) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hmap1 : (items.map kvText).drop (i - 1) = (items.drop (i-1)).map kvText :=
    (List.map_drop ..).symm
  have hmap2 : (items.map kvText).drop i = (items.drop i).map kvText :=
    (List.map_drop ..).symm
  rw [hmap1, hmap2, hcons, List.map_cons]
  by_cases hempty : (items.drop i).map kvText = []
  · have hi_eq : i = items.length := by
      have h0 : ((items.drop i).map kvText).length = 0 := by rw [hempty]; rfl
      rw [List.length_map, List.length_drop] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ items.length := by
      intro he
      apply hempty
      have h0 : ((items.drop i).map kvText).length = 0 := by
        rw [List.length_map, List.length_drop, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

/- The backward-fold step (collection elements): identical reasoning for the
   element renderer `doprint` in place of the entry renderer `kvText`. -/
lemma joinComma_drop_step_elem (elems : List Obj) (i : Nat)
    (hi : 0 < i) (hle : i ≤ elems.length) :
    joinComma ((elems.map doprint).drop (i - 1)) =
      (if i = elems.length then doprint elems[i - 1]!
       else doprint elems[i - 1]! ++ ", ".toList ++ joinComma ((elems.map doprint).drop i)) := by
  have hlt : i - 1 < elems.length := by omega
  have hcons : elems.drop (i - 1) = elems[i - 1]! :: elems.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  have hmap1 : (elems.map doprint).drop (i - 1) = (elems.drop (i-1)).map doprint :=
    (List.map_drop ..).symm
  have hmap2 : (elems.map doprint).drop i = (elems.drop i).map doprint :=
    (List.map_drop ..).symm
  rw [hmap1, hmap2, hcons, List.map_cons]
  by_cases hempty : (elems.drop i).map doprint = []
  · have hi_eq : i = elems.length := by
      have h0 : ((elems.drop i).map doprint).length = 0 := by rw [hempty]; rfl
      rw [List.length_map, List.length_drop] at h0; omega
    rw [hempty, joinComma_single, if_pos hi_eq]
  · have hi_ne : i ≠ elems.length := by
      intro he
      apply hempty
      have h0 : ((elems.drop i).map doprint).length = 0 := by
        rw [List.length_map, List.length_drop, he]; omega
      exact List.length_eq_zero_iff.mp h0
    rw [joinComma_cons_ne _ _ hempty, if_neg hi_ne]

prove_correct printDict by
  loom_solve
  all_goals
    first
      | (rw [joinComma_drop_step_kv items i (by omega) (by omega)]; simp_all)
      | (rw [show items.length = (items.map kvText).length from (List.length_map ..).symm,
             List.drop_length]; rfl)
      | simp_all [dictRender]

prove_correct printSet by
  loom_solve
  all_goals
    first
      | (rw [joinComma_drop_step_elem elems i (by omega) (by omega)]; simp_all)
      | (rw [show elems.length = (elems.map doprint).length from (List.length_map ..).symm,
             List.drop_length]; rfl)
      | simp_all [setRender]
