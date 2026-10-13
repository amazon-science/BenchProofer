#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12273 (nagini).

SHADOW: the impl region of ``assign_identity`` from model.py, copied verbatim
below with the contract calls stripped (the loop's ``Invariant(...)`` lines
are the only contract content inside the impl region). There are no @Pure
helpers, no @ContractOnly callees, and no PSeq usage in this bundle; the
carriers are plain ``List[int]`` / ``int``, so no shim is needed.

ORACLE: the REAL patched repo operation the model models per mapping.md —
the primary-key value setter reached through the ``pk`` property of
``django.db.models.base.Model``. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable. The operation only performs attribute writes on the instance
(no database I/O), so the oracle drives it on in-memory instances of
structural-twin model classes and observes the resulting attribute store.

Type bridge (mapping.md "Type abstraction"):
  * ``store``  <-> the instance's attribute store, one slot per concrete
    field attname under a fixed deterministic layout (the sorted attname
    list); ``store[slot(a)] = v`` <-> ``setattr(instance, a, v)`` and
    ``store[slot(a)]`` <-> ``getattr(instance, a)``.
  * ``pk_idx`` <-> the slot of ``instance._meta.pk.attname``.
  * ``target[k]`` / ``active[k]`` <-> derived from the k-th entry of
    ``instance._meta.parents.values()``: the target slot is the slot of that
    link's ``target_field.attname``, and the entry is active (== 1) iff the
    link is present and is not the pk field itself. Entries with no link
    object carry no target slot and are omitted (they contribute no write
    on either side).
  * ``value``  <-> the assigned identity value. The model treats it as an
    opaque int (the propagation is value-agnostic); fuzzing uses ints, and
    the boundary set additionally passes ``None`` through both sides to
    witness the reset-identity scenario, which the shadow handles
    identically because it only ever stores the value.

