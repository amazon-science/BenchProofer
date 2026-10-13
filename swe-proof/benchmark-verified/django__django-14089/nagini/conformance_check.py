#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14089 (nagini).

SHADOW: the impl region of model.py's ``reverse_order``, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The
@Pure helper ``rev`` copies over as a plain function on top of a small
immutable-tuple PSeq shim; it is contract-side but serves here as an internal
cross-check of the shadow. There are no @ContractOnly callees in this bundle
(the axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md /
refinement.md — ``django.utils.datastructures.OrderedSet.__reversed__``. The
gate applies the patch to /testbed before this script runs; this script only
imports the patched class and materializes its backward enumeration
(``list(reversed(OrderedSet(items)))``).

Type bridge (mapping.md section 2): the model carrier ``elements: List[int]``
is the collection's ordered contents — the distinct element keys in insertion
order. An ``OrderedSet`` built from a raw item list collapses duplicates while
keeping first-occurrence order, so the bridge from a raw generated item list is
``elements = list(dict.fromkeys(raw_items))`` (== ``list(iter(oset))``, which
is asserted per case). The shadow runs on ``elements``; the oracle's
materialized backward enumeration is compared element-wise against the
shadow's result list. The collection is also re-enumerated forward afterwards
to confirm the backward traversal left it unchanged (the read-only half of the
contract, directive 5).

Input domain: the precondition demands only a readable list, so every
``List[int]`` of distinct keys in insertion order is Requires-satisfying;
generation covers the empty collection, singletons, long runs, negative keys,
and raw lists with duplicates (exercising the carrier's key collapsing).

>= 1e5 Requires-satisfying inputs: 18 boundary cases + 100000 fuzz lists.
Pinned fuzz seed: 140890.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import sys

SEED = 140890
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
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

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(list(lst))


# --- pure helper from model.py, contracts stripped ----------------------------

def rev(s):
    """The reversal of a sequence: the reversal of its tail followed by its
    head. Front-recursive (one unfold per element) so a backward impl loop that
    appends the head each step can discharge it."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return rev(s.drop(1)) + PSeq(s[0])


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reverse_order(elements):
    result = []  # type: list
    i = len(elements)
    while i > 0:
        e = elements[i - 1]
        # (the stripped Assert lines carried only proof-side sequence facts)
        result = result + [e]
        i = i - 1
    return result


# --- differential driver -------------------------------------------------------

def check(OrderedSet, raw_items):
    """Build the real collection from raw_items, bridge to the model carrier,
    and diff shadow vs the real patched backward enumeration. Returns an error
    string on disagreement, else None."""
    oset = OrderedSet(raw_items)
    elements = list(dict.fromkeys(raw_items))   # bridge: distinct keys, insertion order

    forward = list(iter(oset))
    if forward != elements:
        return ("BRIDGE: forward enumeration of %r is %r, expected %r"
                % (raw_items, forward, elements))

    shadow = reverse_order(elements)
    real = list(reversed(oset))                  # the patched repo function

    if shadow != real:
        return ("DISAGREEMENT on items %r (carrier %r):\n"
                "  shadow (impl region) = %r\n"
                "  real (patched backward enumeration) = %r"
                % (raw_items, elements, shadow, real))

    # read-only: the backward traversal must not disturb the collection
    if list(iter(oset)) != forward:
        return ("FRAME: backward enumeration mutated the collection on %r"
                % (raw_items,))

    # internal cross-check: the executable impl agrees with the pure theory
    if ToSeq(shadow) != rev(ToSeq(elements)):
        return ("INTERNAL: impl region and pure rev disagree on %r"
                % (raw_items,))
    return None


def boundary_cases():
    return [
        [],
        [0],
        [1],
        [-1],
        [1, 2],
        [2, 1],
        [1, 2, 3],
        [3, 2, 1],
        [-1, 0, 1],
        list(range(10)),
        list(range(50)),
        list(range(200)),
        list(range(199, -1, -1)),
        [5, 4, 3, 2, 1],
        # raw duplicates collapse to distinct keys, first-occurrence order kept
        [1, 1, 2, 2, 3, 3],
        [2, 1, 2, 3, 1],
        [7] * 20,
        [0, -1, 0, 1, -1, 2],
    ]


def main():
    from django.utils.datastructures import OrderedSet

    checked = 0
    for raw in boundary_cases():
        err = check(OrderedSet, raw)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 32)
        if rng.random() < 0.5:
            # small pool -> duplicates collapse in the carrier
            raw = [rng.randint(-8, 8) for _ in range(n)]
        else:
            # wide pool -> mostly-distinct keys
            raw = [rng.randint(-10**6, 10**6) for _ in range(n)]
        err = check(OrderedSet, raw)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow == real backward enumeration on %d inputs "
          "(%d boundary + %d fuzz, seed %d); zero disagreements"
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
