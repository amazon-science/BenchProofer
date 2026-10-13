"""Twin-artifact model for scikit-learn__scikit-learn-25747.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper places transformed data into a labelled tabular container so the
  configured output format is honoured. Its row labels (the container's
  "index") and column labels are governed by two rules that depend on whether
  the data handed in is ALREADY a labelled tabular container:

    (1) When the incoming data is already a labelled container, the helper
        keeps that container's OWN row labels untouched. A transformer is free
        to change the number of rows (e.g. by aggregating), so the helper must
        NOT overwrite the container's row labels with a separately supplied set
        of labels — even when such a set is supplied. Only the column labels
        are refreshed, and only when a replacement set is supplied; otherwise
        both label axes are left exactly as they were.

    (2) When the incoming data is NOT already a labelled container, the helper
        builds a fresh container, stamping each axis with the supplied set of
        labels for that axis when one is given; when no set is supplied for an
        axis, that axis receives the default positional labelling
        ``[0, 1, ..., k-1]`` sized to the data payload (k = the payload's row
        count for the row axis, its column count for the column axis).

The labelled container is modelled as a minimal class carrying only its two
touched facets — its row labels and its column labels, each a sequence of
label codes (``List[int]``). The two optional supplied label sets are modelled
as ``Optional[List[int]]`` (read-only); the payload's row/column counts are the
``nrows``/``ncols`` parameters. Sequence values are compared via the pure
``PSeq[int]`` theory (``ToSeq``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Frame:
    def __init__(self, index: List[int], columns: List[int],
                 si: PSeq[int], sc: PSeq[int]) -> None:
        # `si`/`sc` are ghost witnesses of the intended label sequences, so the
        # caller can relate the constructed container's label values to values
        # it still holds after the list permissions move into the fields.
        Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
        Requires(ToSeq(index) == si and ToSeq(columns) == sc)
        # Constructing a container is a bounded step (two field writes); its
        # level (1) sits strictly below every method that allocates one.
        Requires(MustTerminate(1))
        Ensures(Acc(self.index) and self.index is index)      # type: ignore
        Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
        Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
        Ensures(ToSeq(self.index) == si)   # type: ignore
        Ensures(ToSeq(self.columns) == sc)  # type: ignore
        self.index = index
        self.columns = columns


# axioms-start
# (no axioms: the behaviour is a self-contained labelling rule; both the
# in-place relabelling of an existing container and the construction of a fresh
# container are modelled deeply over the touched facets.)
# axioms-end


# pure-start
@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The sequence value of an optional label set: its element sequence when a
    set is supplied, the empty sequence when none is. Guards the None-case so
    the spec can compare supplied-label values without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def is_range(s: PSeq[int], n: int) -> bool:
    """``s`` is the default positional labelling ``[0, 1, ..., n-1]`` for an axis
    of length ``n``: it has exactly ``n`` elements and element ``k`` is ``k``.
    This is the label set a fresh container assigns to an axis when no
    replacement set is supplied for it (a default positional labelling)."""
    return len(s) == n and Forall(int, lambda k:
        (Implies(0 <= k and k < n, s[k] == k), [[s[k]]]))
# pure-end


def wrap_in_container(data_is_frame: bool,
                      df: Frame,
                      columns: Optional[List[int]],
                      index: Optional[List[int]],
                      nrows: int,
                      ncols: int) -> Frame:
    # `nrows`/`ncols` are the row/column counts of the data payload being
    # placed into the container (the shape the fresh container is built from).
    # pre-conditions-start
    Requires(Acc(df.index) and Acc(df.columns))
    Requires(Acc(list_pred(df.index)) and Acc(list_pred(df.columns)))
    Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
    Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
    Requires(nrows >= 0 and ncols >= 0)
    # Placing the data into a container must COMPLETE (total correctness).
    # Without this obligation every Ensures below is claimed only of runs that
    # reach the return, so an implementation that never gets there satisfies the
    # whole postcondition vacuously. Level 3 is strictly above every callee it
    # invokes (the two label helpers at 2, the container constructor at 1).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().index) and Acc(Result().columns))
    Ensures(Acc(list_pred(Result().index)) and Acc(list_pred(Result().columns)))
    # Read-only supplied label sets are returned at the fractional permission
    # they were lent at (they are never mutated).
    Ensures(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
    Ensures(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
    # (1) Already-a-container branch: the SAME container is returned, its row
    # labels are kept exactly as they were on entry (the discriminating
    # guarantee: a separately supplied set of row labels never overrides them),
    # and its column labels are refreshed only when a replacement set is given.
    Ensures(Implies(data_is_frame, Result() is df))
    Ensures(Implies(data_is_frame,
                    ToSeq(Result().index) == Old(ToSeq(df.index))))
    Ensures(Implies(data_is_frame and columns is not None,
                    ToSeq(Result().columns) == opt_seq(columns)))
    Ensures(Implies(data_is_frame and columns is None,
                    ToSeq(Result().columns) == Old(ToSeq(df.columns))))
    # (2) Not-a-container branch: a fresh container stamped with the supplied
    # row labels and column labels. When a label set is NOT supplied for an
    # axis, that axis gets the default positional labelling [0, 1, ..., k-1]
    # sized to the data payload (k = nrows for the row axis, ncols for the
    # column axis) — NOT an arbitrary set of labels.
    Ensures(Implies(not data_is_frame and index is not None,
                    ToSeq(Result().index) == opt_seq(index)))
    Ensures(Implies(not data_is_frame and index is None,
                    is_range(ToSeq(Result().index), nrows)))
    Ensures(Implies(not data_is_frame and columns is not None,
                    ToSeq(Result().columns) == opt_seq(columns)))
    Ensures(Implies(not data_is_frame and columns is None,
                    is_range(ToSeq(Result().columns), ncols)))
    # post-conditions-end
    # impl-start
    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    # Tie the constructed label values to the supplied label values (or the
    # default positional labelling when none is supplied): the copy / fill
    # preserved each intended sequence, so the fresh container's labels equal
    # opt_seq of the supplied sets, or range_labels of the payload shape.
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
    return result
    # impl-end


def _copy_labels(src: List[int]) -> List[int]:
    Requires(Acc(list_pred(src), 1 / 2))
    # Copying a label set must COMPLETE: level 2 leaves room for the list
    # allocation it performs (at level 1 the allocation's own obligation has
    # nowhere below the caller to go), and sits strictly below its caller's 3.
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(src))
    out = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(src))
        Invariant(len(out) == i)
        Invariant(ToSeq(out) == ToSeq(src).take(i))
        # At most len(src) - i + 1 passes remain: the source is held read-only by
        # the invariant above so its length cannot change, and i rises by exactly
        # one per pass, so the bound strictly decreases; the guard i < len(src)
        # keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        out.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return out


def _range_labels(n: int) -> List[int]:
    Requires(n >= 0)
    # Filling the default positional labelling must COMPLETE: level 2 leaves room
    # for the list allocation it performs, and sits strictly below its caller's 3.
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(is_range(ToSeq(Result()), n))
    out = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
        # change, and i rises by exactly one per pass, so the bound strictly
        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        old_seq = ToSeq(out)  # type: PSeq[int]
        out.append(i)
        Assert(ToSeq(out) == old_seq + PSeq(i))
        Assert(len(ToSeq(out)) == i + 1)
        Assert(Forall(int, lambda k:
            (Implies(0 <= k and k < i, ToSeq(out)[k] == old_seq[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == i)
        i = i + 1
    return out
