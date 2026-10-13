#!/usr/bin/env python3
"""G-CONF for django__django-15525.

Mechanical differential test of the R/I skeleton of `implementation_resolveRecord`
against a faithful transcription of the PATCHED `build_instance` control flow,
over >=1e5 fuzzed inputs. exit 0 iff zero disagreements.

The A-consumed callees (`derive`/natural_key, `lookupByKey`/get_by_natural_key,
`coerceId`/to_python) are stubbed IDENTICALLY on every leg (mapping.md
bijection): G-CONF validates the R/I control/data flow — that the impl
establishes the target store on the record BEFORE deriving the key, and that it
runs the derivation step only where and on what that step is defined — not the
internals of those callees (G-AX's remit).

Three properties of the real callee are modelled, because the spec is stated
over all three:

  * `derive` is STORE-DEPENDENT: in the real ORM `natural_key()` may follow a
    ForeignKey, which is resolved against the instance's `_state.db`. So the key
    encodes the store it was derived on and the test exercises the exact
    multi-database discriminator the fix addresses.

  * `derive` is PARTIAL IN THE MODEL: not every model has a `natural_key`, and on
    one that does not, `obj.natural_key()` raises `AttributeError` rather than
    returning a key. Modelled as a FAILURE outcome, available exactly when
    `has_key` holds — the `hasKey = false` half of `derivationAvailability`.

  * `derive` is PARTIAL IN THE STORE: when the key follows a reference to a
    record that lives only in one store, deriving it on an instance carrying any
    OTHER store alias resolves nothing and raises `DoesNotExist`. That is not a
    hypothetical — it is the regression scenario, and it was confirmed directly
    against the F2P's model shape (a default-store `natural_key()` call raises
    `Person.DoesNotExist` where the target-store call returns the key). Modelled
    with a per-case `key_home`: the store the referenced record lives in, or None
    when the key follows no reference. This is the `hasKey = true` half of
    `derivationAvailability`, which assumes a key comes back only for the record
    assembled ON THE TARGET STORE.

Both real failures collapse onto the single `Failure` value the Lean carrier has
(see mapping.md): no impl can discriminate them, and clause (C0) forbids either
escaping, so nothing is lost by the collapse.

NEGATIVE CONTROLS. A differential test that cannot fail is worth nothing, so the
run also drives two rival control flows and requires EACH to disagree with the
patch:

  * `hoisted_build_instance` — the assemble-and-derive prelude lifted above the
    guard (the first audit rival: resolved the F2P, broke 26 PASS_TO_PASS tests).
  * `probing_build_instance` — the patch with one EXTRA `natural_key()` call on
    the not-yet-established instance, its result discarded (the second audit
    rival: PASS_TO_PASS 53/53 but FAIL_TO_PASS 0/1).

If either ever agreed on every input, the harness would have lost the power to
see a defect the fix is about, and this script exits non-zero on that too.
"""
import json
import random
import sys

DEFAULT_STORE = "default"
N = 120_000
SEED = 20240630

# The failure the derivation channel can carry (Failure.keyDerivationUnavailable).
UNAVAILABLE = ("error", "keyDerivationUnavailable")


# --- A-consumed callee stubs (shared, identical on every leg; mapping.md) ---

def _key(payload, store):
    """The tuple `natural_key()` yields for a record assembled on `store`."""
    return tuple(payload) + (("@" + store),)


def derive(record, has_key, key_home):
    """`obj.natural_key()`, as a step that is PARTIAL in two dimensions.

    `record` is (payload, store).

    * absent on a model that offers no such step (`has_key` false) — the real
      `AttributeError`;
    * unable to resolve when the key follows a reference to a record that lives
      in `key_home` and this record carries some other store alias — the real
      `DoesNotExist`.

    Otherwise it yields a key that ENCODES the store it was derived on, so a
    store mismatch is visible to the differential test.
    """
    payload, store = record
    if not has_key:
        return UNAVAILABLE
    if key_home is not None and store != key_home:
        return UNAVAILABLE
    return ("ok", _key(payload, store))


def lookup_by_key(store, key, table):
    """get_by_natural_key(*nk).pk in `store`, DoesNotExist -> None."""
    return table.get((store, key))


def coerce_id(raw):
    """pk.to_python(raw)."""
    return int(raw)


# --- Leg A: R/I shadow of implementation_resolveRecord (Solution.lean) ---

def impl_shadow(data_id, payload, store, has_key, key_home, table):
    if data_id is None and has_key is True:
        obj = (payload, DEFAULT_STORE)     # fresh record starts on default
        obj = (payload, store)             # the fix: establish target store
        outcome, key = derive(obj, has_key, key_home)
        if outcome == "error":
            return UNAVAILABLE             # the `←` short-circuits
        raw = lookup_by_key(store, key, table)
        if raw is not None:
            return ("ok", (coerce_id(raw), payload))
        return ("ok", (data_id, payload))
    return ("ok", (data_id, payload))


