#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13794 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's four impl regions
              transliterated to Python over the *real* repo types
              (`str`, `int`), via the mapping.md bijection:
                deferredConcatLeft  (str) : forced + other
                deferredConcatRight (str) : other  + forced
                deferredSumLeft     (int) : forced + other
                deferredSumRight    (int) : other  + forced
              with success ↔ a normal return and rejection ↔ a raised
              TypeError (mapping.md §2). There are no A-tagged callees.
  * ORACLE  — patch.diff's behaviour: a REAL lazy-value proxy built at
              base_commit WITH the gold patch applied
              (`django.utils.functional.lazy`), exercising the actual `+`
              operator in both operand positions and both result classes.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied by
the harness before this runs), stdlib + django only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13794
N_FUZZ = 100_000

# `lazy` proxies build settings-free when the result class is given explicitly;
# use the identity callable so the underlying value is exactly our test value.
from django.utils.functional import lazy

_lazy_str = lazy(lambda v: v, str)
_lazy_int = lazy(lambda v: v, int)


# --- the R/I shadow: Solution.lean's four impl regions, transliterated -------
# Outcome is encoded as ('ok', value) or ('err',) mirroring Except AddOutcome.

def shadow_concat_left(forced, other):
    return ('ok', forced + other)          # deferredConcatLeft : forced ++ other


def shadow_concat_right(forced, other):
    return ('ok', other + forced)          # deferredConcatRight: other ++ forced


def shadow_sum_left(forced, other):
    return ('ok', forced + other)          # deferredSumLeft : forced + other


def shadow_sum_right(forced, other):
    return ('ok', other + forced)          # deferredSumRight: other + forced


# --- the oracle: the REAL patched proxy's `+` operator -----------------------

def _run(thunk):
    """Run a `+` expression, mapping a normal return to ('ok', value) and a
    TypeError (the rejection the add filter would swallow to '') to ('err',)."""
    try:
        return ('ok', thunk())
    except TypeError:
        return ('err',)


def oracle_concat_left(forced, other):
    # deferred value on the LEFT: proxy.__add__(other)  -> forced + other
    return _run(lambda: _lazy_str(forced) + other)


def oracle_concat_right(forced, other):
    # deferred value on the RIGHT: proxy.__radd__(other) -> other + forced
    return _run(lambda: other + _lazy_str(forced))


def oracle_sum_left(forced, other):
    return _run(lambda: _lazy_int(forced) + other)


def oracle_sum_right(forced, other):
    return _run(lambda: other + _lazy_int(forced))


# --- fuzz inputs -------------------------------------------------------------

def str_inputs(n, rng):
    alphabet = list("abcXYZ 0;#'\"<>&") + ["é", "•"]
    # boundary cases first
    seeds = ["", "a", "string", "lazy", "Joe's", "&amp;", "  ", "x", "abc"]
    for s in seeds:
        for t in seeds:
            yield s, t
    for _ in range(n):
        k1 = rng.randint(0, 12)
        k2 = rng.randint(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(k1))
        t = "".join(rng.choice(alphabet) for _ in range(k2))
        yield s, t


def int_inputs(n, rng):
    seeds = [0, 1, -1, 4, 5, 9, 1000, -1000, 2 ** 40, -(2 ** 40)]
    for a in seeds:
        for b in seeds:
            yield a, b
    for _ in range(n):
        a = rng.randint(-10 ** 9, 10 ** 9)
        b = rng.randint(-10 ** 9, 10 ** 9)
        yield a, b


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- string result class: both operand positions --------------------
    for forced, other in str_inputs(N_FUZZ // 2, rng):
        for shadow_fn, oracle_fn, tag in (
            (shadow_concat_left, oracle_concat_left, "concatLeft"),
            (shadow_concat_right, oracle_concat_right, "concatRight"),
        ):
            count += 1
            sh = shadow_fn(forced, other)
            orc = oracle_fn(forced, other)
            if sh != orc:
                disagreements.append((tag, forced, other, sh, orc))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break

    # --- int result class: both operand positions -----------------------
    if len(disagreements) < 5:
        for forced, other in int_inputs(N_FUZZ // 2, rng):
            for shadow_fn, oracle_fn, tag in (
                (shadow_sum_left, oracle_sum_left, "sumLeft"),
                (shadow_sum_right, oracle_sum_right, "sumRight"),
            ):
                count += 1
                sh = shadow_fn(forced, other)
                orc = oracle_fn(forced, other)
                if sh != orc:
                    disagreements.append((tag, forced, other, sh, orc))
                    if len(disagreements) >= 5:
                        break
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d comparisons:"
              % (len(disagreements), count))
        for tag, f, o, sh, orc in disagreements:
            print("  [%s] forced=%r other=%r shadow=%r oracle=%r"
                  % (tag, f, o, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of the four deferred-add methods agrees with "
          "patch.diff behaviour on %d comparisons (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
