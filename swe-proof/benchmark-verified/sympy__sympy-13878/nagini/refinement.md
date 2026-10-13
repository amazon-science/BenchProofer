# refinement.md — sympy__sympy-13878

The operation-by-operation correspondence between `model.py`'s implementation
(the `cdf_result` / `closed_form_for_family` / `query_arrives` impl regions and
the deep `has_closed_form` / `closed_form_for` / `closed_form_arrives` /
`query_delivers` predicates in the `pure` region) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed**, the proof uses the axiom's `Ensures`;
or **A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural hunk — the inverse-sine family's precomputed cumulative

The gold patch (`sympy/stats/crv_types.py`) ADDS a `_cdf` method to
`ArcsinDistribution`:

```python
    def _cdf(self, x):
        from sympy import asin
        a, b = self.a, self.b
        return Piecewise(
            (S.Zero, x < a),
            (2*asin(sqrt((x - a)/(b - a)))/pi, x <= b),
            (S.One, True))
```

The UNCHANGED dispatch `SingleContinuousDistribution.cdf` (`crv.py:214-220`)
then selects this closed form on a default query:

```python
    def cdf(self, x, **kwargs):
        if len(kwargs) == 0:
            cdf = self._cdf(x)         # now returns the inverse-sine Piecewise
            if cdf is not None:
                return cdf             # closed-form branch
        return self.compute_cdf(**kwargs)(x)   # integral branch
```

