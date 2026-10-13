#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13878.

This bundle consumes NO `@ContractOnly` axiom: the modeled behaviour is the
cumulative-function dispatch (closed form when the family supplies one, else the
integral fallback), modeled DEEPLY (spelled out in model.py's `cdf_result` /
`closed_form_for` / `has_closed_form` over a family tag and the
default-vs-customised query flag). There is no unchanged opaque callee whose
`Ensures` the proof relies on.

What G-AX validates here is the DEEP MODEL itself (an A-reference): for the
inverse-sine family the model distinguishes, the real cumulative dispatch of the
post-patch repository agrees with the model's verdict, when the model is fed the
same observation the real code reads (the family -- via whether it supplies a
precomputed closed-form cumulative -- and whether the query is the default
no-option query).

The real dispatch (sympy/stats/crv.py, SingleContinuousDistribution.cdf):

    if len(kwargs) == 0:
        c = self._cdf(x)
        if c is not None:
            return c                      # the closed-form branch
    return self.compute_cdf(**kwargs)(x)  # the integral branch

so the result-form is the CLOSED FORM exactly when the query is the default
(no kwargs) AND `_cdf` is supplied (not None); otherwise it is the integral
fallback. The model's `has_closed_form(fam)` mirrors `_cdf is not None`, and
`closed_form_for(fam, default_query)` mirrors this dispatch.

Concretely it asserts, against the REAL sympy:

  (1) `has_closed_form` mirrors `_cdf is not None`: the inverse-sine family
      supplies a precomputed closed-form cumulative; a control family the change
      does not touch does not.

  (2) The dispatch mirrors `closed_form_for` on the closed-form branch: a
      default query on the inverse-sine family takes the closed-form branch (the
      returned cumulative equals the precomputed closed form and carries no
      unevaluated integral). The integral branch is identified faithfully by the
      dispatch FACET (`_cdf is None`, or kwargs present), NOT by a
      value-membership proxy on the output: the dispatch
      (`SingleContinuousDistribution.cdf`) is UNCHANGED source the patch does
      not touch, and for any family whose `_cdf` is None — or any query carrying
      options — it necessarily routes through `compute_cdf` (integration). The
      check therefore asserts that facet directly (the control family's `_cdf`
      is None) rather than triggering the integration the issue reports can
      hang.

  (3) CF_ARCSIN names the family's TRUE cumulative function: the closed form
      returned on a default inverse-sine query equals, symbolically, the exact
      three-branch inverse-sine expression the FAIL_TO_PASS test (test_arcsin)
      asserts -- the index-level discriminator -- and its derivative on the
      support equals the density (so it is genuinely the CDF).

  (4) `closed_form_returns` names the real facet the CLOSED-FORM route's arrival
      turns on, and `quadrature_returns` the integrating route's. The closed
      form is a three-branch expression whose branch conditions are exactly the
      comparisons of the query point against each support bound (asserted
      structurally on the real expression), but that route's arrival is settled
      by whether the supplied closed form it asks the family for comes back at
      all -- a strictly weaker fact than "the ordering admits those two
      comparisons", since assembling the branches can end without a value even
      where both comparisons stand. The check calls that supplied closed form
      directly (independently of the dispatch), proves its table reaches a query
      that separates the two readings, and asserts
      the model's per-route delivery verdict (`query_delivers`, the value
      `query_arrives` returns) equals what the real dispatch does on a table of
      concrete instantiations: support bounds and query points on the order
      line, where the closed-form route arrives, and magnitudes that are not on
      it (a non-real quantity, an indeterminate, an unsigned infinity), where it
      arrives with no value; and on the option-carrying route, where the closed
      form is bypassed and arrival is the integration's business alone.

It imports only `sympy` (the repository under test) and the standard library.
Exit 0 iff every observation matches the model.

