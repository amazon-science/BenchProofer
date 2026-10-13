#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7606 (nagini).

SHADOW: the impl regions of model.py (`eq_unparsed_name`, `eq_unit`), copied
verbatim below with the contract calls (Requires/Ensures) stripped. The pure
region (the three integer result tags) copies over unchanged. There are no
PSeq values and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`astropy.units.core.UnrecognizedUnit.__eq__` and
`astropy.units.core.UnitBase.__eq__`. The gate applies patch.diff to /testbed
before this script runs (this script does NOT apply it); PYTHONPATH=/testbed
makes the patched module importable. We observe the RAW dunder return so the
not-applicable sentinel (`NotImplemented`) stays visible instead of being
collapsed to a bool by the `==` operator; a dunder that RAISES counts as a
disagreement (the model pins a total, never-failing comparison).

TYPE BRIDGE (mapping.md section 2): the model abstracts the arbitrary operand
to the boolean observables the comparison reads off it. For each concrete
(self, operand) pair we compute those observables with the UNCHANGED repo
callees, exactly as mapping.md binds them:
  parse_succeeds    <- Unit(operand, parse_strict='silent') returns normally
                       (vs raising ValueError/UnitsError/TypeError)
  parsed_same_kind  <- isinstance(coerced, type(self))
  names_equal       <- coerced same-kind and self.name == coerced.name
  is_same           <- self is operand
  parsed_is_unit    <- isinstance(coerced, UnitBase)
  convertible       <- self._to(coerced) does not raise UnitsError
  effectively_unity <- convertible and is_effectively_unity(self._to(coerced))
The Requires of eq_unit (effectively_unity implies convertible) holds by
construction. The three-valued raw result maps to the model tags
RES_FALSE/RES_TRUE/RES_NOTIMPL (False/True/NotImplemented).

INPUT DOMAIN: concrete operands spanning the observable space — non-coercible
objects (None, plain objects, containers), recognised unit names and unit
values (identical, convertible-but-unequal, dimensionally incompatible),
unparsed-name units and strings (same and different names), numbers, and
random short strings (a mix of coercible and non-coercible). Every generated
input satisfies the (trivial, boolean-typed) Requires. Zero is excluded from
the number pool: it coerces to a zero-scale dimensionless value on which the
conversion callee divides by zero, so the convertibility observable (defined
as "raises a units error or not", mapping.md) is undefined there — outside
the callee's operating domain, analogous to excluding zero-extent operands.

>= 1e5 Requires-satisfying inputs: boundary catalogue + 55000 fuzz rounds,
each round exercising BOTH modeled functions (>=110000 shadow/oracle diffs).
Pinned fuzz seed: 7606.

Exit 0 iff zero disagreements; on disagreement prints the input, the computed
observables, and both outputs, then exits 1. stdlib + astropy only.
"""
import json
import random
import sys

SEED = 7606
N_FUZZ = 55_000


# --- pure region of model.py, verbatim ----------------------------------------

RES_FALSE = 0
RES_TRUE = 1
RES_NOTIMPL = 2


# --- impl regions of model.py, verbatim, contract calls stripped ---------------

def eq_unparsed_name(parse_succeeds, parsed_same_kind, names_equal):
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than fail.
        return RES_NOTIMPL
    if parsed_same_kind and names_equal:
        return RES_TRUE
    return RES_FALSE


def eq_unit(is_same, parse_succeeds, parsed_is_unit, convertible,
            effectively_unity):
    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than return a definite (and wrong) "not equal".
        return RES_NOTIMPL
    if not parsed_is_unit:
        return RES_NOTIMPL
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE


# --- bridge: concrete operand -> boolean observables / raw result -> tag -------

def _tag(raw):
    """Map a RAW dunder return value to the model's three-valued tag."""
    if raw is NotImplemented:
        return RES_NOTIMPL
    if raw is True:
        return RES_TRUE
    if raw is False:
        return RES_FALSE
    return None  # non-bool, non-sentinel: reported as a disagreement


def make_observers(u, UnitBase, UnitsError, is_effectively_unity):
    """Build the observable extractors over the unchanged repo callees."""

    def coerce(operand):
        """(parse_succeeds, coerced-or-None) via the silent-parse factory."""
        try:
            return True, u.Unit(operand, parse_strict="silent")
        except (ValueError, UnitsError, TypeError):
            return False, None

    def obs_unparsed_name(self_unit, operand):
        ps, parsed = coerce(operand)
        sk = ps and isinstance(parsed, type(self_unit))
        ne = bool(sk and self_unit.name == parsed.name)
        return ps, sk, ne

    def obs_unit(self_unit, operand):
        is_same = self_unit is operand
        ps, parsed = coerce(operand)
        piu = ps and isinstance(parsed, UnitBase)
        conv, eff = False, False
        if piu:
            try:
                scale = self_unit._to(parsed)
                conv = True
                eff = bool(is_effectively_unity(scale))
            except UnitsError:
                conv, eff = False, False
        return is_same, ps, piu, conv, eff

    return obs_unparsed_name, obs_unit


