# mapping.md — django__django-15525

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fbacaa58ffc5a62456ee68b90efa13957f761ce4`, states the type
abstraction, and gives the provenance of the routing mechanism the deep model
is validated against (G-AX).

Repo file under change: `django/core/serializers/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_with_natural_key(target_store, world)` | `build_instance(Model, data, db)` — `django/core/serializers/base.py:325` (changed hunk at body lines 339–342) | the modeled changed function: builds a record and resolves its natural key, whose computation dereferences a related record |
| `ModelInstance` / `ModelInstance.routed` | a model instance and its `instance._state.db` association (`ModelState.db`, `django/db/models/base.py:451`, default `None`) | the built record and the data-store id its query-routing state is associated with |
| `KeyedRecord` | the value `natural_key = obj.natural_key()` yields, together with the two facts about the call that produced it — `django/core/serializers/base.py:341` in the patched body | the outcome of computing one record's natural key. **Constructing it IS that computation**, which is why its precondition is the criterion under which a key exists at all: where the routed dereference misses, the real call raises `DoesNotExist` and there is no key to return |
| `KeyedRecord.routed` | `obj._state.db` **as read by the FK dereference inside that `obj.natural_key()` call** (the `hints={"instance": obj}` the descriptor passes the router, `related_descriptors.py:121–122`) | the store association the record carried at the moment its key was computed |
| `KeyedRecord.queried_store` | the alias the related-object queryset was actually routed to for that call — `ConnectionRouter.db_for_read(..., instance=obj)`'s return (`django/db/utils.py:223–238`) | the store the dereference behind that key was sent to. A completed event: nothing later in the real code revises which store that query went to, which is why the model hands out only a read share of both fields |
| `target_store` | the `db` parameter of `build_instance` (the store `loaddata` loads into; `database="other"` in the F2P test) | the target data store |
| `Deployment` | no repo symbol: the pair of routing facts the loader runs *in* — the settings' `DEFAULT_DB_ALIAS` and the fixture's placement of the FK target row | the given world. Neither fact is an argument of `build_instance`, and neither is something any line of it can change; the model therefore hands it to the loader as a read-only share of an object the loader cannot construct (see §2, "the given world") |
| `Deployment.default_store` | `DEFAULT_DB_ALIAS` (`django/db/utils.py`) — the ambient store an unrouted query falls back to | the default data store. Left **free** by the precondition: the obligations are claimed for every target store, the ambient default one included |
| `Deployment.record_store` | the store the related record (the FK target row) lives in — for the regression scenario, the same target store the fixture is loaded into | where the dereferenced related record actually resides |
| `query_store(routed, default)` *(deep model — A-reference)* | `ConnectionRouter._route_db` (`django/db/utils.py:223–238`): returns `instance._state.db` if set, else `DEFAULT_DB_ALIAS` (with no custom routers) | pure spec: the store a related-object dereference is routed to |
| `dereference_succeeds(routed, default, record_store)` *(deep model — A-reference)* | the forward FK descriptor lookup `get_object` → `qs.get(...)` on the routed queryset (`django/db/models/fields/related_descriptors.py:121–122, 165–168, 204–205`): succeeds iff the related row is present in the queried store | pure spec: whether the dereference finds the related record |

The unrouted sentinel `UNROUTED = -1` corresponds to `instance._state.db is None`
(the state of a freshly built `Model(**data)`; `ModelState.db = None` by default,
`django/db/models/base.py:451`). The router treats a None/falsy `_state.db` as
"no association" (`if instance is not None and instance._state.db:`,
`django/db/utils.py:236`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a model instance (`Model(**data)`) | `ModelInstance` with a single touched field `routed` | only the routing-relevant state is modeled; all other fields/columns are irrelevant to the tested behaviour |
| `instance._state.db` (a database alias `str`, or `None`) | `routed: int` (`UNROUTED = -1` for `None`; non-negative ids for concrete stores) | `None ↔ UNROUTED`; each distinct alias ↔ a distinct non-negative int (the F2P uses `"other"` vs `DEFAULT_DB_ALIAS`) |
| `db` argument / `DEFAULT_DB_ALIAS` | `target_store` / `world.default_store` (`int`) | distinct store aliases ↔ distinct ints; the non-default scenario is `target_store != world.default_store`, and the coinciding one (a load into the ambient default store) is *also* in the domain |
| the deployment the loader runs in: `settings.DATABASES` + `DEFAULT_DB_ALIAS` + which database the FK target row is actually in | `Deployment`, handed in as a parameter, with a **read-only share** of each field and an **unsatisfiable constructor precondition** | the refinement of "no line of `build_instance` can move a row between databases, redefine the default alias, or run in a different deployment than the one it was called in". Both restrictions are operational rather than documentary: `properties.py`'s `uniq-move-record` is refused on the assignment and `uniq-forge-world` on the constructor's precondition. The consequence that matters is that the *same* routing facts govern every dereference the loader performs, which is what makes the existence condition below a claim about all of them rather than only the returned one (`uniq-discarded-unrouted-key`) |
| `Model(**data).natural_key()` computing the natural key, which dereferences `self.author` | `KeyedRecord(record, world)`: constructing the outcome, whose precondition is the routed dereference's success (`dereference_succeeds`) and whose fields are what the computation observed | the natural-key computation's FK dereference is the single store-routed query whose success is observable; the rest of `natural_key()` (string concatenation of names) does not touch a store. The computation is modeled as a **producer** because the patch's content is *when* it happens relative to the association: a value that can only be produced from an already-associated record carries that ordering with no temporal operator (refinement.md §A, §B) |
| a real call either yielding a key or raising `RelatedObjectDoesNotExist` (aborting deserialization — the traceback in the problem statement) | the `Requires(dereference_succeeds(record.routed, world.default_store, world.record_store))` of `KeyedRecord` | the model has no exception channel; "the dereference missed" is represented as *there is no outcome to produce*, so an impl that computes a key on a record whose association routes elsewhere cannot return anything at all. Two things make that representation adequate rather than a modelling gap. (a) It sits on the **producer**, so it is discharged at every key computation an impl performs, not only the one whose value is returned — which matches the repo, where a raising `natural_key()` aborts the whole `build_instance` call and is *not* caught by its `try/except Model.DoesNotExist` (that wraps only the `get_by_natural_key` lookup). (b) It is judged against the **given world**, which the impl can neither write nor mint, so "there is no outcome to produce" cannot be evaded by nominating routing facts under which the missing dereference would have hit. Without (b) the whole clause would be vacuous — an impl could satisfy it with numbers of its own and the model would constrain nothing about the deployment the loader is actually in |
| `_state.db` may be reassigned later, but which store a completed query went to cannot | `Acc(self.routed, 1/2)` / `Acc(self.queried_store, 1/2)`: a read share, never a write share | the observables are a record of one past computation. A full permission would let an impl compute the key on an unassociated record and then overwrite both fields with the wanted values, whose repo counterpart is the un-patched code plus a dead assignment (refinement.md, "Why the outcome's fields are a half share") |
| `default_manager.db_manager(db).get_by_natural_key(*natural_key)` (the subsequent pk lookup) | not modeled | this lookup already targets `db` explicitly in BOTH the buggy and fixed code; it is unchanged by the patch and only reached if `natural_key` itself succeeds. The bug is strictly in computing `natural_key`, so the model pins the dereference performed *inside* `natural_key()`. |

The value returned by `build_with_natural_key` abstracts *the natural key that
was computed*, carrying the two facts about the computation that produced it:
which store association the record had at that moment, and which store the
dereference behind the key was therefore sent to. Its mere existence abstracts
"the dereference found the related record" — in the real code a failed
dereference raises `RelatedObjectDoesNotExist`, aborting deserialization, and no
key is produced at all.

## 3. Mechanism provenance (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** in this bundle. The store-routing
rule the model relies on is the UNCHANGED framework behaviour the patch depends
on; it is modeled **deeply** by the pure `query_store` / `dereference_succeeds`
and validated == the real router by `axiom_check.py` (G-AX).

### 3.1 `query_store` ↔ `ConnectionRouter._route_db` (A-reference)
**Reference:** `django/db/utils.py:222–238`. With no custom routers configured
(the default, and the configuration the regression scenario uses), the routing
function is exactly:

```python
def _route_db(self, model, **hints):
    ...
    instance = hints.get("instance")
    if instance is not None and instance._state.db:
        return instance._state.db
    return DEFAULT_DB_ALIAS
