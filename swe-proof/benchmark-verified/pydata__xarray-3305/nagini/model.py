"""Twin-artifact model for pydata__xarray-3305.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an order-statistic reduction of an array's values is computed
  along one or more dimensions, the caller may ask, via an optional three-valued flag, for the
  source object's metadata payload to be carried over to the reduced result:

    (1) The reduction of a single array produces a result whose metadata is a
        faithful copy of the source metadata when the flag resolves to "keep",
        and is empty when it resolves to "drop". When the flag is left
        unspecified (the omitted, neutral value), it resolves through the
        ambient default policy, which in the default configuration is "drop".

    (2) When the same reduction is requested through the higher-level entry
        point the caller invokes, the result carries the same metadata that
        behaviour (1) produces from the source metadata under the same flag
        value.

The metadata payload is modelled as `List[int]` of code points (Nagini bans
`str` indexing); the pure sequence theory `PSeq[int]` carries the
specification. The three-valued flag is `Optional[bool]` (None = unspecified).

One stdlib-style callee is axiomatized (`ambient_keep_default`, the ambient
default-policy resolver, consulted only when the flag is unspecified); the
metadata-selection itself is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def ambient_keep_default() -> bool:
    """Ambient default-policy resolver, consulted with the "drop" default when
    the caller leaves the keep flag unspecified. Under the default ambient
    configuration this resolves to "drop" (False). Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == False)
# axioms-end


# pure-start
@Pure
def resolve_keep(keep: Optional[bool]) -> bool:
    """Three-valued flag resolution: an explicit True/False is honoured as
    given; the unspecified value (None) falls back to the ambient default."""
    if keep is None:
        return ambient_keep_default()
    return keep


@Pure
def selected_meta(src: PSeq[int], keep: bool) -> PSeq[int]:
    """Metadata of the reduced result: a faithful copy of the source metadata
    when keeping, otherwise the empty payload."""
    if keep:
        return src
    return PSeq(0).take(0)
# pure-end


def reduce_result_metadata(self_meta: List[int],
                            keep_metadata: Optional[bool]) -> List[int]:
    """Behaviour (1): the metadata payload carried onto the reduced result of a
    single array, as a function of the source metadata and the (possibly
    unspecified) keep flag."""
    # pre-conditions-start
    Requires(Acc(list_pred(self_meta), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(self_meta), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result metadata is exactly the source-or-empty selection driven by
    # the resolved flag: keep -> a copy of the source; drop -> empty.
    Ensures(ToSeq(Result()) == selected_meta(ToSeq(self_meta),
                                              resolve_keep(keep_metadata)))
    # post-conditions-end
    # impl-start
    keep = keep_metadata
    if keep is None:
        keep = ambient_keep_default()
    result = []  # type: List[int]
    if keep:
        result = list(self_meta)
    return result
    # impl-end


def entrypoint_reduce_metadata(self_meta: List[int],
                               keep_metadata: Optional[bool]) -> List[int]:
    """Behaviour (2): the metadata payload carried onto the reduced result
    reached through the higher-level entry point the caller invokes, as a
    function of the source metadata and the (possibly unspecified) keep
    flag."""
    # pre-conditions-start
    Requires(Acc(list_pred(self_meta), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(self_meta), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result metadata is the same source-or-empty selection driven by the
    # resolved flag as in behaviour (1).
    Ensures(ToSeq(Result()) == selected_meta(ToSeq(self_meta),
                                              resolve_keep(keep_metadata)))
    # post-conditions-end
    # impl-start
    result = reduce_result_metadata(self_meta, keep_metadata)
    return result
    # impl-end
