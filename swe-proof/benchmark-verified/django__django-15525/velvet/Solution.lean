import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The natural-key derivation for a record, as it depends on the record's
   STORE HANDLE — the identifier of the database the record is currently
   associated with. The derivation may follow references to related records,
   and each such reference is resolved against the database named by the store
   handle; so the resulting key is a function of that handle. This is an
   UNCHANGED routine the operation defers to: it is left OPAQUE (a free
   function), refined never replaced, so no contract is claimed about WHAT it
   returns — only that the operation feeds it the right handle. Because nothing
   is asserted about its value there is nothing to validate against the real
   routine (no axiom_check.py — meta.json G-AX skip). Provenance: mapping.md. -/
opaque naturalKeyVia : Option String → List String
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Deriving the natural key of a freshly built record while loading it into a
   target database.

   A record's natural key may follow references to related records, and those
   references are resolved against whichever database the record is currently
   associated with (its STORE HANDLE). A freshly built record carries no store
   handle yet (`none`). When the record is being loaded into a particular
   target database, the natural key must be derived as that target database
   would see it, so that reference-following resolves against the same database
   the record is being loaded into.

   The desired behavior: associate the record with the target database FIRST —
   set its store handle to that database — and only THEN derive the natural key,
   so the reference-following derivation is routed to the target database.

   `storeHandle` is the record's mutable database association. It comes in
   unset (`none`) for a freshly built record and is genuinely mutated to the
   target database; its post-state is pinned EXACTLY to `some targetDb`
   (directive 5: the changed frame is stated at its exact post-state). The
   returned key is the derivation evaluated at that updated handle, so it is
   grounded in the input `targetDb` (the key is `naturalKeyVia (some targetDb)`,
   the derivation at the target-database handle). -/
method naturalKeyForLoadedRecord (targetDb : String) (mut storeHandle : Option String)
    return (key : List String)
  require storeHandle = none
  ensures storeHandle = some targetDb
  ensures key = naturalKeyVia (some targetDb)
  do
    -- impl-start
    -- Associate the freshly built record with the target database, THEN derive
    -- the natural key from that updated handle (the derivation reads the handle
    -- and routes reference-following to the named database).
    storeHandle := some targetDb
    let key := naturalKeyVia storeHandle
    return key
    -- impl-end

prove_correct naturalKeyForLoadedRecord by
  loom_solve