```

i.e. route to the instance's associated store if it has one, else the default
store. This is precisely `query_store(routed, default)`:
`routed == UNROUTED` (state `None`/falsy) → `default`; otherwise → `routed`.

The forward FK descriptor obtains its queryset via
`self.field.remote_field.model._base_manager.db_manager(hints=hints).all()`
(`related_descriptors.py:121–122`) with `hints={"instance": <the record>}`
(via `_add_hints`/`get_queryset(instance=...)`), so the related-object query is
routed by exactly this rule using the record's own `_state.db`. Setting
`obj._state.db = db` makes that dereference query store `db`.

### 3.2 `dereference_succeeds` ↔ the FK lookup result (A-reference)
**Reference:** `related_descriptors.py:165–168, 204–205`
(`get_object` → `qs.get(self.field.get_reverse_related_filter(instance))`). The
related row exists only in the store it was loaded into; `qs.get` on a store
that lacks it raises `DoesNotExist`. So the dereference finds the record iff the
routed store equals the store the record lives in:
`query_store(routed, default) == record_store`.

**Soundness check (G-AX):** `axiom_check.py` constructs a real
`django.db.utils.ConnectionRouter` with no custom routers and a stand-in record
carrying `_state.db`, and asserts the real `db_for_read(..., instance=rec)`
matches `query_store` for every association (`None`, default, other) and that
the success criterion matches `dereference_succeeds` over all store
combinations plus 20 000 fuzz cases. It imports only Django (the framework
under test); exit 0 iff sound.

## G-CONF (differential conformance: model vs the REAL patched function)

`conformance_check.py` refutes the refinement leg no other gate covers: does the
MODEL agree with the REAL PATCHED repo function?

**Oracle — CALLED, not transliterated.**
`django.core.serializers.base.build_instance(Model, data, db)`
(`django/core/serializers/base.py:325`; the gold hunk rewrites body lines
339–342). The gate applies the gold patch and puts `/testbed` on `PYTHONPATH`,
so the imported `build_instance` IS the patched source; the script asserts this
(`_assert_oracle_is_patched`, which greps `inspect.getsource` for the
`_state.db` assignment and probes the observed association) and exits 1 rather
than comparing against pre-patch code. It is driven against **real Django** —
five sqlite `:memory:` stores via `settings.configure`, `DATABASE_ROUTERS=[]`,
tables built by the real `schema_editor` — with the F2P test's models
(`tests/fixtures_regress/models.py`: `Person` + `NaturalKeyWithFKDependency`,
`natural_key() == (self.name,) + self.author.natural_key()`) reproduced in a
synthetic app because `/testbed`'s test suite is not importable as a library.
The routing decision, the queryset, the query and the `DoesNotExist` are all
real Django; the only additions inside the model are two pure observation hooks
(record `self._state.db`, record the author row actually dereferenced).

Unlike the velvet sibling (which set `conf_skip=true` on the premise that
observing the fix requires the F2P integration test), the whole scenario is
constructible in-container with no fixtures on disk, no migrations and no
test-suite code — so this bundle drives the real function instead of skipping.

**Shadow — verbatim.** `_shadow_build_with_natural_key` is `model.py:232–243`
(the `# impl-start`/`# impl-end` region) character for character — the region
contains no contract call, so nothing is removed from it — plus the classes and
`@Pure` helpers it depends on (`ModelInstance`, `Deployment`, `query_store`,
`dereference_succeeds`, `KeyedRecord`), each minus its `Requires`/`Ensures`/`Acc`.
`Deployment`'s restrictions are contracts (an unsatisfiable constructor
precondition and a read-only share), so stripping them leaves the two field
stores, and the driver **supplies** the world from the case's alias bijection —
which is the point: the routing facts come from outside the function under
diff, exactly as the settings and the fixture supply them in the repo.
Stripping `KeyedRecord`'s contracts leaves exactly its two field stores, so the
shadow's observables are the values the spec's `Ensures` clauses pin. No
restructuring or renaming. No `PSeq`/`ToSeq` carrier appears in this model, so no
sequence shim is needed. There is **no `@ContractOnly` callee** in this bundle
(§3), so every line of the region is executable and diffed.

