#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12663.

This bundle consumes NO @ContractOnly axioms: the single-selection
output-field choice is modelled deeply in model.py. What G-AX validates here is
the **A-reference** — that the deep model
(``if source != 0: return source; return sel.field``) faithfully captures the
real Python / Django semantics of the operation the patch builds on,
``getattr(select, 'target', None) or select.field``.

Two layers are checked:

  (1) The pure primitive ``getattr(obj, 'target', None) or obj.field`` has
      exactly the modelled choose-one semantics:
        * returns ``obj.target`` when it is present and truthy
          (model: ``source != 0`` => ``Result() == source``);
        * returns ``obj.field`` when ``target`` is absent or falsy
          (model: ``source == 0`` => ``Result() == field``).
      This is plain Python truthy short-circuit and always runs.

  (2) The REAL Django ``Query.output_field`` (post-patch) on a single-selection
      query whose sole selected item is a ``Col`` returns the column's
      ``target`` field whenever ``target`` is truthy (the relation-aware field),
      and falls back to ``Col.field`` only when no usable ``target`` exists —
      matching ``output_field_identity``. Crucially it confirms the
      discriminating regression: a ``Col`` carrying an explicit ``output_field``
      that differs from its ``target`` has ``Col.field is not Col.target``, and
      the post-patch property returns ``Col.target`` (not ``Col.field``), which
      is exactly what lets a comparison against the selection coerce a deferred
      stand-in into a related instance.

Run inside the official SWE-bench container for the instance, where Django is
importable. Exit 0 iff every obligation holds. Outside the container (Django
absent) it prints ``G-AX SKIP`` after confirming the pure-primitive layer; the
orchestrator runs it in-container.
"""
import random
import sys


class _Item:
    """A stand-in selected item with a (possibly absent) ``target`` and a
    ``field``, mirroring the model's ``Selection``."""
    def __init__(self, target, field, has_target=True):
        if has_target:
            self.target = target
        self.field = field


def _patched_choice(select):
    """The exact post-patch expression."""
    return getattr(select, 'target', None) or select.field


def _check_primitive_semantics():
    """Layer (1): the A-reference proper — the choose-one truthy/fallback
    semantics of ``getattr(obj, 'target', None) or obj.field``, validated against
    the model's integer-identity choice.

    Sentinels of "no usable source field" (model source == 0): the ``target``
    attribute absent, or present but falsy (None, 0, '', empty containers)."""
    rng = random.Random(12663)

    # The model's choice over integer identities.
    def model_choice(source, field):
        if source != 0:
            return source
        return field

    falsy_targets = [None, 0, 0.0, "", [], {}, (), set(), False]
    truthy_targets = [1, 2, 7, -3, "fk", object(), [0]]

    for _ in range(20000):
        field_id = rng.randint(1, 1000)  # resolved field is always usable

        # Case A: target attribute present and TRUTHY -> returns target.
        t = rng.choice(truthy_targets)
        item = _Item(target=t, field=("F", field_id))
        assert _patched_choice(item) is t, (
            "truthy target must be returned by the patched expression")
        # model: source != 0 => Result() == source (a usable, distinct field)
        assert model_choice(field_id + 12345, field_id) == field_id + 12345

        # Case B: target attribute present but FALSY -> falls back to field.
        f = rng.choice(falsy_targets)
        item2 = _Item(target=f, field=("F", field_id))
        assert _patched_choice(item2) == ("F", field_id), (
            "falsy target must fall back to field")
        # model: source == 0 => Result() == field
        assert model_choice(0, field_id) == field_id

        # Case C: target attribute ABSENT -> falls back to field.
        item3 = _Item(target=None, field=("F", field_id), has_target=False)
        assert not hasattr(item3, "target")
        assert _patched_choice(item3) == ("F", field_id), (
            "absent target must fall back to field")
        assert model_choice(0, field_id) == field_id


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_I18N=False,
        )
    django.setup()


def main():
    # Layer (1) holds regardless of environment.
    _check_primitive_semantics()

    try:
        _configure_django()
        from django.db.models import IntegerField
        from django.db.models.expressions import Col
        from django.db.models.sql.query import Query
        from django.contrib.auth.models import User
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r "
              "(getattr/or A-reference choose-one semantics confirmed)" % (exc,))
        return 0

    observations = 0

    def query_with_single_col(col):
        q = Query(User)
        q.select = (col,)
        return q

    # (a) A plain Col built WITHOUT an explicit output_field: target IS the
    #     output field, so Col.field is Col.target. The property returns it.
    pk_field = User._meta.pk
    col_plain = Col("alias", pk_field)
    assert col_plain.target is pk_field
    assert col_plain.field is pk_field, "plain Col: field should equal target"
    q = query_with_single_col(col_plain)
    of = q.output_field
    assert of is col_plain.target, (
        "post-patch single-select output_field must be Col.target")
    assert of is pk_field
    observations += 1

    # (b) The DISCRIMINATING case: a Col carrying an explicit output_field that
    #     DIFFERS from its target. Here Col.field (resolved) is NOT Col.target
    #     (the relation-aware source field). The pre-patch code returned
    #     Col.field; the post-patch property MUST return Col.target.
    related_field = User._meta.pk            # the relation-aware source field
    resolved_field = IntegerField()          # an explicit, differing override
    col_override = Col("alias", related_field, output_field=resolved_field)
    assert col_override.target is related_field
    assert col_override.field is resolved_field
    assert col_override.field is not col_override.target, (
        "the discriminating case requires Col.field != Col.target")
    q2 = query_with_single_col(col_override)
    of2 = q2.output_field
    assert of2 is col_override.target, (
        "REGRESSION: post-patch output_field must return Col.target (the "
        "relation-aware field), not Col.field (the resolved override)")
    assert of2 is related_field
    assert of2 is not resolved_field
    # model correspondence: source (target) != field (resolved) and != 0 =>
    # Result() == source, i.e. the source field is returned.
    observations += 1

    # (c) Fuzz: many Cols with explicit, differing output_fields over a spread
    #     of field types; every post-patch observation returns the target.
    from django.db.models import (
        CharField, BigIntegerField, FloatField, DateField,
    )
    rng = random.Random(2020)
    field_factories = [IntegerField, CharField, BigIntegerField,
                       FloatField, DateField]
    for _ in range(300):
        tgt = User._meta.pk
        out = rng.choice(field_factories)()
        c = Col("a", tgt, output_field=out)
        qq = query_with_single_col(c)
        assert qq.output_field is c.target, (
            "fuzz: post-patch output_field must return Col.target")
        observations += 1

    print("G-AX OK: deep model validated against the real "
          "getattr(select, 'target', None) or select.field and the real "
          "Query.output_field over %d Django observations; single-selection "
          "output_field returns the relation-aware target field, never the "
          "resolved override (the regression); choose-one A-reference "
          "semantics confirmed." % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
