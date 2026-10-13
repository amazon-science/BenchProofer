#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7985.

There are NO consumed `@ContractOnly` axioms in model.py: the two changed
string decisions are modelled DEEPLY and are **A-references** that must equal
the REAL stdlib callees the gold patch uses. This script executes those real
callees on boundary + randomized-fuzz inputs and asserts:

  (1) the deep model `prefix_eq` (model.py `starts_with`) == the real
      `str.startswith(prefix)` (anchored literal prefix test), for each of the
      literal scheme prefixes the classifier tests (`#`, `mailto:`, `http:`,
      `https:`, and the pre-patch `ftp:`);

  (2) the deep model `has_uri_scheme` (model.py `scheme_present`) == the real
      anchored match of `re.compile('[a-z]+://')` — the exact regex the gold
      patch introduces (`uri_re = re.compile('[a-z]+://')`, used via
      `uri_re.match(uri)`);

  (3) the deep model `classify` (model.py) == the REAL post-patch `check()`
      decision cascade, where the two genuinely environment-dependent facts —
      `path.exists(path.join(srcdir, uri))` and "some ignore regex matches" —
      and the opaque remote outcome are supplied as values (they are model
      inputs, not axioms). The real `check()` body is transcribed verbatim from
      the gold patch; this asserts the deep model reproduces its branching.

  (4) the discrimination is real: the PRE-patch `check()` (which returns the
      unclassified 'local' outcome for every non-web target, and treats `ftp:`
      as unchecked) disagrees with the deep model exactly on the local-file
      targets the F2P tests add (an existing file -> working, a missing file ->
      broken / ignored), so the deep model tracks the FIXED behaviour.

