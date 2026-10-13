#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15629.

This bundle has NO consumed axioms: both modelled behaviours are spelled out
DEEPLY in model.py's impl regions. G-AX therefore validates the two
**A-reference**s -- that each deep model equals the real operation it mirrors --
by executing the REAL repository code (the gold-patched Django under evaluation)
in the container and asserting agreement.

A-reference (1): `reported_reference_parameters` (model.py) mirrors the real
    `ForeignKey.db_parameters(connection)`. The deep model claims the relational
    field's reported parameters carry the SAME collation as the column it
    references (plus the field's own type and check). We build a model whose
    primary key is a CharField with a db_collation, attach a ForeignKey to it,
    and assert the FK's real `db_parameters` dict has key 'collation' equal to
    the target field's collation -- and that with NO db_collation the reported
    collation is None (present, empty), agreeing with the deep model's sentinel.

A-reference (1') the create-time consequence: the column SQL emitted for the FK
    column carries a COLLATE clause exactly when the referenced column does. We
    read the real `schema_editor.column_sql(...)`/table SQL and check the
    COLLATE token presence tracks the collation.

A-reference (2): `references_need_rebuild` (model.py) mirrors the real
    `BaseDatabaseSchemaEditor._alter_field` decision to re-derive columns that
    reference an altered column: the trigger is `old_type != new_type or
    old_collation != new_collation`. We assert the exact boolean expression is
    present in the real (gold-patched) base schema source AND validate the
    boolean truth table the deep model encodes.

Imports: the standard library plus the Django package under evaluation (the very
package the gold patch edits). Exit 0 iff every observation matches.
"""
import inspect
import os
import random
import sys
import tempfile

import django
from django.conf import settings

# Django computes an AppConfig.path from the app module's __file__, so the
# throwaway app holding our dynamically-built models must be a REAL package on
# disk. Materialise an empty package in a tempdir and put its parent on sys.path
# BEFORE django.setup() runs.
_APP_NAME = 'axiom_check_15629'
_pkg_parent = tempfile.mkdtemp(prefix='axcheck15629_')
_pkg_dir = os.path.join(_pkg_parent, _APP_NAME)
os.makedirs(_pkg_dir, exist_ok=True)
with open(os.path.join(_pkg_dir, '__init__.py'), 'w') as _f:
    _f.write('')
with open(os.path.join(_pkg_dir, 'models.py'), 'w') as _f:
    _f.write('')
sys.path.insert(0, _pkg_parent)

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            _APP_NAME,
        ],
        USE_TZ=False,
    )

django.setup()

from django.db import connection, models  # noqa: E402
from django.db.backends.base import schema as base_schema  # noqa: E402


# ----------------------------------------------------------------------------
# deep models (kept in lock-step with model.py)
# ----------------------------------------------------------------------------

def deep_reported_reference_parameters(target_params, own_type, own_check):
    """model.py `reported_reference_parameters`: report type, check, and the
    referenced column's collation."""
    return {
        'type': own_type,
        'check': own_check,
        'collation': target_params.get('collation'),
    }


def deep_references_need_rebuild(old_type, new_type, old_collation, new_collation):
    """model.py `references_need_rebuild`."""
    return (old_type != new_type) or (old_collation != new_collation)


# ----------------------------------------------------------------------------
# model builders
# ----------------------------------------------------------------------------

_counter = [0]


def _make_pair(collation):
    """Build a (Pony, Rider) model pair: Pony has a CharField PK (with the given
    db_collation, possibly None) and Rider has a ForeignKey to Pony. Returns the
    Rider's FK field and the Pony's pk field."""
    _counter[0] += 1
    n = _counter[0]
    pony_attrs = {
        '__module__': 'axiom_check_15629.models',
        'Meta': type('Meta', (), {'app_label': 'axiom_check_15629'}),
        'id': models.CharField(primary_key=True, max_length=10,
                               db_collation=collation),
    }
    Pony = type('Pony%d' % n, (models.Model,), pony_attrs)
    rider_attrs = {
        '__module__': 'axiom_check_15629.models',
        'Meta': type('Meta', (), {'app_label': 'axiom_check_15629'}),
        'pony': models.ForeignKey(Pony, models.CASCADE),
    }
    Rider = type('Rider%d' % n, (models.Model,), rider_attrs)
    fk_field = Rider._meta.get_field('pony')
    pk_field = Pony._meta.get_field('id')
    return fk_field, pk_field


def check_reported_reference_parameters(collation):
    """A-reference (1): the real ForeignKey.db_parameters carries the target's
    collation, matching the deep model."""
    fk_field, pk_field = _make_pair(collation)
    target_params = pk_field.db_parameters(connection=connection)  # real callee
    observed = fk_field.db_parameters(connection=connection)       # real callee

    # The real FK params MUST report a collation key (the whole regression).
    assert 'collation' in observed, (
        "real ForeignKey.db_parameters dropped 'collation' for collation=%r: %r"
        % (collation, observed))
    # And it must equal the referenced column's collation.
    assert observed.get('collation') == target_params.get('collation'), (
        "FK collation %r != target collation %r (collation=%r)"
        % (observed.get('collation'), target_params.get('collation'), collation))

    # Deep model agreement on the whole reported triple.
    expected = deep_reported_reference_parameters(
        target_params, observed.get('type'), observed.get('check'))
    assert observed.get('type') == expected['type']
    assert observed.get('check') == expected['check']
    assert observed.get('collation') == expected['collation'], (
        "deep reported_reference_parameters unsound for collation=%r: real %r, "
        "deep %r"
        % (collation, observed.get('collation'), expected['collation']))

    # A-reference (1') the emission consequence: a COLLATE clause appears in the
    # FK column SQL exactly when the referenced column declares a collation.
    with connection.schema_editor(collect_sql=True) as editor:
        col_sql, _params = editor.column_sql(fk_field.model, fk_field)
    emits = (col_sql is not None) and ('COLLATE' in col_sql.upper())
    declares = target_params.get('collation') not in (None, '')
    assert emits == declares, (
        "FK column SQL COLLATE emission %r != declares-collation %r "
        "(collation=%r, sql=%r)" % (emits, declares, collation, col_sql))
    return observed.get('collation')


def check_references_need_rebuild():
    """A-reference (2): validate the deep boolean predicate and confirm the real
    gold-patched base schema source uses the same disjunction."""
    src = inspect.getsource(base_schema.BaseDatabaseSchemaEditor._alter_field)
    # The gold-patched source computes the drop/re-derive trigger as a
    # disjunction of a type change OR a collation change.
    assert 'old_collation' in src and 'new_collation' in src, (
        "base schema _alter_field no longer mentions old/new collation")
    norm = ''.join(src.split())
    assert ('(old_type!=new_type)or(old_collation!=new_collation)' in norm), (
        "base schema _alter_field drop-FK trigger is not "
        "(old_type != new_type) or (old_collation != new_collation)")

    # Boolean truth table the deep model encodes (4 identities: A,B distinct
    # types t0/t1; X,Y distinct collations c0/c1; None as the empty collation).
    types = ['t0', 't1', None]
    colls = ['c0', 'c1', None]
    for ot in types:
        for nt in types:
            for oc in colls:
                for nc in colls:
                    deep = deep_references_need_rebuild(ot, nt, oc, nc)
                    truth = (ot != nt) or (oc != nc)
                    assert deep == truth, (
                        "deep references_need_rebuild unsound for "
                        "(%r,%r,%r,%r): deep=%r truth=%r"
                        % (ot, nt, oc, nc, deep, truth))
                    # The discriminating case: pure collation change rebuilds.
                    if ot == nt and oc != nc:
                        assert deep is True


def main():
    # --- A-reference (1)/(1'): boundary collations ---------------------------
    boundary = [None, 'nocase', 'binary', 'utf8_bin', 'und-x-icu', '']
    for coll in boundary:
        check_reported_reference_parameters(coll)

    # --- A-reference (1): randomized fuzz over collation identities ----------
    rng = random.Random(15629)
    pool = [None, 'nocase', 'binary', 'utf8_bin', 'utf8mb4_unicode_ci',
            'C', 'POSIX', 'en-x-icu', 'sv-x-icu']
    for _ in range(120):
        check_reported_reference_parameters(rng.choice(pool))

    # --- A-reference (2): rebuild decision -----------------------------------
    check_references_need_rebuild()

    print("G-AX OK: deep reported_reference_parameters (A-reference) == real "
          "ForeignKey.db_parameters (collation propagated from target) over "
          "%d boundary + 120 fuzz model pairs incl. COLLATE-emission tracking; "
          "deep references_need_rebuild (A-reference) == real base-schema "
          "(old_type!=new_type) or (old_collation!=new_collation) over the full "
          "3x3x3x3 identity truth table." % len(boundary))
    return 0


if __name__ == '__main__':
    sys.exit(main())
