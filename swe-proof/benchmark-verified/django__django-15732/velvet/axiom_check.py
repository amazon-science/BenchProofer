#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15732.

This bundle declares **no axioms** and **no deep-model references**: the single
operation the gold patch changes (the constraint-name narrowing decision) is
modeled *identically* (`narrowed`/`selectedTarget`), and the three helper
results it consumes (`_constraint_names`, `_unique_constraint_name`, the
`allows_multiple_constraints_on_same_fields` feature flag) are taken as opaque
method inputs — the contract assumes nothing about them. Every refinement leg
is therefore R or I and is handled mechanically by G-CONF
(conformance_check.py); there is no opaque callee whose CONTRACT the proof
assumes.

G-AX consequently has no axiom `ensures` to validate. To keep the gate
meaningful (rather than a silent pass), this script:

  1. asserts the bundle truly declares no axioms (meta.json `axioms == []` and
     `deep_model_references == []`), so a future edit that smuggles in an axiom
     without a soundness check is caught here; and
  2. exercises the three real semantics the mapping.md §2/§3 bijection relies on
     against live Django objects, confirming they are as documented:
       * `allows_multiple_constraints_on_same_fields` — the base default is
         True and the F2P-relevant backend exposes a bool (mapping.md §3,
         `allowMultiple` carrier);
       * the `canonical` carrier — the unquoted unique_together name for
         (table, columns) — is a pure, deterministic function carrying the
         `_uniq` suffix, reconstructed from the **base-commit** machinery
         (`IndexName` + `_create_index_name`) that the gold patch later factors
         into `_unique_constraint_name`; `quote=True` round-trips through
         `quote_name` (the pure-refactor claim, refinement.md §B). (G-AX runs in
         the unpatched base container, so the patch-introduced method is not yet
         present — we exercise the equivalent base expression.)
       * Python list membership / `len` semantics that `narrowed`/`selectedTarget`
         transliterate to (`canonical in names`, `len(names) == 1`) — the
         `List String` ↔ `list[str]` bijection (mapping.md §2).

Imports Django (present in the SWE-Bench instance image) + stdlib only. Exit 0
iff the no-axiom claim holds and the callee/builtin semantics are as documented.
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
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django.db import connection
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.ddl_references import IndexName


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


def check_feature_flag():
    """`allows_multiple_constraints_on_same_fields` ↔ allowMultiple (bool).

    Base default is True; the connected backend exposes a bool. The F2P test is
    @skipUnlessDBFeature-guarded on this flag, i.e. runs with it True."""
    assert BaseDatabaseFeatures.allows_multiple_constraints_on_same_fields is True, (
        "base feature default changed; mapping.md §3 assumed True")
    val = connection.features.allows_multiple_constraints_on_same_fields
    assert isinstance(val, bool), (
        "feature flag must be a bool, got %r" % (type(val),))


def check_unique_constraint_name():
    """The `canonical` carrier (mapping.md §3, refinement.md §B): the unquoted
    unique_together name a column set is assigned.

    G-AX runs in the **base_commit (unpatched)** container, where the gold
    patch's `_unique_constraint_name` method does NOT yet exist — it is the very
    method the patch *introduces* by extracting the inline
    `IndexName(table, columns, "_uniq", create_unique_name)` expression out of
    `_create_unique_sql`. So we reconstruct `canonical` from the **base**
    machinery the patch factors over (`IndexName` + `_create_index_name`), which
    is exactly what `_unique_constraint_name(..., quote=False)` evaluates to
    post-patch. This confirms:
      * the value is a pure, deterministic function of (table, columns)
        carrying the `_uniq` suffix (so `canonical` is well-defined), and
      * the `quote=True` form is `quote_name` applied to the unquoted form (the
        refinement §B pure-refactor claim — the only behaviour-bearing use of
        the extracted helper is site A, via this unquoted `canonical`).
    Because `canonical` is an OPAQUE method input (the spec assumes no property
    of it), this is a provenance/bijection check, not an axiom-soundness check;
    there is no axiom `ensures` to validate (the bundle declares none)."""
    with connection.schema_editor() as editor:
        table = "myapp_pony"
        columns = ["name"]
        # Base-commit reconstruction of `_unique_constraint_name(quote=False)`:
        #   IndexName(table, columns, "_uniq", self._create_index_name)
        unquoted = IndexName(table, columns, "_uniq", editor._create_index_name)
        n1 = str(unquoted)
        n2 = str(IndexName(table, columns, "_uniq", editor._create_index_name))
        assert n1 == n2, "unquoted name must be deterministic, got %r vs %r" % (n1, n2)
        assert "_uniq" in n1, "unique_together name must carry the _uniq suffix: %r" % n1
        # quote=True reconstruction: quote_name applied to the unquoted name.
        def create_unique_name(*args, **kwargs):
            return editor.quote_name(editor._create_index_name(*args, **kwargs))
        q = str(IndexName(table, columns, "_uniq", create_unique_name))
        assert editor.quote_name(n1) == q, (
            "quote=True must equal quote_name(unquoted): %r vs %r" % (q, editor.quote_name(n1)))


def check_list_semantics():
    """The list ops `narrowed`/`selectedTarget` transliterate to (mapping.md §2):
    membership is element equality; a singleton has len 1 and index [0]."""
    names = ["a_uniq", "b_key"]
    assert ("a_uniq" in names) is True
    assert ("zzz" in names) is False
    one = ["only"]
    assert len(one) == 1 and one[0] == "only"
    assert len([]) != 1 and len(["x", "y"]) != 1


def main():
    check_no_axioms()
    check_feature_flag()
    check_unique_constraint_name()
    check_list_semantics()
    print("G-AX OK: bundle declares no axioms / no A-references; the feature "
          "flag, _unique_constraint_name purity/quoting, and list membership/len "
          "semantics match the mapping.md bijection on live Django objects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
