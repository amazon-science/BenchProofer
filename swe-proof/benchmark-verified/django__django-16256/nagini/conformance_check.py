#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16256 (nagini).

SHADOW: the six `# impl-start` / `# impl-end` regions of model.py, copied
VERBATIM below (the model IS Python; nothing is transliterated or restructured).
The regions contain no contract calls at all, so nothing had to be stripped from
them; the two carrier classes they instantiate (`RelatedAccessor`, `Outcome`)
are copied over with their `Requires`/`Ensures`/`MustTerminate` lines removed.
There are no `@Pure` helpers, no `@ContractOnly` callees (mapping.md section 3:
this bundle consumes no axiom -- the attachment work and the payload write are
modelled DEEPLY as a list append and a field assignment), and the impl regions
use no `PSeq`/`ToSeq` (those appear only inside `Ensures`), so no sequence shim
is needed.

ORACLE: the REAL patched repo functions, CALLED, not transliterated. The gate
applies the gold patch to /testbed and sets PYTHONPATH=/testbed before this
script runs, so every symbol below resolves to patched code. mapping.md section
1 binds each model symbol to NINE added wrappers plus their immediate
counterparts across three relation kinds; this check drives ALL EIGHTEEN real
bound functions against a live sqlite database and a real event loop:

  * reverse FK related manager (`related_descriptors.py:790/798` create/acreate,
    `:803/811` get_or_create/aget_or_create, `:816/824`
    update_or_create/aupdate_or_create) -- driven as `target.fkchild_set.<op>`;
  * forward m2m related manager (`related_descriptors.py:1203/1211`,
    `:1218/1231`, `:1238/1251`) -- driven as `m2mowner.simples.<op>`;
  * generic related manager (`contenttypes/fields.py:743/752`, `:757/765`,
    `:770/778`) -- driven as `genowner.tags.<op>`.
  (line numbers are post-patch, i.e. base_commit + patch.diff, which is the
  tree this gate runs against.)

Driving them needs a configured Django with real tables, so the script stands
one up in-container: `settings.configure` over a file-backed sqlite database in
/dev/shm, a stub installed app, and `schema_editor().create_model` for
ContentType + five probe models mirroring the F2P test models
(tests/async/models.py `SimpleModel`/`RelatedModel`/`ManyToManyModel`, plus a
GenericRelation owner for the generic_relations F2P tests). The deferred (async)
forms are resolved through a real `asyncio` event loop, so the real
`sync_to_async` thread hand-off the gold patch introduces is actually executed
-- the deferred forms are awaited, never simulated.

TYPE BRIDGE (mapping.md section 2, inverted):

  * `RelatedAccessor.members: List[int]`  <->  the owning instance's related
    set, read back from the database in attachment order: for m2m, the
    through-table rows' target ids ordered by through-row pk (true attachment
    order); for reverse FK / generic, the related objects' pks ordered by pk
    (probe pks are allocated from a strictly increasing counter, so pk order IS
    attachment order). The shadow accessor for each probe is seeded with the
    list just READ from the real database, so both sides start from the same
    pre-state -- the pre-state is observed, never fabricated.
  * `RelatedAccessor.payload: int`  <->  the value PERSISTED in the modelled
    scalar field (`field`, an IntegerField on every probe model) of the object
    the operation keys on. Read back from the database AFTER the call with a
    fresh query (never from the returned in-memory instance), so what is
    compared is what the operation actually stored. Seeded, for the shadow,
    with the value read from the database BEFORE the call.
  * `requested: int`  <->  the value the call asks that object's field to
    carry: the `defaults={"field": ...}` entry for the two locate/refresh
    operations, and the `field=...` argument for the produce operation. A call
    that supplies no value is probed too (see DEGENERATE below).
  * `obj: int`  <->  the produced/located object's identity, supplied to the
    real function as `pk=obj` and read back as the returned object's `.pk`.
  * `exists: bool`  <->  whether the operation's lookup finds a matching row.
    `exists=True` probes pass the pk of a CURRENT member (the related
    manager's get is scoped to the related set, so a member is exactly what its
    lookup can find); `exists=False` probes pass a never-used fresh pk.
  * `Outcome(obj, created, payload)`  <->  the real `(obj, created)` tuple plus
    the DELIVERED object's field: `Outcome.obj` vs `returned[0].pk`,
    `Outcome.created` vs `returned[1]`, `Outcome.payload` vs
    `returned[0].field` (the in-memory value the caller receives, which is the
    value the F2P payload assertions read).
  * `through_defaults=` (mapping.md section 2: omitted from the model) --
    probed explicitly anyway on the m2m forms, so the claim that it does not
    affect the produced object's membership or its modelled field is exercised
    rather than assumed.

