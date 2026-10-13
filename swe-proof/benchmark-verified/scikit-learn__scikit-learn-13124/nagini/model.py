"""Twin-artifact model for scikit-learn__scikit-learn-13124.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stratified splitter assigns, independently within each class, a randomized
  test-fold ordering drawn from a configured pseudo-random source. The source
  is described by a single seed value. When several classes are processed in
  turn, the randomized draw used for each class must come from one shared
  pseudo-random stream that ADVANCES between classes: the draw for the k-th
  class is the stream's state after k advances from the seed's initial state.

  The consequence the specification pins is that successive classes are NOT all
  drawn from one and the same unchanging state. A correct splitter therefore
  makes the per-class draws depend on the position in the stream (class 0 from
  the initial state, class 1 from the once-advanced state, and so on), so that
  the whole assignment is a function of the entire stream rather than of a
  single repeated draw.

The pseudo-random source's internal state is modelled as an integer. Turning
the configured seed into a source, and advancing the source by one draw, are
unchanged primitives, modelled as abstract pure functions (`seed_state`,
`advance`) whose real counterparts are validated out-of-band by axiom_check.py
(G-AX). The per-class stream of draw states is modelled deeply as a
front-recursive fold (`state_stream`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def seed_state(seed: int) -> int:
    """Initial internal state of the pseudo-random source obtained from an
    integer seed (the unchanged seed-to-source conversion). Abstract: the proof
    relies only on this being a deterministic function of the seed, not on any
    particular value. Real counterpart + executable soundness: mapping.md /
    axiom_check.py.
    """


@Pure
@ContractOnly
def advance(state: int) -> int:
    """Internal state of the pseudo-random source after one draw advances it
    (the unchanged per-draw state transition). Abstract: the proof relies only
    on it being a deterministic function of the current state. That the real
    transition actually MOVES the state (so successive per-class draws differ)
    is the discriminating fact validated by axiom_check.py (G-AX), not a
    consumed contract here. Real counterpart: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def state_stream(s: int, n: int) -> PSeq[int]:
    """The sequence of draw states for `n` successive classes sharing one
    advancing source that starts at state `s`: class 0 draws from `s`, class 1
    from `advance(s)`, class k from the k-fold advance of `s`. Front-recursive
    on `n` so a single unfold is available per loop step."""
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(s) + state_stream(advance(s), n - 1)
# pure-end


def per_class_draw_states(seed: int, n_classes: int) -> List[int]:
    """Per-class draw states when `n_classes` classes are processed in turn
    from the source configured by integer `seed`. Element k is the state the
    k-th class's randomized draw is taken from."""
    # pre-conditions-start
    Requires(n_classes >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_classes)
    # The per-class draw states are the advancing stream from the seed's
    # initial state: class k draws from the k-fold-advanced state, so no two
    # classes are pinned to one and the same unchanging state.
    Ensures(ToSeq(Result()) == state_stream(seed_state(seed), n_classes))
    # post-conditions-end
    # impl-start
    start = seed_state(seed)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_classes:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_classes)
        Invariant(len(result) == i)
        # "what is built ++ the stream of the rest == the whole stream":
        # `result` is the first i draw states and `cur` is the state the i-th
        # class would draw, so the stream of the remaining n-i classes from
        # `cur` completes exactly the full stream.
        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
                  state_stream(start, n_classes))
        # invariants-end
        # The remaining stream is non-empty (i < n_classes), so it unfolds to
        # its head `cur` followed by the stream from the advanced state --
        # exactly the move performed below.
        Assert(state_stream(cur, n_classes - i) ==
               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
        result = result + [cur]
        cur = advance(cur)
        i = i + 1
    return result
    # impl-end
