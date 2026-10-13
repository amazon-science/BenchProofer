import Velvet.Std
-- imports-end

/- Total-correctness semantics: the real copy is a straight-line construction
   (clone the underlying values, rebuild the wrapper) that always COMPLETES,
   so the spec must also rule out implementations that diverge — under
   partial correctness a non-terminating body would vacuously satisfy every
   postcondition. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The dtype-preserving clone is modeled deeply
--  as a record construction. The fact that an index's underlying array
--  representation may re-derive a DIFFERENT element dtype than the one the
--  wrapper stores — the property that makes preservation observable — is
--  carried as a plain input field (`inferredDtype`) and validated against the
--  real wrapper behaviour by axiom_check.py (G-AX) as an A-reference. Nothing
--  is consumed as an axiom.)
-- axioms-end

-- pure-start
/- A wrapper around a one-dimensional index that records both its element
   values and the precise element dtype it presents.

   `values` are the ordered element identities the index carries.
   `storedDtype` is the precise element dtype the wrapper presents (e.g. a
   fixed-width unicode dtype). `inferredDtype` is the element dtype that would
   be re-derived purely from the wrapper's underlying array representation,
   ignoring the stored dtype; for some kinds of element this re-derived dtype
   DIFFERS from `storedDtype` because the underlying representation cannot carry
   the precise stored dtype (it falls back to a generic object dtype), and for
   others the two agree. The dtype is modeled by its name (a `String`); the
   element values by a `List Int` (their ordered identities). -/
structure IndexAdapter where
  values : List Int
  storedDtype : String
  inferredDtype : String
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Copying an index wrapper returns a fresh wrapper with the SAME element values
   and the SAME stored element dtype as the original. The stored dtype must be
   carried through unchanged — never re-derived from the underlying array
   representation, which for some element kinds would yield a different
   (generic) dtype. The `deep` flag governs only whether the underlying values
   are physically duplicated; it does not affect the observable element values
   or the stored dtype, which are identical for either setting.

   The dtype that would be re-derived from the copy's underlying representation
   (`inferredDtype`) is a property of the element values alone; since the values
   are unchanged, it too is identical to the original's.

   `self` and `deep` are read-only (not `mut`); a fresh wrapper is constructed
   and nothing is mutated (directive 5). -/
method adapterCopy (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  ensures out.values = self.values
  ensures out.storedDtype = self.storedDtype
  ensures out.inferredDtype = self.inferredDtype
  do
    -- impl-start
    -- `deep` selects whether the underlying values are physically duplicated;
    -- either choice yields the same element values, so the resulting carrier is
    -- the original's values in both cases.
    let arr := if deep then self.values else self.values
    return { values := arr, storedDtype := self.storedDtype,
             inferredDtype := self.inferredDtype }
    -- impl-end

prove_correct adapterCopy by
  loom_solve

/- An index-valued variable copies its data by delegating to the wrapper's own
   copy, which preserves the stored element dtype. The result therefore carries
   the same element values and the same stored element dtype as the original,
   for either setting of `deep` — copying never silently changes the element
   dtype of an index.

   As with the wrapper copy, the re-derived (`inferredDtype`) dtype is a
   property of the unchanged element values and is therefore identical too.

   `self` and `deep` are read-only (not `mut`); nothing is mutated
   (directive 5). -/
method indexVariableCopy (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  ensures out.values = self.values
  ensures out.storedDtype = self.storedDtype
  ensures out.inferredDtype = self.inferredDtype
  do
    -- impl-start
    let data ← adapterCopy self deep
    return data
    -- impl-end

prove_correct indexVariableCopy by
  loom_solve
