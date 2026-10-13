"""Twin-artifact model for django__django-14493.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable, possibly-zero number of refinement passes is run over a set
  of files. Each pass reports whether it produced any change. A single boolean
  flag records whether the most recently completed pass produced a change; the
  loop stops early as soon as a pass produces no change. After the passes
  finish, that flag is consulted to decide whether to report that the bound on
  the number of passes was reached without the process settling.

  The contract demanded here is that this consultation is always well defined,
  INCLUDING when the configured number of passes is zero: with zero passes the
  flag must read as "no change produced" (so that no spurious "bound reached"
  report is emitted), and the operation must complete normally and return a
  definite boolean on every path — never leave the flag undefined.

  The returned boolean is exactly: at least one pass was run AND every pass that
  ran produced a change (equivalently: the loop exhausted its allowance without
  ever observing a change-free pass). With zero allowed passes this is false.

The per-pass "produced a change" outcomes are modelled as a read-only
`List[int]` of 0/1 flags (flag i is the outcome of pass i); the number of
allowed passes is a non-negative `int`. The specification is carried over the
pure mathematical sequence `PSeq[int]` by the front-recursive predicate
`all_changed`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axioms. The only behaviour under specification — the definite-assignment
# and early-stop semantics of the pass loop — is modelled deeply below; it
# calls no opaque, unchanged library callee that the proof must assume.)
# axioms-end


# pure-start
@Pure
def all_changed(flags: PSeq[int], n: int) -> bool:
    """True iff every one of the first n passes reported a change (flag != 0).
    Recursive on the pass count n; n == 0 is vacuously True (no pass reported
    'no change'). Phrased over a pure sequence so it carries no heap framing.
    """
    Requires(0 <= n and n <= len(flags))
    if n == 0:
        return True
    return flags[n - 1] != 0 and all_changed(flags, n - 1)
# pure-end


def lemma_unfold(flags: PSeq[int], n: int) -> None:
    """One-step unfold of `all_changed` at a symbolic count, so the loop can
    extend the all-changed prefix from n-1 to n after a change-reporting pass.
    """
    Requires(1 <= n and n <= len(flags))
    Ensures(all_changed(flags, n) ==
            (flags[n - 1] != 0 and all_changed(flags, n - 1)))


def lemma_change_free_kills(flags: PSeq[int], k: int, n: int) -> None:
    """If pass k reported no change (flag == 0) and k < n, then the first n
    passes are not all-changed. Proved by recursion downward on n.
    """
    Requires(0 <= k and k < n and n <= len(flags))
    Requires(flags[k] == 0)
    Ensures(not all_changed(flags, n))
    if k < n - 1:
        lemma_change_free_kills(flags, k, n - 1)


def run_passes(pass_changed: List[int], max_passes: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(pass_changed), 1 / 2))
    # The number of allowed passes is non-negative and indexes into the
    # per-pass outcomes; max_passes == 0 (the zero-pass configuration) is the
    # boundary the contract must keep well defined.
    Requires(0 <= max_passes and max_passes <= len(pass_changed))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pass_changed), 1 / 2))
    Ensures(0 <= max_passes and max_passes <= len(pass_changed))
    # The flag consulted after the passes is ALWAYS a definite boolean (this
    # function returns on every path, including the zero-pass path) and equals
    # the closed form: some pass ran AND every pass that ran reported a change.
    Ensures(Result() == (max_passes > 0 and
                         all_changed(ToSeq(pass_changed), max_passes)))
    # With zero allowed passes the flag reads as "no change to report": the
    # result is a definite False (never absent).
    Ensures(Implies(max_passes == 0, Result() == False))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton. Upstream the flag is assigned ONLY inside the loop body,
    # never before it, so when the loop body never runs (max_passes == 0) the
    # post-loop read is of an UNBOUND local: the operation does not hand back the
    # definite False the contract demands, it exits abruptly (UnboundLocalError).
    # That is the defect under specification, and it is written below as the abrupt
    # exit it produces rather than as the unbound read itself, because the unbound
    # read is not expressible in a translatable module: with no binding on entry
    # mypy reports 'Cannot determine type of "substitutions"' at the first Invariant
    # that reads the flag and nagini aborts in the FRONT END (Translation failed),
    # reaching no Viper verdict at all — and a twin that reaches no verdict is a
    # rejection G-DIFF/G-GOLD never witnessed. Dropping the two invariants that read
    # the flag does make the literal unbound read translate ('Local variable may not
    # have been defined'), but that obligation is emitted at every local read
    # independently of the contract, so it would not show this SPEC sensing the
    # change. The abrupt exit is rejected by the postcondition region itself, which
    # declares no Exsures and so demands normal completion on every path.
    # The pre-loop assignment below is retained ONLY so mypy can type the flag; it is
    # dead on the zero-pass path (the abrupt exit precedes any read), so the
    # observable behaviour is the pre-patch's: abrupt exit iff zero passes, the same
    # value as the gold otherwise.
    substitutions = False
    i = 0
    while i < max_passes:
        # invariants-start
        Invariant(Acc(list_pred(pass_changed), 1 / 2))
        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
        # Before each iteration the flag reflects the passes run so far: True
        # iff at least one pass ran (i > 0) and all of the first i passes changed.
        Invariant(substitutions == (i > 0 and
                                    all_changed(ToSeq(pass_changed), i)))
        # The loop is only re-entered after a change-reporting pass, so reaching
        # i > 0 means the flag is set and the first i passes all changed.
        Invariant(i == 0 or substitutions)
        # invariants-end
        substitutions = pass_changed[i] != 0
        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
        if not substitutions:
            # Early stop: pass i reported no change. Then the full count of
            # passes is not all-changed, so the closed form is False regardless
            # of the remaining allowance.
            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
            return False
        # pass i changed: extend the all-changed prefix from i to i+1.
        lemma_unfold(ToSeq(pass_changed), i + 1)
        i = i + 1
    if max_passes == 0:
        # PRE-PATCH: the post-loop read of the never-initialised flag happens on
        # exactly this path, so the operation exits ABRUPTLY here instead of
        # returning the definite False the contract demands. Nagini's builtin class
        # table has no NameError/UnboundLocalError, so the carrier is the base
        # Exception; what the spec must forbid is the abrupt exit, not the class.
        raise Exception('unbound local: substitutions (zero passes)')
    # Normal completion: i == max_passes, so the running flag already equals the
    # full-range closed form (congruence over the single count argument).
    return substitutions
    # impl-end
