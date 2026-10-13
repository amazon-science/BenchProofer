# mapping.md — scikit-learn__scikit-learn-14496

## Instance
- repo: `scikit-learn/scikit-learn`
- base_commit: `d49a6f13af2f22228d430ac64ac2b518937800d0`
- modeled file: `sklearn/cluster/optics_.py`
- F2P test: `sklearn/cluster/tests/test_optics.py::test_extract_xi`
- pinned G-CONF fuzz seed: **14496**

## What the fix does (issue + gold patch)
A neighborhood-size threshold may be supplied either as an absolute count (an
integer `> 1`) or as a fraction of the number of samples (a value in `(0, 1]`).
When supplied as a fraction it must be converted to an absolute integer count,
rounded up to be at least 2:

```python
if min_samples <= 1:
    min_samples = max(2, min_samples * n_samples)        # PRE-PATCH: still a float
    min_samples = max(2, int(min_samples * n_samples))   # POST-PATCH: integer
```

Pre-patch, `min_samples * n_samples` is a float, so `max(2, float)` returns a
**non-integral float** (e.g. `max(2, 0.1*30) == 3.0`). Downstream consumers
require an integer count (`NearestNeighbors(n_neighbors=...)` raises
`TypeError: n_neighbors does not take <class 'numpy.float64'> value` on a float);
the fix wraps the product in `int(...)` (truncation toward zero; for the
non-negative product this is `floor`). The same defect is fixed at **three
sites**:

| site | function | line @ base | edit |
|---|---|---|---|
| 1 | `compute_optics_graph` | optics_.py:440 | `min_samples = max(2, int(min_samples * n_samples))` |
| 2 | `cluster_optics_xi` | optics_.py:622 | `min_samples = max(2, int(min_samples * n_samples))` |
| 3 | `cluster_optics_xi` | optics_.py:627 | `min_cluster_size = max(2, int(min_cluster_size * n_samples))` |

`_xi_cluster` (optics_.py:753+) only had docstring edits — no behavior change.

The full preparation in `cluster_optics_xi` also defaults the second threshold to
the (already-normalized) first when it is unset:

```python
n_samples = len(reachability)
_validate_size(min_samples, n_samples, 'min_samples')
if min_samples <= 1:
    min_samples = max(2, int(min_samples * n_samples))
if min_cluster_size is None:
    min_cluster_size = min_samples           # the normalized min_samples (>= 2, so skips below)
_validate_size(min_cluster_size, n_samples, 'min_cluster_size')
if min_cluster_size <= 1:
    min_cluster_size = max(2, int(min_cluster_size * n_samples))
```

## Modeled functions
Two triples, one per changed function (callees-before-callers ordering is moot —
neither calls the other):

1. **`resolveMinSamples`** — the single normalization in `compute_optics_graph`
   (site 1). Input: a threshold (fraction-or-count) and the sample count; output:
   the integer count that flows to `NearestNeighbors(n_neighbors=...)`.
2. **`resolveThresholds`** — `cluster_optics_xi`'s full two-threshold
   preparation (sites 2 + 3 plus the unset-default step). Input: the first
   threshold, an optional second threshold, the sample count; output: the pair of
   integer counts that flow into the clustering routine.

Both reduce the shared per-site reduction to the pure helper `normCount`
(post-patch / fixed form, with the `int(...)` truncation as `Int.floor`).

### Model boundary — where the scaling lives
The patch changed the *reduction* `max(2, ·)` → `max(2, int(·))`; it did NOT
change the multiply `min_samples * n_samples`. That multiply is therefore OUTSIDE
the modeled behavior, and the amount it produces enters the model as an input
(`scaled`, and `scaledLead` / `scaledTrail` for the pair). This is a faithfulness
requirement, not a stylistic choice: the repo's multiply yields the nearest
representable double, and re-deriving the product inside the model as an exact
rational `x * (n : ℚ)` and flooring THAT computes a different function. The two
disagree wherever the representable product lands on the far side of an integer
from the exact one — e.g. `min_samples = 0.6`, `n_samples = 5`, where the double
product is exactly `3.0` (so the repo delivers `n_neighbors = 3`) while the exact
rational product `3/5 * 5` computed from the decimal-shortest reading of `0.6`
sits below 3 and would floor to 2. Measured members of that class:
`0.6 @ 5`, `0.3 @ 10`, `0.7 @ 10`, `0.9 @ 10`, `8/9 @ 9`, `3/7 @ 7`. With the
multiply outside the boundary and the scaled amount carried exactly, the model
agrees with the repo on all of them.

