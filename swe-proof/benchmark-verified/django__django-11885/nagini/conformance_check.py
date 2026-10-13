#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11885 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures/Invariant/Assert) stripped; the
          @Pure helpers `contains` and `distinct_count` copy over as plain
          functions. PSeq is a thin tuple shim (`ToSeq` wraps a list). No
          @ContractOnly callees in this bundle.

BRIDGE  — mapping.md section 2: each fast-removable candidate relation is
          carried as the integer identity of the related table it targets;
          the candidate run is a List[int]. Per configuration the bridge
          walks the real candidate relations of the target model (the
          unchanged candidate enumeration + fast-removability predicate) and
          records one identity per fast-removable candidate, mapping each
          distinct related model to a distinct int. Any consistent labeling
          and any candidate ordering realises the same configuration, so the
          shadow is exercised over many permutations and relabelings of each
          configuration's run — each a distinct Requires-satisfying input
          whose oracle observable is the same real collector run.

ORACLE  — the REAL patched cascade-deletion planner (PYTHONPATH=/testbed,
          gold patch applied by the gate before this script runs):
          django.db.models.deletion.Collector.collect on an instance of a
          freshly-built target model referenced by freshly-built models with
          varying foreign-key multiplicities; the observable is the number
          of bulk fast-removal querysets the plan issues
          (len(collector.fast_deletes)). No query is ever executed, so no
          database tables are needed.

Input domain: the modeled precondition demands only read access to the
candidate run, so every List[int] is Requires-satisfying. Configurations
range over 0..4 referencing models x 1..3 referencing columns each,
including the shapes where several columns of one model target the same
table, plus non-participating (DO_NOTHING) columns that never enter the run.

>= 1e5 Requires-satisfying inputs: ~220 configurations x 500 permuted /
relabelled runs each. Pinned seed: 11885.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import random
import sys

SEED = 11885
N_VARIANTS = 500          # permutations/relabelings per configuration
N_FUZZ_CONFIGS = 200

# ---------------------------------------------------------------------------
# Contract shims: nagini_contracts symbols stripped to executable Python.
# ---------------------------------------------------------------------------


