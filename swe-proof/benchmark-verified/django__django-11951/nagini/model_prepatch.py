"""Twin-artifact model for django__django-11951.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a bulk database write is split into batches, the size of each batch is
  governed by two numbers:

    * a caller-requested size (a positive integer when the caller asks for an
      explicit size, or absent/auto when the caller leaves it to the system),
      and
    * a backend-imposed maximum, which is whatever the backend reports as the
      largest workable batch, but never less than one.

  The effective batch size that drives the slicing of the work into batches
  must respect BOTH bounds:

    * if the caller requested an explicit size, the effective size is the
      smaller of that request and the backend maximum (so an over-large
      request can never exceed what the backend can actually handle), and
    * if the caller requested nothing, the effective size is the backend
      maximum.

  In particular the effective size is always at least one and never exceeds
  the backend maximum, regardless of how large a value the caller requested.
  The number of batches the work is divided into is the ceiling of the item
  count over the effective size, so a request that would have produced too few
  (too large) batches is correctly tightened down to the backend's capacity.

The values involved are ordinary non-negative integers; no string or float
modelling is needed. The backend maximum is modelled as an opaque non-negative
integer the backend reports (clamped up to one), and the auto/absent request is
modelled as the integer zero (a real explicit request is always strictly
positive). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the clamp and the min/auto selection are modelled
#  deeply over plain integers)
# axioms-end


# pure-start
@Pure
def clamped_max(raw_backend_limit: int) -> int:
    """The backend-reported maximum, never allowed below one: the backend may
    report any non-negative integer, but the workable maximum is at least
    one."""
    Requires(raw_backend_limit >= 0)
    Ensures(Result() >= 1)
    Ensures(Implies(raw_backend_limit >= 1, Result() == raw_backend_limit))
    Ensures(Implies(raw_backend_limit < 1, Result() == 1))
    if raw_backend_limit >= 1:
        return raw_backend_limit
    return 1
# pure-end


def effective_batch_size(requested: int, raw_backend_limit: int) -> int:
    # pre-conditions-start
    # `requested == 0` models the auto/absent request; a real explicit request
    # is strictly positive. The backend value is a non-negative integer.
    Requires(requested >= 0)
    Requires(raw_backend_limit >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result respects the backend maximum (clamped to at least one) ...
    Ensures(Result() >= 1)
    Ensures(Result() <= clamped_max(raw_backend_limit))
    # ... and an explicit request additionally caps the result at that request,
    # the result being exactly the smaller of the two bounds.
    Ensures(Implies(requested > 0, Result() <= requested))
    Ensures(Implies(requested > 0,
                    Result() == (requested if requested <= clamped_max(raw_backend_limit)
                                 else clamped_max(raw_backend_limit))))
    # With no explicit request the result is exactly the backend maximum.
    Ensures(Implies(requested == 0, Result() == clamped_max(raw_backend_limit)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: an explicit request is used as-is, ignoring
    # the backend maximum; only the auto/absent case consults the backend.
    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        result = requested
    else:
        result = max_batch_size
    return result
    # impl-end
