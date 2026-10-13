#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11740.

This bundle declares **no consumed axioms**. The patch adds, to the caller
`generate_altered_fields`, a *call* to the UNCHANGED method
`MigrationAutodetector._get_dependencies_for_foreign_key(field)`; that method's
result is modeled **deeply** by `relationDeps` (with `baseDep`/`mkDep`) in
Solution.lean's pure region — a **deep-model reference (A-reference)**. G-AX
validates that deep model against the REAL callee.

What this script asserts:

  1. (no-axiom claim) meta.json lists no consumed axioms — a future edit that
     smuggles in an `axiom` without an executable soundness check is caught here.

  2. (A-reference) for every relational-field configuration the bijection
     (mapping.md §2) maps a `RelField` to, the REAL
     `_get_dependencies_for_foreign_key` returns exactly the dependency list
     the deep model `relationDeps` predicts:
        swappable target            -> [("__setting__", setting, None, True), ...]
        non-swappable target        -> [(targetApp, targetObj, None, True), ...]
        + explicit (non-auto) through -> append (throughApp, throughObj, None, True)
        + auto-created/absent through -> no extra dependency
     over boundary fields and randomized app/object/through configurations.

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


# --- the deep model relationDeps (kept in lock-step with Solution.lean) ------
# A RelField is a dict: targetApp, targetObj, through (None | (app, obj)),
# swappable (None | str). relationDeps returns a list of 4-tuples.
def mk_dep(app, name):
    return (app, name, None, True)


def base_dep(rf):
    if rf["swappable"] is not None:
        return mk_dep("__setting__", rf["swappable"])
    return mk_dep(rf["targetApp"], rf["targetObj"])


def relation_deps(rf):
    """Transliteration of Solution.lean `relationDeps`."""
    d = base_dep(rf)
    if rf["through"] is None:
        return [d]
    ta, to_ = rf["through"]
    return [d, mk_dep(ta, to_)]


# --- building REAL relational fields + the matching RelField -----------------

def main():
    check_no_consumed_axioms()
    _setup_django()
    from django.db import models
    from django.db.migrations.state import ProjectState
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.apps import apps as global_apps

    ad = MigrationAutodetector(ProjectState(), ProjectState())

    counter = {"n": 0}

    def fresh(prefix):
        counter["n"] += 1
        return "%s%d" % (prefix, counter["n"])

    def make_field(kind, target_app, target_obj, through_spec, swappable):
        """Build a real relational field on a freshly defined model, plus the
        RelField the bijection assigns it.

        kind: 'fk' | 'o2o' | 'm2m'
        target_app/target_obj: app_label / CamelCase object name of the target
        through_spec: None (no/auto through) | (app, obj) explicit through
        swappable: if True, target the AUTH_USER_MODEL (swappable)
        """
        tname = fresh("Tgt")
        target = type(tname, (models.Model,),
                       {"__module__": __name__,
                        "Meta": type("Meta", (), {"app_label": target_app})})
        # object_name is the class name as given; force it via __name__
        target.__name__ = target_obj
        target._meta.object_name = target_obj
        target._meta.model_name = target_obj.lower()

        if swappable:
            to = swappable_sentinel
        else:
            to = target

        attrs = {"__module__": __name__,
                 "Meta": type("Meta", (), {"app_label": "ownerapp"})}
        if kind == "fk":
            attrs["rel"] = models.ForeignKey(to, null=True, on_delete=models.SET_NULL)
        elif kind == "o2o":
            attrs["rel"] = models.OneToOneField(to, null=True, on_delete=models.SET_NULL)
        elif kind == "m2m":
            if through_spec is None:
                attrs["rel"] = models.ManyToManyField(to)
            else:
                tapp, tobj = through_spec
                # an explicit through model with two FKs
                owner_name = fresh("Owner")
                thr_name = fresh("Thr")
                thr = type(thr_name, (models.Model,),
                           {"__module__": __name__,
                            "left": models.ForeignKey("ownerapp.%s" % owner_name,
                                                      models.CASCADE),
                            "right": models.ForeignKey(to, models.CASCADE),
                            "Meta": type("Meta", (), {"app_label": tapp})})
                thr.__name__ = tobj
                thr._meta.object_name = tobj
                thr._meta.model_name = tobj.lower()
                attrs["rel"] = models.ManyToManyField(to, through=thr)
                attrs["Meta"] = type("Meta", (), {"app_label": "ownerapp"})
                owner = type(owner_name, (models.Model,), attrs)
                return owner._meta.get_field("rel")
        owner = type(fresh("Owner"), (models.Model,), attrs)
        return owner._meta.get_field("rel")

    # the swappable sentinel target (AUTH_USER_MODEL)
    from django.conf import settings
    swappable_sentinel = settings.AUTH_USER_MODEL

    def rel_field_of(field):
        """Compute the RelField (mapping.md §2) for a real field, mirroring the
        bijection — used to predict relationDeps."""
        rf = field.remote_field
        swappable = getattr(field, "swappable_setting", None)
        if swappable is not None:
            target_app = target_obj = None
        else:
            target_app = rf.model._meta.app_label
            target_obj = rf.model._meta.object_name
        through = None
        thr = getattr(rf, "through", None)
        if thr is not None and not thr._meta.auto_created:
            through = (thr._meta.app_label, thr._meta.object_name)
        return {"targetApp": target_app, "targetObj": target_obj,
                "through": through, "swappable": swappable}

    checked = 0

    def check(field):
        nonlocal checked
        observed = [tuple(t) for t in ad._get_dependencies_for_foreign_key(field)]
        rf = rel_field_of(field)
        expected = relation_deps(rf)
        assert observed == expected, (
            "A-reference relationDeps unsound: real "
            "_get_dependencies_for_foreign_key gave %r, deep model says %r "
            "(RelField=%r)" % (observed, expected, rf))
        checked += 1

    # ---- boundary fields -----------------------------------------------------
    check(make_field("fk", "testapp", "Author", None, False))
    check(make_field("o2o", "otherapp", "Profile", None, False))
    check(make_field("fk", "authapp", "User", None, True))   # swappable
    check(make_field("m2m", "tagapp", "Tag", None, False))    # auto through
    check(make_field("m2m", "tagapp", "Tag", ("thrapp", "Membership"), False))  # explicit through
    check(make_field("m2m", "tagapp", "Tag", ("ownerapp", "LocalThrough"), False))  # same-app through

    # ---- randomized fuzz -----------------------------------------------------
    rng = random.Random(11740)
    apps = ["testapp", "otherapp", "authors", "thirdapp", "app2", "ownerapp"]
    objs = ["Author", "Book", "Publisher", "Tag", "Membership", "Profile", "X"]

    for _ in range(2000):
        kind = rng.choice(["fk", "o2o", "m2m"])
        swappable = (kind != "m2m") and rng.random() < 0.2
        tapp = rng.choice(apps)
        tobj = rng.choice(objs)
        through = None
        if kind == "m2m" and rng.random() < 0.5:
            through = (rng.choice(apps), rng.choice(objs))
        check(make_field(kind, tapp, tobj, through, swappable))

    print("G-AX OK: A-reference relationDeps == real "
          "_get_dependencies_for_foreign_key on %d relational fields "
          "(6 boundary + 2000 fuzz); bundle declares no consumed axioms." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
