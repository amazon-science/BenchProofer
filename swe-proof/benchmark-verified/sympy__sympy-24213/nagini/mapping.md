# mapping.md — sympy__sympy-24213

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e8c22f6eac7314be8d92590bfff92ced79ee03e2`, states the type
abstraction, and gives the provenance of the axiom / deep-model reference
(callee source + the exact behaviour encoded), checked by G-AX / axiom_check.py.

Repo file under change: `sympy/physics/units/unitsystem.py` (the `Add` branch of
`UnitSystem._collect_factor_and_dimension`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collect_sum_dimension(surf, red)` | the `Add` branch of `UnitSystem._collect_factor_and_dimension(self, expr)` — `sympy/physics/units/unitsystem.py:173-184` (the changed guard at `:178`) | the modeled changed function: reduce a sum's dimension, rejecting only physically inequivalent addends |
| `equivalent(surf_a, red_a, surf_b, red_b)` *(deep model — A-reference)* | `DimensionSystem.equivalent_dims(dim1, dim2)` — `sympy/physics/units/dimensions.py:428-431` | pure spec: physical equivalence of two dimensions = equality of their canonical reductions; validated `== equivalent_dims` by axiom_check.py (G-AX) |
| `reduction_of(surface)` *(axiom — A-consumed)* | `DimensionSystem.get_dimensional_dependencies(name)` — `sympy/physics/units/dimensions.py:422-426` (via `_get_dimensional_dependencies_for_name`, `:359-420`) | unchanged engine that reduces a dimension to its base-dimension dependency multiset; the proof consumes only that it is a genuine function of the dimension |
| `DimensionMismatch` | the `raise ValueError('Dimension of "{}" is {}, but it should be {}'…)` at `unitsystem.py:179-182` | the rejection the reduction signals on inequivalent addends (user-defined exception; builtin-exception `Exsures` crashes the translator) |

The pre-patch repo symbol the change removes (for the refinement audit, not
referenced from the consumer spec view): the guard `if dim != addend_dim:`
(`unitsystem.py:178`), a **structural** (surface-description) inequality of the
two `Dimension` objects.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `Dimension` object collected for an addend (whose `.name` is a `Symbol`/`Mul` symbolic expression, e.g. `velocity` or `acceleration*time`) | two `int` facets per addend: `surf[i]` (its surface-description identity) and `red[i]` (its canonical-reduction identity) | `dim_i == dim_j` (structural `==`) ↔ `surf[i] == surf[j]`; `get_dimensional_dependencies(dim_i) == get_dimensional_dependencies(dim_j)` ↔ `red[i] == red[j]` |
| the recursion's first addend `expr.args[0]` (the reference dimension `dim`) | index `0` of `surf` / `red` | the loop compares every later addend against index 0, exactly as the gold loops `for addend in expr.args[1:]` against `dim` |
| `get_dimensional_dependencies` is a function of the dimension | the standing well-formedness fact `surf[i] == surf[j] ==> red[i] == red[j]`, encoded as `red[i] == reduction_of(surf[i])` with `reduction_of` `@Pure` | a `Dimension` always reduces the same way; equal surface descriptions reduce equally. The converse fails — distinct `surf` may share `red` — and that is the discriminating case. |
| `factor += addend_factor` (the magnitude accumulation, unchanged by the patch) | omitted | the patch does not touch factor accumulation; the only changed operation is the dimension-compatibility guard. The F2P test observes solely whether a `ValueError` is raised. |
| the `Add` branch always DELIVERS a verdict: the `for addend in expr.args[1:]` loop is a bounded pass over a finite tuple that either returns `(factor, dim)` or raises `ValueError` | `Requires(MustTerminate(2))` with the loop discharging `Invariant(MustTerminate(len(surf) - i + 1))` | total correctness: the model may not diverge before returning or raising. Without this obligation an infinite-loop implementation satisfies every value postcondition vacuously while its faithful real patch hangs the hidden tests (the G-PANEL-1/G-EQ `while True` exploit). |

`str` is not used; dimensions are modelled by integer identity facets, so no
banned `str` indexing arises. Every `Forall`/`Exists` body indexing `surf`/`red`
carries an explicit in-bounds guard.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `equivalent` deep model ↔ `equivalent_dims` (A-reference)
**Callee:** `DimensionSystem.equivalent_dims` (`dimensions.py:428-431`):

```python
def equivalent_dims(self, dim1, dim2):
    deps1 = self.get_dimensional_dependencies(dim1)
    deps2 = self.get_dimensional_dependencies(dim2)
    return deps1 == deps2
```

The changed comparison is modelled **deeply** by the `@Pure` `equivalent`
(`red_a == red_b`); there is **no `equivalent_dims` axiom** the proof consumes.
The deep model is validated equal to the real callee out-of-band by
axiom_check.py: for two dimensions `d_a, d_b`,

  `equivalent_dims(d_a, d_b)  ==  (reduction(d_a) == reduction(d_b))`,

i.e. equivalence is decided purely by the canonical reductions, never by the
surface descriptions. Verified over all 729 pairs of a basis of named/base/
composite dimensions plus 4000 randomized product/quotient fuzz pairs, 0
mismatch. The discriminating witness — `velocity` vs `acceleration*time`:
distinct surface descriptions (`Dimension.__eq__` returns `False`) but identical
reductions `{length: 1, time: -1}`, so `equivalent_dims` returns `True` — is the
exact behaviour the F2P test `test_issue_24211` demands and the pre-patch
structural `!=` rejects.

