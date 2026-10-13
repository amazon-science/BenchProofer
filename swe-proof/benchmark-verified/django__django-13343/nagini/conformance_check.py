#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13343 (nagini).

SHADOW: the impl regions of model.py (`configure` and `describe_store`),
copied verbatim below with the contract calls (Requires/Ensures) stripped.
The model IS Python: the impl operates on a plain field object carrying
three attributes (store / has_producer / producer_id), so it runs directly.
The one @Pure helper `default_store_id` copies over as a plain function.
There are no @ContractOnly callees in this bundle (no consumed axioms).

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
the storage-handling block of `FileField.__init__` (the configuration site)
and the storage-handling block of `FileField.deconstruct` (the description
site), on real FileField / Storage objects. The gate applies the gold patch
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
package importable.

Type bridge (mapping.md section 2): store objects and store producers are
modelled by object identity, carried as distinct ints; the ambient default
store carries the reserved id 0. Per trial a fresh id map is built:
  default store object       <-> 0
  each other object involved <-> a fresh nonzero int
Field-state bridge: the live store attribute <-> field.store; the presence
of the recorded-producer attribute <-> field.has_producer; its value (when
present) <-> field.producer_id. Output bridge for the description query:
the storage entry absent from the deconstructed kwargs <-> None; present
with object o <-> the id of o.

Input domain:
  configure  — Requires: given != 0 (a real, non-default store or producer
      is supplied) and, when a producer is supplied, its evaluation is a
      DISTINCT real non-default store (evaluated != given, evaluated != 0).
      Realized as a real Storage instance (direct case) or a real callable
      whose evaluation yields a pre-chosen distinct Storage instance
      (producer case). For the non-producer case the `evaluated` argument
      is unconstrained; the shadow gets random junk there to confirm the
      impl ignores it.
  describe_store — Requires: only read access to the field; ANY field state
      is in-domain. Realized by building a real FileField and setting its
      storage / recorded-producer attributes directly, including states not
      reachable through configuration (default live store with a recorded
      producer, recorded producer equal to the live store, etc.).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials,
