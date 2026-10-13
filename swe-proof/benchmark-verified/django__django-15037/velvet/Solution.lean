import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axiom. The only outside callee the modeled decision consults —
--  the lookup that yields the target collection's identity-key column — is an
--  UNCHANGED callee whose result is taken as the free input `idKey` (an
--  A-reference, not a consumed contract). Its only relied-on property — that it
--  reports the target collection's identity-key column when one exists and
--  nothing otherwise — is validated against the real introspection machinery by
--  axiom_check.py (G-AX).)
-- axioms-end

-- pure-start
/- The explicit target-column qualifier a stored cross-row reference must carry.

   A reference points at a column of another collection. When the reference is a
   plain (many-to-one) link AND the target collection's identity-key column is
   present and is a DIFFERENT column from the one actually referenced, the
   generated description must carry an explicit qualifier that names the
   referenced column; in every other case no qualifier is added. A
   one-to-one / identity reference never carries the qualifier.

   `isUniqueRef` is true when the link is one-to-one (identity) rather than a
   plain many-to-one link; `refColumn` is the referenced column; `idKey` is the
   target collection's identity-key column (`none` when the collection has no
   identity key). A present identity key is recognised only when it is a
   non-empty column name (an absent / empty key is treated as "no key"). -/
def targetQualifier (isUniqueRef : Bool) (refColumn : List Char)
    (idKey : Option (List Char)) : Option (List Char) :=
  if isUniqueRef then none
  else
    match idKey with
    | none   => none
    | some k => if k ≠ [] ∧ k ≠ refColumn then some refColumn else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Deriving the explicit target-column qualifier for one stored cross-row
   reference. The inputs are read-only (none is `mut`; the derivation mutates
   nothing — directive 5):

   - `isUniqueRef` — the link is one-to-one (identity) rather than a plain
     many-to-one link;
   - `refColumn`   — the column the reference points at in the target
     collection;
   - `idKey`       — the target collection's identity-key column, or `none`
     when the collection exposes no identity key.

   The result is the explicit qualifier to attach to the generated description:
   `some refColumn` exactly when a plain link points at a non-identity-key
   column (the identity key is present, non-empty and different from the
   referenced column), and `none` otherwise. Pinned to `targetQualifier` so the
   derivation is forced to be that structural decision over the inputs, not an
   echo of any one carrier. -/
method qualifyReference (isUniqueRef : Bool) (refColumn : List Char)
    (idKey : Option (List Char)) return (out : Option (List Char))
  ensures out = targetQualifier isUniqueRef refColumn idKey
  do
    -- impl-start
    -- A one-to-one / identity link never carries an explicit qualifier.
    if isUniqueRef then
      return none
    else
      -- A plain many-to-one link: consult the target collection's identity key.
      match idKey with
      | none   => return none
      | some k =>
        -- Qualify only when the identity key is a present, non-empty column
        -- that differs from the column actually referenced.
        if k ≠ [] ∧ k ≠ refColumn then
          return (some refColumn)
        else
          return none
    -- impl-end

prove_correct qualifyReference by
  loom_solve <;> simp_all [targetQualifier]
  all_goals tauto
