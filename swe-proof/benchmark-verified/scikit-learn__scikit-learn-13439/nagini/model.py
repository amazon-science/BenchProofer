"""Twin-artifact model for scikit-learn__scikit-learn-13439.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite estimator is built as an ORDERED collection of constituent
  stages. Client code that indexes the composite with an integer- or
  slice-based handle relies on the collection reporting its SIZE: a query for
  "how many stages does this composite hold?" must return the exact number of
  stages it was constructed from — every stage counted once, including the
  final stage and any inert placeholder stages, none omitted and none counted
  twice. The size is therefore the cardinality of the stage collection itself,
  so that an index handle spanning "from the start up to the size" covers the
  whole collection.

The stage collection is modelled as `List[int]`, one element per stage (the
element values — the (name, estimator) pairs — are irrelevant; only the
cardinality is observed). The reported size is an `int` equal to the length of
that collection. No callee is axiomatized: the behaviour is the length of the
input collection, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: the reported size is the length of the input
#  collection, modelled deeply.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


def composite_size(steps: List[int]) -> int:
    # pre-conditions-start
    # The stage collection is read-only: the size query never mutates it, so it
    # is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(steps), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(steps), 1 / 2))
    # The reported size is exactly the cardinality of the stage collection:
    # every stage counted once (final stage and inert placeholders included),
    # none omitted. Grounded in the actual input collection.
    Ensures(Result() == len(steps))
    # post-conditions-end
    # impl-start
    return len(steps)
    # impl-end
