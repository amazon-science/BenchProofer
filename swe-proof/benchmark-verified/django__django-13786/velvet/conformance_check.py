#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13786 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real repo type (`dict`), via the mapping.md
              bijection (`List (String × String)` ↔ dict, set-of-pairs equality).
              The impl seed `mergeMaps baseMap newMap` and the prune `while` fold
              (`eraseKey`/`keyPresent`) are transliterated directly. No A-tagged
              callee appears in the computed `out` (the only A-reference,
              `trackedKeys`, is bound to the real ALTER_OPTION_KEYS — concrete
              data), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the options dict the patched real
              `CreateModel.reduce(AlterModelOptions(...))` emits at base_commit
              with the gold patch applied (the harness applies patch.diff first).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container (the prebuilt
SWE-Bench instance image), stdlib only. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

from django.conf import settings

if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})

from django.db.migrations.operations.models import (  # noqa: E402
    CreateModel, AlterModelOptions,
)

SEED = 13786
N_FUZZ = 100_000
APP_LABEL = "testapp"
MODEL_NAME = "MyModel"

# trackedKeys (A-reference): bound to the real managed-key constant.
TRACKED_KEYS = list(AlterModelOptions.ALTER_OPTION_KEYS)


# --- the R/I shadow: Solution.lean mergeMaps + pruneFold, transliterated ------

def shadow_reduce_options(base_map, new_map):
    """combineTrackedSettings impl region transliterated:
        result := mergeMaps baseMap newMap           -- loop seed
        for k in trackedKeys (backward): result :=    -- prune fold
            result if keyPresent k newMap else eraseKey k result
    `mergeMaps a b` = b over a; `eraseKey k` drops key k; `keyPresent k m` = k∈m."""
    # mergeMaps baseMap newMap
    result = dict(base_map)
    result.update(new_map)
    # the prune while-fold (iteration order is immaterial — each step erases or
    # keeps an independent key; matches pruneFold's set-of-pairs result)
    for k in TRACKED_KEYS:
        if k not in new_map:          # keyPresent k newMap == False
            result.pop(k, None)       # eraseKey k result
    return result


def oracle_reduce_options(base_map, new_map):
    """patch.diff's behaviour: the patched real CreateModel.reduce options out."""
    create = CreateModel(MODEL_NAME, fields=[], options=dict(base_map))
    alter = AlterModelOptions(MODEL_NAME, options=dict(new_map))
    reduced = create.reduce(alter, APP_LABEL)[0]
    return dict(reduced.options)


# --- fuzz inputs --------------------------------------------------------------

NON_TRACKED = ["proxy", "db_table", "app_label", "unique_together", "indexes"]
ALL_KEYS = TRACKED_KEYS + NON_TRACKED
VALUES = ["v0", "v1", "v2", "My Model", "My Model plural", "id"]


def rand_map(rng):
    n = rng.randint(0, len(ALL_KEYS))
    ks = rng.sample(ALL_KEYS, n)
    return {k: rng.choice(VALUES) for k in ks}


def fuzz_inputs(n, rng):
    # boundary cases first (incl. the two F2P configurations)
    yield ({}, {})
    yield ({"verbose_name": "My Model"}, {})
    yield ({"verbose_name": "My Model", "verbose_name_plural": "My Model plural"},
           {"verbose_name": "My Model"})
    yield ({"verbose_name": "old"}, {"verbose_name": "new"})
    yield ({"ordering": "a"}, {})
    yield ({"proxy": "True"}, {})
    yield ({k: "x" for k in TRACKED_KEYS}, {})
    yield ({k: "x" for k in TRACKED_KEYS}, {k: "y" for k in TRACKED_KEYS})
    yield ({"managed": "False", "proxy": "True"}, {"permissions": "p"})
    for _ in range(n):
        yield (rand_map(rng), rand_map(rng))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for base_map, new_map in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_reduce_options(base_map, new_map)
        oracle = oracle_reduce_options(base_map, new_map)
        if shadow != oracle:
            disagreements.append((base_map, new_map, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for b, n, sh, orc in disagreements:
            print("  base=%r new=%r shadow=%r oracle=%r" % (b, n, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of combineTrackedSettings agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