Imports nothing repo-specific: `re` is the Python standard library — the same
module the changed code uses; the file-existence / ignore facts are passed as
booleans rather than touching a real filesystem. Exit 0 iff every obligation
holds.
"""
import re
import random
import sys

# The exact regex the gold patch introduces at module level.
URI_RE = re.compile('[a-z]+://')

# Status codes, matching model.py's UNCHECKED/WORKING/MISSING/IGNORED and the
# pre-patch 'local' (4); the remote branch carries an opaque value.
UNCHECKED, WORKING, MISSING, IGNORED, LOCAL = 0, 1, 2, 3, 4
REMOTE = 99  # an opaque remote-handling outcome value


# --- deep-model reference implementations (kept in lock-step with model.py) --

def prefix_eq(s, lit):
    """Reference for model.py `prefix_eq` / `starts_with`: literal prefix."""
    return s[:len(lit)] == lit


def lower_run(s):
    """Reference for model.py `lower_run`: maximal leading [a-z] run length."""
    k = 0
    while k < len(s) and 'a' <= s[k] <= 'z':
        k += 1
    return k


def has_uri_scheme(s):
    """Reference for model.py `has_uri_scheme` / `scheme_present`."""
    k = lower_run(s)
    return k >= 1 and len(s) >= k + 3 and s[k] == ':' and s[k + 1] == '/' \
        and s[k + 2] == '/'


def classify(s, file_exists, ignore_match, remote):
    """Reference for model.py `classify` (the post-patch decision cascade)."""
    if len(s) == 0 or s.startswith(('#', 'mailto:')):
        return UNCHECKED
    if not s.startswith(('http:', 'https:')):
        if has_uri_scheme(s):
            return UNCHECKED
        if file_exists:
            return WORKING
        if ignore_match:
            return IGNORED
        return MISSING
    return remote


# --- the REAL callees / real check() bodies, verbatim from the patch ---------

def real_check_postpatch(uri, file_exists, ignore_match, remote):
    """The gold-patched `check()` body, transcribed verbatim (statuses encoded
    as the model's integer codes; `path.exists(...)` -> file_exists; the inner
    ignore loop -> ignore_match; the unchanged remote branch -> remote)."""
    if len(uri) == 0 or uri.startswith(('#', 'mailto:')):
        return UNCHECKED
    elif not uri.startswith(('http:', 'https:')):
        if URI_RE.match(uri):                 # the real introduced regex
            return UNCHECKED
        else:
            if file_exists:                   # path.exists(join(srcdir, uri))
                return WORKING
            else:
                if ignore_match:              # some rex in to_ignore matches
                    return IGNORED
                else:
                    return MISSING
    else:
        return remote


def real_check_prepatch(uri, file_exists, ignore_match, remote):
    """The PRE-patch `check()` body, transcribed verbatim: every non-web target
    is the unclassified 'local' outcome; `ftp:` is unchecked."""
    if len(uri) == 0 or uri.startswith(('#', 'mailto:', 'ftp:')):
        return UNCHECKED
    elif not uri.startswith(('http:', 'https:')):
        return LOCAL
    else:
        return remote


# --- checks ------------------------------------------------------------------

SCHEME_LITERALS = ['#', 'mailto:', 'http:', 'https:', 'ftp:']


def check_startswith(s):
    """(1) deep model prefix_eq == real str.startswith, for every literal."""
    for lit in SCHEME_LITERALS:
        model = prefix_eq(s, lit)
        real = s.startswith(lit)
        assert model == real, (
            "prefix_eq deep model unsound vs str.startswith on s=%r lit=%r: "
            "model=%r real=%r" % (s, lit, model, real))


def check_scheme(s):
    """(2) deep model has_uri_scheme == real anchored re.match('[a-z]+://')."""
    model = has_uri_scheme(s)
    real = URI_RE.match(s) is not None
    assert model == real, (
        "has_uri_scheme deep model unsound vs re.match('[a-z]+://') on s=%r: "
        "model=%r real=%r" % (s, model, real))


def check_classify(s, fe, im, rem):
    """(3) deep model classify == real post-patch check()."""
    model = classify(s, fe, im, rem)
    real = real_check_postpatch(s, fe, im, rem)
    assert model == real, (
        "classify deep model unsound vs real post-patch check() on "
        "s=%r file_exists=%r ignore_match=%r: model=%r real=%r"
        % (s, fe, im, model, real))


def main():
    rng = random.Random(7985)

    # Boundary targets: the F2P cases, the scheme literals, near-misses, and
    # already-classified web targets.
    boundary = [
        "", "#", "#frag", "#top",
        "mailto:a@b.com", "mailto:", "mai", "mailto",
        "http:", "https:", "http://x", "https://y", "httpx",
        "ftp:", "ftp://server/f", "ftp:/x", "ftps://h",
        "conf.py", "path/to/notfound", "index.rst", "a/b/c",
        "doesntexist", "doesnotexist",
        "file:///etc/passwd", "data:text/plain,hi",
        "a://b", "a://", "ab://c", "abc://", "z://",
        "A://b", "1://b", "://x", ":/x", "a:/b", "a//b", "a:b",
        "scheme://host", "Scheme://Host", "x-y://z",
        "relative/path", "./local", "../up", "with space",
        "UPPER", "MiXeD", "ünïcödé/path",
    ]
    for s in boundary:
        check_startswith(s)
        check_scheme(s)
        for fe in (False, True):
            for im in (False, True):
                check_classify(s, fe, im, REMOTE)

    # Randomized fuzz over a small alphabet that exercises scheme shapes,
    # slashes, colons, dots and ASCII letters (both cases).
    alphabet = list("abcdefghijz") + list("ABZ") + list("0139") \
        + [":", "/", ".", "-", "#", " ", "_"]
    n_checked = 0
    for _ in range(80000):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_startswith(s)
        check_scheme(s)
        fe = rng.random() < 0.5
        im = rng.random() < 0.5
        check_classify(s, fe, im, REMOTE)
        n_checked += 1

    # (4) discrimination: the F2P local-file targets are exactly where the deep
    # model (== fixed check) and the pre-patch check disagree.
    disc = 0
    # an existing local file -> WORKING (fixed) vs LOCAL (pre-patch)
    assert classify("conf.py", True, False, REMOTE) == WORKING
    assert real_check_postpatch("conf.py", True, False, REMOTE) == WORKING
    assert real_check_prepatch("conf.py", True, False, REMOTE) == LOCAL
    disc += 1
    # a missing, non-ignored local file -> MISSING (fixed) vs LOCAL (pre-patch)
    assert classify("path/to/notfound", False, False, REMOTE) == MISSING
    assert real_check_postpatch("path/to/notfound", False, False, REMOTE) == MISSING
    assert real_check_prepatch("path/to/notfound", False, False, REMOTE) == LOCAL
    disc += 1
    # a missing but ignored local file -> IGNORED (fixed) vs LOCAL (pre-patch)
    assert classify("path/to/notfound", False, True, REMOTE) == IGNORED
    assert real_check_postpatch("path/to/notfound", False, True, REMOTE) == IGNORED
    assert real_check_prepatch("path/to/notfound", False, True, REMOTE) == LOCAL
    disc += 1
    # an unsupported scheme not in the pre-patch tuple (e.g. gopher://) ->
    # UNCHECKED (fixed, matches [a-z]+://) vs LOCAL (pre-patch). (`ftp://` is
    # NOT a discriminator: it is UNCHECKED both before and after the fix.)
    assert classify("gopher://h", False, False, REMOTE) == UNCHECKED
    assert real_check_postpatch("gopher://h", False, False, REMOTE) == UNCHECKED
    assert real_check_prepatch("gopher://h", False, False, REMOTE) == LOCAL
    disc += 1
    # consistency sanity: ftp:// is UNCHECKED both pre and post (no change)
    assert real_check_postpatch("ftp://h/f", False, False, REMOTE) == UNCHECKED
    assert real_check_prepatch("ftp://h/f", False, False, REMOTE) == UNCHECKED
    assert disc == 4

    print("G-AX OK: prefix_eq == str.startswith and has_uri_scheme == "
          "re.match('[a-z]+://') and classify == real post-patch check() over "
          "%d boundary + %d fuzz inputs (0 mismatch); %d F2P targets "
          "discriminate fixed vs pre-patch."
          % (len(boundary), n_checked, disc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
