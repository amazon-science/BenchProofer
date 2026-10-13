#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-16493 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the
              `serializedStorageArg` `do` block) transliterated to Python over
              the *real* repo types, via the mapping.md bijection:
                  Backend                 <-> a storage object (identity only)
                  defaultBackend          <-> the `default_storage` proxy object
                  storage : Backend       <-> the evaluated backend the field holds
                  storageCallable : Option <-> the original storage callable, when
                                              the field was configured by one
              Concretely the shadow is:
                  value := storageCallable.getD storage   # callable if present, else backend
                  out   := some value  if value != defaultBackend  else none
              There are NO A-tagged callees in the computed output (no consumed
              axioms — refinement.md §C), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: a patched real `FileField` constructed
              with `storage=arg` and then deconstructed; we read
              `deconstruct()[3].get('storage')` (the real correctness oracle,
              G-RESOLVE). The harness applies patch.diff at base_commit before
              this runs (gate_conf passes apply_gold=True).

Both sides are classified into a comparable tag:
  ('omitted',)            -- no `storage` kwarg emitted
  ('ref', id)             -- a storage reference emitted, compared by identity
                             (the original callable when one was supplied, else
                             the evaluated backend object)

The decisive corner (the issue's F2P scenario): a callable that returns
`default_storage`. Its evaluated backend IS the default, but the recorded
reference is the *callable*, which differs from the default — so the patched
field emits `('ref', id(callable))`, never `('omitted',)`. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), stdlib +
django only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16493
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        # Django 5.0: rely on the built-in default STORAGES (FileSystemStorage);
        # DEFAULT_FILE_STORAGE is deprecated and conflicts with STORAGES, so we
        # set only MEDIA_ROOT (where default_storage will point).
        settings.configure(
            DEBUG=True,
            USE_I18N=False,
            INSTALLED_APPS=[],
            DATABASES={},
            MEDIA_ROOT='/tmp/cf_media_16493',
        )
    django.setup()


def main():
    rng = random.Random(SEED)
    try:
        _setup_django()
        import tempfile
        from django.db.models import FileField
        from django.core.files.storage import (
            FileSystemStorage, default_storage,
        )
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not load patched django FileField: %r" % e)
        return 2

    # The default storage backend's identity is the abstract `defaultBackend`.
    # `default_storage` is the proxy object the patched `deconstruct` compares
    # against (`storage is not default_storage`).
    DEFAULT = id(default_storage)

    # ---- a small pool of real storage objects / callables to fuzz over -------
    concrete_storages = [FileSystemStorage(location=tempfile.mkdtemp())
                         for _ in range(4)]

    def make_callable(storage_obj):
        def _producer():
            return storage_obj
        return _producer

    # callables returning *non-default* storages
    producer_storages = [FileSystemStorage(location=tempfile.mkdtemp())
                         for _ in range(3)]
    producers = [make_callable(s) for s in producer_storages]

    # THE corner (issue F2P): a callable returning default_storage. Its evaluated
    # backend is the default, but the recorded reference is the callable itself,
    # which must be emitted, not omitted.
    def producer_to_default():
        return default_storage
    producers_default = [producer_to_default]

    # ---- model the field's known mapping arg_py -> (evaluated backend, callable)
    # This mirrors FileField.__init__: `self.storage = storage or default_storage;
    # if callable(self.storage): self._storage_callable = self.storage;
    # self.storage = self.storage()`. It is UNCHANGED by the patch (mapping.md §3,
    # an R abstraction); the patch only changes which reference deconstruct emits.
    def field_state(arg_py):
        """Returns (evaluated_backend_id, storage_callable_id_or_None)."""
        if arg_py is None:
            return (DEFAULT, None)
        if callable(arg_py):
            return (id(arg_py()), id(arg_py))       # backend := arg(); callable := arg
        return (id(arg_py), None)                    # concrete backend, no callable

    # ---- SHADOW: serializedStorageArg (storageCallable.getD storage) ----------
    def shadow(arg_py):
        backend, callable_id = field_state(arg_py)
        # value := storageCallable.getD storage  (callable when present, else backend)
        value = callable_id if callable_id is not None else backend
        if value != DEFAULT:
            return ('ref', value)
        return ('omitted',)

    # ---- ORACLE: patched FileField(storage=arg).deconstruct()['storage'] ------
    def oracle(arg_py):
        f = FileField(storage=arg_py, upload_to='x')
        kwargs = f.deconstruct()[3]
        if 'storage' not in kwargs:
            return ('omitted',)
        return ('ref', id(kwargs['storage']))

    # ---- input stream --------------------------------------------------------
    def inputs(n):
        # boundary cases first (plan §4.1 step 4)
        yield None                                   # no storage -> default -> omitted
        for s in concrete_storages:
            yield s                                  # concrete non-default backend
        for p in producers:
            yield p                                  # callable -> non-default backend
        for p in producers_default:
            yield p                                  # callable -> default backend (F2P)
        pool = ([None]
                + concrete_storages
                + producers
                + producers_default)
        for _ in range(n):
            yield rng.choice(pool)

    disagreements = []
    count = 0
    for arg_py in inputs(N_FUZZ):
        count += 1
        sh = shadow(arg_py)
        try:
            orc = oracle(arg_py)
        except Exception as e:
            disagreements.append((repr(arg_py), sh, "ORACLE-RAISED:%r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append((repr(arg_py), sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for s, sh, orc in disagreements:
            print("  input=%s shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of serializedStorageArg agrees with patch.diff "
          "(patched FileField construct+deconstruct) on %d inputs (seed=%d), 0 "
          "disagreements (recorded reference = the configuring callable when "
          "supplied, else the evaluated backend; omitted iff that reference is "
          "the default backend)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
