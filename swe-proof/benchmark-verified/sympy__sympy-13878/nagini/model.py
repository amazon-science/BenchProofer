"""Twin-artifact model for sympy__sympy-13878.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The cumulative distribution function of a continuous random variable is
  obtained by a two-stage dispatch:

    (1) When a default (no-option) cumulative query is made and the variable's
        family supplies a closed-form cumulative function, that exact closed
        form is the answer.
    (2) Otherwise the answer is produced by integrating the density from the
        family's lower support bound up to the query point.

  The families differ in whether stage (1) applies. For the family supported on
  a bounded interval whose density is the reciprocal of a square root over that
  interval (the family named for the inverse-sine function), the closed-form
  cumulative function IS available, and it is the inverse-sine expression:

        below the lower bound          -> the exact 0;
        on the support [low, high]     -> (2/pi) * asin(sqrt((x-low)/(high-low)));
        above the upper bound          -> the exact 1.

  For that family the default query therefore returns this three-branch
  inverse-sine closed form, NOT the integral of its density (which for this
  density does not evaluate to a finite closed form).

WHETHER a query hands a value back is a question separate from WHICH form its
answer has, and the two routes settle it on two DIFFERENT facts. The routes are
disjoint, and each one reads its own fact and only its own:

  * The closed-form route hands a value back exactly when the family's supplied
    closed form, assembled for this query point, comes back
    (`closed_form_returns`). Assembling it is bounded, loop-free work, but it is
    not unconditional: the three branches above are selected by comparing the
    query point against each support bound, and an ordering question the
    assembly cannot settle ends it with no value instead. This fact is neither
    guessed nor enumerated here -- it is OBSERVED on that supplied closed form
    itself, exactly as the integrating route's fact is observed on the
    integration.
  * The integrating route hands a value back exactly when the integration it
    needs comes back (`quadrature_returns`). Integration of an arbitrary density
    over an arbitrary support carries no such guarantee in general -- the public
    issue records queries that fail to converge, run without end, or end in an
    error instead of a value.

Both facts are carried as inputs and OBSERVED on the route's own callee, never
assumed and never reconstructed from a guess about how that callee works.
Delivery is not left to a proof obligation alone: `query_arrives` hands the
delivery verdict back AS A VALUE, pinned on every input, and pinned per route to
that route's own fact ALONE -- the closed-form route's arrival may not be made
to depend on the integration, and the integrating route's may not be made to
depend on the closed form. The result FORM is specified on every query; the
promise to arrive is claimed exactly where the query arrives.

The query option set, the distribution family, and the symbolic result are
modelled as discrete codes (Nagini has no symbolic-algebra type): the family is
an integer tag, the requested option set is a boolean (default vs. customised),
the two delivery facts are booleans, and the produced result is an integer code
naming one closed form (or the integral fallback). A concrete per-family map
(`closed_form_for`) carries WHICH result each family produces under a default
query; that the code-named inverse-sine closed form numerically EQUALS the
family's true cumulative function -- and that `closed_form_returns` is the real
facet the closed-form route's arrival turns on -- are the out-of-band
obligations checked by axiom_check.py (G-AX), not consumed axioms. The dispatch
(closed form when available, else the integral fallback), the family -> code
correspondence, and the per-route delivery verdict are what is verified here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# Result-form codes: a cumulative result is one of these distinct forms.
CF_INTEGRAL = 0     # the integral of the density from the lower bound up to x
                    # (the fallback when no closed form is supplied)
CF_ARCSIN = 1       # the inverse-sine three-branch closed form (see docstring)

# Distribution-family tags.
FAM_ARCSIN = 1      # bounded support, density = 1/(pi*sqrt((x-a)*(b-x)))
FAM_OTHER = 0       # any family without a supplied closed-form cumulative


# axioms-start
# (no consumed @ContractOnly axioms: the dispatch and the family -> result-form
# correspondence are concrete control flow modelled directly. WHICH closed form
# is correct for the inverse-sine family, and that `closed_form_returns` is the
# real fact the closed-form route's arrival turns on, are validated against the
# real family out-of-band by axiom_check.py / G-AX -- A-references, not consumed
# axioms; see refinement.md.)
# axioms-end


# pure-start
@Pure
def has_closed_form(fam: int) -> bool:
    """Whether the family supplies a closed-form cumulative function (so a
    default query can answer in closed form rather than by integration)."""
    return fam == FAM_ARCSIN


@Pure
def closed_form_for(fam: int, default_query: bool) -> int:
    """The result-form code a cumulative query produces for family `fam`.

    A default (no-option) query on a family that supplies a closed form returns
    that closed form; otherwise -- a customised query, OR a family with no
    supplied closed form -- the answer is the integral fallback.

    This map is concrete: it states only WHICH result form is produced. That the
    inverse-sine code names a closed form that EQUALS the family's true
    cumulative function is the G-AX obligation (axiom_check.py)."""
    if default_query and fam == FAM_ARCSIN:
        return CF_ARCSIN
    return CF_INTEGRAL


@Pure
def answers_from_closed_form(fam: int, default_query: bool) -> bool:
    """Whether the query is answered by consulting the supplied closed form
    rather than by integrating: a default (no-option) query on a family that
    supplies one."""
    return default_query and has_closed_form(fam)


@Pure
def closed_form_arrives(fam: int, default_query: bool,
                        closed_form_returns: bool) -> bool:
    """Whether the CLOSED-FORM route hands a value back.

    That route's whole work is assembling the family's supplied closed form for
    this query point, so it arrives exactly when that assembly comes back
    (`closed_form_returns`) -- and it never consults the integration, so its
    arrival is independent of `quadrature_returns` (which is why that input does
    not appear here)."""
    return answers_from_closed_form(fam, default_query) and closed_form_returns


@Pure
def query_delivers(fam: int, default_query: bool,
                   quadrature_returns: bool,
                   closed_form_returns: bool) -> bool:
    """Whether the query hands back a result at all.

    An exact per-route split, not a blanket claim: the route the dispatch takes
    decides which fact settles delivery, and each route reads only its own.
      * On the closed-form route delivery is `closed_form_returns`: assembling
        the family's supplied closed form for this query point is the work that
        route does, and an ordering question that assembly cannot settle ends it
        with no value.
      * Otherwise the query must integrate, and delivery is exactly whether that
        integration comes back -- a search with no guarantee in general (the
        public issue records such queries failing to converge, running without
        end, and ending in an error rather than a value)."""
    if answers_from_closed_form(fam, default_query):
        return closed_form_arrives(fam, default_query, closed_form_returns)
    return quadrature_returns
# pure-end


def cdf_result(fam: int, default_query: bool, quadrature_returns: bool,
               closed_form_returns: bool) -> int:
    # pre-conditions-start
    Requires(fam == FAM_ARCSIN or fam == FAM_OTHER)
    # TERMINATION, claimed exactly where the query hands back a result
    # (`query_delivers`). Under partial-correctness semantics a diverging body
    # (e.g. an endless loop before the return) satisfies every Ensures only
    # vacuously yet never answers the query; this obligation rejects any such
    # implementation. The measure 2 leaves room for the closed-form supplier
    # callee (which holds MustTerminate(1) < 2).
    #
    # The guard is the per-route split `query_delivers`, because the two routes
    # arrive on two different facts and the claim must track each:
    #   * on the closed-form route the dispatch is a guard, an availability
    #     probe and a return, so that route arrives exactly when the closed form
    #     it asks the family for comes back (`closed_form_returns`); or
    #   * the query must integrate, and it arrives exactly when the integration
    #     it needs comes back (`quadrature_returns`).
    # What is deliberately NOT claimed is delivery where the real query hands
    # nothing back: a query that must integrate and whose integration does not
    # come back (the public issue: failing to converge, running without end, or
    # ending in an error instead of a value), and a closed-form query whose
    # assembly the ordering cannot settle. Asserting delivery on either region
    # would demand a property the real query does not have. Nothing is left
    # unpinned by withholding it: `query_arrives` below states the delivery
    # verdict as a VALUE on every input, in both directions, so a rival can
    # neither over- nor under-claim its delivery region; and the result-form
    # clauses here bind every query including those two regions.
    Requires(Implies(query_delivers(fam, default_query, quadrature_returns,
                                    closed_form_returns),
                     MustTerminate(2)))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the form the dispatch selects: a default query on a
    # family with a closed-form cumulative returns that closed form; otherwise
    # the integral fallback.
    Ensures(Result() == closed_form_for(fam, default_query))
    # The inverse-sine family under a default query produces the inverse-sine
    # closed form -- NOT the integral fallback. This is the behaviour the test
    # demands.
    Ensures(Implies(default_query and fam == FAM_ARCSIN, Result() == CF_ARCSIN))
    Ensures(Implies(default_query and fam == FAM_ARCSIN, Result() != CF_INTEGRAL))
    # A family with no supplied closed form, or any customised query, falls back
    # to the integral.
    Ensures(Implies(not has_closed_form(fam), Result() == CF_INTEGRAL))
    Ensures(Implies(not default_query, Result() == CF_INTEGRAL))
    # (The first clause above pins Result() to a function of `fam` and
    # `default_query` ALONE, so the result FORM reads NEITHER delivery fact: a
    # rival may not make the form it hands back depend on whether the
    # integration comes back or on whether the closed form's assembly comes
    # back. Those two facts govern delivery only.)
    # post-conditions-end
    # impl-start
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end


def closed_form_for_family(fam: int, closed_form_returns: bool) -> int:
    # pre-conditions-start
    Requires(has_closed_form(fam))
    # TERMINATION of the closed-form supplier, claimed exactly where that
    # supplier hands a value back. Building the family's closed form is bounded,
    # loop-free work -- it selects among finitely many branches by comparing the
    # query point against each support bound -- so it never diverges; where that
    # assembly comes back it therefore arrives, and the strictly smaller measure
    # (1 < 2) lets the dispatch holding MustTerminate(2) invoke it without
    # leaking its own obligation. Where an ordering question the assembly cannot
    # settle stops it, the supplier hands nothing back, so delivery is not
    # claimed there; `query_arrives` pins that region as a value instead.
    Requires(Implies(closed_form_returns, MustTerminate(1)))
    # pre-conditions-end
    # post-conditions-start
    # The supplied closed-form cumulative for the inverse-sine family is the
    # inverse-sine three-branch expression (its concrete code). This holds on
    # every call, including one whose assembly the ordering cannot settle: the
    # FORM this family supplies is the inverse-sine one either way.
    Ensures(Result() == CF_ARCSIN)
    Ensures(Result() != CF_INTEGRAL)
    # post-conditions-end
    # impl-start
    return CF_ARCSIN
    # impl-end


def query_arrives(fam: int, default_query: bool, quadrature_returns: bool,
                  closed_form_returns: bool) -> bool:
    # pre-conditions-start
    Requires(fam == FAM_ARCSIN or fam == FAM_OTHER)
    # TERMINATION, claimed UNCONDITIONALLY. Settling WHETHER a query arrives is
    # bounded work on every input, including the two inputs on which the query
    # itself hands nothing back: the dispatch reads the option set and the
    # family's availability probe, and each route's own fact is then read
    # directly. So no input excuses a body that never answers this question.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # The delivery verdict, as a VALUE, on every input in the domain: an
    # observable a rival must compute, not a promise it may quietly decline.
    Ensures(Result() == query_delivers(fam, default_query, quadrature_returns,
                                      closed_form_returns))
    # PER-ROUTE, EACH ROUTE READING ONLY ITS OWN FACT. On the closed-form route
    # arrival is exactly `closed_form_returns` -- so a rival may not let it depend
    # on the integration, in either direction: not claim arrival because the
    # integration would come back, and not deny arrival because it would not.
    Ensures(Implies(answers_from_closed_form(fam, default_query),
                    Result() == closed_form_returns))
    # And on the integrating route arrival is exactly `quadrature_returns`, so a
    # rival may not let it depend on the closed form either.
    Ensures(Implies(not answers_from_closed_form(fam, default_query),
                    Result() == quadrature_returns))
    # The two edges of the closed-form route, stated separately so neither can
    # be dropped: the inverse-sine family's default query DOES arrive when the
    # closed form it asks for comes back (the cell the test exercises), and does
    # NOT when it does not.
    Ensures(Implies(default_query and fam == FAM_ARCSIN and closed_form_returns,
                    Result()))
    Ensures(Implies(default_query and fam == FAM_ARCSIN
                    and not closed_form_returns, not Result()))
    # post-conditions-end
    # impl-start
    if default_query:
        if has_closed_form(fam):
            return closed_form_returns
    return quadrature_returns
    # impl-end
