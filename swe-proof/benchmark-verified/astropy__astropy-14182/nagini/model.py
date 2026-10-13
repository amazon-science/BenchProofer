"""Twin-artifact model for astropy__astropy-14182.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A simple reStructuredText table is laid out, for ``n`` header text rows
  (``n >= 1``; the conventional single name row is ``n == 1``), as a block of
  processed (non-blank) lines:

      line 0           a rule line  (a run of the position character ``=``)
      lines 1 .. n     the ``n`` header text rows (names, units, dtypes, ...)
      line n+1         a rule line  (the run of ``=`` closing the header)
      lines n+2 ..     the data value rows

  Two layout indices must therefore track the number of header rows ``n``
  rather than assuming a single header row:

  (1) OUTPUT.  The underlying fixed-width rendering of a table with ``n`` header
      rows is the block ``[ header_0, ..., header_{n-1}, rule, data... ]``; the
      closing rule line sits at offset ``n``.  The simple-RST rendering frames
      that block by repeating the rule line above the headers and below the
      data.  So the framed output is ``[ block[n] ] + block + [ block[n] ]``,
      and the two framing lines must be exactly the closing rule line of the
      block.  The framing line is a copy of that actual block line (whose width
      content is unknown a priori), not any predetermined value an
      implementation could synthesise on its own.

  (2) INPUT.  When recovering the values from such a block, the first data
      value row is the line immediately after the closing header rule, i.e. at
      offset ``n + 2`` (one leading rule, ``n`` header rows, one closing rule).

Each layout offset is an affine function of the header-row count ``n``; pinning
either to a constant is correct only for the single-header-row case.

Lines are modelled as ``List[int]`` / ``PSeq[int]`` row tags.  The closing rule
line of a given block carries an opaque per-block value ``rule`` (the distinct
content of that rendered line); the header rows carry values other than
``rule``.  The two integer offsets are the verified layout content; the row-tag
carrier lets the framing postcondition pin the framing lines to the *actual
closing rule line value of this block* (a witnessed structural property of the
input), not to a bare index or a predetermined constant an implementation could
echo.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: both changed behaviours are layout-index arithmetic, modelled
# deeply below; there is no unchanged opaque callee the proof must consume.)
# axioms-end


# pure-start
@Pure
def rule_at(rows: PSeq[int], n: int) -> int:
    """The block's row tag at offset ``n`` (its closing rule line), guarded
    in-bounds so it can be named inside a postcondition."""
    Requires(n >= 0 and n < len(rows))
    return rows[n]


@Pure
def frame_index(n: int) -> int:
    """Offset, inside the fixed-width block of a table with ``n`` header rows,
    of the closing rule line that frames the simple-RST output.  The block is
    ``[ header_0 .. header_{n-1}, rule, data... ]`` so the rule is at ``n``."""
    Requires(n >= 1)
    Ensures(Result() == n)
    return n


@Pure
def data_start_index(n: int) -> int:
    """Offset of the first data value row in a simple-RST table with ``n``
    header rows: one leading rule, ``n`` header rows, one closing rule, then
    the data."""
    Requires(n >= 1)
    Ensures(Result() == n + 2)
    return n + 2
# pure-end


def rst_frame_block(block: List[int], n: int, rule: int) -> List[int]:
    """Frame the fixed-width block of a table with ``n`` header rows by
    repeating its closing rule line above and below the block.

    ``block`` is the row-tag sequence ``[ header_0 .. header_{n-1}, rule,
    data... ]``; its closing rule line sits at offset ``n`` and carries the
    opaque per-block value ``rule`` (the distinct content of that rendered
    line), while the ``n`` header rows before it carry values other than
    ``rule``.  The framed result is that closing rule line, then the whole
    block, then that same closing rule line.
    """
    # pre-conditions-start
    Requires(n >= 1)
    Requires(Acc(list_pred(block), 1 / 2))
    # The block is well-formed: long enough to contain its closing rule, that
    # line at offset n carries the block's opaque rule value, and the header
    # rows before it carry other values.
    Requires(len(ToSeq(block)) > n)
    Requires(ToSeq(block)[n] == rule)
    Requires(Forall(int, lambda k:
        Implies(0 <= k and k < n, ToSeq(block)[k] != rule)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(block), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(block)) > n)
    # The framed output is exactly: [rule line] + block + [rule line], with the
    # framing lines equal to the actual closing rule line of THIS block (its
    # value at offset n) — not a synthesisable constant.
    Ensures(len(Result()) == len(block) + 2)
    Ensures(frame_index(n) == n)
    Ensures(ToSeq(Result()) == PSeq(rule_at(ToSeq(block), n))
            + ToSeq(block)
            + PSeq(rule_at(ToSeq(block), n)))
    # The two framing lines carry the block's closing rule value (witnessed by
    # the block, not assumed equal to any predetermined constant).
    Ensures(ToSeq(Result())[0] == rule)
    Ensures(ToSeq(Result())[len(Result()) - 1] == rule)
    # post-conditions-end
    # impl-start
    idx = frame_index(n)
    sep = block[idx]
    result = [sep] + block + [sep]  # type: List[int]
    return result
    # impl-end


def data_row_offset(header_rows: List[int]) -> int:
    """The processed-line offset at which the first data value row begins, for a
    simple-RST table whose header consists of the rows ``header_rows`` (length
    ``n >= 1``).  One leading rule, ``n`` header rows, one closing rule, then
    the data: offset ``n + 2``.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(header_rows), 1 / 2))
    Requires(len(header_rows) >= 1)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(header_rows), 1 / 2))
    Ensures(len(header_rows) >= 1)
    # The data offset is two rule lines plus the header rows, an affine
    # function of the header-row count (correct for every n >= 1).
    Ensures(Result() == data_start_index(len(header_rows)))
    Ensures(Result() == len(header_rows) + 2)
    # post-conditions-end
    # impl-start
    n = len(header_rows)
    return 2 + n
    # impl-end
