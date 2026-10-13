import Mathlib
-- imports-end

/-!
Converting an array-like object into its indexed form should yield an
INDEPENDENT object: the returned object must not be the same object as the
source, so that later in-place edits to the returned object cannot reach back
and alter the source. We model the universe of live objects as a heap (an
`Array` of records); an object's identity is its slot index (a handle). The
modeled operation takes a source handle and returns the updated heap together
with the handle of the produced object.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: producing the independent
-- object is modeled DEEPLY as a fresh heap allocation duplicating the source
-- record, rather than abstracted behind an axiom. The proof agent may add
-- `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A live object, holding the touched fields: its axis labels (`dims`, a list
of label codes) and an opaque contents code (`data`). Two objects are equal
exactly when both fields agree. -/
structure VarRec where
  dims : List Nat
  data : Nat
deriving DecidableEq, Repr, Inhabited
-- pure-end

-- post-conditions-start
/-- The result of converting the object at handle `src` to its indexed form.

`result.1` is the resulting heap, `result.2` the handle of the produced object.

* Independence: the produced handle is a brand-new slot (`= heap.size`), hence
  distinct from every pre-existing handle — in particular from `src`. This is
  what guarantees that mutating the produced object later cannot affect `src`.
* The heap grows by exactly one slot.
* Contents: the produced object carries the same fields as the source object.
* Frame: every pre-existing object is left untouched. -/
def problem_spec_toIndexVariable
    (heap : Array VarRec) (src : Nat)
    (result : Array VarRec × Nat) : Prop :=
  result.2 = heap.size ∧
  result.1.size = heap.size + 1 ∧
  result.1[result.2]! = heap[src]! ∧
  (∀ i, i < heap.size → result.1[i]! = heap[i]!)
-- post-conditions-end

-- impl-start
def implementation_toIndexVariable
    (heap : Array VarRec) (src : Nat) : Array VarRec × Nat := Id.run do
  let mut h := heap
  let fresh := h[src]!        -- the contents of the source object
  let handle := h.size        -- identity of the produced object: a new slot
  h := h.push fresh           -- allocate the produced object as an independent slot
  return (h, handle)
-- impl-end

-- proof-start
theorem correct_toIndexVariable :
    ∀ (heap : Array VarRec) (src : Nat), src < heap.size →
    problem_spec_toIndexVariable heap src
      (implementation_toIndexVariable heap src) := by
  intro heap src hsrc
  unfold problem_spec_toIndexVariable implementation_toIndexVariable
  simp only [Id.run, pure]
  refine ⟨trivial, ?_, ?_, ?_⟩
  · simp [Array.size_push]
  · simp [Array.getElem!_eq_getD]
  · intro i hi
    rw [Array.getElem!_eq_getD, Array.getElem!_eq_getD,
        Array.getD_eq_getD_getElem?, Array.getD_eq_getD_getElem?,
        Array.getElem?_push]
    simp [Nat.ne_of_lt hi, hi]
-- proof-end
