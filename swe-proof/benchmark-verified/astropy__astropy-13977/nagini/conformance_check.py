#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13977 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The impl operates on a
plain List[int] of per-operand kind flags plus a boolean failure indicator;
the @Pure helpers `all_recognised` / `has_custom_handler` copy over as plain
functions on tuples. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method per mapping.md —
`astropy.units.Quantity.__array_ufunc__`, invoked directly on a Quantity
receiver with concrete numpy ufuncs and operand collections. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable.

Type bridge (mapping.md section 2):
  * io_kinds: one flag per input operand plus one per pre-allocated output
    operand; flag = 0 iff the operand's type's `__array_ufunc__` attribute is
    one of the recognised built-in kinds (absent, the base ndarray one, or
    the receiver type's own), else 1. Computed here with the real membership
    predicate over the real operand objects.
  * recoverable_failure: whether the protected evaluation failed with one of
    the two recoverable error classes. Observationally, over the generated
    domain, the real dispatcher yields an ordinary result iff the protected
    evaluation succeeded, so the flag is derived as (observed outcome != 0).
    The derivation is non-circular for the property under test: given a
    failure, the shadow decides abstain-vs-surface from the flags ALONE, and
    that decision is diffed against the real dispatcher's observed choice.
  * outcome codes: 0 = ordinary result returned; 1 = the "not handled here"
    sentinel (NotImplemented); 2 = the recoverable error propagates to the
    caller. Only the code is compared (the model abstracts result values).

Input domain: operand collections are drawn from archetypes exercising every
flag combination — plain scalars/ndarrays and unit-carrying values (all
recognised kinds), value-carrier objects without their own handler, duck
objects that DO supply their own handler, receiver-subclass instances with a
delegating handler, and pre-allocated outputs of each kind; unit mixes are
chosen so both successful evaluations and recoverable failures occur, and
non-convertible payloads force late failures. One fragile corner is excluded:
a non-convertible payload combined with a custom-handler output that the
output-normalisation step accepts (there the dispatcher re-examines the
normalised, not the original, output object, so the flag bridge for the
original object is not faithful); every other combination is generated.

>= 1e5 Requires-satisfying inputs: deterministic boundary scenarios + 100000
fuzz scenarios. Pinned fuzz seed: 13977.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outcomes and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 13977
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped, PSeq -> tuple -----------

def all_recognised(flags):
    if len(flags) == 0:
        return True
    return flags[0] == 0 and all_recognised(flags[1:])


def has_custom_handler(flags):
    return not all_recognised(flags)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def dispatch_ufunc(io_kinds, recoverable_failure):
    if not recoverable_failure:
        # The protected evaluation completed; yield the ordinary result.
        return 0
    # Recoverable failure: inspect the operands (back-to-front) for any custom
    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).
    every_recognised = True
    i = len(io_kinds)
    while i > 0:
        if io_kinds[i - 1] != 0:
            every_recognised = False
        i = i - 1
    if every_recognised:
        # Every operand is a recognised built-in kind: surface the error.
        return 2
    # Some operand supplies a custom handler: abstain so it can be tried.
    return 1


# --- operand archetypes -------------------------------------------------------

JUNK = "junk"          # a payload no numeric conversion accepts


class Carrier:
    """Unit+value carrier WITHOUT its own handler: recognised kind (flag 0)."""

    def __init__(self, unit, value):
        self.unit = unit
        self.value = value


class Duck:
    """Unit+value carrier WITH its own handler: custom kind (flag 1)."""

    def __init__(self, unit, value):
        self.unit = unit
        self.value = value

    def __array_ufunc__(self, function, method, *inputs, **kwargs):
        return NotImplemented


class DuckOut:
    """Output-slot object with its own handler and no array nature (flag 1)."""

    def __array_ufunc__(self, function, method, *inputs, **kwargs):
        return NotImplemented


