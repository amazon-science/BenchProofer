#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13615.

This bundle declares **no value-bearing axioms** and **no deep-model references**.
The single operation the gold patch changes (re-routing each element of a finite
operand by a three-valued membership verdict) is modeled *directly* by the
`definiteOut` / `symbolicUnknown` selections and the verified loop; every
refinement leg is therefore R or I and is handled mechanically by G-CONF
(conformance_check.py).  The one opaque symbol, `contains`, models the UNCHANGED
callee `Set.contains` and carries no value contract — only determinism — so there
is no axiom `ensures` to refute (SPEC_GUIDE directive 7).

To keep the gate meaningful rather than a silent pass, this script:

  1. asserts the bundle truly declares no value-bearing axioms (meta.json
     `axioms == []` and `deep_model_references == []`), so a future edit that
     smuggles in a value-bearing axiom without a soundness check is caught here;
     and
  2. exercises the REAL `Set.contains` / `ternary_sift` trichotomy in-container
     (the gold's `contains if contains in [True, False] else None`) over
     decided-inside, decided-outside and undetermined cases plus fuzz, confirming
     every observation lands in exactly one of {True, False, None} — i.e. that
     the `Trit` carrier is total and the mapping.md §2 trichotomy is faithful.

Runs in-container (the prebuilt SWE-Bench instance image), sympy + stdlib only.
Exit 0 iff the no-value-axiom claim holds and the membership trichotomy is sound.
"""
import json
import os
import random
import sys

SEED = 13615


def check_no_value_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], (
        "axiom_check expected no value-bearing axioms but meta.json lists %r; "
        "an axiom requires an executable soundness check here." % (axioms,))
    assert refs == [], (
        "axiom_check expected no deep-model references but meta.json lists %r; "
        "an A-reference requires a == real-callee check here." % (refs,))


def _ternary_sift(ambient, el):
    """The gold's classification key, mapped to a stable Python verdict.

    The gold writes `contains if contains in [True, False] else None`; the
    decided verdict is sympy `S.true` / `S.false` (which compare `== True` /
    `== False` but are not the Python singletons), so normalize to a plain
    'inside' / 'outside' / 'unknown' trit — exactly the mapping.md §2 carrier."""
    contains = ambient.contains(el)
    if contains in [True, False]:
        return "inside" if contains == True else "outside"   # noqa: E712
    return "unknown"


def check_membership_trichotomy():
    from sympy import (FiniteSet, Interval, Symbol, Integer, S)

    rng = random.Random(SEED)

    # Boundary: each verdict must be reachable and be one of the three trits.
    iv = Interval(-10, 10)
    x = Symbol("x")
    assert _ternary_sift(iv, Integer(2)) == "inside", "decided-inside expected"
    assert _ternary_sift(iv, Integer(50)) == "outside", "decided-outside expected"
    assert _ternary_sift(iv, x) == "unknown", "undetermined (symbol) expected"

    # A finite ambient too.
    fs = FiniteSet(Integer(1), Integer(2), Integer(3))
    assert _ternary_sift(fs, Integer(2)) == "inside"
    assert _ternary_sift(fs, Integer(7)) == "outside"
    assert _ternary_sift(fs, x) == "unknown"

    # Fuzz: every observation is exactly one of the three trits, and the decided
    # ones agree with the obvious membership truth for numbers.
    n_checked = 0
    for _ in range(20_000):
        lo = rng.randint(-40, 0)
        hi = rng.randint(1, 40)
        ambient = Interval(lo, hi)
        if rng.random() < 0.6:
            v = Integer(rng.randint(-60, 60))
            t = _ternary_sift(ambient, v)
            assert t in ("inside", "outside"), "number must be decidable in an Interval"
            expected = "inside" if (lo <= int(v) <= hi) else "outside"
            assert t == expected, (
                "decided verdict disagrees with interval membership: %r in %r"
                % (v, ambient))
        else:
            sym = Symbol("y%d" % rng.randint(0, 30))
            t = _ternary_sift(ambient, sym)
            assert t == "unknown", "free symbol must be undetermined"
        n_checked += 1

    return n_checked


def main():
    check_no_value_axioms()
    n = check_membership_trichotomy()
    print("G-AX OK: bundle declares no value-bearing axioms / no A-references; "
          "the opaque `contains` models the UNCHANGED Set.contains, whose "
          "three-valued verdict (ternary_sift) lands in exactly {True,False,None} "
          "on 6 boundary + %d fuzz observations (Trit carrier total & faithful)."
          % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
