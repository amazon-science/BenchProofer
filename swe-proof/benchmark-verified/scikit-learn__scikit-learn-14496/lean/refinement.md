# refinement.md — scikit-learn__scikit-learn-14496

Maps every operation in `implementation_resolveMinSamples` and
`implementation_resolveThresholds` to its `patch.diff` counterpart in
`sklearn/cluster/optics_.py`.
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## The modeled decision
A neighborhood-size threshold supplied as a fraction in `(0, 1]` must be turned
into an absolute whole-number count: `max(2, int(frac * n_samples))`. The fix is
the `int(...)` truncation — pre-patch `max(2, frac * n_samples)` returned a float
(e.g. `0.1 * 30 → 3.0`, and `0.1 * 25 → 2.5`), which is not a valid count for the
downstream consumer (it requires an integer). The same normalization is fixed at
three sites:

```python
# compute_optics_graph (optics_.py:439-440)               -> resolveMinSamples
if min_samples <= 1:
    min_samples = max(2, int(min_samples * n_samples))
# cluster_optics_xi (optics_.py:620-627)                  -> resolveThresholds
if min_samples <= 1:
    min_samples = max(2, int(min_samples * n_samples))
if min_cluster_size is None:
    min_cluster_size = min_samples
if min_cluster_size <= 1:
    min_cluster_size = max(2, int(min_cluster_size * n_samples))
```

`int(x)` truncates toward zero; the scaled amount `frac * n_samples` is `≥ 0`, so
for this branch `int(·) = floor(·) = ⌊·⌋` (measured over the modeled domain: 0
divergences).

The threshold is modeled as a two-form `Threshold` (mapping.md): either an
absolute `count (k : ℤ)`, or a divisible `quantity (q : ℚ)` — a fraction `≤ 1`,
or any float. `normCount scaled = .count (max 2 ⌊scaled⌋)` is the post-patch
reduction, and it delivers its outcome in **count** form.

That form is load-bearing, not decoration. `int(...)` returns a Python `int`,
while the pre-patch `max(2, frac * n)` returns the `float` operand whenever it
exceeds two; the downstream consumer is a TYPE check
(`sklearn/neighbors/base.py:275`: `if not isinstance(self.n_neighbors,
numbers.Integral): raise TypeError(...)`), so it admits `3` and rejects `3.0` —
values of equal magnitude. A magnitude-only carrier models that distinction away:
measured, an implementation reducing as `normCount scaled / 1` satisfies even an
explicit `∃ k : ℤ, result = (k : ℚ)` under such a carrier (build exit 0), while
its faithful patch leaves `test_extract_xi` failing on that very `TypeError`. So
the specification's clauses are equalities of *thresholds*, pinning form together
with magnitude; `Threshold.amount` is used only where the real routine genuinely
tests the magnitude alone (`if min_samples <= 1`), so the branch guards are not
accidentally turned into form tests.

**Model boundary — the multiply is upstream, not modeled.** The patch left
`min_samples * n_samples` untouched and changed only what is done to its result.
The scaled amount therefore enters the model as an input (`scaled`, and
`scaledLead` / `scaledTrail`) rather than being recomputed inside it. Faithfulness
demands this: the repo's multiply yields the nearest representable double, and an
in-model exact-rational product `x * (n : ℚ)` is a different function — they
disagree wherever the representable product lands on the far side of an integer
from the exact one (`0.6 @ 5` → the repo's amount is exactly 3 and it delivers a
count of 3; the exact rational product sits below 3 and floors to 2). Every value
the multiply can produce is a dyadic rational, so the `ℚ` binder carries it
exactly and nothing is abstracted away: the whole reduction — floor, clamp to two,
branch guards, unset default — remains pinned.

## Operation correspondence — `resolveMinSamples` (site 1, compute_optics_graph)
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 0 | `if minSamples.admits populationSize then … else return none` | `_validate_size(min_samples, n_samples, 'min_samples')` (optics_.py:438; validator body :280-290) | R | the range check, modeled deeply: `size > 0` ↔ `0 < t.amount`, `size == int(size) or size <= 1` ↔ `t.amount.den = 1 ∨ t.amount ≤ 1`, `size <= n_samples` ↔ `t.amount ≤ (populationSize : ℚ)`. It raises rather than returning, so its refusal ↔ `result = none` and the routine is PARTIAL (`Option`). A magnitude test on both sides: `3.0 @ 10` passes, `2.5 @ 10` raises, `11 @ 10` raises. |
| 1 | `let mut ms := minSamples` | `min_samples` parameter (the threshold) | R | `int`-or-`float` threshold ↔ `Threshold` (`count` / `quantity`; mapping.md). |
| 2 | `if ms.amount ≤ 1 then` | `if min_samples <= 1:` | I | fraction-vs-count discriminator: an identical comparison, and a comparison of MAGNITUDES on both sides — Python compares the number regardless of whether it arrived as `int` or `float`, so `.amount` (not the form) is the correct subject here. |
| 3a | `scaled` binder | `min_samples * n_samples` (unchanged by the patch) | R | the scaling step, OUTSIDE the modeled behavior: the repo's float product is carried in as an exact `ℚ` (a double is dyadic). NOT recomputed in Lean — see "Model boundary" above. |
| 3b | `ms := normCount scaled` | `max(2, int(...))` applied to that amount | R | the introduced reduction: `int(·)` ↔ `⌊·⌋` over `≥0`; `max(2,·)` over `ℤ`; and `.count` for the `int` TYPE the composite returns — `max` of two Python `int`s is an `int` on every admissible input, so the count form is unconditional here. G-CONF drives the real `compute_optics_graph`, captures the `n_neighbors` delivered to the neighbor query, and compares against a shadow that takes its scaled amount from the identical multiply, in form as well as magnitude. |
| 4 | `return ms` | the integer threshold flowing to `NearestNeighbors(n_neighbors=...)` | I | return the normalized count. On the keep-unchanged branch this is Python's identity assignment, which preserves the form exactly — hence the spec's `result = minSamples` there rather than a claim that the result is a count. `_validate_size` admits a whole-valued float above one (measured: `3.0` passes, `2.5` / `7.5` raise), so demanding count form on that branch would narrow the domain the real function accepts. |

