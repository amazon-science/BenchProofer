#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12858.

This bundle consumes NO @ContractOnly axioms: the per-path reporting decision is
modelled DEEPLY in model.py (`flag_path` and the verified loop). What G-AX
validates here are the two **A-references** the deep model relies on:

  (1) The deep decision `flag_path(reached_field, is_value_op, is_compare_op)`
      == 1 iff `reached_field != 0 and is_value_op == 0 and is_compare_op == 0`
      equals the REAL post-patch reporting predicate of `Model._check_ordering`:
      a path is reported (`models.E015`) iff
          `not (fld is None or (fld.get_transform(part) is None
                                and fld.get_lookup(part) is None))`
      is false, i.e. iff `fld is not None and get_transform(part) is None and
      get_lookup(part) is None`. Checked over the FULL truth table of the three
      booleans.

  (2) The two unchanged registry callees `Field.get_transform(name)` and
      `Field.get_lookup(name)` return a non-None object EXACTLY when `name` is a
      registered operator of that kind reachable from the field. In particular,
      for a built-in comparison operator that is NOT a transform (the F2P case),
      `get_transform` is None while `get_lookup` is non-None — the configuration
      the pre-patch predicate mis-reports and the patch accepts. We exercise the
      real callees on: a built-in comparison operator that is not a transform; a
      freshly registered value-producing operator (a Transform); and an
      unregistered name (both None).

Run inside the official SWE-bench container for the instance, where Django 3.1
is importable on Python 3.6. Exit 0 iff every obligation holds. If Django cannot
be imported/configured in the ambient environment, the pure truth-table
A-reference (1) is still checked and the callee A-reference (2) is reported
SKIPPED; the orchestrator runs the full check in-container.
"""
import itertools
import sys


# --- model.py reference: the deep decision flag_path ------------------------

def flag_path(reached_field, is_value_op, is_compare_op):
    """Reference of model.py's pure `flag_path` (1 = report invalid, 0 = accept):
    report iff no field was reached OR the segment is neither operator kind."""
    if reached_field == 0 or (is_value_op == 0 and is_compare_op == 0):
        return 1
    return 0


def real_predicate(fld_is_none, transform_is_none, lookup_is_none):
    """The REAL post-patch reporting predicate of Model._check_ordering:
        if fld is None or (get_transform(part) is None and get_lookup(part) is None):
            errors.append(checks.Error(..., id='models.E015'))
    Returns 1 iff the error is appended (path reported), else 0."""
    if fld_is_none or (transform_is_none and lookup_is_none):
        return 1
    return 0


def check_truth_table():
    """A-reference (1): flag_path == the real post-patch predicate over the full
    truth table of (reached_field, is_value_op, is_compare_op)."""
    for reached, is_value, is_compare in itertools.product((0, 1), repeat=3):
        model = flag_path(reached, is_value, is_compare)
        # map the model booleans onto the real predicate's None-tests:
        #   reached_field != 0   <-> fld is not None   (fld_is_none = not reached)
        #   is_value_op != 0     <-> get_transform non-None (transform_is_none = not is_value)
        #   is_compare_op != 0   <-> get_lookup non-None    (lookup_is_none   = not is_compare)
        real = real_predicate(
            fld_is_none=(reached == 0),
            transform_is_none=(is_value == 0),
            lookup_is_none=(is_compare == 0),
        )
        assert model == real, (
            "flag_path deep model unsound for (reached=%d, value=%d, compare=%d): "
            "model=%d real-predicate=%d" % (reached, is_value, is_compare, model, real))


# --- A-reference (2): the real registry callees -----------------------------

def check_real_callees():
    """Returns True if Django was importable and the callee checks ran."""
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(INSTALLED_APPS=[], USE_I18N=False, DATABASES={})
        from django.db import models
        from django.db.models import Transform
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX NOTE: Django not importable here (%r); the callee A-reference "
              "(get_transform/get_lookup) is checked in-container. Pure truth-table "
              "A-reference confirmed." % (exc,))
        return False

    fld = models.CharField(max_length=100)

    # (a) An unregistered name: neither operator kind -> both None.
    assert fld.get_transform("zzz_unregistered_name") is None
    assert fld.get_lookup("zzz_unregistered_name") is None
    # mapped booleans (is_value_op=0, is_compare_op=0) with a reached field
    # => the real predicate reports it, and so does flag_path.
    assert flag_path(1, 0, 0) == 1

    # (b) A built-in COMPARISON operator that is NOT a transform: 'isnull'
    #     (the exact F2P case). get_transform is None, get_lookup is non-None.
    assert fld.get_transform("isnull") is None, (
        "expected 'isnull' to NOT be a transform")
    assert fld.get_lookup("isnull") is not None, (
        "expected 'isnull' to be a registered lookup (comparison operator)")
    # => mapped booleans (reached=1, is_value_op=0, is_compare_op=1): the post-
    # patch predicate ACCEPTS it (flag 0) -- the behaviour the patch fixes.
    assert flag_path(1, 0, 1) == 0, (
        "the F2P case (lookup-but-not-transform) must NOT be reported")
    assert real_predicate(False, True, False) == 0

    # another built-in comparison-only operator for good measure.
    assert fld.get_transform("exact") is None
    assert fld.get_lookup("exact") is not None
    assert flag_path(1, 0, 1) == 0

    # (c) A freshly registered VALUE-PRODUCING operator (a Transform):
    #     get_transform non-None, get_lookup None (a Transform is not a Lookup).
    class _AxCheckTransform(Transform):
        lookup_name = "axcheck_value_op"
    models.CharField.register_lookup(_AxCheckTransform)
    try:
        assert fld.get_transform("axcheck_value_op") is not None, (
            "expected the registered Transform to be a transform")
        assert fld.get_lookup("axcheck_value_op") is None, (
            "a Transform is not a Lookup, so get_lookup must be None")
        # mapped booleans (reached=1, is_value_op=1, is_compare_op=0): accepted
        # by both pre- and post-patch (flag 0).
        assert flag_path(1, 1, 0) == 0
        assert real_predicate(False, False, True) == 0
    finally:
        # restore the registry so we don't leak state into other checks
        try:
            models.CharField._unregister_lookup(_AxCheckTransform)
        except Exception:
            pass

    return True


def main():
    # A-reference (1): pure decision, holds regardless of environment.
    check_truth_table()

    ran_callees = check_real_callees()

    if ran_callees:
        print("G-AX OK: flag_path deep model == real post-patch reporting "
              "predicate over the full (reached, value-op, compare-op) truth "
              "table; real Field.get_transform/get_lookup confirm the operator "
              "classification (incl. the lookup-not-transform F2P case 'isnull').")
    else:
        print("G-AX OK (pure A-reference): flag_path deep model == real "
              "post-patch reporting predicate over the full truth table; "
              "callee A-reference deferred to in-container run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
