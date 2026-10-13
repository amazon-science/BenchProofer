#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13343 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`storage`-value <-> BackendArg, Storage-object-identity <->
              Backend.handle, callable <-> Producer, Python truthiness <->
              `.present`). Concretely the shadow is `emit (initState arg)`
              (the `roundTripStorage` postcondition):
                  initState: omitted OR not-present (falsy) -> default,
                             nothing retained (a falsy producer is never
                             consulted); present concrete b -> b (no
                             producer); present producer p -> (yields:=p(),
                             retain p)
                  emit:      backend==default -> omitted;
                             retained producer -> producer; else -> concrete
              There are NO A-tagged callees in the computed output (no consumed
              axioms — refinement.md §C), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched real `FileField`
              constructed with `storage=arg` and then deconstructed; we read
              `deconstruct()[3].get('storage')` (the real correctness oracle,
              G-RESOLVE). The harness applies patch.diff at base_commit before
              this runs.

Both sides are classified into a comparable tag:
  ('omitted',)            -- no `storage` kwarg emitted
  ('producer', id)        -- the original callable returned (identity preserved)
  ('concrete', id)        -- a concrete Storage instance returned (by identity)

They must agree on every input, including the producer-yields-default corner
(a callable returning `default_storage` must deconstruct to `omitted`, never to
the producer — mapping.md §2) and the falsy-storage corner (`storage or
default_storage` short-circuits on any falsy value — falsy callable, falsy
Storage instance, 0, '' — so the field falls back to the ambient storage and
deconstructs to `omitted`; a falsy callable is never called and never
retained). Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13343
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_I18N=False,
            INSTALLED_APPS=[],
            DATABASES={},
            DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
            MEDIA_ROOT='/tmp/cf_media_13343',
        )
    django.setup()


def main():
    rng = random.Random(SEED)
    try:
        _setup_django()
        import tempfile
        from django.db.models import FileField
        from django.core.files.storage import (
            FileSystemStorage, default_storage, Storage,
        )
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not load patched django FileField: %r" % e)
        return 2

    # The default storage's identity is the abstract `defaultBackend`. `id()` of
    # the `default_storage` proxy is stable across the run, and is precisely the
    # object the patched `deconstruct` compares against
    # (`self.storage is not default_storage`).
    DEFAULT = id(default_storage)

    # ---- a small pool of real storage objects / callables to fuzz over -------
    locs = [tempfile.mkdtemp() for _ in range(4)]
    concrete_storages = [FileSystemStorage(location=l) for l in locs]

    def make_callable(storage_obj):
        def _producer():
            return storage_obj
        return _producer

    # callables returning *non-default* storages
    producer_storages = [FileSystemStorage(location=tempfile.mkdtemp())
                         for _ in range(3)]
    producers = [make_callable(s) for s in producer_storages]

    # the corner: a callable returning default_storage -> must deconstruct to
    # `omitted`, never to the producer (mapping.md §2, emit checks default first)
    def producer_to_default():
        return default_storage
    producers_default = [producer_to_default]

    # the falsy-storage corner: `storage or default_storage` short-circuits on
    # ANY falsy value, so the field falls back to the ambient storage and
    # deconstructs to `omitted`. A falsy callable is never even called (the
    # presence test precedes the callable test) and never retained.
    class _FalsyCallable:
        def __init__(self, storage_obj):
            self._storage_obj = storage_obj

        def __call__(self):
            return self._storage_obj

        def __bool__(self):
            return False

    class _FalsyStorage(FileSystemStorage):
        def __bool__(self):
            return False

    falsy_values = [
        _FalsyCallable(FileSystemStorage(location=tempfile.mkdtemp())),
        _FalsyStorage(location=tempfile.mkdtemp()),
        0,
        '',
    ]

    # ---- SHADOW: emit (initState arg) over the bijection ---------------------
    def classify_arg(arg_py):
        # presence = Python truthiness (`storage or default_storage`), the
        # pre-existing presence test `initState` applies before anything else:
        # a not-present value is classified but never consulted/retained.
        if arg_py is None:
            return ('omitted',)
        present = bool(arg_py)
        if callable(arg_py):
            # a not-present producer is never consulted: yields is irrelevant
            yields = id(arg_py()) if present else None
            return ('producer', id(arg_py), yields, present)
        return ('concrete', id(arg_py), present)

    def init_state(arg):
        # returns (backend_id, retained_producer_id_or_None)
        if arg[0] == 'omitted':
            return (DEFAULT, None)
        if arg[0] == 'concrete':
            if not arg[2]:          # not present -> ambient, nothing retained
                return (DEFAULT, None)
            return (arg[1], None)
        # producer
        if not arg[3]:              # not present -> ambient, nothing retained
            return (DEFAULT, None)
        # backend := yields (arg[2]); retain producer id (arg[1])
        return (arg[2], arg[1])

    def emit(st):
        backend, retained = st
        if backend == DEFAULT:
            return ('omitted',)
        if retained is not None:
            return ('producer', retained)
        return ('concrete', backend)

    def shadow(arg_py):
        return emit(init_state(classify_arg(arg_py)))

    # ---- ORACLE: patched FileField(storage=arg).deconstruct()['storage'] -----
    def oracle(arg_py):
        f = FileField(storage=arg_py, upload_to='x')
        kwargs = f.deconstruct()[3]
        if 'storage' not in kwargs:
            return ('omitted',)
        val = kwargs['storage']
        if callable(val):
            return ('producer', id(val))
        return ('concrete', id(val))

    # ---- input stream --------------------------------------------------------
    def inputs(n):
        # boundary cases first (plan §4.1 step 4)
        yield None                                   # omitted
        for s in concrete_storages:
            yield s                                  # concrete
        for p in producers:
            yield p                                  # producer (non-default)
        for p in producers_default:
            yield p                                  # producer -> default corner
        for v in falsy_values:
            yield v                                  # falsy-storage corner
        pool = ([None]
                + concrete_storages
                + producers
                + producers_default
                + falsy_values)
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
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%s shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of roundTripStorage (emit . initState) agrees "
          "with patch.diff (patched FileField construct+deconstruct) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
