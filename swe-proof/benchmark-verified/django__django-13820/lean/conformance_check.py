#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_providesMigrations against the patch.diff behaviour (the
post-patch namespace-package guard in MigrationLoader.load_disk).

The impl region is entirely I-tagged (boolean introspection ops; no A-reference,
no domain callee), so this runs a real fuzz. The shadow reproduces the impl's
control flow op-for-op; `patched_guard` is an independent reconstruction of the
post-patch django guard expressed directly in terms of the real introspection
predicates (`__path__` present, `__path__` is a list, `__file__` is not None).
We assert zero disagreements over the full 6-point domain plus >=10^5 fuzzed
inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13820          # pinned in mapping.md
N = 120_000           # >= 10^5

# ModulePath discriminants (mapping.md bijection).
NO_PATH, LIST_PATH, CUSTOM_PATH = "noPath", "listPath", "customPath"
PATHS = [NO_PATH, LIST_PATH, CUSTOM_PATH]


def is_package(path: str) -> bool:
    return path != NO_PATH


def is_list(path: str) -> bool:
    return path == LIST_PATH


def shadow(has_file: bool, path: str) -> bool:
    """R/I shadow of implementation_providesMigrations (op-for-op).

    if not isPackage: return False
    if not has_file and not isList: return False
    return True
    """
    if not is_package(path):
        return False
    if (not has_file) and (not is_list(path)):
        return False
    return True


def patched_guard(has_file: bool, path: str) -> bool:
    """Independent reconstruction of the POST-PATCH django guard:

        if not hasattr(module, '__path__'):              -> unmigrated (False)
        if getattr(module,'__file__',None) is None
           and not isinstance(module.__path__, list):     -> unmigrated (False)
        else                                             -> migrated   (True)
    """
    has_path = path != NO_PATH                 # hasattr(module, '__path__')
    file_is_none = not has_file                # getattr(...,'__file__',None) is None
    path_is_list = path == LIST_PATH           # isinstance(module.__path__, list)
    if not has_path:
        return False
    if file_is_none and not path_is_list:
        return False
    return True


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Exhaustive 6-point domain first.
    cases = [(hf, p) for hf in (False, True) for p in PATHS]
    # Pad with fuzz, oversampling the discriminating (False, listPath) case.
    weighted = PATHS + [LIST_PATH] * 2
    cases += [(rng.random() < 0.5, rng.choice(weighted)) for _ in range(N)]

    for hf, p in cases:
        got = shadow(hf, p)
        want = patched_guard(hf, p)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((hf, p, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for hf, p, g, w in examples:
            print(f"  has_file={hf} path={p} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
