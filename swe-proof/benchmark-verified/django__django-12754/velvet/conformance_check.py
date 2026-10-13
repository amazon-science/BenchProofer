#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12754 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real field-name carriers (mapping.md §2):
              `isMoved` / `movedFold` over the created (derived) model's own field
              names, given the base model's field-name sets BEFORE and AFTER the
              change (each `None` when the base model is absent from that side).
              The observable is the SET of field names the routine sequences (the
              modeled `out`).
  * ORACLE  — `patch.diff`'s behaviour: the field-dependency tuples the REAL,
              gold-patched `MigrationAutodetector.generate_created_models`
              actually appends for the created derived model. The patched lines
              append `(base_app, base_name, removed_base_field, False)` for each
              field name in
                  set(old_base.fields) - set(new_base.fields)
                  intersected with the derived model's own fields.
              We capture them by wrapping `add_operation` and driving the REAL
              autodetector over in-memory `ProjectState`s, exactly as the F2P
              `get_changes` helper does (DB-free).

They must agree on every input: for the created derived model, the SET of
field names the real patched code makes the create depend on (its removal-of-base
deps) equals the shadow's `movedFold` over the derived model's fields. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), stdlib
+ the in-image Django only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 12754
N_FUZZ = 3000   # each input drives a full autodetector pass over real states


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


# --- the R/I shadow: Solution.lean isMoved / movedFold -----------------------
def is_moved(old_base, new_base, n):
    """Transliteration of `isMoved`: qualifies iff base present BOTH sides and
    `n` was a base field before but not after. `None` carriers mean absent."""
    if old_base is None or new_base is None:
        return False
    return (n in old_base) and (n not in new_base)


def moved_fold(old_base, new_base, derived_fields):
    """Transliteration of `movedFold`: the derived field names sequenced, in
    derived-field order (compared as a set, matching the patch's `set`)."""
    return [n for n in derived_fields if is_moved(old_base, new_base, n)]


