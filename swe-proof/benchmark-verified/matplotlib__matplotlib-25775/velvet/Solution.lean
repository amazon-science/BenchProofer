import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The behavior modeled here is a closed function of its inputs: the effective
   antialiasing flag carried by a text object is either the value supplied for
   that object, or — when none was supplied for it — the ambient/global default.
   Both the supplied value and the ambient default are ordinary booleans handed
   to the routine directly, so nothing about a separate callee needs to be
   assumed. The downstream plumbing that carries this resolved flag to the
   renderer is an identity on the boolean it transports (a type-only refinement,
   refinement.md §A/§B), validated against the real objects by
   conformance_check.py (G-CONF); it is not consumed as a Lean contract, so no
   `axiom` is introduced. -/
-- axioms-end

-- pure-start
/- The effective per-object rendering-quality flag. An object MAY carry an
   explicit choice for this flag (`some b`); if it does NOT (`none`), the
   ambient/global default is meant instead. The resolved flag is therefore the
   explicit choice when present, and the ambient default otherwise — so that
   leaving the per-object choice unspecified and naming the ambient default
   explicitly produce the same effective flag. -/
def resolveAA (requested : Option Bool) (ambient : Bool) : Bool :=
  match requested with
  | none   => ambient
  | some b => b

@[grind] lemma resolveAA_none (ambient : Bool) :
    resolveAA none ambient = ambient := rfl
@[grind] lemma resolveAA_some (b ambient : Bool) :
    resolveAA (some b) ambient = b := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the effective rendering-quality flag a text object will use, then
   expose it so the rest of the drawing path can honour it.

   The flag is a per-object property: an object may be given an explicit choice
   (`some b`), in which case that choice is the effective flag; if it is given
   no explicit choice (`none`), the ambient/global default is used. Consequently
   giving an object the ambient value explicitly and leaving it unspecified
   yield the same effective flag, while an explicit choice that differs from the
   ambient default takes effect for that object alone.

   Both inputs are read-only — neither is declared `mut` (directive 5): the
   routine only reads the optional per-object choice and the ambient default and
   returns the resolved flag; it mutates neither. The resolved value is pinned
   exactly by `resolveAA`. -/
method textAntialiased (requested : Option Bool) (ambient : Bool) return (out : Bool)
  ensures out = resolveAA requested ambient
  do
    -- impl-start
    -- Start from the ambient/global default, then let an explicit per-object
    -- choice override it when one was supplied.
    let aa := match requested with
      | none   => ambient
      | some b => b
    return aa
    -- impl-end

prove_correct textAntialiased by
  loom_solve
