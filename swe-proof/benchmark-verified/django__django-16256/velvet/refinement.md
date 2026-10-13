# refinement.md — django__django-16256

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `aCreate` / `aGetOrCreate` / `aUpdateOrCreate` `do` blocks) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A** (axiomatized/abstracted callee — **A-consumed**
where the proof uses an axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The added async members — three behavioural shapes

The gold patch adds three async members to each of three related-manager
factories (reverse-FK, forward-m2m, generic-relation): nine new methods, three
distinct behavioural shapes. Each member delegates, through the unchanged
`asgiref.sync.sync_to_async` bridge, to the **related manager's own**
synchronous member (`create` / `get_or_create` / `update_or_create`) — the
member that establishes the parent↔child relation. The three modeled `method`s
capture the three shapes; the forward/reverse/generic variants are the same
shape over different relation carriers (mapping.md §3.2).

Gold hunk (representative, `acreate`):
```
+        async def acreate(self, **kwargs):
+            return await sync_to_async(self.create)(**kwargs)
```

### A.1 `aCreate` ↔ `acreate`

| # | Solution.lean impl op (`aCreate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `related : List Nat` (the parent's collection of related-object identities, `mut`) | the parent's related collection accessed/mutated through the manager (`self`) | R | "object `o` is linked to the parent" ↔ `o ∈ related`; `len(collection)` ↔ `related.length` (mapping.md §2). |
| A2 | `newObj : Nat` | the saved object's identity produced by the create call | R | `pk` ↔ the `Nat` identity (mapping.md §2). |
| A3 | `require newObj ∉ related` | a freshly created object is not already linked to the parent | R | a `create` produces a brand-new row whose identity is not already in the parent's collection. |
| A4 | `related := related ++ [newObj]` (settle the object) | `await sync_to_async(self.create)(**kwargs)` — the related manager's OWN `create` links the new object | **A-reference** | the awaited bridged call is modeled by the synchronous relation-establishing effect itself; `sync_to_async` is behaviour-preserving (mapping.md §3.1, validated by G-AX). The link (`++ [newObj]`) IS the changed routing's observable. |
| A5 | `return newObj` | the coroutine returns the created object | R | identity on the returned object (mapping.md §2). |

### A.2 `aGetOrCreate` ↔ `aget_or_create`, A.3 `aUpdateOrCreate` ↔ `aupdate_or_create`

Both share one shape: a `preexists` branch reports an existing object with
`created = False` and leaves the collection unchanged; the `¬ preexists` branch
settles a new object with `created = True`.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `(preexists, existingObj, newObj)` inputs | the (object, created) the sync `get_or_create`/`update_or_create` resolves | R | `(obj, created)` ↔ `(identity, flag)`; `True`/`False` ↔ `true`/`false` (mapping.md §2). |
| B2 | `if preexists then return (existingObj, false)` (collection unchanged) | a matching object already exists ⇒ it is returned with `created=False`, no new link | I + R | concrete branch; `related = relatedOld` pins the unchanged frame (directive 5). |
| B3 | `else related := related ++ [newObj]; return (newObj, true)` | `await sync_to_async(self.get_or_create/update_or_create)(...)` runs the related manager's OWN member, which links the new object | **A-reference** | same A-reference as A4: the awaited bridged call is the synchronous relation-establishing effect; `++ [newObj]` is the new link. G-AX. |

`update_or_create` differs from `get_or_create` only in that it refreshes the
matching object's fields; that refresh does not change the parent's collection
**membership**, which is the observable the F2P tests pin (`acount`/`aget`), so
both map to the identical modeled shape. (The `defaults={"field": 3}` refresh in
`test_aupdate_or_create` is a field write on an already-linked row — out of the
membership carrier, mapping.md §2.)

## C. No kind-3 (inexpressible-changed-op) steps; conf_skip

Every step is R, A, or I. The one operation that genuinely *changed* — routing
the coroutine to the related manager's own relation-establishing member instead
of the inherited QuerySet coroutine — is modeled as the **A-reference** link
step (`related := related ++ [newObj]`), whose equality to the real awaited
`sync_to_async(self.<member>)(...)` is validated by G-AX (`axiom_check.py`):
the bridge preserves both the return value and the relation side effect. There
is no consumed axiom about the function under change.

The impl region's only non-trivial op is that A-reference link step; there is no
DB-free, input-dependent R/I computation to differential-test. Per SPEC_GUIDE
§0, `meta.json conf_skip=true` and `conformance_check.py` is a `status=skip`
stub. The observable (the object becomes reachable through the parent's related
manager) is a live DB relation side effect, reproducible only by the F2P
integration tests, not by a fuzzable transliteration.

## D. verify(Solution) ⇒ resolved

`aCreate`/`aGetOrCreate`/`aUpdateOrCreate` verify only if a freshly produced
object is settled into the parent's collection (`related = relatedOld ++
[newObj]`) on the create / no-preexisting branch, and the collection is left
unchanged (`related = relatedOld`) when a matching object already exists. By R
(`collection ↔ List Nat`, `pk ↔ Nat`, `(obj,created) ↔ (Nat,Bool)`) the verified
methods equal the gold patch's async members on the tested operations; by the
A-reference (G-AX) the modeled link step equals the real awaited
`sync_to_async(self.<member>)(...)`. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited bridge — and the gold patch resolves (G-RESOLVE). The three prepatches
reproduce the bug (the inherited coroutine that never links): each fails exactly
the `related = relatedOld ++ [newObj]` clause (G-DIFF). Trust points are exactly
the two of plan §1.1: A-reference soundness (G-AX) and refinement fidelity (this
doc, G-EQ).