## Operation correspondence — `resolveThresholds` (sites 2+3, cluster_optics_xi)
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 0 | `if minSamples.admits populationSize then … else return none` | `_validate_size(min_samples, n_samples, 'min_samples')` (optics_.py:620) | R | the leading range check, same correspondence as site 1's row 0; a rejected leading threshold refuses the whole pair (`result = none`). |
| 1 | `let mut ms := minSamples` | `min_samples` parameter | R | threshold ↔ `Threshold`. |
| 2 | `if ms.amount ≤ 1 then ms := normCount scaledLead` | `if min_samples <= 1: min_samples = max(2, int(min_samples * n_samples))` | R | site 2, same reduction as above, on the leading scaled amount carried in from the repo's multiply. |
| 3 | `let mcs0 := trailingThreshold.getD ms` | `if min_cluster_size is None: min_cluster_size = min_samples` | R | unset trailing threshold defaults to the already-reduced leading one, carried in whatever form that has (Python's assignment is identity); `None` ↔ `Option.none`, `getD` ↔ the default-assignment. |
| 3b | `if mcs0.admits populationSize then … else return none` | `_validate_size(min_cluster_size, n_samples, 'min_cluster_size')` (optics_.py:625) | R | the TRAILING range check — applied to `mcs0`, the value row 3 just computed, *after* the default is taken. So this leg cannot be expressed as a precondition on the arguments, and it can refuse a pair whose leading threshold the same check admitted: at `min_samples=0.5, min_cluster_size=None, n_samples=1` the leading check admits `0.5`, the reduction makes it `2`, the default carries `2` into the trailing slot, and `2 > 1 = n_samples` raises `ValueError: min_cluster_size must be no greater than the number of samples`. Measured against the patched repo; the explicit-trail control `(0.5, 0.5, 1)` at the same population size is admitted and delivers `(2, 2)`, which shows the refusal comes from the DEFAULT and not from the population size alone. |
| 4 | `if mcs.amount ≤ 1 then mcs := normCount scaledTrail` | `if min_cluster_size <= 1: min_cluster_size = max(2, int(min_cluster_size * n_samples))` | R | site 3, same reduction, on the trailing scaled amount. (When defaulted from a reduced `ms ≥ 2`, the guard is false and neither `mcs` nor `scaledTrail` is consumed — matches Python, where the defaulted value `≥ 2` skips the branch and no product is formed.) |
| 5 | `return some (ms, mcs)` | `(min_samples, min_cluster_size)` passed positionally into `_xi_cluster(...)` | I | return the normalized pair. `some` ↔ the routine reaching this point at all; the two `none` legs (rows 0 and 3b) are the two `_validate_size` raises. |

Every op is **R** or **I**. **No A row** — no unchanged callee's return value is
consumed. The `_validate_size` guard is not an exception to that: it returns
nothing (it raises or falls through), and its decision is modeled deeply as
`Threshold.admits` with the routines made partial (`Option`), rather than assumed
as a contract or hoisted into a precondition — it has to be, because at
optics_.py:625 the check is applied to a value the specification itself computes.
The reduction is likewise modeled deeply. `axiom_check.py` is a skip stub; the R/I legs are
mechanically refuted by `conformance_check.py` (G-CONF).

## Prepatch (the real bug)
The twins encode `max(2, scaled)` as
`if scaled ≤ 2 then .count 2 else .quantity scaled`. That is Python's `max`
faithfully: it returns whichever OPERAND is larger and preserves its type — the
literal `2` (an `int`) when the scaled amount does not exceed it, and the `float`
itself otherwise. Confirmed against the real routine in both form and magnitude at
0.5, 1.5, 1.9999, 2.0, 2.0000001, 2.4, 3.0, 3.7, 30.0 — all nine agree, including
the subtle `max(2, 2.0) → int 2`.

- `Solution_prepatch_1.lean`: `resolveMinSamples` drops the `int(...)`, so on a
  fractional input above the clamp floor it delivers the unreduced divisible
  amount — the actual site-1 bug. The carried gold proof's `rfl` step no longer
  closes (`.quantity scaled` is not the count `normCount scaled` delivers), so it
  fails G-VERIFY.
- `Solution_prepatch_2.lean`: `resolveThresholds` drops the `int(...)` at both
  sites 2+3 — the actual site-2/3 bug; the carried gold proof fails the same way.
One prepatch per independently-observable fixed behavior (the two changed
functions).
