#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12273 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`writeSlot`/`writtenSlots` + the dedicated pk write)
              transliterated to a Python dict update over the model's REAL
              parent-link layout, via the mapping.md bijection
              (`Store` ↔ attr-name → value dict, `slots` ↔ parents.values()
              descriptors, `None` ↔ `none`). There is NO A-tagged callee in this
              bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Model._set_pk_val` applied
              at base_commit (the harness applies patch.diff before this runs)
              to a real model instance, observed as the resulting attribute
              store restricted to the identity cells.

Observable per input = the full attribute store (every primary/inherited
identity cell of the instance) after assigning `value`. The model says exactly
the cells `{pk} ∪ {slot.attr : not slot.isPrimary}` become `value`, all others
unchanged. The oracle must agree on every input. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample (e.g. an inherited
identity cell left holding its old value — the pre-patch bug).

Runs in-container (the prebuilt SWE-Bench instance image), `django` + stdlib
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys

import django
from django.conf import settings

SEED = 12273
N_FUZZ = 100_000


def _setup():
    sys.path.insert(0, "/testbed/tests")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_sqlite")
    django.setup()
    from django.apps import apps
    if "model_inheritance_regress" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + [
            "model_inheritance_regress"
        ]
        apps.set_installed_apps(settings.INSTALLED_APPS)


def identity_cells(model):
    """Every attribute name that is a primary or inherited-identity cell of the
    model — the cells the observable tracks. (pk attname + each parent link's
    target_field.attname + each link's own attname, deduped.)"""
    meta = model._meta
    cells = {meta.pk.attname}
    for parent_link in meta.parents.values():
        if parent_link is None:
            continue
        cells.add(parent_link.target_field.attname)
        cells.add(parent_link.attname)
    return cells


# --- the R/I shadow: Solution.lean writeSlot/writtenSlots + pk write ---------
def shadow_store(model, initial, value):
    """assignPrimaryIdentity transliterated: write `value` to each non-primary
    slot's target attname, then to the pk attname; other cells unchanged."""
    meta = model._meta
    store = dict(initial)
    pk_attname = meta.pk.attname
    for parent_link in meta.parents.values():
        if parent_link is None:
            continue
        is_primary = (parent_link == meta.pk)        # Slot.isPrimary
        if not is_primary:
            store[parent_link.target_field.attname] = value   # writeSlot
    store[pk_attname] = value                        # the dedicated pk write
    return store


# --- the oracle: patch.diff's behaviour (the real patched setter) ------------
def oracle_store(model, initial, value):
    """patch.diff's behaviour: assign `value` to a real instance's `.pk`
    (which invokes the patched `_set_pk_val`), then read back the identity
    cells."""
    inst = model()
    for name, v in initial.items():
        setattr(inst, name, v)
    inst.pk = value                                  # patched _set_pk_val
    cells = identity_cells(model)
    return {name: getattr(inst, name) for name in cells}


def restrict(store, cells):
    return {name: store.get(name) for name in cells}


def fuzz_inputs(n, rng, models):
    # boundary cases first (plan §4.1 step 4): the reset value None + ints
    boundary_values = [None, 0, 1, -1, 7, 2 ** 31 - 1, 123456789]
    for model in models:
        for v in boundary_values:
            yield (model, {}, v)
    # pre-seeded identity cells (the realistic "loaded then reset" case)
    for model in models:
        cells = sorted(identity_cells(model))
        seed = {name: 1000 + i for i, name in enumerate(cells)}
        for v in boundary_values:
            yield (model, dict(seed), v)
    for _ in range(n):
        model = rng.choice(models)
        cells = sorted(identity_cells(model))
        initial = {}
        for name in cells:
            if rng.random() < 0.7:
                initial[name] = rng.choice(
                    [None, rng.randint(-(2 ** 31), 2 ** 31)])
        v = rng.choice([None, rng.randint(-(2 ** 31), 2 ** 31)])
        yield (model, initial, v)


def main():
    _setup()
    from model_inheritance_regress.models import (
        Person, Politician, Congressman, User, Profile,
    )
    models = [Person, Politician, Congressman, User, Profile]

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for model, initial, value in fuzz_inputs(N_FUZZ, rng, models):
        count += 1
        cells = identity_cells(model)
        shadow = restrict(shadow_store(model, initial, value), cells)
        oracle = oracle_store(model, initial, value)
        if shadow != oracle:
            disagreements.append((model.__name__, initial, value, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nm, ini, v, sh, orc in disagreements:
            print("  model=%s initial=%r value=%r shadow=%r oracle=%r"
                  % (nm, ini, v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assignPrimaryIdentity agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
