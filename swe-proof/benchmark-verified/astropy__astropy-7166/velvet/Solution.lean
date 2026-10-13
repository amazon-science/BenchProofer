import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A class member, abstracted to only the observations that decide whether its
   documentation string is filled in from the corresponding member of a base
   class. `isCallable` and `isProperty` are the two member kinds that may
   participate; `isPublic` is the visibility test; `ownDoc` is the member's own
   documentation (`none` when it has none); `inheritedDoc` is the documentation
   resolved from the base classes in resolution order (`none` when no base
   supplies the member). -/
structure Member where
  isCallable : Bool
  isProperty : Bool
  isPublic : Bool
  ownDoc : Option (List Char)
  inheritedDoc : Option (List Char)
  deriving Inhabited

/- A member receives inherited documentation exactly when it is either a
   callable member or a property, is publicly visible, and carries no
   documentation of its own. Both member kinds qualify. -/
@[grind] def eligible (m : Member) : Bool :=
  (m.isCallable || m.isProperty) && m.isPublic && m.ownDoc.isNone

/- The resulting documentation of a single member: an eligible member takes the
   documentation resolved from its base classes, every other member keeps its
   own. -/
@[grind] def finalDoc (m : Member) : Option (List Char) :=
  if eligible m then m.inheritedDoc else m.ownDoc

/- The resulting documentation of every member, in member order. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def resolvedDocs : List Member → List (Option (List Char))
  | []      => []
  | m :: ms => finalDoc m :: resolvedDocs ms

@[grind] lemma resolvedDocs_nil : resolvedDocs [] = [] := rfl
@[grind] lemma resolvedDocs_cons (m : Member) (ms : List Member) :
    resolvedDocs (m :: ms) = finalDoc m :: resolvedDocs ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveMemberDocstrings (members : List Member)
    return (out : List (Option (List Char)))
  ensures out = resolvedDocs members
  do
    -- impl-start
    let mut result : List (Option (List Char)) := []
    let mut i := members.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ members.length
      invariant result = resolvedDocs (members.drop i)
      done_with i = 0
      decreasing i
    do
      let m := members[i - 1]!
      result := finalDoc m :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `resolvedDocs` peels one `finalDoc`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma resolvedDocs_drop_step (members : List Member) (i : Nat)
    (hi : 0 < i) (hle : i ≤ members.length) :
    resolvedDocs (members.drop (i - 1))
      = finalDoc members[i - 1]! :: resolvedDocs (members.drop i) := by
  have hlt : i - 1 < members.length := by omega
  have hcons : members.drop (i - 1) = members[i - 1]! :: members.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, resolvedDocs_cons]

prove_correct resolveMemberDocstrings by
  loom_solve
  rw [resolvedDocs_drop_step members i (by omega) (by omega)]
  simp_all
