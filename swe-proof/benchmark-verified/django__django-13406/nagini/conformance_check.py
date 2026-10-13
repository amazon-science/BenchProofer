#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13406 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl region itself contains no Requires/Ensures lines).
The carrier classes (ResultSet / LookupDescription) are re-declared as plain
Python classes with the same two/one touched fields; there are no @Pure
helpers, no @ContractOnly callees, and no PSeq usage in this bundle, so no
shim beyond the plain classes is needed.

ORACLE: the REAL patched repo code the model models per mapping.md — the
``django.db.models.query.QuerySet.query`` property setter. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched code importable. Django is configured in-memory (no tables are
created: the setter never executes a database query).

Type bridge (mapping.md §2):
  * ``producer_tag`` (int 0/1) <-> ``QuerySet._iterable_class`` (a class
    object): ModelIterable <-> 0, ValuesIterable (and, per mapping.md §2,
    every value-list producer flavour) <-> 1. The driver installs only the
    two canonical classes as initial producers; after the call the tag is
    read back through the same map.
  * ``value_field_count`` (int >= 0) <-> ``Query.values_select`` (a tuple of
    field-name strings): the count is the tuple's length; the real code only
    ever tests the tuple's truthiness, never its element characters, so a
    synthetic tuple of ``count`` placeholder names sits exactly at the
    modeling boundary. Boundary cases additionally use REAL
    values()/values_list()-built queries so the correspondence is also
    exercised on organically-constructed descriptions.
  * ``description`` (Optional reference) <-> ``QuerySet._query``: identity
    (`is`) compared on both sides.

Input domain (the model's Requires): value_field_count >= 0 plus write access
to the result set's two fields; the result set's initial producer tag ranges
over the model's tag domain {0, 1} and its initial description over
{None, some other description} (the model's __init__ starts at None; the
setter's contract does not read the old description, but varying it guards
against accidental sensitivity).

>= 1e5 Requires-satisfying inputs: boundary cases (counts 0..8 x both initial
tags x both initial descriptions, plus 10 real querysets) + 100000 fuzz
triples. Pinned fuzz seed: 13406.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13406
N_FUZZ = 100_000


# --- carrier classes and constants from model.py (contracts stripped) --------

PRODUCES_MODEL_INSTANCES = 0   # default producer (full model instances)
PRODUCES_VALUE_MAPPINGS = 1    # producer that yields one value mapping per row


class LookupDescription:
    def __init__(self, values_field_count):
        self.value_field_count = values_field_count


class ResultSet:
    def __init__(self, producer_tag):
        self.producer_tag = producer_tag
        self.description = None


# --- the impl region of model.py, verbatim -----------------------------------

def attach_description(rs, value):
    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value


# --- oracle driver ------------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                '__main__',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            USE_TZ=False,
        )
    django.setup()


