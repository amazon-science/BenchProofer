#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13406 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`QuerySet.query` setter.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule `shaperAfter`, transliterated to
              Python over the real repo types, via the mapping.md §2 bijection:
                  projectsColumns incoming  <->  bool(value.values_select)
                  Shaper.namedValues        <->  ValuesIterable
                  shaperOld (preserved)     <->  the container's prior
                                                 _iterable_class
              i.e.  shaper_after(prior, incoming) =
                        ValuesIterable if bool(value.values_select) else prior
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `QuerySet.query`
              setter. We construct a real container with a chosen prior
              `_iterable_class`, then run `container.query = value` (the patched
              setter) and read `container._iterable_class`.

They must agree on every input. The incoming carrier `value` is a real query
object obtained by pickling-and-reloading the `.query` of a real queryset built
by `.all()` / `.values(...)` / `.values_list(...)` / `.annotate(...)` — exactly
the pickled-query reload path the issue is about.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. No database rows are touched (we read `.query` lazily and never
evaluate the queryset). stdlib + django only. Fuzz seed pinned (mapping.md §4).
"""
import pickle
import random
import sys

SEED = 13406
N_FUZZ = 100_000


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


# Bootstrap + model definition happen at MODULE level so the model is a
# top-level class whose `qs.query` (which references it) is picklable — the
# pickled-query reload path is the whole point of this check.
_bootstrap_django()

from django.db import models  # noqa: E402  (after django.setup())


# A minimal stand-in for the issue's `Toy` model: a couple of value columns plus
# an aggregatable numeric, so values()/values_list()/annotate() all build a
# non-empty values_select, and .all() builds an empty one. Defined at TRUE module
# top level (not inside a function) so its `__qualname__` is plain `Toy` and the
# pickled `qs.query` — which references the model class by qualified name — can be
# unpickled. The pickled-query reload path is the whole point of this check.
class Toy(models.Model):
    name = models.CharField(max_length=16)
    material = models.CharField(max_length=16)
    price = models.PositiveIntegerField()

    class Meta:
        app_label = "auth"


def main():
    from django.db.models import Sum
    from django.db.models.query import (
        ModelIterable, ValuesIterable, ValuesListIterable,
        FlatValuesListIterable, NamedValuesListIterable,
    )

    # The five prior shaper classes a container may already hold (mapping.md §2
    # Shaper inductive). `shaperOld` ranges over all of them so "the existing
    # shaper is preserved" is tested against an arbitrary prior, not just the
    # default ModelIterable.
    PRIOR_SHAPERS = [
        ModelIterable, ValuesIterable, ValuesListIterable,
        FlatValuesListIterable, NamedValuesListIterable,
    ]

    # The carrier-builders. Each yields (label, builds-a-projection?, queryset).
    # The boolean is the abstraction's `projectsColumns` for that carrier, which
    # we ALSO cross-check against the real value.values_select below.
    def carriers():
        return [
            ("all", False, Toy.objects.all()),
            ("values", True, Toy.objects.values("material")),
            ("values_annotate", True,
             Toy.objects.values("material").annotate(total=Sum("price"))),
            ("values_list", True, Toy.objects.values_list("name")),
            ("values_list_flat", True,
             Toy.objects.values_list("name", flat=True)),
            ("values_list_named", True,
             Toy.objects.values_list("name", named=True)),
        ]

    # Pre-compute the reloaded (pickled-round-tripped) query for each carrier and
    # confirm the abstraction flag matches the REAL value.values_select. This is
    # the mapping.md §2 bijection honesty guard.
    reloaded_queries = []
    for label, projects, qs in carriers():
        reloaded = pickle.loads(pickle.dumps(qs.query))
        real_projects = bool(reloaded.values_select)
        if real_projects != projects:
            print(f"G-CONF FAIL: abstraction flag wrong for carrier {label!r}: "
                  f"bool(values_select)={real_projects}, declared={projects} "
                  f"(values_select={reloaded.values_select!r})")
            return 1
        reloaded_queries.append((label, projects, reloaded))

    # --- the R/I shadow: Solution.lean shaperAfter, transliterated -------------
    # def shaperAfter (incoming) (prior) :=
    #   if projectsColumns incoming then Shaper.namedValues else prior
    def shadow_shaper_after(prior_cls, projects):
        if projects:
            return ValuesIterable          # Shaper.namedValues
        return prior_cls                   # preserved

    # --- the ORACLE: the REAL patched QuerySet.query setter --------------------
    def oracle_shaper_after(prior_cls, reloaded_query):
        """patch.diff behaviour: build a real container with the given prior
        shaper, run the REAL patched setter (`container.query = value`), and read
        back the resulting `_iterable_class`."""
        container = Toy.objects.all()
        container._iterable_class = prior_cls   # the prior shaper (shaperOld)
        container.query = reloaded_query         # <-- the patched setter runs
        return container._iterable_class

    rng = random.Random(SEED)

    disagreements = []
    count = 0
    # Exhaustive boundary sweep: every (prior shaper) x (carrier) combination.
    for prior_cls in PRIOR_SHAPERS:
        for label, projects, rq in reloaded_queries:
            count += 1
            shadow = shadow_shaper_after(prior_cls, projects)
            oracle = oracle_shaper_after(prior_cls, rq)
            if shadow is not oracle:
                disagreements.append((prior_cls.__name__, label,
                                      shadow.__name__, oracle.__name__))

    # Randomized fuzz to ≥N_FUZZ: draw (prior, carrier) combinations by seed.
    while count < N_FUZZ:
        prior_cls = PRIOR_SHAPERS[rng.randrange(len(PRIOR_SHAPERS))]
        label, projects, rq = reloaded_queries[rng.randrange(len(reloaded_queries))]
        count += 1
        shadow = shadow_shaper_after(prior_cls, projects)
        oracle = oracle_shaper_after(prior_cls, rq)
        if shadow is not oracle:
            disagreements.append((prior_cls.__name__, label,
                                  shadow.__name__, oracle.__name__))
            if len(disagreements) >= 10:
                break

    if disagreements:
        print(f"G-CONF FAIL: {len(disagreements)} R/I disagreement(s) over "
              f"{count} inputs (seed={SEED}):")
        for prior, label, sh, orc in disagreements[:10]:
            print(f"  prior={prior} carrier={label} shadow={sh} oracle={orc}")
        return 1

    print(f"G-CONF OK: R/I shadow of assignQuery agrees with patch.diff "
          f"behaviour on {count} inputs (seed={SEED}), 0 disagreements "
          f"(projecting carrier -> ValuesIterable; non-projecting -> prior "
          f"shaper preserved).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
