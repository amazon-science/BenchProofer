"""Twin-artifact model for django__django-11490.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a compound query that restricts its result to a chosen list of columns
  is compiled, each of its component sub-queries must be given THAT chosen
  column list for the current compilation. Crucially this must hold every time
  the compound query is compiled, even when the very same component sub-query
  object is reused across compilations: a later compilation that asks for a
  DIFFERENT column list must produce that different list. So:

    (1) applying a chosen column list to a component sub-query CLASSIFIES each
        requested name against the derived columns that sub-query exposes at
        that moment: a requested name that names one of the derived columns the
        sub-query emits ahead of its own columns is served by that derived
        column; failing that, one that names a derived column the sub-query
        emits after its own columns is served by that one; every other
        requested name becomes one of the sub-query's OWN columns. The derived
        columns the sub-query goes on to expose are narrowed to exactly those
        that were requested. Hence a component exposing no derived columns ends
        up with its own column list equal to exactly the chosen list;

    (2) a compilation must not be able to lock in the component sub-query's
        column selection for later compilations: the reused (shared) component
        sub-query is observably left with no column list of its own AND with
        its derived columns un-narrowed after a compilation, so that a
        subsequent compilation choosing a different column list is neither
        silently forced to reuse the earlier one nor deprived of the derived
        columns that earlier one did not request; and

    (3) the per-compilation working object must CARRY the component sub-query's
        accumulated state: everything else the sub-query has built up that
        determines which rows it contributes must be preserved on the object
        the compilation actually uses. A working object built from a blank
        slate merely matching the column list loses that accumulated state and
        no longer contributes the rows the sub-query defines.

  Because the classification in (1) is made against the derived columns the
  working object exposes AT THAT MOMENT, and each application narrows them,
  applying a chosen column list to an already-narrowed working object does not
  agree with applying it once to a faithful copy of the shared sub-query: a
  derived column dropped by an earlier application is no longer recognised as
  derived by a later one, so a requested name that names it is then taken for
  one of the sub-query's own columns instead. The specification therefore pins
  the outcome of the CURRENT compilation as a function of the SHARED
  sub-query's own (un-narrowed) derived columns and the chosen list — which
  only a single application to a faithful copy achieves.

A sub-query is modelled as a minimal object carrying the touched aspects — its
own chosen column list, and the two ordered families of derived columns it
exposes (``leading``: emitted ahead of its own columns and taking precedence in
the classification; ``trailing``: emitted after them), each a ``List[int]`` of
column codes (an empty own-column list meaning "no column list chosen yet") —
together with the remainder of its accumulated per-query state, abstracted to a
single opaque ``int`` token (``state``). The two query operations the behaviour
rests on are modelled deeply at the value level: obtaining a per-compilation
working object that mirrors the input (same column selection, SAME state token)
without being tied to it, and applying a chosen column list to a working object
(which classifies and narrows exactly as in (1) and leaves its state token
alone).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Query:
    def __init__(self, columns: List[int], leading: List[int],
                 trailing: List[int], state: int) -> None:
        Requires(Acc(list_pred(columns)))
        Requires(Acc(list_pred(leading)))
        Requires(Acc(list_pred(trailing)))
        Requires(MustTerminate(1))
        Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
        Ensures(Acc(list_pred(self.columns)))  # type: ignore
        Ensures(ToSeq(self.columns) == Old(ToSeq(columns)))  # type: ignore
        Ensures(Acc(self.leading) and self.leading is leading)  # type: ignore
        Ensures(Acc(list_pred(self.leading)))  # type: ignore
        Ensures(ToSeq(self.leading) == Old(ToSeq(leading)))  # type: ignore
        Ensures(Acc(self.trailing) and self.trailing is trailing)  # type: ignore
        Ensures(Acc(list_pred(self.trailing)))  # type: ignore
        Ensures(ToSeq(self.trailing) == Old(ToSeq(trailing)))  # type: ignore
        Ensures(Acc(self.state) and self.state == state)  # type: ignore
        self.columns = columns
        self.leading = leading
        self.trailing = trailing
        self.state = state


# axioms-start
# (no @ContractOnly axioms: the two query operations the behaviour rests on are
#  both modelled deeply by the contracted functions below.)
# axioms-end


# pure-start
@Pure
def kept_leading(leading: PSeq[int], fields: PSeq[int]) -> PSeq[int]:
    """The leading derived columns a sub-query still exposes once the chosen
    column list ``fields`` has been applied to it: exactly those that were
    requested, kept in the sub-query's own order. Built from the LAST leading
    column backwards, so an append-loop tracks it with the invariant
    ``kept == kept_leading(prefix, fields)``."""
    if len(leading) == 0:
        return PSeq(0).take(0)
    if leading[len(leading) - 1] in fields:
        return (kept_leading(leading.take(len(leading) - 1), fields)
                + PSeq(leading[len(leading) - 1]))
    return kept_leading(leading.take(len(leading) - 1), fields)


@Pure
def kept_trailing(trailing: PSeq[int], fields: PSeq[int],
                  leading: PSeq[int]) -> PSeq[int]:
    """The trailing derived columns a sub-query still exposes once the chosen
    column list ``fields`` has been applied to it: those that were requested
    AND were not already claimed by a leading derived column of the same name
    (a requested name is classified against the leading family first), kept in
    the sub-query's own order. Back-recursive, as ``kept_leading``."""
    if len(trailing) == 0:
        return PSeq(0).take(0)
    if (trailing[len(trailing) - 1] in fields
            and not (trailing[len(trailing) - 1] in leading)):
        return (kept_trailing(trailing.take(len(trailing) - 1), fields, leading)
                + PSeq(trailing[len(trailing) - 1]))
    return kept_trailing(trailing.take(len(trailing) - 1), fields, leading)


