#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-7606 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of `refinement.md`: the deep
comparison model of `Solution.lean` (`compareSpec` — a failed interpretation
declines with `deferred`/`NotImplemented`; a same-kind operand compares by name
equality; an other-kind operand is unequal; the result is ALWAYS a verdict, never
an escaped exception) transliterated to Python, differential-tested against
`patch.diff`'s behaviour driven through the REAL gold-patched
`UnrecognizedUnit.__eq__` at base_commit+gold.

ORACLE — the gold-patched `UnrecognizedUnit.__eq__` itself, called directly so we
observe its raw return (`NotImplemented` or a `bool`) and whether it raises. The
patch's whole content is that an operand the interpreter rejects now yields
`NotImplemented` instead of letting the exception escape.

SHADOW — `Solution.lean`'s `compareSpec`, transliterated. It classifies the
operand by running the SAME unchanged callee `Unit(other, parse_strict='silent')`
(run live — the A-tagged-as-free-input callee, NOT an axiom model):
  * raises (ValueError/UnitsError/TypeError)        -> deferred       (NotImplemented)
  * interprets to an UnrecognizedUnit named `name`  -> decided(self.name == name)
  * interprets to anything else                     -> decided(False)

For each (receiver, operand) we compare the pair (raised?, normalized verdict)
between ORACLE and SHADOW. `NotImplemented` normalizes to the sentinel
`"__deferred__"`; a bool to itself. Exit 0 iff zero disagreements over the
boundary operands plus the fuzz budget (seed pinned, mapping.md §4).

astropy-only; no network, no database.
"""
import random
import sys

from astropy import units as u
from astropy.units.core import UnitBase, UnrecognizedUnit, Unit, UnitsError

SEED = 7606
FUZZ = 120000  # > 1e5 fuzzed operands (plan §4.1)

DEFERRED = "__deferred__"   # normalized NotImplemented


# ---- SHADOW: Solution.lean compareSpec, transliterated ----------------------
def classify(other):
    """Run the UNCHANGED interpreter and bucket its outcome into the three
    InterpretOutcome shapes (mapping.md §2)."""
    try:
        interp = Unit(other, parse_strict='silent')
    except (ValueError, UnitsError, TypeError):
        return ("uninterpretable", None)
    if isinstance(interp, UnrecognizedUnit):
        return ("sameKind", interp.name)
    return ("otherKind", None)


def shadow_observe(self_name, other):
    """compareSpec(selfName, outcome): the verdict the model assigns.
    Returns (raised, verdict) where verdict is DEFERRED or a bool."""
    kind, name = classify(other)
    if kind == "uninterpretable":
        return (False, DEFERRED)              # Except.ok .deferred
    if kind == "sameKind":
        return (False, self_name == name)     # decided (selfName = name)
    return (False, False)                     # otherKind -> decided false


# ---- ORACLE: the real gold-patched UnrecognizedUnit.__eq__ ------------------
def oracle_observe(receiver, other):
    """Call the real patched __eq__ directly so we see its raw return.
    Returns (raised, verdict): verdict is DEFERRED for NotImplemented, else the
    bool it returned."""
    try:
        res = UnrecognizedUnit.__eq__(receiver, other)
    except Exception:                                          # noqa: BLE001
        return (True, None)
    if res is NotImplemented:
        return (False, DEFERRED)
    return (False, bool(res))


# ---- operand corpus ---------------------------------------------------------
class _Weird:
    """An object of an unrelated type — the interpreter rejects it (TypeError)."""
    def __repr__(self):
        return "<weird>"


def receivers():
    """Genuine UnrecognizedUnit receivers under several names. Names are chosen
    so they do NOT parse to a known unit (so `Unit(name, parse_strict='silent')`
    really yields an UnrecognizedUnit, i.e. `type(self) == UnrecognizedUnit`,
    matching mapping.md §2). Any spelling that slips through to a real unit is
    filtered out."""
    cand = [u.Unit(n, parse_strict='silent')
            for n in ["FOO", "BAR", "asdf", "FOO BAR", "x", "qwerty", "ZZZ"]]
    recs = [r for r in cand if isinstance(r, UnrecognizedUnit)]
    assert recs, "expected at least one UnrecognizedUnit receiver"
    return recs


def boundary_operands():
    """The operands the F2P/P2P matrix and issue exercise, plus boundaries."""
    return [
        None,                                   # the bug: TypeError -> must defer
        "FOO", "BAR", "asdf", "",               # strings: parse as units (known/unknown)
        "m", "kg", "s", "cm",                   # recognized unit spellings
        "FOO BAR", "10+22/cm2",                 # odd spellings
        u.m, u.kg, u.s, u.dimensionless_unscaled,   # real UnitBase values (otherKind)
        u.Unit("FOO", parse_strict='silent'),   # another UnrecognizedUnit named FOO
        u.Unit("BAR", parse_strict='silent'),   # UnrecognizedUnit named BAR
        0, 1, -5, 3.14, float("nan"), float("inf"),   # numbers -> CompositeUnit (otherKind)
        b"FOO", b"m",                           # bytes operands
        [u.m], (None,), {}, _Weird(),           # unrelated objects -> TypeError
        True, False,                            # bool ints
    ]


def fuzz_operands(rng):
    alphabet = list("abcFOOBARmkgs 0123456789+-/.*^()") + ["\n", "你"]
    for _ in range(FUZZ):
        roll = rng.random()
        if roll < 0.12:
            yield None
        elif roll < 0.20:
            yield rng.choice([0, 1, -1, 2, 3.5, -2.0, float("nan"),
                              float("inf"), -float("inf")])
        elif roll < 0.28:
            yield rng.choice([u.m, u.kg, u.s, u.cm, u.dimensionless_unscaled,
                              u.Unit("FOO", parse_strict='silent'),
                              u.Unit("BAR", parse_strict='silent')])
        elif roll < 0.34:
            yield rng.choice([[u.m], (1,), {}, _Weird(), object()])
        else:
            k = rng.randint(0, 8)
            s = "".join(rng.choice(alphabet) for _ in range(k))
            yield s.encode("ascii", "replace") if roll > 0.92 else s


def main():
    rng = random.Random(SEED)
    recs = receivers()
    disagreements = []
    count = 0

    def check(receiver, other):
        nonlocal count
        count += 1
        oracle = oracle_observe(receiver, other)
        shadow = shadow_observe(receiver.name, other)
        # The fix's core guarantee: the real __eq__ NEVER raises.
        if oracle[0]:
            disagreements.append(("RAISED", receiver.name, other, shadow, oracle))
        elif oracle[1] != shadow[1]:
            disagreements.append(("VERDICT", receiver.name, other, shadow, oracle))

    for receiver in recs:
        for other in boundary_operands():
            check(receiver, other)
            if len(disagreements) >= 8:
                break
        if len(disagreements) >= 8:
            break

    if not disagreements:
        for other in fuzz_operands(rng):
            check(rng.choice(recs), other)
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tag, nm, other, sh, orc in disagreements:
            print("  [%s] self=%s operand=%s shadow=%s oracle=%s"
                  % (tag, ascii(nm), ascii(other), ascii(sh), ascii(orc)))
        return 1
    print("G-CONF OK: R/I shadow of compareName (decline-on-uninterpretable, "
          "name-equality verdict) agrees with patch.diff behaviour through the "
          "real UnrecognizedUnit.__eq__ on %d operands (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