def main():
    _configure_django()
    from django.db import models
    from django.db.models.query import (
        ModelIterable, ValuesIterable, ValuesListIterable,
        FlatValuesListIterable, NamedValuesListIterable,
    )
    from django.db.models.sql import Query

    class Toy(models.Model):
        name = models.CharField(max_length=16)
        material = models.CharField(max_length=16)
        price = models.PositiveIntegerField()

        class Meta:
            app_label = '__main__'

    TAG_BY_CLASS = {
        ModelIterable: PRODUCES_MODEL_INSTANCES,
        ValuesIterable: PRODUCES_VALUE_MAPPINGS,
        # mapping.md §2: all value-list producer flavours collapse to tag 1.
        ValuesListIterable: PRODUCES_VALUE_MAPPINGS,
        FlatValuesListIterable: PRODUCES_VALUE_MAPPINGS,
        NamedValuesListIterable: PRODUCES_VALUE_MAPPINGS,
    }
    CLASS_BY_TAG = {
        PRODUCES_MODEL_INSTANCES: ModelIterable,
        PRODUCES_VALUE_MAPPINGS: ValuesIterable,
    }

    def make_real_query(count):
        """A real sql.Query whose value-field selection has exactly `count`
        entries. The selection tuple is injected directly: the code under
        test reads only the tuple's truthiness (never its elements), so the
        injection sits exactly at the documented modeling boundary."""
        q = Query(Toy)
        q.values_select = tuple("f%d" % i for i in range(count))
        return q

    def run_real(init_tag, init_desc_count, real_query):
        """Run the REAL patched setter on a fresh result set whose initial
        producer tag / stored description are forced to the given values;
        return (final tag, stored-is-value, selection preserved)."""
        qs = Toy.objects.all()
        qs._iterable_class = CLASS_BY_TAG[init_tag]
        if init_desc_count is not None:
            qs._query = make_real_query(init_desc_count)
        before_select = real_query.values_select
        qs.query = real_query                       # the setter under test
        out_class = qs._iterable_class
        if out_class not in TAG_BY_CLASS:
            return ("<unmapped producer %r>" % (out_class,), False, False)
        return (TAG_BY_CLASS[out_class],
                qs.query is real_query,
                real_query.values_select is before_select)

    def run_shadow(init_tag, init_desc_count, count):
        rs = ResultSet(init_tag)
        if init_desc_count is not None:
            rs.description = LookupDescription(init_desc_count)
        value = LookupDescription(count)
        before = value.value_field_count
        attach_description(rs, value)
        return (rs.producer_tag,
                rs.description is value,
                value.value_field_count == before)

    checked = [0]

    def check(init_tag, init_desc_count, count, real_query=None, label=""):
        if real_query is None:
            real_query = make_real_query(count)
        shadow_out = run_shadow(init_tag, init_desc_count, count)
        real_out = run_real(init_tag, init_desc_count, real_query)
        if shadow_out != real_out:
            print("DISAGREEMENT%s\n"
                  "  init_tag=%r init_desc_count=%r value_field_count=%r\n"
                  "  shadow=(tag, stored-is-value, count-preserved)=%r\n"
                  "  real  =(tag, stored-is-value, selection-preserved)=%r"
                  % ((" [%s]" % label) if label else "",
                     init_tag, init_desc_count, count, shadow_out, real_out))
            return False
        checked[0] += 1
        return True

    # --- boundary: synthetic counts 0..8 x initial tags x initial descriptions
    for count in list(range(0, 9)) + [16, 64, 257]:
        for init_tag in (PRODUCES_MODEL_INSTANCES, PRODUCES_VALUE_MAPPINGS):
            for init_desc_count in (None, 0, 3):
                if not check(init_tag, init_desc_count, count):
                    return 1

    # --- boundary: organically-built real querysets (values / values_list
    #     flavours and plain model queries), attached to a fresh default
    #     result set — the count is read off the REAL selection tuple.
    real_querysets = [
        Toy.objects.values('material'),
        Toy.objects.values('name', 'material'),
        Toy.objects.values('material').annotate(total=models.Sum('price')),
        Toy.objects.values_list('name'),
        Toy.objects.values_list('name', flat=True),
        Toy.objects.values_list('name', named=True),
        Toy.objects.values_list('name', 'material'),
        Toy.objects.all(),
        Toy.objects.filter(material='wood'),
        Toy.objects.order_by('name'),
    ]
    for qs in real_querysets:
        q = qs.query
        count = len(q.values_select)
        if not check(PRODUCES_MODEL_INSTANCES, None, count,
                     real_query=q, label="organic queryset"):
            return 1

    # --- fuzz: pinned seed, edge-biased counts ---------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        choice = rng.randint(0, 4)
        if choice == 0:
            count = 0
        elif choice == 1:
            count = 1
        elif choice == 2:
            count = rng.randint(0, 4)
        elif choice == 3:
            count = rng.randint(0, 32)
        else:
            count = rng.randint(0, 300)
        init_tag = rng.randint(0, 1)
        init_desc_count = rng.choice((None, 0, rng.randint(1, 8)))
        if not check(init_tag, init_desc_count, count):
            return 1

    print("G-CONF OK: shadow impl == real attachment behaviour on %d inputs "
          "(boundary incl. 10 organic querysets + %d fuzz, seed %d)."
          % (checked[0], N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
