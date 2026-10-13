# properties.py — PBT manifest for sympy__sympy-13757. NOT a Nagini module; a
# record of adversarial cases. The runner (swebench_nagini.pbt) executes each and
# stamps RESULT. Spec cases are full model.py variants (same frozen spec, swapped
# impl, built by region-surgery on the impl-start/impl-end region) checked by
# Nagini verify + same_spec; axiom cases are real-callee probes checked in Docker.
#
# Defended surface (read from model.py + refinement.md + mapping.md):
#   - default_priority()        @Pure (axioms region): Ensures Result()==10.0.
#   - resolved_by_right(...)     @Pure (pure region): the FIXED dispatch predicate
#                                `other_has_handler and other_priority > self_priority`.
#   - product_is_evaluated(self_priority, self_evaluates, other_priority,
#       other_evaluates, other_has_handler): NO precondition; Ensures Result() ==
#       (other_evaluates if resolved_by_right(...) else self_evaluates). All five
#       params are PRIMITIVE SCALARS PASSED BY VALUE (float/bool) -> Nagini holds
#       no fractional permission on them, so there is NO read-only reference to
#       overwrite: the frame-mutation class is N/A for this instance (see
#       'assessment').
#   - polynomial_priority(): Ensures Result() >= default_priority() + 1e-15. THE
#       LOAD-BEARING discriminating clause (the modeled changed datum:
#       Poly._op_priority crossing above the default by at least the runtime
#       scalar's resolution at that magnitude, so the strict order survives
#       materialization). model_prepatch.py fails exactly here.
#   - generic_times_polynomial(): Ensures Result() == True. The required F2P
#       behaviour; its discrimination is anchored upstream in polynomial_priority's
#       FROZEN postcondition, not in its own (bare-constant) postcondition.
from pathlib import Path

INSTANCE = "sympy__sympy-13757"
FLOAT_ENCODING = "real"   # meta.json float_encoding; the dispatch turns on a strict
                          # real order (10.001 > 10.0), so floats are interpreted.

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (verbatim from model.py) ---------------------------

# product_is_evaluated impl (lines 71-73)
_PROD_IMPL = (
    "    if resolved_by_right(self_priority, other_priority, other_has_handler):\n"
    "        return other_evaluates\n"
    "    return self_evaluates"
)

# polynomial_priority impl (line 88)
_POLY_IMPL = "    return 10.001"

# generic_times_polynomial impl: the final return (line 128-129). Used by the
# admissibility self-call case (we inject an Assert just before it).
_GTP_RETURN = (
    "    return product_is_evaluated(left_priority, left_evaluates,\n"
    "                                right_priority, right_evaluates, True)"
)


