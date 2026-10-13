# properties.py — PBT manifest for scikit-learn__scikit-learn-12973.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants (frozen spec, swapped impl region only) checked by Nagini
# verify + markers.same_spec; the single axiom case is a real-callee probe run
# in the instance Docker image (the A-reference deep boolean model).
#
# Defended surface (frozen spec of `fit(config, data, copy_X)`):
#   Requires(Acc(config.default_copy, 1/2))   # READ-ONLY input (half perm)
#   Requires(Acc(data.intact))                # mutable (full perm)
#   Requires(Acc(data.native_format, 1/2))    # READ-ONLY input (half perm)
#   Ensures(Acc(config.default_copy, 1/2))
#   Ensures(config.default_copy == Old(config.default_copy))     # config frozen
#   Ensures(Acc(data.intact))
#   Ensures(Acc(data.native_format, 1/2))
#   Ensures(data.native_format == Old(data.native_format))       # format frozen
#   Ensures(Result() == selected_preference(Old(config.default_copy), copy_X))  # (4) LOAD-BEARING
#   Ensures(data.intact == (Result() or not data.native_format))                # (5) array fate
# selected_preference is a @Pure helper FULLY GROUNDED in the inputs
# (per_call if per_call is not None else default_copy) — not an opaque
# answer-key oracle, so there is no "wrong echo" to build (see assessment).
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12973"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region of model.py (edited ONLY between # impl-start/# impl-end
# so spec_view — hence same_spec — is preserved verbatim).
_GOLD_IMPL = """\
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X  # governs both preprocessing and the fitting routine
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective"""

# --- 1. POSITIVE CONTROL (soundness) -----------------------------------------
# Structurally-different but CORRECT impl: branch-reorder (test `is not None`
# first, no mutation of the parameter `copy_X`, explicit two-arm if/else) and
# the array fate written as a single boolean expression. Keeps every proof
# obligation the gold needs (no induction/lemma). MUST verify; if it
# cannot, the postcondition is SPEC-TOO-STRONG.
_POS = """\
    if copy_X is not None:
        effective = copy_X
    else:
        effective = config.default_copy
    data.intact = effective or not data.native_format
    return effective"""

# --- 2. ADMISSIBILITY --------------------------------------------------------
# A self-call caller (inside the impl region, so same_spec holds): constructs a
# fresh F2P-shaped input (LassoLarsIC(copy_X=True) called as fit(.., copy_X=False)
# => the discriminating F2P[False] shape) and invokes fit on it. The call site
# must be able to establish fit's Requires for a normal input (else
# PRECOND-TOO-STRONG), and the assumed postcondition pins the resolved value.
#
# TERMINATION: the probe call is now GUARDED by `not data.native_format`. This is
# not a weakening of the probe — it is what makes the self-call's termination
# provable at all, and the guard is chosen so the probe still runs on exactly the
# inputs that reach it. fit's level is parametric (2 if data.native_format else 3),
# because a CONSTANT level can never dominate itself: callee level must be
# strictly less than caller level, so under any fixed n a self-call is an
# obligation leak ("Callee fit might not take all unsatisfied obligations from the
# caller"). Under the guard, an outer non-native input (level 3) makes one nested
# call on the freshly built native-format InputArray(True, True) (level 2), whose
# own guard is then FALSE — so recursion depth is at most 2 and the descent
# 3 > 2 > 1 is well-founded. The guard is FEASIBLE, not a vacuity dodge: replacing
# the probe body with Assert(False) is REJECTED ("Assertion False might not hold"),
# confirming the guarded branch is genuinely reachable and the probe still proves
# something.
_ADMISS = """\
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    if not data.native_format:
        probe_cfg = Estimator(True)
        probe_data = InputArray(True, True)
        probe_res = fit(probe_cfg, probe_data, False)
        Assert(probe_res == False)
        Assert(probe_data.intact == False)
    return effective"""

# --- 3. FRAME-MUTATION (uniqueness; MANDATORY — read-only input) -------------
# config.default_copy has Acc(..,1/2) (read-only). This rival keeps the CORRECT
# resolution but WRITES to the read-only input. It must be rejected for
# INSUFFICIENT PERMISSION (a write needs full perm; only 1/2 is granted) — even
# though it would otherwise satisfy every value postcondition (config frozen
# clause aside, the write is the violation). A byte-fuzzer never tries this.
_FRAME_MUT = """\
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X
    config.default_copy = effective
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective"""

# --- 4. PARTIAL-DOMAIN (uniqueness) ------------------------------------------
# Correct on most of the domain but diverges on the sub-domain copy_X is False:
# it routes the construction-time default instead of the explicit per-call False.
# Diverges exactly on the F2P[False] case (copy_X=False, default_copy=True),
# where postcondition (4) demands Result()==False but this returns the default.
_PARTIAL = """\
    if copy_X is None or copy_X == False:
        effective = config.default_copy
    else:
        effective = copy_X
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective"""

