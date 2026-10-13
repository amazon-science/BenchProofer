#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-17029 (nagini).

SHADOW: the impl region of model.py's ``clear_all_caches``, copied VERBATIM
below with only the contract calls (Requires / Ensures / MustTerminate)
stripped, together with the minimal ``Registry`` carrier class (its
``__init__`` body, contracts stripped). There are no @Pure helpers and no
@ContractOnly callees (mapping.md section 3: no consumed axioms; the single
external fact is an A-reference on the unchanged stdlib ``functools.cache``,
exercised by axiom_check.py).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``django.apps.registry.Apps.clear_cache``. The gate applies
patch.diff to /testbed and sets PYTHONPATH so imports resolve to the patched
module before this script runs. Each probe drives a real registry (the
default ``django.apps.apps``, made ready via ``settings.configure`` +
``django.setup``) to a chosen starting occupancy on each of its two
``functools.cache``-decorated methods, calls ``clear_cache()``, and reads
both ``cache_info().currsize`` values back.

TYPE BRIDGE (mapping.md section 2): the repo state is the pair of
``cache_info().currsize`` values of ``Apps.get_models`` and
``Apps.get_swappable_settings_name`` (non-negative ints); the model carrier
is the pair of non-negative int fields ``models_cache_occupancy`` /
``swappable_cache_occupancy``. Lowering: read both ``currsize`` values into a
``Registry``; raising: compare the shadow's fields against the ``currsize``
values observed after the real call. The two wrappers are class-level, so
occupancy of the all-models cache is raised with distinct argument tuples
across a pool of auxiliary ``Apps`` instances, and occupancy of the
swappable-name cache with distinct lookup strings; direct
``cache_clear()`` on a wrapper (the stdlib operation, not the function under
check) is used only as setup to reach asymmetric starting states such as
(0, s>0).

