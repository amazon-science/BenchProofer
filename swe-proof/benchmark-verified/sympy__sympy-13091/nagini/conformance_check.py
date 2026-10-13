#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13091 (nagini).

SHADOW  — the impl regions of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures, MustTerminate) stripped; the
          @Pure helpers (EQ_FALSE/EQ_TRUE/EQ_NI, eq_code, op_eq) copy over
          as plain functions. No @ContractOnly callees in this bundle
          (op_eq is a deep model of the language-level operator dispatch,
          spelled out in the pure region).

BRIDGE  — mapping.md section 2: a right-hand object is observed through two
          predicates — `sympifiable` (the strict coercion of the object to a
          comparable peer succeeds) and `content_equal` (when coercible, the
          symbolic value's own definite verdict on the coerced peer, an
          unchanged content comparison) — and through `other_answer`, the
          three-valued reply of the right-hand object's own reflected
          equality (True <-> 1, False <-> 0, the delegation sentinel <-> 2).
          The shadow's three-valued output code maps back through the same
          reply bijection.

ORACLE  — the REAL patched rich-comparison methods (PYTHONPATH=/testbed,
          gold patch applied by the gate before this script runs):
            sym_eq  vs the raw reply of type(self).__eq__(self, other) on
                    real symbolic values of the four patched reply families
                    (expression/symbol, rational/integer, float, symbolic
                    constant);
            sym_ne  vs the fully-resolved `self != other` operator result.

Input domain: the modeled preconditions demand mode codes in {0,1,2} (met by
construction of the bridge) and totality; every (self, other) pair is
Requires-satisfying. Right-hand objects range over equal peers, unequal
peers, coercible plain numbers, and foreign (non-coercible) objects whose
own equality replies True / False / the delegation sentinel — including the
symmetry witness (a foreign object that considers itself equal).