@Pure
def own_columns(fields: PSeq[int], leading: PSeq[int],
                trailing: PSeq[int]) -> PSeq[int]:
    """The requested names a sub-query must carry as its OWN columns once the
    chosen column list ``fields`` has been applied to it: the ones naming
    neither a leading nor a trailing derived column it exposes, kept in the
    requested order. When the sub-query exposes no derived columns at all this
    is the whole chosen list. Back-recursive, as ``kept_leading``."""
    if len(fields) == 0:
        return PSeq(0).take(0)
    if (fields[len(fields) - 1] in leading
            or fields[len(fields) - 1] in trailing):
        return own_columns(fields.take(len(fields) - 1), leading, trailing)
    return (own_columns(fields.take(len(fields) - 1), leading, trailing)
            + PSeq(fields[len(fields) - 1]))
# pure-end


def detached_copy(q: Query) -> Query:
    # pre-conditions-start
    Requires(Acc(q.columns, 1 / 4))
    Requires(Acc(list_pred(q.columns), 1 / 4))
    Requires(Acc(q.leading, 1 / 4))
    Requires(Acc(list_pred(q.leading), 1 / 4))
    Requires(Acc(q.trailing, 1 / 4))
    Requires(Acc(list_pred(q.trailing), 1 / 4))
    Requires(Acc(q.state, 1 / 4))
    # the working object must actually be delivered: a compilation that never
    # finishes cannot satisfy this contract vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # the original is read-only: its fields and lists are returned untouched.
    Ensures(Acc(q.columns, 1 / 4))
    Ensures(Acc(list_pred(q.columns), 1 / 4))
    Ensures(Acc(q.leading, 1 / 4))
    Ensures(Acc(list_pred(q.leading), 1 / 4))
    Ensures(Acc(q.trailing, 1 / 4))
    Ensures(Acc(list_pred(q.trailing), 1 / 4))
    Ensures(Acc(q.state, 1 / 4))
    Ensures(ToSeq(q.columns) == Old(ToSeq(q.columns)))
    Ensures(ToSeq(q.leading) == Old(ToSeq(q.leading)))
    Ensures(ToSeq(q.trailing) == Old(ToSeq(q.trailing)))
    Ensures(q.state == Old(q.state))
    # a distinct, independent object whose column selection mirrors the
    # original's — its own column list AND both families of derived columns,
    # each in an independent container (updating one does not affect the other)
    # — and which carries the ORIGINAL's accumulated state token; a blank-slate
    # working object would not.
    Ensures(Acc(Result().columns))
    Ensures(Acc(list_pred(Result().columns)))
    Ensures(Acc(Result().leading))
    Ensures(Acc(list_pred(Result().leading)))
    Ensures(Acc(Result().trailing))
    Ensures(Acc(list_pred(Result().trailing)))
    Ensures(Acc(Result().state))
    Ensures(Result() is not q)
    Ensures(Result().columns is not q.columns)
    Ensures(Result().leading is not q.leading)
    Ensures(Result().trailing is not q.trailing)
    Ensures(ToSeq(Result().columns) == ToSeq(q.columns))
    Ensures(ToSeq(Result().leading) == ToSeq(q.leading))
    Ensures(ToSeq(Result().trailing) == ToSeq(q.trailing))
    Ensures(Result().state == q.state)
    # post-conditions-end
    # impl-start
    copied = []  # type: List[int]
    i = 0
    while i < len(q.columns):
        # invariants-start
        Invariant(Acc(q.columns, 1 / 4))
        Invariant(Acc(list_pred(q.columns), 1 / 4))
        Invariant(Acc(list_pred(copied)))
        Invariant(0 <= i and i <= len(q.columns))
        Invariant(ToSeq(q.columns) == Old(ToSeq(q.columns)))
        Invariant(ToSeq(copied) == ToSeq(q.columns).take(i))
        Invariant(MustTerminate(len(q.columns) - i))
        # invariants-end
        copied.append(q.columns[i])
        i = i + 1
    Assert(i == len(q.columns))
    Assert(ToSeq(q.columns).take(i) == ToSeq(q.columns))
    Assert(ToSeq(copied) == ToSeq(q.columns))

    front = []  # type: List[int]
    j = 0
    while j < len(q.leading):
        # invariants-start
        Invariant(Acc(q.leading, 1 / 4))
        Invariant(Acc(list_pred(q.leading), 1 / 4))
        Invariant(Acc(list_pred(front)))
        Invariant(0 <= j and j <= len(q.leading))
        Invariant(ToSeq(q.leading) == Old(ToSeq(q.leading)))
        Invariant(ToSeq(front) == ToSeq(q.leading).take(j))
        Invariant(MustTerminate(len(q.leading) - j))
        # invariants-end
        front.append(q.leading[j])
        j = j + 1
    Assert(ToSeq(q.leading).take(j) == ToSeq(q.leading))
    Assert(ToSeq(front) == ToSeq(q.leading))

    back = []  # type: List[int]
    k = 0
    while k < len(q.trailing):
        # invariants-start
        Invariant(Acc(q.trailing, 1 / 4))
        Invariant(Acc(list_pred(q.trailing), 1 / 4))
        Invariant(Acc(list_pred(back)))
        Invariant(0 <= k and k <= len(q.trailing))
        Invariant(ToSeq(q.trailing) == Old(ToSeq(q.trailing)))
        Invariant(ToSeq(back) == ToSeq(q.trailing).take(k))
        Invariant(MustTerminate(len(q.trailing) - k))
        # invariants-end
        back.append(q.trailing[k])
        k = k + 1
    Assert(ToSeq(q.trailing).take(k) == ToSeq(q.trailing))
    Assert(ToSeq(back) == ToSeq(q.trailing))

    result = Query(copied, front, back, q.state)
    Assert(result.columns is copied)
    Assert(ToSeq(result.columns) == ToSeq(q.columns))
    Assert(ToSeq(result.leading) == ToSeq(q.leading))
    Assert(ToSeq(result.trailing) == ToSeq(q.trailing))
    return result
    # impl-end


