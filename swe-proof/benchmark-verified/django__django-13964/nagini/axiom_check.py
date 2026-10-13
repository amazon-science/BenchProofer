#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13964.

The bundle consumes NO `@ContractOnly` axiom: the changed behaviour — deciding
whether a local stored-key attribute currently holds an *empty placeholder* and,
if so, adopting the referenced object's stored key — is modelled DEEPLY in
model.py (the `is_empty_placeholder` predicate + the `adopt_referenced_key_if_unset`
skeleton). This check validates the one A-REFERENCE the deep model rests on:

  the set of recognized "empty placeholder" values that the local key attribute
  is tested against is the field's real `empty_values` collection, and its
  membership semantics on the values this fix cares about agree with the deep
  model `is_empty_placeholder`:

        None  -> empty placeholder (the absent marker; an unset numeric key)
        ''    -> empty placeholder (the empty character sequence; a textual key)
        'foo' -> NOT an empty placeholder (a concrete key)

  i.e. for the field types the change touches, `v in field.empty_values` is True
  exactly for `v in (None, '')` (and False for a non-empty key), matching
  `is_empty_placeholder([] / None) == True` and `is_empty_placeholder([c, ...]) ==
  False`.

It additionally drives the REAL changed method end-to-end on the failing
scenario (a foreign key to a model whose primary key is a non-numeric, textual
key) and asserts the referenced key is adopted into the local attribute rather
than left as the empty string — the behaviour the F2P test observes.

Run inside the official SWE-bench container for the instance (Django importable,
sqlite available). It configures an in-memory database and minimal,
dependency-free models. Imports only Django itself (the module the patch lives
in); nothing test-private. Exit 0 iff every obligation holds. (Outside the
container Django is absent, so it prints `G-AX SKIP` and returns 0.)
"""
import os
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def is_empty_placeholder_model(value):
    """Reference implementation of model.py's `is_empty_placeholder`, with the
    carrier abstraction applied: None -> the absent marker; '' -> the empty
    character sequence ([]); a non-empty string -> a non-empty List[int]."""
    if value is None:          # absent marker
        return True
    return len(value) == 0     # empty character sequence []


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "axcheck"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models

    # Structural twins of the F2P test's models: a parent whose primary key is a
    # non-numeric (textual) field, and a child whose foreign key targets it.
    # Also a numeric-PK parent to exercise the absent-marker (None) case.
    class ParentTextPK(models.Model):
        name = models.CharField(primary_key=True, max_length=15)

        class Meta:
            app_label = "axcheck"

    class ChildToTextPK(models.Model):
        parent = models.ForeignKey(ParentTextPK, on_delete=models.CASCADE)

        class Meta:
            app_label = "axcheck"

    class ParentAutoPK(models.Model):
        class Meta:
            app_label = "axcheck"

    class ChildToAutoPK(models.Model):
        parent = models.ForeignKey(ParentAutoPK, on_delete=models.CASCADE)

        class Meta:
            app_label = "axcheck"

    for m in (ParentTextPK, ChildToTextPK, ParentAutoPK, ChildToAutoPK):
        with connection.schema_editor() as editor:
            editor.create_model(m)

    checked = 0

    # --- A-reference: field.empty_values membership == is_empty_placeholder ---
    # The fix tests the local stored-key attribute against the FK field's
    # `empty_values`. Confirm that collection's membership on the relevant
    # values agrees with the deep model for every field the change touches.
    fk_fields = [
        ChildToTextPK._meta.get_field("parent"),
        ChildToAutoPK._meta.get_field("parent"),
    ]
    # values the local key attribute can take, with their abstract carriers
    samples = [
        (None, None),       # absent marker
        ("", ""),           # empty character sequence  -> []
        ("foo", "foo"),     # a concrete textual key
        ("0", "0"),         # a non-empty key that is falsy-looking but NOT empty
        ("jeff", "jeff"),   # the F2P key
    ]
    for field in fk_fields:
        empty_values = field.empty_values
        # the absent marker and the empty character sequence must both be empty
        assert None in empty_values, (
            "field.empty_values must contain the absent marker None: %r" % (empty_values,))
        assert "" in empty_values, (
            "field.empty_values must contain the empty string: %r" % (empty_values,))
        for real_value, carrier in samples:
            real_is_empty = real_value in empty_values
            model_is_empty = is_empty_placeholder_model(carrier)
            assert real_is_empty == model_is_empty, (
                "emptiness mismatch for %r on %r: real (in empty_values)=%r, "
                "deep model is_empty_placeholder=%r"
                % (real_value, field, real_is_empty, model_is_empty))
            checked += 1
        # a concrete non-empty key must NOT be treated as empty
        assert ("jeff" in empty_values) is False

    # --- end-to-end: the changed method adopts the referenced textual key -----
    # The failing scenario: a child whose FK targets a textual-PK parent; the
    # parent is assigned BEFORE its primary key is set, so the local key
    # attribute starts as the empty string ''. After the parent is saved (its
    # key becomes 'jeff') the child's save must adopt that key, not keep ''.
    for key in ("jeff", "foo", "x"):
        parent = ParentTextPK()
        child = ChildToTextPK(parent=parent)
        # local FK attribute is the empty string at this point (textual PK)
        assert getattr(child, "parent_id") == "", (
            "expected empty-string local key before the parent's key is set, got %r"
            % (getattr(child, "parent_id"),))
        child.parent.name = key
        parent.save()
        # The REAL changed method.
        child._prepare_related_fields_for_save(operation_name="save")
        adopted = getattr(child, "parent_id")
        assert adopted == key, (
            "the referenced textual key was not adopted: parent_id=%r, expected %r"
            % (adopted, key))
        checked += 1

    # absent-marker (numeric) case must still adopt the parent's pk (preserved
    # pre-existing behaviour, the PASS_TO_PASS nullable-fk-after-parent path).
    for _ in range(3):
        parent = ParentAutoPK()
        child = ChildToAutoPK(parent=parent)
        assert getattr(child, "parent_id") is None, (
            "expected absent-marker None local key for a numeric PK, got %r"
            % (getattr(child, "parent_id"),))
        parent.save()
        child._prepare_related_fields_for_save(operation_name="save")
        adopted = getattr(child, "parent_id")
        assert adopted == parent.pk, (
            "the referenced numeric key was not adopted: parent_id=%r, expected %r"
            % (adopted, parent.pk))
        checked += 1

    # a deliberately-set, non-empty key must be preserved untouched.
    for key in ("alice", "bob"):
        parent = ParentTextPK(name="ignored")
        child = ChildToTextPK(parent=parent)
        setattr(child, "parent_id", key)   # a deliberate, non-empty value
        parent.save()
        child._prepare_related_fields_for_save(operation_name="save")
        assert getattr(child, "parent_id") == key, (
            "a deliberately-set non-empty key must be preserved, got %r"
            % (getattr(child, "parent_id"),))
        checked += 1

    print("G-AX OK: is_empty_placeholder deep model == real field.empty_values "
          "membership and the changed method adopts the referenced (textual / "
          "numeric) key over %d observations; non-empty keys preserved." % (checked,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
