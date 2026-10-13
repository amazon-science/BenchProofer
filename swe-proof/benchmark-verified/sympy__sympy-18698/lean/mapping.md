# mapping.md — sympy__sympy-18698

## Symbol binding

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_combineFactors` / `problem_spec_combineFactors` / `correct_combineFactors` | the `method == 'sqf'` post-processing block appended to `_symbolic_factor_list` | `sympy/polys/polytools.py:5898-5955` (added block at gold-patch lines 5950-5952) |

The modeled behavior is the gold patch's new tail of `_symbolic_factor_list`:

```python
if method == 'sqf':
    factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
               for k in set(i for _, i in factors)]
```

This rebuilds the `factors` list so each *multiplicity* `k` that occurs in the
input appears exactly once, paired with the product (`reduce(mul, …)`) of all
input factors carrying that multiplicity.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `factors : list[(Expr, int)]` — a list of `(factor, multiplicity)` pairs | `List (Int × Nat)` | each polynomial factor `f` ↦ an `Int` token (a commutative-monoid representative under `*`); multiplicity `k` (a non-negative `int`) ↦ `Nat`. The post-processing block treats factors purely as elements of the multiplicative monoid (`reduce(mul, …)`), so a faithful R-refinement of "factor" to "`Int` under `*`" preserves the consolidation exactly: products of distinct integers stand in for products of distinct polynomials. |
| `set(i for _, i in factors)` | `(factors.map Prod.snd).dedup` (as a set; order irrelevant) | the distinct multiplicities |
| `reduce(mul, (f for f,_ in factors if _==k))` | `prodOf factors k` = `foldl (· * ·) 1` over the matching factors | product of same-multiplicity factors |
| result list (order then fixed by `_sorted_factors`) | `List (Int × Nat)`, contract is order-independent (`Nodup` + set-membership) | downstream `_sorted_factors` re-orders, so the spec pins the result as a set |

## Callee provenance / flag deps

- `reduce` (`functools.reduce`) and `mul` (`operator.mul`) are stdlib, modeled
  deeply as the Lean `foldl (· * ·) 1`. They are **not** consumed axioms.
- The block is gated on `method == 'sqf'`; for `method == 'factor'` it is a no-op.
  We model only the `sqf` path (the fixed behavior). G-CONF drives the real
  `sqf_list` end-to-end, which routes through this block with `method='sqf'`.
- `reduce(mul, gen)` over a *non-empty* generator never supplies an initial
  value; every multiplicity `k` in `set(...)` is witnessed by at least one
  factor, so the generator is always non-empty — matching `prodOf`'s `foldl`
  starting at `1` over a non-empty matching sublist (which equals the
  initializer-free reduce).

## G-CONF fuzz seed

`SEED = 18698` (pinned in `conformance_check.py`).
