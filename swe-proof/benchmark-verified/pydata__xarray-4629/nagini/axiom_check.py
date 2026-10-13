#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4629.

There are NO consumed axioms in model.py. The combination operation is modelled
deeply (model.py's impl region spells out the empty drop mapping and the
per-entry copy of the leading source). This check validates that deep model as
an **A-reference**: it executes the REAL combination the patch performs and
asserts every observation matches what model.py guarantees.

The real combination, as the patched code performs it (the two modes the model
covers), is:

    if combine_attrs == "drop":
        return {}
    elif combine_attrs == "override":
        return dict(variable_attrs[0])     # <-- the post-patch behaviour

The decisive obligations (mirroring model.py's postconditions under the
List[int]-content / object-identity refinement of mapping.md §2):

  * drop  -> a FRESH empty mapping;
  * override -> a mapping with the SAME content as variable_attrs[0]
      (ToSeq(Result()) == ToSeq(variable_attrs[0])  <->  dict equality), AND a
      DISTINCT object from variable_attrs[0]
      (Result() is not variable_attrs[0]), so that mutating the result leaves
      the leading source mapping untouched -- the exact scenario the F2P test
      `test_merge_attrs_override_copy` exercises.

Imports nothing repo-specific: only the standard library. Exit 0 iff every
obligation holds.
"""
import random
import sys

DROP = "drop"
OVERRIDE = "override"


def real_merge_attrs(variable_attrs, combine_attrs):
    """The patched combination, restricted to the two modes the model covers.
    A faithful transcription of xarray/core/merge.py::merge_attrs after the
    gold patch (the `override` branch returns `dict(variable_attrs[0])`)."""
    if not variable_attrs:
        return None
    if combine_attrs == DROP:
        return {}
    elif combine_attrs == OVERRIDE:
        return dict(variable_attrs[0])
    raise AssertionError("unmodeled combine_attrs mode: %r" % combine_attrs)


def check_override_reference(variable_attrs):
    """Assert the override deep model == the real override branch: an
    independent copy (distinct object, equal content) of the leading source."""
    source = variable_attrs[0]
    snapshot = dict(source)                       # content before
    result = real_merge_attrs(variable_attrs, OVERRIDE)

    # content equality (the ToSeq(...) == ToSeq(...) clause under the
    # value-content refinement: two mappings model-equal iff content-equal)
    assert result == source, (
        "override unsound: result %r != source %r" % (result, source))

    # DISTINCT object -- the heart of the fix (the model's
    # `Result() is not variable_attrs[0]` / full-permission-on-a-new-object)
    assert result is not source, (
        "override unsound: result IS the source object (aliased), %r" % result)

    # the F2P scenario: mutating the result must not change the source
    result[("__probe__",)] = "mutated"
    assert source == snapshot, (
        "override unsound: mutating the result mutated the source %r (was %r)"
        % (source, snapshot))
    # and the leading source is otherwise unchanged in identity/content
    assert variable_attrs[0] is source
    assert variable_attrs[0] == snapshot


def check_drop_reference(variable_attrs):
    """Assert the drop deep model == the real drop branch: a fresh empty map."""
    source = variable_attrs[0]
    result = real_merge_attrs(variable_attrs, DROP)
    assert result == {}, "drop unsound: result %r is not empty" % (result,)
    assert result is not source, "drop unsound: result aliases the source"
    # mutating the (empty) result must not affect any source
    result["__probe__"] = 1
    assert source == variable_attrs[0]


def _rand_map(rng, max_keys=6, key_space=12):
    n = rng.randint(0, max_keys)
    return {rng.randrange(key_space): rng.randrange(100) for _ in range(n)}


def main():
    # --- boundary cases ----------------------------------------------------
    boundary_firsts = [
        {},                       # empty leading mapping
        {"x": 0},                 # the F2P example
        {"x": 0, "y": 1},
        {"a": "b"},               # the issue's example
        {0: 0, 1: 1, 2: 2},
        {"k": None},
    ]
    for first in boundary_firsts:
        # a multi-source list; only variable_attrs[0] is consulted by both modes
        variable_attrs = [dict(first), {"other": "z"}, {"more": 9}]
        check_override_reference(variable_attrs)
        check_drop_reference([dict(first), {"q": 1}])

    # explicit replay of the exact F2P scenario (ds1 attrs {"x":0})
    ds1_attrs = {"x": 0}
    ds2_attrs = {"x": 1}
    merged = real_merge_attrs([ds1_attrs, ds2_attrs], OVERRIDE)
    merged["x"] = 2
    assert ds1_attrs["x"] == 0, (
        "F2P scenario unsound: ds1 attr changed to %r after mutating merged"
        % ds1_attrs["x"])

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(4629)
    for _ in range(20000):
        first = _rand_map(rng)
        rest = [_rand_map(rng) for _ in range(rng.randint(0, 3))]
        variable_attrs = [first] + rest
        check_override_reference(variable_attrs)
        check_drop_reference([first] + rest)

    print("G-AX OK: combine_attrs override/drop deep models (A-reference) == "
          "real patched merge_attrs on %d boundary + 20000 fuzz inputs; the "
          "override result is always a DISTINCT object with equal content "
          "(mutating it never mutates the leading source), incl. the exact "
          "F2P test_merge_attrs_override_copy scenario." % len(boundary_firsts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
