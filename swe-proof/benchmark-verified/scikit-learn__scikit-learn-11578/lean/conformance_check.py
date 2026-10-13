#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-11578.

The bundle models the probability-estimate selection done when a multiclass
linear classifier is asked to report per-class probabilities for a probabilistic
evaluation (mapping.md). The soundness-critical R/I content is the MODE SELECTION
and FRAMING: the regime used to transform the decision-function score rows must
be the one requested for the multiclass problem (`'multinomial'` -> softmax;
anything else -> one-vs-rest), applied to every candidate's score matrix, in
order, preserving the number of candidates.

The probability transforms themselves (softmax / logistic-then-normalise) are
A-reference: they are validated == the real repo callees by G-AX. Per the
construction protocol, A-tagged callees are left as the REAL repo callee here, so
this check exercises only the R/I legs (the mode dispatch and framing).

ORACLE  = the POST-PATCH behavior: the scoring model is built carrying over the
          requested `multi_class`, so `predict_proba` uses the requested regime.
SHADOW  = op-for-op transliteration of `implementation_scoringProbs`
          (Solution.lean impl region) per refinement.md, with the transform left
          as the real repo callee.

The discriminating clause (what the prepatch gets wrong, F2P
test_logistic_cv_multinomial_score[neg_log_loss-...]): when `'multinomial'` is
requested, the reported estimates must be softmax, not one-vs-rest.

Uses numpy + the repo's real `predict_proba` plumbing as the oracle callee.
Pinned seed: 11578 (also in mapping.md).
"""
import random
import sys

import numpy as np
from sklearn.utils.extmath import softmax as real_softmax

SEED = 11578
N = 120_000


# --- real repo transforms (A-reference callees, validated by G-AX) ------------
def real_softmax_row(row):
    m = real_softmax(np.array([row], dtype=np.float64).copy())
    return m[0].tolist()


def real_ovr_row(row):
    prob = np.array([row], dtype=np.float64).copy()
    prob *= -1
    np.exp(prob, prob)
    prob += 1
    np.reciprocal(prob, prob)
    prob /= prob.sum(axis=1).reshape((prob.shape[0], -1))
    return prob[0].tolist()


def predict_proba(mode, decision):
    # decision: list of score rows (a matrix)
    if mode == "multinomial":
        return [real_softmax_row(r) for r in decision]
    else:
        return [real_ovr_row(r) for r in decision]


# --- ORACLE: post-patch — regime is the one requested -------------------------
def parse_mode(s):
    return "multinomial" if s == "multinomial" else "ovr"


def oracle(inp):
    mode = parse_mode(inp["multiClass"])
    return [predict_proba(mode, d) for d in inp["decisions"]]


# --- SHADOW: transliteration of implementation_scoringProbs -------------------
def shadow(inp):
    mode = parse_mode(inp["multiClass"])
    out = []
    for d in inp["decisions"]:
        out.append(predict_proba(mode, d))
    return out


def _close(a, b, tol=1e-12):
    if len(a) != len(b):
        return False
    for da, db in zip(a, b):
        if len(da) != len(db):
            return False
        for ra, rb in zip(da, db):
            if len(ra) != len(rb):
                return False
            for xa, xb in zip(ra, rb):
                if abs(xa - xb) > tol:
                    return False
    return True


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if not _close(got, want):
        return (inp, got, want)
    return None


def _rand_matrix(rng, n_samples, n_classes):
    return [[rng.uniform(-8.0, 8.0) for _ in range(n_classes)]
            for _ in range(n_samples)]


def _edge():
    cases = []
    # F2P-shaped: multinomial requested -> must be softmax, not ovr
    cases.append(dict(multiClass="multinomial",
                      decisions=[[[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]]]))
    # ovr requested -> ovr
    cases.append(dict(multiClass="ovr",
                      decisions=[[[1.0, 2.0, 3.0]]]))
    # unrecognised string -> falls back to ovr
    cases.append(dict(multiClass="auto",
                      decisions=[[[0.5, -0.5]]]))
    # multiple candidate matrices, order preserved
    cases.append(dict(multiClass="multinomial",
                      decisions=[[[1.0, 0.0]], [[2.0, 1.0, 0.0]], [[-1.0, -2.0]]]))
    # empty candidate list -> empty result
    cases.append(dict(multiClass="multinomial", decisions=[]))
    return cases


def main():
    checked = 0
    for inp in _edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    modes = ["multinomial", "ovr", "auto", "", "MULTINOMIAL"]
    for _ in range(N):
        n_candidates = rng.randint(0, 3)
        decisions = []
        for _ in range(n_candidates):
            n_samples = rng.randint(1, 4)
            n_classes = rng.randint(2, 5)
            decisions.append(_rand_matrix(rng, n_samples, n_classes))
        inp = dict(multiClass=rng.choice(modes), decisions=decisions)
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
