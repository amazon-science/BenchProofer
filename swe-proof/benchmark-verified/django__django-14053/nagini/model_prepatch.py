"""Twin-artifact model for django__django-14053.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-pass routine consumes a collection of distinct files and reports, to
  its caller, the outcome for each file. Every file in the collection must be
  reported, and — this is the property under specification — each file must be
  reported EXACTLY ONCE for its settled outcome, regardless of how many internal
  passes the routine performs over it.

  The collection has two kinds of file. A plain file is settled in a single
  pass and reported once. An adjustable file (one whose contents may reference
  other files and therefore may be revisited across several passes) is, by its
  nature, examined repeatedly until the references stabilise; nevertheless the
  routine must report it to the caller only once, carrying its final outcome —
  not once per pass.

  A file's examination may also FAIL outright instead of yielding a settled
  outcome. That failure outcome is not the routine's to interpret: the caller is
  the component that decides what a failure means and acts on it (it stops the
  run and re-surfaces the failure), so the routine must hand every failure to
  the caller AT THE POINT THE FIRST PASS REACHES IT, at the position the
  enumeration gives that file. This obligation is INDEPENDENT of the multiplicity
  property above, and holding a file back in order to satisfy that property must
  not swallow it: a failure outcome may never be deferred to the end of the run,
  and may never be displaced by the same file's later settled outcome. Deferring
  or displacing it is observable to the caller as a run that reports a settled
  outcome for a file whose examination did not settle, and never reports the
  failure at all.

  Concretely, the reported sequence is two segments. The FIRST-PASS segment:
  every plain file, plus every adjustable file whose examination fails, each
  appearing once, in the order in which the routine enumerates the collection.
  Then the SETTLED segment: every adjustable file, each appearing once, in that
  same enumeration order. The number of reports is therefore the number of files
  in the collection plus one for each adjustable file whose examination fails
  (which is reported for its failure and again for its settled outcome); no file
  is reported twice for a settled outcome.

The collection is modelled as three equal-length parallel `List[int]` streams,
presented in the order the routine enumerates the files: a distinct integer id
per file (the input is keyed, so ids do not repeat), a 0 / non-0 flag marking
which files are adjustable, and a 0 / non-0 flag marking which files' examination
fails. The spec is parametric in that enumeration order -- it constrains WHICH
files are reported and HOW OFTEN, relative to the order the streams present them.

The specification is carried by the pure sequence theory `PSeq[int]` via
`ToSeq`. The reported id sequence is spelled out deeply as the concatenation of
two front-recursive sub-sequence folds (the first-pass ids, then the settled
adjustable ids); no callee is axiomatized — the behaviour is selection/structure
logic over the inputs, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axiom: the report-collection behaviour is membership/structure
# logic over the input streams, modelled deeply as front-recursive folds.)
# axioms-end


# pure-start
@Pure
def first_pass_ids(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> PSeq[int]:
    """The sub-sequence of file ids reported while the FIRST pass runs, in the
    order the stream presents them: a file is reported there if it is not
    adjustable (flag 0) OR if its examination fails (flag non-0) — a failure is
    handed to the caller as the pass reaches the file, adjustable or not.
    Front-recursive so a single unfold is available per loop step (the streams
    are aligned, so all three are consumed in lock-step)."""
    Ensures(len(Result()) <= len(ids))
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return PSeq(0).take(0)
    rest = first_pass_ids(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] == 0 or err[0] != 0:
        return PSeq(ids[0]) + rest
    return rest


@Pure
def adj_ids(ids: PSeq[int], adj: PSeq[int]) -> PSeq[int]:
    """The sub-sequence of file ids that ARE adjustable (flag non-0), in the
    order the stream presents them, each appearing once — the settled segment,
    reported after the passes have stabilised, carrying each file's final
    outcome. Front-recursive."""
    Ensures(len(Result()) <= len(ids))
    if len(ids) == 0 or len(adj) == 0:
        return PSeq(0).take(0)
    rest = adj_ids(ids.drop(1), adj.drop(1))
    if adj[0] != 0:
        return PSeq(ids[0]) + rest
    return rest


@Pure
def failing_adj_count(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> int:
    """How many adjustable files have a failing examination — equivalently, how
    many files are reported in BOTH segments (once for the failure as the first
    pass reaches them, once for their settled outcome). Front-recursive."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(ids))
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return 0
    rest = failing_adj_count(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] != 0 and err[0] != 0:
        return 1 + rest
    return rest


