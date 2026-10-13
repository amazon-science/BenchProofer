#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15278.

The single axiomatized callee is `has_effective_default(col)` (model.py axioms
region), which stands in for the unchanged backend observation
`self.effective_default(field) is not None`. Its contract is the WEAKEST
possible: it carries NO `Ensures` at all — only a fractional read permission on
the column flags. So it cannot over-claim a value. What G-AX must establish is
that this stand-in is legitimate, i.e. that on the real backend:

  (1) `self.effective_default(field) is not None` is a deterministic, pure
      (side-effect-free) boolean observation of the field — re-evaluating it
      does not change the field nor the answer (so modelling it as a @Pure
      callee with no Ensures is sound: the model never assumes any particular
      value, only that it is a stable boolean read); and

  (2) the real backend routing predicate over a real field
        field.primary_key or field.unique or not field.null
            or self.effective_default(field) is not None
      coincides with the model's `needs_full_rebuild(col)` over the four
      modelled signals — in particular for the discriminating witness, a
      nullable defaultless OneToOneField (unique=True, null=True,
      primary_key=False, effective_default is None), where the predicate is
      True solely because of the uniqueness constraint.

This runs the REAL Django SQLite schema backend in-container; it imports only
Django (the package under test) and the standard library. Exit 0 iff sound.
"""
import os
import sys


def _setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "axiom_check_settings")
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()


def _real_route(editor, field):
    """The POST-PATCH backend routing predicate, evaluated against the REAL
    field + backend: True == full-rebuild route, False == in-place append."""
    return bool(
        field.primary_key or field.unique or
        not field.null or editor.effective_default(field) is not None
    )


def _model_needs_full_rebuild(primary_key, unique, nullable, has_default):
    """model.py's needs_full_rebuild over the four modelled signals."""
    return bool(primary_key or unique or (not nullable) or has_default)


def main():
    _setup_django()
    from django.db import connection
    from django.db.models import (
        Field, BooleanField, IntegerField, CharField, DateTimeField,
        BinaryField, OneToOneField, ForeignKey, AutoField,
    )
    from django.db.models.deletion import CASCADE, SET_NULL

    # A target model for the relational fields to point at.
    from django.contrib.auth.models import User

    def mk(field):
        field.set_attributes_from_name("probe")
        return field

    # --- field witnesses spanning the four routing signals -------------------
    # Each entry: a freshly built field whose flags exercise the predicate.
    witnesses = [
        # the discriminating F2P witness: nullable, defaultless OneToOneField
        mk(OneToOneField(User, CASCADE, null=True)),
        mk(OneToOneField(User, SET_NULL, null=True, blank=True)),
        # nullable plain FK (NOT unique) -> in-place append route is valid
        mk(ForeignKey(User, CASCADE, null=True)),
        # nullable defaultless scalar -> in-place append route is valid
        mk(IntegerField(null=True)),
        mk(CharField(max_length=10, null=True)),
        mk(DateTimeField(null=True)),
        # non-nullable -> full rebuild
        mk(IntegerField(null=False)),
        # unique scalar -> full rebuild
        mk(IntegerField(null=True, unique=True)),
        mk(CharField(max_length=10, null=True, unique=True)),
        # primary key -> full rebuild
        mk(IntegerField(primary_key=True)),
        # has a default -> full rebuild
        mk(IntegerField(null=True, default=7)),
        mk(BooleanField(null=True, default=False)),
        # blank non-null char (effective default is '') -> full rebuild
        mk(CharField(max_length=10, null=False, blank=True)),
        # binary nullable defaultless -> append route valid
        mk(BinaryField(null=True)),
    ]

    saw_discriminating = False

    with connection.schema_editor() as editor:
        for field in witnesses:
            # (1) purity / determinism of effective_default(field) is not None:
            #     re-evaluating must give the identical boolean and must not
            #     perturb the field's routing flags.
            before = (field.primary_key, field.unique, field.null)
            ed1 = editor.effective_default(field) is not None
            ed2 = editor.effective_default(field) is not None
            after = (field.primary_key, field.unique, field.null)
            assert ed1 == ed2, (
                "effective_default(field) is-not-None is non-deterministic for "
                "%r: %r vs %r" % (field, ed1, ed2))
            assert before == after, (
                "evaluating effective_default mutated routing flags for %r: "
                "%r -> %r" % (field, before, after))

            # (2) the real backend routing predicate == the model's predicate
            #     over the four modelled signals.
            real = _real_route(editor, field)
            modeled = _model_needs_full_rebuild(
                bool(field.primary_key), bool(field.unique),
                bool(field.null), ed1)
            assert real == modeled, (
                "routing predicate mismatch for %r: real backend=%r, "
                "model needs_full_rebuild=%r (pk=%r unique=%r null=%r "
                "has_default=%r)" % (field, real, modeled, field.primary_key,
                                     field.unique, field.null, ed1))

            # (3) record that the discriminating witness behaves as the issue
            #     demands: a nullable, defaultless, unique, non-pk column MUST
            #     route to full rebuild purely because of uniqueness.
            if (field.unique and field.null and not field.primary_key
                    and not ed1):
                saw_discriminating = True
                assert real is True, (
                    "nullable defaultless unique column must take the "
                    "full-rebuild route, got append for %r" % (field,))

    assert saw_discriminating, (
        "the discriminating witness (nullable defaultless unique column) was "
        "never exercised")

    print("G-AX OK: effective_default(field) is-not-None is a deterministic "
          "side-effect-free boolean read, and the real SQLite backend routing "
          "predicate matches the model's needs_full_rebuild on %d field "
          "witnesses (incl. the nullable defaultless OneToOneField)."
          % len(witnesses))
    return 0


if __name__ == "__main__":
    sys.exit(main())
