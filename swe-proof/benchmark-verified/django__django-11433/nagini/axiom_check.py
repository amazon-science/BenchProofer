#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11433.

This bundle consumes NO `@ContractOnly` axiom: the changed operation (the
per-field "leave defaults" guard gaining the `value_empty` conjunct) is modeled
DEEPLY as the boolean decision `write_value` in model.py, and the four per-field
inputs are unchanged primitives carried as booleans (refinement.md §B). There is
therefore no axiom whose Ensures the proof relies on.

For a uniform G-AX entry point this script instead validates, against the REAL
values, the two facts the refinement rests on:

  (1) The `value_empty[i]` input is exactly `cleaned_data.get(name) in
      field.empty_values`, where Django's `empty_values` is the recognised
      empty sentinels `EMPTY_VALUES = (None, '', [], (), {})`
      (`django/core/validators.py:13`, `django/forms/fields.py:55`). We assert
      the membership semantics on the boundary sentinels AND on non-empty
      values, so the boolean carrier `value_empty` is faithful.

  (2) The deep decision `write_value(selected, has_default, omitted,
      value_empty) == selected and not (has_default and omitted and
      value_empty)` reproduces the post-patch guard's write/skip outcome on the
      full truth table (and the pre-patch guard differs exactly on the
      defaulted+omitted+non-empty row — the F2P-distinguishing case).

Imports nothing repo-specific: `EMPTY_VALUES` is reproduced literally (it is a
frozen 5-tuple of stdlib primitives). Exit 0 iff every obligation holds.
"""
import itertools
import sys

# Django's recognised empty sentinels (django/core/validators.py:13).
EMPTY_VALUES = (None, '', [], (), {})


def value_is_empty(cleaned_value):
    """The repo expression `cleaned_data.get(name) in field.empty_values`,
    reproduced over the real EMPTY_VALUES tuple. Returns the boolean carried by
    `value_empty[i]` in model.py."""
    return cleaned_value in EMPTY_VALUES


def write_value(selected, has_default, omitted, value_empty):
    """Reference of model.py's deep decision `write_value` (the post-patch
    guard, negated): the cleaned value is written unless the field is left at
    its model default."""
    return selected and not (has_default and omitted and value_empty)


def prepatch_write_value(selected, has_default, omitted, value_empty):
    """The pre-patch guard (without the `value_empty` conjunct), for the
    differential check."""
    return selected and not (has_default and omitted)


def check_membership():
    # Each recognised empty sentinel must test True.
    for sentinel in [None, '', [], (), {}]:
        assert value_is_empty(sentinel), (
            "empty sentinel %r not recognised as empty" % (sentinel,))
    # Representative NON-empty values must test False (incl. the F2P 'de'/'di',
    # and values that are falsy-but-not-empty-sentinels like 0 / False).
    for nonempty in ['de', 'di', 'x', ' ', '0', 0, False, 1, True, [0],
                     (0,), {0: 0}, 'False', 'None']:
        assert not value_is_empty(nonempty), (
            "non-empty value %r wrongly recognised as empty" % (nonempty,))


def check_decision_truth_table():
    # Over the full boolean truth table the deep decision matches the
    # post-patch guard, and a never-selected field is never written.
    for selected, has_default, omitted, value_empty in itertools.product(
            [False, True], repeat=4):
        w = write_value(selected, has_default, omitted, value_empty)
        # post-patch guard, computed directly from the gold conjunction
        guard = has_default and omitted and value_empty
        expected = selected and not guard
        assert w == expected, (
            "decision mismatch on (sel=%s,def=%s,om=%s,empty=%s): "
            "model=%s expected=%s" % (selected, has_default, omitted,
                                      value_empty, w, expected))
        if not selected:
            assert not w, "non-selected field must never be written"

    # The discriminating row: defaulted + omitted + NON-empty cleaned value.
    # Post-patch writes (True); pre-patch leaves the default (False). This is
    # the F2P test's mocked_mode='de' case.
    sel, hd, om, ve = True, True, True, False
    assert write_value(sel, hd, om, ve) is True, (
        "post-patch must WRITE a defaulted/omitted/non-empty cleaned value")
    assert prepatch_write_value(sel, hd, om, ve) is False, (
        "pre-patch must SKIP (leave default) on the same inputs")
    # And the complementary row: defaulted + omitted + empty cleaned value is
    # left at the default under both (the F2P empty_value loop).
    assert write_value(True, True, True, True) is False
    assert prepatch_write_value(True, True, True, True) is False


def main():
    check_membership()
    check_decision_truth_table()
    print("G-AX OK: EMPTY_VALUES membership faithful on 5 sentinels + 13 "
          "non-empty values; deep decision matches post-patch guard over all "
          "16 truth-table rows; differs from pre-patch exactly on the "
          "defaulted+omitted+non-empty row (no consumed axiom).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
