#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15280 (nagini).

SHADOW: the impl region of model.py `link_children_to_parents`, copied
verbatim below with the contract calls (Requires/Ensures/Invariant) stripped.
The impl operates on plain Python lists, so it is directly executable as-is.
The @Pure helper `linked_parent` copies over as a plain function and serves
as an internal cross-check. There are no @ContractOnly callees.

ORACLE: the REAL patched repo code per mapping.md — the reverse-relation
population loop inside `RelatedManager.get_prefetch_queryset` (the manager
class produced by `create_reverse_many_to_one_manager`), exercised end-to-end
against an in-memory sqlite database. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched ORM
importable. Pre-populated slots are arranged through a QuerySet subclass
whose fetch hook fills selected children's parent-field cache entries as the
rows materialize — i.e. before the population loop under test touches them,
exactly the state a separately fetched child-to-parent collection leaves
behind. The post-state observation is each child's parent-field cache entry
after the call.

Type bridge (mapping.md section 2): child i <-> the i-th row of the returned
queryset (row order); slot_full[i] <-> whether the fetch hook pre-populated
that child's slot; parent identity <-> a unique integer token per distinct
parent Python object (fresh copies of the same DB row are distinct objects
with distinct tokens, so preserved-vs-overwritten is decided by object
identity, never by primary-key coincidence); slot_value[i] <-> the
pre-populated parent's token or the -1 empty sentinel; supplied[i] <-> the
token of the instances-collection member whose row the child references.

Input domain: the preconditions demand three parallel lists with 0/1
occupancy flags — satisfied by construction for every scenario. Scenarios
vary the fetched-parents subset (including parents with no children, so the
empty collection is hit), each child's occupancy, and the pre-populated
parent (a stale copy, a supplied member, or a copy of an unrelated parent).