# --- 5. VALUE DOUBLE-MASK / array-effect decoupling (uniqueness) -------------
# Resolves the preference correctly (satisfies (4)) but DECOUPLES the array's
# fate: it always leaves the array intact (data.intact = True) regardless of the
# selected preference. Postcondition (5) data.intact == (Result() or not
# data.native_format) must catch this when the selected preference is False on a
# native-format array. The cheapest "looks right" impl that forgets to route the
# resolved preference into preprocessing.
_DOUBLE_MASK = """\
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X
    data.intact = True
    return effective"""

# NOTE on _DOUBLE_MASK vs the format-aware spec: postcondition (5) is
# data.intact == (Result() or not data.native_format). The always-intact
# rival still violates it exactly when the selected preference is False AND
# data.native_format is True (the F2P-shaped native-format case), so the
# reject expectation is unchanged.

SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS),
        "rationale": ("a structurally-different but CORRECT impl (two-arm if/else "
                      "testing `is not None` first, no mutation of the copy_X param) "
                      "must satisfy postconditions (4)+(5); if it cannot, SPEC-TOO-STRONG. "
                      "No induction/lemma needed — keeps the gold proof shape."),
    },
    {
        "id": "admissibility-f2p-shaped-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": ("the Requires (Acc(config.default_copy,1/2), Acc(data.intact), "
                      "Acc(data.native_format,1/2)) must be establishable for a fresh "
                      "F2P-shaped input (Estimator(True), InputArray(True, True) — a "
                      "native-format array — fit(..,copy_X=False)); the assumed "
                      "postcondition then pins probe_res==False and probe_data.intact==False "
                      "(selected_preference(True,False)==False and the array is native-format). "
                      "If the call site cannot establish Requires, PRECOND-TOO-STRONG."),
    },
    {
        "id": "frame-mutation-write-readonly-config",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT),
        "refinement": ("its faithful real patch would WRITE self.copy_X inside fit "
                       "(mutating the estimator's construction-time default as a side "
                       "effect of one fit call). That permanently corrupts the estimator's "
                       "recorded default for every subsequent fit() with copy_X=None — "
                       "P2P test_lasso_lars_copyX_behaviour[True]/[False] (which assert the "
                       "init-time copy_X still governs a no-per-call fit) would break once a "
                       "prior fit with a different copy_X had overwritten self.copy_X. The "
                       "gold patch never assigns self.copy_X; it binds a LOCAL."),
        "rationale": ("REJECT from the PERMISSION SYSTEM: config.default_copy is granted "
                      "only Acc(..,1/2) (read-only); `config.default_copy = effective` needs "
                      "full permission. Insufficient-permission failure — not a value "
                      "postcondition failure. This is the #1 weakness class."),
    },
    {
        "id": "partial-domain-false-routes-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL),
        "refinement": ("its faithful real patch treats an explicit per-call copy_X=False "
                       "the same as copy_X=None: it passes self.copy_X to _preprocess_data "
                       "whenever copy_X is False. On the F2P case "
                       "test_lasso_lars_fit_copyX_behaviour[False] — a default LassoLarsIC "
                       "(self.copy_X==True) called fit(X,y,copy_X=False) — preprocessing "
                       "would copy X (self.copy_X True) leaving it intact, so "
                       "np.array_equal(X,X_copy)==True != copy_X(False): the F2P FAILS. "
                       "Does NOT resolve."),
        "rationale": ("REJECT from postcondition (4) Result()==selected_preference(Old(default),copy_X): "
                      "when copy_X==False the spec requires Result()==False, but this returns "
                      "config.default_copy (True on the F2P instance), violating (4) on that sub-domain."),
    },
    {
        "id": "value-double-mask-array-always-intact",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DOUBLE_MASK),
        "refinement": ("its faithful real patch resolves the per-call copy_X correctly but "
                       "then hard-codes copy=True into _preprocess_data (or otherwise never "
                       "lets X be overwritten). The array is always copied/intact, so the "
                       "F2P test_lasso_lars_fit_copyX_behaviour[False] and P2P "
                       "test_lasso_lars_copyX_behaviour[False] — which require "
                       "np.array_equal(X,X_copy)==False when the selected preference is "
                       "False (X must be mutated in place) — FAIL. Does NOT resolve."),
        "rationale": ("REJECT from postcondition (5) data.intact == (Result() or not "
                      "data.native_format): on a native-format array the resolved preference "
                      "(Result) can be False yet data.intact is hard-set True, so "
                      "data.intact(True) != (False or False). (5) pins the array fate to the "
                      "selected preference (modulo format conversion) and catches the decoupling."),
    },
]

