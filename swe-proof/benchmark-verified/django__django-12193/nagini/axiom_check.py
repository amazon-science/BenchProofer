#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12193.

Executes the REAL Python language primitives the gold patch composes and
asserts that every observation matches the model's axioms (model.py axioms
region):

  (A-consumed) `mapping_with(base, key, flag)` == the dict-display merge
      `{**base, key: flag}` (PEP 448 unpacking, CPython BUILD_MAP/DICT_MERGE).
      Checked obligations (the axiom's Ensures):
        - the result is a FRESH object: `result is not base`  (the heart of the
          fix: the caller's mapping is never the returned object);
        - `base` is NOT mutated by the construction;
        - `key` is present with `flag`;
        - every other key of `base` is carried through with its value;
        - no key outside `base ∪ {key}` appears.

  (A-consumed) `mapping_copy(base)` == the dict copy `{**base}` / `dict(base)`.
      Checked obligations: fresh object distinct from `base`; `base` unmutated;
      same keys both directions; same value at each key.

Imports nothing repo-specific: dict-display merge and copy are pure Python
language primitives (the very constructs the gold patch calls). Exit 0 iff every
obligation holds.
"""
import random
import sys

# The selection attribute key the patch sets. In the model it is the integer
# token attr_selected(); here we exercise both the real string key 'checked'
# (the literal the patch uses) and arbitrary integer keys (the model carrier).
SELECTED_KEY_STR = "checked"


# --- the REAL language primitives under check --------------------------------

def real_mapping_with(base, key, flag):
    """The exact construction the gold patch uses: a fresh merged mapping."""
    return {**base, key: flag}


def real_mapping_copy(base):
    """The exact pass-through copy: a fresh mapping with the same contents."""
    return {**base}


# --- the checks --------------------------------------------------------------

def check_mapping_with(base, key, flag):
    snapshot = dict(base)                      # record base before the op
    result = real_mapping_with(base, key, flag)
    # base is NOT mutated by the construction
    assert base == snapshot, (
        "mapping_with unsound: base mutated %r -> %r" % (snapshot, base))
    # the result is a fresh object, never base (the freshness clause = the fix)
    assert result is not base, "mapping_with unsound: result IS base (not fresh)"
    # the named key is present with the supplied flag
    assert key in result and result[key] == flag, (
        "mapping_with unsound: key %r not set to %r in %r" % (key, flag, result))
    # every other key of base is carried through with its value
    for k, v in snapshot.items():
        if k != key:
            assert k in result and result[k] == v, (
                "mapping_with unsound: base key %r=%r lost in %r" % (k, v, result))
    # no key outside base ∪ {key}
    for k in result:
        assert k == key or k in snapshot, (
            "mapping_with unsound: spurious key %r in %r" % (k, result))


def check_mapping_copy(base):
    snapshot = dict(base)
    result = real_mapping_copy(base)
    assert base == snapshot, (
        "mapping_copy unsound: base mutated %r -> %r" % (snapshot, base))
    assert result is not base, "mapping_copy unsound: result IS base (not fresh)"
    # same keys + values, both directions
    for k, v in snapshot.items():
        assert k in result and result[k] == v, (
            "mapping_copy unsound: base key %r=%r lost in %r" % (k, v, result))
    for k in result:
        assert k in snapshot and result[k] == snapshot[k], (
            "mapping_copy unsound: spurious/changed key %r in %r" % (k, result))


def main():
    # --- boundary cases (the F2P / P2P scenarios) -------------------------
    boundary_bases = [
        {},                                   # attrs is None / empty (coalesced)
        {"checked": False},                   # F2P test_get_context_does_not_mutate_attrs
        {"checked": True},
        {"id": "x", "class": "y"},            # unrelated attributes preserved
        {"id": "x", "checked": False},        # unrelated + the selection key
        {"a": 1, "b": 2, "c": 3},
    ]
    for base in boundary_bases:
        check_mapping_with(base, "checked", True)
        check_mapping_copy(base)

    # the SplitArray scenario: a sequence of widgets sharing one attrs mapping,
    # values [True, False] -> subwidget attrs must be [{'checked': True}, {}].
    # This is precisely what the bug broke (the second widget inherited checked).
    shared = {}
    sub0 = real_mapping_with(shared, "checked", True)   # value True  -> selected
    sub1 = real_mapping_copy(shared)                    # value False -> not sel.
    assert shared == {}, "SplitArray scenario: shared attrs mutated: %r" % shared
    assert sub0 == {"checked": True}, "SplitArray sub0 wrong: %r" % sub0
    assert sub1 == {}, "SplitArray sub1 wrong: %r" % sub1

    # --- integer-keyed carrier (the model's Dict[int, bool]) --------------
    for base in [{}, {0: False}, {0: True}, {1: True, 2: False},
                 {0: False, 5: True, 9: False}]:
        check_mapping_with(base, 0, True)        # 0 == attr_selected()
        check_mapping_copy(base)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(12193)
    for _ in range(20000):
        n = rng.randint(0, 8)
        base = {rng.randint(-3, 12): bool(rng.getrandbits(1)) for _ in range(n)}
        key = rng.randint(-3, 12)
        flag = bool(rng.getrandbits(1))
        check_mapping_with(base, key, flag)
        check_mapping_copy(base)

    print("G-AX OK: mapping_with / mapping_copy axioms sound against the real "
          "dict-display merge/copy on %d boundary bases + the SplitArray "
          "scenario + 20000 fuzz cases (base never mutated; result always "
          "fresh)" % len(boundary_bases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
