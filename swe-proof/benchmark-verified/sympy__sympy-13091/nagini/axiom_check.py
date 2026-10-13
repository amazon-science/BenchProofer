#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13091.

The model has ONE deep-model reference (A-reference), no consumed axiom:

  (A-reference) `op_eq(self_answer, other_answer)` (model.py pure region) is the
      fully-resolved Python `==` OPERATOR on two three-valued equality replies.
      The model encodes:
        * if the left object's __eq__ is decided (True/False), `==` is that bool;
        * else if the right object's __eq__ is decided, `==` is that bool
          (delegation to the reflected method);
        * else (both undecided / NotImplemented) `==` falls back to object
          identity -> distinct objects are NOT equal -> False.
      This is exactly CPython's rich-comparison dispatch for `==`. We validate
      `op_eq` against the REAL Python operator by constructing objects whose
      `__eq__` returns each of the three protocol replies (True / False /
      NotImplemented) and observing `left == right`.

We additionally validate, on the SAME real objects, the two behaviours the model
pins for the symbolic comparison protocol:

  * sym_eq: a symbolic value's __eq__ returns NotImplemented (the delegation
    sentinel) for an incomparable peer, and a definite bool for a comparable
    peer. With NotImplemented (not False), a foreign object that considers
    itself equal is honoured symmetrically.
  * sym_ne: inequality == `not (left == right)` (the resolved operator), so the
    behaviour is symmetric; whereas the buggy `not left.__eq__(right)` would
    coerce the truthy NotImplemented sentinel and give the wrong answer.

Imports nothing repo-specific: only the CPython data-model protocol (the very
mechanism the gold patch relies on). Exit 0 iff every obligation holds.
"""
import itertools
import sys

EQ_FALSE = 0
EQ_TRUE = 1
EQ_NI = 2
_CODES = (EQ_FALSE, EQ_TRUE, EQ_NI)


def _reply(code):
    """Map a three-valued code to the value a real __eq__ should return."""
    if code == EQ_TRUE:
        return True
    if code == EQ_FALSE:
        return False
    return NotImplemented


class Obj(object):
    """A real Python object whose `__eq__` returns a chosen protocol reply
    (True / False / NotImplemented). `__ne__` is the gold-faithful
    `not self == other`, so the pair forms a faithful rich-comparison peer."""

    def __init__(self, code):
        self.code = code

    def __eq__(self, other):
        return _reply(self.code)

    def __ne__(self, other):
        return not self == other

    # an identity-based hash so distinct instances are genuinely distinct keys
    __hash__ = object.__hash__


# --- model.py reference encoding of op_eq (kept in lock-step) ----------------

def op_eq_model(self_answer, other_answer):
    """Reference implementation of model.py's deep model `op_eq`."""
    if self_answer != EQ_NI:
        return self_answer == EQ_TRUE
    if other_answer != EQ_NI:
        return other_answer == EQ_TRUE
    return False


def sym_ne_model(self_answer, other_answer):
    """model.py `sym_ne`: complement of the fully-resolved `==` operator."""
    return not op_eq_model(self_answer, other_answer)


def main():
    checked = 0

    # --- op_eq (A-reference) == real Python `==` dispatch, all 3x3 cases -----
    # Two real objects, the left exhibiting `self_answer`, the right `other_answer`.
    for self_answer, other_answer in itertools.product(_CODES, _CODES):
        left = Obj(self_answer)
        right = Obj(other_answer)

        observed_eq = (left == right)          # REAL CPython `==` dispatch
        # `==` must yield a genuine bool here (no NotImplemented leaks out)
        assert isinstance(observed_eq, bool), (
            "real `==` did not resolve to bool for codes %r,%r: got %r"
            % (self_answer, other_answer, observed_eq))

        expected_eq = op_eq_model(self_answer, other_answer)
        assert observed_eq == expected_eq, (
            "op_eq deep model unsound for self=%r other=%r: real `==` gave %r, "
            "model gives %r" % (self_answer, other_answer, observed_eq, expected_eq))

        # --- sym_ne == `not (left == right)` on the SAME real objects --------
        observed_ne = (left != right)          # REAL CPython `!=` dispatch
        assert isinstance(observed_ne, bool), (
            "real `!=` did not resolve to bool for codes %r,%r: got %r"
            % (self_answer, other_answer, observed_ne))
        expected_ne = sym_ne_model(self_answer, other_answer)
        assert observed_ne == expected_ne, (
            "sym_ne model unsound for self=%r other=%r: real `!=` gave %r, "
            "model gives %r" % (self_answer, other_answer, observed_ne, expected_ne))

        # the gold-faithful __ne__ must agree with the resolved-operator model
        assert observed_ne == (not observed_eq), (
            "`a != b` != `not (a == b)` for codes %r,%r" % (self_answer, other_answer))

        checked += 1

    # --- the symmetry property the fix establishes ---------------------------
    # A symbolic value whose __eq__ returns the delegation sentinel (EQ_NI) for
    # an incomparable peer, paired with a peer that considers itself equal
    # (EQ_TRUE): `==` must be True from BOTH sides (symmetry).
    sym = Obj(EQ_NI)            # symbolic value: undecided about the foreign peer
    peer_eq = Obj(EQ_TRUE)      # foreign peer: considers itself equal
    assert (sym == peer_eq) is True, "delegation to reflected __eq__ failed (s == p)"
    assert (peer_eq == sym) is True, "symmetry of equality broken (p == s)"
    assert (sym != peer_eq) is False, "inequality not symmetric (s != p)"
    assert (peer_eq != sym) is False, "inequality not symmetric (p != s)"

    # A symbolic value (EQ_NI) vs a foreign peer that is genuinely unequal
    # (its __eq__ returns NotImplemented too -> identity fallback -> not equal).
    peer_ni = Obj(EQ_NI)
    assert (sym == peer_ni) is False, "distinct undecided objects must compare unequal"
    assert (sym != peer_ni) is True, "distinct undecided objects must be `!=` True"

    # --- the BUG these guard against: `not self.__eq__(other)` -----------------
    # The buggy __ne__ negates the raw three-valued reply; NotImplemented is
    # truthy, so `not NotImplemented` is False -> it would report (sym != peer_ni)
    # as False, contradicting the resolved-operator answer True. Confirm the
    # divergence is real (sanity that the spec discriminates the bug).
    raw = sym.__eq__(peer_ni)
    assert raw is NotImplemented
    # `not self.__eq__(other)` pre-patch form; NotImplemented is truthy so this
    # is False. (CPython warns about bool(NotImplemented) -- that warning is
    # itself the smell of the bug; silence it, the divergence is the point.)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        buggy_ne = (not raw)
    assert buggy_ne is False
    assert buggy_ne != (sym != peer_ni), (
        "the pre-patch `not self.__eq__(other)` should diverge from the gold "
        "`not self == other` on the incomparable-unequal case")

    print("G-AX OK: op_eq deep model (== real Python `==` dispatch) and the "
          "sym_eq/sym_ne protocol sound on all %d (3x3) reply combinations + "
          "symmetry/identity-fallback witnesses; pre-patch `not __eq__()` "
          "divergence confirmed." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
