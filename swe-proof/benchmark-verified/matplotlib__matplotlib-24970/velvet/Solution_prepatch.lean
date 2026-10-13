import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- pure-start
abbrev underSlot   (paletteSize : Nat) : Nat := paletteSize
abbrev overSlot    (paletteSize : Nat) : Nat := paletteSize + 1
abbrev invalidSlot (paletteSize : Nat) : Nat := paletteSize + 2

/- One already-classified input element. After the upstream value examination,
   each element reaches the slot-assignment step as exactly one of four classes:
   an ordinary in-range index `k`, an out-of-range-low element, an
   out-of-range-high element, or an invalid (no-value) element. -/
inductive Cell where
  | inPalette (k : Nat)
  | belowRange
  | aboveRange
  | invalid
  deriving DecidableEq, Inhabited, Repr

/- The lookup-table slot one element resolves to.

   The three out-of-range / invalid classes resolve to their own reserved trailing
   slot (`underSlot = N`, `overSlot = N+1`, `invalidSlot = N+2`).

   An ordinary index keeps the value it carries ONLY while that value is strictly
   inside the palette. The reserved-marker assignment is NOT a case split over
   disjoint classes evaluated independently: it is a SEQUENCE of selections over
   one container, and the FIRST selection takes every element whose index is not
   strictly below `paletteSize`. That includes an index whose value happens to
   coincide with one of the reserved markers. Such an element does not keep its
   index — the first selection has already taken it and stored `overSlot
   paletteSize` over it, and no later selection takes it back. So `.inPalette k`
   with `paletteSize ≤ k` describes exactly the situation `.aboveRange` describes,
   and this function must send the two to the same slot; anything else would claim
   a resolved value the selection sequence never produces.
   Provenance: mapping.md §2.4 (selection order), soundness: axiom_check.py (G-AX).

   Consequence, and the reason the resolved-slot sequence is informative at all:
   `underSlot` and `invalidSlot` are reachable from their OWN class and from
   nowhere else, so pinning the resolved slot of an element pins which of those two
   ends it came from.

   The resolved slot VALUE is the same regardless of the container width — only
   whether the container can represent the reserved markers changes. -/
def slotOf (paletteSize : Nat) : Cell → Nat
  | .inPalette k => if k < paletteSize then k else overSlot paletteSize
  | .belowRange  => underSlot paletteSize
  | .aboveRange  => overSlot paletteSize
  | .invalid     => invalidSlot paletteSize

@[grind] lemma slotOf_inPalette_of_lt {paletteSize k : Nat} (h : k < paletteSize) :
    slotOf paletteSize (.inPalette k) = k := by
  simp [slotOf, h]

/- An ordinary index that is not strictly inside the palette resolves exactly
   where an out-of-range-high element resolves: the first selection took it. -/
@[grind] lemma slotOf_inPalette_of_ge {paletteSize k : Nat} (h : paletteSize ≤ k) :
    slotOf paletteSize (.inPalette k) = overSlot paletteSize := by
  simp [slotOf, Nat.not_lt.mpr h]

/- No ordinary index resolves to `underSlot`, whatever value it carries: below
   `paletteSize` it resolves to itself, and at or above `paletteSize` the first
   selection sends it to `overSlot`. Likewise none resolves to `invalidSlot`. -/
lemma slotOf_inPalette_ne_underSlot (paletteSize k : Nat) :
    slotOf paletteSize (.inPalette k) ≠ underSlot paletteSize := by
  simp only [slotOf, underSlot, overSlot]
  split <;> omega

lemma slotOf_inPalette_ne_invalidSlot (paletteSize k : Nat) :
    slotOf paletteSize (.inPalette k) ≠ invalidSlot paletteSize := by
  simp only [slotOf, invalidSlot, overSlot]
  split <;> omega

/- The resolved slot sequence of a whole classified row. Front-recursive so a
   single unfold is available per step. -/
def slotSeq (paletteSize : Nat) : List Cell → List Nat
  | []      => []
  | c :: cs => slotOf paletteSize c :: slotSeq paletteSize cs

@[grind] lemma slotSeq_nil (paletteSize : Nat) :
    slotSeq paletteSize [] = [] := rfl
@[grind] lemma slotSeq_cons (paletteSize : Nat) (c : Cell) (cs : List Cell) :
    slotSeq paletteSize (c :: cs) =
      slotOf paletteSize c :: slotSeq paletteSize cs := rfl

lemma slotSeq_eq_map (paletteSize : Nat) (cs : List Cell) :
    slotSeq paletteSize cs = cs.map (slotOf paletteSize) := by
  induction cs with
  | nil => rfl
  | cons c cs ih => rw [slotSeq_cons, List.map_cons, ih]

