#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-12973.

The bundle models ONE value: the boolean `LassoLarsIC.fit` delivers to the data-
preparation step (`LinearModel._preprocess_data`'s `copy` argument), as a function
of the estimator's configured `self.copy_X` and the optional per-call `copy_X`
argument (mapping.md):

    configured : Bool          (self.copy_X, set at construction)
    call : Option Bool         (fit's copy_X arg: None / True / False)
    -> the `copy` boolean _preprocess_data is called with

Post-patch rule: the delivered boolean is the per-call value when one is supplied
(`copy_X is not None`), and the configured value otherwise:
    resolveCopy(configured, call) == call if call is not None else configured

ORACLE — the REAL patched `LassoLarsIC.fit`. We monkeypatch
`LinearModel._preprocess_data` to record the `copy` boolean it is built with and
then raise a sentinel to abort the (expensive) remainder of `fit`. The genuine
`__init__ -> fit(copy_X=...) -> (if copy_X is None: copy_X = self.copy_X) ->
_preprocess_data(..., copy_X)` plumbing runs; the recorded `copy` is the delivered
boolean.

SHADOW — transliteration of `implementation_deliveredCopy`:
`resolveCopy(configured, call)` = `call if call is not None else configured`.

We diff the recorded (oracle) delivered boolean against the shadow for every fuzzed
`(self.copy_X, fit copy_X)` over `self.copy_X in {True, False}` and
`fit copy_X in {None, True, False}`.

stdlib + numpy/sklearn only. Pinned seed: 12973 (also in mapping.md).
"""
import random
import sys

import numpy as np


SEED = 12973
N_FUZZ = 120_000   # >= 1e5 fuzzed (configured, call) draws


class _Captured(Exception):
    pass


def _install_capture():
    """Wrap LinearModel._preprocess_data to record its `copy` arg and abort.
    Returns (restore_fn, record_list)."""
    from sklearn.linear_model.base import LinearModel

    record = []
    orig = LinearModel._preprocess_data

    def spy(X, y, fit_intercept, normalize=False, copy=True, *a, **k):
        record.append(bool(copy))
        raise _Captured()

    # _preprocess_data is a staticmethod on LinearModel; replace with our spy.
    LinearModel._preprocess_data = staticmethod(spy)

    def restore():
        LinearModel._preprocess_data = staticmethod(orig)

    return restore, record


def oracle_delivered(LassoLarsIC, X, y, configured, call, record):
    """Run the real fit; return the `copy` bool delivered to _preprocess_data."""
    record.clear()
    est = LassoLarsIC(copy_X=configured, precompute=False)
    try:
        if call is None:
            est.fit(X, y)
        else:
            est.fit(X, y, copy_X=call)
    except _Captured:
        pass
    if not record:
        return None
    return record[-1]


def shadow_delivered(configured, call):
    # resolveCopy(configured, call) = call.getD configured
    return configured if call is None else call


def main() -> int:
    try:
        from sklearn.linear_model import LassoLarsIC
    except Exception as e:  # pragma: no cover
        print(f"import error: {e}")
        print("status=error")
        return 2

    restore, record = _install_capture()
    try:
        rng = random.Random(SEED)
        nprng = np.random.RandomState(SEED)
        X = nprng.normal(0, 1, (40, 4))
        y = X[:, 2].copy()

        configured_vals = [True, False]
        call_vals = [None, True, False]

        checked = 0
        # exhaustive boundary sweep over the 2 x 3 grid
        for configured in configured_vals:
            for call in call_vals:
                got = oracle_delivered(LassoLarsIC, X, y, configured, call, record)
                want = shadow_delivered(configured, call)
                if got != want:
                    print(f"DISAGREE edge configured={configured} call={call}: "
                          f"oracle={got} shadow={want}")
                    print("status=fail")
                    return 1
                checked += 1

        # fuzz the same grid repeatedly (deterministic order via seed)
        for _ in range(N_FUZZ):
            configured = rng.choice(configured_vals)
            call = rng.choice(call_vals)
            got = oracle_delivered(LassoLarsIC, X, y, configured, call, record)
            want = shadow_delivered(configured, call)
            if got != want:
                print(f"DISAGREE fuzz configured={configured} call={call}: "
                      f"oracle={got} shadow={want}")
                print("status=fail")
                return 1
            checked += 1

        print(f"checked={checked} disagreements=0")
        print("status=pass")
        return 0
    finally:
        restore()


if __name__ == "__main__":
    sys.exit(main())
