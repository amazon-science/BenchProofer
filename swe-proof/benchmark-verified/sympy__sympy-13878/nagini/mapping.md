# mapping.md — sympy__sympy-13878

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7b127bdf71a36d85216315f80c1b54d22b060818`, states the type
abstraction, and records the provenance of the (deeply-modeled) dispatch.

Repo files involved: `sympy/stats/crv_types.py` (the families' precomputed
cumulative methods — the file the gold patch edits) and `sympy/stats/crv.py`
(the unchanged dispatch `SingleContinuousDistribution.cdf` that selects between
the precomputed closed form and the integral fallback).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line) | role |
|---|---|---|
| `cdf_result(fam, default_query, quadrature_returns, closed_form_returns)` | `SingleContinuousDistribution.cdf(self, x, **kwargs)` — `sympy/stats/crv.py:214` | the modeled dispatch: closed form when the family supplies one and the query is the default, else the integral fallback |
| `query_arrives(fam, default_query, quadrature_returns, closed_form_returns)` | the same dispatch, observed for WHETHER it hands a value back: `crv.py:216-219` (the closed-form route returns what the family's `_cdf` builds) vs `crv.py:220` (the dispatch's result IS `compute_cdf(**kwargs)(x)`) | the delivery verdict as a VALUE, per route |
| `has_closed_form(fam)` | `cdf is not None` — the test inside `cdf` (`crv.py:217-218`); supplied per-family by the `_cdf` method on each distribution class in `crv_types.py` | pure predicate: the family supplies a precomputed closed-form cumulative |
| `closed_form_for(fam, default_query)` | the branch selection in `cdf`: `if len(kwargs)==0: cdf=self._cdf(x); if cdf is not None: return cdf` (closed form) else `return self.compute_cdf(**kwargs)(x)` (integral) — `crv.py:216-220` | pure map: which result form a query produces for a family |
| `closed_form_arrives(fam, default_query, closed_form_returns)` | the closed-form route's arrival: the `_cdf` the patch adds selects among its three branches by comparing the query point against each support bound — `crv_types.py:161` (`x < a`) and `crv_types.py:162` (`x <= b`) — and returns the assembled `Piecewise` at `crv_types.py:160-163`, which the dispatch hands straight back (`crv.py:219`) | pure predicate: that route hands a value back exactly when that supplied `_cdf(x)` call itself returns. NOT the narrower proxy "the ordering admits those two comparisons": `Piecewise` assembly is a SECOND, independent thing that can end without a value, so the two predicates differ (see §2 `closed_form_returns`) and it is the call's own return the model carries |
| `query_delivers(fam, default_query, quadrature_returns, closed_form_returns)` | the per-route split of the two arrival grounds above (`crv.py:219` vs `crv.py:220`) | pure predicate: whether the query hands back a result at all |
| `closed_form_for_family(fam, closed_form_returns)` (returns `CF_ARCSIN`) | `ArcsinDistribution._cdf(self, x)` — `crv_types.py:157-163` (ADDED by the gold patch; the inverse-sine three-branch `Piecewise`) | the supplied closed-form cumulative for the inverse-sine family |
| `FAM_ARCSIN` | `ArcsinDistribution` — `crv_types.py:151` (density `1/(pi*sqrt((x-a)*(b-x)))`, `crv_types.py:154-155`) | the inverse-sine family tag |
| `FAM_OTHER` | any `SingleContinuousDistribution` subclass whose `_cdf` is the base-class `return None` (`crv.py:211-212`) | a family with no precomputed cumulative |
| `CF_ARCSIN` | the inverse-sine three-branch closed form `Piecewise((0, x<a), (2*asin(sqrt((x-a)/(b-a)))/pi, x<=b), (1, True))` — `crv_types.py:160-163` | result-form code: the closed cumulative the patch adds for the inverse-sine family |
| `CF_INTEGRAL` | the result of `compute_cdf(**kwargs)(x)` (`crv.py:196-209`), an integral of the density from the lower bound to `x` | result-form code: the integral fallback |

(`crv.py` line numbers are identical at `base_commit` and post-patch — the patch
does not touch that file. `crv_types.py` line numbers for the ADDED `_cdf` and
for anything below it are post-patch; `ArcsinDistribution` is at
`crv_types.py:150` at `base_commit`.)

The pre-patch state the change repairs (for the refinement audit, not referenced
from the consumer spec view): at `base_commit` `ArcsinDistribution` defines only
`pdf`; it has NO `_cdf`, so it inherits `SingleContinuousDistribution._cdf`
which returns `None` (`crv.py:211-212`). Hence a default `cdf(Arcsin(...))(x)`
query falls through to `compute_cdf` and integrates the density
`1/(pi*sqrt((x-a)*(b-x)))`, which does not evaluate to a finite closed form (the
issue reports an unevaluated, non-convergent `Integral(...)/pi`). The gold patch
adds the inverse-sine `_cdf`, so the default query now returns the closed form
directly.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| a continuous distribution object | `fam: int` ∈ {`FAM_ARCSIN`, `FAM_OTHER`} | classification by whether the object supplies a precomputed closed-form cumulative: `FAM_ARCSIN` = the inverse-sine family (its `_cdf` is supplied post-patch); `FAM_OTHER` = a family whose `_cdf` is the base-class `None`. The only facet of the distribution the dispatch's ROUTE CHOICE reads is `self._cdf(x) is not None` (`crv.py:217-218`). G-CONF reads it STRUCTURALLY (`type(dist)._cdf is not SingleContinuousDistribution._cdf`) so that the facet is observable even where evaluating the closed form is not admitted, and asserts the two readings agree wherever `_cdf(x)` does return. |
| the option set passed to a cumulative query (`**kwargs`) | `default_query: bool` | `default_query == (len(kwargs) == 0)`; the dispatch consults the precomputed `_cdf` only on the default query, and integrates whenever options are supplied (`crv.py:216`). |
| a symbolic cumulative result (a `Piecewise`, an `Integral`, …) | `int` result-form code ∈ {`CF_ARCSIN`, `CF_INTEGRAL`} | the result is one of two distinct forms: the inverse-sine closed form (`CF_ARCSIN`) or the integral fallback (`CF_INTEGRAL`). The exact symbolic content of `CF_ARCSIN` (the three-branch inverse-sine `Piecewise`) is validated against the real `_cdf` by axiom_check.py (G-AX), not pinned numerically inside the model. |
| whether the integrating route of THIS query hands a value back — i.e. whether `compute_cdf(**kwargs)(x)` (`crv.py:220` → `crv.py:196-209`) returns rather than raising or failing to converge | `quadrature_returns: bool` | a per-query fact about the INTEGRATING route, read by the delivery obligation and by `query_arrives`, never by the result-form clauses (which is why the 4 result-form points below are still `(fam, default_query)`). It is not derivable from `fam`/`default_query`: `(FAM_OTHER, default)` covers both a single-`Interval` support with a benign density, where `integrate` returns a value, and a `Union`/`FiniteSet` support, where `crv.py:202` raises before integrating. G-CONF observes this facet on the real callee rather than assuming it, and diffs it against `query_arrives` as an EQUALITY in both directions. |
| whether the family's SUPPLIED closed form comes back for this query — i.e. whether `type(dist)._cdf(dist, x)` (`crv_types.py:157-163`) returns rather than raising | `closed_form_returns: bool` | a per-query fact about the CLOSED-FORM route, read by the delivery obligation and by `query_arrives`, never by the result-form clauses. It is not derivable from `fam`/`default_query`: the same family, under the same default query, presents both values. It is the CALL's own return, not the narrower "both branch comparisons stand" proxy, because that route has **two** independent ways to end without a value: (i) a branch comparison the ordering refuses — a magnitude not on the order line at all (a non-real quantity, an indeterminate, an unsigned infinity) as either support bound or as the query point, raising `TypeError` at `crv_types.py:161-162`; and (ii) the `Piecewise` ASSEMBLY itself refusing even though both comparisons stood, when a folding branch condition sends `Piecewise.eval` through `c.as_set()` (`piecewise.py:184` → `boolalg.py:155` → `relational.py:239` → `solve_univariate_inequality`, `inequalities.py:627`) and the condition carries an unresolvable imaginary part, raising `ValueError`. Measured witness of (ii): `ArcsinDistribution(0, oo)` with query point `I*sr` (`sr` real) — both `I*sr < 0` and `I*sr <= oo` come back as standing relations, yet the assembly raises `ValueError: I*sr < 0 contains imaginary parts which cannot be made 0 ...`; with bounds `(0, 1)` the same query point assembles and delivers. So the proxy is a DIFFERENT predicate from the route's delivery, and delivery is what the model carries. G-CONF observes the facet on the route's OWN callee (`_cdf` called directly, not via `dist.cdf`, whose route choice and `None` test are what the diff is about) and diffs the model's per-route verdict against the real dispatch's delivery, so the facet is probed and not echoed; it additionally records the comparison proxy separately to keep the distinction visible. |
| the substitution / `Lambda` wrapping in `compute_cdf` / `SingleContinuousPSpace.compute_cdf` / public `cdf` (`crv.py:309-321,426-431`; `rv.py:726-765`) | omitted (identity on the result form) | these wrap the family's `cdf(z)` into a `Lambda(z, …)` and substitute the query point; they are unchanged and value-preserving on the result form the test observes (`cdf(X)(x)` substitutes `z -> x`). |

Nagini has no symbolic-algebra type, so distributions, option sets, and symbolic
results are modeled as discrete tags / flags / codes; the dispatch and the
family → result-form correspondence are modeled deeply (concrete control flow).

The result-form domain is therefore the 4 pairs `(fam, default_query)`, and the
DELIVERY domain is those 4 pairs crossed with the two per-query facts, split by
route: the closed-form route reads `closed_form_returns` alone, the integrating
route reads `quadrature_returns` alone.

### Delivery: what the spec claims, and why

| repo reality | model clause | justification |
|---|---|---|
| the dispatch RETURNS on the `_cdf` route exactly when the closed form it asks for comes back: `crv.py:216-219` is a `len(kwargs)` guard, a `_cdf` probe and a return, so the dispatch's delivery on this route IS that call's delivery. The added `_cdf` (`crv_types.py:157-163`) is bounded straight-line code, but it has TWO ways to end without a value — the branch comparisons `x < a` / `x <= b` (`crv_types.py:161-162`) and the `Piecewise` assembly itself (§2) — so the model carries the CALL's return rather than either one of them | `closed_form_arrives(fam, default_query, closed_form_returns)`; `Requires(Implies(closed_form_returns, MustTerminate(1)))` on `closed_form_for_family` | that route arrives exactly when the supplied closed form it asks the family for comes back. It never touches `compute_cdf`, so its arrival cannot depend on the integration (which is why `quadrature_returns` is not a parameter of `closed_form_arrives`). |
| the `compute_cdf(**kwargs)(x)` route (`crv.py:220` → `crv.py:196-209`) carries **no** delivery guarantee: it reads `self.set.start` (`crv.py:202`), which raises `AttributeError` when the support is not a single `Interval`, and calls `integrate(..., **kwargs)` (`crv.py:206`), which may raise on an admissible option (`risch=True` → `ValueError`, `heurisch=True` → `TypeError`) or run without converging (the `hangs` cases the issue lists) | `quadrature_returns` as the second arm of `query_delivers` | when the dispatch reaches `crv.py:220` its result IS `compute_cdf(**kwargs)(x)`, so it returns exactly when that returns. |
| the two routes are disjoint and neither is unconditional | `Requires(Implies(query_delivers(fam, default_query, quadrature_returns, closed_form_returns), MustTerminate(2)))` on `cdf_result` | totality, **claimed exactly where the query arrives**. Without an obligation Nagini's semantics are partial, so a diverging same-spec impl (endless loop / unbounded recursion) verifies vacuously while its real counterpart hangs `cdf(Arcsin(...))(x)` forever and resolves nothing; the decreasing measures (2 → 1) let the gold dispatch call the closed-form supplier while rejecting divergence (refinement.md A5). An UNGUARDED `MustTerminate(2)` asserts delivery on BOTH routes unconditionally, which the real callee does not give — verified in-container on the witnesses below. A guard naming only the closed-form route commits the opposite error and lets a rival hang `(FAM_OTHER, default)` queries the real callee answers (`properties.py::uniq-nonterm-quadrature-returns`); a guard treating the closed-form route as unconditional over-claims on the ordering region below. |
| the delivery verdict is itself something a caller can ask for | `query_arrives`, with `Requires(MustTerminate(1))` UNCONDITIONAL and `Ensures(Result() == query_delivers(...))` plus the two per-route equalities and the two closed-form-route edges | withholding the delivery PROMISE where the real query hands nothing back leaves nothing unpinned: the verdict is stated as a VALUE on every input, in both directions, per route to that route's own fact alone. Settling WHETHER a query arrives is bounded work on every input (the dispatch reads `len(kwargs)`, probes `_cdf`, and each route's own fact is then read directly), so no input excuses a body that never answers that question — `properties.py::uniq-arrives-nonterm-refused` is the control. |

**Verified non-delivery, both routes** (post-patch worktree, base image, gold
applied). These are inputs the model's `Requires` admits, so the obligation must
not claim delivery on them:

| real input | route | real result |
|---|---|---|
| `ContinuousDistributionHandmade(Lambda(z, 1/2), Union(Interval(0,1), Interval(3,4)))`, default query | `FAM_OTHER`, `default_query=True` → `compute_cdf` | raises `AttributeError: 'Union' object has no attribute 'start'` (`crv.py:202`) |
| `ContinuousDistributionHandmade(Lambda(z, 1), FiniteSet(0,1))`, default query | same | raises `AttributeError` (`crv.py:202`) |
| `ArcsinDistribution(0, 3).cdf(1, risch=True)` | `FAM_ARCSIN`, `default_query=False` → `compute_cdf(risch=True)` | raises `ValueError: risch=True is only allowed for indefinite integrals.` |
| `ArcsinDistribution(0, 3).cdf(1, heurisch=True)` | same | raises `TypeError` |
| `ArcsinDistribution(I, 1).cdf(x)` | `FAM_ARCSIN`, `default_query=True` → `_cdf` | raises `TypeError: Invalid comparison of complex I` (the branch comparison at `crv_types.py:161`) |
| `ArcsinDistribution(0, 2*I).cdf(x)` | same | raises `TypeError: Invalid comparison of complex 2*I` (`crv_types.py:162`) |
| `ArcsinDistribution(nan, 1).cdf(x)` | same | raises `TypeError: Invalid NaN comparison` |
| `ArcsinDistribution(zoo, 2).cdf(x)` | same | raises `TypeError` on the comparison against an unsigned infinity |
| `ArcsinDistribution(0, 1).cdf(I)` | same | raises `TypeError: Invalid comparison of complex I` — the refused magnitude is the QUERY POINT, not a bound |
| `ArcsinDistribution(0, oo).cdf(I*sr)`, `sr = Symbol('sr', real=True)` | same | raises `ValueError: I*sr < 0 contains imaginary parts which cannot be made 0 for any value of sr ...` — the SECOND refusal mode: both branch comparisons stand as relations here, and it is the `Piecewise` ASSEMBLY that ends without a value. `(-oo, oo)` with the same query point, and `(0, oo)` with `sr + I*sr`, behave the same way; `(0, 1)` with `I*sr` DELIVERS. This is why `closed_form_returns` is the `_cdf` call's own return and not the comparison proxy. |

The first four rows have `quadrature_returns` False and the last six have
`closed_form_returns` False; in each case `query_delivers` is False, so the
obligation is not claimed — and `query_arrives` states False there, as a value.
The complementary rows — where the route DOES hand a value back, so the
obligation IS claimed and `query_arrives` states True — include
`ContinuousDistributionHandmade(Lambda(z, 1), Interval(0,1))` under a default
query, an exponential density on `Interval(0, oo)` under a default query,
`ArcsinDistribution(0, 3).cdf(1, conds='none')`, and (on the closed-form route)
`ArcsinDistribution(a, b)` with real or unconstrained symbolic bounds under any
real, symbolic or signed-infinite query point — an unconstrained symbolic bound
leaves the branch conditions standing as conditions and the three-branch form
comes back. G-CONF diffs `query_arrives` against the observed delivery of the
real dispatch on all of these, as an equality, so neither an over-claim nor an
under-claim survives; its recorded run reaches 681 instantiations on which the
closed-form route hands nothing back and 8 on which the integrating route does
not, alongside 4160 that deliver.

## 3. Callees / axioms

**None consumed.** The change adds a per-family `_cdf` method and relies on the
UNCHANGED dispatch in `SingleContinuousDistribution.cdf` to select it; it calls
no library callee that Nagini cannot express and whose `Ensures` the proof
consumes. The integral fallback (`compute_cdf`, `integrate`) is an UNCHANGED
sub-result carried opaquely as the result-form code `CF_INTEGRAL` (a type
refinement, R — not an axiomatized callee whose `Ensures` the proof relies on).
There is thus no `@ContractOnly` axiom (the `axioms` region is empty) and no
A-consumed row.

**Deep-model reference (A-reference, checked by G-AX / axiom_check.py).** The
dispatch itself, the inverse-sine family's closed form, and the per-route
delivery facts are modeled DEEPLY (`cdf_result` / `closed_form_for` /
`has_closed_form` / `query_delivers` spell out every case, and
`closed_form_for_family` names the inverse-sine code). They are validated equal
to the real sympy behaviour out-of-band: `axiom_check.py`

  * asserts `has_closed_form(fam)` mirrors `dist._cdf(x) is not None` for the
    inverse-sine family and for a control family the change does not touch
    (Benini, whose `_cdf` stays the base-class `None`);
  * asserts the dispatch mirrors `closed_form_for`: a default inverse-sine query
    takes the closed-form branch (no `Integral`), an inverse-sine query WITH
    options takes the integral branch (equals the `compute_cdf` fallback,
    bypassing `_cdf`), and a no-`_cdf` family's default query equals its
    `compute_cdf` integral fallback — each identified by the dispatch FACET
    (`_cdf is None` / kwargs present), not a value-membership proxy;
  * asserts `CF_ARCSIN` names the family's TRUE cumulative: the closed form
    equals the exact three-branch inverse-sine `Piecewise` the FAIL_TO_PASS
    test (`test_arcsin`) asserts, and its derivative on the support equals the
    density;
  * asserts the per-route delivery facts name the REAL facets: the closed form
    is a three-branch expression whose first two branch conditions are
    comparisons of the query point against the lower and the upper support bound
    respectively (read off the real expression, not asserted), and the model's
    per-route delivery verdict equals the real dispatch's delivery on a table of
    concrete instantiations reaching BOTH edges of the closed-form route
    (ordinary real and symbolic bounds; a non-real, an indeterminate and an
    unsigned-infinite bound; a non-real and an indeterminate query point) and
    the option-carrying route, where the closed form is bypassed and arrival is
    the integration's business alone. The facets are observed independently of
    the dispatch (the comparisons are performed directly; the integration is
    called directly), so the check is a probe and not an echo.

It imports only `sympy` (the repository under test) and the standard library.
It models the POST-PATCH behaviour, so it must run with the gold patch applied
(apply_gold=True): at `base_commit` it correctly fails, because there the
inverse-sine family's `_cdf` is `None` and the default query returns an
unevaluated `Integral` rather than the closed form. Soundness pinned at the
post-patch repository (Python 3.6; sympy 1.1), the configuration the harness
evaluates.

## 4. Behavioural provenance of the pinned property

The issue (`problem_statement`) reports that the cumulative distribution
functions of several families are obtained by integrating the density, which for
these families does not work — e.g. `cdf(Arcsin("x", 0, 3))(1)` returns
`Integral(1/sqrt(-_x**2 + 3*_x), (_x, -oo, 1))/pi`, "which is incorrect, and
doesn't converge. The CDF is basically the arcsin function, for which the
distribution is named." The desired behaviour, stated by the issue, is that
these families supply an internal precomputed cumulative so that the query
returns the closed form instead of the failing integral.

The FAIL_TO_PASS test is exactly `test_arcsin`, which asserts

```python
cdf(X)(x) == Piecewise((0, a > x),
                       (2*asin(sqrt((-a + x)/(-a + b)))/pi, b >= x),
                       (1, True))
```

for `X = Arcsin('x', a, b)`. In the model this is the postcondition
`Implies(default_query and fam == FAM_ARCSIN, Result() == CF_ARCSIN)` together
with `Result() != CF_INTEGRAL`, and the G-AX check that `CF_ARCSIN` equals this
exact `Piecewise`. It is the clause `model_prepatch.py` violates: with the
inverse-sine family supplying no closed form, the prepatch's default query
returns `CF_INTEGRAL`, so `Result() == closed_form_for(fam, default_query)` (and
the `CF_ARCSIN` postcondition) fails for the inverse-sine default query. That
test's bounds `a`, `b` are real symbols and its query point is a symbol, so
`closed_form_returns` holds on it: the F2P cell is inside the region the delivery
obligation claims, and `query_arrives` states True there.
