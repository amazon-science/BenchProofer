#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-13786.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed, DJANGO_SETTINGS configured by the harness). Builds the
Python R/I shadow of the Lean `implementation_combineOptions` skeleton and diffs
it against the REAL patched callee
`django.db.migrations.operations.models.CreateModel.reduce` (its
`AlterModelOptions` branch) over a discrete catalogue of option dicts plus
>=1e5 randomized cases.

Modeled case: the `AlterModelOptions` branch of `CreateModel.reduce` — the
branch the gold patch edits. `reduce` returns `[CreateModel(...)]`; the modeled
observable is that single object's `options` dict.

Bridge (mapping.md): a Lean assoc list `List (String × V)` of distinct-key
entries  <->  a Python `dict`; `managedKeys`  <->
`AlterModelOptions.ALTER_OPTION_KEYS`. Values are instantiated as `str` (the fix
is key-structural and never inspects a value). The Lean result is compared as a
dict (key->value) against the real `reduce`'s `options`.

Exit 0 iff zero disagreements. stdlib + Django only; pinned seed.
"""
import os
import random
import sys

SEED = 20240627
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_combineOptions (post-patch R/I leg) -----

def shadow_combine_options(base, override, managed_keys):
    """Transliteration of problem_spec_/implementation_combineOptions.
    `base`, `override` are dicts; `managed_keys` is a list of strings.
    Returns the combined dict."""
    options = {**base, **override}              # mergeOpts base override
    for key in managed_keys:                    # for key in managedKeys
        if key not in override:                 # ! keyPresent override key
            options.pop(key, None)              # dropKey options key
    return options


# ---- real callee observation ------------------------------------------------

def real_combine_options(base, override):
    """Run the REAL patched `CreateModel.reduce` on a CreateModel(options=base)
    reduced by AlterModelOptions(options=override). Return the resulting
    CreateModel's `options` dict."""
    from django.db.migrations.operations.models import (
        CreateModel, AlterModelOptions,
    )
    create = CreateModel("MyModel", fields=[], options=dict(base))
    alter = AlterModelOptions("MyModel", options=dict(override))
    reduced = create.reduce(alter, "testapp")
    assert isinstance(reduced, list) and len(reduced) == 1, reduced
    new_create = reduced[0]
    assert isinstance(new_create, CreateModel), new_create
    return dict(new_create.options)


def main():
    # Minimal Django settings so the operation classes import/instantiate.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_sbl_conf_settings")
    if "_sbl_conf_settings" not in sys.modules:
        import types
        mod = types.ModuleType("_sbl_conf_settings")
        mod.SECRET_KEY = "x"
        mod.INSTALLED_APPS = []
        mod.DATABASES = {}
        sys.modules["_sbl_conf_settings"] = mod
    import django
    django.setup()

    from django.db.migrations.operations.models import AlterModelOptions
    managed_keys = list(AlterModelOptions.ALTER_OPTION_KEYS)

    # A pool of candidate keys: all managed keys + a few non-managed extras, so
    # the clear-managed / keep-non-managed distinction is exercised.
    non_managed = ["proxy", "app_label", "db_table", "abstract"]
    all_keys = managed_keys + non_managed

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def rand_dict(keys, tag):
        d = {}
        for k in keys:
            if rng.random() < 0.5:
                d[k] = f"{tag}:{k}:{rng.randint(0, 3)}"
        return d

    cases = []  # (base, override)

    # discrete catalogue mirroring the F2P tests + boundaries
    cases.append(({"verbose_name": "My Model"}, {}))                       # clear all
    cases.append(({"verbose_name": "My Model",
                   "verbose_name_plural": "My Model plural"},
                  {"verbose_name": "My Model"}))                            # clear one
    cases.append(({}, {}))                                                  # empty/empty
    cases.append(({"proxy": "1"}, {}))                                      # non-managed survives
    cases.append(({"verbose_name": "a", "proxy": "1"},
                  {"ordering": "b"}))                                       # mixed
    for k in managed_keys:                                                  # each managed key alone
        cases.append(({k: "old"}, {}))
        cases.append(({k: "old"}, {k: "new"}))
    for k in non_managed:                                                   # each non-managed alone
        cases.append(({k: "old"}, {}))

    for _ in range(N_RANDOM):
        base = rand_dict(all_keys, "b")
        override = rand_dict(all_keys, "o")
        cases.append((base, override))

    for base, override in cases:
        got = real_combine_options(base, override)
        exp = shadow_combine_options(base, override, managed_keys)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH base={base} override={override}: "
                      f"real={got!r} shadow={exp!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
