#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15572.

The bundle models ONE function: `get_template_directories()`
(`django/template/autoreload.py`). It collects, into a SET, the normalized
absolute directory paths the template watcher should observe, drawn from two
sources per Django-templates backend:

  1. the backend's configured dirs (`backend.engine.dirs`), and
  2. each loader's dirs (`loader.get_dirs()`), excluding framework-internal ones
     (`is_django_path(directory)`).

Each entry `d` is normalized via `cwd / to_path(d)`. The Lean model abstracts
the per-backend / per-loader iteration into two flattened lists `dirs` /
`loaderDirs`, the normalizer into a parameter `resolveDir : str -> str`, and the
framework predicate into a parameter `isFrameworkPath : str -> bool`.

The POST-PATCH behavior (the fix) adds a truthiness guard at both sites:
  - a configured dir is kept iff it is non-empty;
  - a loader dir is kept iff it is non-empty AND not framework-internal.

This script transliterates the R/I Lean impl into Python (`shadow`) and
differential-tests it against an in-process ORACLE replica of the post-patch
`get_template_directories()` decision. Both legs return the SET of normalized
paths (the real function returns a Python `set`), so we compare `set(...)`.

We do NOT stand up Django's template engine machinery (heavy; the modeled value
is a pure set-collection decision over the two directory lists plus the two
abstract callees). Both legs are total functions over the modeled abstraction,
so the input space is enumerated exhaustively over short lists drawn from an
alphabet that includes the empty string `""` (the regression trigger) and
framework / non-framework markers; the fuzz loop additionally samples random
longer points. stdlib-only. Pinned seed: 15572 (also recorded in mapping.md).
"""
import itertools
import random
import sys

SEED = 15572
N = 150_000

# Directory-entry alphabet. "" is the regression trigger (falsy dir). "DJ_*"
# entries are treated as framework-internal by the injected predicate; others
# are ordinary user dirs. A small alphabet keeps exhaustive enumeration cheap.
ALPHABET = ("", "a", "b", "DJ_x", "DJ_y")


def is_framework_path(d):
    # Models is_django_path: true for framework-internal entries.
    return d.startswith("DJ_")


def resolve_dir(d):
    # Models cwd / to_path(d): deterministic injective-ish normalization. Note
    # both legs share the SAME normalizer, so its exact shape is immaterial —
    # what matters is WHICH entries reach it.
    return "/cwd/" + d


# --- ORACLE: post-patch get_template_directories(), faithful replica ----------
def oracle(dirs, loader_dirs):
    items = set()
    items.update(resolve_dir(d) for d in dirs if d)
    items.update(
        resolve_dir(d) for d in loader_dirs if d and not is_framework_path(d)
    )
    return items


# --- SHADOW: transliteration of the R/I Lean impl -----------------------------
def shadow(dirs, loader_dirs):
    items = []
    for d in dirs:
        if d != "":
            items.append(resolve_dir(d))
    for d in loader_dirs:
        if d != "" and is_framework_path(d) is False:
            items.append(resolve_dir(d))
    # Lean spec characterizes membership only (a set); compare as a set.
    return set(items)


def check(dirs, loader_dirs):
    return shadow(dirs, loader_dirs) == oracle(dirs, loader_dirs)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # Exhaustive: all (dirs, loaderDirs) with each list length 0..2 over ALPHABET.
    def lists_up_to(n):
        out = [()]
        for k in range(1, n + 1):
            out.extend(itertools.product(ALPHABET, repeat=k))
        return out

    small = lists_up_to(2)
    for dirs in small:
        for ld in small:
            checked += 1
            if not check(list(dirs), list(ld)):
                disagreements += 1
                if disagreements <= 5:
                    print(f"DISAGREE (exhaustive): dirs={dirs} loaderDirs={ld}")

    # Fuzz: longer random lists, including many empty strings.
    fuzz_alpha = ALPHABET + ("", "", "c", "DJ_z")
    while checked < N:
        ln1 = rng.randint(0, 6)
        ln2 = rng.randint(0, 6)
        dirs = [rng.choice(fuzz_alpha) for _ in range(ln1)]
        ld = [rng.choice(fuzz_alpha) for _ in range(ln2)]
        checked += 1
        if not check(dirs, ld):
            disagreements += 1
            if disagreements <= 5:
                print(f"DISAGREE (fuzz): dirs={dirs} loaderDirs={ld}")

    if disagreements:
        print(f"status=fail {disagreements} disagreement(s) over {checked} inputs")
        sys.exit(1)
    print(f"status=pass 0 disagreements over {checked} inputs (seed={SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