def with_columns(q: Query, fields: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(q.columns))
    Requires(Acc(list_pred(q.columns)))
    Requires(Acc(q.leading))
    Requires(Acc(list_pred(q.leading)))
    Requires(Acc(q.trailing))
    Requires(Acc(list_pred(q.trailing)))
    Requires(Acc(q.state, 1 / 2))
    Requires(Acc(list_pred(fields), 1 / 2))
    # a chosen column list is a RESTRICTION, so it names at least one column;
    # an empty list does not restrict anything and means something else
    # entirely (every column of the query's own table), which is outside the
    # behaviour under specification.
    Requires(len(fields) > 0)
    # applying a column list must complete: no vacuous satisfaction by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # the chosen column list itself is only READ: it comes back unchanged, so a
    # caller that applies a list still knows what it asked for afterwards.
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(ToSeq(fields) == Old(ToSeq(fields)))
    Ensures(Acc(q.columns))
    Ensures(Acc(list_pred(q.columns)))
    Ensures(Acc(q.leading))
    Ensures(Acc(list_pred(q.leading)))
    Ensures(Acc(q.trailing))
    Ensures(Acc(list_pred(q.trailing)))
    # the requested names are CLASSIFIED against the derived columns the query
    # exposed when the list was applied: the query keeps as its own columns
    # exactly the requested names that name none of them, and the derived
    # columns it goes on to expose are narrowed to exactly the requested ones
    # (a requested name is matched against the leading family first). Applying
    # a column list does not disturb the query's other accumulated state.
    Ensures(ToSeq(q.columns) == own_columns(ToSeq(fields),
                                            Old(ToSeq(q.leading)),
                                            Old(ToSeq(q.trailing))))
    Ensures(ToSeq(q.leading) == kept_leading(Old(ToSeq(q.leading)),
                                             ToSeq(fields)))
    Ensures(ToSeq(q.trailing) == kept_trailing(Old(ToSeq(q.trailing)),
                                               ToSeq(fields),
                                               Old(ToSeq(q.leading))))
    Ensures(Acc(q.state, 1 / 2))
    Ensures(q.state == Old(q.state))
    # post-conditions-end
    # impl-start
    kept_front = []  # type: List[int]
    i = 0
    while i < len(q.leading):
        # invariants-start
        Invariant(Acc(q.leading))
        Invariant(Acc(list_pred(q.leading)))
        Invariant(ToSeq(q.leading) == Old(ToSeq(q.leading)))
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(ToSeq(fields) == Old(ToSeq(fields)))
        Invariant(Acc(list_pred(kept_front)))
        Invariant(0 <= i and i <= len(q.leading))
        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(q.leading).take(i),
                                                    ToSeq(fields)))
        Invariant(MustTerminate(len(q.leading) - i))
        # invariants-end
        name = q.leading[i]
        Assert(ToSeq(q.leading).take(i + 1)
               == ToSeq(q.leading).take(i) + PSeq(name))
        Assert(ToSeq(q.leading).take(i + 1).take(i) == ToSeq(q.leading).take(i))
        Assert(ToSeq(q.leading).take(i + 1)[i] == name)
        if name in fields:
            kept_front.append(name)
        i = i + 1
    Assert(ToSeq(q.leading).take(len(q.leading)) == ToSeq(q.leading))

    kept_back = []  # type: List[int]
    j = 0
    while j < len(q.trailing):
        # invariants-start
        Invariant(Acc(q.leading))
        Invariant(Acc(list_pred(q.leading)))
        Invariant(ToSeq(q.leading) == Old(ToSeq(q.leading)))
        Invariant(Acc(q.trailing))
        Invariant(Acc(list_pred(q.trailing)))
        Invariant(ToSeq(q.trailing) == Old(ToSeq(q.trailing)))
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(ToSeq(fields) == Old(ToSeq(fields)))
        Invariant(Acc(list_pred(kept_front)))
        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(q.leading),
                                                    ToSeq(fields)))
        Invariant(Acc(list_pred(kept_back)))
        Invariant(0 <= j and j <= len(q.trailing))
        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(q.trailing).take(j),
                                                    ToSeq(fields),
                                                    ToSeq(q.leading)))
        Invariant(MustTerminate(len(q.trailing) - j))
        # invariants-end
        later = q.trailing[j]
        Assert(ToSeq(q.trailing).take(j + 1)
               == ToSeq(q.trailing).take(j) + PSeq(later))
        Assert(ToSeq(q.trailing).take(j + 1).take(j) == ToSeq(q.trailing).take(j))
        Assert(ToSeq(q.trailing).take(j + 1)[j] == later)
        if later in fields and not (later in q.leading):
            kept_back.append(later)
        j = j + 1
    Assert(ToSeq(q.trailing).take(len(q.trailing)) == ToSeq(q.trailing))

    chosen = []  # type: List[int]
    k = 0
    while k < len(fields):
        # invariants-start
        Invariant(Acc(q.leading))
        Invariant(Acc(list_pred(q.leading)))
        Invariant(ToSeq(q.leading) == Old(ToSeq(q.leading)))
        Invariant(Acc(q.trailing))
        Invariant(Acc(list_pred(q.trailing)))
        Invariant(ToSeq(q.trailing) == Old(ToSeq(q.trailing)))
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(ToSeq(fields) == Old(ToSeq(fields)))
        Invariant(Acc(list_pred(kept_front)))
        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(q.leading),
                                                    ToSeq(fields)))
        Invariant(Acc(list_pred(kept_back)))
        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(q.trailing),
                                                    ToSeq(fields),
                                                    ToSeq(q.leading)))
        Invariant(Acc(list_pred(chosen)))
        Invariant(0 <= k and k <= len(fields))
        Invariant(ToSeq(chosen) == own_columns(ToSeq(fields).take(k),
                                               ToSeq(q.leading),
                                               ToSeq(q.trailing)))
        Invariant(MustTerminate(len(fields) - k))
        # invariants-end
        wanted = fields[k]
        Assert(ToSeq(fields).take(k + 1) == ToSeq(fields).take(k) + PSeq(wanted))
        Assert(ToSeq(fields).take(k + 1).take(k) == ToSeq(fields).take(k))
        Assert(ToSeq(fields).take(k + 1)[k] == wanted)
        if not (wanted in q.leading) and not (wanted in q.trailing):
            chosen.append(wanted)
        k = k + 1
    Assert(ToSeq(fields).take(len(fields)) == ToSeq(fields))

    q.columns = chosen
    q.leading = kept_front
    q.trailing = kept_back
    # impl-end


