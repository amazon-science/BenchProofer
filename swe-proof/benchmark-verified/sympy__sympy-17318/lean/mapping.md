# mapping.md — sympy__sympy-17318

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`d4e0231b08147337745dcf601e62de7eefe2fb2d`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_decompose` / `problem_spec_decompose` / `correct_decompose` | the `is_Add` branch of `_sqrt_match` (decomposing an additive expression into the nested-square-root normal form `[a, b, r]`) | `sympy/simplify/sqrtdenest.py:157-162` |
| `allSquarePosRat` (modeled guard) | `all(sq.is_Rational and sq.is_positive for sq in sqargs)` where `sqargs = [x**2 for x in pargs]` (POST-patch); `all((x**2).is_Rational for x in pargs)` (PRE-patch) | `sympy/simplify/sqrtdenest.py:159` |
| `fastDecomp` (opaque callee) | `split_surds(p)` | `sympy/simplify/radsimp.py:1062` (called from `sqrtdenest.py:160`) |
| `depthMatch` (opaque callee) | the depth-based matcher in the rest of the `is_Add` branch (`pargs.pop`, the `v`/`nmax` selection, building `a, b, r**2`) and the `[]` no-match result | `sympy/simplify/sqrtdenest.py:163-208` |
| `Addend` (carrier) | one element `x` of `pargs = sorted(p.args, …)`; its `sq` field is the value of `x**2` when rational, else `none` | `sympy/simplify/sqrtdenest.py:158` |
| `NestedForm` (carrier) | the matcher's normal form, the `list(res)` of `[a, b, r]` (or `[]`) | `sympy/simplify/sqrtdenest.py:162,215` |

## The observable behavior

`_sqrt_match(p)` returns `[a, b, r]` such that `p = a + b*sqrt(r)` with `sqrt(r)`
of maximal depth, or `[]` when there is no nontrivial match. The gold patch
changes only the decision at the top of the `p.is_Add` branch — the guard that
selects a specialized fast decomposition `split_surds(p)`.

At `base_commit` (`sqrtdenest.py:159`):

```python
pargs = sorted(p.args, key=default_sort_key)
if all((x**2).is_Rational for x in pargs):
    r, b, a = split_surds(p)
    res = a, b, r
    return list(res)
# ... otherwise the general depth-based matcher runs ...
```

`split_surds` is the unchanged callee. It is only applicable when every addend's
square is a POSITIVE rational (it sorts the surds — the squared bases — and runs
`_split_gcd(*surds)`). When some addend square is a rational but NOT positive
(e.g. an addend `c*I` whose square `c**2 * I**2 = -c**2` is a *negative* rational,
or `I` itself with `I**2 == -1`), the guard `(x**2).is_Rational` is still True
(`-1` is Rational), so the old code calls `split_surds`. But for such an
expression `surds` is empty (the addends are not `Pow`s with the structure
`split_surds` expects), so `_split_gcd()` is called with no arguments and
`g = a[0]` raises `IndexError: tuple index out of range`. The exception escapes
`_sqrt_match` and `sqrtdenest`, so `sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2)`
crashes.

The gold patch strengthens the guard to also require each square be POSITIVE:

```python
sqargs = [x**2 for x in pargs]
if all(sq.is_Rational and sq.is_positive for sq in sqargs):
    ...
```

Now an additive expression with a non-positive rational square no longer takes
the fast `split_surds` branch; control falls through to the general depth-based
matcher, which for such an expression returns `[]` (no nontrivial denesting), so
`sqrtdenest` returns the expression unchanged instead of raising. This is the
directly observable consequence the F2P test `test_issue_12420` pins:
`_sqrt_match(4 + I) == []` and `sqrtdenest(e) == e` for non-denestable `e`.

## Type bijection (G-CONF / G-AX use this)

| Lean | Python | note |
|---|---|---|
| `Addend` (`sq : Option Rat`, `tag : Nat`) | one addend `x` of `pargs`; `sq = some q` iff `(x**2).is_Rational` with rational value `q` (`Rational(x**2)`), else `none` (`(x**2).is_Rational` is False); `tag` distinguishes addends with equal square | the spec observes an addend only through `x**2`'s rationality + sign |
| `squarePosRat a` : `Bool` | `sq.is_Rational and sq.is_positive` for `sq = x**2` | `some q ↦ (0 < q)`; `none ↦ False` (`is_Rational` False ⇒ guard False). `sq.is_positive` for a rational `sq` is exactly `0 < q` |
| `allSquarePosRat p` : `Bool` | `all(sq.is_Rational and sq.is_positive for sq in sqargs)` | the POST-patch guard; G-CONF differential-tests this against the real predicate over sympy objects |
| `fastDecomp p : Except Unit NestedForm` | `split_surds(p)` then `res = a,b,r; return list(res)` — `Except.ok f` = the produced `[a,b,r]`; `Except.error ()` = the `IndexError` it raises when inapplicable | unchanged callee; abstract A-reference (no result property consumed) |
| `depthMatch p : NestedForm` | the depth-based matcher (lines 163-208) / the `[]` no-match | unchanged; abstract A-reference. Always produces a form (never raises on this path) |
| result `Except Unit NestedForm` | the function's outcome: `Except.ok form` = a returned `[a,b,r]`/`[]`; `Except.error ()` = `IndexError` escaping | post-patch never yields `error` on the modeled branch; base_commit yields `error` when squares are rational but some is non-positive |

Note: the matcher's `[]` ("no match") and a structural `[a,b,r]` are both
`NestedForm` values produced by `depthMatch`; the spec does not pin which one
(that is internal to the unchanged matcher) — it pins only that on the
non-positive branch the result is `Except.ok (depthMatch p)` rather than the fast
routine's (possibly escaping) result.

## Callee provenance + flag deps

- `fastDecomp` ↔ `split_surds(p)` (`sympy/simplify/radsimp.py:1062`). Abstract
  A-reference — no contract on its result is consumed by the proof. Its
  applicability precondition (every addend square a positive rational) is exactly
  the guard the patch installs; outside that precondition it raises `IndexError`
  (modeled as `Except.error ()`), which the post-patch control flow never reaches
  on this branch. No flag dependency.
- `depthMatch` ↔ the depth-based matcher in the rest of the `is_Add` branch.
  Abstract A-reference — the unchanged routine that produces the result on the
  non-fast branch. No flag dependency.

## G-CONF fuzz seed

conf_skip = **false**: the modeled guard `allSquarePosRat` (Python
`all(sq.is_Rational and sq.is_positive …)`) is genuine R-content — the decision
the patch changes. `conformance_check.py` differential-tests the shadow of
`allSquarePosRat` (and the branch selection it drives) against the REAL patched
predicate executed over sympy objects, over a boundary catalogue (incl. the
issue's `4 + I` shape, where `I**2 == -1` is rational but negative) plus ≥1e5
randomized draws. Pinned seed **17318**. The two opaque callees (`fastDecomp`,
`depthMatch`) are left abstract in the shadow (the conformance check compares
WHICH branch is selected, the observable the patch changes — not the callees'
internal output).
