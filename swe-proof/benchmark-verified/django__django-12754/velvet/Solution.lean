import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed set computation
--  over three field-name collections: the base entity's fields before, the base
--  entity's fields after, and the newly created derived entity's own fields. No
--  unchanged library callee is consulted, so no callee contract is assumed. Every
--  step is an R/I refinement, validated against the real construction by
--  conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- Whether a single derived-entity field name `n` is one that must be sequenced.

   A name qualifies exactly when the base entity is present BOTH before and after
   the change AND the name was a field of the base before but is no longer a field
   of the base after — i.e. it was removed from the base. The presence of the base
   on both sides is carried as `Option (List Int)`: `none` means the base entity
   is absent from that side (so nothing qualifies); `some fields` carries the
   base's field-name set on that side. The decision is by PRESENCE on both sides,
   not by whether either field set is non-empty. -/
def isMoved (oldBase newBase : Option (List Int)) (n : Int) : Bool :=
  match oldBase, newBase with
  | some ob, some nb => decide (n ∈ ob) && decide (n ∉ nb)
  | _, _             => false

@[grind] lemma isMoved_none_left (newBase : Option (List Int)) (n : Int) :
    isMoved none newBase n = false := rfl
@[grind] lemma isMoved_none_right (oldBase : Option (List Int)) (n : Int) :
    isMoved oldBase none n = false := by
  cases oldBase <;> rfl

/- The field names of the derived entity that must be sequenced, in derived-field
   order: keep each derived field name that was removed from the base. This is the
   per-element expansion of the derived entity's field list. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
def movedFold (oldBase newBase : Option (List Int)) : List Int → List Int
  | []      => []
  | n :: ns => (if isMoved oldBase newBase n then [n] else [])
                 ++ movedFold oldBase newBase ns

@[grind] lemma movedFold_nil (oldBase newBase : Option (List Int)) :
    movedFold oldBase newBase [] = [] := rfl
@[grind] lemma movedFold_cons (oldBase newBase : Option (List Int))
    (n : Int) (ns : List Int) :
    movedFold oldBase newBase (n :: ns) =
      (if isMoved oldBase newBase n then [n] else []) ++ movedFold oldBase newBase ns := rfl

/- If the base entity is absent before the change, nothing qualifies. -/
@[grind] lemma movedFold_none_left (newBase : Option (List Int)) (ns : List Int) :
    movedFold none newBase ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [movedFold_cons, isMoved_none_left]; simpa using ih

/- If the base entity is absent after the change, nothing qualifies. -/
@[grind] lemma movedFold_none_right (oldBase : Option (List Int)) (ns : List Int) :
    movedFold oldBase none ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [movedFold_cons, isMoved_none_right]; simpa using ih

/- A sequenced name is always one of the derived entity's own fields (nothing is
   invented) and genuinely qualifies. Proven by induction; `@[grind]` so the
   corresponding postcondition discharges automatically. -/
@[grind] lemma movedFold_mem (oldBase newBase : Option (List Int)) (ns : List Int) :
    ∀ n, n ∈ movedFold oldBase newBase ns → n ∈ ns ∧ isMoved oldBase newBase n = true := by
  induction ns with
  | nil => intro n h; simp [movedFold] at h
  | cons c cs ih =>
      intro n h
      rw [movedFold_cons] at h
      by_cases hk : isMoved oldBase newBase c = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hnc | htail
        · subst hnc; exact ⟨List.mem_cons_self, hk⟩
        · obtain ⟨hmem, hkeep⟩ := ih n htail
          exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
      · rw [if_neg hk] at h
        rw [List.nil_append] at h
        obtain ⟨hmem, hkeep⟩ := ih n h
        exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a new derived entity is created that inherits from an existing base
   entity, some of the derived entity's own fields may be fields that were just
   removed from the base entity (moved down onto the subclass in the same step).
   Creating the derived entity must be sequenced AFTER those base fields are
   removed; otherwise the two definitions of the same field name collide.

   This routine determines exactly which of the derived entity's field names need
   that ordering: a field name qualifies iff the base entity exists both before
   and after the change and the name was a field of the base before but not after
   (it was removed from the base) — restricted to the derived entity's own fields.

   The base entity's field-name sets are read as optionals: `none` when the base
   entity is absent from that side of the change (then nothing qualifies),
   `some names` otherwise. Field names are modeled as distinct integer identifiers
   (`List Int`, mapping.md §2). The result is the list of qualifying derived-field
   names, in derived-field order.

   `oldBaseFields`, `newBaseFields` and `derivedFields` are read-only (none
   `mut`): the routine only reads them and builds a fresh result, mutating no
   input (directive 5). -/
method movedBaseFields (oldBaseFields : Option (List Int))
    (newBaseFields : Option (List Int)) (derivedFields : List Int)
    return (out : List Int)
  ensures out = movedFold oldBaseFields newBaseFields derivedFields
  ensures oldBaseFields = none → out = []
  ensures newBaseFields = none → out = []
  ensures ∀ n, n ∈ out → n ∈ derivedFields ∧ isMoved oldBaseFields newBaseFields n = true
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := derivedFields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ derivedFields.length
      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
      done_with i = 0
      decreasing i
    do
      let n := derivedFields[i - 1]!
      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `movedFold` peels one keep-decision. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma movedFold_drop_step (oldBase newBase : Option (List Int)) (xs : List Int)
    (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    movedFold oldBase newBase (xs.drop (i - 1)) =
      (if isMoved oldBase newBase xs[i - 1]! then [xs[i - 1]!] else [])
        ++ movedFold oldBase newBase (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, movedFold_cons]

prove_correct movedBaseFields by
  loom_solve
  rw [movedFold_drop_step oldBaseFields newBaseFields derivedFields i (by omega) (by omega)]
  rw [‹result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)›]
