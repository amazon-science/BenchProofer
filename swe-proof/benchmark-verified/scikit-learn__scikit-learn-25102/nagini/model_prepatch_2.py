"""Twin-artifact model for scikit-learn__scikit-learn-25102.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A feature-reducing transformer applied to a labelled tabular container picks
  out a subset of the container's columns according to a per-column boolean
  retention mask, and returns the result as a labelled tabular container that
  keeps the column-wise descriptive metadata of the input. Concretely:

    (1) Per-column metadata is preserved. Each output column is one of the
        input columns chosen by the mask, carried over UNCHANGED — in
        particular its per-column descriptor (the value distinguishing a column
        whose entries are, say, an ordinal category from one whose entries are
        a real number). The output column descriptors are exactly the
        descriptors of the retained input columns, in input order; an output
        column NEVER takes a single shared descriptor coerced across all
        columns. The retained columns are those positions whose mask entry is
        set, and only those.

    (2) Row labels are preserved. The output keeps the input container's OWN row
        labels (its "index") unchanged, whatever the number of retained columns
        — including the degenerate case where the mask retains no column at all
        (the output then has zero columns but still the input's row labels), not
        a freshly invented positional row labelling.

The labelled container is modelled as a minimal class carrying only its two
touched facets: its row labels (the "index", a ``List[int]`` of label codes)
and its per-column descriptors (a ``List[int]`` of descriptor codes, one per
column). The retention mask is a ``List[int]`` of per-column flags (0 = drop,
1 = keep). Sequence values are compared via the pure ``PSeq[int]`` theory
(``ToSeq``). The per-column-descriptor selection is modelled deeply as a
front-recursive compress fold (``kept_descs``); the postconditions pin both the
exact per-column descriptors of the result and its row labels.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Frame:
    def __init__(self, index: List[int], descs: List[int],
                 si: PSeq[int], sd: PSeq[int]) -> None:
        # `si`/`sd` are ghost witnesses of the intended row-label and
        # column-descriptor sequences, so the caller can relate the constructed
        # container's facets to values it still holds after the list
        # permissions move into the fields.
        Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
        Requires(ToSeq(index) == si and ToSeq(descs) == sd)
        # Constructing a container is a bounded step (two field writes); its
        # level (1) sits strictly below every method that allocates one.
        Requires(MustTerminate(1))
        Ensures(Acc(self.index) and self.index is index)        # type: ignore
        Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
        Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
        Ensures(ToSeq(self.index) == si)                        # type: ignore
        Ensures(ToSeq(self.descs) == sd)                        # type: ignore
        self.index = index
        self.descs = descs


# axioms-start
# (no axioms: the column-selection behaviour is a self-contained per-column
# compress over the touched facets, modelled deeply; nothing the proof needs is
# delegated to an unchanged opaque callee.)
# axioms-end


# pure-start
@Pure
def kept_descs(descs: PSeq[int], mask: PSeq[int]) -> PSeq[int]:
    """The descriptors of the retained columns, in input order: for each
    position keep the input column's descriptor exactly when its mask flag is
    set, else nothing. Front-recursive so a single unfold is available to the
    matching impl loop. Each kept descriptor is the input column's OWN
    descriptor (never a coerced shared value). Total over any pair of sequences:
    positions past the end of either sequence contribute nothing (the modelled
    inputs always have matching lengths, established by the caller)."""
    if len(descs) == 0 or len(mask) == 0:
        return PSeq(0).take(0)
    if mask[0] != 0:
        return PSeq(descs[0]) + kept_descs(descs.drop(1), mask.drop(1))
    return kept_descs(descs.drop(1), mask.drop(1))
# pure-end


def select_columns(df: Frame, mask: List[int]) -> Frame:
    # `mask` has one flag per input column (0 = drop, 1 = keep), read-only.
    # pre-conditions-start
    Requires(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
    Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
    Requires(Acc(list_pred(mask), 1 / 2))
    Requires(len(df.descs) == len(mask))
    # The selection must COMPLETE (total correctness). Without this obligation
    # every Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
    # at 2, the container constructor at 1).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the fractional permission they were lent
    # at (the input container and the mask are never mutated).
    Ensures(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
    Ensures(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
    Ensures(Acc(list_pred(mask), 1 / 2))
    Ensures(Acc(Result().index) and Acc(Result().descs))
    Ensures(Acc(list_pred(Result().index)) and Acc(list_pred(Result().descs)))
    # (1) Per-column metadata preserved: the output column descriptors are
    # exactly the descriptors of the retained input columns, in input order
    # (each carried over unchanged — never a single coerced shared descriptor).
    Ensures(ToSeq(Result().descs) == kept_descs(ToSeq(df.descs), ToSeq(mask)))
    # (2) Row labels preserved: the output keeps the input's OWN row labels,
    # regardless of how many columns survived (including none).
    Ensures(ToSeq(Result().index) == ToSeq(df.index))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON (behaviour 2 — row labels): the result is built from a
    # bare homogeneous payload that has no row labels of its own, so the output
    # is stamped with a fresh positional row labelling [0, 1, ..., n-1] sized to
    # the input's row count rather than carrying over the input's own row
    # labels. The per-column descriptors are carried over correctly; only the
    # row labels are lost.
    new_index = []  # type: List[int]
    nrows = len(df.index)
    j = 0
    while j < nrows:
        # invariants-start
        Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
        Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
        Invariant(Acc(list_pred(mask), 1 / 2))
        Invariant(len(df.descs) == len(mask))
        Invariant(Acc(list_pred(new_index)))
        Invariant(0 <= j and j <= nrows and len(new_index) == j)
        # At most nrows - j + 1 passes remain: nrows is a local fixed at entry, j
        # rises by exactly one per pass, and the guard j < nrows keeps the bound
        # >= 2 on entry to a pass.
        Invariant(MustTerminate(nrows - j + 1))
        # invariants-end
        new_index.append(j)
        j = j + 1
    new_descs = []  # type: List[int]
    i = len(df.descs)
    while i > 0:
        # invariants-start
        Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
        Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
        Invariant(Acc(list_pred(mask), 1 / 2))
        Invariant(Acc(list_pred(new_index)))
        Invariant(Acc(list_pred(new_descs)))
        Invariant(len(df.descs) == len(mask))
        Invariant(0 <= i and i <= len(df.descs))
        Invariant(ToSeq(new_descs) ==
                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
        # At most i + 1 passes remain: the loop counts DOWN over the input
        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
        Invariant(MustTerminate(i + 1))
        # invariants-end
        d = df.descs[i - 1]
        m = mask[i - 1]
        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
        Assert(ToSeq(mask).drop(i - 1)[0] == m)
        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
        if m != 0:
            new_descs = [d] + new_descs
        i = i - 1
    gi = ToSeq(new_index)    # type: PSeq[int]
    gd = ToSeq(new_descs)    # type: PSeq[int]
    result = Frame(new_index, new_descs, gi, gd)  # type: Frame
    return result
    # impl-end


def _copy_labels(src: List[int]) -> List[int]:
    Requires(Acc(list_pred(src), 1 / 2))
    # Copying the row labels must COMPLETE: level 2 leaves room for the list
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
