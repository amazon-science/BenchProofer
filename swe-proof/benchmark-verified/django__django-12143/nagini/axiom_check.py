#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12143.

The changed behaviour (recognising a submitted key as carrying an edited row's
primary key) is modelled DEEPLY in model.py as the structural decomposition
`recognises(prefix, pkname, key)`:

    key  ==  prefix ++ '-' ++ <one or more decimal digits> ++ '-' ++ pkname

with `prefix` matched LITERALLY (code point for code point). There is no
consumed axiom; instead this deep model is an **A-reference** that must equal
the REAL post-fix compiled-pattern match

    re.compile(r'{}-\\d+-{}$'.format(re.escape(prefix), pkname)).match(key)

over the realistic domain of submitted form keys. This script executes that
real callee on boundary + randomized-fuzz inputs and asserts:

  (1) recognises(prefix, pkname, key)  ==  fixed_match(prefix, pkname, key)
      on the scoped domain (see DOMAIN SCOPING below);

  (2) the discrimination the gold fix introduces is real: on prefixes that
      contain regex metacharacters, the PRE-FIX match (prefix interpolated
      WITHOUT re.escape) disagrees with both the deep model and the fixed
      match — i.e. the deep model tracks the FIXED behaviour, not the bug.

DOMAIN SCOPING (recorded in mapping.md). The equivalence (1) is asserted over
the keys Django actually constructs and receives for list_editable formsets:

  * the digit run consists of ASCII decimal digits U+0030..U+0039 — the formset
    row index is rendered from a Python int, so it is always ASCII (whereas a
    bare `\\d` in a unicode `str` pattern would also accept other Unicode
    decimal digits; that wider acceptance is UNCHANGED by the fix and never
    exercised by real POST keys);
  * the key does not end in U+000A ('\\n') — a `$` anchor in a unicode pattern
    also matches just before a single trailing newline, but an HTTP form-field
    NAME cannot contain a raw newline; this trailing-newline tolerance is
    likewise UNCHANGED by the fix.

Both scopings are properties shared by the pre- and post-fix code and by every
real submitted key; the gold fix changes ONLY how the leading `prefix` is
interpreted, which is exactly what the deep model pins.