**Type bridge (§2 inverted).** `int` store id ↔ database alias `str`;
`UNROUTED = -1` ↔ `instance._state.db is None`; `ModelInstance.routed` ↔
`obj._state.db` at the moment `obj.natural_key()` dereferences the FK;
`target_store` ↔ the `db` argument; `Deployment.record_store` ↔ the alias holding
*the* related `Person` row; `Deployment.default_store` ↔ the id of
`DEFAULT_DB_ALIAS`. The alias↔id bijection is arbitrary, so it is **redrawn
per case** (a random permutation), giving 5 distinct realizable values of
`world.default_store`; only the identity of the ambient default alias is framework-
fixed (`DEFAULT_DB_ALIAS == "default"`). Every store holds a `Person` at every
pk but with a **store-stamped name**, so the resolved author name identifies
*which* store the real deref read — the observable discriminates every misroute,
not merely "default instead of target".

**Observables diffed** — the three `Ensures` of `build_with_natural_key`, read
off the outcome the impl returns:
`routed` (`Ensures Result().routed == target_store` ↔ `obj._state.db` as the
natural-key dereference read it),
`queried_store` (`Ensures Result().queried_store == target_store` ↔ the store the
real FK deref was actually routed to, identified by the store-stamped author
name), and
`deref_ok` (`Ensures dereference_succeeds(...)` ↔ the real deref returned the
*intended* related record rather than raising `RelatedObjectDoesNotExist` or
finding a same-pk row from another store).

