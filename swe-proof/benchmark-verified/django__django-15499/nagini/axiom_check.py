#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15499.

This bundle has NO @ContractOnly axioms: the modelled fold (`reduce_create`)
calls no library/utility callee it does not change — it compares an identity
token, branches on a kind tag, and constructs a new operation by selecting which
facet to carry into which slot (refinement.md §C). There is therefore no axiom
to over-approximate.

What G-AX still validates here is the STRUCTURAL obligation `model.py` pins,
executed against the REAL Django code the gold patch edits: that
`CreateModel.reduce` folds

  * a same-named manager alter into a single `CreateModel` carrying the alter
    step's managers, with fields / options / bases unchanged from the creation
    step (the newly-added behaviour, model.py branch A3 / KIND_ALTER_MANAGERS);
  * a same-named option alter symmetrically (options from the alter step,
    managers unchanged from the creation step — the pre-existing branch A2 /
    KIND_ALTER_OPTIONS);
  * neither when the follow-up step names a DIFFERENT model.

It imports only the standard library plus Django itself (the repo under test —
the very module the gold patch lives in); nothing else. Exit 0 iff every
observation matches the spec encoded in model.py.
"""
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={},
    )
django.setup()

from django.db import migrations, models
from django.db.migrations.operations.models import (
    AlterModelManagers,
    AlterModelOptions,
    CreateModel,
)


def _names(managers):
    """Manager names in order — the observable facet content (the spec's
    identity token for the manager collection)."""
    return [name for name, _ in managers]


def check_manager_fold():
    """A same-named AlterModelManagers folds into one CreateModel carrying the
    alter step's managers; fields / options / bases come from the CreateModel."""
    create = CreateModel(
        "Foo",
        fields=[("name", models.CharField(max_length=10))],
        options={"verbose_name": "foo"},
        bases=(models.Model,),
        managers=[("objects", models.Manager())],
    )
    new_managers = [("objects", models.Manager()), ("things", models.Manager())]
    alter = AlterModelManagers(name="Foo", managers=new_managers)

    result = create.reduce(alter, "testapp")
    assert isinstance(result, list) and len(result) == 1, (
        "manager fold: expected a single folded operation, got %r" % (result,)
    )
    folded = result[0]
    assert isinstance(folded, CreateModel), (
        "manager fold: folded op is not a CreateModel: %r" % (folded,)
    )
    # managers facet carried FROM THE ALTER STEP (the load-bearing change)
    assert _names(folded.managers) == _names(new_managers), (
        "manager fold: folded managers %r != alter-step managers %r"
        % (_names(folded.managers), _names(new_managers))
    )
    # name / fields / options / bases unchanged from the creation step.
    # The name check is CASE-SENSITIVE and load-bearing: the folded op must
    # carry the case-preserved display name self.name ("Foo"), NOT the
    # lower-cased comparison key name_lower ("foo") used only in the guard.
    assert folded.name == create.name, (
        "manager fold: name changed: %r != %r (a fold that installed "
        "operation.name_lower would rename the model to its lowercase key)"
        % (folded.name, create.name)
    )
    assert folded.name == "Foo" and folded.name != "foo", (
        "manager fold: display-name case not preserved: %r" % (folded.name,)
    )
    assert folded.fields == create.fields, "manager fold: fields changed"
    assert folded.options == create.options, "manager fold: options changed"
    assert folded.bases == create.bases, "manager fold: bases changed"


def check_option_fold():
    """A same-named AlterModelOptions folds symmetrically: options from the
    alter step, managers unchanged from the creation step."""
    orig_managers = [("objects", models.Manager())]
    create = CreateModel(
        "Foo",
        fields=[],
        options={},
        bases=(models.Model,),
        managers=orig_managers,
    )
    alter = AlterModelOptions(name="Foo", options={"verbose_name": "Foo!"})
    result = create.reduce(alter, "testapp")
    assert isinstance(result, list) and len(result) == 1, (
        "option fold: expected a single folded operation, got %r" % (result,)
    )
    folded = result[0]
    assert isinstance(folded, CreateModel)
    # case-preserved display name kept (not the lower-cased key)
    assert folded.name == "Foo", (
        "option fold: display name not preserved: %r" % (folded.name,)
    )
    assert folded.options.get("verbose_name") == "Foo!", (
        "option fold: altered option not carried: %r" % (folded.options,)
    )
    # managers facet unchanged from the creation step
    assert _names(folded.managers) == _names(orig_managers), (
        "option fold: managers should come from the creation step, got %r"
        % (_names(folded.managers),)
    )


def check_no_fold_different_name():
    """A manager alter naming a DIFFERENT model does not fold via this branch."""
    create = CreateModel("Foo", fields=[], managers=[("objects", models.Manager())])
    alter = AlterModelManagers(name="Bar", managers=[("things", models.Manager())])
    result = create.reduce(alter, "testapp")
    # reduce returns False / None / [] (anything but a single folded CreateModel
    # carrying Bar's managers). Assert it is NOT the same-name fold.
    if isinstance(result, list) and len(result) == 1 and isinstance(result[0], CreateModel):
        folded = result[0]
        assert _names(folded.managers) != _names(alter.managers), (
            "no-fold: a differently-named manager alter must not install its "
            "managers, but it did: %r" % (_names(folded.managers),)
        )


def main():
    check_manager_fold()
    check_option_fold()
    check_no_fold_different_name()
    print(
        "G-AX OK: real CreateModel.reduce folds a same-named AlterModelManagers "
        "into a single CreateModel carrying the alter step's managers (fields/"
        "options/bases unchanged) and the creation step's CASE-PRESERVED display "
        "name ('Foo', not the lower-cased key 'foo'); option fold symmetric; "
        "differing names do not fold. No @ContractOnly axiom in this bundle."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
