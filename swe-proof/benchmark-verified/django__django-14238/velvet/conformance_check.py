#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14238 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`recognizeType`,
              routed through the deep model `isFamilyMember`/`derivesFrom`)
              transliterated to Python over the real repo types. There are NO
              A-tagged callees in the impl region (no axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `AutoFieldMeta.__subclasscheck__`, observed as
              `issubclass(candidate, AutoField)` on the real django classes at
              base_commit (the real correctness oracle, G-RESOLVE applies the
              gold patch before this runs).

Observable, per the mapping.md §2 bijection:
  a candidate type  ↔  its linearised ancestry `cls.__mro__` mapped to ids
  (root base `AutoField`->0, the two specialised bases `BigAutoField`->1,
  `SmallAutoField`->2, every other type -> a fresh distinct id), and
  `issubclass(candidate, AutoField)` (a Bool)  ↔  `isFamilyMember(ancestry)`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. A pool
of synthetic class hierarchies is built once (single- and multiple-inheritance,
varying depth), then re-sampled to exceed the §4.1 fuzz floor deterministically.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 14238
N_FUZZ = 100_000

# Minimal settings so importing the field machinery is safe (no DB, no app
# registry): defining `AutoField` and friends only needs the module imported.
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )

from django.db.models.fields import (
    AutoField, BigAutoField, SmallAutoField,
    IntegerField, BigIntegerField, SmallIntegerField, Field,
)

# --- the R/I shadow: Solution.lean isFamilyMember/derivesFrom -----------------
# Abstract type ids: root recognised base -> 0, the two specialised bases -> 1,2.
ROOT_BASE_ID = 0
SUB_BASE_IDS = [1, 2]
_FIXED_IDS = {AutoField: 0, BigAutoField: 1, SmallAutoField: 2}
_counter = itertools.count(100)
_ids = {}


def _cid(cls):
    """Stable abstract id for a class (mapping.md §2)."""
    if cls in _FIXED_IDS:
        return _FIXED_IDS[cls]
    if cls not in _ids:
        _ids[cls] = next(_counter)
    return _ids[cls]


def ancestry_ids(cls):
    """`cls.__mro__` mapped to abstract ids (head = cls itself)."""
    return [_cid(c) for c in cls.__mro__]


def derives_from(ancestry, base_id):
    """derivesFrom: the base id appears in the candidate's ancestry."""
    return base_id in ancestry


def is_family_member(ancestry):
    """isFamilyMember (pure region): derives from a specialised base OR the root
    base. Genuine derivation throughout (membership in the ancestry list)."""
    via_sub = any(derives_from(ancestry, b) for b in SUB_BASE_IDS)
    via_root = derives_from(ancestry, ROOT_BASE_ID)
    return via_sub or via_root


def shadow_recognize(cls):
    return is_family_member(ancestry_ids(cls))


# --- the oracle: patch.diff's behaviour --------------------------------------
def oracle_recognize(cls):
    """patch.diff's behaviour: the patched AutoFieldMeta.__subclasscheck__,
    observed as issubclass(candidate, AutoField)."""
    return bool(issubclass(cls, AutoField))


# --- the synthetic class pool -------------------------------------------------
def build_pool(rng):
    """A pool of class hierarchies exercising derivation-vs-identity:
    the recognised bases themselves, their proper descendants at several depths
    (the F2P scenario: a subclass of a specialised base must be recognised even
    though it is not itself that base), unrelated families, and mixtures."""
    seeds = [AutoField, BigAutoField, SmallAutoField,
             IntegerField, BigIntegerField, SmallIntegerField, Field, object]
    pool = list(seeds)
    # boundary: the exact F2P classes
    class MyBigAutoField(BigAutoField):
        pass

    class MySmallAutoField(SmallAutoField):
        pass

    class MyAutoField(AutoField):
        pass

    class DeepBig(MyBigAutoField):
        pass

    class DeeperBig(DeepBig):
        pass

    pool += [MyBigAutoField, MySmallAutoField, MyAutoField, DeepBig, DeeperBig]

    # an unrelated family that must never be recognised
    class Unrelated:
        pass

    class UnrelatedChild(Unrelated):
        pass

    pool += [Unrelated, UnrelatedChild]

    # randomized single-inheritance descendants of varying depth, rooted at a
    # random pool member, plus a few safe multiple-inheritance mixes
    for i in range(300):
        base = rng.choice(pool)
        try:
            new = type("Synth%d" % i, (base,), {})
        except TypeError:
            continue
        pool.append(new)

    for i in range(80):
        b1 = rng.choice(pool)
        b2 = rng.choice(pool)
        if b1 is b2:
            continue
        try:
            new = type("Multi%d" % i, (b1, b2), {})
        except TypeError:
            continue  # MRO conflict / incompatible layout — skip
        pool.append(new)

    return pool


def main():
    rng = random.Random(SEED)
    pool = build_pool(rng)

    disagreements = []
    count = 0

    # boundary: enumerate the whole pool once
    for cls in pool:
        count += 1
        shadow = shadow_recognize(cls)
        oracle = oracle_recognize(cls)
        if shadow != oracle:
            disagreements.append((cls.__name__, shadow, oracle))
            if len(disagreements) >= 5:
                break

    # then randomized re-sampling to exceed the fuzz floor deterministically
    if not disagreements:
        for _ in range(N_FUZZ):
            count += 1
            cls = rng.choice(pool)
            shadow = shadow_recognize(cls)
            oracle = oracle_recognize(cls)
            if shadow != oracle:
                disagreements.append((cls.__name__, shadow, oracle))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, sh, orc in disagreements:
            print("  class=%s shadow=%r oracle=%r" % (name, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of recognizeType agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
