"""Twin-artifact model for django__django-11138.

Behaviour under specification (stated as the desired behaviour):

  A stored datetime that the database holds as a naive wall clock is, on read,
  normalised so that calendar lookups (date / time / extract / truncate) see it
  in the currently-active time zone. The stored wall clock is expressed in the
  *database connection's* time zone, so normalisation must:

    * reinterpret the stored wall clock as an instant in the connection time
      zone (offset `conn_off` minutes from the universal line), then
    * if a distinct target time zone is requested, re-express that instant as a
      wall clock in the target time zone (offset `target_off`).

  Equivalently, the observed wall clock is shifted by `target_off - conn_off`
  minutes. When the connection and target zones coincide the shift is zero, so
  the value is returned unchanged (and no zone-conversion is needed at all).
  When time-zone support is off, or no target zone is requested, the wall clock
  is returned untouched.

Datetimes are modelled as an integer wall-clock instant in minutes; time zones
as their integer UTC offset in minutes (the only operation the conversion uses
is a constant offset add/subtract). A datetime that fails to parse is outside
this (successful-parse) specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axiom is consumed: the time-zone normalisation is modelled deeply as the
# integer wall-clock arithmetic below. The zone reinterpretation it relies on
# is a constant per-zone offset add/subtract.
# axioms-end


# pure-start
@Pure
def normalised_walltime(stored: int, conn_off: int, target_off: int,
                        has_target: bool, use_tz: bool) -> int:
    """The wall-clock instant (minutes) a read returns for a stored value.

    The stored wall clock is read in the connection zone and (when a distinct
    target zone is requested) re-expressed in the target zone; net shift is
    `target_off - conn_off`. Without active tz support, or without a requested
    target zone, the stored wall clock passes through unchanged."""
    if not use_tz:
        return stored
    if not has_target:
        return stored
    return stored - conn_off + target_off
# pure-end


def local_walltime(stored: int, conn_off: int, target_off: int,
                   has_target: bool, use_tz: bool) -> int:
    # pre-conditions-start
    # All inputs are immutable integers/booleans (no aliasable carrier), so no
    # list/dict permission is required; read-only by construction.
    Requires(use_tz or (not has_target))  # without tz support no target zone is requested
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is the connection-zone-sourced normalisation: the source zone
    # is the CONNECTION offset, never a hard-wired universal zero.
    Ensures(Result() == normalised_walltime(stored, conn_off, target_off,
                                            has_target, use_tz))
    # When tz support is active and a target zone is requested, the observed
    # wall clock is shifted by exactly (target_off - conn_off) from the stored
    # connection-zone wall clock.
    Ensures(Implies(use_tz and has_target,
                    Result() == stored + target_off - conn_off))
    # Coinciding connection and target zones leave the value unchanged (the
    # no-conversion optimisation is observationally the identity).
    Ensures(Implies(use_tz and has_target and conn_off == target_off,
                    Result() == stored))
    # No active normalisation -> the stored wall clock passes through untouched.
    Ensures(Implies(not use_tz, Result() == stored))
    Ensures(Implies(not has_target, Result() == stored))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the stored wall clock is read in the UNIVERSAL
    # zero zone (source offset hard-wired to 0), ignoring the connection time
    # zone, then unconditionally re-expressed in the target zone.
    result = stored  # type: int
    if use_tz:
        if has_target:
            result = result + target_off
    return result
    # impl-end