@Pure
def reported(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> PSeq[int]:
    """The full reported id sequence: the first-pass segment (every plain id and
    every failing id, once each) followed by the settled segment (every
    adjustable id, once each)."""
    return first_pass_ids(ids, adj, err) + adj_ids(ids, adj)


@Pure
def lemma_split_len(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> bool:
    """Each file id lands in the first-pass segment, or in the settled segment,
    or — exactly when it is adjustable and its examination fails — in both. So
    the two segment lengths sum to the number of files plus the number of failing
    adjustable files. Proven by front-recursion on the aligned streams; exposed
    to callers as an equation."""
    Requires(len(ids) == len(adj))
    Requires(len(ids) == len(err))
    Ensures(Result())
    Ensures(len(first_pass_ids(ids, adj, err)) + len(adj_ids(ids, adj))
            == len(ids) + failing_adj_count(ids, adj, err))
    if len(ids) == 0:
        return True
    return lemma_split_len(ids.drop(1), adj.drop(1), err.drop(1))
# pure-end


def collect_reports(ids: List[int], adj: List[int], err: List[int]) -> List[int]:
    # pre-conditions-start
    # The three input streams are read-only (the routine reports on them, it
    # does not rewrite the collection): each is required AND ensured at HALF
    # permission (directive 5). The streams are aligned (one adjustable flag and
    # one failure flag per file).
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(adj), 1 / 2))
    Requires(Acc(list_pred(err), 1 / 2))
    Requires(len(ids) == len(adj))
    Requires(len(ids) == len(err))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(adj), 1 / 2))
    Ensures(Acc(list_pred(err), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The report is exactly the first-pass segment followed by the settled
    #     segment: every plain id and every failing id once as the first pass
    #     reaches it, then every adjustable id once with its final outcome. A
    #     failure therefore reaches the caller at its enumeration position and
    #     is never dropped in favour of the same file's settled report.
    Ensures(ToSeq(Result()) == reported(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    # (2) The number of reports equals the number of files, plus one for each
    #     adjustable file whose examination fails. Every file is reported; no
    #     file is reported more than once for a settled outcome (the property
    #     the repeated internal passes must NOT violate — with distinct file ids
    #     this is duplicate-freedom of the settled reports); and every failure
    #     is a report of its own rather than a substitute for one.
    Ensures(len(Result()) == len(ids)
            + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    # post-conditions-end
    # impl-start
    # First pass: report EVERY file (plain and adjustable alike) as the pass
    # reaches it, holding nothing back.
    first = []  # type: List[int]
    i = len(ids)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(ids), 1 / 2))
        Invariant(Acc(list_pred(adj), 1 / 2))
        Invariant(Acc(list_pred(err), 1 / 2))
        Invariant(len(ids) == len(adj))
        Invariant(len(ids) == len(err))
        Invariant(Acc(list_pred(first)))
        Invariant(0 <= i and i <= len(ids))
        Invariant(ToSeq(first) == ToSeq(ids).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        fid = ids[i - 1]
        Assert(ToSeq(ids).drop(i - 1)[0] == fid)
        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
        first = [fid] + first
        i = i - 1
    # Repeat pass over the adjustable files, reporting each one again.
    collected = []  # type: List[int]
    j = len(ids)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(ids), 1 / 2))
        Invariant(Acc(list_pred(adj), 1 / 2))
        Invariant(Acc(list_pred(err), 1 / 2))
        Invariant(len(ids) == len(adj))
        Invariant(len(ids) == len(err))
        Invariant(Acc(list_pred(first)))
        Invariant(Acc(list_pred(collected)))
        Invariant(0 <= j and j <= len(ids))
        Invariant(ToSeq(first) == ToSeq(ids))
        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(j), ToSeq(adj).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        rid = ids[j - 1]
        ra = adj[j - 1]
        Assert(ToSeq(ids).drop(j - 1)[0] == rid)
        Assert(ToSeq(adj).drop(j - 1)[0] == ra)
        Assert(ToSeq(ids).drop(j - 1).drop(1) == ToSeq(ids).drop(j))
        Assert(ToSeq(adj).drop(j - 1).drop(1) == ToSeq(adj).drop(j))
        if ra != 0:
            collected = [rid] + collected
        j = j - 1
    # Report the first pass followed by the repeat pass: adjustable files are
    # reported twice.
    result = first + collected
    return result
    # impl-end
