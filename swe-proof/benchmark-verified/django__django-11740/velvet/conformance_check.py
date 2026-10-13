#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11740 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: the `dependencies = []` init, the referential-branch
              guard (`if isReferential: deps = relationDeps f`), and the deep
              model `relationDeps`/`baseDep`/`mkDep` (here transliterated, NOT
              substituted by an axiom — the differential test exercises the real
              R/I data-flow). Built over the real field-configuration carriers
              via the mapping.md §2 bijection.
  * ORACLE  — `patch.diff`'s behaviour: the dependencies the patched
              `MigrationAutodetector.generate_altered_fields` attaches to the
              `AlterField` operation it emits for the field. The harness applies
              patch.diff at base_commit before this runs, so the live caller
              calls `_get_dependencies_for_foreign_key(new_field)` on the
              referential branch. Observed by driving the REAL autodetector over
              in-memory `ProjectState`s (DB-free, exactly as the F2P test's
              `get_changes`) and reading the resulting operation's `_auto_deps`.

The modeled value depends only on the new field's referential configuration, so
the oracle is exercised directly, DB-free — this bundle has a runnable R/I
shadow (`conf_skip = false`).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 11740
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
        )
    django.setup()


# --- the R/I shadow: Solution.lean impl + relationDeps -----------------------
# A RelField is a dict: targetApp, targetObj, through (None | (app, obj)),
# swappable (None | str).
def mk_dep(app, name):
    return (app, name, None, True)


def base_dep(rf):
    if rf["swappable"] is not None:
        return mk_dep("__setting__", rf["swappable"])
    return mk_dep(rf["targetApp"], rf["targetObj"])


def relation_deps(rf):
    """Transliteration of `relationDeps`."""
    d = base_dep(rf)
    if rf["through"] is None:
        return [d]
    ta, to_ = rf["through"]
    return [d, mk_dep(ta, to_)]


def shadow(is_referential, rf):
    """Transliteration of `alteredFieldDependencies`'s impl region."""
    deps = []
    if is_referential:
        deps = relation_deps(rf)
    return deps


# --- the oracle: drive the patched autodetector, read attached deps ----------
# A scenario specifies the new field's shape; the before state replaces it with
# a plain IntegerField so generate_altered_fields fires an AlterField on it.

def make_oracle():
    from django.db import models
    from django.db.migrations.state import ProjectState, ModelState
    from django.db.migrations.autodetector import MigrationAutodetector

    OWNER_APP = "ownerapp"
    OWNER_OBJ = "Owner"

    def field_state(model_name_app_obj_list, owner_field):
        """Build a ModelState list with the owner model carrying `owner_field`."""
        owner = ModelState(OWNER_APP, OWNER_OBJ,
                           [("id", models.AutoField(primary_key=True)),
                            ("rel", owner_field)])
        return model_name_app_obj_list + [owner]

    def base_state(extra_models):
        owner = ModelState(OWNER_APP, OWNER_OBJ,
                           [("id", models.AutoField(primary_key=True)),
                            ("rel", models.IntegerField(null=True))])
        return extra_models + [owner]

    def get_changes(before, after):
        b = ProjectState()
        a = ProjectState()
        for m in before:
            b.add_model(m.clone())
        for m in after:
            a.add_model(m.clone())
        return MigrationAutodetector(b, a)._detect_changes()

    def alter_auto_deps(changes):
        """The _auto_deps of the AlterField operation on OWNER.rel, or None if no
        AlterField was emitted (non-comparable scenario)."""
        for app, migs in changes.items():
            for mig in migs:
                for op in mig.operations:
                    if type(op).__name__ == "AlterField" and op.name == "rel" \
                            and getattr(op, "model_name", None) == OWNER_OBJ.lower():
                        return [tuple(t) for t in getattr(op, "_auto_deps", [])]
        return None

    def build_after_field(kind, target_app, target_obj, through):
        """Build the new (referential or not) owner field + the supporting target
        / through ModelStates."""
        extra = []
        target_ref = "%s.%s" % (target_app, target_obj)
        extra.append(ModelState(target_app, target_obj,
                                [("id", models.AutoField(primary_key=True))]))
        if kind == "nonref":
            return models.BigIntegerField(null=True), []
        if kind == "fk":
            return (models.ForeignKey(target_ref, models.CASCADE, null=True),
                    extra)
        if kind == "o2o":
            return (models.OneToOneField(target_ref, models.CASCADE, null=True),
                    extra)
        if kind == "m2m":
            if through is None:
                return models.ManyToManyField(target_ref), extra
            thr_app, thr_obj = through
            # explicit through model wiring owner <-> target
            thr = ModelState(thr_app, thr_obj, [
                ("id", models.AutoField(primary_key=True)),
                ("owner", models.ForeignKey("%s.%s" % (OWNER_APP, OWNER_OBJ),
                                            models.CASCADE)),
                ("target", models.ForeignKey(target_ref, models.CASCADE)),
            ])
            extra.append(thr)
            thr_ref = "%s.%s" % (thr_app, thr_obj)
            return models.ManyToManyField(target_ref, through=thr_ref), extra
        raise AssertionError("unknown kind %r" % (kind,))

    def oracle(kind, target_app, target_obj, through):
        owner_field, extra = build_after_field(kind, target_app, target_obj,
                                               through)
        after = field_state(extra, owner_field)
        before = base_state(extra)
        # m2m can't alter from an IntegerField (m2m<->concrete => remove+add),
        # so for m2m use an m2m-to-m2m alteration: before is a plain auto m2m to
        # the SAME target; the change is adding/removing the through.
        if kind == "m2m":
            before_field = models.ManyToManyField("%s.%s" % (target_app,
                                                             target_obj))
            before = field_state(extra, before_field)
        return alter_auto_deps(get_changes(before, after))

    return oracle


