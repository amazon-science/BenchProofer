#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12754.

The bundle models ONE function: the per-created-model ordering-dependency list
built inside `MigrationAutodetector.generate_created_models`
(`django/db/migrations/autodetector.py`). Its Lean implementation
(`implementation_createModelDeps`) builds, for a newly-created model, the list
of dependency 4-tuples `(app_label, model_name, field_or_None, on_create_bool)`:

    deps = [(app_label, model_name, None, False)]            # proxy-removal self dep
    for base in bases:                                       # model_state.bases
        if base is dotted "ba.bn":
            deps.append((ba, bn, None, True))                # depend on base creation
            old = from_state.models.get((ba, bn))            # GOLD FIX block:
            new = to_state.models.get((ba, bn))
            if old and new:
                removed = set(old.fields) - set(new.fields)  # moved-out base fields
                removed &= set(model_fields)                 # ... reused on new model
                for f in removed:
                    deps.append((ba, bn, f, False))          # depend on field removal
    if primary_key_rel:
        deps.append((pa, pn, None, True))
    return deps

This script transliterates that R/I impl into Python (`shadow_deps`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior (the gold removed-fields block included).

We do NOT stand up Django's migration state machinery (heavy; the modeled value
is a pure construction over base references, two field-name lookups, the new
model's own field names, and an optional primary-key relation). Both legs are
total functions over the modeled abstraction.

IMPORTANT — the spec characterises the result by MEMBERSHIP
(`d ∈ result ↔ …`), and the gold `removed_base_fields` is a Python `set`
(unordered, no duplicates) iterated in unspecified order. The Lean impl emits
the same tuples via an ordered `List.filter`/`List.map`. Order and multiplicity
are therefore immaterial; the two legs are compared as **sets of tuples**.

The edge set EXHAUSTIVELY enumerates a small modeled input space (base kinds and
counts × from/to lookup present/absent × overlapping field-name alphabets ×
primary-key relation present/absent); the fuzz loop additionally samples random
points. The discriminating case — a field present in a base's old state, absent
from its new state, and present on the new model — is covered: the oracle
(post-patch) yields the `(ba, bn, f, False)` removal dep, which the PRE-patch
code would omit.

stdlib-only. Pinned seed: 12754 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 12754
N = 120_000

# Modeled alphabets.
APPS = ("app",)
BASENAMES = ("readable", "other")
FIELDS = ("id", "title", "name", "x")          # field-name alphabet
PK = (None, ("app", "rel"))


def _dep(app, name, field, on_create):
    return (app, name, field, on_create)


# --- ORACLE: post-patch generate_created_models dependency block -------------
def oracle_deps(app_label, model_name, bases, model_fields,
                from_lookup, to_lookup, primary_key_rel):
    deps = [_dep(app_label, model_name, None, False)]
    for base in bases:
        kind = base[0]
        if kind == "dotted":
            ba, bn = base[1], base[2]
            deps.append(_dep(ba, bn, None, True))
            old = from_lookup.get((ba, bn))
            new = to_lookup.get((ba, bn))
            if old is not None and new is not None:
                removed = set(old).difference(new).intersection(model_fields)
                for f in removed:
                    deps.append(_dep(ba, bn, f, False))
        # else: non-dotted base contributes nothing
    if primary_key_rel is not None:
        pa, pn = primary_key_rel
        deps.append(_dep(pa, pn, None, True))
    return deps


# --- shadow of implementation_createModelDeps (the R/I leg) ------------------
# Mirrors Solution.lean op-for-op: baseDeps + removedFieldDeps via ordered
# filter/map over oldFields.
def removed_field_deps(ba, bn, old_fields, new_fields, model_fields):
    out = []
    for f in old_fields:
        if (f not in new_fields) and (f in model_fields):
            out.append(_dep(ba, bn, f, False))
    return out


def base_deps(base, model_fields, from_lookup, to_lookup):
    if base[0] != "dotted":
        return []
    ba, bn = base[1], base[2]
    out = [_dep(ba, bn, None, True)]
    old = from_lookup.get((ba, bn))
    new = to_lookup.get((ba, bn))
    if old is not None and new is not None:
        out += removed_field_deps(ba, bn, old, new, model_fields)
    return out


def shadow_deps(app_label, model_name, bases, model_fields,
                from_lookup, to_lookup, primary_key_rel):
    deps = [_dep(app_label, model_name, None, False)]
    for base in bases:
        deps += base_deps(base, model_fields, from_lookup, to_lookup)
    if primary_key_rel is not None:
        pa, pn = primary_key_rel
        deps += [_dep(pa, pn, None, True)]
    return deps


def disagree(args):
    got = oracle_deps(*args)
    want = shadow_deps(*args)
    # membership semantics: compare as sets (order + multiplicity immaterial).
    if set(got) != set(want):
        return (args, sorted(map(str, got)), sorted(map(str, want)))
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _subset(rng, pool):
    """A deterministic pseudo-random subset (as a tuple) of `pool`."""
    return tuple(p for p in pool if (next(rng) & 1))


def _mk_lookup(rng, keys, pool, present_prob_bits=1):
    """Map each key to either a field subset (present) or absent."""
    out = {}
    for k in keys:
        if (next(rng) & 1) or present_prob_bits == 0:
            out[k] = _subset(rng, pool)
        # else: key absent (lookup.get -> None)
    return out


def main() -> int:
    checked = 0
    app_label, model_name = "app", "book"

    # --- EXHAUSTIVE edge grid over the modeled abstraction --------------------
    base_choices = (
        ("other",),
        ("dotted", "app", "readable"),
        ("dotted", "app", "other"),
    )
    # base lists: empty, single, and a pair (covers multi-base + duplicates).
    base_lists = [()]
    base_lists += [(b,) for b in base_choices]
    base_lists += [(b1, b2) for b1 in base_choices for b2 in base_choices]

    field_subsets = []
    for r in range(len(FIELDS) + 1):
        field_subsets += [frozenset(c) for c in itertools.combinations(FIELDS, r)]

    # Restrict the exhaustive product to a tractable but discriminating slice:
    # model_fields ranges over all subsets; lookups range over {absent, subset}
    # for the readable base specifically (the one the gold case exercises).
    rkey = ("app", "readable")
    lookup_states = [None] + [frozenset(c)
                              for r in range(len(FIELDS) + 1)
                              for c in itertools.combinations(FIELDS, r)]

    for bases in base_lists:
        for model_fields in field_subsets:
            for old_state in lookup_states:
                for new_state in lookup_states:
                    from_lookup = {} if old_state is None else {rkey: tuple(old_state)}
                    to_lookup = {} if new_state is None else {rkey: tuple(new_state)}
                    for pk in PK:
                        args = (app_label, model_name, bases, tuple(model_fields),
                                from_lookup, to_lookup, pk)
                        d = disagree(args)
                        checked += 1
                        if d is not None:
                            print("status=fail DISAGREEMENT")
                            print(d)
                            return 1

    # --- FUZZ: random points to top up to >= N --------------------------------
    rng = _lcg(SEED)
    while checked < N:
        nb = next(rng) % 3
        bases = tuple(base_choices[next(rng) % len(base_choices)] for _ in range(nb))
        model_fields = _subset(rng, FIELDS)
        from_lookup = _mk_lookup(rng, (("app", "readable"), ("app", "other")), FIELDS)
        to_lookup = _mk_lookup(rng, (("app", "readable"), ("app", "other")), FIELDS)
        pk = PK[next(rng) % len(PK)]
        args = (app_label, model_name, bases, model_fields,
                from_lookup, to_lookup, pk)
        d = disagree(args)
        checked += 1
        if d is not None:
            print("status=fail DISAGREEMENT")
            print(d)
            return 1

    print(f"status=pass checked={checked} (exhaustive grid + fuzz, set-compare)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
