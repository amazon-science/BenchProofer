import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An element data type, modeled as an opaque comparable handle: the dispatch
   never decomposes a data type, it only resolves a default and compares the
   data type carried by the array it produces. -/
abbrev Dtype := Int

/- A materialized array: its element content (`elems`, an opaque carrier — the
   dispatch never inspects individual elements) together with the element data
   type it is tagged with (`dtype`). The only behaviour the desired contract
   observes is the resulting `dtype`; `elems` rides along to record that the
   content is carried through unchanged. -/
structure MatArray where
  elems : List Int
  dtype : Dtype
  deriving DecidableEq, Inhabited

/- The data type recorded for a view (`adapter` is an opaque handle for the
   view instance). An UNCHANGED observation, never redefined by the desired
   change. Provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
opaque recordedDtype : Int → Dtype

/- Whether the view exposes a single *component* of a composite index (rather
   than the composite index as a whole). When it does, the materialization is
   served from that component's stored values; otherwise it is delegated to the
   base materialization. An UNCHANGED structural observation. Provenance:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque isComponent : Int → Bool

/- The stored values of the exposed component, as an array tagged with whatever
   data type the underlying storage happens to use — which need NOT be the
   view's recorded data type (the underlying storage may use a wider data type).
   An UNCHANGED callee invoked, never redefined; modeled `opaque` with no
   asserted `ensures` (the desired behaviour assumes nothing about WHICH values
   or storage data type it yields). Provenance + soundness: mapping.md §3.1 /
   axiom_check.py (G-AX). -/
opaque componentValues : Int → MatArray

/- Produce an array with the SAME content as the given one but tagged with the
   requested data type `d`. An UNCHANGED conversion callee; modeled `opaque`
   with no asserted `ensures`. The fact that the real conversion yields an array
   whose data type is exactly `d` is the A-reference fact G-AX validates against
   the real callee (mapping.md §3.2). -/
opaque toDtype : MatArray → Dtype → MatArray

/- The base materialization used when the view is NOT a single component: it
   resolves a missing requested data type to the view's recorded data type
   internally and yields an array of that data type. An UNCHANGED inherited
   callee; modeled `opaque` with no asserted `ensures`. Provenance: mapping.md
   §3.3 / axiom_check.py (G-AX). -/
opaque baseMaterialize : Int → Option Dtype → MatArray
-- axioms-end

-- pure-start
/- The intended result of materializing the view as an array.

   First the requested data type is resolved: a missing request defaults to the
   view's recorded data type. Then:

     * if the view exposes a single component of a composite index, its stored
       values are materialized AND retagged to the resolved data type — so the
       result's data type is the view's recorded (or explicitly requested) data
       type, regardless of the data type the underlying storage used;
     * otherwise the materialization is delegated to the base materialization
       (which performs the same default resolution internally).

   The component branch is the discriminating one: it must yield the resolved
   data type, not the storage's native data type. -/
def arrayMaterialize (adapter : Int) (dtype : Option Dtype) : MatArray :=
  let d := dtype.getD (recordedDtype adapter)
  if isComponent adapter then
    toDtype (componentValues adapter) d
  else
    baseMaterialize adapter dtype
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Materialize a view as an array of a definite element data type.

   Desired behaviour: a view carries a recorded element data type. Materializing
   it must produce an array of that recorded data type when none is explicitly
   requested, and of the requested data type otherwise — in particular when the
   view exposes a single component of a composite index, whose stored values may
   be held under a wider data type, materialization must still yield the
   resolved recorded/requested data type rather than the storage's native one
   (the missing behaviour the public problem statement reports: building a
   composite index must not change the element data type of the views it is
   built from). When the view is not such a component, materialization is
   delegated to the base materialization, which resolves the default the same
   way.

   `adapter` (the view handle) and `dtype` (the optionally-requested data type)
   are read-only inputs (not `mut`): the dispatch computes an array and mutates
   no input (directive 5). The view is modeled as an opaque handle; the only
   observations are its recorded data type, whether it is a single component,
   and the component's stored values (mapping.md §2). -/
method arrayDispatch (adapter : Int) (dtype : Option Dtype)
    return (out : MatArray)
  ensures out = arrayMaterialize adapter dtype
  do
    -- impl-start
    -- Resolve a missing requested data type to the view's recorded data type,
    -- then branch on whether the view exposes a single component: a component's
    -- stored values are materialized and RETAGGED to the resolved data type
    -- (rather than escaping with the storage's native data type); otherwise the
    -- materialization is delegated to the base materialization.
    let d : Dtype := dtype.getD (recordedDtype adapter)
    let result : MatArray :=
      if isComponent adapter then
        toDtype (componentValues adapter) d
      else
        baseMaterialize adapter dtype
    return result
    -- impl-end

prove_correct arrayDispatch by
  loom_solve
  simp_all [arrayMaterialize]