def main():
    _setup_django()
    from django.db import models as dj_models
    from django.db.migrations.state import ProjectState, ModelState
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.questioner import MigrationQuestioner

    def model_state(app, name, field_names, bases=None):
        fields = [("id", dj_models.AutoField(primary_key=True))]
        for fn in field_names:
            fields.append((fn, dj_models.CharField(max_length=200)))
        kw = {}
        if bases is not None:
            kw["bases"] = bases
        return ModelState(app, name, fields, **kw)

    def derived_state(app, name, field_names, base_label):
        # An inherited (MTI) model: no explicit id; inherits pk from the base.
        fields = [(fn, dj_models.CharField(max_length=200)) for fn in field_names]
        return ModelState(app, name, fields, bases=(base_label,))

    def project_state(model_states):
        ps = ProjectState()
        for ms in model_states:
            ps.add_model(ms.clone())
        return ps

    def run_scenario(before, after, app, derived_name, base_app, base_name):
        """Drive the REAL patched autodetector over the full `_detect_changes`
        path (exactly the F2P `get_changes` flow), capturing the dependency
        tuples appended for the created derived model.

        Returns (oracle_field_set, shadow_field_set) or None if the derived
        model was not detected as a created model with a string base (nothing to
        compare)."""
        b = project_state(before)
        a = project_state(after)
        q = MigrationQuestioner(defaults={"ask_initial": True})

        captured = {}

        class _RecordingAutodetector(MigrationAutodetector):
            def add_operation(self, app_label, operation, dependencies=None,
                              beginning=False):
                if operation.__class__.__name__ == "CreateModel":
                    captured[(app_label, operation.name)] = list(dependencies or [])
                return super().add_operation(app_label, operation, dependencies,
                                             beginning=beginning)

        ad = _RecordingAutodetector(b, a, q)
        # ---- ORACLE: run the REAL patched full detect path -------------------
        ad._detect_changes()

        key = (app, derived_name)
        if key not in captured:
            return None
        deps = captured[key]
        # The patched lines append removal deps as (base_app, base_name, field, False)
        oracle_fields = {
            fn for (ba, bn, fn, flag) in deps
            if fn is not None and flag is False
            and ba == base_app and bn == base_name
        }

        # ---- SHADOW: predict the same field set ------------------------------
        old_bm = ad.from_state.models.get((base_app, base_name))
        new_bm = ad.to_state.models.get((base_app, base_name))
        old_base = set(old_bm.fields) if old_bm is not None else None
        new_base = set(new_bm.fields) if new_bm is not None else None
        derived_ms = ad.to_state.models.get(key)
        derived_fields = list(derived_ms.fields) if derived_ms is not None else []
        shadow_fields = set(moved_fold(old_base, new_base, derived_fields))

        return oracle_fields, shadow_fields

    # --- scenario construction ------------------------------------------------
    def make_scenario(app, base_name, derived_name,
                      base_before_fields, base_after_fields, derived_fields):
        base_label = "%s.%s" % (app, base_name)
        before = [model_state(app, base_name, base_before_fields)]
        after = [
            model_state(app, base_name, base_after_fields),
            derived_state(app, derived_name, derived_fields, base_label),
        ]
        return before, after, app, derived_name, app, base_name

    rng = random.Random(SEED)

    disagreements = []
    count = 0
    skipped = 0

    def consider(scn_args):
        nonlocal count, skipped
        before, after, app, dn, ba, bn = make_scenario(*scn_args)
        try:
            res = run_scenario(before, after, app, dn, ba, bn)
        except Exception as e:  # pragma: no cover
            disagreements.append((scn_args, "EXCEPTION", repr(e)))
            return
        if res is None:
            skipped += 1
            return
        oracle_fields, shadow_fields = res
        count += 1
        if oracle_fields != shadow_fields:
            disagreements.append((scn_args, sorted(shadow_fields),
                                  sorted(oracle_fields)))

    # Domain note (the function's real, valid input space): a concrete derived
    # (multi-table-inheritance) subclass may NOT redeclare a field that still
    # exists on its base — Django model validation rejects that as a field
    # clash ("Local field 'x' in class 'Sub' clashes with field of the same
    # name from base class 'Base'") and the autodetector never reaches this
    # code for such a model. So every scenario must satisfy
    #     derived_fields ∩ base_after_fields = ∅ :
    # a derived field can only be a *removed* base field that moved down (the
    # whole point of the issue), or a brand-new field never on the base. The
    # boundary cases below and the fuzzer both honour this invariant; a config
    # violating it is not in the modeled domain and is skipped.
    def _valid(base_after, derived):
        return not (set(base_after) & set(derived))

    # boundary cases (plan §4.1 step 4) — incl. the exact issue shape.
    # (app, base, derived, base_before, base_after, derived_fields)
    boundary = [
        # the issue: title removed from base, moved onto the subclass
        ("app", "readable", "book", ["title"], [], ["title"]),
        # F2P shape with explicit names
        ("app", "readable", "book", ["title", "name"], ["name"], ["title"]),
        # nothing removed from base -> no field deps (derived has a fresh field;
        # it may NOT reuse the kept base field name 'title' — that would clash)
        ("app", "readable", "book", ["title"], ["title"], ["extra"]),
        # field removed from base but NOT present on the derived model -> none
        ("app", "readable", "book", ["title"], [], ["other"]),
        # multiple moved fields
        ("app", "base", "sub", ["a", "b", "c"], ["c"], ["a", "b"]),
        # removed-from-base field, derived has a different + a matching one
        ("app", "base", "sub", ["a", "b"], [], ["b", "z"]),
        # base loses a field the derived does not redeclare
        ("app", "base", "sub", ["a", "b"], ["a"], ["x", "y"]),
    ]
    for scn in boundary:
        assert _valid(scn[4], scn[5]), "invalid boundary scenario: %r" % (scn,)
        consider(scn)
        if len(disagreements) >= 5:
            break

    # boundary: base ABSENT before the change (created in the same step) -> the
    # `if old_base_model_state and new_base_model_state` guard short-circuits;
    # exercises the Option-`none` leg of `isMoved`/`movedFold`. old_base = None.
    def consider_raw(before, after, app, dn, ba, bn):
        nonlocal count, skipped
        try:
            res = run_scenario(before, after, app, dn, ba, bn)
        except Exception as e:  # pragma: no cover
            disagreements.append(((before, after), "EXCEPTION", repr(e)))
            return
        if res is None:
            skipped += 1
            return
        oracle_fields, shadow_fields = res
        count += 1
        if oracle_fields != shadow_fields:
            disagreements.append((("base-absent-before", app, dn),
                                  sorted(shadow_fields), sorted(oracle_fields)))

    if len(disagreements) < 5:
        base_label = "app.readable"
        before_none = []  # base absent before -> from_state has no 'readable'
        after_none = [
            model_state("app", "readable", ["title"]),
            derived_state("app", "book", ["extra"], base_label),
        ]
        consider_raw(before_none, after_none, "app", "book", "app", "readable")

    # --- randomized fuzz -------------------------------------------------------
    pool = ["title", "name", "slug", "age", "email", "x", "y", "z", "a", "b", "c"]
    apps = ["app", "testapp", "otherapp", "mig"]
    base_names = ["readable", "base", "parent", "thing"]
    derived_names = ["book", "sub", "child", "node"]
    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        app = rng.choice(apps)
        bn = rng.choice(base_names)
        dn = rng.choice(derived_names)
        if dn == bn:
            continue
        k = rng.randint(0, len(pool))
        base_before = rng.sample(pool, k)
        # base_after keeps a random subset of base_before (some removed)
        base_after = [f for f in base_before if rng.random() < 0.5]
        # derived fields are drawn ONLY from the valid domain (see above):
        #   removed base fields (moved down)  +  fresh names never on the base.
        # This guarantees derived ∩ base_after = ∅ (a valid Django MTI model)
        # and heavily exercises the moved-field path.
        removed = [f for f in base_before if f not in base_after]
        fresh = [f for f in pool if f not in base_before]
        candidates = removed + fresh
        dk = rng.randint(0, len(candidates))
        derived = rng.sample(candidates, dk)
        assert _valid(base_after, derived)
        consider((app, bn, dn, base_before, base_after, derived))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for scn, sh, orc in disagreements:
            print("  scenario=%r\n    shadow=%r\n    oracle=%r" % (scn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of movedBaseFields agrees with patch.diff "
          "behaviour (field-removal dependencies the real patched "
          "generate_created_models appends for the created derived model) on "
          "%d inputs (seed=%d), 0 disagreements (%d no-create scenarios "
          "skipped)." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