# --- AXIOM LANE: the A-reference deep boolean model --------------------------
# The bundle consumes NO @ContractOnly axiom (axioms region empty). The only
# callee-relevant property — preprocessing copies X iff the resolved copy flag
# is True, EXCEPT that input validation materializes a converted working copy
# (shielding the caller's array) when X is not already in the native float
# working dtype — is an A-reference deep model:
#     selected_preference(default_copy, per_call) = per_call if per_call is not
#                                                   None else default_copy
#     InputArray.intact == (selected_preference(default_copy, per_call)
#                           or not native_format)
# Per PBT_PLAN §2.4 an A-reference must equal the real callee on EVERY
# caller-reachable input. The model can reach EXACTLY the cross product
#     default_copy in {True, False}  x  per_call in {True, False, None}
#                                    x  native_format in {True, False}
# (config.default_copy is a bool; copy_X is Optional[bool]; native_format is a
# bool realized as float64 vs int64 input dtype). The probe enumerates that full
# cross product (containment: nothing reachable lies outside it) plus 200 fuzz
# runs, executing the REAL post-gold LassoLarsIC.fit and asserting
# np.array_equal(X, X_copy) == (selected_preference(init, fit) or not native)
# every time. This is axiom_check.py's logic, made self-contained (stdlib +
# numpy + sklearn only).

_AXIOM_PROBE = r'''
import random
import sys

import numpy as np
from sklearn.linear_model import LassoLarsIC


def selected_preference(default_copy, per_call):
    # model.py's @Pure selected_preference, verbatim semantics.
    if per_call is None:
        return default_copy
    return per_call


def observe_real_fit(init_copy_X, fit_copy_X, native, rng):
    # Run the REAL LassoLarsIC.fit; report whether X was left intact
    # (np.array_equal(X, X_copy)) — exactly what the F2P tests read.
    # `native` selects float64 (native working dtype) vs int64 (validation
    # must materialize a converted working copy) input.
    lasso_lars = LassoLarsIC(copy_X=init_copy_X, precompute=False)
    X = rng.normal(0, 1, (100, 5))
    if not native:
        X = (X * 10).astype(np.int64)
    X_copy = X.copy()
    y = X[:, 2].astype(np.float64)
    if fit_copy_X is None:
        lasso_lars.fit(X, y)
    else:
        lasso_lars.fit(X, y, copy_X=fit_copy_X)
    return np.array_equal(X, X_copy)


def check(init_copy_X, fit_copy_X, native, rng):
    intact = observe_real_fit(init_copy_X, fit_copy_X, native, rng)
    expected = selected_preference(init_copy_X, fit_copy_X) or not native
    assert intact == expected, (
        "A-reference deep model unsound for init_copy_X=%r fit_copy_X=%r "
        "native=%r: real fit left X intact=%r, deep model expects=%r"
        % (init_copy_X, fit_copy_X, native, intact, expected))


def main():
    rng = np.random.RandomState(0)
    # containment: EXACTLY the caller-reachable cross product
    # {True,False} x {True,False,None} x {True,False}
    # (config.default_copy bool x copy_X Optional[bool] x native_format bool).
    combos = [(i, f, n) for i in (True, False) for f in (True, False, None)
              for n in (True, False)]
    for init_copy_X, fit_copy_X, native in combos:
        check(init_copy_X, fit_copy_X, native, rng)
    pyrng = random.Random(12973)
    for _ in range(200):
        init_copy_X = pyrng.choice([True, False])
        fit_copy_X = pyrng.choice([True, False, None])
        native = pyrng.choice([True, False])
        check(init_copy_X, fit_copy_X, native, rng)
    print("G-PBT AXIOM OK: A-reference deep model (selected_preference / intact "
          "modulo format conversion) == real LassoLarsIC.fit on %d boundary "
          "combos + 200 fuzz runs (np.array_equal(X, X_copy) matches every time)"
          % len(combos))
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

AXIOM_TESTS = [
    {
        "id": "aref-preprocess-copy-iff-flag",
        "axiom": "selected_preference / InputArray.intact (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": ("AXIOM-UNSOUND if the real post-gold LassoLarsIC.fit ever leaves X "
                      "intact != selected_preference(init_copy_X, fit_copy_X). The probe "
                      "runs the real callee over the FULL caller-reachable cross product "
                      "(containment: bool x Optional[bool] = {T,F} x {T,F,None}) + 200 fuzz "
                      "runs and asserts np.array_equal(X,X_copy) matches the deep model. "
                      "apply_gold=True: the deep model describes post-fix behaviour."),
    },
]
