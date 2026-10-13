import Mathlib
-- imports-end

/-!
Naming an automatically generated test fixture.

When the test framework synthesizes a fixture to run a class/module/function
setup–teardown pair, it assigns that fixture a unique name built from a constant
descriptive template and the owning object's qualified name. Such synthesized
fixtures carry no documentation of their own, so they belong to the framework's
internal machinery rather than the user-facing fixture surface. By convention the
fixture listing hides a fixture whose name begins with an underscore at the
default verbosity (showing it only when extra verbosity is requested); a name
that does NOT begin with an underscore is always shown.

The desired behavior: a generated fixture's name is private — it begins with an
underscore — while every following component of the name (the descriptive
template and the owning object's qualified name) is exactly the descriptive name
built from the inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The fixture name is built purely from
-- the constant descriptive template and the two string inputs (the setup-hook name
-- and the owning object's qualified name); there is no callee contract to model,
-- so the `axioms` region is empty and G-AX skips.
-- axioms-end

-- pure-start
/-- The descriptive part of a generated setup–teardown fixture's name: the constant
template woven together with the setup-hook name and the owning object's
qualified name. Modeled per code point as `List Char` (total, sound indexing). -/
def descriptiveName (setupName qualname : List Char) : List Char :=
  "unittest_".toList ++ setupName ++ "_fixture_".toList ++ qualname
-- pure-end

-- post-conditions-start
/-- The generated fixture name is the descriptive name for the given inputs made
private: an underscore followed by the full descriptive name. This pins every
component — the leading private marker, the constant template, and both string
inputs — so the result is the descriptive name and nothing else, with the private
marker at the front. -/
def problem_spec_generatedFixtureName
    (setupName qualname : List Char) (result : List Char) : Prop :=
  result = '_' :: descriptiveName setupName qualname
-- post-conditions-end

-- impl-start
def implementation_generatedFixtureName
    (setupName qualname : List Char) : List Char := Id.run do
  let mut name : List Char := []
  name := name ++ "_".toList
  name := name ++ "unittest_".toList
  name := name ++ setupName
  name := name ++ "_fixture_".toList
  name := name ++ qualname
  return name
-- impl-end

-- proof-start
theorem correct_generatedFixtureName :
    ∀ (setupName qualname : List Char),
      problem_spec_generatedFixtureName setupName qualname
        (implementation_generatedFixtureName setupName qualname) := by
  intro setupName qualname
  simp only [problem_spec_generatedFixtureName, implementation_generatedFixtureName,
    descriptiveName, Id.run, List.append_assoc, List.nil_append]
  rfl
-- proof-end
