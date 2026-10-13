import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. The field-cleaning step on the
   modeled inputs is the identity on the resolved value (a stored timestamp fed
   to a per-field cleaner that returns it unchanged), so it is transliterated as
   an identity op (refinement.md, tag I) rather than axiomatized. The behaviour
   that actually changes — how a read-only slot's value is resolved — is modeled
   directly in the `pure` region below. -/
-- axioms-end

-- pure-start
/- A timestamp's observable components: a primary count and a finer sub-count.
   (Models the value a per-field cleaner produces; the finer sub-count is the
   part a coarse presentation cannot represent.) -/
structure Stamp where
  sec : Int
  sub : Int
deriving Inhabited, DecidableEq

/- A single field slot the cleaner walks over.
   * `readOnly` — the slot's value is held internally, not taken from supplied data.
   * `coarse`   — the slot's presentation cannot carry the finer sub-count, so
                  the resolved stored value drops it to 0 (standardized handling).
   * `stored`   — the slot's resolved stored value (evaluated once).
   * `given`    — the value supplied for the slot through ordinary data. -/
structure FieldSlot where
  readOnly : Bool
  coarse   : Bool
  stored   : Stamp
  given    : Stamp
deriving Inhabited, DecidableEq

/- The stored value as a slot actually exposes it: a coarse slot zeroes the
   finer sub-count; otherwise the stored value passes through unchanged. -/
def initialFor (f : FieldSlot) : Stamp :=
  if f.coarse then { f.stored with sub := 0 } else f.stored

/- The value used to clean one slot: a read-only slot uses its exposed stored
   value; any other slot uses the value supplied through data. -/
def slotValue (f : FieldSlot) : Stamp :=
  if f.readOnly then initialFor f else f.given

/- The per-slot cleaned values across the whole field list. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def cleanedSeq : List FieldSlot → List Stamp
  | []      => []
  | f :: fs => slotValue f :: cleanedSeq fs

@[grind] lemma cleanedSeq_nil : cleanedSeq [] = [] := rfl
@[grind] lemma cleanedSeq_cons (f : FieldSlot) (fs : List FieldSlot) :
    cleanedSeq (f :: fs) = slotValue f :: cleanedSeq fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method cleanFields (fields : List FieldSlot) return (out : List Stamp)
  ensures out = cleanedSeq fields
  do
    -- impl-start
    let mut result : List Stamp := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = cleanedSeq (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := slotValue f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the slot at `i-1`
   on the front, so `cleanedSeq` peels one `slotValue`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma cleanedSeq_drop_step (fields : List FieldSlot) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    cleanedSeq (fields.drop (i - 1)) = slotValue fields[i - 1]! :: cleanedSeq (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, cleanedSeq_cons]

prove_correct cleanFields by
  loom_solve
  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]
  simp_all
