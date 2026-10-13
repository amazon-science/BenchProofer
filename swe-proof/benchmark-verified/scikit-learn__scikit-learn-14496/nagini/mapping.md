# mapping.md — scikit-learn__scikit-learn-14496

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d49a6f13af2f22228d430ac64ac2b518937800d0`, states the type
abstraction, and documents the (single) deep-model reference and the call
sites it stands for.

Repo file under change: `sklearn/cluster/optics_.py`.

## 0. Model boundary (what is inside / outside the model)

The repository line under change is
`min_samples = max(2, int(min_samples * n_samples))` (gold) vs
`min_samples = max(2, min_samples * n_samples)` (pre-patch). The
**multiplication `min_samples * n_samples` is not changed by the patch**: it
executes in IEEE-754 float64 before and after, producing the same double in
both worlds. It is therefore **outside** the model boundary. The model's input
`scaled: float` is that repo-computed float64 product, taken as given; every
float64 value is an exact rational and is carried losslessly by
`--float-encoding=real`. What the model captures is exactly what the patch
changes: the clamp to a floor of two and the reduction of the (possibly
fractional) value to a whole-number count.

This boundary is faithfulness-critical: modelling the multiplication as an
*exact real* product would diverge from the repo whenever float64 rounds the
product across a whole number (e.g. `0.11165523996082272 * 1021` rounds UP to
exactly `114.0`, so the repo's `int(...)` yields `114` while the exact
rational product is strictly below `114` and its floor is `113`). Taking the
repo's double as the model input removes that divergence: model and repo see
the same number.

## 1. Symbol ↔ repo binding

| model.py symbol | repo construct (file:line @ base_commit) | role |
|---|---|---|
| `neighborhood_size(scaled)` | the fractional-`min_samples` / `min_cluster_size` conversion `min_samples = max(2, min_samples * n_samples)` guarded by `if min_samples <= 1:`, taking as input the already-computed float64 product `min_samples * n_samples` | the modeled changed computation (turn the scaled neighbourhood value into a concrete whole-number size). It occurs at **three** identical sites (see §3). |
| `scaled` (parameter) | the float64 product `min_samples * n_samples` (resp. `min_cluster_size * n_samples`) as the interpreter computed it | out-of-model upstream value, carried in losslessly (§0, §2) |
| `clamp_low(scaled)` | the call `max(2, scaled)` (the `max(2, …)` floor) | pure spec: raise the scaled value to a floor of two |
| `is_whole(v)` | the property the wrapping `int(...)` of the gold patch establishes: the size is a whole-number count of samples | pure spec: integrality predicate |

The pre-patch repo expression the change wraps (for the refinement audit):
`max(2, min_samples * n_samples)` — a possibly-fractional value, fed unchanged
into a place that requires a whole number. The gold patch wraps it as
`int(max(2, min_samples * n_samples))` (equivalently `max(2, int(...))`; see
refinement.md note D).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| the float64 product `min_samples * n_samples` (a Python/NumPy double), computed upstream of the change on the fractional branch | `scaled: float` (interpreted real, `--float-encoding=real`) | **exact injection**: every IEEE-754 double is a rational number, and `--float-encoding=real` carries it with no loss. The multiplication itself (with its float64 rounding) happens in the REPO, outside the model (§0); the model never re-multiplies. |
| the admitted range of that product | `Requires(scaled > 0.0)` | the fractional branch is reached only after `_validate_size` (§4) admits `0 < value ≤ 1` and the guard `value <= 1` holds, with `n_samples ≥ 1`; the float64 product of a positive double and a positive int is positive (never rounds to 0.0 here: the smallest admitted value 1e-9-ish times any n ≥ 1 stays normal). No upper bound and no whole-number structure of `scaled` is assumed — the spec covers every positive double the repo can produce, including products that float64 rounds to exactly a whole value (e.g. `114.0`). |
| `max(2, …)` | `clamp_low(...)` | `2` is the integer literal in the source; in the real domain the floor of two is `2.0`. `clamp_low` returns the larger of `scaled` and `2.0`. Note the repo's `max(2, x)` on a float `x` returns the int `2` or the float `x`; either way its VALUE equals `max(2.0, x)`, and the downstream `int(...)`/whole-number value is identical. |
| `int(...)` (the gold wrap) — float truncation toward zero on a non-negative value | the verified floor loop in `neighborhood_size`'s impl returning a whole `float` whose value is `floor(clamp_low(scaled))`; integrality captured by `is_whole(Result())` | for a non-negative real `v`, `int(v) == floor(v)`; the loop establishes `Result() <= v < Result()+1` and `Result()` whole, i.e. the floor. The return is carried as a `float` (an integral one) so the spec can state the float floor relation; the gold's `int(...)` produces the same whole number. |

Nagini supports neither `float(int)` nor a value-bearing `int(float)` model
(`float___int__` ensures only the result *type*; `float(int)` is unsupported).
The truncation is therefore modelled deeply by a verified loop that carries a
parallel real accumulator `acc` bridged to the integer counter `count` by the
loop invariant `acc == count` (implicit int↔float promotion, which Nagini does
accept inside assertions). The integrality of the result is witnessed by that
same counter (`is_whole(Result())` discharged by `Exists k :: Result() == k`).

## 3. The three identical change sites (one modeled function)

The gold patch makes the **same** edit — wrap `max(2, value * n_samples)` in
`int(...)` — at three sites:

1. `compute_optics_graph(...)`, `min_samples` — `optics_.py:439`
   (`if min_samples <= 1: min_samples = max(2, min_samples * n_samples)`).
2. `cluster_optics_xi(...)`, `min_samples` — `optics_.py:622`.
3. `cluster_optics_xi(...)`, `min_cluster_size` — `optics_.py:627`.

All three are byte-identical instances of the same operation
`int(max(2, x * n_samples))` with the same upstream float64 product. They are
modelled by the single function `neighborhood_size`: each site is the
*identical concrete operation* on its already-computed scaled value
(refinement.md tags every step R or I), so a single contracted function is the
faithful skeleton and a single `model_prepatch.py` (the un-reduced value) is
the differential witness for all three. The accompanying doc-string-only hunks
in the gold patch (parameter descriptions of `min_samples` /
`min_cluster_size`) are non-semantic and carry no modeled operation.

## 4. The guarding callee `_validate_size` (context, not modeled)

`_validate_size(size, n_samples, param_name)` (`optics_.py:280`) runs *before*
the `if value <= 1` branch at every site. It raises unless `size > 0` and
(`size == int(size)` or `size ≤ 1`) and `size ≤ n_samples`. Consequently, when
control reaches the conversion with `value <= 1`, the value satisfies
`0 < value ≤ 1` and the float64 product `value * n_samples` is strictly
positive — exactly the model's `Requires(scaled > 0.0)`. `_validate_size` is
unchanged by the patch, raises on out-of-range input, and gates the
precondition; it is therefore part of the model's `Requires` rather than a
callee the proof invokes, so it is **not** an axiom (no `@ContractOnly`).

## 5. Axioms

None. The only operation that the gold patch changes — wrapping the scaled,
clamped value in `int(...)` — is modelled **deeply** (the floor loop), never
axiomatized. The one supporting operation (`max(2, …)`) is spelled out as a
`@Pure` helper, not an opaque callee; the upstream multiplication is outside
the model boundary (§0) and enters only as the input value. There is thus no
consumed axiom and no `@ContractOnly`. `axiom_check.py` validates the deep
floor model == the real Python `int(max(2, scaled))` **on the shared
repo-computed float64 product** (the A-reference soundness check) over
boundary, the exact F2P inputs, the float64 round-up fixture
`0.11165523996082272 * 1021 == 114.0`, and randomized fuzz.
