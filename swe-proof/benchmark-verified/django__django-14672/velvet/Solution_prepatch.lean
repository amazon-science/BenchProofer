import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The one unchanged callee this construction relies on — a
--  canonicalizer turning an order-only sequence value into its canonical
--  hashable (immutable) form, identity on values that are already hashable — is
--  modeled DEEPLY as `canonicalize` in the pure region, and validated
--  `canonicalize == the real callee` out-of-band by axiom_check.py (G-AX) as an
--  A-reference. Its result is never pinned to an opaque oracle; the spec spells
--  the canonical form out, so no soundness is borrowed from an axiom.)
-- axioms-end

-- pure-start
/- A component slot that may carry a sequence value.

   `none`    — the slot is absent (no sequence supplied).
   `seq xs loose` — an ordered sequence of element names `xs`; `loose = true`
                    means the value is an order-only (loose) container, which is
                    NOT usable as a hash key; `loose = false` means it is in
                    canonical immutable form and IS usable as a hash key. -/
inductive Slot where
  | none
  | seq (items : List String) (loose : Bool)
  deriving DecidableEq, Inhabited

/- A component of a comparison key. `opaque h` is any already-prepared component
   whose only relevant attribute is whether it is usable as a hash key (`h`);
   `slot s` is the one component that carries a sequence value, whose usability
   depends on its canonical form. -/
inductive Comp where
  | opaque (hashable : Bool := true)
  | slot (s : Slot)
  deriving DecidableEq, Inhabited

/- Is a slot value usable as a hash key? An absent slot and a canonical
   (immutable) sequence are; an order-only (mutable) sequence is not. -/
def Slot.isHashable : Slot → Bool
  | Slot.none        => true
  | Slot.seq _ m     => !m

/- Is a component usable as a hash key? -/
def Comp.isHashable : Comp → Bool
  | Comp.opaque h => h
  | Comp.slot s   => s.isHashable

/- A comparison key (a list of components) is usable as a hash key exactly when
   every one of its components is. (A composite key hashes iff every element
   does.) -/
def keyHashable (cs : List Comp) : Bool := cs.all Comp.isHashable

/- The canonical form of a slot value: an absent slot is unchanged; a sequence
   is put into canonical immutable form (its elements and their order are
   preserved; only its mutability/usability changes). Identity on values that
   are already canonical. This is the deep model of the unchanged canonicalizing
   callee (mapping.md §3.1, an A-reference validated by G-AX). -/
def canonicalize : Slot → Slot
  | Slot.none      => Slot.none
  | Slot.seq xs _  => Slot.seq xs false

/- The canonical form of any slot is always usable as a hash key. -/
@[grind, simp] lemma canonicalize_isHashable (s : Slot) :
    (canonicalize s).isHashable = true := by
  cases s <;> rfl

/- Canonicalization preserves the element sequence (content + order). -/
@[grind] lemma canonicalize_items (xs : List String) (m : Bool) :
    canonicalize (Slot.seq xs m) = Slot.seq xs false := rfl

/- `keyHashable` distributes over concatenation of component lists. -/
@[grind, simp] lemma keyHashable_append (a b : List Comp) :
    keyHashable (a ++ b) = (keyHashable a && keyHashable b) := by
  simp [keyHashable, List.all_append]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A relation descriptor's comparison key is assembled from three parts: the
   already-prepared leading components `pre`, the single component that carries a
   sequence value (`slot`), and the already-prepared trailing components `post`.
   The leading and trailing components are read-only and already usable as hash
   keys (they are not `mut`; directive 5).

   The behaviour pinned here: the sequence-carrying component must be placed into
   the key in CANONICAL form (so the key compares and hashes by the sequence's
   content and order, independently of whether the caller supplied an order-only
   or an already-canonical container), and the resulting whole key must be usable
   as a hash key. The discriminating inputs are order-only sequence slots: there
   the produced component must be the canonical form, never the raw order-only
   value (which is not usable as a hash key). -/
method comparisonKey (pre : List Comp) (slot : Slot) (post : List Comp)
    return (out : List Comp)
  require keyHashable pre = true
  require keyHashable post = true
  ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post
  ensures keyHashable out = true
  do
    -- impl-start
    -- Pre-image skeleton: the sequence-carrying component is placed into the key
    -- RAW, without canonicalization. For an order-only (loose) sequence slot the
    -- produced component is then not usable as a hash key, so the frozen
    -- post-conditions (`out = ... canonicalize slot ...` and `keyHashable out`)
    -- are both violated and prove_correct MUST fail.
    return pre ++ [Comp.slot slot] ++ post
    -- impl-end

prove_correct comparisonKey by
  loom_solve
  simp_all [keyHashable, Comp.isHashable]
