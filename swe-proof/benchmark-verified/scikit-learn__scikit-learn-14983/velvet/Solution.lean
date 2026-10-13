import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Resolve the value displayed for one named parameter of an object's textual
   representation. The primary source is the object's own attribute table
   `attrs`; a parameter absent from it (or carrying no value) reads as `none`.
   When the primary source yields no value and a secondary parameter store is
   present (`hasFallback`), the value is taken from that store `fallback`
   instead. Provenance + executable soundness check: mapping.md / axiom_check.py
   (G-AX). -/
def resolveOne (attrs fallback : List (String × Int)) (hasFallback : Bool)
    (key : String) : Option Int :=
  match attrs.lookup key with
  | some v => some v
  | none   => if hasFallback then fallback.lookup key else none

/- The values displayed for a list of parameter names, in the given order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def resolveAll (attrs fallback : List (String × Int)) (hasFallback : Bool) :
    List String → List (Option Int)
  | []      => []
  | k :: ks => resolveOne attrs fallback hasFallback k
                 :: resolveAll attrs fallback hasFallback ks

@[grind] lemma resolveAll_nil (attrs fallback : List (String × Int)) (hf : Bool) :
    resolveAll attrs fallback hf [] = [] := rfl
@[grind] lemma resolveAll_cons (attrs fallback : List (String × Int)) (hf : Bool)
    (k : String) (ks : List String) :
    resolveAll attrs fallback hf (k :: ks)
      = resolveOne attrs fallback hf k :: resolveAll attrs fallback hf ks := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method buildReprValues (keys : List String) (attrs : List (String × Int)) (fallback : List (String × Int)) (hasFallback : Bool) return (out : List (Option Int))
  ensures out = resolveAll attrs fallback hasFallback keys
  do
    -- impl-start
    let mut result : List (Option Int) := []
    let mut i := keys.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ keys.length
      invariant result = resolveAll attrs fallback hasFallback (keys.drop i)
      done_with i = 0
      decreasing i
    do
      let k := keys[i - 1]!
      result := resolveOne attrs fallback hasFallback k :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `resolveAll` peels one `resolveOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma resolveAll_drop_step (keys : List String) (attrs fallback : List (String × Int))
    (hf : Bool) (i : Nat) (hi : 0 < i) (hle : i ≤ keys.length) :
    resolveAll attrs fallback hf (keys.drop (i - 1))
      = resolveOne attrs fallback hf keys[i - 1]! :: resolveAll attrs fallback hf (keys.drop i) := by
  have hlt : i - 1 < keys.length := by omega
  have hcons : keys.drop (i - 1) = keys[i - 1]! :: keys.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, resolveAll_cons]

prove_correct buildReprValues by
  loom_solve
  rw [resolveAll_drop_step keys attrs fallback hasFallback i (by omega) (by omega)]
  simp_all
