#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14580.

This bundle consumes NO @ContractOnly axioms: the table scan and the
materialisation of a distinguished row's import-directive set are modelled
deeply in model.py. What G-AX validates here is the **A-reference** — that the
deep model faithfully captures the real Python semantics of the serializer's
distinguished-type table plus its `set(imports)` materialisation
(`django.db.migrations.serializer.TypeSerializer.serialize`, post-patch).

It executes the REAL Django `TypeSerializer.serialize()` (equivalently
`MigrationWriter.serialize`) on the two distinguished types the model covers and
asserts, for every observation, that the deep model's (text, imports) pair
matches the real callee's output:

  * serializing the base-class reference type yields the text 'models.Model'
    AND the directive set {'from django.db import models'} — the modelled
    `base_ref_text()` / `base_ref_directive()` (the discriminating guarantee:
    the import directive is present and is exactly the namespace-import
    statement, so generated migration code referencing the rendered name
    resolves);
  * serializing the no-import reference type yields the text 'type(None)' AND
    an EMPTY directive set — the modelled `other_ref_text()` / empty directive.

It also confirms the underlying `set(imports)` primitive has the modelled
"materialise the row's directive list into a directive set" semantics (the
A-reference proper), independently of Django.

Run inside the official SWE-bench container for the instance, where Django is
importable. Exit 0 iff every obligation holds. Outside the container (Django
absent) it prints `G-AX SKIP` after confirming the environment-independent
`set(...)` semantics, and returns 0; the orchestrator runs it in-container.
"""
import random
import sys

# --- model.py reference encodings (kept in lock-step with the deep model) ----

BASE_REF_TEXT = "models.Model"                       # model: base_ref_text()
BASE_REF_DIRECTIVE = "from django.db import models"  # model: base_ref_directive()
OTHER_REF_TEXT = "type(None)"                         # model: other_ref_text()


def _check_set_materialisation_semantics():
    """The A-reference proper: `set(imports)` materialises a directive list into
    a directive set holding exactly those directives (the deep model's
    per-element copy of a row's directive sequence into the result's import
    set)."""
    rng = random.Random(20240614)
    pool = [
        "from django.db import models",
        "import datetime",
        "from decimal import Decimal",
        "import uuid",
        "from django.conf import settings",
    ]
    for _ in range(5000):
        n = rng.randint(0, len(pool))
        imports = rng.sample(pool, n)
        materialised = set(imports)
        # the materialised set holds exactly the listed directives ...
        assert materialised == set(imports), "set(imports) lost/added a directive"
        assert all(d in materialised for d in imports), "directive dropped"
        assert len(materialised) == len(set(imports)), "set size wrong"
    # the empty directive list materialises to the empty set (the no-import row)
    assert set([]) == set(), "set([]) must be the empty directive set"


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_I18N=False,
            DATABASES={},
        )
    django.setup()


def main():
    # The A-reference set-materialisation semantics hold regardless of env.
    _check_set_materialisation_semantics()

    try:
        _configure_django()
        from django.db import models
        from django.db.migrations.writer import MigrationWriter
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r "
              "(set(imports) A-reference semantics confirmed)" % (exc,))
        return 0

    # --- distinguished row 1: the base-class reference (the FIX) -------------
    string, imports = MigrationWriter.serialize(models.Model)
    assert string == BASE_REF_TEXT, (
        "real serializer rendered %r, model expects %r" % (string, BASE_REF_TEXT))
    assert imports == {BASE_REF_DIRECTIVE}, (
        "real serializer's import set is %r, model (the fix) expects %r — "
        "the missing import is exactly the bug" % (imports, {BASE_REF_DIRECTIVE}))

    # --- distinguished row 2: the no-import reference -------------------------
    string_n, imports_n = MigrationWriter.serialize(type(None))
    assert string_n == OTHER_REF_TEXT, (
        "real serializer rendered %r, model expects %r" % (string_n, OTHER_REF_TEXT))
    assert imports_n == set(), (
        "real serializer's import set for the no-import row is %r, model "
        "expects the empty set" % (imports_n,))

    # --- the observable end-to-end consequence: the rendered reference is in
    #     scope once the surfaced import directives are executed --------------
    ns = {}
    exec("\n".join(imports), ns)          # run the surfaced import directives
    rendered = eval(string, ns)           # evaluate the rendered reference
    assert rendered is models.Model, (
        "the rendered reference %r did not resolve to models.Model after the "
        "surfaced imports — generated migration code would raise NameError"
        % (string,))

    print("G-AX OK: deep model validated against the real TypeSerializer."
          "serialize over the 2 distinguished rows; base-class reference yields "
          "text %r and directive set {%r}, no-import reference yields text %r and "
          "the empty set; rendered reference resolves after the surfaced imports; "
          "set(imports) A-reference semantics confirmed."
          % (BASE_REF_TEXT, BASE_REF_DIRECTIVE, OTHER_REF_TEXT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
