#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14434 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo carriers, via the mapping.md
              bijection (`String` ↔ `str`, `List String` ↔ `list[str]`,
              `TableSlot.name` ↔ a bare table-name string fed to the columns
              reference). The impl region is pure R/I (it only wires up which
              carrier the columns reference stores); there are no A-tagged
              callees in the computed `out`, so the shadow is the model's
              `referencesColumn` / `referencesTable` predicate over that wiring.
  * ORACLE  — `patch.diff`'s behaviour: the patched `_create_unique_sql`
              data-flow on the F2P column-list path (a given constraint name,
              a non-empty column list), reconstructed with the REAL unchanged
              `django.db.backends.ddl_references` classes. The patch makes
              `_index_columns` receive the bare table *name* string, so the
              real `Columns` stores a value-comparable table slot; the
              `Statement` wraps the name in `Table(...)` for its `table=` part.
              We then observe the real objects' references_column /
              references_table — the exact observable the F2P test asserts —
              plus the rendered column sequence `str(columns_part)` (the
              `Stmt.renderedColumns` observable: what the generated DDL text
              contains, via `Statement.__str__`'s `%(columns)s`).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only (django
is the repo under test). The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

from django.db.backends.ddl_references import Columns, Statement, Table

SEED = 14434
N_FUZZ = 100_000


def quote_name(name):
    return '"%s"' % name


# --- the R/I shadow: Solution.lean impl + model predicates, transliterated ---

def shadow_build(db_table, columns):
    """buildUniqueStatement transliterated: the columns reference stores the
    bare table NAME (TableSlot.name); the statement's table part wraps it."""
    return {
        "slot_kind": "name",     # TableSlot.name dbTable
        "slot_name": db_table,
        "columns": list(columns),
        "table_name": db_table,
    }


def shadow_references_column(s, t, col):
    slot_matches = (s["slot_name"] == t) if s["slot_kind"] == "name" else False
    return slot_matches and (col in s["columns"])


def shadow_references_table(s, t):
    slot_matches = (s["slot_name"] == t) if s["slot_kind"] == "name" else False
    return (s["table_name"] == t) or slot_matches


def shadow_rendered_columns(s):
    """Stmt.renderedColumns = cols.columns, rendered by the real Columns.__str__
    as ', '.join(quote_name(c)) — bridged via the identity-ish quote_name."""
    return ", ".join(quote_name(c) for c in s["columns"])


# --- the oracle: patch.diff's data-flow with the REAL ddl_references ---------

def oracle_build(db_table, columns):
    """patch.diff column-list path: table = model._meta.db_table (a str);
    columns = self._index_columns(table, columns, ...) = Columns(table_str, ...);
    return Statement(table=Table(table_str, quote_name), columns=columns, ...)."""
    cols = Columns(db_table, list(columns), quote_name)   # bare string slot
    return Statement(
        "SQL",
        table=Table(db_table, quote_name),
        name=quote_name("name_uq"),
        columns=cols,
    )


def fuzz_inputs(n, rng):
    # boundary cases first
    yield ("t", ["name"])
    yield ("mytable", ["name"])
    yield ("schema_author", ["name", "birthday"])
    yield ("x", ["a", "b", "c"])
    yield ("Capital_T", ["Name", "name"])
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    def rand_ident(maxlen=10):
        k = rng.randint(1, maxlen)
        return "".join(rng.choice(alphabet) for _ in range(k))
    for _ in range(n):
        db_table = rand_ident()
        columns = [rand_ident() for _ in range(rng.randint(1, 5))]
        yield (db_table, columns)


def queries_for(db_table, columns, rng):
    qs = []
    for col in columns:
        qs.append((db_table, col))            # own table + listed column -> True
        qs.append(("other", col))             # foreign table -> False
    qs.append((db_table, "absent_col"))        # foreign column -> False
    qs.append(("other", "absent_col"))         # both foreign -> False
    # a couple of random queries
    for _ in range(2):
        t = rng.choice([db_table, "rnd_" + str(rng.randint(0, 9))])
        c = rng.choice(columns + ["rnd_col"])
        qs.append((t, c))
    return qs


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (db_table, columns) in fuzz_inputs(N_FUZZ, rng):
        shadow = shadow_build(db_table, columns)
        oracle = oracle_build(db_table, columns)
        # rendered-columns observable (Stmt.renderedColumns): the column
        # sequence the columns part renders into the DDL text, in order.
        count += 1
        sh_r = shadow_rendered_columns(shadow)
        or_r = str(oracle.parts["columns"])
        if sh_r != or_r:
            disagreements.append(
                (db_table, columns, None, None, (sh_r,), (or_r,)))
        for (t, col) in queries_for(db_table, columns, rng):
            count += 1
            sh_c = bool(shadow_references_column(shadow, t, col))
            or_c = bool(oracle.references_column(t, col))
            sh_t = bool(shadow_references_table(shadow, t))
            or_t = bool(oracle.references_table(t))
            if sh_c != or_c or sh_t != or_t:
                disagreements.append(
                    (db_table, columns, t, col,
                     (sh_c, sh_t), (or_c, or_t)))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d observations:"
              % (len(disagreements), count))
        for dt, cols, t, col, sh, orc in disagreements:
            print("  db_table=%r columns=%r q=(%r,%r) shadow(col,tab)=%r "
                  "oracle(col,tab)=%r" % (dt, cols, t, col, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildUniqueStatement agrees with patch.diff "
          "behaviour (real ddl_references) on %d observations (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
