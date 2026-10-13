#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-10356 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (Requires/Ensures/Invariant/Assert removed; nothing else
changed), plus the @Pure helper `concat_chain` copied over as a plain
function. `PSeq` is shimmed as a thin immutable-tuple wrapper providing the
exact operations the model uses (len, indexing, `+`, `.take`, `.drop`, `==`).
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`_pytest.mark.structures.get_unpacked_marks(obj, *, consider_mro)`. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched package importable (same import the bundle's axiom_check.py
uses).

Type bridge (mapping.md section 2): a class `obj` maps to the chain
`PSeq[PSeq[int]]` of its linearisation members' own directly-attached mark
lists — `chain[k]` is `obj.__mro__[k].__dict__.get("pytestmark", [])`,
normalised the same way the real code normalises it, with each mark
identified by its name and each distinct name assigned a distinct int token.
`consider_chain` maps to `consider_mro`. The oracle output (a list of Mark
objects) is rendered through the same name->token map for comparison; order
and multiplicity are compared exactly. Classes are built through the real
decorator path (`pytest.mark.<name>(cls)`), so each class's own dict list is
produced exactly as the repo produces it.

Input domain: the model's precondition is len(chain) >= 1, which every real
class satisfies (its linearisation always contains the class itself). Both
flag values are exercised for every class, and each (class, flag) pair is one
Requires-satisfying input. Boundary cases: the discriminating two-ancestor
shape, single/undecorated/linear/diamond/multi-mark/mixed-empty hierarchies.
Fuzz: randomised class DAGs with random per-class own-mark multisets (names
may repeat within and across classes), sized so total checks >= 1e5.

Pinned fuzz seed: 103560 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input chain, the
flag, and both outputs, then exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 103560
TARGET_CHECKS = 100_000


# --- PSeq shim: immutable tuple wrapper with the ops the model uses -----------

class PSeq:
    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, tup):
        s = cls()
        s._t = tuple(tup)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __repr__(self):
        return "PSeq%r" % (self._t,)


# --- @Pure helper from model.py, decorator stripped ---------------------------

def concat_chain(chain):
    if len(chain) == 0:
        return PSeq(0).take(0)
    return chain[0] + concat_chain(chain.drop(1))


# --- the impl region of model.py, verbatim, contracts stripped ----------------

def unpacked_tokens(chain, consider_chain):
    if not consider_chain:
        return chain[0]
    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
    # is empty, and concat_chain of the empty chain is the empty sequence).
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        result = chain[i - 1] + result
        i = i - 1
    return result


# --- oracle bridge --------------------------------------------------------------

class TokenMap:
    """Distinct mark name <-> distinct int token (assigned on first sight)."""

    def __init__(self):
        self._m = {}

    def tok(self, name):
        if name not in self._m:
            self._m[name] = len(self._m)
        return self._m[name]


def main():
    import pytest
    from _pytest.mark.structures import get_unpacked_marks, normalize_mark_list

    tokens = TokenMap()

    def own_tokens(cls):
        """chain[k]: the marks directly attached to `cls` (its own dict list,
        normalised the way the real code normalises), as int tokens."""
        raw = cls.__dict__.get("pytestmark", [])
        if not isinstance(raw, list):
            raw = [raw]
        return [tokens.tok(m.name) for m in normalize_mark_list(raw)]

    def chain_of(cls):
        return PSeq._wrap(tuple(PSeq._wrap(tuple(own_tokens(m)))
                                for m in cls.__mro__))

    def real_tokens(cls, flag):
        return [tokens.tok(m.name)
                for m in get_unpacked_marks(cls, consider_mro=flag)]

    def make_class(name, bases, mark_names):
        cls = type(name, tuple(bases), {})
        for mn in mark_names:
            cls = getattr(pytest.mark, mn)(cls)
        return cls

    checked = 0

    def check(cls, label):
        nonlocal checked
        chain = chain_of(cls)
        assert len(chain) >= 1  # precondition of the model (always holds)
        for flag in (True, False):
            shadow = list(unpacked_tokens(chain, flag)._t)
            real = real_tokens(cls, flag)
            if shadow != real:
                print("DISAGREEMENT on %s (consider_chain=%r)\n"
                      "  chain=%r\n  shadow=%r\n  real=%r"
                      % (label, flag, chain, shadow, real))
                sys.exit(1)
            checked += 1

    # --- boundary shapes -------------------------------------------------------
    A = make_class("A", [], ["a"])
    B = make_class("B", [], ["b"])
    C = make_class("C", [A, B], ["c"])       # two independently-decorated bases
    check(A, "boundary:A")
    check(B, "boundary:B")
    check(C, "boundary:C(A,B)")

    U = make_class("U", [], [])              # undecorated
    check(U, "boundary:undecorated")

    L0 = make_class("L0", [], ["x"])
    L1 = make_class("L1", [L0], ["y"])
    L2 = make_class("L2", [L1], ["z"])       # linear chain
    check(L2, "boundary:linear")

    M = make_class("M", [], ["p", "q", "r"])  # several own marks
    check(M, "boundary:multi-mark")

    D0 = make_class("D0", [], ["d0"])
    D1 = make_class("D1", [D0], ["d1"])
    D2 = make_class("D2", [D0], ["d2"])
    D3 = make_class("D3", [D1, D2], ["d3"])  # diamond
    check(D3, "boundary:diamond")

    E0 = make_class("E0", [], [])
    E1 = make_class("E1", [], ["e1"])
    E2 = make_class("E2", [E0, E1], [])      # own empty, base decorated
    check(E2, "boundary:mixed-empty")

    RPT = make_class("RPT", [], ["w", "w", "v", "w"])  # repeated names
    check(RPT, "boundary:repeated-marks")

    # --- randomised fuzz over class DAGs until >= TARGET_CHECKS ----------------
    rng = random.Random(SEED)
    pool_names = ["m%d" % k for k in range(12)]
    trial = 0
    while checked < TARGET_CHECKS:
        classes = []
        n = rng.randint(1, 7)
        for idx in range(n):
            k = rng.randint(0, min(2, len(classes)))
            bases = rng.sample(classes, k) if k and classes else []
            nm = rng.randint(0, 3)
            marks = [rng.choice(pool_names) for _ in range(nm)]
            try:
                cls = make_class("T%d_%d" % (trial, idx), bases, marks)
            except TypeError:
                # inconsistent linearisation from the random base choice
                continue
            classes.append(cls)
            check(cls, "fuzz T%d_%d" % (trial, idx))
        trial += 1

    print("G-CONF OK: shadow impl == real collector on %d inputs "
          "(both flag values per class; boundary shapes + %d fuzz trials, "
          "seed %d)." % (checked, trial, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
