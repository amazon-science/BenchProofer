#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-10356.

The changed operation is modelled DEEPLY in model.py: `concat_chain` is the
front-recursive concatenation of a chain of per-member own-token lists, and the
contract pins

  (consider_chain=True)   result == concat_chain(chain)              [all members]
  (consider_chain=False)  result == chain[0]                         [class only]

This check validates that deep model against the REAL callee
`_pytest.mark.structures.get_unpacked_marks` (the patched function). There is no
consumed @ContractOnly axiom; this is the A-reference validation.

The chain abstraction (model.py) ↔ reality:
  chain                = [ own_marks(cls) for cls in obj.__mro__ ]
  chain[k] (PSeq[int]) = the marks directly attached to the k-th class in the
                         method-resolution order (its own `__dict__["pytestmark"]`,
                         normalised), each mark identified by its `name`.
  concat_chain(chain)  = the MRO-ordered concatenation of all members' own marks.

Soundness obligations asserted at the SAME (ordered, per-mark) level the model
decides -- NOT via a value-membership proxy:

  (A-reference, full chain)  get_unpacked_marks(C) (as a name list)
                             == concat_chain([own_marks(m) for m in C.__mro__])
  (A-reference, class only)  get_unpacked_marks(C, consider_mro=False)
                             == own_marks(C)          (= chain[0])

Inputs: boundary class shapes (single, linear, diamond, multiple inheritance,
empty marks, several marks per class) plus randomised fuzz over random DAGs of
classes with random own-mark sets. The F2P shape (C(A,B), each decorated) is
enumerated explicitly and the check fails loudly if it is ever skipped.

Imports only the standard library plus the package under test (`pytest` /
`_pytest`), exactly as the gold patch does. Exit 0 iff every obligation holds.
"""
import random
import sys

import pytest
from _pytest.mark.structures import get_unpacked_marks, normalize_mark_list


# --- chain abstraction over the REAL linearisation (model.py's `chain`) ------

def own_marks(cls):
    """The k-th chain member: the marks DIRECTLY attached to `cls` (its own
    `__dict__["pytestmark"]`, normalised the same way the real code does),
    rendered as the list of mark names. This is `chain[k]` in model.py."""
    raw = cls.__dict__.get("pytestmark", [])
    if not isinstance(raw, list):
        raw = [raw]
    return [m.name for m in normalize_mark_list(raw)]


def model_concat_chain(cls):
    """`concat_chain(chain)`: MRO-ordered concatenation of every member's own
    marks. Computed independently of get_unpacked_marks (no double-mask)."""
    out = []
    for member in cls.__mro__:
        out.extend(own_marks(member))
    return out


def real_names(cls, consider_mro):
    """The REAL callee's output, as a list of mark names."""
    return [m.name for m in get_unpacked_marks(cls, consider_mro=consider_mro)]


def check_class(cls, label):
    # (A-reference, full chain): real == deep-model concatenation, in order.
    real_full = real_names(cls, True)
    model_full = model_concat_chain(cls)
    assert real_full == model_full, (
        "FULL-CHAIN unsound on %s: get_unpacked_marks=%r, "
        "concat_chain(chain)=%r" % (label, real_full, model_full))
    # (A-reference, class only): real == chain[0] (the class's own marks).
    real_self = real_names(cls, False)
    model_self = own_marks(cls)  # chain[0]
    assert real_self == model_self, (
        "CLASS-ONLY unsound on %s: get_unpacked_marks(consider_mro=False)=%r, "
        "chain[0]=%r" % (label, real_self, model_self))


def make_class(name, bases, mark_names):
    """Build a class with the given bases and decorate it with the named marks
    (in order) via the real pytest decorator path (store_mark)."""
    cls = type(name, tuple(bases), {})
    for mn in mark_names:
        cls = getattr(pytest.mark, mn)(cls)
    return cls


def main():
    saw_f2p_shape = False

    # --- boundary: the exact F2P shape, enumerated explicitly --------------
    A = make_class("A", [], ["a"])
    B = make_class("B", [], ["b"])
    C = make_class("C", [A, B], ["c"])
    # The discriminating F2P assertions, named-level:
    assert real_names(C, True) == ["c", "a", "b"], real_names(C, True)
    assert real_names(C, False) == ["c"], real_names(C, False)
    check_class(A, "F2P:A")
    check_class(B, "F2P:B")
    check_class(C, "F2P:C(A,B)")
    saw_f2p_shape = True

    # --- boundary: single, undecorated, linear, multi-mark, diamond -------
    U = make_class("U", [], [])                       # undecorated
    check_class(U, "undecorated")

    L0 = make_class("L0", [], ["x"])
    L1 = make_class("L1", [L0], ["y"])
    L2 = make_class("L2", [L1], ["z"])                # linear chain
    check_class(L2, "linear L2<-L1<-L0")

    M = make_class("M", [], ["p", "q", "r"])          # several own marks
    check_class(M, "multi-mark")

    D0 = make_class("D0", [], ["d0"])
    D1 = make_class("D1", [D0], ["d1"])
    D2 = make_class("D2", [D0], ["d2"])
    D3 = make_class("D3", [D1, D2], ["d3"])           # diamond
    check_class(D3, "diamond D3")

    # some bases undecorated, some decorated
    E0 = make_class("E0", [], [])
    E1 = make_class("E1", [], ["e1"])
    E2 = make_class("E2", [E0, E1], [])               # own empty, base decorated
    check_class(E2, "mixed-empty E2")

    # --- randomised fuzz over random class DAGs ----------------------------
    rng = random.Random(10356)
    pool_names = ["m%d" % k for k in range(12)]
    for trial in range(4000):
        classes = []
        n = rng.randint(1, 7)
        for idx in range(n):
            # pick bases from already-created classes (a DAG, MRO-consistent)
            k = rng.randint(0, min(2, len(classes)))
            bases = rng.sample(classes, k) if k and classes else []
            nm = rng.randint(0, 3)
            marks = [rng.choice(pool_names) for _ in range(nm)]
            try:
                cls = make_class("T%d_%d" % (trial, idx), bases, marks)
            except TypeError:
                # inconsistent MRO from the random base choice; skip this class
                continue
            classes.append(cls)
            check_class(cls, "fuzz T%d_%d" % (trial, idx))

    if not saw_f2p_shape:
        print("G-AX FAIL: F2P shape was never exercised", file=sys.stderr)
        return 1

    print("G-AX OK: concat_chain deep model == real get_unpacked_marks over "
          "F2P + boundary shapes + ~4000 fuzz hierarchies (full chain and "
          "class-only), 0 violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