Note which leg this covers: `queried_store` is the observable the spec added to
express *when* the association exists relative to the key computation, so G-CONF
is the gate that checks that observable against reality rather than against the
model's own definition — the real deref's routed store, over 100 000 cases.

**Inputs — finite domain enumerated exhaustively, then fuzzed.** Under the
bridge the `Requires` (`target_store != UNROUTED`, `world.record_store ==
target_store`; `world.default_store` **free**) leave a FINITE realizable
domain far smaller than 1e5, so it is enumerated **exhaustively** (all 120
id-permutations × **all 5** target aliases — the ambient default one included,
since the spec leaves the ambient default store free — × 3 author pks × both
inner-`get_by_natural_key` outcomes = 3 602 cases including the boundary
pair), which is stronger than 1e5 samples of it; the run then fuzzes over the
same domain (varying record identity and whether the target store already holds
a matching `Book`, exercising the real function's `to_python` branch) to reach
**N = 100 000** cases. The exact F2P shape runs first
(`database="other"`, author `"J.R.R. Tolkien"`, book `"The Lord of the Rings"`).

**Discrimination self-test.** Before diffing, the script drives the **pre-patch
shape** of the same repo line (`Model(**data).natural_key()`, `base.py:332` @
base_commit — no store association) through the same real Django objects and
requires the observation to **disagree** with the shadow; if the harness cannot
tell patched from unpatched it exits 1 instead of reporting a pass. Validated
out-of-band by two mutants: reverting the gold patch is caught by the
provenance guard, and a mutant that associates the target store only when
`db == "other"` (correct for the F2P alias, wrong elsewhere) produces 75 061
disagreements.

**Pinned seed: `SEED = 15525`** (module constant), `N_CASES = 100_000`.
stdlib + Django only; exit 0 iff zero disagreements, with a JSON report as the
last stdout line.
