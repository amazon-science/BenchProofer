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
-- PRE-PATCH (buggy): the generated name is the bare descriptive name with no
-- leading private marker, so a name that should be hidden at default verbosity is
-- always shown. This is the actual bug. Its `correct_*` cannot close: the spec
-- demands a leading `'_'`, absent here.
def implementation_generatedFixtureName
    (setupName qualname : List Char) : List Char := Id.run do
  let mut name : List Char := []
  name := name ++ "unittest_".toList
  name := name ++ setupName
  name := name ++ "_fixture_".toList
  name := name ++ qualname
  return name
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- buggy impl it cannot close: the spec requires `result = '_' :: descriptiveName …`
-- but this impl produces `descriptiveName …` with no leading underscore, so the
-- final structural equality fails. (The proof agent carries the closed Solution.lean
-- proof here; it must fail to typecheck — that is exactly the G-DIFF signal.)
theorem correct_generatedFixtureName :
    ∀ (setupName qualname : List Char),
      problem_spec_generatedFixtureName setupName qualname
        (implementation_generatedFixtureName setupName qualname) := by
  sorry
-- proof-end
