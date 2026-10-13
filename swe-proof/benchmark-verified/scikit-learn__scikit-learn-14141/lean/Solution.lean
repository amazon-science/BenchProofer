import Mathlib
-- imports-end

/-!
Building the overview of installed dependency versions.

A diagnostics helper reports, for a chosen roster of relevant third-party
libraries, the installed version of each. It walks a hardcoded list of library
import-names and, for every name, records that name together with the version it
resolves to (or a null marker when the library is not importable). The result is
an ordered name→version mapping.

The desired behavior:

  * the mapping covers exactly the roster of relevant libraries — in the roster's
    order, with no name omitted and none added;
  * for each library the recorded value is the version produced by resolving that
    library (a null marker when it cannot be resolved);
  * the roster of relevant libraries includes, alongside the core numerical and
    build dependencies, the parallelism/serialization helper library `joblib`.
-/

-- axioms-start
/-- Resolution of a single library's installed version from its import-name: the
imported module's reported version, or a null marker when the library cannot be
imported. This is an unchanged helper, declared opaque so it can appear in the
executable implementation; the specification uses it identically on both sides and
consumes no property of it. -/
opaque lookupVersion : String → Option String
-- axioms-end

-- pure-start
/-- The roster of relevant library import-names the overview must cover, in order.
Includes `joblib` alongside the core numerical and build dependencies. -/
def expectedDeps : List String :=
  ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython", "pandas",
   "matplotlib", "joblib"]
-- pure-end

-- post-conditions-start
/-- The overview maps each library in the roster — in order, exactly that set of
names — to its resolved version. In particular `joblib` is among the covered
names. -/
def problem_spec_dependencyVersions
    (result : List (String × Option String)) : Prop :=
  result = expectedDeps.map (fun m => (m, lookupVersion m))
-- post-conditions-end

-- impl-start
def implementation_dependencyVersions : List (String × Option String) := Id.run do
  let deps := expectedDeps
  let mut depsInfo : List (String × Option String) := []
  for modname in deps do
    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
  return depsInfo
-- impl-end

-- proof-start
theorem correct_dependencyVersions :
    problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  simp [expectedDeps]
-- proof-end
