# mapping.md — sympy__sympy-21379

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`624217179aaf8d094e6ff75b7493ad1ee47599b0`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_factorReduce` / `problem_spec_factorReduce` / `correct_factorReduce` | the common-factor extraction step inside `Mod.eval` (the `# extract gcd` block) | `sympy/core/mod.py:168-172` |
| `extractFactor` (opaque callee) | `gcd(p, q)` | `sympy/polys/polytools.py:5306` (`gcd`), called from `mod.py:169` |
| `reduceByFactor` (opaque callee) | `gcd_terms(i/G, clear=False, fraction=False)` per expression | `sympy/core/exprtools.py` (`gcd_terms`), called from `mod.py:171-172` |
| `one` (carrier value) | `S.One` / the literal `1` compared against `G` | `sympy/core/singleton.py` |
| `Expr` (carrier) | a SymPy `Expr` (`p`, `q`, the factor `G`) | `sympy/core/expr.py` |

## The observable behavior

`Mod.eval(cls, p, q)` is the single function the gold patch changes. The edited
region is the "extract gcd" block. At `base_commit`:

```python
# extract gcd; any further simplification should be done by the user
G = gcd(p, q)
if G != 1:
    p, q = [
        gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]
pwas, qwas = p, q
```

`gcd(p, q)` is the unchanged callee. For some symbolic operands (notably ones
built from a `Piecewise`) it cannot produce a common factor and raises
`PolynomialError`. At `base_commit` that exception escapes the `gcd`-extraction
block — and hence escapes `Mod.eval` and the whole `subs`/assumptions query that
triggered it. That is the reported bug: an "unexpected `PolynomialError`" surfaces
out of an ordinary `subs`.

The gold patch wraps the `gcd` call and the subsequent rewrite in `try/except
PolynomialError`: when the callee raises, the failure is **tolerated** — the
common factor is recorded as the unit `1` (`G = S.One`) and `p, q` are left
unchanged — and control continues normally. On success (no exception) the
behavior is unchanged: the extracted factor `G` is recorded, and when `G != 1`
each of `p, q` is rewritten by dividing out `G` via `gcd_terms`.

The directly observable consequence (asserted by the F2P test `test_Mod`):
`(Piecewise((x_r, y_r > x_r), (y_r, True)) / z) % 1` and
`exp(sinh(Piecewise(...) / z)).subs({1: 1.0})` no longer raise — the modulo
evaluation completes instead of propagating `PolynomialError`.

## Type bijection (G-CONF / G-AX use this)

| Lean | Python | note |
|---|---|---|
| `Expr` (carrier, `repr : String`) | a SymPy `Expr` | the carrier identity for `p`, `q`, `G`; the spec observes it only through `==` (comparing the factor against the unit) and through the two callees |
| `one : Expr` | `S.One` (the literal `1`) | the unit; the value the factor is compared against (`G != 1`) and the value the fix falls back to |
| `extractFactor p q : Except Unit Expr` | `gcd(p, q)` — `Except.ok g` = the returned factor; `Except.error ()` = `PolynomialError` raised | unchanged callee; abstract (no property consumed) — A-reference |
| `reduceByFactor i g : Expr` | `gcd_terms(i/G, clear=False, fraction=False)` | unchanged per-expression rewrite; abstract — A-reference |
| result `Except Unit (Expr × Expr × Expr)` | the outcome of the extraction block: `Except.ok (G, p, q)` = block completed, carrying the (factor, possibly-rewritten p, possibly-rewritten q) forward; `Except.error ()` = `PolynomialError` escaping | post-patch never yields `error`; base_commit yields `error` when `gcd` raises |

The `for i in (p, q)` list comprehension that applies `gcd_terms` to each of `p`
and `q` is modeled as the two per-expression rewrites `reduceByFactor p g` /
`reduceByFactor q g` guarded by `g ≠ one` (the `if G != 1` test). `pwas, qwas =
p, q` and everything after the block is unchanged by the patch and is outside the
modeled step.

## Callee provenance + flag deps

- `extractFactor` ↔ `gcd(p, q)` (`sympy/polys/polytools.py`). Abstract
  A-reference — no contract on its result is consumed by the proof. The only
  result property the model relies on is its SHAPE: it either returns a factor
  (`Except.ok g`) or signals inability by raising `PolynomialError`
  (`Except.error ()`). The trigger configuration for the raise is an operand
  derived from a `Piecewise` ("Piecewise generators do not make sense"); recorded
  here so any G-AX fuzz drives the raising configuration.
- `reduceByFactor` ↔ `gcd_terms(i/G, clear=False, fraction=False)`
  (`sympy/core/exprtools.py`). Abstract A-reference — the unchanged rewrite
  invoked only on the success branch when `G != 1`. The `clear=False,
  fraction=False` flags are recorded for G-AX-fuzz fidelity; no property of its
  result is consumed by the proof.

## G-CONF fuzz seed

conf_skip = **true**: the `implementation_factorReduce` region is all-A-tagged —
it forwards the abstract callees `extractFactor` / `reduceByFactor` and routes
between them on whether `extractFactor` signalled failure, with no R/I data
transformation to transliterate into a Python shadow. G-CONF is therefore a skip
stub (pinned seed 21379 recorded for provenance only). The routing/toleration
logic is pinned by `problem_spec_factorReduce` and discharged by
`correct_factorReduce` (verify⟹correct), and G-DIFF shows the prepatch (which
propagates the failure) violating the discriminating clause.
