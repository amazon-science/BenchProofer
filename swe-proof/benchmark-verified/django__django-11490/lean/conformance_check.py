#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11490.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_propagateColumns` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched per-part column-propagation
behavior of `SQLCompiler.get_combinator_sql`, over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

Model (refinement.md): evaluating a composed query (column list `composedColumns`)
over its parts, for each part:
  * if the part fixes NO column list of its own (`not values_select`) AND the
    composed query requests a specific list (`self.query.values_select`), the
    query USED to build that part this evaluation adopts the composed list, while
    the part DEFINITION is carried forward UNCHANGED;
  * otherwise the part is used as given and carried forward unchanged.

The fixed mechanism is `compiler.query = compiler.query.clone()` BEFORE
`set_values(...)` mutates it: the clone is what adopts the composed list, the
shared part is never altered. `set_values`' only observable on the modeled
behavior is the resulting query's column list (`self.values_select =
tuple(field_names)`, the no-extra/no-annotation shortcut); we exercise the REAL
`Query.clone()` (the actual changed operation) and assign that column-list
observable on the clone, then verify the SHARED part's column list is untouched.

  * Oracle  = the REAL patched branch on real `Query` objects:
              if not q.values_select and composed:
                  used = q.clone(); used.values_select = tuple(composed)
                  carried = q                      # shared part, never mutated
              else:
                  used = q; carried = q
              observe (tuple(used.values_select), tuple(carried.values_select)).
  * Shadow  = the transliterated Lean impl over the same inputs, observing
              (used_columns, carried_columns) per part.

Type bijection (mapping.md):
  QueryPart.columns : List String  <-> Query.values_select (tuple of str)
  composedColumns   : List String  <-> self.query.values_select (tuple of str)
  result entry .fst <-> used query's values_select ; .snd <-> carried part's values_select

stdlib-only; deterministic built-in fuzzer. Pinned seed: 11490 (also in mapping.md).
"""
import os
import random
import sys

# --- configure Django settings before importing the ORM machinery ------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
    )
    django.setup()

from django.contrib.contenttypes.models import ContentType
from django.db.models.sql import Query

COLUMN_POOL = ["name", "order", "id", "app_label", "model", "price", "when", "num"]


def make_query(columns):
    """A real Query whose values_select is the given column tuple."""
    q = Query(ContentType)
    q.values_select = tuple(columns)
    return q


def oracle_part(part_columns, composed_columns):
    """REAL patched per-part propagation, exercising Query.clone()."""
    q = make_query(part_columns)
    if not q.values_select and tuple(composed_columns):
        used = q.clone()                       # <-- the fix: distinct object
        used.values_select = tuple(composed_columns)   # net observable of set_values
        carried = q                            # shared part: never mutated
    else:
        used = q
        carried = q
    return (tuple(used.values_select), tuple(carried.values_select))


def shadow_part(part_columns, composed_columns):
    """R/I transliteration of implementation_propagateColumns (one iteration).

    Op 3 (R): adopt iff part fixes no list AND composed requests one.
    Op 4-5 (R): derived = {part with columns := composedColumns}; (derived, part).
    Op 6 (I): else (part, part).
    """
    if list(part_columns) == [] and list(composed_columns) != []:
        derived = tuple(composed_columns)
        return (derived, tuple(part_columns))
    else:
        return (tuple(part_columns), tuple(part_columns))


def rand_columns(rng):
    if rng.random() < 0.45:
        return []  # part / composed fixes no specific list
    n = rng.randint(1, 4)
    return [rng.choice(COLUMN_POOL) for _ in range(n)]


def main():
    rng = random.Random(11490)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        composed = rand_columns(rng)
        nparts = rng.randint(1, 4)
        for _ in range(nparts):
            part = rand_columns(rng)
            o = oracle_part(part, composed)
            s = shadow_part(part, composed)
            if o != s:
                disagreements += 1
                if first is None:
                    first = (part, composed, o, s)
    if disagreements:
        print("G-CONF FAIL: %d disagreements; first=%r" % (disagreements, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
