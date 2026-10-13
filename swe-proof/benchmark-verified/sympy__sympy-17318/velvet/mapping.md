# mapping.md — sympy__sympy-17318

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d4e0231b08147337745dcf601e62de7eefe2fb2d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `sympy/simplify/sqrtdenest.py` (behavioral) and
`sympy/simplify/radsimp.py` (docstring only — see §4).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `matchAddTerms (xs : List Addend)` | the `p.is_Add` branch of `_sqrt_match(p)` — `sympy/simplify/sqrtdenest.py:140-159` | the modeled changed function: decide whether a sum decomposes as `a + b·√r` |
| `fastSplit (xs : List Addend)` *(`:|`-domain callee stub)* | `split_surds(expr)` — `sympy/simplify/radsimp.py:1061` (which calls `_split_gcd`, `radsimp.py:1103`) | unchanged community routine the fast path delegates to; PARTIAL — defined only on sums of positive-rational-square terms |
| `Addend` (`sqRat`, `sqPos`, `depth`) | one element `x` of `pargs = sorted(p.args, …)` | abstract view of a single addend: `(x**2).is_Rational`, `(x**2).is_positive`, `sqrt_depth(x)` |
| `Outcome` (`empty`, `matched`) | the function result: `[]` vs a 3-list `[a, b, r]` | whether a decomposition is produced |
| `allPosRat xs` | `all(sq.is_Rational and sq.is_positive for sq in sqargs)` — the post-patch guard (`sqrtdenest.py:159-160`) | the dispatch predicate / `fastSplit`'s domain |
| `maxDepth xs` | `nmax[0]` where `nmax = max([(sqrt_depth(x), x, i) …])` — `sqrtdenest.py:166-167` | the maximal `sqrt_depth` over the addends; `== 0 ⇒ res = []` (`sqrtdenest.py:168-169`) |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A sum `p` (a SymPy `Add`) with
`pargs = sorted(p.args, key=default_sort_key)` is abstracted, term by term, to a
`List Addend`; the decision `_sqrt_match` makes on `p` depends on `p` ONLY
through these three per-term observations plus their aggregation.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a SymPy `Add` expression `p` | `xs : List Addend` | `p` ↔ `[mkAddend x | x ← sorted(p.args)]`; `len(pargs)` ↔ `xs.length` |
| one addend `x` of `p` | one `Addend` | `a.sqRat ↔ bool((x**2).is_Rational)`, `a.sqPos ↔ ((x**2).is_positive is True)`, `a.depth ↔ sqrt_depth(x)` |
| `all((x**2).is_Rational and (x**2).is_positive …)` | `allPosRat xs = true` | conjunction over terms ↔ `xs.all (sqRat ∧ sqPos)` |
| `max(sqrt_depth(x) for x in pargs)` (`nmax[0]`) | `maxDepth xs` | Python `max` over a non-empty `pargs` ↔ `foldl Nat.max 0`; for an `Add`, `len(pargs) ≥ 2 > 0` so the fold seed `0` is dominated |
| `split_surds(p)` returns `(r, b, a)` ⇒ `_sqrt_match` returns the 3-list | `fastSplit xs = Outcome.matched` | a successful structural split ↔ `matched`; `split_surds` never returns `[]` |
| `res = []` (no decomposition) | `Outcome.empty` | the `nmax[0] == 0` branch (`sqrtdenest.py:168-169`) |
| `res = (a, b, r**2)` (general decomposition) | `Outcome.matched` | the `nmax[0] != 0` branch (`sqrtdenest.py:170+`) builds and returns a 3-list |

**`Outcome` is intentionally coarse — and that is sound.** `_sqrt_match` returns
either `[]` (length 0) or a 3-element list (`[a,b,r]`). The behavior the issue
and the F2P test pin is *which of the two* is produced — concretely
`_sqrt_match(4 + I) == []` and that no `IndexError` escapes. The exact algebraic
values of `a, b, r` on the `matched` legs are produced by UNCHANGED code (the
general matcher / `split_surds`) and are not what the fix alters; modeling them
would be over-claiming on an unchanged computation (SPEC_GUIDE §0.7). G-CONF
bridges `matched`/`empty` to "`len(result) == 0`" so the differential test still
discriminates the patched behavior exactly.

## 3. Callee provenance — `fastSplit` ↔ `split_surds` (the `:|`-domain stub)

**Callee:** `split_surds(expr)` (`sympy/simplify/radsimp.py:1061`), which calls
`_split_gcd(*surds)` (`radsimp.py:1103`). This routine is UNCHANGED by the gold
patch (the only radsimp.py edit is to its docstring — §4). It is **partial**:

```python
def _split_gcd(*a):
    g = a[0]          # radsimp.py:1106 — IndexError when `a` is empty
    ...
```

`split_surds` builds `surds = [x[1]**2 for x in coeff_muls if x[1].is_Pow]`.
When the sum has no term that is a `Pow` surd (i.e. no real `√` term — which is
exactly what happens when a term's square is rational but **not positive**, e.g.
the imaginary unit `I` with `I**2 == -1`), `surds` is empty and `a[0]` raises
`IndexError: tuple index out of range`. So `split_surds`'s *domain* is "the sum's
terms each have a positive-rational square"; the modeled `require allPosRat xs`
is precisely that domain. The weakest contract the dispatch needs is therefore:

> *defined only when `allPosRat xs`; on that domain it always succeeds
> (`ensures r = matched`) — it never returns `[]`.*

This is captured by the `fastSplit` `method` stub (`require allPosRat`,
`ensures matched`), discharged by `loom_solve` (sound by construction,
SPEC_GUIDE §3). It is an **A-reference** domain stub: G-AX (`axiom_check.py`)
runs the real `split_surds` and asserts (a) on every `allPosRat` sum it returns a
3-tuple (never raises, never length-0), and (b) on a non-`allPosRat` sum lacking
surds it raises `IndexError` — confirming the domain claim is neither too wide
(unsound) nor too narrow.

### 3.1 Flag / context dependencies
None. `split_surds` takes one positional `expr`; `_sqrt_match` calls it with no
flags. `default_sort_key` ordering of `pargs` does not affect `allPosRat`
(a conjunction) or `maxDepth` (a max), so the abstraction is order-insensitive.

### 3.2 The general regime (`allPosRat = false`)
Total, no callee. `_sqrt_match` computes `v = [(sqrt_depth(x), x, i) …]`,
`nmax = max(v, …)`; if `nmax[0] == 0` it sets `res = []` (→ `empty`), else it
builds a decomposition (→ `matched`). `maxDepth xs` models `nmax[0]`. For an
`Add`, `pargs` has ≥ 2 elements, so `max` is over a non-empty list and the
`foldl … 0` seed never spuriously wins (every real depth is `≥ 0`; the issue's
discriminating case `4 + I` has all depths `0`, giving `maxDepth = 0 → empty`).

## 4. The radsimp.py hunks are docstring-only (no behavior, no second site)

The gold patch's two `radsimp.py` hunks edit ONLY docstrings:
`rad_rationalize` ("…squares are rationals" → "…positive rationals.") and
`split_surds` ("…rationals" → "Split …positive rationals…"). They change no code
— they document the very precondition this bundle models (`fastSplit`'s domain).
They are behaviorally inert: not a modeled function, not a second failing
prepatch, and excluded from G-CONF/G-AX. Recorded here for refinement
completeness; the only behavioral edit is the `_sqrt_match` guard.

## 5. G-CONF fuzz seed
Pinned seed: **17318** (used by `conformance_check.py`).
