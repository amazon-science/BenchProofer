# properties.py — PBT falsification battery for scikit-learn__scikit-learn-12682.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant built by region-surgery (only text
# INSIDE an # impl-start/# impl-end block is edited, so same_spec is guaranteed);
# the frozen spec (axioms/pure/pre/post regions) is never touched.
#
# Defended surface (read from model.py + refinement.md + the F2P test_max_iter):
#   The fix is pure INTEGER PARAMETER PROPAGATION. Three modeled fns:
#     encode_iteration_budget(algorithm:int, max_iter:int)->int
#       pre  is_iterative_lasso(algorithm) and max_iter>=1
#       post Result() == max_iter                 [LOAD-BEARING: exact identity]
#     coder_solver_budget(algorithm, max_iter)->int   (forwards to the above)
#       post Result() == max_iter
#     estimator_encode_budget(self:Estimator, algorithm)->int
#       pre  Acc(self.configured_max_iter, 1/2)    [READ-ONLY input]
#            and self.configured_max_iter>=1 and is_iterative_lasso(algorithm)
#       post Acc(self.configured_max_iter, 1/2) and
#            Result() == self.configured_max_iter  [LOAD-BEARING end-to-end pin]
#
# The two ACTUAL bugs the gold patch fixes are encoded as @Pure answer-key
# constants in the frozen pure region:
#     lars_builtin_default()  == 500   (B2: LassoLars built w/o max_iter -> class default)
#     coder_param_default()   == 1000  (B1: transform doesn't forward -> coder default)
# A correct impl must NOT return these constants. They are the canonical wrong
# answers, so a "return the default" rival is the highest-value uniqueness attack.
#
# No @ContractOnly axioms / no A-reference deep model (meta.axioms == []), so
# AXIOM_TESTS is empty by design (the bundle's axiom_check.py is a PROVENANCE
# check of the two constants, not a callee-soundness axiom; it is covered by
# G-AX, not re-run here).
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12682"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer propagation)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The three impl-region anchors (each occurs exactly once; all live strictly
# inside an # impl-start/# impl-end block, so swapping them preserves same_spec).
_E_IMPL = "    budget = max_iter\n    return budget"
_C_IMPL = "    return encode_iteration_budget(algorithm, max_iter)"
_S_IMPL = ("    budget = coder_solver_budget(algorithm, self.configured_max_iter)\n"
           "    return budget")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility): structurally-different but
# CORRECT impls that MUST verify. If any fails -> SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------

# pos-control-1: encode_iteration_budget written with a branch-reorder on the
# algorithm selector instead of a single assignment. Both arms return max_iter
# (the lasso_lars arm and the lasso_cd arm both receive the supplied budget).
# This mirrors the real code's two-branch shape (lasso_lars vs lasso_cd) while
# staying correct. No framing/induction lemma is needed (assignment-only).
_pos1 = _swap(
    _BASE, _E_IMPL,
    "    if is_iterative_lasso(algorithm):\n"
    "        if algorithm == 0:\n"
    "            budget = max_iter\n"
    "        else:\n"
    "            budget = max_iter\n"
    "    else:\n"
    "        budget = max_iter\n"
    "    return budget",
)

# pos-control-2: estimator_encode_budget bound to a local before the call, then
# returned -- a local-variable reshape that keeps the read-only field untouched
# and still satisfies Result() == self.configured_max_iter. Exercises the
# Acc(...,1/2) preservation under a different statement shape.
_pos2 = _swap(
    _BASE, _S_IMPL,
    "    cfg = self.configured_max_iter\n"
    "    budget = coder_solver_budget(algorithm, cfg)\n"
    "    return budget",
)

