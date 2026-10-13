#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14434.

There are NO consumed axioms in this bundle (Solution.lean's `axioms` region is
empty). What G-AX validates here are the **deep-model references** (A-reference):
the Lean `pure`-region model of the unchanged reference classes
`Table` / `Columns` / `Statement` from
`django/db/backends/ddl_references.py`, specifically their
`references_table` / `references_column` semantics.

The deep model (Solution.lean):

    slotMatches (TableSlot.name s)    t  = (s == t)
    slotMatches (TableSlot.wrapped _) _  = False
    ColumnsRef.referencesColumn c t col  = slotMatches c.tableSlot t ∧ col ∈ c.columns
    Stmt.referencesColumn s t col        = s.cols.referencesColumn t col
    Stmt.referencesTable  s t            = (s.tableName == t) ∨ slotMatches s.cols.tableSlot t

This script constructs the REAL `Columns` / `Table` / `Statement` objects BOTH
ways the code can build them — the columns part wrapping a bare name string
(`TableSlot.name`) AND wrapping a `Table` instance (`TableSlot.wrapped`) — over
boundary + randomized fuzz inputs, and asserts the deep-model predicate equals
the real classes' `references_column` / `references_table` on every observation.

Imports only the django repo module under test (`ddl_references`), which is
present and unchanged in the instance image at base_commit. Exit 0 iff sound.
"""
import random
import sys

from django.db.backends.ddl_references import Columns, Statement, Table


# quote_name callback: only used by __str__, never by references_* — but the
# real constructors require it. A faithful identity-ish quoter.
def quote_name(name):
    return '"%s"' % name


# --- deep-model reference encodings (lock-step with Solution.lean) -----------

def model_columns_references_column(slot_kind, slot_name, columns, t, col):
    """ColumnsRef.referencesColumn under the deep model."""
    slot_matches = (slot_name == t) if slot_kind == "name" else False
    return slot_matches and (col in columns)


def model_stmt_references_column(slot_kind, slot_name, columns, table_name, t, col):
    return model_columns_references_column(slot_kind, slot_name, columns, t, col)


def model_stmt_references_table(slot_kind, slot_name, table_name, t):
    slot_matches = (slot_name == t) if slot_kind == "name" else False
    return (table_name == t) or slot_matches


# --- real-object builders ----------------------------------------------------

def build_columns(slot_kind, db_table, columns):
    """Build the REAL Columns object with the table slot built either way."""
    if slot_kind == "name":
        table_slot = db_table                       # bare string (post-patch)
    else:
        table_slot = Table(db_table, quote_name)      # wrapper object (pre-patch)
    return Columns(table_slot, list(columns), quote_name)


def build_statement(db_table, cols):
    return Statement(
        "SQL",
        table=Table(db_table, quote_name),
        name=quote_name("name_uq"),
        columns=cols,
    )


# --- the checks --------------------------------------------------------------

def check_one(slot_kind, db_table, columns, queries):
    cols = build_columns(slot_kind, db_table, columns)
    stmt = build_statement(db_table, cols)
    for (t, col) in queries:
        # Columns.references_column
        obs = bool(cols.references_column(t, col))
        exp = model_columns_references_column(slot_kind, db_table, columns, t, col)
        assert obs == exp, (
            "Columns.references_column mismatch slot=%s db_table=%r columns=%r "
            "q=(%r,%r): real=%r model=%r" % (slot_kind, db_table, columns, t, col, obs, exp))
        # Statement.references_column (lifted through `any`)
        obs_s = bool(stmt.references_column(t, col))
        exp_s = model_stmt_references_column(slot_kind, db_table, columns, db_table, t, col)
        assert obs_s == exp_s, (
            "Statement.references_column mismatch slot=%s db_table=%r columns=%r "
            "q=(%r,%r): real=%r model=%r" % (slot_kind, db_table, columns, t, col, obs_s, exp_s))
        # Statement.references_table
        obs_t = bool(stmt.references_table(t))
        exp_t = model_stmt_references_table(slot_kind, db_table, db_table, t)
        assert obs_t == exp_t, (
            "Statement.references_table mismatch slot=%s db_table=%r q=%r: "
            "real=%r model=%r" % (slot_kind, db_table, t, obs_t, exp_t))


def main():
    tables = ["t", "mytable", "schema_author", "Capital_T", "x", "tbl0"]
    column_sets = [
        ["name"],
        ["name", "birthday"],
        ["a", "b", "c"],
        ["col"],
        ["name", "Name"],
    ]
    n_checks = 0
    # boundary: every (slot_kind, table, columns) crossed with informative
    # queries — the constraint's own table+column (must be True post-patch),
    # a foreign table, a foreign column, the table-as-column and column-as-table
    for slot_kind in ("name", "wrapped"):
        for db_table in tables:
            for columns in column_sets:
                queries = []
                for col in columns:
                    queries.append((db_table, col))            # own table+col
                    queries.append(("other_table", col))       # foreign table
                queries.append((db_table, "no_such_col"))       # foreign column
                queries.append(("other_table", "no_such_col"))  # both foreign
                queries.append((db_table, db_table))            # table name as col
                check_one(slot_kind, db_table, columns, queries)
                n_checks += len(queries)

    # randomized fuzz
    rng = random.Random(14434)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    def rand_ident(maxlen=8):
        n = rng.randint(1, maxlen)
        return "".join(rng.choice(alphabet) for _ in range(n))
    for _ in range(20000):
        slot_kind = rng.choice(("name", "wrapped"))
        db_table = rand_ident()
        columns = [rand_ident() for _ in range(rng.randint(1, 4))]
        # queries: mix in-set columns, the real table, and random idents
        t = rng.choice([db_table, rand_ident()])
        if columns and rng.random() < 0.5:
            col = rng.choice(columns)
        else:
            col = rand_ident()
        check_one(slot_kind, db_table, columns, [(t, col)])
        n_checks += 1

    print("G-AX OK: references_column/references_table deep model agrees with "
          "real ddl_references (Columns/Table/Statement) on %d observations "
          "across both table-slot kinds (name, wrapped)." % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