@[grind] lemma slotSeq_length (paletteSize : Nat) (cs : List Cell) :
    (slotSeq paletteSize cs).length = cs.length := by
  rw [slotSeq_eq_map, List.length_map]

/- The three reserved trailing markers are the highest slots the resolution can
   ever materialise; `invalidSlot paletteSize = paletteSize + 2` is the largest,
   so a container admitting values up to `invalidSlot paletteSize` (representable
   range `≥ paletteSize + 3`) admits EVERY reserved marker as well as every
   ordinary index. -/
lemma reserved_le_invalidSlot (paletteSize : Nat) :
    underSlot paletteSize ≤ invalidSlot paletteSize ∧
    overSlot paletteSize ≤ invalidSlot paletteSize := by
  constructor <;> simp [underSlot, overSlot, invalidSlot]
-- pure-end

-- axioms-start
/- The resolved index CONTAINER: the integer container the slot-assignment step
   leaves the per-element indices in, and the one the palette read then addresses
   rows with. A container is not the bare tuple of the values it reads back — it
   also has the integer width those values are stored in — so two containers that
   read back the same indices in different widths are different objects, and the
   model keeps the representation abstract, reading the indices out with `slotsOf`.
   The two ways a container can come to exist are kept apart on purpose:
   `assignReserved` PRODUCES one by carrying out the reserved-marker assignment,
   while `rowOf` merely BUILDS one out of index values already in hand.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
opaque IndexRow : Type

/- The per-element index sequence readable from a container — exactly what the
   palette read consumes. An UNCHANGED read, invoked by both twins. Provenance +
   executable soundness check: mapping.md / axiom_check.py (G-AX). -/
opaque slotsOf : IndexRow → List Nat

/- The container BUILT from index values already in hand: the ordinary array
   construction over a list of values. This is the container an implementation can
   obtain entirely on its own, with NO reserved-marker assignment carried out
   anywhere, so it records no assignment provenance at all. Provenance +
   executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom rowOf : List Nat → IndexRow

/- A container is always available (build one over no values at all), so the
   abstract container type is inhabited; derived from `rowOf` rather than
   postulated. -/
noncomputable instance : Inhabited IndexRow := ⟨rowOf []⟩

/- The one fact in scope about a BUILT container: reading it back yields exactly
   the index values it was built from (an assumption about the UNCHANGED array
   construction, validated out-of-band by axiom_check.py / G-AX). Building a
   container says nothing about any assignment having been carried out — in
   particular it grants no `markersAdmitted`. -/
axiom slotsOf_rowOf (vs : List Nat) : slotsOf (rowOf vs) = vs

/- An unforgeable capability marking a CONTAINER as one PRODUCED BY a
   reserved-marker assignment that COMPLETED — i.e. every selection step of the
   assignment was live in the container it wrote into, which admits every reserved
   index they store and represents values below zero. It is granted
   ONLY by `assignReserved` (below), for the very container that assignment
   produced, and records it together with the palette size; nothing else can
   fabricate it. It cannot be discharged from the index values a container reads
   back, which are identical whether or not the container admitted the markers,
   and two containers reading back the same values are not thereby the same
   container. The discriminator is the completing-assignment effect, not a slot
   value. Its concrete content is an implementation detail of the underlying array
   operation, hence opaque. Provenance + executable soundness check: mapping.md /
   axiom_check.py (G-AX). -/
opaque markersAdmitted : IndexRow → Nat → Prop

/- The reserved-marker assignment over a classified row, carried out on a container
   described by TWO independent extents, because the assignment reads BOTH ends of
   it: `carrier` is how many non-negative indices it admits (`0 .. carrier-1`),
   which is what the marker writes need, and `admitsNegative` says whether it
   represents values below zero at all, which is what the below-range selection
   needs. It stores the three reserved markers (`underSlot`, `overSlot`,
   `invalidSlot`) for the out-of-range / invalid elements, keeps the ordinary
   indices, and yields the container it wrote into. This is an UNCHANGED array
   operation invoked by both twins — it is modeled as a callee, NOT the function
   under change.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
noncomputable opaque assignReserved
    (cells : List Cell) (paletteSize : Nat) (admitsNegative : Bool) (carrier : Nat) :
    VelvetM IndexRow

