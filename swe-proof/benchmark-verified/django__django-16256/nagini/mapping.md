# mapping.md — django__django-16256

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 76e37513e22f4d9a01c7f15eee36fe44388e6670`, states the type
abstraction, and gives the provenance of the one library primitive the deep
model relies on.

Repo files under change:
- `django/db/models/fields/related_descriptors.py`
- `django/contrib/contenttypes/fields.py`

## 1. Symbol ↔ repo binding

The gold patch adds, to each related-manager factory, an async wrapper next to
each existing synchronous object-producing method, of the uniform shape

```python
async def a<op>(self, **kwargs):
    return await sync_to_async(self.<op>)(**kwargs)
a<op>.alters_data = True
```

where `<op> ∈ {create, get_or_create, update_or_create}` and `self.<op>` is the
**related manager's own** synchronous method (the one that performs the
relation-specific work). The model abstracts the related manager to a minimal
`RelatedAccessor` carrying the two touched data — the related set (`members`)
and the persisted value of the keyed object's modelled scalar field
(`payload`) — and abstracts each `**kwargs`-keyed produced-or-located object to
an integer identity `obj` plus the value the call asks it to carry
(`requested`).

Line numbers below are **post-patch** (`base_commit` + `patch.diff`), which is
the tree the modelled functions live in and the reference for what is TRUE of
them; the three synchronous methods also exist at `base_commit` (unchanged by
the patch, shifted two lines by its import hunk: `related_descriptors.py:788/
796/804` and `:1186/1194/1207`, `contenttypes/fields.py:741/750/758`).

| model.py symbol | repo symbol (file:line @ base_commit + patch.diff) | role |
|---|---|---|
| `create(mgr, obj, requested)` | the related-manager `create` overrides: `related_descriptors.py:790` (reverse FK), `:1203` (forward m2m); `contenttypes/fields.py:743` (generic) | immediate "produce" form: produces the object **carrying the requested field values** and **attaches** it (the m2m one calls `self.add(new_obj, ...)`; FK/generic set the relation fields, so the object is a member of the related set) |
| `acreate(mgr, obj, requested)` | the new `acreate` wrappers: `related_descriptors.py:798` (reverse FK) + `:1211` (forward m2m); `contenttypes/fields.py:752` (generic) | deferred "produce" form; `return await sync_to_async(self.create)(**kwargs)` |
| `get_or_create(mgr, obj, exists, requested)` | `related_descriptors.py:803` (reverse FK), `:1218` (forward m2m); `contenttypes/fields.py:757` (generic), each delegating to `QuerySet.get_or_create` (`query.py:922`) | immediate locate-or-produce; attaches **only when created**, and hands an already-present object back **exactly as it stands** (`query.py:932` `return self.get(**kwargs), False` — `defaults` is consumed only on the create path, `query.py:934-941`) |
| `aget_or_create(mgr, obj, exists, requested)` | new `aget_or_create` wrappers: `related_descriptors.py:811` + `:1231`; `contenttypes/fields.py:765` | deferred locate-or-produce; `return await sync_to_async(self.get_or_create)(**kwargs)` |
| `update_or_create(mgr, obj, exists, requested)` | `related_descriptors.py:816` (reverse FK), `:1238` (forward m2m); `contenttypes/fields.py:770` (generic), each delegating to `QuerySet.update_or_create` (`query.py:953`) | immediate refresh-or-produce; attaches **only when created**, and applies the requested values to an already-present object and **saves** them (`query.py:969` `setattr(obj, k, v)`, `:986`/`:988` `obj.save(...)`) |
| `aupdate_or_create(mgr, obj, exists, requested)` | new `aupdate_or_create` wrappers: `related_descriptors.py:824` + `:1251`; `contenttypes/fields.py:778` | deferred refresh-or-produce; `return await sync_to_async(self.update_or_create)(**kwargs)` |
| `RelatedAccessor.members` | the related set the manager governs (m2m through-table rows; the FK/content-type pointer on the produced object) | first touched field — membership of the produced object in the owning instance's related set |
| `RelatedAccessor.payload` | the value **persisted** in the keyed object's modelled scalar field (`SimpleModel.field` / `RelatedModel`'s inherited field / `TaggedItem.tag` in the F2P tests) | second touched field — what the object the operation keys on ends up carrying in the database |
| `Outcome(obj, created, payload)` | the `(obj, created)` tuple returned by `get_or_create` / `update_or_create`, plus the returned object's field value | delivered object + produced/located flag + the field value the caller receives |

The six repo wrappers are the **same** delegation skeleton at six sites (three
operations × {reverse-FK manager, forward-m2m manager} in
`related_descriptors.py`, plus the three generic-relation wrappers in
`contenttypes/fields.py` — nine added methods total). The model contracts the
three distinct *operations* once each (`acreate`, `aget_or_create`,
`aupdate_or_create`); the per-direction / per-relation-kind variants are the
identical skeleton and are covered by the same three contracts (refinement.md
§A notes the per-site repetition).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| related manager (reverse-FK / forward-m2m / generic) | `RelatedAccessor` with `members` + `payload` | the manager's identity collapses to its two observable touched data: which objects are attached to the owning instance, and what the object the operation keys on ends up persisting |
| the related set (m2m through rows, or the set of objects whose FK / content-type+object-id point at the owning instance) | `members: List[int]` of object identities | membership ↔ presence of the identity in `members`; attaching an object ↔ `members.append(obj)` |
| the value persisted in the keyed object's non-key field (`SimpleModel.field`, `TaggedItem.tag`) | `payload: int` on the accessor | one scalar field stands for the `defaults=`-writable content of the keyed object; the DB value ↔ `mgr.payload`, and "the operation writes the field and saves" ↔ `mgr.payload = requested` |
| the field values the call asks the object to carry (`field=3`, `defaults={"tag": "orange"}`) | `requested: int` parameter | the requested content collapses to one scalar; "apply the caller's values" ↔ `payload == requested`, "leave the object untouched" ↔ `payload == Old(payload)` |
| a call that supplies NO field values (`relatedmodel_set.acreate()`, `...aupdate_or_create(id=1)`) | `requested` := the value the operation leaves the object carrying — the pre-existing persisted value on a locate/refresh with nothing to apply, the field default on a produce | the model's `requested` is the *resulting* requested content, so a no-`defaults` refresh instantiates the unconditional payload clause with `requested = Old(payload)` and stays TRUE of the real callee; probed explicitly in `conformance_check.py` (`supply=False` shape) rather than argued |
| a produced/located object keyed by `**kwargs` | `obj: int` (its identity) | the F2P tests observe the produced object's membership and its field value via the identity it is given |
| whether `get_or_create`/`update_or_create` find an existing object | `exists: bool` parameter | `exists=True` ↔ the get/lookup found a row (no create); `exists=False` ↔ a new object is produced (and, on the related manager, attached) |
| `(obj, created)` return tuple, and the returned object's field value | `Outcome(obj, created, payload)` | `Outcome.obj` ↔ the object, `Outcome.created` ↔ the boolean, `Outcome.payload` ↔ `getattr(obj, field)` on the object the caller receives (distinct from `mgr.payload`, which is what the DB holds: an unsaved write would separate them) |
| `async def` + `await` + `sync_to_async(self.<op>)(**kwargs)` | a plain call to the modelled immediate form `<op>(mgr, ...)` | `await sync_to_async(f)(**kwargs)` delivers EXACTLY `f(**kwargs)` and reproduces its side effect (§3); the awaitable/threadpool machinery is unobservable at this granularity, so the deferred form is the immediate form's result + effect |
| `through_defaults=None` keyword (forward-m2m variants) | omitted | it addresses the through-ROW's own fields, a different object from the one the model's `payload` tracks; it affects neither whether the object is attached nor the keyed object's persisted field, and the F2P membership/`acount`/field observations are independent of it. `defaults=` is NOT omitted — it is the source of `requested` (row above), and both keywords are passed for real in the G-CONF probes |
| `.alters_data = True` flag set on each wrapper | omitted | a template-safety marker; it does not affect the produced object or its membership |
| the call COMPLETES: `await sync_to_async(self.<op>)(**kwargs)` resolves — the immediate form is bounded, loop-free work run in a worker thread, and the awaitable delivers its result | `Requires(MustTerminate(3))` on the deferred forms, `MustTerminate(2)` on the immediate forms, measure 1 on the carrier constructors | the real wrappers always resolve, so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering. Nagini verifies partial correctness by default (no termination proof required), so without this obligation a non-terminating body (`while b: Invariant(True)`) satisfies every `Ensures` vacuously while a real wrapper that hangs would time out every awaiting F2P test — the G-PANEL-1 witness class this obligation closes. |

## 3. The one library primitive (checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** and **no A-reference deep model
validated against a separate stdlib oracle**: the changed behaviour — a deferred
form must run the accessor's OWN immediate form, so a newly-produced object is
attached AND the operation's own payload discipline (locate hands back
untouched, refresh writes and saves) is what happens — is modelled **deeply** (a
list append plus a payload write in `create`/`get_or_create`/
`update_or_create`, with each `a*` wrapper's contract tied to its immediate
counterpart's exact post-state).

The single library fact the abstraction in §2 rests on is the behaviour of the
real `asgiref.sync.sync_to_async` the gold patch introduces
(`from asgiref.sync import sync_to_async`, added to both changed files):

> `await sync_to_async(f)(**kwargs)` runs `f(**kwargs)` in a thread and resolves
> to its return value, reproducing both the return value and any side effect of
> `f`.

`axiom_check.py` executes the **real** `sync_to_async` (asgiref 3.x, present in
the eval image) against representative immediate forms and asserts (a) the
deferred result equals the immediate result, (b) the deferred call reproduces
the immediate form's membership effect (the produced object is attached) and
(c) it reproduces the immediate form's PAYLOAD effect, including the asymmetry
between the two locate forms (locate-or-produce leaves an already-present
object's payload alone; refresh-or-produce overwrites it). It also confirms the
check discriminates on both dimensions: the pre-patch shape (deliver the object,
delegate to a bare produce that never attaches) violates the membership fact,
and a refresh form that delegates to the locate form violates the payload fact.
Provenance: asgiref docs, `asgiref/sync.py` `SyncToAsync.__call__`
(https://asgiref.readthedocs.io/en/latest/sync.html). stdlib + asgiref only.

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: does the MODEL agree with the
REAL patched repository code? (G-VERIFY checks impl-vs-spec, G-PBT checks
spec strength; neither looks at the repository.)

**Shadow.** All six `# impl-start` / `# impl-end` regions of `model.py`, copied
VERBATIM. The regions contain no contract calls, so nothing was stripped from
them; the `RelatedAccessor` / `Outcome` carriers they instantiate are copied with
their `Requires`/`Ensures`/`MustTerminate` lines removed. No `@Pure` helpers, no
`@ContractOnly` callees (§3: this bundle consumes no axiom), and no `PSeq`/
`ToSeq` inside the impl regions, so no sequence shim is needed.