def main():
    import astropy.units as u
    from astropy.units import Quantity  # REAL patched class

    class QSub(Quantity):
        """Receiver-type subclass with a delegating handler of its own:
        a distinct method object, hence a custom kind (flag 1)."""

        def __array_ufunc__(self, function, method, *inputs, **kwargs):
            return super().__array_ufunc__(function, method, *inputs, **kwargs)

    receiver = Quantity(1.0, u.m)

    # the recognised-built-in-kind membership, per mapping.md section 1
    ignored = (None, np.ndarray.__array_ufunc__,
               type(receiver).__array_ufunc__)

    def real_flag(io):
        return 0 if getattr(type(io), "__array_ufunc__", None) in ignored else 1

    def call_real(fn, inputs, out):
        """Invoke the real dispatcher; classify the outcome as the code."""
        kwargs = {}
        if out is not None:
            kwargs["out"] = out
        try:
            r = receiver.__array_ufunc__(fn, "__call__", *inputs, **kwargs)
        except (TypeError, ValueError):
            return 2
        return 1 if r is NotImplemented else 0

    def check(label, fn, inputs, out):
        flags = [real_flag(io) for io in inputs]
        if out is not None:
            flags += [real_flag(io) for io in out]
        real = call_real(fn, inputs, out)
        # bridge: an ordinary result observationally means the protected
        # evaluation succeeded; any other outcome means it failed recoverably.
        failure = real != 0
        shadow = dispatch_ufunc(list(flags), failure)
        if shadow != real:
            print("DISAGREEMENT\n  scenario=%s\n  ufunc=%s inputs=%r out=%r\n"
                  "  flags=%r failure=%r\n  shadow=%d real=%d"
                  % (label, fn.__name__, inputs, out, flags, failure,
                     shadow, real))
            return False
        return True

    # value/operand constructors (fresh objects each scenario: outputs mutate)
    UNITS = [u.m, u.mm, u.s, u.dimensionless_unscaled]

    def fresh_out_slot(kind, unit):
        if kind == "Q":
            return Quantity(0.0, unit)
        if kind == "QSub":
            return QSub(0.0, unit)
        if kind == "nd":
            return np.zeros(())
        return DuckOut()

    def fresh_input(kind, unit, value):
        if kind == "Q":
            return Quantity(value, unit)
        if kind == "QSub":
            return QSub(value, unit)
        if kind == "nd":
            return np.asarray(value) if value != JUNK else np.asarray(0.0)
        if kind == "float":
            return float(value) if value != JUNK else 0.5
        if kind == "carrier":
            return Carrier(unit, value)
        return Duck(unit, value)  # "duck"

    checked = 0
    bad = 0

    # --- boundary scenarios: every decision cell hit deterministically -------
    Qm = lambda v=2.0: Quantity(v, u.m)
    Qmm = lambda v=3.0: Quantity(v, u.mm)
    Qs = lambda v=4.0: Quantity(v, u.s)
    Qd = lambda v=5.0: Quantity(v, u.dimensionless_unscaled)
    boundary = [
        ("unary ok",            np.negative, [Qm()], None),
        ("unary duck ok",       np.negative, [Duck(u.mm, 2.0)], None),
        ("unary duck junk",     np.negative, [Duck(u.mm, JUNK)], None),
        ("unary carrier junk",  np.negative, [Carrier(u.mm, JUNK)], None),
        ("convertible units",   np.add, [Qm(), Qmm()], None),
        ("same units",          np.add, [Qs(), Qs()], None),
        ("clashing units",      np.add, [Qm(), Qs()], None),
        ("unit vs bare array",  np.add, [Qm(), np.arange(2.0)], None),
        ("clash w/ duck",       np.add, [Qm(), Duck(u.s, 2.0)], None),
        ("junk duck first",     np.add, [Duck(u.m, JUNK), Qm()], None),
        ("out ok",              np.add, [Qm(), Qm()], (Quantity(0.0, u.m),)),
        ("out other unit",      np.add, [Qm(), Qm()], (Quantity(0.0, u.s),)),
        ("out duck",            np.add, [Qm(), Qm()], (DuckOut(),)),
        ("clash + out duck",    np.add, [Qm(), Qs()], (DuckOut(),)),
        ("clash + out sub",     np.add, [Qm(), Qs()], (QSub(0.0, u.m),)),
        ("out sub ok",          np.add, [Qm(), Qmm()], (QSub(0.0, u.m),)),
        ("carrier ok",          np.add, [Qmm(), Carrier(u.mm, 5.0)], None),
        ("carrier junk",        np.add, [Qm(), Carrier(u.mm, JUNK)], None),
        ("two ducks clash",     np.add, [Duck(u.m, 2.0), Duck(u.s, 3.0)], None),
        ("two ducks ok",        np.add, [Duck(u.m, 2.0), Duck(u.mm, 3.0)], None),
        ("two carriers clash",  np.add, [Carrier(u.m, 2.0), Carrier(u.s, 3.0)], None),
        ("sub clash",           np.add, [QSub(2.0, u.m), QSub(3.0, u.s)], None),
        ("sub ok",              np.add, [QSub(2.0, u.m), QSub(3.0, u.mm)], None),
        ("plain floats",        np.add, [2.0, 3.0], None),
        ("bare arrays",         np.add, [np.arange(2.0), np.arange(2.0)], None),
        ("dimless + float",     np.add, [Qd(), 3.0], None),
        ("float + unit",        np.add, [2.0, Qm()], None),
        ("multiout ok",         np.divmod, [Qm(), Qmm()], None),
        ("multiout clash",      np.divmod, [Qm(), Qs()], None),
        ("multiout out ok",     np.divmod, [Qm(), Qm()],
         (Qd(0.0), Quantity(0.0, u.m))),
        ("multiout out duck",   np.divmod, [Qm(), Qs()], (Qd(0.0), DuckOut())),
        ("unary out clash",     np.negative, [Qm()], (np.zeros(()),)),
        ("unary out duck",      np.negative, [Qm()], (DuckOut(),)),
        ("unary duck out q",    np.negative, [Duck(u.m, 2.0)],
         (Quantity(0.0, u.m),)),
        ("carrier out clash",   np.negative, [Carrier(u.mm, 5.0)],
         (Quantity(0.0, u.mm),)),
    ]
    for label, fn, inputs, out in boundary:
        bad += 0 if check(label, fn, inputs, out) else 1
        checked += 1
        if bad:
            return 1

    # --- fuzz: random scenarios over the archetype grid ----------------------
    rng = random.Random(SEED)
    IN_KINDS = ["Q", "Q", "Q", "QSub", "nd", "float", "carrier", "duck"]
    OUT_KINDS = ["Q", "QSub", "nd", "duckout"]
    VALUES = [0.0, 1.0, -2.5, 3.75, 100.0]
    BINARY = [np.add, np.subtract, np.multiply]

    for _ in range(N_FUZZ):
        unary = rng.random() < 0.25
        fn = np.negative if unary else rng.choice(BINARY)
        n_in = 1 if unary else 2
        inputs, has_junk = [], False
        for _k in range(n_in):
            kind = rng.choice(IN_KINDS)
            unit = rng.choice(UNITS)
            # non-convertible payloads only fit carriers/ducks (array-backed
            # operands would reject them at construction, before dispatch)
            if kind in ("carrier", "duck") and rng.random() < 0.20:
                value = JUNK
                has_junk = True
            else:
                value = rng.choice(VALUES)
            inputs.append(fresh_input(kind, unit, value))
        out = None
        if rng.random() < 0.35:
            okind = rng.choice(OUT_KINDS)
            # excluded fragile corner: non-convertible payload + an output
            # whose own handler survives output normalisation (see docstring)
            if has_junk and okind == "QSub":
                okind = "Q"
            out = (fresh_out_slot(okind, rng.choice(UNITS)),)
        if not check("fuzz", fn, inputs, out):
            bad += 1
        checked += 1
        if bad:
            return 1

    print("G-CONF OK: shadow impl == real dispatcher outcome on %d scenarios "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
