import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged helpers this operation orchestrates —
   the index materializer and the readiness guard — are modeled DEEPLY in the
   `pure` region (`materializeIndex`, `readinessGuard`) and validated equal to
   their real callees by axiom_check.py (G-AX) as A-references, not assumed
   behind an opaque `axiom`. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The two ways the readiness guard can reject a request to read back the
   feature inventory:

     * `notReady`  — the term→index inventory has never been established (the
       estimator has neither been trained nor handed an explicit inventory yet);
     * `emptyIndex` — an inventory was established but contains no terms.

   These are exactly the rejection shapes the desired behavior distinguishes;
   provenance + executable soundness check: mapping.md §3 / axiom_check.py. -/
inductive InvErr where
  | notReady
  | emptyIndex
  deriving DecidableEq, Inhabited

/- The observable state this operation touches, restricted to the two aspects it
   reads and may establish:

     * `index` — the term→position inventory (`none` until established); each
       entry binds a term to its integer position;
     * `explicit` — whether the established inventory was supplied explicitly at
       construction rather than learned from data (`none` until the
       establishment step has run and recorded this fact).

   Every other field of the estimator is untouched and is not part of this
   carrier (mapping.md §2). -/
structure InvState where
  index : Option (List (String × Nat))
  explicit : Option Bool
  deriving DecidableEq, Inhabited

/- Establish the inventory from the explicitly-supplied terms, if any.

   When an explicit term list is supplied, the inventory is the list of terms
   each bound to its position in that list, and the establishment is recorded as
   explicit. When no list is supplied, no inventory is established (the slot
   stays as it was) and the establishment is recorded as non-explicit. This is
   the unchanged establishment helper, modeled deeply (A-reference, G-AX). The
   supplied term list, when present, is required well-formed (non-empty, no
   repeated term) — the domain on which the new behavior is exercised. -/
def materializeIndex (supplied : Option (List String)) (st : InvState) : InvState :=
  match supplied with
  | none        => { st with explicit := some false }
  | some terms  => { index := some terms.zipIdx, explicit := some true }

/- The readiness guard, modeled deeply (A-reference, G-AX): a request is rejected
   when no inventory has been established (`notReady`) or when the established
   inventory is empty (`emptyIndex`); otherwise it is allowed through. -/
def readinessGuard (st : InvState) : Except InvErr Unit :=
  match st.index with
  | none      => Except.error InvErr.notReady
  | some []   => Except.error InvErr.emptyIndex
  | some _    => Except.ok ()

/- The feature inventory read back: the terms of the established index in
   ascending position order. Modeled deeply (the order-by-position projection)
   so the result is produced by the actual inventory, not echoed from an oracle
   (directive 8). -/
def featureList (m : List (String × Nat)) : List String :=
  (m.mergeSort (fun a b => a.2 ≤ b.2)).map (·.1)

/- The whole operation as a pure transition on `(state, result)`: first, when no
   inventory has yet been established, run the establishment step (which may
   establish the explicit inventory and always records the explicit/non-explicit
   fact); then apply the readiness guard; on admission, read back the ordered
   feature inventory; on rejection, surface the rejection while keeping whatever
   state the establishment step left. -/
def featureNamesRun (st : InvState) (supplied : Option (List String)) :
    InvState × Except InvErr (List String) :=
  let st' := if st.index = none then materializeIndex supplied st else st
  let res : Except InvErr (List String) :=
    match readinessGuard st' with
    | Except.error e => Except.error e
    | Except.ok _    => Except.ok (featureList (st'.index.getD []))
  (st', res)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Read back the inventory mapping integer positions to feature names.

   Desired behavior: a feature inventory can be read back not only after the
   estimator has been trained, but also when an inventory was supplied
   explicitly at construction and the estimator has not yet been trained. To
   make that possible, the read-back must first establish the inventory when one
   has not yet been established — running the same establishment step the
   training path uses — and only then apply the readiness guard. With that step
   in place, supplying an explicit inventory lets the inventory be read back
   without a prior training run, instead of being rejected as not-yet-ready (the
   behavior the public problem statement asks for). When no inventory has been
   established and none was supplied explicitly, the request is still rejected as
   not-yet-ready — but the establishment step has by then recorded that the
   (absent) inventory is non-explicit. When the inventory was already
   established, nothing is established anew and the request proceeds straight to
   the guard. On admission the result is the established inventory's terms in
   ascending position order.

   `st` is the estimator state (`mut`): the establishment step may write the
   inventory and the explicit/non-explicit fact, so its post-state is pinned
   exactly by `featureNamesRun` (directive 5: when nothing is established anew —
   the already-established case — the post-state equals the entry state, which
   `featureNamesRun` returns verbatim). `supplied` is the read-only explicit
   inventory parameter; when present it is required well-formed (mapping.md §2). -/
method getFeatureInventory (mut st : InvState) (supplied : Option (List String))
    return (out : Except InvErr (List String))
  require (match supplied with
            | none       => True
            | some terms => terms ≠ [] ∧ terms.Nodup)
  ensures (st, out) = featureNamesRun stOld supplied
  do
    -- impl-start
    -- Establish the inventory first when one has not yet been established
    -- (running the unchanged establishment step), then apply the readiness
    -- guard and, on admission, read back the ordered feature inventory.
    st := if st.index = none then materializeIndex supplied st else st
    let out : Except InvErr (List String) :=
      match readinessGuard st with
      | Except.error e => Except.error e
      | Except.ok _    => Except.ok (featureList (st.index.getD []))
    return out
    -- impl-end

prove_correct getFeatureInventory by
  loom_solve
  simp_all only [featureNamesRun, materializeIndex, readinessGuard]