# =============================================================================
# SPEC TESTS
# =============================================================================
SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness): structurally-different correct impl ---
    # Reorder product_is_evaluated's branches (guard on the negation first).
    # Logically identical to the gold impl; references only by-value params; keeps
    # every proof obligation (the postcondition is the same frozen clause). MUST
    # verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-control-product-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROD_IMPL,
            "    if not resolved_by_right(self_priority, other_priority, other_has_handler):\n"
            "        return self_evaluates\n"
            "    return other_evaluates",
        ),
        "rationale": "a branch-reorder-equivalent correct impl of product_is_evaluated "
                     "must satisfy the same frozen Ensures (else SPEC-TOO-STRONG). No "
                     "lemma needed: pure boolean case split, by-value params.",
    },

    # A correct impl of polynomial_priority returning a DIFFERENT in-spec value
    # (any real strictly above the default routes the product to the polynomial
    # and resolves). 10.5 > 10.0 satisfies the postcondition and its faithful
    # real patch (_op_priority = 10.5) DOES resolve. This documents that the
    # spec's latitude above the default is correct, not a defect.
    {
        "id": "pos-control-priority-different-valid-value",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _POLY_IMPL, "    return 10.5"),
        "rationale": "polynomial_priority's Ensures only requires Result() >= default "
                     "+ 1e-15; any value above by at least that margin (here 10.5) is "
                     "correct and its faithful real patch (_op_priority=10.5) resolves. "
                     "Must verify (else SPEC-TOO-STRONG: over-pinning the exact 10.001).",
    },

    # ---- ADMISSIBILITY: precondition admits the F2P-shaped input -------------
    # There is no Requires, so admissibility is structural: confirm the modeled
    # dispatch ACCEPTS the normal F2P input (generic-left default priority,
    # polynomial-right strictly-above priority with a handler) and that the
    # self-call on that input is well-formed and the dispatch picks the right
    # operand. Inject an Assert before the (unchanged) gold return. MUST verify;
    # if it cannot, PRECOND-TOO-STRONG (or the modeled call is ill-formed).
    {
        "id": "admiss-f2p-shaped-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GTP_RETURN,
            "    Assert(resolved_by_right(left_priority, right_priority, True))\n"
            "    Assert(product_is_evaluated(left_priority, left_evaluates,\n"
            "                                right_priority, right_evaluates, True) == True)\n"
            "    return product_is_evaluated(left_priority, left_evaluates,\n"
            "                                right_priority, right_evaluates, True)",
        ),
        "rationale": "the modeled dispatch must ACCEPT the normal F2P input "
                     "(default-priority generic left, strictly-above polynomial right "
                     "with handler) and pick the right operand -> product evaluates "
                     "(True). A self-call assertion that succeeds shows the spec admits "
                     "a normal input (else PRECOND-TOO-STRONG / ill-formed call).",
    },

    # ---- UNIQUENESS / the load-bearing discriminator -------------------------
    # The prepatch value: Poly inherits the default priority (10.0). Must FAIL on
    # polynomial_priority's Ensures Result() >= default_priority() + 1e-15. This
    # is exactly model_prepatch.py's failure (G-DIFF). If it VERIFIED, the
    # discriminating clause would be vacuous => SPEC-TOO-WEAK.
    {
        "id": "reject-priority-equals-default-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _POLY_IMPL, "    return 10.0"),
        "refinement": "this is the PRE-PATCH state: Poly inherits Expr._op_priority=10.0. "
                      "By the unchanged dispatch (other_priority > self_priority is FALSE on "
                      "the tie), x*Poly(x) routes to the generic left operand and stays an "
                      "inert Mul -> test_issue_13079's `x*Poly(x) == Poly(x**2,...)` FAILS. "
                      "Faithful real patch does NOT resolve.",
        "rationale": "rejected by polynomial_priority's postcondition Result() >= "
                     "default_priority() + 1e-15 (10.0 >= 10.0 + 1e-15 is false). This is the "
                     "spec's discriminating clause; rejection here is mandatory for "
                     "verify=>resolve.",
    },

    # A priority strictly BELOW the default. Also fails the strict-order Ensures,
    # and its faithful patch routes the product the wrong way.
    {
        "id": "reject-priority-below-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _POLY_IMPL, "    return 9.0"),
        "refinement": "_op_priority = 9.0 < 10.0 makes the dispatch prefer the GENERIC "
                      "operand (other_priority > self_priority is false), so x*Poly(x) "
                      "stays an inert Mul and test_issue_13079 FAILS. Faithful real patch "
                      "does NOT resolve.",
        "rationale": "rejected by Result() >= default_priority() + 1e-15 "
                     "(9.0 >= 10.0 + 1e-15 is false).",
    },

    # ---- UNIQUENESS / partial-domain on product_is_evaluated -----------------
    # Always return self_evaluates (ignore the dispatch). Correct only on the
    # sub-domain where resolved_by_right is False; WRONG (and rejected) where the
    # right operand should win. This is precisely the bug shape (left always
    # handles).
    {
        "id": "reject-product-always-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PROD_IMPL, "    return self_evaluates"),
        "refinement": "a dispatch that always lets the LEFT operand handle (ignoring "
                      "priority) is exactly the pre-patch bug: x*Poly(x) -> Mul (inert), "
                      "test_issue_13079 FAILS. Faithful real patch does NOT resolve.",
        "rationale": "rejected by the postcondition on the sub-domain resolved_by_right==True "
                     "(must return other_evaluates, which can differ from self_evaluates). "
                     "partial-domain: correct only where the left operand legitimately wins.",
    },

    # Always return other_evaluates (always delegate right). Correct only where
    # resolved_by_right is True; WRONG (rejected) when the left operand should
    # win (no handler, or not strictly higher priority).
    {
        "id": "reject-product-always-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PROD_IMPL, "    return other_evaluates"),
        "refinement": "always delegating to the RIGHT operand drops the priority/has-handler "
                      "guard: on equal-priority or no-handler products (e.g. Expr*Expr, or a "
                      "Poly*Poly tie) it would wrongly evaluate via the right reverse handler, "
                      "changing P2P results (test_Poly_mul / dispatch invariants). Faithful "
                      "real patch (unconditional delegation) does NOT faithfully resolve.",
        "rationale": "rejected by the postcondition on the sub-domain resolved_by_right==False "
                     "(must return self_evaluates). partial-domain on the no-delegate side.",
    },

    # Relax the strict order to >= inside product_is_evaluated (drop the strict
    # guard the source has at `if other._op_priority > self._op_priority`). Wrong
    # on the EQUAL-priority tie sub-domain, where the frozen resolved_by_right
    # (strict >) says the LEFT operand wins. Rejected.
    {
        "id": "reject-product-relaxed-ge-on-tie",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _PROD_IMPL,
            "    if other_has_handler and other_priority >= self_priority:\n"
            "        return other_evaluates\n"
            "    return self_evaluates",
        ),
        "refinement": "replacing the strict `>` with `>=` makes the dispatch delegate to the "
                      "right operand on a PRIORITY TIE. In real SymPy that is the equal-priority "
                      "case (e.g. Poly*Poly, or any Expr*Expr where both carry the default "
                      "priority): `>=` would route ties to the right reverse handler, flipping "
                      "established products and breaking P2P invariants. The source line is the "
                      "strict `if other._op_priority > self._op_priority`; a `>=` patch is NOT "
                      "faithful and would not resolve cleanly.",
        "rationale": "rejected by the postcondition on the tie sub-domain "
                     "(other_priority==self_priority, has=True): resolved_by_right is FALSE so "
                     "the spec requires self_evaluates, but the impl returns other_evaluates. "
                     "value-level / partial-domain divergence on the boundary.",
    },
]


