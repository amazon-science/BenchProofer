#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13112 (nagini).

SHADOW: the impl region of ``model.py``, copied verbatim below with the
contract calls (Requires/Ensures/Invariant/Assert) stripped.  The @Pure
helpers ``lower_cp`` / ``first_dot`` / ``normfold`` / ``keep_count`` /
``normalized`` copy over as plain functions on top of a small immutable-tuple
PSeq shim; ``normalized`` additionally serves as an internal cross-check of
the executable loop.  There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md
section 1 — the value assigned to ``kwargs['to']`` by
``django.db.models.fields.related.ForeignObject.deconstruct`` when
``remote_field.model`` is a string (a lazy model reference).  It is observed
through ``django.db.models.ForeignKey``, a concrete ForeignObject subclass
whose ``deconstruct`` chains through that branch and does not modify
``kwargs['to']`` afterwards.  The gate applies patch.diff to /testbed before
this script runs and sets PYTHONPATH=/testbed, so the import resolves the
patched in-tree source.  Settings are configured with an empty app registry,
so no swappable-model substitution can shadow the observed value; ``str()``
is applied defensively anyway.

Type bridge (mapping.md section 2): the reference is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord``, a bijection, so
generation happens over ``str`` and is lowered per call; the shadow's output
list is raised back to ``str`` via ``chr`` for the comparison.

Input domain (mapping.md section 3): a lazy model reference is either a bare
model name (no dot) or a qualified name with EXACTLY ONE dot — the only
shapes the repo produces and the only shapes the patched tuple-unpack
accepts — over the ASCII identifier alphabet (letters/digits/underscore),
plus the empty/degenerate boundary shapes.  Every such input satisfies the
model's Requires (a readable list of code points).

>= 1e5 Requires-satisfying inputs: 26 boundary cases + 120000 fuzz strings
(60000 bare + 60000 single-dot).  Pinned fuzz seed: 131120.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib only (no f-strings: container Python may be old).
"""
import random
import sys

SEED = 131120
N_FUZZ_BARE = 60000
N_FUZZ_DOTTED = 60000


# --- PSeq shim: immutable sequence with the operations the pure region uses --

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @Pure helpers from model.py, verbatim, contracts stripped ---------------

def lower_cp(c):
    if 65 <= c and c <= 90:
        return c + 32
    return c


def first_dot(s):
    if len(s) == 0:
        return 0
    if s[0] == 46:
        return 0
    return 1 + first_dot(s.drop(1))


def normfold(s, keep):
    if len(s) == 0:
        return PSeq(0).take(0)
    if keep > 0:
        return PSeq(s[0]) + normfold(s.drop(1), keep - 1)
    return PSeq(lower_cp(s[0])) + normfold(s.drop(1), 0)


def keep_count(s):
    if first_dot(s) < len(s):
        return first_dot(s)
    return 0


def normalized(s):
    return normfold(s, keep_count(s))


# --- impl region of model.py, verbatim, contract calls stripped --------------

def normalize_reference(text):
    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: list
    i = len(text)
    while i > 0:
        c = text[i - 1]
        # (stripped Assert lines carried only proof-side sequence facts)
        if i - 1 < keep:
            result = [c] + result
        else:
            result = [lower_cp(c)] + result
        i = i - 1
    return result


# --- oracle: the real patched deconstruct, observed via ForeignKey -----------

def make_oracle():
    """Configure a minimal settings module (empty app registry) and return a
    callable str -> str: the kwargs['to'] value the patched deconstruct
    computes for a string-valued remote_field.model."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()
    from django.db import models

    def oracle(ref):
        # swappable=False keeps deconstruct from substituting a settings
        # reference for the computed value (a separate, unmodeled mechanism);
        # with an empty app registry that substitution is inert anyway.
        field = models.ForeignKey(ref, models.CASCADE, swappable=False)
        _name, _path, _args, kwargs = field.deconstruct()
        return str(kwargs['to'])

    return oracle


# --- differential driver ------------------------------------------------------

def check(oracle, ref):
    """Run shadow and oracle on one reference string; return an error string
    on disagreement, else None."""
    text = [ord(ch) for ch in ref]            # bridge: str -> List[int]
    shadow_cps = normalize_reference(text)
    shadow = "".join(chr(c) for c in shadow_cps)
    real = oracle(ref)
    if shadow != real:
        return ("DISAGREEMENT on reference %r (code points %r):\n"
                "  shadow (impl region)            = %r (code points %r)\n"
                "  real (patched deconstruct 'to') = %r"
                % (ref, text, shadow, shadow_cps, real))
    # internal cross-check: the executable loop agrees with the pure spec fold
    if ToSeq(shadow_cps) != normalized(ToSeq(text)):
        return ("INTERNAL: impl region and pure fold disagree on %r" % ref)
    return None


def boundary_cases():
    return [
        "",                       # empty
        "a", "Z", "_", "0",       # single chars
        "Author", "AUTHOR", "author",
        "MiXedCase_migrations",   # mixed-case label, bare
        "MiXedCase_migrations.author",
        "MiXedCase_migrations.Author",
        "MiXedCase_migrations.AUTHOR",
        "MiXedCase_migrations.book",
        "MiXedCase_migrations.magazine",
        "DJ_RegLogin.Category",
        "DJ_RegLogin.Content",
        "app.MyModel",
        "App.model",
        "MyApp.MyModel",
        ".",                      # dot only: both halves empty
        "A.",                     # empty right half
        ".B",                     # empty left half
        "lowerapp.UPPERMODEL",
        "UPPERAPP.lowermodel",
        "auth.User",
        "contenttypes.ContentType",
    ]


def main():
    oracle = make_oracle()

    # ASCII identifier alphabet (the in-domain character set).
    ident_chars = ([chr(c) for c in range(ord('A'), ord('Z') + 1)]
                   + [chr(c) for c in range(ord('a'), ord('z') + 1)]
                   + [chr(c) for c in range(ord('0'), ord('9') + 1)]
                   + ['_'])

    n_checked = 0

    def run_one(ref):
        err = check(oracle, ref)
        if err is not None:
            print(err)
            sys.exit(1)

    boundary = boundary_cases()
    for ref in boundary:
        run_one(ref)
        n_checked += 1

    rng = random.Random(SEED)

    # fuzz: bare names (no dot)
    for _ in range(N_FUZZ_BARE):
        n = rng.randint(0, 18)
        run_one("".join(rng.choice(ident_chars) for _ in range(n)))
        n_checked += 1

    # fuzz: exactly one dot (label.name)
    for _ in range(N_FUZZ_DOTTED):
        a = rng.randint(0, 12)
        b = rng.randint(0, 12)
        left = "".join(rng.choice(ident_chars) for _ in range(a))
        right = "".join(rng.choice(ident_chars) for _ in range(b))
        run_one(left + "." + right)
        n_checked += 1

    print("G-CONF OK: shadow (impl region) == real patched deconstruct "
          "kwargs['to'] on %d inputs (%d boundary + %d fuzz, seed %d); "
          "zero disagreements." % (n_checked, len(boundary),
                                   N_FUZZ_BARE + N_FUZZ_DOTTED, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
