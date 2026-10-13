#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15127.

The only kind-A leg in this bundle is an **A-reference**: the deep model
`recomputeTable` (Solution.lean `pure` region) is claimed equal to the REAL
unchanged callee `django.contrib.messages.utils.get_level_tags()`. The changed
operation (the conditional recompute receiver) is modeled directly, NOT behind a
consumed axiom; G-AX validates the deep model against the real callee.

Deep model (as a key->value mapping):
    recomputeTable(base, overrides) == {**base, **overrides}   (overrides win)
Real callee:
    get_level_tags() == {**constants.DEFAULT_TAGS,
                         **getattr(settings, 'MESSAGE_TAGS', {})}

`recomputeTable` here lists `overrides` first then the base entries whose key is
not overridden; read as a dict that is exactly default-overlaid-by-override.

Runs in-container (the prebuilt SWE-Bench instance image). Imports only `django`
(already installed in the image) + stdlib. Exit 0 iff every observation matches.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys

SEED = 15127
N_FUZZ = 100_000


def configure_django():
    """Minimal settings so `get_level_tags()` (which reads `settings`) works."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            INSTALLED_APPS=['django.contrib.messages'],
        )
    django.setup()


def recompute_table(base, overrides):
    """Reference of Solution.lean's deep model `recomputeTable`, as a dict.

    overrides ++ base.filter(key not in overrides), read as first-binding-wins,
    is exactly {**base, **overrides}. We build it the long way (not just
    {**base, **overrides}) so the check actually exercises the model's overlay
    semantics rather than tautologically echoing the callee."""
    result = dict(overrides)  # overrides win
    for k, v in base.items():
        if k not in overrides:
            result[k] = v
    return result


def check_one(base, overrides):
    from django.conf import settings
    from django.contrib.messages import utils
    # Point the real callee's override source at `overrides`.
    settings.MESSAGE_TAGS = dict(overrides)
    real = utils.get_level_tags()                 # real unchanged callee
    model = recompute_table(base, overrides)      # deep model
    assert real == model, (
        "recomputeTable deep model unsound: get_level_tags()=%r, model=%r "
        "(base=%r overrides=%r)" % (real, model, base, overrides))


def main():
    configure_django()
    from django.contrib.messages import constants

    base = dict(constants.DEFAULT_TAGS)           # {10:'debug',20:'info',...}
    keys = list(base.keys())                      # 10,20,25,30,40
    extra_keys = [12, 0, 100, -5, 99]             # non-default levels (cf. F2P key 12)
    tags = ['info', '', 'debug', 'warning', 'error', 'success', 'bad',
            'custom', 'x', 'TAG']

    # --- boundary cases ---------------------------------------------------
    boundary = [
        {},                                       # no override -> defaults
        {20: 'info'},                             # single default key remapped
        {k: '' for k in keys},                    # all defaults blanked
        {10: 'd', 20: 'i', 25: 's', 30: 'w', 40: 'e'},  # all remapped
        # the F2P shape: all five remapped (some to '') + an extra non-default key
        {20: 'info', 10: '', 30: '', 40: 'bad', 25: '', 12: 'custom'},
        {12: 'custom'},                           # only an extra key
        {k: 'same' for k in keys + extra_keys},   # value collisions
    ]
    for ov in boundary:
        check_one(base, ov)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(SEED)
    all_keys = keys + extra_keys
    for _ in range(N_FUZZ):
        n = rng.randint(0, len(all_keys))
        ks = rng.sample(all_keys, n)
        ov = {k: rng.choice(tags) for k in ks}
        check_one(base, ov)

    print("G-AX OK: recomputeTable deep model (== get_level_tags) sound on "
          "%d boundary + %d fuzz override configurations (seed=%d)."
          % (len(boundary), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
