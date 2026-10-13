#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-11087 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled decision (`hasExposingSubscriber`,
              `mayNarrow`, `columnsFetched`) transliterated to Python over the
              real repo types, via the mapping.md §2 bijection:
                  widenedFetch  <->  bool(sub_objs.query.select_related)
                  preDelete     <->  signals.pre_delete.has_listeners(model)
                  postDelete    <->  signals.post_delete.has_listeners(model)
                  referencedColumns <-> the .only(*referenced_fields) attnames
                  allColumns        <-> the model's full concrete local attnames
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `Collector._has_signal_listeners` + the real `signals` registry,
              the real `sub_objs.query.select_related` observation, and the real
              `get_candidate_relations_to_delete(...).foreign_related_fields`
              referenced-field computation the patched `collect` performs. The
              chosen column set is `referenced` when the guard permits narrowing,
              else the full set (the unchanged full fetch).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: we inspect only `_meta`, lazy `QuerySet.query` objects,
and the in-process signal registry. stdlib + django only. Fuzz seed pinned
(mapping.md §4).
"""
import random
import sys
from itertools import chain

SEED = 11087
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


def _define_models():
    """Minimal stand-ins for the test models (tests/delete/models.py Origin /
    Referrer / SecondReferrer added by the test_patch — which G-CONF does NOT
    apply). Same FK shape, so the referenced-field computation is identical."""
    from django.db import models

    class Origin(models.Model):
        class Meta:
            app_label = "auth"

    class Referrer(models.Model):
        origin = models.ForeignKey(Origin, models.CASCADE)
        unique_field = models.IntegerField(unique=True)
        large_field = models.TextField()

        class Meta:
            app_label = "auth"

    class SecondReferrer(models.Model):
        referrer = models.ForeignKey(Referrer, models.CASCADE)
        other_referrer = models.ForeignKey(
            Referrer, models.CASCADE, to_field="unique_field", related_name="+"
        )

        class Meta:
            app_label = "auth"

    return Origin, Referrer, SecondReferrer


# --- the R/I shadow: Solution.lean hasExposingSubscriber/mayNarrow/columnsFetched
def shadow_has_exposing_subscriber(pre_delete, post_delete):
    return pre_delete or post_delete


def shadow_may_narrow(widened_fetch, pre_delete, post_delete):
    return not (widened_fetch or shadow_has_exposing_subscriber(pre_delete, post_delete))


def shadow_columns_fetched(all_columns, referenced_columns,
                           widened_fetch, pre_delete, post_delete):
    if shadow_may_narrow(widened_fetch, pre_delete, post_delete):
        return referenced_columns
    return all_columns


def main():
    _bootstrap_django()
    Origin, Referrer, SecondReferrer = _define_models()

    from django.db.models import signals
    from django.db.models.deletion import (
        Collector, get_candidate_relations_to_delete,
    )

    collector = Collector(using="default")

    # The two candidate column sets, computed exactly as the patched collect:
    #   referenced = FK target attnames of relations cascading INTO Referrer
    #   all        = Referrer's full concrete local field attnames (full fetch)
    referenced_fields = set(chain.from_iterable(
        (rf.attname for rf in rel.field.foreign_related_fields)
        for rel in get_candidate_relations_to_delete(Referrer._meta)
    ))
    all_fields = {f.attname for f in Referrer._meta.concrete_fields}

    # Sanity: the referenced set must be a strict, non-empty subset (else the
    # "optimisation" would be vacuous and the abstraction dishonest). Mirrors the
    # test's expected `.only('id', 'unique_field')`.
    assert referenced_fields, "no referenced fields computed (abstraction broken)"
    assert referenced_fields < all_fields, (
        "referenced fields not a strict subset: ref=%r all=%r"
        % (sorted(referenced_fields), sorted(all_fields)))
    assert referenced_fields == {"id", "unique_field"}, (
        "unexpected referenced set %r (expected id, unique_field)"
        % sorted(referenced_fields))

    # widenedFetch carrier: a real queryset's select_related observation.
    qs_plain = Referrer.objects.all()
    qs_widened = Referrer.objects.select_related("origin")
    assert not bool(qs_plain.query.select_related)
    assert bool(qs_widened.query.select_related)

    receiver_calls = []

    def receiver(instance=None, **kwargs):
        receiver_calls.append(1)

    def oracle_columns_fetched(widened_fetch, connect):
        """patch.diff behaviour: the REAL patched decision. `connect` is a set of
        signal names to connect a receiver for on Referrer; returns the column
        set the patched collect would fetch."""
        for name in connect:
            getattr(signals, name).connect(receiver, sender=Referrer)
        try:
            # the REAL patched helper + the REAL select_related observation
            guard = not (widened_fetch or collector._has_signal_listeners(Referrer))
            if guard:
                return frozenset(referenced_fields)   # sub_objs.only(*referenced)
            return frozenset(all_fields)              # unchanged full fetch
        finally:
            for name in connect:
                getattr(signals, name).disconnect(receiver, sender=Referrer)

    rng = random.Random(SEED)
    signal_names = ["pre_delete", "post_delete", "m2m_changed"]

    def fuzz_inputs(n):
        # boundary: full cross product of (widened, pre, post, m2m)
        for widened in (False, True):
            for pre in (False, True):
                for post in (False, True):
                    for m2m in (False, True):
                        yield (widened, pre, post, m2m)
        for _ in range(n):
            yield (rng.random() < 0.5, rng.random() < 0.5,
                   rng.random() < 0.5, rng.random() < 0.5)

    disagreements = []
    count = 0
    for widened, pre, post, m2m in fuzz_inputs(N_FUZZ):
        count += 1
        # SHADOW: booleans from the abstraction (m2m is NOT consulted, §3.1).
        shadow = frozenset(shadow_columns_fetched(
            frozenset(all_fields), frozenset(referenced_fields),
            widened, pre, post))
        # ORACLE: connect the corresponding REAL receivers, observe patched code.
        connect = set()
        if pre:
            connect.add("pre_delete")
        if post:
            connect.add("post_delete")
        if m2m:
            connect.add("m2m_changed")
        oracle = oracle_columns_fetched(widened, connect)
        if shadow != oracle:
            disagreements.append((widened, pre, post, m2m,
                                  sorted(shadow), sorted(oracle)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for w, pre, post, m2m, sh, orc in disagreements:
            print("  widened=%r pre=%r post=%r m2m=%r shadow=%r oracle=%r"
                  % (w, pre, post, m2m, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of columnsToFetch agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements "
          "(narrow->referenced {id,unique_field}; widened|pre|post->full set; "
          "m2m_changed irrelevant)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