def columns_for_subquery(cached: Query, outer_select: List[int]) -> Query:
    # pre-conditions-start
    # `cached` is the reused component sub-query, shared across compilations;
    # the compilation only READS it (fractional permission, directive 5).
    Requires(Acc(cached.columns, 1 / 2))
    Requires(Acc(list_pred(cached.columns), 1 / 2))
    Requires(Acc(cached.leading, 1 / 2))
    Requires(Acc(list_pred(cached.leading), 1 / 2))
    Requires(Acc(cached.trailing, 1 / 2))
    Requires(Acc(list_pred(cached.trailing), 1 / 2))
    Requires(Acc(cached.state, 1 / 2))
    # this branch is reached only when the component has no column list of its
    # own and the outer query restricts the columns to a non-empty list.
    Requires(len(cached.columns) == 0)
    Requires(Acc(list_pred(outer_select), 1 / 2))
    Requires(len(outer_select) > 0)
    # the compilation step must complete (the measure leaves room for the two
    # helper operations above).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(outer_select), 1 / 2))
    # (2) the shared component sub-query is observably left UNCHANGED: still no
    # column list of its own, both families of derived columns still exposed
    # un-narrowed, same accumulated state — so a later compilation choosing a
    # different column list is not corrupted by this one.
    Ensures(Acc(cached.columns, 1 / 2))
    Ensures(Acc(list_pred(cached.columns), 1 / 2))
    Ensures(len(cached.columns) == 0)
    Ensures(Acc(cached.leading, 1 / 2))
    Ensures(Acc(list_pred(cached.leading), 1 / 2))
    Ensures(ToSeq(cached.leading) == Old(ToSeq(cached.leading)))
    Ensures(Acc(cached.trailing, 1 / 2))
    Ensures(Acc(list_pred(cached.trailing), 1 / 2))
    Ensures(ToSeq(cached.trailing) == Old(ToSeq(cached.trailing)))
    Ensures(Acc(cached.state, 1 / 2))
    Ensures(cached.state == Old(cached.state))
    # (1) the column selection this compilation uses is the outer query's
    # chosen column list CLASSIFIED against the SHARED sub-query's own
    # (un-narrowed) derived columns — the outcome of applying that list exactly
    # once to a faithful copy of the shared sub-query — and it is carried by an
    # object distinct from `cached`, with containers of its own.
    Ensures(Acc(Result().columns))
    Ensures(Acc(list_pred(Result().columns)))
    Ensures(Acc(Result().leading))
    Ensures(Acc(list_pred(Result().leading)))
    Ensures(Acc(Result().trailing))
    Ensures(Acc(list_pred(Result().trailing)))
    Ensures(Acc(Result().state))
    Ensures(Result() is not cached)
    Ensures(Result().columns is not cached.columns)
    Ensures(Result().leading is not cached.leading)
    Ensures(Result().trailing is not cached.trailing)
    Ensures(ToSeq(Result().columns) == own_columns(ToSeq(outer_select),
                                                   ToSeq(cached.leading),
                                                   ToSeq(cached.trailing)))
    Ensures(ToSeq(Result().leading) == kept_leading(ToSeq(cached.leading),
                                                    ToSeq(outer_select)))
    Ensures(ToSeq(Result().trailing) == kept_trailing(ToSeq(cached.trailing),
                                                      ToSeq(outer_select),
                                                      ToSeq(cached.leading)))
    # (3) the per-compilation object CARRIES the shared sub-query's accumulated
    # state: a blank-slate working object (which would lose the rows the
    # sub-query was built up to produce) is ruled out.
    Ensures(Result().state == cached.state)
    # post-conditions-end
    # impl-start
    # Use a per-compilation working object that is independent of the shared
    # component sub-query but mirrors its column selection and carries its
    # accumulated state, then apply the chosen column list to that object.
    private = detached_copy(cached)
    with_columns(private, outer_select)
    return private
    # impl-end
