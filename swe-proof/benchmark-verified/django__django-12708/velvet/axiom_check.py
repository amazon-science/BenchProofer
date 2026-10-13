#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12708.

This bundle declares **no axioms** and **no deep-model references**: the single
thing the gold patch changes (the constraint-selection filter kwargs) is modeled
*identically* (`keep c = c.isIndex && !c.isUnique`), and the surrounding
selection performed by the unchanged `_constraint_names` callee is a structural
type refinement (`selected` over the flattened constraint list). Every refinement
leg is therefore R or I and is handled mechanically by G-CONF
(conformance_check.py); there is no opaque callee whose contract the proof
assumes (G-CONF runs the real `_constraint_names`, it is not axiomatized).

G-AX consequently has no axiom `ensures` to validate. To keep the gate
meaningful (rather than a silent pass), this script:

  1. asserts the bundle truly declares no axioms (meta.json `axioms == []` and
     `deep_model_references == []`), so a future edit that smuggles in an axiom
     without a soundness check is caught here; and
  2. exercises the index/unique filter semantics of the real, unchanged
     `BaseDatabaseSchemaEditor._constraint_names` selection loop to confirm it
     matches the mapping.md §2 bijection that G-CONF relies on: a constraint is
     selected under kwargs `index=True, unique=False` iff its infodict reports
     `index == True and unique == False`.

Imports only the standard library + json (+ django, present in-container, to
exercise the real selection loop). Exit 0 iff the no-axiom claim holds and the
filter semantics are as documented.
"""
import contextlib
import json
import os
import sys

# Be robust to a container whose stdout defaults to the ASCII codec: force UTF-8
# so any non-ASCII byte in a diagnostic string can never raise UnicodeEncodeError.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def check_no_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    meta_path = os.path.join(here, "meta.json")
    with open(meta_path) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], (
        "axiom_check expected no axioms but meta.json lists %r; an axiom "
        "requires an executable soundness check here." % (axioms,))
    assert refs == [], (
        "axiom_check expected no deep-model references but meta.json lists "
        "%r; an A-reference requires a == real-callee check here." % (refs,))


def check_filter_semantics():
    """Run the real _constraint_names with the post-patch kwargs over every
    (index, unique) flag combination and confirm the selection matches `keep`."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
        django.setup()
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor
    real = BaseDatabaseSchemaEditor._constraint_names

    class _Introspection:
        def __init__(self, c):
            self._c = c
        def identifier_converter(self, name):
            return name
        def get_constraints(self, cursor, table):
            return self._c

    class _Connection:
        def __init__(self, c):
            self.introspection = _Introspection(c)
        @contextlib.contextmanager
        def cursor(self):
            yield object()

    class _Meta:
        db_table = "t"

    class _Model:
        _meta = _Meta()

    class _Shim:
        def __init__(self, c):
            self.connection = _Connection(c)

    def infodict(ix, uq):
        return {"columns": ["a", "b"], "primary_key": False, "unique": uq,
                "index": ix, "check": False, "foreign_key": None, "type": "idx"}

    for ix in (False, True):
        for uq in (False, True):
            constraints = {"c": infodict(ix, uq)}
            selected = list(real(_Shim(constraints), _Model(),
                                 column_names=None, index=True, unique=False,
                                 exclude=None))
            keep = ix and not uq
            got = ("c" in selected)
            assert got == keep, (
                "filter semantics mismatch for index=%r unique=%r: "
                "_constraint_names selected=%r, keep=%r" % (ix, uq, got, keep))


def main():
    check_no_axioms()
    check_filter_semantics()
    print("G-AX OK: bundle declares no axioms / no A-references; the real "
          "_constraint_names selection under the post-patch kwargs "
          "(index=True, unique=False) matches keep = isIndex AND NOT isUnique "
          "over all flag combinations (mapping.md section 2 bijection).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
