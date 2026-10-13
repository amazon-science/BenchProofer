# refinement.md — sympy__sympy-18698

Maps every op in `implementation_combineFactors` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed**, **A-reference**, **I** (identical).

The gold patch appends to `_symbolic_factor_list` (for `method == 'sqf'`):

```python
factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
           for k in set(i for _, i in factors)]
```

| Lean impl op | patch.diff counterpart | tag | note |
|---|---|---|---|
| input `factors : List (Int × Nat)` | `factors : list[(Expr, int)]` | R | polynomial factor ↦ `Int` token in the multiplicative monoid; multiplicity `int` ↦ `Nat`. The block uses factors only under `*`, so this preserves the consolidation (G-CONF drives the real polynomial product). |
| `for k in (factors.map Prod.snd).dedup` | `for k in set(i for _, i in factors)` | R | distinct multiplicities; set vs dedup'd list — order irrelevant (spec is order-independent). |
| inner `let mut prod := 1; for fk in factors do if fk.2 = k then prod := prod * fk.1` | `reduce(mul, (f for f, _ in factors if _ == k))` | R | product of same-multiplicity factors. `foldl (· * ·) 1` over the matching sublist == `reduce(mul, gen)`: the matching generator is always non-empty (every `k` comes from some pair), so the explicit `1` initializer agrees with initializer-free `reduce`. |
| `result := result ++ [(prod, k)]` | list-comprehension element `(…, k)` | I | append the consolidated `(product, multiplicity)` pair. |
| `return result` | rebound `factors` returned from the helper | I | the consolidated list (re-ordered downstream by `_sorted_factors`, which the order-independent spec accommodates). |

No op is changed-inexpressible; every op is R or I. There are no A-tagged
(axiom) ops — the consolidation is modeled deeply, so `conf_skip=false` and
G-CONF mechanically refutes the full R/I chain against the real patched
`sqf_list`. `axiom_check.py` is a skip stub (no consumed callee axiom).
