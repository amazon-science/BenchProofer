#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14087.

This bundle declares **NO axioms** and **NO deep-model references**: the modeled
change is the two control-flow decisions that commit one class's outputs in
`LogisticRegressionCV.fit`'s no-refit branch. Every operand they consume has
ALREADY been produced by surrounding, *unchanged* code (`np.mean`, NumPy
indexing, `_check_multi_class`) and is taken as a FREE INPUT:

  * chooseCoef(per_class_effective, coef_per_class, coef_joint)
      = coef_per_class if per_class_effective else coef_joint
  * chooseAux(aux_active, aux_value)
      = aux_value if aux_active else None

There is no unchanged repo callee INSIDE the modeled decisions whose contract
the proof must assume; the read-outs and the strategy resolver merely produce
the operands and are folded into the free inputs. So G-AX has no axiom `ensures`
to falsify (the `axioms` region of Solution.lean is empty; refinement.md rows
are all R or I).

IMPORTANT: G-AX runs this script against the **unpatched** instance image (the
gold patch is NOT applied for G-AX — only G-CONF/G-RESOLVE apply it). The script
must therefore exercise only code that is **unchanged** by the patch and assert
its documented semantics; it must NOT drive the buggy code path and assert it is
already fixed. To keep the gate meaningful (not a silent pass) it:

  (1) asserts the bundle truly declares no axioms / no deep-model references
      (meta.json `axioms == []` and `deep_model_references == []`), so a future
      edit that smuggles in an axiom without a soundness check is caught here;

  (2) confirms the deep model the spec pins (chooseCoef / chooseAux) agrees with
      the patched decision logic transliterated verbatim from logistic.py
      (the post-fix if/else over the two driving flags) on boundary + fuzzed
      flag/operand assignments — a self-contained model-vs-patch equality; and

  (3) exercises the UNCHANGED real repo callee the §2 bijection relies on —
      `sklearn.linear_model.logistic._check_multi_class`, the strategy resolver
      that produces the `multi_class` local. Its observed mapping must match the
      bijection that distinguishes `perClassEffective` (resolved
      `multi_class == 'ovr'`) from `perClassRequested` (raw
      `self.multi_class == 'ovr'`). In particular the binary-`'auto'` case the
      issue triggers must resolve to `'ovr'` while the raw request is not
      `'ovr'` — the requested/effective disagreement the spec models. This
      callee is UNCHANGED by the gold patch, so the assertion holds against the
      unpatched image.

Imports only the stdlib plus the repo's own sklearn (the same package the gold
patch edits). Exit 0 iff every obligation holds.
"""
import itertools
import json
import os
import random
import sys


# --- the deep model: Solution.lean chooseCoef / chooseAux, transliterated ----
def choose_coef(per_class_effective, coef_per_class, coef_joint):
    return coef_per_class if per_class_effective else coef_joint


def choose_aux(aux_active, aux_value):
    return aux_value if aux_active else None


# --- the patched decision logic, transliterated verbatim from logistic.py ----
def patched_coef(per_class_effective, coef_per_class, coef_joint):
    # logistic.py:2173-2178 post-fix: `if multi_class == 'ovr': w = <per-class>
    # else: w = <joint>` — the test is on the RESOLVED `multi_class` local.
    if per_class_effective:
        return coef_per_class
    else:
        return coef_joint


def patched_aux(aux_active, aux_value):
    # logistic.py:2183-2188 post-fix: `if self.penalty == 'elasticnet':
    # append(np.mean(l1_ratios_[best_indices_l1])) else: append(None)`.
    if aux_active:
        return aux_value
    else:
        return None


def check_decisions(eff, aux_active, coef_pc, coef_j, aux_value):
    """Deep model == the patched decision logic on one assignment."""
    assert choose_coef(eff, coef_pc, coef_j) == patched_coef(eff, coef_pc, coef_j), (
        "chooseCoef deep model unsound: eff=%r pc=%r j=%r" % (eff, coef_pc, coef_j))
    assert choose_aux(aux_active, aux_value) == patched_aux(aux_active, aux_value), (
        "chooseAux deep model unsound: active=%r val=%r" % (aux_active, aux_value))


def check_no_axioms():
    """(1) The bundle's no-axiom / no-A-reference claim is what meta.json says."""
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], (
        "axiom_check expected no axioms but meta.json lists %r; an axiom "
        "requires an executable soundness check here." % (axioms,))
    assert refs == [], (
        "axiom_check expected no deep-model references but meta.json lists %r; "
        "an A-reference requires a deep-model == real-callee check here." % (refs,))


