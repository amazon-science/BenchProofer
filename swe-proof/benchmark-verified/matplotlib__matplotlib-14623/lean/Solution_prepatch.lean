import Mathlib
-- imports-end

/-!
Setting the visible coordinate range of an axis from a requested pair of
endpoints.

A caller supplies two endpoint values describing the range that should become
visible. The caller may supply them in increasing order (the range runs in the
ascending direction) or in decreasing order (the range runs in the descending,
"flipped" direction). Before the range is committed, each endpoint is run
through two normalizing steps:

* a degenerate (zero-width) range is expanded so that the two endpoints are
  distinct, with the normalizer returning its two endpoints in increasing
  order; and
* the endpoints are restricted to the values permitted by the axis (some axes
  only accept endpoints from a limited domain).

The desired behavior: the *direction* the caller asked for must survive these
normalizing steps. If the caller gave the endpoints in increasing order the
committed range is ascending; if the caller gave them in decreasing order the
committed range is descending. In magnitude the committed endpoints are exactly
the two values produced by the normalizing steps; only their order may be
adjusted to match the requested direction.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Two unchanged dependency callees the behavior uses. Their results pass
-- through verbatim into the committed range; the modeled behavior (the
-- direction-restoring reassembly) is spelled out concretely below and consumes
-- no property of either callee, so no `_prop` axiom is declared. Each callee is
-- left as the real repo callee in the differential check (G-CONF, A-reference).

/-- The singularity-avoiding endpoint normalizer: given two endpoints it returns
a pair, expanding a degenerate range when necessary. -/
opaque normalizeRange : Rat → Rat → Rat × Rat

/-- The scale-domain limiter: restricts a pair of endpoints to the axis's
permitted domain. -/
opaque clampToDomain : Rat → Rat → Rat × Rat
-- axioms-end

-- pure-start
-- No additional pure helpers: the modeled behavior is the direction-preserving
-- reassembly of the normalized endpoints, spelled out directly below.
-- pure-end

-- post-conditions-start
/-- `result` is the committed range for requested endpoints `a`, `b`.

Let `p` be the pair obtained by normalizing `(a, b)` and then restricting it to
the axis domain. Then:

* if the caller requested ascending order (`a ≤ b`) the committed range is `p`
  unchanged (ascending); and
* if the caller requested descending order (`a > b`) the committed range is `p`
  with its two endpoints exchanged (descending).

So the committed magnitudes are exactly the two values of `p` and their order is
determined solely by the order the caller requested. -/
def problem_spec_setLim (a b : Rat) (result : Rat × Rat) : Prop :=
  let n := normalizeRange a b
  let p := clampToDomain n.1 n.2
  result = if a > b then (p.2, p.1) else p
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the requested direction is discarded. The
-- endpoints are normalized and committed verbatim in the normalizer's
-- increasing order, so a descending request is silently flipped to ascending.
def implementation_setLim (a b : Rat) : Rat × Rat := Id.run do
  let n := normalizeRange a b
  let c := clampToDomain n.1 n.2
  let mut lo : Rat := c.1
  let mut hi : Rat := c.2
  return (lo, hi)
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (when
-- `a > b` the committed range is ascending, contradicting the `a > b →
-- result.2 ≤ result.1` clause unless the two endpoints coincide).
theorem correct_setLim :
    ∀ (a b : Rat),
      problem_spec_setLim a b (implementation_setLim a b) := by
  sorry
-- proof-end
