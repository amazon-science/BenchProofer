import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The metadata-propagation effect is modeled DEEPLY in the
--  `pure` region as `propagate`; the standard introspection facility whose effect
--  it models is an A-reference, validated == the real facility by axiom_check.py
--  (G-AX), NOT consumed as an axiom. There is no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The introspectable metadata a callable exposes, restricted to exactly the
   three observations the desired behaviour constrains:
     * `name` — the introspected name of the callable;
     * `doc`  — the introspected documentation of the callable;
     * `sig`  — the string form of the callable's introspected call signature.
   Everything else a callable carries is orthogonal to the desired behaviour
   (mapping.md §2), so it is not modeled. -/
structure CallableMeta where
  name : String
  doc  : String
  sig  : String
  deriving DecidableEq

/- The desired effect of building a forwarding wrapper around a target callable,
   modeled deeply. A wrapper that forwards every call to `target` must, when
   introspected, present as the TARGET on all three observations — its
   introspected name, documentation, AND call signature are those of the target,
   never the wrapper's own generic variadic form. `forwarder` (the wrapper's own
   pre-propagation metadata, whose `sig` is the generic forwarding signature) is
   supplied only so the post-state frame is stated against a concrete input;
   under full propagation none of its fields survive. Pinned by the method's
   `ensures`; validated == the real introspection facility by G-AX. -/
def propagate (forwarder target : CallableMeta) : CallableMeta :=
  { name := target.name, doc := target.doc, sig := target.sig }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the introspectable metadata of a wrapper that forwards every call to a
   target callable. Desired behaviour: the wrapper must be indistinguishable from
   the target under introspection — its name, its documentation, AND the string
   form of its call signature must all be those of the target. Copying only the
   name and documentation while leaving the wrapper's own generic forwarding
   signature in place is insufficient: introspection of the call signature must
   resolve to the target's, so that signature-reporting tools observe the target's
   parameters rather than the forwarder's variadic `(*args, **kwargs)`. -/
method buildForwarderMeta (forwarder : CallableMeta) (target : CallableMeta) return (out : CallableMeta)
  ensures out.name = target.name
  ensures out.doc  = target.doc
  ensures out.sig  = target.sig
  do
    -- impl-start
    -- Propagate the full introspectable metadata of `target` onto the wrapper:
    -- name, documentation, AND call signature (so introspection resolves through
    -- to the target). `propagate` is the deep model of the standard facility.
    return propagate forwarder target
    -- impl-end

prove_correct buildForwarderMeta by
  loom_solve <;> simp [propagate]
