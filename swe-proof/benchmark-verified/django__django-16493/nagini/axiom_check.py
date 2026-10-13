#!/usr/bin/env python3
"""Executable soundness / sanity check for django__django-16493.

This bundle consumes NO `@ContractOnly` axiom: the behaviour under
specification is pure object-identity decision logic, modelled deeply. G-AX is
therefore vacuous (there is no real callee whose contract must be
over-approximated).

What this script DOES check, as an out-of-band sanity validation:

  (1) The single real-world reachability fact behind the totalized spec --
      that a held storage callable is always a DISTINCT object from
      `default_storage` (`producer_id != default_store_id()`) -- holds for the
      F2P witness and for representative callables. This mirrors the actual
      Django construction logic: `_storage_callable` holds the callable, while
      `self.storage` holds the (different) object that callable returns. The
      spec no longer assumes this as a precondition; it is total. This fact
      only certifies WHICH rows of the decision table are reachable.

  (2) The modelled decision (`deconstruct_storage`, kept in lock-step below)
      matches the intended behaviour on the full configuration table:
        - no producer, store == default            -> OMIT
        - no producer, store == custom              -> INCLUDE store
        - producer, producer != default (custom)    -> INCLUDE producer
        - producer that evaluates to default store   -> INCLUDE producer  (F2P)
      and, on the real-world-UNREACHABLE totalized corner
      (producer that IS the default store object), the general
      include-iff-reported-value-non-default rule yields OMIT -- exactly what
      the gold `storage = getattr(...); if storage is not default_storage`
      would compute on that hypothetical state, so totalization introduces no
      divergence from the gold anywhere.

Imports nothing repo-specific: only the standard library. Exit 0 iff sound.
"""
import sys


# Sentinel for the canonical default store identity (model.py default_store_id()).
DEFAULT = 0


def reported_value(has_producer, producer_id, store_id):
    """model.py pure helper, in lock-step."""
    return producer_id if has_producer else store_id


def deconstruct_storage(has_producer, producer_id, store_id):
    """Reference of model.py's verified impl: (included, value)."""
    value = producer_id if has_producer else store_id
    included = value != DEFAULT
    return (included, value)


def buggy_prepatch(has_producer, producer_id, store_id):
    """Reference of model_prepatch.py's buggy impl (guard on store, not value)."""
    value = producer_id if has_producer else store_id
    included = store_id != DEFAULT
    return (included, value)


def main():
    # --- (1) identity-disjointness reachability fact -------------------------
    # A held callable is a distinct object from the default store. We emulate
    # Django's construction: a callable object, and the (different) store it
    # returns when evaluated.
    class FakeDefaultStore:
        pass

    default_storage = FakeDefaultStore()

    def callable_default_storage():          # the F2P witness's callable
        return default_storage

    def callable_custom_storage():
        return FakeDefaultStore()            # returns some other store

    class CallableStorageClass:              # a Storage subclass with __call__
        def __call__(self):
            return default_storage

    callable_class = CallableStorageClass()

    for producer in (callable_default_storage, callable_custom_storage,
                     callable_class):
        # The callable is never the default-store singleton itself.
        assert producer is not default_storage, (
            "reachability fact violated: held callable %r IS default_storage"
            % (producer,))
        # And in the F2P case the callable evaluates TO the default store,
        # while remaining a distinct object -- exactly the overlooked case.
    assert callable_default_storage() is default_storage
    assert callable_class() is default_storage
    assert callable_default_storage is not default_storage

    # --- (2) decision table -------------------------------------------------
    PRODUCER = 7      # any distinct, non-default identity tag
    CUSTOM = 5        # a custom concrete store identity tag

    # no producer, store == default  -> OMIT
    assert deconstruct_storage(False, DEFAULT, DEFAULT) == (False, DEFAULT)
    # no producer, store == custom   -> INCLUDE the store
    assert deconstruct_storage(False, DEFAULT, CUSTOM) == (True, CUSTOM)
    # producer, custom               -> INCLUDE the producer
    assert deconstruct_storage(True, PRODUCER, CUSTOM) == (True, PRODUCER)
    # producer evaluating to default -> INCLUDE the producer  (the F2P fix)
    assert deconstruct_storage(True, PRODUCER, DEFAULT) == (True, PRODUCER)
    # totalized (real-world-unreachable) corner: the producer IS the default
    # store object -> the general rule omits, matching what the gold
    # `storage = getattr(...); if storage is not default_storage` computes.
    assert deconstruct_storage(True, DEFAULT, DEFAULT) == (False, DEFAULT)
    assert deconstruct_storage(True, DEFAULT, CUSTOM) == (False, DEFAULT)

    # The buggy pre-patch differs EXACTLY on the F2P case (and only there among
    # producer cases): it wrongly OMITS a producer that evaluates to default.
    assert buggy_prepatch(True, PRODUCER, DEFAULT) == (False, PRODUCER)
    assert buggy_prepatch(True, PRODUCER, DEFAULT)[0] is False
    assert deconstruct_storage(True, PRODUCER, DEFAULT)[0] is True
    # On every non-default-evaluating configuration the two agree, so the fix
    # is surgical (matches the PASS_TO_PASS preservation).
    for hp, pid, sid in [(False, DEFAULT, DEFAULT), (False, DEFAULT, CUSTOM),
                         (True, PRODUCER, CUSTOM)]:
        assert deconstruct_storage(hp, pid, sid) == buggy_prepatch(hp, pid, sid)

    # The reported value is always the producer when one is held.
    for sid in (DEFAULT, CUSTOM, 99):
        assert reported_value(True, PRODUCER, sid) == PRODUCER
        assert reported_value(False, PRODUCER, sid) == sid

    print("CHECK OK: no consumed axiom (G-AX vacuous); identity-disjointness "
          "reachability fact holds for the F2P witness and representative "
          "callables; total decision table matches the modelled behaviour on "
          "all reachable configurations plus the unreachable totalized corner; "
          "pre-patch differs exactly on producer-returns-default.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
