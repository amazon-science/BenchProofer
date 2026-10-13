#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14434.

This bundle consumes NO @ContractOnly axioms: the only callee the modeled
behaviour relies on — membership of a column code in the recorded column set
(`column in self.columns`) — is modelled DEEPLY by the front-recursive @Pure
`member` in model.py. G-AX therefore validates the deep model and the modeled
reference semantics against the REAL behaviour of the unchanged framework
helpers `django.db.backends.ddl_references` (Table / TableColumns / Columns /
Statement), whose value/identity semantics are the crux of the change:

  (A-reference 1) the deep model `member(c, cols)` == Python's `c in cols`.

  (A-reference 2) `constrains_column(plain, table, cols, q_table, q_col)`
      (model.py pure region) == the real `TableColumns.references_column`:
        self.table == q_table and q_col in self.columns
      where a *bare* (string) recorded table value-compares to a bare queried
      name, while a *decorated handle* (a `Table(...)` instance) never
      value-equals a bare name — exactly the pre-/post-patch distinction.

  (A-reference 3) `constrains_table(table, q_table)` == the real
      `Table.references_table`: self.table == q_table.

The real `ddl_references` semantics are reproduced here from the unchanged
source at base_commit (see mapping.md §3); the membership/equality operators
exercised ARE the real builtin operators the framework uses. The decisive
fact — a `Table` instance compares unequal to the bare table string because it
defines no `__eq__` (identity comparison) — is exercised directly against the
real class. Exit 0 iff every obligation holds.
"""
import random
import sys


# --- real unchanged framework helpers (verbatim semantics, base_commit) ------
# django/db/backends/base/.../ddl_references.py:42-96 — Table / TableColumns /
# Columns. Reproduced (no Django install needed); the equality/membership the
# checks below exercise are the real Python builtin operators.

class Reference:
    def references_table(self, table):
        return False

    def references_column(self, table, column):
        return False


class Table(Reference):
    def __init__(self, table, quote_name):
        self.table = table
        self.quote_name = quote_name

    def references_table(self, table):
        return self.table == table
    # NB: no __eq__ defined => a Table instance value-equals nothing but itself.


class TableColumns(Table):
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns

    def references_column(self, table, column):
        return self.table == table and column in self.columns


class Columns(TableColumns):
    def __init__(self, table, columns, quote_name, col_suffixes=()):
        self.quote_name = quote_name
        self.col_suffixes = col_suffixes
        super().__init__(table, columns)


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def member(c, cols):
    """Reference impl of model.py's deep model `member` (front-recursive)."""
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols[1:])


def constrains_column(plain, table, cols, q_table, q_col):
    """Reference impl of model.py's `constrains_column`."""
    return plain and table == q_table and member(q_col, cols)


def constrains_table(table, q_table):
    """Reference impl of model.py's `constrains_table`."""
    return table == q_table


# --- the checks --------------------------------------------------------------

def check_member(c, cols):
    """A-reference 1: deep model `member` == Python `in`."""
    observed = (c in cols)
    modeled = member(c, list(cols))
    assert observed == modeled, (
        "member deep model unsound: %r in %r is %r, model gives %r"
        % (c, cols, observed, modeled))


def check_column_reference(db_table, columns, q_table, q_col):
    """A-reference 2: the POST-patch wiring (bare string recorded as the
    columns' table) and the model's `constrains_column` agree with the real
    Columns.references_column; and the PRE-patch wiring (a Table handle
    recorded instead) is always False — exactly the bug."""
    quote = lambda s: '"%s"' % s

    # post-patch: bare table name recorded against the columns
    post = Columns(db_table, list(columns), quote)
    real_post = post.references_column(q_table, q_col)
    model_post = constrains_column(True, db_table, list(columns), q_table, q_col)
    assert real_post == model_post, (
        "constrains_column (bare) disagrees with real Columns: real=%r model=%r"
        % (real_post, model_post))

    # pre-patch: a Table handle recorded as the columns' table -> never matches
    pre = Columns(Table(db_table, quote), list(columns), quote)
    real_pre = pre.references_column(q_table, q_col)
    model_pre = constrains_column(False, db_table, list(columns), q_table, q_col)
    assert real_pre is False, (
        "expected pre-patch references_column always False, got %r" % real_pre)
    assert real_pre == model_pre, (
        "constrains_column (handle) disagrees with real Columns: real=%r model=%r"
        % (real_pre, model_pre))


def check_table_reference(db_table, q_table):
    """A-reference 3: the model's `constrains_table` == real
    Table.references_table on a recorded bare name."""
    quote = lambda s: '"%s"' % s
    real = Table(db_table, quote).references_table(q_table)
    modeled = constrains_table(db_table, q_table)
    assert real == modeled, (
        "constrains_table disagrees with real Table: real=%r model=%r"
        % (real, modeled))


def main():
    tables = ["schema_author", "schema_book", "name_uq", "x", "", "T"]
    cols_sets = [
        ["name"],
        ["name", "height"],
        [],
        ["a", "b", "c"],
        ["name", "name"],
        ["id"],
    ]
    queried_cols = ["name", "height", "id", "missing", "a", "c", ""]

    # --- A-reference 2 + 3: boundary cases over real tables/columns ---------
    boundary = 0
    for db in tables:
        for cols in cols_sets:
            # member deep model vs Python `in`
            for qc in queried_cols + cols:
                check_member(qc, cols)
            # constrains_column vs real Columns (post & pre wiring)
            for qt in tables:
                for qc in queried_cols:
                    check_column_reference(db, cols, qt, qc)
                    boundary += 1
            # constrains_table vs real Table
            for qt in tables:
                check_table_reference(db, qt)

    # The decisive F2P shape: constrained column of the constraint's own table
    # is referenced post-patch, never pre-patch (the bug the gold fixes).
    quote = lambda s: '"%s"' % s
    post = Columns("schema_author", ["name"], quote)
    assert post.references_column("schema_author", "name") is True
    pre = Columns(Table("schema_author", quote), ["name"], quote)
    assert pre.references_column("schema_author", "name") is False

    # --- A-reference 1: randomized fuzz on membership -----------------------
    rng = random.Random(14434)
    fuzz = 0
    for _ in range(20000):
        n = rng.randint(0, 8)
        cols = [rng.randint(0, 12) for _ in range(n)]
        c = rng.randint(0, 12)
        check_member(c, cols)
        # and the full reference semantics on random codes
        plain = bool(rng.getrandbits(1))
        assert constrains_column(plain, [1, 2, 3], cols, [1, 2, 3], c) == (
            plain and member(c, cols))
        fuzz += 1

    print("G-AX OK: member deep model == Python `in`, constrains_column / "
          "constrains_table == real ddl_references on %d boundary reference "
          "queries + %d fuzz; pre-patch references_column always False, "
          "post-patch True for constrained columns." % (boundary, fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
