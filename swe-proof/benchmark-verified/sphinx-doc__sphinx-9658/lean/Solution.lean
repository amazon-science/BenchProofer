import Mathlib
-- imports-end

/-!
The qualified name reported by a mock stand-in object.

When a documentation tool encounters an attribute access on a mocked module or
object, it fabricates a lightweight stand-in to represent the referenced symbol.
Each stand-in is created with a *short name* — the final dotted component of the
symbol it stands for (e.g. the `Class` in `pkg.sub.Class`).

A downstream renderer forms a complete reference by joining the stand-in's
containing module path with the *qualified name* the stand-in reports. For that
joined reference to be complete (rather than ending at the dot, with the final
component missing), the qualified name a stand-in reports must equal the short
name it was created with.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the reported qualified
-- name is determined directly from the short name the stand-in was created
-- with (a value-level string identity), with no opaque callee involved.
-- axioms-end

-- pure-start
-- No additional pure helpers are required.
-- pure-end

-- post-conditions-start
/-- The qualified name a mock stand-in reports equals the short name it was
created with. -/
def problem_spec_mockQualifiedName (name : String) (result : String) : Prop :=
  result = name
-- post-conditions-end

-- impl-start
def implementation_mockQualifiedName (name : String) : String := Id.run do
  -- the stand-in records the short name it was created with
  let mut nameAttr := name
  -- its qualified name is taken from that recorded short name
  let mut qualname := nameAttr
  return qualname
-- impl-end

-- proof-start
theorem correct_mockQualifiedName :
    ∀ (name : String),
      problem_spec_mockQualifiedName name
        (implementation_mockQualifiedName name) := by
  intro name
  unfold problem_spec_mockQualifiedName implementation_mockQualifiedName
  rfl
-- proof-end
