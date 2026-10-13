"""Twin-artifact model for django__django-10914.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filesystem content store resolves the numeric permission mode it will
  apply to freshly stored content. The store may carry a per-instance override
  for this mode; when it does, that override is used verbatim. When the store
  carries NO per-instance override (the override is absent), the store falls
  back to a project-wide default mode, and that default mode is the definite
  octal value 0o644 (420 in decimal) rather than being absent.

  So the resolution is:
    * an explicit per-instance override passes through unchanged, and
    * in the absence of any override the effective mode is a concrete,
      non-absent permission value, 0o644.

The per-instance override and the resolved mode are modelled as ``Optional[int]``
(an absent value is ``None``; a present value is the integer the caller would
hand to a chmod-style primitive). The desired project-wide default is the
concrete integer 0o644, so the resolved mode is required to be a definite,
non-absent permission value whenever no override is configured.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the resolution is a total integer/None computation modelled
# deeply; it calls no opaque library callee.)
# axioms-end


# pure-start
@Pure
def default_mode() -> int:
    """The project-wide default numeric mode that should be handed to a
    chmod-style primitive when a store configures nothing more specific: a
    definite, owner-and-group-readable octal mode 0o644 (decimal 420)."""
    return 420  # 0o644
# pure-end


def resolve_storage_mode(override: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    # (no heap permissions: the override and result are immutable scalars.)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # An explicit per-instance override is used verbatim.
    Ensures(Implies(override is not None, Result() is override))
    # With no per-instance override the effective mode is the project-wide
    # default, the concrete octal value 0o644 == 420, and is NEVER absent.
    Ensures(Implies(override is None, Result() is not None))
    Ensures(Implies(override is None, Result() == default_mode()))
    Ensures(Implies(override is None, Result() == 420))
    # post-conditions-end
    # impl-start
    # Pre-patch project-wide default: ABSENT -- no concrete fallback mode is
    # configured, so an unconfigured store yields an unspecified (absent) mode.
    default = None  # type: Optional[int]
    # Resolution: an absent override falls back to the project-wide default;
    # otherwise the override is used verbatim.
    if override is None:
        return default
    return override
    # impl-end
