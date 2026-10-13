# mapping.md — django__django-16256

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 76e37513e22f4d9a01c7f15eee36fe44388e6670`, states the type
abstraction (the bijection G-AX / G-CONF use to bridge Lean↔Python), and gives
the provenance of each callee.

Repo files under change:
* `django/db/models/fields/related_descriptors.py`
* `django/contrib/contenttypes/fields.py`

`spec_provenance: "cold"` — the specification was derived from scratch from the
`problem_statement`, the gold `patch`, and the repo source at `base_commit`. No
pre-existing twin/spec was consulted.

## 1. Symbol ↔ repo binding

The gold patch adds three async members to each of three related-manager
factories (reverse-FK, forward-m2m, and the generic-relation manager) — nine new
methods in total. All nine share one behavioural shape: the async member
delegates, through the unchanged `asgiref.sync.sync_to_async` bridge, to the
**related manager's own** synchronous member (`create` / `get_or_create` /
`update_or_create`), which is the member that establishes the parent↔child
relation. The three modeled `method`s capture the three distinct shapes; the
forward/reverse/generic variants are the same shape over different relation
carriers (recorded in §3).

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `aCreate (mut related) (newObj)` | `acreate` — added at `related_descriptors.py:797` (reverse FK), `:1200` (forward m2m); `contenttypes/fields.py:752` (generic) | modeled async creator: delegates to the related manager's own `create`, which links the new object |
| `aGetOrCreate (mut related) (preexists) (existingObj) (newObj)` | `aget_or_create` — added at `related_descriptors.py:804` / `:1208` ; `contenttypes/fields.py:759` | modeled async get-or-create: delegates to the related manager's own `get_or_create` |
| `aUpdateOrCreate (mut related) (preexists) (existingObj) (newObj)` | `aupdate_or_create` — added at `related_descriptors.py:813` / `:1217`; `contenttypes/fields.py:766` | modeled async update-or-create: delegates to the related manager's own `update_or_create` |
| (the unchanged callee, not a `Solution.lean` symbol) | `asgiref.sync.sync_to_async` (`asgiref/sync.py`) | runs the wrapped synchronous callable in a thread and returns its result; preserves both the return value and the relation side effect (A-reference, G-AX) |

The synchronous members the async ones delegate to — `RelatedManager.create`
(`related_descriptors.py:787`), `ManyRelatedManager.create` (`:1185`, which calls
`self.add(...)`), `GenericRelatedObjectManager.create`
(`contenttypes/fields.py:740`), and the `get_or_create` / `update_or_create`
siblings — are **unchanged** by the patch. They are the established, correct
relation-establishing operations; the patch only routes the async members to
them instead of to the inherited `QuerySet` coroutines.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The observable the F2P tests pin is **membership of the operated object in the
parent's related collection** after the operation (every F2P test asserts the
new/updated object is reachable via the parent manager — `acount()` increments,
`aget()` returns it, `assertEqual(new.simple, self.s1)`). We model the parent's
related collection as the carrier and the relation-establishing step as the
append.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the parent's related collection (the set of children reachable through the related manager: the FK back-pointers, the m2m through-rows, or the generic-relation rows) | `related : List Nat` (a `mut` parameter) | the collection of related-object identities ↔ a `List Nat` of object identities; `len(collection)` ↔ `related.length`; "object `o` is linked to the parent" ↔ `o ∈ related`; establishing the link for a fresh `o` ↔ `related := related ++ [o]` |
| an object identity (a saved row's pk) | `Nat` | `pk` ↔ the `Nat` identity; a freshly-created object has an identity not already in the parent's collection (`newObj ∉ related`) |
| `created` flag of `(obj, created)` | `Bool` | `True`/`False` ↔ `true`/`false` |
| the `(obj, created)` tuple returned by `get_or_create`/`update_or_create` | `Nat × Bool` | `(obj, created)` ↔ `(identity, flag)` |
| `await sync_to_async(f)(...)` | a direct call to the modeled relation-establishing step (`sync_to_async` is observationally identity on result + side effects — §3) | the `await` of the threaded sync callable ↔ the synchronous effect itself |

The carrier deliberately abstracts away the asynchronous machinery (event loop,
thread): `sync_to_async` is a behaviour-preserving bridge (§3), so the
observable content the tests check is exactly the synchronous relation effect.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `sync_to_async` is behaviour-preserving (A-reference)
**Callee:** `asgiref.sync.sync_to_async` (unchanged; imported by the patch). The
modeled methods replace `await sync_to_async(self.<sync_member>)(**kwargs)` with
a direct application of the relation-establishing step. The soundness of that
replacement rests on one property of the unchanged bridge: running a synchronous
callable through `sync_to_async` and awaiting it returns **the same value** the
callable returns and performs **the same side effects** (here: linking the new
object into the parent's collection). This is the deep model's A-reference.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`asgiref.sync.sync_to_async` in-container on boundary + fuzz synchronous
callables that (a) return a value and (b) mutate an external collection (the
analogue of "link the child to the parent"), and asserts that the awaited async
result equals the direct synchronous result AND the external collection ends in
the identical state. Imports only `asyncio` + `asgiref.sync` (the unchanged
callee itself) — no patched repo code. Exit 0 iff behaviour-preserving.

### 3.2 The three relation carriers (forward / reverse / generic)
The nine added methods cover three relation kinds. They share the modeled shape;
the only difference is which unchanged sync member establishes the link:
* **reverse FK** (`create_reverse_many_to_one_manager`): `create` sets the FK on
  the new object (`kwargs[self.field.name] = self.instance`), linking it.
* **forward m2m** (`create_forward_many_to_many_manager`): `create` calls
  `self.add(new_obj, ...)`, inserting the through-row.
* **generic relation** (`GenericRelatedObjectManager`): `create` sets the
  content-type + object-id fields, linking it.
In every case the sync member is unchanged and the link is established; the model
abstracts all three as `related := related ++ [newObj]`. No flag-dependent
configuration applies.

## 4. G-CONF fuzz seed
`conformance_check.py` is a **skip stub** (`meta.json conf_skip=true`): the impl
region's only non-trivial op is the A-reference relation-establishing step
(`sync_to_async` bridge, §3.1), validated by G-AX; there is no R/I-tagged
computation to differential-test (see refinement.md §C). The pinned seed
**`16256`** is recorded for parity but the stub exits `status=skip`.
