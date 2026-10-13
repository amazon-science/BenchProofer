import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only behaviour modeled here is which storage
--  reference the serialized form of a file field should record. The two inputs
--  are taken as FREE values: the evaluated storage backend the field currently
--  holds, and the original storage callable the field was configured with when
--  one was supplied. How the backend is produced from the callable is UNCHANGED
--  and is not modeled (an R abstraction, validated against the real field by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom, hence no
--  G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An opaque storage reference. Only reference identity is observable to the
   consumer of the serialized form (it compares the recorded reference to the
   one it supplied, and to the default backend), so a tagged id is the faithful
   carrier. A storage callable and an evaluated backend are both references. -/
structure Backend where
  id : Nat
deriving DecidableEq, Inhabited

/- The default storage backend: the one distinguished reference whose presence
   in the serialized form is redundant and therefore omitted. -/
def defaultBackend : Backend := { id := 0 }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the storage reference to record in a file field's serialized form.

   `storage` is the evaluated backend the field currently holds. `storageCallable`
   is the original callable the field was configured with, present (`some`) iff
   the field was configured by a callable rather than by a backend directly.

   The reference recorded is the original callable when one was supplied, and the
   evaluated backend otherwise. That reference is recorded (`some`) unless it is
   the default backend, in which case nothing is recorded (`none`): a field left
   on the default backend needs no explicit storage entry.

   Both inputs are read-only (neither `mut`): the routine inspects the held
   backend and the configuring callable and decides; it mutates neither
   (directive 5). -/
method serializedStorageArg (storage : Backend) (storageCallable : Option Backend)
    return (out : Option Backend)
  ensures out =
    (if (storageCallable.getD storage) ≠ defaultBackend
     then some (storageCallable.getD storage) else none)
  do
    -- impl-start
    -- The reference to record is the configuring callable when one was supplied,
    -- otherwise the evaluated backend the field currently holds.
    let value := storageCallable.getD storage
    let mut out : Option Backend := none
    if value ≠ defaultBackend then
      out := some value
    return out
    -- impl-end

prove_correct serializedStorageArg by
  loom_solve
