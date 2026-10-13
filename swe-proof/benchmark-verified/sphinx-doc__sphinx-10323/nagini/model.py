"""Twin-artifact model for sphinx-doc__sphinx-10323.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A block of included text is assembled together with an OPTIONAL leading line
  and an OPTIONAL trailing line, under a left-margin trim of width `n` (which
  removes up to `n` leading code points from a line).

  The trim reaches the included text — every one of its lines, ALWAYS: for every
  trim width, and whether or not a leading or a trailing line is supplied. It
  never reaches the leading or the trailing line: those are author-controlled
  and are emitted verbatim, their own indentation preserved exactly.

  An author line is supplied exactly when it has content; an empty author line
  is not supplied and contributes no line at all to the assembled block. So the
  assembled output is:

      [ leading line, verbatim ]        (present only if it has content)
      [ each included line, with its first `n` leading code points removed ]
      [ trailing line, verbatim ]       (present only if it has content)

  and nothing besides: the assembled block carries exactly one line per included
  line, plus one line for each author line that was supplied.

Text is modelled as `PSeq` of lines, each line a `PSeq[int]` of Unicode code
points (Nagini bans `str` indexing). A line's margin trim of width `n` is the
removal of its first `n` code points (`PSeq.drop(n)`), so a width of 0 leaves a
line unchanged. The trim of a whole block is modelled DEEPLY as a per-line fold
(`trim_block`); its equality to the real per-line trim callee is checked
out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom. `emit` models
the presence rule for a single author line.

Assembling a finite block is bounded work that must actually deliver its
result, so the operation carries a total-correctness obligation (MustTerminate
in the precondition): without it a diverging body would satisfy every
postcondition vacuously while never producing the assembled block.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the per-line margin trim is modelled deeply
#  below as `trim_block` and validated == the real trim callee out-of-band by
#  axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def trim_block(lines: PSeq[PSeq[int]], n: int) -> PSeq[PSeq[int]]:
    """The margin trim of a whole block: each line with its first `n` leading
    code points removed (`PSeq.drop(n)`). Front-recursive (one unfold per line)
    so a backward impl loop can discharge the value equality."""
    Requires(n >= 0)
    Ensures(len(Result()) == len(lines))
    if len(lines) == 0:
        return PSeq(PSeq(0).take(0)).take(0)
    return PSeq(lines[0].drop(n)) + trim_block(lines.drop(1), n)


@Pure
def emit(line: PSeq[int]) -> PSeq[PSeq[int]]:
    """The contribution of ONE author-supplied line to the assembled block: the
    single-line block holding it verbatim when it has content, and NO line at
    all when it is empty (an empty author line is not supplied)."""
    Ensures(Implies(len(line) == 0, len(Result()) == 0))
    Ensures(Implies(len(line) >= 1, len(Result()) == 1))
    Ensures(Implies(len(line) >= 1, Result()[0] == line))
    if len(line) == 0:
        return PSeq(line).take(0)
    return PSeq(line)
# pure-end


@Pure
def trim_block_at(lines: PSeq[PSeq[int]], n: int, k: int) -> bool:
    """Lemma: element `k` of the margin-trimmed block is line `k` trimmed by
    width `n`. Proved by induction on the front-recursive `trim_block` (one
    unfold strips the head and shifts the index). Pure, so a caller carrying a
    termination obligation may invoke it without consuming any measure."""
    Requires(n >= 0)
    Requires(0 <= k and k < len(lines))
    Ensures(Result())
    Ensures(trim_block(lines, n)[k] == lines[k].drop(n))
    if k == 0:
        return True
    return trim_block_at(lines.drop(1), n, k - 1)


def assemble(included: PSeq[PSeq[int]], lead: PSeq[int], trail: PSeq[int],
             n: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The trim width is a non-negative count of leading code points to remove; a
    # width of 0 leaves every line unchanged.
    Requires(n >= 0)
    # NOTHING is demanded of the author lines: either or both of them may be
    # absent (empty). Assembling must work — and the margin trim must still
    # reach the included text — in every one of those situations.
    # TERMINATION: assembling a finite block is bounded work and must actually
    # DELIVER the assembled result (total correctness). Without this
    # obligation a body that never returns would satisfy every postcondition
    # vacuously while never producing the block.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The assembled block is the supplied leading line, then the margin-trimmed
    # included text, then the supplied trailing line.
    Ensures(Result() == (emit(lead) + trim_block(included, n)) + emit(trail))
    # It carries one line per included line plus one per supplied author line,
    # and nothing else.
    Ensures(len(Result()) == len(emit(lead)) + len(included) + len(emit(trail)))
    # With NO author line supplied, the assembled block is exactly the
    # margin-trimmed included text: the trim is not contingent on an author line
    # being there, and no line is invented in its place.
    Ensures(Implies(len(lead) == 0 and len(trail) == 0,
                    Result() == trim_block(included, n)))
    # A supplied leading line is element 0 VERBATIM (its indentation preserved,
    # not trimmed): even when the trim width would shorten it, it is emitted as
    # given.
    Ensures(Implies(len(lead) >= 1, Result()[0] == lead))
    Ensures(Implies(len(lead) >= 1 and n >= 1, Result()[0] != lead.drop(n)))
    # A supplied trailing line is the LAST element, likewise VERBATIM.
    Ensures(Implies(len(trail) >= 1, Result()[len(Result()) - 1] == trail))
    # Each included line appears, in order, after the margin trim — starting
    # right after the supplied leading line when there is one, and at the very
    # front when there is not. Either way EVERY included line is trimmed.
    Ensures(Implies(len(lead) >= 1, Forall(int, lambda i: (
        Implies(0 <= i and i < len(included),
                Result()[i + 1] == included[i].drop(n)),
        [[Result()[i + 1]]]))))
    Ensures(Implies(len(lead) == 0, Forall(int, lambda i: (
        Implies(0 <= i and i < len(included),
                Result()[i] == included[i].drop(n)),
        [[Result()[i]]]))))
    # post-conditions-end
    # impl-start
    # Margin trim first — over the included text only, and unconditionally.
    # Build the trimmed block by a backward fold matching `trim_block`.
    trimmed = PSeq()  # type: PSeq[PSeq[int]]
    i = len(included)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(included))
        Invariant(trimmed == trim_block(included.drop(i), n))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(included.drop(i - 1)[0] == included[i - 1])
        Assert(included.drop(i - 1).drop(1) == included.drop(i))
        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
        i = i - 1
    Assert(trimmed == trim_block(included, n))
    Assert(len(trimmed) == len(included))
    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
    # and only when it has content.
    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
    # Discharge the per-included-line characterization of the trim via the
    # lemma, index by index, in both author-line regimes.
    j = 0
    while j < len(included):
        # invariants-start
        Invariant(0 <= j and j <= len(included))
        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))
        Invariant(len(trim_block(included, n)) == len(included))
        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (
            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),
            [[result[k + 1]]]))))
        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (
            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),
            [[result[k]]]))))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(included) - j,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(included) - j + 1))
        # invariants-end
        Assert(trim_block_at(included, n, j))
        Assert(trim_block(included, n)[j] == included[j].drop(n))
        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)
        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])
        j = j + 1
    return result
    # impl-end
