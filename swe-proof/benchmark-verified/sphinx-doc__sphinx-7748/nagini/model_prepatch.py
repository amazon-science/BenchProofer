"""Twin-artifact model for sphinx-doc__sphinx-7748.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documented object may carry, at the top of its documentation block, one or
  more candidate signature lines. The lines form a carry-over run: a line is
  marked as *open* when it ends with a trailing line-spillover marker, meaning
  the signature description carries over to the following line; a line that is
  not so marked *terminates* the run. Each line, once stripped of any spillover
  marker, is parsed into a signature value.

  The behaviour pinned here is how MANY of these candidate signatures are
  gathered: the gatherer collects the values of every line from the top of the
  block up to and including the FIRST terminating (non-open) line. In
  particular:

    * a run whose only line terminates immediately yields exactly that one
      signature;
    * a run whose leading lines are each open yields ALL of them together with
      the first terminating line that follows — never just the first.

  The rendered result is the ordered sequence of those collected signature
  values, in source order. The discriminating case is a run of length >= 2 in
  which the leading line is open: the result must contain every collected
  signature, not merely the leading one.

A documentation block is modelled as two equal-length parallel ``List[int]``
streams aligned to line order: a per-line *carry-over flag* (non-zero iff the
line spills over onto the next) and a per-line *signature value* (an opaque
integer token standing for the parsed ``(args) -> return`` description of that
line). The collected sequence is carried by the pure sequence theory
``PSeq[int]`` as a front-recursive run. No callee is axiomatized: the gathering
is structural logic over the abstract per-line flags and values, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms: the gathering of candidate signatures is structural
#  logic over the abstract per-line carry-over flags and signature values,
#  spelled out in full. There is no unchanged opaque callee whose contract the
#  proof consumes.)
# axioms-end


# pure-start
@Pure
def run_len(cont: PSeq[int]) -> int:
    """Number of lines collected from the top of the block: every leading
    open line plus the first terminating line. A line is *open* iff its flag is
    non-zero. Front-recursive so a single unfold is available per loop step.
    The empty block collects nothing."""
    Ensures(Implies(len(cont) > 0, Result() >= 1 and Result() <= len(cont)))
    Ensures(Implies(len(cont) == 0, Result() == 0))
    if len(cont) == 0:
        return 0
    if cont[0] != 0:
        return 1 + run_len(cont.drop(1))
    return 1


@Pure
def collected(cont: PSeq[int], val: PSeq[int]) -> PSeq[int]:
    """The ordered sequence of collected signature values: the value of every
    line from the top up to and including the first terminating line. While the
    leading line is open, prepend its value and recurse; the first terminating
    line contributes its value and stops the run. Front-recursive (one unfold
    per line) so the forward impl loop can discharge it."""
    Ensures(Implies(len(cont) <= len(val), len(Result()) == run_len(cont)))
    if len(cont) == 0 or len(val) == 0:
        return PSeq(0).take(0)
    if cont[0] != 0:
        return PSeq(val[0]) + collected(cont.drop(1), val.drop(1))
    return PSeq(val[0])
# pure-end


def gather_signatures(cont: List[int], val: List[int]) -> List[int]:
    # pre-conditions-start
    # The two parallel per-line streams of the documentation block: ``cont`` is
    # the carry-over flag of each candidate signature line, ``val`` the parsed
    # signature value of each. Both are read-only (the gatherer mutates neither)
    # and so are required AND ensured at fractional permission (directive 5).
    # The streams are aligned line-for-line, and the block is non-empty (there
    # is at least one candidate signature line to gather).
    Requires(Acc(list_pred(cont), 1 / 2))
    Requires(Acc(list_pred(val), 1 / 2))
    Requires(len(cont) == len(val))
    Requires(len(cont) > 0)
    # The gathering must COMPLETE (total correctness): without this obligation
    # every Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 2 leaves room for the list allocation it performs (at level
    # 1 the allocation's own obligation has nowhere below the caller to go); it
    # calls no other obligated method.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cont), 1 / 2))
    Ensures(Acc(list_pred(val), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the collected run: the values of every line from the
    # top up to and including the first terminating line. This pins the
    # discriminating behaviour — when leading lines are open, ALL their
    # signatures are present, not only the first.
    Ensures(ToSeq(Result()) == collected(ToSeq(cont), ToSeq(val)))
    # The number of collected signatures is exactly the run length, so a run of
    # length >= 2 (an open leading line) yields more than one signature.
    Ensures(len(Result()) == run_len(ToSeq(cont)))
    # The leading signature is always the first collected value.
    Ensures(len(val) > 0 and len(Result()) >= 1 and Result()[0] == val[0])
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: only the single leading candidate signature line is
    # ever consulted; its value is taken and the gather stops immediately,
    # ignoring the carry-over marker entirely. The result is therefore always
    # the singleton [val[0]] regardless of how many open lines follow. This
    # fails the postcondition (and the run-length clause) on any block whose
    # leading line is open: there the collected run has length >= 2.
    result = [val[0]]  # type: List[int]
    return result
    # impl-end