# admiss-1: a self-call admissibility probe -- estimator_encode_budget calls the
# coder on its own configured field and ASSERTS the end-to-end pin holds for an
# in-domain (F2P-shaped) input. If the Requires cannot be established for a
# normal forwarded call -> PRECOND-TOO-STRONG. (Assert keeps same_spec: it is in
# the impl region, not the contract.)
_admiss = _swap(
    _BASE, _S_IMPL,
    "    budget = coder_solver_budget(algorithm, self.configured_max_iter)\n"
    "    Assert(budget == self.configured_max_iter)\n"
    "    return budget",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / REJECT cases: same-spec WRONG impls. If any VERIFIES -> SPEC-TOO-WEAK.
# ---------------------------------------------------------------------------

# weak-echo-lars (ungrounded-oracle echo, B2 bug verbatim): the least-angle arm
# returns the solver class's BUILT-IN DEFAULT (500) instead of the supplied
# budget -- exactly the pre-patch LassoLars(...) constructed without max_iter.
# The @Pure lars_builtin_default() is in the contract; this echoes it.
# refinement: the faithful real patch is `LassoLars(..., )` WITHOUT
# `max_iter=max_iter` (gold removes nothing here -- it ADDS max_iter). With this
# impl the lasso_lars solver runs 500 iters regardless of transform_max_iter, so
# the convergence-vs-warning the F2P observes is decoupled from the configured
# budget => F2P test_max_iter (and the lasso_lars warning in the problem
# statement) would NOT be resolved. expect reject (violates Result()==max_iter
# for max_iter != 500).
_weak_echo_lars = _swap(
    _BASE, _E_IMPL,
    "    if algorithm == 0:\n"
    "        budget = lars_builtin_default()\n"
    "    else:\n"
    "        budget = max_iter\n"
    "    return budget",
)

# weak-echo-coder (ungrounded-oracle echo, B1 bug verbatim): the estimator path
# forwards the coder's OWN PARAMETER DEFAULT (1000) instead of the configured
# field -- exactly the pre-patch transform() that omitted max_iter and let
# sparse_encode fall back to 1000.
# refinement: the faithful real patch is transform() calling sparse_encode
# WITHOUT max_iter=self.transform_max_iter; the user's transform_max_iter is
# dropped. The F2P sets transform_max_iter=1 (expect ConvergenceWarning) and
# =2000 (expect no warning); with the default 1000 forwarded, the =1 case would
# NOT warn (1000 iters) and the assertion `with pytest.warns(ConvergenceWarning)`
# fails => test_max_iter NOT resolved. expect reject (violates
# Result()==self.configured_max_iter for configured != 1000).
_weak_echo_coder = _swap(
    _BASE, _S_IMPL,
    "    budget = coder_solver_budget(algorithm, coder_param_default())\n"
    "    return budget",
)

# weak-partial-domain (partial-domain): correct on the lasso_cd arm
# (algorithm==1, the branch the F2P test_max_iter directly exercises via
# transform_algorithm='lasso_cd') but WRONG on the lasso_lars arm (algorithm==0):
# returns budget-1 there. This is the cheapest rival that passes the literal F2P
# input yet diverges on a reachable in-domain sub-case (algorithm==0 is in
# is_iterative_lasso's domain and is the lasso_lars warning path in the problem
# statement).
# refinement: a faithful patch matching this would build LassoLars with
# max_iter-1; on the lasso_lars convergence path the configured budget is off by
# one for every value, so the documented lasso_lars warning is not faithfully
# fixed and any lasso_lars-budget assertion diverges. expect reject (violates
# Result()==max_iter at algorithm==0 for all max_iter).
_weak_partial = _swap(
    _BASE, _E_IMPL,
    "    if algorithm == 0:\n"
    "        budget = max_iter - 1\n"
    "    else:\n"
    "        budget = max_iter\n"
    "    return budget",
)

# weak-frame-mutation (FRAME-MUTATION -- MANDATORY: self.configured_max_iter is a
# READ-ONLY input held at Acc(...,1/2)). The rival OVERWRITES the read-only field
# to a constant and then returns it, "satisfying" Result()==self.configured_max_iter
# vacuously by mutating the witness. The gold post/invariants are kept verbatim so
# the rejection is attributable to the WRITE, not to a value mismatch. With only
# 1/2 permission this is INSUFFICIENT PERMISSION to assign self.configured_max_iter.
# refinement: a real transform() that reassigned self.transform_max_iter=42 mid-call
# (or any constant) would change the estimator's configured budget away from the
# user's value; the F2P (transform_max_iter=1 vs 2000) would feed a fixed 42 to the
# solver, decoupling convergence-vs-warning from the configured value => test_max_iter
# NOT resolved. expect reject (fails for insufficient permission on the half-perm field).
_weak_frame = _swap(
    _BASE, _S_IMPL,
    "    self.configured_max_iter = 42\n"
    "    budget = coder_solver_budget(algorithm, self.configured_max_iter)\n"
    "    return budget",
)

# weak-const-coder (supporting near-miss): coder_solver_budget returns a fixed
# constant (1) instead of forwarding. Cheap corruption, but carries a real
# refinement: a coder that ignored its max_iter argument and hard-coded 1 would
# force every solver to a single iteration regardless of configuration, so the
# =2000 (expect no warning) F2P case would still warn => not resolved.
# expect reject (violates Result()==max_iter for max_iter != 1).
_weak_const = _swap(
    _BASE, _C_IMPL,
    "    empty = 1  # type: int\n"
    "    return empty",
)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos1,
        "rationale": "structurally-different CORRECT encode_iteration_budget "
                     "(two-arm branch on the selector, both arms return "
                     "max_iter) must satisfy Result()==max_iter; assignment-only "
                     "so no induction lemma is needed (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos2,
        "rationale": "estimator_encode_budget reshaped to bind the read-only "
                     "field to a local before forwarding; keeps Acc(...,1/2) "
                     "untouched and still pins Result()==self.configured_max_iter "
                     "(else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": "the estimator path forwards its configured field through "
                     "the coder and Asserts the end-to-end pin for an F2P-shaped "
                     "in-domain input; the Requires must admit a normal forwarded "
                     "call (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "weak-echo-lars-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_echo_lars,
        "refinement": "echoes the @Pure lars_builtin_default()==500 on the "
                      "lasso_lars arm -- the verbatim B2 bug (LassoLars built "
                      "without max_iter). The constructed solver runs 500 iters "
                      "regardless of the configured budget, so the lasso_lars "
                      "convergence/warning is decoupled from transform_max_iter "
                      "and the F2P/problem-statement behaviour is NOT resolved.",
        "rationale": "must fail the postcondition Result()==max_iter at "
                     "algorithm==0 whenever max_iter != 500. If it verifies, the "
                     "spec admits the canonical wrong-answer echo => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-echo-coder-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_echo_coder,
        "refinement": "echoes the @Pure coder_param_default()==1000 -- the "
                      "verbatim B1 bug (transform omits max_iter, coder falls "
                      "back to 1000). The F2P sets transform_max_iter=1 expecting "
                      "a ConvergenceWarning; with 1000 forwarded it would NOT "
                      "warn, so `with pytest.warns(ConvergenceWarning)` fails => "
                      "test_max_iter NOT resolved.",
        "rationale": "must fail Result()==self.configured_max_iter whenever the "
                     "configured value != 1000. If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-partial-domain-lasso-lars",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_partial,
        "refinement": "correct on lasso_cd (algorithm==1, the literal F2P input) "
                      "but off-by-one (max_iter-1) on the lasso_lars arm "
                      "(algorithm==0), a reachable in-domain sub-case and the "
                      "documented lasso_lars warning path. A faithful patch "
                      "building LassoLars with max_iter-1 mis-budgets every "
                      "lasso_lars call, so that path is not faithfully fixed.",
        "rationale": "must fail Result()==max_iter at algorithm==0 for all "
                     "max_iter. If it verifies, the spec pins only part of the "
                     "is_iterative_lasso domain => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_frame,
        "refinement": "overwrites the READ-ONLY self.configured_max_iter (held "
                      "at Acc(...,1/2)) to 42 to satisfy the end-to-end pin "
                      "vacuously. A real transform() that reassigned "
                      "self.transform_max_iter mid-call would feed a fixed 42 to "
                      "the solver regardless of the user's value, decoupling "
                      "convergence-vs-warning from the configuration => the F2P "
                      "(transform_max_iter=1 vs 2000) is NOT resolved.",
        "rationale": "must fail for INSUFFICIENT PERMISSION: only 1/2 access to "
                     "self.configured_max_iter is held, so the assignment is "
                     "illegal. The gold postcondition/invariants are kept verbatim "
                     "so the rejection is attributable to the write (frame "
                     "violation). If it verifies, a read-only input is mutable "
                     "=> SPEC-TOO-WEAK (#1 weakness class).",
    },
    {
        "id": "weak-const-coder-ignores-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_const,
        "refinement": "supporting near-miss: coder_solver_budget hard-codes 1, "
                      "ignoring its max_iter argument. A coder that forced a "
                      "single iteration would still warn on the =2000 (expect no "
                      "warning) F2P case => not resolved.",
        "rationale": "must fail Result()==max_iter for max_iter != 1. Cheap "
                     "corruption with a real refinement; supports (does not "
                     "substitute for) the reasoned attacks above.",
    },
]


# No @ContractOnly axioms and no A-reference deep model in this bundle
# (meta.axioms == [], deep_model_references == []). The fix is pure integer
# data flow; the bundle's axiom_check.py discharges only a PROVENANCE check of
# the two prepatch fallback constants (LassoLars.max_iter default == 500,
# _sparse_encode/sparse_encode max_iter default == 1000), which is covered by
# G-AX rather than by a callee-soundness obligation. There is therefore no
# axiom-soundness or axiom-containment obligation to probe here.
AXIOM_TESTS = []
