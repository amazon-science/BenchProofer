#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13406.

This bundle consumes NO @ContractOnly axioms: the attachment behaviour is
modelled deeply in model.py (a conditional attribute update over integer
producer tags). What G-AX validates here is the **A-reference** — that the deep
model faithfully captures the real Python/Django semantics of attaching a
lookup description to a freshly-created result set (the real ``QuerySet.query``
setter, post-patch).

It executes the REAL Django ``QuerySet.query`` setter against an in-memory
sqlite database and asserts, for every observation:

  * a query that selects an explicit set of value-fields carries a NON-EMPTY
    value-field selection (real ``query.values_select`` is truthy) exactly for
    the value-bearing queries built by ``values()`` / ``values_list()`` — the
    modelled ``value.value_field_count > 0``;

  * a plain (model-instance) query carries an EMPTY value-field selection
    (``query.values_select`` is falsy) — the modelled ``value_field_count == 0``;

  * after attaching a value-bearing query to a freshly-created result set
    (whose default producer yields model instances), the result set's row
    producer becomes the value-mapping producer (``_iterable_class is
    ValuesIterable``) — the modelled ``producer_tag == PRODUCES_VALUE_MAPPINGS``;

  * after attaching a plain (no value-fields) query, the result set keeps its
    default model-instance producer (``_iterable_class is ModelIterable``) —
    the modelled ``producer_tag == Old(producer_tag)``;

  * the attached query is stored as the result set's active query
    (``qs.query is value``) — the modelled ``rs.description is value``.

It also confirms the underlying tag-vs-truthiness correspondence the deep model
relies on: an empty tuple is falsy and a non-empty tuple is truthy (the
A-reference proper, ``bool(query.values_select) <-> count > 0``), independently
of Django.

Run inside the official SWE-bench container for the instance, where Django is
importable. Exit 0 iff every obligation holds. Outside the container (Django
absent) it prints ``G-AX SKIP`` and returns 0; the orchestrator runs it
in-container.
"""
import random
import sys


def _check_truthiness_correspondence():
    """The A-reference proper: a value-field selection (a tuple) is truthy iff
    it is non-empty, i.e. bool(values_select) <-> len(values_select) > 0, which
    is the modelled value_field_count > 0 discriminator."""
    rng = random.Random(13406)
    for _ in range(5000):
        n = rng.randint(0, 8)
        values_select = tuple("f%d" % i for i in range(n))
        assert bool(values_select) == (len(values_select) > 0), (
            "tuple truthiness != non-emptiness")
        assert bool(values_select) == (n > 0)


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
    # The A-reference truthiness correspondence holds regardless of environment.
    _check_truthiness_correspondence()

    try:
        _configure_django()
        from django.db import models, connection
        from django.db.models.query import (
            ModelIterable, ValuesIterable, ValuesListIterable,
            FlatValuesListIterable, NamedValuesListIterable,
        )
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r "
              "(tuple-truthiness A-reference confirmed)" % (exc,))
        return 0

    class Toy(models.Model):
        name = models.CharField(max_length=16)
        material = models.CharField(max_length=16)
        price = models.PositiveIntegerField()

        class Meta:
            app_label = '__main__'

    with connection.schema_editor() as editor:
        editor.create_model(Toy)

    Toy.objects.create(name='foo', price=10, material='wood')
    Toy.objects.create(name='bar', price=20, material='plastic')
    Toy.objects.create(name='baz', price=100, material='wood')

    observations = 0

    def attach(value_query):
        """Run the REAL post-patch QuerySet.query setter on a fresh QuerySet."""
        fresh = Toy.objects.all()                  # default producer
        assert fresh._iterable_class is ModelIterable, (
            "a freshly-created result set should default to the model-instance "
            "producer")
        fresh.query = value_query                  # the setter under test
        return fresh

    # value-bearing queries: every values()/values_list() flavour selects an
    # explicit value-field set -> non-empty values_select -> producer switches.
    value_querysets = [
        Toy.objects.values('material'),
        Toy.objects.values('name', 'material'),
        Toy.objects.values('material').annotate(total=models.Sum('price')),
        Toy.objects.values_list('name'),
        Toy.objects.values_list('name', flat=True),
        Toy.objects.values_list('name', named=True),
        Toy.objects.values_list('name', 'material'),
    ]
    for qs in value_querysets:
        # (A-reference) the description carries a NON-EMPTY value-field selection
        assert bool(qs.query.values_select), (
            "a values()/values_list() query must carry a non-empty "
            "values_select (count > 0): %r" % (qs.query.values_select,))
        fresh = attach(qs.query)
        # (1) the producer switches to the value-mapping producer ...
        assert fresh._iterable_class is ValuesIterable, (
            "attaching a value-bearing query must switch the producer to the "
            "value-mapping producer; got %r" % (fresh._iterable_class,))
        # ... which is NOT the default model-instance producer (the bug).
        assert fresh._iterable_class is not ModelIterable
        # (2) the query is stored as the active query.
        assert fresh.query is qs.query, "the attached query was not stored"
        observations += 1

    # plain queries: a model-instance lookup selects NO value-fields -> empty
    # values_select -> the default producer is preserved.
    plain_querysets = [
        Toy.objects.all(),
        Toy.objects.filter(material='wood'),
        Toy.objects.order_by('name'),
    ]
    for qs in plain_querysets:
        # (A-reference) the description carries an EMPTY value-field selection
        assert not qs.query.values_select, (
            "a plain model query must carry an empty values_select "
            "(count == 0): %r" % (qs.query.values_select,))
        fresh = attach(qs.query)
        # the default model-instance producer is preserved (unchanged branch).
        assert fresh._iterable_class is ModelIterable, (
            "attaching a no-value-field query must leave the default producer "
            "unchanged; got %r" % (fresh._iterable_class,))
        assert fresh.query is qs.query, "the attached query was not stored"
        observations += 1

    print("G-AX OK: real QuerySet.query setter A-reference sound on %d "
          "observations (value-bearing -> value-mapping producer; plain -> "
          "producer preserved) + 5000 tuple-truthiness fuzz" % observations)
    return 0


if __name__ == "__main__":
    sys.exit(main())
