# properties.py — PBT falsification battery for sympy__sympy-13878. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes
# and stamps with RESULT. Each SPEC_TESTS case is a full model.py variant that
# shares the FROZEN spec exactly (markers.same_spec) and edits ONLY inside a
# # impl-start/# impl-end region; the runner re-runs the Nagini verifier on the
# host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md).
# THREE impl regions, so three attack surfaces:
#
#   cdf_result(fam: int, default_query: bool, quadrature_returns: bool,
#              closed_form_returns: bool) -> int
#     Requires(fam == FAM_ARCSIN or fam == FAM_OTHER)            # fam in {1, 0}
#     Requires(Implies(query_delivers(fam, default_query, quadrature_returns,
#                                     closed_form_returns),
#                      MustTerminate(2)))                         # (P0) totality,
#                        # claimed exactly where the query arrives (P0 note below)
#     Ensures(Result() == closed_form_for(fam, default_query))   # (P1) load-bearing
#     Ensures(Implies(default_query and fam==FAM_ARCSIN, Result()==CF_ARCSIN))   # (P2)
#     Ensures(Implies(default_query and fam==FAM_ARCSIN, Result()!=CF_INTEGRAL)) # (P3)
#     Ensures(Implies(not has_closed_form(fam), Result()==CF_INTEGRAL))          # (P4)
#     Ensures(Implies(not default_query, Result()==CF_INTEGRAL))                 # (P5)
#   closed_form_for_family(fam: int, closed_form_returns: bool) -> int
#     Requires(has_closed_form(fam))                             # fam == FAM_ARCSIN
#     Requires(Implies(closed_form_returns, MustTerminate(1)))       # (P0') totality of
#                        # the supplier, where its branch comparisons are admitted
#     Ensures(Result() == CF_ARCSIN); Ensures(Result() != CF_INTEGRAL)           # (P6)
#   query_arrives(fam: int, default_query: bool, quadrature_returns: bool,
#                 closed_form_returns: bool) -> bool
#     Requires(fam == FAM_ARCSIN or fam == FAM_OTHER)
#     Requires(MustTerminate(1))                                  # (P0'') UNCONDITIONAL
#     Ensures(Result() == query_delivers(fam, default_query, quadrature_returns,
#                                        closed_form_returns))       # (P7) load-bearing
#     Ensures(Implies(answers_from_closed_form(fam, default_query),
#                     Result() == closed_form_returns))              # (P8) route isolation
#     Ensures(Implies(not answers_from_closed_form(fam, default_query),
#                     Result() == quadrature_returns))            # (P9) route isolation
#     Ensures(Implies(default_query and fam == FAM_ARCSIN and closed_form_returns,
#                     Result()))                                  # (P10) arrival edge
#     Ensures(Implies(default_query and fam == FAM_ARCSIN
#                     and not closed_form_returns, not Result()))    # (P11) refusal edge
#   has_closed_form / closed_form_for / answers_from_closed_form /
#   closed_form_arrives / query_delivers are @Pure helpers fully UNFOLDED over
#   the args (no @ContractOnly axiom; the axioms region is empty).
#   query_delivers is the exact PER-ROUTE SPLIT: on the closed-form route
#   (answers_from_closed_form) it is closed_form_returns; otherwise it is
#   quadrature_returns.
#
# Codes: CF_INTEGRAL=0, CF_ARCSIN=1; FAM_ARCSIN=1, FAM_OTHER=0. The result FORM
# depends only on (fam, default_query) -- the two delivery facts
# (quadrature_returns, closed_form_returns) are read by the P0 guard and by
# query_arrives, never by the form -- so the result-form domain is the 4 pairs:
#   (FAM_ARCSIN, True ) -> closed_form_for = CF_ARCSIN   (the FIX / test_arcsin)
#   (FAM_ARCSIN, False) -> closed_form_for = CF_INTEGRAL (options query)
#   (FAM_OTHER , True ) -> closed_form_for = CF_INTEGRAL (no _cdf supplied)
#   (FAM_OTHER , False) -> closed_form_for = CF_INTEGRAL
# and the DELIVERY domain is those 4 pairs x the two delivery facts, split by
# route: the closed-form route reads closed_form_returns alone, the integrating
# route reads quadrature_returns alone.
#
# What the spec defends (load-bearing facts):
#   * (P1) Result() == closed_form_for(fam, default_query) pins the dispatch on
#     EVERY one of the 4 reachable inputs. closed_form_for is a @Pure function
#     fully unfolded over (fam, default_query) — a GROUNDED oracle, NOT an opaque
#     answer-key, so "return closed_form_for(fam, default_query)" is the CORRECT
#     answer (an honest cheapest impl, not a wrong echo). See `assessment` on the
#     ungrounded-oracle class being N/A here. It also pins the form to a function
#     of (fam, default_query) ALONE, so no rival may let the form it hands back
#     read a delivery fact (uniq-form-reads-order is that rival).
#   * (P2/P3) the discriminating clause: the inverse-sine family under a default
#     query MUST yield CF_ARCSIN, never CF_INTEGRAL. This is exactly the clause
#     model_prepatch.py violates (G-DIFF) and the F2P test_arcsin asserts.
#   * (P4/P5) a family with no supplied closed form, or any options query, falls
#     back to CF_INTEGRAL.
#   * (P7-P11) DELIVERY AS AN OBSERVABLE. Whether a cumulative query hands a
#     value back at all is not left to a proof obligation that a rival may
#     silently decline: query_arrives must COMPUTE the delivery verdict on every
#     input, and the verdict is pinned in both directions (an equality, P7), per
#     route to that route's own fact ALONE (P8/P9), and at both edges of the
#     route the F2P query travels (P10/P11). The two routes settle delivery on
#     two DIFFERENT facts and each reads only its own:
#       (a) the CLOSED-FORM route selects among the closed form's three branches
#           by comparing the query point against each support bound, so it hands
#           a value back exactly when the ordering admits those comparisons
#           (closed_form_returns). A magnitude that is not on the order line at all
#           -- a non-real quantity, an indeterminate, an unsigned infinity --
#           appearing as a support bound or as the query point makes such a
#           comparison one the ordering refuses, and the route then ends with no
#           value. Confirmed on the real post-patch family: a support bound or a
#           query point drawn from that region ends the query with no value,
#           while an unconstrained symbolic bound leaves the branch conditions
#           standing as conditions and the three-branch form comes back.
#       (b) the INTEGRATING route hands a value back exactly when the
#           integration it needs comes back (quadrature_returns) -- a search with
#           no guarantee in general (the public issue records such queries
#           failing to converge, running without end, and ending in an error
#           rather than a value; the real callee was run on that route and
#           confirmed: a support that is not a single interval ends in an error
#           before integrating, and several admissible integration options do
#           the same).
#     A rival that promises arrival everywhere (uniq-arrives-always-true), that
#     re-states the two grounds as a DISJUNCTION (uniq-arrives-old-disjunction),
#     that swaps the two routes' facts (uniq-arrives-swap-facts), that reads the
#     ordering fact on both routes (uniq-arrives-order-everywhere), or that
#     denies arrival on an integrating query that does come back
#     (uniq-arrives-deny-quadrature) is refused. So withholding the delivery
#     PROMISE on the region where the real query hands nothing back costs the
#     spec nothing: the delivery verdict itself is pinned there as a value.
#   * (P0/P0'/P0'') TOTALITY, CLAIMED EXACTLY WHERE THE QUERY ARRIVES.
#     Requires(MustTerminate) makes the Ensures a TOTAL-correctness claim:
#     without it Nagini's semantics are partial, so a same-spec impl that
#     DIVERGES (an endless loop, or unbounded self-recursion) satisfies every
#     postcondition vacuously and VERIFIES, yet its faithful real counterpart
#     hangs the query and resolves nothing (the G-PANEL-1 break the
#     uniq-nonterm-* cases pin). Measures: dispatch holds 2, the closed-form
#     supplier holds 1 < 2, so the gold call chain discharges.
#     The dispatch's guard is the PER-ROUTE SPLIT query_delivers(...), because
#     the two routes arrive on two different facts (above) and the claim must
#     track each. Naming only route (a) UNDER-claims and lets a rival hang a
#     query the repository really answers -- uniq-nonterm-quadrature-returns is
#     that rival, and it verified under the narrower guard. Claiming delivery
#     unconditionally OVER-claims on both routes: on (b) an integration that
#     does not come back, and on (a) branch comparisons the ordering refuses.
#     So delivery is withheld on exactly those two regions, and on NEITHER is
#     anything left unpinned (P7-P11 above). The supplier's guard (P0') is the
#     ordering fact alone, because building the family's closed form is the
#     bounded, loop-free work of making those comparisons and assembling the
#     branches. query_arrives' obligation (P0'') is UNCONDITIONAL: settling
#     WHETHER a query arrives is bounded work on every input, including the two
#     inputs on which the query itself hands nothing back.
#     uniq-nonterm-loop / uniq-nonterm-recursion / uniq-nonterm-closedform /
#     uniq-nonterm-quadrature-returns / uniq-nonterm-comparable /
#     uniq-cff-nonterm-comparable / uniq-arrives-nonterm-refused /
#     uniq-order-gates-all pin that divergence anywhere delivery IS promised
#     (incl. the F2P cell) is still rejected, so scoping the measures did not
#     reopen the G-PANEL-1 hole; pos-control-scope-boundary and
#     pos-control-cff-scope-boundary are the SOUND-side controls on the two
#     withheld regions (an impl that arrives everywhere the spec promises and
#     only there must verify).
#
# FRAME-MUTATION (the project's #1 weakness class): N/A here. All inputs are
# pass-by-value scalars (fam: int, default_query: bool, quadrature_returns:
# bool, closed_form_returns: bool); Nagini scalars carry no
# heap permission, so there is no Acc(...,1/2) read-only input to overwrite
# vacuously. has_readonly_input is False — see `assessment`. (The django-11179
# sibling battery documents the same scalar-input situation.)
from pathlib import Path