On the keep-unchanged branch (`1 < min_samples`) the repo forms no scaled amount
at all; the specification's result there is pinned to the threshold independently
of the `scaled` binder, which is simply unconsumed.

## Lean ↔ Python type bijection (G-CONF + G-AX use this)
| Python | Lean | note |
|---|---|---|
| `min_samples` / `min_cluster_size` value | `Threshold` = `count (k : ℤ)` \| `quantity (q : ℚ)` | a threshold as the routine carries it: an integer count, or a divisible amount (a "fraction `≤ 1`", or any `float`). Two-form rather than a bare `ℚ` because the downstream consumer discriminates on the value's TYPE, not only its magnitude — see "Why the carrier is two-form" below. The divisible arm is exact `ℚ` (a double is a dyadic rational, so this is lossless) because the kernel's `Float` order is opaque to tactics (DECISIONS.md). `Threshold.amount : Threshold → ℚ` is the magnitude, disregarding form. |
| `n_samples` (`int`, `>= 1`) | `Nat` | `X.shape[0]` / `len(reachability)`. |
| `min_cluster_size=None` (unset) | `Option Threshold = none` | the unset case that defaults to the normalized first threshold, in whatever form that carries. |
| `min_samples * n_samples` (the scaled amount, an unchanged upstream step) | `scaled : ℚ` (`scaledLead` / `scaledTrail`) | NOT recomputed in Lean. The repo's own float product is passed in; every value it can take is an exact rational (a double is a dyadic rational), so the `ℚ` binder carries it losslessly. See "Model boundary" above for why re-deriving it as `x * (n:ℚ)` would be unfaithful. |
| `max(2, int(scaled))` | `normCount scaled = .count (max 2 ⌊scaled⌋)` | the reduction the patch introduced. `int(·)` on the non-negative scaled amount is truncation = `Int.floor` (measured: 0 divergences over the modeled domain); `max 2 ·` over `ℤ`. Delivered in **count** form, matching that `int(...)` returns a Python `int` and not a whole-valued float. |
| `max(2, scaled)` (PRE-patch) | `if scaled ≤ 2 then .count 2 else .quantity scaled` | Python's `max` returns whichever OPERAND is larger, preserving its type: the literal `2` (an `int`) when the scaled amount does not exceed it, else the `float` itself. Confirmed against the real routine in both form and magnitude at 0.5, 1.5, 1.9999, 2.0, 2.0000001, 2.4, 3.0, 3.7, 30.0 — all nine agree, including `max(2, 2.0) → int 2`. This is what the pre-patch twins encode. |
| normalized count (output) | `Threshold` | the reduction's outcome, form included. |

### Why the carrier is two-form (and not just `ℚ`)
The patch's observable delta at each site has **two** components, and only one of
them is a magnitude:

| | pre-patch | post-patch |
|---|---|---|
| magnitude | `3.0` | `3` |
| representation | `float` — **rejected** downstream | `int` — **accepted** |

The consumer is a type check, not a range check:
`NearestNeighbors.__init__`'s validation at `sklearn/neighbors/base.py:275` reads
`if not isinstance(self.n_neighbors, numbers.Integral): raise TypeError(...)`. It
rejects `3.0` and admits `3`, and those two are the same *number*. So a carrier
that recorded only the magnitude would model the accepted/rejected distinction
away entirely, and the reduction's whole point would be unobservable.

That is not a conjecture; it was measured. With a magnitude-only `ℚ` carrier, an
implementation reducing as `normCount scaled / 1` — magnitude-identical, but a
true division whose Python counterpart yields a `float` — satisfied every clause,
**including** the strongest magnitude-level integrality claim available
(`∃ k : ℤ, result = (k : ℚ)`, which builds with exit 0 against it), because a
whole rational and an integer count are literally the same object there. Its
faithful patch does not resolve the instance: `test_extract_xi` still fails on the
downstream `TypeError`. Hence the defect was the *carrier*, not a missing clause,
and no postcondition over `ℚ` could have closed it.

