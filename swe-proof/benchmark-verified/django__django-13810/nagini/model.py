"""Twin-artifact model for django__django-13810.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request-handling chain is assembled by walking an ordered list of optional
  processing layers. The walk threads a running pair of values forward:

    * the current handler (an opaque object whose identity is observable —
      modelled as the sequence of adaptation tokens applied to it so far), and
    * a single flag recording whether that current handler operates in the
      asynchronous mode.

  For each layer the walk first computes a tentatively-adapted handler for the
  layer's target mode, then attempts to attach the layer. Attaching a layer may
  signal that the layer declines to participate. The required behaviour:

    * When a layer participates, the running handler advances to the attached
      layer's wrapper and the running async-mode flag advances to that layer's
      target mode.

    * When a layer DECLINES to participate, the walk moves on to the next layer
      WITHOUT carrying forward any change: both the running handler and the
      running async-mode flag that the next layer sees must be exactly the
      values that were in force before this declining layer was visited. A
      tentative adaptation computed for a declining layer must leave no trace on
      the chain that the next layer inherits.

  The final running pair (handler, async-mode flag) after the whole walk is the
  assembled chain.

The handler object is modelled as ``List[int]`` — the trace of adaptation
tokens applied to it (Nagini bans opaque-object identity, so the trace makes
identity observable); the async-mode flag is modelled as ``int`` in {0, 1}.
The per-layer data are parallel ``List`` columns: ``target_mode[i]`` in {0, 1}
is the layer's target async mode, ``declines[i]`` in {0, 1} records whether
attaching the layer signals a decline. Two unchanged callees that derive a new
handler from an old one (a mode adapter and a wrapper constructor) are modelled
deeply as token-appending maps and validated out-of-band (axiom_check.py / G-AX),
not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The two unchanged callees that derive a new
#  handler from an old one are modelled DEEPLY as the pure token maps
#  `adapt_token` / `wrap_token` below, validated == the real callees by
#  axiom_check.py / G-AX. See refinement.md (A-reference) / mapping.md.)
# axioms-end


# pure-start
ADAPT_TOKEN = 1   # token appended by the mode adapter
WRAP_TOKEN = 2    # token appended by the wrapper constructor


@Pure
def adapt_token(handler: PSeq[int], target_mode: int) -> PSeq[int]:
    """Deep model of the unchanged mode adapter: it derives a NEW handler from
    `handler` for `target_mode`, recorded as appending an adaptation token. It
    never alters the input handler in place (a fresh derived value)."""
    return handler + PSeq(ADAPT_TOKEN, target_mode)


@Pure
def wrap_token(handler: PSeq[int]) -> PSeq[int]:
    """Deep model of the unchanged wrapper constructor: it derives a NEW handler
    wrapping `handler`, recorded as appending a wrapper token."""
    return handler + PSeq(WRAP_TOKEN)


@Pure
def committed_handler(old_handler: PSeq[int], target_mode: int) -> PSeq[int]:
    """The handler a PARTICIPATING layer commits forward: the old handler is
    adapted to the layer's target mode and then wrapped."""
    return wrap_token(adapt_token(old_handler, target_mode))


@Pure
def final_handler(handler: PSeq[int], async_mode: int,
                  target_mode: PSeq[int], declines: PSeq[int],
                  i: int) -> PSeq[int]:
    """Final running handler after walking layers i, i+1, ... in order, starting
    from running state (handler, async_mode). Front-recursive (one unfold per
    layer). A declining layer passes the running handler through unchanged; a
    participating layer commits the adapted+wrapped handler and the next layer
    starts from the layer's target mode."""
    Requires(0 <= i and i <= len(target_mode))
    Requires(len(target_mode) == len(declines))
    if i == len(target_mode):
        return handler
    if declines[i] == 1:
        return final_handler(handler, async_mode, target_mode, declines, i + 1)
    return final_handler(committed_handler(handler, target_mode[i]),
                         target_mode[i], target_mode, declines, i + 1)


@Pure
def final_async(handler: PSeq[int], async_mode: int,
                target_mode: PSeq[int], declines: PSeq[int],
                i: int) -> int:
    """Final running async-mode flag after walking layers i, i+1, ... in order.
    Same front-recursion: a declining layer passes the flag through unchanged; a
    participating layer advances the flag to the layer's target mode."""
    Requires(0 <= i and i <= len(target_mode))
    Requires(len(target_mode) == len(declines))
    if i == len(target_mode):
        return async_mode
    if declines[i] == 1:
        return final_async(handler, async_mode, target_mode, declines, i + 1)
    return final_async(committed_handler(handler, target_mode[i]),
                       target_mode[i], target_mode, declines, i + 1)
# pure-end


def assemble_chain(target_mode: List[int], declines: List[int],
                   base_async: int) -> Tuple[List[int], int]:
    # pre-conditions-start
    Requires(Acc(list_pred(target_mode), 1 / 2))
    Requires(Acc(list_pred(declines), 1 / 2))
    Requires(len(target_mode) == len(declines))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target_mode), 1 / 2))
    Ensures(Acc(list_pred(declines), 1 / 2))
    Ensures(len(target_mode) == len(declines))
    Ensures(len(ToSeq(target_mode)) == len(ToSeq(declines)))
    Ensures(Acc(list_pred(Result()[0])))
    # The assembled handler is the running handler after the whole walk, started
    # from the empty base handler in mode `base_async`. Declining layers leave
    # no trace on the handler the next layer inherits.
    Ensures(ToSeq(Result()[0]) == final_handler(PSeq(0).take(0), base_async,
                                                 ToSeq(target_mode),
                                                 ToSeq(declines), 0))
    # The assembled async-mode flag is the running flag after the whole walk; a
    # declining layer cannot advance it.
    Ensures(Result()[1] == final_async(PSeq(0).take(0), base_async,
                                        ToSeq(target_mode),
                                        ToSeq(declines), 0))
    # post-conditions-end
    # impl-start
    handler = []  # type: List[int]
    handler_is_async = base_async
    i = 0
    while i < len(target_mode):
        # invariants-start
        Invariant(Acc(list_pred(target_mode), 1 / 2))
        Invariant(Acc(list_pred(declines), 1 / 2))
        Invariant(len(target_mode) == len(declines))
        Invariant(Acc(list_pred(handler)))
        Invariant(0 <= i and i <= len(target_mode))
        # The running pair (handler, handler_is_async) is exactly the fold over
        # the prefix already walked: equivalently, the remaining walk from here
        # reproduces the whole walk's result.
        Invariant(final_handler(ToSeq(handler), handler_is_async,
                                ToSeq(target_mode), ToSeq(declines), i) ==
                  final_handler(PSeq(0).take(0), base_async,
                                ToSeq(target_mode), ToSeq(declines), 0))
        Invariant(final_async(ToSeq(handler), handler_is_async,
                              ToSeq(target_mode), ToSeq(declines), i) ==
                  final_async(PSeq(0).take(0), base_async,
                              ToSeq(target_mode), ToSeq(declines), 0))
        Invariant(MustTerminate(len(target_mode) - i + 1))
        # invariants-end
        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            # Layer declines: move on; the tentative adaptation is discarded so
            # the next layer inherits the unchanged running handler / flag.
            i = i + 1
            continue
        # Layer participates: commit the adapted+wrapped handler and advance the
        # running async-mode flag to this layer's target mode.
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1
    return handler, handler_is_async
    # impl-end
