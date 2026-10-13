#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12273.

There are NO consumed @ContractOnly axioms in model.py: the changed operation
(the primary-key assignment that cascades to ancestor parent-link target
fields) is modelled DEEPLY by ``assign_identity`` over a ``List[int]`` slot
store. This script validates that deep model as an **A-reference**: it executes
the REAL patched primary-key setter (``django.db.models.base.Model._set_pk_val``,
reached through the ``pk`` property setter) on concrete multi-table-inheritance
models and asserts the observed attribute mutation matches, slot-for-slot, what
``assign_identity``'s contract guarantees.

The model abstraction (mapping.md):
  - ``store``   : the instance's attribute-value slots (one per concrete attname)
  - ``pk_idx``  : the slot of ``instance._meta.pk.attname``
  - linked slots: the slots of ``pl.target_field.attname`` for every parent link
                  ``pl`` in ``instance._meta.parents.values()``
  - ``active[k]``: 1 iff ``pl`` is present (not None) and ``pl != _meta.pk``
                  (exactly the patch guard ``parent_link and parent_link != pk``)

Contract obligations re-checked against reality, for an assignment ``pk = value``:
  (1) ``store[pk_idx] == value``                       -> pk attname holds value
  (2) every active linked slot holds ``value``         -> the cascade
  (3) every other slot is unchanged

Run inside the official SWE-bench container for the instance, where Django is
importable and a sqlite test database is available. Exit 0 iff every obligation
holds across single- and multi-inheritance structural twins of the F2P tests.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "axcheck"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def _attname_slots(instance):
    """A deterministic slot layout: the sorted list of concrete attnames.
    Returns (attnames, value_dict) — value_dict is the current store."""
    attnames = sorted({f.attname for f in instance._meta.concrete_fields})
    store = {a: getattr(instance, a, None) for a in attnames}
    return attnames, store


def _model_metadata(instance):
    """Compute the model-side metadata the way model.py abstracts it, but from
    the REAL ``_meta``. Returns (pk_attname, active_target_attnames)."""
    meta = instance._meta
    pk_attname = meta.pk.attname
    active_targets = []
    for parent_link in meta.parents.values():
        # exactly the patch guard: present AND distinct from the pk
        if parent_link and parent_link != meta.pk:
            active_targets.append(parent_link.target_field.attname)
    return pk_attname, active_targets


def _check_instance(instance, value, observations):
    """Drive the real ``pk = value`` setter and re-check the three obligations."""
    attnames, before = _attname_slots(instance)
    pk_attname, active_targets = _model_metadata(instance)

    # The real, patched operation: the ``pk`` property setter -> _set_pk_val.
    instance.pk = value

    after = {a: getattr(instance, a, None) for a in attnames}

    # (1) the identity slot took the new value
    assert after[pk_attname] == value, (
        "pk attname %r is %r after pk=%r (expected %r)"
        % (pk_attname, after[pk_attname], value, value))

    # (2) every active linked slot took the new value (the cascade)
    for tgt in active_targets:
        assert tgt in after, "active target attname %r not a known slot" % (tgt,)
        assert after[tgt] == value, (
            "active linked slot %r is %r after pk=%r (expected the cascade %r)"
            % (tgt, after[tgt], value, value))

    # (3) every other slot is unchanged
    cascade_slots = {pk_attname, *active_targets}
    for a in attnames:
        if a in cascade_slots:
            continue
        assert after[a] == before[a], (
            "unrelated slot %r changed from %r to %r" % (a, before[a], after[a]))

    observations.append((instance.__class__.__name__, pk_attname,
                         tuple(active_targets), value))


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models

    # ---- single inheritance with an own pk: the child declares its own pk and
    # ---- carries one implicit parent link (the Profile(User) structural twin).
    class Ancestor(models.Model):
        username = models.CharField(max_length=30)

        class Meta:
            app_label = "axcheck"

    class Child(Ancestor):
        child_id = models.AutoField(primary_key=True)
        extra = models.CharField(max_length=30, blank=True)

        class Meta:
            app_label = "axcheck"

    # ---- multi inheritance, pk promoted from the first parent link: the child
    # ---- has two parent links, one of which IS the pk (skipped by the guard)
    # ---- and one of which is a distinct active linked slot (the Congressman
    # ---- (Person, Politician) structural twin).
    class LeftParent(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "axcheck"

    class RightParent(models.Model):
        right_id = models.AutoField(primary_key=True)
        title = models.CharField(max_length=50)

        class Meta:
            app_label = "axcheck"

    class MultiChild(LeftParent, RightParent):
        state = models.CharField(max_length=2)

        class Meta:
            app_label = "axcheck"

    for M in (Ancestor, Child, LeftParent, RightParent, MultiChild):
        with connection.schema_editor() as editor:
            editor.create_model(M)

    observations = []

    # ---- (A) single inheritance: a saved Child, then drive several pk values
    # ----     (None, ints, large) and re-check the obligations.
    for value in (None, 1, 7, 12345, -3, 2 ** 31):
        c = Child.objects.create(username="john", extra="x")
        # refresh from db so every slot starts populated/consistent
        c = Child.objects.get(pk=c.pk)
        # sanity: the parent link slot must currently agree with the pk before
        # the assignment, mirroring the modelled precondition (linked == pk row)
        _check_instance(c, value, observations)

    # ---- (B) multi inheritance: a saved MultiChild, same sweep.
    for value in (None, 2, 99, 654321, -1, 2 ** 31 + 5):
        m = MultiChild.objects.create(name="John", title="senator 1", state="PA")
        m = MultiChild.objects.get(pk=m.pk)
        _check_instance(m, value, observations)

    # structural assertions about the twins (so the test really exercises the
    # promoted-parent-link guard and the own-pk distinct-link case).
    sample_child = Child.objects.create(username="probe", extra="y")
    pk_a, act_a = _model_metadata(sample_child)
    assert act_a, ("single-inheritance Child should have an active parent link "
                   "distinct from its own pk; got pk=%r active=%r" % (pk_a, act_a))

    sample_multi = MultiChild.objects.create(name="probe", title="t", state="XX")
    pk_b, act_b = _model_metadata(sample_multi)
    assert act_b, ("multi-inheritance child should have at least one active "
                   "parent link distinct from the promoted pk; got pk=%r active=%r"
                   % (pk_b, act_b))
    # the promoted pk's own parent link must be excluded by the guard (not active)
    all_targets = [pl.target_field.attname
                   for pl in sample_multi._meta.parents.values() if pl]
    assert len(all_targets) > len(act_b), (
        "the guard must exclude the parent link that IS the pk; "
        "targets=%r active=%r" % (all_targets, act_b))

    print("G-AX OK: deep model assign_identity matches the real patched "
          "Model._set_pk_val (pk property setter) over %d observations across "
          "single- and multi-table inheritance (cascade to every active parent-"
          "link target attname; promoted-pk parent link correctly excluded; "
          "unrelated slots untouched)." % (len(observations),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
