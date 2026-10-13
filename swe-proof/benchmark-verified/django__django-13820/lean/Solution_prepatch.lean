import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decision modeled below
-- is a pure predicate over a module's introspected attributes (whether it has a
-- file location, whether it is a package, and whether its package path is an
-- ordinary list). The attribute reads are language-level introspection, modeled
-- directly as boolean field reads (I-tagged in refinement.md); nothing is
-- axiomatized. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The package-path information a module can expose to introspection:
either it is not a package at all, or it is a package whose path is an ordinary
list, or it is a package whose path is a custom (non-list) iterable. -/
inductive ModulePath where
  | noPath       -- the module exposes no package path (it is not a package)
  | listPath     -- the package path is an ordinary list
  | customPath   -- the package path is a custom, non-list iterable
  deriving DecidableEq, Repr

/-- Whether the module is a package (exposes a package path at all). -/
def ModulePath.isPackage : ModulePath → Bool
  | .noPath => false
  | _       => true

/-- Whether the module's package path is an ordinary list. -/
def ModulePath.isList : ModulePath → Bool
  | .listPath => true
  | _         => false
-- pure-end

-- post-conditions-start
/-- A module is treated as a source of migrations exactly when it is a package
AND it either has a file location on disk OR its package path is an ordinary
list. A package that has no file location and whose path is a custom iterable is
an empty-directory placeholder and is NOT treated as a source of migrations;
likewise a non-package is never a source of migrations.

`hasFile` is whether the module exposes a (non-empty) file location; `path`
carries the package-path information described by `ModulePath`. -/
def problem_spec_providesMigrations
    (hasFile : Bool) (path : ModulePath) (result : Bool) : Prop :=
  result = (path.isPackage && (hasFile || path.isList))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: a module with no file location is rejected up
-- front, BEFORE the package check, so EVERY package without a file location is
-- treated as a non-source — even one whose path is an ordinary list. This
-- mis-classifies regular packages that simply do not expose a file location.
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
  -- Reject anything without a file location (wrongly conflates "no file" with
  -- "empty-directory placeholder").
  if !hasFile then
    return false
  -- A module that is not a package cannot provide migrations.
  if !path.isPackage then
    return false
  return true
-- impl-end

-- proof-start
theorem correct_providesMigrations :
    ∀ (hasFile : Bool) (path : ModulePath),
      problem_spec_providesMigrations hasFile path
        (implementation_providesMigrations hasFile path) := by
  -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF):
  -- on hasFile = false, path = listPath the impl returns false while the spec
  -- demands true.
  intro hasFile path
  unfold problem_spec_providesMigrations implementation_providesMigrations
  cases path <;> cases hasFile <;> rfl
-- proof-end
