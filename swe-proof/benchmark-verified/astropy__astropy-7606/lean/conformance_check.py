#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-7606.

The bundle models ONE routine: `UnrecognizedUnit.__eq__` (mapping.md). The
modeled value is a PURE function of `selfName` and the observable outcome of the
UNCHANGED callee `Unit(other, parse_strict='silent')`:

    po = .raised                         if the factory raises (ValueError|UnitsError|TypeError)
       = .parsed(isUnrecognized, name)   otherwise

Post-patch rule (`eqResult`, the gold edit wraps the factory call in a handler):

    .raised                   -> notApplicable    (returns the NotImplemented sentinel)
    .parsed(isUnrec, name)    -> isTrue  if isUnrec and selfName == name else isFalse

This check runs IN-CONTAINER WITH THE GOLD PATCH APPLIED, so it drives the REAL
astropy machinery on both legs:

  * ORACLE = the real, post-patch `UnrecognizedUnit.__eq__(self, other)` — its
    three-valued return (True / False / NotImplemented) mapped to EqResult.
  * SHADOW = the op-for-op transliteration of `implementation_unrecognizedUnitEq`
    (Solution.lean impl region), fed `po` computed by ACTUALLY CALLING the real
    `Unit(other, parse_strict='silent')` factory (the unchanged callee — its
    carried observation is thereby validated against reality).

The soundness-critical clause: an operand that cannot be interpreted as a unit
(e.g. None) must yield the not-applicable sentinel (NotImplemented), never an
escaping exception — matching the F2P expectations (`unit == "FOO"` True,
`unit != u.m`, `unit != None`).

stdlib + astropy (present in the instance image). Pinned seed: 7606 (also in
mapping.md).
"""
import random
import sys

SEED = 7606
N = 120_000

# EqResult enum (mapping.md bijection)
IS_TRUE = "isTrue"
IS_FALSE = "isFalse"
NOT_APPLICABLE = "notApplicable"

try:
    from astropy import units as u
    from astropy.units.core import Unit, UnrecognizedUnit, UnitsError
except Exception as e:  # pragma: no cover
    print(f"import-error: {e}")
    print("status=fail")
    sys.exit(1)


def parse_outcome(other):
    """Compute `po` by calling the REAL unchanged factory (mapping.md)."""
    try:
        parsed = Unit(other, parse_strict='silent')
    except (ValueError, UnitsError, TypeError):
        return ("raised", None, None)
    return ("parsed", isinstance(parsed, UnrecognizedUnit), getattr(parsed, "name", None))


# --- SHADOW of implementation_unrecognizedUnitEq (the R leg) ------------------
def shadow(self_name, po):
    kind = po[0]
    if kind == "raised":
        return NOT_APPLICABLE
    # parsed
    _, is_unrec, other_name = po
    if is_unrec and self_name == other_name:
        return IS_TRUE
    return IS_FALSE


# --- ORACLE: the REAL post-patch UnrecognizedUnit.__eq__ ----------------------
def oracle(self_unit, other):
    res = self_unit.__eq__(other)
    if res is NotImplemented:
        return NOT_APPLICABLE
    if res is True:
        return IS_TRUE
    if res is False:
        return IS_FALSE
    # Defensive: any non-bool, non-sentinel return is an unexpected disagreement.
    return f"UNEXPECTED({res!r})"


def mk_unrecognized(name):
    """A genuine UnrecognizedUnit with the given name."""
    unit = Unit(name, parse_strict='silent')
    assert isinstance(unit, UnrecognizedUnit), (name, type(unit))
    return unit


def disagree(self_name, self_unit, other):
    po = parse_outcome(other)
    got = oracle(self_unit, other)
    want = shadow(self_name, po)
    if got != want:
        return (self_name, repr(other), po, got, want)
    return None


def _edge_cases():
    # (self_name, other)
    cases = []
    # F2P: unit("FOO") == "FOO" -> isTrue
    cases.append(("FOO", "FOO"))
    # F2P: unit("FOO") == None -> notApplicable (the bug fix; pre-patch raised)
    cases.append(("FOO", None))
    # F2P: unit("FOO") == u.m (recognised) -> isFalse
    cases.append(("FOO", u.m))
    cases.append(("FOO", "m"))
    # unit("FOO") == unit("BAR") -> isFalse (different unrecognised name)
    cases.append(("FOO", "BAR"))
    # gh-7603: comparison against non-unit objects -> notApplicable, no raise
    cases.append(("FOO", 3))
    cases.append(("FOO", 3.5))
    cases.append(("FOO", [1, 2, 3]))
    cases.append(("FOO", object()))
    # self compared against an actual UnrecognizedUnit instance with same name
    cases.append(("FOO", mk_unrecognized("FOO")))
    cases.append(("FOO", mk_unrecognized("BAR")))
    # recognised composite / dimensionless
    cases.append(("FOO", u.dimensionless_unscaled))
    cases.append(("FOO", u.m / u.s))
    return cases


def main() -> int:
    checked = 0
    # Edge cases (fixed self name "FOO")
    self_unit = mk_unrecognized("FOO")
    for self_name, other in _edge_cases():
        su = self_unit if self_name == "FOO" else mk_unrecognized(self_name)
        d = disagree(self_name, su, other)
        if d:
            print(f"DISAGREE edge: self={d[0]!r} other={d[1]} po={d[2]} oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    names = ["FOO", "BAR", "asdf", "QUUX", "xyzzy", "ZZ", "abc123", "weird_unit"]
    recognised = ["m", "s", "kg", "Hz", "J", "deg", "", "m/s"]
    self_pool = {n: mk_unrecognized(n) for n in names}
    for _ in range(N):
        self_name = rng.choice(names)
        su = self_pool[self_name]
        pick = rng.random()
        if pick < 0.20:
            other = None
        elif pick < 0.35:
            other = rng.choice([3, 3.5, -1, [1, 2], {"a": 1}, object(), (1, 2)])
        elif pick < 0.65:
            other = rng.choice(names)          # unparsable string -> UnrecognizedUnit
        elif pick < 0.85:
            other = rng.choice(recognised)     # recognised string
        else:
            other = mk_unrecognized(rng.choice(names))  # an UnrecognizedUnit object
        d = disagree(self_name, su, other)
        if d:
            print(f"DISAGREE fuzz: self={d[0]!r} other={d[1]} po={d[2]} oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
