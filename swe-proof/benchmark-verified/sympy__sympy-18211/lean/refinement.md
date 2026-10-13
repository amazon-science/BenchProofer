# refinement.md — sympy__sympy-18211

Operation correspondence between the Lean `implementation_asSet` skeleton and the
gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by G-AX),
**I** (identical concrete op).

No `axiom <callee>_prop` is declared or consumed: the two unchanged callees
(`solveSet`, `fallbackSet`) enter the impl and spec as fully abstract `opaque`
values, and the proof reasons only about the control flow that routes between
them — it consumes NO property of either callee's result. Each callee is an
**A-reference** (its Lean signature stands for the real repo callee; G-AX would
validate the result-shape correspondence, but there is no result property to
soundness-check, so G-AX is a skip stub). Every impl op is A-reference or I.

Because the impl region forwards only the abstract callees and routes on
`solveSet`'s failure signal — there is no R/I data transformation to
transliterate into a Python shadow — **conf_skip = true** and G-CONF is a skip
stub.

## What the gold patch changes

`patch.diff` edits `Relational._eval_as_set` in `sympy/core/relational.py`. At
`base_commit` the body is:

```python
def _eval_as_set(self):
    from sympy.solvers.inequalities import solve_univariate_inequality
    syms = self.free_symbols
    assert len(syms) == 1
    x = syms.pop()
    return solve_univariate_inequality(self, x, relational=False)
```

The patch imports `ConditionSet` and wraps the call in `try/except
NotImplementedError`:

```python
    try:
        xset = solve_univariate_inequality(self, x, relational=False)
    except NotImplementedError:
        xset = ConditionSet(x, self, S.Reals)
    return xset
```

The OBSERVED behavior change: when `solve_univariate_inequality` raises
`NotImplementedError` (an unsolvable univariate relation, e.g.
`Eq(x*cos(x) - 3*sin(x), 0)`), the exception is no longer propagated out of
`_eval_as_set`; instead the symbolic conditional set `ConditionSet(x, self,
S.Reals)` is returned. The success path is unchanged.

## `implementation_asSet` ↔ `Relational._eval_as_set`

| # | Lean op (`implementation_asSet`) | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut xset : SetExpr := fallbackSet rel` | local `xset` introduced by the patch (assigned inside the `try`/`except` arms); the unchanged `ConditionSet(x, self, S.Reals)` constructor as the loop init | A-reference | the accumulator init; `ConditionSet(x, self, S.Reals)` ↦ `fallbackSet rel` (abstract). Overwritten on both branches below. |
| 2 | `match solveSet rel with` | `solve_univariate_inequality(self, x, relational=False)` invoked inside `try` | A-reference | the unchanged callee; `relational=False` flag recorded in mapping.md. `Except.ok s` ↦ the returned set; `Except.error ()` ↦ `NotImplementedError` caught by `except` |
| 3 | `| Except.ok s => xset := s` | `xset = solve_univariate_inequality(...)` (the `try` body completing normally) | A-reference / R | success path: the routine's set is bound to `xset`. `try`-body normal completion ↦ the `ok` arm of the `match` |
| 4 | `| Except.error () => xset := fallbackSet rel` | `except NotImplementedError: xset = ConditionSet(x, self, S.Reals)` | A-reference / R | the fix: the caught `NotImplementedError` ↦ the `error ()` arm; `xset = ConditionSet(x, self, S.Reals)` ↦ `xset := fallbackSet rel`. This is the line the patch ADDS. |
| 5 | `return Except.ok xset` | `return xset` | R | `return xset` ↦ `return Except.ok xset` — the result is always a set (never the propagated exception), matching the post-patch total behavior |

`x = self.free_symbols.pop()` and the `assert len(syms) == 1` precondition are
folded into the abstract callees (which take `rel` directly): under the
function's univariate precondition the symbol extraction is total and is consumed
only inside the callees, so it is not a separately-observable skeleton op
(mapping.md).

## Independently-observable behavior (G-DIFF)

`Solution_prepatch.lean` encodes the base_commit control flow: the `error ()`
arm `return Except.error ()` — the routine's inability propagates out instead of
falling back. The carried gold proof of `correct_asSet` fails to close precisely
on the unsolvable branch (`solveSet rel = Except.error ()`): the spec demands
`Except.ok (fallbackSet rel)` there, the buggy impl yields `Except.error ()`.
That is the exact FAIL_TO_PASS behavior (`test_issue_18188`:
`Eq(x*cos(x) - 3*sin(x), 0).as_set()` must return a `ConditionSet` rather than
raising). A single prepatch suffices — there is one independently-fixed behavior
(toleration of the unsolvable branch).
