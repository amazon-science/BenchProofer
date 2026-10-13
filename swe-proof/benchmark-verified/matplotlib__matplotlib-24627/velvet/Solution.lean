import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled behaviour is the deparenting of the artists that were
-- attached to the axes — a direct field update on each artist, modeled deeply
-- below (`deparent` / `deparentAll`). There is no unchanged opaque callee whose
-- contract the proof consumes: every step is an attribute write or a structural
-- traversal (a type refinement, mapping.md §2), whose cross-language fidelity is
-- checked mechanically by G-CONF, so there is nothing to over-approximate here.
-- axioms-end

-- pure-start
/- One artist attached to the axes, viewed through the two attributes the issue
   talks about: whether its `.axes` link is set (`hasAxes`) and whether its
   `.figure` link is set (`hasFigure`). An attached artist has both set; a
   deparented artist has both unset (both attributes are `None`). -/
structure Artist where
  hasAxes : Bool
  hasFigure : Bool
  deriving Inhabited, Repr

/- Deparent a single artist: unset BOTH its `.axes` and its `.figure` link
   (each becomes `None`). Setting only one is not enough — a deparented artist
   has neither link. -/
def deparent (_a : Artist) : Artist := { hasAxes := false, hasFigure := false }

/- Deparent every artist that was attached, in order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def deparentAll : List Artist → List Artist
  | []      => []
  | a :: rest => deparent a :: deparentAll rest

@[grind] lemma deparentAll_nil : deparentAll [] = [] := rfl
@[grind] lemma deparentAll_cons (a : Artist) (rest : List Artist) :
    deparentAll (a :: rest) = deparent a :: deparentAll rest := rfl
-- pure-end

-- pre-conditions-start
-- (clearAxes: the artists that were attached to the axes, in order.)
-- pre-conditions-end

-- post-conditions-start
-- (clearAxes: every formerly-attached artist comes back deparented — both its
--  `.axes` and `.figure` links unset — and none is left attached.)
-- post-conditions-end

/- Clearing the axes. The input is the sequence of artists that were attached to
   the axes before the clear. The result is that same sequence with every artist
   deparented: each one's `.axes` and `.figure` attributes unset. The issue: a
   plain clear emptied the collection but left each former artist still pointing
   back at the axes; the required behaviour deparents each one. -/
method clearAxes (children : List Artist) return (out : List Artist)
  ensures out = deparentAll children
  do
    -- impl-start
    let mut result : List Artist := []
    let mut i := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant result = deparentAll (children.drop i)
      done_with i = 0
      decreasing i
    do
      let a := children[i - 1]!
      result := deparent a :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the artist at
   `i-1` on the front, so `deparentAll` peels one `deparent`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma deparentAll_drop_step (children : List Artist) (i : Nat)
    (hi : 0 < i) (hle : i ≤ children.length) :
    deparentAll (children.drop (i - 1)) = deparent children[i - 1]! :: deparentAll (children.drop i) := by
  have hlt : i - 1 < children.length := by omega
  have hcons : children.drop (i - 1) = children[i - 1]! :: children.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, deparentAll_cons]

prove_correct clearAxes by
  loom_solve
  rw [deparentAll_drop_step children i (by omega) (by omega)]
  simp_all
