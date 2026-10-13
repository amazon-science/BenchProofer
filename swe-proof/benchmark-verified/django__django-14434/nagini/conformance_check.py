#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14434 (nagini).

SHADOW: the impl region of model.py's ``build_constraint_columns``, copied
VERBATIM below with only the contract calls stripped (the impl region has no
Requires/Ensures/Invariant/Assert inside; the ConstraintPart constructor's
contracts are stripped from the class shim). The @Pure helpers of the pure
region (``member`` / ``constrains_column`` / ``constrains_table``) copy over
as plain functions on a small immutable tuple-backed PSeq shim; they are the
model's query semantics, so the shadow's answer to "does the built part
constrain column C of table T?" is ``constrains_column`` over the built
part's facets, and the table query is ``constrains_table``. There are no
@ContractOnly callees (mapping.md: no consumed axioms).

ORACLE: the REAL patched repo construction per mapping.md section 1 —
``django.db.backends.base.schema.BaseDatabaseSchemaEditor._create_unique_sql``.
The gate applies patch.diff to /testbed and sets PYTHONPATH=/testbed before
this script runs, so the import resolves to the patched module. Each probe
sets the model's ``db_table``, calls ``_create_unique_sql`` (with an explicit
``name=`` so the name part is a plain quoted string carrying no reference
semantics), takes the column-bearing part of the returned ``Statement``
(``stmt.parts['columns']``), and queries the real
``references_column(q_table, q_col)`` / ``references_table(q_table)``.
The whole-Statement ``references_column`` is compared too: with an explicit
name it reduces to the column-bearing part (mapping.md section 2, last row),
and it is the query the hidden test asks at statement level.

TYPE BRIDGE (mapping.md section 2): table identifiers are ``str`` in the
repo and ``List[int]`` of code points in the model (``ord`` per character, a
bijection on surrogate-free strings, so ``str ==`` iff code-point-sequence
==). Column names are ``str`` in the repo and injective integer codes in the
model: per scenario every distinct column name occurring anywhere (recorded
set or query) is assigned a distinct code, which preserves exactly the
equality/membership either side observes. The empty recorded column set is
exercised through the repo's expression-based branch (a literal expression
yields no referenced columns), guarded by the connection feature flag.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): a boundary grid of table
names (empty, one char, quotes, dots, spaces, unicode, long) crossed with
boundary column sets (single, several, duplicates, empty-string name,
unicode, many), plus 15000 random fuzz scenarios over a mixed alphabet; each
scenario runs a battery of column queries (every recorded column, near-miss
and unrelated names, the recorded table, near-miss and unrelated tables) and
table queries. Every shadow-vs-real comparison counts as one check
(>= 100000 total). Pinned fuzz seed: 14434.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14434
N_FUZZ = 15000


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- model.py class, constructor contracts stripped ---------------------------

class ConstraintPart(object):
    """The column-bearing part of a deferred statement, restricted to its
    observed facets. ``plain`` records whether ``table`` is a plain table name
    (value-comparable to a queried name) or an opaque holder (never value-equal
    to a plain name); ``table`` is the recorded table identifier; ``columns`` is
    the constrained column set as a sequence of column-identifier codes."""

    def __init__(self, plain, table, columns):
        self.plain = plain
        self.table = table
        self.columns = columns


# --- pure region of model.py, copied as plain functions -----------------------

def member(c, cols):
    """Whether the column code ``c`` occurs in the column set ``cols``.
    Front-recursive over ``PSeq`` so a single unfold is available to callers."""
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols.drop(1))


def constrains_column(plain, table, cols, q_table, q_col):
    """The column query on a column-bearing part: the recorded table identifier
    must be a plain name AND value-equal the queried table identifier, and the
    queried column code must be a member of the recorded column set. An opaque
    holder (``plain == False``) never value-equals a plain queried name."""
    return plain and table == q_table and member(q_col, cols)


