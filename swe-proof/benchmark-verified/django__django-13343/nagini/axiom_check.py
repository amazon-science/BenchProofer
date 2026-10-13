#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13343.

The bundle ships **no consumed `@ContractOnly` axiom**: the behaviour is pure
object-identity / field-state logic, modelled deeply. Two facts the model
encodes about real Python / Django semantics are validated here as
**A-references** (deep-model assumption ⇔ real semantics), on the SAME producers
the hidden F2P test uses:

  (A-reference 1) Evaluating a storage *producer* yields a concrete store that
      is a DISTINCT object from the producer itself, and that yielded object is
      a real Storage. This is the `configure` precondition `evaluated != given`
      (and `evaluated != default`). If a producer evaluated to ITSELF, the bug
      would be invisible — so this is load-bearing.

  (A-reference 2) The default-store identity comparison: a non-default supplied
      store satisfies `store is not default_storage` (so deconstruct DOES emit
      the `storage` key), and `default_storage is default_storage` (so an
      unconfigured field suppresses it). This is the `describe_store` guard
      `field.store == default_store_id()`.

It also exercises the full modeled round-trip against the REAL FileField on the
F2P field: a FileField configured with a callable storage must deconstruct to
the ORIGINAL callable (`deconstruct()['storage'] is callable_storage`), and a
FileField configured with a concrete storage must deconstruct to that storage.
This is the F2P case enumerated explicitly and asserted at the IDENTITY level
(no double-mask): we compare `is`, not a value proxy.

Runs in-container (the real eval interpreter + the repo's Django). Imports only
the standard library and Django (the very package the patch lives in). Exit 0
iff every obligation holds.
"""
import os
import sys
import tempfile


def main():
    # --- minimal Django settings so the storage / fields machinery imports ---
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
            MEDIA_ROOT=tempfile.mkdtemp(),
            USE_TZ=True,
        )
        django.setup()

    from django.core.files.storage import (
        FileSystemStorage, Storage, default_storage,
    )
    from django.db.models.fields.files import FileField

    # --- the SAME producers the hidden F2P test uses ------------------------
    temp_storage_location = tempfile.mkdtemp()
    temp_storage = FileSystemStorage(location=temp_storage_location)

    def callable_storage():
        return temp_storage

    class CallableStorage(FileSystemStorage):
        def __call__(self):
            return self

    # ===================================================================
    # A-reference 1: producer evaluation yields a DISTINCT real Storage
    # ===================================================================
    producers = [callable_storage, CallableStorage]
    for producer in producers:
        assert callable(producer), (
            "test setup: %r must be callable" % (producer,))
        evaluated = producer()
        # evaluated != given  (the configure precondition; load-bearing)
        assert evaluated is not producer, (
            "A-reference 1 UNSOUND: producer %r evaluated to ITSELF; the model "
            "precondition `evaluated != given` would not hold and the bug "
            "would be invisible" % (producer,))
        # evaluated is a real store, not the ambient default
        assert isinstance(evaluated, Storage), (
            "A-reference 1 UNSOUND: producer %r evaluated to a non-Storage %r"
            % (producer, evaluated))
        assert evaluated is not default_storage, (
            "A-reference 1 UNSOUND: producer %r evaluated to default_storage"
            % (producer,))

    # ===================================================================
    # A-reference 2: default-store identity comparison
    # ===================================================================
    assert temp_storage is not default_storage, (
        "A-reference 2 UNSOUND: a configured non-default store compared `is` "
        "default_storage; deconstruct would wrongly suppress the storage key")
    assert default_storage is default_storage, (
        "A-reference 2 UNSOUND: default_storage identity is not reflexive")

    # ===================================================================
    # End-to-end round-trip on the REAL FileField (the F2P behaviour),
    # asserted at the IDENTITY level (assertIs), no value proxy / double-mask.
    # ===================================================================

    # (a) configured with a callable -> deconstruct gives the ORIGINAL callable
    f_callable = FileField(storage=callable_storage, upload_to='storage_callable')
    *_, kwargs = f_callable.deconstruct()
    assert 'storage' in kwargs, (
        "F2P UNSOUND: storage key absent for a non-default configured store")
    assert kwargs['storage'] is callable_storage, (
        "F2P FAIL: deconstruct gave %r, expected the ORIGINAL callable %r "
        "(this is exactly assertIs(storage, callable_storage))"
        % (kwargs['storage'], callable_storage))
    # and it is NOT the evaluated concrete store (the bug's signature)
    assert kwargs['storage'] is not f_callable.storage, (
        "F2P FAIL: deconstruct gave the EVALUATED store, not the callable")

    # (b) configured with a callable Storage CLASS -> original class reference
    f_callable_cls = FileField(storage=CallableStorage, upload_to='c')
    *_, kwargs_cls = f_callable_cls.deconstruct()
    assert kwargs_cls.get('storage') is CallableStorage, (
        "F2P FAIL: callable-class storage did not deconstruct to the class; "
        "got %r" % (kwargs_cls.get('storage'),))

    # (c) configured with a concrete (non-callable) store -> that same store
    f_concrete = FileField(storage=temp_storage, upload_to='tests')
    *_, kwargs_c = f_concrete.deconstruct()
    assert kwargs_c.get('storage') is temp_storage, (
        "P2P FAIL: concrete-store field did not deconstruct to its store; "
        "got %r" % (kwargs_c.get('storage'),))

    # (d) default storage -> storage key suppressed
    f_default = FileField(upload_to='tests')
    *_, kwargs_d = f_default.deconstruct()
    assert 'storage' not in kwargs_d, (
        "P2P FAIL: default-store field wrongly emitted a storage key: %r"
        % (kwargs_d.get('storage'),))

    print("G-AX OK: A-reference 1 (producer evaluation yields a distinct real "
          "Storage) and A-reference 2 (default-store identity) sound on %d "
          "real producers; F2P/P2P round-trip on the real FileField holds at "
          "identity level (callable->callable, class->class, concrete->concrete, "
          "default->suppressed)." % len(producers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
