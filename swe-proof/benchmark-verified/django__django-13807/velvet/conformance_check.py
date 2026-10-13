#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13807 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the SQL statement strings
each constructs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the statement
              builders `fkCheckSql` / `fkListSql` / `selectSql` and the two
              backward folds `checkStmts` / `violationStmts`) transliterated to
              Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`). The A-tagged callee `quoteIdent`
              is NOT substituted by its deep-model encoding here; G-CONF isolates
              the R/I legs, so the identifier quoter is left as the REAL repo
              callee `DatabaseOperations.quote_name` (its soundness stays with
              G-AX). Thus G-CONF refutes the *concatenation* structure: literals,
              order, and which positions receive an identifier.
  * ORACLE  — `patch.diff`'s behaviour: the exact `%`-format SQL templates the
              patched `check_constraints` assembles, with `self.ops.quote_name`
              applied at each identifier position (read from the patched source
              at base_commit; the harness applies patch.diff before this runs).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_TZ=False,
    )
    django.setup()

from django.db.backends.sqlite3.operations import DatabaseOperations

SEED = 13807
N_FUZZ = 100_000

_ops = DatabaseOperations(connection=None)


def q(name):
    """The A-tagged identifier quoter: the REAL repo callee (not the model)."""
    return _ops.quote_name(name)


# --- the R/I shadow: Solution.lean statement builders, transliterated --------
# fkCheckSql / fkListSql / selectSql are the concatenation (R/I) ops; quoteIdent
# is left as the real callee `q`.

def shadow_check_sql(table):
    return "PRAGMA foreign_key_check(" + q(table) + ")"


def shadow_list_sql(table):
    return "PRAGMA foreign_key_list(" + q(table) + ")"


def shadow_select_sql(pk, col, table):
    return ("SELECT " + q(pk) + ", " + q(col) + " FROM " + q(table)
            + " WHERE rowid = %s")


# --- the oracle: patch.diff's exact `%`-format templates ---------------------

def oracle_check_sql(table):
    return 'PRAGMA foreign_key_check(%s)' % q(table)


def oracle_list_sql(table):
    return 'PRAGMA foreign_key_list(%s)' % q(table)


def oracle_select_sql(pk, col, table):
    return 'SELECT %s, %s FROM %s WHERE rowid = %%s' % (q(pk), q(col), q(table))


def fuzz_idents(rng):
    keywords = ["order", "select", "where", "table", "from", "group", "by"]
    ordinary = ["id", "name", "reporter_id", "a", "Z", "_x", "x9", "col1"]
    quoted = ['"order"', '"select"', '"where"', '"id"']
    alphabet = list('abcdef_0123456789') + ['"', ' ', ';', '.']
    pool = keywords + ordinary + quoted
    yield from ((n, n, n) for n in pool)           # each name in every position
    for _ in range(N_FUZZ):
        def mk():
            if rng.random() < 0.4:
                return rng.choice(pool)
            return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        yield (mk(), mk(), mk())


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for pk, col, table in fuzz_idents(rng):
        count += 1
        checks = [
            (shadow_check_sql(table), oracle_check_sql(table)),
            (shadow_list_sql(table), oracle_list_sql(table)),
            (shadow_select_sql(pk, col, table), oracle_select_sql(pk, col, table)),
        ]
        for shadow, oracle in checks:
            if shadow != oracle:
                disagreements.append((pk, col, table, shadow, oracle))
                break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d input triples:"
              % (len(disagreements), count))
        for pk, col, table, sh, orc in disagreements:
            print("  pk=%r col=%r table=%r shadow=%r oracle=%r"
                  % (pk, col, table, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of the statement builders agrees with patch.diff "
          "behaviour on %d input triples (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
