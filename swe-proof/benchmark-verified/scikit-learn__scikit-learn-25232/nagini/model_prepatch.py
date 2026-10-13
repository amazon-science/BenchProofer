"""Twin-artifact model for scikit-learn__scikit-learn-25232.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the first-round initialization of an iterative imputer uses the
  constant strategy, the per-feature constant it installs for every feature
  must be the user-requested replacement value, carried through to the
  underlying single-pass imputer. Concretely, the user supplies an optional
  replacement value:

    * if a value is supplied, every feature's installed constant equals that
      value (for numerical data this is the user's number, e.g. 100, not the
      neutral numeric default);
    * if no value is supplied, the neutral numeric default (0) is used for
      every feature.

  Either way the installed per-feature constant array has one entry per
  feature and is uniform.

The underlying single-pass imputer's constant-strategy behaviour (turning a
replacement value into the uniform per-feature constant array) is the
unchanged callee; it is axiomatized. The replacement value is modelled as an
``Optional[int]`` (the integral exact value the test observes; precision is
not the behaviour, exact equality is) and the per-feature constant array as a
``List[int]`` of length equal to the feature count.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
def resolved_value(requested: Optional[int]) -> int:
    """The replacement value the underlying single-pass imputer actually uses
    for numerical data: the supplied value if any, else the neutral numeric
    default (0). This default-resolution lives inside the unchanged callee."""
    if requested is None:
        return 0
    return requested


@ContractOnly
def constant_statistics(requested: Optional[int], n_features: int) -> List[int]:
    """The unchanged single-pass imputer's constant-strategy result: it fills
    one constant per feature with the (default-resolved) replacement value.
    Weakest sufficient contract on that callee. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(n_features >= 0)
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n_features)
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < n_features,
                                            Result()[j] == resolved_value(requested)))))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def initial_constant_fill(requested: Optional[int], n_features: int) -> List[int]:
    # pre-conditions-start
    Requires(n_features >= 0)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # One installed constant per feature.
    Ensures(len(Result()) == n_features)
    # Every feature's installed constant is the user-requested replacement
    # value (default-resolved when none is supplied) — NOT always the neutral
    # numeric default.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < n_features,
                                           Result()[j] == resolved_value(requested)))))
    # post-conditions-end
    # impl-start
    # Pre-patch: the user's requested replacement value is NOT carried through
    # to the underlying single-pass imputer; it sees no value and therefore
    # falls back to the neutral numeric default for every feature.
    statistics = constant_statistics(None, n_features)
    return statistics
    # impl-end
