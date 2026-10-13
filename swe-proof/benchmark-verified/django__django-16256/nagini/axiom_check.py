#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16256.

This bundle consumes NO unchanged-callee axiom and pins NO A-reference deep
model against a separate stdlib oracle: the changed behaviour (a deferred
object-producing form must run the related-set accessor's OWN immediate form,
so a newly-produced object is attached to the related set AND the operation's
own payload discipline is what happens to the object) is modelled DEEPLY in
model.py as a list append plus a payload write, and each deferred form's
contract is tied to its immediate counterpart's exact post-state.

The one library primitive the deep model's "deferred form delivers EXACTLY the
result and effect of the immediate form" abstraction rests on is the real
`asgiref.sync.sync_to_async` the gold patch introduces:

    async def acreate(self, **kwargs):
        return await sync_to_async(self.create)(**kwargs)

i.e. `await sync_to_async(f)(**kwargs)` must (a) return EXACTLY `f(**kwargs)`
and (b) reproduce EXACTLY the side effects of running `f` — here BOTH touched
data: attaching the produced object to the related set, and the value the
object the operation keys on ends up carrying. This check executes the REAL
`sync_to_async` against representative immediate forms and asserts both facts,
including the payload ASYMMETRY between the two locate forms that model.py
pins: locate-or-produce hands an already-present object back untouched, while
refresh-or-produce leaves it carrying the requested payload in both branches.

It also confirms the check DISCRIMINATES on both dimensions:
  * membership — the pre-patch shape (a deferred form that delivers the object
    but delegates to a bare produce that does NOT attach) violates the
    membership fact;
  * payload — a deferred refresh-or-produce form that delegates to the LOCATE
    immediate form (identical on identity, flag and membership) violates the
    payload fact.