def constrains_table(table, q_table):
    """The table query on a part holding a table identifier: the recorded
    identifier value-equals the queried one."""
    return table == q_table


# --- impl region of model.py, verbatim with contract calls stripped -----------

def build_constraint_columns(db_table, columns):
    # Record the table as the plain table name (value-comparable), and the
    # constraint's column set, against which membership is tested.
    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart
    return part


# --- oracle: the real patched repo construction --------------------------------

def _make_oracle():
    import os
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[],
        )
    django.setup()
    from django.db import connection, models

    class ConfProbeModel(models.Model):
        class Meta:
            app_label = "conf_probe_14434"
            db_table = "conf_probe_table"

    editor = connection.schema_editor(collect_sql=True)
    return connection, editor, ConfProbeModel


def real_columns_part(editor, model, db_table, columns, expressions=None):
    """Run the real (patched) construction and return (statement,
    column-bearing part). ``name`` is passed explicitly so the name part of
    the statement is a plain string with no reference semantics."""
    model._meta.db_table = db_table
    stmt = editor._create_unique_sql(model, list(columns),
                                     name="conf_probe_name",
                                     expressions=expressions)
    return stmt, stmt.parts["columns"]


# --- bridge helpers -------------------------------------------------------------

def to_cps(s):
    return [ord(ch) for ch in s]


class CodeMap(object):
    """Per-scenario injective column-name -> int-code map (mapping.md
    section 2: only equality/membership of names is observed, preserved
    under any injective map)."""

    def __init__(self):
        self._codes = {}

    def code(self, name):
        if name not in self._codes:
            self._codes[name] = len(self._codes)
        return self._codes[name]


# --- differential driver ---------------------------------------------------------

class Driver(object):
    def __init__(self, editor, model):
        self.editor = editor
        self.model = model
        self.checked = 0
        self.errors = []

    def run_scenario(self, db_table, columns, query_cols, query_tables,
                     expressions=None):
        """Build both sides once, then compare every query.

        db_table: str; columns: list of str recorded column names (empty only
        with ``expressions``); query_cols / query_tables: the queried names.
        """
        cmap = CodeMap()
        col_codes = PSeq._wrap(cmap.code(n) for n in columns)
        table_cps = to_cps(db_table)

        # SHADOW: the impl region builds the part; the pure predicates answer.
        part = build_constraint_columns(table_cps, col_codes)

        # ORACLE: the real patched construction.
        stmt, real_part = real_columns_part(self.editor, self.model,
                                            db_table, columns,
                                            expressions=expressions)

        for q_table in query_tables:
            q_cps = to_cps(q_table)
            for q_col in query_cols:
                shadow = constrains_column(part.plain, ToSeq(part.table),
                                           part.columns, ToSeq(q_cps),
                                           cmap.code(q_col))
                real = real_part.references_column(q_table, q_col)
                self.checked += 1
                if bool(shadow) != bool(real):
                    self._fail(db_table, columns, q_table, q_col,
                               "column part", shadow, real)
                    return
                # whole-statement view (reduces to the column-bearing part
                # because every other part carries no column reference)
                real_stmt = stmt.references_column(q_table, q_col)
                self.checked += 1
                if bool(shadow) != bool(real_stmt):
                    self._fail(db_table, columns, q_table, q_col,
                               "whole statement", shadow, real_stmt)
                    return
            shadow_t = constrains_table(ToSeq(part.table), ToSeq(q_cps))
            real_t = real_part.references_table(q_table)
            self.checked += 1
            if bool(shadow_t) != bool(real_t):
                self._fail(db_table, columns, q_table, None,
                           "table query", shadow_t, real_t)
                return

    def _fail(self, db_table, columns, q_table, q_col, where, shadow, real):
        msg = ("DISAGREEMENT (%s) at db_table=%r columns=%r "
               "q_table=%r q_col=%r:\n  shadow=%r\n  real=%r"
               % (where, db_table, columns, q_table, q_col, shadow, real))
        print(msg)
        self.errors.append(msg)


