#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15037.

The bundle consumes NO axiom. The one outside callee the modeled decision
consults — the introspection lookup that yields the referenced table's
primary-key column — is UNCHANGED by the patch and is taken as the FREE INPUT
`idKey` (an A-reference, not a consumed contract). This check validates that
free input against the REAL Django introspection machinery
(`connection.introspection.get_primary_key_column`) on a live sqlite backend,
and re-derives the gold decision from the real callee's output, asserting it
equals the deep model `target_qualifier` (Solution.lean's `targetQualifier`):

  (A-reference R1)  `get_primary_key_column(cursor, table)` returns the name of
      the table's single-column primary key when one exists, and `None` when it
      does not. Checked over tables whose PK is the implicit `id`, a named
      non-`id` column, or absent.

  (A-reference R2)  the returned value, when present, is a NON-EMPTY column-name
      string — so the model's "present, non-empty" recognition (`k != []`) is
      conservative w.r.t. the real callee (which never returns "").

  (decision)  the gold patch's literal decision
      `to_field = ref_db_column  iff  rel_type == 'ForeignKey'
                                       and ref_pk_column
                                       and ref_pk_column != ref_db_column`
      re-derived from the real `get_primary_key_column` output equals
      `target_qualifier(is_unique_ref, ref_column, id_key)`.

Imports only the standard library and `django.db` (the very module the gold
patch's code path runs through); no repo-test code. Exit 0 iff every obligation
holds.
"""
import random
import sys

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        },
        INSTALLED_APPS=[],
    )

import django  # noqa: E402

django.setup()

from django.db import connection  # noqa: E402


# --- deep model: Solution.lean's targetQualifier, transliterated -------------

def target_qualifier(is_unique_ref, ref_column, id_key):
    """`targetQualifier (isUniqueRef) (refColumn) (idKey)` over the str/None
    carriers (mapping.md §2): id_key is None or a column-name str."""
    if is_unique_ref:
        return None
    if id_key is None:
        return None
    if id_key != "" and id_key != ref_column:
        return ref_column
    return None


# --- gold patch's literal decision, re-derived from the REAL callee ----------

def gold_decision(rel_type, ref_db_column, ref_pk_column):
    """The to_field value the gold hunk assigns (or None if no key is added):
        if rel_type == 'ForeignKey':
            if ref_pk_column and ref_pk_column != ref_db_column:
                extra_params['to_field'] = ref_db_column
    `ref_pk_column` is the REAL get_primary_key_column output."""
    if rel_type == 'OneToOneField':
        return None
    # rel_type == 'ForeignKey'
    if ref_pk_column and ref_pk_column != ref_db_column:
        return ref_db_column
    return None


# --- live introspection over a real sqlite backend ---------------------------

def real_pk_column(cursor, ddl, table):
    """Create `table` with the given DDL and return the REAL
    get_primary_key_column(cursor, table)."""
    cursor.execute('DROP TABLE IF EXISTS %s' % table)
    cursor.execute(ddl)
    return connection.introspection.get_primary_key_column(cursor, table)


def check_callee_and_decision(cursor, ddl, table, expected_pk):
    pk = real_pk_column(cursor, ddl, table)
    # (R1) the callee reports the table's PK column (or None).
    assert pk == expected_pk, (
        "get_primary_key_column(%r) = %r, expected %r (ddl=%r)"
        % (table, pk, expected_pk, ddl))
    # (R2) when present, the name is a non-empty str.
    if pk is not None:
        assert isinstance(pk, str) and pk != "", (
            "get_primary_key_column returned an empty/non-str name: %r" % (pk,))

    # (decision) for every referenced column + rel_type, the gold decision
    # re-derived from the REAL pk equals the deep model target_qualifier.
    candidate_ref_columns = [c for c in (pk, 'other_id', 'id', 'people_unique_id',
                                         '', 'zzz') if c is not None]
    for ref_col in candidate_ref_columns:
        for rel_type, is_unique in (('ForeignKey', False), ('OneToOneField', True)):
            gold = gold_decision(rel_type, ref_col, pk)
            model = target_qualifier(is_unique, ref_col, pk)
            assert gold == model, (
                "decision mismatch: table=%r rel_type=%r ref_col=%r pk=%r -> "
                "gold=%r model=%r" % (table, rel_type, ref_col, pk, gold, model))


def main():
    boundary = [
        # implicit integer PK named `id`
        ('t_id', 'CREATE TABLE t_id (id integer primary key, other_id integer)', 'id'),
        # named non-`id` single-column PK
        ('t_named', 'CREATE TABLE t_named (people_unique_id integer primary key, '
                    'name varchar(50))', 'people_unique_id'),
        # the F2P shape: referenced table has a PK distinct from the FK target col
        ('t_fk', 'CREATE TABLE t_fk (id integer primary key, '
                 'people_unique_id integer unique)', 'id'),
        # no primary key at all -> None
        ('t_nopk', 'CREATE TABLE t_nopk (a integer, b integer)', None),
    ]
    with connection.cursor() as cursor:
        for table, ddl, expected in boundary:
            check_callee_and_decision(cursor, ddl, table, expected)

        # randomized fuzz: vary the PK column name (or none) and the column set.
        rng = random.Random(15037)
        names = ['id', 'pk', 'people_unique_id', 'other_id', 'code', 'uid', 'k0', 'k1']
        for i in range(2000):
            cols = rng.sample(names, k=rng.randint(2, 4))
            has_pk = rng.random() < 0.75
            if has_pk:
                pk_col = cols[0]
                defs = ['%s integer primary key' % pk_col] + \
                       ['%s integer' % c for c in cols[1:]]
                expected = pk_col
            else:
                defs = ['%s integer' % c for c in cols]
                expected = None
            table = 'fz_%d' % i
            ddl = 'CREATE TABLE %s (%s)' % (table, ', '.join(defs))
            check_callee_and_decision(cursor, ddl, table, expected)

    print("G-AX OK: get_primary_key_column reports the table's single-column PK "
          "(or None), always a non-empty name when present; the gold to_field "
          "decision re-derived from the real callee == target_qualifier over "
          "%d boundary + 2000 fuzz schemas." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
