import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The recognition decision is pure boolean / list-frame
--  logic over a FREE INPUT: the ancestry of the candidate type. The membership
--  predicate that decides whether one type derives from another is the language's
--  own total structural relation over a type's linearised ancestor list — the
--  operation reads that ancestry, it never reshapes any outside object, so there
--  is no callee contract to assume and nothing for G-AX.)
-- axioms-end

-- pure-start
/- A type's ancestry is modeled as the linearised list of the identifiers of the
   types it derives from, the candidate type itself listed first (mapping.md §2).
   Identifiers are abstract tags; three of them denote the family's recognised
   base types. -/

/- The root recognised base type (a candidate that derives from it is recognised
   directly). -/
def rootBaseId : Nat := 0

/- The two further recognised base types of the family. A candidate that derives
   from either of them is also a member of the family — derivation, not mere
   identity with one of these bases, is what matters. -/
def subBaseIds : List Nat := [1, 2]

/- Whether one type derives from another: the target base appears in the
   candidate's ancestry. Reflexive (a type's ancestry lists itself) and total. -/
def derivesFrom (ancestry : List Nat) (baseId : Nat) : Bool :=
  ancestry.contains baseId

/- The recognition decision, modeled deeply. A candidate type is a member of the
   family exactly when it derives from ANY recognised base type: from one of the
   two sub-bases, OR from the root base. Genuine derivation throughout — being
   identical to a base is just the reflexive case of deriving from it, and is
   neither necessary (a proper descendant qualifies) nor specially privileged. -/
def isFamilyMember (ancestry : List Nat) : Bool :=
  (subBaseIds.any (fun b => derivesFrom ancestry b)) || derivesFrom ancestry rootBaseId

@[grind] lemma isFamilyMember_def (ancestry : List Nat) :
    isFamilyMember ancestry =
      ((subBaseIds.any (fun b => derivesFrom ancestry b)) || derivesFrom ancestry rootBaseId) :=
  rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a candidate type is recognised as a member of the family.
   Desired behaviour: a candidate is recognised exactly when it genuinely derives
   from a recognised base type — from one of the family's specialised base types
   or from its root base. A type that descends from a specialised base must be
   recognised even when it is not itself one of those bases; recognition is by
   derivation, not by identity. The candidate's ancestry (`ancestry`) is
   read-only and a candidate always has a non-empty ancestry (it lists itself). -/
method recognizeType (ancestry : List Nat) return (result : Bool)
  require ancestry ≠ []
  ensures result = isFamilyMember ancestry
  ensures (subBaseIds.any (fun b => derivesFrom ancestry b)) = true → result = true
  ensures derivesFrom ancestry rootBaseId = true → result = true
  do
    -- impl-start
    -- A candidate derives from one of the specialised bases iff that base is in
    -- its ancestry (genuine derivation, the reflexive case included). The
    -- separate root-base leg recognises candidates deriving from the root.
    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
    return viaSubBases || viaRootBase
    -- impl-end

prove_correct recognizeType by
  loom_solve