def query_battery(db_table, columns, rng=None):
    """The queried names for one scenario: every recorded column, near-miss
    and unrelated column names; the recorded table, near-miss and unrelated
    table names."""
    qcols = list(dict.fromkeys(columns))
    qcols += ["__absent__", ""]
    if columns:
        qcols.append(columns[0] + "x")
        qcols.append(columns[0].upper())
    if rng is not None:
        qcols.append("".join(rng.choice(FUZZ_NAME_ALPHABET)
                             for _ in range(rng.randint(0, 6))))
    qtables = [db_table, db_table + "x", "", "unrelated_table"]
    if db_table:
        qtables.append(db_table.upper())
        qtables.append(db_table[:-1])
    return list(dict.fromkeys(qcols)), list(dict.fromkeys(qtables))


BOUNDARY_TABLES = [
    "schema_author",
    "a",
    "",
    "0",
    "tbl.with.dots",
    'quoted"tbl',
    "tbl with spaces",
    "\u00e9\u4e16_table",
    "x" * 200,
    "_",
]

BOUNDARY_COLSETS = [
    ["name"],
    ["name", "birthday"],
    ["a"],
    ["a", "b", "c", "d", "e", "f", "g", "h"],
    ["dup", "dup"],                      # duplicate entries in the recorded set
    [""],                                # empty-string column name
    ["name", ""],
    ["\u00e9col", "col\u4e16"],
    ["UPPER", "upper"],                  # case-distinct names stay distinct
    ['q"uote', "sp ace", "do.t"],
]

FUZZ_NAME_ALPHABET = ("abcdefgh" "ABC" "0123456789" "_\"'`. \u00e9\u4e16%")


def main():
    connection, editor, model = _make_oracle()
    driver = Driver(editor, model)

    # boundary grid: tables x column sets
    for db_table in BOUNDARY_TABLES:
        for columns in BOUNDARY_COLSETS:
            qcols, qtables = query_battery(db_table, columns)
            driver.run_scenario(db_table, columns, qcols, qtables)
            if driver.errors:
                return 1

    # empty recorded column set via the expression-based branch (a literal
    # expression references no columns), when the backend supports it
    expr_checked = False
    if connection.features.supports_expression_indexes:
        from django.db.models import Value
        for db_table in BOUNDARY_TABLES:
            qcols, qtables = query_battery(db_table, [])
            driver.run_scenario(db_table, [], qcols, qtables,
                                expressions=Value(1))
            if driver.errors:
                return 1
        expr_checked = True

    # randomized fuzz scenarios (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        db_table = "".join(rng.choice(FUZZ_NAME_ALPHABET)
                           for _ in range(rng.randint(0, 16)))
        ncols = rng.randint(1, 6)
        columns = ["".join(rng.choice(FUZZ_NAME_ALPHABET)
                           for _ in range(rng.randint(0, 8)))
                   for _ in range(ncols)]
        qcols, qtables = query_battery(db_table, columns, rng=rng)
        driver.run_scenario(db_table, columns, qcols, qtables)
        if driver.errors:
            return 1

    if driver.checked < 100000:
        print("FAIL: only %d checks executed (< 1e5)" % driver.checked)
        return 1

    print("PASS: shadow (contract-stripped impl region + pure query "
          "predicates) == real patched construction on %d reference-query "
          "checks (%d boundary tables x %d column sets + %s + %d fuzz "
          "scenarios); pinned seed %d; 0 disagreements."
          % (driver.checked, len(BOUNDARY_TABLES), len(BOUNDARY_COLSETS),
             "expression-branch empty sets" if expr_checked
             else "expression branch unsupported, skipped",
             N_FUZZ, SEED))
    print(json.dumps({"checked": driver.checked, "disagreements": 0,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
