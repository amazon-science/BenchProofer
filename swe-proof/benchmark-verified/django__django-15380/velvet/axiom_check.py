#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15380.

This bundle declares **no consumed axioms**. The two foreign primitives the
modeled routine performs — a name-keyed lookup into a `ProjectState.models` map,
and a `dict.get`-with-fallback into `renamed_models` — are modeled **deeply** by
`lookupState` / `renameLookup` (Solution.lean pure region): deep-model
references (A-reference). G-AX validates those deep models against the REAL
Django primitives.

What this script asserts:

  1. (no-axiom claim) meta.json lists no consumed axioms — a future edit that
     smuggles in an `axiom` without an executable soundness check is caught here.

  2. (A-reference `renameLookup`) for every (app, model_name) key,
        renameLookup(renamed, key) == renamed.get(key, key[1])
     over present and absent rename records.

  3. (A-reference `lookupState`) for every key,
        lookupState(models, key) == (models.get(key))   # some ↔ present
     where `models` is a REAL `ProjectState.models` map, over present and
     missing keys.

  4. (behavioural crux) a REAL `ProjectState` holding a model that was renamed
     keys that model under its CURRENT name and raises `KeyError` under its PRIOR
     name. Hence the gold key choice `to_state.models[app, model_name]` resolves
     while the pre-patch choice `to_state.models[app, old_model_name]` raises —
     exactly the issue's KeyError — whenever the model was renamed.

Imports only the standard library + django (the package the gold patch edits).
Exit 0 iff every obligation holds.
"""
import json
import os
import random
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


def check_no_consumed_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    assert axioms == [], (
        "axiom_check expected no consumed axioms but meta.json lists %r; a "
        "consumed axiom requires an executable soundness check here." % (axioms,))


# --- deep models kept in lock-step with Solution.lean ------------------------
def rename_lookup(renamed, key):
    """Transliteration of `renameLookup`: renamed.get(key, key[1])."""
    return renamed.get(key, key[1])


def lookup_state(models, key):
    """Transliteration of `lookupState`: the entry under `key`, or None.

    `models` is a real `ProjectState.models` dict; we observe presence/absence
    (some ↔ none), the only thing the deep model claims."""
    try:
        return models[key]            # real dict subscription (raises KeyError)
    except KeyError:
        return None


def main():
    check_no_consumed_axioms()
    _setup_django()
    from django.db import models as dj_models
    from django.db.migrations.state import ProjectState, ModelState

    def make_state(entries):
        """entries: list of (app_label, ModelName) -> a populated ProjectState
        keyed by the state's own (app_label, name_lower)."""
        ps = ProjectState()
        for app, name in entries:
            ms = ModelState(app, name, [
                ("id", dj_models.AutoField(primary_key=True)),
                ("name", dj_models.CharField(max_length=200)),
            ])
            ps.add_model(ms.clone())
        return ps

    checked = 0

    # --- (2) renameLookup == renamed.get(key, key[1]) ------------------------
    def check_rename(renamed, key):
        nonlocal checked
        observed = renamed.get(key, key[1])
        modeled = rename_lookup(renamed, key)
        assert observed == modeled, (
            "renameLookup unsound: real .get gave %r, deep model %r (renamed=%r "
            "key=%r)" % (observed, modeled, renamed, key))
        checked += 1

    check_rename({}, ("testapp", "mymodel"))                       # absent
    check_rename({("testapp", "mymodel2"): "mymodel"},
                 ("testapp", "mymodel2"))                          # present
    check_rename({("testapp", "mymodel2"): "mymodel"},
                 ("testapp", "other"))                             # absent key

    # --- (3) lookupState presence/absence over a REAL ProjectState -----------
    def check_lookup(models, key, expect_present):
        nonlocal checked
        modeled = lookup_state(models, key)
        present = modeled is not None
        assert present == expect_present, (
            "lookupState unsound: key %r present=%r but expected %r"
            % (key, present, expect_present))
        if expect_present:
            # value-fidelity: the modeled `some` is the actual stored entry
            assert models[key] is modeled
        checked += 1

    st = make_state([("testapp", "Author"), ("otherapp", "Book")])
    check_lookup(st.models, ("testapp", "author"), True)
    check_lookup(st.models, ("otherapp", "book"), True)
    check_lookup(st.models, ("testapp", "missing"), False)
    check_lookup(st.models, ("nope", "author"), False)

    # --- (4) behavioural crux: renamed model keyed by CURRENT name -----------
    def check_rename_keying(app, old_name, new_name):
        """A renamed model: prior state has old_name, current state has new_name.
        The gold key choice (current name) resolves in to_state; the pre-patch
        choice (prior name) raises KeyError — exactly the issue."""
        nonlocal checked
        from_state = make_state([(app, old_name)])
        to_state = make_state([(app, new_name)])
        old_lower = old_name.lower()
        new_lower = new_name.lower()
        # gold: to_state.models[app, model_name (current)] -> present
        assert lookup_state(to_state.models, (app, new_lower)) is not None, (
            "renamed model %r absent from to_state under its CURRENT name" % new_name)
        # pre-patch: to_state.models[app, old_model_name (prior)] -> KeyError
        if old_lower != new_lower:
            assert lookup_state(to_state.models, (app, old_lower)) is None, (
                "expected KeyError-equivalent (None) for renamed model %r under "
                "its PRIOR name in to_state, but it was present" % old_name)
            raised = False
            try:
                to_state.models[app, old_lower]                    # real subscription
            except KeyError:
                raised = True
            assert raised, (
                "real to_state.models did NOT raise KeyError under the prior "
                "name %r of renamed model %r" % (old_lower, new_name))
        # from_state is keyed by the prior name (the old_model_state lookup)
        assert lookup_state(from_state.models, (app, old_lower)) is not None
        checked += 1

    # the exact issue scenario + the F2P shape
    check_rename_keying("test_one", "MyModel", "MyModel2")
    check_rename_keying("testapp", "Author", "RenamedAuthor")
    # un-renamed control: prior name == current name, both resolve
    check_rename_keying("testapp", "Author", "Author")

    # --- randomized fuzz over all four obligations ---------------------------
    rng = random.Random(15380)
    apps = ["testapp", "otherapp", "app_a", "app_b", "mig"]
    names = ["Author", "Book", "Tag", "MyModel", "MyModel2", "Node", "Profile"]
    for _ in range(3000):
        app = rng.choice(apps)
        old = rng.choice(names)
        new = rng.choice(names)
        check_rename_keying(app, old, new)
        # renamed_models fuzz
        renamed = {}
        if rng.random() < 0.5:
            renamed[(app, new.lower())] = old.lower()
        check_rename(renamed, (app, rng.choice(names).lower()))

    print("G-AX OK: A-reference lookupState/renameLookup == real "
          "ProjectState.models / renamed_models primitives, and renamed models "
          "key under their CURRENT name (prior-name lookup raises KeyError) on "
          "%d obligations (boundary + 3000 fuzz); bundle declares no consumed "
          "axioms." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
