"""Twin-artifact model for django__django-11433.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a bound form is turned into a model instance, the cleaned value of each
  candidate field is normally written onto the instance. There is one
  exception, which protects a model-level default from being clobbered by a
  value the form never actually received: a field is left at its model default
  (its cleaned value is NOT written) precisely when ALL of the following hold

    (1) the field carries a model-level default value,
    (2) the field's value was absent from the submitted payload (the widget
        reports the value as omitted from the incoming data), and
    (3) the cleaned value standing for that field is one of the recognised
        "empty" sentinels (an absent / blank value).

  In every other case the cleaned value IS written onto the instance. In
  particular, when a field has a default and was omitted from the payload but
  its cleaned value is NON-empty (e.g. a value derived in cleaning rather than
  submitted directly), that non-empty cleaned value overwrites the default and
  is written onto the instance. A field that fails the earlier candidacy
  filters is never written regardless of the three conditions above.

The set of fields is modelled positionally: index ``i`` ranges over the
candidate fields in iteration order. Each per-field input is a boolean carrier:

  ``selected[i]``   -- the field passed the earlier candidacy filters,
  ``has_default[i]``-- the field carries a model-level default,
  ``omitted[i]``    -- the field's value was omitted from the submitted data,
  ``value_empty[i]``-- the cleaned value for the field is an empty sentinel.

The result is the boolean carrier ``written[i]`` -- whether the field's cleaned
value is written onto the constructed instance. The membership test of a
cleaned value against the recognised empty sentinels and the widget/field
predicates are unchanged primitives whose outcomes are exactly these boolean
inputs; only the per-field decision is under specification, so it is modelled
deeply with no axiomatised callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def write_value(selected: bool, has_default: bool,
                omitted: bool, value_empty: bool) -> bool:
    """Whether a single candidate field's cleaned value is written onto the
    instance. The cleaned value is written unless the field is left at its
    model default, which happens exactly when the field has a default, its
    value was omitted from the payload, AND its cleaned value is an empty
    sentinel. A field that failed the earlier candidacy filters is never
    written."""
    return selected and not (has_default and omitted and value_empty)
# pure-end


def construct_writes(selected: List[bool], has_default: List[bool],
                     omitted: List[bool], value_empty: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(selected), 1 / 2))
    Requires(Acc(list_pred(has_default), 1 / 2))
    Requires(Acc(list_pred(omitted), 1 / 2))
    Requires(Acc(list_pred(value_empty), 1 / 2))
    Requires(len(selected) == len(has_default))
    Requires(len(selected) == len(omitted))
    Requires(len(selected) == len(value_empty))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(selected), 1 / 2))
    Ensures(Acc(list_pred(has_default), 1 / 2))
    Ensures(Acc(list_pred(omitted), 1 / 2))
    Ensures(Acc(list_pred(value_empty), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(selected))
    Ensures(len(Result()) == len(has_default))
    Ensures(len(Result()) == len(omitted))
    Ensures(len(Result()) == len(value_empty))
    # Each field's write decision is exactly the per-field rule: written unless
    # (has_default and omitted and value_empty), and never written if it failed
    # the earlier candidacy filters.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(selected) and k < len(has_default)
                and k < len(omitted) and k < len(value_empty)
                and k < len(Result()),
                Result()[k] == write_value(selected[k], has_default[k],
                                           omitted[k], value_empty[k]))
        )))
    # A field with a default whose value was omitted but whose cleaned value is
    # NON-empty has that non-empty value written, overwriting the default.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(selected) and k < len(has_default)
                and k < len(omitted) and k < len(value_empty)
                and k < len(Result())
                and selected[k] and has_default[k] and omitted[k]
                and not value_empty[k],
                Result()[k])
        )))
    # A field with a default that was omitted and whose cleaned value IS empty
    # is left at its default: its cleaned value is not written.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(has_default)
                and k < len(omitted) and k < len(value_empty)
                and k < len(Result())
                and has_default[k] and omitted[k] and value_empty[k],
                not Result()[k])
        )))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(selected):
        # invariants-start
        Invariant(Acc(list_pred(selected), 1 / 2))
        Invariant(Acc(list_pred(has_default), 1 / 2))
        Invariant(Acc(list_pred(omitted), 1 / 2))
        Invariant(Acc(list_pred(value_empty), 1 / 2))
        Invariant(len(selected) == len(has_default))
        Invariant(len(selected) == len(omitted))
        Invariant(len(selected) == len(value_empty))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(selected))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i and k < len(selected)
                    and k < len(has_default) and k < len(omitted)
                    and k < len(value_empty),
                    result[k] == write_value(selected[k], has_default[k],
                                             omitted[k], value_empty[k]))
            )))
        Invariant(MustTerminate(len(selected) - i + 1))
        # invariants-end
        if selected[i] and not (has_default[i] and omitted[i]):
            result = result + [True]
        else:
            result = result + [False]
        i = i + 1
    return result
    # impl-end