def check_one(label, kind, self_unit, operand, observables, shadow_fn):
    """Diff shadow(observables) against the raw real dunder; error str or None."""
    expected = shadow_fn(*observables)
    try:
        raw = self_unit.__eq__(operand)
    except Exception as exc:
        return ("DISAGREEMENT (%s/%s): real dunder RAISED %r but the shadow "
                "yields tag %d\n  self=%r\n  operand=%r\n  observables=%r"
                % (kind, label, exc, expected, self_unit, operand, observables))
    observed = _tag(raw)
    if observed is None:
        return ("DISAGREEMENT (%s/%s): real dunder returned non-bool, "
                "non-sentinel %r\n  self=%r\n  operand=%r\n  observables=%r"
                % (kind, label, raw, self_unit, operand, observables))
    if observed != expected:
        return ("DISAGREEMENT (%s/%s): shadow tag=%d real tag=%d (raw=%r)\n"
                "  self=%r\n  operand=%r\n  observables=%r"
                % (kind, label, expected, observed, raw,
                   self_unit, operand, observables))
    return None


def main():
    import astropy.units as u
    from astropy.units.core import UnitBase, UnrecognizedUnit, UnitsError
    from astropy.units.utils import is_effectively_unity

    obs_unparsed_name, obs_unit = make_observers(
        u, UnitBase, UnitsError, is_effectively_unity)

    checked = 0

    # ---- fixed selves --------------------------------------------------------
    foo = u.Unit("FOO", parse_strict="silent")
    bar = u.Unit("BAR", parse_strict="silent")
    assert isinstance(foo, UnrecognizedUnit)
    unrec_selves = [foo, bar]

    unit_selves = [u.m, u.cm, u.kg, u.s, u.dimensionless_unscaled,
                   u.m / u.s, u.km]

    # ---- operand pools -------------------------------------------------------
    non_coercible = [None, object(), [1, 2, 3], {"a": 1}, (1, 2), object]
    recognized_strs = ["m", "cm", "km", "kg", "g", "s", "J", "W", "A",
                       "deg", "rad", "m / s", "kg m2 / s2", ""]
    unrec_strs = ["FOO", "BAR", "BAZ", "QUX"]
    unit_vals = [u.m, u.cm, u.km, u.kg, u.g, u.s, u.J,
                 u.dimensionless_unscaled, u.m / u.s, u.m ** 2]
    numbers = [1, 1.0, 2, 2.5, -1, 100.0]

    rng = random.Random(SEED)
    rand_strs = []
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for _ in range(200):
        n = rng.randint(1, 8)
        rand_strs.append("".join(rng.choice(alphabet) for _ in range(n)))

    all_operands = (non_coercible + recognized_strs + unrec_strs
                    + unit_vals + numbers + rand_strs
                    + [foo, bar])

    disagreements = 0

    def run_case(label, kind, self_unit, operand):
        nonlocal checked, disagreements
        if kind == "unparsed_name":
            obs = obs_unparsed_name(self_unit, operand)
            err = check_one(label, kind, self_unit, operand, obs,
                            eq_unparsed_name)
        else:
            obs = obs_unit(self_unit, operand)
            err = check_one(label, kind, self_unit, operand, obs, eq_unit)
        checked += 1
        if err:
            print(err)
            disagreements += 1
            return False
        return True

    # ---- boundary catalogue: full cross of selves x curated operands ---------
    for self_unit in unrec_selves:
        for i, operand in enumerate(non_coercible + recognized_strs
                                    + unrec_strs + unit_vals + numbers
                                    + [foo, bar, self_unit]):
            if not run_case("boundary[%d]" % i, "unparsed_name",
                            self_unit, operand):
                return 1
    for self_unit in unit_selves:
        for i, operand in enumerate(non_coercible + recognized_strs
                                    + unrec_strs + unit_vals + numbers
                                    + [foo, self_unit]):
            if not run_case("boundary[%d]" % i, "unit", self_unit, operand):
                return 1
    n_boundary = checked

    # ---- fuzz: pinned seed, both modeled functions each round ----------------
    for k in range(N_FUZZ):
        s1 = rng.choice(unrec_selves)
        s2 = rng.choice(unit_selves)
        o1 = rng.choice(all_operands)
        o2 = rng.choice(all_operands)
        if not run_case("fuzz[%d]" % k, "unparsed_name", s1, o1):
            return 1
        if not run_case("fuzz[%d]" % k, "unit", s2, o2):
            return 1

    print("G-CONF OK: shadow impl == real patched comparison dunders on %d "
          "inputs (%d boundary + %d fuzz checks, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": disagreements,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
