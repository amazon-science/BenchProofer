#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13878 (nagini).

SHADOW: the impl region of model.py (`cdf_result`, `closed_form_for_family`,
`query_arrives`), copied verbatim below with the contract calls
(Requires/Ensures, MustTerminate) stripped. The @Pure helpers
`has_closed_form`, `closed_form_for`, `answers_from_closed_form`,
`closed_form_arrives` and `query_delivers` copy over as plain functions. There
is no PSeq usage and no @ContractOnly callee in this bundle (the axioms region
is empty).

ORACLE: the REAL patched repo function the model models per mapping.md /
meta.json -- `sympy.stats.crv.SingleContinuousDistribution.cdf`, the dispatch
that returns the family's precomputed closed-form cumulative on a default
(no-option) query when one is supplied, and otherwise the integral fallback
`compute_cdf(**kwargs)(x)`. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched package importable.
This script does NOT apply any patch itself.

Type bridge (mapping.md section 2):
  * `fam: int` <-> a concrete `SingleContinuousDistribution` instance,
    classified by the facet the dispatch reads: FAM_ARCSIN <-> the
    inverse-sine family (`ArcsinDistribution`, whose `_cdf` is supplied);
    FAM_OTHER <-> a family whose `_cdf` is the base-class None (realized here
    by `ContinuousDistributionHandmade` over simple genuine densities --
    monomial and uniform on a bounded interval, exponential on (0, oo) --
    whose integral fallback evaluates quickly, plus supports on which the
    fallback cannot even start).
    Read STRUCTURALLY (`type(dist)._cdf is not SingleContinuousDistribution
    ._cdf`), not by calling `_cdf(x)`: the closed form's construction can
    itself refuse (see `closed_form_returns`), so "does this family supply one"
    must be observable without evaluating it. Where `_cdf(x)` DOES return, the
    script asserts the two readings agree (`supplies == (_cdf(x) is not
    None)`), so the structural reading is checked against the dispatch's own.
  * `default_query: bool` <-> `len(kwargs) == 0`; the non-default queries
    pass an explicit integration option (`conds=...`, `risch=...`,
    `heurisch=...`), which the dispatch forwards to the fallback.
  * `quadrature_returns: bool` <-> whether the integrating route of THIS
    query hands a value back, i.e. whether `dist.compute_cdf(**kwargs)(x)`
    returns rather than raising. Observed, never assumed; consulted only on
    queries that integrate (on the closed-form route the dispatch never
    reaches it, and the fuzzer then feeds BOTH values).
  * `closed_form_returns: bool` <-> whether the family's SUPPLIED closed form
    comes back for this query point, i.e. whether `_cdf(x)` returns rather
    than raising. Observed by calling that supplied method directly -- the
    closed-form route's own callee (`crv.py:217`), exactly as
    `quadrature_returns` is observed by calling the integrating route's own
    callee `compute_cdf(**kwargs)(x)` (`crv.py:220`) directly. Neither facet is
    read off `dist.cdf(...)`: the dispatch additionally reads the option set,
    tests the probe against None and may take the OTHER route, and it is those
    choices the diffs below are about. Consulted only on the closed-form route;
    elsewhere the fuzzer feeds BOTH values.
    NOT reconstructed from the closed form's branch comparisons (`x < a`,
    `x <= b`). That reconstruction is measurably a DIFFERENT predicate: for
    `ArcsinDistribution(0, oo)` and the query point `I*sr` (sr real) both
    comparisons come back as standing relations, yet assembling the closed
    form raises (`ValueError: I*sr < 0 contains imaginary parts which cannot
    be made 0 ...`), while `ArcsinDistribution(0, 1)` with the same query
    point assembles fine. The route's delivery is the fact the model carries;
    which ordering question inside the assembly refused it is not. The
    instantiation pools sample that shape deliberately, and the SETUP guard
    below fails if they stop reaching it.
  * the `int` result-form code <-> which denotation the real result equals:
    CF_ARCSIN iff the result equals the family's precomputed closed form
    `dist._cdf(x)` (necessarily non-None; also asserted to carry no
    unevaluated Integral), CF_INTEGRAL iff it equals the integral fallback
    `dist.compute_cdf(**kwargs)(x)`. The two denotations are asserted
    distinct wherever both are computed (the non-default inverse-sine
    queries), so the classification cannot silently conflate the branches.

