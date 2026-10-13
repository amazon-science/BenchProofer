#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-14087 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. Both
modeled decisions in the `refit=False` branch of `LogisticRegressionCV.fit` are
pure control-flow predicates:

  * chooseLayout — selects the coefficient-aggregation layout from the EFFECTIVE
    multiclass strategy `eff` (a free input, produced upstream by the unchanged
    `_check_multi_class`);
  * ratioEntry — records the mixing-ratio entry iff the combined-penalty regime
    is in force (`combinedPenalty`, a free Bool), carrying the computed mean as
    the free input `ratio`.

Each `correct_<name>` is proved for ALL values of its free inputs, so no callee
property is consumed and there is no opaque callee to validate. The R legs of
both impls are validated by G-CONF (conformance_check.py), which drives the real
patched `fit`. There is therefore no callee contract to check here.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-14087",
    "reason": "no consumed callee axiom and no A-reference; both impls are pure "
              "R/I decision logic over free inputs (validated by G-CONF)",
}))
sys.exit(0)
