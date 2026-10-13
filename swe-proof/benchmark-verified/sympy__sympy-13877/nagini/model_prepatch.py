"""Twin-artifact model for sympy__sympy-13877.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Computing the determinant of a dense symbolic matrix by fraction-free
  elimination requires, at each elimination step, choosing a pivot from a
  column of expressions. A usable pivot must be an entry that is genuinely
  (mathematically) non-zero. Some entries have a non-trivial expression
  structure yet are mathematically equal to zero (for instance an entry whose
  apparent form hides an exact cancellation); these must NOT be chosen as a
  pivot, and dividing by one of them corrupts the computation.

  The pivot to use is therefore the entry of LOWEST index whose value is
  genuinely non-zero. If every entry of the column is mathematically zero, the
  column admits NO pivot, and that elimination step contributes a zero
  determinant.

  Domain of the model: columns of symbolic/exact entries — i.e. columns NOT
  consisting entirely of machine-precision numbers. (A column made up entirely
  of machine-precision numbers is handled by a separate magnitude-based
  selection rule that needs the entries' numeric values; the status-code
  abstraction below carries no magnitudes, so that configuration lies outside
  this model's boundary. See mapping.md §2 for why nothing observable depends
  on it.)

Each column entry is modelled by an integer status code (mapping.md §2): a code
denoting an entry that is mathematically zero (a literal zero, or a
structurally non-trivial expression that is nonetheless exactly zero) versus
one that is genuinely non-zero. The deciding predicate `is_genuinely_zero` is
the model of the real mathematical zero test; its agreement with the real
callee is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

The returned index `-1` signals "no usable pivot" (a zero contribution).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axiom is consumed by the proof. The mathematical zero-test
#  is modelled DEEPLY by `is_genuinely_zero` below, in the pure region, and
#  validated equal to the real library zero-test out-of-band by G-AX. See
#  refinement.md A-reference and mapping.md §3.1.)
# axioms-end


# pure-start
@Pure
def is_genuinely_zero(e: int) -> bool:
    """Is this column entry mathematically (genuinely) zero?

    Deep model of the mathematical zero test the pivot search must use. An
    entry is genuinely zero exactly when its status code is non-positive: a
    literal zero (code 0) or a structurally non-trivial entry that is
    nonetheless exactly zero (negative code). A genuinely non-zero entry has a
    positive code. (Validated == the real callee by G-AX; mapping.md §2,§3.1.)
    """
    return e <= 0


@Pure
def first_usable(s: PSeq[int], k: int) -> int:
    """Lowest index >= k of an entry that is NOT genuinely zero; `len(s)` if no
    such entry exists in s[k:]. Front-recursive so each loop step gets exactly
    one unfold."""
    Requires(0 <= k and k <= len(s))
    Ensures(k <= Result() and Result() <= len(s))
    # The result is in-range-or-len; every entry strictly before it (from k) is
    # genuinely zero, and (if in range) the result entry is not.
    Ensures(Forall(int, lambda t: (Implies(k <= t and t < Result(),
                                            is_genuinely_zero(s[t])),
                                    [[s[t]]])))
    Ensures(Implies(Result() < len(s), not is_genuinely_zero(s[Result()])))
    if k == len(s):
        return len(s)
    if not is_genuinely_zero(s[k]):
        return k
    return first_usable(s, k + 1)
# pure-end


def lowest_live_index(col: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(col), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(col), 1 / 2))
    # The pivot is the lowest-index genuinely-non-zero entry, or -1 ("no pivot").
    Ensures(-1 <= Result() and Result() < len(col))
    # No usable pivot  <=>  every entry is genuinely zero.
    Ensures((Result() == -1) == (first_usable(ToSeq(col), 0) == len(col)))
    # When a pivot exists, it is exactly the lowest non-zero index, so every
    # entry strictly before it IS genuinely zero ...
    Ensures(Implies(Result() != -1, Result() == first_usable(ToSeq(col), 0)))
    Ensures(Implies(Result() != -1,
                    Forall(int, lambda t: (Implies(0 <= t and t < Result(),
                                                   is_genuinely_zero(col[t])),
                                           [[col[t]]]))))
    # ... and the chosen entry itself is NOT genuinely zero.
    Ensures(Implies(Result() != -1, not is_genuinely_zero(col[Result()])))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(col):
        # invariants-start
        Invariant(Acc(list_pred(col), 1 / 2))
        Invariant(0 <= i and i <= len(col))
        # Everything scanned so far is genuinely zero.
        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
                                                  is_genuinely_zero(col[t])),
                                          [[col[t]]])))
        # ... which is exactly first_usable not yet having fired.
        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
        # invariants-end
        # PRE-PATCH BUG: a structural non-zero test (col[i] != 0) instead of the
        # mathematical zero test. A structurally non-trivial entry that is
        # genuinely zero (negative code) tests non-zero, so it is wrongly
        # accepted as a pivot.
        if col[i] != 0:
            return i
        i = i + 1
    return -1
    # impl-end
