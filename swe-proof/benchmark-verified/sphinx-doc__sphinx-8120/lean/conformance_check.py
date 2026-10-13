#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-8120.

The modeled behavior is the assembly of the message-catalog search list inside
`Sphinx._init_i18n` (sphinx/application.py:296). The post-patch assembly is a
self-contained, side-effect-free list construction:

    locale_dirs = [None]                                  # type: List[Optional[str]]
    locale_dirs += list(repo.locale_dirs)
    locale_dirs += [path.join(package_dir, 'locale')]

with no live Sphinx application required (the two data sources
`list(repo.locale_dirs)` and `path.join(package_dir, 'locale')` are ordinary
values). The `oracle` below is that post-patch fragment transcribed verbatim;
the `shadow` is the R/I transliteration of `implementation_searchDirs` (the Lean
impl) per refinement.md. We diff them over >=1e5 fuzzed inputs; zero
disagreements => exit 0.

Type bijection (mapping.md): userDirs<->list(repo.locale_dirs) (list[str]),
bundledDir<->path.join(package_dir,'locale') (str), result<->locale_dirs
(list whose entries are str|None), none<->None, some s<->s.

stdlib-only; no third-party deps.
"""
import random
import sys


def oracle(user_dirs, bundled_dir):
    """Post-patch repo fragment, transcribed verbatim from patch.diff."""
    locale_dirs = [None]                       # type: list
    locale_dirs += list(user_dirs)             # list(repo.locale_dirs)
    locale_dirs += [bundled_dir]               # [path.join(package_dir, 'locale')]
    return locale_dirs


def shadow(user_dirs, bundled_dir):
    """R/I transliteration of implementation_searchDirs (Lean).

    Lean `none` <-> Python `None`; Lean `some s` <-> Python `s`.
    """
    search_dirs = [None]
    search_dirs = search_dirs + [s for s in user_dirs]
    search_dirs = search_dirs + [bundled_dir]
    return search_dirs


def rand_path(rng):
    n = rng.randint(1, 8)
    alpha = "abcEFG_/.-0123 "
    return "".join(rng.choice(alpha) for _ in range(n))


def main():
    rng = random.Random(8120)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        k = rng.randint(0, 6)               # number of caller-supplied dirs (incl. 0)
        user_dirs = [rand_path(rng) for _ in range(k)]
        bundled_dir = rand_path(rng)
        o = oracle(user_dirs, bundled_dir)
        s = shadow(user_dirs, bundled_dir)
        if o != s:
            disagreements += 1
            if first is None:
                first = (user_dirs, bundled_dir, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
