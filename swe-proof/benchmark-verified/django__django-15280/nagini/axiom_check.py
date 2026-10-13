#!/usr/bin/env python3
"""G-AX executable fidelity check for django__django-15280.

This bundle consumes NO @ContractOnly axiom: the slot-occupancy test and the
slot write performed inside the modelled loop are ordinary concrete operations,
modelled directly (kind I in refinement.md). What this script validates is the
fidelity of that direct modelling — i.e. that the parallel-list abstraction
(`slot_full[i]` is the occupancy flag, `slot_value[i]` is the stored parent) and
the deep model `linked_parent` faithfully reproduce the REAL per-child cache
machinery the patched loop drives:

  * occupancy test  : `field.is_cached(child)`        (model: slot_full[i] == 1)
  * slot write      : `setattr(child, field.name, p)` (model: slot_value[i] = p)
                      which routes through the forward relation descriptor's
                      __set__ -> `field.set_cached_value(child, p)`.

The real machinery is `django.db.models.fields.mixins.FieldCacheMixin`:

    def is_cached(self, instance):
        return self.get_cache_name() in instance._state.fields_cache
    def set_cached_value(self, instance, value):
        instance._state.fields_cache[self.get_cache_name()] = value
    def get_cached_value(self, instance, default=NOT_PROVIDED):
        try:    return instance._state.fields_cache[self.get_cache_name()]
        except KeyError: ...

so a child's "slot" is one entry of `instance._state.fields_cache` keyed by the
field's cache name: `is_cached` is exactly membership of that key, and writing
the slot is exactly setting that key. The model's `slot_full` (membership flag)
and `slot_value` (stored parent id) are therefore a faithful 1:1 abstraction.

We exercise the REAL `FieldCacheMixin` in-container (importing it iff Django is
importable; otherwise we fall back to the documented two-line reconstruction,
clearly labelled) over boundary + randomized child collections, and assert the
real machinery driven by the FIXED guarded loop produces, for every child,
exactly `linked_parent(was_full, old_value, supplied)`:

    populated slot (was_full == 1) -> keeps old_value
    empty slot     (was_full == 0) -> receives the supplied parent

and that the buggy unconditional write would instead clobber a populated slot
(the discriminating behaviour). Exit 0 iff every observation matches the model.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def linked_parent(was_full, old_value, supplied):
    """Reference of model.py's deep model `linked_parent`."""
    if was_full == 1:
        return old_value
    return supplied


# --- the real cache machinery (in-container) or a labelled reconstruction ----

class _FakeState:
    def __init__(self):
        self.fields_cache = {}


def _load_cache_machinery():
    """Return (is_cached, set_cached_value, make_child, CACHE_NAME, mode).

    `is_cached(child)`/`set_cached_value(child, v)` operate the REAL slot; a
    child is any object carrying a `_state.fields_cache` dict, exactly like a
    Django model instance. We bind the methods off the REAL
    FieldCacheMixin when Django is importable (in-container G-AX), else off a
    two-line reconstruction equal to the documented source above.
    """
    cache_name = "parent"
    try:
        from django.db.models.fields.mixins import FieldCacheMixin, NOT_PROVIDED

        class _Field(FieldCacheMixin):
            def get_cache_name(self):
                return cache_name

        field = _Field()

        def is_cached(child):
            return field.is_cached(child)

        def set_cached_value(child, value):
            field.set_cached_value(child, value)

        mode = "real django.db.models.fields.mixins.FieldCacheMixin"
    except Exception:
        # Documented two-line reconstruction (identical to the source quoted in
        # the module docstring); used only when Django is not importable.
        def is_cached(child):
            return cache_name in child._state.fields_cache

        def set_cached_value(child, value):
            child._state.fields_cache[cache_name] = value

        mode = "stdlib reconstruction of FieldCacheMixin (Django not importable)"

    def make_child():
        class _Child:
            pass
        c = _Child()
        c._state = _FakeState()
        return c

    return is_cached, set_cached_value, make_child, cache_name, mode


