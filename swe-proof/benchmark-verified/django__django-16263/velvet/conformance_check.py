#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16263 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed query shapes and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `needsNesting` / `anyPriorAggregate` / `keptNames` /
              `maskFold`. The A-reference callee `referencedNames` (== real
              `get_refs`) is NOT re-encoded here; the shadow consumes the SAME
              real `get_refs` result the oracle does, so the only thing under
              test is the R/I decision algebra (the A-reference leg lives in
              axiom_check.py / G-AX).

  * ORACLE  — `patch.diff`'s behaviour: a direct transcription of the patched
              `Query.get_aggregation` decision lines (query.py:449-473 and the
              mask construction query.py:498-503 / 534-547), with the reference
              collection done by the **real** patched `Ref.get_refs` /
              `BaseExpression.get_refs` executed in-container.

A query shape is fuzzed as: a set of prior annotations (each: selected?,
aggregate?, window?), a set of added summary annotations (each with a real
Django expression tree whose `get_refs` is computed live), and the four
structural-trigger booleans + the HAVING/QUALIFY flag. The two sides must agree
on (needsNesting, keptNames-as-set) for every shape. Exit 0 iff zero
disagreements.

Runs in-container against /testbed (the gold patch is applied by the harness
before this runs). stdlib + Django only. Seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 16263
N_FUZZ = 100_000
NAME_POOL = ["a", "b", "c", "authors_count", "name_lower", "x1", "y2"]


def _setup_django():
    sys.path.insert(0, "/testbed")
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


# ---------------------------------------------------------------------------
# Real expression trees (so the oracle calls the real, patched get_refs).
# A model tree is ('ref', name) | ('comp', [children]); built into real
# Django expressions exactly as in axiom_check.py.
# ---------------------------------------------------------------------------

def build_real(node, Ref, Value, Func):
    if node[0] == "ref":
        return Ref(node[1], Value(1))
    children = [build_real(c, Ref, Value, Func) for c in node[1]]
    if not children:
        return Value(1)
    # Func: a generic Expression of any arity ≥ 1 (Coalesce demands ≥ 2 and
    # would crash on single-child composites); get_refs unions over children.
    return Func(*children, function="F")


def rand_tree(rng, depth):
    if depth <= 0 or rng.random() < 0.55:
        return ("ref", rng.choice(NAME_POOL))
    k = rng.randint(0, 3)
    return ("comp", [rand_tree(rng, depth - 1) for _ in range(k)])


# ---------------------------------------------------------------------------
# SHADOW — Solution.lean impl region (R/I ops) transliterated.
# `added` is a list of (name, refs_set); `annos` a list of
# (name, selected, is_aggregate, is_window). refs_set is the REAL get_refs
# output (shared with the oracle — the A-reference leg is out of G-CONF scope).
# ---------------------------------------------------------------------------

def shadow(annos, added, group_by_tuple, is_sliced, distinct, combinator,
           having_filter):
    names = [a[0] for a in added]
    name_set = set(names)
    # isExisting names a = a.selected && !(names.contains a.name)
    existing = [a for a in annos if a[1] and a[0] not in name_set]
    # anyPriorAggregate
    prior_agg = any(a[2] or a[3] for a in existing) or having_filter
    nesting = group_by_tuple or is_sliced or prior_agg or distinct or combinator
    # maskFold: each added contributes its own name then its referenced names
    mask = []
    for nm, refs in added:
        mask.append(nm)
        mask.extend(sorted(refs))
    # keptNames nesting distinct annos added:
    #   nesting && distinct  -> added names ++ existing selected names
    #   nesting && !distinct -> maskFold added
    #   !nesting             -> added names
    if nesting:
        kept = (set(names) | {a[0] for a in existing}) if distinct else set(mask)
    else:
        kept = set(names)
    return bool(nesting), kept


# ---------------------------------------------------------------------------
# ORACLE — patch.diff's get_aggregation decision, transcribed from the patched
# source, with reference collection via the REAL get_refs.
# ---------------------------------------------------------------------------

