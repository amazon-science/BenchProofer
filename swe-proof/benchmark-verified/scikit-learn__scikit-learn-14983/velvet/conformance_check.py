#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14983.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List String` ↔ sorted param-name list; `List (String × Int)` ↔
              attribute / secondary-store dicts; `Option Int` ↔ value-or-None).
              This bundle consumes NO axioms, so the impl region is pure R/I:
              the shadow is the transliterated `resolveAll`.
  * ORACLE  — `patch.diff`'s behaviour: the exact patched value-resolution
              `_build_repr` performs,
                  value = getattr(self, key, None)
                  if value is None and hasattr(self, 'cvargs'):
                      value = self.cvargs.get(key, None)
              executed over a REAL object materialized from the same state.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Additionally, when the patched sklearn is importable (it is, in-container after
patch.diff is applied), an END-TO-END leg drives the real
`RepeatedKFold`/`RepeatedStratifiedKFold` objects and confirms the shadow's
resolved value map is consistent with their real `repr()` (the n_splits /
n_repeats / random_state values that appear in the rendered string) — tying the
R/I shadow directly to the G-RESOLVE oracle.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only (plus the
patched repo for the optional end-to-end leg). The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 14983
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean resolveOne/resolveAll, transliterated ------
def shadow_resolve_one(attrs, fallback, has_fallback, key):
    v = attrs.get(key, None)            # attrs.lookup key
    if v is not None:
        return v                        # some v
    if has_fallback:                    # none-branch with secondary store
        return fallback.get(key, None)  # fallback.lookup key
    return None                         # none, no fallback


def shadow_resolve_all(attrs, fallback, has_fallback, keys):
    """resolveAll (the backward `while` fold computes exactly this left-to-right
    ordered list)."""
    return [shadow_resolve_one(attrs, fallback, has_fallback, k) for k in keys]


# --- the ORACLE: patch.diff's genuine value-resolution over a real object -----
class _Obj:
    pass


def build_obj(attrs, fallback, has_fallback):
    obj = _Obj()
    for k, v in attrs.items():
        setattr(obj, k, v)
    if has_fallback:
        obj.cvargs = dict(fallback)
    return obj


def oracle_resolve(attrs, fallback, has_fallback, keys):
    obj = build_obj(attrs, fallback, has_fallback)
    out = []
    for key in keys:
        value = getattr(obj, key, None)                  # patched line (unchanged)
        if value is None and hasattr(obj, 'cvargs'):     # patched ADDED guard
            value = obj.cvargs.get(key, None)            # patched ADDED fallback
        out.append(value)
    return out


def fuzz_inputs(n, rng):
    key_pool = ["n_splits", "n_repeats", "random_state", "shuffle",
                "p", "max_train_size", "alpha", "k", "z"]
    repeated_keys = ["n_repeats", "n_splits", "random_state"]
    # boundary cases first (plan §4.1 step 4)
    yield ({"n_repeats": 6}, {"n_splits": 2}, True, repeated_keys)
    yield ({"n_repeats": 10}, {"n_splits": 5}, True, repeated_keys)
    yield ({"n_repeats": 6, "random_state": 0}, {"n_splits": 2}, True, repeated_keys)
    yield ({"n_repeats": 6}, {}, False, repeated_keys)
    yield ({"n_splits": 9, "n_repeats": 6}, {"n_splits": 2}, True, repeated_keys)
    yield ({}, {"n_repeats": 6, "n_splits": 2}, True, repeated_keys)
    yield ({}, {}, True, repeated_keys)
    yield ({}, {}, False, repeated_keys)
    yield ({"a": 1}, {"b": 2}, True, [])
    yield ({"a": 1}, {}, True, ["a"])
    yield ({}, {"a": 1}, True, ["a"])
    yield ({}, {"a": 1}, False, ["a"])
    for _ in range(n):
        nk = rng.randint(0, 6)
        keys = rng.sample(key_pool, nk)
        attrs, fallback = {}, {}
        for k in key_pool:
            r = rng.random()
            if r < 0.35:
                attrs[k] = rng.randint(-3, 12)
            elif r < 0.70:
                fallback[k] = rng.randint(-3, 12)
            elif r < 0.85:
                attrs[k] = rng.randint(-3, 12)
                fallback[k] = rng.randint(-3, 12)
        has_fallback = rng.random() < 0.8
        yield (attrs, fallback, has_fallback, keys)


def end_to_end_leg():
    """Optional: drive the REAL patched classes and confirm the shadow's value
    map matches the values rendered in their real repr(). Returns a status str."""
    try:
        from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold
    except Exception as e:  # pragma: no cover - only when sklearn absent
        return "skip (sklearn import failed: %s)" % e
    cases = [
        (RepeatedKFold, 2, 6), (RepeatedStratifiedKFold, 2, 6),
        (RepeatedKFold, 5, 10), (RepeatedStratifiedKFold, 3, 4),
    ]
    for cls, n_splits, n_repeats in cases:
        obj = cls(n_splits=n_splits, n_repeats=n_repeats)
        rendered = repr(obj)
        # shadow value map for the tested key order
        keys = ["n_repeats", "n_splits", "random_state"]
        attrs = {"n_repeats": obj.n_repeats}  # random_state is None -> absent
        fallback = {"n_splits": n_splits}
        vals = dict(zip(keys, shadow_resolve_all(attrs, fallback, True, keys)))
        # the rendered repr must show exactly these resolved values
        m = re.match(r"^%s\((.*)\)$" % re.escape(cls.__name__), rendered)
        assert m, "unexpected repr shape: %r" % rendered
        for k, v in vals.items():
            shown = "None" if v is None else str(v)
            assert ("%s=%s" % (k, shown)) in rendered, (
                "shadow value %s=%s not in real repr %r" % (k, shown, rendered))
        # the bug being fixed: n_splits must NOT render as None
        assert "n_splits=None" not in rendered, (
            "regression: n_splits rendered as None in %r" % rendered)
    return "ok (%d real RepeatedCV objects)" % len(cases)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for attrs, fallback, hf, keys in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_resolve_all(attrs, fallback, hf, keys)
        oracle = oracle_resolve(attrs, fallback, hf, keys)
        if shadow != oracle:
            disagreements.append((keys, attrs, fallback, hf, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for keys, a, f, hf, sh, orc in disagreements:
            print("  keys=%r attrs=%r fallback=%r hf=%r shadow=%r oracle=%r"
                  % (keys, a, f, hf, sh, orc))
        return 1
    e2e = end_to_end_leg()
    print("G-CONF OK: R/I shadow of buildReprValues agrees with patch.diff "
          "value-resolution on %d inputs (seed=%d), 0 disagreements; "
          "end-to-end: %s." % (count, SEED, e2e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
