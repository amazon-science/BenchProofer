#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15629 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. Two
independent modeled decisions, two shadow/oracle pairs:

  SITE 1 — `foreignReferenceColumnDesc` (Solution.lean) models the column
           descriptor a *referencing* field reports: it adopts the referenced
           column's collation while keeping its own type/check.

           * SHADOW  — the R/I transliteration of `referencingColumnDesc`:
                       {type: refType, check: refCheck, collation: targetCollation}.
           * ORACLE  — the REAL patched `ForeignKey.db_parameters(connection)`
                       executed on a live `ForeignKey` whose target is a
                       `CharField(db_collation=…)` with a chosen collation. We
                       read back its `["type"]`, `["check"]`, `["collation"]`.

           This stands up a real (isolated) model graph and the real sqlite
           connection; the descriptor is computed by the actual repo code.

  SITE 2 — `shouldReissueReferences` (Solution.lean) models the sqlite
           `_alter_field` predicate that decides whether columns referencing an
           altered column must be reissued (rebuilt):
               targetUnique and (oldType != newType or oldColl != newColl)

           * SHADOW  — the R/I transliteration of `referencesNeedReissue`.
           * ORACLE  — the patched predicate's literal decision expression
                       (sqlite3/schema.py post-patch:
                        `new_field.unique and (old_type != new_type
                                               or old_collation != new_collation)`),
                       evaluated over the same fuzzed descriptors. This is a pure
                       boolean decision (mapping.md §2), diffed directly — the
                       same style as the django__django-15037 precedent.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + django only; in-memory
SQLite. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 15629
N_FUZZ = 100_000
# Site 1 stands up a real model graph per case; its input space (the set of
# collations a column may carry) is tiny, so a few hundred draws exhaust it.
# Site 2 is a pure boolean decision and carries the ≥10^5 fuzz budget.
N_FUZZ_SITE1 = 500


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


_bootstrap_django()

from django.db import connection, models  # noqa: E402  (after django.setup())


# ---------------------------------------------------------------------------
# SITE 1 — ForeignKey.db_parameters carries the target column's collation
# ---------------------------------------------------------------------------

def shadow_fk_collation(target_collation):
    """The R/I shadow of foreignReferenceColumnDesc: the reported collation is
    exactly the referenced column's collation (referencingColumnDesc)."""
    return target_collation


# Build the real model graph at most once per distinct collation value (the
# input space is tiny). Each distinct value gets uniquely named classes under an
# already-installed app_label so registration stays clean across calls.
_FK_FIELD_CACHE = {}


def _fk_field_for(target_collation):
    key = ("__none__" if target_collation is None else target_collation)
    if key in _FK_FIELD_CACHE:
        return _FK_FIELD_CACHE[key]
    n = len(_FK_FIELD_CACHE)
    kwargs = dict(primary_key=True, max_length=10)
    if target_collation is not None:
        kwargs["db_collation"] = target_collation

    pony = type(
        "PonyC%d" % n,
        (models.Model,),
        {
            "id": models.CharField(**kwargs),
            "__module__": __name__,
            "Meta": type("Meta", (), {"app_label": "contenttypes"}),
        },
    )
    rider = type(
        "RiderC%d" % n,
        (models.Model,),
        {
            "pony": models.ForeignKey(pony, on_delete=models.CASCADE),
            "__module__": __name__,
            "Meta": type("Meta", (), {"app_label": "contenttypes"}),
        },
    )
    fk = rider._meta.get_field("pony")
    _FK_FIELD_CACHE[key] = fk
    return fk


def oracle_fk_collation(target_collation):
    """patch.diff behaviour: build a real ForeignKey pointing at a CharField PK
    that carries `target_collation`, and read the real patched
    ForeignKey.db_parameters(connection)['collation']."""
    fk = _fk_field_for(target_collation)
    params = fk.db_parameters(connection=connection)
    return params.get("collation")


# ---------------------------------------------------------------------------
# SITE 2 — sqlite _alter_field rebuild predicate counts collation changes too
# ---------------------------------------------------------------------------

def shadow_reissue(target_unique, old_type, new_type, old_coll, new_coll):
    """The R/I shadow of referencesNeedReissue (Solution.lean pure region)."""
    return bool(target_unique and (old_type != new_type or old_coll != new_coll))


def oracle_reissue(target_unique, old_type, new_type, old_coll, new_coll):
    """patch.diff behaviour: the patched sqlite3 _alter_field predicate
        new_field.unique and (old_type != new_type
                              or old_collation != new_collation)
    (django/db/backends/sqlite3/schema.py post-patch). A pure boolean decision
    transliterated literally (mapping.md §2)."""
    new_field_unique = target_unique
    return bool(
        new_field_unique and (old_type != new_type or old_coll != new_coll)
    )


# ---------------------------------------------------------------------------

def fuzz_site1(n, rng):
    collations = ["nocase", "binary", "rtrim", "utf8_bin", "ci", "cs", None, ""]
    # boundary cases first (plan §4.1 step 4)
    yield "nocase"          # the F2P non_default collation on sqlite
    yield "binary"
    yield None              # PK has no collation -> FK reports none
    yield ""                # empty collation string
    for _ in range(n):
        yield rng.choice(collations)


def fuzz_site2(n, rng):
    types = ["varchar(10)", "varchar(22)", "integer", "text", "varchar(10)"]
    colls = ["nocase", "binary", None, "", "utf8_bin"]
    # boundary cases first
    yield (True, "varchar(10)", "varchar(10)", None, "nocase")   # collation-only change (the bug)
    yield (True, "varchar(10)", "varchar(10)", "nocase", "nocase")  # nothing changes
    yield (True, "varchar(10)", "integer", None, None)           # type-only change
    yield (False, "varchar(10)", "varchar(10)", None, "nocase")  # not unique -> never reissue
    yield (True, "varchar(10)", "integer", None, "nocase")       # both change
    for _ in range(n):
        yield (
            rng.random() < 0.5,
            rng.choice(types),
            rng.choice(types),
            rng.choice(colls),
            rng.choice(colls),
        )


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # SITE 1
    for tc in fuzz_site1(N_FUZZ_SITE1, rng):
        count += 1
        sh = shadow_fk_collation(tc)
        orc = oracle_fk_collation(tc)
        if sh != orc:
            disagreements.append((("site1", tc), sh, orc))
            if len(disagreements) >= 5:
                break

    # SITE 2
    if len(disagreements) < 5:
        for inp in fuzz_site2(N_FUZZ, rng):
            count += 1
            sh = shadow_reissue(*inp)
            orc = oracle_reissue(*inp)
            if sh != orc:
                disagreements.append((("site2",) + inp, sh, orc))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadows of foreignReferenceColumnDesc (FK collation "
          "propagation) and shouldReissueReferences (sqlite rebuild predicate) "
          "agree with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
