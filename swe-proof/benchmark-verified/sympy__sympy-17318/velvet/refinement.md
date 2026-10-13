# refinement.md — sympy__sympy-17318

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`matchAddTerms` `do` block, the `fastSplit` domain stub, and the pure
`allPosRat`/`maxDepth` predicates) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; state the bijection), **A-consumed** (proof
uses the stub's `require`/`ensures`), **A-reference** (deep/stub model validated
== real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A,
or I; there is no kind-3 (changed-inexpressible) op.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs + this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviorally equal to the
gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dispatch site — `_sqrt_match`'s `is_Add` branch (`sqrtdenest.py:158-160`)

Gold hunk (the only behavioral edit):
```
-        if all((x**2).is_Rational for x in pargs):
+        sqargs = [x**2 for x in pargs]
+        if all(sq.is_Rational and sq.is_positive for sq in sqargs):
             r, b, a = split_surds(p)
```

| # | Solution.lean impl op (`matchAddTerms`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `xs : List Addend` | `pargs = sorted(p.args, …)` of the `is_Add` branch | R | SymPy `Add` ↔ `List Addend`, one element per sorted addend, each carrying `(sqRat, sqPos, depth)` (mapping.md §2). G-CONF builds `xs` from a fuzzed `Add`. |
| A2 | guard `if allPosRat xs` (`xs.all (sqRat ∧ sqPos)`) | `if all(sq.is_Rational and sq.is_positive for sq in sqargs)` | R + I | the post-patch guard, transliterated: per-term `(x**2).is_Rational ∧ (x**2).is_positive` ↔ `a.sqRat ∧ a.sqPos`, `all` ↔ `List.all`. This IS the changed predicate. |
| A3 | `fastSplit xs` (within `allPosRat`) ⇒ `matched` | `r, b, a = split_surds(p); res = a, b, r; return list(res)` | A-consumed + A-reference | `split_surds` is the unchanged partial callee; modeled by the `fastSplit` stub (`require allPosRat`, `ensures matched`). The proof CONSUMES the `require`/`ensures` (A-consumed); G-AX validates the stub against real `split_surds` (A-reference). A non-empty 3-list ↔ `matched`. mapping.md §3. |
| A4 | else: `if maxDepth xs = 0 then empty else matched` | `nmax = max(v,…); if nmax[0] == 0: res = []` else build `(a,b,r**2)` | R + I | general regime: `nmax[0]` ↔ `maxDepth xs`; `res = []` ↔ `empty`, the decomposition build ↔ `matched`. Total; no callee. mapping.md §3.2. |
| A5 | `return r` (`Outcome`) | `return list(res)` | R | `[] ↔ empty` (len 0), `[a,b,r] ↔ matched` (len 3). G-CONF bridges via `len(result) == 0`. |

Discriminating content of the change — a term whose square is rational but
**not positive** (the imaginary unit `I`, `I**2 = -1`) must NOT take the fast
path. Pre-patch the guard `all((x**2).is_Rational)` is `True` for `4 + I`
(squares `16, -1`, both rational), so `split_surds` is called and its
`_split_gcd` does `g = a[0]` on an empty surd list → `IndexError`. Post-patch the
strengthened guard is `False` (`-1` is not positive), so control falls to the
general regime; `4 + I` has `maxDepth = 0`, giving `res = []`. The
`Solution_prepatch.lean` impl uses the weak guard `xs.all sqRat` and therefore
calls `fastSplit` whose `require allPosRat xs` is undischargeable — **G-DIFF
fails on exactly that `require` goal** (the out-of-domain invocation = the bug).

## B. The radsimp.py hunks — docstring-only, no refinement step

The gold patch's two `radsimp.py` hunks change ONLY docstrings (of
`rad_rationalize` and `split_surds`), documenting that the squared terms must be
**positive** rationals — i.e. they document `fastSplit`'s domain (`allPosRat`).
No code changes, no observable behavior, hence no impl op, no R/A/I row, and no
separate failing prepatch (a prepatch must keep the spec byte-identical; there is
nothing behavioral to break here). They are excluded from G-CONF and G-AX.
mapping.md §4.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely changed — the dispatch
guard deciding whether to invoke the partial `split_surds` — is modeled
**directly** as the boolean `allPosRat` test (A2, R+I). The unchanged partial
callee `split_surds` is modeled by a `require`/`ensures` domain stub
(`fastSplit`, A3, A-consumed + A-reference), never axiomatized as the function
under spec. The general regime (A4) is concrete (I). No changed operation is
hidden behind an axiom; nothing is inexpressible.

## D. verify(Solution) ⇒ resolved

`matchAddTerms` verifies only if (i) on an `allPosRat` sum it returns `matched`
by calling `fastSplit` **inside its domain** — discharging the `require` proves
the guard is correctly strengthened (A2/A3); (ii) on a non-`allPosRat` sum with
`maxDepth = 0` it returns `empty` (A4) — the `4 + I` case the F2P test pins
(`_sqrt_match(4 + I) == []`); (iii) on a non-`allPosRat` sum with `maxDepth ≠ 0`
it returns `matched`. By R (`Add ↔ List Addend`, `len(result)==0 ↔ empty`) the
verified dispatch equals the post-patch `_sqrt_match` `is_Add` branch on the
tested inputs; by G-AX the `fastSplit` stub's domain == real `split_surds`'s
domain (it succeeds on `allPosRat`, raises off it); by G-CONF the R/I
transliteration agrees with `patch.diff`'s behavior over ≥10⁵ fuzzed sums.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: callee-domain
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
