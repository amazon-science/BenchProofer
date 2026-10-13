"""Twin-artifact model for scikit-learn__scikit-learn-26323.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite transformer propagates an output-container configuration to its
  child transformers. The configuration must reach EVERY child that is an
  actual estimator -- including the child that handles the columns left over
  after the explicitly-listed children have claimed theirs. Children that are
  not estimators but mere routing sentinels (the "pass the columns through
  unchanged" and "discard the columns" markers) carry no output container and
  are left untouched.

  Concretely, after the configuration call:
    * every explicitly-listed child that is an estimator has its output code
      set to the requested code;
    * the leftover-columns child, when it too is an estimator, has its output
      code set to the requested code as well;
    * every sentinel child keeps whatever it had (it is never configured).

A child is modelled as a small object exposing two observable fields: a `kind`
flag distinguishing a configurable estimator (1) from a routing sentinel (0),
and `cfg`, the integer code of the output container currently configured on it
(a distinguished value 0 meaning "unconfigured / default"). The requested
output code is an integer.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none) The configuration propagation is modelled deeply; the per-child
# configuration primitive is a plain field write, so there is no unchanged
# opaque callee consumed as an axiom (see refinement.md A-reference rows).
# axioms-end


# pure-start
class Child:
    def __init__(self, kind: int, cfg: int) -> None:
        Requires(kind == 0 or kind == 1)
        Ensures(Acc(self.kind) and Acc(self.cfg))
        Ensures(self.kind == kind and self.cfg == cfg)
        self.kind = kind  # type: int  # 1 == configurable estimator, 0 == sentinel
        self.cfg = cfg    # type: int  # configured output code; 0 == default/unset


@Pure
def is_configurable(c: Child) -> bool:
    Requires(Acc(c.kind, 1 / 4))
    return c.kind == 1
# pure-end


def configure_output(children: List[Child], leftover: Child, requested: int) -> None:
    # pre-conditions-start
    # `requested` is a genuine output-container code, distinct from the
    # distinguished UNSET code 0, so a child that was configured is observably
    # different from one left at its default.
    Requires(requested != 0)
    Requires(Acc(list_pred(children)))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                             Acc(children[k].kind) and Acc(children[k].cfg))
                                     , [[children[k]]])))
    # entering this configuration step, no child carries a container yet
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            children[k].cfg == 0), [[children[k]]])))
    Requires(Acc(leftover.kind) and Acc(leftover.cfg))
    Requires(leftover.cfg == 0)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            leftover is not children[k]), [[children[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(children)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                            Acc(children[k].kind) and Acc(children[k].cfg))
                                    , [[children[k]]])))
    Ensures(Acc(leftover.kind) and Acc(leftover.cfg))
    Ensures(len(children) == Old(len(children)))
    # the kind classification of every child is preserved
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                           children[k].kind == Old(children[k].kind))
                                   , [[children[k]]])))
    Ensures(leftover.kind == Old(leftover.kind))
    # every explicitly-listed estimator child carries the requested container;
    # every sentinel child remains unconfigured (it is never set up)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children) and children[k].kind == 1,
                                           children[k].cfg == requested), [[children[k]]])))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(children) and children[k].kind == 0,
                                           children[k].cfg == 0), [[children[k]]])))
    # the leftover-columns child: configured iff it is an estimator, else left
    # unconfigured -- this is the clause the leftover-columns handling must meet
    Ensures(Implies(leftover.kind == 1, leftover.cfg == requested))
    Ensures(Implies(leftover.kind == 0, leftover.cfg == 0))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(children):
        # invariants-start
        Invariant(Acc(list_pred(children)))
        Invariant(len(children) == Old(len(children)))
        Invariant(0 <= i and i <= len(children))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                  Acc(children[k].kind) and Acc(children[k].cfg))
                                          , [[children[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(children),
                                                 children[k].kind == Old(children[k].kind))
                                         , [[children[k]]])))
        # children already visited: estimators configured, sentinels still unset
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 1,
                                                 children[k].cfg == requested), [[children[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and children[k].kind == 0,
                                                 children[k].cfg == 0), [[children[k]]])))
        # children not yet visited: still at their unconfigured default
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(children),
                                                 children[k].cfg == 0), [[children[k]]])))
        Invariant(MustTerminate(len(children) - i + 1))
        # invariants-end
        c = children[i]
        if is_configurable(c):
            c.cfg = requested
        i = i + 1
    if is_configurable(leftover):
        leftover.cfg = requested
    # impl-end
