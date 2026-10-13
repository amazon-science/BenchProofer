import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- This bundle models an object-identity / heap-aliasing property. Lean is
   value-functional, so a naive value model could not distinguish "return the
   same object" from "return a fresh, independent object" — the very behaviour
   under specification. Following the heap-as-function discipline of the Velvet
   memory examples, objects are addresses (`Handle`) into an explicit store of
   their mutable per-object state (`slot : Handle → Payload`), and allocation is
   a strictly-increasing frontier (`nextFresh`). With this carrier the identity
   of the result, and whether a later write to the result can reach the source,
   are first-class facts the spec pins. -/

-- axioms-start
/- Object identity: an address into the per-object mutable-state store. -/
abbrev Handle := Int

/- The mutable per-object state observed and (potentially, downstream) altered
   by callers: a tuple of small integer tags. -/
abbrev Payload := List Int
-- axioms-end

-- pure-start
/- A store mapping each live object to its current mutable state. Distinct
   handles address disjoint store slots, so an update through one handle leaves
   every other handle's state untouched (`Function.update`'s defining property).
   This is the fact that makes "the result is a distinct object" equivalent to
   "mutating the result cannot affect the source". -/
abbrev Store := Handle → Payload
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Return the source object in a related representation. The desired behaviour:
   the result is an INDEPENDENT object — a handle distinct from the source whose
   mutable state is INITIALIZED FROM but NOT SHARED WITH the source. Concretely
   the result is freshly allocated (`res = nextFreshOld`, above every live
   handle), carries the source's state at call time (`store res = storeOld self`),
   the source's own state is untouched (`store self = storeOld self`), and no
   other live object's state changes (frame). Because the result is a fresh,
   distinct handle, a subsequent write to the result's slot cannot alias the
   source — the property a caller relies on. `store`/`nextFresh` are genuinely
   mutated (an allocation happens), so they are `mut`; `self` is read-only. -/
method reifyIndependent
    (self : Handle) (mut store : Store) (mut nextFresh : Handle)
    return (res : Handle)
  require self < nextFresh
  ensures res = nextFreshOld
  ensures nextFresh = nextFreshOld + 1
  ensures res ≠ self
  ensures store res = storeOld self
  ensures store self = storeOld self
  ensures ∀ h, h ≠ res → store h = storeOld h
  do
    -- impl-start
    let r := nextFresh
    store := Function.update store r (store self)
    nextFresh := nextFresh + 1
    return r
    -- impl-end

prove_correct reifyIndependent by
  loom_solve
  · intro h hne; exact Function.update_of_ne hne _ _
  · exact Function.update_of_ne (ne_of_lt require_1) _ _
  · exact Function.update_self _ _ _
