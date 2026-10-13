#!/usr/bin/env python3
"""G-CONF for django__django-12965.

The gold patch is already applied to /testbed when this runs. We compare the
R/I + A-reference Python shadow of `implementation_isSingleTableDelete` (the Lean
impl, transliterated op-for-op per refinement.md) against the REAL patched
`SQLDeleteCompiler.single_alias`, over >=1e5 fuzzed reference-count
configurations. Zero disagreements => exit 0.

Model (refinement.md): a deletion's `single_alias` decision is a single boolean
determined solely by the query's recorded table references and their reference
counts. Table NAMES are irrelevant to the boolean (only dict keys), so the query
is modeled as `refs : List Nat` = the reference counts in `alias_map` insertion
order. The fix first calls `get_initial_alias()` (guarantee the primary table is
recorded), then counts references with positive count and compares to one.

  * Oracle  = the REAL patched `SQLDeleteCompiler.single_alias` for a query whose
              alias_map/alias_refcount carry the fuzzed `refs` (empty `refs` is
              left as a genuine fresh full-table-delete query, so the REAL
              `get_initial_alias` empty branch runs).
  * Shadow  = (op 1, A-reference) `includePrimary refs`
              (op 2, R)          count of entries with count > 0
              (op 3, I)          `== 1`.

`includePrimary` (deep model of `get_initial_alias`'s effect on the count
multiset): `[] -> [1]`; `c :: rest -> (c+1) :: rest`.

Type bijection (mapping.md): refs<->[alias_refcount[t] for t in alias_map]
(List Nat <-> list[int>=0]); result<->bool(single_alias).
stdlib-only; no hypothesis required.
"""
import collections
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
    django.setup()

from django.db import connection
from django.db.models.sql.query import Query
from django.db.models.sql.compiler import SQLDeleteCompiler
from django.db.models.sql.datastructures import BaseTable
from django.contrib.auth.models import User


def build_query(refs):
    """Materialize a real Query whose recorded references have the given counts.

    Empty `refs` is left as a genuine fresh full-table-delete query so the REAL
    `get_initial_alias` empty branch (add a fresh count-1 reference) runs inside
    the oracle. Non-empty `refs` are installed directly into
    alias_map/alias_refcount in insertion order.
    """
    q = Query(User)
    if not refs:
        return q
    q.alias_map = collections.OrderedDict()
    q.alias_refcount = {}
    q.table_map = {}
    for i, c in enumerate(refs):
        alias = "t%d" % i
        table = "tbl%d" % i
        q.alias_map[alias] = BaseTable(table, alias)
        q.alias_refcount[alias] = c
        q.table_map.setdefault(table, []).append(alias)
    # invalidate the cached base_table so it reflects the installed alias_map
    q.__dict__.pop('base_table', None)
    return q


def oracle(refs):
    """Behavior of the patched repo function for these reference counts."""
    q = build_query(refs)
    compiler = SQLDeleteCompiler(q, connection, connection.alias)
    return bool(compiler.single_alias)


def include_primary(refs):
    """Deep model of get_initial_alias's effect on the reference-count list."""
    if not refs:
        return [1]
    return [refs[0] + 1] + list(refs[1:])


def shadow(refs):
    """R/I + A-reference transliteration of implementation_isSingleTableDelete."""
    refs2 = include_primary(refs)           # op 1 (A-reference)
    active = 0                              # op 2 (R)
    for c in refs2:
        if c > 0:
            active += 1
    return active == 1                      # op 3 (I)


def main():
    rng = random.Random(12965)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        # weight the empty (full-table delete) case heavily — it is the
        # discriminating case the fix targets.
        if rng.random() < 0.25:
            refs = []
        else:
            n = rng.randint(1, 6)
            refs = [rng.randint(0, 3) for _ in range(n)]
        o = oracle(refs)
        s = shadow(refs)
        if o != s:
            disagreements += 1
            if first is None:
                first = (refs, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
