"""Twin-artifact model for django__django-17029.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An application registry keeps several memoizing lookup methods, each backed
  by its own bounded result cache whose occupancy (the number of distinct
  argument tuples whose result is currently retained) can be observed. The
  registry exposes a single cache-reset operation whose documented promise is
  to discard ALL of those retained results — every memoizing method's cache —
  so that immediately afterwards each cache's occupancy is zero, regardless of
  how full any of them was beforehand. A reset that leaves any one method's
  retained results in place would violate that promise: a later observer would
  still see stale memoized values for that method.

  The reset is a bounded, straight-line operation: it MUST terminate and
  return to its caller (a total-correctness obligation, carried as
  MustTerminate in the precondition). A reset that diverges never delivers
  the emptied caches to any later observer, so it does not honour the
  promise either.

The registry is modelled as a minimal class carrying only the touched state:
one non-negative occupancy counter per memoizing method (here the all-models
lookup and the swappable-settings-name lookup). The reset operation clears
every counter to zero. No string/float content is involved, so the carrier
types are plain ints; no library callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Registry:
    def __init__(self, models_cache_occupancy: int,
                 swappable_cache_occupancy: int) -> None:
        Requires(models_cache_occupancy >= 0)
        Requires(swappable_cache_occupancy >= 0)
        # Constructing a registry is bounded work; the strictly smaller
        # measure (1 < 2) lets a caller holding MustTerminate(2) construct
        # a fresh registry without leaking its obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.models_cache_occupancy) and  # type: ignore
                self.models_cache_occupancy == models_cache_occupancy)  # type: ignore
        Ensures(Acc(self.swappable_cache_occupancy) and  # type: ignore
                self.swappable_cache_occupancy == swappable_cache_occupancy)  # type: ignore
        self.models_cache_occupancy = models_cache_occupancy
        self.swappable_cache_occupancy = swappable_cache_occupancy


# axioms-start
# (no library callee is axiomatized: the reset is a pure state operation on the
#  registry's own observable cache occupancies, modelled directly.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def clear_all_caches(registry: Registry) -> None:
    # pre-conditions-start
    Requires(Acc(registry.models_cache_occupancy))
    Requires(Acc(registry.swappable_cache_occupancy))
    # The reset performs a bounded amount of straight-line work and MUST
    # terminate (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. `while True: pass` inserted before the clears)
    # would satisfy the two zero-occupancy postconditions only vacuously,
    # yet would never return to its caller and never deliver the emptied
    # caches to any later observer; this obligation rejects any such
    # implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(registry.models_cache_occupancy))
    Ensures(Acc(registry.swappable_cache_occupancy))
    # EVERY memoizing method's cache is emptied: each occupancy is zero
    # afterwards, no matter what it was before.
    Ensures(registry.models_cache_occupancy == 0)
    Ensures(registry.swappable_cache_occupancy == 0)
    # post-conditions-end
    # impl-start
    registry.models_cache_occupancy = 0
    # impl-end