class PSeq:
    """Plain tuple shim for nagini's pure sequence type."""

    def __init__(self, t=()):
        self._t = tuple(t)

    def drop(self, n):
        return PSeq(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq(lst)


# ---------------------------------------------------------------------------
# model.py pure region, copied over as plain functions (@Pure and the
# Ensures ghost lines stripped).
# ---------------------------------------------------------------------------


def contains(s, x):
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


def distinct_count(s):
    if len(s) == 0:
        return 0
    rest = distinct_count(s.drop(1))
    if contains(s.drop(1), s[0]):
        return rest
    return 1 + rest


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------


def combined_fast_delete_count(related_tables):
    count = 0
    i = len(related_tables)
    while i > 0:
        table = related_tables[i - 1]
        # A related table is counted at its FIRST occurrence: count it iff it
        # does not appear later in the run (i.e. in the already-processed
        # suffix). This combines the columns of a table that recurs into one
        # removal.
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count
    # (recursion depth of `contains` is bounded by the run length; runs here
    # stay short, so the default recursion limit suffices)


# ---------------------------------------------------------------------------
# Configuration construction: fresh target + referencing models per config.
# ---------------------------------------------------------------------------


def build_config(idx, fk_counts, do_nothing_extra):
    """Build one configuration: a target model plus one referencing model per
    entry of fk_counts, entry j carrying fk_counts[j] cascading foreign keys
    to the target (all fast-removable by construction: nothing references
    the referencing models). do_nothing_extra adds one referencing model
    whose column opts out of cascade participation entirely."""
    from django.db import models

    label = "confapp%d" % idx

    class Meta:
        app_label = label

    target = type("Target%d" % idx, (models.Model,), {
        "__module__": __name__, "Meta": Meta})

    referencing = []
    for j, k in enumerate(fk_counts):
        attrs = {"__module__": __name__,
                 "Meta": type("Meta", (), {"app_label": label})}
        for f in range(k):
            attrs["fk%d" % f] = models.ForeignKey(
                target, models.CASCADE, related_name="+")
        referencing.append(type("Ref%d_%d" % (idx, j), (models.Model,), attrs))

    if do_nothing_extra:
        attrs = {"__module__": __name__,
                 "Meta": type("Meta", (), {"app_label": label}),
                 "fk0": models.ForeignKey(target, models.DO_NOTHING,
                                          related_name="+")}
        type("RefDN%d" % idx, (models.Model,), attrs)

    return target


def extract_run(collector_cls, target):
    """The bridge: the ordered run of fast-removable candidate relations of
    the target, each mapped to the integer identity of its related table
    (distinct related models -> distinct ints)."""
    from django.db.models.deletion import (get_candidate_relations_to_delete,
                                           DO_NOTHING)
    collector = collector_cls(using="default")
    ids = {}
    run = []
    for related in get_candidate_relations_to_delete(target._meta):
        field = related.field
        if field.remote_field.on_delete == DO_NOTHING:
            continue
        related_model = related.related_model
        if collector.can_fast_delete(related_model, from_field=field):
            run.append(ids.setdefault(related_model, len(ids) + 1))
    return run


def oracle_count(collector_cls, target):
    """The real patched planner: number of bulk fast-removal querysets issued
    when one target instance is collected (no query is executed)."""
    collector = collector_cls(using="default")
    collector.collect([target(pk=1)])
    return len(collector.fast_deletes)


def variants(run, rng, n):
    """n Requires-satisfying inputs realising the same configuration:
    permutations composed with bijective relabelings of the identity space."""
    out = [list(run)]
    ids = sorted(set(run))
    for _ in range(n - 1):
        perm = list(run)
        rng.shuffle(perm)
        # bijective relabeling into a scattered identity space
        fresh = rng.sample(range(-10**6, 10**6), len(ids)) if ids else []
        table = dict(zip(ids, fresh))
        out.append([table[x] for x in perm])
    return out


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[],
        )
        django.setup()
    from django.db.models.deletion import Collector

    rng = random.Random(SEED)

    # boundary configurations: (fk_counts per referencing model, DO_NOTHING extra)
    configs = [
        ([], False),          # no referencing models at all
        ([], True),           # only a non-participating column
        ([1], False),
        ([2], False),         # two columns of ONE model target the table
        ([3], False),
        ([1, 1], False),
        ([1, 2], False),
        ([2, 2], False),
        ([1, 1, 1], False),
        ([3, 2, 1], False),
        ([1, 3], True),
        ([2], True),
        ([1, 1, 1, 1], False),
        ([3, 3], False),
        ([1, 2, 3], True),
    ]
    for _ in range(N_FUZZ_CONFIGS):
        m = rng.randint(0, 4)
        fk_counts = [rng.randint(1, 3) for _ in range(m)]
        configs.append((fk_counts, rng.random() < 0.25))

    checked = 0
    for idx, (fk_counts, dn) in enumerate(configs):
        target = build_config(idx, fk_counts, dn)
        run = extract_run(Collector, target)
        real = oracle_count(Collector, target)
        for inp in variants(run, rng, N_VARIANTS):
            shadow = combined_fast_delete_count(inp)
            if shadow != real:
                print("G-CONF FAIL (seed=%d):" % SEED)
                print("DISAGREEMENT\n"
                      "  config: fk_counts=%r do_nothing_extra=%r\n"
                      "  input run=%r\n  shadow=%r\n  real=%r"
                      % (fk_counts, dn, inp, shadow, real))
                return 1
            checked += 1

    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "cascade-deletion planner's bulk fast-removal count on %d inputs "
          "(%d configurations x %d permuted/relabelled runs, seed=%d), "
          "0 disagreements." % (checked, len(configs), N_VARIANTS, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
