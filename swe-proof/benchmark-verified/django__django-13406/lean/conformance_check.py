#!/usr/bin/env python3
"""G-CONF for django__django-13406.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_installQuery` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `QuerySet.query` setter,
over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): installing a prepared query into a result set
  * stores the query verbatim (`self._query = value`), and
  * if the query projects a specific set of fields (`value.values_select` non-empty)
    switches the row-building strategy to the field-value-mapping one
    (`ValuesIterable`); otherwise leaves the strategy untouched.

  * Oracle  = the REAL patched `QuerySet.query` setter run on a live QuerySet whose
              `_iterable_class` is pre-set to one of the five concrete iterable
              classes, installing a Query whose `values_select` is the fuzzed field
              list. Observation = (qs._iterable_class.__name__, qs._query is value).
  * Shadow  = the transliterated Lean impl over the same inputs, observing
              (rowMode_name, stored_query_is_value).

Type bijection (mapping.md):
  rowMode : RowMode            <-> _iterable_class (BaseIterable subclass), by __name__
  storedQuery : StoredQuery    <-> _query (Query), by object identity
  selectedFields : List String <-> value.values_select (tuple of str), emptiness preserved

stdlib-only; no hypothesis required.
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
from django.db.models.query import (
    QuerySet,
    ModelIterable,
    ValuesIterable,
    ValuesListIterable,
    FlatValuesListIterable,
    NamedValuesListIterable,
)
from django.db.models.sql import Query

# RowMode enumeration <-> the five concrete iterable classes (mapping.md).
ROW_MODES = [
    ("modelInstances", ModelIterable),
    ("fieldValuesDict", ValuesIterable),
    ("fieldValuesTuple", ValuesListIterable),
    ("fieldValuesFlat", FlatValuesListIterable),
    ("fieldValuesNamed", NamedValuesListIterable),
]
NAME_BY_CLASS = {cls.__name__: name for name, cls in ROW_MODES}

FIELD_POOL = ["name", "material", "price", "id", "app_label", "model", "when"]


def make_query(selected_fields):
    """A real Query whose values_select is the fuzzed field-name tuple."""
    q = Query(ContentType)
    q.values_select = tuple(selected_fields)
    return q


def oracle(initial_mode_cls, selected_fields):
    """Behavior of the REAL patched `QuerySet.query` setter."""
    qs = QuerySet(model=ContentType)
    qs._iterable_class = initial_mode_cls
    value = make_query(selected_fields)
    qs.query = value  # patched setter
    return (qs._iterable_class.__name__, qs._query is value)


def shadow(initial_mode_name, initial_mode_cls, selected_fields):
    """R/I transliteration of implementation_installQuery (Lean).

    Op 1: bind a mutable handle on (rowMode, storedQuery).
    Op 2 (R): if selectedFields != [] then rowMode := fieldValuesDict.
    Op 3 (R/I): storedQuery := value.
    Op 4: return.
    """
    value = make_query(selected_fields)
    row_mode_name = initial_mode_name
    if list(value.values_select) != []:  # selectedFields != []
        row_mode_name = "fieldValuesDict"
    stored = value
    # Observation mirrors the oracle: (iterable class __name__, query is value).
    cls_name = dict(ROW_MODES)[row_mode_name].__name__
    return (cls_name, stored is value)


def rand_fields(rng):
    if rng.random() < 0.4:
        return []  # empty: query projects no specific fields
    n = rng.randint(1, 4)
    return [rng.choice(FIELD_POOL) for _ in range(n)]


def main():
    rng = random.Random(13406)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        mode_name, mode_cls = rng.choice(ROW_MODES)
        selected = rand_fields(rng)
        o = oracle(mode_cls, selected)
        s = shadow(mode_name, mode_cls, selected)
        if o != s:
            disagreements += 1
            if first is None:
                first = (mode_name, selected, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
