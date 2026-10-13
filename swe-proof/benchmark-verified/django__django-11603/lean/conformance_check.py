#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-11603.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_construct` skeleton and diffs it against the REAL patched
aggregate classes over the full discrete input matrix plus >=1e5 randomized
draws.

  observable of `Aggregate.__init__`:
    * does constructing `Cls(expr, distinct=…, filter=…)` raise TypeError
      ("… does not allow distinct.")  -> Except.error AggError.distinctNotAllowed
    * else it constructs successfully, recording self.distinct / self.filter
      -> Except.ok { kind, distinct, filter }

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import sys
import tempfile

SEED = 20240612
N_RANDOM = 120_000  # >= 1e5


def setup_django():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "testapp"))
    open(os.path.join(d, "testapp", "__init__.py"), "w").close()
    open(os.path.join(d, "testapp", "models.py"), "w").close()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "testapp"],
        USE_TZ=True,
    )
    django.setup()


# ---- the modeled per-kind policy (post-patch desired behavior) -------------
# This mirrors `permitsDistinct` in Solution.lean. It is the contract under
# test; G-CONF confirms the REAL patched classes match it.
PERMITS = {
    "avg": True, "count": True, "sum": True,
    "max": False, "min": False, "stddev": False, "variance": False,
}


def shadow_construct(kind, distinct, filter_present):
    # transliteration of problem_spec_construct / implementation_construct
    if distinct and not PERMITS[kind]:
        return ("error",)
    return ("ok", distinct, filter_present)


def main():
    setup_django()
    from django.db.models import F, Q
    from django.db.models.aggregates import (
        Avg, Count, Sum, Max, Min, StdDev, Variance,
    )

    # AggKind <-> concrete aggregate class
    kinds = [
        ("avg", Avg), ("count", Count), ("sum", Sum), ("max", Max),
        ("min", Min), ("stddev", StdDev), ("variance", Variance),
    ]
    SENTINEL_FILTER = Q(rating__gt=3)

    def real(cls, distinct, filter_present):
        expr = F("rating")
        kw = {"distinct": distinct}
        if filter_present:
            kw["filter"] = SENTINEL_FILTER
        try:
            inst = cls(expr, **kw)
        except TypeError as e:
            if "does not allow distinct" in str(e):
                return ("error",)
            raise
        fp = inst.filter is not None
        return ("ok", bool(inst.distinct), fp)

    cases = []
    for kname, _ in kinds:
        for distinct in (True, False):
            for filter_present in (True, False):
                cases.append((kname, distinct, filter_present))

    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        kname, _ = rng.choice(kinds)
        cases.append((kname, rng.choice([True, False]),
                      rng.choice([True, False])))

    cls_by_kind = dict(kinds)
    disagreements = 0
    checked = 0
    for kname, distinct, filter_present in cases:
        got = real(cls_by_kind[kname], distinct, filter_present)
        exp = shadow_construct(kname, distinct, filter_present)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH kind={kname} distinct={distinct} "
                      f"filter_present={filter_present}: real={got} shadow={exp}")

    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s) over {checked} checks")
    return 1


if __name__ == "__main__":
    sys.exit(main())
