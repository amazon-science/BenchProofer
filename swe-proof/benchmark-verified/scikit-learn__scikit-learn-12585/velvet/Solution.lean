import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The operation the desired behaviour changes — how a
   reconstruction routine classifies an incoming value and decides what to do
   with it — is modeled DEEPLY and concretely in the `pure` region (`route`):
   it is a finite decision over three boolean observations of the value plus the
   caller's strictness flag, validated against the real classification by
   conformance_check.py (G-CONF). The two surrounding routines the chosen branch
   then defers to (a structure-preserving deep copy, and the parameter-based
   reconstruction of a configured object) are UNCHANGED callees; the only one a
   reproduced case depends on for its observable result — the structure-preserving
   deep copy applied to a class object — is an A-reference validated `== the real
   callee` by axiom_check.py (G-AX), NOT consumed as an axiom (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The action taken for an incoming value when reproducing a configured object.
   Exactly one of four mutually exclusive outcomes:
   * `mapElements`     — the value is a homogeneous sequence/collection, so each
                         element is reproduced and a like collection rebuilt;
   * `deepCopy`        — the value is not a configurable object, and the caller
                         is lenient, so a structure-preserving deep copy is made;
   * `refuse`          — the value is not a configurable object, and the caller
                         is strict, so reproduction is refused;
   * `reconstruct`     — the value is a configurable object, so it is rebuilt
                         from its declared parameters. -/
inductive Route where
  | mapElements
  | deepCopy
  | refuse
  | reconstruct
  deriving DecidableEq, Inhabited, Repr

/- The routing decision, as a function of three independent observations of the
   value and the caller's strictness:
   * `isCollection`    — the value is one of the recognized homogeneous
                         collection kinds;
   * `exposesParams`   — the value advertises a declared-parameter interface;
   * `isClassObject`   — the value is itself a class, not an instance of one;
   * `strict`          — the caller demands a configurable object (no fallback).

   A value qualifies for parameter-based reconstruction ONLY when it both
   advertises the parameter interface AND is a genuine instance — a class object
   advertises the interface yet cannot be reconstructed through it, so it must be
   treated as a non-configurable value and routed to the deep-copy / refuse
   branch. Collections are handled first, before either test. -/
def route (isCollection exposesParams isClassObject strict : Bool) : Route :=
  if isCollection then Route.mapElements
  else
    if (!exposesParams) || isClassObject then
      if strict then Route.refuse else Route.deepCopy
    else Route.reconstruct
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how a single incoming value is reproduced while rebuilding a
   configured object. The decision is driven entirely by three independent
   observations of the value — whether it is a recognized homogeneous collection,
   whether it advertises a declared-parameter interface, and whether it is itself
   a class object rather than an instance — together with whether the caller
   demands a configurable object. A class object that happens to advertise the
   parameter interface is NOT a reconstructable configured object: it must fall
   through to the deep-copy (lenient) or refuse (strict) branch alongside ordinary
   non-configurable values, never to parameter-based reconstruction. -/
method copyRoute (isCollection : Bool) (exposesParams : Bool)
    (isClassObject : Bool) (strict : Bool)
    return (out : Route)
  ensures out = route isCollection exposesParams isClassObject strict
  do
    -- impl-start
    if isCollection then
      return Route.mapElements
    else
      -- A configured object must advertise the parameter interface AND be a
      -- genuine instance; a class object is excluded from reconstruction here.
      let nonConfigurable : Bool := (!exposesParams) || isClassObject
      if nonConfigurable then
        if strict then
          return Route.refuse
        else
          return Route.deepCopy
      else
        return Route.reconstruct
    -- impl-end

prove_correct copyRoute by
  loom_solve <;> simp_all [route]
