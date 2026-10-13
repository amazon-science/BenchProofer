"""Twin-artifact model for matplotlib__matplotlib-24970.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colormap maps each data value to a row of a lookup table that has ``N``
  ordinary colour rows (indices ``0 .. N-1``) followed by three special rows:
  the under-range row at index ``N``, the over-range row at index ``N + 1`` and
  the bad/masked row at index ``N + 2``.

  For one element the final lookup row is determined as follows. The element
  carries an integer value ``v`` (for floating inputs this is the
  scaled-and-clipped value). The three special rows are applied in turn --
  over-range, then under-range, then bad -- so they take this precedence: a
  bad/masked element selects the bad row ``N + 2`` regardless of ``v``;
  otherwise an out-of-range-high value (``v > N - 1``) selects the over-range
  row ``N + 1``; otherwise a negative value (``v < 0``) selects the under-range
  row ``N``; any remaining in-range value keeps its own index ``v``. The
  selected index is then clipped into the valid table-row range ``0 .. N + 2``.

  The required behaviour is that this row assignment COMPLETES for any data
  value of any integer width -- in particular it must not perform an operation
  that is only conditionally valid for the data's integer container. Assigning
  the special row indices is such an operation: an integer container only
  admits an index it can represent, and the special indices run up to ``N + 2``.
  The operation must therefore be carried out on a container that admits every
  index it assigns (an index of ``N + 2`` requires a container that admits
  values up to ``N + 2``); a container that admits only a narrower range than
  the special indices it is asked to hold does not admit the assignment. The
  result is required to be one produced BY such an admitting assignment, so the
  whole operation completes for every input width rather than for some widths
  only.

The data array is modelled as ``List[int]`` of per-element integer values plus
a parallel ``List[bool]`` mask. ``modulus`` abstracts the range of values the
INPUT integer container admits (a container admitting ``modulus`` distinct
values represents ``0 .. modulus - 1``). The pure sequence theory ``PSeq[int]``
carries the per-element specification.

The per-element row assignment over the array is an UNCHANGED integer-array
operation; it is modelled as a callee ``assign_special_rows`` whose contract
captures both its result (the per-element selected-and-clipped rows) and the
EFFECT that distinguishes a completing assignment from a non-completing one --
it is well-defined (it grants the unforgeable ``rows_assigned`` token) ONLY when
the container it writes into admits every special index it assigns. The result's
postcondition REQUIRES that token, so a verifying operation must route its
result through an admitting assignment; it cannot return a row sequence that no
admitting assignment produced. No callee under change is axiomatized; the
callee's contract is validated against the real integer-array operation
out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# Abstract token marking a row sequence PRODUCED BY a well-defined per-element
# special-row assignment for a table of ``n`` ordinary rows: a capability the
# assignment grants on its output, that nothing else can fabricate. Its
# arguments record the produced rows and the table size. The result of the
# whole operation must hold this token, so the result can only be a row sequence
# an admitting assignment actually produced -- an assignment into a container
# that does not admit the special indices it must hold is not well-defined and
# never grants it. Provenance + executable soundness check: mapping.md /
# axiom_check.py.
@ContractOnly
@Predicate
def rows_assigned(rows: PSeq[int], n: int) -> bool:
    pass


@ContractOnly
def assign_special_rows(values: List[int], bads: List[bool], n: int,
                        modulus: int) -> List[int]:
    """The per-element special-row assignment over the whole array (the
    UNCHANGED integer-array operation: write the special indices for the
    out-of-range / masked elements, then clip into the table-row range). It is
    carried out on an integer container that admits ``0 .. modulus - 1``.

    The assignment is only WELL-DEFINED -- actually yielding a row sequence and
    granting the ``rows_assigned`` token -- when that container admits every
    special index it assigns. The largest special index is ``n + 2``, so the
    container must admit values up to ``n + 2``; that is the precondition
    ``modulus >= n + 3``. A container narrower than the special indices it is
    asked to hold does not admit the assignment, so this contract does not apply
    to it (the operation is not well-defined there). On a well-defined
    assignment it returns the per-element selected-and-clipped rows AND grants
    the ``rows_assigned`` token on its output for this table size. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(Acc(list_pred(bads), 1 / 2))
    Requires(len(values) == len(bads))
    Requires(len(ToSeq(values)) == len(ToSeq(bads)))
    Requires(n >= 1)
    # A well-defined assignment requires the container to admit every special
    # index it writes; the largest is n + 2, so the container must admit values
    # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
    Requires(modulus >= n + 3)
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(bads), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(values))
    Ensures(len(ToSeq(values)) == len(ToSeq(bads)))
    # The well-defined assignment yields exactly the per-element rows...
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))
    # ...and grants the token marking it as an admitting assignment's output.
    Ensures(rows_assigned(ToSeq(Result()), n))
