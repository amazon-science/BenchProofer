import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the only derivation this operation defers to — the
--  recomputation of the read-through view from the registry — is modeled
--  DEEPLY as `recomputeLookups` in the `pure` region and validated against the
--  real callee by G-AX (an A-reference), not consumed as an axiom. See
--  mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Lookup the value bound to `name` in an association list (first binding wins;
   the carriers come from real mappings, whose keys are unique). -/
def lookupKey : List (String × Nat) → String → Option Nat
  | [],             _    => none
  | (k, v) :: rest, name => if k = name then some v else lookupKey rest name

/- Whether `name` is currently bound in the registry. -/
def hasKey (reg : List (String × Nat)) (name : String) : Bool :=
  (lookupKey reg name).isSome

/- Remove every binding for `name` from an association list (keys are unique,
   so this drops exactly the one binding for `name`). -/
def eraseKey : List (String × Nat) → String → List (String × Nat)
  | [],             _    => []
  | (k, v) :: rest, name =>
      if k = name then eraseKey rest name else (k, v) :: eraseKey rest name

/- The recomputed read-through view of the registry: the registry's own
   bindings, overlaid on the inherited bindings (an inherited binding survives
   only when its key is not present in the registry). As a key→value mapping
   this is exactly "inherited defaults updated by the registry's own bindings"
   (the registry's own bindings win). Deep model of the unchanged derivation
   that builds the view; validated equal to that derivation by G-AX
   (A-reference, mapping.md §3.1), so no axiom about it is consumed. -/
def recomputeLookups (inherited registry : List (String × Nat)) : List (String × Nat) :=
  registry ++ inherited.filter (fun kv => (lookupKey registry kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- (removeBinding requires the name to be currently bound, so removing it is
--  well-defined; stated on the method below.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Remove a named binding from a registry while keeping a derived, cached
   read-through view of that registry consistent with it.

   The registry holds the bindings owned at this level; a separate cached view
   exposes those bindings overlaid on the inherited ones (the registry's own
   bindings winning), and is what callers consult. The desired behavior: drop
   the named binding from the registry AND re-derive the cached view from the
   now-current registry, so that a subsequent consultation of the cached view
   reflects the removal (the removed name is no longer exposed unless it is
   independently inherited).

   `registry` is the owned-binding store; it is genuinely mutated — the named
   binding is dropped — and its post-state is pinned EXACTLY to
   `eraseKey registryOld name` (directive 5: the changed frame is stated at its
   exact post-state). `cached` is the read-through view; it is re-derived from
   the updated registry, so it is pinned to `recomputeLookups inherited
   registry` and thereby grounded in the inputs. `inherited` is read-only. -/
method removeBinding
    (mut registry : List (String × Nat))
    (mut cached : List (String × Nat))
    (inherited : List (String × Nat))
    (name : String)
    return (u : Unit)
  require hasKey registry name = true
  ensures registry = eraseKey registryOld name
  ensures cached = recomputeLookups inherited registry
  do
    -- impl-start
    -- Pre-image skeleton: the named binding is dropped from the registry, but
    -- the cached read-through view is left at its prior value — it is NOT
    -- re-derived from the now-current registry. The frozen spec requires the
    -- cached view to equal `recomputeLookups inherited registry` (the view of
    -- the registry AFTER the removal), so prove_correct MUST fail on the second
    -- `ensures`: the stale view still exposes the removed name.
    registry := eraseKey registry name
    cached := cached
    return
    -- impl-end

prove_correct removeBinding by
  loom_solve
