#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14434.

The bundle models ONE function: `BaseDatabaseSchemaEditor._create_unique_sql`
(`django/db/backends/base/schema.py`), in the `columns` (non-empty) branch. Its
Lean implementation (`implementation__create_unique_sql`) builds a `Statement`
whose `columns` part is a `Columns` reference storing the BARE table-name string
(the post-patch behavior), and answers `references_column` / `references_table`
queries over that statement.

ORACLE = the post-patch behavior, built directly from the REAL repo reference
classes (`Table`, `Columns`, `Statement` from
`django.db.backends.ddl_references` — the unchanged callees the fix uses). We
reproduce exactly what post-patch `_create_unique_sql` constructs in the
`if columns:` branch:

    table = model._meta.db_table                        # bare string (the fix)
    columns_part = Columns(table, columns, quote_name)   # via _index_columns
    stmt = Statement(sql, table=Table(table, quote_name), columns=columns_part, ...)

and then query `stmt.references_column(t, c)` / `stmt.references_table(t)` plus
the rendered column sequence `str(columns_part)` (the `Statement.renderedColumns`
observable — what the generated DDL text contains).
These classes are pure (no DB / no compiler) for this branch, so no Django
framework stand-up is needed. The `sql`, `name`, `condition`, `deferrable`,
`include` kwargs carry no table/column reference and do not affect the queries
(verified: only `Table`/`Columns` parts implement `references_*`).

SHADOW = `implementation__create_unique_sql` transliterated op-for-op into
Python, mirroring Solution.lean (bare-string `tableId`, structural
`references_column` / `references_table`).

Differential test diffs SHADOW vs ORACLE over an exhaustive edge grid plus
>=10^5 fuzzed inputs. exit 0 iff zero disagreements. stdlib-only (+ the real
in-tree django import). Pinned seed: 14434 (also in mapping.md).
"""
import json
import sys

SEED = 14434
N = 120_000


def quote_name(s):
    # identity quoting is sufficient: the reference comparisons used by
    # references_table / references_column never call quote_name (it is only
    # used by __str__). Kept faithful to the real signature.
    return s


# --- ORACLE: post-patch construction using the REAL repo classes --------------
def make_oracle():
    from django.db.backends.ddl_references import Table, Columns, Statement

    def oracle(db_table, columns, q_table, q_col):
        # Mirror the post-patch `if columns:` branch of _create_unique_sql.
        table = db_table                                   # the fix: bare string
        columns_part = Columns(table, list(columns), quote_name)   # _index_columns
        stmt = Statement(
            "sql",
            table=Table(table, quote_name),
            name="n",
            columns=columns_part,
            condition="",
            deferrable="",
            include="",
        )
        return (bool(stmt.references_column(q_table, q_col)),
                bool(stmt.references_table(q_table)),
                str(columns_part))   # rendered column sequence (in order)

    return oracle


# --- SHADOW of implementation__create_unique_sql (R leg) ----------------------
# Mirrors Solution.lean op-for-op. tableId is the bare string ("name" variant);
# references_column = (tableId == t) and (col in columns).
def shadow(db_table, columns, q_table, q_col):
    table = db_table                              # let table : String := dbTable
    cols_table_id = ("name", table)               # TableId.name table
    cols = list(columns)
    # Statement.references_column = columnsPart.references_column
    ref_col = (cols_table_id[0] == "name" and cols_table_id[1] == q_table
               and q_col in cols)
    # Statement.references_table = tablePart.references_table OR columnsPart's
    table_part_match = (table == q_table)
    cols_part_match = (cols_table_id[0] == "name" and cols_table_id[1] == q_table)
    ref_table = table_part_match or cols_part_match
    # Statement.renderedColumns = columnsPart.columns, rendered by Columns.__str__
    # as ', '.join(quote_name(c)) with identity quote_name.
    rendered = ", ".join(cols)
    return (bool(ref_col), bool(ref_table), rendered)


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    oracle = make_oracle()
    checked = 0

    tables = ("t", "t2", "schema_author")
    colsets = (["name"], ["name", "age"], ["a", "b", "c"])
    queries_t = ("t", "t2", "other", "schema_author")
    queries_c = ("name", "age", "a", "missing")

    import itertools
    for db_table in tables:
        for columns in colsets:
            for qt in queries_t:
                for qc in queries_c:
                    o = oracle(db_table, columns, qt, qc)
                    s = shadow(db_table, columns, qt, qc)
                    if o != s:
                        print(f"DISAGREE grid db_table={db_table!r} "
                              f"columns={columns!r} q=({qt!r},{qc!r}): "
                              f"oracle={o} shadow={s}")
                        print("status=fail")
                        return 1
                    checked += 1

    # Random fuzz over a wider alphabet.
    rnd = _lcg(SEED)
    alpha = ("t", "t2", "other", "name", "age", "a", "b", "c", "schema_author",
             "missing", "")
    colpool = ("name", "age", "a", "b", "c", "id", "title")

    def pick(seq):
        return seq[next(rnd) % len(seq)]

    for _ in range(N):
        db_table = pick(alpha)
        k = 1 + (next(rnd) % 4)
        columns = [pick(colpool) for _ in range(k)]
        qt = pick(alpha)
        qc = pick(colpool + ("missing",))
        o = oracle(db_table, columns, qt, qc)
        s = shadow(db_table, columns, qt, qc)
        if o != s:
            print(f"DISAGREE fuzz db_table={db_table!r} columns={columns!r} "
                  f"q=({qt!r},{qc!r}): oracle={o} shadow={s}")
            print("status=fail")
            return 1
        checked += 1

    print(json.dumps({"status": "pass", "checked": checked,
                      "disagreements": 0, "instance": "django__django-14434"}))
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
