"""Twin-artifact model for django__django-13513.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A diagnostic report walks a chain of exceptions (an exception together with
  the chain of causes that produced it) and emits, for each exception in the
  chain, one report entry per source location recorded in THAT exception's own
  location trace. The whole report is the concatenation, over every exception in
  the chain, of the per-exception entries.

  The obligations the report must meet:

    (1) Per exception: the entries contributed by a single exception describe
        that exception's OWN trace's source locations, one entry each, in trace
        order -- the location the trace starts at first, the location where that
        exception surfaced last. So their number equals the number of locations
        recorded in that exception's own trace, and an exception whose trace is
        empty contributes no entries.

    (2) Across the chain: EVERY exception contributes its own entries
        INDEPENDENTLY of every other. The entries of one exception never depend
        on, and are never suppressed by, the trace of another. Hence the total
        number of entries is the sum of the per-exception trace lengths; an
        exception with a non-empty trace still contributes its entries even when
        another exception in the chain has an empty trace.

    (3) The report is READ POSITIONALLY, so WHICH location each entry describes,
        and where that entry sits, are as observable as how many entries there
        are. A reader is shown the innermost cause's locations first and the
        outermost exception's own locations last; each exception's entries stay
        together, in trace order, as one contiguous block; and the blocks appear
        in the order the report consumes the chain. So no block is interleaved
        with another, internally reordered, or exchanged with another, and the
        entry a given position carries is determined by the chain alone.

    (4) Each entry is ATTRIBUTED: it says not merely which position of some
        trace it describes but WHOSE trace that is. A reader distinguishes the
        exceptions of the chain from one another, so the block a given exception
        contributes must be drawn from THAT exception's own trace -- never from
        another exception's, and not even from one whose trace happens to record
        the same number of locations. Two exceptions of the chain therefore never
        contribute the same entries, and an exception's own locations are never
        reported in place of a different exception's.

A single exception is abstracted by the length of its own location trace (a
non-negative int). The chain is the list of those lengths in chain order, the
innermost cause LAST.
The chain's source locations are NUMBERED consecutively, exception by exception
in chain order: the first exception of the chain owns the lowest numbers, one per
location its own trace records, then the next exception owns the numbers that
follow, and so on. Every exception therefore owns a block of consecutive location
numbers of its OWN, disjoint from every other exception's, and `locations_before`
gives where an exception's block of numbers begins. A report entry is abstracted
by the number of the chain location it describes, which names both WHOSE trace
the entry comes from and WHICH location of that trace it is. The report is
therefore a `List[int]` of those location numbers in report order, which makes
the count, the content, the placement and the attribution of every entry
observable. The pure fold `chain_total` gives the report's length and the pure
function `entry_location` gives, for a report position, the chain location the
entry there must describe; together they determine the report completely from the
chain.

No callee is axiomatized: the behaviour is pure counting/placement logic over the
chain's own data, modelled deeply.

Termination (total correctness): emitting the report is bounded work -- one pass
per exception in the FINITE chain and, inside it, one pass per source location in
that exception's FINITE trace -- and the report must actually be DELIVERED.
Nagini is a partial-correctness verifier by default, so without an explicit
obligation an implementation that never reaches its return (e.g. an inserted
`while True: pass`) satisfies every `Ensures` vacuously while the real reporter
hangs and emits nothing. The obligation is carried as `MustTerminate` in each
precondition, with each loop discharging it through a strictly decreasing,
bounded-below measure.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def chain_total(lens: PSeq[int]) -> int:
    """Total report-entry count for a chain: the sum of the per-exception trace
    lengths. Front-recursive so a single unfold is available per loop step."""
    if len(lens) == 0:
        return 0
    return lens[0] + chain_total(lens.drop(1))


@Pure
def locations_before(lens: PSeq[int], k: int) -> int:
    """Where exception `k`'s own block of chain location numbers begins: the
    number of locations owned by the exceptions BEFORE it in chain order, i.e.
    the sum of their trace lengths. Since consecutive exceptions own consecutive
    blocks, exception `k` owns exactly the numbers `locations_before(lens, k)`
    up to `locations_before(lens, k) + lens[k]`, and no two exceptions of the
    chain own a number in common."""
    return chain_total(lens) - chain_total(lens.drop(k))


@Pure
def entry_location(lens: PSeq[int], pos: int) -> int:
    """Which of the chain's numbered source locations the entry at report
    position `pos` describes -- the datum that says both WHOSE trace the entry
    comes from and WHICH location of that trace it is.

    Reading the report's structure off the chain: the entries of the exceptions
    the report consumes BEFORE `lens[0]` -- i.e. of `lens.drop(1)`, ending at the
    innermost cause -- come first and there are `chain_total(lens.drop(1))` of
    them; since `lens[0]` is the FIRST exception of the chain it owns the lowest
    `lens[0]` location numbers, so every location number of the rest of the chain
    is shifted up by `lens[0]`. The remaining positions are the block of
    `lens[0]` itself, laid down in trace order, so the position `k` places past
    that block's start describes that exception's own location `k`. Total on every
    int (positions past the report's end are not constrained by anything that
    reads it)."""
    if len(lens) == 0:
        return 0
    if pos < chain_total(lens.drop(1)):
        return lens[0] + entry_location(lens.drop(1), pos)
    return pos - chain_total(lens.drop(1))
# pure-end


def frames_from_traceback(chain: PSeq[int], k: int) -> List[int]:
    # pre-conditions-start
    # ONE named exception's contribution: the entries for the source locations
    # recorded in the trace of exception `k` OF THIS CHAIN. The exception is
    # identified by its place in the chain, not merely by how long its trace is,
    # because the entries it contributes are its OWN (obligation 4).
    Requires(0 <= k and k < len(chain))
    Requires(chain[k] >= 0)
    # TERMINATION (total correctness): a single exception's contribution is one
    # bounded pass over its own FINITE trace, and it must actually DELIVER the
    # entries. Level 2 (not 1): the body builds a list, and `list.__init__` /
    # `list.append` carry their own obligation at level 1, so the caller needs
    # room strictly above them.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The per-exception count is exactly this exception's own trace length: an
    # empty trace yields no entries (obligation 1).
    Ensures(len(Result()) == chain[k])
    # ... and the entries describe the locations THIS exception owns, one each, in
    # trace order: the entry in position j is the one for this exception's own
    # location j, which is the chain location numbered
    # `locations_before(chain, k) + j`, so the location where this exception
    # surfaced is the block's LAST entry. Because an exception's block of location
    # numbers is disjoint from every other exception's, an entry drawn from a
    # DIFFERENT exception's trace -- even one recording the same number of
    # locations -- carries a number outside this range and is excluded. Nothing is
    # emitted for a location this exception's trace does not record, and no
    # location is emitted twice (obligations 1, 3 and 4).
    Ensures(Forall(int, lambda j: Implies(0 <= j and j < chain[k],
                                          Result()[j] ==
                                          locations_before(chain, k) + j)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    start = locations_before(chain, k)
    trace_len = chain[k]
    i = 0
    while i < trace_len:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= trace_len)
        Invariant(trace_len == chain[k])
        Invariant(start == locations_before(chain, k))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                result[j] == start + j)))
        Invariant(MustTerminate(trace_len - i + 1))
        # invariants-end
        result.append(start + i)
        i = i + 1
    return result
    # impl-end


def assemble_frames(trace_lens: List[int]) -> List[int]:
    # pre-conditions-start
    # The chain: `trace_lens[k]` is the trace length of the k-th exception, in
    # chain order (the innermost cause LAST). Read-only input at fractional
    # permission (directive 5): assembling the report mutates nothing it is given.
    Requires(Acc(list_pred(trace_lens), 1 / 2))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                            trace_lens[k] >= 0)))
    # TERMINATION (total correctness): the report is the concatenation over a
    # FINITE chain of per-exception contributions, each itself finite, so
    # assembling it is bounded work that must actually DELIVER the report.
    # Level 3, strictly above frames_from_traceback's level 2, because this
    # method calls it (and above the level-1 list builtins it also uses).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(trace_lens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Every exception contributes its own entries independently of every other
    # (obligation 2): the total entry count is the SUM of the per-exception trace
    # lengths -- never short merely because some exception's trace is empty while
    # another's is not.
    Ensures(len(Result()) == chain_total(ToSeq(trace_lens)))
    # ... and every position of the report carries the entry the chain says
    # belongs there: the blocks of the exceptions consumed earlier first, each
    # exception's own locations contiguous and in trace order, the outermost
    # exception's own locations last (obligations 1 and 3). Because an entry names
    # the CHAIN location it describes, and each exception owns a block of location
    # numbers disjoint from every other's, this also pins WHOSE trace each entry
    # comes from (obligation 4). Since it pins every position, no block may be
    # dropped, interleaved with another, internally reordered, exchanged with
    # another, generated from an exception other than the one whose turn it is
    # (even one whose trace records the same number of locations), reported twice
    # in place of a different exception's, or filled with an entry that describes
    # a location other than its own.
    Ensures(Forall(int, lambda p: Implies(0 <= p and p < len(Result()),
                                          Result()[p] ==
                                          entry_location(ToSeq(trace_lens), p))))
    # post-conditions-end
    # impl-start
    frames = []  # type: List[int]
    # A SINGLE traversal pointer walks the chain from its end. It enters the
    # trace of the exception being consumed and only ever advances to the NEXT
    # exception from INSIDE the per-location loop, so an exception whose own
    # trace records no location leaves the pointer with nothing to advance from:
    # the walk stops there and every exception still unconsumed -- however many
    # locations its own trace records -- is left out of the report.
    n = len(trace_lens)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(trace_lens))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                 trace_lens[k] >= 0)))
        # TERMINATION: at most `i` passes remain; `i` either drops by one or is
        # cleared when the walk stops, so the bound strictly decreases.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        m = trace_lens[i - 1]
        # where the block of chain location numbers owned by the exception the
        # pointer is walking begins
        start = locations_before(ToSeq(trace_lens), i - 1)
        # Position of the location the pointer stands on within the trace it is
        # walking; the entry emitted describes that location.
        pos = 0
        while pos < m:
            # invariants-start
            Invariant(Acc(list_pred(trace_lens), 1 / 2))
            Invariant(Acc(list_pred(frames)))
            Invariant(n == len(trace_lens))
            Invariant(0 < i and i <= n)
            Invariant(0 <= pos and pos <= m)
            Invariant(m == trace_lens[i - 1])
            Invariant(start == locations_before(ToSeq(trace_lens), i - 1))
            Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                     trace_lens[k] >= 0)))
            # TERMINATION: at most `m - pos` passes remain within this trace.
            Invariant(MustTerminate(m - pos + 1))
            # invariants-end
            frames.append(start + pos)
            pos = pos + 1
        if m == 0:
            # The pointer never entered a location, so there is nothing for it to
            # advance from: the walk ends here.
            i = 0
        else:
            i = i - 1
    return frames
    # impl-end
