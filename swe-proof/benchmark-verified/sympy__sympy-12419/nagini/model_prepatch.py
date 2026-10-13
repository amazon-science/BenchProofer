"""Twin-artifact model for sympy__sympy-12419.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The (i, j) entry of an identity matrix, where i and j are index expressions
  that may be symbolic. The entry depends on the *symbolic* equality of the two
  indices, classified three ways by the unchanged equality decision procedure:

    - if the two indices are decidably EQUAL, the entry is the unit value;
    - if they are decidably UNEQUAL, the entry is the zero value;
    - if equality cannot be decided (the indices are symbolic and neither
      provably equal nor provably unequal), the entry is the deferred symbolic
      value.

  Producing the entry is a single bounded decision: the operation MUST
  terminate and deliver its result (a total-correctness obligation, carried as
  ``MustTerminate`` in the precondition). An implementation that diverges
  before returning — e.g. by re-invoking the entry on the same indices, or
  spinning in a loop — would satisfy the value postconditions only vacuously
  and never deliver an entry; the real operation always returns.

Index expressions are modelled as opaque `int` identity tags; the model never
does arithmetic on them. The result is a 3-valued *tag* identifying which of
the three cell values the entry is (unit / zero / deferred symbolic), not a
number to be summed. Two unchanged equality callees are axiomatized: the 3-valued
equality decision `eq_class` (the equality of the two index expressions,
classified as provably-equal / provably-unequal / undecided) and the structural
identity `struct_eq` (tree-level sameness of the two expressions); their
soundness — including the structural-identity ⟹ provably-equal link — is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# The three outcomes of the unchanged equality-decision callee.
EQ_FALSE = 0    # the two indices are provably unequal
EQ_TRUE = 1     # the two indices are provably equal
EQ_UNKNOWN = 2  # equality of the two indices is undecided

# The three possible cell values, as pairwise-distinct tags. Chosen disjoint
# from the EQ_* codes so the entry cannot be produced by echoing the classifier;
# it must be produced by genuinely branching on it.
ZERO = 10       # the zero cell value
ONE = 11        # the unit cell value
DEFERRED = 12   # the deferred symbolic cell value


# axioms-start
@Pure
@ContractOnly
def eq_class(i: int, j: int) -> int:
    """Unchanged callee: the equality-decision procedure for the two index
    expressions, read as a 3-valued outcome (provably-equal / provably-unequal /
    undecided). Returns one of EQ_TRUE, EQ_FALSE, EQ_UNKNOWN. Reflexive:
    identical indices are decidably equal. The weakest contract the proof needs
    — it does NOT claim any undecided pair is decided.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == EQ_FALSE or Result() == EQ_TRUE
            or Result() == EQ_UNKNOWN)
    Ensures(Implies(i == j, Result() == EQ_TRUE))


@Pure
@ContractOnly
def struct_eq(i: int, j: int) -> bool:
    """Unchanged callee: structural (tree) identity of two index expressions
    (Python `==`). Reflexive. Structural identity is a SUFFICIENT condition for
    the equality decision: it implies the equality-decision callee classifies
    the pair as provably-equal (the converse does NOT hold — two structurally-
    distinct expressions may still be equal or undecided).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(i == j, Result()))
    Ensures(Implies(Result(), eq_class(i, j) == EQ_TRUE))
# axioms-end


# pure-start
# (no deep-model helpers: the changed operation is a 3-way branch on the
#  axiomatized equality callee, modelled directly in the impl.)
# pure-end


def diagonal_unit_entry(i: int, j: int) -> int:
    # pre-conditions-start
    # TERMINATION: producing the entry is a bounded, loop-free decision that
    # always returns a cell value. An implementation that diverges would meet
    # the value postconditions only vacuously and never deliver an entry;
    # this obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The entry is exactly one of the three cell tags.
    Ensures(Result() == ZERO or Result() == ONE or Result() == DEFERRED)
    # Decidably equal indices -> the unit cell.
    Ensures(Implies(eq_class(i, j) == EQ_TRUE, Result() == ONE))
    # Decidably unequal indices -> the zero cell.
    Ensures(Implies(eq_class(i, j) == EQ_FALSE, Result() == ZERO))
    # Undecided indices -> the deferred symbolic cell.
    Ensures(Implies(eq_class(i, j) == EQ_UNKNOWN, Result() == DEFERRED))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: decides the entry by structural identity only,
    # treating every structurally-distinct pair as the zero cell — including
    # undecided symbolic pairs, which must instead yield the deferred cell.
    if struct_eq(i, j):
        return ONE
    else:
        return ZERO
    # impl-end