THREE diffs are run per lowered input, because the model states three things:

  (D1) RESULT FORM. Whenever the real dispatch hands a value back, the
       shadow's `cdf_result(...)` code must equal the denotation the real
       result has. This covers all four abstract (fam, default_query) points.
  (D2) DELIVERY, as a VALUE. The shadow's `query_arrives(fam, default_query,
       quadrature_returns, closed_form_returns)` must EQUAL whether the real
       dispatch hands a value back at all. An equality in both directions, so
       it refutes both an over-claim (the model promising a value where the
       real callee raises) and an under-claim (the model withholding it where
       the real callee does return). Both sides are observable: on the
       closed-form route (`crv.py:216-219`) the dispatch probes `_cdf` and
       hands back what that returns, WITHOUT catching anything and without
       falling through to the fallback, so it returns exactly when `_cdf(x)`
       does; otherwise the dispatch's result IS `compute_cdf(**kwargs)(x)`
       (`crv.py:220`), so it returns exactly when that does. What this diff
       tests is therefore the dispatch's own content -- which route a query
       takes, and that the chosen route's outcome is passed through
       unrecovered -- with each route's fact observed on that route's OWN
       callee.
  (D3) ROUTE INDEPENDENCE OF THE FORM. The shadow's result form is recomputed
       under all four (quadrature_returns, closed_form_returns) combinations and
       asserted invariant: which form the answer has is settled by the family
       and the option set alone. The real dispatch reads neither delivery
       facet when choosing the route, so a form that moved with one would be
       a model artefact.

Input domain: the model's Requires admits {FAM_ARCSIN, FAM_OTHER} x {default,
non-default} x {quadrature_returns T,F} x {closed_form_returns T,F} -- all
covered. Each abstract point is lowered to MANY concrete oracle
instantiations (distinct rational/symbolic bounds AND distinct query points for
the inverse-sine family, including bounds and query points the ordering refuses;
distinct densities, intervals and rate parameters for the no-closed-form
families; several option sets for the non-default queries; and
supports/options on which the integrating route does NOT hand a value back),
and every instantiation is independently diffed. The real dispatch is a
deterministic pure function of (instantiation, query point, options), so, as in
the other sympy bundles, oracle observations are memoized per (instantiation,
query point, options) once freshly computed; every generated input is still
individually diffed.

>= 1e5 Requires-satisfying inputs: ~4000 fresh concrete instantiations
(every one a real in-container oracle call, spanning all four abstract
(fam, default_query) points and both delivery outcomes on BOTH routes,
boundary bound/density/query-point shapes included) + fuzz draws over the
abstract domain lowered onto the instantiation pools, to 100000+ total. Pinned
fuzz seed: 13878.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 13878
N_TOTAL = 100_000


# --- model.py constants (kept in lock-step with model.py) ---------------------

CF_INTEGRAL = 0
CF_ARCSIN = 1
FAM_ARCSIN = 1
FAM_OTHER = 0


# --- pure region of model.py, contracts stripped -------------------------------

def has_closed_form(fam):
    """Whether the family supplies a closed-form cumulative function (so a
    default query can answer in closed form rather than by integration)."""
    return fam == FAM_ARCSIN


def closed_form_for(fam, default_query):
    """The result-form code a cumulative query produces for family `fam`."""
    if default_query and fam == FAM_ARCSIN:
        return CF_ARCSIN
    return CF_INTEGRAL


def answers_from_closed_form(fam, default_query):
    """Whether the query is answered by consulting the supplied closed form
    rather than by integrating."""
    return default_query and has_closed_form(fam)


def closed_form_arrives(fam, default_query, closed_form_returns):
    """Whether the CLOSED-FORM route hands a value back."""
    return answers_from_closed_form(fam, default_query) and closed_form_returns


def query_delivers(fam, default_query, quadrature_returns, closed_form_returns):
    """Whether the query hands back a result at all (per-route split)."""
    if answers_from_closed_form(fam, default_query):
        return closed_form_arrives(fam, default_query, closed_form_returns)
    return quadrature_returns


# --- impl region of model.py, verbatim (contracts stripped) --------------------

def cdf_result(fam, default_query, quadrature_returns, closed_form_returns):
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL


def closed_form_for_family(fam, closed_form_returns):
    return CF_ARCSIN


def query_arrives(fam, default_query, quadrature_returns, closed_form_returns):
    if default_query:
        if has_closed_form(fam):
            return closed_form_returns
    return quadrature_returns


# --- oracle: the real patched dispatch, classified into result-form codes ------

class Oracle(object):
    """Runs the real `SingleContinuousDistribution.cdf` dispatch on one
    concrete (distribution, query point, options) instantiation and reports

        (delivered, quadrature_returns, closed_form_returns, code, detail)

    `delivered` is whether the dispatch handed a value back at all (False when
    it raised). `quadrature_returns` is whether the integrating route of this
    query hands a value back -- observed by calling
    `compute_cdf(**kwargs)(x)`, except on the closed-form route, where the
    dispatch never reaches it and the facet is not consulted (None).
    `closed_form_returns` is whether the family's SUPPLIED closed form comes
    back for this query -- observed by calling that supplied method directly,
    and only on the closed-form route, where it is the work that route does
    (None elsewhere). It is the call's own return, not the narrower "both
    branch comparisons stand" reconstruction, which is a different predicate.
    `code` is the result-form denotation when a value was delivered, or None
    when the result matches NEITHER denotation (a real disagreement surface, reported by the
    caller). Deterministic per instantiation, so observations are memoized;
    the fresh pass computes every one once."""

    def __init__(self, Integral, base_cdf, arcsin_cls):
        self.Integral = Integral
        self.base_cdf = base_cdf
        self.arcsin_cls = arcsin_cls
        self.memo = {}

    def _quadrature_returns(self, dist, kwargs, x):
        """Does the integrating route hand a value back for this query?"""
        try:
            dist.compute_cdf(**kwargs)(x)
        except Exception:
            return False
        return True

    def _closed_form_returns(self, dist, x):
        """Does the family's SUPPLIED closed form come back for this query?

        The closed-form route's whole work is `self._cdf(x)` (`crv.py:217`),
        whose value the dispatch then hands straight back (`crv.py:219`). So
        the facet is observed by calling that supplied method DIRECTLY -- the
        route's own callee, exactly as `quadrature_returns` calls the
        integrating route's own callee. Not read off `dist.cdf(...)`: the
        dispatch additionally reads the option set, tests the probe against
        None, and may take the other route instead, and it is those choices
        the diff is about.

        Deliberately NOT reconstructed from the closed form's branch
        comparisons (`x < dist.a`, `x <= dist.b`). Measured: for
        `ArcsinDistribution(0, oo)` and query point `I*sr` (sr real) BOTH
        comparisons come back as standing relations while the assembly itself
        raises `ValueError: I*sr < 0 contains imaginary parts which cannot be
        made 0 ...`; for `ArcsinDistribution(0, 1)` and the same query point
        the assembly comes back. The reconstruction is therefore a different
        predicate from the route's delivery, and it is the delivery the model
        carries."""
        if not isinstance(dist, self.arcsin_cls):
            # No other family in the pools supplies a closed form, so this
            # facet has no other closed form to be about. Reaching here would
            # mean a pool row supplies one without a probe, which is a script
            # defect, not an observation: say so loudly.
            raise AssertionError(
                "no closed-form probe for a closed-form-supplying "
                "family: %r" % (type(dist),))
        try:
            got = type(dist)._cdf(dist, x)
        except Exception:
            return False
        if got is None:
            # The structural route facet said this family supplies a closed
            # form; a None here would contradict it. A script/pool defect.
            raise AssertionError(
                "family read as supplying a closed form returned None: %r"
                % (type(dist),))
        return True

    def _comparisons_stand(self, dist, x):
        """Do the closed form's two branch comparisons come back as standing
        relations for this query? Not the facet the model carries -- recorded
        only so the run can PROVE its pools reach the shape that separates the
        two readings (comparisons standing while the assembly still refuses),
        which is what the SETUP guard in main() asserts."""
        try:
            x < dist.a
            x <= dist.b
        except Exception:
            return False
        return True

    def observe(self, key, make_dist, kwargs, x):
        if key in self.memo:
            return self.memo[key]
        # Constructing the distribution is SETUP, not the dispatch: let a
        # constructor failure propagate loudly rather than be mistaken for the
        # dispatch withholding a value.
        dist = make_dist()
        # The route facet, read structurally so that it is available even when
        # evaluating the closed form would refuse.
        supplies = type(dist)._cdf is not self.base_cdf
        default_query = (len(kwargs) == 0)
        closed_route = default_query and supplies
        # Facets, each observed only on the route that consults it.
        oc = self._closed_form_returns(dist, x) if closed_route else None
        qr = (None if closed_route
              else self._quadrature_returns(dist, kwargs, x))
        try:
            res = dist.cdf(x, **kwargs)
        except Exception as exc:
            out = (False, qr, oc, None,
                   "no value delivered: %s: %s" % (type(exc).__name__, exc))
            self.memo[key] = out
            return out
        # A value came back. Classify which denotation it is.
        closed = None
        if supplies:
            try:
                closed = dist._cdf(x)
            except Exception:
                closed = None
        # Where the closed form DOES evaluate, the structural route facet must
        # agree with the dispatch's own test (`_cdf(x) is not None`).
        if closed is not None and not supplies:
            out = (True, qr, oc, None,
                   "structural route facet disagrees with the dispatch's own "
                   "test: `_cdf` not overridden yet `_cdf(x)` is %r" % (closed,))
            self.memo[key] = out
            return out
        if closed is not None and res == closed:
            # the precomputed-closed-form branch; must carry no unevaluated
            # integral (the form the result-form code names is closed). The
            # integrating route is not reached, so its facet is not consulted.
            if res.has(self.Integral):
                out = (True, qr, oc, None,
                       "closed-form branch result carries an "
                       "unevaluated Integral: %r" % (res,))
            else:
                out = (True, qr, oc, CF_ARCSIN, "closed form: %r" % (res,))
            self.memo[key] = out
            return out
        # must be the integral-fallback denotation. compute_cdf is cached
        # by the repo, so this recomputation is the value the dispatch
        # itself produced on this route.
        # NB: on this route res != closed (or closed is None), so the two
        # denotations are distinct here and the codes cannot conflate.
        if qr is None:
            qr = self._quadrature_returns(dist, kwargs, x)
        fallback = dist.compute_cdf(**kwargs)(x)
        if res == fallback:
            out = (True, qr, oc, CF_INTEGRAL, "integral fallback")
        else:
            out = (True, qr, oc, None,
                   "result equals neither the precomputed closed "
                   "form (%r) nor the integral fallback (%r): %r"
                   % (closed, fallback, res))
        self.memo[key] = out
        return out


def check_one(oracle, fam, default_query, key, make_dist, kwargs, x,
              qr_when_unconsulted, oc_when_unconsulted):
    """Diff shadow vs real on one lowered input; return an error string on
    disagreement, else None.

    `qr_when_unconsulted` / `oc_when_unconsulted` are the values the fuzzer
    supplies for a facet the real dispatch never consults on this input's route
    (the integration on the closed-form route; the branch comparisons on the
    integrating route). Feeding BOTH values there is itself a check: neither the
    result form nor the delivery verdict may depend on a facet the real dispatch
    does not read on that route."""
    delivered, real_qr, real_oc, real_code, detail = oracle.observe(
        key, make_dist, kwargs, x)
    quadrature_returns = (qr_when_unconsulted if real_qr is None else real_qr)
    closed_form_returns = (oc_when_unconsulted if real_oc is None else real_oc)
    where = ("  input: fam=%d default_query=%r quadrature_returns=%r "
             "closed_form_returns=%r\n"
             "         instantiation=%r x=%r kwargs=%r\n"
             % (fam, default_query, quadrature_returns, closed_form_returns,
                key, x, kwargs))

    # (D2) DELIVERY as a VALUE, both directions.
    model_arrives = query_arrives(fam, default_query, quadrature_returns,
                                  closed_form_returns)
    if model_arrives != delivered:
        kind = ("model promises a value the real dispatch does not hand back"
                if model_arrives else
                "model withholds the promise on a query the real dispatch "
                "does answer")
        return ("DISAGREEMENT (delivery)\n" + where +
                "  model query_arrives=%r  real delivered=%r\n"
                "  %s\n  real: %s"
                % (model_arrives, delivered, kind, detail))

    # (D3) the result form reads NEITHER delivery facet.
    forms = set(cdf_result(fam, default_query, q, o)
                for q in (True, False) for o in (True, False))
    if len(forms) != 1:
        return ("DISAGREEMENT (result form depends on a delivery facet)\n"
                + where + "  shadow forms over (qr, oc): %r" % (sorted(forms),))

    # (D1) RESULT FORM, wherever a value exists to classify.
    if not delivered:
        return None
    shadow = cdf_result(fam, default_query, quadrature_returns,
                        closed_form_returns)
    if real_code is None:
        return ("DISAGREEMENT (unclassifiable oracle result)\n" + where +
                "  shadow=%d\n  real: %s" % (shadow, detail))
    if shadow != real_code:
        return ("DISAGREEMENT\n" + where +
                "  shadow=%d\n  real=%d (%s)" % (shadow, real_code, detail))
    return None


def main():
    # REAL patched repo classes (mapping.md section 1) -- import from /testbed.
    from sympy import (Symbol, Rational, Lambda, Interval, Integral, exp, oo,
                       FiniteSet, Union, S, I, nan, zoo, sqrt, pi, Float)
    from sympy.stats.crv import (ContinuousDistributionHandmade,
                                 SingleContinuousDistribution)
    from sympy.stats.crv_types import ArcsinDistribution

    x = Symbol("x")
    a_sym = Symbol("a", real=True)
    b_sym = Symbol("b", real=True)
    a_gen = Symbol("ag")
    a_imag = Symbol("ai", imaginary=True)
    x_real = Symbol("xr", real=True)
    x_imag = Symbol("xi", imaginary=True)
    z = Symbol("z", real=True, positive=True)
    rng = random.Random(SEED)

    # ---- concrete instantiation pools, one per abstract input point ---------
    # Each pool entry: (key, make_dist, kwargs, x). Keys are hashable
    # descriptors used for memoization and disagreement printing.

    def arcsin(lo, hi):
        return ArcsinDistribution(lo, hi)

    def handmade_monomial(k, scale_num, scale_den):
        # genuine density on (0, s): (k+1) * z**k / s**(k+1), s = num/den
        s = Rational(scale_num, scale_den)
        dens = Lambda(z, (k + 1) * z ** k / s ** (k + 1))
        return ContinuousDistributionHandmade(dens, Interval(0, s))

    def handmade_uniform(c_num, c_den, d_num, d_den):
        c = Rational(c_num, c_den)
        d = Rational(d_num, d_den)
        dens = Lambda(z, 1 / (d - c))
        return ContinuousDistributionHandmade(dens, Interval(c, d))

    def handmade_exponential(rate_num, rate_den):
        lam = Rational(rate_num, rate_den)
        dens = Lambda(z, lam * exp(-lam * z))
        return ContinuousDistributionHandmade(dens, Interval(0, oo))

    def handmade_on(support):
        # a genuine constant density carried on a support that is NOT a single
        # Interval, so the integrating route cannot read a lower bound at all
        # (crv.py:202 reads self.set.start).
        return ContinuousDistributionHandmade(Lambda(z, S.Half), support)

    # (FAM_ARCSIN, default): distinct bound pairs x distinct query points --
    # BOTH dimensions of the closed-form route's branch comparisons. Boundary
    # shapes on the bounds: the constructor-default unit interval, symbolic
    # bounds (the exact shape the failing test exercises), unconstrained
    # symbolic bounds, negative / mixed-sign bounds, a tiny interval,
    # large-magnitude bounds, degenerate and reversed bounds, unbounded bounds,
    # and bounds the ordering REFUSES (imaginary literal and symbol, an
    # indeterminate, an unsigned infinity). Boundary shapes on the query point:
    # a plain and a real symbol, rationals, a float, both signed infinities,
    # and query points the ordering refuses.
    arcsin_bounds = [
        ("sym", a_sym, b_sym),
        ("gensym", a_gen, Symbol("bg")),
        ("unit", S.Zero, S.One),
        ("neg", Rational(-7, 2), Rational(-1, 3)),
        ("mixed", Rational(-5), Rational(9)),
        ("tiny", S.Zero, Rational(1, 10 ** 9)),
        ("big", Rational(-10 ** 12), Rational(10 ** 12)),
        ("degenerate", Rational(2), Rational(2)),
        ("reversed", Rational(5), Rational(1)),
        ("unbounded", -oo, oo),
        ("halfline", S.Zero, oo),
        ("irrational", sqrt(2), pi),
        ("float", Float(0.25), Float(2.5)),
        # bounds the ordering refuses -> the closed-form route hands nothing back
        ("imag-lo", I, S.One),
        ("imag-hi", S.Zero, 2 * I),
        ("imag-sym-lo", a_imag, S.One),
        ("complex-lo", 1 + I, Rational(2)),
        ("nan-lo", nan, S.One),
        ("zoo-lo", zoo, Rational(2)),
    ]
    arcsin_points = [
        ("x", x),
        ("xreal", x_real),
        ("rat", Rational(1, 2)),
        ("int", Rational(1)),
        ("float", Float(0.75)),
        ("+oo", oo),
        ("-oo", -oo),
        # query points the ordering refuses
        ("I", I),
        ("2I", 2 * I),
        ("ximag", x_imag),
        ("nan", nan),
        ("zoo", zoo),
        # A query point whose realness is UNKNOWN rather than refused: both
        # branch comparisons come back as standing relations, so the narrower
        # reconstruction says this route delivers, while on an unbounded support
        # assembling the branches still ends with no value. This is the shape
        # that separates the two readings of the facet, and the SETUP guard
        # below requires the pool to reach it.
        ("I*xreal", I * x_real),
    ]
    arcsin_default = []
    for btag, lo, hi in arcsin_bounds:
        for ptag, xv in arcsin_points:
            arcsin_default.append(
                (("arcsin", btag, ptag),
                 (lambda lo=lo, hi=hi: arcsin(lo, hi)), {}, xv))
    # plus a rational sweep, each draw paired with a drawn query point
    sweep_points = [x, x_real, Rational(1, 3), oo, -oo, I, nan, zoo]
    for i in range(1500):
        num = rng.randint(-10 ** 4, 10 ** 4)
        den = rng.randint(1, 100)
        width_num = rng.randint(1, 10 ** 4)
        width_den = rng.randint(1, 100)
        lo = Rational(num, den)
        hi = lo + Rational(width_num, width_den)
        pi_ = rng.randrange(len(sweep_points))
        arcsin_default.append(
            (("arcsin", num, den, width_num, width_den, pi_),
             (lambda lo=lo, hi=hi: arcsin(lo, hi)), {}, sweep_points[pi_]))

    # (FAM_ARCSIN, non-default): explicit integration options. These route
    # through the integral fallback (a slow symbolic integration), so the
    # pool is small; each entry is still a fresh real dispatch call. Several
    # carry options or bounds on which that route hands NO value back.
    arcsin_kwargs = []
    for i, (lo, hi) in enumerate([(S.Zero, Rational(3)),
                                  (S.Zero, S.One),
                                  (Rational(-1), S.One),
                                  (Rational(1, 2), Rational(5, 2))]):
        arcsin_kwargs.append(
            (("arcsin-kw-none", i),
             (lambda lo=lo, hi=hi: arcsin(lo, hi)), {"conds": "none"}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-none", "sym"),
         (lambda: arcsin(a_sym, b_sym)), {"conds": "none"}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-piecewise", 0),
         (lambda: arcsin(S.Zero, Rational(2))), {"conds": "piecewise"}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-risch", 0),
         (lambda: arcsin(S.Zero, Rational(3))), {"risch": True}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-heurisch", 0),
         (lambda: arcsin(S.Zero, Rational(3))), {"heurisch": True}, x))
    # the ordering-refusing dimension on the OPTIONS route, where the closed
    # form is bypassed entirely: whether a value comes back is then the
    # integration's business alone.
    arcsin_kwargs.append(
        (("arcsin-kw-none", "imag-lo"),
         (lambda: arcsin(I, S.One)), {"conds": "none"}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-none", "nan-lo"),
         (lambda: arcsin(nan, S.One)), {"conds": "none"}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-none", "zoo-lo"),
         (lambda: arcsin(zoo, Rational(2))), {"conds": "none"}, x))
    arcsin_kwargs.append(
        (("arcsin-kw-none", "x-imag"),
         (lambda: arcsin(S.Zero, Rational(3))), {"conds": "none"}, I))

    # (FAM_OTHER, default): families whose `_cdf` is the base-class None.
    other_default = []
    other_default.append((("uniform", 0, 1, 1, 1), (lambda: handmade_uniform(0, 1, 1, 1)), {}, x))
    other_default.append((("mono", 0, 1, 1), (lambda: handmade_monomial(0, 1, 1)), {}, x))
    other_default.append((("expo", 1, 1), (lambda: handmade_exponential(1, 1)), {}, x))
    other_default.append((("uniform-xreal", 0, 1, 1, 1),
                          (lambda: handmade_uniform(0, 1, 1, 1)), {}, x_real))
    other_default.append((("uniform-xrat", 0, 1, 1, 1),
                          (lambda: handmade_uniform(0, 1, 1, 1)), {}, Rational(1, 2)))
    # supports that are not a single Interval: the integrating route cannot
    # read a lower bound, so no value is handed back.
    other_default.append(
        (("split-support", 0),
         (lambda: handmade_on(Union(Interval(0, 1), Interval(3, 4)))), {}, x))
    other_default.append(
        (("finite-support", 0),
         (lambda: handmade_on(FiniteSet(0, 1))), {}, x))
    for i in range(700):
        k = rng.randint(0, 6)
        sn = rng.randint(1, 50)
        sd = rng.randint(1, 20)
        other_default.append(
            (("mono", k, sn, sd),
             (lambda k=k, sn=sn, sd=sd: handmade_monomial(k, sn, sd)), {}, x))
    for i in range(700):
        cn = rng.randint(-500, 500)
        cd = rng.randint(1, 30)
        wn = rng.randint(1, 500)
        wd = rng.randint(1, 30)
        dn, dd = cn * wd + wn * cd, cd * wd  # c + w as a single rational
        other_default.append(
            (("uniform", cn, cd, dn, dd),
             (lambda cn=cn, cd=cd, dn=dn, dd=dd:
              handmade_uniform(cn, cd, dn, dd)), {}, x))
    for i in range(300):
        rn = rng.randint(1, 100)
        rd = rng.randint(1, 20)
        other_default.append(
            (("expo", rn, rd),
             (lambda rn=rn, rd=rd: handmade_exponential(rn, rd)), {}, x))

    # (FAM_OTHER, non-default): same family shapes with explicit options, plus
    # the two shapes on which the integrating route hands no value back.
    other_kwargs = []
    other_kwargs.append(
        (("split-support-kw-none", 0),
         (lambda: handmade_on(Union(Interval(0, 1), Interval(3, 4)))),
         {"conds": "none"}, x))
    other_kwargs.append(
        (("uniform-kw-risch", 0),
         (lambda: handmade_uniform(0, 1, 1, 1)), {"risch": True}, x))
    for i in range(600):
        k = rng.randint(0, 6)
        sn = rng.randint(1, 50)
        sd = rng.randint(1, 20)
        conds = "none" if i % 2 == 0 else "piecewise"
        other_kwargs.append(
            (("mono-kw-" + conds, k, sn, sd),
             (lambda k=k, sn=sn, sd=sd: handmade_monomial(k, sn, sd)),
             {"conds": conds}, x))
    for i in range(600):
        cn = rng.randint(-500, 500)
        cd = rng.randint(1, 30)
        wn = rng.randint(1, 500)
        wd = rng.randint(1, 30)
        dn, dd = cn * wd + wn * cd, cd * wd
        conds = "none" if i % 2 == 0 else "piecewise"
        other_kwargs.append(
            (("uniform-kw-" + conds, cn, cd, dn, dd),
             (lambda cn=cn, cd=cd, dn=dn, dd=dd:
              handmade_uniform(cn, cd, dn, dd)), {"conds": conds}, x))
    for i in range(200):
        rn = rng.randint(1, 100)
        rd = rng.randint(1, 20)
        conds = "none" if i % 2 == 0 else "piecewise"
        other_kwargs.append(
            (("expo-kw-" + conds, rn, rd),
             (lambda rn=rn, rd=rd: handmade_exponential(rn, rd)),
             {"conds": conds}, x))

    pools = {
        (FAM_ARCSIN, True): arcsin_default,
        (FAM_ARCSIN, False): arcsin_kwargs,
        (FAM_OTHER, True): other_default,
        (FAM_OTHER, False): other_kwargs,
    }

    oracle = Oracle(Integral, SingleContinuousDistribution._cdf,
                    ArcsinDistribution)
    checked = 0
    fresh = 0
    delivered_n = 0
    withheld_n = 0
    withheld_closed = 0
    withheld_quad = 0

    # ---- pass 1: every concrete instantiation freshly diffed (covers all ----
    # four abstract (fam, default_query) points exhaustively, and both
    # delivery outcomes on BOTH routes), under BOTH values of every facet the
    # real dispatch does not consult on that input's route.
    for (fam, default_query), pool in sorted(pools.items()):
        for key, mk, kwargs, xv in pool:
            for qr in (True, False):
                for oc in (True, False):
                    err = check_one(oracle, fam, default_query, key, mk,
                                    kwargs, xv, qr, oc)
                    if err:
                        print(err)
                        return 1
                    checked += 1
            fresh += 1
            obs = oracle.memo[key]
            if obs[0]:
                delivered_n += 1
            else:
                withheld_n += 1
                # which route withheld it: the closed-form one (its branch
                # comparisons refused) or the integrating one.
                if obs[2] is not None:
                    withheld_closed += 1
                else:
                    withheld_quad += 1

    if not withheld_quad:
        print("SETUP ERROR: no instantiation on which the INTEGRATING route "
              "withholds a value; the delivery diff (D2) would be one-sided "
              "on that route.")
        return 1
    if not withheld_closed:
        print("SETUP ERROR: no instantiation on which the CLOSED-FORM route "
              "withholds a value; the ordering facet would be unsampled -- "
              "which is exactly the region an earlier version of this pool "
              "never reached.")
        return 1
    if not delivered_n:
        print("SETUP ERROR: no instantiation on which the real dispatch hands "
              "a value back.")
        return 1
    # The closed-form route can end without a value in two independent ways, and
    # the facet this diff carries is the route's own delivery rather than the
    # narrower "both branch comparisons stand" reconstruction. That choice is
    # only tested if the pool reaches a query where the two DISAGREE: both
    # comparisons standing while the route still hands nothing back. Without
    # such a row the diff would pass under either reading and would not be
    # evidence for the one the model carries.
    separating = [
        (key, xv) for key, mk, kwargs, xv in pools[(FAM_ARCSIN, True)]
        if oracle._comparisons_stand(mk(), xv)
        and not oracle._closed_form_returns(mk(), xv)]
    if not separating:
        print("SETUP ERROR: no instantiation on which the closed form's branch "
              "comparisons stand while the closed-form route still hands no "
              "value back; the facet would be indistinguishable here from the "
              "narrower branch-comparison reconstruction.")
        return 1
    print("SETUP: %d instantiation(s) separate the route's delivery from the "
          "branch-comparison reconstruction, e.g. %r at x=%r"
          % (len(separating), separating[0][0], separating[0][1]))

    # ---- pass 2: fuzz over the abstract Requires domain, lowered onto the ---
    # pools (memoized deterministic observations; each draw is still an
    # individually diffed Requires-satisfying input).
    n_fuzz = N_TOTAL - checked
    abstract = [(FAM_ARCSIN, True), (FAM_ARCSIN, False),
                (FAM_OTHER, True), (FAM_OTHER, False)]
    for i in range(n_fuzz):
        fam, default_query = rng.choice(abstract)
        key, mk, kwargs, xv = rng.choice(pools[(fam, default_query)])
        err = check_one(oracle, fam, default_query, key, mk, kwargs, xv,
                        rng.choice((True, False)), rng.choice((True, False)))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow dispatch == real cumulative-query dispatch on "
          "%d inputs (%d fresh concrete instantiations spanning all 4 "
          "abstract (fam, default_query) points -- %d on which the real "
          "dispatch hands a value back, %d on which it does not (%d because "
          "the closed form's branch comparisons were refused, %d because the "
          "integration did not come back) -- + %d fuzz draws, seed %d). The "
          "result-form diff, the delivery diff (equality, both directions) "
          "and the form's independence of both delivery facets agreed "
          "everywhere."
          % (checked, fresh, delivered_n, withheld_n, withheld_closed,
             withheld_quad, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "fresh_instantiations": fresh,
                      "delivering_instantiations": delivered_n,
                      "withholding_instantiations": withheld_n,
                      "withholding_closed_form_route": withheld_closed,
                      "withholding_integrating_route": withheld_quad,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