# =============================================================================
# AXIOM TESTS
#
# meta.json: axioms == [] (no @ContractOnly consumed axioms). There are TWO
# A-reference deep models (resolved_by_right, default_priority) that MUST equal
# the real SymPy callees on every caller-reachable input. We validate them
# against the real library in-container (the existing G-AX logic, embedded here
# self-contained), plus a containment check that every callee-input the model
# can reach lies in the deep model's intended domain.
# =============================================================================

# --- axiom-soundness probe: deep models == real SymPy callees ----------------
# Embeds the core of axiom_check.py (the runner mounts ONLY this probe; model.py
# / axiom_check.py are NOT in-container). Imports only sympy. apply_gold=True so
# Poly._op_priority is the post-patch 10.001 (the A-reference world we validate).
_AX_SOUND = r'''
import random, sys

DEFAULT_PRIORITY = 10.0          # default_priority()  (model.py axioms region)
POLYNOMIAL_PRIORITY = 10.001     # polynomial_priority()

def resolved_by_right(self_priority, other_priority, other_has_handler):
    # the model.py @Pure deep dispatch model, verbatim semantics
    return other_has_handler and other_priority > self_priority

def real_delegates(self_priority, other_priority, other_has_handler):
    """Run the REAL binary_op_wrapper from
    sympy.core.decorators.call_highest_priority and report whether it delegated
    to the right operand's reverse handler (patch-independent decorator code)."""
    from sympy.core.decorators import call_highest_priority
    delegated = {"v": False}

    class Left(object):
        _op_priority = self_priority
        @call_highest_priority('__rother__')
        def op(self, other):
            return "left"            # func(self, other): left handled it

    class RightWithHandler(object):
        _op_priority = other_priority
        def __rother__(self, other):
            delegated["v"] = True
            return "right"           # right operand's reverse handler ran

    class RightNoHandler(object):
        _op_priority = other_priority   # exposes _op_priority, NOT the handler

    right = RightWithHandler() if other_has_handler else RightNoHandler()
    Left().op(right)
    return delegated["v"]

def check_dispatch(ps, po, has):
    observed = real_delegates(ps, po, has)
    expected = resolved_by_right(ps, po, has)
    assert observed == expected, (
        "DISPATCH DEEP MODEL UNSOUND on (self=%r, other=%r, has=%r): real "
        "binary_op_wrapper delegated=%r, model resolved_by_right=%r"
        % (ps, po, has, observed, expected))

def main():
    # A-reference (mapping.md 3.1): deep model == real binary_op_wrapper over a
    # boundary grid + fuzz, INCLUDING the 10.0/10.001 tie and strict-cross loci.
    grid = [10.0, 10.001, 9.999, 11.0, 0.0, -1.0, 1e9, 10.0000001]
    boundary = [(ps, po, has) for ps in grid for po in grid for has in (True, False)]
    boundary += [
        (10.0, 10.0, True),     # tie: left handles (the pre-patch bug locus)
        (10.0, 10.001, True),   # strict cross: right (Poly) handles (the fix)
        (10.0, 10.001, False),  # cross but no handler: left handles
    ]
    for ps, po, has in boundary:
        check_dispatch(ps, po, has)
    rng = random.Random(13757)
    for _ in range(20000):
        ps = rng.choice([rng.uniform(-1e3, 1e3), 10.0, 10.001])
        po = rng.choice([rng.uniform(-1e3, 1e3), 10.0, 10.001])
        has = rng.random() < 0.5
        check_dispatch(ps, po, has)

    # A-reference (mapping.md 3.2): modeled priorities == real class data.
    from sympy.core.expr import Expr
    from sympy import Poly
    assert Expr._op_priority == DEFAULT_PRIORITY, (
        "DEFAULT PRIORITY DRIFT: model %r != real Expr._op_priority %r"
        % (DEFAULT_PRIORITY, Expr._op_priority))
    poly_prio = Poly._op_priority
    strict_above = poly_prio > Expr._op_priority
    assert strict_above, (
        "apply_gold expected Poly._op_priority strictly above default; got %r "
        "(<= %r). Probe must run with the gold patch applied." % (poly_prio, Expr._op_priority))
    assert poly_prio == POLYNOMIAL_PRIORITY, (
        "POLYNOMIAL PRIORITY DRIFT: model %r != real Poly._op_priority %r"
        % (POLYNOMIAL_PRIORITY, poly_prio))

    # end-to-end: x*Poly(x) evaluates iff the strict order holds (it does here).
    from sympy.abc import x
    p = Poly(x)
    left_times = p * x            # Poly(x)*x : always an evaluated Poly
    right_times = x * p           # x*Poly(x) : the bugged side; post-patch evaluated
    assert getattr(left_times, "is_Poly", False), (
        "Poly(x)*x should be an evaluated Poly, got %r" % (left_times,))
    assert getattr(right_times, "is_Poly", False), (
        "post-patch: x*Poly(x) must be an evaluated Poly, got %r" % (right_times,))
    assert right_times == left_times, (
        "post-patch: x*Poly(x) must equal Poly(x)*x, got %r vs %r"
        % (right_times, left_times))
    print("AX-SOUND OK: resolved_by_right == real binary_op_wrapper over %d "
          "boundary + 20000 fuzz; Expr._op_priority==10.0, Poly._op_priority==%r "
          "(> default); x*Poly(x) evaluates and == Poly(x)*x." % (len(boundary), poly_prio))
    return 0

sys.exit(main())
'''

