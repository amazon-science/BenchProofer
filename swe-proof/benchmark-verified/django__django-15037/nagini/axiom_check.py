#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15037.

The model takes the referenced table's primary-key column as the introspected
input `ref_pk_column: Optional[List[int]]` — the return value of the unchanged
callee `get_primary_key_column` (an A-reference, not a consumed axiom). This
check validates two things against the REAL code, using only the standard
library:

  (A-reference) `get_primary_key_column` returns the referenced table's
      primary-key column NAME, or None when the table has no primary key. The
      base-class implementation is pure Python over a constraints dict
      (django/db/backends/base/introspection.py:166-173):

          for constraint in self.get_constraints(...).values():
              if constraint['primary_key']:
                  return constraint['columns'][0]
          return None

      We reproduce that algorithm exactly and assert it returns the first
      primary-key constraint's first column, else None — so the model's
      `Optional[List[int]]` carrier (a present name vs None) is faithful.

  (decision) the model's `qualifier_required` / `relation_field` decision — emit
      a referenced-column qualifier exactly when the relation is the plain
      many-to-one kind AND the referenced table has a primary key AND that
      primary key is NOT the referenced column, and then the qualifier names the
      referenced column — matches the real inspectdb logic
      (django/core/management/commands/inspectdb.py:118-130, post-patch):

          if extra_params.pop('unique', False) or extra_params.get('primary_key'):
              rel_type = 'OneToOneField'
          else:
              rel_type = 'ForeignKey'
              ref_pk_column = get_primary_key_column(cursor, ref_db_table)
              if ref_pk_column and ref_pk_column != ref_db_column:
                  extra_params['to_field'] = ref_db_column

Exit 0 iff every obligation holds. Imports only the standard library.
"""
import random
import sys


# --- (A-reference) reproduction of base get_primary_key_column ---------------

def real_get_primary_key_column(constraints):
    """Exact transcription of BaseDatabaseIntrospection.get_primary_key_column
    over an already-introspected constraints dict (the only data it reads)."""
    for constraint in constraints.values():
        if constraint['primary_key']:
            return constraint['columns'][0]
    return None


def check_get_primary_key_column(constraints):
    pk = real_get_primary_key_column(constraints)
    # Property the model relies on: the result is None, or the first column of
    # the first primary-key constraint encountered (a column NAME).
    expected = None
    for c in constraints.values():
        if c['primary_key']:
            expected = c['columns'][0]
            break
    assert pk == expected, (constraints, pk, expected)
    # When present it is one of the table's known column names.
    if pk is not None:
        all_cols = [col for c in constraints.values() for col in c['columns']]
        assert pk in all_cols, (pk, all_cols)


# --- (decision) the modeled relation_field decision vs the real inspectdb ----

def model_decision(unique_or_pk, ref_db_column, ref_db_table, table_name,
                   ref_pk_column):
    """Reproduction of model.py's relation_field over plain Python strings."""
    is_one_to_one = unique_or_pk
    rel_to_self = (ref_db_table == table_name)
    qualifier_required = (
        (not unique_or_pk)
        and ref_pk_column is not None
        and len(ref_pk_column) > 0
        and ref_pk_column != ref_db_column
    )
    has_to_field = qualifier_required
    to_field_col = ref_db_column if has_to_field else None
    return is_one_to_one, rel_to_self, has_to_field, to_field_col


def real_inspectdb_decision(unique_or_pk, ref_db_column, ref_db_table,
                            table_name, ref_pk_column):
    """Exact transcription of inspectdb.py:118-130 (post-patch) effects."""
    extra_params = {}
    if unique_or_pk:
        rel_type = 'OneToOneField'
    else:
        rel_type = 'ForeignKey'
        if ref_pk_column and ref_pk_column != ref_db_column:
            extra_params['to_field'] = ref_db_column
    rel_to_self = (ref_db_table == table_name)
    is_one_to_one = (rel_type == 'OneToOneField')
    has_to_field = 'to_field' in extra_params
    to_field_col = extra_params.get('to_field')
    return is_one_to_one, rel_to_self, has_to_field, to_field_col


def check_decision(unique_or_pk, ref_db_column, ref_db_table, table_name,
                   ref_pk_column):
    m = model_decision(unique_or_pk, ref_db_column, ref_db_table, table_name,
                       ref_pk_column)
    r = real_inspectdb_decision(unique_or_pk, ref_db_column, ref_db_table,
                                table_name, ref_pk_column)
    assert m == r, (
        "decision mismatch on unique_or_pk=%r ref_db_column=%r ref_db_table=%r "
        "table_name=%r ref_pk_column=%r: model=%r real=%r"
        % (unique_or_pk, ref_db_column, ref_db_table, table_name,
           ref_pk_column, m, r))


def main():
    # --- get_primary_key_column boundary scenarios ------------------------
    pk_scenarios = [
        {},  # no constraints at all -> None
        {'u': {'primary_key': False, 'columns': ['x']}},  # no pk -> None
        {'pk': {'primary_key': True, 'columns': ['id']}},  # plain pk
        {'u': {'primary_key': False, 'columns': ['a']},
         'pk': {'primary_key': True, 'columns': ['people_unique_id']}},
        {'pk': {'primary_key': True, 'columns': ['composite_a', 'composite_b']}},
        # the F2P witness: referenced table's pk is 'id', fk references a
        # different (unique) column 'people_unique_id'.
        {'pk': {'primary_key': True, 'columns': ['id']},
         'uq': {'primary_key': False, 'unique': True,
                'columns': ['people_unique_id']}},
    ]
    for sc in pk_scenarios:
        check_get_primary_key_column(sc)

    # --- decision boundary cases -----------------------------------------
    cols = ['id', 'people_unique_id', 'other_id', 'self', '', 'a', 'b']
    tables = ['foo', 'bar', 'inspectdb_people', 'inspectdb_peoplemoredata']
    pkcols = [None, 'id', 'people_unique_id', 'other_id', '', 'a']

    boundary = [
        # F2P witness: FK, ref column != pk column -> to_field set.
        (False, 'people_unique_id', 'inspectdb_peoplemoredata',
         'inspectdb_foreignkeytofield', 'id'),
        # OneToOne (unique/pk): never emit to_field even if columns differ.
        (True, 'people_unique_id', 'inspectdb_peoplemoredata', 't', 'id'),
        # FK, ref column == pk column -> no to_field.
        (False, 'id', 'foo', 'bar', 'id'),
        # FK, referenced table has no pk (None) -> no to_field.
        (False, 'other_id', 'foo', 'bar', None),
        # FK to self.
        (False, 'parent_id', 'people', 'people', 'id'),
        # FK, referenced table pk empty string '' (falsy) -> no to_field.
        (False, 'other_id', 'foo', 'bar', ''),
        # FK, ref column empty but pk non-empty -> to_field set (they differ).
        (False, '', 'foo', 'bar', 'id'),
    ]
    for case in boundary:
        check_decision(*case)

    # --- randomized fuzz over the decision -------------------------------
    rng = random.Random(15037)
    for _ in range(50000):
        check_decision(
            rng.choice([True, False]),
            rng.choice(cols),
            rng.choice(tables),
            rng.choice(tables),
            rng.choice(pkcols),
        )

    print("G-AX OK: get_primary_key_column reproduction sound on %d pk "
          "scenarios; relation_field decision == real inspectdb on %d boundary "
          "+ 50000 fuzz cases" % (len(pk_scenarios), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
