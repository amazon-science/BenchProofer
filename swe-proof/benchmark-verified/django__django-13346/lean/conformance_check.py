#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_inClauseSql
against the patch.diff behaviour (post-patch membership-clause RHS rendering).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: start from the base bare placeholder
`(%s, …, %s)`, and on a backend without a native JSON column type rebuild the
clause with each slot replaced by that backend's value-extraction wrapper.

We diff that against an INDEPENDENT reconstruction of the post-patch rendering
that mirrors the real Python control flow: build the base placeholder exactly as
`lookups.In.process_rhs` does (`'(' + ', '.join(['%s'] * n) + ')'`), and on a
non-native-JSON backend apply the real `rhs = rhs % func` substitution with
`func` the per-vendor template tuple — the literal string operations the gold
patch performs. Zero disagreements required over >= 10^5 fuzzed inputs.

Scope: the four modeled string-builder backends (postgresql / sqlite / mysql /
mariadb). The Oracle branch (per-value json.loads/json.dumps round-trip) is out
of model scope (mapping.md) and not fuzzed.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13346          # pinned in mapping.md
N = 120_000           # >= 10^5

VENDORS = ["postgresql", "sqlite", "mysql", "mariadb"]

# native JSON column type by vendor (django backend `has_native_json_field`)
HAS_NATIVE = {
    "postgresql": True,
    "sqlite": False,
    "mysql": False,
    "mariadb": False,
}

# per-vendor value-extraction template (the gold `func` element)
WRAPPER = {
    "postgresql": "%s",
    "sqlite": "JSON_EXTRACT(%s, '$')",
    "mysql": "JSON_EXTRACT(%s, '$')",
    "mariadb": "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))",
}


def shadow(vendor: str, n: int) -> str:
    """R/I shadow of implementation_inClauseSql (op-for-op)."""
    def build(slot):
        return "(" + ", ".join([slot] * n) + ")"
    rhs = build("%s")
    if not HAS_NATIVE[vendor]:
        rhs = build(WRAPPER[vendor])
    return rhs


def patched_render(vendor: str, n: int) -> str:
    """Independent reconstruction mirroring the real Python string ops:
    base placeholder from lookups.In.process_rhs, then `rhs % func`."""
    # lookups.In.process_rhs direct-value path: one '%s' per value
    rhs = "(" + ", ".join(["%s"] * n) + ")"
    if not HAS_NATIVE[vendor]:
        if vendor == "mariadb":
            func = ("JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))",) * n
        else:  # sqlite, mysql
            func = ("JSON_EXTRACT(%s, '$')",) * n
        rhs = rhs % func           # the gold substitution: %s -> wrapper(%s)
    return rhs


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact n=1 F2P shape per vendor.
    fixed = []
    for v in VENDORS:
        for n in (1, 2, 3):
            fixed.append((v, n))

    cases = fixed + [
        (rng.choice(VENDORS), rng.randint(1, 12))
        for _ in range(N)
    ]

    for vendor, n in cases:
        got = shadow(vendor, n)
        want = patched_render(vendor, n)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((vendor, n), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
