#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_ensureSupportedVersion against the patch.diff behaviour
(post-patch check_sqlite_version).

The impl region is all I/R (no A-tagged callee), so this runs a real fuzz. The
shadow reconstructs the Lean impl op-for-op (versionLt + errorMessage), bridged
through the type bijection in mapping.md; the oracle is an independent
reconstruction of the post-patch Python:

    if version_info < (3, 9, 0):
        raise ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % version)

We map a normal return to ('ok', None) and a raise to ('error', msg), then assert
zero disagreements over >=10^5 fuzzed version tuples. exit 0 iff zero
disagreements. stdlib-only.
"""
import random
import sys

SEED = 13821          # pinned in mapping.md
N = 120_000           # >= 10^5

REQUIRED_MIN = (3, 9, 0)


def version_lt(info, other):
    """Lean `versionLt` — identical to Python tuple `<` (lexicographic, prefix
    rule). Implemented from scratch to mirror the Lean recursion, NOT via the
    builtin, so the differential is meaningful."""
    a, b = list(info), list(other)
    i = 0
    while True:
        if i >= len(a) and i >= len(b):
            return False
        if i >= len(a):            # a is a strict prefix of b
            return True
        if i >= len(b):            # b is a strict prefix of a
            return False
        if a[i] < b[i]:
            return True
        if b[i] < a[i]:
            return False
        i += 1


def error_message(version_str):
    return "SQLite 3.9.0 or later is required (found " + version_str + ")."


def shadow(version_info, version_str):
    """R/I shadow of implementation_ensureSupportedVersion."""
    if version_lt(tuple(version_info), REQUIRED_MIN):
        return ("error", error_message(version_str))
    return ("ok", None)


def patched(version_info, version_str):
    """Independent reconstruction of post-patch check_sqlite_version, using the
    real Python tuple comparison and %-formatting."""
    if tuple(version_info) < REQUIRED_MIN:
        return ("error",
                'SQLite 3.9.0 or later is required (found %s).' % version_str)
    return ("ok", None)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Components oversample the boundary digits so the threshold is hit hard.
    comp_pool = [0, 1, 2, 3, 8, 9, 10, 11, 3, 8, 9, 0]

    def rand_version():
        n = rng.randint(0, 6)
        return tuple(rng.choice(comp_pool) for _ in range(n))

    # Deterministic boundary cases first (incl. the F2P test input).
    fixed = [
        ((3, 8, 11, 1), "3.8.11.1"),   # F2P: must now be rejected
        ((3, 8, 2), "3.8.2"),          # old F2P input: rejected under both
        ((3, 9, 0), "3.9.0"),          # exactly the minimum: accepted
        ((3, 8, 3), "3.8.3"),          # old minimum: now rejected
        ((3, 9), "3.9"),               # prefix of minimum: 3.9 < 3.9.0 -> rejected
        ((3, 10), "3.10"),             # accepted
        ((3, 11, 0), "3.11.0"),        # Xenial: accepted
        ((), ""),                      # empty tuple: () < (3,9,0) -> rejected
        ((4,), "4"),                   # accepted
        ((3, 9, 0, 0), "3.9.0.0"),     # extension of minimum: accepted
    ]
    cases = fixed + [(rand_version(),
                      ".".join(str(x) for x in rand_version()))
                     for _ in range(N)]

    for info, vstr in cases:
        got = shadow(list(info), vstr)
        want = patched(info, vstr)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((info, vstr, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for info, vstr, g, w in examples:
            print(f"  info={info!r} str={vstr!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