**Oracle.** The real patched functions, **called** (not transliterated). All
**18** repo functions §1 binds — `create`/`acreate`, `get_or_create`/
`aget_or_create`, `update_or_create`/`aupdate_or_create` on each of the reverse-FK
`RelatedManager` and forward-m2m `ManyRelatedManager`
(`related_descriptors.py`) and the `GenericRelatedObjectManager`
(`contenttypes/fields.py`) — are driven against a live sqlite database stood up
in-container (`settings.configure` + `schema_editor().create_model` over probe
models mirroring the F2P test models). The deferred forms are awaited on a real
`asyncio` event loop, so the real `sync_to_async` hand-off the gold patch
introduces actually executes rather than being simulated.

**Type bridge (§2 inverted).** `RelatedAccessor.members: List[int]` ↔ the
owning instance's related set read back from the DB in attachment order (m2m:
through-row target ids ordered by through pk; FK/generic: related pks, allocated
from a strictly increasing counter so pk order is attachment order);
`RelatedAccessor.payload: int` ↔ the value **re-read from the database** for the
keyed object's modelled field (so an in-memory write that was never saved does
NOT count as a payload effect); `requested: int` ↔ the field value the call
supplies (`field=requested` for the produce form, `defaults={"field":
requested}` for the two locate/refresh forms); `obj: int` ↔ the object identity,
passed as `pk=obj` and read back as `.pk`; `exists: bool` ↔ whether the lookup
finds a row (`True` probes pass a current member's pk, `False` a fresh pk);
`Outcome(obj, created, payload)` ↔ the real `(obj, created)` tuple plus
`getattr(returned_obj, field)`. Each probe seeds the shadow accessor with the
pre-state just **read from the real database** (both members and payload), so
both sides start from the same observed state. `through_defaults=` (omitted from
the model per §2) and `defaults=` (the source of `requested`) are both passed for
real rather than assumed irrelevant, and the no-`defaults` / no-field degenerate
shape of §2 is probed as its own case (`supply=False`).

**Compared per probe:** five observables — delivered identity, produced/located
flag, **delivered payload** (`Outcome.payload`), the FULL ordered post-state of
the related set, and the **persisted payload** re-read from the DB. The last
three are the discriminating observations: the membership clause
`ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)` is what a deferred
form that delivers the object without ATTACHING it violates, and the payload
clauses are what separate the two locate forms, which agree on identity, flag
and membership in every branch.

**Inputs.** 120 boundary probes (empty/singleton pre-states, every one of the 18
real functions × each impl branch, both `requested == pre-payload` and
`requested != pre-payload`, the no-supply degenerate shape, and the exact F2P
shapes) + **100000** seeded fuzz probes over relation kind × operation ×
deferred/immediate × branch × pre-state size × payload relation; the fuzz loop
counts only inputs actually COMPARED, and **three** coverage ledgers fail the
gate if anything went untested: all 30 (kind, op, deferred, branch) cells, all 30
of those cells reached with a payload that DIFFERS from the pre-state payload
(without which the payload comparison could pass vacuously on every probe), and
all 6 (op, deferred) degenerate no-supply cells. A generator that drifted away
from the attach branch, or that only ever asked for the value already stored,
therefore cannot yield a vacuous pass.

**Pinned seed: `SEED = 16256`** (module constant in `conformance_check.py`).

**Capable of failing (verified), on both dimensions.**
*Membership:* run against the UNPATCHED repo the check fails on boundary probe 1:
the real `acreate` resolves to the inherited `QuerySet.acreate`, which creates
the object but never attaches it (`shadow members=[1004]` vs `real members=[]`).
With only `contenttypes/fields.py` patched it fails on the m2m manager; with only
`related_descriptors.py` patched it fails on the generic manager.
*Payload:* against the fully patched repo, two shadows mutated in OPPOSITE
directions each disagree with the real code on the same boundary probe
`[singleton pre, locate, payload differs]` — a shadow whose refresh form hands an
already-present object back untouched reports `delivered=41 payload=41` where the
real `aupdate_or_create` gives `delivered=77 payload=77`, and a shadow whose
locate form refreshes reports `delivered=77 payload=77` where the real
`aget_or_create` gives `delivered=41 payload=41`. So the asymmetric payload
clauses are pinned to the real callee in both directions, not just one.
Exit 0 iff zero disagreements; last stdout line is a JSON summary.
