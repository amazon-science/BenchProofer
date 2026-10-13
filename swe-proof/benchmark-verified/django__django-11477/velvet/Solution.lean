import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none) The modeled operation post-processes values already produced by the
-- pattern engine; it calls no further routine whose contract must be assumed.
-- axioms-end

-- pure-start
/- A captured named group: its name paired with the value the engine bound to
   it, or `none` when the group took part in no alternative that actually
   participated in the overall capture (an optional group that contributed
   nothing). -/
abbrev Named := String × Option String

/- Per-group contribution to the keyword bindings: a group that bound a value
   contributes itself; a group that bound nothing contributes nothing. -/
def keepOne (p : Named) : List Named :=
  if p.2.isSome then [p] else []

/- The keyword bindings of a whole capture list: concatenate the per-group
   contributions, in order. Front-recursive so a single unfold is available per
   loop step (the fold pattern). -/
def keepPresent : List Named → List Named
  | []      => []
  | p :: ps => keepOne p ++ keepPresent ps

@[grind] lemma keepPresent_nil : keepPresent [] = [] := rfl
@[grind] lemma keepPresent_cons (p : Named) (ps : List Named) :
    keepPresent (p :: ps) = keepOne p ++ keepPresent ps := rfl
-- pure-end

/- The result of binding a single capture: the keyword bindings, plus the
   positional bindings (used only when there are no keyword bindings). -/
structure Bindings where
  named : List Named
  positional : List String
deriving Repr, Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method bindCaptures (namedGroups : List Named) (positionalGroups : List String)
    return (out : Bindings)
  ensures out.named = keepPresent namedGroups
  ensures out.positional = (if out.named = [] then positionalGroups else [])
  do
    -- impl-start
    let mut result : List Named := []
    let mut i := namedGroups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ namedGroups.length
      invariant result = keepPresent (namedGroups.drop i)
      done_with i = 0
      decreasing i
    do
      let p := namedGroups[i - 1]!
      result := keepOne p ++ result
      i := i - 1
    return ⟨result, if result = [] then positionalGroups else []⟩
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `keepPresent` peels one `keepOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keepPresent_drop_step (xs : List Named) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    keepPresent (xs.drop (i - 1)) = keepOne xs[i - 1]! ++ keepPresent (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepPresent_cons]

prove_correct bindCaptures by
  loom_solve
  rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]
  simp_all
