#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-14087
(plan §4.1).

Refutes the R/I refinement legs of the two changed decisions modeled in
Solution.lean (`recordClassResult` → `chooseCoef` / `chooseAux`). There are NO
axioms in this bundle: every op is a pure two-way choice over free inputs (two
candidate coefficient vectors, an averaged auxiliary scalar, three boolean
flags), so the whole impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched decision logic instead of
reading the booleans back off a full `LogisticRegressionCV.fit` run:
  The two decisions live deep inside `LogisticRegressionCV.fit`'s no-refit
  branch, after a full cross-validation path has produced `coefs_paths`,
  `best_indices`, `l1_ratios_`, and the resolved `multi_class` local. Exercising
  the REAL branch for every (flag, candidate) assignment would require driving a
  complete SAGA/liblinear CV fit per point — impractical and not isolating the
  modeled decision. So, per the worker prompt, the ORACLE is the patched decision
  logic transliterated VERBATIM from the gold-patched
  sklearn/linear_model/logistic.py (lines 2173-2188):

    # coefficient selection (post-fix tests the RESOLVED `multi_class`)
    if multi_class == 'ovr':
        w = <per-class read-out>          # coefByPerClass
    else:
        w = <joint read-out>              # coefByJoint
    # auxiliary append (post-fix guarded by the penalty)
    if self.penalty == 'elasticnet':
        self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))   # some v
    else:
        self.l1_ratio_.append(None)                                   # none

  The surrounding read-outs (`np.mean(...)`) and the resolver
  `_check_multi_class` are UNCHANGED by the patch — pre- and post-patch both run
  them — and only PRODUCE the operands the decision chooses between / records.
  They are folded into the free inputs (mapping.md §3). As a non-vacuous
  end-to-end witness we ALSO drive the real patched estimator on the issue's
  reproducer (binary, multi_class='auto', refit=False) and on the F2P l2 cases,
  confirming no IndexError and the contracted no-refit attribute shapes.

  The SHADOW is the model from Solution.lean (chooseCoef + chooseAux).
  We differential-test SHADOW vs ORACLE over every assignment of the boolean
  flags (perClassEffective, perClassRequested, auxActive) and tagged candidate
  vectors / auxiliary scalar — an exhaustive cube plus seeded fuzz. Exit 0 iff
  zero disagreements. stdlib + sklearn only.
