#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13821.

There is NO consumed `@ContractOnly` axiom in this bundle: the version ordering
is the *changed decision* and is modelled DEEPLY by the front-recursive fold
`lt_lex` (model.py pure region). G-AX validates that deep model against the REAL
callee it stands in for — Python's tuple comparison `<` (the operation
`Database.sqlite_version_info < (3, 9, 0)` the gold patch performs), an
A-reference.

Two obligations, both checked by running the real operation:

  (A-reference) `lt_lex(a, b)` (model.py) == the REAL Python tuple ordering
      `tuple(a) < tuple(b)` for every pair of version-component sequences. This
      is the lexicographic order: first differing component decides; a sequence
      that is a strict prefix of another is the smaller.

  (end-to-end) the accept/reject decision the model pins —
      reject iff `lt_lex(version, (3, 9, 0))` — equals the REAL decision
      `version_info < (3, 9, 0)` for runtime version tuples, including the
      discriminating F2P case `(3, 8, 11, 1)` (rejected: below 3.9.0) and the
      boundary `(3, 9, 0)` itself (accepted).

Imports nothing repo-specific: tuple comparison is a Python language operation.
Exit 0 iff every obligation holds.
"""
import random
import sys

MIN_VERSION = (3, 9, 0)   # model.py min_version()


def lt_lex(a, b):
    """Reference implementation of model.py's deep model `lt_lex` (component-wise
    / lexicographic strict-less), as a fold over two component lists."""
    a = list(a)
    b = list(b)
    while a and b:
        if a[0] < b[0]:
            return True
        if a[0] > b[0]:
            return False
        a = a[1:]
        b = b[1:]
    # one (or both) exhausted: the strict prefix is the smaller
    if not a and b:
        return True   # a is a strict prefix of b
    return False      # a longer-or-equal => not below


def check_lt_lex_reference(a, b):
    """Assert the deep model lt_lex(a, b) == the REAL Python tuple `<`."""
    model = lt_lex(a, b)
    real = (tuple(a) < tuple(b))     # the real callee: Python tuple comparison
    assert model == real, (
        "lt_lex deep model unsound on (%r, %r): model gave %r, real tuple "
        "comparison gives %r" % (tuple(a), tuple(b), model, real))


def check_decision(version):
    """Assert the modeled reject decision == the REAL `version < (3, 9, 0)`."""
    model_reject = lt_lex(version, MIN_VERSION)
    real_reject = (tuple(version) < MIN_VERSION)   # the real gold-patch test
    assert model_reject == real_reject, (
        "reject decision unsound on %r: model %r, real %r"
        % (tuple(version), model_reject, real_reject))


def main():
    # --- boundary version tuples (the cases the contract pins) -------------
    boundary = [
        (),
        (3,), (3, 8), (3, 9), (3, 10),
        (3, 8, 2),                     # old test's rejected version
        (3, 8, 3),                     # old threshold exactly
        (3, 8, 11), (3, 8, 11, 1),     # the new F2P discriminating version
        (3, 8, 99), (3, 8, 3, 0),
        (3, 9, 0),                     # new minimum exactly (accepted)
        (3, 9, 0, 0), (3, 9, 1), (3, 10, 0),
        (3, 11, 0),                    # Ubuntu Xenial (accepted)
        (2, 9, 9), (4, 0, 0),
        (3, 9), (3, 8, 3, 9, 9, 9),
    ]
    # pairwise A-reference check over all boundary pairs
    for a in boundary:
        for b in boundary:
            check_lt_lex_reference(a, b)
        check_decision(a)
    # also against the minimum, both directions
    for v in boundary:
        check_lt_lex_reference(v, MIN_VERSION)
        check_lt_lex_reference(MIN_VERSION, v)

    # --- randomized fuzz over component sequences --------------------------
    rng = random.Random(13821)
    for _ in range(50000):
        la = rng.randint(0, 5)
        lb = rng.randint(0, 5)
        a = [rng.randint(0, 12) for _ in range(la)]
        b = [rng.randint(0, 12) for _ in range(lb)]
        check_lt_lex_reference(a, b)
        check_decision(a)

    # --- the discriminating F2P facts, explicitly --------------------------
    assert lt_lex((3, 8, 11, 1), MIN_VERSION) is True, \
        "3.8.11.1 must be rejected (below 3.9.0)"
    assert (3, 8, 11, 1) < MIN_VERSION, "real: 3.8.11.1 < 3.9.0"
    assert lt_lex((3, 9, 0), MIN_VERSION) is False, \
        "3.9.0 must be accepted (not below itself)"
    assert not ((3, 9, 0) < MIN_VERSION), "real: 3.9.0 not < 3.9.0"
    # pre-patch threshold would have WRONGLY accepted the F2P version:
    assert not ((3, 8, 11, 1) < (3, 8, 3)), \
        "pre-patch threshold 3.8.3 would accept 3.8.11.1 (the bug)"

    print("G-AX OK: lt_lex deep model (== Python tuple comparison) sound on "
          "%d boundary pairs + 50000 fuzz pairs; reject decision == "
          "(version < (3, 9, 0)); F2P discriminator 3.8.11.1 rejected, 3.9.0 "
          "accepted." % (len(boundary) * len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