>= 1e5 Requires-satisfying inputs: boundary scenarios + 100000 fuzz
scenarios. Pinned fuzz seed: 15280.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outcomes and exits 1. stdlib + Django (the repo under test) only.
"""
import json
import random
import sys
import types

SEED = 15280
N_FUZZ = 100000

# --- repo under test (patched /testbed) ---------------------------------------

import django
from django.conf import settings

# a minimal in-memory app package so the test models are installable
_app = types.ModuleType('confch')
_app.__path__ = ['/tmp']
sys.modules['confch'] = _app

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'confch'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
    )
django.setup()

from django.db import connection, models   # noqa: E402


# --- pure helper from model.py, contracts stripped -----------------------------

def linked_parent(was_full, old_value, supplied):
    if was_full == 1:
        return old_value
    return supplied


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def link_children_to_parents(slot_full, slot_value, supplied):
    i = 0
    while i < len(slot_value):
        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1


# --- test schema ----------------------------------------------------------------

class Parent(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        app_label = 'confch'


# occupancy plan applied as rows materialize: pk -> parent object to pre-link
PLAN = {}


class OccupancyQuerySet(models.QuerySet):
    def _fetch_all(self):
        first = self._result_cache is None
        super()._fetch_all()
        if first and PLAN and self.model is Child:
            f = Child._meta.get_field('parent')
            for obj in self._result_cache:
                if isinstance(obj, Child) and obj.pk in PLAN:
                    f.set_cached_value(obj, PLAN[obj.pk])


class Child(models.Model):
    tag = models.CharField(max_length=30)
    parent = models.ForeignKey(Parent, models.CASCADE,
                               related_name='children')
    objects = models.Manager.from_queryset(OccupancyQuerySet)()

    class Meta:
        app_label = 'confch'


def main():
    with connection.schema_editor() as se:
        se.create_model(Parent)
        se.create_model(Child)

    NPAR = 5
    # parents 0..3 have children; parent 4 has none (empty-collection cell)
    parents = [Parent.objects.create(name='p%d' % i) for i in range(NPAR)]
    child_dist = [3, 2, 2, 1, 0]   # children per parent
    for i, cnt in enumerate(child_dist):
        for j in range(cnt):
            Child.objects.create(tag='c%d_%d' % (i, j), parent=parents[i])

    # distinct old-value parent objects: fresh copies of each parent row
    stale = [Parent.objects.get(pk=p.pk) for p in parents]

    # unique token per distinct parent Python object (identity-keyed)
    token = {}
    for t, obj in enumerate(parents + stale):
        token[id(obj)] = t
    field = Child._meta.get_field('parent')
    mgr = parents[0].children     # any instance's related manager will do

    def run_scenario(instance_idxs, occupancy_choice):
        """One get_prefetch_queryset call diffed against the shadow.

        instance_idxs:    indices of the parents fetched for (non-empty)
        occupancy_choice: pk -> old-value parent object, or callable applied
                          per (child pk) returning None (empty) or an object
        Returns an error string on disagreement, else None.
        """
        instances = [parents[i] for i in instance_idxs]
        PLAN.clear()
        rows_probe = list(Child.objects.filter(parent__in=instances)
                          .values_list('pk', flat=True))
        for pk in rows_probe:
            old = occupancy_choice(pk)
            if old is not None:
                PLAN[pk] = old
        try:
            qs, rel_obj_attr, instance_attr, single, cache_name, is_desc = \
                mgr.get_prefetch_queryset(instances,
                                          queryset=Child.objects.all())
            rows = list(qs)
        finally:
            PLAN.clear()

        # bridge the pre-state to the parallel lists, in row order
        by_pk = dict((p.pk, p) for p in instances)
        slot_full, slot_value, supplied = [], [], []
        for r in rows:
            if r.pk in occupancy_map:
                slot_full.append(1)
                slot_value.append(token[id(occupancy_map[r.pk])])
            else:
                slot_full.append(0)
                slot_value.append(-1)
            supplied.append(token[id(by_pk[r.parent_id])])

        shadow = list(slot_value)
        link_children_to_parents(slot_full, shadow, supplied)

        # real post-state: each child's parent-slot entry, tokenized
        real = []
        for r in rows:
            if not field.is_cached(r):
                real.append(-1)
            else:
                obj = field.get_cached_value(r)
                if id(obj) not in token:
                    return ('BRIDGE ERROR: slot holds an unknown object %r'
                            % obj)
                real.append(token[id(obj)])

        if shadow != real:
            return ('DISAGREEMENT\n  instances=%r\n  slot_full=%r\n'
                    '  old_values=%r\n  supplied=%r\n  shadow=%r\n  real=%r'
                    % (instance_idxs, slot_full, slot_value, supplied,
                       shadow, real))
        # cross-check the pure helper on each position
        for k in range(len(rows)):
            if shadow[k] != linked_parent(slot_full[k], slot_value[k],
                                          supplied[k]):
                return 'SHADOW SELF-CHECK failed at %d' % k
        return None

    occupancy_map = {}

    def fixed(mapping):
        occupancy_map.clear()
        occupancy_map.update(mapping)
        return lambda pk: occupancy_map.get(pk)

    child_pks = list(Child.objects.order_by('pk')
                     .values_list('pk', flat=True))
    checked = 0

    # --- boundary scenarios ---------------------------------------------------
    boundary = [
        # (instance indices, occupancy mapping pk->old object)
        ([0, 1], {}),                                   # all slots empty
        ([0], dict((pk, stale[3]) for pk in child_pks)),  # all pre-populated
        ([0, 1], {child_pks[0]: stale[2]}),             # one stale slot
        ([0, 1], {child_pks[0]: parents[0]}),           # pre-linked to the
                                                        # supplied object itself
        ([0, 1], {child_pks[0]: stale[0]}),             # stale copy of the
                                                        # same DB row
        ([4], {}),                                      # parent w/o children
        ([0, 1, 2, 3], dict((pk, stale[4]) for pk in child_pks[::2])),
        ([3], {child_pks[-1]: parents[1]}),             # single-child parent
        ([0, 1, 2, 3, 4], {}),
    ]
    for idxs, mapping in boundary:
        err = run_scenario(idxs, fixed(mapping))
        if err:
            print(err)
            return 1
        checked += max(1, len(list(Child.objects.filter(
            parent__in=[parents[i] for i in idxs]))))

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    all_old = parents + stale
    for _ in range(N_FUZZ):
        size = rng.randint(1, NPAR)
        idxs = rng.sample(range(NPAR), size)
        mapping = {}
        for pk in child_pks:
            r = rng.random()
            if r < 0.45:
                continue                     # slot stays empty
            mapping[pk] = rng.choice(all_old)
        err = run_scenario(idxs, fixed(mapping))
        if err:
            print(err)
            return 1
        checked += 1

    print('G-CONF OK: shadow slot updates == real prefetch relink on %d '
          'scenarios (%d boundary + %d fuzz, seed %d).'
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({'checked': checked, 'disagreements': 0, 'seed': SEED,
                      'shadow': 'direct (contract-stripped impl region)'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
