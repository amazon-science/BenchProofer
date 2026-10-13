import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- A descriptor value carries an integer ordinal (`counter`) assigned once when
   the descriptor is created, and an optional owning-scope identity (`owner`). The
   owning scope, when present, is identified by an ordered pair of names: an
   outer namespace name and an inner entity name. A descriptor that has not been
   attached to any scope has `owner = none`. -/
structure FieldRec where
  counter : Int
  owner : Option (String × String)
deriving DecidableEq, Inhabited

/- The hashing key derived from a descriptor: its ordinal together with the two
   component names of its owning-scope identity (each absent when unattached).
   `keyOf` makes explicit exactly which observable components determine the
   key. -/
structure IdentityKey where
  counter : Int
  scopeName : Option String
  entityName : Option String
deriving DecidableEq, Inhabited

-- axioms-start
/- An abstract content-addressed digest over an `IdentityKey`. This stands for
   the standard-library value digest of the tuple of the key's components;
   opaque because its concrete numeric output is an implementation detail of the
   runtime. Provenance + executable soundness check: mapping.md / axiom_check.py
   (G-AX) validates `pyHash (keyOf a)` against the real digest of the
   corresponding component tuple. -/
opaque pyHash : IdentityKey → Int
-- axioms-end

-- pure-start
/- The key extracted from a descriptor: its ordinal plus each of the two
   component names of its owning-scope identity, or `none` when unattached. -/
def keyOf (a : FieldRec) : IdentityKey :=
  { counter := a.counter,
    scopeName := a.owner.map (·.1),
    entityName := a.owner.map (·.2) }

/- Strict order on owning-scope identities: lexicographic on the pair
   (outer namespace name, inner entity name), comparing names by the standard
   code-point string order. -/
def ownerLt (p q : String × String) : Bool :=
  decide (p.1 < q.1) || (decide (p.1 = q.1) && decide (p.2 < q.2))

/- The strict order a descriptor exposes. Descriptors are ordered primarily by
   their ordinal `counter`; an ordinal tie is resolved only when both
   descriptors are attached to a scope, in which case an attached descriptor never precedes an
   unattached one with the same ordinal, and two attached descriptors with the
   same ordinal are ordered by the lexicographic order of their owning-scope
   identities. -/
@[grind] def fieldLtSpec (a b : FieldRec) : Bool :=
  if a.counter ≠ b.counter ∨ (a.owner = none ∧ b.owner = none) then
    decide (a.counter < b.counter)
  else
    if a.owner.isSome ≠ b.owner.isSome then
      decide (a.owner = none)
    else
      match a.owner, b.owner with
      | some pa, some pb => ownerLt pa pb
      | _, _ => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Equality of two descriptors: their ordinals agree AND their owning-scope
   identities agree (both unattached, or attached to the same scope identity). -/
method fieldEq (a : FieldRec) (b : FieldRec) return (out : Bool)
  ensures out = (decide (a.counter = b.counter) && decide (a.owner = b.owner))
  do
    -- impl-start
    return (decide (a.counter = b.counter) && decide (a.owner = b.owner))
    -- impl-end

prove_correct fieldEq by loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The strict order exposed by a descriptor (see `fieldLtSpec`). -/
method fieldLt (a : FieldRec) (b : FieldRec) return (out : Bool)
  ensures out = fieldLtSpec a b
  do
    -- impl-start
    if a.counter ≠ b.counter ∨ (a.owner = none ∧ b.owner = none) then
      return decide (a.counter < b.counter)
    else
      if a.owner.isSome ≠ b.owner.isSome then
        return decide (a.owner = none)
      else
        let r := match a.owner, b.owner with
          | some pa, some pb => ownerLt pa pb
          | _, _ => false
        return r
    -- impl-end

prove_correct fieldLt by loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The digest a descriptor exposes: the digest of its key, i.e. of its ordinal
   together with both component names of its owning-scope identity. -/
method fieldHash (a : FieldRec) return (out : Int)
  ensures out = pyHash (keyOf a)
  do
    -- impl-start
    -- Pre-image skeleton: the digest is taken over the ordinal alone, with the
    -- owning-scope identity components forced absent. The frozen spec digests
    -- the full key (keyOf a), so prove_correct MUST fail.
    return pyHash { counter := a.counter, scopeName := none, entityName := none }
    -- impl-end

prove_correct fieldHash by loom_solve