# --- mapping a scenario to its RelField (mapping.md §2) ----------------------

def rel_field_of(kind, target_app, target_obj, through):
    if kind == "nonref":
        return None
    # swappable not fuzzed here: AUTH_USER_MODEL needs auth as a real app in the
    # state graph (G-AX covers the swappable callee branch directly).
    return {"targetApp": target_app, "targetObj": target_obj,
            "through": (None if kind != "m2m" else through),
            "swappable": None}


def is_referential(kind):
    return kind != "nonref"


# --- fuzz generation ----------------------------------------------------------

def fuzz_inputs(n, rng):
    apps = ["testapp", "otherapp", "authors", "thirdapp", "app2", "tagapp"]
    objs = ["Author", "Book", "Publisher", "Tag", "Profile", "Node"]

    # boundary cases (plan §4.1 step 4)
    boundary = [
        ("nonref", "testapp", "Author", None),                # the bug's foil
        ("fk", "testapp", "Author", None),                     # the F2P shape
        ("o2o", "testapp", "Profile", None),
        ("m2m", "tagapp", "Tag", None),                        # auto through
        ("m2m", "tagapp", "Tag", ("thrapp", "Membership")),    # explicit through
        ("m2m", "tagapp", "Tag", ("ownerapp", "LocalThrough")),  # same-app through
    ]
    for case in boundary:
        yield case

    for _ in range(n):
        kind = rng.choice(["nonref", "fk", "o2o", "m2m", "m2m"])
        target_app = rng.choice(apps)
        target_obj = rng.choice(objs)
        through = None
        if kind == "m2m" and rng.random() < 0.5:
            through = (rng.choice(apps + ["thrapp", "ownerapp"]),
                       "Thr" + rng.choice(objs))
        yield (kind, target_app, target_obj, through)


def main():
    _setup_django()
    oracle = make_oracle()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for (kind, target_app, target_obj, through) in fuzz_inputs(N_FUZZ, rng):
        orc = oracle(kind, target_app, target_obj, through)
        if orc is None:
            # no AlterField emitted for this scenario (not comparable) — skip
            skipped += 1
            continue
        count += 1
        rf = rel_field_of(kind, target_app, target_obj, through)
        sh = shadow(is_referential(kind), rf)
        # compare as multisets of dependencies (order is not part of the spec /
        # the test compares dependency SETS — assertMigrationDependencies)
        if sorted(map(repr, sh)) != sorted(map(repr, orc)):
            disagreements.append((kind, target_app, target_obj, through, sh,
                                  orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, ta, to_, th, sh, orc in disagreements:
            print("  kind=%r target=(%r,%r) through=%r\n"
                  "    shadow=%r\n    oracle=%r" % (kind, ta, to_, th, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of alteredFieldDependencies agrees with "
          "patch.diff behaviour (real generate_altered_fields _auto_deps) on %d "
          "inputs (seed=%d), 0 disagreements (%d non-AlterField scenarios "
          "skipped)." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
