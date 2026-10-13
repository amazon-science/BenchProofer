#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12325 (nagini).

SHADOW: the impl region of model.py `select_inheritance_links`, copied
verbatim below with the contract calls (Requires/Ensures/Invariant) stripped.
The impl operates on plain Python lists and a dict, so it is directly
executable as-is. There are no @Pure helpers and no @ContractOnly callees in
this bundle.

ORACLE: the REAL patched repo code per mapping.md — the parent-link
collection loop inside `django.db.models.base.ModelBase.__new__`, exercised
end-to-end by creating model classes dynamically. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
ORM importable. The loop's output dict is a metaclass local, so it is
observed through its one consumer inside the same call: for every concrete
parent base, the class's recorded parents mapping holds the collected
relation when one was recorded for that base's key, else a fresh
auto-created link. Field object identity recovers WHICH declared relation
was recorded (the model's position value), and the auto-created flag
distinguishes "no relation recorded for this key".

Type bridge (mapping.md section 2): the i-th declared one-to-one relation on
the child <-> index i of the parallel lists (declaration order == scan order
here: the child is the only non-skipped base in the scan); its parent_link
flag <-> is_parent_link[i]; the target model's identity <-> the token
related_key[i] (pool models indexed 0..5); the recorded position result[k]
<-> the field object stored for that key's parent. Keys whose model is not
an inherited concrete parent have no consumer observation and are checked
only for non-interference (they must not disturb any parent's recording).

Input domain: the precondition demands only two parallel read-only lists —
every generated scenario satisfies it. Scenarios vary the number of declared
relations (0-6), their targets (inherited parents, repeated targets, and
non-inherited models), their designation flags, and the declaration order,
covering the eligibility filter, order independence, and last-writer-wins.

>= 1e5 Requires-satisfying inputs: boundary scenarios + 100000 fuzz
scenarios. Pinned fuzz seed: 12325.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outputs and exits 1. stdlib + Django (the repo under test) only; the
container is Python 3.6.
"""
import json
import random
import sys
import types

SEED = 12325
N_FUZZ = 100000
NPOOL = 6

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

from django.apps import apps       # noqa: E402
from django.db import models       # noqa: E402


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_inheritance_links(is_parent_link, related_key):
    result = {}
    i = 0
    while i < len(is_parent_link):
        if is_parent_link[i]:
            result[related_key[i]] = i
        i = i + 1
    return result


# --- candidate-target model pool ----------------------------------------------

POOL = []
for _i in range(NPOOL):
    POOL.append(type('ConfParent%d' % _i, (models.Model,), {
        '__module__': 'confch.models',
        'pk_p%d' % _i: models.AutoField(primary_key=True),
        'Meta': type('Meta', (), {'app_label': 'confch'}),
    }))

_counter = [0]


def _purge_children():
    """Drop dynamically created child classes from the app registry so the
    run stays memory-bounded (pool parents are kept)."""
    reg = apps.all_models['confch']
    keep = set('confparent%d' % i for i in range(NPOOL))
    for k in list(reg):
        if k not in keep:
            del reg[k]
    apps.clear_cache()


def run_scenario(parent_idxs, rels):
    """Create one child model class and diff the shadow's recording against
    the relation each inherited parent actually ends up linked through.

    parent_idxs: distinct pool indices the child inherits (concrete bases)
    rels:        [(target_pool_idx, parent_link_flag)] declared relations,
                 in declaration order
    Returns an error string on disagreement, else None.
    """
    _counter[0] += 1
    n = _counter[0]
    attrs = {'__module__': 'confch.models',
             'Meta': type('Meta', (), {'app_label': 'confch'})}
    fields = []
    for j, (tok, flag) in enumerate(rels):
        f = models.OneToOneField(POOL[tok], models.CASCADE,
                                 parent_link=flag, related_name='+')
        attrs['rel%d' % j] = f
        fields.append(f)
    bases = tuple(POOL[i] for i in parent_idxs) or (models.Model,)
    try:
        child = type('ConfChild%d' % n, bases, attrs)
    except Exception as e:
        return ('SCENARIO ERROR parents=%r rels=%r: %s: %s'
                % (parent_idxs, rels, type(e).__name__, e))

    # shadow over the bridged parallel lists
    is_parent_link = [flag for _tok, flag in rels]
    related_key = [tok for tok, _flag in rels]
    shadow = select_inheritance_links(is_parent_link, related_key)

    # real observation: the relation each inherited parent is linked through
    real_parents = dict(child._meta.parents)
    if set(real_parents) != set(POOL[i] for i in parent_idxs):
        return ('DISAGREEMENT parents=%r rels=%r: recorded parent set %r'
                % (parent_idxs, rels,
                   [p.__name__ for p in real_parents]))
    for idx in parent_idxs:
        parent = POOL[idx]
        field = real_parents[parent]
        if idx in shadow:
            expect = fields[shadow[idx]]
            if field is not expect or field.auto_created:
                return ('DISAGREEMENT parents=%r rels=%r target=%d:\n'
                        '  shadow records position %d (%s)\n'
                        '  real links through %s (auto_created=%r)'
                        % (parent_idxs, rels, idx, shadow[idx],
                           expect.name, field.name, field.auto_created))
        else:
            if not field.auto_created:
                return ('DISAGREEMENT parents=%r rels=%r target=%d:\n'
                        '  shadow records nothing\n'
                        '  real links through declared %s'
                        % (parent_idxs, rels, idx, field.name))
    if n % 2000 == 0:
        _purge_children()
    return None


def main():
    checked = 0

    # --- boundary scenarios: every decision cell -----------------------------
    boundary = [
        # (inherited parents, [(target, parent_link)])
        ([0], [(0, False), (0, True)]),   # ordinary first, link second
        ([0], [(0, True), (0, False)]),   # link first, ordinary second
        ([0], [(0, True), (0, True)]),    # two links same target: last wins
        ([0], []),                        # nothing declared: auto link
        ([0], [(0, False)]),              # ordinary only: auto link, no error
        ([0], [(0, True)]),               # single designated link
        ([0, 1], [(1, True)]),            # link one parent, auto the other
        ([0, 1], [(0, True), (1, True)]),
        ([0, 1], [(1, True), (0, True)]),
        ([0], [(1, True)]),               # link targets a NON-inherited model
        ([0], [(0, True), (1, False)]),
        ([], [(0, True)]),                # no inherited parents at all
        ([], []),
        ([0, 1, 2], [(2, False), (1, True), (2, True), (0, False),
                     (0, True), (2, False)]),
        ([0], [(0, False), (0, False)]),  # ordinaries only, same target
        ([0], [(0, True), (0, False), (0, True)]),  # link-ordinary-link
    ]
    for parent_idxs, rels in boundary:
        err = run_scenario(parent_idxs, rels)
        if err:
            print(err)
            return 1
        checked += 1

    # --- fuzz -----------------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n_parents = rng.choice([0, 1, 1, 1, 2, 2, 3])
        parent_idxs = rng.sample(range(NPOOL), n_parents)
        n_rels = rng.randint(0, 6)
        rels = []
        for _j in range(n_rels):
            # bias targets toward the inherited parents so the consumer
            # observes most recordings; mix in non-inherited targets too
            if parent_idxs and rng.random() < 0.8:
                tok = rng.choice(parent_idxs)
            else:
                tok = rng.randrange(NPOOL)
            rels.append((tok, rng.random() < 0.5))
        err = run_scenario(parent_idxs, rels)
        if err:
            print(err)
            return 1
        checked += 1

    print('G-CONF OK: shadow recording == real inheritance-link selection on '
          '%d scenarios (%d boundary + %d fuzz, seed %d).'
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({'checked': checked, 'disagreements': 0, 'seed': SEED,
                      'shadow': 'direct (contract-stripped impl region)'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