At `base_commit` `ArcsinDistribution` has no `_cdf`, so `self._cdf(x)` is the
inherited `return None` and the default query falls through to the integral
branch (the unevaluated, non-convergent `Integral` the issue reports).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | parameter `fam: int` | the distribution object whose `cdf`/`_cdf` is invoked | R | `fam` classifies the distribution by the only facet the dispatch reads — whether it supplies a precomputed closed-form cumulative (`_cdf is not None`); `FAM_ARCSIN` ↔ `ArcsinDistribution` (post-patch `_cdf` supplied), `FAM_OTHER` ↔ a family whose `_cdf` is the base-class `None` (mapping.md §2). |
| A1 | parameter `default_query: bool` | `**kwargs` of `cdf` | R | `default_query == (len(kwargs) == 0)`; the `if len(kwargs) == 0` guard at `crv.py:216` (mapping.md §2). |
| A2 | `if default_query: if has_closed_form(fam): return closed_form_for_family(fam, closed_form_returns)` | `if len(kwargs)==0: cdf = self._cdf(x); if cdf is not None: return cdf` (`crv.py:216-218`) | R + I | `has_closed_form(fam)` ↔ `self._cdf(x) is not None` (the dispatch facet); the closed-form branch returns the family's precomputed cumulative. The concrete control flow (default-query guard, then closed-form-available guard, then return the closed form) is identical; only the carrier types are refined. The patch ENABLES this branch for the inverse-sine family by supplying its `_cdf`. |
| A3 | `closed_form_for_family(FAM_ARCSIN, closed_form_returns)` returns `CF_ARCSIN` | the added `ArcsinDistribution._cdf` returns the inverse-sine three-branch `Piecewise` | A-reference | the changed operation — WHICH closed form the inverse-sine family supplies — is modeled **deeply**: `CF_ARCSIN` is the inverse-sine three-branch closed form, named concretely in the `pure`/impl regions. There is no consumed `_cdf` axiom; the proof depends on no `@ContractOnly` `Ensures`. Instead the deep model is validated **== the real `_cdf`** out-of-band: G-AX (axiom_check.py) asserts the closed form the real default query returns equals the exact `Piecewise` the test asserts and integrates to the density (mapping.md §3). |
| A4 | `return CF_INTEGRAL` (the fall-through) | `return self.compute_cdf(**kwargs)(x)` (`crv.py:220`) | R | the integral fallback is an UNCHANGED sub-result carried opaquely as `CF_INTEGRAL`; it is reached when the query carries options OR the family supplies no closed form. The proof consumes no `Ensures` about it — it is a type refinement of "the integral-branch result form", not an axiomatized callee (mapping.md §3). |
| A5 | parameter `closed_form_returns: bool` | whether the added `_cdf` (`crv_types.py:157-163`) itself comes back for this query, i.e. whether `type(dist)._cdf(dist, x)` returns rather than raising | R | the closed form is a three-branch `Piecewise` whose first two conditions compare the query point against the lower and the upper support bound; the third is the catch-all. Building it has **two** independent ways to end without a value, not one: (i) a branch comparison the ordering refuses (`TypeError` at `crv_types.py:161-162`) when either support bound or the query point is a magnitude that is not on the order line at all (a non-real quantity, an indeterminate, an unsigned infinity); and (ii) the `Piecewise` ASSEMBLY refusing although both comparisons stood, when a folding branch condition drives `Piecewise.eval` through `c.as_set()` (`piecewise.py:184` -> `boolalg.py:155` -> `relational.py:239` -> `solve_univariate_inequality`, `inequalities.py:627`) on a condition with an unresolvable imaginary part (`ValueError`). `closed_form_returns` therefore carries the CALL's own return — the single observable whose extension is the route's delivery — and NOT the narrower "both comparisons stand" proxy, which is a different predicate: measured, `ArcsinDistribution(0, oo)._cdf(I*sr)` (`sr` real) has both comparisons standing yet raises `ValueError`, while `(0, 1)._cdf(I*sr)` returns. It is True for real bounds and query point and for unconstrained symbolic ones (the conditions stand and the `Piecewise` is assembled), and False on both refusal modes above. It is a per-query fact of the same kind as `quadrature_returns`, observed on the real callee by G-CONF and G-AX rather than assumed, and it is read ONLY by the delivery clauses — the result FORM is pinned to `(fam, default_query)` alone (`properties.py::uniq-form-reads-order` is the control on that). |
| A6 | `Requires(Implies(query_delivers(fam, default_query, quadrature_returns, closed_form_returns), MustTerminate(2)))` on `cdf_result`; `Requires(Implies(closed_form_returns, MustTerminate(1)))` on `closed_form_for_family` | on the `_cdf` route the real `cdf` is a `len(kwargs)` guard, a probe and a return (`crv.py:216-219`) and the added `_cdf` is bounded straight-line code (`crv_types.py:157-163`) whose branch comparisons the ordering may refuse and whose `Piecewise` assembly may independently refuse (A5); the `compute_cdf` route (`crv.py:220`) has no delivery guarantee of its own | R | totality obligation, **claimed exactly where the query arrives**. Under Nagini's default partial-correctness semantics a same-spec impl that DIVERGES (endless loop / unbounded self-recursion) satisfies every `Ensures` vacuously and verifies, yet its faithful real counterpart hangs the cumulative query and resolves nothing — the G-PANEL-1 break this obligation closes. The strictly decreasing measures (2 for the dispatch, 1 for the supplier it calls) let the gold call chain discharge it while rejecting any diverging rival (Nagini's obligation leak check). The guard is required for FAITHFULNESS in BOTH directions, and NEITHER route delivers unconditionally. An unguarded `MustTerminate(2)` claims delivery over the whole admitted domain: on the integrating route, where `compute_cdf` reads `self.set.start` (`crv.py:202`, raises `AttributeError` for a non-`Interval` support) and calls `integrate(..., **kwargs)` (`crv.py:206`, raises on `risch=True`/`heurisch=True` and may not converge; the issue's own `hangs` cases); and on the closed-form route, where a support bound or a query point off the order line makes a branch comparison one the ordering refuses, or the assembly itself refuses, and the query ends with no value (mapping.md §2 witnesses: `ArcsinDistribution(I, 1)`, `(0, 2*I)`, `(nan, 1)`, `(zoo, 2)`, `ArcsinDistribution(0,1).cdf(I)`, and the assembly-refusal row `ArcsinDistribution(0, oo).cdf(I*sr)`). But a guard naming only the closed-form route UNDER-claims: on the integrating route the dispatch's result simply *is* `compute_cdf(**kwargs)(x)` (`crv.py:220`), so it delivers whenever that integration delivers — which for a single-`Interval` support with a benign density it does. Hence the guard is the exact PER-ROUTE SPLIT `query_delivers`: on the closed-form route it is `closed_form_returns` (the condition under which the real code returns at `crv.py:219` without reaching `crv.py:220`, given `has_closed_form(fam) ⇔ _cdf is not None` and `default_query ⇔ len(kwargs)==0`), and otherwise it is `quadrature_returns`. Each route reads its OWN fact and only its own: the closed-form route never touches `compute_cdf`, and the integrating route never evaluates the closed form's branch conditions. The model therefore claims delivery precisely where the real dispatch hands a value back — including the F2P cell (`FAM_ARCSIN`, default, real bounds and query point), where the obligation stays live and `uniq-nonterm-closedform` / `uniq-nonterm-comparable` confirm a rival hanging on that route is still refused, and including the integrating-and-returning queries, where `uniq-nonterm-quadrature-returns` confirms the same; `uniq-order-gates-all` refuses a rival that lets the closed-form route's fact gate the integrating route's obligation. `pos-control-scope-boundary` and `pos-control-cff-scope-boundary` are the sound-side controls on the two withheld regions. See mapping.md §2 for the in-container witnesses. |
| A7 | `query_arrives(fam, default_query, quadrature_returns, closed_form_returns)` with `Requires(MustTerminate(1))` UNCONDITIONAL, `Ensures(Result() == query_delivers(...))`, the two per-route equalities and the two closed-form-route edges | the same dispatch (`crv.py:214-220`) observed for WHETHER it hands a value back, rather than for which form its answer has | R | withholding the delivery PROMISE on the two regions above is a weakening only if nothing else pins them. This function removes that: the delivery verdict is handed back AS A VALUE on every input the precondition admits, in BOTH directions (an equality, so neither an over- nor an under-claim survives), pinned per route to that route's own fact ALONE, and pinned separately at the two edges of the route the F2P query travels. Settling whether a query arrives is bounded work on every input — the dispatch reads `len(kwargs)` (`crv.py:216`), probes `_cdf` (`crv.py:217`), and each route's own fact is then read directly — so the obligation is UNCONDITIONAL and no input excuses a body that never answers the question (`properties.py::uniq-arrives-nonterm-refused` is the control; `uniq-arrives-always-true`, `uniq-arrives-old-disjunction`, `uniq-arrives-swap-facts`, `uniq-arrives-order-everywhere` and `uniq-arrives-deny-quadrature` are the controls on the value). G-CONF diffs this function against the real dispatch's observed delivery as an equality on 100000 inputs, its facets probed independently of the outcome, with 681 fresh instantiations on which the closed-form route hands nothing back and 8 on which the integrating route does not. |

The discriminating content of the change — the inverse-sine family now SUPPLYING
a closed-form cumulative, so its default query yields the closed form instead of
the integral — lives in `has_closed_form(FAM_ARCSIN) == True` (model) ⇔ the added
`ArcsinDistribution._cdf` returning a non-`None` `Piecewise` (real). The
postcondition `Implies(default_query and fam == FAM_ARCSIN, Result() ==
CF_ARCSIN)` (and `Result() == closed_form_for(fam, default_query)`) pins it.
`model_prepatch.py` reproduces the pre-patch state on BOTH observables — with no
closed form supplied for any family, its `cdf_result` returns `CF_INTEGRAL` on
every default query (mirroring the inherited `_cdf` returning `None`), and its
`query_arrives` returns `quadrature_returns` on every query (with every query
integrating, whether one arrives is whether its integration comes back) — and
**fails** exactly the two postconditions those states contradict, the spec
sensing the change on both (G-DIFF):

```
model_prepatch.py:200: Postcondition of cdf_result might not hold.
Assertion (Result() == closed_form_for(fam, default_query)) might not hold.
model_prepatch.py:267: Postcondition of query_arrives might not hold.
Assertion (Result() == query_delivers(fam, default_query, quadrature_returns,
closed_form_returns)) might not hold.
```

The second failure is the delivery content of the change: post-patch, an
inverse-sine default query whose supplied closed form comes back arrives
because the closed form is supplied and handed straight back, whether or not the
integration it no longer performs would have come back.

For the issue's witness `cdf(Arcsin("x", 0, 3))(1)`: post-patch the closed-form
branch fires and returns the inverse-sine value `2*asin(sqrt(1/3))/pi`;
pre-patch the integral branch fires and returns the unevaluated, non-convergent
`Integral(1/sqrt(-_x**2 + 3*_x), (_x, -oo, 1))/pi` the issue reports.

## B. The other hunks are not separately-tested behaviours

The gold patch also adds `_cdf` methods to many other families (Dagum, Erlang,
Frechet, Gamma, GammaInverse, Kumaraswamy, Laplace, Logistic, Nakagami,
StudentT, UniformSum), tidies the `Erlang` scale (`1/l` → `S.One/l`), and adds
documentation examples. But the FAIL_TO_PASS set is **exactly** `test_arcsin` —
the only independently-tested fixed behaviour for resolution. Those other
families are exercised solely by `test_long_precomputed_cdf` (a numeric
differentiate-and-compare test that is NOT in FAIL_TO_PASS or PASS_TO_PASS), so
they are not separately modeled as fixed behaviours; they instantiate the SAME
dispatch (`has_closed_form(fam)` now true), already captured by site A. One
`model_prepatch.py` exercises the single independently-observable fixed
behaviour. The whitespace/doc hunks are behaviour-neutral.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I, plus the single **A-reference** A3 (no consumed
axiom). The operation that genuinely *changed* — the inverse-sine family
supplying its closed-form cumulative, so the unchanged dispatch returns the
closed form rather than the integral — is modeled **deeply** (the `has_closed_form`
predicate and the `closed_form_for_family` body, with `CF_ARCSIN` naming the
inverse-sine closed form). The deep model is validated == the real `_cdf`/`cdf`
by axiom_check.py / G-AX (an A-reference). The integral fallback is an UNCHANGED
opaque sub-result (R), not an axiom. The two per-query delivery facts (A5, and
`quadrature_returns`) are R carriers of observable properties of the real
callee, checked on it by G-CONF and G-AX; neither is an assumption the proof
consumes. There is no `@ContractOnly` the proof consumes (the `axioms` region is
empty).

## D. verify(model) ⇒ resolved

`cdf_result` verifies only if a default query on the inverse-sine family returns
the inverse-sine closed form (`CF_ARCSIN`, not the integral fallback) — A2/A3 —
and a query with options, or a family with no closed form, returns the integral
fallback — A4. By R (`fam ↔` the `_cdf is not None` dispatch facet,
`default_query ↔ len(kwargs)==0`, `CF_INTEGRAL ↔` the unchanged
`compute_cdf(**kwargs)(x)` result form) the verified function equals the gold
dispatch on the tested distribution/query — and it equals it in the same
*modality*: the spec claims DELIVERY of that result exactly where the gold
dispatch hands one back — on the closed-form route for those queries whose branch
supplied closed form comes back, and on the integrating route for those queries
whose integration comes back (A6) — so the gold patch itself satisfies the claim
on every input the precondition admits. Delivery is unclaimed on exactly two
regions, one per route: a query that must integrate and whose integration does
not come back, and a closed-form query whose branch comparisons the ordering
refuses. On neither is anything left unpinned: the spec still binds the result
FORM there (P1/P4/P5), matching the real callee, and `query_arrives` (A7) states
the delivery verdict itself as a VALUE there, in both directions and per route,
under an unconditional termination obligation — so a rival can neither promise
arrival where the real query hands nothing back nor withhold it where the real
query answers. By G-AX the deep model `CF_ARCSIN`
equals the real `ArcsinDistribution._cdf` — the exact `Piecewise` `test_arcsin`
asserts, integrating to the density (A-reference). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited closed form — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ) plus the A-reference's
G-AX audit; there is no consumed-axiom trust point.
