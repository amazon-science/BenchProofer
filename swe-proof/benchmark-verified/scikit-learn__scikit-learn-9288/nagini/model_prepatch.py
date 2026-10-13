"""Twin-artifact model for scikit-learn__scikit-learn-9288.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A clustering routine performs several independent restarts from a configured
  pseudo-random source, then keeps the best restart. The routine offers two
  execution strategies (a single-worker strategy and a multi-worker strategy),
  selected by a resource count, but BOTH strategies must explore the same
  restarts so the kept result does not depend on which strategy is used.

  To guarantee this, the per-restart randomness must be drawn ONCE, up front,
  as a single vector of independent restart seeds taken from the configured
  source: restart i is run from `seed_vector[i]`, the i-th draw of the shared
  source. Every execution strategy then consumes that same vector, so the
  restart that restart i explores is a function of the configured source alone
  and is identical across strategies.

  The consequence the specification pins is that the single-worker strategy's
  per-restart seeds are NOT taken from a differently-evolving source than the
  multi-worker strategy's; both equal the one up-front draw vector. Restart i is
  seeded from the i-th draw (the (i)-fold-advanced state of the source), so the
  vector advances across restarts and is shared verbatim by both strategies.

The pseudo-random source's internal state is modelled as an integer. Obtaining
the source's initial state from the configuration, advancing it by one draw, and
reading the integer seed a draw yields are unchanged primitives, modelled as
abstract pure functions (`source_state`, `advance`, `draw`) whose real
counterparts are validated out-of-band by axiom_check.py (G-AX). The up-front
restart-seed vector is modelled deeply as a front-recursive fold (`seed_vector`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def source_state(config: int) -> int:
    """Initial internal state of the pseudo-random source obtained from an
    integer configuration value (the unchanged configuration-to-source step).
    Abstract: the proof relies only on this being a deterministic function of
    the configuration, not on any particular value. Real counterpart +
    executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def advance(state: int) -> int:
    """Internal state of the pseudo-random source after one draw advances it
    (the unchanged per-draw state transition). Abstract: the proof relies only
    on it being a deterministic function of the current state. That the real
    transition actually MOVES the state (so successive restart seeds differ) is
    the discriminating fact validated by axiom_check.py (G-AX), not a consumed
    contract here. Real counterpart: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def draw(state: int) -> int:
    """The integer restart seed yielded by a single draw taken at source state
    `state` (the unchanged read of a draw's value). Abstract: a deterministic
    function of the current state. Real counterpart: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def seed_vector(s: int, n: int) -> PSeq[int]:
    """The up-front vector of `n` independent restart seeds drawn from one
    shared source starting at state `s`: restart 0 takes the draw at `s`,
    restart 1 the draw at `advance(s)`, restart k the draw at the k-fold advance
    of `s`. Front-recursive on `n` so a single unfold is available per loop
    step. This is the one vector both execution strategies must consume."""
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(draw(s)) + seed_vector(advance(s), n - 1)
# pure-end


def restart_seeds(config: int, n_restarts: int) -> List[int]:
    """The per-restart seeds the single-worker strategy uses for `n_restarts`
    restarts from the source configured by integer `config`. Element k is the
    integer seed restart k is run from. The specification requires this to be
    the SAME up-front draw vector the multi-worker strategy consumes, so the
    kept result is strategy-independent."""
    # pre-conditions-start
    Requires(n_restarts >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_restarts)
    # The per-restart seeds are the one up-front draw vector from the source's
    # initial state: restart k is seeded from the k-th draw (the k-fold-advanced
    # state), the identical vector the multi-worker strategy consumes.
    Ensures(ToSeq(Result()) == seed_vector(source_state(config), n_restarts))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the single-worker strategy hands the one live
    # source object to EVERY restart instead of consuming the up-front draw
    # vector. Conceptually every restart shares the one source at its initial
    # state, so each restart's effective seed is the single draw at `start`,
    # rather than the i-th draw of the advancing vector the multi-worker
    # strategy uses. The per-restart seeds therefore collapse to one repeated
    # value and diverge from the up-front vector.
    start = source_state(config)
    shared = draw(start)
    result = []  # type: List[int]
    i = 0
    while i < n_restarts:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_restarts)
        Invariant(len(result) == i)
        Invariant(MustTerminate(n_restarts - i + 1))
        # invariants-end
        result = result + [shared]  # the one shared source, every restart
        i = i + 1
    return result
    # impl-end
