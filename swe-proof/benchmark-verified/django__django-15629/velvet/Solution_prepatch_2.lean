import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. Both modeled operations
--  are pure data-flow over their inputs: the column descriptor a referencing
--  field reports, and a boolean decision over already-computed descriptors.
--  The values they consume — a field's own column type/check, the column
--  descriptor of the field it points to, and the before/after descriptors of a
--  field being altered — are taken as plain inputs (abstracted, mapping.md §2),
--  so there is nothing to consume as an axiom and nothing to validate against an
--  outside callee.)
-- axioms-end

-- pure-start
/- The portion of a column descriptor this construction observes. A field is
   asked to describe the column that backs it:
   * `sqlType`  — the column's storage type (e.g. a varchar of some width);
   * `check`    — an optional column check expression (`none` if the field
                  imposes none);
   * `collation`— the optional sort/equality collation for the column
                  (`none` when the column carries no explicit collation).
   The collation is the field the rest of this construction is about: two
   columns joined by a reference must agree on it. -/
structure ColumnDesc where
  sqlType   : String
  check     : Option String
  collation : Option String
deriving DecidableEq, Inhabited, Repr

/- The column descriptor a *referencing* field reports. A referencing field
   does not own an independent collation: the column it stores must line up with
   the column it points at, so it adopts the referenced column's collation while
   keeping its own storage type and check. `refType`/`refCheck` are the
   referencing field's own type and check; `targetCollation` is the collation of
   the column it references. -/
def referencingColumnDesc
    (refType : String) (refCheck : Option String)
    (targetCollation : Option String) : ColumnDesc :=
  { sqlType := refType, check := refCheck, collation := targetCollation }

/- Whether altering a referenced column forces the columns that point at it to
   be reissued. A reference must be reissued exactly when the referenced column
   can be a reference target (it is unique) AND something a referencing column
   mirrors actually changes — either its storage type or its collation. Earlier
   only a storage-type difference counted; a collation-only difference must
   count too, since a referencing column mirrors the collation as well.
   `targetUnique` says the referenced column is unique (so references may point
   at it); the `old…`/`new…` pairs are the referenced column's descriptor before
   and after the alteration. -/
def referencesNeedReissue
    (targetUnique : Bool)
    (oldType newType : String)
    (oldCollation newCollation : Option String) : Bool :=
  targetUnique && ((oldType != newType) || (oldCollation != newCollation))
-- pure-end

-- pre-conditions-start
-- (preconditions are the inline `require` clauses on each `method` below)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- The column descriptor reported by a referencing field. Read-only inputs (no
   `mut`): the descriptor is derived, nothing is altered. The reported collation
   is exactly the referenced column's collation (in particular, when the
   referenced column carries a collation the reference reports the SAME one, not
   the absence of a collation). -/
method foreignReferenceColumnDesc
    (refType : String) (refCheck : Option String)
    (targetCollation : Option String) return (out : ColumnDesc)
  ensures out = referencingColumnDesc refType refCheck targetCollation
  ensures out.collation = targetCollation
  ensures out.sqlType = refType
  ensures out.check = refCheck
  do
    -- impl-start
    return { sqlType := refType, check := refCheck, collation := targetCollation }
    -- impl-end

prove_correct foreignReferenceColumnDesc by
  loom_solve
  simp_all [referencingColumnDesc]

/- The decision whether references to an altered column must be reissued.
   Read-only inputs (no `mut`). The result is true exactly when the referenced
   column is unique and either its storage type or its collation differs between
   the before and after descriptors — so a collation-only change is sufficient
   to force reissue. -/
method shouldReissueReferences
    (targetUnique : Bool)
    (oldType : String) (newType : String)
    (oldCollation : Option String) (newCollation : Option String) return (out : Bool)
  ensures out = referencesNeedReissue targetUnique oldType newType oldCollation newCollation
  ensures out = true → (targetUnique = true ∧ ((oldType != newType) = true ∨ (oldCollation != newCollation) = true))
  ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
  do
    -- impl-start
    -- Pre-image skeleton: references are reissued only on a storage-type
    -- difference; a collation-only change is NOT counted. The frozen spec
    -- requires reissue whenever the collation differs (even with equal type),
    -- so `prove_correct` MUST fail on a collation-only alteration.
    return targetUnique && (oldType != newType)
    -- impl-end

prove_correct shouldReissueReferences by
  loom_solve
  simp_all [referencesNeedReissue]