# --- axiom-containment probe: every model-reachable callee-input is in domain -
# The deep dispatch model resolved_by_right is total over (float, float, bool):
# it has NO Requires constraint, so any priority triple the model produces is
# trivially in its domain. The model can only ever pass the priority pair
# {default_priority()=10.0, polynomial_priority()=10.001} with has=True (the
# generic-left x polynomial-right F2P product). We assert (a) the real callee
# accepts exactly that reachable input and (b) it lies on the STRICT-CROSS side
# (10.001 > 10.0) so the deep model's domain covers the caller. Covering MORE
# (the whole grid) is sound, not a defect.
_AX_CONTAIN = r'''
import sys

def resolved_by_right(self_priority, other_priority, other_has_handler):
    return other_has_handler and other_priority > self_priority

def main():
    from sympy.core.expr import Expr
    from sympy import Poly
    # The exact (and only) priority pair the modeled F2P product reaches:
    self_p = Expr._op_priority      # default_priority(), the generic LEFT operand
    other_p = Poly._op_priority     # polynomial_priority(), the polynomial RIGHT operand
    has = True                      # a Poly exposes _op_priority AND __rmul__
    # Containment: this reachable input is in the deep model's (unconstrained)
    # domain, and the dispatch picks the RIGHT operand exactly here.
    assert resolved_by_right(self_p, other_p, has) is True, (
        "CALLER-REACHABLE INPUT MIS-COVERED: the F2P product (self=%r, other=%r, "
        "has=%r) must route to the right operand, got resolved_by_right=False"
        % (self_p, other_p, has))
    # And the symmetric tie input the model can ALSO reach inside
    # generic_times_polynomial's Assert (left_priority on both sides): must route
    # LEFT (the strict guard), confirming the deep model covers that locus too.
    assert resolved_by_right(self_p, self_p, has) is False, (
        "TIE INPUT MIS-COVERED: equal priorities must route LEFT (strict >), "
        "got resolved_by_right=True on (self=%r, other=%r, has=%r)"
        % (self_p, self_p, has))
    print("AX-CONTAIN OK: the modeled F2P product reaches only the priority pair "
          "(%r, %r, has=True) [strict cross] and the tie (%r, %r, has=True); both "
          "lie in the deep dispatch model's domain and route as the model expects."
          % (self_p, other_p, self_p, self_p))
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-resolved_by_right-and-priorities",
        "axiom": "resolved_by_right / default_priority (A-reference deep models)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND,
        "rationale": "the A-reference deep models must equal the real SymPy callees on every "
                     "input: resolved_by_right == real binary_op_wrapper delegation over a "
                     "boundary grid (incl. the 10.0/10.001 tie + strict cross) + 20000 fuzz, "
                     "default_priority()==Expr._op_priority, polynomial_priority()==Poly._op_"
                     "priority (post-patch, strictly above), and x*Poly(x) evaluates == Poly(x)*x. "
                     "Any disagreement is AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-dispatch-caller-domain",
        "axiom": "resolved_by_right (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN,
        "rationale": "every callee-input the model can reach (the strict-cross F2P pair "
                     "(10.0, 10.001, True) and the equal-priority tie (10.0, 10.0, True) inside "
                     "generic_times_polynomial's Assert) lies in the deep dispatch model's "
                     "(unconstrained) domain and routes exactly as the model expects. A "
                     "reachable input outside the covered domain would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
