# refinement.md — django__django-15525

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_with_natural_key` impl region, the outcome-producing constructor
`KeyedRecord`, the given-world carrier `Deployment`, and the deep routing model
`query_store` / `dereference_succeeds`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses a `@ContractOnly`
axiom's `Ensures`), **A-reference** (a deep model is validated == the real
callee/mechanism by axiom_check.py / G-AX, NOT consumed), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The build/route site — `build_instance` (`django/core/serializers/base.py:339`)

Gold hunk:
```
-        natural_key = Model(**data).natural_key()
+        obj = Model(**data)
+        obj._state.db = db
+        natural_key = obj.natural_key()
```

Read the shape of this hunk before the table: the three added lines introduce no
new *value*. Both versions end up holding a natural key computed from the same
field data, and the instance the key was computed on is discarded either way.
What the patch changes is **when** the store association exists relative to the
key computation — an event, not a final state. So the model carries the key
computation as a value-*producing* step (`KeyedRecord`) whose existence requires
the record's association to already route the dereference to the store the
related record lives in, and whose two fields record what that one computation
observed. That is the refinement of "before" into something a state-based
verifier can see; it is not extra machinery bolted on beside the observables.

| # | model.py impl op (`build_with_natural_key`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `obj = ModelInstance(UNROUTED)` | `obj = Model(**data)` | R | a freshly built record. Its routing state is unassociated: `ModelInstance.routed = UNROUTED` ↔ `obj._state.db is None` (`ModelState.db = None` default; mapping.md §1–2). Only the routing-relevant field is modeled. |
| A2 | `obj.routed = target_store` | `obj._state.db = db` | R | associate the record with the target store. `routed ↔ _state.db`, `target_store ↔ db` (the integer-id ↔ alias bijection, mapping.md §2). This is the line of the fix that carries state. |
| A0 | `world` (the `Deployment` parameter) | — (no counterpart: the settings' `DEFAULT_DB_ALIAS` and the fixture's placement of the related row) | R | the two routing facts the loader runs *in*. Not a `build_instance` argument and not something it can produce or write; see "The given world" below. |
| A3 | `keyed = KeyedRecord(obj, world)` | `natural_key = obj.natural_key()` (whose body dereferences the related record, e.g. `self.author.natural_key()`) | R + A-reference | **this construction IS the natural-key computation**, and it is the only operation in the model that performs the dereference. R: producing the outcome ↔ producing `natural_key`; `keyed.routed` ↔ the `_state.db` the instance carried at that moment, `keyed.queried_store` ↔ the store the related-record query was actually routed to (mapping.md §3.3 — the observable conformance_check.py diffs against real patched Django). A-reference: *which* store that is, and whether the related record is found there, is the **unchanged** framework router, modeled **deeply** by `query_store` / `dereference_succeeds` with **no consumed axiom** — validated == the real `ConnectionRouter._route_db` + FK lookup out-of-band by G-AX (axiom_check.py): with no custom routers the dereference routes to `obj._state.db` if set, else the default store, and succeeds iff that store holds the related record (mapping.md §3.1–3.2). The constructor's precondition `dereference_succeeds(record.routed, world.default_store, world.record_store)` refines the real line's two outcomes: where the routed query misses, there is no natural key and no outcome to return — the real code raises `DoesNotExist` instead of returning one. Because that precondition sits on the *producer*, it refines the real line's failure mode at **every** occurrence of the real line, not only at the one whose value is returned: a `natural_key()` call whose dereference misses raises before anything downstream runs, and `build_instance`'s `try/except Model.DoesNotExist` wraps only the `get_by_natural_key` lookup, so it does not catch it. |
| A4 | `return keyed` | `natural_key = obj.natural_key()` then `… get_by_natural_key(*natural_key) …; return Model(**data)` | R + (unchanged tail) | the modeled observable is the computed key's provenance: the association the record carried when its key was computed, and the store the dereference behind that key was sent to. The subsequent `db_manager(db).get_by_natural_key(*natural_key)` lookup is unchanged by the patch (it already targets `db` in both pre- and post-patch code) and is only reachable once `natural_key` succeeds; it is therefore outside the modeled delta. |

One impl-region op an auditor may see in a rival has **no** counterpart at all:
evaluating `query_store` / `dereference_succeeds` in an `Assert` (as
`properties.py`'s `uniq-skip-assoc-keep-assert` does) refines to **nothing** — it
is a statement about a routing state, not a query issued against a store, so it
must not be read as an early or extra `natural_key()` call. The dereference
happens at A3 and nowhere else.

### Why the outcome's fields are a half share

`KeyedRecord` hands out `Acc(self.routed, 1/2)` and
`Acc(self.queried_store, 1/2)`: enough for any consumer to read what the key
computation observed, never enough for a later step to restate it. That is a
refinement obligation, not hygiene. In the real code "which store did that
dereference go to" is a completed event; no subsequent line can revise it. A full
permission would let an impl compute the key on an unassociated record and then
overwrite both fields with the values the postcondition asks for — an impl whose
repo counterpart is the un-patched code plus a dead assignment, which does **not**
resolve. `properties.py`'s `uniq-restate-observables` is exactly that impl, and it
is refused for lack of permission. (Measured, not assumed: with a full permission
in the constructor's `Ensures`, that rival verifies.)

The discriminating content of the change — the store association existing
**before** the natural key is computed — therefore lives in A2 *together with* the
A3 precondition that consumes it. `model_prepatch.py` reproduces the pre-patch
code (builds `obj = ModelInstance(UNROUTED)`, computes its natural key directly,
never sets `routed`) and **fails** at A3: `The precondition of method KeyedRecord
might not hold. Assertion dereference_succeeds(record.routed,
world.default_store, world.record_store) might not hold.` — an unrouted query falls back to the default
store, which on a non-default target does not hold the related record. This is
exactly the spec sensing the change (G-DIFF).

Note where that failure lands: at the key computation, not on the final state of
anything. An impl that computes the key first and associates afterwards
(`properties.py`'s `uniq-key-before-assoc`) reaches a final state identical to the
gold one and is refused at the same point, while an impl that associates, computes
the key, and then *releases* the association again (`pos-control-release-after`)
is correct and does verify — once the key is in hand the association is dead, in
the model and in the repo alike (the lookup that follows names `db` explicitly).

### The given world `Deployment` — what it refines, and why it is not an input

`build_with_natural_key` takes a `Deployment` carrying two ints, and neither is
an argument of the real `build_instance(Model, data, db)`. They are **facts about
the surroundings the fix operates in**, not impl inputs that get refined to a
`build_instance` argument:

- `world.record_store` = the store the related (FK-target) record actually
  resides in — a fact about the fixture under load, not a value `build_instance`
  receives. The precondition pins `world.record_store == target_store` (the
  regression scenario loads the related record into the same target store), so
  under the precondition any impl that reads it is reading a value equal to
  `target_store`; it coincides with reading `target_store` and refines
  accordingly. It carries no refinable counterpart of its own.
- `world.default_store` = `DEFAULT_DB_ALIAS`, the ambient store an unrouted query
  falls back to — also a fact about the surroundings (the router's default), not
  a `build_instance` argument. It is left **free**: the spec claims its
  obligations for every target store, the ambient default one included, so no
  clause below is satisfiable only on the differing-stores half of the domain.

What makes these facts rather than parameters is **operational**, not a matter of
this document's assurance, and that is the load-bearing part of the design:

1. The loader holds a **read-only share** of each field (`Acc(..., 1/2)`, handed
   back by the `Ensures`), so it cannot write them. The refinement is exact: no
   line of `build_instance` moves a row from one database to another, and none
   redefines `DEFAULT_DB_ALIAS`. `properties.py`'s `uniq-move-record` is the impl
   that answers a missing related row by declaring the row to be in the default
   database instead of associating the instance with the database being loaded
   into; it is refused on the assignment.
2. A `Deployment` **cannot be produced** — its constructor's precondition is
   unsatisfiable — so a loader holds a world only because it was handed one. The
   refinement: `build_instance` runs in the deployment it is called in, and
   cannot conjure a second one in which the query it wants to make would have
   succeeded. This is what makes A3's precondition a claim about the deployment
   the loader actually runs in. `properties.py`'s `uniq-forge-world` is the impl
   that mints a convenient world (one whose ambient fallback holds the related
   record) and computes the key against it; it is refused because no world can be
   produced. (Measured, not assumed: with a satisfiable constructor precondition,
   that rival verifies.)

Together, 1 and 2 mean the two routing facts are the **same** at every
dereference the loader performs. That is why A3's precondition binds every
occurrence of the real `natural_key()` line rather than only the occurrence whose
value is returned — see `uniq-discarded-unrouted-key`, an impl whose returned
observables are byte-identical to the gold's and which additionally performs the
unpatched `Model(**data).natural_key()` call, i.e. the exact line that raises on
the F2P scenario.

The discrimination is on whether a dereference **finds** the related record, not
on how many dereferences happen: `pos-control-two-associated-keys` performs two
key computations, both on associated records, and verifies. Pinning the gold
impl's dereference count would over-fit — the real function guarantees no such
thing.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or unchanged-tail. The operation that
genuinely *changed* is the pair (A2, A3): establishing the store association (a
plain field assignment, an **R** type refinement of `obj._state.db = db`) and
computing the natural key with that association in force (**R** on the value
produced, **A-reference** on the routing mechanism). The ordering between them —
the part of the hunk that has no state of its own — is expressed with no temporal
operator at all: the outcome of a key computation can only be *produced*, and
producing it requires the record's association to already route the dereference to
the store the related record lives in — judged against the world the loader was
handed, which it can neither write nor replace, so the judgement is the same at
every key computation the loader performs. `KeyedRecord` is **not** an axiom: it
carries a real body, verified against its own contract, so nothing here is assumed
rather than established. `Deployment` is not an axiom either: it is an ordinary
class, and the unavailability of its constructor is a precondition the verifier
**discharges** (`uniq-forge-world` fails on `Assertion False might not hold`)
rather than an assumption it grants. The routing *mechanism* A3 depends on is the
**unchanged** framework router; it is modeled **deeply** (`query_store` /
`dereference_succeeds`) and checked against the real router by G-AX as an
**A-reference**, never hidden behind a consumed axiom. There is no consumed
`@ContractOnly` axiom in this bundle.

## C. verify(model) ⇒ resolved

`build_with_natural_key` verifies only if it produces an outcome, and it can
produce one only by computing a natural key on a record whose own association
routes the dereference to the store the related record lives in (A3's
precondition, judged against the given world) — and only if that outcome reports
the association `target_store` (`Result().routed == target_store`, A2) with the
dereference behind the key sent there rather than to the ambient default
(`Result().queried_store == target_store`, A3). On a non-default target those
clauses hold **only** when the record was associated with the target store before
its key was computed, and the outcome's fields cannot be restated afterwards
(half share). Because the ambient default store is left free, the clauses must
hold on the coinciding sub-domain too, where the existence condition is
satisfiable without any association and only `Result().routed` refuses the rival
(`uniq-assoc-only-when-not-default`). And because the world can be neither
written nor minted, the existence condition binds **every** key computation the
impl performs, not only the returned one — so an impl cannot pass by keeping the
unpatched dereference alongside a correct one (`uniq-discarded-unrouted-key`). By R (`routed ↔ _state.db`, `target_store ↔ db`, the
instance/field bijection, and the key computation ↔ `obj.natural_key()`) the
verified impl equals the gold patch's `obj = Model(**data); obj._state.db = db;
obj.natural_key()` on the tested scenario; by G-AX the deep routing model equals
the real `ConnectionRouter` routing + FK lookup (A-reference), and by G-CONF both
reported observables agree with real patched Django over 100 000 store
combinations. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited mechanism — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ) plus the A-reference soundness (G-AX); there is no consumed-axiom
trust point.
