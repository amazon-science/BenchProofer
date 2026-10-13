# refinement.md — django__django-16256

The operation-by-operation correspondence between `model.py`'s implementation
(the three deferred forms `acreate`/`aget_or_create`/`aupdate_or_create` and the
three immediate forms `create`/`get_or_create`/`update_or_create` they delegate
to) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** when the proof uses the
axiom's `Ensures`, **A-reference** when a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The added deferred forms (the same skeleton at six/nine sites)

The gold patch adds, beside each existing synchronous object-producing method of
each related-manager factory, an async wrapper of the uniform shape

```python
async def a<op>(self, **kwargs):
    return await sync_to_async(self.<op>)(**kwargs)
a<op>.alters_data = True
```

for `<op> ∈ {create, get_or_create, update_or_create}`, in both
`related_descriptors.py` (reverse-FK manager lines 798/811/824 and forward-m2m
manager lines 1211/1231/1251) and `contenttypes/fields.py` (generic manager
lines 752/765/778 — all post-patch line numbers). All nine are the identical
skeleton; the model contracts the three distinct operations once each and the
per-site variants map onto the same three contracts.

The pre-patch defect: there were no such wrappers on the related managers, so
`a<op>` resolved to the QuerySet's async method, which ran the QuerySet's bare
`<op>` — producing the object but **not** running the related manager's own
`<op>`, so a newly-produced object was never attached to the owning instance's
related set.

**Two touched data, not one.** Each `a<op>` must run the SAME-named immediate
form, and the three immediate forms differ along two independent dimensions, so
the model observes both (mapping.md §2):

* **membership** — `create` always attaches; `get_or_create` and
  `update_or_create` attach only what they had to produce;
* **payload**, i.e. what the object the operation keys on ends up carrying —
  `create` gives it the requested values; `get_or_create` hands an
  already-present object back **exactly as it stands** (`QuerySet.get_or_create`
  consumes `defaults` only on the create path: `query.py:932`
  `return self.get(**kwargs), False`, vs `:934-941`); `update_or_create`
  **applies the requested values and saves them** (`query.py:969`
  `setattr(obj, k, v)`, `:986`/`:988` `obj.save(...)`).

On membership the two locate forms are the same shape; on payload they are
opposites. A model that observed membership only would let `aupdate_or_create`
run `get_or_create` — same identity, same flag, same set — and still verify,
which is why the payload legs below (A3b/B2b/C2b) are part of the refinement.

### A.1 `acreate` (model) ↔ `acreate` wrappers (patch)

| # | model.py impl op (`acreate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `mgr: RelatedAccessor` | the bound `self` (the related manager) | R | manager ↔ its two touched data: the related set `members` and the keyed object's persisted field `payload` (mapping.md §2). |
| A2 | params `obj: int`, `requested: int` | the `**kwargs`-keyed object produced, and the field values `**kwargs` asks it to carry | R | object ↔ its identity; requested field content ↔ one scalar (mapping.md §2). |
| A3 | `return create(mgr, obj, requested)` — delegate to the accessor's OWN immediate form (which **attaches**) | `return await sync_to_async(self.create)(**kwargs)` | R + A-reference | the `async`/`await`/`sync_to_async` layer refines to a plain call delivering the immediate form's result + effect: `await sync_to_async(f)(**kwargs)` returns exactly `f(**kwargs)` and reproduces its side effects — checked against the **real** `sync_to_async` by G-AX (mapping.md §3). The load-bearing fidelity point is that the delegate is `self.create` (the related manager's OWN attaching create), not a bare QuerySet create. |
| A3b | `create`'s body `mgr.payload = requested`, pinned by `Ensures(mgr.payload == requested)` | the produced object is saved carrying the `**kwargs` field values (`Model(**kwargs)` + `save()` inside the manager's `create`, e.g. `related_descriptors.py:790` → `super().create(**kwargs)`) | R | "the produced object carries what the caller asked for" ↔ the payload write. Unconditional here because `create` has no locate branch. |
| A4 | `create`'s body `mgr.members.append(obj)` | the related manager's own `create` body (m2m: `self.add(new_obj, ...)`; FK/generic: relation fields set so the object is in the related set) | R | attaching the produced object ↔ list append on `members` (mapping.md §2). `create` is a sibling modelled function, so `acreate` discharges A3 against `create`'s **spec** (not an axiom — it is under spec, per SPEC_GUIDE §3 multi-site). |
| A5 | `Requires(MustTerminate(3))` on the deferred forms / `MustTerminate(2)` on the immediate forms / measure 1 on the carrier constructors | the real wrapper `await sync_to_async(self.<op>)(**kwargs)` COMPLETES: `sync_to_async` runs the bounded, loop-free immediate form in a worker thread and resolves the awaitable with its result — every call answers | R | a total-correctness obligation carried in the preconditions. Nagini checks partial correctness by default, so without it a same-spec impl that spins forever before returning verifies vacuously while its real counterpart never resolves the awaited coroutine — hanging every awaiting F2P test (the recorded G-PANEL-1 weakness class). The obligation adds NO behaviour beyond what the real code already has (the wrappers always resolve), so it cannot exclude a correct impl; the strictly decreasing measures (3 > 2 > 1) let each deferred form delegate to its immediate sibling and the siblings build the carrier objects without leaking their own obligation. |