# axioms-end


# pure-start
@Pure
def selected_index(v: int, n: int, bad: bool) -> int:
    """The special-or-ordinary row index selected for one element, before it is
    clipped into the table. The three special rows are applied in turn
    (over-range, then under-range, then bad), so the bad row has the highest
    precedence, then over-range, then under-range; any remaining in-range value
    keeps its own index."""
    Requires(n >= 1)
    if bad:
        return n + 2            # bad/masked row (applied last, wins)
    if v > n - 1:
        return n + 1            # over-range row
    if v < 0:
        return n                # under-range row
    return v                    # ordinary in-range index


@Pure
def clip_row(idx: int, n: int) -> int:
    """Clip a row index to the valid lookup-table row range ``0 .. N+2`` (the
    ``mode='clip'`` of the row gather)."""
    Requires(n >= 1)
    if idx < 0:
        return 0
    if idx > n + 2:
        return n + 2
    return idx


@Pure
def final_row(v: int, n: int, bad: bool) -> int:
    """The lookup-table row a single element ends up at: select the row, then
    clip into range. Every selected index already lies in ``0 .. N+2``, so this
    is exactly the selected index."""
    Requires(n >= 1)
    return clip_row(selected_index(v, n, bad), n)


@Pure
def rows_of(vs: PSeq[int], bs: PSeq[bool], n: int) -> PSeq[int]:
    """The row sequence for a whole element sequence: the per-element
    final_row of each element. Front-recursive so a single unfold is available
    per loop step."""
    Requires(n >= 1)
    Requires(len(vs) == len(bs))
    if len(vs) == 0:
        return PSeq(0).take(0)
    return PSeq(final_row(vs[0], n, bs[0])) + rows_of(vs.drop(1), bs.drop(1), n)
# pure-end


def take_rows(values: List[int], bads: List[bool], n: int,
              modulus: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(Acc(list_pred(bads), 1 / 2))
    Requires(len(values) == len(bads))
    Requires(n >= 1)
    Requires(modulus >= 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(bads), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(values) == len(bads))
    Ensures(len(Result()) == len(values))
    # Every element ends at the row dictated by selection + clip.
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))
    # Load-bearing: the result must be one PRODUCED BY a special-row assignment
    # that completed -- an assignment carried out on a container that admits
    # every special index it writes. The token is granted only by such an
    # admitting assignment; it cannot be discharged by value-equality alone,
    # because the row values are identical whether or not the assignment's
    # container admitted the special indices -- the discriminator is the
    # completing-assignment effect, not a row value.
    Ensures(rows_assigned(ToSeq(Result()), n))
    # post-conditions-end
    # impl-start
    # Build the per-element special-row assignment input-by-input, mirroring the
    # element-wise array operation, then carry it out on a container that admits
    # every special index it writes. The special indices are the under-range row
    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
    # admits the whole assignment -- the input's own container may be narrower.
    sel_values = []  # type: List[int]
    sel_bads = []  # type: List[bool]
    i = len(values)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(Acc(list_pred(bads), 1 / 2))
        Invariant(Acc(list_pred(sel_values)))
        Invariant(Acc(list_pred(sel_bads)))
        Invariant(len(values) == len(bads))
        Invariant(0 <= i and i <= len(values))
        Invariant(len(sel_values) == len(values) - i)
        Invariant(len(sel_bads) == len(bads) - i)
        Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
        Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        v = values[i - 1]
        bad = bads[i - 1]
        Assert(ToSeq(values).drop(i - 1)[0] == v)
        Assert(ToSeq(values).drop(i - 1).drop(1) == ToSeq(values).drop(i))
        Assert(ToSeq(bads).drop(i - 1)[0] == bad)
        Assert(ToSeq(bads).drop(i - 1).drop(1) == ToSeq(bads).drop(i))
        sel_values = [v] + sel_values
        sel_bads = [bad] + sel_bads
        i = i - 1
    Assert(ToSeq(sel_values) == ToSeq(values))
    Assert(ToSeq(sel_bads) == ToSeq(bads))
    carrier = n + 3
    result = assign_special_rows(sel_values, sel_bads, n, carrier)
    return result
    # impl-end
