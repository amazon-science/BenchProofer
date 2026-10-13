#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15127 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types: the conditional control flow
              (`changedKey = watchedKey`, A3) and the mut-frame (`else cached`,
              A5). The recompute (A4) is **A-tagged** (an A-reference to the real
              `get_level_tags()`), so G-CONF does NOT substitute the deep model
              `recomputeTable` here — it calls the real callee, isolating the
              R/I (control-flow + frame) legs. Deep-model soundness is G-AX's job.
  * ORACLE  — `patch.diff`'s behaviour: the patched receiver
              `django.contrib.messages.apps.update_level_tags(setting=...)`
              applied to the module global `base.LEVEL_TAGS`, observed after the
              call (the real correctness oracle, G-RESOLVE).

They must agree on every input: for the watched key the table is recomputed; for
any other key it is left exactly unchanged. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15127
N_FUZZ = 100_000
WATCHED = 'MESSAGE_TAGS'


def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            INSTALLED_APPS=['django.contrib.messages'],
        )
    django.setup()


def shadow_refresh(cached_before, changed_key, overrides):
    """R/I shadow of refreshCachedTable's impl region:
        cached := if changedKey = watchedKey then <recompute> else cached
    The recompute (A4, A-reference) is the REAL get_level_tags() callee, not the
    deep model; the conditional (A3) and frame (A5) are the R/I ops under test."""
    from django.conf import settings
    from django.contrib.messages import utils
    if changed_key == WATCHED:
        settings.MESSAGE_TAGS = dict(overrides)
        return utils.get_level_tags()          # A-tagged: real callee
    else:
        return dict(cached_before)             # mut-frame: unchanged


def oracle_refresh(cached_before, changed_key, overrides):
    """patch.diff's behaviour: set the module global to `cached_before`, invoke
    the patched receiver with `setting=changed_key`, read the global back."""
    from django.conf import settings
    from django.contrib.messages.storage import base
    from django.contrib.messages.apps import update_level_tags  # added by patch
    settings.MESSAGE_TAGS = dict(overrides)
    base.LEVEL_TAGS = dict(cached_before)
    update_level_tags(setting=changed_key)     # the patched receiver
    return dict(base.LEVEL_TAGS)


def fuzz_inputs(n, rng, default_tags):
    keys = list(default_tags.keys())
    extra_keys = [12, 0, 100, -5, 99]
    all_keys = keys + extra_keys
    tags = ['info', '', 'debug', 'warning', 'error', 'success', 'bad',
            'custom', 'x', 'TAG']
    other_settings = ['DEBUG', 'INSTALLED_APPS', 'USE_TZ', 'TEMPLATES',
                      'MESSAGE_LEVEL', 'message_tags', 'MESSAGE_TAGSX']

    def rand_overrides():
        m = rng.randint(0, len(all_keys))
        ks = rng.sample(all_keys, m)
        return {k: rng.choice(tags) for k in ks}

    def rand_cached():
        m = rng.randint(0, len(all_keys))
        ks = rng.sample(all_keys, m)
        return {k: rng.choice(tags) for k in ks}

    # --- boundary cases first (plan §4.1 step 4) --------------------------
    # the F2P shape: watched key changes, full remap incl. an extra key
    f2p = {20: 'info', 10: '', 30: '', 40: 'bad', 25: '', 12: 'custom'}
    yield (dict(default_tags), WATCHED, f2p)            # recompute branch
    yield ({}, WATCHED, f2p)                            # recompute from empty
    yield (dict(default_tags), WATCHED, {})             # recompute, no override
    yield (dict(default_tags), 'DEBUG', f2p)            # frame: other key
    yield ({99: 'keep'}, 'USE_TZ', f2p)                 # frame: arbitrary cached
    yield (dict(default_tags), 'message_tags', f2p)     # frame: case-different key
    yield (dict(default_tags), 'MESSAGE_TAGSX', f2p)    # frame: prefix-similar key

    for _ in range(n):
        cached = rand_cached()
        overrides = rand_overrides()
        # bias ~half toward the watched key so both branches are well covered
        if rng.random() < 0.5:
            changed = WATCHED
        else:
            changed = rng.choice(other_settings + [WATCHED])
        yield (cached, changed, overrides)


def main():
    configure_django()
    from django.contrib.messages import constants
    default_tags = dict(constants.DEFAULT_TAGS)

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cached_before, changed_key, overrides in fuzz_inputs(N_FUZZ, rng, default_tags):
        count += 1
        shadow = shadow_refresh(cached_before, changed_key, overrides)
        oracle = oracle_refresh(cached_before, changed_key, overrides)
        if shadow != oracle:
            disagreements.append((cached_before, changed_key, overrides, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cb, ck, ov, sh, orc in disagreements:
            print("  cached=%r changed=%r overrides=%r shadow=%r oracle=%r"
                  % (cb, ck, ov, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of refreshCachedTable (conditional + mut-frame) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
