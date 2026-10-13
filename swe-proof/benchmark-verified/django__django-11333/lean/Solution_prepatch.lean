import Mathlib
-- imports-end

/-!
Looking up the artifact that is associated with a configuration.

A configuration may be supplied explicitly, or it may be omitted, in which case
a designated default configuration is meant instead. The artifact for a configuration
is produced by a memoized factory: the factory is keyed on the configuration it
is asked about, and asking it twice about the same configuration yields the very
same artifact — not merely an equivalent copy, but the identical one.

The desired behavior concerns this identity. Omitting the configuration must
denote *exactly* the default configuration: a lookup that leaves the
configuration unspecified and a lookup that names the default configuration
explicitly describe the same configuration, and so they must yield the identical
artifact. The artifact is therefore pinned to the factory applied to the
effective configuration — the explicit one when given, the default one when
omitted — so that the unspecified and explicit-default lookups coincide.
-/

-- axioms-start
/-- An opaque handle standing for a produced artifact. Equality on `Artifact`
models identity of the produced object in the host runtime: two lookups yield
the *same* artifact exactly when these handles are equal. -/
structure Artifact where
  handle : Nat
deriving Inhabited, DecidableEq

/-- The memoized factory that produces the artifact for a configuration key.

It is keyed on the configuration it is given (the key space includes the
"omitted" key, represented by `none`, as well as every explicit configuration
`some s`). Being an ordinary function, it is referentially transparent: asking
it about equal keys yields the identical artifact. It is consumed here as an
opaque carrier — the behavior modeled in this bundle is *which key* is presented
to it, not how it builds an artifact. -/
opaque buildArtifact : Option String → Artifact
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is selecting
-- the effective configuration key and presenting it to the memoized factory.
-- pure-end

-- post-conditions-start
/-- The produced artifact is fully pinned: it is the one the memoized factory
produces for the *effective* configuration — the explicitly supplied
configuration when one is given, and the default configuration when the
configuration is omitted. Because the effective configuration of an omitted
lookup equals that of an explicit default lookup, both yield the identical
artifact. No part of the result is left free. -/
def problem_spec_cachedLookup
    (config : Option String) (defaultConfig : String) (result : Artifact) : Prop :=
  result = buildArtifact (some (config.getD defaultConfig))
-- post-conditions-end

-- impl-start
def implementation_cachedLookup
    (config : Option String) (defaultConfig : String) : Artifact := Id.run do
  let mut key := config
  return buildArtifact key
-- impl-end

-- proof-start
theorem correct_cachedLookup :
    ∀ (config : Option String) (defaultConfig : String),
      problem_spec_cachedLookup config defaultConfig
        (implementation_cachedLookup config defaultConfig) := by
  intro config defaultConfig
  unfold problem_spec_cachedLookup implementation_cachedLookup
  cases config <;> rfl
-- proof-end
