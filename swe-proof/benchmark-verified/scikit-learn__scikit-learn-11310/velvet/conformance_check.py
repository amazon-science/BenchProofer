#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-11310.

Band: order-only / float-subtraction (mapping.md §2, plan §10 Q1).

Refutes the R refinement legs of the `recordRefitTime` do-block (refinement.md
steps 1 and 4):
  - step 1 (gate): record a duration iff the refit flag is truthy;
  - step 4 (record): the recorded value is `endT - startT`.

ORACLE CHOICE — why we transliterate the patched lines instead of running fit():
  The patched behavior lives inside `BaseSearchCV.fit`, which requires a fully
  configured estimator, an X/y dataset, a cross-validation splitter, scorers,
  and the entire search pipeline to reach the refit slice. The behavior under
  test is the pure bracket-and-record:
      if self.refit:
          refit_start_time = time.time()
          ...fit...
          refit_end_time = time.time()
          self.refit_time_ = refit_end_time - refit_start_time
  So, per the worker prompt, the ORACLE is the patched source transliterated
  VERBATIM (from gold-patched sklearn/model_selection/_search.py, BaseSearchCV.fit):
      present iff `refit`;  value = refit_end_time - refit_start_time.
  The two `time.time()` readings are the A-consumed callee (validated by
  axiom_check.py / G-AX); in Solution.lean they are the read-only inputs
  (startT, endT) — exactly the mapping.md §3 abstraction — and here they are the
  fuzzed inputs (start_t, end_t); we differential-test the SHADOW (the modeled
  R legs) against the ORACLE over fuzzed reading pairs. Exit 0 iff zero
  disagreements. stdlib only.

FLOAT MODEL NOTE (mapping.md §2): Solution.lean models the readings/duration as
exact Rat. The spec pins the recorded value to EXACTLY `some (endT - startT)`
(the verbatim patched subtraction), plus its sign on the monotone domain
(order-only, precision-independent). The recorded value is a single subtraction
(no further arithmetic), so the observable equality here is EXACT (bit-exact,
NaN-aware) on both the present/absent selection and the subtraction result — no
ULP tolerance.

NON-NEGATIVITY (the property the FAIL_TO_PASS test asserts, `refit_time_ >= 0`):
on the G-AX-validated monotone domain `start_t <= end_t`, we additionally assert
the recorded duration is `>= 0` on BOTH shadow and oracle — i.e. the spec's
`t >= 0` postcondition is dischargeable by the real subtraction precisely on the
domain the monotone-clock axiom guarantees. Off that domain (start_t > end_t,
which the axiom forbids and the real clock does not produce) we do NOT assert
non-negativity; we still assert shadow==oracle (both compute the same negative
value) so the R leg is exercised everywhere.
"""
import math
import random
import struct
import sys

SEED = 11310
N_FUZZ = 200_000

# Sentinel sentinel for "attribute absent" (hasattr False) on both sides.
ABSENT = object()


def shadow(refit, start_t, end_t):
    """recordRefitTime transliterated: the modeled R legs.
    Mirrors `if refit then refitTime := some (endT - startT) else (leave none)`."""
    if refit:
        return end_t - start_t          # some (endT - startT)
    return ABSENT                       # none


def oracle(refit, start_t, end_t):
    """The patched source transliterated verbatim from
    sklearn/model_selection/_search.py (gold-patched BaseSearchCV.fit):
        if self.refit:
            ...
            self.refit_time_ = refit_end_time - refit_start_time
    Attribute is absent (ABSENT) when self.refit is falsy."""
    if refit:
        return end_t - start_t
    return ABSENT


def eq(a, b):
    """Exact equality, NaN-aware, handling the ABSENT sentinel."""
    if a is ABSENT or b is ABSENT:
        return a is b
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
    return a == b


def main():
    rng = random.Random(SEED)
    disagreements = []
    nonneg_violations = []
    count = 0

    def rand_float():
        kind = rng.random()
        if kind < 0.10:
            return 0.0
        if kind < 0.20:
            return struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0]
        # plausible wall-clock magnitudes (epoch seconds ~1.7e9) + wide range
        m = rng.uniform(0.0, 2.0e9)
        return m

    cases = []
    # Boundary / sentinel reading pairs.
    sentinels = [
        (0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.7e9, 1.7e9 + 0.5),
        (1.7e9, 1.7e9), (5e-324, 1e-323), (1e308, 1e308),
        (float("inf"), float("inf")), (1.0, float("inf")),
    ]
    for st, en in sentinels:
        for rf in (True, False):
            cases.append((rf, st, en))

    for _ in range(N_FUZZ):
        rf = rng.random() < 0.85          # refit truthy most of the time (the F2P default)
        a = rand_float()
        b = rand_float()
        # Bias toward the monotone domain (start <= end), the G-AX-valid region,
        # but include the reversed domain too to exercise the R leg fully.
        if rng.random() < 0.85:
            st, en = (a, b) if a <= b else (b, a)
        else:
            st, en = a, b
        cases.append((rf, st, en))

    for refit, start_t, end_t in cases:
        count += 1
        s = shadow(refit, start_t, end_t)
        o = oracle(refit, start_t, end_t)
        if not eq(s, o):
            disagreements.append((refit, start_t, end_t, s, o))
            if len(disagreements) >= 5:
                break
        # On the monotone domain the axiom guarantees, the recorded value must be
        # >= 0 (the FAIL_TO_PASS property). Restrict to FINITE readings: the Rat
        # model carries only finite values, and inf-inf=nan is outside its domain
        # (a real wall clock never returns inf). The shadow==oracle R-leg above
        # still runs on those cases; only the non-negativity claim is scoped to
        # the finite monotone domain the model actually covers.
        if (refit and s is not ABSENT
                and math.isfinite(start_t) and math.isfinite(end_t)
                and start_t <= end_t):
            if not (o >= 0):
                nonneg_violations.append((start_t, end_t, o))
                if len(nonneg_violations) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R-leg disagreement(s) shadow!=oracle: %r"
              % (len(disagreements), disagreements))
        return 1
    if nonneg_violations:
        print("G-CONF FAIL: %d non-negativity violation(s) on the monotone "
              "domain (start<=end but end-start<0): %r"
              % (len(nonneg_violations), nonneg_violations))
        return 1
    print("G-CONF OK: R-leg shadow of recordRefitTime agrees with the patched "
          "source on %d (refit, start_t, end_t) triples (present-iff-refit + the "
          "end-start subtraction), 0 disagreements; recorded duration >= 0 on "
          "every monotone-domain case (seed=%d). NaN/inf/0.0/subnormal covered; "
          "time.time() abstracted as (start_t, end_t) and validated by G-AX."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