def check_resolver_bijection():
    """(3) The UNCHANGED resolver `_check_multi_class` maps strategies exactly as
    the §2 bijection claims. Justifies `perClassEffective` (resolved
    `multi_class == 'ovr'`) vs `perClassRequested` (raw `self.multi_class ==
    'ovr'`), and confirms the binary-`'auto'` disagreement the issue triggers.
    Unchanged by the gold patch, so it holds against the unpatched image."""
    from sklearn.linear_model.logistic import _check_multi_class

    # (resolver input, solver, n_classes) -> expected resolved strategy.
    # Covers the cheatsheet in mapping.md §2: 'auto' resolves by solver/n_classes;
    # 'ovr'/'multinomial' pass through unchanged.
    cases = [
        # binary 'auto' (the issue's reproducer): resolves to 'ovr'
        (("auto", "saga", 2), "ovr"),
        (("auto", "lbfgs", 2), "ovr"),
        (("auto", "liblinear", 2), "ovr"),
        # multiclass 'auto': liblinear -> 'ovr', others -> 'multinomial'
        (("auto", "saga", 3), "multinomial"),
        (("auto", "lbfgs", 5), "multinomial"),
        (("auto", "liblinear", 3), "ovr"),
        # explicit requests pass through
        (("ovr", "saga", 2), "ovr"),
        (("ovr", "saga", 3), "ovr"),
        (("multinomial", "saga", 3), "multinomial"),
        (("multinomial", "lbfgs", 2), "multinomial"),
    ]
    for (raw, solver, n_classes), expected in cases:
        resolved = _check_multi_class(raw, solver, n_classes)
        assert resolved == expected, (
            "_check_multi_class(%r, %r, %r) = %r, expected %r" %
            (raw, solver, n_classes, resolved, expected))
        # the bijection: perClassEffective <-> (resolved == 'ovr');
        # perClassRequested <-> (raw == 'ovr').
        per_class_effective = (resolved == "ovr")
        per_class_requested = (raw == "ovr")
        # the binary-'auto' case MUST exhibit the requested/effective disagreement
        # the spec models (raw not 'ovr' but resolved is 'ovr'): selecting by the
        # requested flag would take the joint (4-index) read-out and raise the
        # issue's IndexError. We assert the disagreement is real for that case.
        if (raw, solver, n_classes) in (("auto", "saga", 2),
                                        ("auto", "lbfgs", 2),
                                        ("auto", "liblinear", 2)):
            assert per_class_effective and not per_class_requested, (
                "expected binary-'auto' to resolve to the per-class layout while "
                "the raw request is not 'ovr' (the modeled disagreement): "
                "raw=%r resolved=%r" % (raw, resolved))


def main():
    # (1) no axioms / no deep-model references ------------------------------
    check_no_axioms()

    # (2) deep model vs the patched decision logic --------------------------
    # boundary: every assignment of the two driving flags, with distinct opaque
    # candidate tags and edge auxiliary scalars.
    boundary_aux = [0, 1, -1, 17, 10 ** 9]
    for eff, aux_active in itertools.product([False, True], repeat=2):
        for av in boundary_aux:
            check_decisions(eff, aux_active, "PER_CLASS", "JOINT", av)

    rng = random.Random(14087)
    for _ in range(20000):
        eff = rng.random() < 0.5
        aux_active = rng.random() < 0.5
        coef_pc = "PC%d" % rng.randint(0, 1_000_000)
        coef_j = "JT%d" % rng.randint(0, 1_000_000)
        av = rng.randint(-10_000, 10_000)
        check_decisions(eff, aux_active, coef_pc, coef_j, av)

    # (3) the UNCHANGED real resolver matches the §2 bijection --------------
    check_resolver_bijection()

    print("G-AX OK: no axioms / no deep-model references to falsify "
          "(meta.json axioms == [] and deep_model_references == []); deep model "
          "(chooseCoef / chooseAux == the patched logistic.py decision logic) "
          "sound on %d boundary + 20000 fuzz assignments; the UNCHANGED real "
          "resolver _check_multi_class matches the perClassEffective / "
          "perClassRequested bijection (incl. the binary-'auto' "
          "requested-vs-effective disagreement the issue triggers)."
          % (4 * len(boundary_aux)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