### 3.2 `reduction_of` ↔ `get_dimensional_dependencies` (A-consumed)
**Callee:** `DimensionSystem.get_dimensional_dependencies` (`dimensions.py:422`),
delegating to `_get_dimensional_dependencies_for_name` (`:359-420`): it expands a
dimension's symbolic name (Symbol → base dependency, Mul → summed exponents, Pow
→ scaled exponents, …) into a dict `{base_dimension: integer_exponent}`.

The axiom encodes the **weakest** property the proof needs: the reduction is a
genuine FUNCTION of the dimension (modelled as the `@Pure` `reduction_of`, so
`red[i] == reduction_of(surf[i])` makes equal surface identities yield equal
reduction identities). It does NOT claim any exact reduction value, nor that the
engine never raises — only determinism / functionality. `equivalent_dims` (and
hence the deep model `equivalent`) consults exactly this reduction.

**Flag/domain dependencies:** the engine is consulted with its default
arguments (`mark_dimensionless=False`); the dimensions reaching the guard are
the ones the recursion collects, whose `.name` is a `Symbol`/`Mul` (never a
doubly-wrapped `Dimension`). Reductions involving a non-integer or symbolic Pow
raise `TypeError` in the real engine — out of the modeled domain; the gold and
the model agree there (both propagate the raise), so axiom_check.py skips them.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`get_dimensional_dependencies` and `equivalent_dims` (in-container, the eval
sympy) on: a basis of base dimensions (length, time, mass, current, temperature,
amount, luminosity), named dimensions (velocity, acceleration, force, energy,
momentum, frequency, area, volume, pressure, power, charge), and composites
written differently (acceleration·time, force·length, mass·acceleration,
length/time, …). It asserts (a) the reduction is deterministic and a function of
the surface description (A-consumed), (b) `equivalent_dims == reduction-equality`
on all pairs and fuzz (A-reference), (c) the issue witness `velocity ==
acceleration*time` is accepted while `velocity` vs `force` is rejected, and
(d) end-to-end the gold-collected dimension of `A1*T1 + V1` reduces equal to
`velocity`. Imports only `sympy` (the repo under test). Exit 0 iff sound.

## G-CONF (differential conformance: model vs the REAL patched repo function)

`conformance_check.py` refutes (does not prove) the refinement leg §1 claims:
that the impl region of `model.py` agrees with the real patched repo function.

**Shadow** — `collect_sum_dimension`'s impl region copied VERBATIM from
`model.py`, with only the `Invariant(...)` calls and the
`# invariants-start/-end` markers deleted, plus the `@Pure` helper `equivalent`
minus its contracts. Provenance is `direct` (the model IS Python; nothing is
transliterated or paraphrased).

**Oracle** — the real patched `UnitSystem._collect_factor_and_dimension`
(`sympy/physics/units/unitsystem.py:152`, `Add` branch `:173-184`), **called**,
not replicated: the gate applies `patch.diff` to /testbed and `PYTHONPATH`
resolves the patched module, so `SI._collect_factor_and_dimension(expr)` is
driven on a genuine `Add` of `Quantity`-valued terms and its return-vs-`ValueError`
verdict and reported dimension are the observations compared. The
`@ContractOnly` axiom `reduction_of` (§3.2) likewise calls the REAL
`DimensionSystem.get_dimensional_dependencies` (`dimensions.py:422`), so the
axiom is exercised on real values rather than assumed: `red[i] ==
reduction_of(surf[i])` is re-checked against the real engine for every input.

**Type bridge** (§2 inverted) — generation runs repo→model, so every input
satisfies the `Requires` by construction. For each addend's collected
`Dimension` `d`: `surf[i] = intern(d)` under structural `Dimension.__eq__` (the
pre-patch `dim != addend_dim` observation) and `red[i] =
intern(frozenset(get_dimensional_dependencies(d).items()))` (exactly what
`equivalent_dims` compares). Model→repo: the shadow's `red[0]` is compared with
the interned reduction of the dimension the real function reports, and
`DimensionMismatch` with `ValueError`.

**Inputs** — 100000 `Requires`-satisfying inputs: 15 boundary cases (the F2P
shape `A1*T1 + V1`, its reversal, singletons, each equivalent-but-surface-distinct
pair class, rejection at each index), the exhaustive enumeration of all
length-1/2/3 sums over a fixed 14-term catalog (14 + 196 + 2744 = 2954), then
seeded fuzz over lengths 1..6 to reach the count. Out-of-domain inputs (the
engine raising `TypeError` on a symbolic/non-integer `Pow`, §3.2) are counted
and reported, never silently dropped. **Pinned seed: `SEED = 24213`** (module
constant; same seed as the velvet/lean siblings).

**Coverage obligations** — a green run must have exercised all seven of
`loop-not-entered`, `loop-completes`, `reject-at-first-addend`,
`reject-after-accepting`, `accept-surface-distinct`, `reject-surface-distinct`,
`f2p-shape`; a miss is a hard failure, so the check cannot pass by routing
around the branch the gold patch changed.

**Negative controls run during construction** (each must and did fail):
(a) the same script against the UNPATCHED repo (pre-patch structural `!=`
guard) → 1746 disagreements, first witness the F2P shape
`cf_A1*cf_T1 + cf_V1`, `surf=[0,1] red=[0,0]`, shadow `ok` vs oracle `raise`;
(b) the shadow mutated to compare `surf` instead of `red` against the patched
oracle → 2012 disagreements, same witness inverted; (c) the catalog stripped of
its surface-distinct/reduction-equal terms → `COVERAGE MISS:
accept-surface-distinct` despite zero output disagreements.

Exit 0 iff zero disagreements; the final stdout line is a JSON report
(`checked`, `disagreements`, `seed`, `obligations`, `shadow`, `oracle`).
