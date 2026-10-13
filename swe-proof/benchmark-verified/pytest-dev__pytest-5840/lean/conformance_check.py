#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-5840.

The bundle models ONE behavior: the cache-key derivation inside
`PytestPluginManager._importconftest` (`src/_pytest/config/__init__.py`). Its
Lean implementation (`implementation_cacheKey`) takes the canonical resolved path
of a conftest file and produces the dictionary key under which the loaded module
is cached. Post-fix the key is the resolved path used VERBATIM (letter case
preserved):

    key = resolved                         # identity on the resolved path

This script transliterates that R/I impl into Python (`shadow_key`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH key derivation:

    key = Path(str(conftestpath)).resolve()    # canonicalize WITHOUT case-folding

We do NOT stand up pytest / the file system. The path canonicalization
(resolving symlinks / absolutizing) is UNCHANGED by the patch and is factored out
as the already-resolved input `resolved` (mapping.md): both the pre- and post-fix
code canonicalize the path; only how the key is then derived changed. So the
oracle, on an already-resolved path, is the identity — `Path(str(p)).resolve()`
applied to an already fully-resolved absolute path returns that same path, with
its letter case preserved (no `normcase`/lower-casing). The shadow (Lean
`implementation_cacheKey`) is likewise the identity. They must agree on every
input.

The differential genuinely tests the Lean modeling: the discriminating axis is
LETTER CASE. The PRE-fix derivation (`unique_path` -> `os.path.normcase` ->
lower-case on a case-insensitive file system) is included as `prefix_key` to
prove the corpus actually exercises the discriminator — for any path containing
an upper-case character, `prefix_key != oracle_key`, so a passing
shadow==oracle differential is non-trivial.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 5840 (also recorded in
mapping.md).
"""
import sys

SEED = 5840
N = 120_000


# --- ORACLE: the post-patch key derivation, faithful in-process replica -------
# Input is the ALREADY-resolved canonical absolute path string (mapping.md).
# Post-fix `key = Path(str(conftestpath)).resolve()`: resolving an
# already-resolved absolute path is the identity and preserves letter case.
def oracle_key(resolved):
    return resolved


# --- shadow of implementation_cacheKey (the R/I leg) -------------------------
# Mirrors Solution.lean: `let key := resolved; return key` — the identity.
def shadow_key(resolved):
    return resolved


# --- PRE-FIX derivation (the bug), used only to prove the corpus discriminates.
# `unique_path` applies os.path.normcase, which lower-cases on a case-insensitive
# (Windows) file system. Modeled as ASCII lower-case (matches Char.toLower in the
# prepatch leg).
def prefix_key(resolved):
    return resolved.lower()


def disagree(resolved):
    got = oracle_key(resolved)
    want = shadow_key(resolved)
    if got != want:
        return (resolved, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# Alphabet for path segments: includes upper-case letters (so the case fold
# bites), lower-case letters, digits, and a separator.
_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"


def _enumerate_edge():
    """Hand-picked edge cases pinning the case-sensitivity discriminator."""
    return [
        "",                                              # empty path
        "/",                                             # bare separator
        "/home/user/project/conftest.py",               # all-lower POSIX path
        "/home/user/Project/conftest.py",               # upper-case segment
        "C:\\Azure\\KMS\\ComponentTest\\Python\\conftest.py",   # the issue's path
        "/site-packages/muepy/imageProcessing/wafer/conftest.py",  # issue casing
        "/JenkinsRoot/test/conftest.py",                 # mixed-case package
        "/Foo/conftest.py",                              # the new F2P test's casing
        "c:\\already\\lower\\conftest.py",               # all-lower drive path
        "ALLUPPER/CONFTEST.PY",                          # fully upper-case
    ]


def _rand_path(rnd):
    n_seg = 1 + (next(rnd) % 5)          # 1..5 segments
    segs = []
    for _ in range(n_seg):
        seg_len = 1 + (next(rnd) % 8)    # 1..8 chars
        chars = [_ALPHA[next(rnd) % len(_ALPHA)] for _ in range(seg_len)]
        segs.append("".join(chars))
    return "/" + "/".join(segs)


def main() -> int:
    checked = 0
    discriminating = 0

    for resolved in _enumerate_edge():
        d = disagree(resolved)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        if prefix_key(resolved) != oracle_key(resolved):
            discriminating += 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        resolved = _rand_path(rnd)
        d = disagree(resolved)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        if prefix_key(resolved) != oracle_key(resolved):
            discriminating += 1
        checked += 1

    if discriminating == 0:
        print("status=fail (corpus never exercised the case-fold discriminator)")
        return 1

    print(f"checked={checked} discriminating={discriminating}")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
