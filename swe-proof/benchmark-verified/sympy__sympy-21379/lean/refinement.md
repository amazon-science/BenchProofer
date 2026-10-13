# refinement.md — sympy__sympy-21379

Operation correspondence between the Lean `implementation_factorReduce` skeleton
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No `axiom <callee>_prop` is declared or consumed: the two unchanged callees
(`extractFactor` ↔ `gcd`, `reduceByFactor` ↔ `gcd_terms`) enter the impl and spec
as fully abstract `opaque` values, and the proof reasons only about the control
flow that routes between them — it consumes NO property of either callee's
result. Each callee is an **A-reference** (its Lean signature stands for the real
repo callee; G-AX would validate the result-shape correspondence, but there is no
result property to soundness-check, so G-AX is a skip stub). Every impl op is
A-reference or I.

Because the impl region forwards only the abstract callees and routes on
`extractFactor`'s failure signal — there is no R/I data transformation to
transliterate into a Python shadow — **conf_skip = true** and G-CONF is a skip
stub.

## What the gold patch changes

`patch.diff` edits `Mod.eval` in `sympy/core/mod.py`. At `base_commit` the
"extract gcd" block is:

```python
# extract gcd; any further simplification should be done by the user
G = gcd(p, q)
if G != 1:
    p, q = [
        gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]
pwas, qwas = p, q
```

The patch adds an import of `PolynomialError` and wraps the block in `try/except
PolynomialError`:

```python
try:
    G = gcd(p, q)
    if G != 1:
        p, q = [gcd_terms(i/G, clear=False, fraction=False)
                for i in (p, q)]
except PolynomialError:  # issue 21373
    G = S.One
pwas, qwas = p, q
```

The OBSERVED behavior change: when `gcd(p, q)` raises `PolynomialError` (an
operand the polynomial machinery cannot handle, e.g. one built from a
`Piecewise`), the exception is no longer propagated out of `Mod.eval`; instead
the common factor is recorded as the unit `1` and `p, q` are left unchanged, and
the block completes normally. The success path is unchanged.

## `implementation_factorReduce` ↔ the `Mod.eval` extract-gcd block

| # | Lean op (`implementation_factorReduce`) | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut G : Expr := one` | the factor variable `G`, set to `S.One` on the tolerated branch (and the value compared against `1`) | A-reference / I | accumulator init; `S.One` ↦ `one`. Overwritten on the success branch. |
| 2 | `let mut p' := p` / `let mut q' := q` | `p`, `q` carried forward (rebound only inside the `if G != 1` rewrite) | I | the operands; unchanged unless the success+nontrivial-factor branch rewrites them |
| 3 | `match extractFactor p q with` | `G = gcd(p, q)` invoked inside `try` | A-reference | the unchanged callee; `Except.ok g` ↦ `gcd` returning a factor; `Except.error ()` ↦ `PolynomialError` raised inside the `try` and caught by `except` |
| 4 | `| Except.ok g => G := g` | `G = gcd(p, q)` completing normally | A-reference / R | success path: the extracted factor is recorded |
| 5 | `if g ≠ one then p' := reduceByFactor p g; q' := reduceByFactor q g` | `if G != 1: p, q = [gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]` | A-reference / R | the unchanged nontrivial-factor rewrite; `G != 1` ↦ `g ≠ one`; the per-element `gcd_terms(i/G, …)` ↦ `reduceByFactor _ g`. Unchanged by the patch. |
| 6 | `| Except.error () => G := one` | `except PolynomialError: G = S.One` | A-reference / R | **the fix**: the caught `PolynomialError` ↦ the `error ()` arm; `G = S.One` ↦ `G := one`, leaving `p', q'` at their unchanged init. This is the toleration the patch ADDS. |
| 7 | `return Except.ok (G, p', q')` | block falls through to `pwas, qwas = p, q` (i.e. the step completed and carries `(G, p, q)` forward) | R | the block always completes (never propagates the exception); `Except.ok (G, p', q')` ↦ the post-patch total behavior carrying the factor + (possibly rewritten) operands onward |

## Independently-observable behavior (G-DIFF)

`Solution_prepatch.lean` encodes the base_commit control flow: the `error ()`
arm `return Except.error ()` — the callee's `PolynomialError` propagates out
instead of being tolerated. The carried gold proof of `correct_factorReduce`
fails to close precisely on the failure branch (`extractFactor p q = Except.error
()`): the spec demands `Except.ok (one, p, q)` there, the buggy impl yields
`Except.error ()`. That is the exact FAIL_TO_PASS behavior (`test_Mod`: the
`Piecewise`-derived modulo expressions must evaluate without raising
`PolynomialError`). A single prepatch suffices — there is one independently-fixed
behavior (toleration of the `gcd` failure).
