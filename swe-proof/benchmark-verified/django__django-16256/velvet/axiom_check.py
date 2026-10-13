#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16256.

The bundle has NO consumed `axiom`. The single callee the modeled methods rely
on — the asynchronous bridge that runs a synchronous callable and awaits it —
is UNCHANGED (it is imported, not modified, by the gold patch). The deep model
abstracts the awaited call to the synchronous relation-establishing effect
itself (`related := related ++ [newObj]`), an **A-reference** (mapping.md §3.1):
the model is sound only if running a synchronous callable through the real
bridge and awaiting it is OBSERVATIONALLY THE CALLABLE ITSELF — same return
value, same side effect on the parent's collection.

This check validates that A-reference against the REAL bridge
(`asgiref.sync.sync_to_async`, the very callable the gold patch imports and
calls), on boundary + randomized fuzz synchronous callables that

  (a) return a value (the analogue of the created/fetched object's identity),
  and
  (b) mutate an external collection (the analogue of "settle the new object
      into the parent's related collection").

For each callable it asserts:

  (A-reference 1)  the value obtained by ``await sync_to_async(f)(*args)`` equals
      the value obtained by calling ``f(*args)`` directly;
  (A-reference 2)  the external collection ends in the IDENTICAL state after the
      awaited bridged call as after the direct synchronous call — i.e. the
      relation side effect is preserved by the bridge, not dropped.

It also confirms the converse half of the issue's premise: a coroutine that does
NOT run the synchronous callable (the inherited-QuerySet behaviour the bug
exhibited — produce a value but never settle it) leaves the collection in a
DIFFERENT state, so the discriminating side effect is real and observable.

Imports only the standard library (`asyncio`, `random`, `copy`) and
`asgiref.sync` (the unchanged callee itself, an installed Django dependency in
the instance image). No patched repo code. Exit 0 iff behaviour-preserving.
"""
import asyncio
import copy
import random
import sys

from asgiref.sync import sync_to_async


# --- the modeled side effect: a synchronous "relation-establishing" callable -
# Each callable mutates an external list `collection` (the parent's related
# collection) and returns an identity value, mirroring the real sync members
# (`create` / `get_or_create` / `update_or_create`) that link the new object.

def make_create(collection, new_obj):
    """Analogue of the related manager's own `create`: settle a fresh object
    into the collection and return its identity."""
    def f():
        collection.append(new_obj)        # link the new object to the parent
        return new_obj
    return f


def make_get_or_create(collection, preexists, existing_obj, new_obj):
    """Analogue of `get_or_create`: return an existing object unchanged, or
    settle and return a new one with a `created` flag."""
    def f():
        if preexists:
            return (existing_obj, False)
        collection.append(new_obj)
        return (new_obj, True)
    return f


def make_no_link(collection, new_obj):
    """Analogue of the inherited-QuerySet coroutine the issue describes: it
    produces an object but NEVER settles it into the parent's collection."""
    def f():
        return new_obj
    return f


def run_async(coro_callable, *args):
    """Run `await sync_to_async(coro_callable)(*args)` to completion, returning
    the awaited result. This drives the REAL bridge end to end."""
    async def driver():
        return await sync_to_async(coro_callable)(*args)
    return asyncio.run(driver())


def check_value_and_effect(build, *build_args):
    """A-reference 1 + 2: the bridged-and-awaited call yields the same value AND
    leaves the external collection in the same state as the direct sync call."""
    # direct synchronous baseline
    direct_collection = []
    direct_f = build(direct_collection, *build_args)
    direct_value = direct_f()

    # the REAL bridge: run an equivalent callable through sync_to_async + await
    bridged_collection = []
    bridged_f = build(bridged_collection, *build_args)
    bridged_value = run_async(bridged_f)

    assert bridged_value == direct_value, (
        "sync_to_async changed the return value: direct=%r bridged=%r"
        % (direct_value, bridged_value))
    assert bridged_collection == direct_collection, (
        "sync_to_async dropped/altered the relation side effect: "
        "direct collection=%r bridged collection=%r"
        % (direct_collection, bridged_collection))


def check_link_is_observable(new_obj):
    """The discriminating fact: the relation-establishing callable changes the
    collection, whereas the no-link callable (the bug) does not — so the side
    effect the spec pins (`related = relatedOld ++ [newObj]`) is real."""
    linked = []
    run_async(make_create(linked, new_obj))
    assert linked == [new_obj], (
        "relation-establishing callable failed to settle the object: %r" % linked)

    unlinked = []
    val = run_async(make_no_link(unlinked, new_obj))
    assert unlinked == [], "no-link callable unexpectedly mutated the collection"
    assert val == new_obj
    assert linked != unlinked, "link vs no-link must be observably different"


def main():
    # --- boundary cases ---------------------------------------------------
    boundary_objs = [0, 1, 2, 7, 42, 1000, 2 ** 31]
    for obj in boundary_objs:
        # acreate analogue: always settles a fresh object
        check_value_and_effect(make_create, obj)
        # the side effect is observable / the bug surface is real
        check_link_is_observable(obj)

    # aget_or_create / aupdate_or_create analogue: both branches
    for preexists in (True, False):
        for existing_obj, new_obj in [(3, 9), (0, 0), (5, 5), (100, 7)]:
            check_value_and_effect(make_get_or_create, preexists,
                                   existing_obj, new_obj)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(16256)
    for _ in range(2000):
        new_obj = rng.randint(0, 10 ** 6)
        check_value_and_effect(make_create, new_obj)

        preexists = rng.random() < 0.5
        existing_obj = rng.randint(0, 10 ** 6)
        new_obj2 = rng.randint(0, 10 ** 6)
        check_value_and_effect(make_get_or_create, preexists,
                               existing_obj, new_obj2)

    # randomized observability of the link side effect
    for _ in range(500):
        check_link_is_observable(rng.randint(0, 10 ** 6))

    print("G-AX OK: asgiref.sync.sync_to_async is behaviour-preserving on "
          "value + relation side effect (A-reference) over %d boundary objects, "
          "both get-or-create branches, and 2000+500 fuzz callables; the "
          "relation-establishing effect is observably distinct from the "
          "no-link (inherited-coroutine) behaviour." % len(boundary_objs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
