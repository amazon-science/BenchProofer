#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13089 (nagini).

SHADOW: the impl region of model.py `boundary_for_prune`, copied verbatim
below with the contract calls (Requires/Ensures) stripped. The model IS
Python: the carrier is a plain Optional[List[int]], no PSeq shim is needed,
and this bundle has no @Pure helpers and no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.core.cache.backends.db.DatabaseCache._cull`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched module importable. `_cull` is driven with a scripted DB-API
cursor test double so that the boundary fetch (the culling SELECT's
fetchone) yields exactly the modeled row; every other `_cull` step
(expiry DELETE, COUNT, the cull-threshold test) is unchanged surrounding
logic that the double satisfies deterministically so the modeled site is
reached on every input.

Type bridge (mapping.md section 2):
  * model input `row: Optional[List[int]]`  <->  the boundary fetchone()
    result: None for an empty result set, else a DB-API row realized here
    as a non-empty tuple of column values (int column values stand in for
    the key column; the modeled observable is presence + first-column
    identity, not lexical content).
  * model Result(): Optional[int]  <->  the observable of the real run:
    the parameter bound into the prune statement issued after the boundary
    fetch (executes are recorded by the cursor double), or None when no
    such statement is issued.
The Requires (row is None, or len(row) > 0) is enforced by the generator:
only None or non-empty rows are fed, which is exactly the reachable domain
(the culling SELECT projects a single column, so a returned row is never
empty).

>= 1e5 Requires-satisfying inputs: 24 boundary cases (None; single-column
rows at 0 / +-1 / extreme 64-bit values; multi-column rows; duplicated and
descending columns) + 100000 fuzz rows (absent ~1/8 of the time; lengths
1..6; values across small / large / negative ranges). Pinned fuzz seed:
13089.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import datetime
import json
import random
import sys

SEED = 13089
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ---------

def boundary_for_prune(row):
    if row is not None:
        last = row[0]
        return last
    return None


# --- scripted DB-API cursor double (the real function's I/O surface) --------

class ScriptedCursor(object):
    """Records execute() calls; fetchone() answers from a fixed script:
    first the row-count answer (drives the unchanged threshold test into
    the culling branch), then the boundary row under test."""

    def __init__(self, count_row, boundary_row):
        self.executed = []
        self._fetch_script = [count_row, boundary_row]

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params) if params is not None else None))

    def fetchone(self):
        return self._fetch_script.pop(0)


def make_real_prune_key(cache_obj):
    """The oracle observable: drive the REAL patched _cull to the boundary
    fetch with `row`, and report the key bound into the prune statement
    issued after that fetch — or None when no such statement was issued."""
    now = datetime.datetime(2020, 1, 1, 12, 0, 0)

    def real_prune_key(row):
        cur = ScriptedCursor(count_row=(100,), boundary_row=row)
        cache_obj._cull('default', cur, now)
        # deterministic prefix: expiry DELETE, COUNT SELECT, culling SELECT.
        n = len(cur.executed)
        assert n in (3, 4), "unexpected statement count %d: %r" % (n, cur.executed)
        if n == 4:
            params = cur.executed[3][1]
            assert params is not None and len(params) == 1
            return params[0]
        return None

    return real_prune_key


# --- input generation (Requires-satisfying: None or a non-empty row) --------

def boundary_rows():
    rows = [None]
    for v in (0, 1, -1, 2, 42, -42, 2**31 - 1, -2**31, 2**63 - 1, -2**63):
        rows.append((v,))
    rows += [
        (0, 0), (1, 2), (2, 1), (-1, -1, -1),
        (5, 4, 3, 2, 1), (7, 7), (0, 2**63 - 1), (-2**63, 0),
        tuple(range(6)), (9,) * 6,
        (2**63 - 1, -2**63), (123456789, 0, -1),
        (3,),
    ]
    return rows


def fuzz_row(rng):
    if rng.random() < 0.125:
        return None
    length = rng.randint(1, 6)
    vals = []
    for _ in range(length):
        pick = rng.random()
        if pick < 0.5:
            vals.append(rng.randint(-10, 10))
        elif pick < 0.8:
            vals.append(rng.randint(-10**6, 10**6))
        else:
            vals.append(rng.choice((2**63 - 1, -2**63, 2**31, -2**31, 10**18)))
    return tuple(vals)


# --- the differential check --------------------------------------------------

def check_row(real_prune_key, row):
    # bridge the modeled carrier: the shadow takes the row as a plain
    # sequence of column values (List[int] in the model); the oracle takes
    # the same values as a DB-API row tuple. Requires holds by generation.
    assert row is None or len(row) > 0
    shadow_row = None if row is None else list(row)

    try:
        real = real_prune_key(row)
    except Exception as exc:  # a crash on a Requires-satisfying input
        print("DISAGREEMENT\n  row=%r\n  real raised %r\n  shadow=%r"
              % (row, exc, boundary_for_prune(shadow_row)))
        return False
    shad = boundary_for_prune(shadow_row)
    if real != shad or (real is None) != (shad is None):
        print("DISAGREEMENT\n  row=%r\n  real prune key=%r\n  shadow=%r"
              % (row, real, shad))
        return False
    return True


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            USE_TZ=False,
            DATABASES={'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }},
        )
    django.setup()
    from django.core.cache.backends.db import DatabaseCache  # REAL patched code

    cache_obj = DatabaseCache('conf_check_table', {})
    # unchanged surrounding logic, pinned so every input reaches the
    # modeled site: nonzero cull frequency, threshold below the scripted
    # row count.
    cache_obj._max_entries = 10
    cache_obj._cull_frequency = 3
    real_prune_key = make_real_prune_key(cache_obj)

    checked = 0
    n_boundary = 0
    for row in boundary_rows():
        if not check_row(real_prune_key, row):
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        if not check_row(real_prune_key, fuzz_row(rng)):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real _cull prune-boundary observable on "
          "%d rows (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
