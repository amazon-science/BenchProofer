"""Twin-artifact model for scikit-learn__scikit-learn-14894.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A compressed-sparse-row block layout places a constant number of stored
  entries in each of its rows. For `n_rows` rows each holding `width` consecutive
  entries, the row-pointer array — the boundaries that delimit each row's slice
  of the flat storage — is the arithmetic progression

      [0, width, 2*width, ..., n_rows*width],

  whose final entry is the total number of stored entries, `width*n_rows`. When
  a row is empty (`width == 0`) the layout stores nothing: its row-pointer is
  exactly the pair of boundaries `[0, 0]` (the canonical empty layout — one
  opening boundary and one closing boundary, both 0), and the layout is still
  well defined. Constructing it must not require a positive per-row width —
  the all-empty case is a valid layout.

  The row-pointer array is produced by the numeric range-builder
  `range_step(start, stop, step)`, which enumerates `start, start+step, ...`
  up to (but excluding) `stop`. That builder is defined only for a strictly
  positive step (it advances by `step` per element, so a zero step has no
  progression). The construction therefore must establish a positive step
  before invoking the builder; that step is the per-row width.

The row-pointer is modelled as a `List[int]`; the per-row width and row count
are non-negative integers. The number of stored entries (the observable that
distinguishes the empty layout) is the final row-pointer entry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def range_step(start: int, stop: int, step: int) -> List[int]:
    """Numeric range-builder: the contiguous progression
    `start, start+step, start+2*step, ...` taking every value strictly below
    `stop`. It advances by `step` per element, so it is defined only for a
    strictly positive step (a zero step has no progression — a non-advancing
    enumeration of a half-open interval is undefined). The weakest contract the
    construction consumes: with `start == 0`, a positive `step`, and an upper
    bound that is one past the `count`-th multiple of the step
    (`stop == count*step + 1` with `count >= 1`, so the multiples
    `0..count*step` lie below `stop` and the next one does not), the result is
    the `count+1` boundaries `[0, step, 2*step, ..., count*step]`, whose k-th
    element is `k*step`. The progression is keyed to the multiple `count`
    (here `>= 1`, the number of rows) that the upper bound encodes.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(step >= 1)
    Requires(start == 0)
    Requires(Exists(int, lambda count: (count >= 1 and stop == count * step + 1,
                                        [[count * step]])))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) >= 2)
    # The k-th enumerated boundary is the k-th multiple of the step.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                            Result()[k] == k * step),
                                   [[Result()[k]]])))
    # Exactly the multiples below `stop` are enumerated: the last one is < stop
    # and the next would reach or pass it. This pins the final boundary to the
    # number of stored entries without any integer division.
    Ensures((len(Result()) - 1) * step + 1 == stop)
# axioms-end


# pure-start
# (no pure helpers required)
# pure-end


def row_pointer_for_block_layout(width: int, n_rows: int) -> List[int]:
    # pre-conditions-start
    Requires(width >= 0)
    Requires(n_rows >= 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The row-pointer is non-empty; it opens at boundary 0 (the start of the
    # flat storage) and its final entry is the number of stored entries:
    # `width` per row across `n_rows` rows. The final entry is 0 exactly when
    # the per-row width is 0, which is the empty-layout observable.
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == 0)
    Ensures(Result()[len(Result()) - 1] == width * n_rows)
    # The empty layout is pinned EXACTLY: its row-pointer is the canonical
    # two-boundary pair [0, 0] (with the opening/closing clauses above, the
    # length pin leaves no unconstrained interior entries).
    Ensures(Implies(width == 0, len(Result()) == 2))
    # For a non-empty layout the row-pointer is the full progression
    # [0, width, ..., n_rows*width]: one boundary per row plus the closing one.
    Ensures(Implies(width >= 1, len(Result()) == n_rows + 1))
    Ensures(Implies(width >= 1,
                    Forall(int, lambda k: (Implies(0 <= k and k <= n_rows,
                                                   Result()[k] == k * width),
                                           [[k * width]]))))
    # post-conditions-end
    # impl-start
    size = width * n_rows
    # Pre-patch: the row-pointer is built unconditionally with a step equal to
    # the per-row width (the flat storage split across n_rows rows), with no
    # special case for a layout whose per-row width is zero.
    step = width
    indptr = range_step(0, size + 1, step)
    return indptr
    # impl-end
