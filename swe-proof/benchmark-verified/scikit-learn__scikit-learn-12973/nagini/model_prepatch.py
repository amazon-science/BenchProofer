"""Twin-artifact model for scikit-learn__scikit-learn-12973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An estimator records, at construction time, a default boolean preference for
  whether the training-data array passed to the model-fitting routine is
  preserved (left byte-for-byte intact) or may be overwritten in place during
  preprocessing. The fitting routine ALSO accepts a per-call preference.

  The desired behaviour is that the per-call preference, when the caller
  supplies one, takes precedence over the construction-time default; when the
  caller supplies no per-call preference (the "unset" value), the
  construction-time default is used. Whichever preference is thus selected
  governs preprocessing in full:

    (1) the preference that actually governs preprocessing equals the per-call
        preference if one was supplied, otherwise the construction-time default
        (the per-call choice is never silently discarded); and

    (2) the input array's fate follows that selected preference, subject to
        the routine's numeric working format: the routine computes in a
        designated numeric representation, and when the supplied array is not
        already in that representation, input validation materializes a
        converted working copy up front, so the caller's array is left intact
        regardless of the selected preference. When the array IS already in
        the native working format, it is left intact after fitting if and
        only if the selected preference is "preserve" (True): a "preserve"
        selection copies the array before preprocessing, a "may overwrite"
        selection lets preprocessing mutate it in place.

The per-call preference is modelled as ``Optional[bool]`` (``None`` = "unset").
The estimator's construction-time default and the input array's touched
observables are modelled as minimal objects carrying only the touched fields:
``intact`` (the boolean the fitting routine's caller observes afterwards) and
``native_format`` (whether the array is already in the routine's native
numeric working representation — the property that decides whether validation
must materialize a converted copy).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Estimator:
    def __init__(self, default_copy: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
        self.default_copy = default_copy


class InputArray:
    def __init__(self, intact: bool, native_format: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
        Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
        self.intact = intact
        self.native_format = native_format


# axioms-start
# (no callee is axiomatized: the changed behaviour is a boolean dataflow — the
# selection of the governing preference and its consequence for the input array
# — and is modelled deeply below, not behind a @ContractOnly axiom.)
# axioms-end


# pure-start
@Pure
def selected_preference(default_copy: bool, per_call: Optional[bool]) -> bool:
    """The preference that governs preprocessing: the per-call preference if the
    caller supplied one (not ``None``), otherwise the construction-time default."""
    if per_call is None:
        return default_copy
    return per_call
# pure-end


def fit(config: Estimator, data: InputArray, copy_X: Optional[bool]) -> bool:
    # pre-conditions-start
    # config is read-only (the construction-time default is consulted, not
    # changed) -> fractional permission; the array's format flag is likewise
    # only consulted -> fractional permission; data.intact IS mutated -> full
    # permission.
    Requires(Acc(config.default_copy, 1 / 2))
    Requires(Acc(data.intact))
    Requires(Acc(data.native_format, 1 / 2))
    # Level is parametric because the specification must admit a call site that
    # invokes fit on a FRESH native-format input (the admissibility probe): a
    # constant level can never dominate itself, so a self-call cannot be proven
    # terminating at any single constant n. A non-native input sits at level 3
    # and may make one nested call on a native-format input at level 2; a
    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
    # constructors' level), so the descent is well-founded and depth is <= 2.
    Requires(MustTerminate(2 if data.native_format else 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(config.default_copy, 1 / 2))
    Ensures(config.default_copy == Old(config.default_copy))
    Ensures(Acc(data.intact))
    Ensures(Acc(data.native_format, 1 / 2))
    Ensures(data.native_format == Old(data.native_format))
    # (1) the preference governing preprocessing is the per-call one when given,
    # else the construction-time default — the per-call choice is not discarded.
    Ensures(Result() == selected_preference(Old(config.default_copy), copy_X))
    # (2) the input array is left intact iff the selected preference is True OR
    # the array was not already in the native working format (in which case
    # validation materialized a converted copy, shielding the caller's array).
    Ensures(data.intact == (Result() or not data.native_format))
    # post-conditions-end
    # impl-start
    # Pre-patch buggy dataflow: preprocessing consults the construction-time
    # default directly (ignoring any per-call preference), and the per-call
    # value is routed elsewhere. Both the array's fate and the surfaced
    # preference therefore reflect the construction-time default, silently
    # discarding the caller's per-call choice.
    effective = config.default_copy
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective
    # impl-end
