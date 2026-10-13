# mapping.md — sympy__sympy-18211

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`b4f1aa3540fe68d078d76e78ba59d022dd6df39f`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_asSet` / `problem_spec_asSet` / `correct_asSet` | `Relational._eval_as_set` (the set computation of a univariate relation) | `sympy/core/relational.py:389-394` |
| `solveSet` (opaque callee) | `solve_univariate_inequality(self, x, relational=False)` | `sympy/solvers/inequalities.py:397` (called from `relational.py:393`) |
| `fallbackSet` (opaque callee) | `ConditionSet(x, self, S.Reals)` constructor | `sympy/sets/conditionset.py:21` (`S.Reals` = `sympy/sets/fancysets.py` Reals singleton) |
| `Relation` (carrier) | `self` — a univariate `Relational` instance (`Eq`/`Lt`/… with exactly one free symbol) | `sympy/core/relational.py` |
| `SetExpr` (carrier) | a SymPy `Set` (the value `_eval_as_set` returns / `as_set()` surfaces) | `sympy/sets/sets.py` |

## The observable behavior

`Relational._eval_as_set` is the single function whose behavior the gold patch
changes. At `base_commit`:

```python
def _eval_as_set(self):
    # self is univariate and periodicity(self, x) in (0, None)
    from sympy.solvers.inequalities import solve_univariate_inequality
    syms = self.free_symbols
    assert len(syms) == 1
    x = syms.pop()
    return solve_univariate_inequality(self, x, relational=False)
```

`solve_univariate_inequality(self, x, relational=False)` is the unchanged callee.
For some univariate relations it cannot produce a set and raises
`NotImplementedError` (e.g. `Eq(x*cos(x) - 3*sin(x), 0)` — a transcendental
equation it cannot solve). At `base_commit` that exception escapes
`_eval_as_set`, so `as_set()` raises `NotImplementedError`.

The gold patch wraps the call in `try/except NotImplementedError`: when the
callee raises, the failure is **tolerated** and a fallback set
`ConditionSet(x, self, S.Reals)` is returned (the symbolic set `{x | x ∈ ℝ ∧
self}`) instead of propagating the exception. On success the callee's result is
returned unchanged.

The directly observable consequence (asserted by the F2P test `test_issue_18188`):
`Eq(x*cos(x) - 3*sin(x), 0).as_set()` returns
`ConditionSet(x, Eq(x*cos(x) - 3*sin(x), 0), Reals)` rather than raising. The
PASS_TO_PASS test `test_univariate_relational_as_set` pins the success path
(solvable relations still return the callee's set unchanged).

## Type bijection (G-CONF / G-AX use this)

| Lean | Python | note |
|---|---|---|
| `Relation` (opaque carrier, `repr : String`) | a univariate `Relational` `self` | the carrier identity for the relation; the spec observes it only as the argument threaded to the two callees |
| `SetExpr` (carrier, `repr : String`) | a SymPy `Set` | the value carried out of the function; observed only through `==` |
| `solveSet self : Except Unit SetExpr` | `solve_univariate_inequality(self, x, relational=False)` — `Except.ok s` = the returned set; `Except.error ()` = `NotImplementedError` raised | unchanged callee; abstract (no property consumed) — A-reference |
| `fallbackSet self : SetExpr` | `ConditionSet(x, self, S.Reals)` | unchanged constructor newly invoked by the fix; abstract — A-reference |
| result `Except Unit SetExpr` | the function's outcome: `Except.ok set` = a set returned; `Except.error ()` = `NotImplementedError` escaping | post-patch never yields `error`; base_commit yields `error` on the unsolvable branch |

`x = self.free_symbols.pop()` (the univariate symbol extraction) is not a
separately-observable op: it is total under the function's precondition
(`len(self.free_symbols) == 1`) and is consumed only inside the two callees, so
the relation `self` alone is the carrier and `x` is folded into the opaque
callees `solveSet` / `fallbackSet` which take `self` directly.

## Callee provenance + flag deps

- `solveSet` ↔ `solve_univariate_inequality(self, x, relational=False)`. The
  `relational=False` flag is the configuration under which the callee returns a
  `Set` (not a relational expression); recorded here so any G-AX fuzz drives the
  same configuration. Abstract A-reference — no contract on its result is
  consumed by the proof.
- `fallbackSet` ↔ `ConditionSet(x, self, S.Reals)`. Abstract A-reference — the
  unchanged constructor, newly invoked on the tolerated branch.

## G-CONF fuzz seed

conf_skip = **true**: the `implementation_asSet` region is all-A-tagged — it
forwards the abstract callees `solveSet` / `fallbackSet` and routes between them
on whether `solveSet` signalled failure, with no R/I data transformation to
transliterate. G-CONF is therefore a skip stub (pinned seed 18211 recorded for
provenance only). The routing/toleration logic is pinned by `problem_spec_asSet`
and discharged by `correct_asSet` (verify⟹correct), and G-DIFF shows the
prepatch (which propagates the failure) violating the discriminating clause.