### A.2 `aget_or_create` (model) ↔ `aget_or_create` wrappers (patch)

| # | model.py impl op (`aget_or_create`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `return get_or_create(mgr, obj, exists, requested)` | `return await sync_to_async(self.get_or_create)(**kwargs)` | R + A-reference | as A3: the deferred form delivers exactly the immediate `get_or_create`'s `(obj, created)` (and the returned object's field value) and reproduces its membership AND payload effects (G-AX). |
| B2 | `get_or_create`: `if exists: return Outcome(obj, False, mgr.payload)` (no attach) `else: members.append(obj); mgr.payload = requested; return Outcome(obj, True, requested)` | the related manager's `get_or_create`: `obj, created = super().get_or_create(...)`; `if created: self.add(obj, ...)`; `return obj, created` | R + I | located ↔ `exists` (set unchanged); produced ↔ `not exists` (attach). The "attach only when created" `if created: self.add(...)` ↔ the `not exists` append branch (mapping.md §2). `(obj, created)` ↔ `Outcome`. |
| B2b | `Implies(exists, mgr.payload == Old(mgr.payload))` and `Implies(exists, Result().payload == Old(mgr.payload))`; `Implies(not exists, ... == requested)` | `QuerySet.get_or_create` (`query.py:922`), which on the located path is `return self.get(**kwargs), False` (`query.py:932`) — `defaults` is unpacked into the object only on the create path (`query.py:934-941`) | R + I | LOCATE hands the object back exactly as it stands: neither the DB value nor the delivered value moves. Pinned by the F2P/P2P observations `test_generic_async_aget_or_create` (the located tag still reads `"fatty"`) and `test_generic_get_or_create_when_exists` (`tag.tag == "stinky"`). |

### A.3 `aupdate_or_create` (model) ↔ `aupdate_or_create` wrappers (patch)

| # | model.py impl op (`aupdate_or_create`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `return update_or_create(mgr, obj, exists, requested)` | `return await sync_to_async(self.update_or_create)(**kwargs)` | R + A-reference | as B1, for the refresh-or-produce operation. |
| C2 | `update_or_create`: same `exists`-branch append as B2 (attach only when created) | the related manager's `update_or_create`: `obj, created = super().update_or_create(...)`; `if created: self.add(obj, ...)`; `return obj, created` | R + I | on MEMBERSHIP only, the same shape as B2. The two operations are NOT interchangeable — see C2b, where they are opposites. |
| C2b | `Ensures(mgr.payload == requested)` and `Ensures(Result().payload == requested)`, **unconditional** (both branches), realised by the impl's `if exists: mgr.payload = requested` | `QuerySet.update_or_create` (`query.py:953`): on the located path it applies the requested values (`query.py:969` `setattr(obj, k, v)`) and PERSISTS them (`query.py:986`/`:988` `obj.save(...)`) | R + I | REFRESH leaves the object carrying the caller's values in both branches, and the caller receives that value. This is the asymmetry with B2b and the only place the two operations differ: identity, flag and membership agree in every branch. Pinned by the F2P observations `test_aupdate_or_create` (`new_simple.field == 3` on an existing row) and `test_generic_async_aupdate_or_create` (the located tag reads `"orange"`), and by P2P `test_generic_update_or_create_when_updated` (`tag.tag == "juicy"`). Degenerate calls that supply no values instantiate this with `requested = Old(mgr.payload)`, so it stays TRUE of the real callee there too (mapping.md §2, probed as the `supply=False` G-CONF shape). |

The discriminating content of the change is **two-dimensional**, and the spec
observes both dimensions:

1. **Membership** — a newly-produced object must be **attached** to the related
   set, because the deferred form runs the related manager's OWN immediate form.
   This lives in `ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)` (for
   `acreate`, and under `not exists` for the other two). `model_prepatch*.py`
   reproduce the pre-patch behaviour (deliver the object but do NOT attach) and
   **fail** exactly those clauses (G-DIFF, §D).
2. **Payload** — the deferred form must run the same-named immediate form, and
   the three immediate forms have three different payload disciplines. This
   lives in the A3b/B2b/C2b clauses, whose shapes are deliberately different:
   unconditional for `create`, `exists`-conditional and Old-preserving for
   `get_or_create`, unconditional for `update_or_create`. Without this dimension
   the `get_or_create` and `update_or_create` contracts would be identical, and
   an `aupdate_or_create` that delegated to `get_or_create` — the wrong immediate
   form, contradicting the very fidelity point A3 rests on — would verify.

