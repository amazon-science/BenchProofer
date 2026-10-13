import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure data-flow over a record's attribute cells: assigning the record's
   primary identity writes a value to a set of attribute names determined solely
   by the record's own identity layout, which is the read-only input `slots`
   here. Every observable is computed from the inputs; nothing is borrowed from
   an oracle. There is therefore no consumed axiom and no deep-model reference to
   a foreign callee (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A record's attribute cells, addressed by an attribute identity (`Nat`). A
   cell holds an optional scalar: `none` is the "unset / cleared" value, `some n`
   a concrete identity number. -/
abbrev Store := Nat → Option Int

/- One inherited-identity slot a record carries. `attr` is the attribute cell
   that holds this identity; `isPrimary` flags whether this slot coincides with
   the record's own primary identity cell (in which case it must NOT be written
   separately — the primary write below covers it). A record with no inherited
   identities carries an empty slot list. -/
structure Slot where
  isPrimary : Bool
  attr : Nat
deriving DecidableEq, Inhabited, Repr

/- Fold one slot into the attribute store while assigning `value`: a slot that is
   the primary identity is left to the dedicated primary write (no change here);
   any other slot has its attribute cell set to `value`. -/
def writeSlot (s : Store) (value : Option Int) (l : Slot) : Store :=
  if l.isPrimary then s else (fun k => if k = l.attr then value else s k)

/- The store after writing `value` into every non-primary inherited-identity
   slot, in slot order. The dedicated primary write is applied separately by the
   caller. -/
def writtenSlots (s : Store) (slots : List Slot) (value : Option Int) : Store :=
  slots.foldl (fun g l => writeSlot g value l) s

/- Closed-form characterization: a cell `k` ends up holding `value` iff some
   non-primary slot names `k`; otherwise it is unchanged. This pins the fold to a
   membership predicate over the input slots, so the result must be PRODUCED by
   writing each slot — not echoed from an oracle. -/
lemma writtenSlots_spec (value : Option Int) (slots : List Slot) :
    ∀ (g : Store) (k : Nat),
      writtenSlots g slots value k
        = if slots.any (fun l => !l.isPrimary && l.attr == k) then value else g k := by
  unfold writtenSlots
  induction slots with
  | nil => intro g k; simp
  | cons hd tl ih =>
    intro g k
    rw [List.foldl_cons, List.any_cons, ih (writeSlot g value hd) k]
    by_cases hpk : hd.isPrimary
    · simp [writeSlot, hpk]
    · by_cases hk : k = hd.attr
      · simp [writeSlot, hpk, hk]
      · have hne : ¬ hd.attr = k := fun h => hk h.symm
        simp [writeSlot, hpk, hk, hne]

/- A non-primary slot's attribute cell ends up holding the assigned `value`: the
   propagation guarantee the spec needs. -/
lemma writtenSlots_hits (s : Store) (slots : List Slot) (value : Option Int)
    (l : Slot) (hl : l ∈ slots) (hp : l.isPrimary = false) :
    writtenSlots s slots value l.attr = value := by
  rw [writtenSlots_spec value slots s l.attr]
  have hmem : slots.any (fun l' => !l'.isPrimary && l'.attr == l.attr) = true :=
    List.any_eq_true.mpr ⟨l, hl, by simp [hp]⟩
  rw [hmem]; simp

/- Forward-fold step: extending the consumed prefix by one slot writes that slot
   into the store built from the shorter prefix. The single goal `loom_solve`
   leaves for the loop body (the Velvet forward-fold pattern, plan §5.4). -/
lemma writtenSlots_take_step (s : Store) (slots : List Slot) (value : Option Int)
    (i : Nat) (hi : i < slots.length) :
    (slots.take (i + 1)).foldl (fun g l => writeSlot g value l) s
      = writeSlot ((slots.take i).foldl (fun g l => writeSlot g value l) s) value slots[i]! := by
  have hcons : slots.take (i + 1) = slots.take i ++ [slots[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assign `value` to the record's primary identity. The record carries a primary
   identity cell `pk` plus a list of inherited-identity `slots`. Assigning the
   primary identity must set the primary cell AND every distinct inherited
   identity cell to the same `value`, so the whole identity of the record is
   reset together — leaving an inherited identity cell holding its old value is
   the defect this guards against.

   `attrs`, `slots`, `value`, `pk` are read-only: the method builds and returns a
   fresh store and never mutates its inputs. -/
method assignPrimaryIdentity (attrs : Store) (slots : List Slot) (value : Option Int) (pk : Nat)
    return (out : Store)
  ensures out = (fun k => if k = pk then value else writtenSlots attrs slots value k)
  ensures out pk = value
  ensures ∀ l ∈ slots, l.isPrimary = false → out l.attr = value
  do
    -- impl-start
    let mut result : Store := attrs
    let mut i := 0
    while i < slots.length
      invariant i ≤ slots.length
      invariant result = (slots.take i).foldl (fun g l => writeSlot g value l) attrs
      done_with i = slots.length
      decreasing slots.length - i
    do
      let l := slots[i]!
      result := writeSlot result value l
      i := i + 1
    return (fun k => if k = pk then value else result k)
    -- impl-end

prove_correct assignPrimaryIdentity by
  loom_solve
  case «invariant_2: result = (slots.take i).foldl (fun g l => writeSlot g value l) attrs» =>
    have hi : i < slots.length := by omega
    rw [invariant_2, writtenSlots_take_step attrs slots value i hi]
  case «ensures_1: ∀ l ∈ slots, l.isPrimary = false → out l.attr = value» =>
    intro l hl hp
    have hhit := writtenSlots_hits attrs slots value l hl hp
    by_cases hkpk : l.attr = pk
    · simp [hkpk]
    · simp only [hkpk, if_false]
      simp only [writtenSlots] at hhit ⊢
      simp_all
  all_goals simp_all [writtenSlots]
