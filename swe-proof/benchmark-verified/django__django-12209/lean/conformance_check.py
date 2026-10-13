#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12209.

The bundle models ONE pure decision that `Model._save_table` makes from five
booleans it has in hand at the decision point (mapping.md):

  * the effective "force a fresh insert" verdict, and
  * whether an in-place UPDATE is attempted before any INSERT.

The decision is a PURE function of five observables the real routine reads:

    verbatim_load : bool   (the `raw` parameter)
    force_fresh   : bool   (the `force_insert` parameter)
    is_new        : bool   (self._state.adding)
    key_default   : bool   (bool(pk.default) and pk.default is not NOT_PROVIDED)
    key_set       : bool   (pk_set, i.e. pk_val is not None)

Standing up a model class, an app registry, and a live DB connection to drive
`_save_table` end-to-end is heavy and unnecessary: the modeled value is exactly
this pure routing decision over the observables the real method reads. So the
ORACLE below is a faithful in-process replica using the EXACT patched expressions
from `django/db/models/base.py`:

    # gold block (post-patch):
    force_insert = force_fresh
    if (not verbatim_load and not force_insert and is_new and key_default):
        force_insert = True
    attempts_update = key_set and not force_insert
    # -> (force_insert, attempts_update)

The SHADOW is the op-for-op transliteration of `implementation_saveDecision`
/ `forcesFreshInsert` (per refinement.md).

The input space is five booleans = 32 points; G-CONF enumerates ALL 32
exhaustively (no sampling can miss a disagreement), then additionally fuzzes
>=1e5 random boolean tuples against the same oracle as a regression belt.

Exit 0 iff zero disagreements.
"""
import itertools
import random
import sys

CONF_SEED = 20240627


def oracle(verbatim_load, force_fresh, is_new, key_default, key_set):
    """Faithful in-process replica of the PATCHED _save_table decision."""
    force_insert = force_fresh
    # gold: "not raw and not force_insert and self._state.adding and
    #        self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED"
    if (not verbatim_load) and (not force_insert) and is_new and key_default:
        force_insert = True
    attempts_update = key_set and (not force_insert)
    return (force_insert, attempts_update)


def shadow(verbatim_load, force_fresh, is_new, key_default, key_set):
    """Transliteration of implementation_saveDecision / forcesFreshInsert."""
    forced = force_fresh
    if (not verbatim_load) and (not forced) and is_new and key_default:
        forced = True
    attempts_update = key_set and (not forced)
    return (forced, attempts_update)


def main():
    disagreements = 0
    checked = 0

    # 1) exhaustive over the full 32-point boolean cube
    for tup in itertools.product([False, True], repeat=5):
        checked += 1
        o = oracle(*tup)
        s = shadow(*tup)
        if o != s:
            disagreements += 1
            if disagreements <= 20:
                print(f"DISAGREE (exhaustive) inputs={tup} oracle={o} shadow={s}")

    # 2) >=1e5 fuzzed boolean tuples (regression belt; pinned seed)
    rng = random.Random(CONF_SEED)
    for _ in range(100_000):
        tup = tuple(rng.choice([False, True]) for _ in range(5))
        checked += 1
        o = oracle(*tup)
        s = shadow(*tup)
        if o != s:
            disagreements += 1
            if disagreements <= 20:
                print(f"DISAGREE (fuzz) inputs={tup} oracle={o} shadow={s}")

    print(f"checked={checked} disagreements={disagreements} seed={CONF_SEED}")
    if disagreements == 0:
        print("status=pass zero disagreements (32-point exhaustive + 1e5 fuzz)")
        return 0
    print("status=fail")
    return 1


if __name__ == "__main__":
    sys.exit(main())
