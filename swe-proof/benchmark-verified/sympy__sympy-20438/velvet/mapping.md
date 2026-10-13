# mapping.md — sympy__sympy-20438

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 33b47e4bd60e2302e42616141e76285038b724d6`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo files under change:
`sympy/sets/handlers/issubset.py`, `sympy/sets/handlers/comparison.py`,
`sympy/core/relational.py`.

`spec_provenance: cold` — the spec was derived only from `problem_statement`,
the gold `patch`, and the repo source at `base_commit`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `everyElementMember (memberships : List (Option Bool))` | `is_subset_sets(a_ps, b_fs)` — new `@dispatch(ProductSet, FiniteSet)` rule, `sympy/sets/handlers/issubset.py:136-138` (post-patch) | modeled changed behavior #1: a finite product is contained in a finite collection iff every element is, three-valued |
| `setsCoincide (subAB subBA : Option Bool)` | `_eval_is_eq(lhs, rhs)` — `@dispatch(Set, Set)`, `sympy/sets/handlers/comparison.py:57-59` (body changed) | modeled changed behavior #2: two sets coincide iff each is contained in the other (three-valued) |
| `guardedSimplify (bothExpr : Bool) (r normal : Int)` | `_eval_simplify` guard — `sympy/core/relational.py:303` (`Relational`) and `:558` (`Equality`); the two added `if not isinstance(...Expr...): return ...` guards | modeled changed behavior #3 (one model, two identical sites): when the operands are not both expressions, return the relational unchanged instead of forming their difference |
| `tand2`, `triAll` *(pure, deep model — A-reference)* | `fuzzy_and` — `sympy/core/logic.py:115` (unchanged) | three-valued conjunction; deeply modeled, validated `triAll == fuzzy_and` by axiom_check.py (G-AX), NOT a consumed axiom |

The pre-patch repo facts the change overturns (refinement audit only, NOT in the
consumer spec view): there was **no** `(ProductSet, FiniteSet)` subset rule, so
`is_subset_sets` fell through to the generic `(Set, Set)` rule returning `None`
(`issubset.py:11-13`); `_eval_is_eq(Set, Set)` returned `None`
(`comparison.py:58-59`); and `_eval_simplify` formed `lhs - rhs` unconditionally
(`relational.py:307`), which raised `AttributeError` on non-`Expr` operands.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| three-valued logic value (`True` / `False` / `None`) returned by `fuzzy_*`, `contains`, `is_subset`, `_eval_is_eq` | `Option Bool` | `True ↔ some true`, `False ↔ some false`, `None ↔ none`. Total, exact. |
| `fuzzy_and(iterable)` over the per-element membership values | `triAll : List (Option Bool) → Option Bool` | the list is the membership values in iteration order; `fuzzy_and` is order-insensitive in result (False dominates, then None), so any order maps to the same `Option Bool` |
| `tfn[v]` (`sympy/sets/sets.py:31`) — maps `True→S.true`, `False→S.false`, else `None` | identity on `Option Bool` | `tfn` is the identity on the three-valued domain once `S.true/S.false/None` are themselves modeled as `some true / some false / none`; omitted as an R-identity |
| `b_fs.contains(x)` for `x` an element of the product set | an entry of the `memberships : List (Option Bool)` input | reference callee (unchanged); G-CONF computes the real `contains` on the real elements to build the input |
| `lhs.is_subset(rhs)`, `rhs.is_subset(lhs)` | `subAB`, `subBA : Option Bool` inputs | reference callees (unchanged at this call site); G-CONF computes the real `is_subset` to build the inputs |
| a relational object (`Eq(...)`, `Lt(...)`, ...) — opaque identity in the changed branch | `Int` token (`r`, `normal`) | the changed branch returns the relational **unchanged**; only its identity is observed, so an opaque token suffices. `normal` = the result of the unchanged general simplification path (`super()._eval_simplify` / the `Expr`-difference path), a reference callee; G-CONF supplies the real value. |
| `isinstance(lhs, Expr) and isinstance(rhs, Expr)` | `bothExpr : Bool` | the run-time type predicate the guard tests; G-CONF supplies the real value |

## 3. Callee provenance

### 3.1 `fuzzyAnd` deep model ↔ `fuzzy_and` (A-reference)
**Callee:** `sympy.core.logic.fuzzy_and` (unchanged by the patch). Source at
`base_commit` (`sympy/core/logic.py:115-148`):

```python
def fuzzy_and(args):
    rv = True
    for ai in args:
        ai = fuzzy_bool(ai)
        if ai is False:
            return False
        if rv:            # stops updating once a None is trapped
            rv = ai
    return rv
```

Result semantics (order-insensitive): any argument `False` ⇒ `False`; else any
argument `None` ⇒ `None`; else `True`. Modeled deeply in the `pure` region by
the binary reducer `tand2` and the front-recursive fold `triAll` (identity
`some true`). There is **no consumed `fuzzy_and` axiom**; the equality
`triAll == fuzzy_and` is validated by axiom_check.py (G-AX) over fuzzed lists
of `{True, False, None}` (including empty, all-True, single-False, single-None,
mixed) at every length up to 8, and the 2-argument case `tand2` separately.

`fuzzy_bool` (applied inside `fuzzy_and` to each arg) is the identity on
genuine `True/False/None`; the inputs we feed are already three-valued, so the
bridge is exact.

### 3.2 Reference callees feeding the inputs (G-CONF bridge)
- `contains` (`FiniteSet._contains` and friends) — unchanged; produces each
  `memberships` entry for behavior #1. G-CONF runs the real `contains` on the
  real `ProductSet` elements.
- `is_subset` (`Set.is_subset`) — unchanged at the `_eval_is_eq` call site;
  produces `subAB`/`subBA` for behavior #2. (Note: for the F2P case the inner
  `is_subset` itself routes through behavior #1's new rule — G-CONF runs the
  fully-patched repo, so this composition is exercised end to end.)
- the unchanged general simplification path (`super()._eval_simplify` and the
  `Expr`-difference branch) — produces `normal` for behavior #3's `bothExpr`
  branch. G-CONF supplies its real value.

None of these is axiomatized: each is either a reference input bridged by
G-CONF, or (for `fuzzy_and`) a deep model checked by G-AX.

## 4. G-CONF fuzz seed
Pinned **seed = 20438**, `N_FUZZ` split across the three behaviors (≥10⁵ total
comparisons). Element pool: small integers and a symbolic atom, so `ProductSet`
enumeration and `contains` stay decidable and fast. Disagreement cap = 5.