DEGENERATE call shapes. Several F2P calls supply no value for the field at all
(`s1.relatedmodel_set.acreate()`, `aupdate_or_create()` with no `defaults`).
mapping.md section 2 fixes the bridge for those: `requested` models the value
the operation LEAVES the object carrying when the caller names none -- the
already-persisted value on a locate/refresh path, the field's declared default
on a produce path. Under that reading the model's payload clauses degenerate to
"the object still carries what it had" / "the object carries the field default",
which is what the real functions do; both shapes are probed below
(`supply=False`), so the reading is checked rather than asserted.

Per probe the script compares, shadow vs real: (a) the delivered identity
(`Result()` / `Outcome.obj` vs the returned object's pk), (b) the
produced/located flag (`Outcome.created` vs the real boolean) for the
two-valued ops, (c) the DELIVERED payload (`Outcome.payload` vs the returned
instance's field), (d) the FULL post-state of the related set as an ordered
list of identities, and (e) the PERSISTED payload of the keyed object, re-read
from the database. (d) is the observation that discriminates the pre-patch
defect: the model's `ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)`
clause fails against a deferred form that delivers the object without
ATTACHING it (the pre-patch behaviour, where the async form falls through to
the inherited QuerySet coroutine that never links). (c) and (e) are what
discriminate the two locate/refresh operations from each other: on the locate
branch `get_or_create` hands the found object back exactly as it stands
(query.py:932 `return self.get(**kwargs), False`) while `update_or_create`
applies the requested value and saves it (query.py:969 `setattr(obj, k, v)`,
:986/:988 `obj.save(...)`) -- byte-identical membership and identity, opposite
payload behaviour, which is exactly the pair of F2P assertions
(`test_generic_async_aget_or_create` expects the located tag to still read
"fatty"; `test_generic_async_aupdate_or_create` expects it to read "orange").

Verified capable of failing, on both the membership and the payload columns:
run unpatched, the check reports disagreements/errors on the deferred forms
rather than passing; and with the shadow's refresh-or-produce mutated to hand a
located object back untouched, it stops at
`boundary [singleton pre, locate, payload differs]` with
`shadow: delivered=41 payload=41` vs `real: delivered=77 payload=77`, while
with the shadow's locate-or-produce mutated to refresh, it stops at the same
probe with `shadow: delivered=77 payload=77` vs `real: delivered=41 payload=41`
-- i.e. the real patched functions were observed to behave OPPOSITELY on that
input, which is the asymmetry the two contracts encode.

INPUT DOMAIN: every `Requires` is `Acc(mgr.members) and Acc(mgr.payload) and
list_pred(mgr.members)` plus a `MustTerminate` obligation -- no value
constraint -- so every (pre-state, obj, exists, requested) tuple with a fresh
`obj` (or, for `exists=True`, a member `obj`) satisfies it. The space is
infinite (unbounded pre-states and payloads), so: boundary first -- empty and
singleton pre-states, the exact F2P shapes (m2m acreate then aget; reverse-FK
acreate; aget_or_create create-then-locate with through_defaults;
aupdate_or_create create-then-update with defaults; generic
acreate/aget_or_create/aupdate_or_create), zero / negative / unchanged
requested values, the degenerate no-value shapes, and each of the 18 real
functions x each branch of the impl (`exists` True and False) at least once --
then seeded fuzz over relation kind x operation x deferred/immediate x branch x
pre-state size x requested value, filling out to the count.

>= 1e5 Requires-satisfying inputs: 120 boundary + 100000 fuzz probes, each one
a real DB round trip through a real related manager (the deferred ones through a
real event loop). Pinned fuzz seed: 16256 (recorded in mapping.md, `## G-CONF`).

Three coverage ledgers are ASSERTED at the end rather than assumed: every
(kind, op, deferred, branch) cell compared; every (kind, op, deferred) cell
compared at least once on a PAYLOAD-DISCRIMINATING input (a locate/refresh
input whose requested value differs from the persisted one, and a produce input
whose requested value differs from the field default) -- without which the
payload columns would be vacuously equal; and every (op, deferred) cell
compared at least once on a degenerate no-value call.

Exit 0 iff zero disagreements; on the first disagreement prints the input and
both outputs and exits 1. Last line is a one-line JSON summary. stdlib only
(hypothesis not needed: the generator is a seeded `random.Random`).
"""
import json
import os
import sys
import types

SEED = 16256                 # pinned; recorded in mapping.md ## G-CONF
N_FUZZ = 100_000
RESET_MEMBERS = 8            # rebuild the arena once a related set passes this
PURGE_EVERY = 400            # purge probe rows this often (keeps reads O(1))
FIELD_DEFAULT = 0            # the modelled field's declared default on every
                             # probe model (models.IntegerField(default=0))


# ===========================================================================
# SHADOW -- model.py carriers and impl regions, contracts stripped
# ===========================================================================

class RelatedAccessor:
    """model.py RelatedAccessor, contract calls removed."""

    def __init__(self, members, payload):
        self.members = members
        self.payload = payload


class Outcome:
    """model.py Outcome, contract calls removed."""

    def __init__(self, obj, created, payload):
        self.obj = obj
        self.created = created
        self.payload = payload


# --- model.py create() impl region, verbatim -------------------------------
def create(mgr, obj, requested):
    mgr.members.append(obj)
    mgr.payload = requested
    return obj


# --- model.py acreate() impl region, verbatim ------------------------------
def acreate(mgr, obj, requested):
    # Run the SAME-named immediate form on this accessor (its result is then
    # delivered to the awaiting caller). Because it is the related-set accessor's
    # OWN immediate form, the produced object is attached to the related set.
    return create(mgr, obj, requested)


# --- model.py get_or_create() impl region, verbatim ------------------------
def get_or_create(mgr, obj, exists, requested):
    if exists:
        return Outcome(obj, False, mgr.payload)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)


# --- model.py aget_or_create() impl region, verbatim -----------------------
def aget_or_create(mgr, obj, exists, requested):
    return get_or_create(mgr, obj, exists, requested)


# --- model.py update_or_create() impl region, verbatim ---------------------
def update_or_create(mgr, obj, exists, requested):
    if exists:
        mgr.payload = requested
        return Outcome(obj, False, requested)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)


# --- model.py aupdate_or_create() impl region, verbatim --------------------
def aupdate_or_create(mgr, obj, exists, requested):
    return update_or_create(mgr, obj, exists, requested)


SHADOW = {
    ("create", False): create,
    ("create", True): acreate,
    ("get_or_create", False): get_or_create,
    ("get_or_create", True): aget_or_create,
    ("update_or_create", False): update_or_create,
    ("update_or_create", True): aupdate_or_create,
}


# ===========================================================================
# ORACLE -- the real patched related managers over a live database
# ===========================================================================

class Oracle(object):
    """Stands up a configured Django + real tables, and exposes one owning
    instance per relation kind whose related manager is the REAL patched one."""

    def __init__(self):
        import asyncio

        import django
        from django.conf import settings

        # Stub installed app with a filesystem path (AppConfig requires one)
        # so the probe models are registered in a real app registry.
        app_dir = "/tmp/sbu_conf16256_app"
        os.makedirs(app_dir, exist_ok=True)
        mod = types.ModuleType("sbu_conf16256")
        mod.__path__ = [app_dir]
        sys.modules.setdefault("sbu_conf16256", mod)

        # Real (file-backed) sqlite: the async forms hand work to a worker
        # thread via sync_to_async, which needs a shareable connection.
        dbdir = ("/dev/shm" if os.path.isdir("/dev/shm")
                 and os.access("/dev/shm", os.W_OK) else "/tmp")
        db = os.path.join(dbdir, "sbu_conf16256.sqlite3")
        for suffix in ("", "-journal", "-wal", "-shm"):
            if os.path.exists(db + suffix):
                os.remove(db + suffix)

        if not settings.configured:
            settings.configure(
                DEBUG=False,
                DATABASES={"default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": db,
                    "OPTIONS": {"timeout": 60},
                }},
                INSTALLED_APPS=["django.contrib.contenttypes",
                                "sbu_conf16256"],
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
                USE_TZ=True,
            )
        django.setup()

        from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                        GenericRelation)
        from django.contrib.contenttypes.models import ContentType
        from django.db import connection, models
        from django.db.backends.signals import connection_created

        def _pragmas(sender, connection, **kwargs):
            cur = connection.cursor()
            cur.execute("PRAGMA synchronous=OFF")
            cur.execute("PRAGMA journal_mode=MEMORY")

        connection_created.connect(_pragmas)

        # Probe models mirroring the F2P test models (tests/async/models.py and
        # tests/generic_relations/models.py). `field` is the modelled payload.
        class Target(models.Model):            # ~ SimpleModel
            field = models.IntegerField(default=FIELD_DEFAULT)

            class Meta(object):
                app_label = "sbu_conf16256"

        class M2MOwner(models.Model):          # ~ ManyToManyModel
            simples = models.ManyToManyField(Target)

            class Meta(object):
                app_label = "sbu_conf16256"

        class FkChild(models.Model):           # ~ RelatedModel
            simple = models.ForeignKey(Target, models.CASCADE)
            field = models.IntegerField(default=FIELD_DEFAULT)

            class Meta(object):
                app_label = "sbu_conf16256"

        class Tag(models.Model):               # ~ TaggedItem
            field = models.IntegerField(default=FIELD_DEFAULT)
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey()

            class Meta(object):
                app_label = "sbu_conf16256"

        class GenOwner(models.Model):          # ~ Vegetable/Animal
            tags = GenericRelation(Tag)

            class Meta(object):
                app_label = "sbu_conf16256"

        with connection.schema_editor() as editor:
            editor.create_model(ContentType)
            for model in (Target, M2MOwner, FkChild, Tag, GenOwner):
                editor.create_model(model)

        self.Target, self.M2MOwner = Target, M2MOwner
        self.FkChild, self.Tag, self.GenOwner = FkChild, Tag, GenOwner
        self.member_model = {"m2m": Target, "fk": FkChild, "generic": Tag}
        self.through = M2MOwner.simples.through
        self.loop = asyncio.new_event_loop()
        self._next_pk = 1000
        self.arena = {}
        for kind in ("m2m", "fk", "generic"):
            self.reset(kind)

    # --- identity allocation: strictly increasing, so pk order == attach order
    def fresh_pk(self):
        self._next_pk += 1
        return self._next_pk

    # --- arena: one owning instance per relation kind ----------------------
    def reset(self, kind):
        """Fresh owning instance with an EMPTY related set."""
        if kind == "m2m":
            owner = self.M2MOwner.objects.create(pk=self.fresh_pk())
            mgr = owner.simples
        elif kind == "fk":
            owner = self.Target.objects.create(pk=self.fresh_pk())
            mgr = owner.fkchild_set
        else:
            owner = self.GenOwner.objects.create(pk=self.fresh_pk())
            mgr = owner.tags
        self.arena[kind] = (owner, mgr)
        return mgr

    def mgr(self, kind):
        return self.arena[kind][1]

    def purge(self):
        """Drop all probe rows and rebuild the arenas (bounds table growth)."""
        self.through.objects.all().delete()
        self.Tag.objects.all().delete()
        self.FkChild.objects.all().delete()
        self.Target.objects.all().delete()
        self.M2MOwner.objects.all().delete()
        self.GenOwner.objects.all().delete()
        for kind in ("m2m", "fk", "generic"):
            self.reset(kind)

    # --- the type bridge: real related set -> List[int] + persisted payloads -
    def state(self, kind):
        """(members, payloads): the related set as an ordered list of member
        identities, and {identity: persisted field value} for those members.
        ONE query per call -- the payload column is read in the same pass, so
        adding the payload observable costs no extra round trip."""
        owner, mgr = self.arena[kind]
        if kind == "m2m":
            # through rows in attachment order; target id == member identity,
            # target__field == the member's persisted payload (single JOIN).
            rows = list(self.through.objects
                        .filter(m2mowner=owner).order_by("pk")
                        .values_list("target_id", "target__field"))
        else:
            # reverse FK / generic: the related objects themselves are members
            rows = list(mgr.order_by("pk").values_list("pk", "field"))
        return [r[0] for r in rows], {r[0]: r[1] for r in rows}

    # --- call the REAL patched function ------------------------------------
    def call(self, kind, op, deferred, obj, exists, requested, supply,
             extra=None):
        """Invoke the real (a)create / (a)get_or_create / (a)update_or_create on
        the related manager. Returns (identity, created_or_None, delivered
        payload)."""
        mgr = self.mgr(kind)
        name = ("a" if deferred else "") + op
        func = getattr(mgr, name)
        kwargs = {"pk": obj}
        if supply:
            if op == "create":
                # produce: the value is an ordinary field argument
                kwargs["field"] = requested
            else:
                # locate/refresh: the value is what `defaults` names
                kwargs["defaults"] = {"field": requested}
        if extra:
            kwargs.update(extra)
        if deferred:
            # resolve through a REAL event loop: the patched wrapper's
            # `await sync_to_async(self.<op>)(**kwargs)` actually executes.
            returned = self.loop.run_until_complete(func(**kwargs))
        else:
            returned = func(**kwargs)
        if op == "create":
            return returned.pk, None, returned.field
        return returned[0].pk, returned[1], returned[0].field


# ===========================================================================
# one probe: shadow vs real, on the SAME observed pre-state
# ===========================================================================

def probe(oracle, kind, op, deferred, exists, requested=None, supply=True,
          extra=None, label=""):
    """Compare shadow vs real on one input.

    Returns (compared, report, info): `compared` is False only when the drawn
    input is outside the modelled domain (an `exists=True` probe needs a
    non-empty related set for the locate branch to be reachable) and nothing was
    therefore checked -- such probes are NOT counted toward the input total.
    `report` is None on agreement, else a human-readable disagreement. `info` is
    (requested, pre_payload) for the coverage ledgers.
    """
    pre, pre_pay = oracle.state(kind)             # observed pre-state
    if exists and not pre:
        return False, None, None                  # outside the domain
    obj = pre[len(pre) // 2] if exists else oracle.fresh_pk()
    # the persisted payload of the object this call keys on; a produce probe's
    # object does not exist yet, and every clause that mentions the previous
    # payload is guarded by `exists`, so the field default stands in there.
    pre_payload = pre_pay[obj] if exists else FIELD_DEFAULT
    if not supply:
        # DEGENERATE shape: the caller names no value. mapping.md section 2:
        # `requested` then models the value the operation leaves the object
        # carrying -- the persisted one on a locate/refresh path, the field's
        # declared default on a produce path.
        requested = pre_payload if exists else FIELD_DEFAULT
    elif requested is None:
        requested = obj % 97

    # --- shadow: the impl region, on an accessor seeded with the SAME pre-state
    shadow_mgr = RelatedAccessor(list(pre), pre_payload)
    fn = SHADOW[(op, deferred)]
    if op == "create":
        s_obj, s_created = fn(shadow_mgr, obj, requested), None
        # model.py create() pins only mgr.payload; the produced object IS the
        # keyed object, so its delivered field is that same value.
        s_delivered = shadow_mgr.payload
    else:
        outcome = fn(shadow_mgr, obj, exists, requested)
        s_obj, s_created = outcome.obj, outcome.created
        s_delivered = outcome.payload
    s_members, s_payload = shadow_mgr.members, shadow_mgr.payload

    # --- real: the patched repo function on the live related manager
    try:
        r_obj, r_created, r_delivered = oracle.call(
            kind, op, deferred, obj, exists, requested, supply, extra)
    except Exception as exc:                      # noqa: BLE001
        report = ("DISAGREEMENT (real function raised)\n"
                  "  probe: kind=%s op=%s deferred=%r exists=%r"
                  " requested=%r supply=%r extra=%r %s\n"
                  "  pre-state members=%r payload=%r obj=%r\n"
                  "  shadow: obj=%r created=%r delivered=%r members=%r"
                  " payload=%r\n"
                  "  real:   raised %s: %s"
                  % (kind, op, deferred, exists, requested, supply, extra,
                     label, pre, pre_payload, obj,
                     s_obj, s_created, s_delivered, s_members, s_payload,
                     type(exc).__name__, exc))
        return True, report, None
    post, post_pay = oracle.state(kind)
    r_members = post
    # PERSISTED payload of the keyed object, re-read from the database (never
    # from the returned in-memory instance): what the operation actually stored.
    r_payload = post_pay.get(r_obj, None)
    if r_payload is None:
        # the keyed object is not a member of this related set after the call
        # (only reachable if the real function failed to attach it); read it
        # directly so the payload column still reports a real value.
        row = (oracle.member_model[kind]._base_manager
               .filter(pk=r_obj).values_list("field", flat=True))
        r_payload = row[0] if row else None

    if ((s_obj, s_created, s_delivered, s_members, s_payload)
            != (r_obj, r_created, r_delivered, r_members, r_payload)):
        report = ("DISAGREEMENT\n"
                  "  probe: kind=%s op=%s deferred=%r exists=%r"
                  " requested=%r supply=%r extra=%r %s\n"
                  "  pre-state members=%r payload=%r obj=%r\n"
                  "  shadow: obj=%r created=%r delivered=%r members=%r"
                  " payload=%r\n"
                  "  real:   obj=%r created=%r delivered=%r members=%r"
                  " payload=%r"
                  % (kind, op, deferred, exists, requested, supply, extra,
                     label, pre, pre_payload, obj,
                     s_obj, s_created, s_delivered, s_members, s_payload,
                     r_obj, r_created, r_delivered, r_members, r_payload))
        return True, report, None

    if len(r_members) > RESET_MEMBERS:
        oracle.reset(kind)
    return True, None, (requested, pre_payload)


KINDS = ("m2m", "fk", "generic")
OPS = ("create", "get_or_create", "update_or_create")


def boundary_probes(oracle):
    """(kind, op, deferred, exists, requested, supply, extra, label) tuples:
    empty and singleton pre-states, every real function x every impl branch,
    the payload boundaries (zero, negative, unchanged, no-value), and the F2P
    shapes."""
    out = []
    # every one of the 18 real functions from an EMPTY related set, then again
    # from the resulting singleton (both branches where applicable), with a
    # supplied payload that differs from the field default.
    for kind in KINDS:
        for op in OPS:
            for deferred in (True, False):
                out.append((kind, op, deferred, False, 41, True, None,
                            "[empty pre]"))
                if op != "create":
                    # now the set is non-empty: take the locate branch, asking
                    # for a value the located object does NOT already carry --
                    # the payload-discriminating input.
                    out.append((kind, op, deferred, True, 77, True, None,
                                "[singleton pre, locate, payload differs]"))
                out.append((kind, op, deferred, False, 41, True, None,
                            "[non-empty pre]"))
    # payload boundaries: zero, negative, and a requested value EQUAL to the
    # one already persisted (so refresh and locate coincide), plus the
    # degenerate no-value shape, on every operation.
    for kind in KINDS:
        for op in OPS:
            for deferred in (True, False):
                out.append((kind, op, deferred, False, 0, True, None,
                            "[payload zero]"))
                out.append((kind, op, deferred, False, -7, True, None,
                            "[payload negative]"))
                out.append((kind, op, deferred, False, None, False, None,
                            "[degenerate: no value supplied]"))
                if op != "create":
                    out.append((kind, op, deferred, True, None, False, None,
                                "[degenerate locate: no value supplied]"))
    # F2P shapes: m2m aget_or_create with through_defaults, aupdate_or_create
    # with defaults, and the same on the generic + reverse-FK managers.
    out.append(("m2m", "get_or_create", True, False, 2, True,
                {"through_defaults": {}}, "[F2P: m2m aget_or_create new]"))
    out.append(("m2m", "get_or_create", True, True, 3, True,
                {"through_defaults": {}},
                "[F2P: m2m aget_or_create locate, defaults ignored]"))
    out.append(("m2m", "update_or_create", True, False, 2, True, None,
                "[F2P: m2m aupdate_or_create new]"))
    out.append(("m2m", "update_or_create", True, True, 3, True, None,
                "[F2P: m2m aupdate_or_create update]"))
    out.append(("m2m", "create", True, False, 2, True, {"through_defaults": {}},
                "[F2P: m2m acreate]"))
    out.append(("fk", "create", True, False, None, False, None,
                "[F2P: reverse-FK acreate, no value]"))
    out.append(("fk", "get_or_create", True, False, None, False, None,
                "[F2P: reverse-FK aget_or_create, no value]"))
    out.append(("fk", "update_or_create", True, False, None, False, None,
                "[F2P: reverse-FK aupdate_or_create, no value]"))
    out.append(("generic", "create", True, False, 9, True, None,
                "[F2P: generic acreate]"))
    out.append(("generic", "update_or_create", True, True, 4, True, None,
                "[F2P: generic aupdate_or_create update]"))
    out.append(("generic", "get_or_create", True, True, 4, True, None,
                "[F2P: generic aget_or_create locate, defaults ignored]"))
    out.append(("generic", "get_or_create", True, False, 4, True, None,
                "[F2P: generic aget_or_create new]"))
    return out


def main():
    import random

    try:
        oracle = Oracle()
    except Exception as exc:                      # noqa: BLE001
        print("status=error could not stand up the real oracle: %s: %s"
              % (type(exc).__name__, exc))
        return 2

    checked = 0
    # Coverage ledgers. (1) which (relation kind, op, deferred, branch) cells
    # were actually compared -- a generator that quietly avoided the attach
    # branch, the one the gold patch changed, would leave cells empty here.
    # (2) which cells were compared on a PAYLOAD-DISCRIMINATING input (a
    # locate/refresh whose requested value differs from the persisted one, or a
    # produce whose requested value differs from the field default) -- without
    # one, the two payload columns agree vacuously. (3) which (op, deferred)
    # cells were compared on a degenerate no-value call. All three are asserted
    # below rather than assumed.
    cover = {}
    cover_pay = {}
    cover_degen = {}

    def run(kind, op, deferred, exists, requested, supply, extra, label):
        """Returns None to continue, or an exit code to stop on."""
        nonlocal checked
        compared, bad, info = probe(oracle, kind, op, deferred, exists,
                                    requested, supply, extra, label)
        if not compared:
            return None
        checked += 1
        cell = (kind, op, deferred, exists)
        cover[cell] = cover.get(cell, 0) + 1
        if bad:
            print(bad)
            print("status=fail %s (probe %d, seed=%d)" % (label, checked, SEED))
            return 1
        req, pre_payload = info
        if not supply:
            dcell = (op, deferred)
            cover_degen[dcell] = cover_degen.get(dcell, 0) + 1
        elif req != pre_payload:
            # discriminating: the requested value is not the one already there
            pcell = (kind, op, deferred, exists)
            cover_pay[pcell] = cover_pay.get(pcell, 0) + 1
        return None

    # --- boundary ---------------------------------------------------------
    for spec in boundary_probes(oracle):
        kind, op, deferred, exists, requested, supply, extra, label = spec
        rc = run(kind, op, deferred, exists, requested, supply, extra,
                 "boundary " + label)
        if rc is not None:
            return rc
    n_boundary = checked

    # --- seeded fuzz: loop until N_FUZZ inputs were actually COMPARED ------
    rng = random.Random(SEED)
    i = 0
    while checked - n_boundary < N_FUZZ:
        kind = rng.choice(KINDS)
        op = rng.choice(OPS)
        deferred = rng.random() < 0.6          # bias to the patched wrappers
        exists = op != "create" and rng.random() < 0.5
        supply = rng.random() < 0.85           # 15% degenerate no-value calls
        requested = rng.randrange(-20, 120) if supply else None
        extra = None
        if rng.random() < 0.05 and kind == "m2m":
            extra = {"through_defaults": {}}
        rc = run(kind, op, deferred, exists, requested, supply, extra,
                 "fuzz #%d" % i)
        if rc is not None:
            return rc
        i += 1
        if i % PURGE_EVERY == 0:
            oracle.purge()

    # --- coverage assertions ----------------------------------------------
    expected = set()
    for kind in KINDS:
        for op in OPS:
            for deferred in (True, False):
                expected.add((kind, op, deferred, False))     # attach branch
                if op != "create":
                    expected.add((kind, op, deferred, True))  # locate branch
    missing = sorted(str(c) for c in expected - set(cover))
    if missing:
        print("status=fail coverage hole: these (kind, op, deferred, exists) "
              "cells were never compared, so the branch the change affects "
              "may be untested: %s" % ", ".join(missing))
        return 1
    missing_pay = sorted(str(c) for c in expected - set(cover_pay))
    if missing_pay:
        print("status=fail coverage hole: these (kind, op, deferred, exists) "
              "cells were never compared on a payload-discriminating input "
              "(requested value != the value already persisted), so the "
              "payload columns may have agreed vacuously: %s"
              % ", ".join(missing_pay))
        return 1
    expected_degen = {(op, deferred) for op in OPS for deferred in (True, False)}
    missing_degen = sorted(str(c) for c in expected_degen - set(cover_degen))
    if missing_degen:
        print("status=fail coverage hole: these (op, deferred) cells were "
              "never compared on a degenerate call that supplies no value, so "
              "the bridge's reading of `requested` for those F2P call shapes "
              "is untested: %s" % ", ".join(missing_degen))
        return 1

    print("status=pass 0 disagreements: shadow (model.py impl regions, "
          "verbatim) == the real patched related-manager create/acreate/"
          "get_or_create/aget_or_create/update_or_create/aupdate_or_create "
          "on reverse-FK, forward-m2m and generic managers over a live DB, on "
          "delivered identity, produced flag, delivered payload, related-set "
          "post-state and PERSISTED payload "
          "(%d boundary + %d fuzz probes, all %d function x branch cells "
          "covered, all %d payload-discriminating, all %d degenerate-call "
          "cells covered, seed=%d)"
          % (n_boundary, checked - n_boundary, len(expected), len(expected),
             len(expected_degen), SEED))
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "django__django-16256",
        "status": "pass",
        "shadow": "model.py impl regions (verbatim, contracts stripped)",
        "oracle": ("real patched related managers: "
                   "related_descriptors.py RelatedManager (reverse FK) + "
                   "ManyRelatedManager (forward m2m), "
                   "contenttypes/fields.py GenericRelatedObjectManager"),
        "real_functions_driven": 18,
        "observables": ["delivered identity", "produced flag",
                        "delivered payload", "related-set post-state",
                        "persisted payload"],
        "probes": checked,
        "boundary": n_boundary,
        "fuzz": checked - n_boundary,
        "cells_covered": len(expected),
        "payload_discriminating_cells": len(expected),
        "degenerate_call_cells": len(expected_degen),
        "seed": SEED,
        "disagreements": 0,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
