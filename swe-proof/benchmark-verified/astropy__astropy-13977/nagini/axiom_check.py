#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13977.

The changed decision operation is modelled DEEPLY (no consumed @ContractOnly
axiom). This script validates the two deep-model facts the bundle relies on
against REAL Python / numpy:

  (A-reference 1) the per-operand kind flag. The gold patch classifies each
      input/output operand by whether its type's ``__array_ufunc__`` is one of
      the recognised built-in kinds:
          ignored = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)
          flag = 0  iff  getattr(type(io), "__array_ufunc__", None) in ignored
          flag = 1  otherwise (the operand supplies its own custom handler).
      We construct representative operands of each kind and assert the real
      membership test yields the flag the model's `has_override`/`all_recognised`
      predicate consumes.

  (A-reference 2) the decision itself. We transcribe the gold control flow
      (return NotImplemented when not all operands are ignored, else re-raise)
      and check it equals the model's outcome map
          success                          -> 0
          failure & all operands recognised -> 2 (surface the error)
          failure & some custom handler    -> 1 (abstain / NotImplemented)
      over boundary + fuzzed operand collections and failure flags.

Imports only `numpy` (and stdlib); nothing repo-specific. Exit 0 iff sound.
"""
import dataclasses
import random
import sys

import numpy as np


# --- the recognised-built-in-kind classification, exactly as the gold patch --
# `self` in the real method is a Quantity (an np.ndarray subclass). We emulate
# `type(self).__array_ufunc__` with a dedicated ndarray subclass that does NOT
# override __array_ufunc__ (so it inherits ndarray's) — matching the fact that
# Quantity's own __array_ufunc__ is the very method under change and is in its
# own ignored tuple.

class _SelfType(np.ndarray):
    """Stand-in for the dispatcher's own type (an ndarray subclass)."""


def _ignored_tuple(self_type):
    return (None, np.ndarray.__array_ufunc__, self_type.__array_ufunc__)


def real_flag(io, self_type):
    """The REAL per-operand flag the gold patch computes: 0 if the operand's
    type's __array_ufunc__ is in the ignored tuple, else 1."""
    ignored = _ignored_tuple(self_type)
    in_ignored = getattr(type(io), "__array_ufunc__", None) in ignored
    return 0 if in_ignored else 1


# --- model.py deep model, transcribed --------------------------------------

def all_recognised(flags):
    return all(f == 0 for f in flags)


def has_custom_handler(flags):
    return not all_recognised(flags)


def model_outcome(flags, recoverable_failure):
    """model.py dispatch_ufunc outcome code."""
    if not recoverable_failure:
        return 0
    if all_recognised(flags):
        return 2
    return 1


def gold_outcome(flags, recoverable_failure):
    """Reference transcription of the GOLD control flow, on flags + a failure
    flag. 0 = ordinary result; 1 = NotImplemented; 2 = raise."""
    if not recoverable_failure:
        return 0  # try-body succeeded; ordinary result returned
    # except (TypeError, ValueError):  ignored membership over inputs+outputs
    all_ignored = all(f == 0 for f in flags)
    if not all_ignored:
        return 1  # return NotImplemented
    return 2      # raise e


# --- representative operands of each kind -----------------------------------

@dataclasses.dataclass
class _DuckPlain:
    """An operand with NO __array_ufunc__ attribute on its type (like a dict,
    or the issue's DuckQuantity1/2): getattr(...,None) is None -> ignored."""
    data: object = None


@dataclasses.dataclass(eq=False)
class _DuckCustom:
    """An operand that DOES define its own __array_ufunc__ (the issue's
    DuckArray / the test's DuckQuantity3): NOT in the ignored tuple -> flag 1."""
    data: object = None

    def __array_ufunc__(self, function, method, *inputs, **kwargs):
        return NotImplemented


def main():
    self_type = _SelfType

    # operand kinds and their EXPECTED flag (model side)
    kinds = [
        ("None", None, 0),                          # type(None).__array_ufunc__ -> None
        ("python_scalar", 11.412, 0),               # float: no __array_ufunc__ -> None
        ("dict", {"a": 1}, 0),                       # dict: no __array_ufunc__ -> None
        ("ndarray", np.arange(3.0), 0),              # np.ndarray.__array_ufunc__ -> ignored
        ("self_type_instance",
         np.zeros(3).view(self_type), 0),            # type(self).__array_ufunc__ -> ignored
        ("duck_plain", _DuckPlain(7), 0),            # no __array_ufunc__ -> None -> ignored
        ("duck_custom", _DuckCustom(7), 1),          # custom override -> NOT ignored
    ]

    # (A-reference 1) per-operand flag == real membership outcome
    for name, io, expected in kinds:
        got = real_flag(io, self_type)
        assert got == expected, (
            "operand-kind flag unsound for %s: real membership gave flag %d, "
            "model assigns %d" % (name, got, expected))

    # operand pool for building collections, with their real flags
    pool = [(io, real_flag(io, self_type)) for _, io, _ in kinds]

    def collection_flags(items):
        return [real_flag(io, self_type) for io in items]

    # (A-reference 2) boundary collections: decision agrees, model == gold,
    # over both failure outcomes.
    boundary = [
        [],
        [None],
        [np.arange(2.0)],
        [_DuckCustom(1)],
        [np.arange(2.0), _DuckCustom(1)],            # ndarray + duck -> abstain on failure
        [_DuckCustom(1), np.arange(2.0)],
        [np.arange(2.0), np.arange(2.0)],            # all recognised -> surface on failure
        [np.zeros(2).view(self_type), _DuckCustom(1)],
        [1 * 1.0, {"a": 1}],                         # scalar + dict (the issue's q1 + {'a':1})
        [np.arange(2.0), _DuckPlain(1)],             # ndarray + plain duck (no override)
        [_DuckCustom(1), _DuckCustom(2), np.arange(2.0)],
    ]
    for items in boundary:
        flags = collection_flags(items)
        for failure in (False, True):
            m = model_outcome(flags, failure)
            g = gold_outcome(flags, failure)
            assert m == g, (
                "decision mismatch on %r failure=%s: model=%d gold=%d"
                % (items, failure, m, g))

    # (A-reference) fuzz: random collections of operand kinds, both failure flags
    rng = random.Random(13977)
    raw = [io for _, io, _ in kinds]
    for _ in range(20000):
        n = rng.randint(0, 6)
        items = [rng.choice(raw) for _ in range(n)]
        flags = collection_flags(items)
        # cross-check the deep predicates too
        assert has_custom_handler(flags) == (not all(f == 0 for f in flags))
        for failure in (False, True):
            m = model_outcome(flags, failure)
            g = gold_outcome(flags, failure)
            assert m == g, (
                "fuzz decision mismatch on flags=%r failure=%s: model=%d gold=%d"
                % (flags, failure, m, g))

    print("G-AX OK: per-operand kind classification == real __array_ufunc__ "
          "membership (%d kinds); decision map (model == gold) on %d boundary "
          "+ 20000 fuzz operand collections x 2 failure flags."
          % (len(kinds), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