each trial exercising one configure input and >=1 describe_store input.
Pinned fuzz seed: 13343.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random fuzzing; no hypothesis needed).
"""
import json
import random
import sys
import tempfile

SEED = 13343
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped ---------------------------

def default_store_id():
    """The reserved identity of the ambient default store."""
    return 0


# --- the field state carrier from model.py, contracts stripped ---------------

class AttachmentField:
    def __init__(self):
        self.store = 0             # live concrete store identity
        self.has_producer = False  # whether a producer was recorded
        self.producer_id = 0       # recorded original producer id


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def configure(field, given, given_is_producer, evaluated):
    field.store = given
    if given_is_producer:
        # Record a reference to the original producer, then adopt the concrete
        # store it yields as the live store.
        field.has_producer = True
        field.producer_id = given
        field.store = evaluated
    else:
        field.has_producer = False
    # impl-end (verbatim copy ends here)


def describe_store(field):
    if field.store == default_store_id():
        return None
    if field.has_producer:
        return field.producer_id
    return field.store
    # impl-end (verbatim copy ends here)


# --- identity bridge ----------------------------------------------------------

class IdMap:
    """Per-trial bijection object-identity <-> int id; default store <-> 0."""

    def __init__(self, default_obj):
        self._objs = [default_obj]          # index == id; also pins objects
        self._ids = {id(default_obj): 0}

    def bind(self, obj):
        """Register obj (fresh nonzero id if unseen) and return its id."""
        k = id(obj)
        if k not in self._ids:
            self._ids[k] = len(self._objs)
            self._objs.append(obj)
        return self._ids[k]

    def lookup(self, obj):
        """Id of an already-registered object, or None if outside the map."""
        return self._ids.get(id(obj))


_SENTINEL = object()


def observe_real_field(real_field, idmap):
    """Project the real field's state through the bridge:
    (store_id, has_producer, producer_id_or_None)."""
    store_id = idmap.lookup(real_field.storage)
    rec = getattr(real_field, '_storage_callable', _SENTINEL)
    if rec is _SENTINEL:
        return store_id, False, None
    return store_id, True, idmap.lookup(rec)


def real_description(real_field, idmap):
    """The description the real field emits, through the output bridge:
    None iff no storage entry; else the id of the emitted object (or the
    string '<unmapped>' if the object is outside the trial's universe)."""
    _, _, _, kwargs = real_field.deconstruct()
    if 'storage' not in kwargs:
        return None
    got = idmap.lookup(kwargs['storage'])
    return got if got is not None else '<unmapped>'


def fail(label, ctx, shadow, real):
    print("DISAGREEMENT [%s]\n  input: %s\n  shadow: %r\n  real:   %r"
          % (label, ctx, shadow, real))
    return 1


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
    from django.db.models.fields.files import FileField  # REAL patched code

    # The ambient default store is a (possibly lazy) module-level singleton;
    # the repo's identity comparisons are against that singleton object
    # itself, so it is exactly the object bound to the reserved id 0.

    rng = random.Random(SEED)
    checked_configure = 0
    checked_describe = 0

    class CallableStore(FileSystemStorage):
        """A store object that is itself callable: evaluating it yields a
        fixed, distinct other store (set post-construction)."""
        _yields = None

        def __call__(self):
            return self._yields

    def fresh_store():
        return Storage()

    # ------------------------------------------------------------------
    # one configure trial: realize inputs, run shadow + real, diff state
    # and the follow-on description
    # ------------------------------------------------------------------
    def run_configure_trial(kind):
        nonlocal checked_configure, checked_describe
        idmap = IdMap(default_storage)

        if kind == 'direct':
            given_obj = fresh_store()
            given_id = idmap.bind(given_obj)
            is_producer = False
            evaluated_id = rng.randint(-10**6, 10**6)  # junk: must be ignored
            supplied = given_obj
            expect_eval_obj = None
        elif kind == 'func_producer':
            evaluated_obj = fresh_store()

            def producer(_ret=evaluated_obj):
                return _ret
            given_obj = producer
            given_id = idmap.bind(given_obj)
            evaluated_id = idmap.bind(evaluated_obj)
            is_producer = True
            supplied = given_obj
            expect_eval_obj = evaluated_obj
        elif kind == 'lambda_producer':
            evaluated_obj = fresh_store()
            given_obj = (lambda _ret=evaluated_obj: _ret)
            given_id = idmap.bind(given_obj)
            evaluated_id = idmap.bind(evaluated_obj)
            is_producer = True
            supplied = given_obj
            expect_eval_obj = evaluated_obj
        else:  # 'callable_store_producer': a store that is itself callable
            evaluated_obj = fresh_store()
            given_obj = CallableStore()
            given_obj._yields = evaluated_obj
            given_id = idmap.bind(given_obj)
            evaluated_id = idmap.bind(evaluated_obj)
            is_producer = True
            supplied = given_obj
            expect_eval_obj = evaluated_obj

        # Requires realization sanity (not part of the diff)
        assert given_id != 0
        if is_producer:
            assert evaluated_id != given_id
            assert evaluated_id != 0

        # shadow
        f = AttachmentField()
        configure(f, given_id, is_producer, evaluated_id)
        checked_configure += 1

        # real
        real = FileField(storage=supplied, upload_to='x')
        r_store, r_has, r_prod = observe_real_field(real, idmap)
        ctx = ("kind=%s given_id=%d is_producer=%r evaluated_id=%r"
               % (kind, given_id, is_producer, evaluated_id))
        if expect_eval_obj is not None and real.storage is not expect_eval_obj:
            return fail("configure/live-store-object", ctx,
                        "evaluation yields the pre-chosen store",
                        "different object: %r" % (real.storage,))
        if (r_store, r_has) != (f.store, f.has_producer):
            return fail("configure/state", ctx,
                        (f.store, f.has_producer, f.producer_id),
                        (r_store, r_has, r_prod))
        if r_has and r_prod != f.producer_id:
            return fail("configure/recorded-producer", ctx,
                        f.producer_id, r_prod)

        # follow-on description on the same field (the round-trip)
        d_shadow = describe_store(f)
        d_real = real_description(real, idmap)
        checked_describe += 1
        if d_shadow != d_real:
            return fail("describe-after-configure", ctx, d_shadow, d_real)
        return 0

    # ------------------------------------------------------------------
    # one describe-only trial: realize an arbitrary field state directly
    # ------------------------------------------------------------------
    def run_describe_trial(store_is_default, has_producer, producer_kind):
        nonlocal checked_describe
        idmap = IdMap(default_storage)

        real = FileField(upload_to='x')  # live store starts as the default
        f = AttachmentField()

        if store_is_default:
            f.store = 0
        else:
            s = fresh_store()
            real.storage = s
            f.store = idmap.bind(s)

        if has_producer:
            f.has_producer = True
            if producer_kind == 'distinct':
                p = fresh_store()
            elif producer_kind == 'same_as_store' and not store_is_default:
                p = real.storage
            elif producer_kind == 'default':
                p = default_storage
            else:
                p = (lambda: None)
            real._storage_callable = p
            f.producer_id = idmap.bind(p) if p is not default_storage else 0
        else:
            f.has_producer = False
            f.producer_id = rng.randint(-10**6, 10**6)  # junk: must be unread

        d_shadow = describe_store(f)
        d_real = real_description(real, idmap)
        checked_describe += 1
        ctx = ("store_is_default=%r has_producer=%r producer_kind=%s "
               "state=(%r,%r,%r)" % (store_is_default, has_producer,
                                     producer_kind, f.store, f.has_producer,
                                     f.producer_id))
        if d_shadow != d_real:
            return fail("describe-only", ctx, d_shadow, d_real)
        return 0

    # ---------------- boundary cases ----------------
    boundary = [
        lambda: run_configure_trial('direct'),
        lambda: run_configure_trial('func_producer'),
        lambda: run_configure_trial('lambda_producer'),
        lambda: run_configure_trial('callable_store_producer'),
        lambda: run_describe_trial(True, False, None),
        lambda: run_describe_trial(True, True, 'distinct'),
        lambda: run_describe_trial(True, True, 'default'),
        lambda: run_describe_trial(False, False, None),
        lambda: run_describe_trial(False, True, 'distinct'),
        lambda: run_describe_trial(False, True, 'same_as_store'),
        lambda: run_describe_trial(False, True, 'default'),
        lambda: run_describe_trial(False, True, 'callable'),
    ]
    for case in boundary:
        if case():
            return 1
    n_boundary = len(boundary)

    # ---------------- fuzz ----------------
    conf_kinds = ['direct', 'func_producer', 'lambda_producer',
                  'callable_store_producer']
    prod_kinds = ['distinct', 'same_as_store', 'default', 'callable']
    for _ in range(N_FUZZ):
        if rng.random() < 0.65:
            if run_configure_trial(rng.choice(conf_kinds)):
                return 1
        else:
            if run_describe_trial(rng.random() < 0.25,
                                  rng.random() < 0.5,
                                  rng.choice(prod_kinds)):
                return 1

    total = checked_configure + checked_describe
    print("G-CONF OK: shadow impl == real patched FileField behaviour on %d "
          "inputs (%d configure + %d describe; %d boundary cases + %d fuzz "
          "trials, seed %d)."
          % (total, checked_configure, checked_describe, n_boundary,
             N_FUZZ, SEED))
    print(json.dumps({"checked": total, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