Imports nothing repo-specific: `re` is the Python standard library — the same
module the changed code uses. Exit 0 iff every obligation holds.
"""
import re
import random
import sys
import warnings

# The pre-fix raw-prefix compilations legitimately emit FutureWarning (e.g.
# "possible nested set") for prefixes that read as regex syntax — that noise IS
# the bug. Silence it so this check's own output stays clean; the fixed match
# (re.escape) never triggers it.
warnings.filterwarnings("ignore", category=FutureWarning)

DIGITS = "0123456789"


def recognises(prefix, pkname, key):
    """Reference implementation of model.py's deep model `recognises`
    (the literal structural decomposition), over Python ``str``."""
    np_, nk, n = len(prefix), len(pkname), len(key)
    d = n - np_ - nk - 2
    if d < 1:
        return False
    return (
        key[:np_] == prefix
        and key[np_] == '-'
        and all('0' <= c <= '9' for c in key[np_ + 1:np_ + 1 + d])
        and key[np_ + 1 + d] == '-'
        and key[np_ + 2 + d:] == pkname
    )


def fixed_match(prefix, pkname, key):
    """The REAL post-fix compiled-pattern match (gold patch: re.escape)."""
    pat = re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname))
    return pat.match(key) is not None


def buggy_match(prefix, pkname, key):
    """The PRE-FIX compiled-pattern match (prefix interpolated raw). The raw
    interpolation can also raise re.error for a prefix that is not itself a
    valid regex (part of the bug's harm); we surface that as the sentinel
    string 'RAISES', which by definition differs from the never-raising fixed
    match."""
    try:
        pat = re.compile(r'{}-\d+-{}$'.format(prefix, pkname))
    except re.error:
        return 'RAISES'
    return pat.match(key) is not None


def in_scope(key):
    """The scoped realistic-POST-key domain: no trailing newline."""
    return not key.endswith('\n')


def check_reference(prefix, pkname, key):
    """(1) deep model == real fixed match on the scoped domain."""
    if not in_scope(key):
        return
    model = recognises(prefix, pkname, key)
    real = fixed_match(prefix, pkname, key)
    assert model == real, (
        "deep model `recognises` unsound vs real fixed match on "
        "prefix=%r pkname=%r key=%r: model=%r real=%r"
        % (prefix, pkname, key, model, real))


# ---------------------------------------------------------------------------

PK_NAMES = ["uuid", "id", "pk", "code", "objectid"]
META = list("$.^*+?()[]{}|\\")          # regex metacharacters
PLAIN = list("formAZxy_") + list("09")


def build_matching_key(prefix, pkname, d):
    """A key that the FIXED pattern recognises: prefix-<d digits>-pkname."""
    digits = "".join(random.choice(DIGITS) for _ in range(d))
    return "%s-%s-%s" % (prefix, digits, pkname)


def main():
    rng = random.Random(12143)
    random.seed(12143)

    boundary_prefixes = [
        "", "form", "form$", "a.b", "a+b", "a*b", "x|y", "a(b)c",
        "[set]", "{n}", "q?", "^anchor", "back\\slash", "form$$",
        "$", ".", "+", "*", "form-", "fo-rm",
    ]
    boundary_pknames = ["uuid", "id", "pk"]

    discriminating = 0
    checked = 0

    # --- boundary: for each prefix, build the literally-matching key and a
    #     handful of structurally-near misses; assert (1) on all of them. -----
    for prefix in boundary_prefixes:
        for pkname in boundary_pknames:
            keys = [
                build_matching_key(prefix, pkname, 1),
                build_matching_key(prefix, pkname, 2),
                build_matching_key(prefix, pkname, 5),
                "%s-%s" % (prefix, pkname),                 # no digit region
                "%s--%s" % (prefix, pkname),                # empty digit run
                "%s-0-%sX" % (prefix, pkname),              # trailing junk
                "x%s-0-%s" % (prefix, pkname),              # leading junk
                "%s-0a-%s" % (prefix, pkname),              # non-digit in run
                "%s-0-%s" % (prefix, pkname[:-1]) if pkname else pkname,
            ]
            for key in keys:
                check_reference(prefix, pkname, key)
                checked += 1
                if in_scope(key) and fixed_match(prefix, pkname, key) != \
                        buggy_match(prefix, pkname, key):
                    discriminating += 1

    # --- the exact F2P discriminating case --------------------------------
    assert recognises("form$", "uuid", "form$-0-uuid") is True
    assert fixed_match("form$", "uuid", "form$-0-uuid") is True
    assert buggy_match("form$", "uuid", "form$-0-uuid") is False, (
        "expected the pre-fix raw-prefix match to FAIL on the F2P case")

    # --- randomized fuzz: random prefixes (incl. metacharacters), pknames,
    #     and keys (both built-to-match and arbitrary), assert (1). ----------
    alphabet = PLAIN + META + ["-"]
    for _ in range(60000):
        plen = rng.randint(0, 6)
        prefix = "".join(rng.choice(alphabet) for _ in range(plen))
        pkname = rng.choice(PK_NAMES)
        roll = rng.random()
        if roll < 0.5:
            # a key built to (usually) match the FIXED pattern
            d = rng.randint(1, 4)
            key = build_matching_key(prefix, pkname, d)
        else:
            # an arbitrary key over a small alphabet
            klen = rng.randint(0, 18)
            key = "".join(rng.choice(alphabet + list(DIGITS))
                          for _ in range(klen))
        check_reference(prefix, pkname, key)
        checked += 1
        if in_scope(key) and \
                fixed_match(prefix, pkname, key) != buggy_match(prefix, pkname, key):
            discriminating += 1

    assert discriminating > 0, (
        "no discriminating input found — the fix would be a no-op")

    print("G-AX OK: deep model `recognises` == real re.escape-fixed pattern "
          "match over %d scoped boundary+fuzz inputs (0 mismatch); "
          "%d inputs discriminate fixed vs pre-fix (incl. the F2P "
          "prefix='form$' case)." % (checked, discriminating))
    return 0


if __name__ == "__main__":
    sys.exit(main())
