#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_relaunchModule
against the patch.diff behaviour (post-patch `-m` module-name selection in
`get_child_arguments`).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: compute `isMainEntry(moduleName)` (exact equality
to '__main__' OR endswith '.__main__'), then select `parentPackage` iff
`isMainEntry and parentPackage != ''`, else `moduleName`. We diff that against an
independent reconstruction of the patched name-selection block:

    if (spec.name == '__main__' or spec.name.endswith('.__main__')) and spec.parent:
        name = spec.parent
    else:
        name = spec.name

over >=10^5 fuzzed (name, parent) pairs. Zero disagreements required.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14311          # pinned in mapping.md
N = 120_000           # >= 10^5

# Name/parent alphabets: dotted identifiers; oversample '__main__' and the
# '.__main__' suffix so the entry-point boundary is exercised heavily.
SEGMENTS = ["foo", "bar", "baz", "manage", "app", "x", "__main__", "main_module",
            "my__main__", "pkg", "mod"]


def is_main_entry(module_name: str) -> bool:
    """R/I shadow of isMainEntry."""
    return module_name == "__main__" or module_name.endswith(".__main__")


def shadow(module_name: str, parent_package: str) -> str:
    """R/I shadow of implementation_relaunchModule."""
    if is_main_entry(module_name) and parent_package != "":
        return parent_package
    else:
        return module_name


def patched_select(module_name: str, parent_package: str) -> str:
    """Independent reconstruction of the patched name-selection block.
    `spec.name` = module_name, `spec.parent` = parent_package."""
    spec_name = module_name
    spec_parent = parent_package
    if (spec_name == "__main__" or spec_name.endswith(".__main__")) and spec_parent:
        name = spec_parent
    else:
        name = spec_name
    return name


def rand_dotted(rng: random.Random) -> str:
    k = rng.randint(0, 4)
    if k == 0:
        return ""
    return ".".join(rng.choice(SEGMENTS) for _ in range(k))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        # F2P: python -m foo.bar.baz where baz is a plain module
        ("utils_tests.test_module.main_module", "utils_tests.test_module"),
        # package entry point: foo/bar/__main__.py
        ("foo.bar.__main__", "foo.bar"),
        # bare __main__
        ("__main__", ""),
        ("__main__", "foo"),
        # plain top-level module, no parent
        ("baz", ""),
        # plain dotted module with parent (the bug shape)
        ("foo.bar.baz", "foo.bar"),
        # corner case from hints: a module literally named *.my__main__
        ("foo.my__main__", "foo"),
        # endswith '.__main__' but no parent
        (".__main__", ""),
        ("a.__main__", "a"),
    ]
    cases = fixed + [
        (rand_dotted(rng), rand_dotted(rng))
        for _ in range(N)
    ]

    for module_name, parent_package in cases:
        got = shadow(module_name, parent_package)
        want = patched_select(module_name, parent_package)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((module_name, parent_package), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
