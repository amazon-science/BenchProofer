#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16595 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `reduceDecision` over a `ReduceInput`
              (`keepLater` iff (incomingIsAlter ∨ incomingIsRemove) ∧ sameField,
              else `deferToInherited`), via the mapping.md bijection (the
              following migration operation ↔ the three observable booleans;
              the reducer's outcome ↔ the `ReduceResult` tag). There are NO
              A-tagged callees in this bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `AlterField.reduce(operation, app_label)` applied at base_commit
              (the real correctness oracle, G-RESOLVE), driven on real migration
              operation objects. Its observable is classified to the same binary
              tag: `keepLater` iff the reducer returns exactly `[operation]`
              (the earlier alteration is dropped and only the following
              operation is kept); every other return value (a multi-element
              list, `[self]`, or a bool) is the unchanged pre-existing dispatch,
              i.e. `deferToInherited`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
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

from django.db import migrations, models
from django.db.migrations.operations.fields import (
    AddField, AlterField, RemoveField, RenameField,
)

SEED = 16595
N_CASES = 120_000
APP_LABEL = "migrations"

# The fixed "earlier" operation under reduction: an AlterField of one field.
_SELF_MODEL = "Book"
_SELF_FIELD = "title"

_MODELS = ["Book", "book", "Author", "Shelf"]
_FIELDS = ["title", "Title", "name", "pages"]


def make_self():
    return AlterField(model_name=_SELF_MODEL, name=_SELF_FIELD,
                      field=models.CharField(max_length=128, null=True))


def make_following(kind, model, field, rng):
    """Materialize a real migration operation of `kind` targeting (model, field)."""
    if kind == "alter":
        ht = rng.choice([None, "help", "other"])
        kwargs = {} if ht is None else {"help_text": ht}
        return AlterField(model_name=model, name=field,
                          field=models.CharField(max_length=128, **kwargs))
    if kind == "remove":
        return RemoveField(model_name=model, name=field)
    if kind == "rename":
        # db_column None so the real RenameField branch (a 2-element list) fires
        # when same-field; this is an unchanged branch -> deferToInherited.
        return RenameField(model_name=model, old_name=field, new_name="renamed")
    if kind == "add":
        return AddField(model_name=model, name=field, field=models.IntegerField())
    if kind == "create":
        return migrations.CreateModel(
            name=model, fields=[(field, models.IntegerField())])
    raise AssertionError(kind)


# --- the R/I shadow: Solution.lean reduceDecision ----------------------------

def shadow_decision(incoming_is_alter, incoming_is_remove, same_field):
    """reduceDecision (Solution.lean): keepLater iff
    (incomingIsAlter ∨ incomingIsRemove) ∧ sameField, else deferToInherited."""
    if (incoming_is_alter or incoming_is_remove) and same_field:
        return "keepLater"
    return "deferToInherited"


# --- the oracle: the real patched AlterField.reduce --------------------------

def oracle_decision(self_op, operation):
    """Classify the REAL patched reduce(operation, app_label) into the binary
    tag. keepLater iff the reducer returns exactly [operation]; anything else
    (a 2-element list, [self], or a bool) is the unchanged dispatch."""
    result = self_op.reduce(operation, APP_LABEL)
    if isinstance(result, list) and len(result) == 1 and result[0] is operation:
        return "keepLater"
    return "deferToInherited"


# --- observable booleans for the shadow, from the real following op ----------

def observe(self_op, operation):
    incoming_is_alter = isinstance(operation, AlterField)
    incoming_is_remove = isinstance(operation, RemoveField)
    # is_same_field_operation: same model (case-insensitive) AND same field name
    # (case-insensitive). Only FieldOperation subclasses carry both
    # model_name_lower and name_lower; non-field operations (CreateModel) are
    # never "same field" (the real reducer only calls is_same_field_operation
    # after an isinstance(operation, (AlterField, RemoveField, RenameField))
    # guard, so it never reaches a non-field operation here).
    same_field = (
        hasattr(operation, "model_name_lower")
        and hasattr(operation, "name_lower")
        and self_op.is_same_field_operation(operation)
    )
    return incoming_is_alter, incoming_is_remove, bool(same_field)


def run_case(self_op, operation, disagreements):
    a, r, s = observe(self_op, operation)
    shadow = shadow_decision(a, r, s)
    oracle = oracle_decision(self_op, operation)
    if shadow != oracle:
        disagreements.append((type(operation).__name__,
                              dict(alter=a, remove=r, same=s), shadow, oracle))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- boundary cases first (plan §4.1 step 4): the F2P scenario -----------
    self_op = make_self()
    boundary = [
        # F2P: a following AlterField on the SAME field -> keepLater (the new
        # behaviour; the earlier alteration is dropped).
        make_following("alter", _SELF_MODEL, _SELF_FIELD, rng),
        # A following RemoveField on the same field -> keepLater (unchanged).
        make_following("remove", _SELF_MODEL, _SELF_FIELD, rng),
        # A following AlterField on a DIFFERENT field -> deferToInherited.
        make_following("alter", _SELF_MODEL, "name", rng),
        make_following("alter", "Author", _SELF_FIELD, rng),
        # A following RenameField same field -> unchanged 2-list branch.
        make_following("rename", _SELF_MODEL, _SELF_FIELD, rng),
        # AddField / CreateModel -> deferToInherited.
        make_following("add", _SELF_MODEL, _SELF_FIELD, rng),
        make_following("create", _SELF_MODEL, _SELF_FIELD, rng),
        # case-insensitive same-field match.
        make_following("alter", "book", "Title", rng),
    ]
    for op in boundary:
        count += 1
        run_case(self_op, op, disagreements)

    # --- randomized fuzz -----------------------------------------------------
    kinds = ["alter", "remove", "rename", "add", "create"]
    for _ in range(N_CASES):
        if len(disagreements) >= 5:
            break
        self_op = make_self()
        kind = rng.choice(kinds)
        model = rng.choice(_MODELS)
        field = rng.choice(_FIELDS)
        op = make_following(kind, model, field, rng)
        count += 1
        run_case(self_op, op, disagreements)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, obs, sh, orc in disagreements:
            print("  following=%s obs=%r shadow=%r oracle=%r"
                  % (name, obs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reduceDecision agrees with patch.diff "
          "AlterField.reduce behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
