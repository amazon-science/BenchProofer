#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5631 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
`counts_as_mock` / `count_sentinel_directives` copy over as plain functions;
PSeq is realized as an immutable tuple shim (only `drop`/indexing/len are
used) and ToSeq as the List -> shim lift. There are no @ContractOnly callees
in this bundle (the membership decision is modelled deeply).

ORACLE: the REAL patched repo function the model models per mapping.md —
`_pytest.compat.num_mock_patch_args`, imported from the patched /testbed
(the gate applies patch.diff before this script runs; PYTHONPATH=/testbed).
It is called with a carrier object whose recorded replacement directives are
real objects exposing the two attributes the helper reads: the bound
attribute name and the replacement value.

Type bridge (mapping.md section 2): each directive maps to one integer kind
tag in {0,1,2,3}. The tag is computed from the real directive by the same
observables the model abstracts:
  0 — binds an attribute name (value not inspected)
  1 — no attribute name; value IS a placeholder singleton by identity
  2 — no attribute name; comparable non-placeholder value
  3 — no attribute name; value whose equality is not truth-evaluable
The placeholder singletons used are exactly the ones the patched helper
consults at call time (the loaded mock modules' DEFAULT placeholder objects),
discovered here through the same module-registry lookups, so identity is
judged against the very same objects on both sides. Directive populations
include values whose equality raises (the non-truth-evaluable case): the
oracle must return a count for them — totality is part of the diff.

>= 1e5 Requires-satisfying inputs: boundary populations + 110000 fuzz
populations. Pinned fuzz seed: 5631.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; unittest.mock is the stdlib module
whose placeholder singleton the helper consults).
"""
import json
import random
import sys
import unittest.mock

SEED = 5631
N_FUZZ = 110_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- pure helpers from model.py, contracts stripped ---------------------------

def counts_as_mock(kind):
    return kind == 1


def count_sentinel_directives(s):
    if len(s) == 0:
        return 0
    return (1 if counts_as_mock(s[0]) else 0) + count_sentinel_directives(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def count_mock_patch_args(kinds):
    count = 0
    i = len(kinds)
    while i > 0:
        c = kinds[i - 1]
        # Total identity decision: kind 1 (identity match, no attribute name)
        # counts; every other kind — including kind 3 (non-truth-evaluable
        # equality) — does not, and is handled without failure.
        if counts_as_mock(c):
            count = count + 1
        i = i - 1
    return count


# --- bridge: real directive objects <-> kind tags ------------------------------

class Directive:
    """A real replacement directive exposing the only two attributes the
    helper reads: the bound attribute name and the replacement value."""

    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new


class Carrier:
    """Callable stand-in carrying its recorded directives the way the repo
    helper looks them up."""

    def __init__(self, patchings):
        self.patchings = patchings


class NonTruthEvaluable:
    """A replacement value whose equality comparison does not yield a usable
    boolean (comparing it raises). Identity comparison remains total on it."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        raise ValueError("truth value of this comparison is ambiguous")

    __hash__ = None


def placeholder_singletons():
    """The placeholder singletons the patched helper consults at call time:
    the DEFAULT attribute of whichever mock modules are loaded. Discovered by
    the same module-registry lookups, so both sides judge identity against
    the very same objects."""
    out = []
    for name in ("mock", "unittest.mock"):
        m = sys.modules.get(name)
        d = getattr(m, "DEFAULT", None)
        if m is not None and d is not None:
            out.append(d)
    return out


def real_kind(d, sentinels):
    """The kind tag the model assigns to a real directive (mapping.md sec 2),
    computed by the total identity decision plus an equality-usability probe
    (the probe only labels the population; it is not the counted decision)."""
    if d.attribute_name:
        return 0
    if any(d.new is s for s in sentinels):
        return 1
    try:
        bool(d.new == object())
        return 2
    except Exception:
        return 3


def check_population(oracle, directives, sentinels):
    kinds = [real_kind(d, sentinels) for d in directives]
    assert all(0 <= k <= 3 for k in kinds)   # Requires holds

    shadow_n = count_mock_patch_args(list(kinds))
    # the pure fold agrees with the loop by construction; keep both honest
    fold_n = count_sentinel_directives(ToSeq(kinds))

    try:
        real_n = oracle(Carrier(list(directives)))
    except Exception as e:                       # totality is part of the diff
        return ("DISAGREEMENT (oracle raised)\n  kinds=%r\n  shadow=%r\n"
                "  real raised: %r" % (kinds, shadow_n, e))

    if shadow_n != real_n or fold_n != real_n:
        return ("DISAGREEMENT\n  kinds=%r\n  shadow=%r fold=%r\n  real=%r"
                % (kinds, shadow_n, fold_n, real_n))
    if not (0 <= shadow_n <= len(kinds)):
        return "DISAGREEMENT (range)\n  kinds=%r\n  shadow=%r" % (kinds, shadow_n)
    return None


def boundary_populations(sentinels):
    s0 = sentinels[0]
    nt = NonTruthEvaluable(50)
    pops = [
        [],
        [Directive(None, s0)],
        [Directive("name", s0)],
        [Directive(None, nt)],
        [Directive(None, object())],
        [Directive("", s0)],                       # empty name binds nothing
        [Directive(None, s0), Directive(None, NonTruthEvaluable(1))],
        [Directive("a", s0), Directive(None, s0),
         Directive(None, NonTruthEvaluable(2)), Directive(None, 5)],
        [Directive(None, s) for s in sentinels],   # every loaded placeholder
        [Directive(None, s0)] * 8,
    ]
    return pops


def sample_value(rng, sentinels):
    r = rng.random()
    if r < 0.30:
        return rng.choice(sentinels)                      # kind 1 candidate
    if r < 0.60:
        return NonTruthEvaluable(rng.randint(0, 100))     # kind 3
    if r < 0.80:
        return object()                                   # kind 2
    return rng.choice([0, 1, "x", (1, 2), None, 3.5])    # kind 2


def main():
    sys.path.insert(0, "/testbed/src")
    from _pytest.compat import num_mock_patch_args   # REAL patched callee

    sentinels = placeholder_singletons()
    assert sentinels, "no placeholder singleton loaded"

    checked = 0
    boundary = boundary_populations(sentinels)
    for pop in boundary:
        err = check_population(num_mock_patch_args, pop, sentinels)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 8)
        pop = []
        for _ in range(n):
            attr = None if rng.random() < 0.7 else "attr%d" % rng.randint(0, 3)
            pop.append(Directive(attr, sample_value(rng, sentinels)))
        err = check_population(num_mock_patch_args, pop, sentinels)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched helper on %d populations "
          "(%d boundary + %d fuzz, seed %d), including non-truth-evaluable "
          "replacement values (totality checked)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
