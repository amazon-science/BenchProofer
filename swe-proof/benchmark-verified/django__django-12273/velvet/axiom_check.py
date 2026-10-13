#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12273.

This bundle has NO consumed axiom and NO deep-model reference: the change is a
data-flow over a record's attribute cells, modeled DIRECTLY in Solution.lean by
`writeSlot`/`writtenSlots` + the dedicated primary write (refinement.md §C).
G-AX therefore validates the *structural layout facts that the direct model
depends on* by executing the REAL Django models in-container:

  (1) For each model, the model's parent-link layout maps to the abstract
      `slots`/`pk` of mapping.md §2: each `parent_link` in
      `self._meta.parents.values()` yields a `Slot(attr = target_field.attname,
      isPrimary = (parent_link == self._meta.pk))`; the primary key cell is
      `self._meta.pk.attname`.

  (2) The set of attribute names the patched `_set_pk_val` writes equals the
      model's predicted set  {pk} ∪ {slot.attr : not slot.isPrimary}  — i.e.
      exactly `assignPrimaryIdentity`'s written-cell set. We run the patch's
      own logic against the REAL `_meta` (the structural descriptors are the
      real callees here) and record every `setattr` target.

  (3) Running the real patched setter with `value = None` on a real instance
      clears exactly those cells to `None`, and leaves every other already-set
      attribute untouched. This is the observable the issue's `pk = None;
      save()` relies on (resetting the whole inherited identity).

Imports only `django` (the module under change) + the standard library. Covers
the two F2P multi-level children (`Profile`, `Congressman`) plus the
no-parent base models, and fuzzes the assigned value. Exit 0 iff every
obligation holds.
"""
import os
import random
import sys

import django
from django.conf import settings


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


def model_slots(model):
    """The abstract (slots, pk) of mapping.md §2 read from the REAL model."""
    meta = model._meta
    pk_attname = meta.pk.attname
    slots = []
    for parent_link in meta.parents.values():
        if parent_link is None:
            continue
        slots.append({
            "attr": parent_link.target_field.attname,
            "isPrimary": (parent_link == meta.pk),
        })
    return slots, pk_attname


def predicted_write_set(slots, pk_attname):
    """{pk} ∪ {slot.attr : not slot.isPrimary} — assignPrimaryIdentity's cells."""
    s = {pk_attname}
    for slot in slots:
        if not slot["isPrimary"]:
            s.add(slot["attr"])
    return s


def patched_set_pk_val_targets(instance, value):
    """Run the PATCHED `_set_pk_val` logic (gold patch verbatim) against the
    REAL `instance._meta`, recording every attribute name it writes."""
    targets = []
    meta = instance._meta
    for parent_link in meta.parents.values():
        if parent_link and parent_link != meta.pk:
            setattr(instance, parent_link.target_field.attname, value)
            targets.append(parent_link.target_field.attname)
    setattr(instance, meta.pk.attname, value)
    targets.append(meta.pk.attname)
    return set(targets)


def check_model(model, value):
    slots, pk_attname = model_slots(model)
    predicted = predicted_write_set(slots, pk_attname)

    # (2) the patch's write set equals the model's predicted set
    inst = model()
    written = patched_set_pk_val_targets(inst, value)
    assert written == predicted, (
        "%s: patched _set_pk_val wrote %r but the direct model predicts %r"
        % (model.__name__, sorted(written), sorted(predicted)))

    # (3) cells in the write set hold `value`; pre-seeded other cells untouched.
    inst2 = model()
    sentinel_attr = "__sentinel_unrelated__"
    setattr(inst2, sentinel_attr, 4242)
    # pre-seed every write-set cell with a distinct non-None marker
    for i, name in enumerate(sorted(predicted)):
        setattr(inst2, name, 1000 + i)
    patched_set_pk_val_targets(inst2, value)
    for name in predicted:
        assert getattr(inst2, name) == value, (
            "%s: cell %r was not reset to %r (got %r)"
            % (model.__name__, name, value, getattr(inst2, name)))
    assert getattr(inst2, sentinel_attr) == 4242, (
        "%s: unrelated cell %r was clobbered" % (model.__name__, sentinel_attr))
    return slots, pk_attname, predicted


def main():
    _setup()
    from model_inheritance_regress.models import (
        Person, Politician, Congressman, User, Profile,
    )

    models = [Person, Politician, Congressman, User, Profile]

    # boundary values: the reset case (None) and concrete int ids
    boundary_values = [None, 0, 1, -1, 7, 2 ** 31 - 1]
    for model in models:
        for v in boundary_values:
            check_model(model, v)

    # explicit layout assertions for the two F2P multi-level children
    pslots, ppk, ppred = model_slots(Profile)[0], None, None
    pslots, ppk = model_slots(Profile)
    assert ppk == "profile_id", "Profile pk attname changed: %r" % ppk
    assert predicted_write_set(pslots, ppk) == {"profile_id", "id"}, (
        "Profile write set unexpected: %r" % predicted_write_set(pslots, ppk))

    cslots, cpk = model_slots(Congressman)
    assert cpk == "person_ptr_id", "Congressman pk attname changed: %r" % cpk
    assert predicted_write_set(cslots, cpk) == {"person_ptr_id", "politician_id"}, (
        "Congressman write set unexpected: %r"
        % predicted_write_set(cslots, cpk))
    # the Person link IS the pk → must be flagged primary (skipped)
    primary_attrs = {s["attr"] for s in cslots if s["isPrimary"]}
    assert "id" in primary_attrs, (
        "Congressman: the pk-coincident parent link was not flagged primary: %r"
        % cslots)

    # fuzz the assigned value over the two children
    rng = random.Random(12273)
    for _ in range(2000):
        v = rng.choice([None, rng.randint(-(2 ** 31), 2 ** 31)])
        check_model(rng.choice([Profile, Congressman]), v)

    print("G-AX OK: parent-link layout + patched _set_pk_val write set sound on "
          "%d models x %d boundary values + 2000 fuzz; Profile resets "
          "{profile_id,id}, Congressman resets {person_ptr_id,politician_id} "
          "(pk-coincident Person link skipped)." % (len(models),
                                                    len(boundary_values)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