"""
import itertools
import random
import sys

SEED = 14087
N_FUZZ = 100_000

# Opaque tags standing for the two candidate coefficient vectors (mapping.md
# §2: only WHICH candidate is selected is observed, never its numbers).
PER_CLASS = "coefByPerClass"
JOINT = "coefByJoint"


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def shadow_choose_coef(per_class_effective, coef_per_class, coef_joint):
    """chooseCoef: select by the EFFECTIVE strategy flag."""
    return coef_per_class if per_class_effective else coef_joint


def shadow_choose_aux(aux_active, aux_value):
    """chooseAux: record the averaged value only when the auxiliary mode is in
    effect, else `none` (modeled as Python None)."""
    return aux_value if aux_active else None


# ---- ORACLE: gold-patched logistic.py decision logic, transliterated -------

def oracle_choose_coef(per_class_effective, coef_per_class, coef_joint):
    """Post-fix `:2173-2178`: `if multi_class == 'ovr': w = <per-class> else: w =
    <joint>`. The test is on the RESOLVED `multi_class` local (mapping.md §2),
    i.e. exactly `per_class_effective`. (The raw `self.multi_class` requested
    flag does NOT enter the patched decision.)"""
    if per_class_effective:
        return coef_per_class
    return coef_joint


def oracle_choose_aux(aux_active, aux_value):
    """Post-fix `:2183-2188`: `if self.penalty == 'elasticnet': append(np.mean(
    l1_ratios_[best_indices_l1])) else: append(None)`. `aux_active` ⇔ the penalty
    is 'elasticnet'; the appended value is the averaged scalar or None."""
    if aux_active:
        return aux_value
    return None


def fuzz_points(n, rng):
    # Exhaustive over the three boolean flags; the candidate tags and the aux
    # scalar are varied alongside. perClassRequested is carried for parity with
    # the spec signature but does NOT affect the patched decision — the shadow
    # selects by perClassEffective, so any requested value must agree.
    flags = list(itertools.product([False, True], repeat=3))  # eff, req, aux
    aux_vals = [0, 1, -3, 17, 1000000]
    for eff, req, aux in flags:
        for av in aux_vals:
            yield (eff, req, PER_CLASS, JOINT, aux, av)
    for _ in range(n):
        eff = rng.random() < 0.5
        req = rng.random() < 0.5
        aux = rng.random() < 0.5
        # distinct opaque candidate tags so a wrong selection is observable
        cpc = "PC%d" % rng.randint(0, 1_000_000)
        cj = "JT%d" % rng.randint(0, 1_000_000)
        av = rng.randint(-10_000, 10_000)
        yield (eff, req, cpc, cj, aux, av)


def end_to_end_witness():
    """Drive the REAL patched estimator on the issue's reproducer and the F2P
    shapes. Pre-fix this raised IndexError (binary 'auto' → resolved 'ovr', the
    joint 4-index read-out on a 3-D array) and produced a malformed l1_ratio_ for
    non-elastic-net penalties. Post-fix: no raise, and the no-refit attribute
    shapes hold."""
    import numpy as np
    from sklearn.linear_model import LogisticRegressionCV

    # (1) the issue's exact reproducer: binary, multi_class default ('auto'),
    #     refit=False — must NOT raise IndexError.
    rng = np.random.RandomState(29)
    X = rng.normal(size=(200, 3))
    beta = rng.normal(size=3)
    intercept = rng.normal(size=None)
    y = np.sign(intercept + X @ beta)
    LogisticRegressionCV(cv=3, solver='saga', tol=1e-2,
                         refit=False).fit(X, y)  # raised pre-fix

    # (2) the F2P attribute-shape contract for refit=False across penalties and
    #     resolved strategies (l2 = the FAIL_TO_PASS cases).
    from sklearn.datasets import make_classification
    n_classes, n_features = 3, 20
    Xm, ym = make_classification(n_samples=200, n_classes=n_classes,
                                 n_informative=n_classes,
                                 n_features=n_features, random_state=0)
    Cs = np.logspace(-4, 4, 3)
    for penalty in ('l2', 'elasticnet'):
        l1_ratios = np.linspace(0, 1, 2) if penalty == 'elasticnet' else None
        for multi_class in ('ovr', 'multinomial', 'auto'):
            lrcv = LogisticRegressionCV(
                penalty=penalty, Cs=Cs, solver='saga', l1_ratios=l1_ratios,
                random_state=0, multi_class=multi_class, refit=False).fit(Xm, ym)
            assert lrcv.C_.shape == (n_classes,), (
                "C_ shape %r for penalty=%s multi_class=%s"
                % (lrcv.C_.shape, penalty, multi_class))
            assert lrcv.l1_ratio_.shape == (n_classes,), (
                "l1_ratio_ shape %r for penalty=%s multi_class=%s"
                % (lrcv.l1_ratio_.shape, penalty, multi_class))
            assert lrcv.coef_.shape == (n_classes, n_features), (
                "coef_ shape %r for penalty=%s multi_class=%s"
                % (lrcv.coef_.shape, penalty, multi_class))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for eff, req, cpc, cj, aux, av in fuzz_points(N_FUZZ, rng):
        count += 1
        s_coef = shadow_choose_coef(eff, cpc, cj)
        o_coef = oracle_choose_coef(eff, cpc, cj)
        s_aux = shadow_choose_aux(aux, av)
        o_aux = oracle_choose_aux(aux, av)
        if s_coef != o_coef or s_aux != o_aux:
            disagreements.append((eff, req, cpc, cj, aux, av,
                                  s_coef, o_coef, s_aux, o_aux))
            if len(disagreements) >= 8:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  %r" % (d,))
        return 1

    try:
        end_to_end_witness()
    except Exception as e:  # noqa: BLE001 — surface any failure as G-CONF fail
        print("G-CONF FAIL: end-to-end patched estimator witness failed: %r" % e)
        return 1

    print("G-CONF OK: R/I shadow of recordClassResult (chooseCoef + chooseAux) "
          "agrees with the patched logistic.py decision logic on %d checks "
          "(exhaustive cube + fuzz, seed=%d), 0 disagreements; real patched "
          "LogisticRegressionCV(refit=False) runs the issue reproducer without "
          "IndexError and yields the contracted no-refit attribute shapes."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