def run_fixed_loop(children, supplied, is_cached, set_cached_value):
    """The FIXED behaviour: only write the slot of a child whose slot is empty
    (mirrors `if not self.field.is_cached(rel_obj): setattr(...)`)."""
    for child, parent in zip(children, supplied):
        if not is_cached(child):
            set_cached_value(child, parent)


def run_buggy_loop(children, supplied, is_cached, set_cached_value):
    """The PRE-PATCH behaviour: write every slot unconditionally."""
    for child, parent in zip(children, supplied):
        set_cached_value(child, parent)


def slot(child, is_cached, set_cached_value, cache_name):
    if not is_cached(child):
        return None
    return child._state.fields_cache[cache_name]


SENTINEL_EMPTY = -1


def main():
    is_cached, set_cached_value, make_child, cache_name, mode = _load_cache_machinery()

    def build(occupancy, preset, supplied):
        """occupancy[i] in {0,1}: whether child i's slot is pre-populated;
        preset[i]: the pre-populated parent id (used iff occupancy[i]==1)."""
        children = []
        was_full = []
        old_value = []
        for occ, pre in zip(occupancy, preset):
            c = make_child()
            if occ == 1:
                set_cached_value(c, pre)
            children.append(c)
            was_full.append(1 if occ == 1 else 0)
            old_value.append(pre if occ == 1 else SENTINEL_EMPTY)
        return children, was_full, old_value

    checked = 0

    def check_case(occupancy, preset, supplied):
        nonlocal checked
        # FIXED loop must reproduce linked_parent for every child.
        children, was_full, old_value = build(occupancy, preset, supplied)
        run_fixed_loop(children, supplied, is_cached, set_cached_value)
        for i in range(len(children)):
            got = slot(children[i], is_cached, set_cached_value, cache_name)
            expect = linked_parent(was_full[i], old_value[i], supplied[i])
            assert got == expect, (
                "fidelity break (FIXED) at child %d: occupancy=%r preset=%r "
                "supplied=%r -> real slot %r, model linked_parent %r"
                % (i, occupancy, preset, supplied, got, expect))
        # BUGGY loop must clobber every populated slot whose supplied differs
        # (the discriminating behaviour the spec forbids).
        children2, was_full2, old_value2 = build(occupancy, preset, supplied)
        run_buggy_loop(children2, supplied, is_cached, set_cached_value)
        for i in range(len(children2)):
            got = slot(children2[i], is_cached, set_cached_value, cache_name)
            assert got == supplied[i], (
                "buggy loop did not unconditionally overwrite child %d" % i)
            if was_full2[i] == 1 and old_value2[i] != supplied[i]:
                assert got != linked_parent(was_full2[i], old_value2[i], supplied[i]), (
                    "buggy loop unexpectedly matched linked_parent at child %d" % i)
        checked += 1

    # --- boundary cases ------------------------------------------------------
    # empty collection
    check_case([], [], [])
    # single empty slot
    check_case([0], [SENTINEL_EMPTY], [7])
    # single populated slot, supplied differs (the bug's witness)
    check_case([1], [99], [7])
    # single populated slot, supplied equals existing
    check_case([1], [7], [7])
    # mixed: empty, populated-different, populated-same, empty
    check_case([0, 1, 1, 0], [SENTINEL_EMPTY, 5, 8, SENTINEL_EMPTY], [3, 4, 8, 6])
    # all populated, all differ
    check_case([1, 1, 1], [10, 11, 12], [20, 21, 22])
    # all empty
    check_case([0, 0, 0], [SENTINEL_EMPTY] * 3, [1, 2, 3])

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(15280)
    for _ in range(20000):
        n = rng.randint(0, 12)
        occupancy = [rng.randint(0, 1) for _ in range(n)]
        preset = [rng.randint(0, 50) for _ in range(n)]
        supplied = [rng.randint(0, 50) for _ in range(n)]
        check_case(occupancy, preset, supplied)

    print("G-AX OK: linked_parent deep model == real %s over %d boundary + "
          "fuzz child collections; FIXED guarded loop preserves populated slots "
          "and fills empty ones; buggy loop clobbers populated slots."
          % (mode, checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
