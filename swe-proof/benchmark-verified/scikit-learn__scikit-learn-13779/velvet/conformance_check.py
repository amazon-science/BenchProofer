#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13779.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`validate`)
              transliterated to Python over the real container type (the
              `estimators` list of `(name, step)` pairs), via the mapping.md
              bijection: a member's `present` bit <-> `step is not None`, its
              `supports` bit <-> `has_fit_parameter(step, 'sample_weight')` for a
              present step, its `name` <-> the member label. The scan skips
              absent members and reports the FIRST present-unsupported member.
              There is NO A-tagged callee left symbolic in the impl region, so
              `conf_skip=false`.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `_BaseVoting.fit`
              (driven via `VotingRegressor.fit(X, y, sample_weight=...)`) applied
              at base_commit with the gold patch applied (the harness applies
              patch.diff before this runs). We observe whether the validation
              block raises the "does not support sample weights" ValueError and,
              if so, which member label it names; otherwise the fit proceeds.

They must agree on every input: same verdict (raise vs no-raise) and, on the
raise leg, the same offending member label. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
with sklearn + numpy. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

import numpy as np

from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import VotingRegressor

SEED = 13779
N_FUZZ = 100_000

# A tiny target the mock regressors fit instantly on (4 samples, 1 feature).
_X = np.arange(4, dtype=float).reshape(4, 1)
_Y = np.arange(4, dtype=float)
_SW = np.ones(4, dtype=float)

_MSG = "does not support sample weights"


class _Supported(RegressorMixin, BaseEstimator):
    """A member whose fit ACCEPTS a per-sample weighting parameter
    (has_fit_parameter(..., 'sample_weight') -> True). Fits to a no-op."""

    def fit(self, X, y=None, sample_weight=None):
        self.is_fitted_ = True
        return self

    def predict(self, X):
        return np.zeros(np.asarray(X).shape[0])


class _Unsupported(RegressorMixin, BaseEstimator):
    """A member whose fit does NOT accept a per-sample weighting parameter
    (has_fit_parameter(..., 'sample_weight') -> False)."""

    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def predict(self, X):
        return np.zeros(np.asarray(X).shape[0])


# member kind codes used by the fuzzer
_ABSENT, _SUPPORTED, _UNSUPPORTED = 0, 1, 2


def _build_estimator(kind):
    if kind == _ABSENT:
        return None
    if kind == _SUPPORTED:
        return _Supported()
    return _Unsupported()


# --- the R/I shadow: Solution.lean `validate`, transliterated ----------------
def shadow_verdict(kinds, names):
    """`validate (members)`: skip absent members; report the FIRST present member
    that does not support a per-sample weighting; else ok."""
    for kind, name in zip(kinds, names):
        present = (kind != _ABSENT)
        supports = (kind == _SUPPORTED)
        if present and not supports:
            return ("error", name)
    return ("ok", None)


# --- the oracle: patch.diff's real patched VotingRegressor.fit ----------------
def oracle_verdict(kinds, names):
    """patch.diff behaviour: run the real patched validation block and report its
    observable outcome (raise-with-label vs proceed)."""
    estimators = [(name, _build_estimator(kind))
                  for kind, name in zip(kinds, names)]
    voter = VotingRegressor(estimators=estimators)
    try:
        voter.fit(_X, _Y, sample_weight=_SW)
    except ValueError as exc:
        msg = str(exc)
        if _MSG in msg:
            # extract the offending label from "Underlying estimator 'NAME' ..."
            label = msg.split("'")[1] if "'" in msg else None
            return ("error", label)
        # any other ValueError is outside the modeled validation block -> surface
        return ("other", msg)
    return ("ok", None)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4). Names are simple/unique; at least
    # one present member always present (avoid the "all None" ValueError, which
    # is a different, unmodeled branch).
    def named(kinds):
        return (kinds, ["e%d" % i for i in range(len(kinds))])

    yield named([_SUPPORTED])                         # single supported -> ok
    yield named([_UNSUPPORTED])                       # single unsupported -> err e0
    yield named([_ABSENT, _SUPPORTED])                # absent skipped -> ok  (THE FIX)
    yield named([_ABSENT, _UNSUPPORTED])              # absent skipped, then err e1
    yield named([_SUPPORTED, _ABSENT])                # ok (absent last)
    yield named([_UNSUPPORTED, _SUPPORTED])           # first unsupported -> err e0
    yield named([_SUPPORTED, _UNSUPPORTED])           # err e1
    yield named([_UNSUPPORTED, _UNSUPPORTED])         # first wins -> err e0
    yield named([_ABSENT, _ABSENT, _SUPPORTED])       # two absent skipped -> ok
    yield named([_ABSENT, _UNSUPPORTED, _UNSUPPORTED])# err e1 (first present-unsupp)
    yield named([_SUPPORTED, _ABSENT, _UNSUPPORTED])  # err e2

    for _ in range(n):
        width = rng.randint(1, 6)
        kinds = [rng.choice([_ABSENT, _SUPPORTED, _UNSUPPORTED]) for _ in range(width)]
        # guarantee >= 1 present member (else the unmodeled all-None branch)
        if all(k == _ABSENT for k in kinds):
            kinds[rng.randrange(width)] = rng.choice([_SUPPORTED, _UNSUPPORTED])
        yield named(kinds)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for kinds, names in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_verdict(kinds, names)
        oracle = oracle_verdict(kinds, names)
        if shadow != oracle:
            disagreements.append((kinds, names, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for k, nm, sh, orc in disagreements:
            print("  kinds=%r names=%r shadow=%r oracle=%r" % (k, nm, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of validateWeightSupport agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
