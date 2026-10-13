"""Twin-artifact model for sphinx-doc__sphinx-11445.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document may begin with a run of leading lines that have a specific
  ``:name: value`` shape (a header block). When boilerplate text is prepended
  to the document, it must be placed AFTER that leading header block but BEFORE
  the document body, so the body — in particular a first-line section title —
  is left untouched.

  The number of leading lines that belong to the header block therefore decides
  where the boilerplate is inserted. A line counts as a header line only when
  it has exactly this shape:

      a leading colon, then a non-empty name (whose first code point is neither
      a colon nor a space), then a closing colon, where that closing colon is
      immediately followed by a space or the end of the line, and the code
      point just before it is not a space.

  A line that does not have this exact shape — for example one whose leading
  ``:name:`` is immediately followed by some other code point rather than a
  space or end of line — is NOT a header line, and therefore ends the header
  block: the boilerplate is inserted before it.

  The contracted function returns the length of the leading header block: the
  greatest prefix length `p` such that every one of the first `p` lines has the
  header-line shape, and (when the document is longer) line `p` does not.

Lines are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a document is a `PSeq[PSeq[int]]`. The header-line predicate is
modelled DEEPLY (`is_header_line`) and validated out-of-band by axiom_check.py
(G-AX), NOT consumed as an axiom. The modelled domain excludes the back-slash
escape character (code point 92) inside a line and lines containing a newline
or carriage-return, which the inputs in scope never use (see mapping.md /
refinement.md).

Scanning a finite document is bounded work that must actually deliver its
count, so the operation carries a total-correctness obligation (MustTerminate
in the precondition, discharged by a per-loop measure in the invariants
region): without it a diverging body would satisfy every postcondition
vacuously while never producing the insertion point.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the header-line predicate is modelled
#  deeply below as `is_header_line` and validated out-of-band by
#  axiom_check.py / G-AX.)
# axioms-end


# pure-start
COLON = 58     # ':'
SPACE = 32     # ' '
BACKTICK = 96  # '`'


@Pure
def first_boundary(line: PSeq[int], k: int) -> int:
    """Index of the first *boundary colon* at position >= k, or len(line) if
    none. A boundary colon is a colon immediately followed by a space, a
    back-quote, or the end of the line (i.e. a colon the name part cannot
    absorb). Recursive over the decreasing measure len(line) - k."""
    Requires(0 <= k and k <= len(line))
    Ensures(k <= Result() and Result() <= len(line))
    Ensures(Implies(Result() < len(line), line[Result()] == COLON))
    if k >= len(line):
        return len(line)
    if line[k] == COLON and (k == len(line) - 1
                             or line[k + 1] == SPACE
                             or line[k + 1] == BACKTICK):
        return k
    return first_boundary(line, k + 1)


@Pure
def is_header_line(line: PSeq[int]) -> bool:
    """The header-line predicate (deep model, over the back-slash-free domain).
    True iff the line is ``:name:`` whose closing colon is followed by a space
    or end of line and not preceded by a space — and the name's first code
    point is neither a colon nor a space. A ``:name:`` whose closing colon is
    followed by any other code point (rather than a space or end of line) does
    NOT have the header-line shape."""
    if len(line) < 2:
        return False
    if line[0] != COLON:
        return False
    if line[1] == COLON or line[1] == SPACE:
        return False
    b = first_boundary(line, 2)
    if b >= len(line):
        return False
    if line[b - 1] == SPACE:
        return False
    return b == len(line) - 1 or line[b + 1] == SPACE


@Pure
def leading_header_count(doc: PSeq[PSeq[int]]) -> int:
    """The length of the leading header block: the greatest prefix length `p`
    such that the first `p` lines all have the header-line shape, and (when the
    document is longer) line `p` does not. Front-recursive (one unfold per
    line)."""
    Ensures(0 <= Result() and Result() <= len(doc))
    Ensures(Implies(Result() < len(doc), not is_header_line(doc[Result()])))
    if len(doc) == 0:
        return 0
    if not is_header_line(doc[0]):
        return 0
    return 1 + leading_header_count(doc.drop(1))
# pure-end


def lfc_all_markers(doc: PSeq[PSeq[int]]) -> None:
    """Lemma: every line strictly before leading_header_count(doc) has the
    header-line shape. Proved by front-recursion mirroring
    leading_header_count's unfold."""
    # Ghost recursion over the finite document: one unfold per line, on the
    # strictly decreasing, bounded-below measure len(doc) (the tail is one
    # shorter). The + 1 keeps it positive at len(doc) == 0, where the lemma
    # returns without recursing.
    Requires(MustTerminate(len(doc) + 1))
    Ensures(Forall(int, lambda i: (
        Implies(0 <= i and i < leading_header_count(doc), is_header_line(doc[i])),
        [[doc[i]]])))
    if len(doc) > 0 and is_header_line(doc[0]):
        lfc_all_markers(doc.drop(1))
        # leading_header_count unfolds by one when the head is a header line.
        Assert(leading_header_count(doc) == 1 + leading_header_count(doc.drop(1)))
        # the tail's per-line shapes shift back to indices >= 1 in `doc`:
        # for i in [1, lhc(doc)), doc[i] == doc.drop(1)[i-1], which the
        # recursive postcondition has already shown to be a header line.
        Assert(Forall(int, lambda i: (
            Implies(1 <= i and i < leading_header_count(doc),
                    doc[i] == doc.drop(1)[i - 1]),
            [[doc[i]]])))
        Assert(Forall(int, lambda i: (
            Implies(1 <= i and i < leading_header_count(doc),
                    is_header_line(doc.drop(1)[i - 1])),
            [[doc[i]]])))


