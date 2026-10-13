#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7671 (nagini).

SHADOW: the impl region of model.py's `version_meets_minimum`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped and
PSeq realized as an immutable tuple shim (`ToSeq` materializes a list into the
shim). The @Pure helpers `is_numeric` / `normalize` / `loose_ge` / `loose_gt`
copy over verbatim as plain recursive functions. There are no @ContractOnly
callees in this bundle (its axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md —
`astropy.utils.introspection.minversion`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched module
importable. The unchanged input-acquisition prologue (module / version_path
resolution) is exercised through its simplest concrete vector: a synthetic
`types.ModuleType` carrying `__version__` — exactly how the repo's own test
suite drives the function — so the oracle call covers the full changed tail of
the real function.

TYPE BRIDGE (mapping.md section 2): a version string maps to the model carrier
`List[int]` of parsed release segments via `encode()` below — the leading
dotted-numeric run becomes its integer components; if a non-numeric qualifier
tail remains, a single sentinel -1 is appended (the model only tracks THAT a
qualifier tail exists). Fuzz inputs are generated as canonical segment strings
(no leading zeros, no epoch), so `encode` is total and exact on them.

INPUT DOMAIN (the Requires region): the installed version `have` is a plain
numeric version (is_numeric carrier), and the requested version `want` begins
with a numeric release segment (len > 0 and first segment >= 0). Both
inclusive and strict comparisons are checked for every pair.

>= 1e5 Requires-satisfying inputs: boundary cases + 60000 fuzz pairs, each
checked at inclusive=True and inclusive=False (>= 120000 checks total).
Pinned fuzz seed: 7671.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (Python 3.6 compatible for the pinned
instance image).
"""
import json
import random
import re
import sys
import types

SEED = 7671
N_FUZZ_PAIRS = 60000

QUALIFIER = -1   # model.py sentinel: start of the non-numeric qualifier tail

# The leading dotted-release-number prefix grammar (used only to realize the
# documented string <-> List[int] bijection of mapping.md section 2).
EXPR = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'


# --- PSeq shim: immutable sequence, the operations the model regions use -----

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    """Materialize a plain list into the pure-sequence shim."""
    return PSeq._wrap(xs)


# --- pure region of model.py, verbatim, decorators stripped -------------------

def is_numeric(s):
    if len(s) == 0:
        return True
    return s[0] >= 0 and is_numeric(s.drop(1))


def normalize(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    if s[0] < 0:
        return PSeq(0).take(0)
    return PSeq(s[0]) + normalize(s.drop(1))


def loose_ge(a, b):
    if len(a) == 0 and len(b) == 0:
        return True
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_ge(a.drop(1), b.drop(1))


def loose_gt(a, b):
    if len(a) == 0 and len(b) == 0:
        return False
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_gt(a.drop(1), b.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def version_meets_minimum(have, want, inclusive):
    norm = []  # type: list
    i = len(want)
    while i > 0:
        c = want[i - 1]
        if c < 0:
            norm = []  # qualifier marker: discard the tail accumulated so far
        else:
            norm = [c] + norm
        i = i - 1
    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(norm))
    else:
        return loose_gt(ToSeq(have), ToSeq(norm))


# --- bridge: version string -> model carrier (mapping.md section 2) -----------

class Unencodable(Exception):
    """Version label outside the model carrier's domain (epoch form)."""


def encode(version):
    """The documented bijection: leading dotted-numeric run -> int components,
    a single QUALIFIER (-1) sentinel appended iff a non-numeric tail remains.
    Raises Unencodable for epoch labels, which the carrier does not represent
    (they are outside the generated input domain anyway)."""
    m = re.match(EXPR, version)
    prefix = m.group(0) if m else ""
    if '!' in prefix:
        raise Unencodable("epoch version %r outside model carrier domain"
                          % version)
    comps = [int(x) for x in prefix.split('.')] if prefix else []
    if prefix != version:
        comps = comps + [QUALIFIER]
    return comps


def in_domain(have_c, want_c):
    """The Requires region: have is a plain numeric carrier; want begins with
    a numeric release segment."""
    if any(c < 0 for c in have_c):
        return False
    return len(want_c) > 0 and want_c[0] >= 0


# --- oracle plumbing -----------------------------------------------------------

_mod = types.ModuleType(str("conf_probe_module"))


def real_result(minversion, have_str, want_str, inclusive):
    """Call the REAL patched repo function with the installed version supplied
    through a synthetic module's __version__ (the repo test suite's own call
    vector). Returns the bool, or an 'exception' tag string if it raises."""
    _mod.__version__ = have_str
    try:
        return bool(minversion(_mod, want_str, inclusive))
    except Exception as e:
        return "raised %s: %s" % (type(e).__name__, e)


def check_one(minversion, have_str, want_str, inclusive):
    """Run shadow and oracle on one (have, want, inclusive) triple; return an
    error string on disagreement, else None."""
    have_c = encode(have_str)
    want_c = encode(want_str)
    assert in_domain(have_c, want_c), (
        "generator bug: (%r, %r) outside the Requires domain"
        % (have_str, want_str))
    shadow = version_meets_minimum(have_c, want_c, inclusive)
    real = real_result(minversion, have_str, want_str, inclusive)
    if shadow != real:
        return ("DISAGREEMENT\n  have=%r (carrier %r)\n  want=%r (carrier %r)\n"
                "  inclusive=%s\n  shadow=%r\n  real=%r"
                % (have_str, have_c, want_str, want_c, inclusive, shadow, real))
    return None


# --- input generation -----------------------------------------------------------

def boundary_cases():
    """Boundary (have, want) pairs, all inside the Requires domain. Includes
    the repo test suite's installed/requested version constellation plus
    prefix/extension/qualifier-tail edges."""
    haves = ["0.12.2", "0", "1", "0.12", "0.12.0", "1.14.3", "2.0.0",
             "10.0", "0.0.1", "3.6.0", "1.0"]
    wants = ["0.12", "0.12.1", "0.12.0.dev", "0.12dev",   # test-suite good set
             "1", "1.2rc1",                                # test-suite bad set
             "0.12.2", "0.12.2.dev", "0.12.3", "0.11",
             "0", "0dev", "0.0", "10.0", "9.9", "1.14dev",
             "2.0.0.rc1", "1.0a1", "2.1.0.post1", "3.6.0rc2",
             "0.12.2.0", "0.12.2.0.dev"]
    return [(h, w) for h in haves for w in wants]


QUAL_TAILS = ["", "", "", "dev", "rc1", "rc2", "a1", "b2", ".dev", ".dev0",
              "post1", ".post0", "c1", "alpha", "beta"]


def rand_numeric(rng, max_segs=4, hi=99):
    n = rng.randint(1, max_segs)
    segs = []
    for _ in range(n):
        if rng.random() < 0.3:
            segs.append("0")
        else:
            segs.append(str(rng.randint(1, hi)))
    return ".".join(segs)


def main():
    # the REAL patched callee (PYTHONPATH=/testbed, gold patch applied by gate)
    from astropy.utils.introspection import minversion

    checked = 0
    n_boundary = 0
    for have_str, want_str in boundary_cases():
        for inclusive in (True, False):
            err = check_one(minversion, have_str, want_str, inclusive)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ_PAIRS):
        have_str = rand_numeric(rng)
        # a requested label: numeric head (canonical segments) + optional
        # non-numeric qualifier tail; always inside the Requires domain
        want_str = rand_numeric(rng) + rng.choice(QUAL_TAILS)
        for inclusive in (True, False):
            err = check_one(minversion, have_str, want_str, inclusive)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real patched version-requirement check "
          "on %d checks (%d boundary + %d fuzz pairs x inclusive/strict, "
          "seed %d)." % (checked, n_boundary, N_FUZZ_PAIRS, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
