# refinement.md — sympy__sympy-17318

Operation correspondence between the Lean `implementation_decompose` skeleton and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No `axiom <callee>_prop` is declared or consumed. The genuinely-changed op is the
GUARD predicate that selects between two decomposition routines; it is modeled
DEEPLY as `allSquarePosRat` (exact rational arithmetic over `Option Rat`), so it
is **R**, not axiomatized. The two routines the guard selects between
(`fastDecomp` ↔ `split_surds`, `depthMatch` ↔ the depth-based matcher) enter the
impl and spec as fully abstract `opaque` values and are **A-reference** (their
result-shape stands for the real callees; the proof consumes no property of
either). G-CONF differential-tests the R guard; G-AX is a skip stub (no consumed
callee axiom, no result-property to soundness-check).

## What the gold patch changes

`patch.diff` edits the `p.is_Add` branch of `_sqrt_match` in
`sympy/simplify/sqrtdenest.py`. At `base_commit` the guard that selects the fast
decomposition is:

```python
pargs = sorted(p.args, key=default_sort_key)
if all((x**2).is_Rational for x in pargs):
    r, b, a = split_surds(p)
    res = a, b, r
    return list(res)
```

The patch strengthens the guard to also require each square be positive:

```python
pargs = sorted(p.args, key=default_sort_key)
sqargs = [x**2 for x in pargs]
if all(sq.is_Rational and sq.is_positive for sq in sqargs):
    r, b, a = split_surds(p)
    res = a, b, r
    return list(res)
```

(The patch also rewords three docstrings in `radsimp.py`/`sqrtdenest.py`
— "rationals" → "positive rationals" — which are pure documentation with no
behavioral effect and are not modeled.)

The OBSERVED behavior change: when every addend's square is rational but at
least one is NOT positive (e.g. an imaginary addend whose square is a negative
rational), the base_commit guard still enters `split_surds`, which raises
`IndexError` (its surd list is empty, `_split_gcd()` → `a[0]`), and that
exception escapes. The patched guard rejects the fast branch for such an
expression, so the general depth-based matcher runs and yields a normal form
(`[]` = no denesting), and the caller returns the expression unchanged.

## `implementation_decompose` ↔ the `is_Add` branch of `_sqrt_match`

| # | Lean op (`implementation_decompose`) | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if allSquarePosRat p then` | `sqargs = [x**2 for x in pargs]; if all(sq.is_Rational and sq.is_positive for sq in sqargs):` | R | the changed guard. `x**2` rationality ↦ `Addend.sq : Option Rat` (`some q`/`none`); `sq.is_Rational and sq.is_positive` ↦ `squarePosRat` (`some q ↦ 0 < q`, `none ↦ false`); the `all(... )` ↦ `List.all squarePosRat`. G-CONF differential-tests this predicate. |
| 2 | `return fastDecomp p` | `r, b, a = split_surds(p); res = a, b, r; return list(res)` | A-reference | the fast branch: the unchanged `split_surds` callee produces the normal form, returned unchanged. `Except.ok f` ↦ the returned `[a,b,r]`; `Except.error ()` ↦ the `IndexError` it raises when (mis)applied. Abstract — no property consumed. |
| 3 | `return Except.ok (depthMatch p)` | the rest of the `is_Add` branch: the depth-based matcher (`v`/`nmax`/`pargs.pop`/building `a,b,r**2`) or the `[]` no-match | A-reference | the non-fast branch: the unchanged general matcher produces the result. Always `Except.ok` (never raises on this path). Abstract — no property consumed. |

Every impl op is **R** (op 1) or **A-reference** (ops 2, 3). There is no
A-consumed axiom.

## Independently-observable behavior (G-DIFF)

`Solution_prepatch.lean` encodes the base_commit guard: `p.all (fun a =>
a.sq.isSome)` — the fast branch is selected whenever every square is RATIONAL,
omitting the positivity requirement. On an additive expression with a
non-positive rational square (`allSquarePosRat p = false` but every
`a.sq.isSome`), the spec requires `result = Except.ok (depthMatch p)`, but the
prepatch impl returns `fastDecomp p` — which cannot be shown equal (it may even
be the escaping `Except.error ()`). The carried gold proof of `correct_decompose`
fails to close precisely on that discriminating clause.

That is the exact FAIL_TO_PASS behavior (`test_issue_12420`: `_sqrt_match(4 + I)
== []` and `sqrtdenest(e) == e` for non-denestable `e` with imaginary parts —
where previously `split_surds` raised `IndexError`). A single prepatch suffices:
there is one independently-fixed behavior (the guard rejecting the fast branch
for non-positive rational squares).
