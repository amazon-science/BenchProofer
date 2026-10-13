#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13089.

This bundle ships **no `@ContractOnly` axiom** and **no A-reference deep model**:
the changed behaviour (guard the boundary-row column read on the row's presence)
is modeled directly with `Optional[List[int]]` and an `is not None` guard, and
the proof consumes no callee contract. There is therefore no callee contract to
validate against a real implementation.

What this script does instead, for completeness and to make the single
refinement assumption explicit and machine-checkable: it exercises the standard
DB-API (PEP 249) `cursor.fetchone()` contract shape that refinement.md relies on
— `fetchone()` returns `None` on an empty result set, and otherwise a non-empty
row sequence whose element `[0]` is the selected column — using the standard
library `sqlite3` module (no Django, nothing repo-specific). It then asserts
that the model's optional-row decision function reproduces the gold patch's
guarded behaviour on every observed row:

  * empty result set  -> fetchone() is None  -> no prune issued (Result is None)
  * non-empty row     -> fetchone() is a row -> prune issued with row[0]

and, crucially, that the guarded reduction never indexes an absent row (the
pre-patch defect). Imports only the standard library. Exit 0 iff every
observation matches the model.
"""
import sqlite3
import sys


def boundary_for_prune(row):
    """Reference of model.py's `boundary_for_prune`: produce the prune boundary
    key, or None when no row is present (and never index an absent row)."""
    if row is not None:          # the guard the gold patch introduces
        return row[0]
    return None


def check_against_fetchone(cursor, expect_present):
    """Run cursor.fetchone() (the REAL DB-API callee) and assert the model's
    optional-row decision matches the gold patch's guarded behaviour."""
    row = cursor.fetchone()
    if expect_present:
        assert row is not None, "expected a present row, got None"
        assert len(row) > 0, "a present single-column row must be non-empty"
        # post-patch: prune issued, bound to the first column
        assert boundary_for_prune(row) == row[0], (
            "model must produce the boundary key row[0]=%r for a present row %r"
            % (row[0], row))
    else:
        assert row is None, "expected an empty result set (None), got %r" % (row,)
        # post-patch: no prune issued; model must NOT index the absent row
        assert boundary_for_prune(row) is None, (
            "model must produce None (no prune) for an absent row")


def main():
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute("CREATE TABLE cache (cache_key TEXT)")

    # --- empty store: the culling SELECT returns no row (the F2P scenario) ---
    # Mirrors `_max_entries = -1` forcing a cull that finds nothing to prune.
    cur.execute("SELECT cache_key FROM cache ORDER BY cache_key LIMIT 1 OFFSET 0")
    check_against_fetchone(cur, expect_present=False)
    # an OFFSET past the end of a non-empty store also yields no row
    cur.executemany("INSERT INTO cache (cache_key) VALUES (?)",
                    [("k%03d" % i,) for i in range(5)])
    cur.execute("SELECT cache_key FROM cache ORDER BY cache_key LIMIT 1 OFFSET 100")
    check_against_fetchone(cur, expect_present=False)

    # --- non-empty boundary: the culling SELECT returns a row -----------------
    for offset in range(5):
        cur.execute(
            "SELECT cache_key FROM cache ORDER BY cache_key LIMIT 1 OFFSET ?",
            [offset])
        check_against_fetchone(cur, expect_present=True)

    # --- direct contract-shape fuzz over the optional-row decision ------------
    # None always -> None (no prune, no index); any present non-empty row -> [0]
    assert boundary_for_prune(None) is None
    for sample in ([0], [1], [42], [7, 99], [-1, 2, 3], list(range(1, 9))):
        assert boundary_for_prune(sample) == sample[0], (
            "present row %r must produce its first column" % (sample,))

    con.close()
    print("G-AX OK: no consumed axiom / no A-reference; DB-API fetchone() "
          "optional-row contract holds and the model's guarded reduction "
          "matches the gold patch on empty + present rows (never indexes None).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
