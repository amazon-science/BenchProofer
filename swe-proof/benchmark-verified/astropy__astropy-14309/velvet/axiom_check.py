#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14309.

Validates the single **A-reference** of this bundle: the deep model `hasKnownExt`
(Solution.lean `pure` region) against the REAL unchanged standard-library string
operation it transliterates — the case-folding suffix test
`str.lower().endswith((".fits",".fits.gz",".fit",".fit.gz",".fts",".fts.gz"))`.

There is NO consumed axiom in this bundle (directive 7): the changed control flow
is modeled directly in the spec and the extension test is a DEEP model. What G-AX
establishes is that that deep model is FAITHFUL to the real callee on every
boundary + fuzzed path (mapping.md §3.1, refinement.md §A2).

This check deliberately does NOT exercise `is_fits` itself: `is_fits` is the
function UNDER CHANGE, never a callee to axiomatize (directive 7). The control
flow the patch fixes (a present path returns the extension verdict outright; the
trailing-arg branch raises `IndexError` on empty `*args`) is the post-patch
behaviour, validated against the gold-patched repo by G-CONF, not here.

The callee under test is the Python standard library `str.lower()` / `str.endswith`
— the very operations the gold patch keeps unchanged — so this check is sound on
the unpatched repo G-AX runs against. stdlib only. Exit 0 iff every obligation
holds.
"""
import random
import string
import sys

KNOWN_EXTS = (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")


# --- the A-reference: the REAL unchanged extension test (connect.py:67-69) ----
def real_ext_test(path):
    return path.lower().endswith(KNOWN_EXTS)


# --- hasKnownExt: the Lean deep model, transliterated verbatim ----------------
#     hasKnownExt p = knownExts.any (fun ext => ext.isSuffixOf (p.map toLower))
def has_known_ext_model(path):
    low = path.lower()                                     # List.map Char.toLower
    return any(low.endswith(ext) for ext in KNOWN_EXTS)    # any · isSuffixOf


def check_ext_faithful(path):
    model = has_known_ext_model(path)
    real = real_ext_test(path)
    assert model == real, (
        "hasKnownExt(%r) = %r but real .lower().endswith((...)) = %r"
        % (path, model, real))


def main():
    # --- A-reference: hasKnownExt faithful on boundary inputs -----------------
    boundary = [
        "", ".", "foo", "foo.bar", "bububu.ecsv",          # non-matching
        "a.fits", "a.fit", "a.fts",                         # each single suffix
        "a.fits.gz", "a.fit.gz", "a.fts.gz",                # multi-dot suffixes
        "A.FITS", "B.Fits.GZ", "C.FiT", "x.FTS.gz",         # case variants
        ".fits", ".fits.gz",                                # suffix == whole name
        "a.fits.bak", "fits", "myfits", "a.fitsx",          # near-miss, no real suffix
        "a.fit.gz.txt", "report.fit.csv",                   # suffix not at end
        "weird.FiTs", "two.fits.fits",                      # repeated / mixed
    ]
    for p in boundary:
        check_ext_faithful(p)

    # --- A-reference (cont): randomized fuzz over hasKnownExt -----------------
    rng = random.Random(14309)
    alphabet = string.ascii_letters + string.digits + "._-/ "
    n_fuzz = 20_000
    n_match = 0
    for _ in range(n_fuzz):
        base = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
        if rng.random() < 0.5:
            # bias toward genuine matches: append a (possibly case-mangled) suffix
            ext = rng.choice(KNOWN_EXTS)
            ext = "".join(c.upper() if rng.random() < 0.3 else c for c in ext)
            p = base + ext
        else:
            p = base
        check_ext_faithful(p)
        if real_ext_test(p):
            n_match += 1
    assert n_match > 200, (
        "fuzz produced too few genuine extension matches (%d) — the matching "
        "leg is under-exercised" % n_match)

    print("G-AX OK: hasKnownExt deep model (== real str.lower().endswith((...))) "
          "sound on %d boundary + %d fuzz paths (%d genuine matches). "
          "A-reference fidelity confirmed; no consumed axiom; is_fits (the "
          "function under change) deliberately not exercised here (G-CONF covers "
          "the post-patch control flow against the patched repo)."
          % (len(boundary), n_fuzz, n_match))
    return 0


if __name__ == "__main__":
    sys.exit(main())
