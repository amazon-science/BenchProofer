#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15104 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the REAL field carriers (mapping.md §2): for each field,
              take the UNCHANGED callee `deep_deconstruct`'s kwargs dict and the
              UNCHANGED relational test `field.remote_field and
              field.remote_field.model`, then apply the modeled changed op
              `dropTarget` (`fieldView`): a relational field's kwargs lose the
              `"to"` key (whether or not present); a non-relational field's kwargs
              pass through. The routine NEVER raises (carried as Except.ok). The
              observable is (raised?, per-field resulting kwargs dict).
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `MigrationAutodetector.only_relation_agnostic_fields(fields)` run on
              the same field mapping, observing (raised?, per-field kwargs dict of
              the returned `fields_def` entries).

They must agree on every input — INCLUDING the issue's shape: a custom
`ForeignKey` that hardcodes its `to` and removes it from its own deconstructed
kwargs (a relational field whose kwargs carry no `"to"` binding). On that field
the pre-patch raised `KeyError`; the gold patch and the shadow both complete and
yield the field's remaining bindings. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + the in-image Django only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 15104
N_COLLECTIONS = 9000   # each drives a full only_relation_agnostic_fields pass
                       # (avg ~12 fields ⇒ >10^5 per-field comparisons)


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


def main():
    _setup_django()
    from django.db import models as dj_models
    from django.db.migrations.state import ProjectState
    from django.db.migrations.autodetector import MigrationAutodetector

    # An autodetector instance only to reach the bound `deep_deconstruct` /
    # `only_relation_agnostic_fields` methods; the states are irrelevant here.
    ad = MigrationAutodetector(ProjectState(), ProjectState())

    # --- the issue's shape: a custom FK that hardcodes `to` and removes it -----
    class HardcodedForeignKey(dj_models.ForeignKey):
        def __init__(self, *args, **kwargs):
            kwargs["to"] = "testapp.HardcodedModel"
            super().__init__(*args, **kwargs)

        def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            # remove the hardcoded target from the deconstructed kwargs
            kwargs.pop("to", None)
            return name, path, args, kwargs

    # --- field builders --------------------------------------------------------
    def char_field():
        return dj_models.CharField(max_length=100)

    def int_field():
        return dj_models.IntegerField(default=0)

    def bool_field():
        return dj_models.BooleanField(default=False)

    def fk_field():
        # ordinary relational field: kwargs carry a `to` binding
        return dj_models.ForeignKey("testapp.Author", on_delete=dj_models.CASCADE)

    def o2o_field():
        return dj_models.OneToOneField("testapp.Profile", on_delete=dj_models.CASCADE)

    def m2m_field():
        return dj_models.ManyToManyField("testapp.Tag")

    def hardcoded_fk():
        # the issue: relational, but deconstructed kwargs carry NO `to`
        return HardcodedForeignKey(on_delete=dj_models.CASCADE)

    BUILDERS = [char_field, int_field, bool_field, fk_field, o2o_field,
                m2m_field, hardcoded_fk]

    # --- the R/I shadow: fieldView / dropTarget over the real callees ----------
    def shadow_observe(fields):
        """Solution.lean's viewAll/fieldView transliterated. Uses the UNCHANGED
        callee `deep_deconstruct` and the UNCHANGED relational test, then applies
        the modeled changed op `dropTarget`. Returns (raised, [kwargs dict,...])
        in the same `sorted(fields.items())` order the method uses. Never raises
        (raised is always False)."""
        out = []
        for name, field in sorted(fields.items()):
            decon = ad.deep_deconstruct(field)
            kwargs = dict(decon[2])
            relational = bool(field.remote_field and field.remote_field.model)
            if relational:
                kwargs = {k: v for k, v in kwargs.items() if k != "to"}  # dropTarget
            out.append(kwargs)
        return (False, out)

    # --- the ORACLE: the REAL gold-patched method ------------------------------
    def oracle_observe(fields):
        """Run the real patched only_relation_agnostic_fields; observe
        (raised, [kwargs dict of each returned definition entry])."""
        try:
            defs = ad.only_relation_agnostic_fields(fields)
        except Exception as e:  # noqa: BLE001  -- pre-patch raised KeyError here
            return (True, repr(e))
        return (False, [dict(d[2]) for d in defs])

    rng = random.Random(SEED)
    disagreements = []
    n_fields_compared = 0
    n_collections = 0
    n_hardcoded = 0

    def make_field_dict(names_builders):
        return {nm: b() for nm, b in names_builders}

    def consider(names_builders):
        nonlocal n_fields_compared, n_collections, n_hardcoded
        fields = make_field_dict(names_builders)
        oracle = oracle_observe(fields)
        # rebuild a fresh dict for the shadow so in-place pop on the oracle side
        # cannot affect it (only_relation_agnostic_fields mutates kwargs dicts)
        fields2 = make_field_dict(names_builders)
        shadow = shadow_observe(fields2)
        n_collections += 1
        if any(b is hardcoded_fk for _, b in names_builders):
            n_hardcoded += 1
        if oracle[0] != shadow[0]:
            disagreements.append((sorted(fields.keys()), shadow, oracle))
            return
        if not oracle[0]:
            if oracle[1] != shadow[1]:
                disagreements.append((sorted(fields.keys()), shadow[1], oracle[1]))
            else:
                n_fields_compared += len(oracle[1])

    # --- boundary cases (plan §4.1 step 4): the exact issue shape first --------
    boundary = [
        [("custom", hardcoded_fk)],                                  # the issue
        [("custom", hardcoded_fk), ("name", char_field)],
        [("author", fk_field), ("custom", hardcoded_fk)],
        [("name", char_field)],                                      # no relational
        [("author", fk_field)],                                      # ordinary FK
        [("p", o2o_field)],
        [("tags", m2m_field)],
        [],                                                          # empty
        [("a", char_field), ("b", int_field), ("c", bool_field)],
        [("z", hardcoded_fk), ("a", fk_field), ("m", char_field)],
    ]
    for nb in boundary:
        consider(nb)
        if len(disagreements) >= 8:
            break

    # --- randomized fuzz -------------------------------------------------------
    name_pool = ["a", "b", "c", "d", "e", "f", "author", "tag", "name",
                 "custom", "ref", "owner", "parent", "x", "y", "z"]
    for _ in range(N_COLLECTIONS):
        if len(disagreements) >= 8:
            break
        k = rng.randint(0, 25)
        names = rng.sample(name_pool, min(k, len(name_pool)))
        # if more than the pool, allow duplicates suffixed
        while len(names) < k:
            names.append("f%d" % len(names))
        nb = [(nm, rng.choice(BUILDERS)) for nm in names]
        consider(nb)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d collections:"
              % (len(disagreements), n_collections))
        for keys, sh, orc in disagreements:
            print("  fields=%r\n    shadow=%r\n    oracle=%r"
                  % (keys, ascii(sh), ascii(orc)))
        return 1
    print("G-CONF OK: R/I shadow of fieldDefsIgnoringRelationTargets "
          "(relation-target elided via total dropTarget, never raising) agrees "
          "with patch.diff behaviour through the REAL gold-patched "
          "only_relation_agnostic_fields on %d field collections / %d field "
          "comparisons (incl. %d hardcoded-`to` custom-FK shapes), seed=%d, "
          "0 disagreements." % (n_collections, n_fields_compared, n_hardcoded,
                                SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