Imports only the standard library plus `asgiref` — the very module the gold
patch imports (`from asgiref.sync import sync_to_async`); nothing repo-specific.
Exit 0 iff every obligation holds.
"""
import asyncio
import random
import sys

from asgiref.sync import sync_to_async


# --- the touched state -------------------------------------------------------
# Mirrors model.py's RelatedAccessor: the related set (`members`) plus the value
# currently persisted for the object the operation keys on (`payload`).

class Accessor:
    def __init__(self, members, payload):
        self.members = list(members)
        self.payload = payload

    def snapshot(self):
        return (list(self.members), self.payload)


# --- model.py reference: the immediate forms (deeply modelled) ----------------

def immediate_create(acc, obj, requested):
    """Related-set accessor's OWN immediate produce form: attach the produced
    object to the related set, give it the requested payload, and deliver it
    (model.py `create`)."""
    acc.members.append(obj)
    acc.payload = requested
    return obj


def immediate_get_or_create(acc, obj, exists, requested):
    """Immediate locate-or-produce (model.py `get_or_create`): an already-present
    object leaves the set unchanged and is handed back EXACTLY as it stands (the
    requested payload is used only when a new object has to be produced); a
    produced object is attached and carries the requested payload."""
    if exists:
        return (obj, False, acc.payload)
    acc.members.append(obj)
    acc.payload = requested
    return (obj, True, requested)


def immediate_update_or_create(acc, obj, exists, requested):
    """Immediate refresh-or-produce (model.py `update_or_create`): SAME
    membership effect as locate-or-produce, but the object ends up carrying the
    requested payload in BOTH branches — an already-present object is refreshed
    with it rather than handed back untouched."""
    if exists:
        acc.payload = requested
        return (obj, False, requested)
    acc.members.append(obj)
    acc.payload = requested
    return (obj, True, requested)


# --- the deferred forms, built with the REAL sync_to_async (gold patch shape) --

async def deferred_create(acc, obj, requested):
    # mirrors: return await sync_to_async(self.create)(**kwargs)
    return await sync_to_async(lambda: immediate_create(acc, obj, requested))()


async def deferred_get_or_create(acc, obj, exists, requested):
    return await sync_to_async(
        lambda: immediate_get_or_create(acc, obj, exists, requested)
    )()


async def deferred_update_or_create(acc, obj, exists, requested):
    return await sync_to_async(
        lambda: immediate_update_or_create(acc, obj, exists, requested)
    )()


# --- the pre-patch deferred shape: deliver the object but DO NOT attach -------

async def unattached_deferred_create(acc, obj, requested):
    # a bare produce that never attaches to THIS related set (and so never
    # touches the accessor's payload either)
    return await sync_to_async(lambda: obj)()


# --- a deferred refresh form that runs the WRONG immediate form ---------------

async def collapsed_deferred_update_or_create(acc, obj, exists, requested):
    # delegates to locate-or-produce: identical on delivered identity, on the
    # produced/located flag and on membership in every branch, and differs ONLY
    # in the payload dimension.
    return await sync_to_async(
        lambda: immediate_get_or_create(acc, obj, exists, requested)
    )()


# --- the checks --------------------------------------------------------------

def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def check_create(obj, pre_members, pre_payload, requested):
    """await sync_to_async(immediate) == immediate, INCLUDING both effects."""
    acc_def = Accessor(pre_members, pre_payload)
    acc_imm = Accessor(pre_members, pre_payload)
    r_def = _run(deferred_create(acc_def, obj, requested))
    r_imm = immediate_create(acc_imm, obj, requested)
    # (a) same delivered object
    assert r_def == r_imm, (obj, r_def, r_imm)
    # (b) same membership effect (the produced object is attached) AND
    # (c) same payload effect (it carries what the caller asked for)
    expected = (list(pre_members) + [obj], requested)
    assert acc_def.snapshot() == acc_imm.snapshot() == expected, (
        "deferred create did not reproduce the immediate attach + payload "
        "effect: %r vs %r vs expected %r"
        % (acc_def.snapshot(), acc_imm.snapshot(), expected))


def check_pair(immediate, deferred, obj, exists, pre_members, pre_payload,
               requested, refreshes):
    """`refreshes` says whether this operation applies the caller's payload to an
    already-present object (refresh-or-produce) or hands it back untouched
    (locate-or-produce). The two differ ONLY here."""
    acc_def = Accessor(pre_members, pre_payload)
    acc_imm = Accessor(pre_members, pre_payload)
    r_def = _run(deferred(acc_def, obj, exists, requested))
    r_imm = immediate(acc_imm, obj, exists, requested)
    assert r_def == r_imm, (obj, exists, r_def, r_imm)
    if exists:
        exp_members = list(pre_members)
        exp_payload = requested if refreshes else pre_payload
    else:
        exp_members = list(pre_members) + [obj]
        exp_payload = requested
    expected = (exp_members, exp_payload)
    assert acc_def.snapshot() == acc_imm.snapshot() == expected, (
        "deferred locate/refresh did not reproduce the immediate membership + "
        "payload effect: %r vs %r vs expected %r (exists=%r refreshes=%r)"
        % (acc_def.snapshot(), acc_imm.snapshot(), expected, exists, refreshes))
    # the DELIVERED payload must equal the persisted one in every branch
    assert r_def[2] == exp_payload, (r_def, exp_payload)


def check_discriminates_membership(obj, pre_members, pre_payload, requested):
    """The pre-patch shape (no attach) must FAIL the membership fact, proving
    this check distinguishes running the accessor's own immediate form from
    merely delivering an object."""
    acc = Accessor(pre_members, pre_payload)
    r = _run(unattached_deferred_create(acc, obj, requested))
    assert r == obj                              # it still delivers the object
    assert acc.members == list(pre_members)      # ... but never attaches it
    # so the membership clause the model pins would be violated:
    assert acc.members != list(pre_members) + [obj]


def check_discriminates_payload(obj, pre_members, pre_payload, requested):
    """A deferred refresh form that runs the LOCATE immediate form must FAIL the
    payload fact, proving this check distinguishes the two operations that agree
    on identity, flag and membership."""
    if requested == pre_payload:
        return  # nothing to discriminate when the caller asks for what is there
    acc = Accessor(pre_members, pre_payload)
    r = _run(collapsed_deferred_update_or_create(acc, obj, True, requested))
    ref = Accessor(pre_members, pre_payload)
    r_ref = immediate_update_or_create(ref, obj, True, requested)
    # identity and flag agree ...
    assert r[0] == r_ref[0] and r[1] == r_ref[1], (r, r_ref)
    # ... and so does membership ...
    assert acc.members == ref.members == list(pre_members)
    # ... but both payload observables disagree, so the model's
    # `mgr.payload == requested` / `Result().payload == requested` clauses are
    # exactly what reject the collapse.
    assert acc.payload == pre_payload and ref.payload == requested, (
        acc.payload, ref.payload)
    assert r[2] == pre_payload and r_ref[2] == requested, (r, r_ref)


def main():
    rng = random.Random(16256)
    cases = 0
    for _ in range(200):
        obj = rng.randint(100, 10_000)
        pre_members = [rng.randint(1, 99) for _ in range(rng.randint(0, 4))]
        pre_payload = rng.randint(0, 50)
        # exercise both the "asks for something new" and the degenerate "asks for
        # the value already stored" shapes
        requested = pre_payload if rng.random() < 0.25 else rng.randint(51, 100)
        check_create(obj, pre_members, pre_payload, requested)
        for exists in (True, False):
            check_pair(immediate_get_or_create, deferred_get_or_create,
                       obj, exists, pre_members, pre_payload, requested,
                       refreshes=False)
            check_pair(immediate_update_or_create, deferred_update_or_create,
                       obj, exists, pre_members, pre_payload, requested,
                       refreshes=True)
        check_discriminates_membership(obj, pre_members, pre_payload, requested)
        check_discriminates_payload(obj, pre_members, pre_payload, requested)
        cases += 1

    print("G-AX OK: real sync_to_async reproduces the immediate form's "
          "delivered result AND both of its effects (membership + payload, "
          "including the locate-vs-refresh payload asymmetry) for acreate / "
          "aget_or_create / aupdate_or_create over %d randomized cases; the "
          "no-attach pre-patch shape is rejected on membership and a refresh "
          "form that runs the locate immediate form is rejected on payload."
          % cases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
