#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11603 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`avgInit`,
              `sumInit`, routed through the deep model `construct`) transliterated
              to Python over the real repo types. There are NO A-tagged callees
              in the impl region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `django.db.models.Avg` /
              `Sum` constructed at base_commit (the real correctness oracle,
              G-RESOLVE applies the gold patch before this runs).

Observable of a construction, per the mapping.md §2 bijection:
  - whether construction succeeds or raises the "distinct not accepted" error
    (`TypeError`)  ↔  `Except.ok _` vs `Except.error .distinctNotAccepted`;
  - on success, the constructed aggregate's recorded SQL function name and
    its recorded distinct flag  ↔  the `AggState { function, distinct }` payload.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only (the
input space is tiny and total, so the whole cross product is enumerated and
then re-sampled to exceed the §4.1 fuzz floor deterministically). The fuzz seed
is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys

SEED = 11603
N_FUZZ = 100_000

# Configure minimal settings so importing the ORM expression machinery is safe.
# Constructing an aggregate (`Avg('field', distinct=...)`) only wraps the field
# name in an `F()` and runs `Aggregate.__init__`'s guard — it touches neither
# the database nor the populated app registry, so `django.setup()` (which pulls
# in unrelated subsystems) is deliberately avoided.
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )

from django.db.models import Avg, Sum  # patched: allow_distinct = True


# --- the R/I shadow: Solution.lean construct/avgInit/sumInit ------------------
# Per-kind capability `acceptsDistinct` as modeled in the impl region: both
# modeled kinds accept the duplicate-elimination option.
_SHADOW = {
    "AVG": {"cls": Avg, "accepts_distinct": True},
    "SUM": {"cls": Sum, "accepts_distinct": True},
}


def shadow_construct(function, accepts_distinct, distinct):
    """construct (pure region) transliterated. Returns either
    ('error', 'distinctNotAccepted') or ('ok', {function, distinct})."""
    if distinct and not accepts_distinct:
        return ("error", "distinctNotAccepted")
    return ("ok", {"function": function, "distinct": distinct})


def oracle_construct(cls, function, distinct):
    """patch.diff's behaviour: build the real aggregate and observe the result.
    A refused construction surfaces as TypeError (Aggregate.__init__ raises
    when a distinct request is made of a kind that does not accept it)."""
    try:
        agg = cls("a_field", distinct=distinct)
    except TypeError:
        return ("error", "distinctNotAccepted")
    return ("ok", {"function": agg.function, "distinct": bool(agg.distinct)})


def fuzz_inputs(n, rng):
    functions = list(_SHADOW.keys())
    # boundary: full cross product first
    for fn in functions:
        for distinct in (False, True):
            yield (fn, distinct)
    # then randomized re-sampling to exceed the fuzz floor deterministically
    for _ in range(n):
        yield (rng.choice(functions), rng.random() < 0.5)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for fn, distinct in fuzz_inputs(N_FUZZ, rng):
        count += 1
        info = _SHADOW[fn]
        shadow = shadow_construct(fn, info["accepts_distinct"], distinct)
        oracle = oracle_construct(info["cls"], fn, distinct)
        if shadow != oracle:
            disagreements.append((fn, distinct, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fn, d, sh, orc in disagreements:
            print("  function=%r distinct=%r shadow=%r oracle=%r" % (fn, d, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of avgInit/sumInit agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