INPUT PLAN (>= 1e5 Requires-satisfying inputs — the precondition demands
only two non-negative occupancies plus termination): a boundary battery of
occupancy pairs (both zero, each singly zero, singletons, small mixed pairs,
and large pairs up to the pool capacity), then 100000 random fuzz pairs over
a distribution weighted toward small occupancies with occasional large ones.
The oracle RETURNING on every probe is the executable image of the
MustTerminate obligation. Pinned fuzz seed: 17029. Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs and exits
1. stdlib only.
"""
import json
import random
import sys

SEED = 17029
N_FUZZ = 100000
POOL_SIZE = 300           # 4 distinct get_models argument tuples per instance
MAX_MODELS_OCC = POOL_SIZE * 4
MAX_SWAP_OCC = 1200


# --- impl region of model.py, verbatim with contract calls stripped ----------

class Registry:
    def __init__(self, models_cache_occupancy, swappable_cache_occupancy):
        self.models_cache_occupancy = models_cache_occupancy
        self.swappable_cache_occupancy = swappable_cache_occupancy


def clear_all_caches(registry):
    registry.swappable_cache_occupancy = 0
    registry.models_cache_occupancy = 0


# --- oracle plumbing: a ready real registry + occupancy realization ----------

def _setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
        )
    django.setup()
    from django.apps import apps
    from django.apps.registry import Apps
    # Auxiliary ready registries: each contributes up to 4 distinct
    # argument tuples to the class-level all-models cache.
    pool = [Apps([]) for _ in range(POOL_SIZE)]
    return apps, pool


def _swap_keys():
    """Distinct lookup strings for the swappable-name cache (the cache key
    is the string as passed, so case variants are distinct entries)."""
    keys = ["auth.user", "auth.User", "AUTH.USER",     # real swappable label
            "contenttypes.contenttype", "auth.permission",
            "auth.group", "nosuch.model", "", " ", ".",
            "a.b", "A.b", "a.B", "étude.modèle"]
    i = 0
    while len(keys) < MAX_SWAP_OCC:
        keys.append("fuzzapp%d.model%d" % (i % 97, i))
        i += 1
    return keys


def _fill_models(pool, n):
    """Add n distinct entries to the class-level all-models cache using the
    auxiliary pool (argument tuples disjoint from any internal lookup, which
    uses the default registry with a keyword argument)."""
    added = 0
    for inst in pool:
        for iac in (False, True):
            for isw in (False, True):
                if added >= n:
                    return
                inst.get_models(iac, isw)
                added += 1


def _realize(apps, pool, keys, m_target, s_target):
    """Drive the two wrapper caches to exactly (m_target, s_target)."""
    gm = apps.get_models
    sw = apps.get_swappable_settings_name
    sw.cache_clear()
    gm.cache_clear()
    for i in range(s_target):
        sw(keys[i])
    # A swappable-name miss primes one all-models entry internally; drop any
    # primed entries when the target is smaller, then fill to the target.
    cur = gm.cache_info().currsize
    if cur > m_target:
        gm.cache_clear()
        cur = 0
    _fill_models(pool, m_target - cur)


# --- differential driver ------------------------------------------------------

def _trial(apps, pool, keys, m_target, s_target):
    """One probe. Returns an error string on disagreement, else None."""
    _realize(apps, pool, keys, m_target, s_target)
    gm = apps.get_models
    sw = apps.get_swappable_settings_name
    m0 = gm.cache_info().currsize
    s0 = sw.cache_info().currsize
    if m0 != m_target or s0 != s_target:
        return ("INTERNAL: realized occupancies (%d, %d) != targets (%d, %d)"
                % (m0, s0, m_target, s_target))
    if not (m0 >= 0 and s0 >= 0):
        return "INTERNAL: negative currsize (%d, %d)" % (m0, s0)

    # shadow on the lowered state
    reg = Registry(m0, s0)
    clear_all_caches(reg)
    shadow = (reg.models_cache_occupancy, reg.swappable_cache_occupancy)

    # oracle: the real patched reset; returning is the termination image
    apps.clear_cache()
    real = (gm.cache_info().currsize, sw.cache_info().currsize)

    if shadow != real:
        return ("DISAGREEMENT on starting occupancies "
                "(models=%d, swappable=%d):\n"
                "  shadow (impl region)          -> "
                "(models=%d, swappable=%d)\n"
                "  real (patched Apps.clear_cache) -> "
                "(models=%d, swappable=%d)"
                % (m0, s0, shadow[0], shadow[1], real[0], real[1]))
    return None


def boundary_pairs():
    pairs = [
        (0, 0), (1, 0), (0, 1), (1, 1),               # empty / singly filled
        (2, 1), (1, 2), (2, 2), (3, 0), (0, 3),
        (4, 4), (7, 5), (16, 3), (3, 16), (31, 31),
        (64, 64), (100, 100), (255, 1), (1, 255),
        (MAX_MODELS_OCC, 0), (0, MAX_SWAP_OCC),        # each cache maximal
        (MAX_MODELS_OCC, MAX_SWAP_OCC),                # both maximal
        (MAX_MODELS_OCC - 1, MAX_SWAP_OCC - 1),
    ]
    return pairs


def main():
    apps, pool = _setup()
    keys = _swap_keys()

    checked = 0
    boundary = boundary_pairs()
    for m, s in boundary:
        err = _trial(apps, pool, keys, m, s)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        r = rng.random()
        if r < 0.85:                       # small occupancies dominate
            m = rng.randint(0, 8)
            s = rng.randint(0, 8)
        elif r < 0.97:                     # medium
            m = rng.randint(0, 64)
            s = rng.randint(0, 64)
        else:                              # occasional large
            m = rng.randint(0, MAX_MODELS_OCC)
            s = rng.randint(0, MAX_SWAP_OCC)
        err = _trial(apps, pool, keys, m, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched Apps.clear_cache on %d "
          "occupancy pairs (%d boundary + %d fuzz, seed %d); every oracle "
          "call returned (termination); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
