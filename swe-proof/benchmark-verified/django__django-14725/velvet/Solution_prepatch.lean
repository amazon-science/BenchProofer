import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
   of are abstracted as free inputs:
     * `existing` — the identities settled by persisting the already-known rows
       of the collection. This step runs identically regardless of the policy
       below, so only its result is needed (an A-reference, mapping.md §3.1).
     * `fresh` — the identities that producing brand-new rows would settle, and,
       as a side effect, add to the stored collection. The relation
       "produced identities = the rows it adds to storage" is the reference
       behaviour of that unchanged producing step, validated against the real
       callee by axiom_check.py (G-AX, an A-reference, mapping.md §3.2). -/
-- axioms-end

-- pure-start
/- The list of identities a persistence pass reports, given the policy and the
   two component results:
     * when creation of brand-new rows is disallowed, only the already-known
       rows' identities are reported;
     * otherwise the already-known identities are followed by the freshly
       produced ones, in that order. -/
def reported (noCreate : Bool) (existing fresh : List Nat) : List Nat :=
  if noCreate then existing else existing ++ fresh

/- The stored collection of brand-new identities after a persistence pass,
   given its prior contents `priorStored`:
     * when creation is disallowed, the stored collection is left untouched;
     * otherwise the freshly produced identities are appended to it. -/
def storedAfter (noCreate : Bool) (priorStored fresh : List Nat) : List Nat :=
  if noCreate then priorStored else priorStored ++ fresh
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Persist a collection of editable rows and report the identities it settled.

   Desired behaviour: a policy flag controls whether persisting may bring brand
   new rows into being. When the flag forbids new rows, the pass settles only
   the already-known rows: it reports just those identities AND leaves the stored
   set of brand-new rows exactly as it found it — producing no new rows as a side
   effect. When the flag permits new rows, the pass reports the already-known
   identities followed by the freshly produced ones, and those fresh rows are
   added to the stored set.

   `existing` and `fresh` are the (read-only) identities the two component
   persistence steps would settle. `stored` is the persistent collection of
   brand-new identities; it is `mut` because the permit-new branch grows it, and
   the forbid-new branch must leave it untouched — pinned explicitly so that an
   implementation reporting an edit-only result cannot silently create rows
   (directive 5). Identities are modeled as `Nat`; order is preserved
   (mapping.md §2). -/
method saveFormset (noCreate : Bool) (existing : List Nat) (fresh : List Nat)
    (mut stored : List Nat) return (out : List Nat)
  ensures out = reported noCreate existing fresh
  ensures stored = storedAfter noCreate storedOld fresh
  ensures noCreate = true → (out = existing ∧ stored = storedOld)
  ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
  do
    -- impl-start
    -- Pre-image skeleton: the persistence pass ignored the policy flag — it
    -- ALWAYS produced the brand-new rows (appending their identities to the
    -- stored collection) and reported the already-known identities followed by
    -- the freshly produced ones. The frozen spec demands that the forbid-new
    -- policy report only the already-known identities and leave the stored
    -- collection untouched, so prove_correct MUST fail on that clause.
    stored := stored ++ fresh
    return existing ++ fresh
    -- impl-end

prove_correct saveFormset by
  loom_solve <;> simp_all [reported, storedAfter]