/- The callee contract (an assumption validated out-of-band by axiom_check.py /
   G-AX, NOT a property of the function under change):

   the assignment is WELL-DEFINED — it yields a container whose readable indices
   are the per-element resolved slots `slotSeq paletteSize cells` AND grants that
   container the `markersAdmitted` capability — ONLY on a container that admits
   BOTH ends of what the assignment does to it. Two independent obligations, one
   per end, and each is the exact boundary of one selection step:

   * `admitsNegative = true` — the container represents values below zero. The
     below-range selection is a comparison against zero, so in a container with no
     value below zero it selects NOTHING: every below-range element keeps whatever
     the above-range selection already stored, and the produced container reads
     back `overSlot` where `slotSeq` says `underSlot`. Without this obligation the
     readback claim would be false on such a container, so it is required for
     soundness of the contract, not for convenience.
   * `paletteSize + 3 ≤ carrier` — the container admits every reserved index the
     assignment writes. The largest is `invalidSlot paletteSize = paletteSize + 2`,
     so it must admit values up to `paletteSize + 2`. A container narrower than the
     markers it is asked to store does not admit the assignment at all.

   When either obligation is missing the contract does not apply, no capability is
   granted, and the precondition cannot be discharged at the call site. Each is the
   EXACT boundary of the step it governs — the first the point at which the
   below-range selection becomes live, the second the point at which the largest
   reserved marker first fits — so together they are neither too strong nor too weak
   (axiom_check.py). Note what the contract does NOT say: it pins the readable
   indices of the container it PRODUCED, and nothing at all about any other
   container that happens to read back the same indices. -/
axiom assignReserved_contract
    (cells : List Cell) (paletteSize : Nat) (admitsNegative : Bool) (carrier : Nat)
    (post : IndexRow → Prop) :
    (admitsNegative = true ∧ paletteSize + 3 ≤ carrier ∧
      (∀ r, slotsOf r = slotSeq paletteSize cells ∧ markersAdmitted r paletteSize → post r))
    ≤ wp (assignReserved cells paletteSize admitsNegative carrier) post

/- The weakest-precondition generator the verifier consumes for a call to
   `assignReserved`. A call obligation therefore SPLITS into (i) the two container
   obligations `admitsNegative = true` and `paletteSize + 3 ≤ carrier`, both
   discharged at the call site, and (ii) the continuation under the produced
   container + its capability. Soundness (`get` under-approximates the true `wp`)
   rests on the single contract axiom above. -/
@[loomSpec]
noncomputable def assignReservedSpec
    (cells : List Cell) (paletteSize : Nat) (admitsNegative : Bool) (carrier : Nat) :
    WPGen (assignReserved cells paletteSize admitsNegative carrier) where
  get := fun post =>
    admitsNegative = true ∧ paletteSize + 3 ≤ carrier ∧
      (∀ r, slotsOf r = slotSeq paletteSize cells ∧ markersAdmitted r paletteSize → post r)
  prop := assignReserved_contract cells paletteSize admitsNegative carrier
-- axioms-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method resolveSlots (paletteSize : Nat) (cells : List Cell) return (out : IndexRow)
  -- The container handed on must read back the per-element resolved slots, one
  -- per input element, in order.
  ensures slotsOf out = slotSeq paletteSize cells
  ensures (slotsOf out).length = cells.length
  -- Load-bearing: the container handed on must be one PRODUCED BY a
  -- reserved-marker assignment that completed — carried out on a container
  -- admitting every reserved index it writes (up to `invalidSlot paletteSize`)
  -- and representing values below zero, so that every selection step of the
  -- assignment is live in it.
  -- The `markersAdmitted` capability is granted ONLY by such an admitting
  -- assignment and ONLY for the container it produced; it cannot be obtained for
  -- a container built out of the resolved index values, because those values are
  -- identical whether or not the container the assignment wrote into admitted the
  -- markers. The discriminator is the completing-assignment effect, independent of
  -- which slots the input selects.
  ensures markersAdmitted out paletteSize
  do
    -- impl-start
    -- Pre-image skeleton: the reserved-marker assignment is carried out on the
    -- input element's OWN container. For the integer-dtype input the widening runs
    -- only inside the float branch, so the element keeps the container it arrived
    -- in: an unsigned one (`admitsNegative = false`) whose non-negative extent is
    -- only `paletteSize` (it admits just the ordinary indices `0 .. paletteSize-1`).
    -- Neither end of it admits what the assignment does: the reserved markers up to
    -- `invalidSlot paletteSize = paletteSize + 2` are outside its extent, and the
    -- below-range selection is not even live in it. So the callee obligations
    -- `admitsNegative = true` — here `false = true` — and `paletteSize + 3 ≤ carrier`
    -- — here `paletteSize + 3 ≤ paletteSize` — cannot be discharged at the call
    -- site, the `markersAdmitted` capability is never granted, and the
    -- postcondition cannot be proved. Both obligations are INDEPENDENT of `cells`
    -- (they fail even for an empty or wholly-in-range row), so prove_correct MUST
    -- fail.
    let out <- assignReserved cells paletteSize false paletteSize
    return out
    -- impl-end

prove_correct resolveSlots by
  loom_solve
