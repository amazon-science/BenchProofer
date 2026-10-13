#!/usr/bin/env python
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-14087.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The bundle models two independent decisions taken in the
`refit=False` branch of `LogisticRegressionCV.fit` (mapping.md):

  decision 1 — chooseLayout(req, eff):
      coefficient-aggregation layout, chosen by the EFFECTIVE multiclass strategy
      `eff` (the resolved `_check_multi_class(...)` value), NOT the raw requested
      `req` (`self.multi_class`, possibly 'auto').
          chooseLayout = perClassLayout if eff == 'ovr' else jointLayout

  decision 2 — ratioEntry(combinedPenalty, ratio):
      the per-class mixing-ratio summary entry, recorded as the computed ratio
      mean only under the combined-penalty ('elasticnet') regime, else absent.
          ratioEntry = some(ratio) if combinedPenalty else none

Two legs:

ORACLE leg — drive the REAL patched `LogisticRegressionCV.fit(refit=False)` over
the `{l2, elasticnet} x {ovr, multinomial, auto}` config grid on fixed 3-class and
binary datasets. We capture the effective strategy by wrapping
`_check_multi_class`, and observe `lrcv.l1_ratio_` (presence/absence) and that the
fit completes with `coef_.shape == (n_classes, n_features)` (the observable
consequence of choosing the coefficient layout by the effective strategy). Each
observation is diffed against the Lean-impl shadow.

FUZZ leg — >=1e5 randomized `(req, eff, penalty, ratio)` draws diffed between the
shadow (transliteration of the Lean impls) and an INDEPENDENT transliteration of
the gold patch's `if` logic. Zero disagreements required.

