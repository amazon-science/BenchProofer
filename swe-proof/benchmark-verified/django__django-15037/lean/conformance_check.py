#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_relationField
against the patch.diff behaviour (the post-patch `is_relation` block).

The impl region is NOT all-A-tagged (it has R/I structure). The single
A-reference op (`table2model`) is left as the REAL repo callee in BOTH legs, so
it cancels and the test exercises the R/I control flow that computes
`rel_type` / `rel_to` / `to_field`. We assert zero disagreements vs an
independent reconstruction of the patched branch over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import re
import sys

SEED = 15037          # pinned in mapping.md
N = 120_000           # >= 10^5


def table2model(table_name: str) -> str:
    """REAL unchanged callee (A-reference), shared by both legs."""
    return re.sub(r'[^a-zA-Z0-9]', '', table_name.title())


def shadow(is_unique, is_primary_key, ref_db_column, ref_db_table, table_name, ref_pk_column):
    """R/I shadow of implementation_relationField.

    `ref_pk_column` is None (falsy / no detectable pk) or a non-empty str.
    """
    rel_type = "ForeignKey"
    to_field = None
    if is_unique or is_primary_key:
        rel_type = "OneToOneField"
    else:
        rel_type = "ForeignKey"
        if ref_pk_column is not None and ref_pk_column != ref_db_column:
            to_field = ref_db_column
    rel_to = "self" if ref_db_table == table_name else table2model(ref_db_table)
    return (rel_type, rel_to, to_field)


def patched_branch(is_unique, is_primary_key, ref_db_column, ref_db_table, table_name, ref_pk_column):
    """Independent reconstruction of the post-patch `if is_relation:` block.
    Mirrors inspectdb.py:118-133 verbatim in structure; `extra_params` modeled
    as a dict so `pop`/`get`/assignment match Python truthiness exactly."""
    extra_params = {}
    if is_unique:
        extra_params['unique'] = True
    if is_primary_key:
        extra_params['primary_key'] = True

    if extra_params.pop('unique', False) or extra_params.get('primary_key'):
        rel_type = 'OneToOneField'
    else:
        rel_type = 'ForeignKey'
        ref_pk = ref_pk_column   # get_primary_key_column(...) result
        if ref_pk and ref_pk != ref_db_column:
            extra_params['to_field'] = ref_db_column
    rel_to = ('self' if ref_db_table == table_name else table2model(ref_db_table))
    return (rel_type, rel_to, extra_params.get('to_field'))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    tables = ["", "self_t", "foo", "bar", "inspectdb_peoplemoredata",
              "inspectdb_foreignkeytofield", "a b", "T-1", "123tbl"]
    cols = ["", "id", "other_id", "people_unique_id", "people_unique",
            "col", "x", "a_b"]
    # ref_pk: None (no/empty detectable pk) or a column name.
    pks = [None, "id", "other_id", "people_unique_id", "", "col"]

    fixed = [
        # F2P: plain FK to non-pk column, pk differs -> to_field set.
        (False, False, "people_unique_id", "inspectdb_peoplemoredata",
         "inspectdb_foreignkeytofield", "id"),
        # pk == referenced column -> no to_field.
        (False, False, "id", "t", "u", "id"),
        # no detectable pk -> no to_field.
        (False, False, "c", "t", "u", None),
        (False, False, "c", "t", "u", ""),
        # unique -> OneToOne, no to_field even when pk differs.
        (True, False, "c", "t", "u", "id"),
        # primary_key -> OneToOne.
        (False, True, "c", "t", "u", "id"),
        # self relation.
        (False, False, "c", "t", "t", "id"),
    ]

    cases = fixed + [
        (rng.random() < 0.4, rng.random() < 0.4,
         rng.choice(cols), rng.choice(tables), rng.choice(tables),
         rng.choice(pks))
        for _ in range(N)
    ]

    for args in cases:
        # In Python an empty pk string '' is falsy; the Option model collapses
        # it to None, so normalize the shadow's view consistently.
        is_unique, is_primary_key, ref_db_column, ref_db_table, table_name, ref_pk = args
        shadow_pk = ref_pk if ref_pk else None   # '' / None -> none
        got = shadow(is_unique, is_primary_key, ref_db_column, ref_db_table,
                     table_name, shadow_pk)
        want = patched_branch(is_unique, is_primary_key, ref_db_column,
                              ref_db_table, table_name, ref_pk)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((args, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements over {len(cases)} cases")
        for a, g, w in examples:
            print(f"  args={a} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: R/I shadow == post-patch branch on {len(cases)} cases "
          f"(seed={SEED}), 0 disagreements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