G-AX INVOCATION: this script models the *fixed* dispatch, so it must run on the
POST-PATCH worktree (apply_gold=True). At base_commit it correctly FAILS,
because the base repository lacks the inverse-sine family's precomputed
cumulative (`_cdf` returns None there), so its default query returns an
unevaluated Integral rather than the inverse-sine closed form -- exactly the
bug the gold patch fixes.
"""
import sys

# --- model.py reference codes (kept in lock-step with model.py) --------------
CF_INTEGRAL = 0
CF_ARCSIN = 1
FAM_ARCSIN = 1
FAM_OTHER = 0


def model_has_closed_form(fam):
    return fam == FAM_ARCSIN


def model_closed_form_for(fam, default_query):
    if default_query and fam == FAM_ARCSIN:
        return CF_ARCSIN
    return CF_INTEGRAL


def model_answers_from_closed_form(fam, default_query):
    return default_query and model_has_closed_form(fam)


def model_query_delivers(fam, default_query, quadrature_returns,
                         closed_form_returns):
    """model.py's `query_delivers` / the value `query_arrives` returns."""
    if model_answers_from_closed_form(fam, default_query):
        return closed_form_returns
    return quadrature_returns


def main():
    from sympy import Symbol, Piecewise, sqrt, asin, pi, simplify, diff, Dummy
    from sympy import Integral, Rational, S, I, oo
    from sympy.stats import Arcsin, Benini, cdf, density
    from sympy.stats.crv import SingleContinuousDistribution
    from sympy.stats.crv_types import ArcsinDistribution

    x = Symbol("x")
    a = Symbol("a", real=True)
    b = Symbol("b", real=True)
    t = Dummy("t", real=True, finite=True)

    # ---- (1) has_closed_form mirrors `_cdf is not None` ---------------------
    arcsin_dist = Arcsin("x", a, b).pspace.distribution
    arcsin_has = arcsin_dist._cdf(t) is not None
    assert arcsin_has == model_has_closed_form(FAM_ARCSIN), (
        "availability mismatch: real arcsin `_cdf is not None`=%s, model=%s"
        % (arcsin_has, model_has_closed_form(FAM_ARCSIN)))

    # A control family the change does NOT touch (Benini): no precomputed _cdf.
    benini_dist = Benini("y", 1, 1, 1).pspace.distribution
    benini_has = benini_dist._cdf(t) is not None
    assert benini_has == model_has_closed_form(FAM_OTHER), (
        "control family unexpectedly supplies a precomputed cumulative: "
        "real `_cdf is not None`=%s model=%s" % (benini_has,
                                                 model_has_closed_form(FAM_OTHER)))

    # ---- (2) dispatch mirrors closed_form_for (closed-form branch) ----------
    # (2a) default inverse-sine query -> closed-form branch: the result equals
    # the precomputed closed form and carries NO unevaluated integral. Because
    # `_cdf` is supplied, the UNCHANGED dispatch returns it directly WITHOUT
    # calling compute_cdf (no integration is triggered here).
    arcsin_default = cdf(Arcsin("x", a, b))(x)
    assert model_closed_form_for(FAM_ARCSIN, True) == CF_ARCSIN
    assert not arcsin_default.has(Integral), (
        "default inverse-sine query did NOT take the closed-form branch "
        "(result still carries an Integral): %r" % (arcsin_default,))

    # (2b) integral branch is identified by the dispatch FACET, asserted
    # directly without triggering the (possibly non-terminating) integration:
    #   * a query carrying options is the non-default query (model: CF_INTEGRAL);
    #   * the control family supplies no precomputed closed form, so its default
    #     query necessarily routes through compute_cdf in the UNCHANGED dispatch.
    assert model_closed_form_for(FAM_ARCSIN, False) == CF_INTEGRAL
    assert model_closed_form_for(FAM_OTHER, True) == CF_INTEGRAL
    assert benini_dist._cdf(t) is None, (
        "control family unexpectedly supplies a precomputed closed form: %r"
        % (benini_dist._cdf(t),))

    # ---- (3) CF_ARCSIN names the family's TRUE cumulative function ----------
    # Exact symbolic equality with the three-branch inverse-sine form the
    # FAIL_TO_PASS test (test_arcsin) asserts -- the index-level discriminator,
    # no value-membership proxy.
    expected = Piecewise((0, a > x),
                         (2 * asin(sqrt((-a + x) / (-a + b))) / pi, b >= x),
                         (1, True))
    assert arcsin_default == expected, (
        "inverse-sine closed form != the test's asserted Piecewise:\n  got %r\n"
        "  want %r" % (arcsin_default, expected))

    # And it really is the CDF: its derivative on the support equals the density.
    # Use the numeric verifier sympy's own test suite uses (verify_numerically)
    # rather than bare `simplify(... ) == 0`: the residual is a TRUE radical
    # identity (sqrt((9-x)(x+5)) vs sqrt(9-x)*sqrt(x+5)) that plain `simplify`
    # cannot discharge without positivity assumptions -- a simplifier
    # incompleteness, not a math error.
    A, B = -5, 9
    Xd = Arcsin("X", A, B)
    cdf_expr = cdf(Xd)(x)
    on_support = cdf_expr.args[1][0]    # the inverse-sine (middle) branch
    dens = density(Xd)(x)
    from sympy.utilities.randtest import verify_numerically
    assert verify_numerically(diff(on_support, x), dens), (
        "derivative of the inverse-sine CDF branch != density: d/dx %r vs %r"
        % (on_support, dens))

    # ---- (4) the per-route delivery facets name the real facets -------------
    # (4a) The closed form's branch conditions ARE the comparisons of the query
    # point against each support bound. Read off the REAL expression, so the
    # model's account of what that route does is grounded, not asserted.
    branches = arcsin_default.args
    assert len(branches) == 3, (
        "inverse-sine closed form is not the three-branch expression the model "
        "describes: %r" % (arcsin_default,))
    lo_cond, hi_cond, tail_cond = (branches[0][1], branches[1][1],
                                   branches[2][1])
    assert lo_cond.is_Relational and set(lo_cond.free_symbols) == {a, x}, (
        "first branch condition is not a comparison of the query point against "
        "the lower support bound: %r" % (lo_cond,))
    assert hi_cond.is_Relational and set(hi_cond.free_symbols) == {b, x}, (
        "second branch condition is not a comparison of the query point "
        "against the upper support bound: %r" % (hi_cond,))
    assert tail_cond is True or tail_cond == S.true, (
        "third branch is not the catch-all: %r" % (tail_cond,))

    # (4b) The family's supplied closed form, CALLED DIRECTLY on the route's own
    # callee -- the facet observed independently of the dispatch, so what
    # follows is a check and not an echo. Deliberately NOT reconstructed from
    # the branch comparisons `q < dist.a` / `q <= dist.b`: selecting among the
    # branches is only one of the ways this route can end without a value, and
    # assembling them is a second, independent one, so that reconstruction is a
    # DIFFERENT predicate from the route's delivery. The table below carries a
    # row on which both comparisons come back as standing relations while the
    # assembly still ends with no value, which is what separates the two.
    def closed_form_returns(dist, q):
        try:
            got = type(dist)._cdf(dist, q)
        except Exception:
            return False
        return got is not None

    def comparisons_stand(dist, q):
        """The narrower reconstruction, kept only so the run can PROVE its table
        reaches the shape that separates it from the facet above."""
        try:
            q < dist.a
            q <= dist.b
        except Exception:
            return False
        return True

    def quadrature_returns(dist, q, kwargs):
        try:
            dist.compute_cdf(**kwargs)(q)
        except Exception:
            return False
        return True

    def delivers(dist, q, kwargs):
        try:
            dist.cdf(q, **kwargs)
        except Exception:
            return False
        return True

    # A table of concrete instantiations of the inverse-sine family: bounds and
    # query points on the order line, and magnitudes that are not on it at all.
    # `None` for a facet means the real dispatch does not consult it on this
    # row's route, and the model prediction is then checked under BOTH values.
    rows = [
        # (label, lower, upper, query point, kwargs)
        ("real bounds, symbolic query", S.Zero, S.One, x, {}),
        ("real bounds, rational query", Rational(-3), Rational(4),
         Rational(1, 2), {}),
        ("symbolic real bounds", a, b, x, {}),
        ("non-real lower bound", I, S.One, x, {}),
        ("non-real upper bound", S.Zero, 2 * I, x, {}),
        ("indeterminate lower bound", S.NaN, S.One, x, {}),
        ("unsigned-infinite lower bound", S.ComplexInfinity, Rational(2), x,
         {}),
        ("non-real query point", S.Zero, S.One, I, {}),
        ("indeterminate query point", S.Zero, S.One, S.NaN, {}),
        # Both branch comparisons come back as standing relations here, and the
        # route still ends with no value: the row that makes the facet above and
        # the narrower reconstruction distinguishable.
        ("real-multiple-of-I query, unbounded support",
         S.Zero, oo, I * Symbol("sr", real=True), {}),
        # the option-carrying route: the closed form is bypassed, so arrival is
        # whether the integration comes back and the ordering does not enter.
        ("option-carrying query", S.Zero, Rational(3), x, {"conds": "none"}),
        ("option-carrying, non-real bound", I, S.One, x, {"conds": "none"}),
    ]
    for label, lo, hi, q, kwargs in rows:
        dist = ArcsinDistribution(lo, hi)
        # The route facet, read structurally: this family supplies a closed form
        # whether or not evaluating it on this row's magnitudes is admitted.
        supplies = type(dist)._cdf is not SingleContinuousDistribution._cdf
        assert supplies == model_has_closed_form(FAM_ARCSIN), (
            "%s: family supplies a closed form=%s, model=%s"
            % (label, supplies, model_has_closed_form(FAM_ARCSIN)))
        default_query = (len(kwargs) == 0)
        closed_route = default_query and supplies
        real_delivers = delivers(dist, q, kwargs)
        oc = closed_form_returns(dist, q) if closed_route else None
        qr = None if closed_route else quadrature_returns(dist, q, kwargs)
        for oc_v in ([oc] if oc is not None else [True, False]):
            for qr_v in ([qr] if qr is not None else [True, False]):
                predicted = model_query_delivers(FAM_ARCSIN, default_query,
                                                 qr_v, oc_v)
                assert predicted == real_delivers, (
                    "%s: model per-route delivery verdict %s != real dispatch "
                    "%s (closed_form_returns=%s quadrature_returns=%s)"
                    % (label, predicted, real_delivers, oc_v, qr_v))

    # The table must actually reach BOTH edges of the closed-form route, or the
    # facet would be named without ever being exercised.
    reached = {}
    for label, lo, hi, q, kwargs in rows:
        if kwargs:
            continue
        dist = ArcsinDistribution(lo, hi)
        reached[closed_form_returns(dist, q)] = label
    assert True in reached and False in reached, (
        "the delivery table does not reach both edges of the closed-form "
        "route: %r" % (reached,))

    # And it must reach the shape that separates the facet from the narrower
    # reconstruction -- a row where both comparisons stand yet the route hands
    # nothing back -- or (4b)'s choice of observable would be untested.
    separating = [
        label for label, lo, hi, q, kwargs in rows
        if not kwargs
        and comparisons_stand(ArcsinDistribution(lo, hi), q)
        and not closed_form_returns(ArcsinDistribution(lo, hi), q)]
    assert separating, (
        "the delivery table never reaches a query on which the branch "
        "comparisons stand while the route still hands nothing back, so the "
        "facet is indistinguishable here from the narrower reconstruction")

    print("G-AX OK: deep cumulative-dispatch model == real sympy cdf/_cdf "
          "(inverse-sine family supplies a closed form whose default query "
          "equals the test's Piecewise and integrates to the density; options "
          "or a no-_cdf family take the integral branch; and the per-route "
          "delivery verdict matches the real dispatch on both edges of the "
          "closed-form route, that route's facet observed on the supplied "
          "closed form itself and separated from the narrower "
          "branch-comparison reading); no consumed axiom")
    return 0


if __name__ == "__main__":
    sys.exit(main())
