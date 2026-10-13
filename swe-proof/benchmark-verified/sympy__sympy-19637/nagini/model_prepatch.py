"""Twin-artifact model for sympy__sympy-19637.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual pre-processor decides whether a later post-processing pass is
  needed. The signal it returns ("processing-was-applied") is derived from a
  substitution key, but that key is created ONLY inside an inner branch — the
  branch that actually performs a space-to-key substitution. Two outer cases:

    * ENTERED-AND-SUBSTITUTED — the input qualifies for the transform (the
      outer guard holds) AND, after the structural rewrite, a substitution was
      actually performed (a key was created and spliced in). Here the signal is
      whether that freshly-created key occurs in the rewritten text.

    * NO-SUBSTITUTION — either the input never qualified for the transform, or
      it qualified but, after the rewrite, NO substitution was performed (no
      key was ever created). Here NO key exists, so the signal MUST be false;
      there is no key to test for membership.

  The behaviour pinned here: the signal equals "the created key occurs in the
  rewritten text" ONLY in the entered-and-substituted case, and is false in the
  no-substitution case. The key's membership may be inspected ONLY when a key
  was actually created. Inspecting a key's membership when no key exists (the
  no-substitution case) is never permitted — there is nothing to inspect.

The presence/absence of the created key is modelled as `Optional[bool]`
(absent = None = no key was created; present = the key's membership in the
rewritten text). The outer-guard and substitution-performed conditions are
booleans. The key-membership inspection is a `@Pure` accessor defined only when
a key is present (its precondition forbids inspecting an absent key).

The signal computation is a bounded, straight-line decision: it MUST terminate
(a total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges — e.g. hangs instead of returning the false
signal on the no-substitution path — would satisfy the value postconditions
only vacuously and would hang the caller forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the signal selection is concrete boolean / Optional control flow,
# modelled directly — no unchanged opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def key_member(key: Optional[bool]) -> bool:
    """Whether the created substitution key occurs in the rewritten text. This
    inspection is defined ONLY when a key was actually created (key is not
    None); inspecting an absent key is excluded by the precondition — there is
    nothing to inspect when no key exists."""
    Requires(key is not None)
    return key  # type: ignore[return-value]


@Pure
def expected_signal(entered: bool, key: Optional[bool]) -> bool:
    """The signal the desired behaviour demands: the created key's membership in
    the rewritten text when a key was created (the entered-and-substituted
    case), and false otherwise (the no-substitution case — no key exists)."""
    if entered and key is not None:
        return key_member(key)
    return False
# pure-end


def compute_processing_signal(entered: bool, key: Optional[bool]) -> bool:
    # pre-conditions-start
    # `entered` is the outer guard (the input qualified for the transform).
    # `key` carries the created substitution key's membership in the rewritten
    # text when a key was created (the substitution-performed inner branch),
    # and is absent (None) when no key was created.  A key can exist only inside
    # the transform, so an absent outer guard implies an absent key.
    Requires(Implies(not entered, key is None))
    # The signal computation is a bounded, straight-line decision: it MUST
    # terminate and hand the signal back — total correctness. A diverging impl
    # (e.g. hanging instead of returning the false signal on the
    # no-substitution path) would satisfy the value postconditions only
    # vacuously and hang the caller forever. This obligation rejects any such
    # implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The signal is exactly the membership of a created key in the entered-and-
    # substituted case, and false in the no-substitution case.
    Ensures(Result() == expected_signal(entered, key))
    # No key created (the no-substitution case) forces the signal false: there
    # is no key whose membership could make it true.
    Ensures(Implies(key is None, not Result()))
    # post-conditions-end
    # impl-start
    # Default: no processing was applied.
    hit = False
    if entered:
        # PRE-PATCH BUG: a key is created only when a substitution is performed
        # (the inner key-is-not-None branch), but the signal is read from the
        # key's membership UNCONDITIONALLY here — outside that inner branch. On
        # the entered-but-no-substitution path no key was ever created, so this
        # inspects a key that does not exist.
        if key is not None:
            key = key
        hit = key_member(key)
    return hit
    # impl-end