def lfc_reaches(doc: PSeq[PSeq[int]], p: int) -> None:
    """Lemma: if the first `p` lines all have the header-line shape, then the
    leading header block of the whole document has length at least `p`. Proved
    by front-recursion: the head is a header line, so leading_header_count
    unfolds by one and the tail's prefix is shorter by one."""
    Requires(0 <= p and p <= len(doc))
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < p, is_header_line(doc[i])),
        [[doc[i]]])))
    # Ghost recursion on the prefix length: each call passes p - 1, so the
    # measure p strictly decreases and the recursion stops at p == 0 (where the
    # + 1 keeps it positive).
    Requires(MustTerminate(p + 1))
    Ensures(leading_header_count(doc) >= p)
    if p > 0:
        Assert(is_header_line(doc[0]))
        Assert(Forall(int, lambda i: (
            Implies(0 <= i and i < p - 1, doc.drop(1)[i] == doc[i + 1]),
            [[doc.drop(1)[i]]])))
        lfc_reaches(doc.drop(1), p - 1)


def count_leading_header_lines(content: PSeq[PSeq[int]]) -> int:
    # pre-conditions-start
    # (content is a read-only pure sequence; PSeq carries no permission.)
    # TERMINATION: the count must actually be DELIVERED — the prolog's
    # insertion point is the returned value. Without this obligation an
    # implementation that scans forever satisfies every Ensures vacuously.
    # The LEVEL len(content) + 2 strictly exceeds both ghost lemmas' levels
    # (lfc_reaches at pos + 1 <= len(content), lfc_all_markers at
    # len(content) + 1), so the impl may call them but may NOT re-invoke
    # itself: no strictly smaller level is available for a self-call.
    Requires(MustTerminate(len(content) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The result is the length of the leading header block: it counts exactly
    # the maximal run of leading header lines, so the boilerplate is inserted
    # after the header block and before the body.
    Ensures(Result() == leading_header_count(content))
    Ensures(0 <= Result() and Result() <= len(content))
    # Within the counted prefix every line has the header-line shape ...
    Ensures(Forall(int, lambda i: (
        Implies(0 <= i and i < Result(), is_header_line(content[i])),
        [[content[i]]])))
    # ... and (when the document is longer) the run stops at the first line
    # that does not have the header-line shape.
    Ensures(Implies(Result() < len(content),
                    not is_header_line(content[Result()])))
    # post-conditions-end
    # impl-start
    pos = 0
    # Pre-patch line test (inlined): a line counts as a header line as soon as
    # it begins with a colon, a non-colon name code point, and contains any
    # later colon — regardless of what follows that colon. This classifies a
    # `:name:`role`` heading as a header line, so the boilerplate is mis-placed.
    line = content[pos] if pos < len(content) else PSeq(0).take(0)
    hit = len(line) >= 3 and line[0] == COLON and line[1] != COLON
    if hit:
        j = 2
        found = False
        while j < len(line):
            # invariants-start
            Invariant(2 <= j and j <= len(line))
            # This line-scan loop terminates on its own counter: `j` either
            # rises by one or jumps straight to len(line) on the early exit, so
            # the remaining-iteration bound len(line) - j strictly falls and
            # stays >= 1 under the guard j < len(line) (`line` is not written
            # inside the loop, so len(line) is fixed).
            Invariant(MustTerminate(len(line) - j + 1))
            # invariants-end
            if line[j] == COLON:
                found = True
                j = len(line)
            else:
                j = j + 1
        hit = found
    hit = hit and pos < len(content)
    while hit:
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Implies(hit, pos < len(content)))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # OUTER loop measure. `pos` rises by exactly one per pass and the
        # invariant Implies(hit, pos < len(content)) pins pos < len(content)
        # whenever the guard `hit` holds, so len(content) - pos strictly falls
        # and stays >= 1 (the + 1 keeps the last pass's 0-remaining case
        # satisfiable). It must NOT mention the inner counter `j`, which is
        # reset to 2 on every outer pass and so does not descend across passes.
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
        line = content[pos] if pos < len(content) else PSeq(0).take(0)
        hit = len(line) >= 3 and line[0] == COLON and line[1] != COLON
        if hit:
            j = 2
            found = False
            while j < len(line):
                # invariants-start
                Invariant(2 <= j and j <= len(line))
                # INNER loop measure, within ONE outer pass: `line` is bound
                # once before this loop and never written inside it, so
                # len(line) is fixed and len(line) - j strictly falls (j rises
                # by one, or jumps to len(line) on the early exit) and stays
                # >= 1 under the guard. It is independent of the outer counter
                # `pos`: this loop's bound is the current line's length, not a
                # function of how far the outer scan has got.
                Invariant(MustTerminate(len(line) - j + 1))
                # invariants-end
                if line[j] == COLON:
                    found = True
                    j = len(line)
                else:
                    j = j + 1
            hit = found
        hit = hit and pos < len(content)
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    return pos
    # impl-end
