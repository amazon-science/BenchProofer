#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16595.

This bundle declares **no axioms** and **no deep-model references**: the single
operation the gold patch changes (whether one field alteration is superseded by
the operation that immediately follows it) is modeled *identically*
(`reduceDecision`), and there is no opaque unchanged callee whose contract the
proof assumes. Every refinement leg is therefore R or I and is handled
mechanically by G-CONF (conformance_check.py).

G-AX consequently has no axiom `ensures` to validate. To keep the gate
meaningful (rather than a silent pass), this script:

  1. asserts the bundle truly declares no axioms (meta.json `axioms == []` and
     `deep_model_references == []`), so a future edit that smuggles in an axiom
     without a soundness check is caught here; and
  2. exercises the two real Django operations the §2 bijection refines against
     live migration-operation objects, confirming their fixed semantics:
       * `isinstance(operation, (AlterField, RemoveField))` — the kind test that
         decides `incomingIsAlter` / `incomingIsRemove`;
       * `self.is_same_field_operation(operation)` — same model (case
         insensitive) AND same field name (case insensitive), the `sameField`
         observable.

Imports Django (present in the SWE-Bench instance image) + stdlib only. Exit 0
iff the no-axiom claim holds and the builtin/callee semantics are as documented.
"""
import json
import os
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django.db import models
from django.db.migrations.operations.fields import (
    AddField, AlterField, RemoveField, RenameField,
)


def check_no_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], (
        "axiom_check expected no axioms but meta.json lists %r; an axiom "
        "requires an executable soundness check here." % (axioms,))
    assert refs == [], (
        "axiom_check expected no deep-model references but meta.json lists "
        "%r; an A-reference requires a == real-callee check here." % (refs,))


def check_kind_dispatch():
    """isinstance(op, (AlterField, RemoveField)) ↔ incomingIsAlter/incomingIsRemove."""
    alter = AlterField("Book", "title", models.CharField(max_length=10))
    remove = RemoveField("Book", "title")
    rename = RenameField("Book", "title", "name")
    add = AddField("Book", "title", models.IntegerField())
    assert isinstance(alter, AlterField) and not isinstance(alter, RemoveField)
    assert isinstance(remove, RemoveField) and not isinstance(remove, AlterField)
    assert not isinstance(rename, AlterField) and not isinstance(rename, RemoveField)
    assert not isinstance(add, AlterField) and not isinstance(add, RemoveField)


def check_same_field_operation():
    """self.is_same_field_operation(op) ↔ sameField: same model + same field,
    both case-insensitive."""
    self_op = AlterField("Book", "title", models.CharField(max_length=10))
    same = AlterField("Book", "title", models.CharField(max_length=20))
    same_ci = AlterField("book", "Title", models.CharField(max_length=20))
    diff_field = AlterField("Book", "name", models.CharField(max_length=20))
    diff_model = AlterField("Author", "title", models.CharField(max_length=20))
    remove_same = RemoveField("Book", "title")
    assert self_op.is_same_field_operation(same) is True
    assert self_op.is_same_field_operation(same_ci) is True
    assert self_op.is_same_field_operation(diff_field) is False
    assert self_op.is_same_field_operation(diff_model) is False
    assert self_op.is_same_field_operation(remove_same) is True


def main():
    check_no_axioms()
    check_kind_dispatch()
    check_same_field_operation()
    print("G-AX OK: bundle declares no axioms / no A-references; the kind "
          "dispatch (isinstance over AlterField/RemoveField) and "
          "is_same_field_operation (case-insensitive same model + field) match "
          "the mapping.md bijection on live migration-operation objects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
