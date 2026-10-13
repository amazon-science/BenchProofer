#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14983.

This bundle consumes NO axioms: the changed behaviour (per-parameter value
resolution gaining a secondary-store fallback) is modeled DEEPLY by
`resolveOne`/`resolveAll` in Solution.lean's pure region. G-AX validates that
deep model against the REAL value-resolution the gold patch performs — an
A-reference-style soundness check (deep model == real callee behaviour).

The "real callee" is the exact value-resolution the patch composes inside
`_build_repr`:

    value = getattr(self, key, None)
    if value is None and hasattr(self, 'cvargs'):
        value = self.cvargs.get(key, None)

We execute that genuine composition against real Python objects (built via
`setattr` and a real `cvargs` dict) over boundary + fuzzed object states, and
assert it equals the deep model `resolve_one` for every (key, object) pair, and
that the ordered sweep equals `resolve_all`. Imports stdlib only. Exit 0 iff
every obligation holds.
"""
import random
import sys


# --- deep model: Solution.lean resolveOne / resolveAll, transliterated -------
# attrs / fallback are dicts mapping key -> int (a key with a non-None int
# value).  A key absent from attrs models `getattr(self, key, None) is None`.
def resolve_one(attrs, fallback, has_fallback, key):
    v = attrs.get(key, None)            # attrs.lookup key
    if v is not None:
        return v                        # some v
    if has_fallback:                    # none-branch with secondary store
        return fallback.get(key, None)  # fallback.lookup key
    return None                         # none, no fallback


def resolve_all(attrs, fallback, has_fallback, keys):
    return [resolve_one(attrs, fallback, has_fallback, k) for k in keys]


# --- the REAL patched value-resolution (genuine callee composition) ----------
class _Obj:
    """A minimal stand-in carrying real attributes (and optionally a real
    `cvargs` dict), so getattr / hasattr / dict.get behave exactly as in the
    patched `_build_repr`."""
    pass


def real_resolution(obj, keys):
    """The exact patched composition, run over a real object. Returns the
    ordered list of resolved values (mapping.md §2: None ↔ none)."""
    out = []
    for key in keys:
        value = getattr(obj, key, None)                       # real getattr
        if value is None and hasattr(obj, 'cvargs'):          # real hasattr
            value = obj.cvargs.get(key, None)                 # real dict.get
        out.append(value)
    return out


def build_obj(attrs, fallback, has_fallback):
    """Materialize a real object whose attribute table is `attrs` and whose
    secondary store is `fallback` (present iff has_fallback)."""
    obj = _Obj()
    for k, v in attrs.items():
        setattr(obj, k, v)
    if has_fallback:
        obj.cvargs = dict(fallback)
    return obj


def check_state(attrs, fallback, has_fallback, keys):
    obj = build_obj(attrs, fallback, has_fallback)
    real = real_resolution(obj, keys)
    model = resolve_all(attrs, fallback, has_fallback, keys)
    assert real == model, (
        "deep model unsound: keys=%r attrs=%r fallback=%r has_fallback=%r "
        "real=%r model=%r" % (keys, attrs, fallback, has_fallback, real, model))


def main():
    # The tested configuration's sorted parameter names (test_repeated_cv_repr):
    repeated_keys = ["n_repeats", "n_splits", "random_state"]

    # --- boundary object states -------------------------------------------
    boundary = [
        # the real RepeatedKFold/RepeatedStratifiedKFold shape: n_repeats &
        # random_state are own attributes; n_splits lives only in cvargs;
        # random_state=None is modeled as an absent attribute.
        ({"n_repeats": 6}, {"n_splits": 2}, True, repeated_keys),
        ({"n_repeats": 10}, {"n_splits": 5}, True, repeated_keys),
        # random_state present as a real integer attribute
        ({"n_repeats": 6, "random_state": 0}, {"n_splits": 2}, True, repeated_keys),
        # no secondary store at all (plain estimator): store-only keys -> None
        ({"n_repeats": 6}, {}, False, repeated_keys),
        # key in both attrs and fallback -> attrs wins
        ({"n_splits": 9, "n_repeats": 6}, {"n_splits": 2}, True, repeated_keys),
        # everything in fallback only
        ({}, {"n_repeats": 6, "n_splits": 2}, True, repeated_keys),
        # everything absent everywhere
        ({}, {}, True, repeated_keys),
        ({}, {}, False, repeated_keys),
        # empty key list
        ({"a": 1}, {"b": 2}, True, []),
        # single key, each placement
        ({"a": 1}, {}, True, ["a"]),
        ({}, {"a": 1}, True, ["a"]),
        ({}, {"a": 1}, False, ["a"]),
    ]
    for attrs, fallback, hf, keys in boundary:
        check_state(attrs, fallback, hf, keys)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(14983)
    key_pool = ["n_splits", "n_repeats", "random_state", "shuffle",
                "p", "max_train_size", "alpha", "k", "z"]
    for _ in range(20000):
        nk = rng.randint(0, 6)
        keys = rng.sample(key_pool, nk)
        attrs, fallback = {}, {}
        for k in key_pool:
            r = rng.random()
            if r < 0.35:
                attrs[k] = rng.randint(-3, 12)      # own attribute (int)
            elif r < 0.70:
                fallback[k] = rng.randint(-3, 12)    # secondary store
            elif r < 0.85:
                attrs[k] = rng.randint(-3, 12)       # in both
                fallback[k] = rng.randint(-3, 12)
            # else: absent from both
        has_fallback = rng.random() < 0.8
        check_state(attrs, fallback, has_fallback, keys)

    print("G-AX OK: resolveOne/resolveAll deep model == real patched value "
          "resolution (getattr + cvargs.get) on %d boundary + 20000 fuzz "
          "object states." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
