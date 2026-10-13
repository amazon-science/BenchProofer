#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-14141.

The bundle models ONE routine: `_get_deps_info` (mapping.md), which builds an
ordered name->version overview by walking a hardcoded list of dependency
import-names and, for each, recording the version that name resolves to (or None
on import failure). The gold patch APPENDS "joblib" to that name list; nothing
else changes.

The modeled value is the returned dict, as an ordered list of (name, version)
pairs. Standing up the real importlib resolution is unnecessary and
environment-dependent: the per-name resolution (`lookupVersion`) is UNCHANGED by
the patch and is exercised IDENTICALLY by both legs. We fuzz it as a deterministic
version table over a universe of module names (including names that resolve to
None), and check that the SHADOW (op-for-op transliteration of
`implementation_dependencyVersions`) agrees with the ORACLE (faithful in-process
replica of the POST-PATCH dict construction) on the full ordered (key, value)
sequence.

This genuinely tests the soundness-critical fact: the overview's keys, in order,
are exactly the post-patch roster INCLUDING "joblib", each mapped to its resolved
version — matching the F2P expectation `'joblib' in deps_info`.

stdlib-only. Pinned seed: 14141 (also in mapping.md).
"""
import random
import sys

SEED = 14141
N = 120_000

# Post-patch roster (expectedDeps). The fix is the trailing "joblib".
EXPECTED_DEPS = ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
                 "pandas", "matplotlib", "joblib"]

# A universe of plausible module names for fuzzing the resolution table; includes
# the roster names plus extras that should never appear in the result.
UNIVERSE = EXPECTED_DEPS + ["six", "threadpoolctl", "absent_pkg", "wheel", "numexpr"]


def make_lookup(rng):
    """A fuzzed deterministic version resolver: name -> version str or None."""
    table = {}
    for name in UNIVERSE:
        r = rng.random()
        if r < 0.2:
            table[name] = None  # import failure
        else:
            table[name] = "%d.%d.%d" % (rng.randint(0, 9), rng.randint(0, 30),
                                         rng.randint(0, 30))
    return lambda m: table.get(m, None)


# --- ORACLE: faithful in-process replica of POST-PATCH _get_deps_info ----------
def oracle(lookup):
    deps = ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
            "pandas", "matplotlib", "joblib"]
    deps_info = {}
    for modname in deps:
        deps_info[modname] = lookup(modname)
    # ordered (insertion-order) (key, value) view
    return list(deps_info.items())


# --- SHADOW of implementation_dependencyVersions (R/I legs) -------------------
def shadow(lookup):
    deps = EXPECTED_DEPS
    deps_info = []
    for modname in deps:
        deps_info = deps_info + [(modname, lookup(modname))]
    return deps_info


def disagree(lookup):
    got = oracle(lookup)
    want = shadow(lookup)
    if got != want:
        return (got, want)
    return None


def main() -> int:
    checked = 0

    # Edge: joblib must be a key (the discriminating F2P fact), regardless of
    # whether it resolves to a version or None.
    for jl in ("1.0.0", None):
        lk = (lambda v: (lambda m: v if m == "joblib" else "x.y.z"))(jl)
        out = shadow(lk)
        keys = [k for k, _ in out]
        assert "joblib" in keys, "joblib missing from keys"
        assert keys == EXPECTED_DEPS, f"key set/order wrong: {keys}"
        d = disagree(lk)
        if d:
            print(f"DISAGREE edge: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    # All-None and all-present extremes.
    for const in (None, "9.9.9"):
        lk = (lambda c: (lambda m: c))(const)
        d = disagree(lk)
        if d:
            print(f"DISAGREE edge-const: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        lk = make_lookup(rng)
        d = disagree(lk)
        if d:
            print(f"DISAGREE fuzz: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
