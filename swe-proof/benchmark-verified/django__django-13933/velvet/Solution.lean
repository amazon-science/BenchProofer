import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The rendering of a parametrized message — the
--  substitution of the offending value into the value placeholder — is the one
--  operation that changes, and it is modeled DEEPLY below (`rendered`), then
--  validated == the real string-interpolation builtin out-of-band by
--  axiom_check.py (G-AX). There is no unchanged callee whose contract the proof
--  must assume.)
-- axioms-end

-- pure-start
/- A fragment of a parametrized message: either a literal code point that passes
   through verbatim, or the value placeholder slot that stands for the offending
   submitted value. A message template is a sequence of such fragments — the
   abstract shape of a human-readable message with a single named substitution
   parameter. -/
inductive Frag where
  | lit (c : Char)
  | valueSlot
  deriving Inhabited, DecidableEq, Repr

/- The rendering of one fragment under a given value: a literal contributes its
   one code point; the value slot is FILLED with the value's code points. This is
   the substitution the parametrized message performs — the placeholder is
   replaced by the value, not left standing. -/
def renderFrag (value : List Char) : Frag → List Char
  | .lit c     => [c]
  | .valueSlot => value

/- The rendering of a whole template under a value: concatenate the per-fragment
   renderings left to right. Front-recursive so a single unfold is available per
   loop step (the Velvet fold pattern). -/
def rendered (value : List Char) : List Frag → List Char
  | []      => []
  | f :: fs => renderFrag value f ++ rendered value fs

@[grind] lemma rendered_nil (value : List Char) : rendered value [] = [] := rfl
@[grind] lemma rendered_cons (value : List Char) (f : Frag) (fs : List Frag) :
    rendered value (f :: fs) = renderFrag value f ++ rendered value fs := rfl

/- Behavioral anchors (definitional). A lone value slot renders to EXACTLY the
   value — the placeholder is substituted, never echoed literally — and a lone
   literal renders to exactly that one code point. Marked `@[grind]` so
   `loom_solve` discharges the corroborating postconditions automatically. -/
@[grind] lemma rendered_valueSlot (value : List Char) :
    rendered value [Frag.valueSlot] = value := by simp [rendered, renderFrag]
@[grind] lemma rendered_lit (value : List Char) (c : Char) :
    rendered value [Frag.lit c] = [c] := by simp [rendered, renderFrag]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When an invalid choice is rejected, the human-readable rejection message is
   produced by interpolating the offending submitted value into the message
   template. The template is a sequence of fragments (literal code points and a
   value placeholder slot); rendering substitutes the offending value at the
   placeholder and passes every literal through unchanged.

   The guarantee the issue demands: the rendered message is the template with the
   value FILLED IN at the placeholder — so a template that carries a value slot
   exposes the offending value, rather than leaving the placeholder standing
   uninterpreted.

   `template` and `value` are read-only (not `mut`): the rendering builds a fresh
   character sequence and mutates neither input (directive 5). -/
method renderInvalidChoice (template : List Frag) (value : List Char) return (out : List Char)
  ensures out = rendered value template
  ensures rendered value [Frag.valueSlot] = value
  ensures ∀ c, rendered value [Frag.lit c] = [c]
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := template.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ template.length
      invariant result = rendered value (template.drop i)
      done_with i = 0
      decreasing i
    do
      let f := template[i - 1]!
      result := renderFrag value f ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the fragment at
   `i-1` on the front, so `rendered` peels one `renderFrag`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma rendered_drop_step (value : List Char) (template : List Frag) (i : Nat)
    (hi : 0 < i) (hle : i ≤ template.length) :
    rendered value (template.drop (i - 1)) =
      renderFrag value template[i - 1]! ++ rendered value (template.drop i) := by
  have hlt : i - 1 < template.length := by omega
  have hcons : template.drop (i - 1) = template[i - 1]! :: template.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, rendered_cons]

prove_correct renderInvalidChoice by
  loom_solve
  rw [rendered_drop_step value template i (by omega) (by omega)]
  simp_all