# --- Leg B: faithful transcription of PATCHED build_instance (patch.diff) ---

def patched_build_instance(data_id, payload, store, has_key, key_home, table):
    new_id = data_id
    if data_id is None and has_key:
        obj = (payload, DEFAULT_STORE)     # Model(**data) fresh instance
        obj = (payload, store)             # obj._state.db = db
        outcome, natural_key = derive(obj, has_key, key_home)
        if outcome == "error":
            return UNAVAILABLE             # the exception propagates
        try:
            pk = lookup_by_key(store, natural_key, table)
            if pk is None:
                raise KeyError                      # DoesNotExist
            new_id = coerce_id(pk)
        except KeyError:
            pass                                    # except Model.DoesNotExist
    return ("ok", (new_id, payload))


# --- Leg C: NEGATIVE CONTROL — the same patch with the assemble-and-derive
# prelude hoisted ABOVE the guard (the first audit rival). Must DISAGREE. ---

def hoisted_build_instance(data_id, payload, store, has_key, key_home, table):
    obj = (payload, DEFAULT_STORE)
    obj = (payload, store)
    outcome, natural_key = derive(obj, has_key, key_home)  # for EVERY record
    if outcome == "error":
        return UNAVAILABLE
    new_id = data_id
    if data_id is None and has_key:
        try:
            pk = lookup_by_key(store, natural_key, table)
            if pk is None:
                raise KeyError
            new_id = coerce_id(pk)
        except KeyError:
            pass
    return ("ok", (new_id, payload))


# --- Leg D: NEGATIVE CONTROL — the same patch plus one extra derivation on the
# not-yet-established record, result discarded (the second audit rival). Must
# DISAGREE. ---

def probing_build_instance(data_id, payload, store, has_key, key_home, table):
    new_id = data_id
    if data_id is None and has_key:
        obj = (payload, DEFAULT_STORE)     # Model(**data) fresh instance
        probe, _ = derive(obj, has_key, key_home)   # obj.natural_key() too early
        if probe == "error":
            return UNAVAILABLE             # the discarded call still raises
        obj = (payload, store)             # obj._state.db = db
        outcome, natural_key = derive(obj, has_key, key_home)
        if outcome == "error":
            return UNAVAILABLE
        try:
            pk = lookup_by_key(store, natural_key, table)
            if pk is None:
                raise KeyError
            new_id = coerce_id(pk)
        except KeyError:
            pass
    return ("ok", (new_id, payload))


def main():
    rnd = random.Random(SEED)
    stores = ["default", "other", "replica", "shard_a", "shard_b"]
    disagreements = 0
    hoist_disagreements = 0
    probe_disagreements = 0
    for _ in range(N):
        store = rnd.choice(stores)
        plen = rnd.randint(0, 3)
        payload = [rnd.choice(["a", "b", "c", "x", "y"]) for _ in range(plen)]
        data_id = None if rnd.random() < 0.6 else rnd.randint(0, 50)
        has_key = rnd.random() < 0.7
        # Where the record the key references lives: usually the target store
        # (the regression shape), sometimes another store, sometimes nowhere
        # because the key follows no reference at all.
        roll = rnd.random()
        key_home = None if roll < 0.4 else (store if roll < 0.8
                                            else rnd.choice(stores))

        # populate a lookup table that sometimes has an entry for the
        # store-derived key (and sometimes the WRONG, default-store key, to
        # catch a leg that derived against the wrong store).
        table = {}
        if rnd.random() < 0.7:
            table[(store, _key(payload, store))] = rnd.randint(100, 999)
        if rnd.random() < 0.3:
            table[(store, _key(payload, DEFAULT_STORE))] = rnd.randint(100, 999)

        args = (data_id, payload, store, has_key, key_home, table)
        a = impl_shadow(*args)
        b = patched_build_instance(*args)
        c = hoisted_build_instance(*args)
        d = probing_build_instance(*args)
        if a != b:
            disagreements += 1
            if disagreements <= 5:
                print(f"DISAGREE store={store} id={data_id} hk={has_key} "
                      f"key_home={key_home} payload={payload} impl={a} "
                      f"patched={b}", file=sys.stderr)
        if b != c:
            hoist_disagreements += 1
        if b != d:
            probe_disagreements += 1

    ok = (disagreements == 0 and hoist_disagreements > 0
          and probe_disagreements > 0)
    for name, n in (("hoisted", hoist_disagreements),
                    ("probing", probe_disagreements)):
        if n == 0:
            print(f"NEGATIVE CONTROL FAILED: the {name} control flow agreed with "
                  "the patch on every input, so this test has no power over a "
                  "defect the fix is about", file=sys.stderr)
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "django__django-15525",
        "status": "pass" if ok else "fail",
        "n": N,
        "seed": SEED,
        "disagreements": disagreements,
        "negative_control_disagreements": hoist_disagreements,
        "hoisted_control_disagreements": hoist_disagreements,
        "probing_control_disagreements": probe_disagreements,
    }))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
