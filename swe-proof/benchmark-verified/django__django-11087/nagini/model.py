"""Twin-artifact model for django__django-11087.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the deletion collector walks a relation to gather the related rows that
  a cascade must visit, it issues a SELECT over those rows. The set of columns
  that SELECT fetches is the behaviour pinned here: the query is to read only
  the fields it actually requires, so a column the deletion itself never needs
  is not fetched back.

  Two contracted functions carry that behaviour.

  (1) ``rows_exposed_to_observers`` reduces the pair of per-model boolean
      observations that the column decision consults down to the single boolean
      it needs. Its postconditions pin that boolean by value at every point of
      the two-flag domain.

  (2) ``select_cascade_fields`` returns the column set to fetch for one related
      set. Its inputs are the related model's full column set, the column set
      the pending query for that set would already fetch on its own, the
      sub-collection of consulted columns (the primary-key-style references)
      that a reduction of the fetch can still reach, that model's own row-identity
      column, and the three boolean inputs. Its postconditions pin the result
      by value on each cell of the decision partition.

      What is pinned is the observable column set in each case, not any
      particular means of arriving at it. Three cases are pinned as separate
      obligations:

        * when the fetch is reduced to the consulted columns, the set fetched is
          exactly those columns together with the row-identity column, which is
          always fetched whether or not it is itself one of the consulted
          columns;
        * when no consulted column is reachable by a reduction at all, the full
          column set is fetched;
        * when the fetch is left as the pending query had it, what that query
          already fetches is what is fetched -- which need not be the full
          column set, since it may carry a restriction of its own from wherever
          it was obtained.

      The reduction therefore applies only when at least one consulted column
      is still reachable by it; when none is, every column is fetched, and
      otherwise the pending query's own column set stands.

  The postconditions below, not this prose, are the specification: nothing about
  the required behaviour is stated here that they do not state formally.

Column identities are modelled as ``int`` tokens and a column set as a
``List[int]`` of those tokens (Nagini bans ``str`` indexing); the specification
is carried over ``PSeq[int]`` via ``ToSeq``. Membership of the primary-key token
in a column list is phrased as an indexed ``Exists`` rather than ``PSeq``
containment, because Viper relates the two only through an explicit witness.
The first function is called by the second (it is under specification, not an
axiom).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms: both modelled decisions are pure boolean / sequence
#  logic over the abstract observation flags and column tokens, spelled out in
#  full. There is no unchanged opaque callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def exposed_to_observers(pre: bool, post: bool) -> bool:
    """The single boolean that the column decision consults, as a function of the
    two boolean observations in its signature. Grounded in its arguments (it is
    not an opaque answer-key), so it constrains no value that the postconditions
    below do not already constrain.
    """
    return pre or post
# pure-end


def rows_exposed_to_observers(pre: bool, post: bool) -> bool:
    # pre-conditions-start
    # Two abstract boolean observations; plain booleans, no heap permission.
    # Total: every one of the four flag combinations is admissible.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is pinned by value at all four points of the two-flag domain:
    # a function of exactly these two arguments, monotone in each.
    Ensures(Result() == exposed_to_observers(pre, post))
    Ensures(Result() == (pre or post))
    Ensures(Implies(pre, Result() is True))
    Ensures(Implies(post, Result() is True))
    Ensures(Implies(not pre and not post, Result() is False))
    # post-conditions-end
    # impl-start
    return pre or post
    # impl-end


def select_cascade_fields(all_fields: List[int], already_selected: List[int],
                          referenced: List[int], pk: int,
                          whole_row_required: bool, pre: bool,
                          post: bool) -> List[int]:
    # pre-conditions-start
    # ``all_fields`` is the full column set of the related model;
    # ``already_selected`` is the column set the pending query for the related
    # set would fetch if the fetch were left as it stands; ``referenced`` is
    # the sub-collection of consulted columns that a reduction of the fetch can
    # still reach; ``pk`` is that model's row-identity column. The three lists are
    # read-only here (fractional permission, directive 5). The structural
    # assumptions are only the three that always hold of a real model: every
    # entry of ``referenced`` and of ``already_selected`` is one of the model's
    # columns, and the row-identity column is one of the model's columns too.
    # Nothing further is assumed -- ``referenced`` may be empty, may equal
    # ``all_fields``, may contain ``pk`` or omit it; ``already_selected`` may be
    # the whole column set or any part of it; and the three booleans range
    # freely over all eight combinations.
    Requires(Acc(list_pred(all_fields), 1 / 2))
    Requires(Acc(list_pred(already_selected), 1 / 2))
    Requires(Acc(list_pred(referenced), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(referenced),
                                             referenced[k] in ToSeq(all_fields)))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(already_selected),
                                             already_selected[k] in ToSeq(all_fields)))))
    Requires(pk in ToSeq(all_fields))
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the same fractional permission.
    Ensures(Acc(list_pred(all_fields), 1 / 2))
    Ensures(Acc(list_pred(already_selected), 1 / 2))
    Ensures(Acc(list_pred(referenced), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is pinned BY VALUE on each cell of the decision partition, so
    # the returned column set is determined by these seven inputs and no cell
    # may return another cell's set.
    #
    # Cell 1 -- rows not exposed, the whole row is not required, at least one
    # consulted column is still reachable by a reduction, and the
    # row-identity column is among those consulted: exactly the consulted
    # columns are fetched.
    Ensures(Implies(not whole_row_required
                    and not exposed_to_observers(pre, post)
                    and len(referenced) > 0
                    and Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)),
                    ToSeq(Result()) == ToSeq(referenced)))
    # Cell 2 -- same, but the row-identity column is NOT among the consulted
    # ones: it is fetched in addition to them, because the row-identity column
    # is always fetched.
    Ensures(Implies(not whole_row_required
                    and not exposed_to_observers(pre, post)
                    and len(referenced) > 0
                    and not Exists(int, lambda k: (0 <= k and k < len(referenced)
                                                   and referenced[k] == pk)),
                    ToSeq(Result()) == ToSeq(referenced) + PSeq(pk)))
    # Cell 3 -- rows not exposed, the whole row is not required, but NO
    # consulted column is reachable by a reduction at all: every column is
    # fetched -- including any the pending query was not itself going to fetch.
    Ensures(Implies(not whole_row_required
                    and not exposed_to_observers(pre, post)
                    and len(referenced) == 0,
                    ToSeq(Result()) == ToSeq(all_fields)))
    # Cell 4 -- the whole row is required, or the rows are exposed to an
    # observer: the pending query's own column set stands unchanged.
    Ensures(Implies(whole_row_required or exposed_to_observers(pre, post),
                    ToSeq(Result()) == ToSeq(already_selected)))
    # The reduction cell and the leave-alone cell with the helper unfolded to
    # its arguments, so the partition is grounded in the parameters and needs no
    # lemma about it.
    Ensures(Implies(not (whole_row_required or pre or post)
                    and len(referenced) > 0
                    and Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)),
                    ToSeq(Result()) == ToSeq(referenced)))
    Ensures(Implies(whole_row_required or pre or post,
                    ToSeq(Result()) == ToSeq(already_selected)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    exposed = rows_exposed_to_observers(pre, post)
    Assert(exposed == exposed_to_observers(pre, post))
    # No request is made when the whole row is required or the rows are exposed;
    # otherwise a narrowing is requested, and it can only be a narrowing when at
    # least one consulted column is still reachable by it.
    leave_alone = False
    if whole_row_required or exposed:
        leave_alone = True
    Assert(leave_alone == (whole_row_required
                           or exposed_to_observers(pre, post)))
    reduce_cols = False
    if not leave_alone and len(referenced) > 0:
        reduce_cols = True
    Assert(reduce_cols == (not whole_row_required
                           and not exposed_to_observers(pre, post)
                           and len(referenced) > 0))
    if leave_alone:
        i = 0
        while i < len(already_selected):
            # invariants-start
            Invariant(Acc(list_pred(already_selected), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(already_selected))
            Invariant(ToSeq(result) == ToSeq(already_selected).take(i))
            Invariant(MustTerminate(len(already_selected) - i + 1))
            # invariants-end
            result = result + [already_selected[i]]
            i = i + 1
        Assert(ToSeq(already_selected).take(len(already_selected))
               == ToSeq(already_selected))
        Assert(ToSeq(result) == ToSeq(already_selected))
    elif reduce_cols:
        n_ref = len(referenced)
        Assert(n_ref > 0)
        i = 0
        found = False
        while i < len(referenced):
            # invariants-start
            Invariant(Acc(list_pred(referenced), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(referenced) == n_ref)
            Invariant(0 <= i and i <= len(referenced))
            Invariant(ToSeq(result) == ToSeq(referenced).take(i))
            Invariant(found == Exists(int, lambda k: (0 <= k and k < i
                                                      and referenced[k] == pk)))
            Invariant(MustTerminate(len(referenced) - i + 1))
            # invariants-end
            if referenced[i] == pk:
                found = True
            result = result + [referenced[i]]
            i = i + 1
        Assert(ToSeq(referenced).take(len(referenced)) == ToSeq(referenced))
        Assert(found == Exists(int, lambda k: (0 <= k and k < len(referenced)
                                               and referenced[k] == pk)))
        # The row identity is retained whether or not it was named.
        if not found:
            result = result + [pk]
    else:
        Assert(not whole_row_required
               and not exposed_to_observers(pre, post)
               and len(referenced) == 0)
        i = 0
        while i < len(all_fields):
            # invariants-start
            Invariant(Acc(list_pred(all_fields), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(all_fields))
            Invariant(ToSeq(result) == ToSeq(all_fields).take(i))
            Invariant(MustTerminate(len(all_fields) - i + 1))
            # invariants-end
            result = result + [all_fields[i]]
            i = i + 1
        Assert(ToSeq(all_fields).take(len(all_fields)) == ToSeq(all_fields))
        Assert(ToSeq(result) == ToSeq(all_fields))
    return result
    # impl-end