>= 1e5 Requires-satisfying inputs: 50000 cases x 2 modeled functions,
boundary cases first. Pinned seed: 13091.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo package only.
"""
import random
import sys

SEED = 13091
N_CASES = 50_000

# ---------------------------------------------------------------------------
# model.py pure region, copied over as plain functions (@Pure and the
# Ensures/Requires ghost lines stripped).
# ---------------------------------------------------------------------------


def EQ_FALSE():
    # the comparison answers a definite "not equal"
    return 0


def EQ_TRUE():
    # the comparison answers a definite "equal"
    return 1


def EQ_NI():
    # the delegation sentinel: "undecided, ask the other side"
    return 2


def eq_code(sympifiable, content_equal):
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()


def op_eq(self_answer, other_answer):
    if self_answer != EQ_NI():
        return self_answer == EQ_TRUE()
    if other_answer != EQ_NI():
        return other_answer == EQ_TRUE()
    return False


# ---------------------------------------------------------------------------
# model.py impl regions, VERBATIM with contract statement lines
# (Requires/Ensures) stripped.
# ---------------------------------------------------------------------------


def sym_eq(sympifiable, content_equal):
    if not sympifiable:
        return EQ_NI()
    if content_equal:
        return EQ_TRUE()
    return EQ_FALSE()


def sym_ne(sympifiable, content_equal, other_answer):
    e = sym_eq(sympifiable, content_equal)
    return not op_eq(e, other_answer)


# ---------------------------------------------------------------------------
# Bridge helpers.
# ---------------------------------------------------------------------------


def reply_code(reply):
    """Three-valued rich-comparison reply -> int code."""
    if reply is NotImplemented:
        return EQ_NI()
    return EQ_TRUE() if reply else EQ_FALSE()


class ForeignTrue(object):
    """A non-coercible object that considers itself equal to anything
    (the symmetry witness)."""
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return 0


class ForeignFalse(object):
    """A non-coercible object that considers itself unequal to anything."""
    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return 0


class ForeignNI(object):
    """A non-coercible object that leaves equality undecided (the default
    object protocol reply)."""
    __hash__ = object.__hash__


def run_case(self_val, other, _sympify, SympifyError):
    """One (symbolic value, right-hand object) pair: bridge the inputs, run
    both modeled functions against the real replies. Returns an error string
    on disagreement, else None."""
    # bridge input 1: does the strict coercion accept the right-hand object?
    try:
        coerced = _sympify(other)
        sympifiable = True
    except (SympifyError, TypeError, ValueError):
        coerced = None
        sympifiable = False

    # bridge input 2: the unchanged content comparison on the coerced peer
    # (the symbolic value's own definite verdict against a genuine peer)
    if sympifiable:
        peer_reply = type(self_val).__eq__(self_val, coerced)
        if peer_reply is NotImplemented:
            # outside the modeled domain slice: the reply families under
            # test answer definitely on coerced peers
            return None
        content_equal = bool(peer_reply)
    else:
        content_equal = False

    # bridge input 3: the right-hand object's own reflected equality reply
    other_answer = reply_code(type(other).__eq__(other, self_val))

    # --- modeled function #1: the three-valued equality reply --------------
    real_eq_code = reply_code(type(self_val).__eq__(self_val, other))
    shadow_eq_code = sym_eq(sympifiable, content_equal)
    if shadow_eq_code != real_eq_code:
        return ("DISAGREEMENT (equality reply)\n"
                "  self=%r other=%r (type %s)\n"
                "  bridge: sympifiable=%r content_equal=%r\n"
                "  shadow code=%r  real code=%r"
                % (self_val, other, type(other).__name__, sympifiable,
                   content_equal, shadow_eq_code, real_eq_code))

    # --- modeled function #2: the resolved inequality -----------------------
    real_ne = bool(self_val != other)
    shadow_ne = sym_ne(sympifiable, content_equal, other_answer)
    if shadow_ne != real_ne:
        return ("DISAGREEMENT (inequality)\n"
                "  self=%r other=%r (type %s)\n"
                "  bridge: sympifiable=%r content_equal=%r other_answer=%r\n"
                "  shadow=%r  real=%r"
                % (self_val, other, type(other).__name__, sympifiable,
                   content_equal, other_answer, shadow_ne, real_ne))
    return None


def main():
    import sympy
    from sympy import Symbol, Integer, Rational, Float, pi, E
    from sympy.core.sympify import _sympify, SympifyError

    x = Symbol("x")
    y = Symbol("y")

    # symbolic values covering the patched reply families: expression/symbol
    # (Basic), integer/rational (Rational), float (Float), constant
    # (NumberSymbol)
    selves = [
        x, x + 1, x * y,
        Integer(0), Integer(3), Integer(-7), Rational(1, 2), Rational(-5, 3),
        Float(2.5), Float(0.0), Float(-1e10),
        pi, E,
    ]

    def peers(rng):
        """Right-hand objects: peers, coercible numbers, foreign objects."""
        return [
            x, x + 1, y, Integer(3), Rational(1, 2), Float(2.5), pi,
            0, 3, -7, 2, int(rng.randint(-10**6, 10**6)),
            2.5, 0.0, float(rng.uniform(-1e6, 1e6)),
            Rational(rng.randint(-100, 100), rng.randint(1, 100)),
            ForeignTrue(), ForeignFalse(), ForeignNI(),
            "not a peer", (1, 2), [1, 2], {"a": 1}, None, object(),
        ]

    rng = random.Random(SEED)

    # boundary sweep: every symbolic value against every right-hand kind
    boundary = [(s, o) for s in selves for o in peers(rng)]

    checked = 0
    cases = 0
    for s, o in boundary:
        err = run_case(s, o, _sympify, SympifyError)
        if err:
            print("G-CONF FAIL (seed=%d):" % SEED)
            print(err)
            return 1
        cases += 1
        checked += 2

    while cases < N_CASES:
        s = rng.choice(selves)
        o = rng.choice(peers(rng))
        err = run_case(s, o, _sympify, SympifyError)
        if err:
            print("G-CONF FAIL (seed=%d):" % SEED)
            print(err)
            return 1
        cases += 1
        checked += 2

    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "rich-comparison replies on %d modeled-function inputs "
          "(%d cases, seed=%d), 0 disagreements." % (checked, cases, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
