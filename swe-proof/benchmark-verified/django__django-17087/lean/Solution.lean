import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: every datum the reference
-- string is built from (the defining module, the owning class's bare name and
-- its fully-qualified dotted name, and the method's own name) is an attribute
-- read, modeled directly as an input field. The string assembly is plain
-- concatenation, modeled deeply and checked mechanically. The proof agent may
-- add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A method object bound to a class (the case where the migration writer must
emit a dotted reference to a method that lives on a class). The four fields are
the data the reference is assembled from:
* `module`        — the dotted module path the owning class is defined in;
* `ownerName`     — the owning class's bare, innermost name;
* `ownerQualname` — the owning class's fully-qualified dotted name (for a class
  nested inside another class this includes the enclosing class names, e.g.
  `Outer.Inner`; for a top-level class it coincides with `ownerName`);
* `methodName`    — the method's own name. -/
structure BoundClassMethod where
  module : List Char
  ownerName : List Char
  ownerQualname : List Char
  methodName : List Char

/-- The assembled reference: the dotted reference string plus the import
statements it requires. -/
structure DottedRef where
  text : List Char
  imports : List (List Char)

/-- The single import statement needed to resolve a reference defined in
`module`. -/
def importFor (module : List Char) : List Char := "import ".toList ++ module
-- pure-end

-- post-conditions-start
/-- A reference to a class-bound method is the dotted path
`module . ownerQualname . methodName`, qualified by the owning class's FULLY
qualified name so that a method living on a class nested inside another class
resolves to its true location; together with the single import of the defining
module. Both result components are pinned to the inputs. -/
def problem_spec_classMethodRef (m : BoundClassMethod) (result : DottedRef) : Prop :=
  result.text =
      m.module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName ∧
  result.imports = [importFor m.module]
-- post-conditions-end

-- impl-start
def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
  let module := m.module
  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
  return { text := text, imports := [importFor module] }
-- impl-end

-- proof-start
theorem correct_classMethodRef : ∀ m : BoundClassMethod,
    problem_spec_classMethodRef m (implementation_classMethodRef m) := by
  intro m
  unfold problem_spec_classMethodRef implementation_classMethodRef
  refine ⟨rfl, rfl⟩
-- proof-end