def oracle(annos, added, group_by_tuple, is_sliced, distinct, combinator,
           having_filter):
    names = [a[0] for a in added]
    added_aggregate_names = set(names)
    # existing_annotations = {alias: ann for alias, ann in
    #   self.annotation_select.items() if alias not in added_aggregate_names}
    # (annotation_select = annotations whose alias is in the SELECT mask, i.e.
    #  a[1] == selected.)
    existing_annotations = {a[0]: a for a in annos
                            if a[1] and a[0] not in added_aggregate_names}
    # has_existing_aggregation = any(getattr(ann,"contains_aggregate",True)
    #   or getattr(ann,"contains_over_clause",True) for ann in
    #   existing_annotations.values()) or any(self.where.split_having_qualify()[1:])
    has_existing_aggregation = any(
        a[2] or a[3] for a in existing_annotations.values()
    ) or having_filter
    # if (isinstance(self.group_by, tuple) or self.is_sliced
    #     or has_existing_aggregation or self.distinct or self.combinator):
    nesting = (group_by_tuple or is_sliced or has_existing_aggregation
               or distinct or combinator)
    if nesting:
        # inner_query.set_annotation_mask(self.annotation_select)  -- baseline:
        # every selected annotation (added + existing selected) survives.
        # if not inner_query.distinct:            (query.py:486 post-patch)
        #     ... mask-narrowing:
        #     annotation_mask = set()
        #     for name in added_aggregate_names:
        #         annotation_mask.add(name)
        #         annotation_mask |= inner_query.annotations[name].get_refs()
        #     inner_query.set_annotation_mask(annotation_mask)
        # i.e. under query-level DISTINCT the narrowing is SKIPPED and the
        # baseline annotation_select mask stands.
        if distinct:
            kept = set(names) | set(existing_annotations.keys())
        else:
            annotation_mask = set()
            for nm, refs in added:
                annotation_mask.add(nm)
                annotation_mask |= refs
            kept = annotation_mask
    else:
        # else branch: when existing_annotations, inline + set_annotation_mask(
        # added_aggregate_names); the produced mask is exactly the added names.
        kept = set(names)
    return bool(nesting), kept


def fuzz_shape(rng, Ref, Value, Func):
    # Annotation aliases are dict keys (self.annotation_select / self.annotations
    # are dicts) => UNIQUE per query. The bijection (mapping.md §2) carries that
    # domain constraint: sample alias names without replacement.
    added_pool = ["__count", "total", "avg_x", "s1"]
    n_added = rng.randint(1, min(3, len(added_pool)))
    added_names = rng.sample(added_pool, n_added)
    added = []
    for nm in added_names:
        tree = rand_tree(rng, 3)
        refs = set(build_real(tree, Ref, Value, Func).get_refs())
        added.append((nm, refs))
    # Prior annotations: unique aliases drawn from NAME_POOL, disjoint-or-not
    # from the added names (a prior alias may coincide with an added one, in
    # which case it is excluded by the `not in added_aggregate_names` filter).
    n_annos = rng.randint(0, min(4, len(NAME_POOL)))
    anno_names = rng.sample(NAME_POOL, n_annos)
    annos = [(nm, rng.random() < 0.7, rng.random() < 0.5, rng.random() < 0.25)
             for nm in anno_names]
    flags = tuple(rng.random() < p for p in (0.3, 0.2, 0.2, 0.15, 0.3))
    return annos, added, flags


def main():
    _setup_django()
    from django.db.models.expressions import Ref, Value, Func
    if not hasattr(Ref, "get_refs"):
        print("G-CONF ERROR: real get_refs absent (gold patch not applied?)")
        return 1

    rng = random.Random(SEED)
    disagreements = 0
    for _ in range(N_FUZZ):
        annos, added, flags = fuzz_shape(rng, Ref, Value, Func)
        s = shadow(annos, added, *flags)
        o = oracle(annos, added, *flags)
        if s != o:
            disagreements += 1
            if disagreements <= 5:
                print(f"G-CONF DISAGREE: annos={annos} added={added} "
                      f"flags={flags} shadow={s} oracle={o}")
    if disagreements:
        print(f"G-CONF FAIL: {disagreements}/{N_FUZZ} disagreements (seed={SEED}).")
        return 1
    print(f"G-CONF OK: R/I shadow of countQueryShape agrees with patch.diff "
          f"behaviour on {N_FUZZ} inputs (seed={SEED}), 0 disagreements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
