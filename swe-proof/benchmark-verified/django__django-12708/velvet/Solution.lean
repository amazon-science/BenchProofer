import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled operation is a selection over the constraints defined
-- on a given set of columns; each constraint is described by two boolean flags
-- (is it an index? is it a uniqueness constraint?) read directly as fields of
-- `Constraint`, and the selection predicate is modeled directly. There is no
-- unchanged opaque callee whose contract the proof must assume, so there is
-- nothing to over-approximate; the cross-language soundness of the structural
-- refinements is checked mechanically by G-CONF.
-- axioms-end

-- pure-start
/- One constraint defined on the target column set. `name` is its identity;
   `isIndex` records whether the constraint provides an index over the columns;
   `isUnique` records whether it enforces uniqueness. A uniqueness constraint is
   typically backed by an index too, so a constraint may have both flags set. -/
structure Constraint where
  name : String
  isIndex : Bool
  isUnique : Bool
  deriving Inhabited

/- A constraint is selectable for removal of a composite index exactly when it
   is an index AND is NOT a uniqueness constraint. A uniqueness constraint over
   the same columns (even though it is index-backed) must be left untouched. -/
def keep (c : Constraint) : Bool := c.isIndex && !c.isUnique

/- The selection over a whole constraint list: keep each selectable constraint,
   in order. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def selected : List Constraint → List Constraint
  | []      => []
  | c :: cs => (if keep c then [c] else []) ++ selected cs

@[grind] lemma selected_nil : selected [] = [] := rfl
@[grind] lemma selected_cons (c : Constraint) (cs : List Constraint) :
    selected (c :: cs) = (if keep c then [c] else []) ++ selected cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectIndexConstraints (cs : List Constraint) return (out : List Constraint)
  ensures out = selected cs
  do
    -- impl-start
    let mut result : List Constraint := []
    let mut i := cs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cs.length
      invariant result = selected (cs.drop i)
      done_with i = 0
      decreasing i
    do
      let c := cs[i - 1]!
      result := (if keep c then [c] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the constraint at
   `i-1` on the front, so `selected` peels one `keep` test. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selected_drop_step (cs : List Constraint) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cs.length) :
    selected (cs.drop (i - 1))
      = (if keep cs[i - 1]! then [cs[i - 1]!] else []) ++ selected (cs.drop i) := by
  have hlt : i - 1 < cs.length := by omega
  have hcons : cs.drop (i - 1) = cs[i - 1]! :: cs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selected_cons]

prove_correct selectIndexConstraints by
  loom_solve
  rw [selected_drop_step cs i (by omega) (by omega)]
  simp_all
