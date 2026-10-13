import Mathlib
-- imports-end

/-!
Building a delegating method that forwards calls to an underlying method, while
remaining faithful to that underlying method under introspection.

A delegating method is created as a generic forwarding wrapper: intrinsically it
carries only catch-all, placeholder introspectable metadata — a generic call
signature that accepts arbitrary arguments, its own internal qualified name and
defining module, and no documentation or parameter annotations. Tooling that
inspects a method (to display its call signature, its documentation, its
identity) reads this metadata.

For the delegating method to be indistinguishable from the method it stands in
for, ALL of its observable introspection metadata must mirror the underlying
method's:

  * the reported name,
  * the reported qualified name,
  * the reported defining module,
  * the documentation,
  * the parameter annotations,
  * and — crucially — the call signature reported for it, which must be the
    underlying method's real parameter list rather than the generic catch-all of
    a bare forwarding wrapper.

The desired behavior is that every one of these introspectable attributes of the
delegating method equals the corresponding attribute of the underlying method;
none is left at the generic placeholder value a bare wrapper would carry.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The underlying
-- method's introspectable metadata and the bare wrapper's placeholder metadata
-- enter as plain data; the only operation is the field-by-field selection of
-- which metadata the produced method exposes, modeled directly over the metadata
-- carrier. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The introspectable metadata of a method, restricted to the observable
attributes that method-inspection tooling reads. Each is modeled as a `String`
(only equality is observed):
* `name` — the reported method name;
* `qualname` — the reported qualified name;
* `module` — the reported defining module;
* `doc` — the documentation (empty string when absent);
* `annotations` — the parameter annotations, serialized (empty when absent);
* `signature` — the rendered call signature (parameter list) inspection reports.
-/
structure MethodMetadata where
  name : String
  qualname : String
  module : String
  doc : String
  annotations : String
  signature : String
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The produced delegating method's metadata is fully pinned to the underlying
method's: every observable introspection attribute equals the underlying
method's corresponding attribute. In particular the reported call signature is
the underlying method's real parameter list — never the generic catch-all of the
bare wrapper. No metadata field is left free or at a placeholder value. -/
def problem_spec_delegateMetadata
    (underlying rawDelegate : MethodMetadata) (result : MethodMetadata) : Prop :=
  result.name = underlying.name ∧
  result.qualname = underlying.qualname ∧
  result.module = underlying.module ∧
  result.doc = underlying.doc ∧
  result.annotations = underlying.annotations ∧
  result.signature = underlying.signature
-- post-conditions-end

-- impl-start
def implementation_delegateMetadata
    (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
  -- PRE-PATCH (buggy): only the name and documentation are propagated onto the
  -- bare forwarding wrapper; the reported signature, qualified name, module, and
  -- annotations are left at the generic placeholder values, so inspection sees a
  -- catch-all signature instead of the underlying method's real parameter list.
  let mut md := rawDelegate
  md := { md with
    name := underlying.name,
    doc := underlying.doc }
  return md
-- impl-end

-- proof-start
theorem correct_delegateMetadata :
    ∀ (underlying rawDelegate : MethodMetadata),
      problem_spec_delegateMetadata underlying rawDelegate
        (implementation_delegateMetadata underlying rawDelegate) := by
  intro underlying rawDelegate
  unfold problem_spec_delegateMetadata implementation_delegateMetadata
  simp only [Id.run, bind, pure]
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
