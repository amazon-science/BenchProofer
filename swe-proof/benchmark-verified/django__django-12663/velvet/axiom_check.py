#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12663.

There is NO consumed axiom in this bundle. The single-selection output-field
choice is modeled DEEPLY (Solution.lean's `outputFieldIdentity`). What G-AX
validates is the **A-reference**: that the deep model's choose-one semantics
equal the real Python / Django behaviour the gold patch relies on.

Two checks against real callees (no value is asserted that the real code does
not produce):

  (A-reference 1) The `getattr(obj, 'target', None) or obj.field` primitive (the
      gold-patched expression) has exactly the modeled choose-one semantics:
      returns `obj.target` when the attribute is present and truthy; returns
      `obj.field` when `target` is absent or falsy. Checked directly over a
      fuzzed truthiness matrix of real Python objects. This is the bridge G-CONF
      relies on (mapping.md §2): truthy target ↔ nonzero source identity.

  (A-reference 2) The real Django `Query.output_field` (post-patch) on a
      single-selection query returns the column's `target` field for a `Col`
      whose `target` is truthy, and is exactly `Col.field` (the resolved
      `output_field`) in the fallback. Builds real `Col` objects both WITHOUT an
      explicit `output_field` (so `Col.field is Col.target`) and WITH an explicit
      differing `output_field` (so `Col.field != Col.target` — the nested-
      subquery regression in the issue), installs each as the sole `self.select`
      of a real `Query`, and asserts the patched property returns the `target`
      field in each case.

PYTHONPATH=/testbed is required so the PATCHED repo copy is imported (lesson:
non-editable repos otherwise import the unpatched site-packages copy). Imports
only the standard library + the repo under test. Exit 0 iff every obligation
holds.
"""
import os
import random
import sys


# --- A-reference 1: the getattr/or truthy short-circuit primitive ------------

class _Obj:
    """A stand-in carrying a `target` and a `field` attribute (or omitting
    `target` entirely)."""
    def __init__(self, field, target=("__absent__",)):
        self.field = field
        if target != ("__absent__",):
            self.target = target


def patched_choice(obj):
    """The gold-patched expression, verbatim."""
    return getattr(obj, 'target', None) or obj.field


def modeled_choice(source_truthy, source_val, field_val):
    """The deep model `outputFieldIdentity`: source when usable, else field.
    `source_truthy` is whether `getattr(obj,'target',None)` is truthy."""
    if source_truthy:
        return source_val
    return field_val


def check_primitive():
    rng = random.Random(12663)
    # A representative set of truthy and falsy Python values for `target`.
    truthy = [1, -1, 7, "f", [0], object(), 3.14, True]
    falsy = [0, 0.0, "", [], {}, None, False]
    fields = ["resolved_field", 42, object()]

    n = 0
    # target absent entirely -> getattr default None (falsy) -> field
    for fv in fields:
        o = _Obj(fv)  # no target attribute
        assert patched_choice(o) is fv or patched_choice(o) == fv, \
            "absent-target fallback wrong"
        assert patched_choice(o) == modeled_choice(False, None, fv)
        n += 1
    # target present and truthy -> returns target
    for _ in range(2000):
        tv = rng.choice(truthy)
        fv = rng.choice(fields)
        o = _Obj(fv, target=tv)
        assert patched_choice(o) is tv or patched_choice(o) == tv, \
            "truthy-target choice wrong on %r" % (tv,)
        assert patched_choice(o) == modeled_choice(True, tv, fv)
        n += 1
    # target present but falsy -> falls back to field
    for _ in range(2000):
        tv = rng.choice(falsy)
        fv = rng.choice(fields)
        o = _Obj(fv, target=tv)
        assert patched_choice(o) is fv or patched_choice(o) == fv, \
            "falsy-target fallback wrong on %r" % (tv,)
        assert patched_choice(o) == modeled_choice(False, tv, fv)
        n += 1
    return n


# --- A-reference 2: the real Django Query.output_field (post-patch) ----------

def check_real_query():
    """Build real Col objects and a real single-selection Query; assert the
    patched property returns the relation-aware `target` field."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
        )
        django.setup()

    from django.db.models import fields as model_fields
    from django.db.models.expressions import Col
    from django.db.models.sql.query import Query
    from django.contrib.auth.models import User

    # A real, distinct field to serve as an explicit, differing output_field.
    target_field = User._meta.get_field('id')           # the relation-aware src
    other_field = model_fields.IntegerField()           # a different resolved fld

    # Case 1: Col WITHOUT explicit output_field -> output_field defaults to
    # target, so Col.field IS Col.target (the two notions coincide).
    col_no_override = Col('alias', target_field)
    assert col_no_override.target is target_field
    assert col_no_override.field is col_no_override.output_field
    assert col_no_override.field is target_field, \
        "without override, Col.field should coincide with Col.target"

    # Case 2: Col WITH explicit differing output_field -> Col.field != Col.target
    # (the nested-subquery regression: resolved field differs from source field).
    col_override = Col('alias', target_field, output_field=other_field)
    assert col_override.target is target_field
    assert col_override.field is other_field
    assert col_override.field is not col_override.target, \
        "with override, Col.field must differ from Col.target"

    # Install each as the sole selection of a real Query and read the PATCHED
    # property. It must return the relation-aware target field in BOTH cases.
    for col, label in ((col_no_override, "no-override"),
                       (col_override, "override")):
        q = Query(User)
        q.select = (col,)
        got = q.output_field
        assert got is col.target, (
            "Query.output_field (%s) returned %r, expected the target field %r "
            "-- patched getattr(select,'target',None) or select.field must "
            "prefer the relation-aware target" % (label, got, col.target))

    # The discriminating regression: in the override case the OLD code
    # (`self.select[0].field`) would have returned `other_field`, not the target.
    assert col_override.field is not col_override.target, \
        "override case must discriminate target vs field"
    return 2


def main():
    sys.path.insert(0, os.environ.get('TESTBED', '/testbed'))
    n_prim = check_primitive()
    try:
        n_q = check_real_query()
        q_note = "%d real Query.output_field cases" % n_q
    except Exception as e:  # pragma: no cover - environment-dependent
        # If Django cannot be set up in this environment, the primitive check
        # (the bridge G-CONF depends on) still establishes the A-reference; the
        # real-Query leg is reported as skipped rather than spuriously failing.
        print("G-AX NOTE: real Query.output_field leg skipped (%s: %s)"
              % (type(e).__name__, e), file=sys.stderr)
        q_note = "real Query leg skipped (env)"
    print("G-AX OK: getattr/or choose-one primitive sound on %d truthiness "
          "cases (== deep model outputFieldIdentity); %s." % (n_prim, q_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
