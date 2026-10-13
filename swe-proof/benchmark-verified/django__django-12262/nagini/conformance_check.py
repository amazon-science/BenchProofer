#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12262 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped and PSeq realized as an
immutable tuple shim. The @Pure helpers `contains` / `acceptable` copy over as
plain functions (`outcome` lives only in contracts and is not needed by the
impl). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.template.library.parse_bits`, driven through its keyword-handling
branch. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2): integer parameter-name codes map to
distinct identifier strings ("p<code>"); the supplied-keyword run maps to a
token list of "name=value" bits (each one the successfully-extracted-keyword
case); the declared positional / keyword-only name sets map to the `params` /
`kwonly` arguments; the defaulted keyword-only subset maps to the
`kwonly_defaults` dict; `catch_all` maps to a non-None `varkw`. The oracle's
outcome code is read off its control flow: the raise whose message reports an
unexpected keyword -> 1, the raise whose message reports multiple values for
a keyword -> 2, and completion of the keyword scan -> 0. A post-scan raise
about arguments that were never supplied is OUTSIDE the modeled decision
(mapping.md section 3: the scan itself completed problem-free), so it also
reads as 0.

Input domain: Requires demands read permission on the supplied run plus the
well-formedness that every defaulted keyword-only name is a keyword-only name
(true of every real signature); generation enforces exactly that, drawing
params/kwonly as disjoint name sets (as in a real signature) with defaults a
subset of kwonly. Supplied runs are arbitrary (declared and undeclared names,
with repeats).

>= 1e5 Requires-satisfying inputs: boundary cases + exhaustive small
enumeration + 100000 fuzz tuples. Pinned fuzz seed: 12262.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib-only.
"""
import itertools
import random
import sys

SEED = 12262
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
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


# --- pure helpers from model.py, contracts stripped ---------------------------

def contains(s, x):
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


def acceptable(positional, keyword_only, catch_all, name):
    return catch_all or contains(positional, name) or contains(keyword_only, name)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def bind_keywords(supplied, positional, keyword_only, keyword_only_with_default,
                  catch_all):
    seen = PSeq(0).take(0)  # type: PSeq
    i = 0
    while i < len(supplied):
        name = supplied[i]
        if not acceptable(positional, keyword_only, catch_all, name):
            return 1
        if contains(seen, name):
            return 2
        seen = seen + PSeq(name)
        i = i + 1
    return 0


# --- bridge: int codes <-> parameter-name strings, outcome <-> control flow ---

def name_of(code):
    return "p%d" % code


def real_outcome(parse_bits, TemplateSyntaxError, parser,
                 supplied, params, kwonly, defaults, catch_all):
    """Outcome code of the real keyword scan: drive parse_bits with a run of
    keyword bits and classify its control-flow result per mapping.md."""
    bits = ["%s=%d" % (name_of(c), i + 1) for i, c in enumerate(supplied)]
    kwonly_defaults = {name_of(c): None for c in defaults} or None
    varkw = "extra" if catch_all else None
    try:
        parse_bits(parser, bits,
                   [name_of(c) for c in params],   # positional params
                   None,                            # no *args
                   varkw,                           # **catch-all or None
                   None,                            # no positional defaults
                   [name_of(c) for c in kwonly],    # keyword-only params
                   kwonly_defaults,
                   False,                           # takes_context
                   "tagname")
    except TemplateSyntaxError as e:
        msg = str(e)
        if "unexpected keyword argument" in msg:
            return 1
        if "multiple values for keyword argument" in msg:
            return 2
        # any other raise fires only after the keyword scan finished without
        # flagging a keyword (e.g. a declared argument was never supplied);
        # that is outside the modeled decision -> the scan outcome is OK.
        return 0
    return 0


def check_one(ctx, supplied, params, kwonly, defaults, catch_all):
    """Run shadow and oracle on one input tuple; return an error string on
    disagreement, else None."""
    parse_bits, TemplateSyntaxError, parser = ctx
    # Requires well-formedness: defaults is a sub-collection of kwonly
    assert all(d in kwonly for d in defaults)
    shadow = bind_keywords(list(supplied),
                           PSeq(*params), PSeq(*kwonly), PSeq(*defaults),
                           catch_all)
    real = real_outcome(parse_bits, TemplateSyntaxError, parser,
                        supplied, params, kwonly, defaults, catch_all)
    if shadow != real:
        return ("DISAGREEMENT\n  supplied=%r params=%r kwonly=%r defaults=%r "
                "catch_all=%r\n  shadow=%r real=%r"
                % (list(supplied), list(params), list(kwonly), list(defaults),
                   catch_all, shadow, real))
    return None


def boundary_cases():
    # (supplied, params, kwonly, defaults, catch_all)
    return [
        # a defaulted keyword-only name supplied once must be OK
        ([1], [], [1], [1], False),
        # a keyword-only name supplied twice must be DUPLICATE, not UNEXPECTED
        ([1, 1], [], [1], [], False),
        ([1, 1], [], [1], [1], False),
        # empty run
        ([], [], [], [], False),
        ([], [], [], [], True),
        # positional name supplied as keyword; twice -> DUPLICATE
        ([1], [1], [], [], False),
        ([1, 1], [1], [], [], False),
        # undeclared name: UNEXPECTED without catch-all, OK with it
        ([9], [], [], [], False),
        ([9], [], [], [], True),
        ([9, 9], [], [], [], True),   # catch-all name repeated -> DUPLICATE
        # mixed defaulted / non-defaulted keyword-only names
        ([1, 2], [], [1, 2], [2], False),
        ([2, 2], [], [1, 2], [2], False),
        # first problematic keyword wins, in both orders
        ([1, 9, 1], [], [1], [], False),
        ([1, 1, 9], [], [1], [], False),
        ([9, 1, 1], [], [1], [], False),
    ]


def _subsets(xs):
    for r in range(0, len(xs) + 1):
        for c in itertools.combinations(xs, r):
            yield list(c)


def _rand_subset(rng, xs):
    return [x for x in xs if rng.random() < 0.5]


def main():
    from django.template.library import parse_bits          # REAL patched fn
    from django.template.base import Parser
    from django.template.exceptions import TemplateSyntaxError
    parser = Parser([])   # value expressions are numeric literals: no engine,
                          # no filters, no settings access needed
    ctx = (parse_bits, TemplateSyntaxError, parser)

    checked = 0
    n_boundary = 0
    for supplied, params, kwonly, defaults, catch_all in boundary_cases():
        err = check_one(ctx, supplied, params, kwonly, defaults, catch_all)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # exhaustive small enumeration: signatures over names {1,2,3}, supplied
    # runs of length 0-3 over {0,1,2,3,9} (0/9 never declared)
    n_enum = 0
    names = [1, 2, 3]
    name_universe = [0, 1, 2, 3, 9]
    for params in _subsets(names):
        for kwonly in _subsets([n for n in names if n not in params]):
            for defaults in _subsets(kwonly):
                for catch_all in (False, True):
                    for length in range(0, 4):
                        for supplied in itertools.product(name_universe,
                                                          repeat=length):
                            err = check_one(ctx, list(supplied), params,
                                            kwonly, defaults, catch_all)
                            if err:
                                print(err)
                                return 1
                            checked += 1
                            n_enum += 1

    # randomized fuzz, pinned seed
    rng = random.Random(SEED)
    universe = list(range(0, 8))
    for _ in range(N_FUZZ):
        params = _rand_subset(rng, universe)
        rest = [n for n in universe if n not in params]
        kwonly = _rand_subset(rng, rest)
        defaults = _rand_subset(rng, kwonly)
        catch_all = rng.random() < 0.5
        n = rng.randint(0, 8)
        supplied = [rng.choice(universe) for _ in range(n)]
        err = check_one(ctx, supplied, params, kwonly, defaults, catch_all)
        if err:
            print(err)
            return 1
        checked += 1

    import json
    print("G-CONF OK: shadow impl == real keyword-binding decision on %d "
          "inputs (%d boundary + %d enumerated + %d fuzz, seed %d)."
          % (checked, n_boundary, n_enum, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
