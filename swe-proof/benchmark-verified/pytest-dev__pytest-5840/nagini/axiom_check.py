#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5840.

The changed operation in this bundle -- the deduplication key under which a
configuration helper file is cached and later looked up -- is modelled in
model.py by three callee contracts validated here against the REAL cache
semantics the gold patch relies on:

  * `canonical(loc)` -- the unchanged value-level canonicalisation of a
    location string (its structural resolution). Modelled as a deterministic
    pure callee; the real callee is `Path(str(loc)).resolve()` (and the removed
    convention's `realpath(str(loc))`), which produce the SAME location string.

  * `make_key(loc, recognised_convention)` -- the key constructor. Either
    convention returns a key carrying the canonical location STRING; only the
    recognised convention's key is RECOGNISED by the cache's membership test.

  * `lookup_recognised(canon)` -- the unforgeable token granted only by the
    recognised convention: a key the membership test recognises as equal to an
    independently-recomputed key for the same canonical location.

The cache's membership test is `recomputed_key in conftestpath2mod`, where the
stored key was produced by the constructor and `recomputed_key` is an
INDEPENDENT recomputation for the same location (exactly what the FAIL_TO_PASS
test does: `key = Path(str(subconftest)).resolve(); assert key in
conftest._conftestpath2mod`). The two constructor conventions are the two real
key kinds:

  * recognised convention  ->  `Path(str(loc)).resolve()`            (pathlib)
  * unrecognised convention ->  `type(local)(normcase(realpath(...)))` i.e.
                                `unique_path` of a `py.path.local`     (py.path)

The check asserts, on real files (the issue scenarios + the FAIL_TO_PASS subdir
names + randomized fuzz):

  (canonical)   both conventions carry the IDENTICAL canonical location string
                -- so location-string equality is NOT the discriminator;
  (recognised)  an independently-recomputed key IS found in a dict keyed by the
                recognised convention's key (the token is sound: lookup HITS);
  (unrecognised) the same independently-recomputed key is NOT found in a dict
                keyed by the unrecognised convention's key (no token: lookup
                MISSES), even though the location strings are identical.

This binds the modeled discriminator (the recognition effect) to a real
PRE-miss / POST-hit on the dimension the graded tests observe on THIS platform,
not to letter casing (which `normcase` leaves untouched on POSIX). Imports only
`pathlib`, `os`, `py` (the modules the patch and the test use) plus stdlib
fixtures. Exit 0 iff every obligation holds.
"""
import os
import os.path
import random
import sys
import tempfile
from pathlib import Path

import py  # py.path.local -- the pre-change key object kind


def canonical_string(loc):
    """Reference of model.py `canonical`: the value-level canonical location
    string. Both real conventions resolve to the same string on this platform;
    we take the recognised convention's resolution as the canonical string."""
    return str(Path(str(loc)).resolve())


def recognised_key(loc):
    """The recognised convention's key (gold): `Path(str(loc)).resolve()`."""
    return Path(str(loc)).resolve()


def unrecognised_key(loc):
    """The unrecognised convention's key (the removed `unique_path`): a
    `py.path.local` wrapping `normcase(realpath(str(loc)))`."""
    local = py.path.local(str(loc))
    return type(local)(os.path.normcase(str(local.realpath())))


def recomputed_lookup_key(loc):
    """The key an INDEPENDENT later lookup recomputes for the same location --
    exactly the FAIL_TO_PASS test's `Path(str(subconftest)).resolve()`."""
    return Path(str(loc)).resolve()


def check_location(real_file):
    """Validate the three contracts on one real file."""
    canon = canonical_string(real_file)

    rec_key = recognised_key(real_file)
    unrec_key = unrecognised_key(real_file)
    lookup = recomputed_lookup_key(real_file)

    # (canonical) both conventions carry the IDENTICAL canonical location string
    # -- location-string equality is necessary but NOT the discriminator.
    assert str(rec_key) == canon, (
        "recognised key string %r != canonical %r" % (str(rec_key), canon))
    assert str(unrec_key) == canon, (
        "unrecognised key string %r != canonical %r" % (str(unrec_key), canon))
    assert str(rec_key) == str(unrec_key), (
        "the two conventions disagree on the location string: %r vs %r"
        % (str(rec_key), str(unrec_key)))

    # (recognised) the recognised convention's key IS recognised by the cache's
    # membership test -- an independently-recomputed key HITS. (Token is sound.)
    cache_recognised = {rec_key: "mod"}
    assert lookup in cache_recognised, (
        "recognised key not found by recomputed-key membership on %r"
        % str(real_file))

    # (unrecognised) the unrecognised convention's key is NOT recognised --
    # the same recomputed key MISSES, despite the identical location string.
    cache_unrecognised = {unrec_key: "mod"}
    assert lookup not in cache_unrecognised, (
        "unrecognised key was unexpectedly found by recomputed-key membership "
        "on %r (location string %r)" % (str(real_file), canon))


def main():
    tmp = tempfile.mkdtemp()

    # Boundary: the FAIL_TO_PASS subdir names (all lowercase -- proving the
    # discriminator is NOT casing on this platform) + the issue scenarios.
    boundary_names = [
        "test", "tests",            # the FAIL_TO_PASS subdir names (lowercase)
        "Foo",                      # #5819 uppercase-package scenario
        "JenkinsRoot",              # #5792 case-insensitivity scenario
        "imageProcessing",          # user-reported mixed-case package
        "abc", "plain", "x",        # extra all-lowercase names
        "ABC", "MixedCASE_123",
    ]
    for name in boundary_names:
        d = os.path.join(tmp, name)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "conftest.py")
        with open(f, "w"):
            pass
        check_location(f)

    # Randomized fuzz of mixed/lower/upper basenames.
    rng = random.Random(5840)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    for _ in range(2000):
        n = rng.randint(1, 16)
        name = "".join(rng.choice(letters) for _ in range(n))
        if not any(ch.isalpha() for ch in name):
            continue
        d = os.path.join(tmp, "fuzz_%s" % name)
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            continue
        f = os.path.join(d, "conftest.py")
        with open(f, "w"):
            pass
        check_location(f)

    print("G-AX OK: on %d boundary + 2000 fuzz real files, both key conventions "
          "carry the IDENTICAL canonical location string, the recognised "
          "convention's key is FOUND by an independently-recomputed lookup "
          "(lookup_recognised sound), and the unrecognised convention's key is "
          "NOT found despite the identical string (no token). The discriminator "
          "is the recognition effect, not letter casing." % len(boundary_names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