Structural shapes exercised (each a distinct (target, active, pk_idx)
configuration, validated against the shadow's Requires before use):
  S1 single inheritance, child declares its own pk  -> one active link;
  S2 multi inheritance, pk promoted from a parent link -> one link that IS
     the pk (inactive) plus one distinct active link;
  S3 single inheritance, pk promoted (no own pk)   -> one link, inactive;
  S4 no inheritance                                 -> no links at all.

>= 1e5 Requires-satisfying inputs: 32 boundary cases + 100000 fuzz cases
spread over the four shapes, each with freshly fuzzed slot contents and
assigned value. Pinned fuzz seed: 122730.

Exit 0 iff zero disagreements; on disagreement prints the input and both
resulting stores and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 122730
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim (Invariant calls stripped) --------

def assign_identity(store, target, active, pk_idx, value):
    k = 0
    n = len(target)
    while k < n:
        if active[k] == 1:
            store[target[k]] = value
        k = k + 1
    store[pk_idx] = value


# --- oracle plumbing ----------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


class Shape(object):
    """One structural twin: a reusable instance plus the abstract-input
    bridge (slot layout, pk_idx, target, active) derived from its _meta the
    way mapping.md defines it."""

    def __init__(self, name, model_cls):
        self.name = name
        self.instance = model_cls()
        meta = model_cls._meta
        self.attnames = sorted({f.attname for f in meta.concrete_fields})
        slot = {a: i for i, a in enumerate(self.attnames)}
        self.pk_idx = slot[meta.pk.attname]
        self.target = []
        self.active = []
        for link in meta.parents.values():
            if link is None:
                # no link object: no target slot exists and no write happens
                # on either side; omitted per the bridge note above.
                continue
            self.target.append(slot[link.target_field.attname])
            self.active.append(1 if link != meta.pk else 0)
        # the shadow's Requires, re-checked on the real metadata
        n_slots = len(self.attnames)
        assert 0 <= self.pk_idx < n_slots
        assert len(self.active) == len(self.target)
        for j, t in enumerate(self.target):
            assert 0 <= t < n_slots
            if self.active[j] == 1:
                assert t != self.pk_idx

    def real_store_after(self, values, value):
        """Load `values` into the instance's slots, drive the real pk setter,
        and read the store back slot-for-slot."""
        inst = self.instance
        for a, v in zip(self.attnames, values):
            setattr(inst, a, v)
        inst.pk = value          # the real, patched operation
        return [getattr(inst, a) for a in self.attnames]


def check_case(shape, values, value):
    store = list(values)
    assign_identity(store, shape.target, shape.active, shape.pk_idx, value)
    real = shape.real_store_after(values, value)
    if store != real:
        return ("DISAGREEMENT\n  shape=%s attnames=%r\n"
                "  pk_idx=%r target=%r active=%r\n"
                "  initial=%r value=%r\n  shadow=%r\n  real  =%r"
                % (shape.name, shape.attnames, shape.pk_idx, shape.target,
                   shape.active, values, value, store, real))
    return None


def build_shapes():
    from django.db import models

    # S1: single inheritance, child declares its own pk
    class Ancestor(models.Model):
        username = models.CharField(max_length=30)

        class Meta:
            app_label = "confcheck"

    class Child(Ancestor):
        child_id = models.AutoField(primary_key=True)
        extra = models.CharField(max_length=30, blank=True)

        class Meta:
            app_label = "confcheck"

    # S2: multi inheritance, pk promoted from the first parent link
    class LeftParent(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "confcheck"

    class RightParent(models.Model):
        right_id = models.AutoField(primary_key=True)
        title = models.CharField(max_length=50)

        class Meta:
            app_label = "confcheck"

    class MultiChild(LeftParent, RightParent):
        state = models.CharField(max_length=2)

        class Meta:
            app_label = "confcheck"

    # S3: single inheritance, pk promoted (child declares no own pk)
    class PlainParent(models.Model):
        label = models.CharField(max_length=20)

        class Meta:
            app_label = "confcheck"

    class PromotedChild(PlainParent):
        note = models.CharField(max_length=20)

        class Meta:
            app_label = "confcheck"

    # S4: no inheritance at all
    class Standalone(models.Model):
        payload = models.IntegerField(null=True)

        class Meta:
            app_label = "confcheck"

    shapes = [
        Shape("S1-own-pk", Child),
        Shape("S2-multi-promoted-pk", MultiChild),
        Shape("S3-promoted-pk", PromotedChild),
        Shape("S4-standalone", Standalone),
    ]
    # structural sanity: the four shapes cover the intended configurations
    assert shapes[0].active.count(1) >= 1
    assert 0 in shapes[1].active and 1 in shapes[1].active
    assert shapes[2].target and shapes[2].active.count(1) == 0
    assert shapes[3].target == [] and shapes[3].active == []
    return shapes


def boundary_values():
    # assigned identity values probing edges; None witnesses the identity
    # reset the acceptance tests drive (bridged through both sides verbatim)
    return [None, 0, 1, -1, 7, 12345, -99999, 2 ** 31, 2 ** 63, -(2 ** 31)]


def main():
    _configure_django()
    shapes = build_shapes()

    checked = 0

    # boundary: every shape x edge value, distinct slot contents, plus the
    # all-slots-equal store (a misdirected write is invisible only if every
    # slot already holds the value, so also probe stores that equal `value`).
    for shape in shapes:
        n = len(shape.attnames)
        for value in boundary_values():
            values = [10 * (i + 1) for i in range(n)]
            err = check_case(shape, values, value)
            if err:
                print(err)
                return 1
            checked += 1
        err = check_case(shape, [5] * n, 5)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        shape = shapes[rng.randrange(len(shapes))]
        n = len(shape.attnames)
        pick = rng.randrange(4)
        if pick == 0:
            values = [rng.randint(-10, 10) for _ in range(n)]
        elif pick == 1:
            values = [rng.randint(-(2 ** 31), 2 ** 31) for _ in range(n)]
        elif pick == 2:
            v = rng.randint(-1000, 1000)
            values = [v] * n            # degenerate: all slots equal
        else:
            values = [rng.randint(0, 3) for _ in range(n)]  # heavy collisions
        value = rng.choice((
            rng.randint(-5, 5),
            rng.randint(-(2 ** 40), 2 ** 40),
            0,
        ))
        err = check_case(shape, values, value)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow assign_identity == real pk setter on %d inputs "
          "across %d structural shapes (seed %d)."
          % (checked, len(shapes), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
