"""PBT falsification battery for scikit-learn__scikit-learn-11578.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap, which mechanically
GUARANTEES same_spec) and are checked by Nagini verify. The axiom lane probes
the single A-consumed @ContractOnly axiom transforms_differ + the two
A-reference transforms in the instance Docker image (real predict_proba).

Defended surface (scoring_estimator_proba(caller_mode: int, d: PSeq[int]) -> PSeq[int])
--------------------------------------------------------------------------------------
Models the gold one-liner
    -    log_reg = LogisticRegression(fit_intercept=fit_intercept)   # multi_class -> 'ovr'
    +    log_reg = LogisticRegression(multi_class=multi_class)
i.e. the throw-away scoring estimator inherits the CALLER's multiclass mode, so
a probabilistic scorer (neg_log_loss, the FAIL_TO_PASS) reads the caller-mode
class-probability transform, not the default one-vs-rest one.

Preconditions:
  (R1) caller_mode == OVR (0) or caller_mode == MULTINOMIAL (1)
  (R2) transforms_differ()  -- the single A-consumed @ContractOnly axiom: the
       two opaque probability transforms are distinct functions on the witness
       decision row (EXISTENTIAL distinctness, validated by axiom_check.py G-AX).

Postconditions (load-bearing clauses):
  (P1) Result() == scoring_proba(caller_mode, d)
       -- the GROUNDING clause. scoring_proba is a @Pure helper that fully
       unfolds to proba_softmax(d) if caller_mode==MULTINOMIAL else proba_ovr(d).
       It is a total function of the modeled inputs caller_mode/d, NOT an opaque
       answer-key the impl can echo, so there is no "wrong echo" rival; the
       cheapest correct impl simply returns scoring_proba(caller_mode, d).
  (P2) Implies(caller_mode == MULTINOMIAL, Result() == proba_softmax(d))
  (P3) Implies(caller_mode == OVR,         Result() == proba_ovr(d))
  (P4) Implies(caller_mode == MULTINOMIAL and d == witness_decision(),
               Result() != proba_ovr(d))
       -- the derived DISCRIMINATING consequence; this is the only clause that
       CONSUMES the transforms_differ axiom (removing R2 makes verification fail
       on exactly P4, per meta.json / refinement.md). It pins that in
       multinomial mode the scorer does NOT see the one-vs-rest vector.

Weakness-class coverage rationale for THIS instance
---------------------------------------------------
* FRAME-MUTATION: NOT APPLICABLE. has_readonly_input == False. Both parameters
  are immutable VALUE types -- caller_mode is an int, d is a PSeq[int] (Nagini's
  mathematical, immutable sequence). There is NO heap object / NO Acc(.,1/2)
  read-only INPUT parameter to overwrite, so the frame-mutation weakness class
  (overwrite a half-permission read-only input to satisfy a postcondition
  vacuously) cannot arise: there is no heap location to write. A "mutate the
  input" rival is unconstructible here. (Justified in 'assessment'.)
* UNGROUNDED-ORACLE ECHO: NO wrong echo exists -- P1 grounds Result() in the
  inputs via the @Pure selector scoring_proba (fully unfolded), not via an
  opaque answer-key. Covered instead by the honest cheapest-/structural-variant
  positive controls (pos-inline-branch, pos-branch-reorder).
* PARTIAL-DOMAIN: weak-always-multinomial (correct on the multinomial caller,
  wrong on the OVR caller) and weak-prepatch / weak-mode-flip below.
* CONTROL-FLOW-EFFECT: NOT APPLICABLE. scoring_estimator_proba is a pure value
  computation -- no raise/return-effect/side-effect dimension is invisible to
  the value abstraction (the result IS the modeled observable). Omitted.
* POSITIVE CONTROL + ADMISSIBILITY: present below.

The free region is the impl block; each variant is built by _swap on _BASE,
editing ONLY inside # impl-start / # impl-end -- the frozen spec
(axioms/pure/pre/post-conditions) is never touched.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-11578"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl body, verbatim from model.py, strictly between (and including)
# the marker lines. Swapping this whole block edits ONLY the free region.
_GOLD = '''    # impl-start
    # The scoring estimator inherits the caller's multiclass mode, so its
    # probability output is that mode's transform of the decision row.
    effective_mode = caller_mode  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): inline the mode dispatch directly on
# caller_mode instead of calling the @Pure selector scoring_proba. scoring_proba
# is @Pure, so the verifier unfolds it; this branch returns exactly the same
# vector (proba_softmax(d) in multinomial mode, else proba_ovr(d)). A
# structurally-different (helper inlined) but provably CORRECT impl. MUST verify;
# else SPEC-TOO-STRONG. No framing/invariant obligations exist (straight-line
# impl, no loop), so nothing to drop.
# ---------------------------------------------------------------------------
_POS_INLINE = '''    # impl-start
    if caller_mode == MULTINOMIAL:
        return proba_softmax(d)
    return proba_ovr(d)
    # impl-end'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): same inlining but with the OVR branch tested
# FIRST (branch reorder, the directive-preferred structural reshape over a
# loop-direction flip). Still returns proba_ovr(d) for OVR and proba_softmax(d)
# otherwise == scoring_proba(caller_mode, d). MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_REORDER = '''    # impl-start
    if caller_mode == OVR:
        return proba_ovr(d)
    return proba_softmax(d)
    # impl-end'''


# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold computation, but FIRST assert (at impl entry) that
# both precondition clauses are establishable for the actual F2P-shaped input --
# the multiclass-mode tag is in domain (R1) and the audited distinctness fact R2
# holds, so the two transforms genuinely differ on the witness row. If a normal
# F2P-shaped input could not establish the Requires this would fail =>
# PRECOND-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS = '''    # impl-start
    # The precondition is non-vacuous for a normal (multiclass-scoring) input:
    Assert(caller_mode == OVR or caller_mode == MULTINOMIAL)        # R1 in domain
    Assert(transforms_differ())                                    # R2 holds
    Assert(proba_softmax(witness_decision()) != proba_ovr(witness_decision()))
    effective_mode = caller_mode  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end'''


# ---------------------------------------------------------------------------
# UNIQUENESS / reject rivals (each MUST be rejected by a postcondition).
# ---------------------------------------------------------------------------

# (a) PREPATCH twin: ignore the caller's mode, force OVR (this is exactly the
#     pre-patch LogisticRegression(fit_intercept=fit_intercept), whose multi_class
#     defaults to 'ovr'). Returns proba_ovr(d) always; fails P1/P2 on the
#     multinomial caller (the verifier cannot prove proba_ovr(d)==proba_softmax(d),
#     and P4 separately forbids the ovr vector in multinomial mode on the witness).
_W_PREPATCH = '''    # impl-start
    effective_mode = OVR  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end'''

# (b) MODE-FLIP: invert the mode, so multinomial callers get the OVR transform
#     and vice versa. Fails P1/P2/P3 on both modes.
_W_FLIP = '''    # impl-start
    effective_mode = OVR if caller_mode == MULTINOMIAL else MULTINOMIAL  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end'''

# (c) PARTIAL-DOMAIN: hardcode MULTINOMIAL. Correct on the multinomial caller,
#     WRONG on the OVR caller (returns proba_softmax(d) where proba_ovr(d) is
#     required). Fails P1/P3 on caller_mode == OVR.
_W_ALWAYS_MULTI = '''    # impl-start
    effective_mode = MULTINOMIAL  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end'''


SPEC_TESTS = [
    {
        "id": "pos-inline-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_INLINE),
        "rationale": "structurally-different CORRECT impl: inline the mode "
        "dispatch on caller_mode (return proba_softmax(d) for MULTINOMIAL else "
        "proba_ovr(d)) instead of calling the @Pure selector scoring_proba. "
        "scoring_proba is @Pure and unfolds to exactly this, so P1 "
        "(Result()==scoring_proba(caller_mode,d)) holds reflexively. Must verify; "
        "else SPEC-TOO-STRONG (the spec would reject a faithful inlining).",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_REORDER),
        "rationale": "correct reshape: test the OVR branch first (return "
        "proba_ovr(d) for OVR else proba_softmax(d)) -- a branch reorder of the "
        "gold dispatch (directive-preferred over a loop flip). Equals "
        "scoring_proba(caller_mode,d) on both modes. Must verify; else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-precond-nonvacuous",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "the precondition is non-vacuous for a normal F2P-shaped "
        "input: caller_mode is in {OVR,MULTINOMIAL} (R1) and the audited "
        "distinctness R2 (transforms_differ) holds, so the two transforms "
        "genuinely differ on the witness row. Must verify; else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-prepatch-ovr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_PREPATCH),
        "refinement": "this IS the pre-patch bug: LogisticRegression("
        "fit_intercept=fit_intercept) omits multi_class, which defaults to 'ovr', "
        "so the throw-away scoring estimator runs one-vs-rest regardless of the "
        "caller. predict_proba then returns the one-vs-rest vector, and the "
        "probabilistic scorer (neg_log_loss) reads the WRONG probabilities -- the "
        "FAIL_TO_PASS test_logistic_cv_multinomial_score[neg_log_loss-...] FAILS "
        "(model_prepatch.py is this skeleton, G-DIFF). A verifying rival here "
        "would be a true verify-not-resolve break.",
        "rationale": "rejected by postcondition P1 Result()==scoring_proba("
        "caller_mode,d) on the caller_mode==MULTINOMIAL case (returns proba_ovr(d) "
        "where proba_softmax(d) is required; the two opaque transforms are not "
        "provably equal). P2 and P4 independently forbid the ovr vector in "
        "multinomial mode.",
    },
    {
        "id": "weak-mode-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_FLIP),
        "refinement": "its faithful real patch is LogisticRegression(multi_class="
        "('ovr' if multi_class=='multinomial' else 'multinomial')) -- the scoring "
        "estimator runs the OPPOSITE mode to the caller, so a multinomial helper "
        "feeds one-vs-rest probabilities (and vice versa) to the scorer. The F2P "
        "neg_log_loss multinomial test reads the wrong (one-vs-rest) vector and "
        "FAILS. A verify-not-resolve break.",
        "rationale": "rejected by postcondition P1: for caller_mode==MULTINOMIAL "
        "it returns proba_ovr(d) != required proba_softmax(d) (and symmetrically "
        "for OVR), so Result()==scoring_proba(caller_mode,d) cannot be proven; P2/"
        "P3/P4 also fail.",
    },
    {
        "id": "weak-always-multinomial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_ALWAYS_MULTI),
        "refinement": "partial-domain: its faithful real patch hardcodes "
        "LogisticRegression(multi_class='multinomial'), ignoring the caller. It is "
        "correct for a multinomial helper but WRONG for an ovr helper -- the "
        "one-vs-rest scoring path (e.g. the ovr branches of the score tests / "
        "test_logistic_cv_mock_scorer, and the PASS_TO_PASS that exercise "
        "multi_class='ovr') now read softmax probabilities. The ovr-mode P2P "
        "scorers FAIL. A verify-not-resolve break on the OVR sub-domain.",
        "rationale": "rejected by postcondition P1/P3 on the caller_mode==OVR "
        "case: returns proba_softmax(d) where proba_ovr(d) is required, so "
        "Result()==scoring_proba(OVR,d) and Implies(caller_mode==OVR, "
        "Result()==proba_ovr(d)) cannot be proven.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane: the bundle has ONE A-consumed @ContractOnly axiom (transforms_differ)
# plus two A-reference transforms (proba_softmax/proba_ovr) validated end-to-end
# by axiom_check.py / G-AX. We re-derive that validation as in-Docker probes
# against the REAL scikit-learn callees the gold patch leaves UNCHANGED
# (extmath.softmax, base._predict_proba_lr, the predict_proba mode dispatch).
#
# axiom-soundness (transforms_differ): the EXISTENTIAL distinctness must HOLD --
#   there is a multiclass decision row where the real softmax and one-vs-rest
#   predict_proba transforms differ, AND a probabilistic (neg-log-loss) score
#   distinguishes the modes (which is why the F2P test discriminates). If no
#   witness existed the axiom would be UNSOUND. We also confirm the two A-refs
#   ARE the real predict_proba branches (softmax / normalised one-vs-rest) and
#   that decision_function is mode-independent (so the mode's only observable
#   effect is the transform selection -- the modeled behaviour).
#
# axiom-containment: the caller (scoring_estimator_proba) reaches the transforms
#   ONLY through scoring_proba(caller_mode in {OVR,MULTINOMIAL}, d) and
#   transforms_differ()'s witness row. The axiom's domain is exactly multiclass
#   decision rows (n_classes >= 2 per witness_decision's len>=2), which is what
#   _log_reg_scoring_path passes (>= 3-class fits in the F2P). Every
#   caller-reachable decision row is a valid input to softmax / _predict_proba_lr
#   (any finite real per-class row), so containment holds: there is no
#   caller-reachable input outside the axiom's Requires domain.
# ---------------------------------------------------------------------------

_PROBE_SOUNDNESS = r'''
import sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.utils.extmath import softmax

def real_softmax(decision_2d):
    return softmax(np.asarray(decision_2d, dtype=np.float64), copy=True)

def real_ovr(decision_2d):
    prob = np.asarray(decision_2d, dtype=np.float64).copy()
    prob *= -1
    np.exp(prob, prob)
    prob += 1
    np.reciprocal(prob, prob)
    prob /= prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob

def _fitted_clf(multi_class, coef, intercept, classes):
    clf = LogisticRegression(multi_class=multi_class)
    clf.coef_ = np.asarray(coef, dtype=np.float64)
    clf.intercept_ = np.asarray(intercept, dtype=np.float64)
    clf.classes_ = np.asarray(classes)
    return clf

rng = np.random.RandomState(11578)

# (1) the two A-references ARE the real predict_proba branches, and
#     decision_function is mode-independent (the modeled invariant).
for _ in range(3000):
    n_classes = rng.randint(3, 6)
    n_features = rng.randint(2, 5)
    n_samples = rng.randint(1, 4)
    coef = rng.uniform(-3, 3, size=(n_classes, n_features))
    intercept = rng.uniform(-2, 2, size=(n_classes,))
    X = rng.uniform(-3, 3, size=(n_samples, n_features))
    classes = np.arange(n_classes)
    clf_m = _fitted_clf("multinomial", coef, intercept, classes)
    clf_o = _fitted_clf("ovr", coef, intercept, classes)
    decision = clf_m.decision_function(X)
    if not np.allclose(decision, clf_o.decision_function(X)):
        print("FAIL: decision_function is NOT mode-independent")
        sys.exit(1)
    if not np.allclose(clf_m.predict_proba(X), real_softmax(decision)):
        print("FAIL: multinomial predict_proba != softmax(decision)")
        sys.exit(1)
    if not np.allclose(clf_o.predict_proba(X), real_ovr(decision)):
        print("FAIL: ovr predict_proba != normalised one-vs-rest")
        sys.exit(1)

# (2) transforms_differ() EXISTENTIAL: a multiclass witness row exists where the
#     two transforms differ, AND a neg-log-loss score distinguishes the modes.
witness_found = False
score_sensitive = False
for _ in range(5000):
    n_classes = rng.randint(3, 6)
    decision = rng.uniform(-4, 4, size=(1, n_classes))
    p_soft = real_softmax(decision)[0]
    p_ovr = real_ovr(decision)[0]
    if not np.allclose(p_soft, p_ovr, atol=1e-9):
        witness_found = True
        true_k = rng.randint(0, n_classes)
        if abs((-np.log(p_soft[true_k])) - (-np.log(p_ovr[true_k]))) > 1e-6:
            score_sensitive = True
            break

if not witness_found:
    print("FAIL: no witness decision row where softmax != one-vs-rest "
          "(transforms_differ would be UNSOUND)")
    sys.exit(1)
if not score_sensitive:
    print("FAIL: neg-log-loss never distinguished the modes on the witness "
          "(the F2P probabilistic scorer could not discriminate)")
    sys.exit(1)

print("AX-SOUND OK: predict_proba routes by multi_class (softmax vs one-vs-rest);"
      " decision_function mode-independent; transforms_differ witness exists and"
      " neg-log-loss discriminates the modes")
sys.exit(0)
'''


_PROBE_CONTAINMENT = r'''
import sys
import numpy as np
from sklearn.utils.extmath import softmax

def real_softmax(decision_2d):
    return softmax(np.asarray(decision_2d, dtype=np.float64), copy=True)

def real_ovr(decision_2d):
    prob = np.asarray(decision_2d, dtype=np.float64).copy()
    prob *= -1
    np.exp(prob, prob)
    prob += 1
    np.reciprocal(prob, prob)
    prob /= prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob

# Containment: the caller (scoring_estimator_proba) reaches the transforms ONLY
# through scoring_proba(caller_mode in {OVR, MULTINOMIAL}, d) and the witness
# decision row. The axiom domain is "a multiclass decision row" (n_classes >= 2,
# per witness_decision len>=2). Enumerate exactly the decision-row shapes the
# caller can produce -- any finite real per-class row with >= 2 classes (the
# F2P/_log_reg_scoring_path fits >= 3 classes) -- and assert each is a VALID
# input to BOTH real transforms (no error, well-defined finite probabilities
# summing to 1). A caller-reachable row that the transforms could NOT handle
# would be AXIOM-TOO-WEAK-FOR-CALLER.
rng = np.random.RandomState(2718)
n_checked = 0
for _ in range(5000):
    n_classes = rng.randint(2, 8)            # >= 2 classes (multiclass witness)
    # span the reachable magnitude regime, incl. boundary/sentinel rows the
    # caller's decision_function could yield (small, large, negative, mixed).
    scale = rng.choice([0.0, 1e-3, 1.0, 6.82, 20.0])   # 6.82 = real fit absmax
    decision = rng.uniform(-scale, scale, size=(1, n_classes)) if scale > 0 \
               else np.zeros((1, n_classes))
    for transform, name in ((real_softmax, "softmax"), (real_ovr, "one-vs-rest")):
        p = transform(decision)
        if p.shape != (1, n_classes):
            print("FAIL: %s changed the row width (containment)" % name)
            sys.exit(1)
        if not np.all(np.isfinite(p)):
            print("FAIL: %s produced non-finite probabilities on a "
                  "caller-reachable row (AXIOM-TOO-WEAK-FOR-CALLER)" % name)
            sys.exit(1)
        if not np.allclose(p.sum(axis=1), 1.0, atol=1e-9):
            print("FAIL: %s row does not sum to 1 on a caller-reachable row"
                  % name)
            sys.exit(1)
    n_checked += 1

print("AX-CONTAIN OK: every caller-reachable multiclass decision row (>=2 "
      "classes, incl. the 0/large-magnitude boundaries) is a valid input to "
      "both real transforms; %d shapes checked" % n_checked)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-transforms-differ",
        "axiom": "transforms_differ",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "the A-consumed existential transforms_differ must hold: a "
        "multiclass decision row exists where the real softmax and one-vs-rest "
        "predict_proba transforms differ, and a neg-log-loss score discriminates "
        "the modes (why the F2P test passes only when the estimator inherits the "
        "mode). Also confirms the two A-references ARE the real predict_proba "
        "branches and decision_function is mode-independent. If the witness did "
        "not exist (or the transforms were equal) the axiom would be AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-decision-rows",
        "axiom": "transforms_differ",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "containment: every decision row the caller can actually "
        "reach (any finite real per-class row with >= 2 classes, incl. the "
        "zero/large-magnitude boundaries) is a valid input to BOTH real transforms "
        "(well-defined finite probabilities summing to 1, row width preserved). No "
        "caller-reachable input lies outside the axiom's multiclass-decision-row "
        "domain, so it is not AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