`Threshold`'s two constructors make the form decidable (it derives
`DecidableEq`), so the specification's clauses — which are equalities of
*thresholds*, not of amounts — pin form and magnitude together. `Threshold.amount`
remains available for the branch guards, which genuinely do test only the
magnitude (`if min_samples <= 1`), so the guards are not accidentally strengthened
into form tests.

Faithfulness of the new clause, per branch:
- **Reduce branch** (amount `≤ 1`): `max(2, int(x*n))` is `max` of two Python
  `int`s, so it returns an `int` on every admissible input — the clause "the
  result is in count form" is TRUE of the real patched function unconditionally.
- **Keep branch** (amount `> 1`): Python's assignment is identity, so the
  threshold's form is preserved exactly. Note this is *not* narrowed to
  count-form inputs: `_validate_size` admits a whole-valued float above one
  (measured: `3.0` passes, `2.5` and `7.5` raise), so the keep-branch clause is
  stated as `result = minSamples` — an identity, true of the real function on the
  float and integer cases alike — rather than as a claim that the result is a
  count.

## Callee provenance + flag deps
- `_validate_size(size, n_samples, name)` (optics_.py:280-290) — pure
  **validator**: raises `ValueError` unless `size > 0` and (`size == int(size)`
  or `size <= 1`) and `size <= n_samples`. It does NOT transform the value (in
  particular it does not change which form carries it); it only decides whether
  the routine proceeds at all. That decision is modeled **deeply**, as
  `Threshold.admits`, and the modeled routines are correspondingly **partial**:
  their result type is `Option`, and `none` is the refusal. It is modeled rather
  than assumed as a contract because in the pair routine the second call
  (optics_.py:625) is applied to a value this specification itself computes — the
  defaulted trailing threshold — so no precondition on the *arguments* can
  express it. Consequently `correct_*` carries **no** preconditions: the modeled
  routines are total over the argument types, and the attested domain includes
  every threshold the validator refuses.
  Correspondence: `size > 0` ↔ `0 < t.amount`; `size == int(size) or size <= 1` ↔
  `t.amount.den = 1 ∨ t.amount ≤ 1`; `size <= n_samples` ↔
  `t.amount ≤ (populationSize : ℚ)`. Both call sites are covered — optics_.py:438
  and :620 for the leading threshold, :625 for the trailing one — and the guard
  is a MAGNITUDE test on both sides, so a whole-valued float above one (`3.0`)
  passes and a fraction above one (`2.5`) raises. No `opaque`/`axiom` needed:
  there is no unchanged callee whose return VALUE the spec consumes.
- No flag-dependent callees.

## Axioms
None consumed; no A-reference. The normalization is modeled deeply (R/I only),
so `axiom_check.py` is a skip stub and G-CONF carries the soundness load.

## G-CONF observables
- `resolveMinSamples`: monkeypatch `sklearn.cluster.optics_.NearestNeighbors` to
  capture the `n_neighbors` it is constructed with (= the reduced
  `min_samples`) and abort before the expensive fit. Drive the real
  `compute_optics_graph`. The shadow takes the scaled amount from the identical
  float multiply the repo performs (`scale(x, n)`), mirroring the model boundary;
  it never re-derives the product in other arithmetic.
- `resolveThresholds`: monkeypatch `sklearn.cluster.optics_._xi_cluster` to
  capture its `min_samples` and `min_cluster_size` positional args, abort. Drive
  the real `cluster_optics_xi`.
Fuzz fractions in `(0,1]`, integer counts in `[2, n]`, and `n` over a small set;
`min_cluster_size ∈ {None} ∪ values`. Seed 14496, ≥10⁵ inputs total. A uniform
fuzz alone is blind to the boundary-straddling class above (0 divergences in 4000
uniform draws for BOTH a faithful and an unfaithful shadow), so both lanes
additionally enumerate the straddling pairs explicitly.
