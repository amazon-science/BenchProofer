#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11848 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`resolveAbbreviatedYear` / `resolvedFullYear`) transliterated to
              Python over the *real* repo type (`int`), via the mapping.md
              bijection (Lean `Int` ↔ Python `int`). The impl region has NO
              A-tagged callee — the reference year `cur` is a free input, and
              the resolution is plain integer arithmetic — so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.utils.http.parse_http_date` applied at base_commit. We
              feed it an RFC850 date string carrying the two-digit year `yy`,
              with `datetime.datetime.utcnow()` mocked to a controlled
              reference year `cur` (exactly the mechanism the gold F2P test
              uses), and read back the resolved full year via
              `datetime.utcfromtimestamp(parsed).year`.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); stdlib only
(`unittest.mock` is stdlib — the same tool the gold test_patch uses). The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import calendar
import datetime as _dt
import random
import sys
from unittest import mock

SEED = 11848
N_FUZZ = 100_000

# Capture the REAL datetime class ONCE, before any patching. `parse_http_date`
# does `import datetime`, so `http.datetime` IS the datetime *module* object —
# the same object as our `_dt`. Patching `http.datetime.datetime` therefore
# rebinds `_dt.datetime` too; any construction routed through `_dt.datetime`
# while the patch is live would re-enter the stand-in. We pin the genuine class
# here so real `datetime` construction (and `utcfromtimestamp`) never touch the
# patched attribute — exactly what the gold test_patch does by capturing
# `from datetime import datetime` at import time and using `side_effect`.
_REAL_DATETIME = _dt.datetime

# Reference-year window over which the oracle is well defined: the resolved
# full year must be a valid `datetime` year (1..9999). With yy in 0..99 the
# resolved year lies in (cur-100, cur+50], so cur in [200, 9900] keeps it valid
# while still exercising both the roll-back and the in-century branch at every
# residue class. (mapping.md §4 pins this window with the seed.)
CUR_LO, CUR_HI = 200, 9900

# RFC850 date template: '\w{6,9}, DD-Mon-YY HH:MM:SS GMT'. Fixed day/month/time;
# only the two-digit year varies. 'Sunday' (6 chars) satisfies \w{6,9}.
_RFC850 = "Sunday, 06-Nov-%02d 08:49:37 GMT"
_FIXED_MONTH, _FIXED_DAY = 11, 6
_FIXED_H, _FIXED_M, _FIXED_S = 8, 49, 37


def shadow_resolve(yy, cur):
    """resolvedFullYear (Solution.lean pure region) transliterated to int.

    The backward branch of resolveAbbreviatedYear computes exactly this:
        cc = cur % 100; century = cur - cc
        (yy + century - 100) if yy - cc > 50 else (yy + century)
    """
    cc = cur % 100
    century = cur - cc
    return (yy + century - 100) if (yy - cc) > 50 else (yy + century)


def oracle_resolve(yy, cur):
    """patch.diff's behaviour: the patched parse_http_date resolves the
    two-digit year `yy` relative to utcnow().year == cur. Returns the resolved
    full year observed via the produced epoch timestamp."""
    from django.utils import http  # patched module (gold applied by harness)

    # Mirror the gold test_patch exactly: patch `django.utils.http.datetime.datetime`
    # with a Mock whose `side_effect` is the REAL datetime class (so `datetime(...)`
    # construction inside parse_http_date stays genuine) and whose `utcnow` returns
    # our controlled reference year. Using `_REAL_DATETIME` (captured pre-patch)
    # avoids the self-recursion that arises because `http.datetime` is the shared
    # `datetime` module object.
    with mock.patch("django.utils.http.datetime.datetime") as mocked_datetime:
        mocked_datetime.side_effect = _REAL_DATETIME
        mocked_datetime.utcnow.return_value = _REAL_DATETIME(cur, 11, 6, 8, 49, 37)
        parsed = http.parse_http_date(_RFC850 % yy)
    return _REAL_DATETIME.utcfromtimestamp(parsed).year


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the F2P matrix + cutoff edges.
    yield (69, 2019)
    yield (70, 2019)
    yield (94, 2019)
    yield (70, 2020)   # the discriminating case (old: 1970, gold: 2070)
    yield (71, 2020)
    yield (0, 2048)
    yield (99, 2048)
    # cutoff edges of the >50 rule at several reference residues
    for cur in (2000, 2019, 2020, 2050, 2099, 2100):
        for yy in (0, 1, 49, 50, 51, 52, 69, 70, 71, 98, 99):
            yield (yy, cur)
    for _ in range(n):
        yield (rng.randint(0, 99), rng.randint(CUR_LO, CUR_HI))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for yy, cur in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_resolve(yy, cur)
        oracle = oracle_resolve(yy, cur)
        if shadow != oracle:
            disagreements.append((yy, cur, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for yy, cur, sh, orc in disagreements:
            print("  yy=%02d cur=%d shadow=%r oracle=%r" % (yy, cur, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveAbbreviatedYear agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