INSTANCE = "sympy__sympy-13878"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl regions (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec. There are THREE
# impl regions: cdf_result (the dispatch), closed_form_for_family (the closed
# form the family supplies) and query_arrives (the delivery verdict).
# ---------------------------------------------------------------------------
_CDF_IMPL_OLD = """    # impl-start
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

_CFF_IMPL_OLD = """    # impl-start
    return CF_ARCSIN
    # impl-end"""

_QA_IMPL_OLD = """    # impl-start
    if default_query:
        if has_closed_form(fam):
            return closed_form_returns
    return quadrature_returns
    # impl-end"""

assert _BASE.count(_CDF_IMPL_OLD) == 1
assert _BASE.count(_CFF_IMPL_OLD) == 1
assert _BASE.count(_QA_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls
# MUST verify (else SPEC-TOO-STRONG). All are straight-line (no loop / no fold)
# except the two scope-boundary controls, whose loop is the point.
# ===========================================================================

# pos-control-guard-reorder: invert the nesting into early-return guard clauses
# (handle the two fall-through cases first, take the closed-form branch last).
# Behaviourally identical to the gold nested form: returns closed_form_for_family
# (= CF_ARCSIN) exactly when default_query AND has_closed_form(fam), else
# CF_INTEGRAL. Must verify.
_POS_GUARD_REORDER = """    # impl-start
    if not default_query:
        return CF_INTEGRAL
    if not has_closed_form(fam):
        return CF_INTEGRAL
    return closed_form_for_family(fam, closed_form_returns)
    # impl-end"""

# pos-control-local-reshape: a different local-variable shape — bind the
# fall-through result in a typed local and the closed-form result in another, and
# return whichever the dispatch selects. Same dispatch, different executable
# shape. Must verify.
_POS_LOCAL_RESHAPE = """    # impl-start
    fallback = CF_INTEGRAL  # type: int
    if default_query and has_closed_form(fam):
        selected = closed_form_for_family(fam, closed_form_returns)  # type: int
        return selected
    return fallback
    # impl-end"""

# pos-control-cff-local: reshape closed_form_for_family to bind a typed local and
# return it (instead of returning the literal directly). Same value (CF_ARCSIN);
# must verify (else SPEC-TOO-STRONG on the closed-form supplier).
_POS_CFF_LOCAL = """    # impl-start
    form = CF_ARCSIN  # type: int
    return form
    # impl-end"""

# pos-control-arrives-grounded: settle the delivery verdict by evaluating the
# grounded @Pure split directly instead of re-deriving the route structure. Same
# value on every input (query_delivers IS the per-route split, fully unfolded
# over the args -- not an opaque answer-key), a structurally different impl.
# Must verify (else SPEC-TOO-STRONG on the delivery observable).
_POS_QA_GROUNDED = """    # impl-start
    return query_delivers(fam, default_query, quadrature_returns,
                          closed_form_returns)
    # impl-end"""

# pos-control-arrives-reshape: settle the delivery verdict by initialising a
# typed local to the integrating route's fact and overwriting it on the
# closed-form route (a single-assignment shape instead of nested returns). Same
# value everywhere; must verify.
_POS_QA_RESHAPE = """    # impl-start
    arrives = quadrature_returns  # type: bool
    if default_query and has_closed_form(fam):
        arrives = closed_form_returns
    return arrives
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (soundness/verify) — confirm the precondition admits a normal
# F2P-shaped input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller
# function: a new module-level def changes the projected spec view and breaks
# same_spec. Instead we inject the admissibility witness INSIDE an impl region
# (elided from the spec view), as a leading block that asserts the concrete
# F2P-shaped input (the inverse-sine family under a default query:
# fam == FAM_ARCSIN, default_query True) satisfies the function's exact Requires
# (fam == FAM_ARCSIN or fam == FAM_OTHER) AND the callee's Requires
# (has_closed_form(FAM_ARCSIN)) that the closed-form branch needs. The real impl
# then runs unchanged. If the precondition could not be established for this
# legitimate F2P input the Assert would fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for the F2P input (elided from the spec view) ---
    # test_arcsin queries cdf(Arcsin(...))(x) with no options: fam == FAM_ARCSIN,
    # default_query True. Confirm this F2P-shaped input satisfies the function's
    # Requires and that the closed-form callee's Requires is establishable for it.
    Assert(FAM_ARCSIN == FAM_ARCSIN or FAM_ARCSIN == FAM_OTHER)
    Assert(has_closed_form(FAM_ARCSIN))
    # The F2P query's support bounds and query point are ordinary reals, so the
    # closed form's branch comparisons are admitted and the query arrives: the
    # delivery guard is satisfiable on the very input the test exercises (an
    # excluding precondition would make this Assert fail).
    Assert(query_delivers(FAM_ARCSIN, True, False, True))
    # --- end admissibility witness; the real impl follows unchanged ---
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# A second admissibility witness, inside query_arrives: BOTH edges of the
# closed-form route must be admissible inputs, or the delivery observable would
# be pinned on a domain the spec has quietly excluded. Asserts that the verdict
# is settled (and settled OPPOSITELY) on the two F2P-shaped inputs -- ordinary
# real bounds and query point, and the same family with a bound the ordering
# refuses -- so neither edge is out of domain.
_ADMISS_QA = """    # impl-start
    # --- admissibility witness for both delivery edges (elided from the view) ---
    Assert(FAM_ARCSIN == FAM_ARCSIN or FAM_ARCSIN == FAM_OTHER)
    Assert(query_delivers(FAM_ARCSIN, True, False, True))
    Assert(not query_delivers(FAM_ARCSIN, True, True, False))
    # and the integrating route's two edges are admissible too
    Assert(query_delivers(FAM_OTHER, True, True, False))
    Assert(not query_delivers(FAM_OTHER, True, False, True))
    # --- end admissibility witness; the real impl follows unchanged ---
    if default_query:
        if has_closed_form(fam):
            return closed_form_returns
    return quadrature_returns
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain — rivals that share the spec exactly and change
# ONLY an impl region. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-prepatch-integral: THE BUG. Always return CF_INTEGRAL (the cdf_result
# region of model_prepatch.py). Correct on 3 of the 4 reachable inputs but WRONG
# on the discriminating one (FAM_ARCSIN, True), where closed_form_for =
# CF_ARCSIN. Rejected by P1 (and P2/P3) at the inverse-sine default query.
_UNIQ_PREPATCH = """    # impl-start
    return CF_INTEGRAL
    # impl-end"""

# uniq-ignore-default: take the closed-form branch whenever the family supplies
# one, IGNORING default_query. Correct on 3 of 4 inputs but WRONG on
# (FAM_ARCSIN, False): returns CF_ARCSIN where closed_form_for = CF_INTEGRAL.
# Rejected by P1 / P5 (a non-default query must fall back to the integral).
_UNIQ_IGNORE_DEFAULT = """    # impl-start
    if has_closed_form(fam):
        return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# uniq-always-arcsin: return CF_ARCSIN unconditionally. Correct only on
# (FAM_ARCSIN, True); WRONG on the other 3 (where closed_form_for = CF_INTEGRAL).
# Rejected by P1 / P4 / P5. closed_form_for_family is not even called.
_UNIQ_ALWAYS_ARCSIN = """    # impl-start
    return CF_ARCSIN
    # impl-end"""

# uniq-other-gets-closedform: a partial-domain swap on the FAMILY facet — give
# the closed-form branch to BOTH families under a default query (i.e. treat
# FAM_OTHER as if it had a closed form). But closed_form_for_family Requires
# has_closed_form(fam); for FAM_OTHER that precondition fails, so the call site
# is rejected (precondition violation) — equivalently P4 (a family with no closed
# form must return CF_INTEGRAL) is violated. Either way: reject.
_UNIQ_OTHER_CLOSEDFORM = """    # impl-start
    if default_query:
        return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# uniq-form-reads-order: make the result FORM read a DELIVERY fact — hand back
# the closed form only when the ordering admits its branch comparisons, and the
# integral fallback otherwise. The real dispatch does no such thing: which route
# it takes is settled by the option set and the family's availability probe
# alone, and where the branch comparisons are refused the query hands back NO
# value rather than a different form. Rejected by P1 (Result() is pinned to a
# function of (fam, default_query) alone) at (FAM_ARCSIN, True,
# closed_form_returns False).
_UNIQ_FORM_READS_ORDER = """    # impl-start
    if default_query:
        if has_closed_form(fam):
            if closed_form_returns:
                return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# uniq-nonterm-loop: DIVERGE instead of answering — an endless loop before the
# fall-through return. Under partial correctness every Ensures holds vacuously
# (this exact shape verified pre-repair: the recorded G-PANEL-1 atk_3 break).
# The MustTerminate(2) obligation is leaked by the unbounded loop, so Nagini's
# obligation leak check rejects it (total correctness).
_UNIQ_NONTERM_LOOP = """    # impl-start
    while default_query or not default_query:
        pass
    return CF_INTEGRAL
    # impl-end"""

# uniq-nonterm-recursion: diverge by unbounded SELF-recursion (no loop token at
# all). The callee needs MustTerminate(2) but the caller holds no measure
# strictly above 2, so the obligation cannot be discharged: rejected.
_UNIQ_NONTERM_RECURSION = """    # impl-start
    return cdf_result(fam, default_query, quadrature_returns, closed_form_returns)
    # impl-end"""

# uniq-nonterm-closedform: diverge EXACTLY on the closed-form route — the route
# the F2P cell (default query on the inverse-sine family) travels. This is the
# sharp test that scoping the obligation to the per-route split did NOT reopen
# the G-PANEL-1 vacuity hole: on that route the guard reduces to
# closed_form_returns, which is free to hold, so the obligation is live and the
# endless loop leaks it. A rival that hangs precisely on the query the issue is
# about must not verify. Corresponds to a real patch whose added closed-form
# supplier loops forever, so the inverse-sine query never returns and the F2P
# test never passes.
_UNIQ_NONTERM_CLOSEDFORM = """    # impl-start
    if default_query and has_closed_form(fam):
        while default_query or not default_query:
            pass
    return CF_INTEGRAL
    # impl-end"""

# uniq-nonterm-comparable: sharper still — diverge on the closed-form route only
# where the ordering DOES admit the branch comparisons, i.e. exactly the region
# the repaired guard still promises delivery for (and exactly the F2P cell:
# ordinary real bounds and query point). A rival that hangs there hangs the query
# the issue is about. If this verified, the repair would have bought its
# faithfulness by giving up the route that does deliver.
_UNIQ_NONTERM_COMPARABLE = """    # impl-start
    if default_query and has_closed_form(fam) and closed_form_returns:
        while default_query or not default_query:
            pass
    return CF_INTEGRAL
    # impl-end"""

# uniq-nonterm-quadrature-returns: diverge on EVERY route except the closed-form
# one -- including a query that must integrate but whose integration DOES come
# back (quadrature_returns True). That is a query the real callee answers: a
# single-interval support with benign options integrates and returns a value, so
# a rival that hangs there hangs a query that really does deliver. The spec's
# delivery guard is a per-route split for exactly this reason; this case is the
# control that the integrating route's fact is live and load-bearing. (A guard
# naming only the closed-form route admitted this rival -- it verified -- which
# is why the per-query delivery fact is carried explicitly.)
_UNIQ_NONTERM_QUAD = """    # impl-start
    if not (default_query and has_closed_form(fam)):
        while default_query or not default_query:
            pass
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# uniq-order-gates-all: smuggle the CLOSED-FORM route's fact into the
# INTEGRATING route's delivery obligation — hang whenever the ordering refuses
# the branch comparisons, on every route. On the integrating route the closed
# form is never consulted, so its branch comparisons are not performed and
# whether the ordering would admit them is nothing to do with that route's
# arrival: an integrating query whose integration comes back must still be
# answered. Rejected because the guard holds there (quadrature_returns True on a
# non-closed-form route) while the loop leaks the obligation. This is the
# route-isolation control on the OBLIGATION, the counterpart of P9 on the value.
_UNIQ_ORDER_GATES_ALL = """    # impl-start
    if not closed_form_returns:
        while default_query or not default_query:
            pass
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# uniq-cff-returns-integral: corrupt the closed-form SUPPLIER so it returns
# CF_INTEGRAL instead of CF_ARCSIN. This violates closed_form_for_family's own
# Ensures(Result() == CF_ARCSIN), and propagates: cdf_result on (FAM_ARCSIN,True)
# would then return CF_INTEGRAL, violating P2. Rejected at the supplier's
# postcondition. (Supporting partial-domain attack on the second impl region.)
_CFF_RETURNS_INTEGRAL = """    # impl-start
    return CF_INTEGRAL
    # impl-end"""

# uniq-cff-integral-when-refused: a BOUNDARY TOKEN SWAP on the supplier — supply
# the integral fallback instead of the family's closed form exactly where the
# ordering refuses the branch comparisons, keeping the closed form everywhere
# else. It looks like a faithful account of "no closed form comes back there",
# but the real code hands back NO value on that region rather than a DIFFERENT
# form, and the FORM this family supplies is the inverse-sine one on every call.
# Rejected by P6 (Ensures(Result() == CF_ARCSIN)) at closed_form_returns False.
_CFF_INTEGRAL_WHEN_REFUSED = """    # impl-start
    if not closed_form_returns:
        return CF_INTEGRAL
    return CF_ARCSIN
    # impl-end"""

# uniq-cff-nonterm-comparable: hang the SUPPLIER exactly where its branch
# comparisons ARE admitted -- the region where P0' still demands it arrive (and
# the F2P cell). Corresponds to a real added `_cdf` that loops forever while
# assembling the branches. Rejected: the guard closed_form_returns holds, so
# MustTerminate(1) is live and the loop leaks it.
_CFF_NONTERM_COMPARABLE = """    # impl-start
    if closed_form_returns:
        while closed_form_returns or not closed_form_returns:
            pass
    return CF_ARCSIN
    # impl-end"""

# uniq-arrives-always-true: OVER-APPROXIMATION on the delivery observable --
# claim every cumulative query hands a value back. Its faithful real counterpart
# reports success for a query that ends with no value at all (a support bound the
# ordering refuses; an integration that does not come back), so a caller that
# trusts it proceeds on a value it does not have. Rejected by P7 (the delivery
# equality) wherever the real query hands nothing back.
_UNIQ_QA_ALWAYS = """    # impl-start
    return True
    # impl-end"""

# uniq-arrives-old-disjunction: the delivery account as a DISJUNCTION -- the
# closed-form route always arrives, and otherwise arrival is the integration's.
# This is the exact over-approximation the faithfulness review refuted: on the
# real post-patch family the closed-form route ends with NO value whenever a
# support bound or the query point is a magnitude the ordering refuses (a
# non-real quantity, an indeterminate, an unsigned infinity), so the first
# disjunct over-claims. Rejected by P7/P8 at (FAM_ARCSIN, True,
# closed_form_returns False).
_UNIQ_QA_DISJUNCTION = """    # impl-start
    if default_query and has_closed_form(fam):
        return True
    return quadrature_returns
    # impl-end"""

# uniq-arrives-swap-facts: read the OTHER route's fact on each route -- the
# closed-form route's arrival taken from the integration, the integrating
# route's from the ordering. Each route's arrival is then settled by work that
# route does not do. Rejected by P8/P9 (route isolation, in both directions).
_UNIQ_QA_SWAP = """    # impl-start
    if default_query:
        if has_closed_form(fam):
            return quadrature_returns
    return closed_form_returns
    # impl-end"""

# uniq-arrives-order-everywhere: read the CLOSED-FORM route's fact on every
# route. On the integrating route the closed form is never consulted, so its
# branch comparisons are never performed: an integrating query whose integration
# comes back arrives regardless of them. Rejected by P9.
_UNIQ_QA_ORDER_EVERYWHERE = """    # impl-start
    return closed_form_returns
    # impl-end"""

# uniq-arrives-deny-quadrature: UNDER-claim -- deny arrival on every integrating
# query, keeping the closed-form route exact. Its faithful real counterpart
# reports failure for cumulative queries the repository answers with a value
# (every no-closed-form family whose density integrates), so a caller would
# abandon results it has. This is the direction a one-sided delivery claim would
# miss; P7 is an EQUALITY, so it is refused.
_UNIQ_QA_DENY_QUAD = """    # impl-start
    if default_query:
        if has_closed_form(fam):
            return closed_form_returns
    return False
    # impl-end"""

# uniq-arrives-nonterm-refused: exploit the freedom the repair might have left --
# the delivery observable itself DIVERGES on exactly the region where the query
# it reports on hands nothing back. If this verified, the repair would have moved
# the hole rather than closed it: the delivery verdict would be unpinned exactly
# where it was needed, and a real counterpart would hang while being asked
# whether a query answers. query_arrives' MustTerminate(1) is UNCONDITIONAL, so
# the loop leaks it and it is refused.
_UNIQ_QA_NONTERM_REFUSED = """    # impl-start
    if default_query and has_closed_form(fam) and not closed_form_returns:
        while default_query or not default_query:
            pass
    if default_query:
        if has_closed_form(fam):
            return closed_form_returns
    return quadrature_returns
    # impl-end"""

# pos-control-scope-boundary: the faithful counterpart of the real callee on the
# regions where the spec withholds the delivery promise -- and ONLY there. It
# fails to arrive exactly where query_delivers is false (an integrating query
# whose integration does not come back; a closed-form query whose branch
# comparisons the ordering refuses) and answers every other query with the
# selected result form. Its real counterpart is the repository behaviour itself
# (`compute_cdf` reading a support bound that is absent, an integration that
# raises or does not converge; and the ordering refusing a comparison against a
# non-real bound), and the sole F2P query has ordinary real bounds and travels
# the closed-form route, which it answers. It MUST verify: if it could not, the
# spec would be demanding delivery the real callee does not give
# (SPEC-TOO-STRONG, and the very unfaithfulness the guard exists to remove).
_POS_SCOPE_BOUNDARY = """    # impl-start
    if not query_delivers(fam, default_query, quadrature_returns,
                          closed_form_returns):
        while default_query or not default_query:
            pass
    if default_query:
        if has_closed_form(fam):
            return closed_form_for_family(fam, closed_form_returns)
    return CF_INTEGRAL
    # impl-end"""

# pos-control-cff-scope-boundary: the same boundary on the SUPPLIER. It fails to
# arrive exactly where the ordering refuses its branch comparisons -- the one
# region P0' withholds the promise on, and the region where the real family's
# `_cdf` hands nothing back -- and supplies the closed form everywhere else. MUST
# verify: the supplier's scoped measure has to admit its own faithful
# counterpart, or P0' would demand arrival the real `_cdf` does not give.
_POS_CFF_SCOPE_BOUNDARY = """    # impl-start
    if not closed_form_returns:
        while closed_form_returns or not closed_form_returns:
            pass
    return CF_ARCSIN
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-guard-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _POS_GUARD_REORDER),
        "rationale": "structurally-different CORRECT impl: invert the nested ifs "
                     "into early-return guard clauses (fall-through cases first, "
                     "closed-form branch last). Same dispatch: CF_ARCSIN iff "
                     "default_query AND has_closed_form(fam), else CF_INTEGRAL. "
                     "Straight-line, no loop/fold so no lemma is needed (pilot "
                     "pitfalls #2/#3 avoided). If a faithful correct impl cannot "
                     "verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _POS_LOCAL_RESHAPE),
        "rationale": "local-variable reshape: bind the fall-through and the "
                     "closed-form results in typed locals and return whichever the "
                     "dispatch selects. Behaviourally identical to the gold nested "
                     "form; must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-cff-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CFF_IMPL_OLD, _POS_CFF_LOCAL),
        "rationale": "reshape the closed-form supplier closed_form_for_family to "
                     "bind CF_ARCSIN in a typed local and return it (vs returning "
                     "the literal directly). Same value; must verify (else "
                     "SPEC-TOO-STRONG on the closed-form supplier).",
    },
    {
        "id": "pos-control-arrives-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _QA_IMPL_OLD, _POS_QA_GROUNDED),
        "rationale": "settle the delivery verdict by evaluating the grounded @Pure "
                     "per-route split directly rather than re-deriving the route "
                     "structure in the body. query_delivers is fully unfolded over "
                     "the args (a grounded oracle, not an opaque answer-key), so "
                     "this is an honest cheapest impl with the same value on every "
                     "input. Must verify (else SPEC-TOO-STRONG on the delivery "
                     "observable).",
    },
    {
        "id": "pos-control-arrives-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _QA_IMPL_OLD, _POS_QA_RESHAPE),
        "rationale": "single-assignment reshape of the delivery observable: "
                     "initialise a typed local to the integrating route's fact and "
                     "overwrite it on the closed-form route. Same value everywhere; "
                     "must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-scope-boundary",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _POS_SCOPE_BOUNDARY),
        "rationale": "the boundary of the delivery guard, from the SOUND side: an "
                     "impl that answers every query the spec promises delivery for "
                     "and only fails to arrive where the spec (and the real callee) "
                     "promises nothing -- an integrating query whose integration "
                     "does not come back, and a closed-form query whose branch "
                     "comparisons the ordering refuses. Its real counterpart is the "
                     "repository behaviour itself, and the F2P query has ordinary "
                     "real bounds and travels the closed-form route it answers. If "
                     "this were rejected the spec would demand delivery the real "
                     "callee does not give => SPEC-TOO-STRONG (and unfaithful).",
    },
    {
        "id": "pos-control-cff-scope-boundary",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CFF_IMPL_OLD, _POS_CFF_SCOPE_BOUNDARY),
        "rationale": "the same boundary on the closed-form SUPPLIER: it arrives "
                     "wherever its branch comparisons are admitted and only fails "
                     "to arrive where the ordering refuses them -- exactly the "
                     "region the real family's `_cdf` hands nothing back on. The "
                     "supplier's scoped measure must admit its own faithful "
                     "counterpart, else P0' demands arrival the real `_cdf` does "
                     "not give => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-arcsin-default",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the cdf_result impl "
                     "region (elided from the spec view, so same_spec holds) asserts "
                     "the F2P input (the inverse-sine family under a default query: "
                     "fam == FAM_ARCSIN, default_query True) satisfies the function's "
                     "Requires (fam in {FAM_ARCSIN, FAM_OTHER}), that the "
                     "closed-form callee's Requires has_closed_form(FAM_ARCSIN) is "
                     "establishable, and that the DELIVERY guard is satisfiable on "
                     "that same input (its bounds and query point are ordinary "
                     "reals, so the branch comparisons are admitted). The real impl "
                     "then runs unchanged. If the precondition could not be "
                     "established for this legitimate F2P input the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-both-delivery-edges",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _QA_IMPL_OLD, _ADMISS_QA),
        "rationale": "the delivery observable is pinned on both edges of BOTH "
                     "routes, so both edges must be admissible inputs or the "
                     "pinning would be over a domain quietly excluded. A witness "
                     "inside the query_arrives impl region asserts the verdict is "
                     "settled -- and settled OPPOSITELY -- on the closed-form "
                     "route's two edges (ordinary real bounds and query point vs. a "
                     "magnitude the ordering refuses) and on the integrating "
                     "route's two edges. If any Assert failed, the precondition "
                     "would be excluding a region the spec claims to bind => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-prepatch-integral",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_PREPATCH),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces "
                      "and G-DIFF flags: at base_commit ArcsinDistribution has no "
                      "_cdf, so the inherited _cdf returns None and the default query "
                      "falls through to compute_cdf, integrating the density "
                      "1/(pi*sqrt((x-a)*(b-x))) into the unevaluated, non-convergent "
                      "Integral(1/sqrt(-_x**2 + 3*_x), (_x, -oo, 1))/pi the issue "
                      "reports. The sole F2P test_arcsin asserts cdf(Arcsin('x',a,b))(x)"
                      " == the inverse-sine Piecewise; with the closed form never "
                      "supplied the assertion fails. Its faithful real patch (the "
                      "un-patched ArcsinDistribution with no _cdf) is exactly what "
                      "does NOT resolve.",
        "rationale": "rejected by P1 (Result() == closed_form_for(fam, default_query))"
                     " and P2/P3 at the input (FAM_ARCSIN, True): closed_form_for is "
                     "CF_ARCSIN there but the impl returns CF_INTEGRAL.",
    },
    {
        "id": "uniq-ignore-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_IGNORE_DEFAULT),
        "refinement": "taking the closed-form branch whenever _cdf is supplied, "
                      "ignoring whether the query is the default, corresponds to a "
                      "patch that dropped the `if len(kwargs)==0` guard in the "
                      "unchanged dispatch (crv.py:216) and consulted _cdf even for an "
                      "options query. The real dispatch must route an options query "
                      "through compute_cdf(**kwargs)(x) (so options like the "
                      "integration variable take effect); returning the bare closed "
                      "form for an options query changes that behaviour and would not "
                      "faithfully resolve (the dispatch's options path is observed by "
                      "the broader cdf API the P2P suite exercises).",
        "rationale": "rejected by P1 / P5 at (FAM_ARCSIN, False): the impl returns "
                     "CF_ARCSIN but closed_form_for(FAM_ARCSIN, False) == CF_INTEGRAL "
                     "(a non-default query must fall back to the integral).",
    },
    {
        "id": "uniq-always-arcsin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_ALWAYS_ARCSIN),
        "refinement": "returning the inverse-sine closed form for EVERY family and "
                      "EVERY query corresponds to a patch that returned the arcsin "
                      "Piecewise unconditionally (ignoring both the family's _cdf and "
                      "the option set). It would surface the arcsin CDF for families "
                      "that have a different (or no) closed form and for options "
                      "queries — wrong on every non-arcsin/non-default case, breaking "
                      "the P2P cdf tests of other families. It does not resolve.",
        "rationale": "rejected by P1 / P4 / P5 on the 3 inputs other than "
                     "(FAM_ARCSIN, True): closed_form_for there is CF_INTEGRAL but the "
                     "impl returns CF_ARCSIN (and P4 demands CF_INTEGRAL for a family "
                     "with no closed form).",
    },
    {
        "id": "uniq-other-gets-closedform",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_OTHER_CLOSEDFORM),
        "refinement": "granting the closed-form branch to ANY family under a default "
                      "query (treating FAM_OTHER as if it supplied a closed form) "
                      "corresponds to a patch that returned a precomputed closed form "
                      "for a family whose real _cdf is the base-class None — it would "
                      "fabricate a closed form where the real dispatch integrates, "
                      "diverging from the real cdf of every no-_cdf family (the P2P "
                      "control families). It does not resolve.",
        "rationale": "rejected at the call site closed_form_for_family(fam, "
                     "closed_form_returns): its Requires(has_closed_form(fam)) cannot be "
                     "established for fam == FAM_OTHER (default_query True), so the "
                     "precondition check fails — equivalently P4 (not "
                     "has_closed_form(fam) => CF_INTEGRAL) is violated.",
    },
    {
        "id": "uniq-form-reads-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_FORM_READS_ORDER),
        "refinement": "letting the result FORM read a delivery fact corresponds to a "
                      "patch whose dispatch chose the integral fallback whenever the "
                      "closed form's branch comparisons could not be made -- i.e. a "
                      "dispatch that consults `_cdf`, catches the ordering's refusal, "
                      "and integrates instead. The real dispatch (crv.py:216-220) "
                      "selects its route from the option set and `_cdf is not None` "
                      "alone and catches nothing: on that region the query ends with "
                      "NO value, it does not come back with a different form. Such a "
                      "patch would hand back an unevaluated non-convergent Integral "
                      "where the repository raises, and it changes the modeled "
                      "dispatch, so it does not faithfully resolve.",
        "rationale": "rejected by P1: Result() is pinned to closed_form_for(fam, "
                     "default_query), a function of the family and the option set "
                     "ALONE, so at (FAM_ARCSIN, True) with closed_form_returns False the "
                     "impl's CF_INTEGRAL contradicts the required CF_ARCSIN "
                     "(also P2/P3).",
    },
    {
        "id": "uniq-nonterm-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_NONTERM_LOOP),
        "refinement": "a same-spec impl that never answers corresponds to a patch "
                      "whose cdf dispatch hangs (e.g. an added _cdf that loops "
                      "forever): cdf(Arcsin(...))(x) never returns, test_arcsin "
                      "times out / never passes, so it does not resolve. Before "
                      "the MustTerminate repair this exact vacuous-divergence "
                      "shape VERIFIED (the recorded G-PANEL-1 atk_3 break: every "
                      "Ensures holds vacuously under partial correctness).",
        "rationale": "rejected by the P0 totality obligation: the unbounded loop "
                     "leaks the caller's MustTerminate(2) obligation (Nagini "
                     "obligation leak check: 'Loop might not take all unsatisfied "
                     "obligations from the context').",
    },
    {
        "id": "uniq-nonterm-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_NONTERM_RECURSION),
        "refinement": "divergence via unbounded self-recursion (no loop construct); "
                      "same real-world shape as uniq-nonterm-loop — a dispatch that "
                      "never delivers the cumulative result cannot resolve.",
        "rationale": "rejected by the P0 totality obligation: the self-call needs "
                     "MustTerminate(2) but the caller holds no strictly larger "
                     "measure ('Callee cdf_result might not take all unsatisfied "
                     "obligations from the caller').",
    },
    {
        "id": "uniq-nonterm-closedform",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_NONTERM_CLOSEDFORM),
        "refinement": "a rival that hangs EXACTLY on the closed-form route — the "
                      "route the F2P cell travels (default query on the inverse-sine "
                      "family). Corresponds to a real patch whose added closed-form "
                      "supplier loops forever: cdf(Arcsin(...))(x) never returns, so "
                      "test_arcsin never passes and it does not resolve. This is the "
                      "sharp control on the SCOPED totality obligation — on that "
                      "route the per-route split reduces to closed_form_returns, which "
                      "is free to hold, so the measure is live and vacuous "
                      "divergence is still refused. (Splitting the obligation per "
                      "route was the faithfulness repair: neither route delivers "
                      "unconditionally in the real callee. This case proves the "
                      "repair did not weaken the route the test travels.)",
        "rationale": "rejected by the P0 totality obligation on the closed-form "
                     "route: with closed_form_returns True the guard holds, so the "
                     "unbounded loop leaks the caller's MustTerminate(2) ('Loop "
                     "might not take all unsatisfied obligations from the "
                     "context').",
    },
    {
        "id": "uniq-nonterm-comparable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_NONTERM_COMPARABLE),
        "refinement": "sharper than uniq-nonterm-closedform: hang the closed-form "
                      "route only where the ordering DOES admit its branch "
                      "comparisons -- precisely the region the spec still promises "
                      "delivery on, and precisely the F2P cell (real bounds, real "
                      "query point). Its real counterpart answers the queries whose "
                      "magnitudes the ordering refuses (by ending with no value) and "
                      "hangs the ones it can compare -- the exact inverse of the "
                      "repository. It cannot resolve.",
        "rationale": "rejected by the P0 totality obligation: on this region the "
                     "per-route split is closed_form_returns and it holds, so "
                     "MustTerminate(2) is live and the unbounded loop leaks it.",
    },
    {
        "id": "uniq-nonterm-quadrature-returns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_NONTERM_QUAD),
        "refinement": "a rival that hangs on every route except the closed-form one, "
                      "including a query that integrates and whose integration DOES "
                      "come back -- e.g. a single-interval support with no options, "
                      "which the real callee answers with a value. Its faithful real "
                      "counterpart hangs cumulative queries the repository answers, "
                      "so the P2P cdf tests of the no-closed-form families never "
                      "return and it does not resolve. This is the control on the "
                      "integrating route's fact: a guard naming only the closed-form "
                      "route admitted exactly this rival.",
        "rationale": "rejected by the P0 totality obligation: with quadrature_returns "
                     "True on a route that integrates, the guard query_delivers(...) "
                     "holds, so MustTerminate(2) is live and the unbounded loop leaks "
                     "it ('Loop might not take all unsatisfied obligations from the "
                     "context').",
    },
    {
        "id": "uniq-order-gates-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CDF_IMPL_OLD, _UNIQ_ORDER_GATES_ALL),
        "refinement": "smuggle the closed-form route's fact into the INTEGRATING "
                      "route's delivery obligation: hang whenever the ordering "
                      "refuses the branch comparisons, on every route. Its real "
                      "counterpart hangs an ordinary integrating query -- a "
                      "no-closed-form family whose density integrates to a value -- "
                      "merely because that query's magnitudes are ones the closed "
                      "form's comparisons (never performed on that route) would have "
                      "refused. It hangs queries the repository answers, so it does "
                      "not resolve. This is the route-isolation control on the "
                      "OBLIGATION side, the counterpart of P9 on the value side.",
        "rationale": "rejected by the P0 totality obligation: on an integrating "
                     "query with quadrature_returns True the guard holds regardless "
                     "of closed_form_returns, so MustTerminate(2) is live and the "
                     "unbounded loop leaks it.",
    },
    {
        "id": "uniq-cff-returns-integral",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CFF_IMPL_OLD, _CFF_RETURNS_INTEGRAL),
        "refinement": "corrupting the closed-form SUPPLIER so it yields the integral "
                      "fallback corresponds to a patch whose added ArcsinDistribution."
                      "_cdf returned something equivalent to None / the integral "
                      "rather than the inverse-sine Piecewise — i.e. the arcsin family "
                      "still has no closed form. cdf(Arcsin(...))(x) would then "
                      "still produce the failing Integral, so test_arcsin fails. It "
                      "does not resolve. (Partial-domain attack on the second impl "
                      "region.)",
        "rationale": "rejected by closed_form_for_family's own Ensures(Result() == "
                     "CF_ARCSIN) and Ensures(Result() != CF_INTEGRAL); it returns "
                     "CF_INTEGRAL.",
    },
    {
        "id": "uniq-cff-integral-when-refused",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CFF_IMPL_OLD, _CFF_INTEGRAL_WHEN_REFUSED),
        "refinement": "a BOUNDARY TOKEN SWAP on the supplier: hand back the integral "
                      "fallback instead of the family's closed form exactly where "
                      "the ordering refuses the branch comparisons. It mimics a "
                      "faithful account of that region but states the wrong thing "
                      "about it -- the real `_cdf` there hands back NO value, it does "
                      "not hand back a different form, and the form this family "
                      "supplies is the inverse-sine one on every call. Its real "
                      "counterpart is an added `_cdf` that silently degrades to the "
                      "non-convergent Integral on some inputs, which the repository "
                      "does not do.",
        "rationale": "rejected by P6 (Ensures(Result() == CF_ARCSIN), Ensures(Result()"
                     " != CF_INTEGRAL)) at closed_form_returns False.",
    },
    {
        "id": "uniq-cff-nonterm-comparable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CFF_IMPL_OLD, _CFF_NONTERM_COMPARABLE),
        "refinement": "hang the SUPPLIER exactly where its branch comparisons ARE "
                      "admitted -- the region P0' still demands arrival on, and the "
                      "F2P cell. Corresponds to a real added `_cdf` that loops "
                      "forever while assembling its branches: cdf(Arcsin(...))(x) "
                      "never returns and test_arcsin never passes.",
        "rationale": "rejected by the P0' totality obligation: the guard "
                     "closed_form_returns holds, so MustTerminate(1) is live and the "
                     "unbounded loop leaks it.",
    },
    {
        "id": "uniq-arrives-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QA_IMPL_OLD, _UNIQ_QA_ALWAYS),
        "refinement": "OVER-APPROXIMATION of the delivery observable: report that "
                      "every cumulative query hands a value back. Its faithful real "
                      "counterpart reports success for queries that end with no "
                      "value at all -- a support bound or query point the ordering "
                      "refuses on the closed-form route, an integration that does "
                      "not come back on the other -- so a caller proceeds on a value "
                      "it does not have. Both regions are real, observed on the "
                      "post-patch repository.",
        "rationale": "rejected by P7 (Result() == query_delivers(...)) wherever the "
                     "real query hands nothing back, e.g. (FAM_ARCSIN, True, "
                     "closed_form_returns False) and (FAM_OTHER, True, "
                     "quadrature_returns False).",
    },
    {
        "id": "uniq-arrives-old-disjunction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QA_IMPL_OLD, _UNIQ_QA_DISJUNCTION),
        "refinement": "the delivery account as a DISJUNCTION -- the closed-form route "
                      "always arrives, else it is the integration's business. This is "
                      "exactly the over-approximation the faithfulness review "
                      "refuted, and the reason the delivery observable is a per-route "
                      "split: on the post-patch family the closed-form route ends "
                      "with NO value whenever a support bound or the query point is a "
                      "magnitude the ordering refuses (a non-real quantity, an "
                      "indeterminate, an unsigned infinity), which was confirmed "
                      "against the real code. A rival holding this account promises "
                      "arrival on a region the repository does not deliver on.",
        "rationale": "rejected by P7/P8 at (FAM_ARCSIN, True) with closed_form_returns "
                     "False: the impl returns True but query_delivers is False and P8 "
                     "pins the closed-form route's verdict to closed_form_returns.",
    },
    {
        "id": "uniq-arrives-swap-facts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QA_IMPL_OLD, _UNIQ_QA_SWAP),
        "refinement": "read the OTHER route's fact on each route: settle the "
                      "closed-form route's arrival by the integration and the "
                      "integrating route's by the ordering. Each route's arrival is "
                      "then decided by work that route never does -- the closed-form "
                      "route never integrates (crv.py:216-219 returns before "
                      "crv.py:220) and the integrating route never evaluates the "
                      "closed form's branch conditions. A boundary token swap of the "
                      "two delivery facts.",
        "rationale": "rejected by P8/P9 (route isolation): on the closed-form route "
                      "the verdict must equal closed_form_returns and on the "
                      "integrating route quadrature_returns; the impl has them the "
                      "other way round.",
    },
    {
        "id": "uniq-arrives-order-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QA_IMPL_OLD, _UNIQ_QA_ORDER_EVERYWHERE),
        "refinement": "read the closed-form route's fact on EVERY route -- a "
                      "partial-domain guard that happens to be right on the "
                      "closed-form route and wrong on the integrating one. On that "
                      "route the closed form is never consulted, so its branch "
                      "comparisons are never performed: an integrating query whose "
                      "integration comes back arrives regardless of them, and one "
                      "whose integration does not come back fails to arrive even "
                      "where they would be admitted.",
        "rationale": "rejected by P9: on the integrating route the verdict must equal "
                     "quadrature_returns, and the impl returns closed_form_returns "
                     "instead.",
    },
    {
        "id": "uniq-arrives-deny-quadrature",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QA_IMPL_OLD, _UNIQ_QA_DENY_QUAD),
        "refinement": "the UNDER-claiming direction: deny arrival on every "
                      "integrating query while keeping the closed-form route exact. "
                      "Its faithful real counterpart reports failure for cumulative "
                      "queries the repository answers with a value -- every "
                      "no-closed-form family whose density integrates, which the P2P "
                      "cdf tests exercise -- so a caller abandons results it has. A "
                      "one-directional delivery claim would miss this; the spec's "
                      "delivery clause is an EQUALITY for exactly this reason.",
        "rationale": "rejected by P7/P9 at (FAM_OTHER, True, quadrature_returns "
                     "True): query_delivers is True there but the impl returns "
                     "False.",
    },
    {
        "id": "uniq-arrives-nonterm-refused",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QA_IMPL_OLD, _UNIQ_QA_NONTERM_REFUSED),
        "refinement": "the attack that exploits the freedom the repair could have "
                      "left: let the DELIVERY OBSERVABLE ITSELF diverge on exactly "
                      "the region where the query it reports on hands nothing back. "
                      "If this verified, the repair would have moved the hole rather "
                      "than closed it -- the verdict would be unpinned precisely "
                      "where it is needed, and a real counterpart would hang while "
                      "being asked whether a query answers, which is strictly worse "
                      "than the query not answering. query_arrives' obligation is "
                      "UNCONDITIONAL for this reason: settling WHETHER a query "
                      "arrives is bounded work on every input.",
        "rationale": "rejected by the P0'' totality obligation: MustTerminate(1) is "
                     "held unconditionally, so the unbounded loop leaks it ('Loop "
                     "might not take all unsatisfied obligations from the "
                     "context').",
    },
]


# ===========================================================================
# AXIOM LANE — no @ContractOnly consumed axiom (the axioms region is empty), but
# the dispatch + inverse-sine closed form are a DEEP MODEL validated == the real
# sympy cdf/_cdf out-of-band (an A-reference; meta.deep_model_references, G-AX).
# We re-run that grounding here under PBT: the same checks axiom_check.py makes,
# executed against the REAL post-patch sympy in the instance image. The runner
# mounts ONLY the probe at /work, so we CANNOT import the bundle's axiom_check.py
# in-container — but its logic imports only sympy (present in the image). We embed
# the bundle's axiom_check.py source on the HOST at load time and exec it in the
# probe, so the PBT soundness probe IS the bundle's own grounding, re-validated.
# Probes MUST run on the post-patch worktree (apply_gold=True): the A-reference
# models the FIXED behaviour; at base_commit it correctly fails (ArcsinDistribution
# ._cdf is None there).
# ===========================================================================

# ax-ref-soundness: the deep model must equal the real callee on every input it
# distinguishes. Embed and run axiom_check.py's main() verbatim against the real
# sympy: it asserts (1) has_closed_form mirrors `_cdf is not None` (arcsin family
# vs Benini control), (2) the default arcsin query takes the closed-form branch
# (no Integral) while a no-_cdf family / options query takes the integral branch
# (identified by the dispatch FACET, not a value proxy), (3) CF_ARCSIN equals
# the exact three-branch inverse-sine Piecewise test_arcsin asserts and its
# derivative on the support equals the density, and (4) the per-route delivery
# facts name the real facets: the closed form's branch conditions ARE the
# comparisons of the query point against each support bound (read off the real
# expression), and the model's per-route delivery verdict equals the real
# dispatch's on a table of concrete instantiations reaching BOTH edges of the
# closed-form route. Any disagreement => the deep model is unsound (the
# A-reference grounding fails). exit 0 iff all hold.
_AX_REF_SOUNDNESS_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# --- embedded bundle axiom_check.py (the A-reference grounding) ---\n"
    + _AXIOM_CHECK_SRC
)

# ax-ref-containment: the model can only ever reach the 4 dispatch inputs
# (FAM in {FAM_ARCSIN, FAM_OTHER}) x (default_query in {True, False}), each
# crossed with the two delivery facts. Each maps to a real dispatch FACET:
# FAM_ARCSIN <-> a family whose _cdf is not None, FAM_OTHER <-> a family whose
# _cdf is the base-class None; default_query <-> len(kwargs)==0;
# closed_form_returns <-> the ordering admitting the closed form's branch
# comparisons; quadrature_returns <-> the integration coming back. This probe
# enumerates EXACTLY those reachable inputs and confirms each lies in the real
# dispatch's domain: the real ArcsinDistribution._cdf is not None and a control
# family's (Benini) _cdf is None, so the model's `fam` facet is realizable for
# both tags; the model's classification (closed_form_for) matches the real
# dispatch's branch selection on each; and BOTH values of the ordering facet are
# realizable on the real inverse-sine family (a real bound pair and one drawn
# from the region the ordering refuses), so no reachable delivery input is
# fictional. A reachable input the real dispatch could not realize => the deep
# model reaches outside what it claims to model (AXIOM-TOO-WEAK-FOR-CALLER
# analogue for an A-reference).
_AX_REF_CONTAINMENT_PROBE = r'''# -*- coding: utf-8 -*-
import sys

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

def model_query_delivers(fam, default_query, quadrature_returns,
                         closed_form_returns):
    if default_query and model_has_closed_form(fam):
        return closed_form_returns
    return quadrature_returns

def main():
    from sympy import Symbol, Integral, Dummy, S, I
    from sympy.stats import Arcsin, Benini, cdf
    from sympy.stats.crv import SingleContinuousDistribution
    from sympy.stats.crv_types import ArcsinDistribution

    a = Symbol("a", real=True)
    b = Symbol("b", real=True)
    x = Symbol("x")
    t = Dummy("t", real=True, finite=True)

    # The two real families the model's `fam` tag abstracts:
    #   FAM_ARCSIN  <-> a family whose _cdf is supplied (not None) post-patch
    #   FAM_OTHER   <-> a family whose _cdf is the base-class None (Benini control)
    arcsin_dist = Arcsin("x", a, b).pspace.distribution
    benini_dist = Benini("y", 1, 1, 1).pspace.distribution

    real_facet = {
        FAM_ARCSIN: arcsin_dist._cdf(t) is not None,
        FAM_OTHER:  benini_dist._cdf(t) is not None,
    }

    # Containment: every reachable model input (fam, default_query) corresponds to
    # a realizable real dispatch facet, and the model's classification matches the
    # real dispatch branch selection. Enumerate ALL 4 reachable inputs.
    reached = []
    for fam in (FAM_ARCSIN, FAM_OTHER):
        # the model's `fam` facet must be realizable by a real family's _cdf state
        assert model_has_closed_form(fam) == real_facet[fam], (
            "AXIOM-TOO-WEAK-FOR-CALLER: model fam=%r claims has_closed_form=%r but "
            "no real family realizes that _cdf-is-not-None facet (real=%r)"
            % (fam, model_has_closed_form(fam), real_facet[fam]))
        for default_query in (True, False):
            want_closed = (default_query and fam == FAM_ARCSIN)
            assert (model_closed_form_for(fam, default_query) == CF_ARCSIN) == want_closed, (
                "model classification self-inconsistent at (fam=%r, default=%r)"
                % (fam, default_query))
            reached.append((fam, default_query))

    # The ONE input where the model claims the closed-form branch (FAM_ARCSIN,
    # default) must be realizable by the real default arcsin query taking that
    # branch (result carries no unevaluated Integral). This is the only reachable
    # input outside the integral fallback; confirm it is inside the real dispatch's
    # closed-form domain (else the deep model reaches a branch the real code does
    # not).
    arcsin_default = cdf(Arcsin("x", a, b))(x)
    assert not arcsin_default.has(Integral), (
        "AXIOM-TOO-WEAK-FOR-CALLER: the model's closed-form-branch input "
        "(FAM_ARCSIN, default) is NOT realizable by the real dispatch (its default "
        "arcsin query still carries an Integral): %r" % (arcsin_default,))

    # BOTH values of the ordering facet must be realizable on the real
    # inverse-sine family, or the model would reach a delivery input the real
    # code cannot present. Observed independently of the dispatch, by performing
    # the closed form's own branch comparisons.
    def closed_form_returns(dist, q):
        try:
            q < dist.a
            q <= dist.b
        except Exception:
            return False
        return True

    def delivers(dist, q):
        try:
            dist.cdf(q)
        except Exception:
            return False
        return True

    realized = {}
    for label, lo, hi, q in [("real bounds", S.Zero, S.One, x),
                             ("non-real lower bound", I, S.One, x),
                             ("non-real query point", S.Zero, S.One, I)]:
        d = ArcsinDistribution(lo, hi)
        assert (type(d)._cdf is not SingleContinuousDistribution._cdf) == \
            model_has_closed_form(FAM_ARCSIN), (
            "%s: the family's closed-form-supplied facet is not what the model "
            "claims" % (label,))
        oc = closed_form_returns(d, q)
        realized.setdefault(oc, label)
        # and the model's delivery verdict for that realized facet matches
        assert model_query_delivers(FAM_ARCSIN, True, False, oc) == \
            delivers(d, q), (
            "%s: model delivery verdict != real dispatch (closed_form_returns=%r)"
            % (label, oc))
    assert True in realized and False in realized, (
        "AXIOM-TOO-WEAK-FOR-CALLER: the ordering facet is not realizable in both "
        "directions on the real family, so a reachable delivery input is "
        "fictional: %r" % (realized,))

    print("AXIOM-CONTAINMENT OK: all %d reachable dispatch inputs "
          "((fam in {ARCSIN, OTHER}) x (default in {T,F})) map to a realizable real "
          "_cdf facet (arcsin _cdf is not None, Benini _cdf is None) and the model's "
          "branch selection matches the real dispatch; the closed-form-branch input "
          "is realized by the real default arcsin query (no Integral); and both "
          "values of the ordering facet are realizable on the real family (%r), the "
          "model's per-route delivery verdict matching the real dispatch on each. No "
          "reachable input lies outside the modeled dispatch."
          % (len(reached), realized))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-ref-soundness",
        "axiom": "cdf_result-dispatch-Aref",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the A-reference models the FIXED behaviour
        "probe": _AX_REF_SOUNDNESS_PROBE,
        "rationale": "the dispatch + inverse-sine closed form + the per-route "
                     "delivery facts are a deep A-reference (no consumed axiom). "
                     "This re-runs the bundle's own axiom_check.py grounding against "
                     "the REAL post-patch sympy: has_closed_form mirrors `_cdf is "
                     "not None` (arcsin vs Benini control), the default arcsin query "
                     "takes the closed-form branch (no Integral) while no-_cdf / "
                     "options queries take the integral branch (by dispatch facet, "
                     "not a value proxy), CF_ARCSIN equals the exact Piecewise "
                     "test_arcsin asserts and integrates to the density, and the "
                     "closed form's branch conditions ARE the comparisons of the "
                     "query point against each support bound, with the model's "
                     "per-route delivery verdict matching the real dispatch on both "
                     "edges of that route. If the real callee disagrees => the "
                     "A-reference grounding is unsound (AXIOM-UNSOUND analogue).",
    },
    {
        "id": "ax-ref-containment",
        "axiom": "cdf_result-dispatch-Aref",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_REF_CONTAINMENT_PROBE,
        "rationale": "the model reaches exactly 4 dispatch inputs "
                     "((fam in {FAM_ARCSIN, FAM_OTHER}) x (default in {T,F})), each "
                     "crossed with the two delivery facts. Each maps to a realizable "
                     "real dispatch facet: FAM_ARCSIN <-> a real _cdf-is-not-None "
                     "family, FAM_OTHER <-> a real _cdf-is-None family (Benini), "
                     "default_query <-> len(kwargs)==0, closed_form_returns <-> the "
                     "ordering admitting the closed form's branch comparisons. The "
                     "probe confirms every reachable input is realized by the real "
                     "dispatch (incl. the closed-form-branch input, where the real "
                     "default arcsin query carries no Integral, and BOTH values of "
                     "the ordering facet, realized by a real bound pair and by one "
                     "the ordering refuses). A reachable input the real dispatch "
                     "could not realize would be the A-reference analogue of "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