The `MustTerminate` obligations (A5) additionally close the partial-correctness
vacuity hole: a deferred form that diverges instead of resolving satisfies every
clause vacuously but leaks its termination obligation, so it does not verify.

## B. The `import` hunks

Each changed file gains `from asgiref.sync import sync_to_async` at module top.
This is the provenance of the one library primitive the deferred forms use; it
is not a modelled operation (it introduces the `sync_to_async` callee whose
behaviour G-AX validates, mapping.md §3). No model op corresponds to it.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The genuinely *changed* operation —
the async delegation `await sync_to_async(self.<op>)(**kwargs)` — is modelled by
a plain call to the sibling immediate form (R), with the single library fact it
relies on (`await sync_to_async(f) == f`, result + effects) validated against the
**real** `sync_to_async` by G-AX (A-reference, mapping.md §3). There is **no
consumed `@ContractOnly` axiom**: both effects of the immediate forms are
modelled deeply (the list append and the payload write in
`create`/`get_or_create`/`update_or_create`), so the axioms region is empty by
design.

The unchanged callees the immediate forms delegate to (`QuerySet.get_or_create`
at `query.py:922` and `QuerySet.update_or_create` at `query.py:953`) are likewise
modelled deeply rather than axiomatised: their two payload disciplines are
written out as the model's locate branch (`return Outcome(obj, False,
mgr.payload)`) and refresh branch (`mgr.payload = requested`), and G-CONF
refutes the modelling by calling the real functions.

## D. Differential coverage (G-DIFF)

Three independently-observable required behaviours, three failing prepatch
models, each sharing the byte-identical spec and failing on its own membership
clause:

| prepatch file | reverted behaviour | fails on |
|---|---|---|
| `model_prepatch.py` | `acreate` delivers the object with the requested payload but does not attach it | `acreate` post `ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)` |
| `model_prepatch_2.py` | `aget_or_create` gets identity, flag and payload right but does not attach a produced object | `aget_or_create` post `not exists ==> ToSeq(mgr.members) == Old(...) + PSeq(obj)` |
| `model_prepatch_3.py` | `aupdate_or_create` gets identity, flag and payload right (including the refresh of an already-present object) but does not attach a produced object | `aupdate_or_create` post `not exists ==> ToSeq(mgr.members) == Old(...) + PSeq(obj)` |

Each twin reproduces the pre-patch PAYLOAD behaviour faithfully — pre-patch,
`a<op>` reached the QuerySet's own async method, which does apply `**kwargs` /
`defaults` correctly; what it never did was run the related manager's attaching
method — so each twin satisfies every A3b/B2b/C2b clause and fails **only** on
membership. That isolation is the point: it shows the payload legs are not what
carries the twins' failure, and conversely (§below) that membership alone is not
what carries the falsification battery's payload cases.

These mirror the F2P tests: `test_acreate` (the produced simple is `aget`-able
from the m2m set), `test_aget_or_create` / `test_aupdate_or_create` (after a
created object, `acount() == 1`), and their reverse / generic counterparts —
all of which observe that the newly-produced object is a **member** of the
owning instance's related set, which only holds if the related manager's own
attaching method ran. The same tests also observe the payload dimension —
`test_aupdate_or_create` asserts `new_simple.field == 3` after an
`aupdate_or_create` on an **existing** row, `test_generic_async_aupdate_or_create`
reads the located tag as `"orange"`, and `test_generic_async_aget_or_create`
reads its located tag as the unchanged `"fatty"` — so both directions of the
locate/refresh asymmetry are pinned by tests that must pass, not by argument.

## E. verify(model) ⇒ resolved

Each `a<op>` verifies only if it delivers exactly what its sibling immediate
`<op>` delivers AND reproduces **both** of its effects:

* membership — the produced object is attached; an already-present object leaves
  the set unchanged;
* payload — the produced object carries the requested values; an already-present
  object is left untouched by `aget_or_create` and refreshed by
  `aupdate_or_create`, with the delivered value equal to the persisted one.

Every modelled observable (`mgr.members`, `mgr.payload`, `Result().obj`,
`Result().created`, `Result().payload`) is pinned in **every** branch of all six
functions, so any implementation that verifies is behaviourally equal to the
model on the whole modelled state — there is no free observable left for a
same-spec rival to move. By R (manager ↔ related set + persisted field, object ↔
identity, requested content ↔ scalar, attach ↔ append, refresh ↔ payload write,
`(obj, created)` + returned field value ↔ `Outcome`) and by the G-AX-validated
fact `await sync_to_async(f) == f` (result + both effects), the verified deferred
forms equal the gold wrappers `await sync_to_async(self.<op>)(**kwargs)` on the
tested inputs. The gold patch resolves (G-RESOLVE). The trust points are the two
of PLAN §1.1: the `sync_to_async` library fact (G-AX) and refinement fidelity
(this document, G-EQ) — the latter now measured on the payload leg too, by two
oppositely-mutated shadows that each disagree with the real patched code
(mapping.md `## G-CONF`).
