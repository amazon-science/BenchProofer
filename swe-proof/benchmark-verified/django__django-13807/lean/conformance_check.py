#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_fkCheckQueries
against the patch.diff behaviour (post-patch constraint-check query rendering).

The impl region is R/I plus one A-reference op (quote_name, row 2 of
refinement.md). Per the construction protocol, the A-tagged callee is left as the
REAL repo callee in the shadow; the surrounding R/I ops are reproduced
op-for-op. We diff the shadow against an independent reconstruction of the
post-patch rendering: the three literal `%`-templates from the patched
`check_constraints`, with every identifier substituted via the real
`quote_name`. Zero disagreements required over >=10^5 fuzzed inputs.

stdlib-only (+ the in-tree django callee). exit 0 iff zero disagreements.
"""
import random
import sys


def real_quote_name(name: str) -> str:
    """The REAL unchanged callee, django/db/backends/sqlite3/operations.py:170-173.

    Imported from the in-tree repo when available; falls back to a byte-for-byte
    copy so the differential test runs even outside a configured django app
    (the source is pinned at base_commit and is not touched by the patch)."""
    try:
        from django.db.backends.sqlite3.operations import DatabaseOperations
        return DatabaseOperations.quote_name(None, name)
    except Exception:
        if name.startswith('"') and name.endswith('"'):
            return name
        return '"%s"' % name


# --- the three literal SQL templates from the patched check_constraints ---
T_FK_CHECK = "PRAGMA foreign_key_check(%s)"
T_FK_LIST = "PRAGMA foreign_key_list(%s)"
T_SELECT = "SELECT %s, %s FROM %s WHERE rowid = %%s"


def shadow(table: str, primary_key: str, column: str):
    """R/I shadow of implementation_fkCheckQueries (A-reference quote_name left
    as the real callee)."""
    qt = real_quote_name(table)
    qp = real_quote_name(primary_key)
    qc = real_quote_name(column)
    fk_check = "PRAGMA foreign_key_check(" + qt + ")"
    fk_list = "PRAGMA foreign_key_list(" + qt + ")"
    select_row = ("SELECT " + qp + ", " + qc + " FROM " + qt
                  + " WHERE rowid = %s")
    return (fk_check, fk_list, select_row)


def patched_render(table: str, primary_key: str, column: str):
    """Independent reconstruction of the post-patch rendering: the exact
    `%`-substitutions performed by the patched check_constraints."""
    fk_check = T_FK_CHECK % real_quote_name(table)
    fk_list = T_FK_LIST % real_quote_name(table)
    select_row = T_SELECT % (
        real_quote_name(primary_key),
        real_quote_name(column),
        real_quote_name(table),
    )
    return (fk_check, fk_list, select_row)


SEED = 13807          # pinned in mapping.md
N = 120_000           # >= 10^5

# SQL-identifier alphabet; reserved words and quoted/empty names oversampled so
# the missing-quote bug and the quote_name idempotence branch are exercised.
IDENT_ALPHABET = list('abcXYZ_0123 "().,select')
RESERVED = ["order", "select", "where", "group", "table",
            '"order"', '"select"', "", "a", "Author_book"]


def rand_ident(rng):
    if rng.random() < 0.4:
        return rng.choice(RESERVED)
    return "".join(rng.choice(IDENT_ALPHABET)
                   for _ in range(rng.randint(0, 16)))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        ("order", "select", "where"),      # the F2P regression case
        ("order", "id", "reporter_id"),
        ('"order"', "id", "x"),            # already-quoted table (idempotence)
        ("", "", ""),
        ("Author", "name", "author_id"),
        ("group", "select", "from"),
    ]
    cases = fixed + [
        (rand_ident(rng), rand_ident(rng), rand_ident(rng))
        for _ in range(N)
    ]

    for table, pk, col in cases:
        got = shadow(table, pk, col)
        want = patched_render(table, pk, col)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((table, pk, col), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