Exit 0 iff zero disagreements across both legs. stdlib + numpy + sklearn only.
Pinned seed: 14087 (also in mapping.md).
"""
import random
import sys
import warnings

SEED = 14087
N_FUZZ = 120_000  # >= 1e5

STRATS = ('ovr', 'multinomial', 'auto')
PENALTIES = ('l2', 'elasticnet')


# ---- shadow: transliteration of the Lean implementations --------------------

def shadow_choose_layout(req, eff):
    # implementation_chooseLayout: select by EFFECTIVE strategy only.
    # returns 'perClassLayout' / 'jointLayout'
    return 'perClassLayout' if eff == 'ovr' else 'jointLayout'


def shadow_ratio_entry(combined_penalty, ratio):
    # implementation_ratioEntry: some(ratio) iff combined-penalty regime.
    # returns ('some', ratio) / ('none', None)
    return ('some', ratio) if combined_penalty else ('none', None)


# ---- independent transliteration of the gold patch's `if` logic -------------

def gold_choose_layout(self_multi_class, eff_multi_class):
    # gold patch line 2173:  if multi_class == 'ovr':  (the EFFECTIVE value)
    if eff_multi_class == 'ovr':
        return 'perClassLayout'
    else:
        return 'jointLayout'


def gold_ratio_entry(self_penalty, ratio):
    # gold patch lines 2181-2185:
    #   if self.penalty == 'elasticnet':
    #       self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
    #   else:
    #       self.l1_ratio_.append(None)
    if self_penalty == 'elasticnet':
        return ('some', ratio)
    else:
        return ('none', None)


# ---- effective-strategy reference (unchanged _check_multi_class) ------------

def eff_reference(multi_class, solver, n_classes):
    # mirrors _check_multi_class resolution (logistic.py:457-471), unchanged code
    if multi_class == 'auto':
        if solver == 'liblinear':
            return 'ovr'
        elif n_classes > 2:
            return 'multinomial'
        else:
            return 'ovr'
    return multi_class


# ---- oracle leg: real patched fit -------------------------------------------

def _install_eff_capture():
    import sklearn.linear_model.logistic as L
    rec = {}
    orig = L._check_multi_class

    def spy(multi_class, solver, n_classes):
        out = orig(multi_class, solver, n_classes)
        rec['eff'] = out
        return out

    L._check_multi_class = spy

    def restore():
        L._check_multi_class = orig

    return restore, rec


def run_oracle_leg():
    import numpy as np
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegressionCV

    disagreements = 0
    checked = 0

    # n_classes == 3 dataset (the F2P configuration) and a binary dataset
    # (the issue's IndexError configuration: multi_class='auto' -> eff 'ovr').
    datasets = []
    X3, y3 = make_classification(n_samples=200, n_classes=3, n_informative=3,
                                 n_features=20, random_state=0)
    datasets.append((3, X3, y3))
    X2, y2 = make_classification(n_samples=200, n_classes=2, n_informative=3,
                                 n_features=20, random_state=0)
    datasets.append((2, X2, y2))

    Cs = np.logspace(-4, 4, 3)

    restore, rec = _install_eff_capture()
    try:
        for n_classes, X, y in datasets:
            n_features = X.shape[1]
            # report shape: binary collapses n_classes -> 1 internally
            report_n = 1 if n_classes == 2 else n_classes
            for penalty in PENALTIES:
                # Pass l1_ratios as a numpy array: in the refit=False elasticnet
                # branch the real code does `l1_ratios_[best_indices_l1]` with a
                # numpy index array, which a plain Python list cannot handle
                # (pre-existing sklearn indexing quirk, unrelated to the modeled
                # ratioEntry decision).  An ndarray indexes correctly.
                l1_ratios = np.array([0.0, 1.0]) if penalty == 'elasticnet' else None
                for req in STRATS:
                    rec.clear()
                    lrcv = LogisticRegressionCV(
                        penalty=penalty, Cs=Cs, solver='saga',
                        l1_ratios=l1_ratios, random_state=0,
                        multi_class=req, refit=False, tol=1e-2, max_iter=50)
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        lrcv.fit(X, y)
                    eff = rec.get('eff')
                    checked += 1

                    # ---- decision 2: l1_ratio_ presence vs shadow -----------
                    l1r = np.asarray(lrcv.l1_ratio_)
                    # 'none' regime -> all entries are None (object array)
                    real_absent = all(v is None for v in l1r.ravel().tolist())
                    sh = shadow_ratio_entry(penalty == 'elasticnet', 1.0)
                    shadow_absent = (sh[0] == 'none')
                    if real_absent != shadow_absent:
                        disagreements += 1
                        print(f"DISAGREE ratioEntry penalty={penalty} req={req} "
                              f"n_classes={n_classes}: real_absent={real_absent} "
                              f"shadow_absent={shadow_absent} l1_ratio_={l1r!r}")

                    # ---- decision 1: layout-by-effective consistency --------
                    # The gold code picks the layout by `eff`; the observable
                    # consequence is a successful fit with the expected coef_
                    # shape. Confirm the shadow's eff-based choice agrees with the
                    # gold transliteration, and that the real fit realized it
                    # (coef_ shape correct, no IndexError).
                    sh_layout = shadow_choose_layout(req, eff)
                    gold_layout = gold_choose_layout(req, eff)
                    if sh_layout != gold_layout:
                        disagreements += 1
                        print(f"DISAGREE chooseLayout(shadow/gold) req={req} "
                              f"eff={eff}: {sh_layout} vs {gold_layout}")
                    if tuple(lrcv.coef_.shape) != (report_n, n_features):
                        disagreements += 1
                        print(f"DISAGREE coef_.shape penalty={penalty} req={req} "
                              f"n_classes={n_classes}: got {lrcv.coef_.shape} "
                              f"want {(report_n, n_features)}")
                    # eff must match the unchanged resolution reference
                    if eff != eff_reference(req, 'saga', n_classes):
                        disagreements += 1
                        print(f"DISAGREE eff resolution req={req} "
                              f"n_classes={n_classes}: real {eff} "
                              f"ref {eff_reference(req, 'saga', n_classes)}")
    finally:
        restore()
    return checked, disagreements


# ---- fuzz leg: shadow vs gold transliteration -------------------------------

def run_fuzz_leg():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0
    n_class_choices = [2, 3, 4]
    for _ in range(N_FUZZ):
        req = rng.choice(STRATS)
        penalty = rng.choice(PENALTIES)
        n_classes = rng.choice(n_class_choices)
        ratio = rng.choice([0.0, 0.25, 0.5, 1.0, 2.0, 7.0])
        eff = eff_reference(req, 'saga', n_classes)

        sh_layout = shadow_choose_layout(req, eff)
        gold_layout = gold_choose_layout(req, eff)
        if sh_layout != gold_layout:
            disagreements += 1
            if disagreements <= 5:
                print(f"FUZZ DISAGREE layout req={req} eff={eff}: "
                      f"{sh_layout} vs {gold_layout}")

        sh_entry = shadow_ratio_entry(penalty == 'elasticnet', ratio)
        gold_entry = gold_ratio_entry(penalty, ratio)
        if sh_entry != gold_entry:
            disagreements += 1
            if disagreements <= 5:
                print(f"FUZZ DISAGREE ratioEntry penalty={penalty} ratio={ratio}: "
                      f"{sh_entry} vs {gold_entry}")
        checked += 1
    return checked, disagreements


def main():
    total_checked = 0
    total_dis = 0

    try:
        oc, od = run_oracle_leg()
        total_checked += oc
        total_dis += od
        print(f"oracle leg: checked={oc} disagreements={od}")
    except Exception as e:  # pragma: no cover
        print(f"oracle leg error: {e!r}")
        print("status=error")
        return 2

    fc, fd = run_fuzz_leg()
    total_checked += fc
    total_dis += fd
    print(f"fuzz leg: checked={fc} disagreements={fd}")

    print(f"checked={total_checked} disagreements={total_dis}")
    if total_dis == 0:
        print(f"status=pass conformance OK ({total_checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {total_dis} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
